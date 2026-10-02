"""Rekonstruksi funding Binance dari indeks premium 1 menit (P92; F-D76). Hanya stdlib; tidak menyentuh jaringan.

Kenapa ada: funding BARU hanya bisa diambil dari zip bulanan (terbit awal bulan berikutnya) karena REST `fapi` tertutup dari laptop builder (TLS terpotong) dan dari
runner GitHub (HTTP 451). Berkas harian `premiumIndexKlines` 1m di data.binance.vision terbit ±09:10Z hari berikutnya dan terjangkau dari keduanya, dan rumus funding
Binance memakainya: F = P + clamp(I - P, -0,05 %, +0,05 %), P = rata-rata tertimbang waktu indeks premium per menit pada interval (bobot menit ke-i = i, i = 1..480
untuk 8 jam), I = 0,01 % per interval 8 jam.

Ini ESTIMASI, bukan funding. Terukur pada peristiwa yang sudah diketahui (Jun-Agu 2026, 16 perp, 4.368 peristiwa; I per simbol dipilih dari Mar-Mei, diuji di luar sampel -
`vault/09-Inbox/Session-2026-10-02-skrip/run15_funding_reconstruct.py`): MAE 0,056 bps per peristiwa (median 0,033; p95 0,20; maks 0,93), per hari-simbol MAE 0,107 bps
(p99 0,55; maks 1,3), bias rata-rata +0,025 bps/hari (estimasi sedikit di atas aktual). Persis sampai pembulatan 8 desimal hanya pada minoritas peristiwa; funding yang
terkunci di I (|P - I| <= 0,05 %) direkonstruksi persis, galat muncul saat funding bergerak bersama P. Satu simbol punya I yang berbeda: BNBUSDT I = 0.

Pemakaian yang sah: (a) laporan PROVISIONAL (bukan catatan rantai); (b) target bot yang memakai funding (B3-CARRY) bila funding aktual belum terbit, dibekukan di
`ledger/bars/fund_est_<SYM>.csv`. Yang TIDAK sah: menggantikan funding aktual pada `settle` final - itu tetap menunggu zip bulanan.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

MIN_MS = 60_000
H8_MS = 8 * 3_600_000
MINUTES_PER_INTERVAL = 480
CLAMP = 0.0005
INTEREST_DEFAULT = 0.0001            # 0,01 % per interval 8 jam (0,03 %/hari)
INTEREST: Dict[str, float] = {"BNBUSDT": 0.0}      # I = 0: funding BNB = 0 selama |P| <= 0,05 % (dipilih pada Mar-Mei 2026, diuji Jun-Agu; run15)


def interest_for(symbol: str) -> float:
    return INTEREST.get(symbol, INTEREST_DEFAULT)


def estimate_rate(closes: Sequence[float], interest: float, hours: float = 8.0) -> float:
    """Funding satu interval dari close indeks premium per menit (menit ke-1..n, urut waktu): P = sum(i*c_i)/sum(i); F = P + clamp(I*h/8 - P, -0,05 %, +0,05 %)."""
    n = len(closes)
    if n == 0:
        raise ValueError("tidak ada menit")
    p = sum((i + 1) * c for i, c in enumerate(closes)) / (n * (n + 1) / 2)
    i_adj = interest * hours / 8.0
    return p + max(-CLAMP, min(CLAMP, i_adj - p))


def day_events(day_ms: int) -> List[int]:
    """Tiga waktu peristiwa funding pada hari UTC `day_ms` (00:00, 08:00, 16:00)."""
    return [day_ms, day_ms + H8_MS, day_ms + 2 * H8_MS]


def estimate_day(symbol: str, closes_by_minute: Dict[int, float], day_ms: int) -> Optional[List[Tuple[int, float]]]:
    """Tiga peristiwa hari `day_ms` sebagai [(waktu_ms, funding)], dibulatkan 8 desimal seperti Binance. Butuh 480 menit PENUH sebelum tiap peristiwa
    (jadi 8 jam terakhir hari sebelumnya + 16 jam pertama hari ini); None bila ada menit yang hilang - tidak pernah diisi/ditebak."""
    out: List[Tuple[int, float]] = []
    for t0 in day_events(day_ms):
        start = t0 - H8_MS
        closes: List[float] = []
        for k in range(MINUTES_PER_INTERVAL):
            c = closes_by_minute.get(start + k * MIN_MS)
            if c is None:
                return None
            closes.append(c)
        out.append((t0, round(estimate_rate(closes, interest_for(symbol)), 8)))
    return out
