---
tags: [submission, deck, slide]
slide: 8
id: market
layout: checkout
theme: night
section: "07 — The market"
transition: fade
guards: []
---

# 08 · The market: pay per call, no subscription, no custody

**Bagian dari:** [[13-SubmmisionsDocs/00 - Hub Submission Deck]]
**Sumber:** [[04-Tools/TL32 - gerbang x402 per sinyal]] · [[04-Tools/TL20 - server MCP]] · [[02-Contracts/C9 - BotRegistry]] · [[02-Contracts/C10 - RevenueSplitter]] · [[08-Backlog/13 - Langkah Builder Tertunda]] · [[00-Overview/03 - Decisions]] (F-D72, F-D98, F-D100) · `engine/locks/harga.lock.json` · `web/src/lib/copy.ts` (beli, doors)
**Ringkasan:** Arus bisnis: pembeli (manusia lewat web/Telegram, agen lewat MCP + x402) membayar per panggilan tanpa langganan; penerbit membawa bot dan agen; Fabius menjalankan gerbang, bukti, dan kasir. Status jujur: kasir hidup di testnet dengan token tanpa nilai, bagi hasil penerbit sudah dibangun tapi belum di-deploy, sinyal waktu-nyata berbayar masih terkunci.

## Scene

**Setting.** Night.

**Top: the checkout, five glass cards in a row, joined by glowing arrows.** 01 BUYER, 02 HTTP 402, 03 SIGN, 04 SETTLE, 05 DELIVER. The first four are quiet glass; the last is tinted violet because it is where the buyer gets what they came for. Two chips at the top right name the lanes: HUMAN · WEB + TELEGRAM and AGENT · MCP + X402.

**Bottom left: the business flow in three blocks.** A violet cube on the left (publishers), a large, bright white-violet cube in the centre (Fabius), a clear misty cube on the right (buyers). Arrows run left to right (bots and signals in, signals and proof out) and back right to left (payment), plus one dashed arrow from Fabius back to the publishers: the revenue share, drawn dashed because it is built but not switched on.

**Bottom right: three status cards.** Each starts with a chip, because every claim on this slide wears its status: LIVE, BUILT, GATED.

**Feeling.** A cash register with the lights on and a padlock on the back door, and nothing hidden about which is which.

## Slide

```yaml
headline: "Pay per call.\n*No subscription. No custody.*"
lanes: ["HUMAN · web + Telegram", "AGENT · MCP + x402"]
flow:
  - {tag: "BUYER", title: "Ask for a signal", text: "A person on web or Telegram, or an agent via MCP, asks for today's signal."}
  - {tag: "HTTP 402", title: "Price first", text: "The gate answers 402 Payment Required, with the price: 0.01 FAB today."}
  - {tag: "SIGN", title: "Sign, don't send", text: "The buyer signs a permit. No gas to hold, no deposit, no balance."}
  - {tag: "SETTLE", title: "The gate settles", text: "x402 and Permit2 move the token. The gate pays the gas."}
  - {tag: "DELIVER", title: "Signal + proof", text: "It arrives with its commit proof, so anyone can check it was sealed first."}
triangle:
  builders: {title: "PUBLISHERS", text: "bring bots and agents"}
  fabius: {title: "FABIUS", text: "gates · proof · checkout"}
  buyers: {title: "BUYERS", text: "humans and agents"}
  arrow_in: "bots + signals"
  arrow_out: "signals + proof"
status:
  - {chip: "LIVE", kind: live, text: "x402 checkout on testnet, paid in a no-value token. No outside buyers yet."}
  - {chip: "BUILT", kind: built, text: "Publisher revenue share, 60/40: written and tested, not deployed."}
  - {chip: "GATED", kind: gated, text: "Real-time paid signals stay locked until the forward test and a legal review."}
```

## Narration

And now the business flow, in the order a buyer experiences it.

A person on the web or in Telegram, or an agent through MCP, asks for today's signal. The gate answers with an HTTP 402 and a price: zero point zero one FAB today. The buyer signs a permit. They send nothing, hold no gas, and keep no balance with us. The x402 contract settles it, our gate pays the gas, and the signal arrives together with its commit proof.

Look at the loop underneath. Publishers bring bots and agents. Buyers pay per call. Fabius runs the gates, the proof and the checkout. And the revenue-share contract that would pay publishers, sixty percent to them with our share only ever going down, is written and tested, not deployed.

Now the honest part. FAB is a test token with no value, and nobody outside our own team has bought a signal. Real-time paid signals stay locked until a bot passes the forward test and a legal review. We built the cash register, and we are keeping it on testnet until something has earned the right to be sold.

## Claims check

| on the slide | evidence | status |
|---|---|---|
| Price 0.01 FAB today | `engine/locks/harga.lock.json` (`dasar: 10000`, 6 decimals); locked table F-D100, rises only when a forward record is measured | live (testnet) |
| Sign a permit; gate pays gas; x402 + Permit2 settle | [[04-Tools/TL32 - gerbang x402 per sinyal]]; `README.md` (settlement with a 0-BNB client wallet) | live (testnet) |
| Human lane: web (Google/Telegram/email login) and Telegram `/buy` | `web/src/lib/copy.ts` (beli.*); `tools/x402_sinyal.py:900-905` | live; direct payment from chat proven once |
| Agent lane: MCP (free, read-only) to discover and verify, x402 to pay | `web/src/lib/mcp-tools.ts`; paid MCP (deposit) exists in code but is switched off ([[07-Testing/01 - Test Commands]] "MCP berbayar: MATI") | free MCP live; paid MCP off |
| FAB is a no-value test token; no outside buyers yet | `contracts/FabiusCredit.sol:8` ("Tanpa nilai: testnet 97 saja"); [[00-Overview/03 - Decisions]] F-D98 ("Ini BUKAN penjualan sinyal"); [[04-Tools/TL32 - gerbang x402 per sinyal]] (external buyers: zero) | true |
| Revenue share 60 % publisher / 40 % Fabius, Fabius share only decreases, not deployed | [[02-Contracts/C9 - BotRegistry]] and [[02-Contracts/C10 - RevenueSplitter]] ("DITULIS + DIUJI LOKAL, BELUM DI-DEPLOY"); `contracts/RevenueSplitter.sol` | built, not deployed |
| Real-time paid signals gated | `web/src/lib/copy.ts` doors.tier1 ("Opens only for a bot that passes the forward test, after a legal review"); [[10-Submissions/01 - Claims Cheat Sheet]] | gated |
