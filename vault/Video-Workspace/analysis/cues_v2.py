"""Cue sheet v2 -> public/data/cues.json (format of analysis/mix_v2.py): scene cuts (music sections) and the SFX cues,
all anchored to voiceover words in public/data/vo.json, so a new read re-times the sound with the picture.
Only clean sounds from public/audio/sfx2 (no crash / broken sounds - the client's rule; analysis/check_sfx.py checks).

  python -X utf8 analysis/cues_v2.py
"""
from __future__ import annotations

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VO = json.load(open(os.path.join(ROOT, "public", "data", "vo.json"), encoding="utf-8"))
LINES = {l["id"]: l for l in VO["lines"]}
norm = lambda s: re.sub(r"[^a-z0-9']", "", s.lower())


def at(lid: str, w: str | int, n: int = 0) -> float:
    l = LINES[lid]
    if isinstance(w, int):
        return l["words"][w]["start"]
    hits = [x for x in l["words"] if norm(x["w"]) == norm(w)]
    return hits[n]["start"]


def cut(scene: str, lead: float = 0.28) -> float:
    ls = [l for l in VO["lines"] if l["scene"] == scene]
    i = VO["lines"].index(ls[0])
    prev = VO["lines"][i - 1]["end"] if i else 0.0
    return max(prev + 0.05, ls[0]["start"] - lead)


SCENES = ["hook", "reveal", "rules", "seal", "desk", "use", "verify", "open", "honest", "end"]


def build() -> dict:
    sec = [{"name": "intro" if s == "hook" else s, "start": round(0.0 if s == "hook" else cut(s), 3)} for s in SCENES]
    c = {s["name"]: s["start"] for s in sec}
    q: list[tuple[float, str, float, float]] = []  # (t, name, gain_db, pan)
    add = lambda t, n, g=-8.0, p=0.0: q.append((round(t, 3), n, g, p))
    # hook: cards drift in, the twist, soft dissolve
    add(0.05, "sub_swell", -10)
    add(0.20, "whoosh_long", -14, -0.2)
    add(at("hook1", "perfect"), "ui_pop", -14, 0.2)
    add(at("hook2", "after") - 0.05, "ui_tick", -10, 0.25)
    add(at("hook2", "after") + 0.1, "whoosh_soft_c", -15)
    add(at("hook2", "moves") + 0.15, "shimmer", -14)
    # reveal: bloom, the name, the seal, pull back to the page
    add(c["reveal"] - 0.35, "reveal_bloom", -8)
    add(at("rev2", "Meet"), "glass_chime_a", -9)
    add(at("rev2", "seals"), "glass_seal", -5)
    add(at("rev2", "before") - 0.1, "whoosh_soft_b", -12, 0.3)
    # rules: whip in, the lock, a rejected edit
    add(c["rules"] - 0.25, "whoosh_soft_a", -9, -0.4)
    add(at("rule2", "locked"), "lock_click", -6)
    add(at("rule2", "rewritten") - 0.25, "key_soft_a", -14, 0.2)
    add(at("rule2", "rewritten") - 0.12, "key_soft_b", -14, 0.2)
    add(at("rule2", "rewritten") + 0.05, "ui_hover", -11)
    # seal: candle closes, the call, the seal, the chain, the tug, not even us
    add(c["seal"] - 0.3, "whoosh_long", -11)
    add(at("seal1", "closes"), "ui_tick", -10, -0.3)
    add(at("seal1", "call"), "data_blip_a", -11)
    add(at("seal2", "seals"), "glass_seal", -4)
    add(at("seal2", "timestamp"), "swipe_up", -12, 0.3)
    add(at("seal2", "timestamp") + 0.75, "lock_click", -8, 0.3)
    add(at("seal2", "change") - 0.05, "ui_click_a", -10, 0.3)
    add(at("seal2", "us"), "glass_chime_b", -10)
    # desk: dip to night, agents, five votes, the formula, sealed
    add(c["desk"] - 0.4, "sub_swell", -13)
    add(at("desk1", "agents"), "ui_pop", -11)
    for i, w in enumerate(["make", "their", "picks"]):
        add(at("desk2", w), "data_blip_a" if i % 2 == 0 else "data_blip_b", -13, -0.4 + 0.4 * i)
    add(at("desk2", "picks") + 0.25, "data_blip_b", -13, 0.4)
    add(at("desk3", "formula"), "glass_chime_c", -10)
    add(at("desk3", "portfolio"), "ui_tick", -11)
    add(at("desk3", "sealed"), "glass_seal", -5)
    # use: three doors, the payment, the proof
    add(c["use"] - 0.3, "reveal_bloom", -12)
    add(at("use2", "web"), "whoosh_soft_c", -11, -0.5)
    add(at("use2", "Telegram"), "notify", -9)
    add(at("use2", "agent"), "key_soft_c", -13, 0.5)
    add(at("use2", "agent") + 0.15, "key_soft_d", -13, 0.5)
    add(at("use2", "MCP") + 0.6, "data_blip_b", -12, 0.5)
    add(at("use3", "x402"), "coin", -7)
    add(at("use3", "gas"), "ui_tick", -10, -0.2)
    add(at("use3", "subscription"), "ui_tick", -10, 0.2)
    add(at("use3", "proof"), "success", -7)
    # verify: dive into the page, pick, verify, four stations, no key no gas
    add(c["verify"] - 0.35, "whoosh_long", -10)
    add(at("ver2", "Pick"), "ui_click_a", -9)
    add(at("ver2", "day"), "ui_click_b", -9)
    for k in range(4):
        add(at("ver2", "rebuilds") + 0.25 + 0.55 * k, "glass_chime_" + "abca"[k], -12)
    add(at("ver3", "key"), "ui_pop", -10, -0.2)
    add(at("ver3", "gas"), "ui_pop", -10, 0.2)
    # open: whip, bring it, the gates
    add(c["open"] - 0.25, "whoosh_soft_a", -9, 0.4)
    add(at("open1", "Bring"), "swipe_up", -10)
    for k in range(6):
        add(at("open2", "same") + 0.16 * k, "ui_tick", -15, -0.5 + 0.2 * k)
    add(at("open2", "ours"), "success", -9)
    # honest: three plain facts, the board, 0 / 6
    add(c["honest"] - 0.3, "whoosh_soft_b", -11)
    add(at("end1", "paper"), "ui_pop", -12, 0.3)
    add(at("end1", "testnet"), "ui_pop", -12, 0.4)
    add(at("end2", "zero"), "data_blip_a", -12)
    add(at("end2", "passed"), "ui_tick", -10)
    # end: the crystal waits, check it, the card
    add(c["end"] - 0.35, "whoosh_long", -12)
    add(at("end3", "proof"), "glass_chime_a", -10)
    add(at("end4", "Check"), "glass_seal", -7)
    add(LINES["end4"]["end"] + 0.3, "shimmer", -12)
    q.sort()
    return {"duration": VO["duration"], "bpm": 120, "sections": sec,
            "sfx": [{"t": t, "name": n, "gain_db": g, "pan": p} for t, n, g, p in q]}


def main() -> None:
    d = build()
    out = os.path.join(ROOT, "public", "data", "cues.json")
    json.dump(d, open(out, "w", encoding="utf-8"), indent=1)
    print(f"cues.json: {len(d['sections'])} sections, {len(d['sfx'])} sfx cues, duration {d['duration']} s")
    for s in d["sections"]:
        print(f"  {s['start']:6.2f}  {s['name']}")


if __name__ == "__main__":
    main()
