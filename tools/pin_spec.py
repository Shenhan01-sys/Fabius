"""P161 B1b: pin sha spesifikasi bot penerbit yang LOLOS_SHADOW ke LockRegistry (chain 97), oleh worker Railway (`operator_loop`, seperti
`book_pin`). Label = `bot_id` (unik di registri; awalan B<n>- dan nama "fabius" dicadangkan untuk bot Fabius, jadi tidak bisa meniru label kami).
Hanya spesifikasi yang cocok dengan registri P83 yang sah (submission_sha + spec_sha + vonis LOLOS_SHADOW) yang di-pin.

Pakai (pemeriksaan lokal, tanpa kirim):  python -X utf8 tools/pin_spec.py
"""
from __future__ import annotations

import glob
import json
import os
import sys
from typing import List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, ROOT]

from engine import chain, registri                                   # noqa: E402
import signal_commit as sc                                           # noqa: E402

REPO_URL = "https://github.com/Shenhan01-sys/Fabius"


def sah(workdir: str) -> Tuple[List[dict], List[str]]:
    """-> (spesifikasi yang boleh di-pin, masalah). Urut waktu lolos."""
    reg_path = os.path.join(workdir, "ledger", "pengajuan", "registri.jsonl")
    entries = registri.load(reg_path) if os.path.exists(reg_path) else []
    masalah = registri.verify(entries)
    if masalah:
        return [], [f"registri tidak sah: {masalah[0]}"]
    lolos = {(e["submission_sha"], e["spec_sha"], e["bot_id"]) for e in entries if e.get("vonis") == registri.LOLOS}
    out = []
    for path in sorted(glob.glob(os.path.join(workdir, "ledger", "pengajuan", "spec", "*.json"))):
        s = json.load(open(path, encoding="utf-8"))
        if (s.get("submission_sha"), s.get("spec_sha"), s.get("bot_id")) not in lolos:
            masalah.append(f"{os.path.basename(path)}: tidak cocok dengan registri LOLOS_SHADOW - tidak di-pin")
            continue
        out.append(s)
    return sorted(out, key=lambda s: (s["t_lolos"], s["bot_id"])), masalah


def label_of(s: dict) -> str:
    return s["bot_id"]


def locked_at(ev, registry: str, committer: str, s: dict) -> int:
    return int(ev.call_decode(registry, sc.SIG_LOCKED_AT, ("address", "bytes32", "bytes32"),
                              (committer, chain.ascii32(label_of(s)), chain.from_hex(s["spec_sha"])), ("uint64",))[0])


def lock_calldata(s: dict, uri: str) -> bytes:
    from evm import calldata
    return calldata(sc.SIG_LOCK, ("bytes32", "bytes32", "string"), (chain.ascii32(label_of(s)), chain.from_hex(s["spec_sha"]), uri))


def spec_uri(head: str, bot_id: str) -> str:
    return f"{REPO_URL}/blob/{head}/ledger/pengajuan/spec/{bot_id}.json"


def main() -> int:
    specs, masalah = sah(ROOT)
    for m in masalah:
        print("MASALAH:", m)
    for s in specs:
        print(f"{s['bot_id']}: spec_sha {s['spec_sha'][:18]}… lolos {s['t_lolos']}")
    print(f"{len(specs)} spesifikasi siap di-pin")
    return 1 if masalah else 0


if __name__ == "__main__":
    raise SystemExit(main())
