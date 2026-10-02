# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/05 - Epik Enam Bot.md dan vault/09-Inbox/Session-2026-10-02.md).
# Bukan alat resmi; keluaran = bukan klaim produk. Unduhan masuk ./data/ (gitignored).
"""Exploratory screening library (NOT part of the Fabius repo). Daily bars, long history, explicit costs.
Conventions: signal is computed at close of day d from data <= d; position applies to the return of day d+1.
pnl_d = pos_d*ret_d - |pos_d-pos_{d-1}|*cost_side - pos_d*funding_d   (funding: long pays positive rate)
"""
import os, numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
ALL = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "LINKUSDT", "LTCUSDT",
       "AVAXUSDT", "TRXUSDT", "DOTUSDT", "BCHUSDT", "ETCUSDT", "ATOMUSDT", "NEARUSDT"]


def _load(path):
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["t"], unit="ms", utc=True).dt.tz_localize(None).dt.normalize()
    return df.set_index("date")[["o", "h", "l", "c", "v"]].astype(float)


def load_all():
    spot, fut, fund = {}, {}, {}
    for s in ALL + ["PAXGUSDT"]:
        p = os.path.join(D, f"spot_{s}_1d.csv")
        if os.path.exists(p): spot[s] = _load(p)
        p = os.path.join(D, f"fut_{s}_1d.csv")
        if os.path.exists(p): fut[s] = _load(p)
        p = os.path.join(D, f"fund_{s}.csv")
        if os.path.exists(p):
            f = pd.read_csv(p)
            f["date"] = pd.to_datetime(f["t"], unit="ms", utc=True).dt.tz_localize(None).dt.normalize()
            fund[s] = f.groupby("date")["rate"].sum()
    return spot, fut, fund


def stats(pnl, ppy=365):
    pnl = pnl.dropna()
    if len(pnl) < 30:
        return dict(ann=np.nan, vol=np.nan, sharpe=np.nan, mdd=np.nan, n=len(pnl))
    m = pnl.mean() * ppy
    s = pnl.std() * np.sqrt(ppy)
    eq = (1 + pnl).cumprod()
    return dict(ann=m, vol=s, sharpe=(m / s if s > 0 else np.nan), mdd=float((eq / eq.cummax() - 1).min()), n=len(pnl))


def by_year(pnl):
    out = {}
    for y, g in pnl.dropna().groupby(pnl.dropna().index.year):
        if len(g) >= 60:
            s = g.std() * np.sqrt(365)
            out[int(y)] = round(g.mean() * 365 / s, 2) if s > 0 else np.nan
    return out


def run_pos(sig, ret, cost_side_bps, fund=None):
    """sig: signal series at close d (position to hold over d+1). ret: simple returns per day. Returns pnl series."""
    pos = sig.shift(1).reindex(ret.index).fillna(0.0)
    turn = pos.diff().abs().fillna(pos.abs())
    pnl = pos * ret - turn * cost_side_bps / 1e4
    if fund is not None:
        f = fund.reindex(ret.index).fillna(0.0)
        pnl = pnl - pos * f
    return pnl, pos


def basket(pnls):
    """equal-weight across assets available on each day (mean of non-NaN)."""
    df = pd.concat(pnls, axis=1)
    return df.mean(axis=1, skipna=True)


# ---------------- signals (each has ONE parameter) ----------------
def sig_donchian(df, N, long_short=True):
    c, h, l = df["c"], df["h"], df["l"]
    hi = h.shift(1).rolling(N).max()
    lo = l.shift(1).rolling(N).min()
    pos = np.zeros(len(c))
    cur = 0.0
    cv, hv, lv = c.values, hi.values, lo.values
    for i in range(len(c)):
        if not np.isnan(hv[i]):
            if cv[i] > hv[i]:
                cur = 1.0
            elif cv[i] < lv[i]:
                cur = -1.0 if long_short else 0.0
        pos[i] = cur
    return pd.Series(pos, index=c.index)


def sig_tsm(df, N, long_short=True):
    r = df["c"] / df["c"].shift(N) - 1
    s = np.sign(r)
    if not long_short:
        s = s.clip(lower=0)
    return s.fillna(0.0)


def sig_meanrev(df, N, z_in=2.0, long_short=True):
    c = df["c"]
    z = (c - c.rolling(N).mean()) / c.rolling(N).std()
    pos = np.zeros(len(c)); cur = 0.0
    zv = z.values
    for i in range(len(c)):
        if not np.isnan(zv[i]):
            if cur == 0.0:
                if zv[i] < -z_in: cur = 1.0
                elif zv[i] > z_in and long_short: cur = -1.0
            elif cur > 0 and zv[i] >= 0: cur = 0.0
            elif cur < 0 and zv[i] <= 0: cur = 0.0
        pos[i] = cur
    return pd.Series(pos, index=c.index)


def sig_reversal(df, k, hold=2):
    """Long after a 1-day drop worse than -k*sigma20 (sigma of daily returns); hold `hold` days."""
    r = df["c"].pct_change()
    sd = r.rolling(20).std().shift(1)
    trig = (r < -k * sd)
    pos = np.zeros(len(r)); left = 0
    tv = trig.values
    for i in range(len(r)):
        if tv[i] and left == 0: left = hold
        pos[i] = 1.0 if left > 0 else 0.0
        if left > 0: left -= 1
    return pd.Series(pos, index=r.index)
