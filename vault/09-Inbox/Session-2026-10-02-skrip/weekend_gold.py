# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/05 - Epik Enam Bot.md dan vault/09-Inbox/Session-2026-10-02.md).
# Bukan alat resmi; keluaran = bukan klaim produk. Unduhan masuk ./data/ (gitignored).
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from zoneinfo import ZoneInfo
df = pd.read_csv("data/spot_PAXGUSDT_1h.csv")
df["ts"] = pd.to_datetime(df["t"], unit="ms", utc=True)
df = df.set_index("ts")
ny = df.copy(); ny.index = ny.index.tz_convert(ZoneInfo("America/New_York"))
op = ny["o"]    # price at the START of each hour (open)
# weekends: Friday 17:00 ET -> Sunday 18:00 ET (CME gold reopen), then next H hours
rows = []
for d in sorted(set(op.index.date)):
    d = pd.Timestamp(d)
    if d.dayofweek != 4: continue                      # Friday
    t_fri = pd.Timestamp(d.year, d.month, d.day, 17, tz=ZoneInfo("America/New_York"))
    sun = d + pd.Timedelta(days=2)
    t_sun = pd.Timestamp(sun.year, sun.month, sun.day, 18, tz=ZoneInfo("America/New_York"))
    try:
        p0 = op.loc[t_fri]; p1 = op.loc[t_sun]
        rec = dict(date=d, wk=np.log(p1 / p0) * 1e4)
        for H in (1, 2, 4, 8, 24):
            t2 = t_sun + pd.Timedelta(hours=H)
            rec[f"h{H}"] = np.log(op.loc[t2] / p1) * 1e4
        rows.append(rec)
    except KeyError:
        continue
W = pd.DataFrame(rows).set_index("date")
print("weekends:", len(W), W.index[0].date(), "->", W.index[-1].date(), "| mean |weekend move| bp:", round(W.wk.abs().mean(), 1), "median", round(W.wk.abs().median(), 1))
print("\nContinuation test: signal = sign(weekend move) ; PnL_H = sign * return over next H hours after Sun 18:00 ET (gross, bp)")
for H in (1, 2, 4, 8, 24):
    pnl = np.sign(W.wk) * W[f"h{H}"]; m = pnl.mean(); se = pnl.std() / np.sqrt(len(pnl))
    hit = (pnl > 0).mean(); big = W.wk.abs() > W.wk.abs().median(); pb = pnl[big]
    print(f"  H={H:2d}h: mean {m:6.2f} bp  t {m/se:5.2f}  hit {hit*100:4.1f}%  n {len(pnl)} | large-move half: mean {pb.mean():6.2f} t {pb.mean()/(pb.std()/np.sqrt(len(pb))):5.2f} | small half: {pnl[~big].mean():6.2f}")
print("\nBy year (H=4h): ", {int(y): (round(g.mean(), 1), len(g)) for y, g in (np.sign(W.wk) * W['h4']).groupby(W.index.year)})
print("Always-long baseline H=4h mean bp:", round(W['h4'].mean(), 2), "| sign-weighted by size (regression slope of h4 on weekend move):", round(np.polyfit(W.wk, W['h4'], 1)[0], 3))
# permutation test
rng = np.random.default_rng(0); x = (np.sign(W.wk) * W['h4']).values; obs = x.mean()
sims = [(rng.choice([-1, 1], size=len(x)) * np.abs(x)).mean() for _ in range(20000)]
print("one-sided permutation p (random sign):", round(float(np.mean(np.array(sims) >= obs)), 4))
# also Monday cash open gap proxy: sunday 18:00 -> monday 09:30 ET
