# Fabius pitch — voiceover script and where every claim comes from

The script lives in `analysis/script.py` (one line per entry, with the plate it belongs to). This page is the same
script with its sources, checked on 6–7 Oct 2026 against the repo (`vault/Conventions.md`: a number only goes in
when a command prints it; `vault/10-Submissions/01 - Claims Cheat Sheet.md`: no profit, no edge, no real money).

| # | Plate | Line | Source |
|---|---|---|---|
| 1 | hook | Over two thousand years ago, Rome kept losing to Hannibal in open battle. | history (Ticinus, Trebia 218 BC, Trasimene 217 BC) |
| 2 | hook | So one general did something radical: he refused the battles Hannibal wanted. | `README.md` (the name) |
| 3 | hook | His name was Fabius. | Quintus Fabius Maximus "Cunctator" |
| 4–6 | problem | Most trading bots want the battle. / They charge in, then show you a screenshot of profit, taken after the market moved. / You can't check what they decided, or when. | framing; the bot on screen is generic ("SOME BOT") |
| 7 | idea | Fabius is a paper-trading desk that commits its decisions to BNB Chain before the outcome exists. | `contracts/SignalAnchor.sol` (commit after the bar, within `maxLag`), `contracts/DeskAnchor.sol` (root only while the 300 s cycle runs); allowed sentence since F-D89 |
| 8 | idea | Even the decision to do nothing. | `web/public/data/snapshot.json`: B1-TREND bars 02–05 Oct committed with n = 0, all SAH |
| 9–10 | lock | It starts with the rules. / Each of our six bots has its strategy hashed and locked on-chain. | `deployments/97.json` `m3.locks` (B1/B3 02 Oct, B2/B4/B5/B6 04 Oct) |
| 11 | lock | A strategy that wasn't locked first can't commit a signal. | `SignalAnchor` `NotLocked` / `LockedAfterBar`; snapshot verdict "SEBELUM KUNCI" for bar 01 Oct of B1 and B3 |
| 12 | commit | Every bar, a bot's signals become one Merkle root, committed to chain 97. | `tools/signal_commit.py`; B2-RS bar 05 Oct: 4 signals, lag 31,458 s |
| 13 | commit | Late commits are rejected. Every reveal is checked against the root. | `SignalAnchor` `TooLate` (`maxLag_s` 43200), `BadProof` |
| 14 | commit | Anyone can rerun the ledger. No keys needed. | `python -X utf8 -m engine.cli ledger verify` (output shown is the real run: six ledgers SAH) |
| 15–18 | desk | On top runs the AI desk. / Every five minutes, AI analysts, each with an ERC-8004 identity, vote on which bot to run, and where. / A locked formula turns their votes into one book. / And its root must reach the chain before the five minutes are up. | F-D109/F-D112/F-D116 (PARAMS2 r4 `0x6f613e50…`), `DeskAnchor.CYCLE = 300`; active seats 2558, 2559, 2561, 2566, 2567 (`config/agents.json`, `deployments/97.json`) |
| 19 | split | The AI picks the rulebook. Code computes the position. | F-D112 #4: direction is computed by the bot's locked rule |
| 20–22 | open | And the desk is open. / Bring your own bot as declarative rules, or plug in your own agent. / Every bot runs the same gates in public, and every verdict comes with its reason. | `engine/rule.py` (P167a), `tools/agen_luar.py` (F-D121), `engine/gates.py` G1–G11, `.github/workflows/bot-review.yml`; the run shown is B3-CARRY's real report (`ledger/book/laporan`) and the slot decision "shadow 3 < 60 days" |
| 23–24 | bnb | Signals sell over x402, and the buyer pays no gas. / All on testnet, with a test token. No real money, by design. | `tools/x402_sinyal.py` (gate + Telegram replies), FabiusCredit (FAB) on chain 97; `config/uang_nyata.json` `"aktif": false`, F-D124 |
| 25–28 | honest | Because here's what we don't claim: profit. / The forward clock started on October 1st. / To pass, a bot needs 20 signals, 20 days, 2 months, and a confidence interval above zero. / Today, zero of six have passed. | `engine/fd16.py`, `python -X utf8 -m engine.cli ledger fd16` (06 Oct: all six "BELUM CUKUP DATA") |
| 29–31 | end | So Fabius does what Fabius does best. / It waits. / Fabius. Refuse the battle. Prove the decision. | — |

Product frames are real captures of `web/` (built locally, `scripts/capture-web.mjs`, `scripts/capture-sections.mjs`);
pages that read the Railway gate were served by the real gate code run locally on the repo
(`tools/x402_sinyal.py --local`). The Telegram chat uses the bot's real reply templates (`tools/x402_sinyal.py`
`HELP`, `/buy`) and the real signal image (`tools/sinyal_gambar.py`, B2-RS bar 2026-10-05). The desk's 5-minute
votes are drawn as sealed ballots, not numbers: no desk cycle data was available offline, so none is shown.

## On screen: the objects

Each claim is shown as the thing it is about, so the picture still explains it with the sound off.

| Plate | Object |
|---|---|
| hook | a time axis; Rome's glass blocks topple at Ticinus, Trebia, Trasimene; Fabius's block stays standing |
| idea | the web's "From candle close to proof" journey (real page frames); two sealed blocks for "n = 0" |
| lock | six thick glass tablets, one rule each; a scan beam hashes each into its spec sha; padlocks snap shut with the real lock times; a signal of bar 01 Oct bounces off SignalAnchor's LockedAfterBar wall |
| commit | a glass candle (the bar) lets out four real signals of B2-RS; light climbs the Merkle tree to one root; a copy is sealed into chain 97; a late commit hits the maxLag wall; one block opens and its proof path lights up |
| desk | the 300 s dial, five analyst orbs with their ERC-8004 ids, sealed ballots, the locked formula card with the book's five slots, DeskAnchor |
| split | the rulebook cards and the analysts' page (the AI's pick) against the bot's locked rule (the code's position) |
| open | glass doors onto /submit and /submit-agent; eleven solid gate portals G1–G11 with B3-CARRY's real statuses |
| bnb | the Telegram bot's real replies and signal image, the x402 handshake, the buyer's gas gauge at zero, the /buy Mini App; a real-money switch that is off and will not flip |
| honest | PROFIT struck out, the /proof-feed record page, four F-D16 tanks, the six bots' rows: 0 / 6 passed |
