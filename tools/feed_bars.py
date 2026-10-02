"""Pengunduh bar harian untuk ledger paper (M2): satu-satunya bagian M2 yang menyentuh jaringan. Hanya stdlib. Tanpa kunci.

Sumber publik tanpa kunci:
  kline harian perp  https://data.binance.vision/data/futures/um/daily/klines/<SYM>/1d/<SYM>-1d-<YYYY-MM-DD>.zip   (berkas statis, terbit sesudah hari UTC itu tutup)
  kline harian spot  .../data/spot/daily/klines/...     (opsional, --spot; dibutuhkan B3/B5)
  funding            REST publik https://fapi.binance.com/fapi/v1/fundingRate (dicoba lebih dulu; dari jaringan tertentu bisa 451/403)
                     lalu zip BULANAN .../futures/um/monthly/fundingRate/... untuk bulan yang sudah tutup (terbit beberapa hari sesudahnya)
  estimasi funding   berkas harian .../futures/um/daily/premiumIndexKlines/<SYM>/1m/... (terbit ±09:10Z hari berikutnya) -> `ledger/bars/fund_est_<SYM>.csv` lewat
                     `engine/funding_est.py` (P92/F-D76). ESTIMASI, bukan funding: galat terukur ±0,1 bps/hari/aset; dipakai untuk laporan PROVISIONAL dan target B3 saja.

Aturan (semuanya ditegakkan di kode, bukan niat):
  * Hanya bar yang SUDAH tertutup (hari UTC < hari ini). Funding hanya baris dengan waktu < awal hari ini, sehingga setiap hari di berkas funding LENGKAP.
  * Append-only per CSV (format fetch.py di vault/09-Inbox/Session-2026-10-02-skrip/: `t,o,h,l,c,v` dan `t,rate`). Baris yang sudah ada tidak pernah ditimpa;
    bar baru harus tepat hari berikutnya; bolong TIDAK diloncati - berhenti di hari yang belum terbit dan dilaporkan.
  * Funding: baris baru harus > baris terakhir + 1 menit (menghindari menghitung ganda peristiwa yang sama dari REST dan zip bulanan).
  * Estimasi: hanya HARI LENGKAP (3 peristiwa sekaligus atau tidak sama sekali), mulai sesudah peristiwa aktual terakhir; menit yang hilang = berhenti, tidak ditebak;
    baris estimasi tidak pernah diubah dan tidak diganti saat funding aktual terbit (log galat estimasi-vs-aktual terkumpul sendiri).
  * Berkas seed harus sudah ada (alat ini hanya MEMPERPANJANG deret, tidak membuat riwayat dari nol). Kegagalan jaringan dilaporkan; tidak ada yang ditebak.

Pakai:  python -X utf8 tools/feed_bars.py                       # perbarui ledger/bars untuk 16 perp (kline + funding)
        python -X utf8 tools/feed_bars.py --dry-run             # hanya laporkan apa yang akan ditambahkan
        python -X utf8 tools/feed_bars.py --symbols BTCUSDT --spot --no-funding
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
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

from engine import funding_est as fest        # noqa: E402
from engine.series import DAY_MS               # noqa: E402
from engine.spec import PERP_UNIVERSE          # noqa: E402

VISION = "https://data.binance.vision/data"
FAPI = "https://fapi.binance.com"
UA = {"User-Agent": "Mozilla/5.0 (fabius-feed/1.0)"}
FUND_DEDUPE_MS = 60_000      # peristiwa funding yang sama dari REST dan zip bulanan beda hitungan milidetik; interval nyata >= 1 jam


class FeedError(Exception):
    pass


def http_get(url: str, tries: int = 3, timeout: int = 40) -> Optional[bytes]:
    """Isi URL; None bila 404 (belum terbit). Kegagalan lain (403/451/jaringan) = FeedError setelah percobaan ulang: tidak pernah ditebak."""
    last = "?"
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            last = f"HTTP {e.code}"
            if e.code not in (429, 500, 502, 503, 504):
                break
        except Exception as e:  # noqa: BLE001
            last = f"{type(e).__name__}"
        time.sleep(1 + i)
    raise FeedError(f"{last} untuk {url.split('?')[0]}")


def day_start(ms: int) -> int:
    return (ms // DAY_MS) * DAY_MS


def date_of(ms: int) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).strftime("%Y-%m-%d")


def last_t(path: str) -> Optional[int]:
    """Waktu baris terakhir sebuah CSV (ms) atau None bila berkas tidak ada / tanpa baris data."""
    if not os.path.exists(path):
        return None
    out = None
    with open(path, newline="") as f:
        for row in csv.reader(f):
            if row and row[0].strip().lstrip("-").replace(".", "", 1).isdigit():
                out = int(float(row[0]))
    return out


def _ms(t: int) -> int:
    return t // 1000 if t > 10**14 else t          # spot memakai mikrodetik sejak 2025


def parse_kline_zip(blob: bytes) -> List[Tuple[int, float, float, float, float, float]]:
    z = zipfile.ZipFile(io.BytesIO(blob))
    rows = []
    with z.open(z.namelist()[0]) as f:
        for r in csv.reader(io.TextIOWrapper(f)):
            if not r or not r[0].strip().lstrip("-").isdigit():
                continue                              # header
            rows.append((_ms(int(r[0])), float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])))
    return rows


def parse_funding_zip(blob: bytes) -> List[Tuple[int, float]]:
    z = zipfile.ZipFile(io.BytesIO(blob))
    rows = []
    with z.open(z.namelist()[0]) as f:
        for r in csv.reader(io.TextIOWrapper(f)):
            if not r or not r[0].strip().lstrip("-").isdigit():
                continue
            rows.append((_ms(int(r[0])), float(r[2])))      # calc_time, interval_hours, last_funding_rate
    return sorted(rows)


def _valid_bar(row, t_expected: int) -> Optional[str]:
    t, o, h, l, c, v = row
    if t != t_expected:
        return f"waktu bar {date_of(t)} != hari yang diharapkan {date_of(t_expected)}"
    for x in (o, h, l, c):
        if not (math.isfinite(x) and x > 0):
            return "harga tidak positif/finite"
    if not (math.isfinite(v) and v >= 0):
        return "volume tidak valid"
    if h < max(o, c) * (1 - 1e-9) or l > min(o, c) * (1 + 1e-9):
        return "high/low tidak mengurung open/close"
    return None


def update_klines(bars_dir: str, kind: str, sym: str, today_ms: int, fetch: Callable[[str], Optional[bytes]] = http_get,
                  dry_run: bool = False) -> dict:
    """Perpanjang `fut_<SYM>_1d.csv` (kind='fut') atau `spot_<SYM>_1d.csv` (kind='spot') dengan bar harian yang sudah tertutup dan terbit."""
    path = os.path.join(bars_dir, f"{kind}_{sym}_1d.csv")
    lt = last_t(path)
    rep = {"sym": sym, "kind": kind, "added": 0, "last": date_of(lt) if lt else None, "stop": None}
    if lt is None:
        rep["stop"] = "berkas seed tidak ada (alat ini hanya memperpanjang)"
        return rep
    market = "futures/um" if kind == "fut" else "spot"
    nxt, rows_out = lt + DAY_MS, []
    while nxt < today_ms:
        d = date_of(nxt)
        try:
            blob = fetch(f"{VISION}/{market}/daily/klines/{sym}/1d/{sym}-1d-{d}.zip")
        except FeedError as e:
            rep["stop"] = f"{d}: {e}"
            break
        if blob is None:
            rep["stop"] = f"{d}: belum terbit"
            break
        try:
            got = [r for r in parse_kline_zip(blob) if r[0] == nxt]
        except Exception as e:  # noqa: BLE001
            rep["stop"] = f"{d}: zip tidak terbaca ({type(e).__name__})"
            break
        if len(got) != 1:
            rep["stop"] = f"{d}: {len(got)} baris untuk hari itu (harus 1)"
            break
        bad = _valid_bar(got[0], nxt)
        if bad:
            rep["stop"] = f"{d}: {bad}"
            break
        rows_out.append(got[0])
        nxt += DAY_MS
    if rows_out and not dry_run:
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            for r in rows_out:
                w.writerow(r)
    rep["added"] = len(rows_out)
    rep["last"] = date_of(rows_out[-1][0]) if rows_out else rep["last"]
    return rep


def _month_iter(t0: int, t1: int):
    a = dt.datetime.fromtimestamp(t0 / 1000, dt.timezone.utc)
    b = dt.datetime.fromtimestamp(t1 / 1000, dt.timezone.utc)
    y, m = a.year, a.month
    while (y, m) <= (b.year, b.month):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


def update_funding(bars_dir: str, sym: str, today_ms: int, fetch: Callable[[str], Optional[bytes]] = http_get,
                   dry_run: bool = False) -> dict:
    """Perpanjang `fund_<SYM>.csv` (t,rate). Hanya baris dengan waktu < awal hari ini (hari lengkap) dan > baris terakhir + 1 menit."""
    path = os.path.join(bars_dir, f"fund_{sym}.csv")
    lt = last_t(path)
    rep = {"sym": sym, "kind": "fund", "added": 0, "last": date_of(lt) if lt else None, "stop": None}
    if lt is None:
        rep["stop"] = "berkas seed tidak ada (alat ini hanya memperpanjang)"
        return rep
    new: List[Tuple[int, float]] = []
    rest_err = None
    cursor = lt + 1
    try:
        while True:                                   # REST: sampai 1000 baris per panggilan, naik menurut waktu
            blob = fetch(f"{FAPI}/fapi/v1/fundingRate?symbol={sym}&startTime={cursor}&limit=1000")
            if blob is None:
                break
            data = json.loads(blob.decode("utf-8"))
            if not isinstance(data, list) or not data:
                break
            batch = sorted((int(x["fundingTime"]), float(x["fundingRate"])) for x in data)
            new.extend(batch)
            if len(data) < 1000:
                break
            cursor = batch[-1][0] + 1
    except (FeedError, ValueError, KeyError, TypeError) as e:
        rest_err = str(e)
        new = []
    if rest_err is not None:                           # cadangan: zip bulanan untuk bulan yang SUDAH tutup
        this_month = dt.datetime.fromtimestamp(today_ms / 1000, dt.timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        for y, m in _month_iter(lt + 1, today_ms - 1):
            if (y, m) >= (this_month.year, this_month.month):
                break
            try:
                blob = fetch(f"{VISION}/futures/um/monthly/fundingRate/{sym}/{sym}-fundingRate-{y}-{m:02d}.zip")
            except FeedError as e:
                rep["stop"] = f"REST: {rest_err}; zip bulanan {y}-{m:02d}: {e}"
                break
            if blob is None:
                rep["stop"] = f"REST: {rest_err}; zip bulanan {y}-{m:02d} belum terbit"
                break
            new.extend(parse_funding_zip(blob))
    keep: List[Tuple[int, float]] = []
    prev = lt
    for t, r in sorted(new):
        if t >= today_ms or t - prev <= FUND_DEDUPE_MS or not math.isfinite(r):
            continue
        keep.append((t, r))
        prev = t
    if keep and not dry_run:
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            for t, r in keep:
                w.writerow([t, r])
    rep["added"] = len(keep)
    rep["last"] = date_of(keep[-1][0]) if keep else rep["last"]
    if rest_err:
        rep["note"] = f"REST gagal ({rest_err})" + ("; diisi dari zip bulanan (hanya bulan yang sudah tutup)" if keep else "")
    if rest_err and not rep["stop"] and not keep:
        rep["stop"] = f"REST: {rest_err}"
    return rep


def parse_premium_daily(blob: bytes) -> Dict[int, float]:
    """{waktu buka menit (ms): close indeks premium} dari satu zip harian premiumIndexKlines 1m (ada baris header)."""
    z = zipfile.ZipFile(io.BytesIO(blob))
    out: Dict[int, float] = {}
    with z.open(z.namelist()[0]) as f:
        for r in csv.reader(io.TextIOWrapper(f)):
            if not r or not r[0].strip().lstrip("-").isdigit():
                continue
            out[_ms(int(r[0]))] = float(r[4])
    return out


def update_funding_est(bars_dir: str, sym: str, today_ms: int, fetch: Callable[[str], Optional[bytes]] = http_get, dry_run: bool = False) -> dict:
    """Perpanjang `fund_est_<SYM>.csv` (t,rate) dengan ESTIMASI funding hari-hari lengkap sesudah peristiwa aktual/estimasi terakhir (`engine/funding_est.py`).
    Satu hari = tiga peristiwa sekaligus; butuh berkas premium hari itu dan hari sebelumnya. Berhenti di hari yang belum terbit; tidak pernah menebak menit."""
    act = os.path.join(bars_dir, f"fund_{sym}.csv")
    path = os.path.join(bars_dir, f"fund_est_{sym}.csv")
    la, le = last_t(act), last_t(path)
    rep = {"sym": sym, "kind": "fest", "added": 0, "last": date_of(le) if le else None, "stop": None}
    if la is None:
        rep["stop"] = "berkas funding aktual (seed) tidak ada"
        return rep
    base = max(la, le or 0)
    nxt = (base // fest.H8_MS) * fest.H8_MS + fest.H8_MS
    if nxt % DAY_MS:
        rep["stop"] = "peristiwa terakhir jatuh di tengah hari (hari parsial); estimasi hanya untuk hari lengkap"
        return rep
    minutes: Dict[int, float] = {}
    loaded: set = set()
    rows: List[Tuple[int, float]] = []
    d = nxt
    while d < today_ms:
        for need in (d - DAY_MS, d):
            if need in loaded:
                continue
            try:
                blob = fetch(f"{VISION}/futures/um/daily/premiumIndexKlines/{sym}/1m/{sym}-1m-{date_of(need)}.zip")
            except FeedError as e:
                rep["stop"] = f"{date_of(need)}: {e}"
                break
            if blob is None:
                rep["stop"] = f"premium {date_of(need)}: belum terbit"
                break
            try:
                minutes.update(parse_premium_daily(blob))
            except Exception as e:  # noqa: BLE001
                rep["stop"] = f"premium {date_of(need)}: zip tidak terbaca ({type(e).__name__})"
                break
            loaded.add(need)
        if rep["stop"]:
            break
        ev = fest.estimate_day(sym, minutes, d)
        if ev is None:
            rep["stop"] = f"premium {date_of(d)}: menit hilang (< 480 menit sebelum satu peristiwa)"
            break
        rows.extend(ev)
        d += DAY_MS
    if rows and not dry_run:
        new_file = not os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            if new_file:
                w.writerow(["t", "rate"])
            for t_ms, r in rows:
                w.writerow([t_ms, r])
    rep["added"] = len(rows)
    rep["last"] = date_of(rows[-1][0]) if rows else rep["last"]
    return rep


def update_all(bars_dir: str, symbols: List[str], today_ms: int, spot: bool = False, funding: bool = True,
               dry_run: bool = False, fetch: Callable[[str], Optional[bytes]] = http_get, est: bool = True) -> List[dict]:
    jobs = ([("fut", s) for s in symbols] + ([("spot", s) for s in symbols] if spot else []) + ([("fund", s) for s in symbols] if funding else [])
            + ([("fest", s) for s in symbols] if funding and est else []))

    def run(job):
        kind, s = job
        try:
            if kind == "fund":
                return update_funding(bars_dir, s, today_ms, fetch, dry_run)
            if kind == "fest":
                return update_funding_est(bars_dir, s, today_ms, fetch, dry_run)
            return update_klines(bars_dir, kind, s, today_ms, fetch, dry_run)
        except Exception as e:  # noqa: BLE001
            return {"sym": s, "kind": kind, "added": 0, "last": None, "stop": f"galat tak terduga: {type(e).__name__}: {e}"}

    with ThreadPoolExecutor(max_workers=8) as ex:
        return list(ex.map(run, jobs))


def main() -> int:
    ap = argparse.ArgumentParser(description="Perpanjang CSV bar harian ledger paper dari sumber publik (hanya bar tertutup).")
    ap.add_argument("--bars", default=os.path.join(ROOT, "ledger", "bars"))
    ap.add_argument("--symbols", default=",".join(PERP_UNIVERSE))
    ap.add_argument("--spot", action="store_true", help="juga kline spot (B3/B5)")
    ap.add_argument("--no-funding", action="store_true")
    ap.add_argument("--no-est", action="store_true", help="jangan memperbarui estimasi funding (fund_est_*.csv)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--today", help="YYYY-MM-DD (UTC) mengganti hari ini (uji)")
    a = ap.parse_args()
    today = int(dt.datetime.strptime(a.today, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp() * 1000) if a.today else day_start(int(time.time() * 1000))
    syms = [s.strip() for s in a.symbols.split(",") if s.strip()]
    reps = update_all(a.bars, syms, today, spot=a.spot, funding=not a.no_funding, dry_run=a.dry_run, est=not a.no_est)
    stuck = 0
    for r in reps:
        flag = "" if not r["stop"] else "  ! " + r["stop"]
        note = "" if not r.get("note") else "  (" + r["note"] + ")"
        stuck += 1 if r["stop"] else 0
        print(f"{r['kind']:5} {r['sym']:10} +{r['added']:<3} terakhir {r['last'] or '-'}{flag}{note}")
    print(f"\n{'DRY-RUN: ' if a.dry_run else ''}{sum(r['added'] for r in reps)} baris ditambahkan; {stuck} deret berhenti sebelum hari ini "
          f"(hari yang belum terbit atau sumber tak terjangkau - TIDAK diisi, TIDAK ditebak).")
    return 0 if not stuck else 3


if __name__ == "__main__":
    sys.exit(main())
