---
tags: [submission, deck, slide]
slide: 3
id: gap
layout: trust_gap
theme: lavender
section: "02 — The gap"
transition: fade
guards: []
---

# 03 · The gap: money moves, proof doesn't

**Bagian dari:** [[13-SubmmisionsDocs/00 - Hub Submission Deck]]
**Sumber:** [[05-Ecosystem/02 - x402 Payment]] · [[00-Overview/02 - Business Process]] · [[06-Results/01 - Claims and Limits]] · `README.md` (settlement x402 nyata di chain 97)
**Ringkasan:** Dengan agen AI, masalahnya melebar: bot murah dibuat, LLM bisa membenarkan apa pun setelah kejadian, dan rel pembayaran (x402) sudah ada tetapi tidak membuktikan kapan sebuah panggilan dibuat.

## Scene

**Setting.** Still the pale lavender world of claims, now wide and horizontal.

**The bridge.** Two dark towers stand at the far left and far right: two agents. Between them runs a bridge of seven pale glass spans. The fourth span is missing: only a dashed red outline of it remains, a hole in the middle of the crossing.

**Two lines of travel.** A violet arc leaves a glowing coin marked 402 on the left tower and sails over the whole bridge to the right tower: payment passes. Under it a thin dashed red line follows the deck of the bridge, reaches the missing span, bends down and ends in a small red ✕: the proof falls through. Under the gap, three red mono questions: WHEN? · WHAT? · UNCHANGED?

**Below.** Three quiet glass cards, one per pressure on the problem: supply, hindsight, rails.

**Feeling.** The audience should feel the missing piece before they read a word.

## Slide

```yaml
headline: "Agents can already pay each other.\n*Money moves. Proof doesn't.*"
pay_label: "PAYMENT PASSES"
proof_label: "proof falls through"
gap_label: "WHEN? · WHAT? · UNCHANGED?"
points:
  - {tag: "SUPPLY", title: "Bots are cheap to launch", text: "Anyone can ship one in an afternoon. Nothing tells them apart."}
  - {tag: "HINDSIGHT", title: "Hindsight is free", text: "An LLM can justify any call after the fact. A reason is not a timestamp."}
  - {tag: "RAILS", title: "Payment rails are ready", text: "x402 moves the money. It cannot say when a signal was made."}
```

## Narration

Now add AI agents. Anyone can launch a bot in an afternoon. A language model can explain any call, convincingly, after the fact. And a new payment rail, x402, lets software pay software over plain HTTP.

So the money can move. We have done it ourselves on BNB testnet: an agent with zero BNB in its wallet paid another agent.

What cannot move is the proof. When was this signal made? What exactly was decided? Did anyone change it? A payment without provenance is a leap of faith at machine speed.

## Claims check

| on the slide | evidence | status |
|---|---|---|
| Agents can already pay each other (x402) | `README.md`: real settlement on chain 97, client wallet with 0 BNB, tx `0xb6093e59…`, balance read from chain | demonstrated on testnet |
| x402 says nothing about when a signal was made | by definition: a payment protocol carries payment, not provenance | framing |
| LLMs justify calls after the fact | framing; the chain cannot prove which model produced a call ([[06-Results/01 - Claims and Limits]]) | framing |
