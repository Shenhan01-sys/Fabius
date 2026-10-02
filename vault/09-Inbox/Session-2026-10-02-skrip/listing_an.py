# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/05 - Epik Enam Bot.md dan vault/09-Inbox/Session-2026-10-02.md).
# Bukan alat resmi; keluaran = bukan klaim produk. Unduhan masuk ./data/ (gitignored).
import json, numpy as np, pandas as pd, datetime as dt
raw = json.load(open("data/listing_raw.json"))
btc = pd.read_csv("data/spot_BTCUSDT_1d.csv"); btc["d"] = pd.to_datetime(btc["t"], unit="ms").dt.normalize(); btc = btc.set_index("d")["c"]
rows = []
for s, r in raw.items():
    d0 = pd.to_datetime(r[0][0], unit="ms").normalize()
    if d0 < pd.Timestamp("2020-01-01") or d0 > pd.Timestamp("2026-07-15") or len(r) < 40: continue
    t = np.array([x[0] for x in r]); o = np.array([x[1] for x in r]); c = np.array([x[2] for x in r]); v = np.array([x[3] for x in r])
    qv1 = c[0] * v[0]
    rec = dict(sym=s, d0=d0, year=d0.year, qv1=qv1, pop=np.log(c[0] / o[0]) * 100)
    for k in (3, 7, 14, 30):
        if len(c) > k:
            dk = d0 + pd.Timedelta(days=k)
            try: mk = np.log(btc.loc[dk] / btc.loc[d0]) * 100
            except KeyError: mk = np.nan
            rec[f"r{k}"] = np.log(c[k] / c[0]) * 100; rec[f"a{k}"] = rec[f"r{k}"] - mk   # raw & BTC-adjusted
    rows.append(rec)
D = pd.DataFrame(rows)
print("listings analysed:", len(D), "| by year:", D.groupby("year").size().to_dict())
def summ(g, col):
    x = g[col].dropna(); 
    if len(x) < 8: return "   n<8"
    return f"n {len(x):3d} mean {x.mean():6.1f}% med {x.median():6.1f}% neg {np.mean(x<0)*100:3.0f}% t {x.mean()/(x.std()/np.sqrt(len(x))):5.1f}"
for flt, name in [(D.qv1 >= 2e6, "day-1 quote volume >= $2M"), (D.qv1 >= 2e7, "day-1 quote volume >= $20M (hot)")]:
    G = D[flt]
    print(f"\n=== {name}: {len(G)} listings ===")
    print("day-1 pop (open->close, %):", {int(y): round(g['pop'].mean(), 1) for y, g in G.groupby('year')})
    for k in (7, 14, 30):
        print(f"  BTC-adjusted return day-1 close -> day-{k} close:")
        for y, g in G.groupby("year"): print(f"    {int(y)}  {summ(g, f'a{k}')}")
        print(f"    ALL   {summ(G, f'a{k}')}")
