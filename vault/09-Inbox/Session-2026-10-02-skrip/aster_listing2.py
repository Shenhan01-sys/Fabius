# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/05 - Epik Enam Bot.md dan vault/09-Inbox/Session-2026-10-02.md).
# Bukan alat resmi; keluaran = bukan klaim produk. Unduhan masuk ./data/ (gitignored).
import json, time, urllib.request, concurrent.futures as cf, numpy as np, pandas as pd
UA = {"User-Agent": "Mozilla/5.0 (screening script)"}; B = "https://fapi.asterdex.com/fapi/v1"
def get(path, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(B + path, headers=UA), timeout=30) as r: return json.loads(r.read())
        except Exception: time.sleep(1 + i)
    return None
D0 = pd.read_csv("data/aster_listing_study.csv"); D0["d0"] = pd.to_datetime(D0.d0)
ei = get("/exchangeInfo"); ob = {s["symbol"]: int(s["onboardDate"]) for s in ei["symbols"] if s.get("onboardDate")}
def kl(sym): return sym, get(f"/klines?symbol={sym}&interval=1d&startTime={ob[sym]}&limit=45")
res = {}
with cf.ThreadPoolExecutor(max_workers=12) as ex:
    for sym, k in ex.map(kl, list(D0.sym)):
        if k and len(k) >= 31: res[sym] = k
print("sample", len(res))
def sim(H, stop, cost=0.01):
    out = []
    for sym, k in res.items():
        h = np.array([float(x[2]) for x in k]); c = np.array([float(x[4]) for x in k]); ent = c[0]
        pnl = None
        for i in range(1, H + 1):
            if stop is not None and h[i] >= ent * (1 + stop): pnl = -stop; break
        if pnl is None: pnl = (ent - c[H]) / ent
        out.append(pnl - cost)       # cost = 1% of notional round trip incl. slippage on a thin new perp (assumption)
    return np.array(out)
print(f"SHORT at day-1 close, simple return on notional, cost 1pct RT assumed (thin new perps) | n={len(res)}")
print(f"{'H':>3} {'stop':>6} {'mean%':>7} {'median%':>8} {'win%':>5} {'sd%':>6} {'t':>5} {'worst%':>7} {'p5%':>6} {'stopped%':>8}")
for H in (7, 14, 30):
    for stop in (0.3, 0.5, 0.9, None):
        x = sim(H, stop) * 100
        st = (x <= -(stop * 100 if stop else 999) - 0.5).mean() * 100 if stop else 0
        print(f"{H:>3} {('none' if stop is None else int(stop*100)):>6} {x.mean():7.1f} {np.median(x):8.1f} {np.mean(x>0)*100:5.0f} {x.std():6.1f} {x.mean()/(x.std()/np.sqrt(len(x))):5.1f} {x.min():7.1f} {np.percentile(x,5):6.1f} {st:8.0f}")
# portfolio sim: each trade sized w of equity, positions overlap by calendar; no stop but loss capped at -100% of notional
import collections
dates = pd.date_range("2025-01-01", "2026-09-30")
def port(H, stop, w):
    eq = 1.0; ev = collections.defaultdict(float); series = pd.Series(1.0, index=dates)
    trades = []
    for sym, k in res.items():
        d0 = pd.to_datetime(k[0][0], unit="ms").normalize(); h = np.array([float(x[2]) for x in k]); c = np.array([float(x[4]) for x in k]); ent = c[0]
        pnl = None; di = H
        for i in range(1, H + 1):
            if stop is not None and h[i] >= ent * (1 + stop): pnl = -stop; di = i; break
        if pnl is None: pnl = (ent - c[H]) / ent
        trades.append((d0 + pd.Timedelta(days=di), pnl - 0.01))
    # equity on each exit date (sequential compounding approximation with fixed fractional w)
    tr = sorted(trades); cur = 1.0; curve = {}
    for d, p in tr:
        cur *= (1 + w * max(p, -1.0)); curve[d] = cur
    s = pd.Series(curve).reindex(dates).ffill().fillna(1.0)
    r = s.pct_change().dropna()
    yrs = (dates[-1] - dates[0]).days / 365
    dd = (s / s.cummax() - 1).min()
    return s.iloc[-1] ** (1 / yrs) - 1, (r.mean() / r.std() * np.sqrt(365) if r.std() > 0 else np.nan), dd, len(tr)
print("\nPORTFOLIO of listing-short trades Jan-2025..Sep-2026 (fixed fraction w of equity per trade, 1% RT cost):")
for H, stop in [(30, None), (30, 0.9), (30, 0.5), (14, None), (14, 0.9)]:
    for w in (0.02, 0.05):
        cagr, sh, dd, n = port(H, stop, w); print(f"  H={H:2d} stop={'none' if stop is None else int(stop*100):>4} w={w*100:3.0f}%: CAGR {cagr*100:6.1f}%  maxDD {dd*100:6.1f}%  trades {n}")
