"""Uji keterjangkauan sumber dari JARINGAN BERSIH - dan panggil tiap API sesuaikontrak aslinya.

Kenapa file ini ada di repo: ia alat bukti untuk kalimat di README/vault. Dari laptop builder,
`api.binance.com` / `web3.binance.com` / OKX / Bybit / Bitget membalas
`CERTIFICATE_VERIFY_FAILED: Hostname mismatch` = intersepsi jaringan lokal, BUKAN layanan mati.
Satu-satunya cara membedakan "diblokir jaringan" dari "memang tidak ada" adalah memanggil dari
tempat lain - dan runner GitHub adalah yang paling murah.

Dua perbaikan setelah jalanan pertama (24 Sep 02:46Z), keduanya salahku:
  1. GMGN dibaratkan GET polos -> 401 "missing api key or client_id". Route GMGN butuh
     `timestamp` + `client_id` di query, jadi URL-nya SEKARANG dirakit oleh fungsi milik
     perekam (`gmgn_url`) - satu sumber kebenaran, bukan dua rakitan yang bisa berbeda.
  2. `smart-money` Binance adalah POST dengan body JSON + header `content-type` + UA khusus,
     bukan GET -> 400 "illegal parameter" kemarin itu salahku, bukan Binance-nya.

Read-only terhadap data publik: tidak ada order, tidak ada kunci wallet, tidak ada rahasia dicetak.
Pakai: python tools/probe_egress.py
"""
import importlib.util
import json
import os
import platform
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# URL GMGN dibangun lewat fungsi perekam, supaya yang diuji adalah jalur yang sama.
_spec = importlib.util.spec_from_file_location(
    "rec", os.path.join(ROOT, "universe", "record_bsc_universe.py"))
_rec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rec)

UA = {"User-Agent": "Mozilla/5.0 (compatible; fabius-egress-probe/1.0)", "Accept": "application/json"}
BINANCE_SM = ("https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/"
              "signal/smart-money/ai")
BINANCE_UA = {"User-Agent": "binance-web3/2.0 (Skill)", "Accept-Encoding": "identity",
              "content-type": "application/json"}

TARGETS = [
    # label, method, url, body/None, headers/None, harapan
    ("GMGN rank BSC (via gmgn_url)", "GET",
     _rec.gmgn_url("/v1/market/rank", chain="bsc", limit=2), None,
     {"X-APIKEY": _rec.GMGN_KEY}, "kontrol: harus hidup, kunci dari konfigurasi perekam"),
    ("Binance smart-money POST BSC", "POST", BINANCE_SM,
     {"chainId": "56", "page": 1, "pageSize": 5}, BINANCE_UA, "jalur /public/, tanpa kunci"),
    ("api.binance.com ticker", "GET",
     "https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT", None, None, "CEX reference"),
    ("OKX funding BNB", "GET",
     "https://www.okx.com/api/v5/public/funding-rate?instId=BNB-USDT-SWAP", None, None, "funding"),
    ("Bybit tickers linear", "GET",
     "https://api.bybit.com/v5/market/tickers?category=linear&symbol=BNBUSDT", None, None, "funding/OI"),
    ("Bitget futures contracts", "GET",
     "https://api.bitget.com/api/v2/mix/market/contracts?productType=usdt-futures", None, None, "CEX"),
    ("Hyperliquid metaAndAssetCtxs", "POST", "https://api.hyperliquid.xyz/info",
     {"type": "metaAndAssetCtxs"}, None, "kontrol: keyless"),
    ("GDELT DOC API", "GET",
     "https://api.gdeltproject.org/api/v2/doc/doc?query=binance&mode=ARTFULLTEXT"
     "&maxrecords=2&format=json", None, None, "dulu 429 di laptop; apa di runner?"),
    ("GDELT files", "GET", "https://data.gdeltproject.org/gdeltv2/lastupdate.txt", None, None,
     "kontrol: hidup"),
    ("CryptoPanic public", "GET", "https://cryptopanic.com/api/v1/posts/?public=true", None, None,
     "dulu 403"),
]


def call(method, url, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    h = dict(UA)
    if headers:
        h.update(headers)
    if data:
        h.setdefault("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:400]
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {str(e)[:150]}".encode()


def describe(label, st, body):
    s = body.decode("utf-8", "replace") if isinstance(body, (bytes, bytearray)) else str(body)
    if st != 200:
        return s[:150].replace("\n", " ")
    if label.startswith("GDELT files"):
        return s.strip().replace("\n", "  |  ")[:150]
    try:
        d = json.loads(s)
    except Exception:
        return f"200 tapi bukan JSON ({len(s)}B)"
    if isinstance(d, dict):
        if label.startswith("Binance smart-money"):
            dat = d.get("data")
            rows = dat if isinstance(dat, list) else ((dat or {}).get("list") if isinstance(dat, dict) else None)
            out = f"code={d.get('code')} msg={d.get('message')} jumlah={len(rows) if isinstance(rows, list) else '?'}"
            if isinstance(rows, list) and rows:
                st_set = {}
                for r in rows:
                    k = str(r.get("status") or r.get("signalStatus") or "?")
                    st_set[k] = st_set.get(k, 0) + 1
                out += f" status={st_set} field={sorted(rows[0].keys())[:12]}"
            return out[:400]
        if label.startswith("Hyperliquid"):
            uni = (d[0] or {}).get("universe") if isinstance(d, list) else None
            ctx = d[1] if isinstance(d, list) else None
            if uni and ctx:
                i = next((j for j, u in enumerate(uni) if u.get("name") == "BNB"), None)
                extra = f"perp={len(uni)}"
                if i is not None and i < len(ctx):
                    c = ctx[i]
                    extra += (f" BNB: OI={float(c.get('openInterest') or 0):,.0f}"
                              f" funding/jam={float(c.get('funding') or 0):.6%}")
                return extra
        return f"keys={sorted(d.keys())[:6]} {len(s)}B"
    return f"json {len(s)}B"


print(f"egress probe dari host: {platform.node()}")
print(f"kunci GMGN yang dipakai: {'demo key publik' if _rec.GMGN_KEY == 'gmgn_solbscbaseethmonadtron' else 'api key pribadi'}")
print("-" * 100)
for label, method, url, body, headers, hope in TARGETS:
    st, raw = call(method, url, body, headers)
    print(f"{label:36}{str(st):>6}  {describe(label, st, raw)[:96]}")
    print(f"{'':36}{'':>6}  harapan: {hope}")
    time.sleep(1.0)

print(
    "\nCara membaca: 200 = terjangkau. `CERTIFICATE_VERIFY_FAILED: Hostname mismatch` = TERPOTONG\n"
    "oleh jaringan kita (bukan server mati). 451/403 geo = memang kebijakan pihak host. 400 dengan\n"
    "pesan server = endpointnya HIDUP, requestnya yang salah. Jangan tertukar ketiganya."
)
