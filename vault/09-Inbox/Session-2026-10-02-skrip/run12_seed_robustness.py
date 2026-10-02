# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/07 - Epik Kolaborasi Bot Terbuka.md §5 dan vault/09-Inbox/Session-2026-10-02.md §8).
# Bukan alat resmi; keluaran = bukan klaim produk. Hanya stdlib + paket `engine/` di akar repo.
"""Apakah vonis gerbang G8 (placebo waktu) stabil terhadap seed? Jawabannya TIDAK untuk titik taksir p pada bot yang dekat ambang.

    python -X utf8 run12_seed_robustness.py                       # memakai ./data (hasil fetch.py)
    set FABIUS_DATA=<folder data>&& python -X utf8 run12_seed_robustness.py

Cetakan: p placebo (200 acak) untuk lima seed per bot. B1 jatuh antara 0,040 dan 0,109 pada data 2 Okt 2026 - dua sisi ambang 0,05 -
karena itu `engine/gates.py::g8_placebo` memvonis dengan batas atas 95% galat Monte Carlo, bukan titik taksirnya.
"""
import dataclasses
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from engine.data import load_csv_dir
from engine.gates import GateParams, _Ctx, g8_placebo
from engine.spec import PERP_UNIVERSE, SPECS

D = os.environ.get("FABIUS_DATA") or str(Path(__file__).resolve().parent / "data")
md = load_csv_dir(D, list(PERP_UNIVERSE) + ["PAXGUSDT", "XAUUSDT"])
for bot in ("B1-TREND", "B6-BOUNCE", "B3-CARRY"):
    row = []
    for seed in (1, 2, 3, 4, 5):
        c = _Ctx(SPECS[bot], md, dataclasses.replace(GateParams(), seed=seed), None)
        row.append(g8_placebo(c).value.split(" (")[0].replace("placebo ", ""))
    print(f"{bot:10} G8 per seed 1..5:", " | ".join(row))
