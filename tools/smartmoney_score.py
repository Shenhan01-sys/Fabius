"""Apakah smart money mengalahkan orang lain - diuji di MASA LALU, bukan ditunggu di masa depan.

Pertanyaan yang dijawab alat ini bukan "apakah whale untung", tapi satu pertanyaan yang bisa
dibantah: **"kalau kami menyalin arah dompet yang dilabeli pintar oleh GMGN, apakah hasilnya
lebih baik daripada menyalin arah DOMPET-DOMPET BIASA pada token dan jam yang sama - setelah
ongkos 20 bps round-trip?"** Kalau jawabannya tidak, maka ⑦ mati dengan cara yang sama matinya
aturan harga di `vault/09`: diukur, bukan diramalkan.

Kenapa sekarang bisa, padahal kemarin tidak:
  - GMGN `user/smartmoney` cuma menutup 8-13 MENIT dan semua parameter pagingnya diabaikan
    (terukur 25 Sep) -> riwayatnya tidak bisa ditarik, jadi dulu satu-satunya jalan adalah
    menunggu accumulation.
  - Dune `dex.trades` (`blockchain='bnb'`) punya riwayat 10 hari ke belakang dan POPULASI seluruh
    wallet (terukur 26 Sep: 205.875 swap / 20.607 wallet dalam satu jam penuh) -> entri masa lalu
    DAN kelompok kontrol tersedia sekaligus.
  - Aster `fapi/v1/klines` punya 400 hari bar 1 jam tanpa API key -> harga forward untuk
    menghitung hasilnya, tanpa bergantung pada Dune (yang barisnya bisa di-*update* retro:
    ada field `_updated_at`).

PEMBAGIAN TUGAS YANG SENGAJA, dan ini bagian penting dari metodenya:
  Dune  = dari mana ENTRY datang (sejarah, populasi, tanpa nilai bukti waktu)
  Aster = dari mana HASIL datang (deret harga yang kami ambil sendiri)
  GMGN  = siapa yang dilabeli pintar (panel) - dan karena itu bias yang harus disebut
  Kami  = perekam live `universe/wallet-flow.jsonl` - SATU-SATUNYA yang bisa dipakai untuk
          klaim "kami tahu sebelum hasilnya ada". Alat ini TIDAK menghasilkan klaim itu.

Dua pagar statistik yang dipasang supaya hasilnya tidak enak-diBaca-saja:
  1. SATU sampel per (wallet, token, jendela 4 jam). Satu dompet panas yang mengirim 20 order
     pada token yang sama dalam 3 menit bukan 20 pertaruhan bebas - tanpa pagar ini `p` palsu
     kecil dan itulah persis penyakit yang `vault/09` tangkap lewat drop-best-fold.
  2. Benjamini-Hochberg lintas wallet (α=0,10) + ambang n>=20, dan angka dilaporkan TERPISAH
     untuk panel vs kontrol. Selisih rata-rata yang tidak lolos BH hanyalah cerita, bukan hasil.

Pakai:  python tools/smartmoney_score.py --days 7 --min-usd 200
         python tools/smartmoney_score.py --tokens 12 --report-only      # tanpa kueri Dune baru
"""
from __future__ import annotations

import argparse
import calendar
import collections
import hashlib
import json
import math
import os
import random
import statistics
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import bars  # noqa: E402  (tools/bars.py - Aster 1h, cache + sha256)

DUNE = "https://api.dune.com"
RT_COST_BPS = 20.0        # vault/08 §3 (5,5 + 4,5 per sisi) - sama dengan backtest & live
HORIZON_BARS = 4          # 4 jam = horizon keputusan kita
MIN_TRADES = 20           # vault/02: jangan simpulkan apa pun dari < 20 sampel independen
BH_ALPHA = 0.10
FLOW = os.path.join(ROOT, "universe", "wallet-flow.jsonl")
CACHE = os.path.join(ROOT, "data", "smartmoney")


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


