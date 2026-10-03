"""Anggaran kesalahan gerbang masuk buku slot (P90 §1; keputusan F-D88, 3 Okt 2026). Fungsi murni + kunci; belum dipakai gerbang (itu P83/P90).

  A1  peluang bot TANPA edge lolos gerbang pada SATU pengajuan jujur <= 5 %. Gerbang adalah saringan PERTAMA: tidak ada sinyal yang dijual sebelum bot juga lolos
      uji maju F-D16 (terkunci, F-D84), sehingga peluang bot tanpa edge sampai dijual ~ A1 x (positif-palsu F-D16, kasar <= 2,5 %) ~ 0,13 %.
  A2  rata-rata penerimaan palsu per KELUARGA penerbit per tahun <= 0,2. Ditegakkan dengan pengeluaran alpha harmonik: pengajuan ke-k dari keluarga yang sama
      dalam 365 hari dinilai dengan alpha = A1 / k. Batas antrean sekarang (`SlotParams`: 2 pengajuan berjalan, jeda 30 hari sesudah penolakan) membolehkan
      paling banyak 26 pengajuan per tahun -> A1 x H(26) = 0,193 <= 0,2. Tanpa pinalti: 26 x 5 % = 1,3 per tahun.
  A3  daya minimum: TIDAK diberi angka. Riwayat beberapa tahun membatasi daya apa pun ambangnya (plafon aritmetika di vault/08-Backlog/08 §1).

Pendekatan (normal untuk Sharpe taksiran, hasil iid) dan angka F-D16 kasar ditulis terang di vault; kuncinya mengikat angka DAN parameter antrean, karena
melonggarkan antrean diam-diam akan menjebol A2.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .locks import LOCK_DIR
from .slots import SlotParams
from .spec import sha0x

LOCK_FILE = os.path.join(LOCK_DIR, "anggaran.lock.json")
LOCK_V = 1


@dataclass(frozen=True)
class Anggaran:
    a1_per_pengajuan: float = 0.05
    a2_per_keluarga_tahun: float = 0.2
    jendela_hari: int = 365
    pengeluaran_alpha: str = "harmonik: pengajuan ke-k dari keluarga yang sama dalam jendela dinilai dengan alpha = A1 / k"


def alpha_for(k: int, a: Anggaran = Anggaran()) -> float:
    """Alpha untuk pengajuan ke-k (k >= 1) dari satu keluarga dalam jendela."""
    if k < 1:
        raise ValueError("k mulai dari 1")
    return a.a1_per_pengajuan / k


def max_pengajuan_per_tahun(p: SlotParams = SlotParams(), a: Anggaran = Anggaran()) -> int:
    """Batas atas pengajuan satu keluarga dalam jendela: tiap siklus jeda boleh `queue_max_per_family` pengajuan (semuanya ditolak seketika = kasus terburuk)."""
    return p.queue_max_per_family * ((a.jendela_hari - 1) // p.cooldown_days + 1)


def batas_palsu_per_tahun(n: int, a: Anggaran = Anggaran(), pinalti: bool = True) -> float:
    """Batas atas rata-rata penerimaan palsu per keluarga per tahun untuk n pengajuan tanpa edge (union bound)."""
    return sum(alpha_for(k, a) for k in range(1, n + 1)) if pinalti else n * a.a1_per_pengajuan


def current_params(a: Anggaran = Anggaran(), p: SlotParams = SlotParams()) -> Dict[str, Any]:
    return {"v": LOCK_V, "anggaran": dataclasses.asdict(a),
            "antrean": {"queue_max_per_family": p.queue_max_per_family, "cooldown_days": p.cooldown_days}}


def status(path: Optional[str] = None) -> Dict[str, Any]:
    path = path or LOCK_FILE
    now_sha = sha0x(current_params())
    if not os.path.exists(path):
        return {"state": "BELUM_DIKUNCI", "sha_kini": now_sha, "sha_kunci": None, "dikunci": None}
    try:
        with open(path, encoding="utf-8") as f:
            lock = json.load(f)
        stored = lock["sha"]
        if sha0x(lock["params"]) != stored:
            return {"state": "RUSAK", "sha_kini": now_sha, "sha_kunci": stored, "dikunci": lock.get("dikunci")}
    except (OSError, ValueError, KeyError, TypeError):
        return {"state": "RUSAK", "sha_kini": now_sha, "sha_kunci": None, "dikunci": None}
    return {"state": "TERKUNCI" if stored == now_sha else "MENYIMPANG", "sha_kini": now_sha, "sha_kunci": stored, "dikunci": lock.get("dikunci")}


def write_lock(note: str, now_iso: Optional[str] = None, path: Optional[str] = None) -> Dict[str, Any]:
    path = path or LOCK_FILE
    if not note or not note.strip():
        raise ValueError("catatan wajib (siapa yang menyetujui dan kapan)")
    if os.path.exists(path):
        raise FileExistsError("kunci anggaran sudah ada: angka baru = keputusan baru + kunci v2, bukan timpa")
    params = current_params()
    n = max_pengajuan_per_tahun()
    if batas_palsu_per_tahun(n) > Anggaran().a2_per_keluarga_tahun:
        raise ValueError(f"A2 tidak terpenuhi pada batas antrean sekarang ({n} pengajuan/tahun): perketat antrean atau ubah keputusan")
    lock = {"v": LOCK_V, "sha": sha0x(params), "params": params,
            "dikunci": now_iso or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "catatan": note.strip()}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(lock, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    return lock
