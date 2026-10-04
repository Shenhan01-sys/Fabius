"""Tanam berkas bar harian BARU dari Binance Vision (P128, F-D95): `feed_bars.update_klines` hanya MEMPERPANJANG berkas yang sudah ada, jadi simbol
baru (mis. spot PAXGUSDT = emas untuk B5-CORE-RWA) butuh berkas awal dengan riwayat. Sumber sama dengan umpan harian: zip BULANAN untuk bulan-bulan
penuh, zip HARIAN untuk bulan berjalan, parser + validasi yang sama (`feed_bars.parse_kline_zip`, `_valid_bar`). Gagal-tertutup:
  - berkas tujuan sudah ada = TOLAK (alat ini menanam, tidak menimpa);
  - satu hari bolong / ganda / bar tidak valid = TOLAK, tidak ada yang ditulis (riwayat dengan lubang diam-diam lebih buruk daripada tidak ada);
  - bulan sebelum simbol terdaftar (404 di awal) dilewati sampai bulan pertama yang ada.
Hanya stdlib; data publik; tanpa kunci.

    python -X utf8 tools/seed_bars.py --kind spot --symbol PAXGUSDT --from 2023-01
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import sys
import time
from typing import Callable, List, Optional, Tuple

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

DAY_MS = fb.DAY_MS
Row = Tuple[int, float, float, float, float, float]


class SeedError(Exception):
    pass


def months_between(start: str, end_excl: str) -> List[str]:
    y, m = map(int, start.split("-"))
    out = []
    while f"{y:04d}-{m:02d}" < end_excl:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def collect(kind: str, sym: str, start: str, today_ms: int, fetch: Callable[[str], Optional[bytes]] = fb.http_get) -> List[Row]:
    """Bar harian tertutup dari bulan `start` sampai kemarin (UTC). -> baris terurut, sudah divalidasi menerus tanpa lubang."""
    market = "futures/um" if kind == "fut" else "spot"
    this_month = fb.date_of(today_ms)[:7]
    rows: List[Row] = []
    started = False
    for mo in months_between(start, this_month):
        blob = fetch(f"{fb.VISION}/{market}/monthly/klines/{sym}/1d/{sym}-1d-{mo}.zip")
        if blob is None and not started:
            continue                                                          # simbol belum terdaftar bulan itu
        started = True
        if blob is not None:
            rows += fb.parse_kline_zip(blob)
            continue
        # zip bulanan belum terbit (beberapa hari sesudah akhir bulan): bulan itu dari zip harian; satu hari hilang = TOLAK (validasi di bawah)
        t = int(dt.datetime.strptime(mo + "-01", "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
        while fb.date_of(t)[:7] == mo:
            day = fetch(f"{fb.VISION}/{market}/daily/klines/{sym}/1d/{sym}-1d-{fb.date_of(t)}.zip")
            if day is None:
                raise SeedError(f"{mo}: zip bulanan belum ada dan harian {fb.date_of(t)} hilang - tidak ditanam")
            rows += [r for r in fb.parse_kline_zip(day) if r[0] == t]
            t += DAY_MS
    t = int(dt.datetime.strptime(this_month + "-01", "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp() * 1000)   # awal bulan berjalan (UTC)
    while t < fb.day_start(today_ms):
        blob = fetch(f"{fb.VISION}/{market}/daily/klines/{sym}/1d/{sym}-1d-{fb.date_of(t)}.zip")
        if blob is None:
            break                                                                     # belum terbit: berhenti di sini, umpan harian melanjutkan
        rows += [r for r in fb.parse_kline_zip(blob) if r[0] == t]
        t += DAY_MS
    if not rows:
        raise SeedError(f"{kind} {sym}: tidak ada bar sejak {start}")
    rows.sort(key=lambda r: r[0])
    for i, r in enumerate(rows):
        expect = rows[0][0] + i * DAY_MS
        bad = fb._valid_bar(r, expect)
        if bad:
            raise SeedError(f"{kind} {sym} baris {i} ({fb.date_of(r[0])}): {bad}")
    return rows


def write(path: str, rows: List[Row]) -> None:
    if os.path.exists(path):
        raise SeedError(f"{os.path.relpath(path, ROOT)} sudah ada - alat ini menanam, tidak menimpa (perpanjang lewat feed_bars)")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["t", "o", "h", "l", "c", "v"])
        for r in rows:
            w.writerow(r)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kind", choices=("spot", "fut"), required=True)
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--from", dest="start", required=True, help="bulan pertama YYYY-MM")
    ap.add_argument("--bars", default=os.path.join(ROOT, "ledger", "bars"))
    a = ap.parse_args()
    path = os.path.join(a.bars, f"{a.kind}_{a.symbol}_1d.csv")
    try:
        rows = collect(a.kind, a.symbol, a.start, int(time.time() * 1000))
        write(path, rows)
    except (SeedError, fb.FeedError) as e:
        print(f"TOLAK: {e}")
        return 1
    print(f"ditanam {os.path.relpath(path, ROOT)}: {len(rows)} bar {fb.date_of(rows[0][0])} .. {fb.date_of(rows[-1][0])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