def sql_run(key, sql, wait=420):
    """POST -> poll -> rows. Jalur bacanya `result.rows` (terukur: `results.rows` tidak ada)."""
    h = {"X-Dune-Api-Key": key, "Content-Type": "application/json", "Accept": "application/json",
         "User-Agent": "Mozilla/5.0 (compatible; fabius-smartmoney/1.0)"}
    body = json.dumps({"sql": sql, "performance": "medium"}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(DUNE + "/api/v1/sql/execute",
                                                           data=body, headers=h), timeout=60) as r:
            j = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return None, f"POST {e.code}: {e.read().decode('utf-8','replace')[:180]}"
    except Exception as e:  # noqa: BLE001
        return None, f"POST gagal {type(e).__name__}: {str(e)[:140]}"
    eid = j.get("execution_id")
    if not eid:
        return None, f"tanpa execution_id: {json.dumps(j)[:180]}"
    t0 = time.time()
    while time.time() - t0 < wait:
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    DUNE + f"/api/v1/execution/{eid}/status", headers=h), timeout=30) as r:
                st = json.loads(r.read().decode())
        except Exception:  # noqa: BLE001
            time.sleep(4)
            continue
        state = str(st.get("state", ""))
        if state and "EXECUTING" not in state and "PENDING" not in state and "STARTING" not in state:
            break
        time.sleep(3)
    if "COMPLETED" not in state:
        return None, f"{state}: {str((st or {}).get('error', {}).get('message'))[:200]}"
    # Halaman hasil DIULANG sampai 3x. Ini bukan kosmetik: pada percobaan pertama satu halaman
    # kena TimeoutError dan kuerinya tetap "sukses" membawa 44.000 baris. Karena ORDER BY-nya
    # block_time ASC, halaman yang hilang adalah yang PALING BARU - yaitu tepat bagian tempat
    # anggota panel kita berada (mereka baru saja muncul di arus live). Jadi kegagalan network
    # itu bukan sekadar "sampel sedikit kurang": dia membiaskan ke bawah selisih panel vs kontrol.
    out, cur, complete = [], None, True
    while True:
        u = DUNE + f"/api/v1/execution/{eid}/results?limit=2000" + (f"&offset={cur}" if cur else "")
        res = None
        for t in range(3):
            try:
                with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=150) as r:
                    res = json.loads(r.read().decode())
                break
            except Exception as e:  # noqa: BLE001
                last_err = f"{type(e).__name__}: {str(e)[:110]}"
                time.sleep(3 + 3 * t)
        if res is None:
            complete = False
            print(f"  HALAMAN GAGAL 3x ({last_err}) -> hasil TIDAK lengkap; angka di bawah harus "
                  f"dibaca terpotong di offset {cur}")
            break
        rows = ((res.get("result") or {}).get("rows") or [])
        out.extend(rows)
        meta = ((res.get("result") or {}).get("metadata") or {})
        nxt = meta.get("next_offset") or res.get("next_offset")
        if not nxt or nxt == cur or not rows:
            break
        cur = nxt
    return out, (f"{state} rows={len(out)} {time.time()-t0:.0f}s"
                 + ("" if complete else " [TERPOTONG]"))


def panel_makers():
    """Alamat yang tercatat di rekaman LIVE kita = 'panel' versi GMGN."""
    c = collections.Counter()
    if not os.path.exists(FLOW):
        return set(), c
    for ln in open(FLOW, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            d = json.loads(ln)
        except Exception:  # noqa: BLE001
            continue
        if d.get("k") == "tx" and d.get("m"):
            # disimpan TANPA prefiks 0x: kunci panel harus satu bentuk dengan `to_hex()` dari Dune,
            # kalau tidak keanggotaan panel jadi selalu False dan "kontrol" mencaplok semuanya -
            # kegagalan yang tidak terlihat kecuali memang dicari.
            c[d["m"].lower().removeprefix("0x")] += 1
    return set(c), c


def perp_tokens(limit=None):
    """Token yang punya dua hal sekaligus: alamat kontrak BSC (universe) DAN kontrak perp (Aster).

    Ini pembatas yang jujur, bukan kemudahan: kami hanya bisa MENILAI arah pada aset yang bisa
    kami hargai sendiri lewat Aster. Token yang tidak punya perp tidak ikut diuji, dan itu
    harus tertulis di laporan - bukan diam-diam hilang dari sampel.
    """
    sys.path.insert(0, HERE)
    import importlib.util
    spec = importlib.util.spec_from_file_location("direction", os.path.join(HERE, "direction.py"))
    D = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(D)
    ps = D.perp_symbols()
    by_base = {}
    for s in ps:
        by_base.setdefault(str(s.get("base") or "").upper(), []).append(s["symbol"])
    snap = D.universe_snapshot()
    out = []
    for r in snap["rows"]:
        sym = str(r.get("symbol") or "").strip().upper()
        addr = str(r.get("address") or "").lower()
        if sym in by_base and len(addr) == 42:
            out.append({"symbol": sym, "perp": by_base[sym][0], "address": addr})
    seen, uniq = set(), []
    for x in out:
        if x["address"] in seen:
            continue
        seen.add(x["address"])
        uniq.append(x)
    return uniq[:limit] if limit else uniq


def fwd_bps(psym, t_ms, side="long"):
    """Return `HORIZON_BARS` bar 1 jam sesudah t_ms, dari cache Aster kami sendiri."""
    d = bars.load(psym, "1h")
    if not d or not d.get("bars"):
        return None, "tidak ter-cache"
    bs = d["bars"]
    i = None
    for k in range(len(bs)):
        if bs[k]["t"] >= t_ms:
            i = k
            break
    if i is None or i + HORIZON_BARS >= len(bs):
        return None, "di luar jendela data"
    p0, p1 = bs[i]["c"], bs[i + HORIZON_BARS]["c"]
    if not p0:
        return None, "harga nol"
    return ((p1 / p0 - 1.0) if side == "long" else (p0 / p1 - 1.0)) * 1e4, None


def sign_test_p(wins, n):
    if n == 0 or wins * 2 <= n:
        return 1.0
    lg2 = math.log(2.0)
    logs = [math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1) - n * lg2
            for k in range(wins, n + 1)]
    mx = max(logs)
    return min(1.0, math.exp(mx) * sum(math.exp(x - mx) for x in logs))


