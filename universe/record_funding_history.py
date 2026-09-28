"""Perekam histori funding + open interest (P13, dibalik bentuknya 28 Sep).

Kenapa bentuknya "sedot mundur", bukan "rekam per jam dan tunggu": probe 28 Sep 02:06Z mengukur
bahwa jalur histori funding/OI benar-benar ada TANPA kunci - Bybit `funding/history` 200 baris =
66,3 hari ke belakang (interval 8 jam), OKX `funding-rate-history` 33,0 hari, Binance
`futures/data/openInterestHist` 500 baris per 1 jam = 20,8 hari. Sebelum itu rencana kita (P13
lama) adalah menunggu 30 hari kalender - yang ternyata tidak perlu. Rinciannya di
`vault/TradingKnowledge/Fakta Terukur` §A.5 dan keputusan F-D25.

Yang TIDAK diubah perekam ini: funding per 8 jam bukan fitur per-bar. Horizon uji kita 1 jam dan
4 jam, jadi deret ini menguji hipotesis carry pada horison HARIAN, tidak lebih. Menulis barisnya
dengan interval 8 jam lalu memaksanya ke `direction.py` yang ambangnya per-4-jam adalah cara
paling cepat menipu diri sendiri.

Baca: `Fakta Terukur` §C - "bisa diakses" itu properti sumber x jaringan x WAKTU, dan jalur yang
mati pada 24 Sep hidup lagi pada 28 Sep. Karena itu tiap baris menyimpan `pull_t` ( kapan kami
menerima angka ini ) - supaya "kami tahu ini per 8 jam pada jam sekian" bisa dibuktikan nanti,
bukan diimprovisasi.

Read-only: GET ke endpoint publik, tanpa kunci, tanpa order, tanpa dana.
Pakai:  python universe/record_funding_history.py            # sedot + tulis + manifest
         python universe/record_funding_history.py --report   # ukur saja, tidak menulis
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "funding-history.jsonl")
MANIFEST = os.path.join(HERE, "funding-history-manifest.txt")
SCHEMA = 1

UA = {"User-Agent": "Mozilla/5.0 (compatible; fabius-funding-recorder/1.0)",
      "Accept": "application/json"}

# Simbol yang sama punya nama berbeda per venue - itu bukan detail, itu sumber bug kelas
# "endpoint membalas 200 tapi untuk aset lain".
SYMBOLS = {
    "BNB":   {"bybit": "BNBUSDT",  "okx": "BNB-USDT-SWAP",  "binance": "BNBUSDT"},
    "BTC":   {"bybit": "BTCUSDT",  "okx": "BTC-USDT-SWAP",  "binance": "BTCUSDT"},
    "ETH":   {"bybit": "ETHUSDT",  "okx": "ETH-USDT-SWAP",  "binance": "ETHUSDT"},
    "SOL":   {"bybit": "SOLUSDT",  "okx": "SOL-USDT-SWAP",  "binance": "SOLUSDT"},
    "DOGE":  {"bybit": "DOGEUSDT", "okx": "DOGE-USDT-SWAP", "binance": "DOGEUSDT"},
    "XRP":   {"bybit": "XRPUSDT",  "okx": "XRP-USDT-SWAP",  "binance": "XRPUSDT"},
}
INTERVAL_H = {"bybit": 8, "okx": 8, "binance_oi": 1}


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha_line(line):
    return "0x" + hashlib.sha256(line.encode("utf-8")).hexdigest()


def fetch(url, tries=3, pause=2.0):
    """Satu respons bukan kesimpulan: 429/5xx/timeout DIULANG, dan kalau tetap gagal kembalikan
    (kode, body, retry) alih-alih melempar - perekam jam-an tidak boleh mati senyap di runner."""
    last = []
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return r.status, r.read().decode("utf-8", "replace"), last
        except urllib.error.HTTPError as e:
            last.append("HTTP %s" % e.code)
            if e.code in (401, 403, 404):
                try:
                    return e.code, e.read(240).decode("utf-8", "replace"), last
                except Exception:
                    return e.code, "", last
            time.sleep(pause * (i + 1))
        except Exception as e:
            last.append("%s: %s" % (type(e).__name__, str(e)[:70]))
            time.sleep(pause * (i + 1))
    return "gagal", "", last


def pull_bybit(sym, pages=4):
    """/v5/market/funding/history: <=200 baris/panggilan, cursor `nextPageCursor` mundur."""
    out, cursor = [], ""
    for _ in range(pages):
        url = ("https://api.bybit.com/v5/market/funding/history?category=linear&symbol=%s&limit=200"
               % sym) + (("&cursor=%s" % urllib.parse.quote(cursor)) if cursor else "")
        code, body, _ = fetch(url)
        if code != 200:
            return out, "bybit %s -> %s" % (sym, code)
        try:
            res = json.loads(body)["result"]
        except Exception as e:
            return out, "bybit %s -> body tak terbaca (%s)" % (sym, type(e).__name__)
        rows = res.get("list") or []
        for r in rows:
            t = int(r.get("fundingRateTimestamp") or 0)
            if t:
                out.append({"k": "fr", "s": "bybit", "sym": sym, "t": t,
                            "rate": float(r.get("fundingRate") or 0.0), "iv_h": INTERVAL_H["bybit"]})
        cursor = res.get("nextPageCursor") or ""
        if not cursor or not rows:
            break
        time.sleep(0.3)
    return out, "ok"


def pull_okx(sym, pages=4):
    """/api/v5/public/funding-rate-history: <=100 baris, paging maju-mundur pakai `after` = ts terkecil."""
    out, after = [], ""
    for _ in range(pages):
        url = "https://www.okx.com/api/v5/public/funding-rate-history?instId=%s&limit=100" % sym
        if after:
            url += "&after=" + after
        code, body, _ = fetch(url)
        if code != 200:
            return out, "okx %s -> %s" % (sym, code)
        try:
            rows = json.loads(body)["data"]
        except Exception as e:
            return out, "okx %s -> body tak terbaca (%s)" % (sym, type(e).__name__)
        ts = []
        for r in rows:
            t = int(r.get("fundingTime") or 0)
            if t:
                ts.append(t)
                out.append({"k": "fr", "s": "okx", "sym": sym, "t": t,
                            "rate": float(r.get("fundingRate") or 0.0), "iv_h": INTERVAL_H["okx"]})
        if len(ts) < 2:
            break
        after = str(min(ts))
        time.sleep(0.3)
    return out, "ok"


def pull_binance_oi(sym, limit=500):
    """`futures/data/openInterestHist` - bukan funding, tapi pasangan yang membuat funding bisa
    dibaca sebagai 'orang bertambah atau berpindah'. Jendela API-nya ±30 hari."""
    url = ("https://fapi.binance.com/futures/data/openInterestHist?symbol=%s&period=1h&limit=%d"
           % (sym, limit))
    code, body, _ = fetch(url)
    if code != 200:
        return [], "binance_oi %s -> %s" % (sym, code)
    try:
        rows = json.loads(body)
    except Exception as e:
        return [], "binance_oi %s -> body tak terbaca (%s)" % (sym, type(e).__name__)
    out = []
    for r in rows:
        t = int(r.get("timestamp") or 0)
        if t:
            out.append({"k": "oi", "s": "binance_oi", "sym": sym, "t": t,
                        "sum_open_interest": float(r.get("sumOpenInterest") or 0.0),
                        "sum_open_value": float(r.get("sumOpenInterestValue") or 0.0),
                        "iv_h": INTERVAL_H["binance_oi"]})
    return out, "ok" if out else "binance_oi %s -> 200 tapi kosong" % sym


def load_state():
    """Baris yang sudah ada + hash baris terakhir (rantai anti-sunting, sama seperti wallet-flow)."""
    seen, last_sha, n = set(), None, 0
    if os.path.exists(OUT):
        for ln in io.open(OUT, encoding="utf-8"):
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            n += 1
            last_sha = sha_line(ln)
            try:
                d = json.loads(ln)
            except Exception:
                continue
            seen.add((d.get("s"), d.get("sym"), d.get("t"), d.get("k")))
    return seen, last_sha, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true", help="ukur dan cetak, jangan menulis berkas")
    ap.add_argument("--manifest", action="store_true",
                    help="hanya tulis ulang manifest dari berkas yang ada (tanpa jaringan)")
    ap.add_argument("--pages", type=int, default=4)
    ap.add_argument("--symbols", default=",".join(SYMBOLS), help="BNB,BTC,ETH,...")
    a = ap.parse_args()

    want = [s.strip().upper() for s in a.symbols.split(",") if s.strip().upper() in SYMBOLS]
    pull_t = int(time.time())
    seen, last_sha, before = load_state()
    fresh, notes = [], []
    if a.manifest:
        write_manifest([], pull_t)
        return

    for base in want:
        names = SYMBOLS[base]
        jobs = [("funding bybit", lambda n=names["bybit"]: pull_bybit(n, a.pages)),
                ("funding okx", lambda n=names["okx"]: pull_okx(n, a.pages)),
                ("OI binance", lambda n=names["binance"]: pull_binance_oi(n))]
        for label, fn in jobs:
            rows, why = fn()
            if why != "ok":
                notes.append("%s %s: %s" % (label, base, why))
            for r in rows:
                r["base"] = base
                r["pull_t"] = pull_t
                r["schema"] = SCHEMA
                key = (r["s"], r["sym"], r["t"], r["k"])
                if key not in seen:
                    seen.add(key)
                    fresh.append(r)
            time.sleep(0.2)

    fresh.sort(key=lambda r: (r["k"], r["s"], r["sym"], r["t"]))
    print("ditarik %s UTC | simbol %s | baris baru %d (sudah ada %d)"
          % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(pull_t)), ",".join(want),
             len(fresh), before))
    for nline in notes:
        print("  catatan: " + nline)

    if not fresh:
        print("tidak ada baris baru - manifest tidak disentuh.")
        return

    if a.report:
        print("(--report: %d baris TIDAK ditulis)" % len(fresh))
        return

    with io.open(OUT, "a", encoding="utf-8", newline="\n") as fh:
        for r in fresh:
            fh.write(canon(r) + "\n")

    # Manifest ditulis ulang penuh (bukan append): idempoten, tidak bisa menghasilkan baris ganda.
    write_manifest(notes, pull_t)
    print("ditulis: %s (+%d)" % (os.path.basename(OUT), len(fresh)))


def write_manifest(notes, pull_t):
    """Ringkasan yang boleh masuk Git: jumlah baris, rentang nyata, dan hash tiap kelompok.

    Aritmetika rentang pernah salah 1000x di sini (`t` milidetik, dibagi 3600 seolah detik) dan
    manifest melaporkan "66.333 hari" untuk dataset 66 hari. Bentuk yang benar di bawah dijaga
    satu assert: kalau rentang hasil lebih besar dari 400 hari, itu hampir pasti satuan, bukan
    data - lebih baik alatnya yang berteriak daripada manifestnya terbaca puitis.
    """
    stats = {}
    total = 0
    for ln in io.open(OUT, encoding="utf-8"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        total += 1
        d = json.loads(ln)
        key = (d["k"], d["s"], d.get("base") or "?")
        s = stats.setdefault(key, {"n": 0, "t0": None, "t1": None, "sha": None})
        s["n"] += 1
        s["t0"] = d["t"] if s["t0"] is None else min(s["t0"], d["t"])
        s["t1"] = d["t"] if s["t1"] is None else max(s["t1"], d["t"])
        s["sha"] = sha_line(ln)
    for key, s in stats.items():
        span_d = (s["t1"] - s["t0"]) / 86400000.0
        assert span_d < 400, ("%s rentang %.0f hari - hampir pasti bug satuan (ms vs s), bukan data"
                              % ("/".join(key), span_d))
    with io.open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# funding-history-manifest.txt - ditulis %s UTC | %d baris total | schema %d\n"
                 % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(pull_t)), total, SCHEMA))
        fh.write("# kolom: jenis sumber basis | jumlah baris | rentang nyata (hari) | tanggal ujung | "
                 "hash baris terakhir kelompok\n")
        for key in sorted(stats):
            s = stats[key]
            span_d = (s["t1"] - s["t0"]) / 86400000.0
            step_h = span_d * 24.0 / max(s["n"] - 1, 1)
            fh.write("%-4s %-12s %-6s baris=%-5d rentang=%5.1f hari | %s .. %s | interval≈%.1f j | sha %s\n"
                     % (key[0], key[1], key[2], s["n"], span_d,
                        time.strftime("%Y-%m-%d", time.gmtime(s["t0"] / 1000)),
                        time.strftime("%Y-%m-%d", time.gmtime(s["t1"] / 1000)), step_h,
                        (s["sha"] or "")[:14]))
        fh.write("# catatan penarikan (yang gagal/hampa, bukan asumsi):\n")
        for nline in notes or ["-"]:
            fh.write("# " + nline + "\n")


if __name__ == "__main__":
    main()
