# EKSPLORATIF - sesi 2 Okt 2026 (P92; lihat vault/00-Overview/03 - Decisions.md F-D75 dan vault/09-Inbox/Session-2026-10-02.md §12).
# Bukan alat resmi; keluaran = bukan klaim produk. Hanya stdlib. Mengunduh berkas statis publik dari data.binance.vision (tanpa kunci) ke ./data/premium (gitignored).
"""Bisakah funding Binance direkonstruksi dari `premiumIndexKlines` 1m (berkas statis Vision, terbit ±09:10Z hari berikutnya) tanpa REST?

    python -X utf8 run15_funding_reconstruct.py --months 2026-06,2026-07,2026-08 [--symbols BTCUSDT,ETHUSDT] [--variants]
    python -X utf8 run15_funding_reconstruct.py --engine-i --months 2025-05,2025-06,2025-07,2025-08     # uji LUAR WAKTU 2025 dengan I per simbol dari engine
    python -X utf8 run15_funding_reconstruct.py --oos          # pilih I per simbol (diskret) pada Mar-Mei 2026, uji DI LUAR SAMPEL pada Jun-Agu 2026 (angka di engine/funding_est.py)

Rumus Binance (dokumen "Introduction to Binance Futures Funding Rates"):  F = P + clamp(I - P, -0,05 %, +0,05 %),
P = rata-rata tertimbang waktu indeks premium per menit pada interval funding: P = sum_i(i * p_i) / sum_i(i), i = 1..n menit (bobot naik menurut waktu),
I = 0,01 % per interval 8 jam (0,03 %/hari; diskalakan H/8 untuk interval lain). Funding aktual dibaca dari ledger/bars/fund_<SYM>.csv (diturunkan dari zip bulanan Vision).

Tujuan: mengukur seberapa dekat rekonstruksi dengan funding AKTUAL pada peristiwa yang sudah diketahui, SEBELUM dipakai untuk apa pun. Hasilnya dilaporkan apa adanya:
galat per peristiwa (satuan 1e-6 = 0,01 bps), galat jumlah harian, dan seberapa besar itu dibanding biaya masuk (7 bps/sisi).
"""
import argparse
import csv
import io
import math
import os
import sys
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
from engine import funding_est as fe                  # noqa: E402
from engine.series import DAY_MS                      # noqa: E402
from engine.spec import PERP_UNIVERSE                 # noqa: E402

BARS = REPO / "ledger" / "bars"
CACHE = Path(os.environ.get("FABIUS_CACHE") or HERE / "data" / "premium")
CACHE.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (fabius-research/1.0)"}
VISION = "https://data.binance.vision/data/futures/um"
MIN_MS = 60_000


