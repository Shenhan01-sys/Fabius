# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/05 - Epik Enam Bot.md, bagian KOREKSI, dan vault/09-Inbox/Session-2026-10-02.md).
# Bukan alat resmi; keluaran = bukan klaim produk. Butuh: pandas+numpy, data/ hasil fetch.py, dan paket `engine/` di akar repo.
"""Bandingkan mesin `engine/` (stdlib) dengan rujukan pandas (run3_funcs.py, run9.py) pada data dan jendela yang SAMA.

    python -X utf8 fetch.py            # sekali: mengisi ./data (gitignored)
    python -X utf8 run10_engine_vs_ref.py

Hasil yang dicari (dicetak ulang tiap kali dijalankan, bukan dikutip dari memori):
  - di luar jendela bolong data (<= 2022-02-24 dan >= 2022-05-15) PnL harian mesin = rujukan (corr ~ 1.0000);
  - di dalam jendela itu mereka berbeda KARENA lima perp (SOL, XRP, LTC, TRX, NEAR) bolong 26-28 Feb dan 1-2 Apr 2022
    di unduhan Binance Vision: pandas `pct_change` memperlakukan return 2-3 hari sebagai satu hari;
  - B2 rujukan = rebalance Rabu (`i % 7` dari 1 Jan 2020 yang jatuh pada hari Rabu); hari lain berbeda jauh.
"""
import dataclasses
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

import numpy as np
import pandas as pd

from lib import *                      # noqa: F401,F403  (D, stats, sig_meanrev, run_pos, basket ...)
import run3_funcs as r3

from engine.data import load_csv_dir
from engine.replay import replay
from engine.spec import PERP_UNIVERSE, SPECS

md = load_csv_dir(D, list(PERP_UNIVERSE) + ["PAXGUSDT"])


def eng(bot, **konst):
    sp = SPECS[bot]
    if konst:
        sp = dataclasses.replace(sp, konstanta={**sp.konstanta, **konst})
    return pd.Series({pd.Timestamp(t, unit="ms"): v for t, v in replay(sp, md)}).sort_index()


spot, fut, fund, R, UNI = r3.spot, r3.fut, r3.fund, r3.R, r3.UNI
b, g = spot["BTCUSDT"]["c"], spot["PAXGUSDT"]["c"]
idx = b.index.intersection(g.index)
rb, rg = b.reindex(idx).pct_change(), g.reindex(idx).pct_change()
vb, vg = rb.rolling(90).std(), rg.rolling(90).std()
wb = (1 / vb) / (1 / vb + 1 / vg)
wb = wb.where(wb.index.to_series().dt.day.eq(1), np.nan).ffill().shift(1).fillna(0.5)
rp = wb * rb + (1 - wb) * rg - wb.diff().abs().fillna(0) * 2 * 10 / 1e4
pn = {}
for s in UNI:
    sg = sig_meanrev(fut[s], N=10, z_in=2.0, long_short=False)
    p, _ = run_pos(sg, R[s], 7, fund.get(s))
    pn[s] = p

REF = {"B1-TREND": r3.bot_trend(60), "B2-RS": r3.bot_rs(28), "B3-CARRY": r3.bot_carry(0.10), "B5-CORE-RWA": rp,
       "B6-BOUNCE": basket(pn)}
ENG = {"B1-TREND": ("B1-TREND", eng("B1-TREND")),
       "B2-RS (Rabu, tranche=1)": ("B2-RS", eng("B2-RS", tranche=1, rebalance_hari_utc=2)),
       "B3-CARRY": ("B3-CARRY", eng("B3-CARRY")),
       "B5-CORE-RWA": ("B5-CORE-RWA", eng("B5-CORE-RWA")),
       "B6-BOUNCE": ("B6-BOUNCE", eng("B6-BOUNCE"))}

WINDOWS = (("penuh", slice(None)), ("sejak 2020-12-01", slice("2020-12-01", None)),
           ("pra-bolong <= 2022-02-24", slice(None, "2022-02-24")), ("pasca-bolong >= 2022-05-15", slice("2022-05-15", None)))
for name, sl in WINDOWS:
    print(f"\n=== jendela {name} ===")
    for k, (ref_key, e) in ENG.items():
        e2, r2 = e.loc[sl].fillna(0), REF[ref_key].loc[sl].fillna(0)
        j = e2.index.intersection(r2.index)
        se, sr = stats(e2), stats(r2)
        d = (e2.reindex(j) - r2.reindex(j)).abs()
        corr = float(np.corrcoef(e2.reindex(j), r2.reindex(j))[0, 1])
        print(f"{k:24} mesin Sharpe {se['sharpe']:6.3f} MDD {se['mdd'] * 100:6.1f}% n {se['n']:5d} | "
              f"rujukan Sharpe {sr['sharpe']:6.3f} MDD {sr['mdd'] * 100:6.1f}% n {sr['n']:5d} | "
              f"corr {corr:.4f} maks|selisih| {d.max():.5f}")

print(f"\nTanggal pertama R.index = {R.index[0].date()}, hari-minggu {R.index[0].weekday()} (0 = Senin): rujukan B2 `i % 7` berjangkar di sini")
_e, _r = ENG["B3-CARRY"][1], REF["B3-CARRY"]
_j = _e.index.intersection(_r.index)
_d = (_e.reindex(_j).fillna(0) - _r.reindex(_j).fillna(0))
_t = _d.abs().idxmax()
print(f"Selisih harian terbesar B3: {_t.date()} mesin {_e.loc[_t]:+.6f} rujukan {_r.loc[_t]:+.6f}")
print("\nB2-RS mesin, Sharpe sejak 2020-12-01 per hari-minggu rebalance (0 = Senin; Rabu = fase rujukan):")
print("  " + "  ".join(f"{wd}:{stats(eng('B2-RS', tranche=1, rebalance_hari_utc=wd).loc['2020-12-01':].fillna(0))['sharpe']:.3f}"
                      for wd in range(7)))
print("\nBolong bar perp pada data ini:")
for a_, s_ in sorted(md.perp.items()):
    for i in range(1, len(s_)):
        if s_.t[i] - s_.t[i - 1] != 86_400_000:
            print(f"  {a_}: {pd.Timestamp(s_.t[i - 1], unit='ms').date()} -> {pd.Timestamp(s_.t[i], unit='ms').date()}")
