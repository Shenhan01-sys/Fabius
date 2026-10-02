# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/05 - Epik Enam Bot.md dan vault/09-Inbox/Session-2026-10-02.md).
# Bukan alat resmi; keluaran = bukan klaim produk. Unduhan masuk ./data/ (gitignored).
import io, re, os, sys, time, zipfile, csv, json, urllib.request, urllib.error, concurrent.futures as cf, datetime as dt
import numpy as np, pandas as pd
UA = {"User-Agent": "Mozilla/5.0 (screening script)"}
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
def get(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(1 + i)
        except Exception: time.sleep(1 + i)
    return None
def list_prefixes(prefix):
    out, marker = [], ""
    while True:
        u = f"{S3}?delimiter=/&prefix={prefix}&max-keys=1000" + (f"&marker={marker}" if marker else "")
        x = get(u)
        if not x: break
        s = x.decode()
        out += re.findall(r"<CommonPrefixes><Prefix>([^<]+)</Prefix>", s)
        if "<IsTruncated>true</IsTruncated>" in s:
            m = re.search(r"<NextMarker>([^<]+)</NextMarker>", s); marker = m.group(1) if m else ""
            if not marker: break
        else: break
    return out
def list_keys(prefix):
    x = get(f"{S3}?prefix={prefix}&max-keys=200")
    return re.findall(r"<Key>([^<]+\.zip)</Key>", x.decode()) if x else []
def parse(blob):
    z = zipfile.ZipFile(io.BytesIO(blob)); rows = []
    with z.open(z.namelist()[0]) as f:
        for r in csv.reader(io.TextIOWrapper(f)):
            if not r or not r[0].strip().isdigit(): continue
            t = int(r[0]); t = t // 1000 if t > 10**14 else t
            rows.append((t, float(r[1]), float(r[4]), float(r[5])))   # t, open, close, base volume
    return rows
pref = list_prefixes("data/spot/monthly/klines/")
syms = [p.split("/")[-2] for p in pref]
bad = re.compile(r"(UP|DOWN|BULL|BEAR)USDT$")
stable = ("USDC", "TUSD", "BUSD", "FDUSD", "USDP", "DAI", "EUR", "GBP", "AUD", "BRL", "TRY", "USTC", "UST", "USDS", "PAX", "XUSD", "AEUR", "USD1", "RLUSD", "USDE")
cand = [s for s in syms if s.endswith("USDT") and not bad.search(s) and not s[:-4].startswith(stable) and s[:-4] not in ("USD", "BIDR", "NGN", "ZAR", "UAH", "IDRT")]
print("symbols total", len(syms), "USDT candidates", len(cand), flush=True)
def job(s):
    keys = sorted(k for k in list_keys(f"data/spot/monthly/klines/{s}/1d/"))
    if not keys: return s, None
    rows = []
    for k in keys[:3]:
        b = get(f"https://data.binance.vision/{k}")
        if b: rows += parse(b)
    rows.sort()
    return s, rows
res = {}
t0 = time.time()
with cf.ThreadPoolExecutor(max_workers=24) as ex:
    for s, rows in ex.map(job, cand):
        if rows: res[s] = rows
print("fetched", len(res), "in", round(time.time() - t0), "s", flush=True)
json.dump(res, open("data/listing_raw.json", "w"))
