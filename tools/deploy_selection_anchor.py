"""Deploy `SelectionAnchor` (P141, F-D102) ke chain 97: pilihan bot per bar oleh agent analis ERC-8004, dikomit sebelum penutupan bar.

Penanda tangan = COMMITTER M3 (kontrak tanpa pemilik dan tanpa hak istimewa; pola sama dengan `deploy_execution_anchor.py`). Kunci dari env
COMMITTER_PRIVATE_KEY atau `.committer.env`, tidak pernah dicetak, alamat HARUS = `m3.committer`. Argumen konstruktor = IdentityRegistry ERC-8004
(`erc8004.identity`). Sesudah deploy dibaca ulang: panjang kode = artefak dan `identity()` = registry; baru ditulis ke `deployments/97.json`
(`contracts.SelectionAnchor` + `erc8004.selection`). Idempoten: sudah ada = berhenti.

    python -X utf8 tools/deploy_selection_anchor.py            # rencana + perkiraan gas
    python -X utf8 tools/deploy_selection_anchor.py --send     # atas kata builder
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

from engine import ledger                              # noqa: E402
import signal_commit as sc                             # noqa: E402

ART = os.path.join(ROOT, "out", "SelectionAnchor.sol", "SelectionAnchor.json")


def main() -> int:
    ap = argparse.ArgumentParser(description="Deploy SelectionAnchor (default = rencana).")
    ap.add_argument("--send", action="store_true")
    a = ap.parse_args()
    import evm as evmmod
    from evm import receipt_ok

    subprocess.run(["forge", "build"], cwd=ROOT, check=True, capture_output=True)
    with open(ART, encoding="utf-8") as f:
        art = json.load(f)
    code, deployed = bytes.fromhex(art["bytecode"]["object"][2:]), bytes.fromhex(art["deployedBytecode"]["object"][2:])
    with open(sc.DEPLOYMENTS, "rb") as f:
        raw = f.read()
    d, nl = json.loads(raw.decode("utf-8")), raw.endswith(b"\n")
    cs = d.setdefault("contracts", {})
    identity, committer = d["erc8004"]["identity"], d["m3"]["committer"]
    ev = evmmod.Evm(sc.rpc_urls(), sc.CHAIN_ID)
    ev.chain_check()
    if cs.get("SelectionAnchor") and ev.code_size(cs["SelectionAnchor"]) > 0:
        print(f"sudah ada: SelectionAnchor {cs['SelectionAnchor']} - tidak di-deploy ulang")
        return 0
    data = code + bytes(12) + bytes.fromhex(identity[2:])                  # constructor(IIdentityRegistry8004 identity_)
    gp, bal = ev.gas_price(), ev.balance(committer)
    try:
        gas = ev.estimate(committer, None, data)
    except Exception:  # noqa: BLE001
        gas = 900_000
    print(f"chain  : {sc.CHAIN_ID} | deployer = committer {committer} saldo {bal / 1e18:.6f} tBNB | gas {gp / 1e9:.2f} gwei")
    print(f"deploy : SelectionAnchor ({len(deployed)} B runtime) constructor identity = {identity} | perkiraan gas {gas:,} (~{gas * gp / 1e18:.6f} tBNB)")
    if not a.send:
        print("RENCANA: tidak ada yang dikirim. --send untuk deploy (atas kata builder).")
        return 0
    pk = sc.committer_key()
    if not pk or evmmod.address_of(pk).lower() != committer.lower():
        print("BERHENTI: kunci committer tidak ada atau alamatnya bukan m3.committer. Tidak ada tx terkirim.")
        return 2
    r = ev.send(pk, None, data)
    if not receipt_ok(r):
        print(f"DITOLAK status 0 tx {r.get('transactionHash')}")
        return 1
    addr = r["contractAddress"]
    got = ev.call_decode(addr, "identity()", (), (), ("address",))[0]
    if ev.code_size(addr) != len(deployed) or got.lower() != identity.lower():
        print(f"BERHENTI: baca ulang tidak cocok (kode {ev.code_size(addr)} vs {len(deployed)} B; identity {got})")
        return 1
    blk = ev.num(r["blockNumber"])
    print(f"  SelectionAnchor {addr} tx {r['transactionHash']} blok {blk} gas {ev.num(r['gasUsed'])} | baca ulang cocok (kode + identity)")
    cs["SelectionAnchor"] = addr
    d["erc8004"]["selection"] = {"address": addr, "tx": r["transactionHash"], "block": blk, "deployed_utc": ledger.utc_iso(ev.block_timestamp() * 1000),
                                 "deployer": committer}
    with open(sc.DEPLOYMENTS, "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + ("\n" if nl else ""))
    print("ditulis: deployments/97.json (contracts.SelectionAnchor, erc8004.selection)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
