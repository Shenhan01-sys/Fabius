# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/05 - Epik Enam Bot.md dan vault/09-Inbox/Session-2026-10-02.md).
# Bukan alat resmi; keluaran = bukan klaim produk. Unduhan masuk ./data/ (gitignored).
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from lib import *
spot, fut, fund = load_all()
UNI = [s for s in ALL if s in fut]
ret = {s: fut[s]["c"].pct_change() for s in UNI}
R = pd.DataFrame(ret)
F = pd.DataFrame({s: fund[s].reindex(R.index).fillna(0.0) for s in UNI})
def fmt(d): return {k: float(v) for k, v in d.items()}
# regime context
print("REGIME CONTEXT - calendar-year return of BTC & EW basket (perp, ex-funding):")
for y in range(2020, 2027):
    m = R.index.year == y
    btc = (1 + R.loc[m, "BTCUSDT"]).prod() - 1
    ew = (1 + R.loc[m].mean(axis=1)).prod() - 1
    vol = R.loc[m, "BTCUSDT"].std() * np.sqrt(365)
    print(f"  {y}: BTC {btc*100:7.1f}%  EW basket {ew*100:8.1f}%  BTC vol {vol*100:4.0f}%")
def evaluate_asset(sigfn, cost, **kw):
    pn = {}; tu = []
    for s in UNI:
        sg = sigfn(fut[s], **kw)
        p, pos = run_pos(sg, ret[s], cost, fund.get(s)); pn[s] = p; tu.append(pos.diff().abs().mean()*365)
    return basket(pn), np.mean(tu)
def row(label, b7, b15, tu):
    s7, s15 = stats(b7), stats(b15)
    print(f"{label:30} sharpe {s7['sharpe']:5.2f} (15bp {s15['sharpe']:5.2f}) ann {s7['ann']*100:6.1f}% mdd {s7['mdd']*100:6.1f}% turn {tu:6.1f}/yr | {by_year(b7)}")
print("\nMEAN-REVERSION z-score(N), enter |z|>2, exit z=0 (per-asset, EW basket):")
for ls, nm in [(True, "L/S"), (False, "L/F")]:
    for N in [10, 20, 50]:
        b7, tu = evaluate_asset(sig_meanrev, 7, N=N, long_short=ls); b15, _ = evaluate_asset(sig_meanrev, 15, N=N, long_short=ls)
        row(f"meanrev {nm} N={N}", b7, b15, tu)
print("\nREVERSAL after 1-day drop < -k*sigma20, hold 2 days, long only:")
for k in [2.0, 2.5, 3.0]:
    b7, tu = evaluate_asset(sig_reversal, 7, k=k, hold=2); b15, _ = evaluate_asset(sig_reversal, 15, k=k, hold=2)
    row(f"reversal k={k}", b7, b15, tu)
print("\nPAIRS: ETH/BTC log-ratio z(N), |z|>2 entry, 0 exit (2 legs cost, funding differential):")
def pair(a, b, N, cost):
    lr = np.log(fut[a]["c"] / fut[b]["c"]).dropna()
    z = (lr - lr.rolling(N).mean()) / lr.rolling(N).std()
    pos = np.zeros(len(z)); cur = 0.0; zv = z.values
    for i in range(len(z)):
        if not np.isnan(zv[i]):
            if cur == 0:
                if zv[i] < -2: cur = 1.0      # long a, short b
                elif zv[i] > 2: cur = -1.0
            elif cur > 0 and zv[i] >= 0: cur = 0.0
            elif cur < 0 and zv[i] <= 0: cur = 0.0
        pos[i] = cur
    sg = pd.Series(pos, index=z.index).shift(1).reindex(R.index).fillna(0.0)
    sp = (R[a] - R[b]); turn = sg.diff().abs().fillna(sg.abs())
    pnl = sg * sp - turn * 2 * cost / 1e4 - sg * (F[a] - F[b])
    return pnl
for a, b in [("ETHUSDT", "BTCUSDT"), ("BNBUSDT", "BTCUSDT"), ("SOLUSDT", "ETHUSDT")]:
    for N in [20, 60, 120]:
        p7 = pair(a, b, N, 7); p15 = pair(a, b, N, 15)
        s7, s15 = stats(p7), stats(p15)
        print(f"pair {a[:-4]}/{b[:-4]} N={N:3}: sharpe {s7['sharpe']:5.2f} (15bp {s15['sharpe']:5.2f}) ann {s7['ann']*100:5.1f}% mdd {s7['mdd']*100:6.1f}% | {by_year(p7)}")
print("\nCROSS-SECTIONAL MOMENTUM: weekly rebalance, rank by N-day return, long top3 / short bottom3 (LS, each leg 1.0) | long-only top3 (LO):")
def xsmom(N, cost, long_only=False, k=3, reb=7):
    ranks = R.rolling(N).apply(lambda x: np.prod(1 + x) - 1, raw=True) if False else (1 + R).rolling(N).apply(np.prod, raw=True) - 1
    W = pd.DataFrame(0.0, index=R.index, columns=R.columns)
    last = None
    dates = list(R.index)
    cur = pd.Series(0.0, index=R.columns)
    for i, d in enumerate(dates):
        if i % reb == 0:
            r = ranks.loc[d].dropna()
            if len(r) >= 8:
                top = r.nlargest(k).index; bot = r.nsmallest(k).index
                cur = pd.Series(0.0, index=R.columns)
                cur[top] = 1.0 / k
                if not long_only: cur[bot] = -1.0 / k
        W.loc[d] = cur
    Wp = W.shift(1).fillna(0.0)
    turn = Wp.diff().abs().fillna(Wp.abs()).sum(axis=1)
    pnl = (Wp * R.fillna(0.0)).sum(axis=1) - turn * cost / 1e4 - (Wp * F).sum(axis=1)
    return pnl, turn.mean() * 365
for lo, nm in [(False, "LS"), (True, "LO")]:
    for N in [7, 14, 28, 56, 90]:
        p7, tu = xsmom(N, 7, lo); p15, _ = xsmom(N, 15, lo)
        s7, s15 = stats(p7), stats(p15)
        print(f"xsmom {nm} N={N:3}: sharpe {s7['sharpe']:5.2f} (15bp {s15['sharpe']:5.2f}) ann {s7['ann']*100:6.1f}% mdd {s7['mdd']*100:6.1f}% turn {tu:5.1f}/yr | {by_year(p7)}")
