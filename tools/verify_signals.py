"""Pemeriksa publik komit sinyal Fabius (P106): baca SignalAnchor + LockRegistry di chain 97 TANPA kunci dan tanpa gas, lalu cocokkan dengan ledger paper
dan bar yang di-commit di repo. Ini alat untuk pembeli/pemeriksa, bukan untuk operator: ia tidak percaya pada worker, log, atau halaman kami.

Untuk tiap tick ledger dan tiap komit dari committer resmi (`deployments/97.json` -> `m3.committer`):
  1. kunci   - (botId, specSha) dikunci committer SEBELUM bar ditutup (`lockedAt <= asof`);
  2. komit   - ada komit untuk bar itu, `committedAt - asof <= maxLag`, akar nol hanya bila n = 0;
  3. ungkap  - semua n sinyal terungkap lewat event `Revealed` (tidak ditandai TIDAK-DIUNGKAP);
  4. daun    - muatan + salt di tiap event, di-hash ulang DI SINI dengan skema `engine/sinyal.py`, sama dengan daun di event;
  5. isi     - id sinyal yang diungkap = `signal_ids` tick di ledger, dan tick itu sendiri dapat direproduksi PERSIS dari bar (`engine`).
Vonis per (bot, bar): SAH · BELUM DIUNGKAP (jendela ungkap masih terbuka) · TIDAK DIUNGKAP (lewat jendela) · MENUNGGU KOMIT (masih dalam maxLag) ·
TIDAK DIKOMIT (tick ada, komit tidak - alasan dicetak) · SEBELUM KUNCI (tick lebih tua dari kunci; tidak bisa dikomit, by design) · ALARM (isi beda).
Komit untuk bot kita dari ALAMAT LAIN dihitung dan dilaporkan, tidak pernah dianggap milik Fabius. "Sekarang" = waktu blok terakhir, bukan jam laptop.

    python -X utf8 tools/verify_signals.py                       # chain 97; nol kunci, nol gas
    python -X utf8 tools/verify_signals.py --bots B3-CARRY --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

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
from engine.sinyal import SIGNAL_V, STRUCT_TYPES       # noqa: E402
from engine.spec import SPECS                          # noqa: E402
import signal_commit as sc                             # noqa: E402

REVEALED_SIG = "Revealed(bytes32,bytes32,bytes32,uint8,int256,int256,uint256,bytes32,bytes32)"
REVEALED_DATA = ("bytes32", "uint8", "int256", "int256", "uint256", "bytes32", "bytes32")
LOG_CHUNK = 5_000


@dataclass
class Row:
    bot: str
    bar: str
    vonis: str
    detail: str
    commit_id: Optional[str] = None
    n: Optional[int] = None
    revealed: Optional[int] = None
    lag_s: Optional[int] = None
    problems: List[str] = field(default_factory=list)


# ---------------------------------------------------------------- baca chain
def all_commits(cv) -> List[Tuple[bytes, dict]]:
    """Semua komit di kontrak (siapa pun pengirimnya), lewat `commitCount()` + `commitIdAt(i)` + `getCommit(id)` - tanpa log, jadi tanpa batas rentang RPC."""
    n = cv.evm.call_decode(cv.anchor, "commitCount()", (), (), ("uint256",))[0]
    out = []
    for i in range(n):
        cid = bytes(cv.evm.call_decode(cv.anchor, "commitIdAt(uint256)", ("uint256",), (i,), ("bytes32",))[0])
        out.append((cid, cv.get_commit(cid)))
    return out


def revealed_events(evm, anchor: str, from_block: int, to_block: int, chunk: int = LOG_CHUNK) -> Dict[bytes, List[dict]]:
    """Semua event `Revealed` kontrak, dikelompokkan per id komit. Rentang dipotong-potong (RPC publik membatasi eth_getLogs); dipotong lebih kecil bila ditolak."""
    from eth_abi import decode
    from evm import RpcError
    topic0 = "0x" + chain.keccak256(REVEALED_SIG.encode()).hex()
    out: Dict[bytes, List[dict]] = {}
    start = from_block
    while start <= to_block:
        end = min(start + chunk - 1, to_block)
        try:
            logs = evm.rpc("eth_getLogs", [{"address": anchor, "fromBlock": hex(start), "toBlock": hex(end), "topics": [topic0]}])
        except (RpcError, RuntimeError):
            if chunk <= 100:
                raise
            chunk //= 2
            continue
        for lg in logs:
            vals = decode(list(REVEALED_DATA), bytes.fromhex(lg["data"][2:]))
            cid = bytes.fromhex(lg["topics"][1][2:])
            out.setdefault(cid, []).append({"leaf": bytes.fromhex(lg["topics"][2][2:]), "asset": vals[0], "aksi": vals[1], "bobotLama": vals[2],
                                            "bobotBaru": vals[3], "hargaRef": vals[4], "dataHash": vals[5], "salt": vals[6],
                                            "tx": lg.get("transactionHash"), "block": int(lg["blockNumber"], 16)})
        start = end + 1
    return out


# ---------------------------------------------------------------- murni
def rebuild_leaf(commit: dict, ev: dict) -> Tuple[bytes, str]:
    """(daun, id sinyal) dari muatan event + identitas komit, dengan skema engine. Daun harus sama dengan daun di event."""
    fields = [SIGNAL_V, bytes(commit["botId"]), bytes(commit["specSha"]), int(commit["asof"]), bytes(ev["asset"]), int(ev["aksi"]),
              int(ev["bobotLama"]), int(ev["bobotBaru"]), int(ev["hargaRef"]), bytes(ev["dataHash"])]
    body = chain.abi_encode(STRUCT_TYPES, fields)
    return chain.keccak256(body + chain.abi_encode(["bytes32"], [bytes(ev["salt"])])), chain.hex0x(chain.keccak256(body))


def is_zero_addr(a) -> bool:
    return int(str(a), 16) == 0


def verify(bots: Sequence[str], ledger_dir: str, views, cv, commits: Sequence[Tuple[bytes, dict]], events: Dict[bytes, List[dict]],
           official: str, now_s: int) -> Tuple[List[Row], dict]:
    max_lag, window = int(cv.max_lag()), int(cv.reveal_window())
    mine = {cid: c for cid, c in commits if str(c["committer"]).lower() == official.lower()}
    others = [(cid, c) for cid, c in commits if str(c["committer"]).lower() != official.lower()]
    used = set()
    rows: List[Row] = []
    for bot in bots:
        spec = SPECS[bot]
        records = ledger.load(os.path.join(ledger_dir, f"{bot}.jsonl"))
        probs = ledger.verify_chain(records) if records else ["ledger kosong"]
        if probs:
            rows.append(Row(bot, "-", "ALARM", f"rantai ledger tidak sah: {probs[0]}"))
            continue
        locked = int(cv.locked_at(official, bot, spec.sha()))
        for tk in (r for r in records if r["type"] == "tick"):
            asof_s, date = sc.asof_s_of(tk), tk["asof_date"]
            cid = sc.commit_id(official, bot, spec.sha(), asof_s)
            c = mine.get(cid)
            if c is None:
                if locked == 0 or locked > asof_s:
                    rows.append(Row(bot, date, "SEBELUM KUNCI", "tick lebih tua dari kunci committer (tidak bisa dikomit, by design)"))
                elif now_s - asof_s <= max_lag:
                    rows.append(Row(bot, date, "MENUNGGU KOMIT", f"{(now_s - asof_s) / 3600:.1f} jam sesudah penutupan (batas {max_lag / 3600:.0f} jam)"))
                else:
                    rows.append(Row(bot, date, "TIDAK DIKOMIT", "tick ada di ledger, komit tidak ada dan batas maxLag sudah lewat"))
                continue
            used.add(cid)
            row = Row(bot, date, "SAH", "", chain.hex0x(cid), int(c["n"]), int(c["revealed"]), int(c["committedAt"]) - asof_s)
            if row.lag_s > max_lag:
                row.problems.append(f"komit {row.lag_s} s sesudah penutupan > maxLag {max_lag}")
            if (bytes(c["root"]) == sc.ZERO32) != (row.n == 0):
                row.problems.append("akar nol tidak sama dengan n nol")
            if row.n != len(tk.get("signal_ids", [])):
                row.problems.append(f"n komit {row.n} != {len(tk.get('signal_ids', []))} sinyal di tick")
            sigs, bprobs = sc.rebuild_signals(spec, tk, views)
            row.problems += [f"ledger: {p}" for p in bprobs]
            evs = events.get(cid, [])
            ids = []
            for ev in evs:
                leaf, sid = rebuild_leaf(c, ev)
                if leaf != ev["leaf"]:
                    row.problems.append(f"daun event {chain.hex0x(ev['leaf'])[:14]}… tidak bisa dihitung ulang dari muatannya")
                ids.append(sid)
            if len(set(ids)) != len(ids):
                row.problems.append("sinyal yang sama diungkap dua kali")
            if not set(ids) <= set(tk.get("signal_ids", [])):
                row.problems.append(f"{len(set(ids) - set(tk.get('signal_ids', [])))} sinyal terungkap TIDAK ada di tick ledger")
            if row.problems:
                row.vonis, row.detail = "ALARM", "; ".join(row.problems)[:300]
            elif len(evs) < row.n:
                if bool(c.get("missed")) or now_s > asof_s + window:
                    row.vonis, row.detail = "TIDAK DIUNGKAP", f"{len(evs)}/{row.n} terungkap, jendela {window // 86400} hari lewat"
                else:
                    row.vonis, row.detail = "BELUM DIUNGKAP", f"{len(evs)}/{row.n} terungkap; jendela sampai {ledger.utc_iso((asof_s + window) * 1000)}"
            else:
                row.detail = f"komit {row.lag_s / 3600:.1f} jam sesudah penutupan; {len(evs)}/{row.n} sinyal terungkap = tick ledger" + \
                             ("" if row.n else " (bot diam: akar nol)")
            rows.append(row)
    for cid, c in mine.items():
        if cid not in used:
            rows.append(Row("?", ledger.utc_iso(int(c["asof"]) * 1000)[:10], "ALARM", "komit resmi tanpa tick di ledger repo", chain.hex0x(cid), int(c["n"])))
    bots_b32 = {chain.ascii32(b): b for b in bots}
    foreign = sum(1 for _, c in others if bytes(c["botId"]) in bots_b32)
    stats = {k: sum(1 for r in rows if r.vonis == k) for k in
             ("SAH", "BELUM DIUNGKAP", "TIDAK DIUNGKAP", "MENUNGGU KOMIT", "TIDAK DIKOMIT", "SEBELUM KUNCI", "ALARM")}
    stats.update({"komit_resmi": len(mine), "komit_alamat_lain_untuk_bot_kita": foreign, "komit_total": len(commits)})
    return rows, stats


def run(bots: Sequence[str], ledger_dir: str, bars_dir: str, deployments: str = sc.DEPLOYMENTS, ev=None):
    """Satu pemeriksaan penuh dari chain 97 (dipakai `main` dan validator ERC-8004 P136). -> (baris, ringkas, info)."""
    import evm as evmmod
    from paper_tick import Views
    with open(deployments, encoding="utf-8") as f:
        d = json.load(f)
    cs, m3 = d.get("contracts", {}), d.get("m3", {})
    anchor, registry, official = cs.get("SignalAnchor"), cs.get("LockRegistry"), m3.get("committer")
    if not (anchor and registry and official):
        raise LookupError("deployments/97.json belum memuat SignalAnchor/LockRegistry/m3.committer")
    if ev is None:
        ev = evmmod.Evm(sc.rpc_urls(), sc.CHAIN_ID)
        ev.chain_check()
    cv = sc.AnchorView(ev, anchor, registry)
    head = int(ev.rpc("eth_blockNumber", []), 16)
    now_s = ev.block_timestamp()
    commits = all_commits(cv)
    events = revealed_events(ev, anchor, int((m3.get("deploy_block") or {}).get("SignalAnchor") or 0), head)
    rows, st = verify(list(bots), ledger_dir, Views(bars_dir), cv, commits, events, official, now_s)
    return rows, st, {"anchor": anchor, "committer": official, "blok": head, "waktu_blok_s": now_s, "cv": cv, "ev": ev}


def main() -> int:
    ap = argparse.ArgumentParser(description="Pemeriksa publik komit sinyal Fabius vs ledger + bar (tanpa kunci, tanpa gas).")
    ap.add_argument("--bots", default=",".join(sc.BOTS_DEFAULT))
    ap.add_argument("--ledger", default=os.path.join(ROOT, "ledger", "paper"))
    ap.add_argument("--bars", default=os.path.join(ROOT, "ledger", "bars"))
    ap.add_argument("--deployments", default=sc.DEPLOYMENTS)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        rows, st, info = run([b.strip() for b in a.bots.split(",") if b.strip()], a.ledger, a.bars, a.deployments)
    except LookupError as e:
        print(e)
        return 2
    anchor, official, head, now_s = info["anchor"], info["committer"], info["blok"], info["waktu_blok_s"]
    cv = info["cv"]
    if a.json:
        print(json.dumps({"chain": sc.CHAIN_ID, "SignalAnchor": anchor, "committer": official, "blok": head, "waktu_blok": ledger.utc_iso(now_s * 1000),
                          "ringkas": st, "baris": [asdict(r) for r in rows]}, indent=2, ensure_ascii=False))
    else:
        print(f"SignalAnchor {anchor} | committer resmi {official} | blok {head} ({ledger.utc_iso(now_s * 1000)}) | maxLag {cv.max_lag()} s | "
              f"jendela ungkap {cv.reveal_window()} s")
        for r in rows:
            print(f"  {r.bot:9s} {r.bar} {r.vonis:15s} {r.detail}")
        print(f"\nRINGKAS: {st}")
        print("VONIS: " + ("tidak ada ALARM" if not st["ALARM"] else f"{st['ALARM']} ALARM - lihat baris di atas"))
    return 1 if st["ALARM"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
