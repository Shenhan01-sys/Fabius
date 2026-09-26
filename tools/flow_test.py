"""Uji H1/H2/H3 yang TERKUNCI di `vault/10-Pra-Registrasi-Uji-Aliran.md` - bukan varian darinya.

Alat ini sengaja sempit. Ia membaca cache aliran Dune, menghitung hasil forward dari kline Aster
kami sendiri, lalu melaporkan tiga angka sesuai hipotesis yang sudah tertulis sebelum hasil pertama
dilihat. Tidak ada tempat untuk menambah fitur keempat: kalau halaman ini bisa diedit sampai
menghasilkan sesuatu, ia berhenti menjadi uji dan mulai menjadi pembenaran.

Peta ke hipotesis:
  H1  net_usd  = (usd_beli - usd_jual)          -> korelasi/quantile vs forward return
  H2  r_wallets= (pembeli - penjual)/(pembeli + penjual)
  H3  kuil tertinggi net_usd -> hasilnya negatif (kerumunan panik = pucuk)

Semua aturan keputusan ada di vault/10: horizon 4 bar, ongkos 20 bps RT, 1 sampel per (token,jam),
n>=20 per token, BH alpha=0,10 lintas token, drop-best-fold 5 segmen, laporan hanya kuintil ekstrem.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import bars  # noqa: E402

RT_COST_BPS = 20.0
HORIZON = 4
MIN_N = 20
BH_ALPHA = 0.10
FOLDS = 5


def norm_hex(a):
    """Satu bentuk untuk semua heks: kecil, tanpa `0x`, panjang 40.

    Ini penyebab kegagalan yang terukur 26 Sep: `to_hex()` Trino membalas heks HURUF BESAR,
    sementara peta alamat kami simpan huruf kecil. Join lintas dua bentuk itu menjatuhkan
    85 dari 86 token dan hasilnya (n=292, satu token) tetap terlihat seperti uji yang sah.
    Semua sisi join kini lewat fungsi ini, dan jumlah yang cocok DICETAK - alat yang gagal
    secara sunyi lebih berbahaya dari alat yang gagal keras.
    """
    a = str(a or "").strip().lower()
    if a.startswith("0x"):
        a = a[2:]
    return a


def load_flow():
    fp = sorted(glob.glob(os.path.join(ROOT, "data", "flow", "flow-*.jsonl")),
                key=lambda p: -int(os.path.basename(p).split("-")[1].split("d")[0]))
    if not fp:
        raise SystemExit("data/flow kosong - jalankan tools/dune_flow.py --window 14 dulu")
    use = fp[0]
    rows = [json.loads(l) for l in open(use, encoding="utf-8") if l.strip()]
    for r in rows:
        r["token"] = norm_hex(r.get("token"))
    return os.path.relpath(use, ROOT), rows


def load_map():
    """addr -> simbol. Baca KAMUS yang ditulis perekam (`addr-<hari>d.json`), bukan `map-perp.json`.

    Kesalahanku di percobaan pertama: `map-perp.json` itu daftar baris mentah hasil kueri, sementara
    kamus simbol->alamat ada di berkas lain. Alat yang mengira bentuk berkas dari namanya akan
    `AttributeError: 'list' object has no attribute 'items'` - berisik, jadi setidaknya jujur. Yang
    penting: kedua bentuk diterima, supaya alat ini tidak mati kalau suatu hari kita cuma punya salah
    satunya, dan yang dipilih selalu kamus bila ada (karena kamus sudah melewati aturan "teraktif").
    """
    d = os.path.join(ROOT, "data", "flow")
    for p in sorted(glob.glob(os.path.join(d, "addr-*.json")), key=os.path.getmtime, reverse=True):
        try:
            j = json.load(open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(j, dict) and j:
            return {norm_hex(v): str(k) for k, v in j.items() if norm_hex(v)}
    p = os.path.join(d, "map-perp.json")
    if os.path.exists(p):
        out = {}
        try:
            for r in json.load(open(p, encoding="utf-8")):        # terurut trades DESC
                a, s = norm_hex(r.get("addr")), str(r.get("symbol") or "")
                if len(a) == 40 and s and a not in out:
                    out[a] = s.upper()
            return out
        except (OSError, ValueError):
            pass
    raise SystemExit("tidak ada peta alamat di data/flow - jalankan tools/dune_flow.py dulu")


def prep_symbol_rows(map_sym_addr, want):
    """Simbol -> kontrak perp Aster, lalu pastikan kline-nya ada di cache."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("direction", os.path.join(HERE, "direction.py"))
    D = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(D)
    ps = D.perp_symbols()
    by_base = {}
    for s in ps:
        by_base.setdefault(str(s.get("base") or "").upper(), []).append(s["symbol"])
    out = {}
    for addr in want:
        sym = map_sym_addr.get(addr)
        if not sym:
            continue
        cand = by_base.get(sym)
        if cand:
            out[addr] = cand[0]
    return out


