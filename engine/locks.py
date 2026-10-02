"""Kunci ambang peninjau-bot (F-D72): sidik jari sha256 atas SEMUA angka yang menentukan lolos/gagal, dipasang SEBELUM kandidat luar pertama.

Kenapa: ambang gerbang, KPI, dan slot adalah "kunci jawaban + nilai lulus" ujian seleksi. Kalau ia bisa digeser setelah melihat siapa yang
lolos, seleksi berubah jadi pilih kasih - termasuk oleh kami sendiri (2 Okt 2026 kami mengubah gerbang G8 dua kali setelah melihat hasil
bot sendiri). Setelah dikunci, mengubah SATU angka menghasilkan sidik jari lain = "kunci baru" yang terlihat semua orang (aturan
"pivot = kunci baru", sama dengan spesifikasi bot). Vonis peninjau-bot hanya MENGIKAT bila parameter yang dipakai sama persis dengan kunci.

Kunci tidak dibuat otomatis: `python -X utf8 -m engine.cli lock --write --note "..."` (perlu kata builder). Sidik jari bisa dicatat di vault/commit
dan kelak di chain lewat `LockRegistry`.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import json
import os
from typing import Any, Dict, Optional

from . import economics
from .gates import GateParams
from .kpi import KpiParams
from .slots import SlotParams
from .spec import sha0x

LOCK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locks")
LOCK_FILE = os.path.join(LOCK_DIR, "review.lock.json")
LOCK_V = 1


def current_params(gate: Optional[GateParams] = None, kpi: Optional[KpiParams] = None, slot: Optional[SlotParams] = None) -> Dict[str, Any]:
    """Semua angka yang menentukan vonis, sebagai objek JSON-murni (tuple -> list lewat sha0x)."""
    g, k, s = gate or GateParams(), kpi or KpiParams(), slot or SlotParams()
    return {"v": LOCK_V, "gerbang": dataclasses.asdict(g), "kpi": dataclasses.asdict(k), "slot": dataclasses.asdict(s),
            "ekonomi": {"issuer_bps": economics.ISSUER_SHARE_BPS, "fabius_bps": economics.FABIUS_SHARE_BPS}}


def fingerprint(params: Optional[Dict[str, Any]] = None) -> str:
    return sha0x(params if params is not None else current_params())


def status(gate: Optional[GateParams] = None, kpi: Optional[KpiParams] = None, slot: Optional[SlotParams] = None,
           path: str = LOCK_FILE) -> Dict[str, Any]:
    """{'state': BELUM_DIKUNCI | TERKUNCI | MENYIMPANG | RUSAK, 'sha_kini', 'sha_kunci', 'berkas'}.
    MENYIMPANG = parameter kode sekarang tidak sama dengan yang dikunci (ada yang mengubah angka sesudah kunci)."""
    now_sha = fingerprint(current_params(gate, kpi, slot))
    if not os.path.exists(path):
        return {"state": "BELUM_DIKUNCI", "sha_kini": now_sha, "sha_kunci": None, "berkas": path}
    try:
        with open(path, encoding="utf-8") as f:
            lock = json.load(f)
        stored = lock["sha"]
        if sha0x(lock["params"]) != stored:
            return {"state": "RUSAK", "sha_kini": now_sha, "sha_kunci": stored, "berkas": path}
    except (OSError, ValueError, KeyError, TypeError):
        return {"state": "RUSAK", "sha_kini": now_sha, "sha_kunci": None, "berkas": path}
    return {"state": "TERKUNCI" if stored == now_sha else "MENYIMPANG", "sha_kini": now_sha, "sha_kunci": stored, "berkas": path}


def write_lock(note: str, now_iso: Optional[str] = None, supersede: bool = False, path: str = LOCK_FILE,
               gate: Optional[GateParams] = None, kpi: Optional[KpiParams] = None, slot: Optional[SlotParams] = None) -> Dict[str, Any]:
    """Tulis kunci dari parameter kode SEKARANG. Menolak menimpa kunci yang ada kecuali `supersede=True`, yang memindahkan kunci lama ke
    `locks/history/` (kunci lama tetap terlihat)."""
    if not note or not note.strip():
        raise ValueError("catatan wajib (siapa yang menyetujui dan kapan)")
    params = current_params(gate, kpi, slot)
    sha = fingerprint(params)
    if os.path.exists(path):
        if not supersede:
            raise FileExistsError("kunci sudah ada; pakai supersede=True (kunci lama dipindah ke history, bukan dihapus)")
        hist = os.path.join(os.path.dirname(path), "history")
        os.makedirs(hist, exist_ok=True)
        with open(path, encoding="utf-8") as f:
            old = json.load(f)
        os.replace(path, os.path.join(hist, f"{str(old.get('sha', 'x'))[2:14]}-{(old.get('dikunci') or 'x').replace(':', '')}.json"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lock = {"v": LOCK_V, "sha": sha, "params": params,
            "dikunci": now_iso or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "catatan": note.strip()}
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(lock, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    return lock
