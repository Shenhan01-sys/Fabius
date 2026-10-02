# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/05 - Epik Enam Bot.md dan vault/09-Inbox/Session-2026-10-02.md).
# Bukan alat resmi; keluaran = bukan klaim produk. Unduhan masuk ./data/ (gitignored).
"""Fetch long-history crypto data from data.binance.vision (static files, keyless).
Exploratory screening only (not part of the Fabius repo). Output: ./data/*.csv
"""
import io, os, sys, time, zipfile, csv, urllib.request, urllib.error, concurrent.futures as cf, datetime as dt

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (screening script)"}
BASE = "https://data.binance.vision/data"

SYMS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT",
        "LINKUSDT", "LTCUSDT", "AVAXUSDT", "TRXUSDT", "DOTUSDT", "BCHUSDT", "ETCUSDT", "ATOMUSDT", "NEARUSDT", "PAXGUSDT"]
START = (2019, 9)
END = (2026, 8)


def months():
    y, m = START
    while (y, m) <= END:
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(1 + i)
        except Exception:
            time.sleep(1 + i)
    return None


def parse_zip(blob, kind):
    z = zipfile.ZipFile(io.BytesIO(blob))
    name = z.namelist()[0]
    rows = []
    with z.open(name) as f:
        rd = csv.reader(io.TextIOWrapper(f))
        for r in rd:
            if not r or not r[0].strip().lstrip("-").isdigit():
                continue  # header
            if kind == "kline":
                t = int(r[0])
                if t > 10**14:
                    t //= 1000  # microseconds -> ms (spot since 2025)
                rows.append((t, float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])))
            else:  # funding: calc_time, interval_hours, last_funding_rate
                t = int(r[0])
                if t > 10**14:
                    t //= 1000
                rows.append((t, float(r[2])))
    return rows


def job(args):
    market, kind, sym, iv, y, m = args
    if kind == "kline":
        url = f"{BASE}/{market}/monthly/klines/{sym}/{iv}/{sym}-{iv}-{y}-{m:02d}.zip"
    else:
        url = f"{BASE}/{market}/monthly/fundingRate/{sym}/{sym}-fundingRate-{y}-{m:02d}.zip"
    blob = get(url)
    if blob is None:
        return args, None
    try:
        return args, parse_zip(blob, kind)
    except Exception as e:
        return args, None


def run(market, kind, iv, tag):
    jobs = [(market, kind, s, iv, y, m) for s in SYMS for (y, m) in months()]
    res = {}
    with cf.ThreadPoolExecutor(max_workers=24) as ex:
        for args, rows in ex.map(job, jobs):
            if rows:
                res.setdefault(args[2], []).extend(rows)
    for s, rows in res.items():
        rows.sort()
        # dedupe by time
        seen = set(); out = []
        for r in rows:
            if r[0] in seen:
                continue
            seen.add(r[0]); out.append(r)
        p = os.path.join(OUT, f"{tag}_{s}_{iv}.csv" if kind == "kline" else f"{tag}_{s}.csv")
        with open(p, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["t", "o", "h", "l", "c", "v"] if kind == "kline" else ["t", "rate"])
            w.writerows(out)
        print(tag, s, len(out), dt.datetime.fromtimestamp(out[0][0] / 1000, dt.timezone.utc).date(),
              "->", dt.datetime.fromtimestamp(out[-1][0] / 1000, dt.timezone.utc).date(), flush=True)




if __name__ == "__main__":
    what = sys.argv[1:] or ["spot1d", "fut1d", "fund"]
    t0 = time.time()
    if "spot1d" in what: run("spot", "kline", "1d", "spot")
    if "fut1d" in what: run("futures/um", "kline", "1d", "fut")
    if "fund" in what: run("futures/um", "fund", None, "fund")
    print("done in", round(time.time() - t0), "s")
