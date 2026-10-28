# public/web: live-site captures for the pitch video

These are read-only captures of the live site https://fabius-one.vercel.app, taken 7 Oct 2026 between 16:17 and 17:10 UTC (each JSON has its exact `capturedUtc`). Headless Chrome 154 rendered WebGL on the GPU (ANGLE D3D11), with `prefers-reduced-motion: no-preference`. Nothing was logged in, signed, paid or submitted. The only in-page presses are the /verify bot chip and its Verify button (a read-only `GET /api/verify`), plus /buy "Sign in", which opens Privy's in-page modal. Nothing inside that modal was touched. Non-GET requests to the Fabius app and gate were blocked during capture.

## How the clips were made

`scripts/capture-flow.mjs` with the flows in `scripts/flows.mjs`. A virtual clock (performance.now, Date, rAF, timers, CSS and Web Animations) advances exactly 1/60 s per frame, so page motion is real and smooth whatever the capture speed was. Each frame is a CDP JPEG piped into ffmpeg.

- **Encoding:** H.264, CRF 18, 60 fps, BT.709 tagged.
- **Desktop:** 2880x1800 (1440x900 CSS px at 2x).
- **Mobile:** 1170x2532 (390x844 at 3x).
- **Cursor:** headless capture draws no cursor. Redraw it from the JSON.

## Clips (`clips/<name>.mp4` + `<name>.json`)

| clip | page | what happens |
|---|---|---|
| home-hero (7.0 s) | `/` | Loaded with time stopped. The glass cube assembles from frame 0 and SIGNALS / SEALED / BEFORE THE OUTCOME spring up with the blinking caret. The cursor drifts over the hero (the cube leans with it) and ends hovering "See the proof feed". |
| home-journey (9.6 s) | `/` | "From candle close to proof": eased scroll through the 5 stations, holding at each (marks `station-1..5`). |
| home-mobile (9.0 s) | `/` on iPhone | Mobile hero assembling, then an eased scroll through the journey to the proof feed. |
| bot-b1 (8.4 s) | `/bot/B1-TREND` | Title, hover on "spec locked on-chain", "The rule, as locked" card centred, then "What it holds right now". |
| desk (14.1 s) | `/desk` | Title, the Fabius Live Book 3D pipeline centred for 7 s, then the 3D trading floor. |
| analysts (8.0 s) | `/analysts` | Hero question, then "Bot Fabius trades now" and the four pick cards. The cursor hovers two picks. |
| buy (8.4 s) | `/buy` | Offer card (B1-TREND, 0.01 FAB). The cursor goes to "Sign in (Google · Telegram · email)" and clicks, and the Privy modal shows for 2.5 s. |
| verify (11.0 s) | `/verify?bot=B1-TREND&bar=2026-10-06` | Clicks B2-RS, keeps 2026-10-06 (the latest closed bar: 5 signals committed and revealed) and clicks Verify. The four stations light up one by one and the 5-signal table and the "Verified" verdict follow. Ends on the verdict. |
| submit (8.0 s) | `/submit` | Title, pipeline strip, then hover on the Rule, Code and Feed method cards. |
| submit-agent (6.0 s) | `/submit-agent` | Hero, then the cursor tours the 4 steps. |
| status (6.1 s) | `/status` | Hero clock, then "Where today's bar is" with its stations revealing. |

### JSON fields

- **Clip info:** `fps`, `frameCount`, `viewport`, `deviceScaleFactor`, `video`.
- **`marks`:** name to frame index.
- **`shots`:** name to frame and still file.
- **`frames[i]`:** `{ t, scrollY, cursor: { x, y, down, visible } }`.
- **`boxes[name][i]`:** `[x, y, w, h]`, or a list of those for multi-element boxes; `null` means the element is absent at that frame.
- **Coordinates:** CSS px in viewport coordinates at that frame. Multiply by `deviceScaleFactor` for video px.
- **Box selectors:** `boxSpecs` lists how each box was found.

## Stills (`stills/`)

- **`<page>-full.jpg` + `.json`:** full-page desktop stills at DPR 2 and JPEG q88, for home, desk, analysts, bot-b1, buy, verify (B2-RS 2026-10-06 result shown), submit, submit-agent and status. The JSON has `[x, y, w, h]` boxes in document coordinates. Pages taller than 8000 CSS px are captured in tiles and stacked, because GPU surfaces wrap beyond 16384 px.
- **`<clip>-<shot>.jpg` + `.json`:** viewport stills at q95 taken at a frame of a clip, with that frame's boxes.

## Re-capture (from `vault/Video-Workspace`)

```
node scripts/capture-flow.mjs                                  # every clip + every still (about 15 min)
node scripts/capture-flow.mjs --clips-only --only verify,buy   # just these clips
node scripts/capture-flow.mjs --stills-only --only home        # just these stills
```

`--only` matches clip **and** still names (`desk`, `buy`, `verify` … exist as both), so always pair it with `--clips-only` or `--stills-only`. A re-capture overwrites `clips/` in place. Don't run it while a render reads these files.

Contact sheets for review go to `out/capture-check/<clip>-NN.jpg`, one cell per 0.5 s.

## Known behaviour (live site, not capture artefacts)

- The hero headline is a spring slide-up with a blinking caret, not per-letter typing.
- The Live Book idle animation is subtle.
- Chrome keeps scroll offsets in whole CSS px, so the slow ends of eased scrolls move in 1 px steps.
- Data is live: bars, counters, the analysts' picks and the verify result reflect the moment of capture.
