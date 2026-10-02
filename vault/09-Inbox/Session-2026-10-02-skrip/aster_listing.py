# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/05 - Epik Enam Bot.md dan vault/09-Inbox/Session-2026-10-02.md).
# Bukan alat resmi; keluaran = bukan klaim produk. Unduhan masuk ./data/ (gitignored).
import json, time, urllib.request, concurrent.futures as cf, datetime as dt, numpy as np, pandas as pd
UA = {"User-Agent": "Mozilla/5.0 (screening script)"}; B = "https://fapi.asterdex.com/fapi/v1"
def get(path, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(B + path, headers=UA), timeout=30) as r: return json.loads(r.read())
        except Exception: time.sleep(1 + i)
    return None
ei = get("/exchangeInfo")
syms = ei["symbols"]
print("aster symbols:", len(syms), "| keys sample:", list(syms[0].keys())[:14])
rows = []
for s in syms:
    if s.get("quoteAsset") != "USDT": continue
    ob = s.get("onboardDate")
    if not ob: continue
    rows.append((s["symbol"], int(ob), s.get("status")))
df = pd.DataFrame(rows, columns=["sym", "ob", "status"]); df["obd"] = pd.to_datetime(df.ob, unit="ms")
print("USDT symbols with onboardDate:", len(df), "| by year:", df.groupby(df.obd.dt.year).size().to_dict())
# Cross-match with Binance spot first listing date
raw = json.load(open("data/listing_raw.json"))
bn = {s: pd.to_datetime(r[0][0], unit="ms").normalize() for s, r in raw.items()}
m = df[df.sym.isin(bn.keys())].copy(); m["bn"] = m.sym.map(bn)
m["lag_days"] = (m.obd.dt.normalize() - m.bn).dt.days
mm = m[(m.bn >= pd.Timestamp("2024-06-01"))]
print("\nTokens listed on Binance spot since 2024-06 that also have an Aster perp:", len(mm))
if len(mm): print("lag (Aster perp onboard - Binance spot listing), days: median", mm.lag_days.median(), "p25", mm.lag_days.quantile(.25), "p75", mm.lag_days.quantile(.75), "| share <=7d:", round((mm.lag_days <= 7).mean() * 100), "% | share <=0d (perp first):", round((mm.lag_days <= 0).mean() * 100), "%")
# Direct perp-based test: Aster perps onboarded since 2025-01-01
tgt = df[(df.obd >= pd.Timestamp("2025-01-01")) & (df.obd <= pd.Timestamp("2026-08-25"))]
def kl(sym, ob):
    k = get(f"/klines?symbol={sym}&interval=1d&startTime={ob}&limit=45")
    return sym, k
res = {}
with cf.ThreadPoolExecutor(max_workers=12) as ex:
    for sym, k in ex.map(lambda r: kl(r.sym, r.ob), tgt.itertuples()):
        if k and len(k) >= 31: res[sym] = k
print("\nAster perps with >=31 daily bars since onboard (onboard 2025-01..2026-08):", len(res))
btc = get("/klines?symbol=BTCUSDT&interval=1d&startTime=1735689600000&limit=800")
bt = pd.Series({pd.to_datetime(x[0], unit="ms").normalize(): float(x[4]) for x in btc})
out = []
for sym, k in res.items():
    o = np.array([float(x[1]) for x in k]); h = np.array([float(x[2]) for x in k]); c = np.array([float(x[4]) for x in k]); qv = np.array([float(x[7]) for x in k])
    d0 = pd.to_datetime(k[0][0], unit="ms").normalize()
    rec = dict(sym=sym, d0=d0, qv1=qv[0], pop=np.log(c[0] / o[0]) * 100)
    for H in (7, 14, 30):
        dk = d0 + pd.Timedelta(days=H)
        try: mk = np.log(bt.loc[dk] / bt.loc[d0]) * 100
        except KeyError: mk = np.nan
        rec[f"r{H}"] = np.log(c[H] / c[0]) * 100; rec[f"a{H}"] = rec[f"r{H}"] - mk
    # short with stop: entry day-1 close, stop if a later daily HIGH >= entry*(1+s); exit day-H close
    for s_ in (0.3, 0.5):
        for H in (14, 30):
            ent = c[0]; pnl = None
            for i in range(1, H + 1):
                if h[i] >= ent * (1 + s_): pnl = -s_; break
            if pnl is None: pnl = (ent - c[H]) / ent
            rec[f"sp_s{int(s_*100)}_H{H}"] = pnl * 100
    out.append(rec)
D = pd.DataFrame(out)
D = D[D.qv1 >= 1e6]
print("tradable-venue sample (day-1 quote vol >= $1M):", len(D))
def t(x): x = x.dropna(); return f"n {len(x)} mean {x.mean():6.1f}% med {x.median():6.1f}% neg {np.mean(x<0)*100:3.0f}% t {x.mean()/(x.std()/np.sqrt(len(x))):5.1f}"
print("day-1 pop (open->close):", round(D["pop"].mean(), 1), "%")
for H in (7, 14, 30): print(f"  BTC-adj return day-1 close -> day-{H}: {t(D[f'a{H}'])}")
print("\nSHORT PnL per trade (%, notional), entry day-1 close, with close-to-high stop:")
for k in [c for c in D.columns if c.startswith("sp_")]:
    x = D[k]; print(f"  {k}: mean {x.mean():5.1f}%  median {x.median():5.1f}%  win {np.mean(x>0)*100:3.0f}%  worst {x.min():6.1f}%  stopped {np.mean(x<=-(int(k.split('_s')[1].split('_')[0])-0.01))*100:3.0f}%  t {x.mean()/(x.std()/np.sqrt(len(x))):4.1f}")
print("\nby onboard half-year (a30):", {f"{y}H{h}": (len(g), round(g['a30'].mean(), 1)) for (y, h), g in D.groupby([D.d0.dt.year, (D.d0.dt.month > 6).astype(int) + 1])})
D.to_csv("data/aster_listing_study.csv", index=False)
