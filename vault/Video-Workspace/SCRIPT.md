# Fabius pitch v2 - voiceover script and where every claim comes from

The read lives in `analysis/vo_v2.py` (`SCRIPT`, one entry per line with its scene and the pause after it). Word timings:
`public/data/vo.json`. This page is the same script with its sources, checked on 7 Oct 2026 against the repo and the live
system (`vault/Conventions.md`: a number only goes in when a command prints it, on the day it is quoted;
`vault/10-Submissions/01 - Claims Cheat Sheet.md`: no profit, no edge, no real money). Plan and exit criteria:
[[Video-Workspace/PLAN-v2]] (P172).

| # | Scene | Line | Source (printed 7 Oct 2026 unless noted) |
|---|---|---|---|
| hook1-2 | hook | Every trading bot has a perfect track record. The catch? It's always written after the market moves. | framing; the profit cards are made-up bots ("AlphaBot", "MoonSignals" ...), not real accounts; deck slide 2 |
| rev1-2 | reveal | So we built the opposite. Meet Fabius. It seals every signal on BNB Chain, before the market answers. | site hero `fabius-one.vercel.app` ("commits every signal on BNB Chain before the market answers"); `contracts/SignalAnchor.sol` |
| rule1-2 | rules | First, the rules. Each bot's strategy is locked on-chain, so it can't be quietly rewritten after a bad day. | `deployments/97.json` `m3.locks`: B1-TREND 2026-10-02 15:49:20Z (spec `0x23cb026b`), B3-CARRY 15:49:25Z (`0xc528abf5`), B2-RS 2026-10-04 16:37:25Z (`0x2dd6ccf2`), B4 16:37:29Z (`0x78bb0e32`), B5 16:37:34Z (`0x2dfb0fa4`), B6 16:37:38Z (`0x4a6d180d`); LockRegistry is write-once (a new spec = a new, visible lock) |
| seal1-2 | seal | Every day, the candle closes, the bot makes its call, and Fabius seals it with a timestamp no one can change. Not even us. | `python -X utf8 tools/verify_signals.py --json` on the origin/master ledger, 16:25:14Z (block 135,429,662): SAH 20, ALARM 0, 22 official commits; B1-TREND bar 2026-10-06 SAH, committed 36,402 s after the close (2026-10-07 10:06:42 UTC), commit id `0xc73c4df3...`; `SignalAnchor` `TooLate` |
| desk1-3 | desk | Who picks the bot? A desk of AI agents. Every five minutes, analysts with their own on-chain identities make their picks, and a locked formula turns them into one paper portfolio, sealed before the cycle ends. | `GET /desk` 15:56:44Z (`src/three/data/desk-snapshot.json`): seats berita/glm/muse/qwenplus active, qwen + x2573 trial; 281 cycles committed in 24 h; `params_v2_sha 0x6f613e50...` (formula r4, F-D116); `DeskAnchor.CYCLE = 300`; ERC-8004 ids from `deployments/97.json` `analis.agents` (2558, 2559, 2561, 2566, 2567) + `agen_luar_uji` 2573 |
| use1-3 | use | Want today's signal? Get it on the web, in Telegram, or let your AI agent fetch it over MCP. Pay per signal with x402. No gas, no subscription, and it arrives with its proof. | `/buy` page (capture); Telegram text = `tools/x402_sinyal.py` `_teaser_en` + `tg_reply` with `GET /teaser/B1-TREND` (bar 2026-10-06, 0.01 FAB); `GET /signal/B1-TREND` = HTTP 402, `PAYMENT-REQUIRED` exact / eip155:97 / 10000 (0.01 FAB) / permit2 (`public/data/live/`); MCP `tools/list` at `fabius-one.vercel.app/mcp` (18 tools, `fabius_signal` paid; P157 on since 7 Oct); "test token, no value" shown on screen |
| ver1-3 | verify | Then check it yourself. Pick any bot, any day. Fabius rebuilds the signal from public data and the chain. No key. No gas. | `/verify` (capture: B2-RS, the page's default day, "Verified"); `tools/verify_signals.py` (no key, no gas) |
| open1-2 | open | Got your own bot, or your own agent? Bring it. It faces the same public gates as ours. | `/submit` (Rule / Code (soon) / Feed) + `/submit-agent` (live still); `engine/gates.py` G1 PIT ... G11 CAPACITY; "60 days forward on paper before a slot" = `/submit` page text |
| end1-2 | honest | No profit promises. It's paper money on testnet, and zero of six bots have passed the forward test yet. | `python -X utf8 -m engine.cli ledger fd16` 15:57:15Z: all six BELUM CUKUP DATA (B1 0/20 signals, B2 15/20, B3 4/20 + 4 days, B4 4/20, B5 2 days, B6 3 days); `config/uang_nyata.json` `"aktif": false` |
| end3-4 | end | Fabius waits for proof. Don't trust. Check it. | site `/verify` headline "Don't trust. Check it." |

## On screen: what is real and where it came from

- **Website frames** = deterministic captures of the live site, 7 Oct 2026 16:17-16:53 UTC (`scripts/capture-flow.mjs`, virtual time,
  60 fps, read-only: no login, no form sent): home hero, "From candle close to proof", `/bot/B1-TREND`, `/buy` (Privy sign-in opened,
  not used), `/verify` (live check), `/submit`, `/analysts`, `/status`; `/submit-agent` = still (`scripts/capture-web.mjs`, 22:40 WIB).
  Cursor positions are the recorded ones; cards "lifted" out of a page are crops of the same frames (`src/ui/browser.tsx` `PageCrop`).
- **3D** = the site's own scenes re-rendered (`src/three/`): the hero crystal (22 verified / 4 sealed / 0 empty = live hero counts), the
  desk floor and the Live Book pipeline from the `GET /desk` snapshot. The Live Book robot shows the newest revealed winner (B2-RS, 6 Oct
  15:55Z) because the live cycle's winner is hidden for 24 h; its five positions are drawn as equal "locked" bars.
- **Motion.so** = the reveal plate (`public/motion/reveal-motion-so.mp4`, generated 7 Oct from our brief + three site screenshots;
  the block number in its corner, #135,379,370, comes from the hero screenshot).
- **Made-up** (and shown as such): the profit cards of "other bots" in the hook; "your-bot" in the gates corridor.

## Voice, music, sound

Voice: `edge-tts` `en-US-AvaMultilingualNeural` (chosen by the builder 8 Oct over Andrew / Emma / Brian), 96 kbit/s. Music: original procedural bed `analysis/music_v2.py`
(120 BPM, D major / B minor, sections from `public/data/cues.json`). SFX: synthesized clean library `public/audio/sfx2/` + Remotion's
CC0 `whoosh`; no crash / broken sounds (`analysis/check_sfx.py` = PASS; the old kit's files were removed from this workspace).
Mix: `analysis/mix_v2.py` -> `public/audio/mix_v2.mp3`, -14.0 LUFS, true peak -1.2 dBTP (ffmpeg ebur128, 8 Oct).
