# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/05 - Epik Enam Bot.md dan vault/09-Inbox/Session-2026-10-02.md).
# Bukan alat resmi; keluaran = bukan klaim produk. Unduhan masuk ./data/ (gitignored).
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from lib import *
import run3_funcs as r3
R, F, fut, fund, UNI = r3.R, r3.F, r3.fut, r3.fund, r3.UNI
def ls_rank(score_df, k=3, reb=7, sign=+1, cost=7):
    W = pd.DataFrame(0.0, index=R.index, columns=R.columns); cur = pd.Series(0.0, index=R.columns)
    for i, d in enumerate(R.index):
        if i % reb == 0:
            r = (sign * score_df.loc[d]).dropna()
            if len(r) >= 8:
                cur = pd.Series(0.0, index=R.columns); cur[r.nlargest(k).index] = 1.0 / k; cur[r.nsmallest(k).index] = -1.0 / k
        W.loc[d] = cur
    Wp = W.shift(1).fillna(0.0); turn = Wp.diff().abs().fillna(Wp.abs()).sum(axis=1)
    pnl = (Wp * R.fillna(0.0)).sum(axis=1) - turn * cost / 1e4 - (Wp * F).sum(axis=1)
    return pnl, turn.mean() * 365
def show(label, p, tu=None):
    s = stats(p); s15 = None
    print(f"{label:34} sharpe {s['sharpe']:5.2f} ann {s['ann']*100:6.1f}% mdd {s['mdd']*100:6.1f}%" + (f" turn {tu:5.0f}/yr" if tu is not None else "") + f" | {by_year(p)}")
print("SHORT-TERM CROSS-SECTIONAL REVERSAL (contrarian ranks; long losers/short winners):")
for N, reb in [(1, 1), (3, 3), (5, 5), (7, 7)]:
    sc = (1 + R).rolling(N).apply(np.prod, raw=True) - 1
    p, tu = ls_rank(sc, reb=reb, sign=-1); show(f"  reversal-LS N={N} reb={reb}d", p, tu)
print("LOW-VOL (long lowest vol3 / short highest vol3), weekly:")
for N in [14, 30, 60]:
    sc = R.rolling(N).std()
    p, tu = ls_rank(sc, sign=-1); show(f"  lowvol-LS N={N}", p, tu)
print("FUNDING-EXTREME contrarian (directional per asset): short when 7d funding pctile>p, long when <1-p (180d window), exit at median:")
def sig_fc(s, p):
    f = fund[s].reindex(R.index).fillna(0.0).rolling(7).mean()
    pr = f.rolling(180).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True)
    pos = np.zeros(len(pr)); cur = 0.0; v = pr.values
    for i in range(len(pr)):
        if not np.isnan(v[i]):
            if cur == 0:
                if v[i] > p: cur = -1.0
                elif v[i] < 1 - p: cur = 1.0
            elif cur < 0 and v[i] <= 0.5: cur = 0.0
            elif cur > 0 and v[i] >= 0.5: cur = 0.0
        pos[i] = cur
    return pd.Series(pos, index=pr.index)
for pq in [0.90, 0.95]:
    pn = {}
    for s in UNI:
        p_, _ = run_pos(sig_fc(s, pq), R[s], 7, fund.get(s)); pn[s] = p_
    show(f"  fund-contra p={pq}", basket(pn))
print("BOLLINGER SQUEEZE breakout (bandwidth pctile < p over 120d, close breaks band -> follow; exit at SMA20; per asset):")
def sig_sq(df, p):
    c = df["c"]; m = c.rolling(20).mean(); sd = c.rolling(20).std(); up_, lo_ = m + 2 * sd, m - 2 * sd; bw = (4 * sd / m)
    pr = bw.rolling(120).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True)
    pos = np.zeros(len(c)); cur = 0.0
    cv, mv, uv, lv, pv = c.values, m.values, up_.values, lo_.values, pr.values
    for i in range(1, len(c)):
        if cur == 0 and not np.isnan(pv[i-1]) and pv[i-1] < p:
            if cv[i] > uv[i-1]: cur = 1.0
            elif cv[i] < lv[i-1]: cur = -1.0
        elif cur > 0 and cv[i] < mv[i]: cur = 0.0
        elif cur < 0 and cv[i] > mv[i]: cur = 0.0
        pos[i] = cur
    return pd.Series(pos, index=c.index)
for pq in [0.10, 0.20, 0.30]:
    pn = {}
    for s in UNI:
        p_, _ = run_pos(sig_sq(fut[s], pq), R[s], 7, fund.get(s)); pn[s] = p_
    show(f"  squeeze p={pq}", basket(pn))
print("\nDAY-OF-WEEK mean daily return BTC perp (bps), full sample / 2023+ (informational; not a bot):")
b = R["BTCUSDT"].dropna()
for lab, x in [("2020-2026", b), ("2023-2026", b.loc["2023":])]:
    g = (x.groupby(x.index.dayofweek).mean() * 1e4).round(1); print(" ", lab, dict(zip(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], g.values)))
