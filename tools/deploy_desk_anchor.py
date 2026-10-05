"""Deploy `DeskAnchor` (P152, F-D109) ke chain 97: satu Merkle root keputusan meja AI 5 menit per siklus, hanya selama siklus itu berjalan.

Committer = kunci gerbang x402 (`x402_sinyal.facilitator`, yang menjalankan loop meja); deployer = kunci yang sama. Kunci dari env / `.x402.env`,
tidak pernah dicetak, alamat HARUS = `x402_sinyal.facilitator`. Sesudah deploy dibaca ulang: panjang kode = artefak dan `committer()` = gerbang; baru
ditulis ke `deployments/97.json` (`contracts.DeskAnchor` + `meja`). Idempoten: sudah ada = berhenti.

    python -X utf8 tools/deploy_desk_anchor.py            # rencana + perkiraan gas
    python -X utf8 tools/deploy_desk_anchor.py --send     # atas kata builder
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

ART = os.path.join(ROOT, "out", "DeskAnchor.sol", "DeskAnchor.json")


def main() -> int:
    ap = argparse.ArgumentParser(description="Deploy DeskAnchor (default = rencana).")
    ap.add_argument("--send", action="store_true")
    a = ap.parse_args()
    import evm as evmmod
    from evm import receipt_ok
    import x402_sinyal as xs

    subprocess.run(["forge", "build"], cwd=ROOT, check=True, capture_output=True)
    with open(ART, encoding="utf-8") as f:
        art = json.load(f)
    code, deployed = bytes.fromhex(art["bytecode"]["object"][2:]), bytes.fromhex(art["deployedBytecode"]["object"][2:])
    with open(sc.DEPLOYMENTS, "rb") as f:
        raw = f.read()
    d, nl = json.loads(raw.decode("utf-8")), raw.endswith(b"\n")
    cs = d.setdefault("contracts", {})
    committer = d["x402_sinyal"]["facilitator"]
    ev = evmmod.Evm(sc.rpc_urls(), sc.CHAIN_ID)
    ev.chain_check()
    if cs.get("DeskAnchor") and ev.code_size(cs["DeskAnchor"]) > 0:
        print(f"sudah ada: DeskAnchor {cs['DeskAnchor']} - tidak di-deploy ulang")
        return 0
    data = code + bytes(12) + bytes.fromhex(committer[2:])                  # constructor(address committer_)
    gp, bal = ev.gas_price(), ev.balance(committer)
    try:
        gas = ev.estimate(committer, None, data)
    except Exception:  # noqa: BLE001
        gas = 400_000
    print(f"chain  : {sc.CHAIN_ID} | deployer = committer = gerbang {committer} saldo {bal / 1e18:.6f} tBNB | gas {gp / 1e9:.2f} gwei")
    print(f"deploy : DeskAnchor ({len(deployed)} B runtime) | perkiraan gas {gas:,} (~{gas * gp / 1e18:.6f} tBNB)")
    if not a.send:
        print("RENCANA: tidak ada yang dikirim. --send untuk deploy (atas kata builder).")
        return 0
    pk = xs.facilitator_key()
    if not pk or evmmod.address_of(pk).lower() != committer.lower():
        print("BERHENTI: kunci gerbang tidak ada atau alamatnya bukan x402_sinyal.facilitator. Tidak ada tx terkirim.")
        return 2
    r = ev.send(pk, None, data)
    if not receipt_ok(r):
        print(f"DITOLAK status 0 tx {r.get('transactionHash')}")
        return 1
    addr = r["contractAddress"]
    got = ev.call_decode(addr, "committer()", (), (), ("address",))[0]
    if ev.code_size(addr) != len(deployed) or got.lower() != committer.lower():
        print(f"BERHENTI: baca ulang tidak cocok (kode {ev.code_size(addr)} vs {len(deployed)} B; committer {got})")
        return 1
    blk = ev.num(r["blockNumber"])
    print(f"  DeskAnchor {addr} tx {r['transactionHash']} blok {blk} gas {ev.num(r['gasUsed'])} | baca ulang cocok (kode + committer)")
    cs["DeskAnchor"] = addr
    d["meja"] = {"address": addr, "tx": r["transactionHash"], "block": blk, "deployed_utc": ledger.utc_iso(ev.block_timestamp() * 1000),
                 "committer": committer, "why": "P152 (F-D109): meja AI 5 menit, satu Merkle root keputusan semua agent per siklus"}
    with open(sc.DEPLOYMENTS, "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + ("\n" if nl else ""))
    print("ditulis: deployments/97.json (contracts.DeskAnchor, meja)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
