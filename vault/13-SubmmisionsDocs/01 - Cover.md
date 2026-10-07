---
tags: [submission, deck, slide]
slide: 1
id: cover
layout: cover
theme: night
section: ""
transition: fade
guards: ["commits >= 1"]
---

# 01 · Cover: the sealed crystal

**Bagian dari:** [[13-SubmmisionsDocs/00 - Hub Submission Deck]]
**Sumber:** [[10-Submissions/01 - Claims Cheat Sheet]] · [[06-Results/01 - Claims and Limits]] · `web/src/lib/copy.ts` (hero) · `docs/design/landing.md` · `web/public/data/snapshot.json`
**Ringkasan:** Sampul. Satu objek (kristal kaca tersegel, bahasa visual hero FE), satu kalimat janji, satu tagline, tiga chip status jujur, dan satu baris detak chain yang membuktikan deck ini jendela ke sistem yang berjalan.

## Scene

**Setting.** Deep indigo night, brightest behind the hero object and almost black in the corners. A soft violet halo sits behind the crystal and seems to breathe.

**Hero object: the Sealed Crystal.** A 3×3×3 cube of glass blocks floats right of centre, drawn in the same isometric language as the website hero. Most blocks are sealed indigo. Three at the top-left are clear, misty glass: empty slots in a record that has only just started. At the front corner three blocks have been lifted out and the cavity glows white-violet: the blocks inside are opened and verified. One luminous block hovers above the crystal, one sealed block drifts off to the right, and two dark hardware panels float at the edges like the plates of an exploded device.

**Orbits.** A dashed violet ring and a fainter lavender ring circle the crystal on an invisible floor. Specks of lavender dust hang in the air.

**Type.** FABIUS in giant bold white, left. Under it the hook in two weights: *Signals sealed* light, *before the outcome.* bold italic violet. Then the one-line tagline, three status chips, and the live URL.

**Live line.** Bottom right, small mono: `LIVE FROM CHAIN {{chain_id}} · #{{block}}`. It reads like a heartbeat. This deck is a window onto a running system, not a mock-up.

**Feeling.** Calm, expensive, a little ominous: a vault that has just opened one door.

## Slide

```yaml
kicker: "BNB CHAIN · TESTNET · PAPER ONLY"
title: "FABIUS"
hook: "Signals sealed\n*before the outcome.*"
tagline: "Plug in your bot or agent, prove every call on-chain, sell it to humans and AI via x402 + MCP."
chips:
  - {text: "Live on BNB testnet", kind: live}
  - {text: "Paper money, no real funds", kind: neutral}
  - {text: "Verify: no key, no gas", kind: neutral}
url: "fabius-one.vercel.app"
live: "LIVE FROM CHAIN {{chain_id}} · #{{block}}"
```

## Narration

*[Slow. Let the crystal sit on screen for a second.]*

Most trading bots show you their results after the market has spoken.

Fabius is built the other way around. A decision is sealed on BNB Chain before the outcome exists, and anyone can check it with no key and no gas.

This is the open platform where bots and AI agents bring their signals, prove them, and, once the proof exists, sell them one call at a time.

*[Beat.]* Let me show you how it works, and where the honest limits are.

## Claims check

| on the slide | evidence | status |
|---|---|---|
| Live on BNB testnet · chain {{chain_id}} · block #{{block}} | `web/public/data/snapshot.json` (`chain.block`, `generated_utc`), printed by `tools/web_snapshot.py` | live, as of {{asof}} |
| Paper money, no real funds | `config/uang_nyata.json` has `"aktif": false`; hero copy "No profit claims: paper only, for now" | true |
| Verify: no key, no gas | `tools/verify_signals.py` docstring; `/verify` page; MCP tool `fabius_verify` | true |
| Tagline: "sell it to humans and AI via x402 + MCP" | direction statement. Checkout runs on testnet with a no-value token; real-time paid signals are locked (slides 8 and 12 say so) | direction, not a sales claim |
