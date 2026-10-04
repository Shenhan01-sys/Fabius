"""Kejadian listing perp USDⓈ-M baru untuk B4-LISTING-FADE (P129, F-D95; dulu P73 "pipeline event" - alasan gerbang v1 TIDAK_TERUKUR).

Sumber = Binance Vision (berkas publik, terjangkau dari runner GitHub; `fapi.binance.com` tidak): daftar simbol di bucket
`data/futures/um/daily/klines/` dan berkas harian PERTAMA tiap simbol = hari listing (hari-1). Tiga berkas di `ledger/bars/`:
  um_symbols.csv            symbol,first_date   - semua simbol perp USDT yang pernah dilihat (tanpa kontrak berjangka ber-`_`, tanpa USDC)
  events_um_listing.csv     asset,day1_open_t,day1_close,day1_quote_volume_usd - hari-1 tiap simbol yang terdaftar sejak `--since-days` (bawaan 60)
  fut_<SYM>_1d.csv          deret perp tiap kejadian yang lolos volume minimum B4 (bahan hargaRef + settle short), ditanam dari hari-1 dan
                            diperpanjang selama posisi B4 bisa aktif (H hari + cadangan)
Gagal-tertutup: daftar/berkas tak terbaca = FeedError (TUNDA, tidak menebak); simbol yang terdaftar SEBELUM Vision mulai mencatat (2019-2020)
tampak "lama" dan tidak pernah menjadi kejadian; simbol yang di-relist dengan nama sama tidak terdeteksi (dicatat, bukan disembunyikan).
Hanya stdlib; tanpa kunci.

    python -X utf8 tools/listing_events.py              # perbarui ketiga berkas (rantai GitHub menjalankannya lewat paper_tick --feed bila B4 aktif)
"""
from __future__ import annotations

import csv
import io
import os
import re
import sys
import time
import urllib.parse
import zipfile
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List, Optional, Tuple

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import feed_bars as fb                                                          # noqa: E402
from engine.spec import SPECS                                                   # noqa: E402

S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
PREFIX = "data/futures/um/daily/klines/"
SYMS_FILE = "um_symbols.csv"
EVENTS_FILE = "events_um_listing.csv"
STAMP_FILE = "events_um_listing.checked"                                      # tanggal UTC pemindaian sukses terakhir (paper_tick: B4 hanya di-tick bila = hari ini)
DAY_MS = fb.DAY_MS
B4 = SPECS["B4-LISTING-FADE"]
MIN_VOL = float(B4.konstanta["min_volume_kuotasi_hari1_usd"])
HOLD_DAYS = int(B4.param)


def is_usdt_perp(sym: str) -> bool:
    return sym.endswith("USDT") and "_" not in sym


def list_symbols(get: Callable[[str], Optional[bytes]] = fb.http_get) -> List[str]:
    """Semua direktori simbol di bucket (berhalaman 1.000; penanda = prefix terakhir)."""
    out, marker = [], ""
    for _ in range(20):
        q = f"{S3}?delimiter=/&prefix={PREFIX}" + (f"&marker={marker}" if marker else "")
        raw = get(q)
        if raw is None:
            raise fb.FeedError("daftar simbol Vision: 404")
        x = raw.decode("utf-8", "replace")
        page = re.findall(r"<Prefix>" + re.escape(PREFIX) + r"([^/<]+)/</Prefix>", x)
        out += page
        if "<IsTruncated>true</IsTruncated>" not in x or not page:
            return sorted(set(out))
        marker = PREFIX + page[-1] + "/"
    raise fb.FeedError("daftar simbol Vision: lebih dari 20 halaman (tak terduga)")


def first_date(sym: str, get: Callable[[str], Optional[bytes]] = fb.http_get) -> Optional[str]:
    """Tanggal berkas harian 1d PERTAMA sebuah simbol (= hari listing), atau None bila belum ada berkas 1d."""
    raw = get(f"{S3}?prefix={urllib.parse.quote(PREFIX + sym + '/1d/')}&max-keys=1")       # ada simbol non-ASCII
    if raw is None:
        raise fb.FeedError(f"daftar {sym}: 404")
    m = re.search(r"<Key>[^<]*-1d-(\d{4}-\d{2}-\d{2})\.zip</Key>", raw.decode("utf-8", "replace"))
    return m.group(1) if m else None


def day1(sym: str, date: str, fetch: Callable[[str], Optional[bytes]] = fb.http_get) -> Optional[Tuple[int, float, float]]:
    """(waktu buka bar hari-1 ms, penutupan, volume kuotasi USD) dari zip harian hari-1; None bila belum terbit."""
    q = urllib.parse.quote(sym)
    blob = fetch(f"{fb.VISION}/futures/um/daily/klines/{q}/1d/{q}-1d-{date}.zip")
    if blob is None:
        return None
    with zipfile.ZipFile(io.BytesIO(blob)) as z, z.open(z.namelist()[0]) as f:
        for r in csv.reader(io.TextIOWrapper(f)):
            if r and r[0].strip().isdigit():
                return fb._ms(int(r[0])), float(r[4]), float(r[7])
    raise fb.FeedError(f"{sym} {date}: zip hari-1 tanpa baris")


