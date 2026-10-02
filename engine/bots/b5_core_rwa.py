"""B5-CORE-RWA: bobot BTC dan emas proporsional 1/sigma; bobot diperbarui bulanan.

sigma = simpangan baku (ddof=1) return harian L hari. Pembaruan di penutupan bar tanggal `hari_pembaruan` (bawaan 1) tiap bulan (UTC); bobot itu
berlaku untuk return bar berikutnya dan seterusnya sampai pembaruan berikut (sama dengan layar: `shift(1)`). Sebelum
pembaruan pertama: 50/50. Emas = kandidat pertama yang ada di `data.spot` ("XAUUSDT" lalu "PAXGUSDT" - PAXG dipakai untuk
riwayat panjang; XAUUSDT Aster baru sejak 2025-11).
"""
from __future__ import annotations

import dataclasses
import datetime as dt
from typing import List, Optional

from ..data import MarketData, aligned_closes
from ..series import pct_change, rolling_std
from ..spec import BotSpec
from ..target import Target


def _gold(spec: BotSpec, data: MarketData) -> Optional[str]:
    for a in spec.konstanta["emas_kandidat"]:
        if a in data.spot:
            return a
    return None


def targets(spec: BotSpec, data: MarketData) -> List[Target]:
    lback = int(spec.param)
    upd_day = int(spec.konstanta["hari_pembaruan"])
    gold = _gold(spec, data)
    if gold is None or "BTCUSDT" not in data.spot:
        return []
    assets = ["BTCUSDT", gold]
    grid, closes = aligned_closes(data.spot, assets)
    # hanya hari ketika kedua aset punya penutupan
    idx = [i for i in range(len(grid)) if closes["BTCUSDT"][i] is not None and closes[gold][i] is not None]
    g = [grid[i] for i in idx]
    cb = [closes["BTCUSDT"][i] for i in idx]
    cg = [closes[gold][i] for i in idx]
    sb = rolling_std(pct_change(cb), lback)
    sg = rolling_std(pct_change(cg), lback)
    wb = 0.5
    out: List[Target] = []
    for j, t in enumerate(g):
        updated = False
        day = dt.datetime.fromtimestamp(t / 1000, dt.timezone.utc).day
        if day == upd_day and sb[j] and sg[j]:
            wb = (1.0 / sb[j]) / ((1.0 / sb[j]) + (1.0 / sg[j]))
            updated = True
        out.append(Target(spec.bot_id, t, {"BTCUSDT": wb, gold: 1.0 - wb},
                          {"L": lback, "emas": gold, "rebalanced": updated}))
    return out


def phase_variants(spec: BotSpec) -> List[BotSpec]:
    """Uji sensitivitas fase (gerbang G6): tanggal pembaruan bulanan yang berbeda."""
    return [dataclasses.replace(spec, konstanta={**spec.konstanta, "hari_pembaruan": d}) for d in (1, 5, 10, 15, 20, 25, 28)]