def get(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(1 + i)
        except Exception:
            time.sleep(1 + i)
    return None


def month_file(sym, ym):
    p = CACHE / f"{sym}-1m-{ym}.zip"
    if not p.exists():
        blob = get(f"{VISION}/monthly/premiumIndexKlines/{sym}/1m/{sym}-1m-{ym}.zip")
        if blob is None:
            return None
        p.write_bytes(blob)
    return p


def parse_premium(path):
    """{open_time_ms: (open, close)} dari satu zip bulanan premiumIndexKlines 1m."""
    out = {}
    with zipfile.ZipFile(path) as z:
        with z.open(z.namelist()[0]) as f:
            for r in csv.reader(io.TextIOWrapper(f)):
                if not r or not r[0].strip().lstrip("-").isdigit():
                    continue
                t = int(r[0])
                if t > 10**14:
                    t //= 1000
                out[t] = (float(r[1]), float(r[4]))
    return out


def load_actual(sym):
    p = BARS / f"fund_{sym}.csv"
    rows = []
    with open(p, newline="") as f:
        rd = csv.reader(f)
        next(rd, None)
        for r in rd:
            rows.append((int(float(r[0])), float(r[1])))
    return rows


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def estimate(prem, S, T0, variant, h_hours, interest=0.0001):
    """Funding terestimasi untuk interval [S, T0) (ms, awal menit). None bila ada menit yang hilang."""
    n = (T0 - S) // MIN_MS
    off = MIN_MS if variant.endswith("shift1") else 0
    vals = []
    for k in range(n):
        v = prem.get(S + k * MIN_MS + off)
        if v is None:
            return None
        vals.append(v[1] if "close" in variant else v[0])
    if variant.startswith("lin"):
        wsum = n * (n + 1) / 2
        P = sum((i + 1) * x for i, x in enumerate(vals)) / wsum
    elif variant.startswith("rev"):
        wsum = n * (n + 1) / 2
        P = sum((n - i) * x for i, x in enumerate(vals)) / wsum
    else:
        P = sum(vals) / n
    I = interest * h_hours / 8.0
    return P + clamp(I - P, -0.0005, 0.0005)


VARIANTS = ["lin_close", "lin_open", "mean_close", "rev_close", "lin_close_shift1"]


def evaluate(sym, months, variants, engine_i=False):
    prem = {}
    for ym in months:
        p = month_file(sym, ym)
        if p is not None:
            prem.update(parse_premium(p))
    if not prem:
        return None
    t_lo, t_hi = min(prem), max(prem) + MIN_MS
    act = load_actual(sym)
    ev = [(round(t / MIN_MS) * MIN_MS, r) for t, r in act]
    res = {v: [] for v in variants}
    skipped = 0
    for k in range(1, len(ev)):
        T0, f = ev[k]
        S = ev[k - 1][0]
        if S < t_lo or T0 > t_hi:
            continue
        h = (T0 - S) / 3_600_000
        got_any = False
        for v in variants:
            e = estimate(prem, S, T0, v, h, fe.interest_for(sym) if engine_i else 0.0001)
            if e is None:
                continue
            res[v].append((T0, h, f, e))
            got_any = True
        if not got_any:
            skipped += 1
    return res, skipped


def stats(rows):
    if not rows:
        return None
    errs = [e - f for _, _, f, e in rows]
    ae = sorted(abs(x) for x in errs)
    n = len(errs)
    mae = sum(ae) / n
    exact = sum(1 for x in ae if x < 6e-8) / n          # dalam pembulatan 8 desimal (tidak lebih dari ±6e-8)
    within = sum(1 for x in ae if x < 1e-6) / n          # < 0,01 bps
    fs = [f for _, _, f, _ in rows]
    es = [e for _, _, _, e in rows]
    mf, me = sum(fs) / n, sum(es) / n
    cov = sum((f - mf) * (e - me) for f, e in zip(fs, es))
    vf = sum((f - mf) ** 2 for f in fs)
    ve = sum((e - me) ** 2 for e in es)
    corr = cov / math.sqrt(vf * ve) if vf > 0 and ve > 0 else float("nan")
    # galat jumlah harian (hari UTC peristiwa jatuh)
    day = {}
    for T0, _, f, e in rows:
        d = (T0 // DAY_MS) * DAY_MS
        a, b = day.get(d, (0.0, 0.0))
        day[d] = (a + f, b + e)
    dae = [abs(b - a) for a, b in day.values()]
    return {"n": n, "mae": mae, "med": ae[n // 2], "p95": ae[int(n * 0.95)], "max": ae[-1], "exact": exact, "within": within, "corr": corr,
            "days": len(day), "day_mae": sum(dae) / len(dae), "day_max": max(dae)}


I_GRID = [0.0, 0.00005, 0.0001, 0.00015, 0.0002, 0.0003]


def interval_rows(sym, months):
    """[(T0, jam_interval, funding_aktual, P)] dengan P = rata-rata tertimbang close indeks premium per menit pada interval."""
    prem = {}
    for ym in months:
        pth = month_file(sym, ym)
        if pth:
            prem.update(parse_premium(pth))
    act = load_actual(sym)
    ev = [(round(t / MIN_MS) * MIN_MS, r) for t, r in act]
    lo, hi = min(prem), max(prem) + MIN_MS
    out = []
    for k in range(1, len(ev)):
        t0, f = ev[k]
        s = ev[k - 1][0]
        if s < lo or t0 > hi:
            continue
        n = (t0 - s) // MIN_MS
        vals = []
        for i in range(n):
            v = prem.get(s + i * MIN_MS)
            if v is None:
                vals = None
                break
            vals.append(v[1])
        if vals is None:
            continue
        out.append((t0, (t0 - s) / 3_600_000, f, sum((i + 1) * x for i, x in enumerate(vals)) / (n * (n + 1) / 2)))
    return out


def est_from_p(p, interest, h):
    return p + clamp(interest * h / 8.0 - p, -0.0005, 0.0005)


def oos(fit_months=("2026-03", "2026-04", "2026-05"), test_months=("2026-06", "2026-07", "2026-08")):
    print(f"pilih I (diskret {I_GRID}) pada {list(fit_months)}; uji di luar sampel pada {list(test_months)}; satuan 1e-6 = 0,01 bps\n")
    tot_err, tot_day, best_i = [], {}, {}
    for sym in PERP_UNIVERSE:
        fe = interval_rows(sym, fit_months)
        best = min(I_GRID, key=lambda i: sum(abs(est_from_p(p, i, h) - f) for _, h, f, p in fe) / len(fe))
        best_i[sym] = best
        te = interval_rows(sym, test_months)
        errs = [est_from_p(p, best, h) - f for _, h, f, p in te]
        ae = sorted(abs(x) for x in errs)
        day = {}
        for (t0, h, f, p), e in zip(te, errs):
            d = (t0 // DAY_MS) * DAY_MS
            day[d] = day.get(d, 0.0) + e
        dv = sorted(abs(x) for x in day.values())
        print(f"{sym:9} I*={best:.5f}  n={len(errs)}  MAE={sum(ae) / len(ae) * 1e6:6.2f}  med={ae[len(ae) // 2] * 1e6:6.2f}  p95={ae[int(len(ae) * .95)] * 1e6:7.2f}  "
              f"max={ae[-1] * 1e6:8.2f} | bias={sum(errs) / len(errs) * 1e6:+6.2f} | harian MAE={sum(dv) / len(dv) * 1e6:6.2f} p95={dv[int(len(dv) * .95)] * 1e6:7.2f} "
              f"max={dv[-1] * 1e6:8.2f} bias={sum(day.values()) / len(day) * 1e6:+7.2f}")
        tot_err += errs
        for k, v in day.items():
            tot_day[(sym, k)] = v
    ae = sorted(abs(x) for x in tot_err)
    n = len(ae)
    dv = sorted(abs(x) for x in tot_day.values())
    print(f"\nGABUNGAN uji: n={n} MAE={sum(ae) / n * 1e6:.2f} med={ae[n // 2] * 1e6:.2f} p95={ae[int(n * .95)] * 1e6:.2f} p99={ae[int(n * .99)] * 1e6:.2f} max={ae[-1] * 1e6:.2f} (1e-6 = 0,01 bps)")
    print(f"harian (simbol-hari) n={len(dv)}: MAE={sum(dv) / len(dv) * 1e6:.2f} med={dv[len(dv) // 2] * 1e6:.2f} p95={dv[int(len(dv) * .95)] * 1e6:.2f} "
          f"p99={dv[int(len(dv) * .99)] * 1e6:.2f} max={dv[-1] * 1e6:.2f}; bias rata-rata={sum(tot_day.values()) / len(tot_day) * 1e6:+.2f} (1e-6/hari)")
    print("I terpilih selain 0,0001:", {k: v for k, v in best_i.items() if v != 0.0001} or "tidak ada")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--months", default="2026-06,2026-07,2026-08")
    ap.add_argument("--symbols", default=",".join(PERP_UNIVERSE))
    ap.add_argument("--variants", action="store_true", help="bandingkan semua varian rumus (bawaan: hanya lin_close)")
    ap.add_argument("--engine-i", action="store_true", help="pakai I per simbol dari engine/funding_est.py (BNBUSDT = 0) alih-alih 0,0001 untuk semua")
    ap.add_argument("--oos", action="store_true", help="pilih I per simbol pada Mar-Mei 2026 dan uji di luar sampel pada Jun-Agu 2026")
    a = ap.parse_args()
    if a.oos:
        oos()
        return
    months = [m.strip() for m in a.months.split(",") if m.strip()]
    syms = [s.strip() for s in a.symbols.split(",") if s.strip()]
    variants = VARIANTS if a.variants else ["lin_close"]
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(lambda s: (s, evaluate(s, months, variants, a.engine_i)), syms))
    print(f"bulan {months}; satuan galat: 1e-6 = 0,01 bps per peristiwa; biaya masuk replay = 7 bps/sisi = 7e-4\n")
    agg = {v: [] for v in variants}
    for s, r in results:
        if r is None:
            print(f"{s}: tidak ada berkas premiumIndexKlines")
            continue
        res, skipped = r
        for v in variants:
            st = stats(res[v])
            if st is None:
                print(f"{s:9} {v:17} tidak ada peristiwa yang bisa dihitung (menit hilang?) dilewati={skipped}")
                continue
            agg[v].extend(res[v])
            print(f"{s:9} {v:17} n={st['n']:4d} MAE={st['mae'] * 1e6:8.3f} med={st['med'] * 1e6:8.3f} p95={st['p95'] * 1e6:8.3f} max={st['max'] * 1e6:9.3f} "
                  f"(1e-6) | persis(<6e-8)={st['exact'] * 100:5.1f}% <1e-6={st['within'] * 100:5.1f}% corr={st['corr']:.5f} | harian MAE={st['day_mae'] * 1e6:8.3f} max={st['day_max'] * 1e6:9.3f} dilewati={skipped}")
    print("\n== GABUNGAN SEMUA SIMBOL ==")
    for v in variants:
        st = stats(agg[v])
        if st:
            print(f"{v:17} n={st['n']:5d} MAE={st['mae'] * 1e6:8.3f} med={st['med'] * 1e6:8.3f} p95={st['p95'] * 1e6:8.3f} max={st['max'] * 1e6:9.3f} (1e-6) | "
                  f"persis={st['exact'] * 100:5.1f}% <1e-6={st['within'] * 100:5.1f}% corr={st['corr']:.5f}")
    print("(galat harian hanya per simbol di atas dan di mode --oos; di baris gabungan ia akan menjumlahkan antar simbol dan menyesatkan, jadi tidak dicetak)")
    print(f"\nwaktu {time.time() - t0:.0f} detik. Dalam-sampel pada peristiwa yang sudah diketahui; BUKAN jaminan untuk hari depan.")


if __name__ == "__main__":
    main()
