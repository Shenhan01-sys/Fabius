# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/05 - Epik Enam Bot.md dan vault/09-Inbox/Session-2026-10-02.md).
# Bukan alat resmi; keluaran = bukan klaim produk. Unduhan masuk ./data/ (gitignored).
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from lib import *
import run3_funcs as r3
bots = {"trend(TSM30 L/F)": r3.bot_trend(30), "rel-strength(xs28 LS)": r3.bot_rs(28), "carry(th10%)": r3.bot_carry(0.10),
        "rebound(k2.5)": r3.bot_rev(2.5), "gold(PAXG TSM60)": r3.bot_gold(60), "bear(TSM30 short)": r3.bot_trend_short(30)}
P = pd.concat(bots, axis=1).loc["2020-09-01":]      # common window where all exist (gold starts 2020-08)
P = P.fillna(0.0)
print("window", P.index[0].date(), "->", P.index[-1].date(), "days", len(P))
print("\nPER-BOT stats (cost-inclusive):")
for c in P.columns:
    s = stats(P[c]); print(f"  {c:24} sharpe {s['sharpe']:5.2f} ann {s['ann']*100:6.1f}% vol {s['vol']*100:5.1f}% mdd {s['mdd']*100:6.1f}% | {by_year(P[c])}")
print("\nCORRELATION of daily pnl:")
print(P.corr().round(2).to_string())
ew = P.mean(axis=1); s = stats(ew); print(f"\nEQUAL-WEIGHT of 6 bots: sharpe {s['sharpe']:.2f} ann {s['ann']*100:.1f}% mdd {s['mdd']*100:.1f}% | {by_year(ew)}")
core = P[["trend(TSM30 L/F)", "rel-strength(xs28 LS)", "carry(th10%)"]].mean(axis=1); s = stats(core)
print(f"EQUAL-WEIGHT of 3 core (trend, rs, carry): sharpe {s['sharpe']:.2f} ann {s['ann']*100:.1f}% mdd {s['mdd']*100:.1f}%")
# ---- regimes (known at d-1) ----
btc = r3.fut["BTCUSDT"]["c"].reindex(P.index.union(r3.fut["BTCUSDT"].index)).sort_index()
up = (btc > btc.rolling(100).mean()).shift(1).reindex(P.index)
vol = btc.pct_change().rolling(30).std().shift(1).reindex(P.index); vhi = vol > vol.expanding(120).median()
er = (btc.diff(60).abs() / btc.diff().abs().rolling(60).sum()).shift(1).reindex(P.index); ehi = er > er.expanding(120).median()
def sh(x): return x.mean() * 365 / (x.std() * np.sqrt(365)) if x.std() > 0 and len(x) > 60 else np.nan
print("\nREGIME-CONDITIONAL Sharpe (regime known at d-1):")
print(f"{'bot':24} {'BTC>SMA100':>11} {'BTC<SMA100':>11} {'vol hi':>8} {'vol lo':>8} {'trendy':>8} {'choppy':>8}")
for c in P.columns:
    print(f"{c:24} {sh(P.loc[up==True, c]):11.2f} {sh(P.loc[up==False, c]):11.2f} {sh(P.loc[vhi==True, c]):8.2f} {sh(P.loc[vhi==False, c]):8.2f} {sh(P.loc[ehi==True, c]):8.2f} {sh(P.loc[ehi==False, c]):8.2f}")
print("share of days: BTC up", round(float((up == True).mean()), 2), "| vol hi", round(float((vhi == True).mean()), 2), "| trendy", round(float((ehi == True).mean()), 2))
# ---- selectors ----
cols = list(P.columns); n = len(cols)
trail = P.rolling(60).mean() / P.rolling(60).std()
tr = trail.shift(1).dropna(how="all")
pick = tr.idxmax(axis=1)
sel = pd.Series([P.loc[d, pick[d]] for d in pick.index], index=pick.index)
s = stats(sel); print(f"\nSELECTOR A trailing-60d-Sharpe pick (no switching cost): sharpe {s['sharpe']:.2f} ann {s['ann']*100:.1f}% mdd {s['mdd']*100:.1f}% | {by_year(sel)}")
def rule(d):
    u = up.get(d)
    if u is True: return "trend(TSM30 L/F)"
    if u is False: return "rel-strength(xs28 LS)"
    return None
sel2 = pd.Series([P.loc[d, rule(d)] if rule(d) else np.nan for d in P.index], index=P.index).dropna()
s = stats(sel2); print(f"SELECTOR B rule (BTC>SMA100 -> trend else rel-strength): sharpe {s['sharpe']:.2f} ann {s['ann']*100:.1f}% mdd {s['mdd']*100:.1f}% | {by_year(sel2)}")
rng = np.random.default_rng(0); sims = []
arr = P.values
for _ in range(2000):
    ch = rng.integers(0, n, size=len(P)); x = arr[np.arange(len(P)), ch]
    sims.append(x.mean() * 365 / (x.std() * np.sqrt(365)))
print(f"RANDOM selector (daily uniform pick, 2000 sims): Sharpe mean {np.mean(sims):.2f}  p5 {np.percentile(sims,5):.2f}  p95 {np.percentile(sims,95):.2f}")
best = max(cols, key=lambda c: stats(P[c])["sharpe"]); print("best single (in-sample, hindsight):", best, round(stats(P[best])["sharpe"], 2))
