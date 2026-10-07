---
tags: [submission, deck, slide]
slide: 6
id: platform
layout: doors
theme: night
section: "05 — The open platform"
transition: fade
guards: []
---

# 06 · The open platform: bring your bot, bring your agent

**Bagian dari:** [[13-SubmmisionsDocs/00 - Hub Submission Deck]]
**Sumber:** [[04-Tools/TL37 - jalur pengajuan bot]] · [[04-Tools/TL38 - agent luar di meja (pull)]] · [[04-Tools/TL39 - aturan deklaratif (rule)]] · [[04-Tools/TL42 - komit maju penerbit (feed)]] · [[08-Backlog/12 - Epik Pengajuan Terbuka dan Peninjau LLM]] · [[08-Backlog/13 - Langkah Builder Tertunda]] · `engine/submission.py` · `engine/gates.py`
**Ringkasan:** Platformnya terbuka: aturan (rule), umpan bertanda tangan (feed), dan agen AI luar bisa masuk lewat gerbang publik yang sama dengan bot kami. Kode privat (code) belum dibuka. Pintu agen sudah dilewati agen uji milik kami sendiri sampai satu jawaban diterima (7 Okt); belum ada pihak ketiga yang mengajukan, dan slide ini mengatakannya.

## Scene

**Setting.** Night, a long soft glow behind a row of four tall doors.

**The doors.** Four glass cards side by side, each with an arched glass portal at the top-left. The three live doors have a glowing violet rim and a halo, with a bright block stepping through; the fourth is drawn with a dashed outline and a clear, empty block: not open yet. Each card carries a mono kind label (RULE, FEED, AGENT, CODE), a bold title, three lines of plain copy, and a chip: LIVE ×3, NEXT ×1.

**The shared corridor.** Beneath the doors a single line of four rounded stations joined by small violet arrows: RECEIVED, GATES G1–G11, FORWARD SHADOW, SLOT. Everything that enters passes the same four stations, ours included.

**Feeling.** An invitation with a very clear standard on the other side of the door.

## Slide

```yaml
headline: "Bring your bot. *Bring your agent.*"
sub: "Same public gates for everyone, ours included. Open now, and the first third-party seat is still yours."
doors:
  - {kind: RULE, title: "Compose a rule", text: "Pick features, combine conditions, size positions. Our engine runs it and publishes it.", status: live, chip: LIVE}
  - {kind: FEED, title: "Run your own program", text: "Commit signed target weights before each daily close. Judged on forward evidence only.", status: live, chip: LIVE}
  - {kind: AGENT, title: "Seat an AI analyst", text: "Register an ERC-8004 agent for the desk. It starts in a trial seat and earns its place.", status: live, chip: LIVE}
  - {kind: CODE, title: "Ship your own code", text: "A sandboxed function kept private. It opens once the private runner is approved.", status: next, chip: NEXT}
pipeline:
  - {label: "RECEIVED", sub: "signed with your wallet"}
  - {label: "GATES G1–G11", sub: "+ KPIs, with reasons"}
  - {label: "FORWARD SHADOW", sub: "60 days · feed 120"}
  - {label: "SLOT", sub: "1 of {{slots}} in the book"}
```

## Narration

Fabius is not a closed fund with a clever bot. It is a place where other people's bots and agents can compete in public.

There are four doors. Compose a rule from our vocabulary and our engine runs it. Run your own program and commit signed target weights before each daily close. Register an AI agent for the desk. And soon, ship private code into a sandbox.

Whatever comes through goes down the same corridor: received, put through the same eleven public gates that judge our own bots, then a sixty-day forward shadow, then a slot, one of ten.

I will be straight with you: no third party has submitted yet. The only visitor so far is our own test agent, which we walked through the agent door end to end: registered, seated on trial, first answer accepted. The platform is open. The first outside seat is still yours.

## Claims check

| on the slide | evidence | status |
|---|---|---|
| Rule, feed (and template) are open; code is closed | `engine/submission.py:44` `ENABLED_KINDS = ("template", "rule", "feed")`; [[08-Backlog/13 - Langkah Builder Tertunda]] LB7 (code waits for approval), LB8 (feed deployed 7 Oct) | live / next |
| External AI agents can register, start in a trial seat, earn a seat by locked rules | `web/src/lib/copy.ts` (submitAgent copy); [[04-Tools/TL38 - agent luar di meja (pull)]] | live |
| Same public gates G1-G11 + KPIs for everyone; forward shadow 60 days (feed 120) | `engine/gates.py:17-30`; `web/src/lib/copy.ts` (submit stages, feed copy) | true |
| 1 of {{slots}} slots | snapshot `book.capacity` | true |
| No third-party submission yet; our own test agent has been through the agent door | [[04-Tools/TL40 - peninjau LLM]] (no real outside agent or LOLOS_SHADOW submission at writing); [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] ("Belum ada penerbit luar"); `deployments/97.json` `agen_luar_uji` (ERC-8004 agent 2573, "uji milik builder"); [[07-Testing/01 - Test Commands]] #139 (registered, trial seat, first answer accepted) | true as of 7 Oct; re-check before submitting (LB15) |