def bh(pairs, alpha=BH_ALPHA):
    m = len(pairs)
    if not m:
        return set()
    order = sorted(range(m), key=lambda i: pairs[i][1])
    kmax = -1
    for r, i in enumerate(order):
        if pairs[i][1] <= alpha * (r + 1) / m:
            kmax = r
    return set(order[:kmax + 1]) if kmax >= 0 else set()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--min-usd", type=float, default=200.0)
    ap.add_argument("--tokens", type=int, default=25, help="batas token perp yang diuji")
    ap.add_argument("--max-rows", type=int, default=40000)
    ap.add_argument("--report-only", action="store_true")
    a = ap.parse_args()

    panel, counts = panel_makers()
    toks = perp_tokens(a.tokens)
    print(f"panel dari rekaman live : {len(panel)} maker ({sum(counts.values())} tx) "
          f"| token uji (punya alamat + kontrak perp): {len(toks)}")
    if not toks:
        raise SystemExit("tidak ada token yang punya alamat DAN kontrak perp - berhenti, jangan uji udara")

    os.makedirs(CACHE, exist_ok=True)
    # REV ada di NAMA berkas. Berkas `entries-10d-500.json` yang lama dihasilkan kueri TANPA
    # `ORDER BY` (potongan LIMIT-nya tidak terdefinisi urutan), jadi memakainya lagi setelah
    # kuerinya diperbaiki akan membuat laporan terlihat seperti hasil kueri baru padahal bukan.
    # Menandai revisi di nama file lebih murah daripada penjelasan di belakang hari.
    # r3 = r2 + halaman yang diulang. Berkas r2 dibuang bukan karena salah kueri, tapi karena
    # SATU HALAMAN-nya hilang akibat timeout -> ia tidak lengkap dengan cara yang membiaskan
    # hasil (yang hilang = paling baru). Menyimpan hasil parsial dengan nama yang sama = cara
    # klasik membuat laporan lama terlihat seperti laporan baru.
    fp = os.path.join(CACHE, f"entries-r3-{a.days}d-{int(a.min_usd)}.json")
    net_trunc = False
    if a.report_only or os.path.exists(fp):
        if not os.path.exists(fp):
            raise SystemExit("--report-only tapi belum ada berkas entri")
        rows = json.load(open(fp, encoding="utf-8"))
        print(f"entri dibaca dari berkas: {len(rows)}")
    else:
        key = dune_key()
        if not key:
            raise SystemExit("tidak ada DUNE_API_KEY (env / .dune.env / ~/.config/dune/.env)")
        addr_list = ", ".join(f"from_hex('{t['address']}')" for t in toks)
        sql = ("SELECT to_hex(token_bought_address) AS token, to_hex(taker) AS wallet, "
               "cast(block_time as varchar) AS t, amount_usd "
               "FROM dex.trades WHERE blockchain = 'bnb' "
               f"AND token_bought_address IN ({addr_list}) "
               f"AND block_time > now() - INTERVAL '{a.days}' DAY "
               f"AND amount_usd > {a.min_usd} "
           # ORDER BY dibuat EKSPLISIT. Tanpa ini `LIMIT` memotong dalam urutan yang tidak
           # diketahui siapa pun - percobaan pertama persis kena: rows=40.000 = batas LIMIT, jadi
           # sampelnya terpotong dan kita tidak tahu bagian mana yang hilang. Dengan urut waktu,
           # pemotongan berarti "yang paling baru dibuang" - masih sebuah batas, tapi JELAS.
           f"ORDER BY block_time ASC LIMIT {a.max_rows}")
        print(f"mengirim 1 kueri Dune ({len(toks)} token, {a.days} hari, > ${a.min_usd:.0f})...")
        rows, note = sql_run(key, sql)
        net_trunc = "[TERPOTONG]" in str(note)
        print(f"  {note if rows is not None else 'GAGAL: ' + str(note)}")
        if not rows:
            raise SystemExit("Dune tidak mengembalikan baris - berhenti, jangan laporkan nol sebagai hasil")
        json.dump(rows, open(fp, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"  tersimpan: {os.path.relpath(fp, ROOT)}")

    # `to_hex()` di Trino mengembalikan hex TANPA prefiks `0x`, sementara alamat di universe kita
    #berprefiks `0x`. Kalau dibandingkan apa adanya, JOIN-nya diam-diam menghasilkan NOL baris -
    # persis yang terjadi pada percobaan pertama (Dune mengirim 8.636 baris, laporan bilang
    # "0 sampel"). Karena itu kuncinya dinormalisasi dua-duanya, dan jumlah baris yang GAGAL
    # dipetakan ikut dicetak: join yang sunyi harus berisik.
    def norm(x):
        x = str(x or "").lower().strip()
        return x[2:] if x.startswith("0x") else x

    by_addr = {norm(t["address"]): t for t in toks}
    # 1 sampel per (wallet, token, jendela 4 jam) - order berulang pada menit yang sama dihitung sekali
    per_window, seen = [], set()
    unmapped = collections.Counter()
    for r in rows:
        addr = norm(r.get("token"))
        w = norm(r.get("wallet"))
        ts = str(r.get("t") or "")
        t = by_addr.get(addr)
        if not t:
            unmapped[addr[:10] or "(kosong)"] += 1
            continue
        if not w:
            continue
        try:
            tt = time.strptime(ts[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        # `calendar.timegm`, BUKAN `time.mktime`: string Dune itu UTC. `mktime` membacanya sebagai
        # waktu LOkal - di laptop WIB ini semuanya bergeser 7 jam (dan di runner Actions yang
        # TZ=UTC tidak bergeser sama sekali). Alat yang hasilnya berubah tergantung mesin tempat
        # ia dijalankan bukan alat; itu bom waktu.
        ms = int(calendar.timegm(tt) * 1000)
        bucket = ms // (HORIZON_BARS * 3_600_000)
        k = (w, addr, bucket)
        if k in seen:
            continue
        seen.add(k)
        per_window.append((w, t, ms))

    # perluas cache kline sekali per token (bukan per entri) -> hemat & bisa diulang
    need = sorted({t["perp"] for _w, t, ms in per_window})
    print(f"memperluas kline untuk {len(need)} kontrak perp sampai {a.days + 2} hari...")
    for p in need:
        d = bars.load(p, "1h")
        have = (d or {}).get("bars") or []
        if not have or have[-1]["t"] < (time.time() - 2 * 86400) * 1000:
            got, meta = bars.fetch(p, "1h", max(30, a.days + 3), verbose=False)
            if got:
                bars.save(p, "1h", got, meta)

    agg = collections.defaultdict(lambda: {"n": 0, "wins": 0, "bps": []})
    cohort = collections.defaultdict(lambda: {"n": 0, "wins": 0, "bps": []})
    skipped = 0
    # "dilewati" harus punya alasan, bukan angka bulat misterius. Pada percobaan pertama 1.736 dari
    # 2.085 entri tidak dinilai, dan tanpa rincian itu angkanya terbaca seperti bug yang disembunyikan
    # atau data yang dibuang seenaknya - padahal penyebabnya beda-beda (belum 4 bar vs tidak ada cache).
    skip_why = collections.Counter()
    priced_keys, priced_nets = [], []
    for w, t, ms in per_window:
        bps, why = fwd_bps(t["perp"], ms, "long")     # BUY => arah long
        if bps is None:
            skipped += 1
            skip_why[why] += 1
            continue
        net = bps - RT_COST_BPS
        priced_keys.append((w, t, ms))
        priced_nets.append(net)
        grp = "panel" if w in panel else "kontrol"
        for d in (agg[w], cohort[grp]):
            d["n"] += 1
            d["wins"] += 1 if net > 0 else 0
            d["bps"].append(net)

    if unmapped:
        # join yang sunyi harus berisik: ini tempat kegagalan format (prefiks, kapital, kolom salah)
        # bersembunyi selama berjam-jam sambil laporan tetap "sukses".
        print(f"PERINGATAN: {sum(unmapped.values())} baris Dune tidak terpetakan ke token uji "
              f"(contoh alamat: {list(unmapped)[:5]}); token uji = {sorted({t['address'][:10] for t in toks})[:5]}")
    print(f"\nentri Dune: {len(rows)} | sampel non-overlap: {len(per_window)} | "
          f"dinilai {len(per_window) - skipped} | dilewati {skipped}"
          + (f"  [{' | '.join(f'{k}={v}' for k, v in skip_why.most_common())}]" if skip_why else ""))
    in_panel = sum(1 for w, _t, _m in per_window if w in panel)
    print(f"entri yang pelakunya ada di panel live kita: {in_panel} "
          f"(sisanya=kelompok kontrol; dua-duanya dari tabel yang sama, bedanya cuma label GMGN)")
    if len(rows) >= a.max_rows or net_trunc:
        print(f"PERINGATAN TRUNCATION ({'LIMIT ' + str(a.max_rows) if len(rows) >= a.max_rows else ''}"
              f"{' + halaman hilang' if net_trunc else ''}): sampel "
              f"TIDAK lengkap (kueri diurut block_time ASC, jadi yang hilang adalah jam-jam "
              f"TERBARU). Angka di bawah boleh dibaca sebagai statistik dari bagian AWAL jendela, "
              f"bukan dari seluruh jendela. Perkecil --tokens atau perbesar --max-rows untuk menutupnya.")
    print()

    print(f"{'kelompok':10}{'n':>8}{'wallet':>8}{'WR':>7}{'net rata2':>12}{'median':>9}  "
          f"{'p (kohort vs 0)':>16}")
    print("-" * 78)
    for grp in ("panel", "kontrol"):
        d = cohort[grp]
        # jumlah wallet dihitung dari GRUP yang sama - versi pertama menaruh `len(agg)` (semua
        # wallet, panel DAN kontrol) di baris "panel", jadi kolomnya membesar tanpa sengaja
        n_wallet = len([w for w in agg if (w in panel) == (grp == "panel")])
        if not d["n"]:
            print(f"{grp:10}{'0':>8}{'-':>8}{'-':>7}{'-':>12}{'-':>9}  (tidak ada sampel)")
            continue
        mean = statistics.fmean(d["bps"])
        med = statistics.median(d["bps"])
        p = sign_test_p(d["wins"], d["n"])
        print(f"{grp:10}{d['n']:>8}{n_wallet:>8}{d['wins']/d['n']*100:>6.1f}%"
              f"{mean:>+12.1f}{med:>+9.1f}  {p:>16.6f}")

    # ---------- uji yang benar: BERPASANGAN per (token, jendela 4 jam) ----------
    # Peringatan metodologis yang harus dibaca orang: membandingkan cohort vs NOL itu salah di
    # sini, karena baseline seorang pembeli bukan nol - baseline-nya adalah "apa yang terjadi pada
    # semua pembeli token itu di jam itu". Pada percobaan pertama kontrol membalas +304 bps net
    # BUKAN karena dompet acak jago, tapi karena 9 token uji memang sedang naik. Jadi drift token
    # dibuang dengan membandingkan panel vs kontrol PADA TOKEN DAN JENDELA YANG SAMA, lalu sign-
    # flip permutation test (bukan p vs nol). Deterministik: seed 0, 20.000 permutasi.
    win = collections.defaultdict(lambda: {"panel": [], "kontrol": []})
    for (w, t, ms), net in zip(priced_keys, priced_nets):
        bucket = ms // (HORIZON_BARS * 3_600_000)
        win[(t["symbol"], bucket)]["panel" if w in panel else "kontrol"].append(net)
    diffs = []
    for k, v in win.items():
        if v["panel"] and v["kontrol"]:
            diffs.append(statistics.fmean(v["panel"]) - statistics.fmean(v["kontrol"]))
    print(f"jendela (token, 4 jam) dengan panel DAN kontrol terisi: {len(diffs)} "
          f" dari {len(win)} jendela total\n")
    perm_p = None
    observed_diff = None
    if diffs:
        observed_diff = statistics.fmean(diffs)
        rng = random.Random(0)
        n_flip = len(diffs)
        ge = 0
        for _ in range(20000):
            s = sum(d if rng.getrandbits(1) else -d for d in diffs) / n_flip
            if s >= observed_diff:
                ge += 1
        perm_p = (ge + 1) / 20001
        print(f"PANEL vs KONTROL, dipasangkan per token+jam:")
        print(f"  selisih net rata-rata : {observed_diff:+.1f} bps   (median {statistics.median(diffs):+.1f})")
        print(f"  jendela terpasang     : {n_flip}")
        print(f"  p (sign-flip, 20k)    : {perm_p:.4f}  -> "
              f"{'LOLOS ambang 0,05' if perm_p < 0.05 else 'TIDAK berbeda dari kerumunan'}")
        print("  Artinya: ini mengukur apakah panel MENGALAHKAN orang lain pada token & jam yang")
        print("  sama - bukan apakah panel 'untung'. Yang terakhir bisa benar karena token naik.\n")

    enough = [(w, d) for w, d in agg.items() if d["n"] >= MIN_TRADES]
    print(f"\nwallet dengan n>={MIN_TRADES}: {len(enough)} (panel={sum(1 for w,_ in enough if w in panel)})")
    if enough:
        pairs = [(w, sign_test_p(d["wins"], d["n"])) for w, d in enough]
        ok = bh(pairs)
        print(f"{'wallet':44}{'panel':>7}{'n':>5}{'WR':>7}{'net rata2':>11}  BH")
        print("-" * 82)
        rowsout = sorted(enough, key=lambda x: -statistics.fmean(x[1]["bps"]))[:12]
        for w, d in rowsout:
            p = sign_test_p(d["wins"], d["n"])
            i = [j for j, (ww, _) in enumerate(pairs) if ww == w][0]
            print(f"{w:44}{'YA' if w in panel else '-':>7}{d['n']:>5}"
                  f"{d['wins']/d['n']*100:>6.1f}%{statistics.fmean(d['bps']):>+11.1f}  "
                  f"{'LOLOS' if i in ok else 'tidak'} (p={p:.4f})")

    print("\nCara membaca yang sah: selisih 'net rata2' panel vs kontrol adalah SATU-SATUNYA angka")
    print("di halaman ini yang menjawab pertanyaan whales-vs-wong-cilik. Kedua-duanya tetap harus")
    print("lolos BH per wallet sebelum boleh disebut hasil. Batas yang tidak boleh dilupakan:")
    print("entri datang dari Dune yang barisnya bisa di-update retro (`_updated_at`) -> alat ini")
    print("menghasilkan STATISTIK, bukan bukti point-in-time; untuk yang terakhir itu tugas")
    print("`universe/wallet-flow.jsonl` + anchor di chain 97.")

    out = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "days": a.days, "min_usd": a.min_usd, "cost_bps_rt": RT_COST_BPS,
           "horizon_bars": HORIZON_BARS, "tokens_tested": [t["symbol"] for t in toks],
           "panel_size": len(panel), "samples": len(per_window) - skipped,
           "dune_rows": len(rows), "dune_truncated": len(rows) >= a.max_rows or net_trunc,
           "query_rev": "r2 (ORDER BY block_time ASC, halaman diulang 3x)",
           "paired_test": {"windows_paired": len(diffs),
                           "mean_diff_net_bps": (round(observed_diff, 2) if diffs else None),
                           "median_diff_net_bps": (round(statistics.median(diffs), 2) if diffs else None),
                           "p_sign_flip": perm_p, "permutations": 20000, "seed": 0},
           "skip_reasons": dict(skip_why),
           "cohort": {g: {"n": d["n"], "wr": (d["wins"] / d["n"] if d["n"] else None),
                          "mean_net_bps": (statistics.fmean(d["bps"]) if d["n"] else None),
                          "median_net_bps": (statistics.median(d["bps"]) if d["n"] else None)}
                      for g, d in cohort.items()},
           "wallets": {w: {"n": d["n"], "panel": w in panel,
                           "mean_net_bps": round(statistics.fmean(d["bps"]), 2)}
                       for w, d in enough}}
    op = os.path.join(ROOT, "decisions", f"smartmoney-{a.days}d-{int(a.min_usd)}.json")
    os.makedirs(os.path.dirname(op), exist_ok=True)
    with open(op, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    print(f"tertulis: {os.path.relpath(op, ROOT)}  sha={hashlib.sha256(json.dumps(out, sort_keys=True).encode()).hexdigest()[:12]}")


if __name__ == "__main__":
    main()