def fwd(perp_cache, perp, t_ms):
    bs = perp_cache.get(perp)
    if not bs:
        return None
    idx = np.searchsorted(bs["t"], t_ms, side="left")
    if idx >= len(bs["t"]) or idx + HORIZON >= len(bs["t"]):
        return None
    p0, p1 = bs["c"][idx], bs["c"][idx + HORIZON]
    if not p0:
        return None
    return (p1 / p0 - 1.0) * 1e4


def sign_p(wins, n):
    import math
    if n == 0 or wins * 2 <= n:
        return 1.0
    lg2 = math.log(2.0)
    logs = [math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1) - n * lg2
            for k in range(wins, n + 1)]
    mx = max(logs)
    return min(1.0, math.exp(mx) * sum(math.exp(x - mx) for x in logs))


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


def folds_mean(vals):
    if len(vals) < FOLDS:
        return []
    parts = np.array_split(np.arange(len(vals)), FOLDS)
    return [float(np.mean([vals[i] for i in p])) for p in parts if len(p)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-q", type=float, default=0.2, help="kuintil ekstrem yang dilaporkan")
    a = ap.parse_args()

    src, rows = load_flow()
    addr_of = load_map()                       # token(hex) -> simbol
    print(f"sumber: {src} | {len(rows)} titik (token,jam)")
    want = {r["token"] for r in rows}
    perp_of = prep_symbol_rows(addr_of, want)
    print(f"terpetakan ke kontrak perp: {len(perp_of)} dari {len(want)} token")
    # Pagarnya, bukan cuma laporannya: percobaan pertama menghasilkan "1 dari 86" dan tetap
    # mencetak tabel H1/H2/H3 yang lengkap - tabel itu terbaca sah, padahal isinya satu token.
    if len(perp_of) < max(10, len(want) // 4):
        raise SystemExit(
            f"CAKUPAN RUNUH: hanya {len(perp_of)}/{len(want)} token terpetakan ke kontrak perp.\n"
            f"  Ini biasanya bentuk heks yang tidak sama antar berkas (to_hex Trino = kapital) atau\n"
            f"  simbol yang tidak sama dengan baseAsset Aster. Jangan baca satu angka pun dari run ini:\n"
            f"  uji yang dirancang untuk 86 token tidak bisa dilaporkan atas 1 token.\n"
            f"  contoh token: {sorted(want)[:3]} | contoh kunci peta: {sorted(addr_of)[:3]}")

    # kumpulkan kline sekali per kontrak
    need = sorted(set(perp_of.values()))
    perp_cache = {}
    for i, p in enumerate(need, 1):
        d = bars.load(p, "1h")
        if not d or not d.get("bars"):
            got, meta = bars.fetch(p, "1h", 25, verbose=False)
            if got:
                bars.save(p, "1h", got, meta)
                d = {"bars": got}
        bs = (d or {}).get("bars") or []
        if bs:
            perp_cache[p] = {"t": np.array([x["t"] for x in bs]),
                             "c": np.array([x["c"] for x in bs], dtype=float)}
        if i % 15 == 0:
            print(f"  kline {i}/{len(need)}", flush=True)
    print(f"kline siap untuk {len(perp_cache)} kontrak")

    # satu titik per (token, jam); forward 4 jam
    pts = []
    for r in rows:
        tok = str(r.get("token") or "").lower()
        perp = perp_of.get(tok)
        if not perp or perp not in perp_cache:
            continue
        jam = r.get("jam")
        try:
            tt = time.strptime(jam[:19], "%Y-%m-%d %H:%M:%S")
        except (TypeError, ValueError):
            continue
        import calendar
        t_ms = calendar.timegm(tt) * 1000 + 3_600_000      # masuk di close bar BERIKUTNYA
        f = fwd(perp_cache, perp, t_ms)
        if f is None:
            continue
        pb, pj = float(r.get("pembeli") or 0), float(r.get("penjual") or 0)
        ub, uj = float(r.get("usd_beli") or 0), float(r.get("usd_jual") or 0)
        pts.append({"token": tok, "sym": addr_of.get(tok), "jam": jam[:16],
                    "net_usd": ub - uj, "r_wallets": (pb - pj) / (pb + pj) if (pb + pj) else 0.0,
                    "gross": f, "net": f - RT_COST_BPS if f > -1e4 else None})
    pts = [p for p in pts if p["net"] is not None]
    print(f"\ntitik uji (token,jam) dengan hasil forward: {len(pts)}")
    if len(pts) < 200:
        raise SystemExit("sampel terlalu kecil untuk uji tiga hipotesis - perlebar jendela, jangan dipaksakan")

    def qtest(name, key, want_sign):
        """Kuintil ekstrem dari `key` vs hasil forward, per token -> BH lintas token."""
        by_tok = {}
        for p in pts:
            by_tok.setdefault(p["token"], []).append(p)
        line = []
        per_tok = []
        for tok, v in by_tok.items():
            v = sorted(v, key=lambda z: z[key])
            n = len(v)
            if n < MIN_N:
                continue
            k = max(3, int(n * a.top_q))
            for j, x in enumerate(v):
                x["_q"] = "hi" if j >= n - k else ("lo" if j < k else "mid")
            hi = [x["net"] for x in v[-k:]]
            lo = [x["net"] for x in v[:k]]
            diff = statistics.fmean(hi) - statistics.fmean(lo)
            wins = sum(1 for x in (hi if want_sign > 0 else lo) if x > 0)
            per_tok.append((tok, v[0]["sym"], n, diff, statistics.fmean(hi), statistics.fmean(lo),
                            wins, 2 * k))
        pvals = [sign_p(t[6], t[7]) for t in per_tok]
        oks = bh(pvals)
        pos = [t for t in per_tok if t[3] > 0]
        print(f"\n=== {name}  ({len(per_tok)} token lolos n>={MIN_N}) ===")
        if not per_tok:
            print("  tidak ada token dengan sampel cukup")
            return
        print(f"  {'simbol':12}{'n':>6}{'hi-net':>9}{'lo-net':>9}{'HI-LO':>9}{'WR ekstrem':>12}  BH")
        for i, (tok, sym, n, diff, hi, lo, w, nn) in enumerate(
                sorted(per_tok, key=lambda z: -z[3])):
            print(f"  {str(sym)[:12]:12}{n:>6}{hi:>+9.1f}{lo:>+9.1f}{diff:>+9.1f}"
                  f"{w / nn * 100:>11.0f}%  {'LOLOS' if i in oks else ''}")
        lo_best = [t for t in per_tok if t[6] / t[7] > 0.5]
        print(f"  ringkasan: {len([t for t in per_tok if t[3] > 0])} token HI>LO; "
              f"{len([t for t in per_tok if t[3] < 0])} token HI<LO; "
              f"lolos BH = {len(oks)}; arah yang diminta {'HI>LO' if want_sign > 0 else 'HI<LO'}")
        # drop-best-fold di atas 5 SEGMEN WAKTU, seperti yang dikunci vault/10.
        # Percobaan pertama malah membagi nilai selisih (urut besaran) lalu menyebutnya "5 segmen"
        # - itu statistik lain dengan nama yang sama, dan persis jenis penyimpangan yang membuat
        # pra-registrasi tidak ada gunanya. Jadi fold dihitung per token atas titik-titiknya yang
        # sudah terurut jam, lalu dirata-ratakan lintas token.
        # Selisih hi-lo per segmen waktu. Versi pertama menghitung rata-rata net seluruh token per
        # segmen - tidak menyentuh `_q` sama sekali, jadi H1/H2/H3 mencetak angka fold yang IDENTIK.
        # Itu bug yang tidak akan kelihatan kalau aku tidak membandingkan ketiga barisnya berdampingan.
        fold_by_token = {}
        for tok, v in by_tok.items():
            if len(v) < MIN_N or any("_q" not in x for x in v):
                continue
            vv = sorted(v, key=lambda z: z["jam"])
            parts = np.array_split(np.arange(len(vv)), FOLDS)
            row = []
            for p in parts:
                h = [vv[i]["net"] for i in p if vv[i]["_q"] == "hi"]
                l = [vv[i]["net"] for i in p if vv[i]["_q"] == "lo"]
                row.append(statistics.fmean(h) - statistics.fmean(l) if (h and l) else None)
            fold_by_token[tok] = row
        fm = []
        for fi in range(FOLDS):
            col = [f[fi] for f in fold_by_token.values() if f[fi] is not None]
            fm.append(float(np.mean(col)) if col else None)
        present = [x for x in fm if x is not None]
        if len(present) > 1:
            drop = [x for i, x in enumerate(present) if i != int(np.argmax(present))]
            print(f"  5 segmen waktu: {['%+.1f' % x for x in fm]} | "
                  f"tanpa segmen terbaik {statistics.fmean(drop):+.1f} bps")

    qtest("H1 - dolar kerumunan (net_usd)", "net_usd", +1)
    qtest("H2 - jumlah kepala (r_wallets)", "r_wallets", +1)
    qtest("H3 - kuil tertinggi net_usd (harusnya NEGATIF)", "net_usd", -1)

    print("\nBatas: entri datang dari Dune yang bisa di-update retro -> ini statistik, bukan bukti")
    print("point-in-time (saksi waktu tetap wallet-flow.jsonl + anchor chain 97). Kerumunan juga")
    print("tidak bisa short token spot, jadi H1/H2 diam-diam sisi long. Dan kalau ada yang lolos,")
    print("kalimat yang diizinkan vault/10 §4 adalah 'lolos pada 14 hari x 86 token x ongkos 20 bps',")
    print("bukan 'ada edge' - itu butuh jendela baru setelah 30 Sep.")


if __name__ == "__main__":
    main()
