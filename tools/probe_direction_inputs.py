"""Uji bahan baku lapisan ARAH (long/short) + endpoint Jev gratis, sekali jalan.

Kenapa urutan ini: lapisan arah butuh deret harga yang CUKUP untuk divalidasi, dan kodenya
mengandung aturan yang harus dibuktikan dulu, bukan diasumsikan. Tiga pertanyaan yang dijawab
file ini dengan angka:

 A. Berapa bar HOURLY yang benar-benar bisa didapat untuk tiap kandidat, lewat 3 jalur berbeda?
    (GMGN token_kline, GeckoTerminal ohlcv, Hyperliquid candleSnapshot untuk perp)
    Aturan validasi kita butuh >=20 trade OOS non-overlap 24 jam => secara kasar ~125 bar harian
    ATAU ~3.000 bar hourly. Di bawah itu, "entry/stop/target" adalah cerita, bukan uji.
 B. Apakah BISA Dijual? Aturan pengguna "jual saja waktu menyentuh 0" mengasumsikan exit selalu
    mungkin. Untuk token yang rug, asumsi itu salah: honeypot / can_not_sell / LP ditarik.
    Jadi kami uji dulu: field mana yang benar-benar melaporkan itu, dan berapa kandidat yang
    lolos gerbang "bisa keluar" SEBELUM bicara stop loss.
 C. Apakah endpoint gratis bynara benar-benar melayani kontrak Jev yang sama?
    (state + questions bertipe -> jawaban berisi angka)

Read-only terhadap pasar: hanya GET/POST baca, satu panggilan model. Tidak ada order, tidak ada
tx, tidak ada dana. Nilai API key tidak dicetak penuh.
Pakai: python tools/probe_direction_inputs.py
"""
import json
import os
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# konfigurasi perekam dipakai ulang, bukan disalin
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("rec", os.path.join(ROOT, "universe", "record_bsc_universe.py"))
rec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rec)

BYNARA = os.environ.get("JEV_BASE_URL") or "https://router.bynara.id"
BYNARA_KEY = os.environ.get("JEV_API_KEY") or ""

CAKE = "0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82"
WBNB = "0xbb4cdb9cbd36b01bd1cbaebf2b11df8f8e6e2b34"
HL_INFO = "https://api.hyperliquid.xyz/info"

# ambang yang kita pakai sendiri (lihat vault/02-Ambang.md)
NEED_HOURLY_FOR_20_TRADES = 20 * 24 * 2 + 24 * 60   # trade 24 jam non-overlap + seed 60 hari


def get(url, headers=None, timeout=30):
    h = dict(rec.UA)
    h.update(headers or {})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:220]
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {str(e)[:150]}".encode()


def post(url, payload, headers=None, timeout=40):
    h = {"Content-Type": "application/json", "Accept": "application/json",
         "User-Agent": "lencana-direction-probe/1.0"}
    h.update(headers or {})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=json.dumps(payload).encode(),
                                                           headers=h), timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:260]
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {str(e)[:200]}"


print("=== A. Kedalaman bar HOURLY, tiga jalur, untuk aset yang sama ===")
for label, addr in (("CAKE", CAKE), ("WBNB", WBNB)):
    st, raw = get(rec.gmgn_url("/v1/market/token_kline", chain="bsc", address=addr,
                               resolution="1h", limit=2000), {"X-APIKEY": rec.GMGN_KEY})
    n = "?"
    if st == 200:
        try:
            d = json.loads(raw)
            cur = (d.get("data") or {})
            lst = cur.get("list") or (cur.get("data") or {}).get("list") or []
            n = len(lst) if isinstance(lst, list) else "?"
        except Exception:
            n = f"bukan json: {raw[:60]}"
    else:
        n = raw[:90]
    print(f"  GMGN kline {label:6} limit=2000 -> {st}  bar={n}")
    time.sleep(1.0)

# GeckoTerminal: butuh alamat POOL, bukan token -> pakai pool dari snapshot terakhir
try:
    snaps = [json.loads(x) for x in open(os.path.join(ROOT, "universe", "bsc-universe.jsonl"), encoding="utf-8")
             if x.strip()]
    last = snaps[-1]
    pools = [(r.get("pool"), r.get("name")) for r in last["rows"] if r.get("pool")][:3]
except Exception:
    pools = []
for p, nm in pools:
    st, raw = get(f"{rec.GT}/pools/{p}/ohlcv/hour?aggregate=1&limit=1000")
    if st == 200:
        lst = ((json.loads(raw).get("data") or {}).get("attributes") or {}).get("ohlcv_list") or []
        span = (lst[0][0] - lst[-1][0]) / 86400 if len(lst) > 1 else 0
        verdict = "CUKUP" if len(lst) * 1 >= NEED_HOURLY_FOR_20_TRADES else "TIDAK CUKUP"
        print(f"  GT ohlcv {str(nm)[:20]:20} -> 200 bar={len(lst)} rentang={span:.1f} hari  "
              f"butuh~{NEED_HOURLY_FOR_20_TRADES} -> {verdict}")
    else:
        print(f"  GT ohlcv {str(nm)[:20]:20} -> {st} {raw[:70]}")
    time.sleep(1.0)

