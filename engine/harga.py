"""Harga satu paket sinyal per (bot, bar) dari teaser confidence (P138a, F-D100) - tabel DIKUNCI sebelum data maju ada.

Aturan:
  - confidence = teaser P137 (`engine/confidence.py`: 1 - p bootstrap F-D16 yang terkunci) yang dihitung dari ledger bot SAMPAI tick bar itu saja
    (settle yang datang sesudahnya tidak ikut) -> harga beku per (bot, bar) dan siapa pun bisa menghitungnya ulang dari ledger publik;
  - hanya status "terukur" (ambang F-D16 tercapai) yang boleh menaikkan harga; "belum terukur" / "awal" = harga dasar. Lima hari yang kebetulan bagus
    tidak membuat sinyal mahal;
  - tingkat tertinggi butuh F-D16 LOLOS (termasuk BH lintas bot), bukan hanya angka confidence.
Satuan: atomic FAB (6 desimal; 10_000 = 0,01 FAB). Mengubah satu angka = keputusan baru + kunci v2 (`engine/locks/harga.lock.json`), bukan timpa.
Fungsi murni: tidak membaca berkas (kecuali kunci di `status`), jaringan, atau jam.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Sequence, Tuple

from . import confidence, fd16
from .locks import LOCK_DIR
from .spec import sha0x

LOCK_FILE = os.path.join(LOCK_DIR, "harga.lock.json")
LOCK_V = 1
DESIMAL = 6


@dataclass(frozen=True)
class HargaParams:
    dasar: int = 10_000                    # 0,01 FAB: belum terukur, awal, atau terukur < 60 %
    tingkat: Tuple[Tuple[int, int], ...] = ((60, 50_000), (75, 250_000))   # (confidence minimal %, harga) untuk status terukur
    puncak_min: int = 90                   # >= 90 % DAN F-D16 LOLOS
    puncak: int = 1_000_000                # 1,00 FAB


def harga_dari_teaser(t: dict, p: HargaParams = HargaParams()) -> Tuple[int, str]:
    """-> (atomic FAB, alasan). Satu-satunya tempat tabel dibaca."""
    pct = t.get("confidence_pct")
    if pct is None or t.get("label") != confidence.LABEL["ok"]:
        return p.dasar, f"harga dasar: confidence {t.get('label')} (hanya 'terukur' yang boleh menaikkan harga)"
    if pct >= p.puncak_min and t.get("fd16") == "LOLOS":
        return p.puncak, f"confidence {pct} % >= {p.puncak_min} % dan F-D16 LOLOS"
    harga, why = p.dasar, f"confidence {pct} % < {p.tingkat[0][0]} %"
    for batas, h in p.tingkat:
        if pct >= batas:
            harga, why = h, f"confidence {pct} % >= {batas} %" + (" (F-D16 belum LOLOS: bukan tingkat puncak)" if pct >= p.puncak_min else "")
    return harga, why


def ledger_sampai(records: Sequence[dict], bar: str) -> list:
    """Rekaman ledger sampai (dan termasuk) tick bar itu; settle sesudahnya dibuang -> harga tidak bergeser sesudah bar dijual."""
    out = []
    for r in records:
        out.append(r)
        if r.get("type") == "tick" and r.get("asof_date") == bar:
            return out
    raise KeyError(f"tick {bar} tidak ada di ledger")


def harga_bar(bot: str, bar: str, ledgers: Dict[str, Sequence[dict]], status: Dict[str, str], gate_v1: Dict[str, str],
              p: HargaParams = HargaParams()) -> dict:
    """Harga paket (bot, bar). BH F-D16 dinilai lintas semua bot dengan ledger yang dipotong di tick bar yang SAMA tanggalnya (satu keluarga)."""
    cut = {}
    for b, recs in ledgers.items():
        try:
            cut[b] = ledger_sampai(recs, bar)
        except KeyError:
            if b == bot:
                raise
            cut[b] = [r for r in recs if r.get("type") != "settle" or str(r.get("bar_date", "")) <= bar]
    t = confidence.teasers(cut, status, gate_v1)[bot]
    atomic, why = harga_dari_teaser(t, p)
    return {"bot": bot, "bar": bar, "atomic": atomic, "fab": atomic / 10 ** DESIMAL, "alasan": why, "teaser": t}


# ---------------------------------------------------------------- kunci (pola engine/fd16.py)

def current_params(p: HargaParams = HargaParams()) -> Dict[str, Any]:
    d = asdict(p)
    d["tingkat"] = [list(x) for x in d["tingkat"]]
    return {"v": LOCK_V, "harga_sinyal": d, "desimal": DESIMAL}


def status(p: HargaParams = HargaParams(), path: str = LOCK_FILE) -> Dict[str, Any]:
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


def write_lock(note: str, now_iso: Optional[str] = None, p: HargaParams = HargaParams(), path: str = LOCK_FILE) -> Dict[str, Any]:
    if not note or not note.strip():
        raise ValueError("catatan wajib (siapa yang menyetujui dan kapan)")
    if os.path.exists(path):
        raise FileExistsError("kunci harga sudah ada: angka baru = keputusan baru + kunci v2, bukan timpa")
    params = current_params(p)
    lock = {"v": LOCK_V, "sha": sha0x(params), "params": params,
            "dikunci": now_iso or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "catatan": note.strip()}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(lock, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    return lock
