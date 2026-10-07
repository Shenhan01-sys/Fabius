---
tags: [submission, deck, slide]
slide: 9
id: live
layout: showcase
theme: night
section: "08 — Live product"
transition: fade
guards: ["alarms == 0", "missed == 0", "silent >= 1"]
---

# 09 · Live product: not a mockup, it is running

**Bagian dari:** [[13-SubmmisionsDocs/00 - Hub Submission Deck]]
**Sumber:** [[04-Tools/TL19 - web landing]] · [[04-Tools/TL20 - server MCP]] · [[Dashboard]] · `web/public/data/snapshot.json` (dicetak `tools/web_snapshot.py`) · `docs/design/landing.md` · `docs/design/bot.md`
**Ringkasan:** Bukti bahwa ini produk yang berjalan: dua tangkapan layar nyata (desktop beranda, mobile halaman bot) dan empat angka yang dicetak mesin dari ledger + chain dengan cap waktu. Angka tidak diketik; semuanya `{{token}}` dari snapshot.

## Scene

**Setting.** Night, with a wide violet glow behind the devices.

**Left: two real devices.** A desktop browser frame, URL `fabius-one.vercel.app`, shows the landing hero as a visitor sees it: the 3D glass cube and the giant headline *SIGNALS SEALED BEFORE THE OUTCOME*. Overlapping its right edge is a phone showing the bot page for B1 TREND: the rule as locked, the identity badge and the chips with the spec lock. The screenshots are real, captured from the current build of the web app on 7 Oct. We cropped away only the navigation and the counter chips of the hero, because those counters belong to the 3D cube's legend, not to the numbers on the right.

**Right: four stat cards, stacked.** A big white number on the left of each card and one short line on the right. The numbers are the live ones from the snapshot: verified commits, how many of them are silent days, bots on forward ledgers, on-chain locks.

**Under the devices.** One mono line with the snapshot time, block number and chain: the receipt for every number on the slide.

**Feeling.** Evidence, not decoration.

## Slide

```yaml
headline: "Not a mockup. It is running."
sub: "Open it, sign in with Google, Telegram or email, and check any signal yourself."
images:
  - file: ui-home-desktop.jpg
    kind: desktop
    caption: "fabius-one.vercel.app"
    alt: "Fabius landing page: a glass cube and the headline Signals sealed before the outcome"
    crop: [0.0, 0.25, 0.0, 0.0]
  - file: ui-bot-mobile.jpg
    kind: phone
    alt: "Fabius bot page for B1 TREND on a phone: the rule as locked and the on-chain spec lock"
stats:
  - {value: "{{verified}}", label: "daily commits verified on-chain: {{alarms}} alarms, {{missed}} missed"}
  - {value: "{{silent}}", label: "silent days: the bot stayed put, and that was sealed too"}
  - {value: "{{bots_clock}}", label: "bots on public forward ledgers, written by machines"}
  - {value: "{{locks}}", label: "on-chain locks: bot rules and policies, stamped by block time"}
asof: "SNAPSHOT {{asof}} · BLOCK {{block}} · CHAIN {{chain_id}} · PRINTED BY tools/web_snapshot.py"
```

## Narration

*[Point at the screen.]* This is not a storyboard. The site is live, and the numbers on the right are printed by a script from the public ledger and from BNB Chain, with a timestamp.

{{verified}} daily commits are on-chain and verified, with {{alarms}} alarms and {{missed}} missed. {{silent}} of those are silent days, days when a bot decided to do nothing, and even that was sealed. {{bots_clock}} bots keep public forward ledgers that a machine writes with no human in the loop. And {{locks}} locks, bot rules and policies, each stamped with its block time.

A visitor can sign in with Google, Telegram or email, read the exact rule a bot is locked to, and verify a day on their own.

## Claims check

| on the slide | evidence | status |
|---|---|---|
| {{verified}} commits verified, {{alarms}} alarms, {{missed}} missed | snapshot `chain.totals` ({{asof}}); `python -X utf8 tools/verify_signals.py` | live |
| {{silent}} of them are silent days | snapshot `chain.verdicts` entries with `n = 0`; FE copy: "No signal today: the bot stayed put. The empty root is committed anyway." | live |
| {{bots_clock}} bots on forward ledgers written by machines | snapshot `ledger`; [[Dashboard]] ("hari pertama penuh TANPA tangan manusia") | live |
| {{locks}} on-chain locks | snapshot `locks` (bot specs plus thresholds, forward-test rules, kill rules, slot book, gate budget) | live |
| Screenshots | captured 7 Oct from a local `npm run build` of `web/` at the current master; hero counter chips cropped out (they count cube blocks, not locks) | real |
