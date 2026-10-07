---
tags: [submission, deck, slide]
slide: 12
id: close
layout: roadmap
theme: night
section: "11 — What is next"
transition: fade
guards: []
---

# 12 · Roadmap and close: live, built, gated

**Bagian dari:** [[13-SubmmisionsDocs/00 - Hub Submission Deck]]
**Sumber:** [[08-Backlog/13 - Langkah Builder Tertunda]] · [[08-Backlog/01 - Backlog]] · [[00-Overview/06 - Roadmap]] · [[10-Submissions/01 - Claims Cheat Sheet]] · [[04-Tools/TL45 - MCP berbayar meja (P157)]] · [[04-Tools/TL41 - kode pengguna di sandbox (code)]] · [[04-Tools/TL43 - evaluasi meja F4]] · `README.md`
**Ringkasan:** Penutup yang jujur. Tiga kolom memakai tiga keadaan blok FE sebagai legenda status: terbuka-bercahaya (LIVE), tersegel (BUILT, menunggu sakelar), kaca kosong (GATED sampai bukti ada). Lalu satu kalimat penutup, tagline, dan tiga cara memeriksa sendiri.

## Scene

**Setting.** Night again, mirroring the cover: the deck ends where it began.

**Three columns, three block states.** Each column is a glass card headed by a small isometric block. LIVE has a white-violet glowing block. BUILT has a deep indigo sealed block. GATED has a clear, empty glass block and a dashed outline. The legend is the product's own block language, so the status of everything on the slide can be read without a word.

**The closing band.** A wide violet-tinted glass band across the bottom. On the left, in large type: *Fabius refuses the battle until the proof exists.* Under it the tagline in small type. On the right, three stacked pills: the live URL (glowing), the repository, and the verification command in mono.

**Feeling.** The calm after a long climb. The ask is a click, a clone and a command, not a pledge.

## Slide

```yaml
headline: "Live. Built. *Gated.*"
columns:
  - state: live
    chip: LIVE
    title: "Running on BNB testnet"
    items:
      - "Proof feed and /verify: no key, no gas"
      - "{{bots_clock}} bots on public forward ledgers"
      - "AI desk every 5 minutes, one paper book"
      - "Open submissions: rule, feed and AI agent"
      - "x402 checkout with a no-value token; free MCP server"
  - state: built
    chip: BUILT
    title: "Written, waiting on a switch"
    items:
      - "Publisher revenue share (BotRegistry + RevenueSplitter)"
      - "Private code submissions"
      - "Paid MCP access to the desk"
      - "Desk evaluation shadow"
  - state: gated
    chip: GATED
    title: "Locked until the evidence exists"
    items:
      - "Real-time paid signals: a bot must pass the forward test, then a legal review"
      - "Real money and mainnet: off the table until then"
closing: "Fabius refuses the battle until the proof exists."
tagline: "Plug in your bot or agent, prove every call on-chain, sell it to humans and AI via x402 + MCP."
cta:
  - {text: "fabius-one.vercel.app", kind: live, raw: true}
  - {text: "github.com/Shenhan01-sys/Fabius", raw: true}
  - {text: "python -X utf8 tools/verify_signals.py", raw: true}
```

## Narration

Let me end with where everything stands, in three words: live, built, gated.

Live today on BNB testnet: the proof feed and the verify page, {{bots_clock}} bots on public forward ledgers, the AI desk running every five minutes, open submissions for rules, feeds and agents, and the x402 checkout with a test token.

Built, and waiting on a switch: the publisher revenue share, private code submissions, paid MCP access to the desk, and an evaluation shadow for the desk.

Gated until the evidence exists: real-time paid signals, which need a bot to pass the forward test and then a legal review. Real money and mainnet are off the table until then.

The man this project is named after, Fabius Maximus, beat Hannibal by refusing the battle Hannibal wanted. We refuse to sell what has not been proven.

*[Pause.]* Do not take our word for any of this. One command, no key, no gas. And when you are ready: plug in your bot or agent, prove every call on-chain, and sell it to humans and AI through x402 and MCP, once the proof exists.

## Claims check

| on the slide | evidence | status |
|---|---|---|
| LIVE items | slides 5-9 and their claims tables; [[08-Backlog/13 - Langkah Builder Tertunda]] LB1 and LB8 (gate and web deployed 7 Oct, feed open) | live as of {{asof_date}} |
| BUILT: revenue share | [[02-Contracts/C9 - BotRegistry]], [[02-Contracts/C10 - RevenueSplitter]] ("BELUM DI-DEPLOY"); LB2 pending | built |
| BUILT: private code | [[04-Tools/TL41 - kode pengguna di sandbox (code)]]; `engine/submission.py` keeps `code` out of `ENABLED_KINDS` (LB7) | built, closed |
| BUILT: paid MCP, desk evaluation shadow | [[04-Tools/TL45 - MCP berbayar meja (P157)]] (switches off); [[04-Tools/TL43 - evaluasi meja F4]] (LB10 pending) | built |
| GATED: real-time paid signals; real money and mainnet | `web/src/lib/copy.ts` doors.tier1; `config/uang_nyata.json` off; [[00-Overview/06 - Roadmap]] ("mainnet" not on the roadmap) | gated |
| Fabius Maximus beat Hannibal by refusing battle | `README.md` lines 5-6 | true (history) |
