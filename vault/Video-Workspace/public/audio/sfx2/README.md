# sfx2 - clean SFX library for the Fabius pitch video v2

Synthesised by `analysis/sfx_synth.py` (numpy/scipy, fixed seeds - re-running gives identical files): no
samples, no licences, owned outright. 48 kHz, 24-bit PCM WAV, every file starts and ends on exactly 0,
peak -1.5 dBFS (true peak <= -1 dBTP).

**Client rule:** nothing that sounds like a crash or something broken - no impacts, slams, debris,
falling pieces, shattering glass, glitches, static, crackle, sizzle, zaps, distortion, tape-stops, rewinds,
reverse sucks, scratches, snips, stamps. `analysis/check_sfx.py` enforces it mechanically (whitelist with
SHA-256 pins, banned-name patterns, cue-sheet check, acoustic screen); run it before every render.

**Sync point (`anchor`)**: the moment inside the file that should land on the picture event (whoosh = its
peak, riser = its end, chime = its onset, glass_seal = the chime at 0.60 s). `analysis/mix_v2.py` places a
cue so that the anchor lands on the cue time `t`. `gain` = a starting cue gain (dB) for a -14 LUFS mix
with voice; files are peak-normalised, so short sounds need less cut than long ones.

| file | length | ch | anchor | gain | use | how it is made |
|---|---|---|---|---|---|---|
| `whoosh_soft_a.wav` | 0.55 s | 2 | 0.319 s | -12 | quick card / panel slide, short camera nudge (peak at 0.32 s) | pink+white noise through a TPT band-pass arcing 380->1900->700 Hz (Q 1.4), faint resonant pitch band, decorrelated air, pan L->R |
| `whoosh_soft_b.wav` | 0.80 s | 2 | 0.440 s | -13 | page-to-page move, UI card lifting out of the page (peak at 0.44 s) | as whoosh_soft_a, slower and darker: band-pass 300->1500->520 Hz (Q 1.2), pan R->L |
| `whoosh_soft_c.wav` | 1.15 s | 2 | 0.690 s | -13 | bigger camera move / scene transition (peak at 0.69 s) | as whoosh_soft_a, longest of the three: band-pass 240->1250->420 Hz (Q 1.0), wide pan |
| `whoosh_long.wav` | 2.10 s | 2 | 1.218 s | -12 | 2 s camera fly-through (corridor, into the 3D scene); peak at 1.2 s | two noise layers (low body 150->700->260 Hz and high air 1.2->4.2->1.6 kHz), a quiet 46 Hz pressure swell, full L->R eased pan |
| `swipe_up.wav` | 0.42 s | 1 | 0.302 s | -11 | upward swipe / card flicked up / panel rising (peak at 0.30 s) | noise band-pass rising 650 Hz -> 5.2 kHz (Q 1.6) with a quiet sine glide 520 -> 1560 Hz under it |
| `ui_click_a.wav` | 0.24 s | 2 | 0.000 s | -4 | cursor click on a button / link (crisp, soft) | damped sines 1.75 kHz + 620 Hz with a 0.3 ms raised-cosine onset + a 2 ms band-passed noise tick at 3.2 kHz, low-passed 8 kHz, touch of small room |
| `ui_click_b.wav` | 0.25 s | 2 | 0.000 s | -6 | rounder click: toggle, select a bot / date, confirm a choice | damped sines 1.15 kHz + 380 Hz + 2.4 kHz noise tick, low-passed 6.5 kHz, small room |
| `ui_tick.wav` | 0.15 s | 2 | 0.000 s | -8 | tiny tick: counter step, list item, cursor hover tick, timestamp digit | damped sine 2.35 kHz (D7) + quiet octave + 1 ms noise tick at 5.2 kHz, 0.3 ms onset |
| `ui_hover.wav` | 0.36 s | 2 | 0.006 s | -15 | tiny airy blip: hover over a card, a pill lighting up | sine gliding E6 -> F#6 over 50 ms with 6 ms onset + breathy band-passed noise, small room |
| `ui_pop.wav` | 0.29 s | 2 | 0.002 s | -11 | soft bubble: an agent raises its cube, a chip/badge appears, a dot lands | sine with a fast upward pitch glide 280 -> 920 Hz (bubble resonance), 2 ms onset, 28 ms decay, quiet 2nd harmonic, low-passed 3.5 kHz |
| `key_soft_a.wav` | 0.29 s | 2 | 0.001 s | -11 | gentle keyboard typing (use a..d in rotation, 60-110 ms apart, +-1.5 dB) | laptop-key model: low thump (damped sine ~210 Hz) + soft plastic tick (noise band-pass ~1.9 kHz, 4 ms) + keycap ring, bottom-out 9 ms later, faint release tick ~80 ms later; low-passed 6.5 kHz |
| `key_soft_b.wav` | 0.29 s | 2 | 0.001 s | -9 | typing, variant b | as key_soft_a with thump 240 Hz, tick 2.3 kHz, release at 86 ms |
| `key_soft_c.wav` | 0.29 s | 2 | 0.001 s | -9 | typing, variant c (slightly darker; good for the space bar / enter) | as key_soft_a with thump 190 Hz, tick 1.7 kHz, release at 95 ms |
| `key_soft_d.wav` | 0.29 s | 2 | 0.001 s | -7 | typing, variant d | as key_soft_a with thump 260 Hz, tick 2.1 kHz, release at 72 ms |
| `glass_chime_a.wav` | 4.11 s | 2 | 0.003 s | -18 | clean glass chime, A5 (880 Hz): a station lights up, a block settles, a soft accent | additive glass partials 1 / 2 / 3.01 / 4.18 / 5.43 / 6.79 with per-partial decay (upper ones die fast), slow-beating twin fundamental, 2.5 ms raised-cosine onset, synthetic hall (RT60 1.9 s) |
| `glass_chime_b.wav` | 3.93 s | 2 | 0.003 s | -20 | clean glass chime, D6 (1175 Hz) - the tonic; pairs with a and c (D major pentatonic) | as glass_chime_a on D6 |
| `glass_chime_c.wav` | 3.77 s | 2 | 0.003 s | -21 | clean glass chime, F#6 (1480 Hz) - brightest of the three | as glass_chime_a on F#6, slightly darker partial balance |
| `glass_seal.wav` | 5.81 s | 2 | 0.600 s | -9 | HERO 'committed / sealed on-chain' moment. Sync point = the chime at 0.60 s | 0-0.6 s: air swell (noise band-pass sweeping 1.2 -> 4.2 kHz) and a warm sub swell (D2 + D3 sines, slow raised-cosine rise) leading in; at 0.6 s a strummed glass chord D5-A5-D6-F#6 (16 ms apart), a soft warm body (D4 + A4, 25 ms onset) and three tiny sparkles; big synthetic hall (RT60 2.8 s). No transient. |
| `lock_click.wav` | 0.31 s | 2 | 0.032 s | -5 | small precise latch: a padlock / lock icon closes, a rule is locked (sync = 2nd click, 32 ms) | two micro-clicks 32 ms apart (engage + seat), each damped sines (2.9/1.5 kHz, then 2.3/1.2 kHz) over a small body (650/520 Hz, 7-9 ms), 0.25 ms onsets, tiny room |
| `success.wav` | 3.12 s | 2 | 0.003 s | -15 | 3-note rising chime: verification passed, all stations lit, task done | glass notes A5 -> D6 -> F#6, 100 ms apart, rising velocity, hall (RT60 1.9 s) |
| `notify.wav` | 0.96 s | 2 | 0.003 s | -14 | a chat message arrives (Telegram reply, agent answer), soft | two short 'glass-marimba' notes B5 -> E6 85 ms apart (fast-decaying partials) + a soft puff of air |
| `coin.wav` | 2.42 s | 2 | 0.003 s | -15 | payment confirmed (x402 pay-per-signal), soft and pleasant | two bright glass notes D6 -> A6 75 ms apart with a faint inharmonic 2.76x 'coin' partial, then a few soft sparkle grains; hall |
| `data_blip_a.wav` | 0.20 s | 2 | 0.002 s | -12 | tiny high data ping: a row updates, a packet arrives, a counter ticks over | sine D7 (2349 Hz) with 1.5 ms onset and 16 ms decay over a quiet A6 |
| `data_blip_b.wav` | 0.24 s | 2 | 0.001 s | -14 | double data ping (A6 -> E7): a request + its answer, a chain confirmation | two sine pips 45 ms apart, 1 ms onsets, 10-12 ms decays |
| `shimmer.wav` | 2.90 s | 2 | 0.000 s | -17 | 1 s sparkle on glass: crystal glints, a card turns into light, the logo catches light | granular cloud of ~42 short glass grains on D-major-pentatonic notes (1.2-3.5 kHz, weighted low), density rising to 0.35 s then thinning, random pan, faint high air, hall (RT60 1.9 s) |
| `riser_2s.wav` | 2.00 s | 2 | 2.000 s | -13 | 2 s build into a cut / reveal (sync point = END of file) | pink+white noise through a TPT low-pass opening 260 Hz -> 7 kHz (late curve) with growing resonance and rising high-pass, + D3/A3/D4 saw chord gliding up an octave; ~30 dB rise, peaks at 96 %, shaped to 0 |
| `riser_4s.wav` | 4.00 s | 2 | 4.000 s | -14 | 4 s build (section lift, 'open' build) - sync point = END of file | as riser_2s over 4 s |
| `downlifter.wav` | 2.36 s | 2 | 0.000 s | -14 | settle after a peak: bright air falling away, a quiet two-note tone easing down a fourth | noise low-pass sweeping 7 kHz -> 650 Hz, quiet A4 + D5 sines easing down 5 semitones (never to zero, so not a tape-stop), narrowing stereo, 25 ms soft onset; sync point = start |
| `sub_swell.wav` | 3.00 s | 1 | 1.300 s | -15 | gentle low swell under a big moment (no punch); sync point = its peak at 1.3 s | D2 sine + 2nd/3rd harmonics (so laptops hear it), 1.3 s raised-cosine rise, 0.55 s release |
| `reveal_bloom.wav` | 5.54 s | 2 | 0.000 s | -10 | airy pad bloom for the logo / headline reveal; sync point = start | Dmaj9 pad (D3 A3 C#4 E4 F#4 A4, 5-voice detuned PolyBLEP saws + sine body) through a low-pass that blooms 320 Hz -> 3.2 kHz in 0.9 s then settles, high air, two glass notes (D6, A6), big hall (RT60 2.8 s) |

## remotion/ - picked from `@remotion/sfx` (CC0, attribution not required)

Fetched by `analysis/fetch_remotion_sfx.py` from https://remotion.media/ (the URLs exported by
`node_modules/@remotion/sfx`); the original's SHA-256 is pinned there (a changed upstream file stops
the script) and recorded in `remotion/SOURCES.json`. Admitted only if CC0 and clean on the acoustic
screen, then conformed to the sfx2 format (48 kHz 24-bit, edge fades, peak -1.5 dBFS).

