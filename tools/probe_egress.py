"""Uji keterjangkauan sumber dari JARINGAN BERSIH - karena dari laptop builder 5 host terpotong TLS.

Kenapa file ini ada di repo, bukan cuma di _research: ia adalah alat bukti untuk satu kalimat di
README/vault. Dari mesin ini, `web3.binance.com`, `api.binance.com`, OKX, Bybit, Bitget membalas
`CERTIFICATE_VERIFY_FAILED: Hostname mismatch` - artinya intersepsi jaringan lokal, BUKAN servernya
mati. Kesimpulanku soal "sinyal smart-money Binance tidak terukur" bergantung pada itu. Satu-satunya
cara membedakan 'diblokir jaringan' dari 'memang tidak tersedia' adalah memanggil dari tempat lain,
dan GitHub Actions runner adalah tempat lain yang paling murah.

Read-only: GET/POST kecil, tidak ada order, tidak ada kunci wallet, tidak ada nilai rahasia dicetak.
Yang menarik perhatian: endpoint sinyal Binance ada di jalur `/public/` (cli.mjs resmi tidak
menyebut env var apa pun), jadi tidak perlu kunci.

Pakai: python tools/probe_egress.py         (di mana saja; di runner = yang sebenarnya penting)
"""
import json
import time
import urllib.error
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (compatible; fabius-egress-probe/1.0)", "Accept": "application/json"}

# (label, method, url, apa yang diharapkan)
TARGETS = [
    ("GMGN rank BSC", "GET",
     "https://openapi.gmgn.ai/v1/market/rank?chain=bsc&limit=2", "kontrol: harus hidup"),
    ("Binance smart-money signals (BSC)", "GET",
     "https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/web/"
     "signal/smart-money/ai?chainId=56&page=1&pageSize=5", "jalur /public/, tanpa kunci"),
    ("api.binance.com ticker", "GET",
     "https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT", "CEX reference"),
    ("OKX funding BNB", "GET",
     "https://www.okx.com/api/v5/public/funding-rate?instId=BNB-USDT-SWAP", "funding"),
    ("Bybit tickers linear", "GET",
     "https://api.bybit.com/v5/market/tickers?category=linear&symbol=BNBUSDT", "funding/OI"),
    ("Bitget contracts", "GET",
     "https://api.bitget.com/api/v2/mix/market/contracts?productType=usdt-futures", "CEX"),
    ("Hyperliquid metaAndAssetCtxs", "POST", "https://api.hyperliquid.xyz/info", "kontrol: keyless"),
    ("GDELT DOC API", "GET",
     "https://api.gdeltproject.org/api/v2/doc/doc?query=binance&mode=ARTFULLTEXT"
     "&maxrecords=2&format=json", "dulu 429 di sini"),
    ("GDELT files", "GET", "https://data.gdeltproject.org/gdeltv2/lastupdate.txt", "kontrol: hidup"),
    ("CryptoPanic public", "GET", "https://cryptopanic.com/api/v1/posts/?public=true", "dulu 403"),
]


def call(method, url, body=None):
    data = json.dumps(body).encode() if body else None
    h = dict(UA)
    if data:
        h["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:200]
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {str(e)[:150]}".encode()


print(f"egress probe dari: {__import__('platform').node()}")
print(f"{'sumber':34}{'status':>8}  yang terlihat")
print("-" * 96)
for label, method, url, note in TARGETS:
    if label.startswith("Hyperliquid"):
        st, body = call("POST", url, {"type": "metaAndAssetCtxs"})
        if st == 200:
            try:
                d = json.loads(body)
                uni = (d[0] or {}).get("universe") or []
                ctx = d[1] or []
                bnb = next((i for i, u in enumerate(uni) if u.get("name") == "BNB"), None)
                extra = f"perp={len(uni)}"
                if bnb is not None and bnb < len(ctx):
                    c = ctx[bnb]
                    fr = float(c.get("funding") or 0)
                    extra += f" BNB: OI={float(c.get('openInterest') or 0):,.0f} funding/jam={fr:.6%}"
                body = extra.encode()
            except Exception as e:  # noqa: BLE001
                body = f"parse gagal: {e}".encode()
    else:
        st, body = call(method, url)
    s = body.decode("utf-8", "replace") if isinstance(body, (bytes, bytearray)) else str(body)
    ringkas = s
    if st == 200:
        try:
            d = json.loads(s)
            if label.startswith("Binance smart-money"):
                dat = d.get("data") if isinstance(d, dict) else None
                rows = dat if isinstance(dat, list) else (
                    (dat or {}).get("list") or (dat or {}).get("records") or [] if isinstance(dat, dict) else [])
                n = len(rows) if isinstance(rows, list) else "?"
                ringkas = f"code={d.get('code')} jumlah_sinyal={n}"
                if isinstance(rows, list) and rows:
                    r0 = rows[0]
                    ringkas += f" | field={sorted(r0.keys())[:10]}"
                    st_set = {}
                    for r in rows:
                        k = str(r.get("status") or r.get("signalStatus") or "?")
                        st_set[k] = st_set.get(k, 0) + 1
                    ringkas += f" | status={st_set}"
                    ringkas += f" | contoh={json.dumps({k: r0.get(k) for k in list(r0)[:7]}, ensure_ascii=False)[:220]}"
            elif isinstance(d, dict):
                ringkas = f"keys={sorted(d.keys())[:6]}" + f" len={len(s)}B"
            else:
                ringkas = f"json len={len(s)}B"
        except Exception:
            ringkas = s[:150].replace("\n", " ")
    else:
        ringkas = s[:150].replace("\n", " ")
    print(f"{label:34}{str(st):>8}  {ringkas[:96]}")
    print(f"{'':34}{'':>8}  (diharapkan: {note})")
    time.sleep(1.0)

print(
    "\nCara membaca: 200 = terjangkau dari jaringan ini. `CERTIFICATE_VERIFY_FAILED: Hostname\n"
    "mismatch` = TERPOTONG oleh jaringan (bukan server mati). 401/403/404/429 = memang respons\n"
    "server. Jangan pernah menuliskan yang pertama sebagai 'sumber tidak tersedia'."
)
