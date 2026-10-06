"""P161 B1c: spesifikasi bot penerbit yang LOLOS_SHADOW -> ikut jam maju (ledger paper harian) seperti bot Fabius.

Sumber kebenaran = registri P83 hash-berantai + salinan publik formulir (`ledger/pengajuan/masuk/<submission_sha>.json`, ditulis peninjau).
`BotSpec` DISUSUN ULANG dari formulir lewat `submission.to_botspec` setelah submission_sha + spec_sha formulir itu cocok dengan catatan LOLOS_SHADOW
di registri; berkas `spec/<bot_id>.json` hanya ringkasan untuk manusia/web dan tidak dipercaya mentah. Registri rusak = tidak ada bot penerbit.
"""
from __future__ import annotations

import copy
import json
import os
from typing import Dict, List, Tuple

from . import registri, submission
from .spec import SPECS, BotSpec

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def penerbit(root: str = ROOT) -> Tuple[Dict[str, BotSpec], List[str]]:
    """-> ({bot_id: BotSpec} bot penerbit yang lolos gerbang dan berhak jam maju, masalah)."""
    d, masalah = rincian(root)
    return {b: x["spec"] for b, x in d.items()}, masalah


def rincian(root: str = ROOT) -> Tuple[Dict[str, dict], List[str]]:
    """-> ({bot_id: {spec, issuer, payout, pembunuh (terstruktur), submission_sha, t_lolos}}, masalah). Dipakai epoch buku (B1d)."""
    d = os.path.join(root, "ledger", "pengajuan")
    path = os.path.join(d, "registri.jsonl")
    if not os.path.exists(path):
        return {}, []
    try:
        entries = registri.load(path)
    except registri.RegistriError as e:
        return {}, [f"registri tak terbaca: {e}"]
    masalah = registri.verify(entries)
    if masalah:
        return {}, [f"registri rusak: {masalah[0]}"]
    out: Dict[str, dict] = {}
    for e in entries:
        if e.get("vonis") != registri.LOLOS:
            continue
        f = os.path.join(d, "masuk", f"{e['submission_sha']}.json")
        if not os.path.exists(f):
            masalah.append(f"{e['bot_id']}: salinan formulir tidak ada")
            continue
        with open(f, encoding="utf-8") as fh:
            sub = copy.deepcopy(json.load(fh)["submission"])
        sub["identity"]["contact"] = "disimpan privat di gerbang"              # tidak ikut hash
        if submission.submission_sha(sub) != e["submission_sha"] or submission.spec_sha_of(sub) != e["spec_sha"]:
            masalah.append(f"{e['bot_id']}: formulir tidak cocok dengan registri - tidak dijalankan")
            continue
        if e["bot_id"] in SPECS or e["bot_id"] in out:
            masalah.append(f"{e['bot_id']}: id bentrok - tidak dijalankan")
            continue
        out[e["bot_id"]] = {"spec": submission.to_botspec(sub), "issuer": e["issuer"], "payout": e["payout"], "pembunuh": sub["theory"]["pembunuh"],
                            "submission_sha": e["submission_sha"], "t_lolos": e["t_s"]}
    return out, masalah


def pnl_sejak_sinyal(records, window_sinyal: int) -> Tuple[List[float], int]:
    """PnL harian net (settle) sejak `window_sinyal` sinyal maju terakhir + jumlah sinyal maju - masukan `slots.killer_triggered`."""
    ticks = [(int(r["asof"]), len(r.get("signal_ids", []))) for r in records if r.get("type") == "tick"]
    n = sum(k for _, k in ticks)
    mulai, hitung = None, 0
    for t, k in reversed(ticks):
        hitung += k
        if hitung >= window_sinyal:
            mulai = t
            break
    if mulai is None:
        return [], n
    return [float(r["net"]) for r in records if r.get("type") == "settle" and int(r["bar"]) >= mulai], n


def semua(root: str = ROOT) -> Dict[str, BotSpec]:
    """Bot Fabius + bot penerbit yang lolos (untuk jam maju dan verifikasi ledger)."""
    return {**SPECS, **penerbit(root)[0]}
