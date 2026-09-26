"""Uji B (batas atas) sesuai `vault/06-Results/06 - Pre-registration Horizon.md`: apakah pilihan token/jam whale lebih baik dari acak, di horizon panjang?

Satu kueri Dune saja. Alasannya uang: baseline "token & hari acak" TIDAK perlu dari Dune - dia bisa
dihitung dari kline Aster yang sudah kami unduh untuk menilai whale juga. Kueri kedua cuma akan
membakar kredit untuk angka yang sudah ada di disk kami.

Hasil kueri di-cache (`data/whale/panel-entries-*.json`), jadi iterasi analisis berikutnya nol
kredit - dan itu penting, karena kemarin kita lihat kueri yang MENGIRIM BARIS adalah konsumer
terbesar (503 detik), bukan yang berpikir.

Cara membacanya: lihat `vault/06-Results/06 - Pre-registration Horizon.md` §"Konsekuensi". Ringkasnya - angka positif di sini BELUM berarti
apa-apa sampai Uji A (prospektif, tanpa lookahead) ikut searah.

Pakai:  python tools/whale_sweep.py --days 90
         python tools/whale_sweep.py --report          # baca cache, nol kueri
"""
from __future__ import annotations

import argparse
import calendar
import collections
import json
import math
import os
import random
import statistics
import sys
import time
import urllib.error
import urllib.request
from bisect import bisect_left
# Windows: cmd.exe default cp1252 dan glyph yang kami cetak (`①④⑥` di arah, `⚠` di laporan)
# bukan bagian dari yang di-hash - jadi encoding stdout yang disetel, bukan stringnya.
# Tanpa ini, `print` bisa pecah DI TENGAH tabel dan separuh hasilnya terbaca seperti laporan penuh.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # stdout tanpa reconfigure (mis. tertangkap harness) = biarkan apa adanya

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import bars  # noqa: E402

DUNE = "https://api.dune.com"
CACHE = os.path.join(ROOT, "data", "whale")
SYMCACHE = os.path.join(ROOT, "data", "aster_symbols.json")
HORIZONS = {"24 jam": 24, "48 jam": 48, "7 hari": 168, "30 hari": 720}
MIN_N = 20
BH_ALPHA = 0.10
MAX_WALLETS = 120          # panel terbesar yang masih muat di satu IN-list yang waras


def dune_key():
    k = (os.environ.get("DUNE_API_KEY") or "").strip()
    if k:
        return k
    for p in (os.path.join(ROOT, ".dune.env"), os.path.expanduser("~/.config/dune/.env")):
        try:
            for ln in open(p, encoding="utf-8"):
                if ln.startswith("DUNE_API_KEY="):
                    return ln.split("=", 1)[1].strip()
        except OSError:
            pass
    return ""


