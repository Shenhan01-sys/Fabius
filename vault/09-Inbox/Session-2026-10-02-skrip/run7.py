# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/05 - Epik Enam Bot.md dan vault/09-Inbox/Session-2026-10-02.md).
# Bukan alat resmi; keluaran = bukan klaim produk. Unduhan masuk ./data/ (gitignored).
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from lib import *
import run3_funcs as r3
print("RS (cross-sectional momentum LS) robustness grid - Sharpe (7 bps/side, funding incl.), universe 16 perps 2020-2026")
print("rows: lookback N ; cols: (k top/bottom, rebalance days)")
cols = [(2, 7), (3, 7), (4, 7), (3, 3), (3, 14)]
print(f"{'N':>4} " + "".join(f"k={k},reb={r:<3d}   " for k, r in cols))
for N in [10, 14, 21, 28, 42, 56]:
    row = f"{N:>4} "
    for k, reb in cols:
        row += f"{stats(r3.bot_rs(N, 7, k=k, reb=reb))['sharpe']:11.2f}   "
    print(row)
print("\nTrend L/F TSM(N) robustness on EW basket, Sharpe by N:", {N: round(stats(r3.bot_trend(N))['sharpe'], 2) for N in [10, 20, 30, 45, 60, 90, 120]})
