"""Pin `book_sha` epoch terakhir buku slot hidup (`ledger/book/buku.jsonl`, P87/F-D85) ke LockRegistry di chain 97: botId = "FABIUS-BUKU-E<epoch>",
specSha = book_sha. Jam blok membuktikan susunan buku (siapa di slot mana, pada epoch itu) sudah ada pada saat itu - buku tidak bisa ditulis ulang
belakangan tanpa terlihat.

Penanda tangan = committer M3 (`m3.committer`); kunci dari env COMMITTER_PRIVATE_KEY atau `.committer.env`, tidak pernah dicetak, alamat HARUS sama
dengan `m3.committer`. Buku diverifikasi lebih dulu (rantai + keputusan dihitung ulang); buku yang tidak sah tidak di-pin. Idempoten.

    python -X utf8 tools/pin_book.py              # rencana (tanpa kunci, tanpa gas)
    python -X utf8 tools/pin_book.py --send       # SATU transaksi lock() bila epoch terakhir belum di-pin
    python -X utf8 tools/pin_book.py --verify     # baca ulang lockedAt
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

from engine import book_live, chain, ledger            # noqa: E402
import signal_commit as sc                             # noqa: E402

BOOK_FILE = os.path.join(ROOT, "ledger", "book", "buku.jsonl")
REPO_URL = "https://github.com/Shenhan01-sys/Fabius"


def main() -> int:
    ap = argparse.ArgumentParser(description="Pin book_sha epoch terakhir ke LockRegistry (default = rencana).")
    ap.add_argument("--file", default=BOOK_FILE)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--send", action="store_true")
    mode.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    import evm as evmmod
    from evm import calldata, receipt_ok
    recs = ledger.load(a.file)
    probs = book_live.verify_book(recs)
    if not recs or probs:
        print("buku hidup kosong atau TIDAK SAH - tidak di-pin:", (probs or ["kosong"])[:3])
        return 2
    last = recs[-1]
    if last.get("type") != "epoch":
        print("belum ada catatan epoch (hanya genesis) - tidak ada yang di-pin")
        return 0
    name = f"FABIUS-BUKU-E{last['epoch']}"
    bot_id, sha = chain.ascii32(name), last["book_sha"]
    with open(sc.DEPLOYMENTS, encoding="utf-8") as f:
        d = json.load(f)
    registry, committer = d["contracts"]["LockRegistry"], d["m3"]["committer"]
    ev = evmmod.Evm(sc.rpc_urls(), sc.CHAIN_ID)
    ev.chain_check()
    rd = lambda: ev.call_decode(registry, sc.SIG_LOCKED_AT, ("address", "bytes32", "bytes32"), (committer, bot_id, chain.from_hex(sha)), ("uint64",))[0]   # noqa: E731
    at = rd()
    print(f"buku   : {os.path.relpath(a.file, ROOT)} SAH, {len(recs)} catatan | epoch {last['epoch']} ({last['now_utc']}) book_sha {sha}")
    print(f"label  : {name} | LockRegistry {registry} | committer {committer}")
    print(f"chain  : lockedAt = {at}" + (f" = {ledger.utc_iso(at * 1000)}" if at else " (belum di-pin)"))
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
    uri = f"{REPO_URL}/blob/{head}/{os.path.relpath(a.file, ROOT).replace(os.sep, '/')}"
    r = ev.send(pk, registry, calldata(sc.SIG_LOCK, ("bytes32", "bytes32", "string"), (bot_id, chain.from_hex(sha), uri)))
    if not receipt_ok(r):
        print(f"DITOLAK status 0 tx {r.get('transactionHash')}")
        return 1
    at = rd()
    print(f"tx {r['transactionHash']} blok {ev.num(r['blockNumber'])} gas {ev.num(r['gasUsed'])} | lockedAt {at} = {ledger.utc_iso(at * 1000)} | uri {uri}")
    pins = d.setdefault("m3", {}).setdefault("pins", {})
    pins[name] = {"file": os.path.relpath(a.file, ROOT).replace(os.sep, "/"), "sha": sha, "lockedAt": at, "lockedAt_utc": ledger.utc_iso(at * 1000),
                  "tx": r["transactionHash"], "uri": uri}
    with open(sc.DEPLOYMENTS, "rb") as f:
        nl = f.read().endswith(b"\n")
    with open(sc.DEPLOYMENTS, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + ("\n" if nl else ""))
    print("ditulis: deployments/97.json (m3.pins)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
