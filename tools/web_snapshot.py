"""Snapshot data untuk FE (`web/public/data/snapshot.json`): SEMUA angka di landing page berasal dari sini, dicetak dari ledger + buku + kunci + chain 97.

Isinya hanya keadaan publik (spesifikasi, tick, settle, komit, vonis pemeriksa, kunci, buku slot) - tidak ada kunci, tidak ada rahasia. Tanpa jaringan
(`--no-chain`) bagian chain diisi null dan halaman menulis "belum dibaca", bukan nol.

    python -X utf8 tools/web_snapshot.py              # baca chain juga (butuh eth-account/eth-abi, seperti verify_signals)
    python -X utf8 tools/web_snapshot.py --no-chain   # hanya repo
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from engine import anggaran, fd16, ledger, locks, pembunuh      # noqa: E402
from engine.spec import SPECS                                    # noqa: E402

OUT = os.path.join(ROOT, "web", "public", "data", "snapshot.json")
LEDGER_DIR = os.path.join(ROOT, "ledger", "paper")
BOOK = os.path.join(ROOT, "ledger", "book", "buku.jsonl")
DEPLOY = os.path.join(ROOT, "deployments", "97.json")
DECISION_ANCHOR = "0xDD162AFB5F5f92d5092f845A93660e3B38259330"


def git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def bots_block() -> list:
    out = []
    for bid, s in SPECS.items():
        p = os.path.join(LEDGER_DIR, f"{bid}.jsonl")
        out.append({"id": bid, "method": s.metode, "param": f"{s.param_nama} = {s.param}", "assets": len(s.universe), "tier": s.tier,
                    "spec_sha": s.sha(), "fingerprint": s.fingerprint(), "forward": os.path.exists(p), "killer": s.pembunuh})
    return out


def ledger_block() -> dict:
    out = {}
    for bid in SPECS:
        p = os.path.join(LEDGER_DIR, f"{bid}.jsonl")
        if not os.path.exists(p):
            continue
        recs = ledger.load(p)
        g = recs[0]
        ticks = [{"date": r["asof_date"], "signals": len(r.get("signal_ids", [])), "held": sum(1 for v in r.get("targets", {}).values() if abs(v) > 1e-12),
                  "lag_s": r.get("lag_s"), "emitted_utc": r.get("emitted_utc")} for r in recs if r["type"] == "tick"]
        settles = [{"date": r["bar_date"], "net_bps": round(r["net"] * 1e4, 2), "held": r.get("n_held")} for r in recs if r["type"] == "settle"]
        gaps = [{"date": r["asof_date"], "reason": r.get("reason")} for r in recs if r["type"] == "gap"]
        months = sorted({s["date"][:7] for s in settles})
        last_closed = ledger.last_closed_bar(int(time.time() * 1000))
        days_live = max(0, (last_closed - g["first_asof"]) // 86_400_000 + 1)
        out[bid] = {"genesis": g["first_asof_date"], "chain_ok": not ledger.verify_chain(recs), "ticks": ticks, "settles": settles, "gaps": gaps,
                    "n_signals": sum(t["signals"] for t in ticks), "n_settled_days": len(settles), "n_months": len(months), "head": recs[-1]["h"],
                    "days_live": days_live, "last_closed": ledger.date_of(last_closed)}
    return out


def book_block() -> dict:
    recs = ledger.load(BOOK) if os.path.exists(BOOK) else []
    ep = next((r for r in reversed(recs) if r.get("type") == "epoch"), None)
    if ep is None:
        return {}
    return {"epoch": ep["epoch"], "recorded_utc": ep["now_utc"], "capacity": 10, "book_sha": ep["book_sha"],
            "occupants": [{"id": e["bot_id"], "identity": e.get("identity", False)} for e in ep["buku"]],
            "challengers": [{"id": c["bot_id"], "gate": c.get("gate_verdict"), "shadow_days": c.get("shadow_days")} for c in ep.get("penantang", [])],
            "decisions": [{"id": d[0], "action": d[1], "reason": d[3]} for d in ep.get("keputusan", [])], "killers": ep.get("pembunuh", {})}


def locks_block() -> list:
    with open(DEPLOY, encoding="utf-8") as f:
        m3 = json.load(f).get("m3", {})
    out = []
    g = ledger.load(os.path.join(LEDGER_DIR, "B1-TREND.jsonl"))[0]
    anc = g.get("lock_anchor") or {}
    out.append({"label": "THRESHOLDS-v1", "what": "gate thresholds", "at_utc": anc.get("anchoredAt_utc"), "tx": anc.get("tx"), "where": "DecisionAnchor"})
    for bid, l in sorted((m3.get("locks") or {}).items()):
        out.append({"label": f"SPEC {bid}", "what": "bot specification", "at_utc": l.get("lockedAt_utc"), "tx": l.get("tx"), "where": "LockRegistry"})
    for name, p in (m3.get("pins") or {}).items():
        out.append({"label": name, "what": name, "at_utc": p.get("lockedAt_utc"), "tx": p.get("tx"), "where": "LockRegistry"})
    return sorted(out, key=lambda x: x["at_utc"] or "")


def fd16_block(led: dict) -> dict:
    p = fd16.Fd16Params()
    return {"required": {"signals": p.n_sinyal_min, "days": p.hari_min, "months": p.bulan_min},
            "bots": {b: {"signals": v["n_signals"], "days": v["n_settled_days"], "months": v["n_months"]} for b, v in led.items()},
            "lock": fd16.status()["state"]}


def chain_block() -> dict:
    import evm as evmmod
    import signal_commit as sc
    import verify_signals as vs
    from paper_tick import Views
    with open(DEPLOY, encoding="utf-8") as f:
        d = json.load(f)
    cs, m3 = d["contracts"], d["m3"]
    ev = evmmod.Evm(sc.rpc_urls(), sc.CHAIN_ID)
    ev.chain_check()
    cv = sc.AnchorView(ev, cs["SignalAnchor"], cs["LockRegistry"])
    head = int(ev.rpc("eth_blockNumber", []), 16)
    now_s = ev.block_timestamp()
    commits = vs.all_commits(cv)
    events = vs.revealed_events(ev, cs["SignalAnchor"], int((m3.get("deploy_block") or {}).get("SignalAnchor") or 0), head)
    rows, st = vs.verify(list(sc.BOTS_DEFAULT), LEDGER_DIR, Views(os.path.join(ROOT, "ledger", "bars")), cv, commits, events, m3["committer"], now_s)
    lock_count = ev.call_decode(cs["LockRegistry"], "lockCount()", (), (), ("uint256",))[0]
    return {"id": 97, "block": head, "block_utc": ledger.utc_iso(now_s * 1000), "signal_anchor": cs["SignalAnchor"], "lock_registry": cs["LockRegistry"],
            "decision_anchor": DECISION_ANCHOR, "committer": m3["committer"], "commit_count": len(commits), "lock_count": int(lock_count),
            "verdicts": [{"bot": r.bot, "bar": r.bar, "verdict": r.vonis, "n": r.n, "revealed": r.revealed, "lag_s": r.lag_s} for r in rows],
            "totals": st}


def build(with_chain: bool = True) -> dict:
    led = ledger_block()
    snap = {"v": 1, "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "repo_head": git_head(),
            "bots": bots_block(), "ledger": led, "book": book_block(), "locks": locks_block(), "fd16": fd16_block(led),
            "lock_states": {"thresholds": locks.status()["state"], "fd16": fd16.status()["state"], "killers": pembunuh.status()["state"],
                            "gate_budget": anggaran.status()["state"]},
            "chain": None}
    if with_chain:
        try:
            snap["chain"] = chain_block()
        except Exception as e:  # noqa: BLE001 - chain tak terbaca = null + alasan, bukan nol
            snap["chain_error"] = f"{type(e).__name__}: {str(e)[:160]}"
    return snap


def main() -> int:
    ap = argparse.ArgumentParser(description="Snapshot data publik untuk landing page.")
    ap.add_argument("--no-chain", action="store_true")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    t0 = time.time()
    snap = build(not a.no_chain)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(snap, f, indent=1, ensure_ascii=False)
        f.write("\n")
    c = snap.get("chain") or {}
    print(f"ditulis {os.path.relpath(a.out, ROOT)} ({time.time() - t0:.0f} s) | bot {len(snap['bots'])} | ledger {', '.join(snap['ledger'])} | "
          f"kunci {len(snap['locks'])} | chain {'blok ' + str(c.get('block')) + ', komit ' + str(c.get('commit_count')) + ', vonis ' + str(c.get('totals')) if c else snap.get('chain_error', 'tidak dibaca')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
