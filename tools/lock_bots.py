"""Kunci SPESIFIKASI bot di LockRegistry chain 97 oleh COMMITTER (P130, F-D95) - syarat sebelum jam maju bot baru dimulai: SignalAnchor hanya
menerima komit untuk (committer, bot, spec_sha) yang sudah dikunci, dan tick yang lebih tua dari kunci tidak bisa dikomit (seperti bar 1 Okt B1/B3).

Kenapa alat terpisah: `tools/m3_setup.py` selalu meminta kunci DEPLOYER (proyek lain) padahal kunci spesifikasi cukup dengan committer, dan
`tools/lock_spec.py` mem-pin BERKAS kunci (`engine/locks/*.lock.json`), bukan spesifikasi bot. Panggilan kontraknya sama dengan langkah kunci
`m3_setup.step_locks`: `lock(bytes32 botId, bytes32 specSha, string uri)`, uri = baris `engine/spec.py` pada commit HEAD.

Aturan (sama dengan lock_spec): bawaan = RENCANA (tanpa kunci, tanpa gas); `--send` = satu tx lock() per bot yang BELUM dikunci; kunci committer dari
env COMMITTER_PRIVATE_KEY atau `.committer.env`, tidak pernah dicetak, dan alamatnya HARUS = `m3.committer` (bila tidak: berhenti tanpa mengirim);
spec_sha kode harus sama dengan genesis ledger bila ledger bot itu sudah ada (pivot diam-diam = berhenti); idempoten; hasil ditulis ke
`deployments/97.json` (`m3.locks`).

    python -X utf8 tools/lock_bots.py --bots B2-RS,B4-LISTING-FADE,B5-CORE-RWA,B6-BOUNCE           # rencana + perkiraan gas
    python -X utf8 tools/lock_bots.py --bots B2-RS,B4-LISTING-FADE,B5-CORE-RWA,B6-BOUNCE --send    # atas kata builder
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
from engine.spec import SPECS                          # noqa: E402
import signal_commit as sc                             # noqa: E402

REPO_URL = "https://github.com/Shenhan01-sys/Fabius"
GAS_GUESS = 120_000                                     # lock() + string uri; dipakai bila estimateGas tak bisa (mis. kunci belum dibaca di mode rencana)


def main() -> int:
    ap = argparse.ArgumentParser(description="Kunci spesifikasi bot oleh committer (default = rencana).")
    ap.add_argument("--bots", required=True, help="daftar bot dipisah koma")
    ap.add_argument("--send", action="store_true", help="kirim lock() untuk bot yang belum dikunci (atas kata builder)")
    a = ap.parse_args()
    import evm as evmmod
    from evm import calldata, receipt_ok

    bots = [b.strip() for b in a.bots.split(",") if b.strip()]
    unknown = [b for b in bots if b not in SPECS]
    if unknown:
        print(f"BERHENTI: bot tidak dikenal {unknown}")
        return 2
    with open(sc.DEPLOYMENTS, encoding="utf-8") as f:
        d = json.load(f)
    registry, committer = d["contracts"]["LockRegistry"], d["m3"]["committer"]
    ev = evmmod.Evm(sc.rpc_urls(), sc.CHAIN_ID)
    ev.chain_check()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    gp, bal = ev.gas_price(), ev.balance(committer)
    print(f"chain  : {sc.CHAIN_ID} | LockRegistry {registry} | committer {committer} saldo {bal / 1e18:.6f} tBNB | gas {gp / 1e9:.2f} gwei | HEAD {head[:10]}")

    todo = []
    for bot in bots:
        spec_sha = SPECS[bot].sha()
        recs = ledger.load(os.path.join(ROOT, "ledger", "paper", f"{bot}.jsonl"))
        if recs and recs[0].get("spec_sha") != spec_sha:
            print(f"BERHENTI: spec_sha ledger {bot} != kode (pivot?) - tidak ada yang dikunci")
            return 2
        at = ev.call_decode(registry, sc.SIG_LOCKED_AT, ("address", "bytes32", "bytes32"),
                            (committer, chain.ascii32(bot), chain.from_hex(spec_sha)), ("uint64",))[0]
        if at:
            print(f"kunci  : {bot:16s} SUDAH dikunci {ledger.utc_iso(at * 1000)} (spec {spec_sha[:18]}…) - dilewati")
            continue
        uri = f"{REPO_URL}/blob/{head}/engine/spec.py#{bot}"
        data = calldata(sc.SIG_LOCK, ("bytes32", "bytes32", "string"), (chain.ascii32(bot), chain.from_hex(spec_sha), uri))
        try:
            gas = ev.estimate(committer, registry, data)
        except Exception:  # noqa: BLE001 - perkiraan saja
            gas = GAS_GUESS
        todo.append((bot, spec_sha, uri, data, gas))
        print(f"kunci  : {bot:16s} spec {spec_sha[:18]}… -> lock() perkiraan gas {gas:,} (~{gas * gp / 1e18:.6f} tBNB)")
    if not todo:
        print("Semua sudah dikunci; tidak ada tx.")
        return 0
    total = sum(g for *_, g in todo) * gp
    print(f"total  : {len(todo)} tx, perkiraan {total / 1e18:.6f} tBNB dari saldo committer {bal / 1e18:.6f} tBNB")
    if not a.send:
        print("RENCANA: tidak ada yang dikirim. --send untuk mengirim (atas kata builder).")
        return 0
    if bal < total * 2:
        print("BERHENTI: saldo committer < 2x perkiraan biaya. Tidak ada tx terkirim.")
        return 2
    pk = sc.committer_key()
    if not pk or evmmod.address_of(pk).lower() != committer.lower():
        print("BERHENTI: kunci committer tidak ada atau alamatnya bukan m3.committer. Tidak ada tx terkirim.")
        return 2
    locks = d.setdefault("m3", {}).setdefault("locks", {})
    for bot, spec_sha, uri, data, _ in todo:
        r = ev.send(pk, registry, data)
        if not receipt_ok(r):
            print(f"DITOLAK {bot}: status 0 tx {r.get('transactionHash')} - berhenti")
            break
        at = ev.call_decode(registry, sc.SIG_LOCKED_AT, ("address", "bytes32", "bytes32"),
                            (committer, chain.ascii32(bot), chain.from_hex(spec_sha)), ("uint64",))[0]
        print(f"  {bot}: tx {r['transactionHash']} blok {ev.num(r['blockNumber'])} gas {ev.num(r['gasUsed'])} | lockedAt {ledger.utc_iso(at * 1000)}")
        locks[bot] = {"specSha": spec_sha, "lockedAt": at, "lockedAt_utc": ledger.utc_iso(at * 1000), "tx": r["transactionHash"], "uri": uri}
        with open(sc.DEPLOYMENTS, "rb") as f:
            nl = f.read().endswith(b"\n")
        with open(sc.DEPLOYMENTS, "w", encoding="utf-8", newline="\n") as f:          # tulis sesudah TIAP tx: proses mati di tengah tidak menghilangkan catatan
            f.write(json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + ("\n" if nl else ""))
    print("ditulis: deployments/97.json (m3.locks). Berikutnya: commit + push berkas itu, lalu genesis jam maju (P131).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
