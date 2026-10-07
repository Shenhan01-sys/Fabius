"""Registri bot: bot_id -> fungsi `targets(spec, data) -> list[Target]`. Satu jalur kode untuk live dan replay."""
from __future__ import annotations

from .. import feed, kode, rule
from . import b1_trend, b2_rs, b3_carry, b4_listing_fade, b5_core_rwa, b6_bounce

REGISTRY = {
    "B1-TREND": b1_trend.targets,
    "B2-RS": b2_rs.targets,
    "B3-CARRY": b3_carry.targets,
    "B4-LISTING-FADE": b4_listing_fade.targets,
    "B5-CORE-RWA": b5_core_rwa.targets,
    "B6-BOUNCE": b6_bounce.targets,
    rule.RULE_METHOD: rule.targets,                  # P167a: bot kind=rule; aturannya di `spec.konstanta["rule"]`
    kode.KODE_METHOD: kode.targets,                  # P167b: bot kind=code; bobot dari pelari sandbox (kode privat, `spec.konstanta["kode"]` = sha)
    feed.FEED_METHOD: feed.targets,                  # P167c: bot kind=feed TIDAK bisa direplay; fungsi ini melempar NotImplementedError (G* tak terukur)
}

# Hipotesis nol yang bermakna per metode (gerbang G8). Bawaan "waktu": bot mengklaim keterampilan timing/seleksi, jadi
# dibandingkan dengan pengacakan waktu (pergeseran melingkar) pada eksposur yang sama. "alokasi": bot menjual CAMPURAN aset yang
# bobotnya nyaris konstan - placebo waktu tidak bermakna (bobot yang digeser hampir sama) - jadi dibandingkan dengan memegang
# aset risiko utamanya saja (buy&hold) pada Sharpe DAN MDD, sama dengan pembunuh B5 yang sudah tertulis di spesifikasinya.
# P89: SETIAP metode di REGISTRY mendeklarasikan jenis nolnya secara EKSPLISIT (tanpa bawaan diam-diam); metode tanpa deklarasi = G8 GAGAL.
# "tidak_berlaku" = bot yang tidak bisa direplay (feed): gerbang replay ditulis N/A, bukan diuji.
NULL_KIND = {
    "B1-TREND": ("waktu", ""),
    "B2-RS": ("waktu", ""),
    "B3-CARRY": ("waktu", ""),
    "B4-LISTING-FADE": ("waktu", ""),
    "B5-CORE-RWA": ("alokasi", "BTCUSDT"),
    "B6-BOUNCE": ("waktu", ""),
    rule.RULE_METHOD: ("waktu", ""),
    kode.KODE_METHOD: ("waktu", ""),
    feed.FEED_METHOD: ("tidak_berlaku", "bot feed tidak bisa direplay"),
}

# Bot dengan jadwal berfase mendeklarasikan varian fasenya; gerbang G6 menuntut hasil tidak bergantung pada satu fase.
# P89: SETIAP metode dideklarasikan; None = TIDAK berfase (G6 tidak berlaku); metode tanpa deklarasi = G6 GAGAL.
PHASE_VARIANTS = {
    "B1-TREND": None,
    "B2-RS": b2_rs.phase_variants,
    "B3-CARRY": None,
    "B4-LISTING-FADE": None,
    "B5-CORE-RWA": b5_core_rwa.phase_variants,
    "B6-BOUNCE": None,
    rule.RULE_METHOD: None,
    kode.KODE_METHOD: None,
    feed.FEED_METHOD: None,
}


def deklarasi_kurang() -> list:
    """Metode di REGISTRY yang belum mendeklarasikan jenis nol (G8) atau varian fase (G6). Harus kosong (tes)."""
    return sorted(m for m in REGISTRY if m not in NULL_KIND or m not in PHASE_VARIANTS)
