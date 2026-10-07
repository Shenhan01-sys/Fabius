"""../public/data/audio.json: the voice's loudness envelope (100 fps, 0..1) and the word onsets, for plates
that breathe with the read (spark glow, karaoke pop). Port of the kit's analysis/audio_vo.py.

    python -m uv run --no-project --with numpy python analysis/audio_vo.py
"""
import json, subprocess
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SR, FPS = 16000, 100
VOP = ROOT / "public" / "audio" / "voiceover.wav"
VOP = VOP if VOP.exists() else VOP.with_suffix(".mp3")
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(VOP), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                     capture_output=True, check=True).stdout
y = np.frombuffer(raw, dtype=np.float32)
dur = len(y) / SR
hop = SR // FPS
n = int(np.ceil(dur * FPS))
win = np.hanning(2 * hop)
pad = np.concatenate([np.zeros(hop), y, np.zeros(3 * hop)])
spec = np.abs(np.fft.rfft(np.stack([pad[i * hop: i * hop + 2 * hop] * win for i in range(n)]), axis=1))


def norm(x):
    x = np.convolve(x, np.ones(3) / 3, mode="same")
    return np.clip(x / (np.percentile(x, 99.5) + 1e-9), 0, 1)


rms = norm(np.sqrt((spec ** 2).mean(1)))
lyr = json.loads((ROOT / "public" / "data" / "lyrics.json").read_text(encoding="utf-8"))
words = [w for l in lyr["lines"] for w in l["words"] if w["end"] > w["start"]]
out = {
    "duration": round(dur, 3), "fps": FPS,
    "rms": rms.round(3).tolist(),
    "onsets": [[round(w["start"], 3), round(float(rms[min(n - 1, int(w["start"] * FPS) + 3)]), 3)] for w in words],
}
(ROOT / "public" / "data" / "audio.json").write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
print(f"duration {dur:.2f}s, {n} frames, {len(words)} word onsets")