| file | source | licence | use | screen notes |
|---|---|---|---|---|
| `remotion/whoosh.wav` | 1bob, freesound.org/s/831936 (via @remotion/sfx `whoosh`) | CC0 1.0 (Remotion detail page) | very short (0.15 s) low air swish: a quick cut, a small card flick; darker than sfx2 whooshes | original flags ['EDGE'] -> after conforming none |

Not taken: `mouse-click` (screen: HF_HEAVY (100 % of energy > 4 kHz) - thin, sharp double click; sfx2/ui_click_a/b instead); `switch` (screen: HF_HEAVY (71 % > 4 kHz), starts/ends mid-signal - plasticky click; sfx2/ui_click_b instead); `ding` (licence: Remotion says it is 'not explicitly released under a free license' (myinstants) - also 97 % of its energy in 2-6 kHz; sfx2/glass_chime_* instead); `shutter-modern` (screen: NOISY_HF + HARSH_ONSET + CRACKLE - mechanical clatter); `page-turn` (screen: HF_HEAVY (72 % > 4 kHz); the file is actually Kenney 'Draw Knife 1' (blade scrape)); `whip` (briefed out (a whip crack); the file is a racquet swish with a sharp crack transient); `snapchat-notification / mac-quack` (brand / meme sounds - not ours to borrow for a product launch); `vine-boom / bone-crack / record-scratch / windows-xp-error / ...` (meme, impact, crack or error sounds - banned by the client rule (screen: THUMP / CRACKLE / PITCH_DIVE / ABRUPT_END)).

Regenerate: `python -X utf8 analysis/sfx_synth.py` then `python -X utf8 analysis/check_sfx.py`
(if a sound was changed on purpose, review it, then refresh its pin with
`python -X utf8 analysis/check_sfx.py --print-whitelist`).
