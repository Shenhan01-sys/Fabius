"""Apakah aturan arah yang sama bisa menghasilkan uang SETELAH ongkos? Uji segmented + drop-best-fold.

Kenapa file ini ada: `tools/direction.py` sudah MEMPRODUKSI arah dan `tools/anchor.py` sudah
mengirimnya ke chain. Itu membuktikan keterikatan dan waktu, BUKAN kualitas. Satu-satunya cara
mengetahui yang kedua tanpa dana sungguhan adalah menjalankan aturan yang sama di atas deret harga
yang sama, bar per bar, seolah waktunya berjalan maju.

Yang diulang dari live, sengaja tidak "diperbaiki" demi hasil (semua angka diuji terhadap ini):
  - gerbang: |acf| >= ACF_EFFICIENT (di bawah itu = mendekati jalan acak -> flat)
  - arah:   sma_gap > +1% dan ret24 > 0 -> LONG ; sma_gap < -1% dan ret24 < 0 -> SHORT ; selain itu FLAT
  - horizon: HORIZON_BARS bar ke depan (= 4 jam, sama dengan horizon keputusan live)
  - ongkos:  20 bps round-trip = 5,5 bps taker + 4,5 bps spread/slippage PER SISI
             (asal: korpus HeliQuant `edge_lab.py:23,24,28` lewat vault/08 §3)

Yang TIDAK bisa diulang, dan itu membatasi kesimpulannya (dibuat eksplisit, bukan disembunyikan):
  1. **Funding historic tidak ada** di jalur ini -> gerbang "funding ekstrem" live tidak ikut diuji.
     Jadi yang diuji adalah aturan harga, bukan aturan lengkap agen live.
  2. **Ambang ini tidak di-fit.** Tidak ada satu parameter pun yang dipilih dengan melihat hasil di
     bawah, jadi ini BUKAN walk-forward dalam arti fitting-recalendar; ini tes bersegmen waktu
     + sensitivitas (drop-best-fold). Menyebutnya "walk-forward" akan menjual hasil yang tidak
     dibeli.
  3. **Beberapa simbol berbagi satu pergerakan pasar** (semua meme-perp naik-turun bersama BTC).
     Karena itu BH diterapkan SATU KALI PER TOKEN di level simbol, dan yang boleh diklaim hanyalah
     "satu simbol lolos", bukan "mayoritas lolos", kecuali kita membetulkan korelasi antar-simbol.

Keputusan dianggap layak-klaim hanya kalau: n >= MIN_TRADES, MEAN NET > 0 (bukan gross),
drop-best-fold masih > 0, dan p lolos BH. Kalau tidak: registry tetap kosong dan itu hasil,
bukan kegagalan (vault/08 §3).

Pakai:  python tools/backtest.py                      # semua simbol yang ter-cache cukup dalam
         python tools/backtest.py --fetch 400          # isi/perbaiki cache dulu (meta benar)
         python tools/backtest.py --symbols BNBUSDT TACUSDT --horizon 4
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import bars as barsmod  # noqa: E402

# ---- ambang: DIIMPOR dari direction.py supaya tidak ada dua kebenaran.
import direction as D  # noqa: E402

RT_COST_BPS = 20.0          # vault/08 §3 (5,5 + 4,5 per sisi)
MIN_TRADES = 20             # vault/02-Ambang.md: jangan simpulkan apa pun dari < 20 trade
FOLDS = 5
BH_ALPHA = 0.10
DEFAULT_SYMBOLS = ["BNBUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "HYPEUSDT",
                   "CAKEUSDT", "SUIUSDT", "WIFUSDT", "1000PEPEUSDT", "TACUSDT", "FLNCUSDT",
                   "MARSCOINUSDT"]


def series(sym):
    d = barsmod.load(sym, "1h")
    if not d or not d.get("bars"):
        return None
    return d


def acf_abs(x, lag):
    """|korelasi| antara x[:-lag] dan x[lag:] - versi vektor dari feats().acf() di direction.py."""
    if len(x) <= lag + 30:
        return None
    a, b = x[:-lag], x[lag:]
    if a.std() == 0 or b.std() == 0:
        return None
    return abs(float(np.corrcoef(a, b)[0, 1]))


def signals(closes, horizon, acf_gate=None, cost_bps=None, flip=False):
    """Datakan sinyal SATU PER SATU pada titik keputusan non-overlap (tiap `horizon` bar).

    Non-overlap itu penting, bukan estetika: kalau tiap bar boleh membuka trade dan semuanya
    tumpang tindih 4 jam, satu pergerakan pasar dihitung 4 kali dan n membengkak tanpa informasi
    (p-value jadi palsu kecil).
    """
    n = len(closes)
    lr = np.diff(np.log(closes))                     # return 1 bar
    out = []
    t = D.MIN_BARS_TINY
    while t + horizon <= n - 1:
        hist = closes[:t]
        hlr = lr[:t - 1]
        acfs = [a for a in (acf_abs(hlr, 1), acf_abs(hlr, 6), acf_abs(hlr, 24)) if a is not None]
        if not acfs:
            t += horizon
            continue
        a = sum(acfs) / len(acfs)
        sma = hist[-24:].mean()
        gap = (hist[-1] - sma) / sma if sma else 0.0
        r24 = hist[-1] / hist[-25] - 1.0 if len(hist) > 25 else 0.0
        mom = "long" if (gap > 0.01 and r24 > 0) else "short" if (gap < -0.01 and r24 < 0) else "flat"
        # `--flip` = aturan yang SAMA dibalik arahnya (jawaban untuk "kalau momentum kalah, jangan-
        # jangan mean-reversion yang menang"). Diuji di sini, bukan di narasi: satu-satunya alasan
        # layak untuk mengganti arah adalah kalau pembalikannya benar-benar berbayar setelah ongkos.
        if flip and mom != "flat":
            mom = "short" if mom == "long" else "long"
        gate_acf = D.ACF_EFFICIENT if acf_gate is None else acf_gate
        cost = RT_COST_BPS if cost_bps is None else cost_bps
        side = mom
        if a < gate_acf:
            side, gate = "flat", "efficient"
        else:
            gate = "structured" if a >= D.ACF_STRUCTURED else "grey"
        entry = closes[t]
        fut = closes[t + horizon]
        move_raw = (fut / entry - 1.0) * 1e4            # positif = harga naik

        def signed(which):
            if which == "long":
                return move_raw
            if which == "short":
                return -move_raw
            return None

        # `mom_*` = apa yang kata aturan momentum SEBELUM gerbang ACF; `side` = setelah gerbang.
        # Keduanya disimpan karena pertanyaan diagnostiknya justru perbandingannya: kalau mom
        # sering nyala tapi trade akhirnya nol, yang berbicara adalah gerbangnya, bukan idenya.
        out.append({"t": t, "side": side, "mom": mom, "gate": gate, "acf": a,
                    "gross_bps": signed(side) if side != "flat" else move_raw,
                    "net_bps": (signed(side) - cost) if side != "flat" else 0.0,
                    "mom_gross_bps": signed(mom),
                    "undecided_bps": abs(move_raw)})
        t += horizon
    return out


def sign_test_p(wins, n):
    """p satu arah untuk H1: lebih sering untung daripada rugi, di bawah H0 p=0,5 (eksak)."""
    if n == 0:
        return 1.0
    if wins * 2 <= n:
        return 1.0                       # kalah angka -> tidak mungkin signifikan satu arah
    # Jumlah di RUANG-LOG. Versi `sum(math.comb(n,k)) * 0.5**n` meledak dengan
    # OverflowError: int too large to convert to float begitu n besar (terukur 25 Sep pada
    # n=2.219 saat --mom-only). koefisien binomial di sini semuanya <= 1, jadi log-nya <= 0
    # dan pergeseran maksimum di bawah aman.
    lg2 = math.log(2.0)
    logs = [math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1) - n * lg2
            for k in range(wins, n + 1)]
    mx = max(logs)
    tail = math.exp(mx) * sum(math.exp(l - mx) for l in logs)
    return min(1.0, tail)


def fold_means(vals, folds):
    if not vals:
        return []
    idx = np.array_split(np.arange(len(vals)), folds)
    return [float(np.mean([vals[i] for i in part])) if len(part) else None for part in idx]


def bh_flag(pvals, alpha=BH_ALPHA):
    """Benjamini-Hochberg step-up: kembalikan himpunan indeks yang dinyatakan signifikan."""
    m = len(pvals)
    if not m:
        return set()
    order = sorted(range(m), key=lambda i: pvals[i])
    thresh = [alpha * (r + 1) / m for r in range(m)]
    kmax = -1
    for r, i in enumerate(order):
        if pvals[i] <= thresh[r]:
            kmax = r
    if kmax < 0:
        return set()
    return set(order[:kmax + 1])


def evaluate(sym, sig, cost_bps=None):
    """Ringkas satu simbol. `mom_*` menjawab SIAPA yang memproduksi nol: aturannya atau gerbangnya."""
    cost = RT_COST_BPS if cost_bps is None else cost_bps
    tr = [s for s in sig if s["side"] != "flat"]
    fl = [s for s in sig if s["side"] == "flat"]
    mom = [s for s in sig if s.get("mom") != "flat"]
    mom_net = [s["mom_gross_bps"] - cost for s in mom if s.get("mom_gross_bps") is not None]
    diag = {"points": len(sig), "mom_n": len(mom),
            "mom_mean_net_bps": round(float(np.mean(mom_net)), 1) if mom_net else None,
            "acf_killed": len([s for s in mom if s["side"] == "flat"])}
    if not tr:
        note = ("nol trade" if not mom else
                f"momentum menyala {len(mom)}/{len(sig)} titik, SEMUANYA dipadamkan gerbang "
                f"|acf| (killed={diag['acf_killed']})")
        return {"symbol": sym, "n": 0, "note": note, **diag}
    nets = [s["net_bps"] for s in tr]
    gross = [s["gross_bps"] for s in tr]
    wins = sum(1 for x in nets if x > 0)
    n = len(nets)
    fm = fold_means(nets, FOLDS)
    present = [x for x in fm if x is not None]
    drop_best = float(np.mean([x for i, x in enumerate(present) if i != int(np.argmax(present))])) \
        if len(present) > 1 else None
    sd = float(np.std(nets, ddof=1)) if n > 1 else 0.0
    tstat = (float(np.mean(nets)) / (sd / math.sqrt(n))) if sd else 0.0
    p = sign_test_p(wins, n)
    return {"symbol": sym, "n": n, "wr": wins / n, "mean_gross_bps": float(np.mean(gross)),
            "mean_net_bps": float(np.mean(nets)), "t": tstat, "p_sign": p, **diag,
            "folds": [None if x is None else round(x, 1) for x in fm],
            "drop_best_fold_net": None if drop_best is None else round(drop_best, 1),
            "flat_n": len(fl), "flat_abs_move_bps": float(np.mean([s["undecided_bps"] for s in fl])) if fl else None,
            "grey_share": round(sum(1 for s in tr if s["gate"] == "grey") / n, 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="*", default=None)
    ap.add_argument("--fetch", type=int, default=0, metavar="DAYS", help="isi/perbaiki cache dulu")
    ap.add_argument("--horizon", type=int, default=4, help="bar 1 jam (=jam) - 4 = horizon live")
    ap.add_argument("--min-bars", type=int, default=D.NEED_BARS)
    ap.add_argument("--mom-only", action="store_true",
                    help="matikan gerbang |acf| (Diagnosa: siapa yang memproduksi nol - aturannya atau gerbangnya?)")
    ap.add_argument("--cost", type=float, default=None, metavar="BPS",
                    help=f"ongkos round-trip bps (default {RT_COST_BPS:.0f})")
    ap.add_argument("--flip", action="store_true",
                    help="balik arah aturan yang sama (tes mean-reversion vs momentum)")
    a = ap.parse_args()
    gate = 0.0 if a.mom_only else None
    cost = RT_COST_BPS if a.cost is None else a.cost

    syms = a.symbols or DEFAULT_SYMBOLS
    if a.fetch:
        for s in syms:
            data, meta = barsmod.fetch(s, "1h", a.fetch, verbose=False)
            if data:
                p = barsmod.save(s, "1h", data, meta)
                print(f"  {s:14} {len(data):>6} bar -> {os.path.basename(p)}"
                      + (f"  WARNING={meta.get('meta_warning')}" if meta.get("meta_warning") else ""),
                      flush=True)
            else:
                print(f"  {s:14} 0 bar - TIDAK ADA DATA (bukan nol perubahan)")

    rows = []
    for s in syms:
        d = series(s)
        if not d:
            rows.append({"symbol": s, "n": 0, "note": "tidak ter-cache"})
            continue
        closes = np.array([b["c"] for b in d["bars"]], dtype=float)
        if len(closes) < a.min_bars:
            rows.append({"symbol": s, "n": 0, "note": f"bar={len(closes)} < {a.min_bars}"})
            continue
        rows.append(evaluate(s, signals(closes, a.horizon, acf_gate=gate, cost_bps=cost,
                                        flip=a.flip), cost_bps=cost))

    ps = [r["p_sign"] for r in rows if r.get("n", 0) >= MIN_TRADES]
    ok_idx = bh_flag(ps)
    ok_syms = {r["symbol"] for i, r in enumerate([x for x in rows if x.get("n", 0) >= MIN_TRADES])
               if i in ok_idx}

    print(f"\nhorizon {a.horizon} bar | ongkos {cost:.0f} bps RT | MIN_TRADES={MIN_TRADES} "
          f"| BH alpha={BH_ALPHA} | gerbang |acf| {'MATI (--mom-only)' if a.mom_only else f'>{D.ACF_EFFICIENT} flat'}"
          f" | arah: gap SMA24 +-1% searah ret24")
    print(f"kolom mom* = aturan momentum SEBELUM gerbang |acf| -> yang memisahkan 'idenya mati' "
          f"dari 'gerbangnya yang menolak'\n")
    print(f"{'simbol':14}{'n':>5}{'WR':>7}{'gross':>8}{'NET':>8}{'t':>7}{'p':>8}{'drop-best':>11}"
          f"{'momN':>6}{'momNet':>8}{'flat|mv|':>10}  BH  folds(net/5 segmen)")
    print("-" * 132)
    for r in rows:
        if r.get("n", 0) < MIN_TRADES:
            # Tampilkan n-nya. Versi pertama mencetak "-" saja untuk baris yang punya 1-19 trade,
            # jadi XRP/TAC terlihat seperti "tidak ada data" padahal datanya ada dan cuma kurang
            # sampel - dua keadaan yang harus beda di layar, sama seperti di decide.py.
            why = r.get("note") or (f"{r.get('n', 0)} trade < {MIN_TRADES} (tidak disimpulkan apa pun)"
                                    if r.get("n", 0) else "tidak ada trade")
            print(f"{r['symbol']:14}{r.get('n', 0):>5}{'':>38}  {why[:56]}")
            continue
        fs = " ".join("-" if x is None else f"{x:+.0f}" for x in r["folds"])
        mn = r.get("mom_mean_net_bps")
        print(f"{r['symbol']:14}{r['n']:>5}{r['wr']*100:>6.1f}%{r['mean_gross_bps']:>8.1f}"
              f"{r['mean_net_bps']:>8.1f}{r['t']:>7.2f}{r['p_sign']:>8.4f}"
              f"{(r['drop_best_fold_net'] if r['drop_best_fold_net'] is not None else 0):>11.1f}"
              f"{r.get('mom_n', 0):>6}{('-' if mn is None else f'{mn:+.1f}'):>8}"
              f"{(r['flat_abs_move_bps'] or 0):>10.1f}  "
              f"{'LOLOS' if r['symbol'] in ok_syms else '     '}  {fs}")

    good = [r for r in rows if r.get("n", 0) >= MIN_TRADES and r["symbol"] in ok_syms
            and r["mean_net_bps"] > 0 and (r["drop_best_fold_net"] or -1) > 0]
    print(f"\n{len(good)} simbol lolos SEMUANYA (n>={MIN_TRADES}, NET>0 setelah ongkos, "
          f"drop-best-fold>0, p lolos BH) dari {sum(1 for r in rows if r.get('n',0)>=MIN_TRADES)} yang bisa dinilai")
    for r in good:
        print(f"  -> {r['symbol']}: net {r['mean_net_bps']:+.1f} bps/trade, WR {r['wr']*100:.1f}%, "
              f"grey-zone {r['grey_share']*100:.0f}%")
    print("\nBatas yang tetap berlaku: (a) funding historic tidak ikut diuji, jadi ini aturan HARGA"
          "\nsaja, bukan agen live penuh; (b) tidak ada parameter yang di-fit, jadi jangan sebut ini"
          "\nwalk-forward fitted; (c) simbol-simbol ini saling berkorelasi lewat satu pasar - BH per"
          "\ntoken adalah pendekatan, bukan perbaikan korelasi silang.")
    os.makedirs(os.path.join(ROOT, "decisions"), exist_ok=True)
    # Nama file memuat MODE-nya. Tanpa ini, satu run diagnostik `--mom-only` (gerbang dimatikan =
    # angka lebih enak dilihat) akan MENIMPA artefak aturan-live yang jujur, dan yang tertinggal
    # di repo adalah versi yang paling flattering - bukan yang paling benar.
    tag = f"h{a.horizon}" + ("-momonly" if a.mom_only else "") + ("-flip" if a.flip else "") + \
          ("" if a.cost is None else f"-c{int(a.cost)}")
    out = os.path.join(ROOT, "decisions",
                       f"backtest-{time.strftime('%Y%m%d', time.gmtime())}Z-{tag}.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "horizon_bars": a.horizon, "cost_bps_rt": cost,
                   "acf_gate": D.ACF_EFFICIENT if gate is None else gate, "mom_only": a.mom_only,
                   "bars_min_required": a.min_bars, "non_overlap": True,
                   "thresholds": {"acf_efficient": D.ACF_EFFICIENT, "acf_structured": D.ACF_STRUCTURED,
                                  "min_bars": D.MIN_BARS_TINY, "sma_gap": 0.01},
                   "bh_alpha": BH_ALPHA, "bh_passed": sorted(ok_syms), "rows": rows},
                  fh, indent=1, sort_keys=True)
    print(f"tertulis: {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