# Hyperliquid: satu-satunya jalur yang kami BELUM pernah coba -> candleSnapshot untuk perp BNB
st, d = post(HL_INFO, {"type": "meta"})
uni = [(i, u.get("name")) for i, u in enumerate((d.get("universe") or []))] if st == 200 else []
bnb = next((n for i, n in uni if n == "BNB"), None)
if bnb:
    st2, c = post(HL_INFO, {"type": "candleSnapshot",
                            "req": {"coin": "BNB", "interval": "1h", "endTime": int(time.time() * 1000),
                                    "startTime": int(time.time() * 1000) - 1000 * 3600 * 24 * 400}})
    if st2 == 200 and isinstance(c, list):
        span = (c[-1]["t"] - c[0]["t"]) / 3600000 / 24 if len(c) > 1 else 0
        print(f"  HL candleSnapshot BNB perp 1h -> 200 bar={len(c)} rentang={span:.1f} hari  "
              f"butuh~{NEED_HOURLY_FOR_20_TRADES} -> "
              f"{'CUKUP' if len(c) >= NEED_HOURLY_FOR_20_TRADES else 'TIDAK CUKUP'}")
    else:
        print(f"  HL candleSnapshot -> {st2} {str(c)[:120]}")

print("\n=== B. Bisakah kita keluar? (uji asumsi 'jual saja waktu menyentuh 0') ===")
rows = last["rows"] if pools else []
have_liq = [r for r in rows if r.get("liquidity") is not None]
hp = [r for r in rows if str(r.get("is_honeypot")) in ("1", "True", "true")]
cns = [r for r in rows if str(r.get("can_not_sell")) in ("1", "True", "true")]
lock = [r for r in rows if r.get("lock_percent") is not None]
tiny = [r for r in have_liq if float(r["liquidity"]) < 50_000]
print(f"  kandidat di jendela terakhir        : {len(rows)}")
print(f"  is_honeypot aktif                   : {len(hp)}")
print(f"  can_not_sell aktif                  : {len(cns)}")
print(f"  lock_percent terisi                 : {len(lock)}  (minimum 20%: "
      f"{sum(1 for r in lock if float(r['lock_percent']) < 0.20)} di bawah itu)")
print(f"  likuiditas < 50k (tidak bisa keluar ukuran wajar): {len(tiny)}")
print("  -> Kalau honeypot/cannot_sell TIDAK bisa dideteksi sebelum masuk, maka aturan 'jual pas 0'"
      " itu tidak bisa dieksekusi: saat harga menyentuh 0 karena rug, jualannya memang ditolak.")

print("\n=== C. Endpoint Jev gratis (router.bynara.id) — kontrak sama? ===")
if not BYNARA_KEY:
    print("  JEV_API_KEY tidak di-set di environment -> dilewati (jangan disimpulkan tidak jalan)")
else:
    state = ("BSC pool. Age_hours 96. Liquidity $178,000. Vol24 $1,900,000. "
             "Top10_holder_share 0.31. Lock 0.42. Bundler_rate 0.06. Holders 2100. "
             "News themes REGULAT=45 SANCTION=17, tone -1.0.")
    body = {"model": "jev-latest", "state": state, "questions": {
        "side": {"type": "choice", "instructions": "Direction for the next 24 hours",
                 "criteria": {"long": "higher", "short": "lower", "flat": "no edge"}},
        "exit_risk": {"type": "noul",
                      "instructions": "The position cannot be closed near entry within 24 hours"},
        "urgency": {"type": "score", "instructions": "How soon to act",
                    "criteria": ["keep watching", "one cycle more", "act now"]}}}
    t0 = time.time()
    st, d = post(f"{BYNARA}/v1/systemone", body, {"Authorization": f"Bearer {BYNARA_KEY}"})
    dt = time.time() - t0
    print(f"  HTTP {st}  latensi {dt:.2f}s  key={BYNARA_KEY[:10]}…({len(BYNARA_KEY)} char)")
    if st == 200 and isinstance(d, dict):
        print(f"  model={d.get('model')} usage={json.dumps(d.get('usage'))}")
        for k, a in (d.get("answers") or {}).items():
            if a.get("type") == "choice":
                print(f"   {k:11} choice={a.get('choice')} conf={a.get('confidence')} p={json.dumps(a.get('probabilities'))}")
            elif a.get("type") == "score":
                print(f"   {k:11} score={a.get('score')} conf={a.get('confidence')}")
            else:
                print(f"   {k:11} noul={a.get('noul')}")
    else:
        print(f"  {str(d)[:260]}")
