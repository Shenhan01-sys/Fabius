"""Uji hipotesis "px GMGN itu cache, bukan harga kini" dengan pembanding yang BERGERAK.

Kenapa ini penting: `tools/flow_cluster_test.py` dan `tools/evidence_stack.py` memakai baris `px`
sebagai harga kedua ujung outcome. Kalau `px` sebenarnya nilai yang di-cache per pool (tidak
berubah tiap tarikan), maka median outcome kami TEREDEM ke nol - dan itu bisa menjelaskan kenapa
beberapa aspek hasilnya persis 0,0 bps. Terukur 28 Sep 09:15-09:18Z: 17 dari 26 token (65,4 %)
punya string `price_usd` IDENTIK antar tarikan 2,5 menit, padahal feed mengirim 15-17 digit -
jadi bukan pembulatan.

Yang diukur di sini:
  1. field apa saja yang ikut bergerak (cari timestamp harga di dalam row)
  2. untuk token yang sama, apakah px-GMGN diam sementara DexScreener bergerak (dan sebaliknya)
  3. berapa lama satu nilai bertahan (berapa siklus berturut-turut string-nya sama)
"""
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(R, "universe"))
import record_bsc_universe as rec  # noqa: E402

GM = {"User-Agent": "Mozilla/5.0 (compatible; fabius-price-probe/1.0)",
      "X-APIKEY": rec.GMGN_KEY, "Accept": "application/json"}
DS = {"User-Agent": "Mozilla/5.0 (compatible; fabius-watch-recorder/1.0)",
      "Accept": "application/json"}


def raw(url, hdr, timeout=30):
    t0 = time.time()
    with urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=timeout) as r:
        b = r.read()
    return json.loads(b.decode("utf-8", "replace"), parse_float=str), round(time.time() - t0, 2)


print("=== 1. satu row mentah: field apa yang ada, mana yang punya waktu sendiri ===")
j, dt = raw(rec.gmgn_url("/v1/user/smartmoney", chain="bsc", limit="100"), GM)
lst = ((j.get("data") or {}).get("list")) or []
row = lst[0] if lst else {}
for k in sorted(row):
    v = row[k]
    if isinstance(v, dict):
        print("   %-26s dict: %s" % (k, {kk: vv for kk, vv in list(v.items())[:6]}))
    else:
        print("   %-26s %s" % (k, str(v)[:60]))

print("\n=== 2/3. dua tarikan GMGN + dua tarikan DexScreener, selang 90-an detik ===")
his_gm = {}
his_ds = {}
for k in range(2):
    j, dt = raw(rec.gmgn_url("/v1/user/smartmoney", chain="bsc", limit="100"), GM)
    g = {str(r0.get("base_address") or "").lower(): str(r0.get("price_usd"))
         for r0 in ((j.get("data") or {}).get("list") or []) if r0.get("base_address")}
    for tk, v in g.items():
        his_gm.setdefault(tk, []).append(v)
    addrs = [tk for tk in g if tk][:30]
    try:
        jd, dt2 = raw("https://api.dexscreener.com/tokens/v1/bsc/" + ",".join(addrs), DS)
    except Exception as e:
        print("   DexScreener tarikan %d gagal: %r" % (k + 1, e))
        jd = []
    for p in jd or []:
        tk = str((p.get("baseToken") or {}).get("address") or "").lower()
        pv = p.get("priceUsd")
        if tk and pv is not None:
            his_ds.setdefault(tk, []).append(str(pv))
    print("   tarikan %d: GMGN %d token (%.2f s) | DEX %d nilai (%.2f s) | %s"
          % (k + 1, len(g), dt, len(jd or []), dt2, time.strftime("%H:%M:%SZ", time.gmtime())))
    if k == 0:
        time.sleep(90)

diam_gm = [tk for tk, v in his_gm.items() if len(v) == 2 and v[0] == v[1]]
gerak_ds = [tk for tk, v in his_ds.items() if len(v) == 2 and v[0] != v[1]]
both = set(diam_gm) & set(his_ds)
diam_saja = [tk for tk in both if len(his_ds[tk]) == 2 and his_ds[tk][0] != his_ds[tk][1]]
print("\n   GMGN string sama 2 tarikan berturut : %d token" % len(diam_gm))
print("   DEX  string berubah 2 tarikan        : %d token" % len(gerak_ds))
print("   IRISAN yang diam di GMGN tapi bergerak di DEX: %d dari %d" % (len(diam_saja), len(both)))
for tk in diam_saja[:8]:
    print("      %s GMGN %s == %s | DEX %s -> %s" % (tk[:12], his_gm[tk][0], his_gm[tk][1],
                                                     his_ds[tk][0], his_ds[tk][1]))
lama = sorted({len(v) for v in his_gm.values()})
print("   panjang seri per token (GMGN): %s" % lama)
