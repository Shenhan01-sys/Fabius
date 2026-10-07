---
tags: [submission, deck, design]
type: design-style
---

# 99 · Design style: how the Fabius deck looks, and why

**Bagian dari:** [[13-SubmmisionsDocs/00 - Hub Submission Deck]]
**Sumber:** `docs/design/landing.md` (kontrak visual FE) · `docs/design/desk.md` · `docs/design/verify.md` · `docs/design/bot.md` · `web/src/app/globals.css` (token warna dan font) · `web/src/app/layout.tsx` (Archivo, Inter, JetBrains Mono) · [[10-Submissions/01 - Claims Cheat Sheet]] (suara dan klaim)
**Ringkasan:** Satu-satunya berkas yang memegang gaya deck. Blok `## Tokens` di bawah DIBACA oleh generator (`vault/13-SubmmisionsDocs/build/build_deck.py`): mengubah warna, font, ukuran, tagline, atau teks kaki di sini mengubah seluruh deck. Selebihnya adalah aturan yang harus diikuti saat menulis atau menambah slide.

## 1. The idea in one line

**Glass / Soft-depth**: lavender-pale light for the world of claims, indigo night for the world of proof, one violet accent, and one object, the glass block, that carries every meaning. It is the same system as the Fabius website, so a judge who opens the product recognises the deck.

## 2. Colour: one accent, red only for holes

| role | token | hex | use |
|---|---|---|---|
| night | `night` / `night2` / `deep` | `#0F0B26` / `#1A1442` / `#07051A` | proof slides (backgrounds, gradient top to bottom) |
| lavender | `lav` / `page` | `#ECE8FA` / `#F6F4FD` | claims slides (problem, gap) |
| ink | `ink` | `#15122B` | text on lavender, dark blocks |
| violet | `violet` | `#6E4BFF` | the accent: live states, key words, glow |
| violet 2 | `violet2` | `#9D86FF` | accent text on night, chart strokes |
| lav 3 | `lav3` | `#C9BDF2` | secondary text on night, rails |
| mist | `mist` | `#8B86A6` | tertiary labels, dashed outlines of things not yet open |
| gap | `gap` | `#FF5A6E` | **only** for holes: deleted, missing, refused. Never decoration |

Rules: no fourth hue. Contrast first: body text on night is `lav` or `lav3`; on lavender it is `ink` or `dim` (`#5B5680`). Glass is a white gradient at 10 % to 2 % alpha on night and 78 % to 42 % on lavender, with a 0.75 pt white edge. No hard shadows; on lavender a soft violet shadow lifts a card.

## 3. The story is told by light

- **Slides 2 and 3 (the problem) are lavender**: bright, flat, a little hollow. That is the world of claims.
- **Slide 4 flips to night** and stays there: from here every object glows. The flip is the story's turning point.
- The cover and the close are night, so the deck ends where it began.

## 4. One object, three states

The glass block is the unit of meaning, exactly as on the website (`docs/design/landing.md`):

| state | look | meaning | status chip |
|---|---|---|---|
| empty | clear misty glass, pale edge | an open slot, the future, not yet measured | `GATED` / `NEXT` (dashed) |
| sealed | deep indigo | committed on-chain, not yet opened | `BUILT` |
| open and verified | white-violet, glowing | revealed and recomputed to match | `LIVE` |

Everything is drawn with true 30° isometric projection from native PowerPoint polygons (select, recolour and move them): three faces per block, left darkest, right mid, top lightest. Horizontal compositions (rails, bridges, timelines) place each block at its own screen position instead of using long isometric axes.

## 5. Type

| role | font | weights | where |
|---|---|---|---|
| display | **Archivo** | regular for the calm half of a headline, bold italic violet for the accent word | titles, card titles, big numbers |
| body | **Inter** | regular, bold for emphasis | lead, card text, captions |
| mono | **JetBrains Mono** | regular, capitals with +1 pt tracking for tags | tags, chips, addresses, commands, footers |

Scale (pt): cover 96 · title 38-44 · lead 17-20 · card title 15-18 · card text 12.5-14 · mono tag 10.5-11 · footer 10. Accent syntax in the slide data: `*accent*` = bold italic violet, `**strong**` = bold, `` `code` `` = mono, `\n` = line break.

**Fonts.** Archivo is bundled as a variable font at `vault/Video-Workspace/public/fonts/Archivo-VF.ttf`; Inter and JetBrains Mono are free (SIL OFL) from Google Fonts. Install all three before opening the deck, or build with `--fonts safe` (Arial and Courier New, same layout, plainer look). The generator tags every run with a pitch-family hint so a viewer without the fonts falls back to a sans or a monospace, not to a serif.

## 6. Layout system

