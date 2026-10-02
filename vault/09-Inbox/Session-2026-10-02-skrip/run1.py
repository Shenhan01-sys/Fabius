# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/05 - Epik Enam Bot.md dan vault/09-Inbox/Session-2026-10-02.md).
# Bukan alat resmi; keluaran = bukan klaim produk. Unduhan masuk ./data/ (gitignored).
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from lib import *
spot, fut, fund = load_all()
UNI = [s for s in ALL if s in fut]
print("universe (perp):", len(UNI), "| BTC fut", fut["BTCUSDT"].index[0].date(), "->", fut["BTCUSDT"].index[-1].date())
ret = {s: fut[s]["c"].pct_change() for s in UNI}
def fr(s): return fund.get(s)
def evaluate(sigfn, cost, label, **kw):
    pn = {}; tn = {}
    for s in UNI:
        sg = sigfn(fut[s], **kw)
        p, pos = run_pos(sg, ret[s], cost, fr(s))
        pn[s] = p; tn[s] = pos.diff().abs().mean()*365
    b = basket(pn)
    st = stats(b)
    return b, st, np.nanmean(list(tn.values())), pn
# baselines
bh = {s: ret[s] - fund[s].reindex(ret[s].index).fillna(0.0) for s in UNI}
print("\nBASELINES (perp buy&hold incl. funding):")
st = stats(bh["BTCUSDT"]); print(f"  BTC B&H     sharpe {st['sharpe']:.2f} ann {st['ann']*100:5.1f}% mdd {st['mdd']*100:5.1f}%")
b = basket(bh); st = stats(b); print(f"  EW basket B&H sharpe {st['sharpe']:.2f} ann {st['ann']*100:5.1f}% mdd {st['mdd']*100:5.1f}%")
print("\nTREND family, basket (equal-weight over available perps). cost 7 bps/side; Sharpe at 15 bps/side in brackets")
print(f"{'method':22} {'N':>4} {'Sharpe':>7} {'(15bp)':>7} {'ann%':>6} {'mdd%':>6} {'turn/yr':>8} | by-year Sharpe")
for name, fn, kw_name in [("Donchian L/S", sig_donchian, "N"), ("Donchian L/F", sig_donchian, "N"),
                          ("TSM L/S", sig_tsm, "N"), ("TSM L/F", sig_tsm, "N")]:
    ls = name.endswith("L/S")
    grid = [20, 50, 100, 200] if name.startswith("Donchian") else [14, 30, 60, 90, 180]
    for N in grid:
        b7, st7, tu, _ = evaluate(fn, 7, name, N=N, long_short=ls)
        _, st15, _, _ = evaluate(fn, 15, name, N=N, long_short=ls)
        print(f"{name:22} {N:>4} {st7['sharpe']:7.2f} {st15['sharpe']:7.2f} {st7['ann']*100:6.1f} {st7['mdd']*100:6.1f} {tu:8.1f} | {by_year(b7)}")
