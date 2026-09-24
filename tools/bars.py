"""Ambil deret harga (bidang ①) dari venue perp BNB-native, dengan paging yang jujur.

Kenapa file ini ada: lapisan arah (long/short, kapan, seberapa banyak) tidak bisa dibangun di atas
potongan harga. kemarin ① hanya bisa dari Hyperliquid - chain-nya sendiri. Terukur 25 Sep:
Aster `fapi/v1/klines` hidup tanpa API key, `BNBUSDT` terdaftar sejak Jan 2022, dan capnya
**1.500 bar per panggilan** (limit 3.000/5.000 ditolak `code -1130`), sementara `startTime`
diterima -> jadi kedalaman didapat dari PAGING, bukan dari satu permintaan besar.

Aturan yang ditancapkan di sini:
  - cache per (symbol, interval) + metadata sumber/waktu ambil: supaya hasil analisis bisa
    direproduksi, dan "data dari mana" tidak jadi pertanyaan terbuka;
  - tumpul ke belakang: halaman paling tua diminta lebih dulu, berhenti saat baris kosong,
    JANGAN saat jumlah kurang - bedanya menentukan apakah kita punya 60 hari atau 300;
  - `weight` dihormati: jeda antar halaman, dan satu percobaan ulang;
  - kalau server memotong limit, kita TURUNKAN dan lanjut - bukan menyimpulkan datanya tidak ada.

Ini hanya membaca data pasar. Tidak ada order, tidak ada transaksi, tidak ada kunci.
Pakai:  python tools/bars.py BNBUSDT --days 300
        python tools/bars.py ETHUSDT --days 90 --interval 4h
        python tools/bars.py --list            # aset yang sudah ter-cache
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "klines")
BASE = "https://fapi.asterdex.com/fapi/v1"
UA = {"User-Agent": "Mozilla/5.0 (compatible; fabius-bars/1.0)", "Accept": "application/json"}

PAGE_CAP = 1500          # server menolak di atas ini (code -1130), terukur 25 Sep
PAGE_SLEEP = 0.45        # REQUEST_WEIGHT 2400/menit; kita jauh di bawahnya
INTERVAL_MS = {"15m": 900_000, "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000}


def _get(path: str, timeout: int = 40):
    """Satu GET -> (status, data ATAU string error). Tidak melempar exception."""
    req = urllib.request.Request(BASE + path, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body[:220]
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {str(e)[:180]}"


def fetch(symbol: str, interval: str = "1h", days: int = 300, verbose: bool = True):
    """Ambil `days` terakhir dengan paging. Mengembalikan (bars, catatan)."""
    step = INTERVAL_MS.get(interval)
    if not step:
        raise SystemExit(f"interval tak dikenal: {interval} (pilih {', '.join(INTERVAL_MS)})")
    end = int(time.time() * 1000)
    start = end - days * 86_400_000
    bars, page = [], 0
    cur = start
    meta = {"source": "aster", "endpoint": f"{BASE}/klines", "symbol": symbol, "interval": interval,
            "requested_days": days, "pages": 0, "http_problems": []}

    while cur < end:
        page += 1
        st, d = _get(f"/klines?symbol={symbol}&interval={interval}"
                     f"&startTime={cur}&endTime={end}&limit={PAGE_CAP}")
        meta["pages"] = page
        if st != 200 or not isinstance(d, list):
            meta["http_problems"].append(f"page{page}:{st}:{str(d)[:120]}")
            if verbose:
                print(f"  halaman {page}: HTTP {st} -> {str(d)[:140]}", flush=True)
            if st == 429:                      # throttled: tunggu sekali lalu coba lagi
                time.sleep(5)
                st, d = _get(f"/klines?symbol={symbol}&interval={interval}"
                             f"&startTime={cur}&endTime={end}&limit={PAGE_CAP}")
                if st != 200 or not isinstance(d, list):
                    meta["http_problems"].append(f"retry:{st}")
                    break
            else:
                break
        if not d:
            break                              # memang tidak ada data lagi
        for b in d:
            # [openTime, o, h, l, c, volume, closeTime, quoteVol, trades, takerBase, takerQuote, ignore]
            bars.append({"t": int(b[0]), "o": float(b[1]), "h": float(b[2]), "l": float(b[3]),
                         "c": float(b[4]), "v": float(b[5]), "n": int(b[8]) if len(b) > 8 else 0})
        last_t = int(d[-1][0])
        nxt = last_t + step
        if nxt <= cur:                          # anti putaran tak berujung
            break
        cur = nxt
        time.sleep(PAGE_SLEEP)

    bars.sort(key=lambda x: x["t"])
    # buang bar yang sedang berjalan: closeTime masih di masa depan -> harga belum selesai
    now = int(time.time() * 1000)
    bars = [b for b in bars if b["t"] + step <= now]
    return bars, meta


def save(symbol: str, interval: str, bars, meta):
    """Tulis cache dengan meta yang DIPAKSA lengkap dan DIPERIKSA sendiri.

    Kenapa bukan sekadar `json.dump`: terukur 25 Sep, `direction.py` menulis cache dengan meta
    karangannya sendiri (`{"source":"aster","pages":1}`) sambil membuang meta asli dari `fetch()`.
    Akibatnya (a) `--list` crash di 9 berkas karena `interval` tidak ada, dan (b) yang lebih
    berbahaya: berkas mengklaim 1 halaman untuk deret yang butuh 7 halaman. Metadata provenance
    yang salah lebih buruk daripada kosong - ia dibaca orang sebagai jejak.
    """
    meta = dict(meta or {})
    meta.setdefault("source", "aster")
    meta.setdefault("symbol", symbol)
    meta.setdefault("interval", interval)
    meta.setdefault("endpoint", f"{BASE}/klines")
    if bars:
        need = max(1, -(-len(bars) // PAGE_CAP))
        claimed = meta.get("pages") or 0
        if 0 < claimed < need:
            meta["meta_warning"] = f"pages={claimed} tapi {len(bars)} bar butuh >= {need} halaman (cap {PAGE_CAP})"
            meta["pages_min_needed"] = need
    os.makedirs(CACHE, exist_ok=True)
    blob = json.dumps(bars, separators=(",", ":")).encode()
    out = {"meta": {**meta, "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "count": len(bars), "sha256": "0x" + hashlib.sha256(blob).hexdigest(),
                    "first_t": bars[0]["t"] if bars else None,
                    "last_t": bars[-1]["t"] if bars else None},
           "bars": bars}
    p = os.path.join(CACHE, f"{symbol}_{interval}.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False)
    return p


def load(symbol: str, interval: str):
    p = os.path.join(CACHE, f"{symbol}_{interval}.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def report(symbol, interval, bars, meta, path=None):
    if not bars:
        print(f"  {symbol} {interval}: 0 bar - TIDAK ADA DATA, bukan 'nol perubahan'. "
              f"problems={meta.get('http_problems')}")
        return
    step = INTERVAL_MS[interval]
    span_days = (bars[-1]["t"] - bars[0]["t"]) / 86_400_000
    # ambang kita (vault/02-Ambang.md): 480 bar utk 20 trade non-overlap 24 jam;
    # horizon 4 jam menuntut 20 * 4 = 80 bar trading, jadi batas nyata adalah jumlah BAR.
    print(f"  {symbol} {interval}: {len(bars):>6} bar / {span_days:>6.1f} hari "
          f"({meta['pages']} halaman)  rentang {time.strftime('%Y-%m-%d', time.gmtime(bars[0]['t']/1000))}"
          f" -> {time.strftime('%Y-%m-%d', time.gmtime(bars[-1]['t']/1000))}")
    verdict = ("✅ lewat 5-fold (>=2400)" if len(bars) >= 2400 else
               "🟡 cukup 20 trade (>=480)" if len(bars) >= 480 else "❌ terlalu pendek")
    print(f"     ambang validasi: {verdict}   harga terakhir={bars[-1]['c']}")
    if path:
        print(f"     cache: {os.path.relpath(path, ROOT)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol", nargs="?", help="mis. BNBUSDT")
    ap.add_argument("--interval", default="1h")
    ap.add_argument("--days", type=int, default=300)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()

    if a.list:
        if not os.path.isdir(CACHE):
            print("cache kosong")
            return
        for f in sorted(os.listdir(CACHE)):
            try:
                d = json.load(open(os.path.join(CACHE, f), encoding="utf-8"))
                m = d["meta"]
                # .get, bukan [ ]: berkas yang ditulis dengan meta separuh harus TERBACA sebagai
                # separuh, bukan membuat daftar isinya crash (`rusak: 'interval'` - itu yang
                # terjadi 25 Sep pada 9 berkas, dan yang bikin bug meta jadi kelihatan cuma sebagai
                # "alatnya rusak").
                iv = m.get("interval", "?TIDAK-DICATAT")
                pg = m.get("pages", "?")
                line = (f"  {f:26} {m.get('count', len(d.get('bars') or [])):>6} bar  {iv:5} "
                        f"hal={pg:>3} diambil {m.get('fetched_utc', '?')}  sha={str(m.get('sha256'))[2:10]}")
                if m.get("meta_warning"):
                    line += f"  WARNING: {m['meta_warning']}"
                print(line)
            except Exception as e:  # noqa: BLE001
                print(f"  {f:26} rusak: {e}")
        return

    if not a.symbol:
        ap.print_help()
        sys.exit(2)

    sym = a.symbol.upper()
    if not sym.endswith(("USDT", "USD1", "U")):
        sym += "USDT"
    print(f"mengambil {sym} {a.interval} {a.days} hari dari Aster (tanpa API key)...")
    t0 = time.time()
    bars, meta = fetch(sym, a.interval, a.days)
    path = None if a.no_save else save(sym, a.interval, bars, meta)
    report(sym, a.interval, bars, meta, path)
    print(f"     {time.time() - t0:.1f}s")
    if meta.get("http_problems"):
        print(f"     catatan HTTP: {str(meta['http_problems'])[:300]}")


if __name__ == "__main__":
    main()
