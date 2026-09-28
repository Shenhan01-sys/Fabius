"""P18 - ukur STRING MENTAH `price_usd` dari feed GMGN (sebelum `float()` menelannya).

Pertanyaan backlog: 21,6 % kejadian punya gross persis 0,0 bps ("harga diam") - pembulatan di
feed atau di penyimpanan kita? Setelah `float()` kita TIDAK bisa membedakan "feed mengirim
4.29e-06" dari "feed mengirim 4.293740471e-06", jadi probe ini mem-parse JSON dengan
`parse_float=str` dan memakai lapisan permintaan milik perekam sendiri (satu bentuk permintaan).

Yang diukur:
  A. digit yang benar-benar dikirim feed (median + distribusi)
  B. token yang string harganya IDENTIK antar dua tarikan berjarak ~75 s  -> lantai resolusi feed
  C. pembanding DexScreener pada detik yang sama (sumur kita vs sumur kedua)
"""
import json
import os
import statistics
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(R, "universe"))
import record_bsc_universe as rec  # noqa: E402  SATU sumber bentuk permintaan + kunci

UA = {"User-Agent": "Mozilla/5.0 (compatible; fabius-price-probe/1.0)",
      "X-APIKEY": rec.GMGN_KEY, "Accept": "application/json"}


def get_raw(url, timeout=30):
    t0 = time.time()
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        body = r.read()
    return json.loads(body.decode("utf-8", "replace"), parse_float=str), round(time.time() - t0, 2)


def digits_of(s):
    t = str(s).lower().split("e")[0].replace(".", "").replace("-", "").lstrip("0")
    return len(t.rstrip("0")) or 1


pulls = []
for k in range(3):
    url = rec.gmgn_url("/v1/user/smartmoney", chain="bsc", limit="100")
    j, dt = get_raw(url)
    lst = ((j.get("data") or {}).get("list")) or []
    snap = {}
    for row in lst:
        tk = str(row.get("base_address") or "").lower()
        p = row.get("price_usd")
        if tk and isinstance(p, str):
            snap[tk] = p
    pulls.append(snap)
    print("tarikan %d: %d baris list | %d token berharga | HTTP %.2f s | %s"
          % (k + 1, len(lst), len(snap), dt, time.strftime("%H:%M:%SZ", time.gmtime())))
    if k < 2:
        time.sleep(75)

dig = [digits_of(v) for s in pulls for v in s.values()]
print("\nA. digit yang DIKIRIM FEED: median %d | min %d | maks %d | distribusi %s"
      % (statistics.median(dig), min(dig), max(dig),
         dict(sorted({d: dig.count(d) for d in set(dig)}.items()))))

iris = set(pulls[0]) & set(pulls[2])
tetap = sum(1 for tk in iris if pulls[0][tk] == pulls[2][tk])
print("B. token muncul di tarikan 1 dan 3: %d | string harga IDENTIK: %d (%.1f %%)"
      % (len(iris), tetap, 100.0 * tetap / max(len(iris), 1)))
print("   -> ini lantai resolusi feed: pergerakan di bawahnya tidak akan pernah terlihat alat kami,"
      "\n      berapa pun bagus statistiknya. `harga diam` = konsekuensi yang terukur, bukan bug.")

print("\nC. sumur kedua pada detik yang sama (DexScreener):")
smp = [tk for tk in iris if digits_of(pulls[2][tk]) >= 4][:10]
try:
    j, dt = get_raw("https://api.dexscreener.com/tokens/v1/bsc/" + ",".join(smp))
    n = 0
    for p in j or []:
        tk = str((p.get("baseToken") or {}).get("address") or "").lower()
        if tk not in pulls[2]:
            continue
        ours, theirs = pulls[2][tk], str(p.get("priceUsd"))
        print("   %s | GMGN %-20s (%2d digit) | DEX %-12s (%d digit) | selisih %+7.3f %%"
              % (tk[:12], ours, digits_of(ours), theirs, digits_of(theirs),
                 100.0 * (float(theirs) - float(ours)) / float(ours)))
        n += 1
        if n >= 6:
            break
    if not n:
        print("   (tidak ada pasangan yang kembali)")
except Exception as e:
    print("   DexScreener gagal: %r" % e)
