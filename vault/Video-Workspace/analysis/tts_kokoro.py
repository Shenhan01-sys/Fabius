"""Scratch voiceover: Kokoro TTS (af_heart) line by line, placed on a timeline, then word-aligned.

This stands in for a recorded or ElevenLabs voiceover so the picture can be timed now. Each line of
script.py is synthesized on its own, so line starts and ends are exact; the words inside a line are
forced-aligned with pocketsphinx (offline, its English model ships inside the wheel). The pauses between
lines are written here (GAP_*), which is the one thing a TTS read lets us choose.

Writes ../public/audio/voiceover.wav (+ .mp3, the committed copy) and ../public/data/lyrics.json (the engine's format:
{ lines: [{ text, start, end, words: [{ w, start, end, syl? }] }] }).

    python -m uv run --no-project --with kokoro-onnx --with soundfile --with pocketsphinx --with numpy python analysis/tts_kokoro.py

The model files (~340 MB) are fetched once into analysis/models/ from the kokoro-onnx GitHub release.
To use your own recording instead, drop it at public/audio/voiceover.wav and run align_vo.py.
"""
import json, subprocess, sys, urllib.request
from pathlib import Path
import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import script as S  # noqa: E402
from align import align_line  # noqa: E402

MODELS = HERE / "models"
REL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
VOICE, SPEED = "af_heart", 0.94
SR = 24000

GAP_LINE = 0.32  # between two lines of the same plate
GAP_PLATE = 0.70  # at a plate cut (the picture needs the pause to turn)
LEAD, TAIL = 1.0, 3.4  # silence before the first line (the spark arrives) and after the last (end card)
GAP_AFTER = {  # extra breath after particular lines (display text prefix -> seconds, replaces the default)
    "His name was Fabius.": 0.95,
    "Even the decision to do nothing.": 0.85,
    "Because here’s what we don’t claim": 0.62,
    "So Fabius does what Fabius does best.": 0.95,
    "It waits.": 1.55,
}


def fetch(name):
    p = MODELS / name
    if not p.exists():
        MODELS.mkdir(exist_ok=True)
        print(f"downloading {name} …", file=sys.stderr)
        urllib.request.urlretrieve(REL + name, p)
    return p


def main():
    from kokoro_onnx import Kokoro
    k = Kokoro(str(fetch("kokoro-v1.0.onnx")), str(fetch("voices-v1.0.bin")))
    clips = []
    for plate, text in S.LINES:
        a, sr = k.create(S.say(text), voice=VOICE, speed=SPEED, lang="en-us")
        assert sr == SR
        clips.append(np.asarray(a, np.float32))
        print(f"{len(a) / SR:5.2f}s  {text}", file=sys.stderr)

    # place the lines
    t = LEAD
    starts = []
    for i, (plate, text) in enumerate(S.LINES):
        starts.append(t)
        t += len(clips[i]) / SR
        if i + 1 < len(S.LINES):
            gap = GAP_PLATE if S.LINES[i + 1][0] != plate else GAP_LINE
            for pre, g in GAP_AFTER.items():
                if text.startswith(pre):
                    gap = g
            t += gap
    total = t + TAIL
    vo = np.zeros(int(round(total * SR)) + 1, np.float32)
    for st, c in zip(starts, clips):
        i0 = int(round(st * SR))
        vo[i0:i0 + len(c)] += c
    pk = np.abs(vo).max()
    vo *= 10 ** (-1.0 / 20) / pk  # peak -1 dBFS
    out = ROOT / "public" / "audio" / "voiceover.wav"
    sf.write(out, vo, SR, subtype="PCM_16")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-c:a", "libmp3lame", "-b:a", "160k", str(out.with_suffix(".mp3"))], check=True)

    # word timings, one line at a time (exact line offsets, robust alignment)
    lines = []
    for (plate, text), st, c in zip(S.LINES, starts, clips):
        words = align_line(c, SR, text)
        for w in words:
            w["start"] = round(w["start"] + st, 3)
            w["end"] = round(w["end"] + st, 3)
            if "syl" in w:
                w["syl"] = [[round(a + st, 3), round(b + st, 3)] for a, b in w["syl"]]
        lines.append({"plate": plate, "text": text, "start": words[0]["start"], "end": words[-1]["end"], "words": words})
    data = {"source": f"tts_kokoro.py (Kokoro v1.0 {VOICE} x{SPEED}, pocketsphinx alignment)", "duration": round(total, 3), "lines": lines}
    (ROOT / "public" / "data" / "lyrics.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    for l in lines:
        print(f"{l['start']:6.2f}-{l['end']:6.2f}  " + " ".join(f"{w['w']}[{w['start']:.2f}]" for w in l["words"]))
    print(f"total {total:.2f}s -> {out.relative_to(ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    main()
