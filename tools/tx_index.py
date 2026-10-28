"""Indeks tx on-chain Fabius (P178): commitId -> tx komit + tx ungkap, (locker, botId, specSha) -> tx kunci, dari event SignalAnchor + LockRegistry.

Kenapa ada: halaman web (/verify, /tour) di Vercel membaca event lewat eth_getLogs, dan RPC publik gratis yang menyimpan riwayat log (onfinality,
thirdweb) membatasi laju IP Vercel bersama -> "tak terbaca" (terukur 28 Okt). Struk tx (eth_getTransactionReceipt) untuk tx lama justru dilayani
banyak RPC (drpc, thirdweb, dataseed bnbchain). Maka web cukup tahu HASH tx-nya: indeks ini = petunjuk saja, BUKAN sumber kebenaran - web
mengambil struk tiap tx dari chain dan mencocokkan alamat kontrak + topik event sendiri sebelum memakainya; petunjuk yang tak cocok dibuang.

Inkremental: `scanned_to` disimpan, jalan berikutnya hanya memindai blok baru. Tanpa kunci, tanpa transaksi.

    python -X utf8 tools/tx_index.py              # perbarui ledger/chain/tx-index.json
    python -X utf8 tools/tx_index.py --dry-run    # cetak ringkasan, tidak menulis
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Callable, Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import evm as evmmod                                   # noqa: E402
import signal_commit as sc                             # noqa: E402

OUT = os.path.join(ROOT, "ledger", "chain", "tx-index.json")
COMMITTED_SIG = "Committed(bytes32,address,bytes32,bytes32,uint64,bytes32,uint32)"
REVEALED_SIG = "Revealed(bytes32,bytes32,bytes32,uint8,int256,int256,uint256,bytes32,bytes32)"
LOCKED_SIG = "Locked(bytes32,address,bytes32,bytes32,uint64,string)"
LOG_SOURCES = (("https://bnb-testnet.api.onfinality.io/public", 9_999), ("https://97.rpc.thirdweb.com", 999))
FINALITY = 15                                          # blok terakhir yang belum dipindai: hindari reorg kecil di kepala chain


def topic0(sig: str) -> str:
    return "0x" + evmmod.keccak(sig.encode()).hex()


T_COMMITTED, T_REVEALED, T_LOCKED = topic0(COMMITTED_SIG), topic0(REVEALED_SIG), topic0(LOCKED_SIG)


def empty_index(anchor: str, registry: str, start: int) -> dict:
    return {"v": 1, "chain_id": sc.CHAIN_ID, "anchor": anchor.lower(), "registry": registry.lower(), "scanned_to": start - 1,
            "note": "petunjuk hash tx saja; web memeriksa tiap tx lewat strukturnya di chain sebelum dipakai (tools/tx_index.py)",
            "commits": {}, "locks": {}}


def lock_key(locker: str, bot_id: str, spec_sha: str) -> str:
    return f"{locker.lower()}|{bot_id.lower()}|{spec_sha.lower()}"


def topic_addr(t: str) -> str:
    return "0x" + t[-40:].lower()


def apply_logs(ix: dict, logs: Sequence[dict]) -> int:
    """Lipat log mentah eth_getLogs ke indeks. Log dari alamat lain diabaikan. Idempoten (ungkap per daun, kunci per kunci). -> jumlah entri baru."""
    added = 0
    for lg in logs:
        addr, tp = lg["address"].lower(), [t.lower() for t in lg["topics"]]
        tx, block = lg["transactionHash"].lower(), int(lg["blockNumber"], 16)
        if addr == ix["anchor"] and tp[0] == T_COMMITTED:
            c = ix["commits"].setdefault(tp[1], {"reveals": []})
            if c.get("tx") != tx:
                c.update({"tx": tx, "block": block})
                added += 1
        elif addr == ix["anchor"] and tp[0] == T_REVEALED:
            c = ix["commits"].setdefault(tp[1], {"reveals": []})
            if all(r["leaf"] != tp[2] for r in c["reveals"]):
                c["reveals"].append({"leaf": tp[2], "tx": tx, "block": block})
                c["reveals"].sort(key=lambda r: (r["block"], r["leaf"]))
                added += 1
        elif addr == ix["registry"] and tp[0] == T_LOCKED:
            k = lock_key(topic_addr(tp[2]), tp[3], "0x" + lg["data"][2:66].lower())
            if ix["locks"].get(k, {}).get("tx") != tx:
                ix["locks"][k] = {"tx": tx, "block": block}
                added += 1
    return added


def get_logs(sources: Sequence[tuple], q: dict, a: int, b: int, sleep: Callable[[float], None]) -> List[dict]:
    """Satu rentang [a, b] dari sumber pertama yang menjawab; rentang dipotong sesuai batas sumber; ditolak -> mundur 1, 2, 4, 8 s lalu sumber berikut."""
    last: Optional[Exception] = None
    for ev, span in sources:
        out: List[dict] = []
        try:
            x = a
            while x <= b:
                y = min(x + span, b)
                for i, wait in enumerate((0, 1, 2, 4, 8)):
                    if wait:
                        sleep(wait)
                    try:
                        out += ev.rpc("eth_getLogs", [{**q, "fromBlock": hex(x), "toBlock": hex(y)}])
                        break
                    except (evmmod.RpcError, RuntimeError) as e:
                        last = e
                        if i == 4:
                            raise
                sleep(0.25)
                x = y + 1
            return out
        except (evmmod.RpcError, RuntimeError):
            continue
    raise RuntimeError(f"eth_getLogs [{a}, {b}] gagal di semua sumber log: {last}")


def run(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--window", type=int, default=50_000, help="blok per putaran tulis (indeks disimpan tiap putaran)")
    a = ap.parse_args(argv)

    addrs = sc.load_addresses()
    with open(sc.DEPLOYMENTS, encoding="utf-8") as f:
        blocks = (json.load(f).get("m3", {}) or {}).get("deploy_block") or {}
    start = min((int(v) for v in blocks.values()), default=0) if isinstance(blocks, dict) else int(blocks)   # {"LockRegistry": n, "SignalAnchor": n}
    if not (addrs["anchor"] and addrs["registry"] and start):
        print("alamat SignalAnchor/LockRegistry atau m3.deploy_block tidak ada di deployments/97.json", file=sys.stderr)
        return 2
    ix = empty_index(addrs["anchor"], addrs["registry"], start)
    if os.path.isfile(a.out):
        with open(a.out, encoding="utf-8") as f:
            old = json.load(f)
        if old.get("anchor") == ix["anchor"] and old.get("registry") == ix["registry"]:
            ix = old

    chain_ev = evmmod.Evm(sc.rpc_urls(), sc.CHAIN_ID)
    sources = [(evmmod.Evm([u], sc.CHAIN_ID, timeout=20.0), span) for u, span in LOG_SOURCES]
    head = int(chain_ev.rpc("eth_blockNumber", []), 16) - FINALITY
    q = {"address": [ix["anchor"], ix["registry"]], "topics": [[T_COMMITTED, T_REVEALED, T_LOCKED]]}
    added = 0
    x = ix["scanned_to"] + 1
    print(f"tx-index: pindai blok {x}..{head} ({max(0, head - x + 1):,} blok)")
    while x <= head:
        y = min(x + a.window - 1, head)
        added += apply_logs(ix, get_logs(sources, q, x, y, time.sleep))
        ix["scanned_to"] = y
        if not a.dry_run:
            write(a.out, ix)
        x = y + 1
    n_rev = sum(len(c["reveals"]) for c in ix["commits"].values())
    print(f"tx-index: {len(ix['commits'])} komit, {n_rev} ungkap, {len(ix['locks'])} kunci; {added} entri baru; scanned_to {ix['scanned_to']}")
    return 0


def write(path: str, ix: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ix, f, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


if __name__ == "__main__":
    sys.exit(run())
