"""Data pasar untuk bot + pemuat CSV (format keluaran `fetch.py` di vault/09-Inbox/Session-2026-10-02-skrip/).

Mesin TIDAK mengunduh apa pun sendiri di M1: ia menerima `MarketData`. Pengunduh (Binance Vision / Aster) menyusul di M2
dengan guard umur bar (`engine/freshness.py`).
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .series import DAY_MS, Series


@dataclass(frozen=True)
class ListingEvent:
    """Perp baru di venue. `day1_open_t` = waktu buka bar hari-1 perp (ms UTC); entri di PENUTUPAN bar itu."""
    asset: str
    day1_open_t: int
    day1_close: float
    day1_quote_volume_usd: float


@dataclass
class MarketData:
    perp: Dict[str, Series] = field(default_factory=dict)
    spot: Dict[str, Series] = field(default_factory=dict)
    funding: Dict[str, Dict[int, float]] = field(default_factory=dict)    # aset -> {awal-hari-UTC ms: jumlah funding 8 j hari itu}
    events: List[ListingEvent] = field(default_factory=list)

    def upto(self, t_ms: int) -> "MarketData":
        """Potongan point-in-time: hanya bar dengan waktu buka <= t_ms; funding sampai hari itu; event yang sudah terjadi."""
        return MarketData(
            perp={a: s.upto(t_ms) for a, s in self.perp.items()},
            spot={a: s.upto(t_ms) for a, s in self.spot.items()},
            funding={a: {d: v for d, v in f.items() if d <= t_ms} for a, f in self.funding.items()},
            events=[e for e in self.events if e.day1_open_t <= t_ms],
        )


def aligned_closes(series_by_asset: Dict[str, Series], assets: List[str]):
    """Grid hari gabungan (terurut) dan penutupan per aset yang disejajarkan (None bila tak ada bar)."""
    grid = sorted({t for a in assets for t in series_by_asset[a].t})
    out = {}
    for a in assets:
        s = series_by_asset[a]
        m = dict(zip(s.t, s.c))
        out[a] = [m.get(t) for t in grid]
    return grid, out


def _read_kline_csv(path: str) -> Optional[Series]:
    if not os.path.exists(path):
        return None
    rows = []
    with open(path, newline="") as f:
        rd = csv.reader(f)
        next(rd, None)
        for r in rd:
            rows.append([float(x) for x in r[:6]])
    return Series.from_rows(rows) if rows else None


FUNDING_VIEWS = ("actual", "provisional", "targets")
EST_EVENTS_PER_DAY = 3          # estimasi selalu 3 peristiwa/hari (interval 8 jam, `engine/funding_est.py`); hari yang kurang dari itu tidak dipakai


def _read_funding(path: str, min_events: int = 1) -> Dict[int, float]:
    """{awal-hari-UTC ms: jumlah funding hari itu} dari CSV `t,rate`; hanya hari dengan >= `min_events` peristiwa."""
    per_day: Dict[int, float] = {}
    cnt: Dict[int, int] = {}
    if not os.path.exists(path):
        return per_day
    with open(path, newline="") as f:
        rd = csv.reader(f)
        next(rd, None)
        for r in rd:
            t = int(float(r[0]))
            day = (t // DAY_MS) * DAY_MS
            per_day[day] = per_day.get(day, 0.0) + float(r[1])
            cnt[day] = cnt.get(day, 0) + 1
    return {d: v for d, v in per_day.items() if cnt[d] >= min_events}


def load_csv_dir(dirpath: str, symbols: List[str], funding_view: str = "actual") -> MarketData:
    """Muat `fut_<SYM>_1d.csv` (perp), `spot_<SYM>_1d.csv` (spot) dan funding 8 j (t, rate).

    `funding_view` memilih sumber funding (F-D76; `engine/funding_est.py`):
      "actual"       hanya `fund_<SYM>.csv` (funding AKTUAL dari zip bulanan). Dipakai `settle` final dan verifikasi: bawaan.
      "provisional"  aktual bila ada, selain itu estimasi `fund_est_<SYM>.csv`. Hanya untuk laporan PROVISIONAL; bukan catatan rantai.
      "targets"      estimasi untuk hari >= hari pertama berkas estimasi, aktual untuk hari sebelumnya. Dipakai target bot yang memakai funding (B3-CARRY):
                     estimasi dibekukan (append-only), jadi hitung-ulang sebuah tick tetap sama sesudah funding aktual terbit belakangan."""
    if funding_view not in FUNDING_VIEWS:
        raise ValueError(f"funding_view harus salah satu dari {FUNDING_VIEWS}")
    md = MarketData()
    for s in symbols:
        fut = _read_kline_csv(os.path.join(dirpath, f"fut_{s}_1d.csv"))
        if fut is not None:
            md.perp[s] = fut
        spot = _read_kline_csv(os.path.join(dirpath, f"spot_{s}_1d.csv"))
        if spot is not None:
            md.spot[s] = spot
        fp = os.path.join(dirpath, f"fund_{s}.csv")
        actual = _read_funding(fp)
        est = _read_funding(os.path.join(dirpath, f"fund_est_{s}.csv"), EST_EVENTS_PER_DAY) if funding_view != "actual" else {}
        if funding_view == "actual":
            per_day = actual
        elif funding_view == "provisional":
            per_day = {**est, **actual}
        else:
            start = min(est) if est else None
            per_day = {d: v for d, v in actual.items() if start is None or d < start}
            per_day.update(est)
        if os.path.exists(fp) or per_day:
            md.funding[s] = per_day
    # P129 (F-D95): kejadian listing untuk B4 + deret perp tiap koin barunya (ditulis `tools/listing_events.py`). Dimuat untuk SEMUA pemanggil;
    # bot lain tidak terpengaruh: target dan `data_fingerprint` hanya memakai aset universe-nya sendiri, dan `target_view` mengosongkan kejadian.
    md.events = load_events(dirpath)
    for e in md.events:
        if e.asset not in md.perp:
            fut = _read_kline_csv(os.path.join(dirpath, f"fut_{e.asset}_1d.csv"))
            if fut is not None:
                md.perp[e.asset] = fut
    return md


EVENTS_FILE = "events_um_listing.csv"


def load_events(dirpath: str) -> List[ListingEvent]:
    """`events_um_listing.csv` (asset, day1_open_t, day1_close, day1_quote_volume_usd), terurut hari-1; berkas tidak ada = tidak ada kejadian."""
    p = os.path.join(dirpath, EVENTS_FILE)
    if not os.path.exists(p):
        return []
    with open(p, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f)]
    return sorted((ListingEvent(r["asset"], int(r["day1_open_t"]), float(r["day1_close"]), float(r["day1_quote_volume_usd"])) for r in rows),
                  key=lambda e: (e.day1_open_t, e.asset))
