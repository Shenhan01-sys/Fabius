# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/05 - Epik Enam Bot.md dan vault/09-Inbox/Session-2026-10-02.md).
# Bukan alat resmi; keluaran = bukan klaim produk. Unduhan masuk ./data/ (gitignored).
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from lib import *
import run3_funcs as r3
spot, fut, fund, R, UNI = r3.spot, r3.fut, r3.fund, r3.R, r3.UNI
b = spot["BTCUSDT"]["c"]; g = spot["PAXGUSDT"]["c"]; idx = b.index.intersection(g.index)
rb, rg = b.reindex(idx).pct_change(), g.reindex(idx).pct_change()
vb, vg = rb.rolling(90).std(), rg.rolling(90).std(); wb = (1/vb)/(1/vb+1/vg)
wb = wb.where(wb.index.to_series().dt.day.eq(1), np.nan).ffill().shift(1).fillna(0.5)
rp = wb*rb + (1-wb)*rg - wb.diff().abs().fillna(0)*2*10/1e4
pn = {}
for s in UNI:
    sg = sig_meanrev(fut[s], N=10, z_in=2.0, long_short=False); p, _ = run_pos(sg, R[s], 7, fund.get(s)); pn[s] = p
mr = basket(pn)
P = pd.concat({"trend60": r3.bot_trend(60), "rs28": r3.bot_rs(28), "carry10": r3.bot_carry(0.10), "coreRWA90": rp, "bounce10": mr}, axis=1).loc["2020-12-01":].fillna(0)
for c in P: s = stats(P[c]); print(f"  {c:10} sharpe {s['sharpe']:5.2f} ann {s['ann']*100:6.1f}% mdd {s['mdd']*100:6.1f}%")
ew = P.mean(axis=1); s = stats(ew); print(f"EW of 5 daily bots (2020-12 -> 2026-08): sharpe {s['sharpe']:.2f} ann {s['ann']*100:.1f}% mdd {s['mdd']*100:.1f}% | by-year {by_year(ew)}")
print("pairwise corr max off-diagonal:", round(float((P.corr().where(~np.eye(5, dtype=bool))).max().max()), 2), "| mean:", round(float((P.corr().where(~np.eye(5, dtype=bool))).stack().mean()), 2))
print("2025-01..2026-08 EW sharpe:", round(stats(ew.loc['2025-01-01':])['sharpe'], 2), " | trend/rs/coreRWA/bounce in that window:", {c: round(stats(P[c].loc['2025-01-01':])['sharpe'], 2) for c in P})
