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
# Metode baru (method_pr) WAJIB mendeklarasikan jenis nolnya di sini.
NULL_KIND = {
    "B5-CORE-RWA": ("alokasi", "BTCUSDT"),
}

# Bot dengan jadwal berfase mendeklarasikan varian fasenya; gerbang G6 menuntut hasil tidak bergantung pada satu fase.
PHASE_VARIANTS = {
    "B2-RS": b2_rs.phase_variants,
    "B5-CORE-RWA": b5_core_rwa.phase_variants,
}
