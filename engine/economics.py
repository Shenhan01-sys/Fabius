"""Ekonomi program penerbit bot (F-D72): bagi hasil 60/40 dari PENDAPATAN PENJUALAN SINYAL, bukan dari profit pengikut.

Keputusan builder 2 Okt 2026 (malam): penerbit 60 %, Fabius 40 %. Basis = uang yang dibayar pembeli sinyal bot itu lewat x402
(`payTo` = kontrak pemisah milik bot). Ini versi Python yang tepat-bilangan-bulat sebagai rujukan (dan vektor uji) untuk
`RevenueSplitter` di Solidity kelak; tidak ada angka desimal, tidak ada nilai yang hilang.

Catatan penting (hasil `engine.cli gate`, K5): kalau basisnya PROFIT TRADING Fabius (penerbit ambil 60 % dari bulan untung, Fabius
menanggung bulan rugi), bot yang untung 50 %/tahun pun bisa membuat Fabius rugi - jadi basis profit tidak dipakai.
"""
from __future__ import annotations

from typing import Tuple

BPS = 10_000
ISSUER_SHARE_BPS = 6_000
FABIUS_SHARE_BPS = 4_000
assert ISSUER_SHARE_BPS + FABIUS_SHARE_BPS == BPS


def split(amount: int, issuer_bps: int = ISSUER_SHARE_BPS) -> Tuple[int, int]:
    """Bagi `amount` (bilangan bulat, satuan atom token) menjadi (penerbit, Fabius). Penerbit = floor(amount x bps / 10000);
    Fabius = sisanya (debu pembulatan jatuh ke Fabius). Jumlah keduanya selalu sama dengan `amount`."""
    if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
        raise ValueError("amount harus bilangan bulat >= 0")
    if not isinstance(issuer_bps, int) or isinstance(issuer_bps, bool) or not 0 <= issuer_bps <= BPS:
        raise ValueError("issuer_bps di luar 0..10000")
    issuer = amount * issuer_bps // BPS
    return issuer, amount - issuer


def share_change_allowed(old_fabius_bps: int, new_fabius_bps: int) -> bool:
    """Bagian Fabius hanya boleh TURUN (pola 'bps hanya turun'): tidak ada kenaikan setelah bot masuk, oleh siapa pun."""
    return 0 <= new_fabius_bps <= old_fabius_bps <= BPS


def break_even_subscribers(opex_month_usd: float, price_month_usd: float, fabius_bps: int = FABIUS_SHARE_BPS) -> float:
    """Pelanggan berbayar per bulan yang dibutuhkan agar bagian Fabius menutup biaya operasi bot itu. KALKULATOR, bukan gerbang:
    harga dan biaya operasi adalah asumsi sampai ada penjualan nyata (label 'assumed-builder')."""
    if price_month_usd <= 0 or fabius_bps <= 0:
        raise ValueError("harga dan bagian Fabius harus > 0")
    return opex_month_usd / (price_month_usd * fabius_bps / BPS)
