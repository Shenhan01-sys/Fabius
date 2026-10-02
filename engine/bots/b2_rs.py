"""B2-RS: long k teratas dan short k terbawah menurut return L hari (dollar-neutral), dirotasi mingguan.

Hari rebalance TIDAK dipilih. Layar eksploratif 2 Okt 2026 memakai `i % 7` dari tanggal pertama data (1 Jan 2020 = Rabu) dan
mencatat Sharpe 1.27-1.29; hari lain memberi 0.29-1.22 pada data yang sama (`python -X utf8 -m engine.golden` mencetak ketujuh
hari). Memilih hari = memilih nasib. Jadi bawaan mesin: `tranche=7` - tujuh sub-buku, sub-buku j direbalance mingguan pada
penutupan hari-UTC j (0 = Senin), bobot gabungan = rerata sub-buku yang sudah aktif. Turnover total sama dengan satu
rebalance mingguan; yang hilang hanyalah ketergantungan pada hari. `tranche=1` + `rebalance_hari_utc` tetap tersedia untuk
pengujian (laporan sensitivitas), BUKAN untuk produksi.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
from typing import Dict, List

from ..data import MarketData, aligned_closes
from ..spec import BotSpec
from ..target import Target


def _weekday(t_ms: int) -> int:
    return dt.datetime.fromtimestamp(t_ms / 1000, dt.timezone.utc).weekday()


def targets(spec: BotSpec, data: MarketData) -> List[Target]:
    lback = int(spec.param)
    k = int(spec.konstanta["k"])
    tranche = int(spec.konstanta.get("tranche", 1))
    min_aset = int(spec.konstanta["min_aset"])
    if tranche not in (1, 7):
        raise ValueError("tranche harus 1 atau 7")
    fixed_wd = spec.konstanta.get("rebalance_hari_utc")
    if tranche == 1 and fixed_wd is None:
        raise ValueError("tranche=1 butuh konstanta rebalance_hari_utc (hanya untuk uji sensitivitas)")
    assets = [a for a in spec.universe if a in data.perp]
    grid, closes = aligned_closes(data.perp, assets)
    books: Dict[int, Dict[str, float]] = {}     # hari-minggu -> bobot sub-buku itu
    out: List[Target] = []
    for i, t in enumerate(grid):
        wd = _weekday(t)
        rebal = False
        if (tranche == 7 or wd == int(fixed_wd)) and i - lback >= 0:
            rets = {}
            for a in assets:
                c1, c0 = closes[a][i], closes[a][i - lback]
                if c1 is not None and c0 not in (None, 0):
                    rets[a] = c1 / c0 - 1.0
            if len(rets) >= min_aset:
                longs = sorted(rets, key=lambda a: (-rets[a], a))[:k]
                shorts = sorted(rets, key=lambda a: (rets[a], a))[:k]
                book = {a: 1.0 / k for a in longs}
                book.update({a: -1.0 / k for a in shorts})
                books[wd] = book
                rebal = True
        if tranche == 7:
            acc: Dict[str, float] = {}
            for b in books.values():
                for a, w in b.items():
                    acc[a] = acc.get(a, 0.0) + w
            n = len(books)
            cur = {a: w / n for a, w in acc.items() if abs(w) > 1e-12} if n else {}
        else:
            cur = dict(books.get(int(fixed_wd), {}))
        if any(closes[a][i] is not None for a in assets):
            out.append(Target(spec.bot_id, t, cur, {"L": lback, "k": k, "tranche": tranche, "rebalanced": rebal}))
    return out


def phase_variants(spec: BotSpec) -> List[BotSpec]:
    """Uji sensitivitas fase (gerbang G6): satu buku, rebalance mingguan di tiap hari-minggu. Bukan untuk produksi."""
    return [dataclasses.replace(spec, konstanta={**spec.konstanta, "tranche": 1, "rebalance_hari_utc": wd}) for wd in range(7)]
