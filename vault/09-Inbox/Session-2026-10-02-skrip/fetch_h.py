# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/05 - Epik Enam Bot.md dan vault/09-Inbox/Session-2026-10-02.md).
# Bukan alat resmi; keluaran = bukan klaim produk. Unduhan masuk ./data/ (gitignored).
import io, os, sys, time, zipfile, csv, urllib.request, urllib.error, concurrent.futures as cf, datetime as dt
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"); os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (screening script)"}
def get(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(1+i)
        except Exception: time.sleep(1+i)
    return None
def parse(blob):
    z = zipfile.ZipFile(io.BytesIO(blob)); rows = []
    with z.open(z.namelist()[0]) as f:
        for r in csv.reader(io.TextIOWrapper(f)):
            if not r or not r[0].strip().isdigit(): continue
            t = int(r[0]); t = t // 1000 if t > 10**14 else t
            rows.append((t, float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])))
    return rows
sym, iv = sys.argv[1], sys.argv[2]
months = [(y, m) for y in range(2020, 2027) for m in range(1, 13) if (y, m) <= (2026, 8)]
def job(ym):
    y, m = ym; b = get(f"https://data.binance.vision/data/spot/monthly/klines/{sym}/{iv}/{sym}-{iv}-{y}-{m:02d}.zip")
    return parse(b) if b else []
rows = []
with cf.ThreadPoolExecutor(max_workers=16) as ex:
    for r in ex.map(job, months): rows.extend(r)
rows.sort(); seen=set(); out=[]
for r in rows:
    if r[0] in seen: continue
    seen.add(r[0]); out.append(r)
with open(os.path.join(OUT, f"spot_{sym}_{iv}.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["t","o","h","l","c","v"]); w.writerows(out)
print(sym, iv, len(out), dt.datetime.fromtimestamp(out[0][0]/1000, dt.timezone.utc), "->", dt.datetime.fromtimestamp(out[-1][0]/1000, dt.timezone.utc))
