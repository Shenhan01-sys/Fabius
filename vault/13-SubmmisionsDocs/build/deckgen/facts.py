"""Fakta hidup untuk deck: angka dibaca dari `web/public/data/snapshot.json` (dicetak mesin dari ledger + chain, dengan cap waktu), bukan diketik.

Prinsip vault: "tiap angka menyebut perintah yang mencetaknya". Slide menulis `{{commits}}`; build menggantinya dengan angka snapshot, dan
`guards` di front matter membuat build GAGAL kalau kalimat naratif tidak lagi benar (mis. "0 dari 6 bot lolos" padahal satu bot sudah lolos).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
_TOKEN = re.compile(r"\{\{\s*([a-z0-9_]+)\s*\}\}")
_GUARD = re.compile(r"^\s*([a-z0-9_]+)\s*(==|!=|>=|<=|>|<)\s*(-?\d+)\s*$")


class FactError(Exception):
    pass


def find_snapshot(start: str) -> str | None:
    """Naik dari `start` sampai ketemu web/public/data/snapshot.json (akar repo)."""
    cur = os.path.abspath(start)
    for _ in range(8):
        cand = os.path.join(cur, "web", "public", "data", "snapshot.json")
        if os.path.isfile(cand):
            return cand
        nxt = os.path.dirname(cur)
        if nxt == cur:
            break
        cur = nxt
    return None


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def short_addr(a: str) -> str:
    return f"{a[:6]}…{a[-4:]}" if a and len(a) > 12 else a


def compute(snap: dict) -> dict:
    chain, totals = snap["chain"], snap["chain"]["totals"]
    gen = dt.datetime.strptime(snap["generated_utc"], "%Y-%m-%dT%H:%M:%SZ")
    conf = snap.get("confidence", {})
    req = snap.get("fd16", {}).get("required", {})
    verdicts = chain.get("verdicts", [])
    sah = [v for v in verdicts if v.get("verdict") == "SAH"]
    lags = [v["lag_s"] / 3600.0 for v in sah if v.get("lag_s")]
    gates = [c.get("gerbang_v1") for c in conf.values()]
    f = {
        "commits": int(chain["commit_count"]),
        "verified": int(totals.get("SAH", 0)),
        "alarms": int(totals.get("ALARM", 0)),
        "missed": int(totals.get("TIDAK DIKOMIT", 0)),
        "unopened": int(totals.get("BELUM DIUNGKAP", 0)) + int(totals.get("TIDAK DIUNGKAP", 0)),
        "before_lock": int(totals.get("SEBELUM KUNCI", 0)),
        "signals_total": sum(int(v.get("n") or 0) for v in sah),
        "signal_days": sum(1 for v in sah if (v.get("n") or 0) > 0),
        "silent": sum(1 for v in sah if not v.get("n")),
        "lag_min_h": f"{min(lags):.1f}" if lags else "n/a",
        "lag_max_h": f"{max(lags):.1f}" if lags else "n/a",
        "locks": len(snap.get("locks", [])),
        "locks_chain": int(chain["lock_count"]),
        "bots": len(snap.get("bots", [])),
        "bots_clock": len(snap.get("ledger", {})),
        "fd16_passed": sum(1 for b in conf.values() if b.get("fd16") == "LOLOS"),
        "fd16_signals": int(req.get("signals", 20)),
        "fd16_days": int(req.get("days", 20)),
        "fd16_months": int(req.get("months", 2)),
        "gate_rejected": sum(1 for g in gates if g == "TOLAK"),
        "gate_shadow": sum(1 for g in gates if g == "LOLOS_SHADOW"),
        "gate_unmeasured": sum(1 for g in gates if g == "TIDAK_TERUKUR"),
        "slots": int(snap.get("book", {}).get("capacity", 10)),
        "chain_id": int(chain["id"]),
        "block": f"{int(chain['block']):,}",
        "asof_date": f"{gen.day} {_MONTHS[gen.month - 1]} {gen.year}",
        "asof_time": gen.strftime("%H:%M UTC"),
        "head": str(snap.get("repo_head", ""))[:7],
        "signal_anchor": chain.get("signal_anchor", ""),
        "lock_registry": chain.get("lock_registry", ""),
        "decision_anchor": chain.get("decision_anchor", ""),
    }
    f["asof"] = f"{f['asof_date']} · {f['asof_time']}"
    f["signal_anchor_short"] = short_addr(f["signal_anchor"])
    f["lock_registry_short"] = short_addr(f["lock_registry"])
    f["bots_not_passed"] = f["bots"] - f["fd16_passed"]
    return f


def render(text, facts: dict, where: str = "") -> str:
    """Ganti {{kunci}}; kunci tak dikenal = galat (bukan teks kosong diam-diam)."""
    if not isinstance(text, str):
        return text

    def rep(m):
        k = m.group(1)
        if k not in facts:
            raise FactError(f"{where}: fakta '{k}' tidak ada (tersedia: {', '.join(sorted(facts))})")
        return str(facts[k])

    return _TOKEN.sub(rep, text)


def render_tree(obj, facts: dict, where: str = ""):
    if isinstance(obj, str):
        return render(obj, facts, where)
    if isinstance(obj, list):
        return [render_tree(x, facts, where) for x in obj]
    if isinstance(obj, dict):
        return {k: render_tree(v, facts, where) for k, v in obj.items()}
    return obj


def check_guard(expr: str, facts: dict) -> tuple[bool, str]:
    m = _GUARD.match(expr or "")
    if not m:
        raise FactError(f"guard tidak valid: {expr!r} (bentuk: kunci == angka)")
    key, op, rhs = m.group(1), m.group(2), int(m.group(3))
    if key not in facts:
        raise FactError(f"guard memakai fakta tak dikenal: {key}")
    lhs = facts[key]
    if isinstance(lhs, bool) or not isinstance(lhs, int):
        raise FactError(f"guard hanya untuk fakta bilangan bulat: {key} = {lhs!r}")
    ok = {"==": lhs == rhs, "!=": lhs != rhs, ">=": lhs >= rhs, "<=": lhs <= rhs, ">": lhs > rhs, "<": lhs < rhs}[op]
    return ok, f"{key} {op} {rhs} (sekarang {lhs})"
