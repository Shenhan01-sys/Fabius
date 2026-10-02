# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/05 - Epik Enam Bot.md dan vault/09-Inbox/Session-2026-10-02.md).
# Bukan alat resmi; keluaran = bukan klaim produk. Unduhan masuk ./data/ (gitignored).
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from lib import *
import run3_funcs as r3
spot, fut, fund, R, F, UNI = r3.spot, r3.fut, r3.fund, r3.R, r3.F, r3.UNI
def sh(x): x = x.dropna(); return x.mean()*365/(x.std()*np.sqrt(365)) if len(x) > 60 and x.std() > 0 else np.nan
# --- risk parity BTC + PAXG (spot), monthly rebalance, inverse-vol(L) weights ---
b = spot["BTCUSDT"]["c"]; g = spot["PAXGUSDT"]["c"]; idx = b.index.intersection(g.index)
rb, rg = b.reindex(idx).pct_change(), g.reindex(idx).pct_change()
def riskparity(L, cost=10):
    vb, vg = rb.rolling(L).std(), rg.rolling(L).std()
    wb = (1/vb) / (1/vb + 1/vg)
    wb = wb.where(wb.index.is_month_start | wb.index.to_series().dt.day.eq(1), np.nan).ffill()   # monthly rebalance
    wb = wb.shift(1).fillna(0.5)
    wg = 1 - wb
    turn = wb.diff().abs().fillna(0) * 2
    return wb * rb + wg * rg - turn * cost / 1e4
print("RISK-PARITY BTC+PAXG (spot, monthly rebalance, 10 bps/side on turnover): Sharpe / ann / MDD / by-year")
for L in (30, 60, 90, 180):
    p = riskparity(L); s = stats(p); print(f"  L={L:3d}: sharpe {s['sharpe']:.2f} ann {s['ann']*100:5.1f}% mdd {s['mdd']*100:6.1f}% | {by_year(p)}")
print("  BTC B&H sharpe %.2f mdd %.1f%% | 50/50 static (monthly reb) sharpe %.2f" % (stats(rb)['sharpe'], stats(rb)['mdd']*100, stats(0.5*rb+0.5*rg)['sharpe']))
# --- marginal contribution of candidate #6 to a base-4 EW portfolio ---
bots = {"trend": r3.bot_trend(60), "rs": r3.bot_rs(21), "carry": r3.bot_carry(0.10), "goldrot": None}
# gold rotation daily pnl
on = (b.reindex(idx)/g.reindex(idx) > (b.reindex(idx)/g.reindex(idx)).rolling(100).mean()).astype(float).shift(1).fillna(0)
bots["goldrot"] = on*rb + (1-on)*rg - on.diff().abs().fillna(0)*2*10/1e4
bots["riskparity"] = riskparity(60)
cands = {"rebound k2.5": r3.bot_rev(2.5), "meanrev L/F N10": None, "squeeze p0.3": None, "volmanaged BTC T40": None}
def basket_sig(fn, **kw):
    pn = {}
    for s in UNI:
        sg = fn(fut[s], **kw); p, _ = run_pos(sg, R[s], 7, fund.get(s)); pn[s] = p
    return basket(pn)
cands["meanrev L/F N10"] = basket_sig(sig_meanrev, N=10, z_in=2.0, long_short=False)
def sig_sq(df, p):
    c = df["c"]; m = c.rolling(20).mean(); sd = c.rolling(20).std(); up_, lo_ = m + 2*sd, m - 2*sd; bw = 4*sd/m
    pr = bw.rolling(120).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True)
    pos = np.zeros(len(c)); cur = 0.0; cv, mv, uv, lv, pv = c.values, m.values, up_.values, lo_.values, pr.values
    for i in range(1, len(c)):
        if cur == 0 and not np.isnan(pv[i-1]) and pv[i-1] < p:
            if cv[i] > uv[i-1]: cur = 1.0
            elif cv[i] < lv[i-1]: cur = -1.0
        elif cur > 0 and cv[i] < mv[i]: cur = 0.0
        elif cur < 0 and cv[i] > mv[i]: cur = 0.0
        pos[i] = cur
    return pd.Series(pos, index=c.index)
cands["squeeze p0.3"] = basket_sig(sig_sq, p=0.3)
ret = r3.fut["BTCUSDT"]["c"].pct_change(); vol = ret.rolling(20).std()*np.sqrt(365); ex = (0.40/vol).clip(0, 1.5)
cands["volmanaged BTC T40"], _ = run_pos(ex, ret, 7, fund["BTCUSDT"])
start = "2020-12-01"
base = pd.concat({k: v for k, v in bots.items() if k in ("trend", "rs", "carry", "goldrot")}, axis=1).loc[start:].fillna(0)
def rep(name, P):
    ew = P.mean(axis=1); s = stats(ew); print(f"  {name:34} sharpe {s['sharpe']:5.2f} ann {s['ann']*100:5.1f}% mdd {s['mdd']*100:6.1f}%")
print("\nEQUAL-WEIGHT portfolios (window %s -> 2026-08):" % start)
rep("base-4: trend, rs, carry, goldrot", base)
for k, v in cands.items():
    rep(f"base-4 + {k}", pd.concat([base, v.loc[start:].fillna(0).rename(k)], axis=1))
rep("base-4 + riskparity(BTC+gold)", pd.concat([base, bots["riskparity"].loc[start:].fillna(0).rename("rp")], axis=1))
print("\ncorrelation of each candidate with base-4 EW pnl:")
ewb = base.mean(axis=1)
for k, v in list(cands.items()) + [("riskparity", bots["riskparity"])]:
    print(f"  {k:22} corr {v.loc[start:].fillna(0).corr(ewb):5.2f}   standalone sharpe {stats(v.loc[start:].fillna(0))['sharpe']:5.2f}")