def api(path, key, body=None, timeout=150):
    h = {"X-Dune-Api-Key": key, "Accept": "application/json", "User-Agent": "Mozilla/5.0 (compatible; fabius-whale/1.0)"}
    data = json.dumps(body).encode() if body is not None else None
    if data:
        h["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(DUNE + path, data=data, headers=h),
                                    timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        t = e.read().decode("utf-8", "replace")
        try:
            return json.loads(t)
        except Exception:  # noqa: BLE001
            return {"_raw": t[:220]}
    except Exception as e:  # noqa: BLE001
        return {"_error": f"{type(e).__name__}: {str(e)[:130]}"}


def run_sql(key, sql, wait=900):
    j = api("/api/v1/sql/execute", key, {"sql": sql, "performance": "medium"})
    eid = j.get("execution_id")
    if not eid:
        raise SystemExit(f"execute gagal: {json.dumps(j)[:220]}")
    t0 = time.time()
    while time.time() - t0 < wait:
        st = api(f"/api/v1/execution/{eid}/status", key)
        state = str(st.get("state", ""))
        if state and state not in ("QUERY_STATE_EXECUTING", "QUERY_STATE_PENDING",
                                   "QUERY_STATE_STARTING"):
            break
        time.sleep(4)
    if "COMPLETED" not in state:
        raise SystemExit(f"kueri {state}: {str(st.get('error', {}).get('message'))[:200]}")
    out, cur, ok = [], None, True
    # `limit=5000` adalah dugaan besarku kemarin, dan dugaan itu menghasilkan "0 baris" yang
    # terbaca seperti "whale tidak trading apa pun". API ini membalas error untuk limit di atas
    # 1000 TANPA mengangkat pengecualian - jadi nilainya kukunci ke 1000 dan setiap respons
    # gagal DICETAK mentah-mentah. Kegagalan yang diam adalah kegagalan yang akan kuulang.
    PAGE = 1000
    while True:
        p = f"/api/v1/execution/{eid}/results?limit={PAGE}" + (f"&offset={cur}" if cur else "")
        res = None
        for t in range(3):
            res = api(p, key, timeout=180)
            if isinstance(res, dict) and (res.get("result") or {}).get("rows") is not None:
                break
            print(f"  halaman {cur} percobaan {t + 1}: {json.dumps(res)[:220]}")
            time.sleep(4 + 4 * t)
        else:
            ok = False
            break
        if not isinstance(res, dict) or (res.get("result") or {}).get("rows") is None:
            ok = False
            # Jangan menyebut "terpotong" kalau yang terjadi sebenarnya "query tidak mengembalikan
            # apa pun" - yang pertama berarti kurang telan, yang kedua berarti filter kita salah
            # (dan kemarin filter kita memang salah: from_hex menolak prefiks 0x secara diam-diam).
            last = json.dumps(res)[:180] if isinstance(res, dict) else str(res)[:180]
            print(f"  respons hasil: {last}")
            break
        rows = res["result"]["rows"]
        out.extend(rows)
        meta = (res["result"].get("metadata") or {})
        total = meta.get("total_row_count")
        # API ini TIDAK mengirim `next_offset` - key itu tidak ada, dan bergantung padanya
        # membuat kita berhenti diam-diam di halaman pertama (terukur: cache hanya 1.000 baris
        # padahal total_row_count memberi tahunya). Jadi geser offset sendiri dan berhenti hanya
        # kalau (a) sudah terkumpul total-nya, atau (b) halaman ini kosong.
        cur = (cur or 0) + len(rows)
        if len(rows) < PAGE or (total and len(out) >= int(total)):
            break
        print(f"  ... {len(out)}/{total} baris", flush=True)
    dur = (st.get("total_duration_ms") or 0) / 1000
    return out, f"durasi_dune={dur:.0f}s baris={len(out)}" + ("" if ok else " [TERPOTONG]"), ok


def panel_wallets():
    """Daftar wallet panel, dinormalisasi ke heks 40 karakter TANPA prefiks 0x.

    Kenapa sekeras ini: `from_hex('0x4af2…')` di Trino TIDAK melempar error - ia menghasilkan
    nilai yang tidak pernah cocok, jadi `taker IN (…)` membalas 0 baris dan seluruh uji terlihat
    seperti "whale tidak trading apa pun". Ini jebakan heks yang sama untuk KETIGA kalinya di
    proyek ini (`to_hex` tanpa prefiks, `len==42`, sekarang prefiks masuk). Maka prefiks dibuang
    DAN jumlahnya dipaksa: kalau ada satu saja yang tidak 40, alatnya berhenti.
    """
    c = collections.Counter()
    for ln in open(os.path.join(ROOT, "universe", "wallet-flow.jsonl"), encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        r = json.loads(ln)
        if r.get("k") == "tx" and r.get("m"):
            m = str(r["m"]).lower()
            c[m[2:] if m.startswith("0x") else m] += 1
    thick = [(w, n) for w, n in c.most_common() if n >= MIN_N]
    out = [w for w, _ in thick][:MAX_WALLETS]
    rusak = [w for w in out if len(w) != 40]
    if rusak:
        raise SystemExit(f"wallet tidak berbentuk heks 40 karakter: {rusak[:3]} -> berhenti, "
                         "jangan kirim IN-list yang akan cocok dengan nol apa pun")
    return out, len(thick)


def perp_base_index():
    """base asset -> kontrak perp (dari cache exchangeInfo Aster)."""
    if not os.path.exists(SYMCACHE):
        raise SystemExit("data/aster_symbols.json belum ada - jalankan tools/direction.py sekali "
                         "untuk mengisi cache daftar perp")
    out = collections.defaultdict(list)
    for s in json.load(open(SYMCACHE, encoding="utf-8")):
        b = str(s.get("base") or "").upper()
        if b and s.get("status") == "TRADING":
            out[b].append(s["symbol"])
    return out


SKIP_BASES = {"USDT", "USDC", "USD1", "DAI", "WBNB", "WBTC", "BTCB", "BTC", "ETH", "SOL", "XRP",
              "LTC", "BCH", "ADA", "DOT", "LINK", "AVAX", "TRX", "TON", "SUI", "APT", "NEAR"}


def _kandidat_simbol():
    """Simbol yang boleh masuk: base asset ber-kontrak perp, bukan stable/wrapped.

    Satu fungsi untuk dua pemanggil (`fetch_entries` dan `--probe`): kalau daftarnya ditulis dua
    kali, "probe" dan "produksi" bisa menguji query yang berbeda sambil terlihat sama - dan hasil
    0 baris tidak akan pernah bisa diinterpretasi dengan jujur.
    """
    return sorted(b for b in perp_base_index() if 3 <= len(b) <= 12 and b not in SKIP_BASES)


def fetch_entries(days, force=False):
    fp = os.path.join(CACHE, f"panel-entries-{days}d.json")
    if os.path.exists(fp) and not force:
        rows = json.load(open(fp, encoding="utf-8"))
        print(f"entri dibaca dari cache: {len(rows)} baris (nol kredit)")
        return rows
    key = dune_key()
    if not key:
        raise SystemExit("tidak ada DUNE_API_KEY")
    wallets, thick_n = panel_wallets()
    cand = _kandidat_simbol()
    print(f"panel: {len(wallets)} wallet (dari {thick_n} yang n>={MIN_N}) | "
          f"simbol kandidat: {len(cand)}")
    in_w = ", ".join(f"from_hex('{w}')" for w in wallets)
    in_s = ", ".join(f"'{s}'" for s in cand)
    sql = ("SELECT date_trunc('day', d.block_time) AS hari, to_hex(d.taker) AS wallet, "
           "to_hex(d.token_bought_address) AS token, upper(t.symbol) AS simbol, "
           "min(d.block_time) AS masuk, count(*) AS beli, sum(d.amount_usd) AS usd "
           "FROM dex.trades d JOIN tokens.erc20 t "
           "  ON d.token_bought_address = t.contract_address AND t.blockchain = 'bnb' "
           "WHERE d.blockchain = 'bnb' "
           f"AND d.block_time > now() - INTERVAL '{days}' DAY "
           f"AND upper(t.symbol) IN ({in_s}) AND d.taker IN ({in_w}) "
           "GROUP BY 1,2,3,4 ORDER BY 1")
    os.makedirs(CACHE, exist_ok=True)
    print("kirim 1 kueri Dune (entri panel 90 hari)...")
    rows, note, ok = run_sql(key, sql)
    print(f"  {note}")
    if not rows:
        raise SystemExit("tidak ada baris - berhenti")
    if not ok:
        print("  HASIL TERPOTONG: jangan dipakai menyimpulkan (bias ke arah yang tidak diketahui)")
    json.dump(rows, open(fp, "w", encoding="utf-8"), ensure_ascii=False)
    return rows


def klines(perp, days):
    d = bars.load(perp, "1h")
    have = (d or {}).get("bars") or []
    if not have or len(have) < (days + 40) * 24 * 0.6:
        got, meta = bars.fetch(perp, "1h", days + 40, verbose=False)
        if got:
            bars.save(perp, "1h", got, meta)
            have = got
    if not have:
        return None
    return {"t": [b["t"] for b in have], "c": [float(b["c"]) for b in have]}


def fwd(kl, t_ms, hours):
    ts = kl["t"]
    i = bisect_left(ts, t_ms)
    if i is None or i >= len(ts):
        return None
    j = i + hours
    if j >= len(ts) or not ts[i]:
        return None
    return (kl["c"][j] / kl["c"][i] - 1.0) * 1e4


def bh(pvals, alpha=BH_ALPHA):
    m = len(pvals)
    if not m:
        return set()
    order = sorted(range(m), key=lambda i: pvals[i])
    kmax = -1
    for r, i in enumerate(order):
        if pvals[i] <= alpha * (r + 1) / m:
            kmax = r
    return set(order[:kmax + 1]) if kmax >= 0 else set()


def boot_p(panel, base, iters=4000, seed=0):
    """Bootstrap dua sisi atas selisih rata-rata. Deterministik (seed tetap) supaya bisa diulang
    orang lain dan menghasilkan angka yang sama persis."""
    if len(panel) < 5 or len(base) < 5:
        return 1.0
    rng = random.Random(seed)
    obs = statistics.fmean(panel) - statistics.fmean(base)
    pool = panel + base
    n1 = len(panel)
    ge = 0
    for _ in range(iters):
        rng.shuffle(pool)
        d = statistics.fmean(pool[:n1]) - statistics.fmean(pool[n1:])
        if abs(d) >= abs(obs):
            ge += 1
    return (ge + 1) / (iters + 1), obs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--count-only", action="store_true",
                    help="cetak respons MENTAH untuk satu kueri count(*) - untuk bedakan "
                         "'filter tidak cocok' dari 'caraku membaca respons salah'")
    ap.add_argument("--probe", action="store_true",
                    help="kirim SQL besar yang SESUNGGUHNYA dipakai; cetak state, "
                         "execution_cost_credits, dan hasil mentah - lalu berhenti")
    ap.add_argument("--refetch", action="store_true", help="buang cache, kirim ulang kueri")
    a = ap.parse_args()

    if a.probe:
        key = dune_key()
        wallets, thick_n = panel_wallets()
        in_w = ", ".join("from_hex('%s')" % w for w in wallets)
        in_s = ", ".join("'%s'" % s for s in _kandidat_simbol())
        sql = ("SELECT date_trunc('day', d.block_time) AS hari, to_hex(d.taker) AS wallet, "
               "to_hex(d.token_bought_address) AS token, upper(t.symbol) AS simbol, "
               "min(d.block_time) AS masuk, count(*) AS beli, sum(d.amount_usd) AS usd "
               "FROM dex.trades d JOIN tokens.erc20 t "
               "  ON d.token_bought_address = t.contract_address AND t.blockchain = 'bnb' "
               "WHERE d.blockchain = 'bnb' AND d.block_time > now() - INTERVAL '90' DAY "
               "AND upper(t.symbol) IN (" + in_s + ") AND d.taker IN (" + in_w + ") "
               "GROUP BY 1,2,3,4 ORDER BY 1")
        print(f"SQL {len(sql)} char | wallet={len(wallets)} simbol={in_s.count(',') + 1}")
        j = api("/api/v1/sql/execute", key, {"sql": sql, "performance": "medium"})
        eid = j.get("execution_id")
        if not eid:
            print(f"execute ditolak: {json.dumps(j)[:400]}")
            return
        st = {}
        for _ in range(140):
            st = api(f"/api/v1/execution/{eid}/status", key)
            if str(st.get("state", "")).endswith(("COMPLETED", "FAILED", "CANCELLED")):
                break
            time.sleep(5)
        print(f"state={st.get('state')} credits={st.get('execution_cost_credits')} "
              f"mulai={st.get('execution_started_at')} selesai={st.get('execution_ended_at')}")
        if "FAILED" in str(st.get("state")):
            print(f"error: {json.dumps(st.get('error'))[:500]}")
            return
        print("RAW:", json.dumps(api(f"/api/v1/execution/{eid}/results?limit=3", key))[:700])
        return

    if a.count_only:
        key = dune_key()
        if not key:
            raise SystemExit("tidak ada DUNE_API_KEY")
        wallets, thick_n = panel_wallets()
        in_w = ", ".join(f"from_hex('{w}')" for w in wallets[:5])
        for label, sql in (
            ("panel 5 wallet, 30 hari",
             "SELECT count(*) AS n FROM dex.trades WHERE blockchain='bnb' "
             f"AND taker IN ({in_w}) AND block_time > now() - INTERVAL '30' DAY"),
            ("tanpa filter wallet, 1 hari",
             "SELECT count(*) AS n FROM dex.trades WHERE blockchain='bnb' "
             "AND block_time > now() - INTERVAL '1' DAY"),
        ):
            j = api("/api/v1/sql/execute", key, {"sql": sql, "performance": "medium"})
            eid = j.get("execution_id")
            print(f"\n{label}: id={eid}")
            for _ in range(60):
                st = api(f"/api/v1/execution/{eid}/status", key)
                if "COMPLETED" in str(st.get("state", "")) or "FAILED" in str(st.get("state", "")):
                    break
                time.sleep(3)
            print(f"  status keys : {sorted(st.keys())}")
            print(f"  state       : {st.get('state')}")
            rs = api(f"/api/v1/execution/{eid}/results?limit=5", key)
            print(f"  RAW results : {json.dumps(rs)[:500]}")
        return

    rows = fetch_entries(a.days, force=a.refetch)

    idx = perp_base_index()
    kl_cache = {}
    panel = collections.defaultdict(lambda: collections.defaultdict(list))
    entri = []
    for r in rows:
        tok = str(r.get("token") or "").lower()
        sym = str(r.get("simbol") or "")
        perps = idx.get(sym) or []
        if not perps or not tok:
            continue
        p = perps[0]
        if p not in kl_cache:
            kl_cache[p] = klines(p, a.days)
        if not kl_cache[p]:
            continue
        try:
            tt = time.strptime(str(r.get("masuk"))[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        t_ms = calendar.timegm(tt) * 1000 + 3_600_000      # UTC, bukan waktu lokal
        w = str(r.get("wallet") or "").lower()
        for hname, hrs in HORIZONS.items():
            v = fwd(kl_cache[p], t_ms, hrs)
            if v is None:
                continue
            entri.append({"w": w, "tok": tok, "sym": sym, "perp": p, "jam": hname,
                          "t_ms": t_ms, "hari": str(r.get("hari"))[:10], "bps": v,
                          "usd": float(r.get("usd") or 0)})
    print(f"entri ternilai: {len(entri)} (token dengan kline: {len(kl_cache)})")

    # BASELINE: semua (perp, hari) di jendela yang sama, entry di bar pertama hari itu.
    print("menghitung baseline acak dari kline lokal...")
    base = collections.defaultdict(list)
    for p, kl in kl_cache.items():
        if not kl:
            continue
        seen_day = set()
        for i, t in enumerate(kl["t"]):
            day = time.strftime("%Y-%m-%d", time.gmtime(t / 1000))
            if day in seen_day:
                continue
            seen_day.add(day)
            for hname, hrs in HORIZONS.items():
                v = (kl["c"][i + hrs] / kl["c"][i] - 1.0) * 1e4 if i + hrs < len(kl["c"]) else None
                if v is not None:
                    # disimpan bersama tanggalnya: tanpa `day`, split-sample tidak bisa dibelah
                    # menurut waktu dan kolom "AWAL/AKHIR" akan jadi hiasan.
                    base[hname].append({"day": day, "v": v})

    def base_vals(hname, lo="0000", hi="9999"):
        return [x["v"] for x in base.get(hname, []) if lo <= x["day"] < hi]

    def mean_diff(pv, bv):
        return (statistics.fmean(pv) - statistics.fmean(bv)) if (pv and bv) else None

    print(f"\n{'horizon':10}{'n panel':>9}{'panel bps':>11}{'baseline':>10}{'selisih':>10}"
          f"{'p boot':>9}  split AWAL / AKHIR")
    print("-" * 82)
    out_rows = []
    for hname in HORIZONS:
        e = [x for x in entri if x["jam"] == hname]
        b = base_vals(hname)
        if len(e) < 30 or len(b) < 30:
            print(f"{hname:10}{len(e):>9}{'-':>41}  (sampel kurang)")
            continue
        pv = [x["bps"] for x in e]
        pr, obs = boot_p(pv, b)
        half = sorted({x["hari"] for x in e})
        cut = half[len(half) // 2] if half else ""
        a1 = [x["bps"] for x in e if x["hari"] < cut]
        a2 = [x["bps"] for x in e if x["hari"] >= cut]
        # Baseline dibelah menurut WAKTU, bukan menurut indeks. Versi pertama memotong daftar lewat
        # posisi (`b[:len//2]`) padahal daftar itu disusun per kontrak, bukan per tanggal - jadi
        # "AWAL/AKHIR" panel dibandingkan dengan dua potong baseline yang bukan periode yang sama,
        # dan kolom itu tidak mengukur apa yang dijanjikan vault/11.
        b1 = mean_diff(a1, base_vals(hname, "0000", cut))
        b2 = mean_diff(a2, base_vals(hname, cut, "9999"))
        def tanda(v):
            return "?" if v is None else ("+" if v > 0 else "-")
        print(f"{hname:10}{len(e):>9}{statistics.fmean(pv):>+11.1f}{statistics.fmean(b):>+10.1f}"
              f"{obs:>+10.1f}{pr:>9.4f}  {tanda(b1)}{abs(b1 or 0):>6.1f} {tanda(b2)}{abs(b2 or 0):>6.1f}")
        # Rata-rata bisa dibajak ekor gemuk. Untuk hasil positif, yang menentukan bukan "mean-nya
        # naik" tapi "medianya ikut naik dan bukan satu-dua lottery ticket yang mengangkatnya".
        srt = sorted(pv)
        med = statistics.median(pv)
        share_big = sum(1 for x in pv if x > 1000.0) / len(pv)
        top1 = statistics.fmean(srt[-max(1, len(srt) // 100):])
        rest = statistics.fmean(srt[:-max(1, len(srt) // 100)] if len(srt) > 100 else srt[:-1])
        print(f"{'':10}median {med:+.1f} bps | share entri > +1.000 bps {share_big*100:.1f}% | "
              f"1% teratas {top1:+.0f} bps, sisanya {rest:+.1f} bps")
        out_rows.append({"horizon": hname, "n_panel": len(e), "panel_bps": statistics.fmean(pv),
                         "panel_median_bps": med, "share_over_1000bps": round(share_big, 4),
                         "top1pct_bps": round(top1, 1), "tanpa_top1pct_bps": round(rest, 1),
                         "base_bps": statistics.fmean(b), "diff_bps": obs, "p_boot": pr,
                         "split_awal": b1, "split_akhir": b2})

    # per-wallet, BH lintas wallet DI DALAM satu horizon terpanjang yang diuji
    print(f"\nper wallet (n>={MIN_N} pada 7 hari):")
    by_w = collections.defaultdict(list)
    for x in entri:
        if x["jam"] == "7 hari":
            by_w[x["w"]].append(x["bps"])
    thick = [(w, v) for w, v in by_w.items() if len(v) >= MIN_N]
    pvals = []
    bmed = statistics.fmean(base_vals("7 hari")) if base_vals("7 hari") else 0.0
    for w, v in thick:
        wins = sum(1 for y in v if y > bmed)
        pvals.append(_sign_p(wins, len(v)))
    oki = bh(pvals)
    print(f"  {len(thick)} wallet mencapai n>={MIN_N}; lolos BH vs baseline: "
          f"{len(oki)}; rata-rata 7 hari = "
          f"{statistics.fmean([statistics.fmean(v) for _, v in thick]) if thick else 0:+.1f} bps")
    for i, (w, v) in enumerate(sorted(thick, key=lambda z: -statistics.fmean(z[1]))[:6]):
        print(f"    0x{w[:38]:38} n={len(v):>4} {statistics.fmean(v):>+8.1f} bps  "
              f"p={pvals[i]:.4f}{'  LOLOS BH' if i in oki else ''}")

    verdict = [r for r in out_rows if r["p_boot"] < 0.05 and r["diff_bps"] > 0
               and (r["split_awal"] or 0) > 0 and (r["split_akhir"] or 0) > 0]
    print(f"\nVERDIK: {len(verdict)} horizon lolos SEMUA syarat (p<0,05, selisih>0, dua periode "
          "searah)")
    for r in verdict:
        print(f"  -> {r['horizon']}: {r['diff_bps']:+.1f} bps di atas acak")
    if not verdict:
        print("  Tidak ada. Dan ini masih BATAS ATAS yang ramah ke panel: Uji A (prospektif) "
              "belum tersentuh.")
    os.makedirs(os.path.join(ROOT, "decisions"), exist_ok=True)
    p = os.path.join(ROOT, "decisions", f"whale-sweep-{a.days}d.json")
    json.dump({"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "prereg": "vault/06-Results/06 - Pre-registration Horizon.md",
               "horizons": HORIZONS, "cost_bps_applied": 0.0,
               "note_ongkos": "belum memasukkan ongkos - itu harus diukur per venue dulu",
               "rows": out_rows, "wallets_n": len(thick)},
              open(p, "w", encoding="utf-8"), indent=1, sort_keys=True)
    print(f"tertulis: {os.path.relpath(p, ROOT)}")


def _sign_p(wins, n):
    if n == 0 or wins * 2 <= n:
        return 1.0
    lg2 = math.log(2.0)
    logs = [math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1) - n * lg2
            for k in range(wins, n + 1)]
    mx = max(logs)
    return min(1.0, math.exp(mx) * sum(math.exp(x - mx) for x in logs))


if __name__ == "__main__":
    main()
