# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/05 - Epik Enam Bot.md dan vault/09-Inbox/Session-2026-10-02.md).
# Bukan alat resmi; keluaran = bukan klaim produk. Unduhan masuk ./data/ (gitignored).
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from lib import *
import run3_funcs as r3
spot, fut, fund, R, F, UNI = r3.spot, r3.fut, r3.fund, r3.R, r3.F, r3.UNI
def sh(x): x = x.dropna(); return x.mean()*365/(x.std()*np.sqrt(365)) if len(x) > 60 and x.std() > 0 else np.nan
print("A) BTC<->GOLD ROTATION (spot, long-only): hold BTC if BTC/PAXG ratio > SMA(N) else PAXG; cost 10 bps/side on switch")
b = spot["BTCUSDT"]["c"]; g = spot["PAXGUSDT"]["c"]; idx = b.index.intersection(g.index)
b, g = b.reindex(idx), g.reindex(idx); rb, rg = b.pct_change(), g.pct_change(); ratio = b / g
for N in [50, 100, 150, 200]:
    on_btc = (ratio > ratio.rolling(N).mean()).astype(float).shift(1).fillna(0.0)
    turn = on_btc.diff().abs().fillna(0.0)
    pnl = on_btc * rb + (1 - on_btc) * rg - turn * 2 * 10 / 1e4
    s = stats(pnl); print(f"  N={N:3}: sharpe {s['sharpe']:5.2f} ann {s['ann']*100:5.1f}% mdd {s['mdd']*100:6.1f}% time-in-BTC {on_btc.mean()*100:3.0f}% | {by_year(pnl)}")
s = stats(rb); print(f"  BTC B&H (spot): sharpe {s['sharpe']:.2f} ann {s['ann']*100:.1f}% mdd {s['mdd']*100:.1f}% | PAXG B&H sharpe {stats(rg)['sharpe']:.2f}")
print("  vs BTC trend-with-cash (TSM60 L/F spot):", end=" ")
sg = sig_tsm(spot["BTCUSDT"], N=60, long_short=False); p, _ = run_pos(sg, spot["BTCUSDT"]["c"].pct_change(), 10); s = stats(p.reindex(idx)); print(f"sharpe {s['sharpe']:.2f} ann {s['ann']*100:.1f}% mdd {s['mdd']*100:.1f}%")

print("\nB) PER-ASSET robustness (perp, cost 7 bps/side, funding incl.) Sharpe 2020-2026 | first half 2020-09..2023-06 / second half 2023-07..2026-08")
cands = {"TSM30 L/F": lambda df: sig_tsm(df, 30, False), "Donch50 L/F": lambda df: sig_donchian(df, 50, False),
         "meanrev10 L/F": lambda df: sig_meanrev(df, 10, 2.0, False), "rebound k2.5": lambda df: sig_reversal(df, 2.5, 2)}
print(f"{'asset':9}" + "".join(f"{k:>30}" for k in cands))
for s_ in ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "LINKUSDT", "ADAUSDT"]:
    row = f"{s_[:-4]:9}"
    for k, fn in cands.items():
        p, _ = run_pos(fn(fut[s_]), R[s_], 7, fund.get(s_))
        a = sh(p.loc["2020-09-01":"2023-06-30"]); c = sh(p.loc["2023-07-01":]); row += f"{sh(p):8.2f} ({a:5.2f}/{c:5.2f})        "
    print(row)
print("\nC) SPLIT-SAMPLE for the main basket bots (Sharpe: 2020-09..2023-06 | 2023-07..2026-08):")
bots = {"trend TSM30 L/F": r3.bot_trend(30), "rel-strength xs28 LS": r3.bot_rs(28), "rel-strength xs14 LS": r3.bot_rs(14), "rel-strength xs56 LS": r3.bot_rs(56),
        "carry th10%": r3.bot_carry(0.10), "gold TSM60": r3.bot_gold(60)}
for k, p in bots.items():
    print(f"  {k:24} {sh(p.loc['2020-09-01':'2023-06-30']):6.2f} | {sh(p.loc['2023-07-01':]):6.2f}   (2025-01..2026-08: {sh(p.loc['2025-01-01':]):6.2f})")
print("\nD) COST SENSITIVITY rel-strength xs28 LS: Sharpe at cost/side 0 / 7 / 15 / 30 bps:", [round(stats(r3.bot_rs(28, cost=c))['sharpe'], 2) for c in (0, 7, 15, 30)])
print("   trend TSM30 L/F:", [round(stats(r3.bot_trend(30, cost=c))['sharpe'], 2) for c in (0, 7, 15, 30)])
