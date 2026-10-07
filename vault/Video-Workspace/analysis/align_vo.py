"""Word timings for YOUR voiceover (a recording or an ElevenLabs read of analysis/script.py).

Put the file at public/audio/voiceover.wav (or .mp3), keep the words of script.py, and run:

    python -m uv run --no-project --with pocketsphinx --with numpy python analysis/align_vo.py [--tail 3.4]

The whole read is force-aligned against the script with pocketsphinx (offline; nothing to download), then cut
back into the script's lines and words. Writes public/data/lyrics.json; every plate re-times itself because it
finds its moments by content. Then rebuild the sound: audio_vo.py, music_bed.py, sfx_mix.py.
"""
import argparse, json, subprocess, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import script as S  # noqa: E402
from align import SR16, decoder, segments, tighten, to_display, voiced_mask  # noqa: E402


def find_vo():
    for name in ("voiceover.wav", "voiceover.mp3", "voiceover.m4a"):
        p = ROOT / "public" / "audio" / name
        if p.exists():
            return p
    sys.exit("no public/audio/voiceover.(wav|mp3|m4a)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tail", type=float, default=3.4, help="seconds of video after the read ends (the end card)")
    a = ap.parse_args()
    vo = find_vo()
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(vo), "-ac", "1", "-ar", str(SR16), "-f", "s16le", "-"], capture_output=True, check=True).stdout
    dur = len(pcm) / 2 / SR16
    words = [w for _, text in S.LINES for tok in text.split(" ") for w in S.spoken(tok)]
    segs = tighten(segments(pcm, words, decoder()), voiced_mask(pcm))
    lines, k = [], 0
    for plate, text in S.LINES:
        n = sum(len(S.spoken(tok)) for tok in text.split(" "))
        ws = to_display(text, segs[k:k + n])
        k += n
        lines.append({"plate": plate, "text": text, "start": ws[0]["start"], "end": ws[-1]["end"], "words": ws})
    total = max(dur, lines[-1]["end"] + a.tail)
    out = {"source": f"align_vo.py (pocketsphinx) on {vo.name}", "duration": round(total, 3), "lines": lines}
    (ROOT / "public" / "data" / "lyrics.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for l in lines:
        print(f"{l['start']:6.2f}-{l['end']:6.2f}  {l['text']}")
    print(f"audio {dur:.2f}s, video {total:.2f}s -> public/data/lyrics.json")


if __name__ == "__main__":
    main()
