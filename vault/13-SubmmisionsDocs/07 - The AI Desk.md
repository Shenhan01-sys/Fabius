---
tags: [submission, deck, slide]
slide: 7
id: desk
layout: desk
theme: night
section: "06 — The AI desk"
transition: fade
guards: []
---

# 07 · The AI desk: a desk of agents, sealed on the clock

**Bagian dari:** [[13-SubmmisionsDocs/00 - Hub Submission Deck]]
**Sumber:** [[04-Tools/TL36 - meja v2 bot + instrumen]] · [[04-Tools/TL34 - meja AI 5 menit]] · [[04-Tools/TL33 - agent analis]] · [[08-Backlog/11 - Epik Meja AI v2]] · `contracts/DeskAnchor.sol` · `contracts/SelectionAnchor.sol` · `docs/design/desk.md` · `tools/meja2.py`
**Ringkasan:** Meja AI: agen analis (tiap agen punya identitas ERC-8004) menilai keenam bot terkunci, rumus tetap yang diterbitkan memilih satu bot, kode menerapkan aturan bot itu ke satu buku paper. Akar Merkle siklus 5 menit masuk DeskAnchor selama siklus berjalan.

## Scene

**Setting.** Night. A diorama of a trading floor, seen in the same isometric language as the website's /desk page.

**Left of the stage: three workstations.** Each is a dark glass desk with a glowing monitor slab standing on it and a small violet cube for the analyst sitting beside it. Under each one a mono label: ANALYST, and below it ERC-8004 identity.

**The wiring.** From each desk a thin violet line runs right to a vertical bus, and from the bus one line, with an arrowhead, runs into the centre.

**The centre: the formula.** Three concentric rings lie on the floor and a luminous white-violet core cube floats at their heart: the fixed, published formula. Label: FIXED FORMULA r4.

**Right of the stage: the tower.** A line leaves the hub and climbs to a tower of twelve slabs, alternating indigo and dark glass, with the top three glowing white-violet: the last twelve five-minute cycles, the freshest committed. Label: DESKANCHOR · LAST 12 CYCLES.

**Chips and note.** EVERY 5 MIN · ERC-8004 ANALYSTS · ONE PAPER BOOK · MAX 5 POSITIONS, and in small mono at the right: REAL DECISIONS · PAPER MONEY.

**Left column.** Headline, then three numbered steps.

**Feeling.** Agents at work, and a clock you can hear ticking.

## Slide

```yaml
headline: "A desk of agents.\n*Sealed on the clock.*"
steps:
  - {title: "Analysts score", text: "Each AI analyst reads the same data and scores the six locked bots. Direction is not its call."}
  - {title: "A fixed formula picks", text: "A published formula (r4) picks one bot. Plain code applies its rule to one paper book."}
  - {title: "The cycle is sealed", text: "One Merkle root per 5-minute cycle goes to DeskAnchor, which refuses it once the cycle is over."}
agents:
  - {name: "ANALYST", role: "ERC-8004 identity"}
  - {name: "ANALYST", role: "ERC-8004 identity"}
  - {name: "ANALYST", role: "ERC-8004 identity"}
hub_label: "FIXED FORMULA r4"
tower_label: "DESKANCHOR · LAST 12 CYCLES"
tower_blocks: 12
stats: ["EVERY 5 MIN", "ERC-8004 ANALYSTS", "ONE PAPER BOOK · MAX 5 POSITIONS"]
note: "REAL DECISIONS · PAPER MONEY"
```

## Narration

Now the part that makes Fabius more than a registry: a desk where AI agents work as a team.

Every five minutes, a panel of AI analysts, each with its own ERC-8004 identity on BNB Chain, reads the same data. They do not trade. They score our six locked bots and say which instruments matter and how much exposure they want. Direction is not their decision.

A fixed, published formula merges the scores and picks one bot. Then plain code applies that bot's locked rule to a single paper book, with at most five positions.

And the whole cycle is sealed. One Merkle root goes to the DeskAnchor contract, and the contract only accepts it while the five minutes are still running. The agents collaborate. The clock keeps them honest.

## Claims check

| on the slide | evidence | status |
|---|---|---|
| 5-minute cycle; root accepted only while the cycle runs (300 s) | `contracts/DeskAnchor.sol:5,8,29` ("SELAMA siklusnya masih berjalan", `CYCLE = 300`) | enforced by contract |
| Analysts score the six bots, up to 8 instruments, an exposure; direction is not the AI's call | [[04-Tools/TL36 - meja v2 bot + instrumen]] ("AI tidak menentukan arah: kode menjalankan aturan bot terkunci") | true |
| Fixed published formula r4; one paper book, max 5 positions | `tools/meja2.py:26` (`"v": 4`), `tools/meja_slot.py:14` (`maks_posisi: 5`); formula hash shown on `/desk` as `params_v2_sha` ("locked" = published hash, not a LockRegistry lock) | true |
| Each analyst has an ERC-8004 identity | `deployments/97.json` (house agents ids 2558, 2559, 2561, 2566, 2567); [[04-Tools/TL33 - agent analis]] | true; the count that votes changes over time, so no number is shown |
| Not every cycle lands | 271 of 288 cycles in the 6 Oct audit (94.1 %, [[08-Backlog/01 - Backlog]]); the slide says "sealed on the clock", never "every cycle" | stated in notes |
| Paper money only | [[10-Submissions/01 - Claims Cheat Sheet]]; `config/uang_nyata.json` off | true |
