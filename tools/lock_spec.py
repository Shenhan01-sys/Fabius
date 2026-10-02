"""Pin satu berkas kunci (`engine/locks/*.lock.json`) ke LockRegistry di chain 97 (F-D84): botId = label (ascii32), specSha = sha kunci itu.
Jam yang berlaku untuk kunci = `lockedAt` (waktu blok), bukan `dikunci` di berkas (jam laptop) - pola yang sama dengan kunci ambang v1 (F-D74).

Penanda tangan = committer M3 (`deployments/97.json` -> `m3.committer`); kuncinya dari env COMMITTER_PRIVATE_KEY atau `.committer.env`, tidak pernah dicetak,
dan alamatnya HARUS sama dengan `m3.committer` (bila tidak: berhenti tanpa mengirim). Idempoten: kunci yang sudah ada di chain tidak dikirim lagi.

    python -X utf8 tools/lock_spec.py --file engine/locks/fd16.lock.json --name FABIUS-FD16-MAJU-v1             # rencana (tanpa kunci, tanpa gas)
    python -X utf8 tools/lock_spec.py --file engine/locks/fd16.lock.json --name FABIUS-FD16-MAJU-v1 --send      # SATU transaksi lock()
    python -X utf8 tools/lock_spec.py --file engine/locks/fd16.lock.json --name FABIUS-FD16-MAJU-v1 --verify    # baca ulang lockedAt
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from engine import chain, ledger                       # noqa: E402
from engine.spec import sha0x                          # noqa: E402
import signal_commit as sc                             # noqa: E402

REPO_URL = "https://github.com/Shenhan01-sys/Fabius"


def load_lock(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        lock = json.load(f)
    if sha0x(lock["params"]) != lock["sha"]:
        raise SystemExit("berkas kunci RUSAK: sha != sha(params). Tidak ada yang dikirim.")
    return lock


def main() -> int:
    ap = argparse.ArgumentParser(description="Pin berkas kunci ke LockRegistry (default = rencana).")
    ap.add_argument("--file", required=True)
    ap.add_argument("--name", required=True, help="label <= 32 karakter ASCII, mis. FABIUS-FD16-MAJU-v1")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--send", action="store_true")
    mode.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    import evm as evmmod
    from evm import calldata, receipt_ok
    lock = load_lock(a.file)
    bot_id = chain.ascii32(a.name)
    with open(sc.DEPLOYMENTS, encoding="utf-8") as f:
        d = json.load(f)
    registry, committer = d["contracts"]["LockRegistry"], d["m3"]["committer"]
    ev = evmmod.Evm(sc.rpc_urls(), sc.CHAIN_ID)
    ev.chain_check()
    rd = lambda: ev.call_decode(registry, sc.SIG_LOCKED_AT, ("address", "bytes32", "bytes32"), (committer, bot_id, chain.from_hex(lock["sha"])), ("uint64",))[0]   # noqa: E731
    at = rd()
    print(f"kunci  : {os.path.relpath(a.file, ROOT)}  sha {lock['sha']}  dikunci(jam laptop) {lock.get('dikunci')}")
    print(f"label  : {a.name}  | LockRegistry {registry} | committer {committer}")
    print(f"chain  : lockedAt = {at}" + (f" = {ledger.utc_iso(at * 1000)} (jam yang berlaku)" if at else " (belum di-pin)"))
    if a.verify:
        return 0 if at else 1
    if at:
        print("Sudah di-pin; tidak mengirim lagi.")
        return 0
    if not a.send:
        print("RENCANA: tidak ada yang dikirim. --send untuk SATU transaksi lock() dari committer.")
        return 0
    pk = sc.committer_key()
    if not pk or evmmod.address_of(pk).lower() != committer.lower():
        print("BERHENTI: kunci committer tidak ada atau alamatnya bukan m3.committer. Tidak ada tx terkirim.")
        return 2
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    rel = os.path.relpath(a.file, ROOT).replace("\\", "/")
    uri = f"{REPO_URL}/blob/{head}/{rel}"
    r = ev.send(pk, registry, calldata(sc.SIG_LOCK, ("bytes32", "bytes32", "string"), (bot_id, chain.from_hex(lock["sha"]), uri)))
    if not receipt_ok(r):
        print(f"DITOLAK status 0 tx {r.get('transactionHash')}")
        return 1
    at = rd()
    print(f"tx {r['transactionHash']} blok {ev.num(r['blockNumber'])} gas {ev.num(r['gasUsed'])} | lockedAt {at} = {ledger.utc_iso(at * 1000)} | uri {uri}")
    pins = d.setdefault("m3", {}).setdefault("pins", {})
    pins[a.name] = {"file": rel, "sha": lock["sha"], "lockedAt": at, "lockedAt_utc": ledger.utc_iso(at * 1000), "tx": r["transactionHash"], "uri": uri}
    with open(sc.DEPLOYMENTS, "rb") as f:
        nl = f.read().endswith(b"\n")
    with open(sc.DEPLOYMENTS, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + ("\n" if nl else ""))
    print("ditulis: deployments/97.json (m3.pins)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
