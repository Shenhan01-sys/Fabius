# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/07 - Epik Kolaborasi Bot Terbuka.md §7 dan vault/09-Inbox/Session-2026-10-02.md §8).
# Bukan alat resmi; keluaran = bukan klaim produk. Hanya stdlib + paket `engine/` di akar repo.
"""Sharpe net bot Fabius pada jendela terakhir 6 / 12 / 18 / 24 / 36 "bulan" (1 bulan = 30 hari) - dasar gerbang G4 (RECENT).

    python -X utf8 run11_recent_windows.py                       # memakai ./data (hasil fetch.py)
    set FABIUS_DATA=<folder data>&& python -X utf8 run11_recent_windows.py

Pembacaan yang dicari: peluruhan 12 bulan terakhir pada hampir semua bot (jendela pendek berisik: SE Sharpe ~ 1/sqrt(tahun)).
"""
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from engine.data import load_csv_dir
from engine.replay import replay
from engine.series import DAY_MS, max_drawdown, sharpe
from engine.spec import PERP_UNIVERSE, SPECS

D = os.environ.get("FABIUS_DATA") or str(Path(__file__).resolve().parent / "data")
md = load_csv_dir(D, list(PERP_UNIVERSE) + ["PAXGUSDT", "XAUUSDT"])
WINDOWS = (6, 12, 18, 24, 36)
print("bot           " + "  ".join(f"{m:>3}b" for m in WINDOWS) + "   tahunan(12b)%  MDD(12b)%")
for b in ("B1-TREND", "B2-RS", "B3-CARRY", "B5-CORE-RWA", "B6-BOUNCE"):
    pnl = replay(SPECS[b], md)
    last = pnl[-1][0]
    row = [sharpe([v for t, v in pnl if t > last - m * 30 * DAY_MS]) for m in WINDOWS]
    v12 = [v for t, v in pnl if t > last - 12 * 30 * DAY_MS]
    print(f"{b:13} " + "  ".join(f"{x:+4.2f}" for x in row) + f"   {sum(v12) / len(v12) * 365 * 100:+9.1f}   {max_drawdown(v12) * 100:9.1f}")
print("\nData berakhir:", max(s.t[-1] for s in md.perp.values()) // DAY_MS, "(hari ke-N sejak epoch)")
