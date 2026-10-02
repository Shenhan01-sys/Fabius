# EKSPLORATIF - sesi 2 Okt 2026 (P92 lanjutan; lihat vault/00-Overview/03 - Decisions.md F-D76 dan vault/09-Inbox/Session-2026-10-02.md §13).
# Bukan alat resmi; keluaran = bukan klaim produk. Hanya stdlib + paket `engine/`; memakai berkas premium yang sudah di-cache oleh run15 (atau mengunduhnya dari data.binance.vision).
"""Seberapa sering TARGET B3-CARRY berubah bila funding dari hari-hari terbaru diganti ESTIMASI (indeks premium) alih-alih funding aktual?

    python -X utf8 run16_b3_est_fidelity.py [--data <folder CSV fetch.py>] [--start 2026-06-01] [--end 2026-08-31]

Meniru operasi maju: funding AKTUAL untuk hari < --start, ESTIMASI beku untuk hari >= --start (seperti pandangan `targets` di `engine.data`, dengan estimasi dimulai di hari pertama berkas estimasi).
Perbandingan: target B3 (bobot per hari) dari funding aktual vs dari pandangan "targets"; lalu PnL B3 dengan funding AKTUAL pada settle untuk kedua deret target (selisih = harga memakai estimasi).
Dalam-sampel pada Jun-Agu 2026 untuk satu bot; BUKAN jaminan untuk hari depan.
"""
import argparse
import importlib.util
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from engine import funding_est as fe                      # noqa: E402
from engine.bots import REGISTRY                          # noqa: E402
from engine.data import MarketData, load_csv_dir          # noqa: E402
from engine.replay import replay                          # noqa: E402
from engine.report import date_ms, fmt, summary           # noqa: E402
from engine.series import DAY_MS                          # noqa: E402
from engine.spec import PERP_UNIVERSE, SPECS              # noqa: E402

_spec = importlib.util.spec_from_file_location("run15", HERE / "run15_funding_reconstruct.py")
run15 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run15)


def est_by_day(sym, months, start_ms, end_ms):
    minutes = {}
    for ym in months:
        p = run15.month_file(sym, ym)
        if p is not None:
            minutes.update({t: c for t, (o, c) in run15.parse_premium(p).items()})
    out, d = {}, start_ms
    while d <= end_ms:
        ev = fe.estimate_day(sym, minutes, d)
        if ev is not None:
            out[d] = sum(r for _, r in ev)
        d += DAY_MS
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    default_data = os.environ.get("FABIUS_DATA") or str(HERE / "data")
    ap.add_argument("--data", default=default_data, help="folder CSV fut_/spot_/fund_ (keluaran fetch.py); bawaan: $FABIUS_DATA atau ./data")
    ap.add_argument("--start", default="2026-06-01")
    ap.add_argument("--end", default="2026-08-31")
    ap.add_argument("--months", default="2026-05,2026-06,2026-07,2026-08")
    a = ap.parse_args()
    start, end = date_ms(a.start), date_ms(a.end)
    months = [m.strip() for m in a.months.split(",") if m.strip()]
    spec = SPECS["B3-CARRY"]
    md = load_csv_dir(a.data, list(PERP_UNIVERSE) + ["PAXGUSDT", "XAUUSDT"])
    est = {s: est_by_day(s, months, start, end) for s in PERP_UNIVERSE}
    funding_t = {}
    for s in PERP_UNIVERSE:
        act = md.funding.get(s, {})
        funding_t[s] = {d: v for d, v in act.items() if d < start}
        funding_t[s].update(est[s])                                               # estimasi beku sejak hari pertama berkas estimasi
    md_t = MarketData(perp=md.perp, spot=md.spot, funding=funding_t, events=md.events)
    tg_a = {t.t: t for t in REGISTRY["B3-CARRY"](spec, md)}
    tg_t = {t.t: t for t in REGISTRY["B3-CARRY"](spec, md_t)}
    days = [d for d in sorted(tg_a) if start <= d <= end and d in tg_t]
    n_diff_days, flips, held_a, held_t = 0, 0, 0, 0
    flip_detail = {}
    for d in days:
        wa, wt = tg_a[d].weights, tg_t[d].weights
        sa, st = set(wa), set(wt)
        held_a += len(sa)
        held_t += len(st)
        if sa != st or any(abs(wa[x] - wt[x]) > 1e-12 for x in sa & st):
            n_diff_days += 1
        for x in sa ^ st:
            flips += 1
            flip_detail[x] = flip_detail.get(x, 0) + 1
    print(f"B3-CARRY theta={spec.param}; {a.start}..{a.end}: {len(days)} hari; estimasi hanya untuk hari >= {a.start}; aktual sebelum itu")
    print(f"hari dengan bobot BERBEDA: {n_diff_days}/{len(days)} ({100 * n_diff_days / max(len(days), 1):.1f}%)")
    print(f"aset-hari dipegang (aktual): {held_a}; (estimasi): {held_t}; aset-hari yang BERUBAH status: {flips} ({100 * flips / max(held_a, 1):.2f}% dari yang dipegang)")
    if flip_detail:
        print("per aset:", dict(sorted(flip_detail.items(), key=lambda kv: -kv[1])))
    pa = [(t, v) for t, v in replay(spec, md, tg=[tg_a[d] for d in sorted(tg_a)]) if start <= t <= end]
    pt = [(t, v) for t, v in replay(spec, md, tg=[tg_t[d] for d in sorted(tg_t)]) if start <= t <= end]
    print("\nPnL net B3 dengan funding AKTUAL pada settle:")
    print("  target dari funding aktual  :", fmt(summary(pa)))
    print("  target dari estimasi (beku) :", fmt(summary(pt)))
    da = sum(v for _, v in pa)
    dt_ = sum(v for _, v in pt)
    print(f"  jumlah net: aktual {da * 1e4:+.2f} bps vs estimasi {dt_ * 1e4:+.2f} bps (selisih {(dt_ - da) * 1e4:+.2f} bps selama {len(pa)} hari)")
    print("\nDalam-sampel pada satu jendela; BUKAN klaim edge dan BUKAN jaminan untuk hari depan.")


if __name__ == "__main__":
    main()