Canvas 13.333 × 7.5 in (16:9), 0.65 in side margins, footer at 7.08 in. Every slide has: a numbered marker (`NN — LABEL`, a mini glass block plus mono caps, the website's own motif), one headline placed in the real title placeholder (outline view and screen readers work), one illustration or evidence object, and a footer with the date and a live slide-number field. Twelve layouts, one per slide, each driven by the YAML block in its markdown file:

| layout | slide | what its data block holds |
|---|---|---|
| `cover` | 1 | `kicker`, `title`, `hook`, `tagline`, `chips`, `url`, `live` |
| `claims_gap` | 2 | `headline`, `lead`, `shown_*`, `holes` (3), `closing` |
| `trust_gap` | 3 | `headline`, `points` (3), `pay_label`, `proof_label`, `gap_label` |
| `seal` | 4 | `headline`, `sub`, `stations` (3), `principles` (3), `closing` |
| `rail` | 5 | `headline`, `sub`, `lock_note`, `stations` (5, each with a block `state`), `verify_cmd`, `verify_chips` |
| `doors` | 6 | `headline`, `sub`, `doors` (4), `pipeline` (4) |
| `desk` | 7 | `headline`, `steps` (3), `agents`, `hub_label`, `tower_label`, `stats`, `note` |
| `checkout` | 8 | `headline`, `lanes`, `flow` (5), `triangle`, `status` (3) |
| `showcase` | 9 | `headline`, `sub`, `images` (real screenshots, optional `crop`), `stats` (4), `asof` |
| `stack` | 10 | `headline`, `sub`, `contracts` (5, full addresses), `enforced`, `external`, `foot` |
| `honesty` | 11 | `headline`, `stat`, `proves`, `not_proves`, `evidence` (3), `ribbon` |
| `roadmap` | 12 | `headline`, `columns` (3), `closing`, `tagline`, `cta` |

## 7. Voice: sell the proof, never the profit

The deck must sound serious and valuable because it is exact, not because it is loud.

- **Lead with the mechanism, then the limit.** Every strong claim sits next to what it does not claim. *Proof of timing, not of profit.*
- **Status on everything.** LIVE (deployed on testnet), BUILT (in the repo, not switched on), GATED (waiting on evidence). Never describe a built or gated thing as live.
- **Numbers come from the machine.** Write `{{verified}}`, never `22`. The build fills them from `web/public/data/snapshot.json` and prints the "as of" time. A `guards` line in the front matter (for example `fd16_passed == 0`) fails the build when a sentence stops being true.
- **Forbidden** (from the Claims Cheat Sheet and Claims and Limits): profit or edge claims, win rates, "used by other agents", "has customers", "real-time signals available", "trustless", zkML or TEE verification, "first" or "only" among BNB projects, integration with BNB Agent Studio, anything real-money. The unit tests scan every slide for these phrases.
- **Words.** Say *publisher* for someone who brings a bot (in this vault, *builder* means the project owner). Say *no-value test token* for FAB. Say *paper* for money that is not real.

## 8. Accessibility

Every picture and key group has alt text. Colour never carries meaning alone (every chip also has a word and a shape). Titles sit in title placeholders. Speaker notes hold the visual script, the narration, the sources and the snapshot time for each slide, so a presenter can run the deck without opening these files.

## 9. Tokens

The generator reads this block and falls back to its own defaults for any missing key. Hex values are quoted so YAML keeps them as text.

```yaml
tokens:
  deck:
    title: "Fabius: Submission Deck"
    subject: "Open platform for bots and AI agents: every signal committed on BNB Chain before the outcome, sold per call over x402 and MCP."
    author: "Fabius"
    keywords: "Fabius, BNB Chain, x402, MCP, ERC-8004, commit-reveal, AI agents, paper trading"
    tagline: "Plug in your bot or agent, prove every call on-chain, sell it to humans and AI via x402 + MCP."
    footer: "FABIUS · SUBMISSION DECK"
    transition: fade
    language: "en-US"
    size_in: [13.333, 7.5]
  palette:
    night: "0F0B26"
    night2: "1A1442"
    deep: "07051A"
    ink: "15122B"
    lav: "ECE8FA"
    lav2: "DDD5F6"
    lav3: "C9BDF2"
    page: "F6F4FD"
    violet: "6E4BFF"
    violet2: "9D86FF"
    violet_dark: "3B22B8"
    indigo: "2A1F7A"
    mist: "8B86A6"
    dim: "5B5680"
    gap: "FF5A6E"
    white: "FFFFFF"
  fonts:
    profile: brand
    brand: {display: "Archivo", body: "Inter", mono: "JetBrains Mono"}
    safe: {display: "Arial", body: "Arial", mono: "Courier New"}
  type:
    cover: 96
    title: 44
    headline: 40
    sub: 20
    lead: 18
    body: 16
    card_title: 18
    card: 14
    caption: 12
    tag: 11
    mono: 11
    stat: 84
    stat_s: 44
    footer: 10
```
