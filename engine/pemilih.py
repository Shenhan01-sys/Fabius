"""Bot AKTIF Fabius per bar dari pilihan agent analis (P143, F-D102) - aturan DIKUNCI sebelum dipakai; siapa pun bisa menghitungnya ulang dari
SelectionAnchor (pilihan) + ledger paper publik (skor).

Untuk penutupan bar C (pilihan yang dikomit sebelum C):
  1. tidak ada pilihan sama sekali -> bot identitas (penghuni buku slot; hari ini B1-TREND);
  2. ada agent dengan >= `min_terskor` pilihan terskor (final, atau provisional bila final belum ada) -> PEMIMPIN = agent dengan jumlah selisih
     (net bot pilihannya - net bot identitas, bar yang sama) tertinggi atas `jendela` pilihan terskor terakhirnya; seri -> agentId terkecil.
     Pemimpin memilih untuk C -> bot itu;
  3. selain itu -> suara terbanyak di antara pilihan untuk C; seri -> bot identitas bila ikut seri, selain itu id bot terkecil (abjad).
Skor dihitung HANYA dari bar yang sudah ditutup sebelum C (tidak ada skor yang memakai hasil bar C sendiri).
Mengubah satu angka = keputusan baru + kunci v2 (`engine/locks/pemilih.lock.json`), bukan timpa. Fungsi murni.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .locks import LOCK_DIR
from .spec import sha0x

LOCK_FILE = os.path.join(LOCK_DIR, "pemilih.lock.json")
LOCK_V = 1


@dataclass(frozen=True)
class PemilihParams:
    min_terskor: int = 20
    jendela: int = 30


def pemimpin(skor: Dict[int, List[Tuple[int, float]]], sebelum: int, p: PemilihParams = PemilihParams()) -> Optional[Tuple[int, float, int]]:
    """`skor[agentId]` = [(barClose, selisih)] terskor. Hanya bar < `sebelum`. -> (agentId, jumlah selisih jendela, n terskor) atau None."""
    best = None
    for aid in sorted(skor):
        xs = sorted((c, v) for c, v in skor[aid] if c < sebelum)
        if len(xs) < p.min_terskor:
            continue
        s = sum(v for _, v in xs[-p.jendela:])
        if best is None or s > best[1]:
            best = (aid, s, len(xs))
    return best


def aktif(pilihan: Dict[int, str], skor: Dict[int, List[Tuple[int, float]]], identitas: str, bar_close: int,
          p: PemilihParams = PemilihParams()) -> Tuple[str, str]:
    """-> (bot aktif, alasan). `pilihan` = {agentId: bot} yang dikomit untuk `bar_close`."""
    if not pilihan:
        return identitas, "tidak ada pilihan agent untuk bar ini -> bot identitas"
    lead = pemimpin(skor, bar_close, p)
    if lead is not None and lead[0] in pilihan:
        return pilihan[lead[0]], (f"pemimpin agent {lead[0]} (selisih {lead[1] * 1e4:+.1f} bps atas {min(lead[2], p.jendela)} pilihan terskor terakhir)"
                                  f" memilih {pilihan[lead[0]]}")
    votes = Counter(pilihan.values())
    top = max(votes.values())
    tied = sorted(b for b, n in votes.items() if n == top)
    bot = identitas if identitas in tied else tied[0]
    why = "belum ada agent dengan rekam jejak cukup" if lead is None else f"pemimpin agent {lead[0]} tidak memilih bar ini"
    return bot, f"{why} -> suara terbanyak {dict(sorted(votes.items()))}" + (" (seri -> bot identitas)" if len(tied) > 1 and bot == identitas else "")


# ---------------------------------------------------------------- kunci (pola engine/harga.py)

def current_params(p: PemilihParams = PemilihParams()) -> Dict[str, Any]:
    return {"v": LOCK_V, "pemilih_bot_aktif": asdict(p), "aturan": "identitas bila tanpa pilihan; pemimpin (selisih vs identitas) bila ada; selain itu suara terbanyak, seri -> identitas"}


def status(p: PemilihParams = PemilihParams(), path: str = LOCK_FILE) -> Dict[str, Any]:
    now_sha = sha0x(current_params(p))
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


def write_lock(note: str, now_iso: Optional[str] = None, p: PemilihParams = PemilihParams(), path: str = LOCK_FILE) -> Dict[str, Any]:
    if not note or not note.strip():
        raise ValueError("catatan wajib (siapa yang menyetujui dan kapan)")
    if os.path.exists(path):
        raise FileExistsError("kunci pemilih sudah ada: angka baru = keputusan baru + kunci v2, bukan timpa")
    params = current_params(p)
    lock = {"v": LOCK_V, "sha": sha0x(params), "params": params,
            "dikunci": now_iso or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "catatan": note.strip()}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(lock, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    return lock
