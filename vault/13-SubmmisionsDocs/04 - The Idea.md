---
tags: [submission, deck, slide]
slide: 4
id: idea
layout: seal
theme: night
section: "03 — The idea"
transition: fade
guards: []
---

# 04 · The idea: commit first, prove later

**Bagian dari:** [[13-SubmmisionsDocs/00 - Hub Submission Deck]]
**Sumber:** [[02-Contracts/C7 - SignalAnchor]] · [[02-Contracts/C6 - LockRegistry]] · [[Concepts/Anchored Before Outcome]] · `contracts/SignalAnchor.sol` · `contracts/LockRegistry.sol`
**Ringkasan:** Pembalikan urutan: aturan dikunci dulu, sinyal disegel jadi satu akar Merkle per bar, dan cap waktu blok jadi alibi. Yang dibuktikan adalah urutan, bukan untung.

## Scene

**Setting.** The switch. The slide goes back to night and the palette flips from hollow to glowing: this is the moment the deck turns from problem to answer.

**Left.** The headline at poster size: *Commit first.* in light weight, **Prove later.** in bold italic violet. Under it one calm sentence of lead copy.

**Right: a timeline of three objects on one horizontal axis.** On the left a deep indigo cube with a small white seal slab resting on top: the decision, sealed. In the middle a tall, thin wall of white-violet light: the bar closing, the line nothing can cross. On the right a clear, misty, empty cube: the outcome, not known yet. A thin lavender axis with an arrowhead runs beneath all three, with glowing nodes and labels: DECISION, BAR CLOSES, OUTCOME.

**Below.** Three glass cards, the three rules of the idea. Then one closing line.

**Feeling.** Quiet certainty. The sealed cube is on the left of the wall, always.

## Slide

```yaml
headline: "Commit first.\n*Prove later.*"
sub: "Fabius seals every decision on-chain before the market answers, so nobody has to take our word for the order."
stations: ["DECISION|sealed on-chain", "BAR CLOSES|00:00 UTC", "OUTCOME|not known yet"]
principles:
  - {title: "Rules locked first", text: "A bot's rule is locked on-chain before it may commit a signal."}
  - {title: "Signals sealed", text: "One Merkle root per bar. A signal cannot be swapped afterwards."}
  - {title: "Block time is the alibi", text: "The chain proves when. Anyone can recompute what."}
closing: "The order is the product. *Proof of timing, not of profit.*"
```

## Narration

So we flip the order.

First, each bot's rule is hashed and locked on BNB Chain. The bot is not allowed to commit a single signal before that lock exists.

Then, every day, the bot's signals are folded into one Merkle root and committed to the SignalAnchor contract. The block time is the alibi. Only after that does the market answer.

I want to be precise about what this proves. It does not prove a signal was profitable. It proves the one thing a seller cannot fake: that the call came first.

## Claims check

| on the slide | evidence | status |
|---|---|---|
| A rule is locked on-chain before the bot may commit a signal | `contracts/SignalAnchor.sol:69` error `LockedAfterBar(lockedAt, asof)`: a spec locked after the bar cannot commit for it; `contracts/LockRegistry.sol:8,41` write-once | enforced by contract |
| One Merkle root per bar; reveals are checked against it | `contracts/SignalAnchor.sol:21-23` (header comment, items 2-4) | true |
| Proof of timing, not of profit | [[06-Results/01 - Claims and Limits]]; `README.md` ("Kontrak membuktikan keberadaan, keutuhan, penanda tangan, dan urutan waktu") | stated limit |
