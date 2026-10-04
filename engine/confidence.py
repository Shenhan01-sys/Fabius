"""Teaser confidence per bot (P137, F-D98/F-D99): angka yang boleh dilihat SEBELUM membayar sinyal - dari rekam jejak MAJU, tanpa detail sinyal.

Definisi (tidak ada angka baru; semuanya dari pemeriksa F-D16 yang dikunci 3 Okt, `engine/fd16.py`):
  confidence = 1 - p, dengan p = p satu sisi bootstrap blok F-D16 untuk H0 "rerata net harian <= 0" pada settle maju final bot itu.
  Artinya: seberapa yakin data MAJU (bukan backtest) bahwa rerata net harian bot ini > 0. Bukan peluang sinyal hari ini benar.
Kematangan = kemajuan menuju ambang F-D16 (sinyal, hari settle, bulan). Sebelum ambang tercapai angkanya dicetak dengan label "awal" - sedikit
hari = angka liar - dan tidak pernah disebut "terukur". Kurang dari 2 hari settle = tidak ada angka sama sekali.

Yang TIDAK pernah ada di teaser: aset, arah, bobot, jumlah posisi, id sinyal, atau apa pun dari tick yang belum dibayar. Isinya hanya status
bot, vonis gerbang v1, vonis F-D16, dan statistik rekam jejak yang memang publik di ledger. Fungsi murni: tidak membaca berkas, jaringan, atau jam.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from . import fd16

DASAR = "1 - p bootstrap blok F-D16 (H0: rerata net harian maju <= 0); bukan peluang sinyal hari ini benar"
LABEL = {"none": "belum terukur", "early": "awal - belum bermakna", "ok": "terukur"}


def teaser(r: fd16.Fd16Result, status: Optional[str], gate_v1: Optional[str], p: fd16.Fd16Params = fd16.Fd16Params()) -> dict:
    """Satu teaser dari hasil F-D16 bot (sesudah `fd16.check`, jadi BH lintas bot sudah dinilai)."""
    pct = None if r.p is None else int(round((1 - r.p) * 100))
    if pct is None:
        label = LABEL["none"]
    elif r.vonis == "BELUM CUKUP DATA":
        label = LABEL["early"]
    else:
        label = LABEL["ok"]
    alasan: List[str] = []
    if status == "INTI":
        alasan.append("status INTI: bot identitas pilihan builder - peran di buku, bukan bukti bot terbaik")
    elif status:
        alasan.append(f"status {status}: berjalan untuk transparansi, bisa digantikan bot yang memenuhi kriteria")
    if gate_v1:
        alasan.append(f"gerbang v1 (backtest terkunci, `engine/book.py::GATE_V1`): {gate_v1}")
    if pct is None:
        alasan.append(f"rekam jejak maju: {r.n_hari} hari settle - butuh >= 2 untuk angka apa pun")
    else:
        alasan.append(f"rekam jejak maju: {r.n_hari} hari settle, rerata net {r.mean_bps:+.2f} bps/hari, CI 95 % "
                      f"[{r.ci_lo_bps:+.2f}, {r.ci_hi_bps:+.2f}] bps")
    alasan.append(f"F-D16 (syarat uang nyata / jual): {r.vonis}" + (f" - {'; '.join(r.alasan[:3])}" if r.alasan else ""))
    return {"bot": r.bot, "confidence_pct": pct, "label": label, "dasar": DASAR, "status": status,
            "gerbang_v1": gate_v1, "fd16": r.vonis,
            "rekam": {"mean_bps": r.mean_bps, "ci_lo_bps": r.ci_lo_bps, "ci_hi_bps": r.ci_hi_bps, "p": r.p},
            "kematangan": {"sinyal": [r.n_sinyal, p.n_sinyal_min], "hari": [r.n_hari, p.hari_min], "bulan": [r.n_bulan, p.bulan_min]},
            "alasan": alasan}


def teasers(ledgers: Dict[str, Sequence[dict]], status: Dict[str, str], gate_v1: Dict[str, str],
            p: fd16.Fd16Params = fd16.Fd16Params()) -> Dict[str, dict]:
    """Teaser untuk semua bot berjam maju; BH F-D16 dinilai lintas SEMUA bot itu (satu keluarga, F-D95)."""
    return {r.bot: teaser(r, status.get(r.bot), gate_v1.get(r.bot), p) for r in fd16.check(ledgers, p)}
