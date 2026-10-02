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


def load_csv_dir(dirpath: str, symbols: List[str]) -> MarketData:
    """Muat `fut_<SYM>_1d.csv` (perp), `spot_<SYM>_1d.csv` (spot) dan `fund_<SYM>.csv` (funding 8 j: t, rate)."""
    md = MarketData()
    for s in symbols:
        fut = _read_kline_csv(os.path.join(dirpath, f"fut_{s}_1d.csv"))
        if fut is not None:
            md.perp[s] = fut
        spot = _read_kline_csv(os.path.join(dirpath, f"spot_{s}_1d.csv"))
        if spot is not None:
            md.spot[s] = spot
        fp = os.path.join(dirpath, f"fund_{s}.csv")
        if os.path.exists(fp):
            per_day: Dict[int, float] = {}
            with open(fp, newline="") as f:
                rd = csv.reader(f)
                next(rd, None)
                for r in rd:
                    t = int(float(r[0]))
                    day = (t // DAY_MS) * DAY_MS
                    per_day[day] = per_day.get(day, 0.0) + float(r[1])
            md.funding[s] = per_day
    return md