def _read(path: str) -> List[List[str]]:
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.reader(f) if r]
    return rows[1:]


def _write(path: str, header: List[str], rows: List[list]) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    os.replace(tmp, path)


def seed_fut(bars_dir: str, sym: str, t_day1: int, today_ms: int, fetch: Callable[[str], Optional[bytes]] = fb.http_get) -> int:
    """Tanam fut_<SYM>_1d.csv dari hari-1 sampai bar tertutup terakhir yang terbit (zip harian). Sudah ada = tidak disentuh (umpan memperpanjang)."""
    path = os.path.join(bars_dir, f"fut_{sym}_1d.csv")
    if os.path.exists(path):
        return 0
    rows, t = [], t_day1
    while t < fb.day_start(today_ms):
        blob = fetch(f"{fb.VISION}/futures/um/daily/klines/{sym}/1d/{sym}-1d-{fb.date_of(t)}.zip")
        if blob is None:
            break
        got = [r for r in fb.parse_kline_zip(blob) if r[0] == t]
        if len(got) != 1 or fb._valid_bar(got[0], t):
            raise fb.FeedError(f"{sym} {fb.date_of(t)}: bar hari tidak valid - tidak ditanam")
        rows.append(got[0])
        t += DAY_MS
    if rows:
        _write(path, ["t", "o", "h", "l", "c", "v"], rows)
    return len(rows)


def update(bars_dir: str, today_ms: int, get: Callable[[str], Optional[bytes]] = fb.http_get, fetch: Callable[[str], Optional[bytes]] = fb.http_get,
           since_days: int = 60, log=print) -> dict:
    sp = os.path.join(bars_dir, SYMS_FILE)
    ep = os.path.join(bars_dir, EVENTS_FILE)
    known: Dict[str, str] = {r[0]: r[1] for r in _read(sp)}
    perps = [s for s in list_symbols(get) if is_usdt_perp(s)]
    new = [s for s in perps if s not in known or not known[s]]
    with ThreadPoolExecutor(max_workers=16) as pool:                       # ±1.100 daftar kecil saat pertama; sesudahnya hanya simbol baru
        for s, d in zip(new, pool.map(lambda x: first_date(x, get), new)):
            known[s] = d or ""
    _write(sp, ["symbol", "first_date"], sorted([s, d] for s, d in known.items()))
    events: Dict[str, List[str]] = {r[0]: r for r in _read(ep)}
    cutoff = fb.date_of(today_ms - since_days * DAY_MS)
    today = fb.date_of(today_ms)
    added = []
    for s, d in sorted(known.items()):
        if not d or d < cutoff or d >= today or s in events:
            continue                                                          # lama / hari-1 belum tertutup / sudah tercatat
        got = day1(s, d, fetch)
        if got is None:
            continue                                                          # zip hari-1 belum terbit: dicoba lagi putaran berikut
        events[s] = [s, str(got[0]), repr(got[1]), repr(got[2])]
        added.append(s)
    _write(ep, ["asset", "day1_open_t", "day1_close", "day1_quote_volume_usd"], sorted(events.values(), key=lambda r: (int(r[1]), r[0])))
    seeded, extended = {}, 0
    for s, r in events.items():
        t1 = int(r[1])
        if float(r[3]) < MIN_VOL or t1 + (HOLD_DAYS + 3) * DAY_MS < fb.day_start(today_ms) - DAY_MS:
            continue                                                          # di bawah volume minimum B4, atau jendela B4 sudah lewat
        n = seed_fut(bars_dir, s, t1, today_ms, fetch)
        if n:
            seeded[s] = n
        else:
            extended += fb.update_klines(bars_dir, "fut", s, today_ms, fetch)["added"]
    with open(os.path.join(bars_dir, STAMP_FILE), "w", encoding="utf-8", newline="\n") as f:
        f.write(fb.date_of(today_ms) + "\n")
    log(f"listing: {len(perps)} perp USDT ({len(new)} simbol baru diperiksa), kejadian baru {added or '-'}, deret ditanam {seeded or '-'}, "
        f"+{extended} bar diperpanjang")
    return {"perps": len(perps), "new_symbols": new, "events_added": added, "seeded": seeded, "extended": extended}


def main() -> int:
    bars = os.path.join(ROOT, "ledger", "bars")
    try:
        update(bars, int(time.time() * 1000))
    except fb.FeedError as e:
        print(f"TUNDA: {e} - kejadian listing tidak diperbarui")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
