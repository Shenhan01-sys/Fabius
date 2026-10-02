"""B1-TREND: long bila penutupan > penutupan N hari lalu, selain itu flat. Bobot sama rata atas aset yang punya data."""
from __future__ import annotations

from typing import List

from ..data import MarketData, aligned_closes
from ..spec import BotSpec
from ..target import Target


def targets(spec: BotSpec, data: MarketData) -> List[Target]:
    n = int(spec.param)
    assets = [a for a in spec.universe if a in data.perp]
    grid, closes = aligned_closes(data.perp, assets)
    out: List[Target] = []
    for i, t in enumerate(grid):
        avail = [a for a in assets if closes[a][i] is not None]
        if not avail:
            continue
        w = {}
        for a in avail:
            if i - n >= 0 and closes[a][i - n] is not None and closes[a][i] > closes[a][i - n]:
                w[a] = 1.0 / len(avail)
        out.append(Target(spec.bot_id, t, w, {"n_aset": len(avail), "N": n}))
    return out
