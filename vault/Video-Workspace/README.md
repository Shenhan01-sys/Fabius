# Fabius pitch video v2 - Remotion, the live site, the site's own 3D, Motion.so

A ±94 s pitch (1920x1080, 60 fps) for Fabius: consumer + agentic, built so that every frame is a pure function of the frame number
(React + [Remotion](https://www.remotion.dev) 4.0.534) and every claim has a file or a command behind it (`SCRIPT.md`).
Plan, exit criteria and decisions: `PLAN-v2.md` (P172). v1 (2:06, Motion-as-Code style) is in git history (`b37b278d`, `59eace09`).

- `render/fabius-pitch-v2.mp4` - the video. `render/fabius-pitch-v2.en.srt` / `.en.vtt` - captions; `.id.srt` - Indonesian (USULAN).
- Captions are also burned in (the video works with the sound off).

## What is on screen

| Source | What | Where |
|---|---|---|
| live site captures | 60 fps clips recorded with virtual time (smooth regardless of capture speed), real cursor paths, element boxes per frame | `public/web/clips/*.mp4` + `.json`, `scripts/capture-flow.mjs`, `scripts/flows.mjs`, `public/web/README.md` |
| the site's 3D | hero crystal, desk floor, Live Book pipeline, ported to `@remotion/three` (deterministic, camera as data) | `src/three/` (README there), snapshot `src/three/data/desk-snapshot.json` |
| Motion.so | the reveal plate (cards dissolve -> crystal assembles -> headline) | `public/motion/reveal-motion-so.mp4` |
| motion graphics | cameras, worlds, cards lifted out of pages, kinetic type, devices, transitions | `src/cam/`, `src/fx/`, `src/ui/`, `src/scenes/S1Hook.tsx` ... `S10End.tsx`, `src/timeline.ts` |

## Layout

| Path | Role |
|---|---|
| `analysis/vo_v2.py` | the script + neural TTS read, line by line, word timings from the TTS -> `public/audio/voiceover.wav`, `public/data/vo.json` |
| `analysis/cues_v2.py` | music sections + SFX cue sheet anchored to voiceover words -> `public/data/cues.json` |
| `analysis/sfx_synth.py`, `music_v2.py`, `mix_v2.py`, `check_sfx.py` | clean SFX library (`public/audio/sfx2/`), original procedural music, the mix (-14 LUFS), the SFX guard |
| `analysis/captions_v2.py` | `.srt` / `.vtt` from the word timings |
| `src/lib/` | palette, fonts (Archivo with its width axis, Inter, JetBrains Mono - the site's), easing, voiceover timing lookups |
| `src/data/captures.ts` | capture metadata (cursor, boxes, marks) for the scenes |
| `src/timeline.ts` | which scene plays when (cuts sit in the pause before a scene's first line) and the transitions |

## Run

```sh
npm ci
npm run studio                                    # live preview
npx remotion still src/index.ts Fabius out/wip/f.png --frame=1800     # one frame (60 fps)
npx remotion render src/index.ts Fabius out/draft-v2.mp4 --scale=0.5 --concurrency=8   # draft
npm run render                                    # master -> out/fabius-pitch-v2.mp4
```

WebGL (the 3D) renders on the GPU through ANGLE (`remotion.config.ts`); without a GPU set `REMOTION_GL=swangle` (slow).

## Rebuild the sound

```sh
python -X utf8 analysis/vo_v2.py              # voiceover (cached per line in out/vo-cache); --samples renders other voices
python -X utf8 analysis/cues_v2.py            # cue sheet
python -X utf8 -P analysis/music_v2.py --png  # music bed + stems (out/audio)
python -X utf8 -P analysis/mix_v2.py --png    # public/audio/mix_v2.mp3 (+ loudness report)
python -X utf8 -P analysis/check_sfx.py       # guard: whitelist + hashes + no crash / broken sounds
python -X utf8 analysis/captions_v2.py
```

**Rule from the builder:** never a sound that gives the impression of a crash or something broken (impacts, debris, shattering,
glitch, static, zaps, tape-stops, reverse sucks ...). The old kit's SFX were removed from this workspace on 7-8 Oct and
`check_sfx.py` refuses any unlisted file or banned name.

## Re-capture the site

```sh
node scripts/capture-flow.mjs              # all flows (see scripts/flows.mjs); read-only, no login
```

## Credits

Remotion (free licence for individuals / companies up to 3 people). Fonts: Archivo, Inter, JetBrains Mono (SIL OFL, `public/fonts/OFL.txt`).
Voice: Microsoft neural TTS via `edge-tts` (USULAN, see PLAN-v2 LB20). Music + SFX: synthesized for this video; `whoosh` from
`@remotion/sfx` (CC0). Reveal plate: Motion.so (generated for this project). 3D: ports of the Fabius website's own scenes.
