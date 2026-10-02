"""Data sintetis untuk tes: deterministik, tanpa jaringan dan tanpa file di luar folder sementara."""
from __future__ import annotations

import os
import random
from typing import Dict, List, Optional

from engine.data import MarketData
from engine.series import DAY_MS, Series

T0 = 1_577_836_800_000        # 2020-01-01 00:00 UTC (Rabu)
BTC, ETH, BNB = "BTCUSDT", "ETHUSDT", "BNBUSDT"


def mk_series(closes: List[float], t0: int = T0, skip: Optional[List[int]] = None) -> Series:
    """OHLC = penutupan (cukup untuk bot yang hanya memakai penutupan). `skip` = indeks hari yang dibolongkan."""
    rows = [[t0 + i * DAY_MS, c, c, c, c, 1.0] for i, c in enumerate(closes) if not skip or i not in skip]
    return Series.from_rows(rows)


def walk(n: int, seed: int, drift: float = 0.0, vol: float = 0.02, p0: float = 100.0) -> List[float]:
    rnd = random.Random(seed)
    p, out = p0, []
    for _ in range(n):
        p *= 1.0 + rnd.gauss(drift, vol)
        out.append(p)
    return out


def regime_closes(n: int, seed: int, mu: float = 0.012, vol: float = 0.02, block: int = 90, p0: float = 100.0) -> List[float]:
    """Pasar berganti rezim naik/turun tiap `block` hari: pengikut tren punya edge nyata di sini (dan tidak di `walk`)."""
    rnd = random.Random(seed)
    p, out, sign = p0, [], 1
    for i in range(n):
        if i % block == 0:
            sign = 1 if rnd.random() < 0.5 else -1
        p *= 1.0 + sign * mu + rnd.gauss(0.0, vol)
        out.append(p)
    return out


def grow(n: int, rate: float, p0: float = 100.0) -> List[float]:
    return [p0 * (1.0 + rate) ** i for i in range(n)]


def md_perp(closes_by_asset: Dict[str, List[float]], t0: int = T0) -> MarketData:
    return MarketData(perp={a: mk_series(c, t0) for a, c in closes_by_asset.items()})


def write_csvs(d: str, perp: Dict[str, List[float]], spot: Optional[Dict[str, List[float]]] = None,
               fund_per_day: Optional[Dict[str, float]] = None, t0: int = T0) -> None:
    """Tulis format keluaran fetch.py: fut_<S>_1d.csv, spot_<S>_1d.csv (t,o,h,l,c,v) dan fund_<S>.csv (t,rate; 3x per hari)."""
    for kind, bag in (("fut", perp), ("spot", spot or {})):
        for s, closes in bag.items():
            with open(os.path.join(d, f"{kind}_{s}_1d.csv"), "w", newline="") as f:
                f.write("t,o,h,l,c,v\n")
                for i, c in enumerate(closes):
                    f.write(f"{t0 + i * DAY_MS},{c},{c},{c},{c},1.0\n")
    for s, rate in (fund_per_day or {}).items():
        n = len(perp.get(s, spot.get(s) if spot else []))
        with open(os.path.join(d, f"fund_{s}.csv"), "w", newline="") as f:
            f.write("t,rate\n")
            for i in range(n):
                for h in (0, 8, 16):
                    f.write(f"{t0 + i * DAY_MS + h * 3_600_000},{rate / 3.0}\n")
