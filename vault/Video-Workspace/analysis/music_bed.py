"""A quiet synthesized music bed (no samples, no licence questions): a pad whose chord changes at each plate cut,
a low pulse under the AI desk, and a soft air layer, through a small Schroeder reverb. Written so the voice stays
on top: sfx_mix.py ducks it under the voice and normalises the whole mix.

    python -m uv run --no-project --with numpy --with scipy python analysis/music_bed.py     (writes out/bed.wav)
"""
import json, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SR = 48000
LY = json.loads((ROOT / "public" / "data" / "lyrics.json").read_text(encoding="utf-8"))
DUR = LY["duration"]
lines = LY["lines"]


def cut_before(plate):
    """The plate's first line start, less the kit's pre-roll (same rule as src/lib/lyrics.ts cut())."""
    i = next(k for k, l in enumerate(lines) if l["plate"] == plate)
    gap = lines[i]["start"] - lines[i - 1]["end"] if i else 1
    return lines[i]["start"] - min(0.18, max(0.04, gap * 0.45))


# chord per plate (MIDI notes): a calm D-minor world that brightens on the lavender plates and resolves at the end
CHORDS = {
    "hook": [38, 45, 50, 53, 57, 60],        # Dm9-ish, low
    "problem": [34, 41, 46, 50, 53, 57],     # Bbmaj7
    "idea": [41, 48, 53, 57, 60, 64],        # Fmaj7 (the hero, brighter)
    "lock": [36, 43, 48, 52, 55, 62],        # C add9
    "commit": [38, 45, 50, 53, 57, 64],      # Dm9
    "desk": [43, 50, 55, 58, 62, 65],        # Gm9
    "split": [43, 50, 55, 58, 62, 65],
    "open": [41, 48, 53, 57, 60, 67],        # F add9
    "bnb": [36, 43, 48, 52, 55, 62],         # C add9
    "honest": [34, 41, 46, 50, 53, 57],      # Bbmaj7
    "end": [38, 45, 50, 53, 57, 60],         # Dm9 (the wait) ...
}
FINAL = [41, 48, 53, 57, 60, 64, 69]          # ... resolving to Fmaj7 on the hero


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pad(notes, n, seed):
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    for k, m in enumerate(notes):
        f = hz(m)
        for det, pan in ((-0.0035, 0.25), (0.0035, 0.75)):
            ph = rng.uniform(0, 2 * np.pi)
            vib = 1 + 0.0012 * np.sin(2 * np.pi * (0.13 + 0.05 * k) * t + ph)
            x = np.sin(2 * np.pi * f * (1 + det) * vib * t + ph)
            x += 0.18 * np.sin(2 * np.pi * 2 * f * (1 + det) * t + ph * 1.7)  # a little body
            amp = (0.9 if m < 48 else 0.55) / len(notes)
            L += (amp * (1 - pan) * x).astype(np.float32)
            R += (amp * pan * x).astype(np.float32)
    return L, R


def lowpass(x, fc):
    """One-pole low-pass (scipy if present, else a plain loop)."""
    a = np.exp(-2 * np.pi * fc / SR)
    try:
        from scipy.signal import lfilter
        return lfilter([1 - a], [1, -a], x).astype(np.float32)
    except ImportError:
        y = np.empty_like(x)
        acc = 0.0
        for j, v in enumerate(x):
            acc = (1 - a) * v + a * acc
            y[j] = acc
        return y


def reverb(x, mix=0.32, seed=0, decay=0.9):
    """A soft hall: convolution with an exponentially decaying noise burst (2.6 s), 25 ms pre-delay."""
    from scipy.signal import fftconvolve
    rng = np.random.default_rng(100 + seed)
    n = int(2.6 * SR)
    tt = np.arange(n) / SR
    ir = rng.normal(0, 1, n) * np.exp(-tt / decay)
    ir = lowpass(ir.astype(np.float32), 5200)
    ir = np.concatenate([np.zeros(int(0.025 * SR), np.float32), ir])
    ir /= np.sqrt((ir ** 2).sum()) + 1e-9
    wet = fftconvolve(x, ir)[: len(x)].astype(np.float32)
    wet *= np.sqrt((x ** 2).mean() / ((wet ** 2).mean() + 1e-12))
    return (1 - mix) * x + mix * wet


def main():
    n = int(DUR * SR) + SR
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    plates = list(CHORDS.keys())
    starts = [0.0] + [cut_before(p) for p in plates[1:]]
    hero = next(l["start"] for l in lines if l["text"].startswith("Fabius. Refuse")) - 0.45
    segs = [(starts[i], starts[i + 1] if i + 1 < len(starts) else hero, CHORDS[p]) for i, p in enumerate(plates)] + [(hero, DUR + 1, FINAL)]
    xf = 1.4  # crossfade seconds
    for k, (a, b, notes) in enumerate(segs):
        i0 = max(0, int((a - xf / 2) * SR)); i1 = min(n, int((b + xf / 2) * SR))
        l, r = pad(notes, i1 - i0, k + 1)
        env = np.ones(i1 - i0, np.float32)
        f = int(xf * SR)
        env[:f] = np.linspace(0, 1, f) ** 1.5 if k else np.linspace(0, 1, f) ** 2
        env[-f:] = np.minimum(env[-f:], np.linspace(1, 0, f) ** 1.5)
        L[i0:i1] += l * env; R[i0:i1] += r * env
    # the desk's pulse: a soft low thump once a second (the cycle's clock), from 'Every five minutes' to 'are up.'
    d0 = next(l["start"] for l in lines if l["text"].startswith("Every five minutes"))
    d1 = next(l["end"] for l in lines if l["text"].startswith("And its root must"))
    tt = np.arange(int(0.35 * SR)) / SR
    thump = (np.sin(2 * np.pi * 55 * tt * (1 - 0.3 * tt)) * np.exp(-tt * 11)).astype(np.float32) * 0.35
    for s in np.arange(d0, d1, 1.0):
        i = int(s * SR); m = min(len(thump), n - i)
        L[i:i + m] += thump[:m]; R[i:i + m] += thump[:m]
    # air: filtered noise, very low
    rng = np.random.default_rng(3)
    air = rng.normal(0, 1, n).astype(np.float32)
    air = (air - lowpass(air, 2000)) * 0.004
    L += air; R += np.roll(air, 977)
    L = lowpass(L, 3800); R = lowpass(R, 3800)
    L = reverb(L, seed=1); R = reverb(R, seed=2)
    # fades
    fi, fo = int(1.2 * SR), int(3.0 * SR)
    for ch in (L, R):
        ch[:fi] *= np.linspace(0, 1, fi)
        ch[-fo:] *= np.linspace(1, 0, fo)
    st = np.stack([L, R], 1)
    st *= 0.5 / (np.abs(st).max() + 1e-9)
    (ROOT / "out").mkdir(exist_ok=True)
    with wave.open(str(ROOT / "out" / "bed.wav"), "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((np.clip(st, -1, 1) * 32767).astype("<i2").tobytes())
    print(f"bed {DUR:.1f}s, {len(segs)} chords, desk pulse {d0:.1f}-{d1:.1f}s -> out/bed.wav")


if __name__ == "__main__":
    main()
