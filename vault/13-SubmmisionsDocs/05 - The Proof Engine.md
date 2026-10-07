---
tags: [submission, deck, slide]
slide: 5
id: engine
layout: rail
theme: night
section: "04 — How it works"
transition: fade
guards: ["alarms == 0"]
---

# 05 · The proof engine: from candle close to proof

**Bagian dari:** [[13-SubmmisionsDocs/00 - Hub Submission Deck]]
**Sumber:** [[02-Contracts/C7 - SignalAnchor]] · [[02-Contracts/C6 - LockRegistry]] · [[04-Tools/TL20 - server MCP]] · `web/src/lib/copy.ts` (journey, verify) · `tools/verify_signals.py` · `docs/design/verify.md`
**Ringkasan:** Satu sinyal melewati lima stasiun publik, dari bar tutup sampai diperiksa ulang siapa pun. Langkah 0 (aturan dikunci) mendahului semuanya; blok berubah dari kaca kosong menjadi tersegel, tercatat di chain, lalu terbuka dan bercahaya.

## Scene

**Setting.** Night. A wide, faint violet halo lies along a horizontal rail across the middle of the slide.

**The rail.** One glowing lavender rail with an arrowhead, five round nodes on it. Above each node sits one isometric block, and the block changes state station by station, using the three states of the Fabius block language:

1. **The bar closes.** A clear, misty glass cube: an empty slot, nothing in it yet.
2. **The bot decides.** The cube turns deep indigo: a decision exists, sealed.
3. **Sealed.** The same indigo cube with a small white seal slab floating on top: signals folded into one Merkle root.
4. **Committed on BNB Chain.** The sealed cube now rests on two dark chain slabs: it has landed in a block.
5. **Opened and checked.** The cube is white-violet and glowing: revealed, recomputed, verified.

**Step 0.** A wide violet pill above the rail, left: *Step 0 · rules locked on-chain first*. It comes before the first node, because the lock comes before the first signal.

**Under each node.** A mono time label (00:00 UTC, + seconds, + minutes, ≤ 12 h, after), a bold title, two short lines of copy, and the contract that does the work in small mono type.

**Bottom strip.** A glass bar holding the verification command in mono and three chips: NO KEY, NO GAS, SAH = recomputes exactly.

**Feeling.** A factory line where every station has a window.

## Slide

```yaml
headline: "From candle close to proof"
sub: "One signal, five stations. Every station is public and can be checked without us."
lock_note: "Step 0 · rules locked on-chain first"
stations:
  - {time: "00:00 UTC", title: "The bar closes", text: "The daily candle settles. Nothing later can enter the signal.", state: clear, tag: "public market bars"}
  - {time: "+ seconds", title: "The bot decides", text: "One locked method, one parameter: enter, exit or resize.", state: sealed, tag: "LockRegistry rule"}
  - {time: "+ minutes", title: "Sealed", text: "Every signal is salted and folded into one Merkle root.", state: root, tag: "Merkle root"}
  - {time: "≤ 12 h", title: "Committed on BNB Chain", text: "The root lands in SignalAnchor. The block time is the alibi.", state: committed, tag: "SignalAnchor.commit"}
  - {time: "after", title: "Opened and checked", text: "Payloads are revealed. Anyone recomputes them from public bars.", state: open, tag: "reveal · verify"}
verify_cmd: "python -X utf8 tools/verify_signals.py"
verify_chips: ["NO KEY", "NO GAS", "SAH = recomputes exactly"]
```

## Narration

Here is the whole machine, one signal at a time.

Before anything else, the bot's rule is locked on-chain. Then the daily bar closes at midnight UTC, and from that moment nothing new can enter the signal.

The bot decides. Its signals are salted and folded into a single Merkle root, and that root is committed to the SignalAnchor contract. The contract accepts it only within twelve hours of the close, and rejects anything late. So far our commits have landed {{lag_min_h}} to {{lag_max_h}} hours after the close.

Then the payloads are opened, and anyone can recompute them from public price bars. One command, no key, no gas. If it matches, the verdict is SAH: it recomputes exactly.

## Claims check

| on the slide | evidence | status |
|---|---|---|
| Commit within 12 h of the close, late commits revert | `contracts/SignalAnchor.sol:71` error `TooLate`; `maxLag` 43200 s in `deployments/97.json` | enforced by contract |
| Commits so far land {{lag_min_h}}-{{lag_max_h}} h after the close | computed from `chain.verdicts[].lag_s` in the snapshot ({{asof}}) | measured |
| SAH = recomputes exactly | `web/src/lib/copy.ts` verify.explain.SAH ("Proof of timing, not of profit") | true |
| No key, no gas | `tools/verify_signals.py` docstring (needs a clone of the repo); `/verify` page needs nothing | true |
