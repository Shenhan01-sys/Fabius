---
tags: [submission, deck, slide]
slide: 11
id: honesty
layout: honesty
theme: night
section: "10 — Built to be doubted"
transition: fade
guards: ["fd16_passed == 0", "gate_rejected >= 1"]
---

# 11 · Built to be doubted: zero of six, said out loud

**Bagian dari:** [[13-SubmmisionsDocs/00 - Hub Submission Deck]]
**Sumber:** [[06-Results/01 - Claims and Limits]] · [[10-Submissions/01 - Claims Cheat Sheet]] · [[06-Results/32 - Hasil P90 R1+R2]] · [[06-Results/34 - Hasil P90 Gelombang 2]] · [[08-Backlog/13 - Langkah Builder Tertunda]] · [[00-Overview/05 - Corrections]] · `README.md` · `web/public/data/snapshot.json` · `engine/fd16.py`
**Ringkasan:** Slide kepercayaan. Angka "0 / 6" dicetak dari snapshot (dijaga guard: build gagal bila satu bot lolos dan kalimatnya jadi salah). Apa yang dibuktikan chain vs tidak; tiga bukti bahwa standar yang sama dipakai ke diri sendiri: bot kami ditolak gerbang kami, peninjau LLM kami hanya bisa menahan atau menolak (tidak pernah memberi slot) dan versi untuk agen gagal kalibrasi (5 dari 6) sehingga mati, gerbang diuji pada pasar sintetik.

## Scene

**Setting.** Night. The most austere slide in the deck: very little decoration, because the content is the decoration.

**Left: the number.** A giant white **0 / 6** with a violet halo behind it, and under it in bold: *bots have passed the forward test*. In small mono underneath, the pass bar: 20 signals, 20 settled days, 2 months.

**Centre and right: two columns.** The left column is a solid glass card, title WHAT THE CHAIN PROVES, with violet check marks. The right column is the same size but dashed and quieter, title WHAT IT DOES NOT PROVE, with dashes instead of checks. Same visual weight, on purpose: the limits get as much room as the claims.

**Bottom: three evidence cards.** Three small glass cards, each a time we turned the standard on ourselves.

**Ribbon.** One line of mono capitals across the bottom, like the marquee on the website: PAPER ONLY · NO EDGE CLAIMED · EVERY RULE LOCKED BEFORE THE DATA · VERIFY, DON'T TRUST.

**Feeling.** Calm confidence from a team that publishes its own failure rate.

## Slide

```yaml
headline: "A desk built to be doubted"
stat:
  value: "{{fd16_passed}} / {{bots}}"
  label: "bots have passed the forward test"
  sub: "needs {{fd16_signals}} signals · {{fd16_days}} settled days · {{fd16_months}} months"
proves:
  - "The signal existed before the outcome"
  - "It was not changed afterwards"
  - "Which rule produced it, and when that rule was locked"
not_proves:
  - "That a call was right or profitable"
  - "That a particular model produced it"
  - "Any edge. None is claimed."
evidence:
  - {title: "We reject our own bots", text: "{{gate_rejected}} of {{bots}} house bots fail our entry gates; {{gate_unmeasured}} cannot be measured; {{gate_shadow}} runs in shadow."}
  - {title: "Our AI reviewer cannot approve", text: "It can hold or reject, never grant a slot. The agent version missed calibration: off."}
  - {title: "Gates tested on noise", text: "Synthetic test: no-edge strategies pass about 1% (budget 5%)."}
ribbon: "PAPER ONLY · NO EDGE CLAIMED · EVERY RULE LOCKED BEFORE THE DATA · VERIFY, DON'T TRUST"
```

## Narration

Here is the slide I would most like you to remember.

Zero of six. {{fd16_passed}} of our {{bots}} bots have passed the forward test, which needs {{fd16_signals}} signals, {{fd16_days}} settled days and {{fd16_months}} months, with a confidence interval above zero. We say it on the landing page and we say it here.

What the chain proves: that a signal existed before the outcome, that it was not changed, and which rule produced it. What it does not prove: that a call was right, that it made money, or which model produced it. We claim no edge.

And we apply the standard to ourselves. {{gate_rejected}} of our {{bots}} bots are rejected by our own entry gates. Our AI reviewer can only hold or reject, it can never grant a slot, and the version that reviews agents missed its calibration, five cases out of six, so it is switched off. Our gates were tested on synthetic noise: strategies with no edge passed about one percent of the time, against a five percent budget.

A desk built to be doubted is a desk you can actually check.

## Claims check

| on the slide | evidence | status |
|---|---|---|
| {{fd16_passed}} of {{bots}} bots passed the forward test | snapshot `confidence[*].fd16` ({{asof}}); guard `fd16_passed == 0` stops the build if this changes | live; guarded |
| Pass bar: {{fd16_signals}} signals, {{fd16_days}} days, {{fd16_months}} months | snapshot `fd16.required`; `engine/fd16.py` (also needs mean net > 0 and a lower confidence bound above 0) | locked on-chain (`FABIUS-FD16-MAJU-v1`) |
| What the chain proves and does not prove | `README.md` ("Kontrak membuktikan keberadaan, keutuhan, penanda tangan, dan urutan waktu. Ia tidak membuktikan keputusan itu benar, menguntungkan, atau benar-benar dihasilkan model yang disebutkan") | stated limit |
| {{gate_rejected}} of {{bots}} house bots rejected by the gates, {{gate_unmeasured}} unmeasurable, {{gate_shadow}} in shadow | snapshot `confidence[*].gerbang_v1` (TOLAK / TIDAK_TERUKUR / LOLOS_SHADOW); B1 holds the identity slot by the builder's choice, not by passing | live |
| AI reviewer can only hold or reject; its agent version missed calibration (5 of 6) and is off | `engine/peninjau.py` (`keputusan_bot`: no output grants a slot); `python -X utf8 tools/peninjau_llm.py status` ("peninjau agent: KALIBRASI GAGAL, aktif TIDAK"); `ledger/peninjau/kalibrasi/20261007T124452Z-agent.json`; [[00-Overview/03 - Decisions]] F-D131 | true as of 7 Oct; re-check before submitting (LB15) |
| No-edge strategies pass about 1 % vs a 5 % budget | [[06-Results/32 - Hasil P90 R1+R2]] (0.82-1.18 %), [[06-Results/34 - Hasil P90 Gelombang 2]] (up to 1.45 % after the proposed G8 change, not yet anchored); synthetic worlds only | measured on synthetic markets |
