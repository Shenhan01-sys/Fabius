---
tags: [submission, deck, slide]
slide: 2
id: problem
layout: claims_gap
theme: lavender
section: "01 — The problem"
transition: fade
guards: []
---

# 02 · The problem: every track record is written after the move

**Bagian dari:** [[13-SubmmisionsDocs/00 - Hub Submission Deck]]
**Sumber:** [[10-Submissions/02 - Project Detail]] · [[00-Overview/01 - Briefing]] · [[06-Results/01 - Claims and Limits]]
**Ringkasan:** Masalah inti dalam satu gambar: pembeli hanya melihat hasil sesudah pasar menjawab, dan tidak bisa memeriksa sinyal yang dihapus, aturan yang diubah, atau panggilan yang ditulis mundur.

## Scene

**Setting.** The only light slide in the first half, on purpose: pale lavender, bright, flat and a little hollow. This is the world of claims. It looks clean, and that is the trick.

**Left.** The headline in light weight with one word in bold violet italic: *after*. Two calm lines of lead copy. At the bottom, one bold sentence that lands the point.

**Right, top: the screenshot.** A frosted-glass card, the kind of thing a signal seller posts. Inside it, a smooth violet line climbs from bottom-left to top-right with a glowing dot at the end. No axes, no numbers, on purpose: it is a picture of a promise, and the caption under it says so (*screenshot · posted after the fact*). A small dashed chip in the corner reads AFTER THE MOVE.

**Right, bottom: the holes.** Three stacked rows, each a glass card with a dashed red outline and a cracked, empty glass block as its icon. Red appears here because the Fabius visual system reserves red for holes and only holes: deleted signals, edited rules, back-dated calls.

**Feeling.** Reassuring on the surface, uneasy once you read the three rows.

## Slide

```yaml
headline: "Every track record is written *after* the move"
lead:
  - "A screenshot of profit. A curated history. A backtest with no costs."
  - "Bots and signal sellers show you the result once the market has already answered."
shown_label: "WHAT YOU ARE SHOWN"
shown_chip: "AFTER THE MOVE"
shown_caption: "screenshot · posted after the fact"
holes:
  - {title: "Deleted signals", text: "The losing calls quietly disappear."}
  - {title: "Edited rules", text: "The strategy is fitted to the data afterwards."}
  - {title: "Back-dated calls", text: "Decided after the candle closed."}
closing: "A buyer can check none of it. *Trust is the whole product.*"
```

## Narration

Look at any signal seller's page. You will see a chart that only goes up. A screenshot of profit. A backtest with no trading costs.

Now look at what you cannot see. Which calls were deleted the moment they lost? Which rule was rewritten to fit the data? Which prediction was posted after the candle had already closed?

A buyer can check none of it. That is the real problem. It is not that there are too few bots. It is that nobody can prove a bot was honest.

## Claims check

| on the slide | evidence | status |
|---|---|---|
| Sellers show results after the fact; buyers cannot check deletions, edits or back-dating | framing of the problem: `10-Submissions/02 - Project Detail.md` ("tidak ada yang bisa membuktikan bot-nya jujur") | framing |
| The rising line | stylised drawing with no axes and no data; labelled "screenshot · posted after the fact" | illustration, not a data claim |
| Red marks the holes | FE rule: red only for gaps (`docs/design/landing.md`) | design rule |
