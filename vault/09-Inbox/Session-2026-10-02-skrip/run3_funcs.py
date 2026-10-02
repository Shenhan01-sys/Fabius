# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/05 - Epik Enam Bot.md dan vault/09-Inbox/Session-2026-10-02.md).
# Bukan alat resmi; keluaran = bukan klaim produk. Unduhan masuk ./data/ (gitignored).
import numpy as np, pandas as pd
from lib import *
spot, fut, fund = load_all()
UNI = [s for s in ALL if s in fut]
R = pd.DataFrame({s: fut[s]["c"].pct_change() for s in UNI})
F = pd.DataFrame({s: fund[s].reindex(R.index).fillna(0.0) for s in UNI})
def bot_trend(N=30, cost=7):
    pn = {}
    for s in UNI:
        sg = sig_tsm(fut[s], N=N, long_short=False); p, _ = run_pos(sg, R[s], cost, fund.get(s)); pn[s] = p
    return basket(pn)
def bot_trend_short(N=30, cost=7):
    pn = {}
    for s in UNI:
        sg = -sig_tsm(fut[s], N=N, long_short=True).clip(upper=0)*(-1)  # short-only: -1 when TSM<0
        sg = (sig_tsm(fut[s], N=N, long_short=True) < 0).astype(float) * -1.0
        p, _ = run_pos(sg, R[s], cost, fund.get(s)); pn[s] = p
    return basket(pn)
def bot_rs(N=28, cost=7, k=3, reb=7):
    ranks = (1 + R).rolling(N).apply(np.prod, raw=True) - 1
    W = pd.DataFrame(0.0, index=R.index, columns=R.columns); cur = pd.Series(0.0, index=R.columns)
    for i, d in enumerate(R.index):
        if i % reb == 0:
            r = ranks.loc[d].dropna()
            if len(r) >= 8:
                cur = pd.Series(0.0, index=R.columns); cur[r.nlargest(k).index] = 1.0 / k; cur[r.nsmallest(k).index] = -1.0 / k
        W.loc[d] = cur
    Wp = W.shift(1).fillna(0.0); turn = Wp.diff().abs().fillna(Wp.abs()).sum(axis=1)
    return (Wp * R.fillna(0.0)).sum(axis=1) - turn * cost / 1e4 - (Wp * F).sum(axis=1)
def bot_carry(theta=0.10, cost_leg=7.0, win=7):
    pn = {}
    for s in ALL:
        if not (s in fut and s in spot and s in fund): continue
        sr = spot[s]["c"].pct_change(); fr_ = fut[s]["c"].pct_change(); idx = fr_.index.intersection(sr.index)
        f = fund[s].reindex(idx).fillna(0.0); ann = f.rolling(win).mean() * 365
        pos = (ann > theta).astype(float).shift(1).fillna(0.0)
        hedged = sr.reindex(idx) - fr_.reindex(idx) + f; turn = pos.diff().abs().fillna(pos.abs())
        pn[s] = pos * hedged - turn * 2 * cost_leg / 1e4
    return pd.concat(pn, axis=1).mean(axis=1, skipna=True)
def bot_rev(k=2.5, hold=2, cost=7):
    pn = {}
    for s in UNI:
        sg = sig_reversal(fut[s], k=k, hold=hold); p, _ = run_pos(sg, R[s], cost, fund.get(s)); pn[s] = p
    return basket(pn)
def bot_gold(N=60, cost=10):
    g = spot["PAXGUSDT"]; rg = g["c"].pct_change(); sg = sig_tsm(g, N=N, long_short=False); p, _ = run_pos(sg, rg, cost); return p
