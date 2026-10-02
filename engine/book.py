"""Buku slot awal (genesis) dan bot identitas Fabius (F-D73).

Keputusan builder 2 Okt 2026 (malam): bot identitas harus bot yang **trading instrumen kripto** supaya kelihatan Fabius sungguh
trading; kandidat yang dipilih: B1-TREND (long/flat atas perp kripto mayor; long-only sehingga bisa dieksekusi di Binance Agentic
Wallet kelak). Identitas = PENUNJUKAN (kebal rolling), bukan kelulusan gerbang: catatan gerbang B1 (G8, G10 gagal tipis; 12 bulan
terakhir negatif) tetap tampil, ia mati lewat pembunuhnya sendiri, dan F-D16 tetap berlaku sebelum uang nyata.

Buku genesis hanya berisi bot identitas. Bot Fabius lain (B2, B3, B5, B6) masuk lewat jalur yang SAMA dengan penerbit luar
(gerbang -> shadow -> slot): mereka tidak diberi slot gratis.
"""
from __future__ import annotations

from typing import Dict, List, Sequence

from .slots import FABIUS, Entry
from .spec import PERP_UNIVERSE, SPECS, BotSpec

IDENTITY_BOT_ID = "B1-TREND"
CRYPTO_INSTRUMENTS = frozenset(PERP_UNIVERSE)             # perp kripto mayor; emas/RWA (PAXG, XAU) BUKAN termasuk
# Bot Fabius yang BOLEH punya ledger paper maju (M2): identitas (penunjukan) + yang LOLOS_SHADOW pada kunci v1 (B3-CARRY; epik 07 §7, dicetak ulang
# 2 Okt 2026). B2/B5/B6 TOLAK dan B4 tak terukur: tidak diberi jam maju gratis (mereka lewat gerbang -> shadow -> slot seperti penerbit luar).
# Daftar ini sengaja statis dan terlihat; kunci baru (v2) yang mengubah vonis = keputusan builder + baris baru di sini.
SHADOW_ELIGIBLE = (IDENTITY_BOT_ID, "B3-CARRY")


def trades_crypto_only(spec: BotSpec) -> bool:
    """Bot identitas harus memperdagangkan instrumen kripto SAJA (syarat builder), bukan RWA atau campuran."""
    return bool(spec.universe) and all(a in CRYPTO_INSTRUMENTS for a in spec.universe) and spec.method != "B5-CORE-RWA"


def genesis_book(now_s: int) -> List[Entry]:
    """Buku awal: satu entri, bot identitas. `now_s` = detik Unix saat buku dibuat (WAJIB: tidak ada bawaan)."""
    sp = SPECS[IDENTITY_BOT_ID]
    if not trades_crypto_only(sp):
        raise ValueError(f"{IDENTITY_BOT_ID} bukan bot instrumen-kripto-saja: tidak boleh jadi identitas (F-D73)")
    return [Entry(bot_id=sp.bot_id, issuer=FABIUS, spec_sha=sp.sha(), fingerprint=sp.fingerprint(), admitted_s=now_s,
                  identity=True, score_bps=None, payout="")]


def fabius_specs(book: Sequence[Entry]) -> Dict[str, BotSpec]:
    """Spesifikasi bot Fabius sendiri di buku (yang bisa di-replay); entri penerbit luar tidak termasuk (PnL mereka datang dari ledger shadow)."""
    return {e.bot_id: SPECS[e.bot_id] for e in book if e.issuer == FABIUS and e.bot_id in SPECS}
