# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/05 - Epik Enam Bot.md dan vault/09-Inbox/Session-2026-10-02.md).
# Bukan alat resmi; keluaran = bukan klaim produk. Unduhan masuk ./data/ (gitignored).
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from lib import *
spot, fut, fund = load_all()
UNI = [s for s in ALL if s in fut and s in spot and s in fund]
print("carry universe:", len(UNI))
def carry(theta, cost_leg=7.0, win=7):
    pn = {}; act = {}
    for s in UNI:
        sr = spot[s]["c"].pct_change(); fr_ = fut[s]["c"].pct_change()
        idx = fr_.index.intersection(sr.index)
        f = fund[s].reindex(idx).fillna(0.0)
        ann = f.rolling(win).mean() * 365
        sig = (ann > theta).astype(float)
        pos = sig.shift(1).fillna(0.0)
        hedged = sr.reindex(idx) - fr_.reindex(idx) + f      # long spot, short perp: receive funding
        turn = pos.diff().abs().fillna(pos.abs())
        pnl = pos * hedged - turn * 2 * cost_leg / 1e4       # two legs each way
        pn[s] = pnl; act[s] = pos.mean()
    df = pd.concat(pn, axis=1)
    b = df.mean(axis=1, skipna=True)                          # capital split equally across assets, idle when flat
    return b, np.mean(list(act.values())), df
print("\nCARRY (long spot + short perp when trailing-7d funding annualized > theta; 2 legs x 7 bps/side):")
for th in [0.05, 0.10, 0.20, 0.30]:
    b, a, _ = carry(th); b15, _, _ = carry(th, 15.0)
    s, s15 = stats(b), stats(b15)
    print(f"  theta={th*100:4.0f}%  sharpe {s['sharpe']:5.2f} (15bp {s15['sharpe']:5.2f}) ann {s['ann']*100:5.1f}% mdd {s['mdd']*100:6.1f}% active {a*100:4.0f}% of days | {by_year(b)}")
print("  reference: 'always on' (theta=-inf):", end=" ")
b, a, _ = carry(-9.0); s = stats(b); print(f"sharpe {s['sharpe']:.2f} ann {s['ann']*100:.1f}% mdd {s['mdd']*100:.1f}% | {by_year(b)}")
print("\nVOL-MANAGED BTC (perp): exposure = clip(T / vol20_ann, 0, 1.5); cost 7 bps/side; funding incl.")
ret = fut["BTCUSDT"]["c"].pct_change(); f = fund["BTCUSDT"]
vol = ret.rolling(20).std() * np.sqrt(365)
for T in [0.30, 0.40, 0.60]:
    expo = (T / vol).clip(0, 1.5)
    p, pos = run_pos(expo, ret, 7, f); s = stats(p)
    print(f"  T={T*100:3.0f}%  sharpe {s['sharpe']:5.2f} ann {s['ann']*100:5.1f}% mdd {s['mdd']*100:6.1f}% avg exposure {pos.mean():.2f} | {by_year(p)}")
bh = ret - f.reindex(ret.index).fillna(0); s = stats(bh)
print(f"  BTC B&H     sharpe {s['sharpe']:5.2f} ann {s['ann']*100:5.1f}% mdd {s['mdd']*100:6.1f}% | {by_year(bh)}")
print("\nGOLD (PAXG spot, long/flat; cost 10 bps/side):")
g = spot["PAXGUSDT"]; rg = g["c"].pct_change()
bhg = stats(rg); print(f"  PAXG B&H  sharpe {bhg['sharpe']:.2f} ann {bhg['ann']*100:.1f}% mdd {bhg['mdd']*100:.1f}% ({g.index[0].date()} -> {g.index[-1].date()}) | {by_year(rg)}")
for nm, fn, grid in [("Donchian", sig_donchian, [20, 50, 100, 200]), ("TSM", sig_tsm, [30, 60, 90, 180])]:
    for N in grid:
        sg = fn(g, N=N, long_short=False); p, pos = run_pos(sg, rg, 10); s = stats(p)
        print(f"  {nm:9} L/F N={N:3}: sharpe {s['sharpe']:5.2f} ann {s['ann']*100:5.1f}% mdd {s['mdd']*100:6.1f}% in-mkt {pos.mean()*100:3.0f}% | {by_year(p)}")
print("  gold vs BTC daily-return correlation:", round(rg.corr(spot['BTCUSDT']['c'].pct_change()), 3))
