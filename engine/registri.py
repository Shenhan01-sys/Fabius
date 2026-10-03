"""Registri pengajuan penerbit (P83): penghitung percobaan GLOBAL per keluarga - k dihitung dari registri, bukan diketik operator atau penerbit.

Kenapa: anggaran F-D88 (A2 = 0,2 penerimaan palsu per keluarga per tahun) hanya berlaku bila pengajuan ke-k dinilai dengan alpha A1/k
(`anggaran.gate_params_for`) dan antrean ditegakkan. Sebelum P83, `review --prior-submissions` diisi tangan: angka yang menentukan ketatnya
gerbang bisa lupa diisi, atau diisi kecil.

Bentuk: berkas append-only berantai hash `ledger/pengajuan/registri.jsonl` (rantai hash `engine/ledger.py`; LF murni). Penulisnya peninjau
(`engine.cli review --catat`), bukan rantai GitHub (`paper-ledger` hanya menulis `ledger/paper`, `ledger/bars`, `ledger/book`).

Aturan:
  - keluarga = union-find dompet penerbit + dompet payout atas SEMUA catatan (dua penerbit yang pernah berbagi payout = satu keluarga, F-D71);
  - yang dihitung = pengajuan yang gerbangnya DIJALANKAN dalam 365 hari (`TOLAK_FORMULIR` tidak menjalankan uji statistik, jadi tidak memakan alpha);
  - masa tunggu sesudah penolakan (`slots.can_submit`, 30 hari) dibaca dari registri: batas 26 pengajuan/tahun yang menjadi dasar A2 ditegakkan,
    bukan diandaikan;
  - hanya pengajuan dengan identitas TERVERIFIKASI yang dicatat (dompet diklaim tanpa tanda tangan bisa dipakai menaikkan k keluarga orang lain);
  - `verify` menghitung ulang k setiap catatan dari catatan sebelumnya: k yang dikarang terlihat.

Batas yang jujur: dompet baru = keluarga baru (Sybil; belum ada KYC). Pertahanannya bukan registri ini sendirian: G10 (korelasi dengan buku),
shadow maju, dan F-D16 sebelum uang (gates.py, keterangan KETERBATASAN). Jumlah pengajuan BERJALAN per keluarga (`queue_max_per_family`) belum
dibaca dari sini: itu menunggu antrean pengajuan sungguhan (P82).
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Sequence

from . import ledger
from .anggaran import Anggaran, alpha_for
from .slots import SlotParams, can_submit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRI = os.path.join(ROOT, "ledger", "pengajuan", "registri.jsonl")
TYPE = "pengajuan"
DAY_S = 86_400
TANPA_UJI = ("TOLAK_FORMULIR",)          # vonis yang tidak menjalankan gerbang: tidak memakan alpha, tidak memicu masa tunggu
LOLOS = "LOLOS_SHADOW"
FIELDS = ("type", "t_s", "t_utc", "issuer", "payout", "bot_id", "submission_sha", "spec_sha", "fingerprint", "report_sha", "vonis", "k", "alpha", "n_trials")


class RegistriError(Exception):
    pass


def load(path: str = REGISTRI) -> List[dict]:
    try:
        return ledger.load(path)
    except ledger.LedgerError as e:
        raise RegistriError(str(e)) from None


def _keluarga(entries: Sequence[dict], issuer: str, payout: str) -> set:
    parent: Dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        parent[find(a)] = find(b)

    pairs = [(e["issuer"].lower(), e["payout"].lower()) for e in entries] + [(issuer.lower(), payout.lower())]
    for a, b in pairs:
        union(a, b)
    root = find(issuer.lower())
    return {x for x in list(parent) if find(x) == root}


def status_keluarga(entries: Sequence[dict], issuer: str, payout: str, now_s: int, a: Anggaran = Anggaran(),
                    p: SlotParams = SlotParams()) -> Dict[str, Any]:
    """k untuk pengajuan berikut keluarga ini + apakah ia boleh mengajukan sekarang (masa tunggu sesudah penolakan)."""
    fam = _keluarga(entries, issuer, payout)
    mine = [e for e in entries if e["issuer"].lower() in fam or e["payout"].lower() in fam]
    diuji = [e for e in mine if e["vonis"] not in TANPA_UJI]
    jendela = [e for e in diuji if now_s - int(e["t_s"]) < a.jendela_hari * DAY_S]
    k = len(jendela) + 1
    tolak = [int(e["t_s"]) for e in diuji if e["vonis"] != LOLOS]
    last = max(tolak) if tolak else None
    boleh, alasan = can_submit(family_pending=0, last_rejected_s=last, now_s=now_s, params=p)
    return {"k": k, "alpha": alpha_for(k, a), "sebelumnya_dalam_jendela": len(jendela), "anggota": sorted(fam),
            "penolakan_terakhir_s": last, "boleh_ajukan": boleh, "alasan": alasan}


def record(report: Dict[str, Any], sub: Dict[str, Any], keluarga: Dict[str, Any], now_s: int) -> dict:
    """Catatan (belum di-seal) untuk satu pengajuan yang sudah ditinjau dengan k dari registri."""
    if not report.get("identitas", {}).get("diverifikasi"):
        raise RegistriError("identitas belum terverifikasi: tidak dicatat (dompet tanpa tanda tangan bisa menaikkan k keluarga orang lain)")
    if report.get("vonis") in TANPA_UJI:
        raise RegistriError("formulir ditolak sebelum gerbang: tidak ada uji yang perlu dicatat")
    ident = sub["identity"]
    return {"type": TYPE, "t_s": int(now_s), "t_utc": ledger.utc_iso(int(now_s) * 1000), "issuer": ident["issuer_wallet"], "payout": ident["payout_wallet"],
            "bot_id": report["bot_id"], "submission_sha": report["submission_sha"], "spec_sha": report["spec_sha"], "fingerprint": report["fingerprint"],
            "report_sha": report["report_sha"], "vonis": report["vonis"], "k": int(keluarga["k"]), "alpha": keluarga["alpha"], "n_trials": report["n_trials"]}


def append(path: str, rec: dict, entries: Sequence[dict]) -> dict:
    sealed = ledger.seal(rec, ledger.head(entries))
    ledger.append(path, sealed, entries)
    return sealed


def verify(entries: Sequence[dict], a: Anggaran = Anggaran()) -> List[str]:
    """Rantai hash utuh, jenis + medan lengkap, waktu tidak mundur, dan k tiap catatan = hitung ulang dari catatan sebelumnya."""
    out: List[str] = []
    prev = ledger.ZERO
    for i, e in enumerate(entries):
        if e.get("prev") != prev or e.get("h") != ledger.record_hash(e):
            out.append(f"#{i}: rantai hash putus atau hash salah")
        prev = e.get("h", "")
        missing = [f for f in FIELDS if f not in e]
        if e.get("type") != TYPE or missing:
            out.append(f"#{i}: bukan catatan pengajuan yang lengkap ({', '.join(missing) or e.get('type')})")
            continue
        if i and int(e["t_s"]) < int(entries[i - 1].get("t_s", 0)):
            out.append(f"#{i}: waktu mundur")
        want = status_keluarga(entries[:i], e["issuer"], e["payout"], int(e["t_s"]), a)["k"]
        if int(e["k"]) != want:
            out.append(f"#{i} {e['bot_id']}: k tercatat {e['k']}, hitung ulang {want}")
        if abs(float(e["alpha"]) - alpha_for(int(e["k"]), a)) > 1e-15:
            out.append(f"#{i} {e['bot_id']}: alpha tercatat {e['alpha']} != A1/k")
    return out


def summary(entries: Sequence[dict], now_s: int, a: Anggaran = Anggaran()) -> Optional[str]:
    if not entries:
        return None
    n = sum(1 for e in entries if now_s - int(e["t_s"]) < a.jendela_hari * DAY_S)
    return f"{len(entries)} pengajuan tercatat, {n} dalam {a.jendela_hari} hari terakhir"
