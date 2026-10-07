# Fabius pitch video — Motion as Code, rendered with Remotion

A 2-minute pitch (1920×1080, 30 fps) for Fabius. Every frame is a pure function of the frame number, written in
React and rendered by [Remotion](https://www.remotion.dev). Animations are timed by the voiceover's word timings,
so a new read re-times the whole video.

The workflow and the visual grammar follow the Motion-as-Code kit in `../Reference-VideoPitchs/`
(`Motion-as-Code-Workflow-Guide.pdf`, `Motion_as_kit/`): voiceover → word alignment → plates (scenes found by
content, `lineOf` / `wordOf` / `cut`) → preview → render → sound. The kit's engine is three.js; this project ports
its ideas to Remotion (plotter pen, graph paper, karaoke words, crop-mark HUD, grain) and keeps its fonts (Archivo,
Cormorant Garamond, IBM Plex Mono, Hershey single-stroke) and its 33 sound effects. Colours are the Fabius web
palette (`web/src/app/globals.css`, `docs/design/landing.md`): lavender, night indigo, one violet accent, red only
for a gap.

- `render/fabius-pitch.mp4` — the video. `render/fabius-pitch.en.srt` / `.vtt` — captions.
- `SCRIPT.md` — the voiceover line by line, with the file or command behind every claim.

## Layout

| Path | Role |
|---|---|
| `analysis/script.py` | the script: one line per entry, with its plate, plus spoken forms (x402, ERC-8004, 97 …) |
| `analysis/tts_kokoro.py` | scratch voiceover: Kokoro TTS (`af_heart`), line by line, word-aligned |
| `analysis/align_vo.py` | your own voiceover → `public/data/lyrics.json` (pocketsphinx forced alignment, offline) |
| `analysis/audio_vo.py` | voice envelope → `public/data/audio.json` |
| `analysis/music_bed.py` | a quiet synthesized pad (chord per plate) → `out/bed.wav` |
| `analysis/sfx_mix.py` | cue sheet (≈300 cues on the same word times) + ducking + −14 LUFS → `public/audio/mix.mp3` |
| `analysis/captions.py` | `.srt` / `.vtt` from the word timings |
| `src/timeline.ts` | which plate plays when; cuts in the pause before a line; transitions (zoom, whip, iris, push, flash) |
| `src/plates/*.tsx` | the eleven plates (Hook … End) |
| `src/components/` | kit (karaoke, pen, graph paper, spark), camera (3D moves, parallax, ambient), solid (a real 3D stage in CSS: boxes, thick glass tablets, the web's glass blocks as true cubes, padlocks), devices (browser, phone, Telegram), glass, HUD, transitions |
| `public/ui/` | captures of the real web app and Telegram signal image (see below) |
| `scripts/stills.mjs` | render stills at given seconds, with a contact sheet |
| `scripts/capture-web.mjs`, `scripts/capture-sections.mjs` | capture `web/` pages (desktop + mobile) and the home page's sections |

## Run

```sh
npm install
npm run studio                      # live preview with the soundtrack
node scripts/stills.mjs --t 12.5,40.2 --sheet          # stills while editing (out/wip)
npm run render                      # out/fabius-pitch.mp4 (h264, CRF 18)
```

`render/fabius-pitch.mp4` (≈47 MB) is a two-pass H.264 copy of the master for the web and chat apps:

```sh
VF="scale=in_range=full:out_range=tv,format=yuv420p"
ffmpeg -i out/fabius-pitch.mp4 -vf "$VF" -c:v libx264 -preset slow -b:v 2800k -pass 1 -an -f null /dev/null
ffmpeg -i out/fabius-pitch.mp4 -vf "$VF" -c:v libx264 -preset slow -b:v 2800k -pass 2 -c:a aac -b:a 192k -movflags +faststart render/fabius-pitch.mp4
```

Remotion downloads its own headless Chrome on first render. Without network access to it, point it at any
Chromium: `REMOTION_BROWSER_EXECUTABLE=/path/to/chrome npm run render`.

## Swap the voiceover

1. Record (or generate with ElevenLabs) the lines of `analysis/script.py`, keeping the words.
2. Save it as `public/audio/voiceover.wav` (or `.mp3`).
3. Re-time everything and rebuild the sound:

```sh
python -m uv run --no-project --with pocketsphinx --with numpy python analysis/align_vo.py
python -m uv run --no-project --with numpy python analysis/audio_vo.py
python -m uv run --no-project --with numpy --with scipy python analysis/music_bed.py
python -m uv run --no-project --with numpy python analysis/sfx_mix.py
python analysis/captions.py
```

The scratch read in this folder is Kokoro TTS (Apache-2.0): `python -m uv run --no-project --with kokoro-onnx
--with soundfile --with pocketsphinx --with numpy python analysis/tts_kokoro.py` (fetches the model, ~340 MB).

## Product captures

```sh
cd ../../web && npm run build && npx next start -p 3100
# optional, for pages that read the Railway gate: the real gate, run offline on the repo
python tools/x402_sinyal.py --local      # :8050 (needs eth-abi, eth-account; see railway/requirements.txt)
node scripts/capture-web.mjs --gate http://127.0.0.1:8050
node scripts/capture-sections.mjs
```

The Telegram chat is drawn from the bot's real reply templates (`tools/x402_sinyal.py`) and its real signal image
(`tools/sinyal_gambar.py`).

## Credits

Visual language: the Motion-as-Code kit, built on pdoom-video by mexicat (MIT, `LICENSE.pdoom-engine`). Fonts:
SIL Open Font License (`public/fonts/OFL.txt`); Hershey fonts per their notice in the SVG files. Sound effects:
ElevenLabs Sound Effects (from the kit). Scratch voice: Kokoro-82M (Apache-2.0).
