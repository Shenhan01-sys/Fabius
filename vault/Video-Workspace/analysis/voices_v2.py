"""Sound generators shared by sfx_synth.py (one-shot effects) and music_v2.py (the music bed's fx + bells).

Everything is synthesised from oscillators and filtered noise (dsp_v2), deterministic for a given seed, so the
library and the bed are fully owned and reproducible. Nothing here makes a transient louder than its body:
attacks are raised-cosine ramps (>= 0.25 ms), so there are no clicks, cracks or impacts by construction.
"""
from __future__ import annotations

import numpy as np

from dsp_v2 import (SR, adsr, automation, biquad, butter, chorus, exp_curve, fade, noise, osc_saw, osc_sine,
                    pan_mono, raised_cos, svf, undb)

# D major pentatonic (D E F# A B) in Hz, octaves 5..7
PENTA = {
    "D5": 587.33, "E5": 659.26, "F#5": 739.99, "A5": 880.00, "B5": 987.77,
    "D6": 1174.66, "E6": 1318.51, "F#6": 1479.98, "A6": 1760.00, "B6": 1975.53,
    "D7": 2349.32, "E7": 2637.02, "F#7": 2959.96, "A7": 3520.00,
}

# glass / bell partials: (frequency ratio, relative amplitude, relative decay). Mostly harmonic (musical, warm),
# with two slightly inharmonic upper modes for the glassy sparkle; the upper modes die quickly.
GLASS = ((1.0, 1.0, 1.0), (2.0, 0.40, 0.55), (3.01, 0.15, 0.32), (4.18, 0.08, 0.17), (5.43, 0.04, 0.09),
         (6.79, 0.02, 0.05))


def ramp_in(n, attack_s):
    """Raised-cosine onset multiplier of length n (1.0 after attack_s)."""
    env = np.ones(int(n))
    a = max(1, int(attack_s * SR))
    a = min(a, len(env))
    env[:a] = raised_cos(a)
    return env


def glass_note(f0, dur=2.5, vel=1.0, tau=1.2, bright=1.0, attack=0.0025, beat_hz=0.6, seed=0,
               partials=GLASS):
    """A clean glass/bell tone: additive partials with individual exponential decays, a slow beating twin of the
    fundamental (alive, not static) and a raised-cosine attack (no click). Returns mono, peak ~ vel."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    y = np.zeros(n)
    for k, (r, a, d) in enumerate(partials):
        f = f0 * r
        if f > 0.42 * SR:
            continue
        amp = a * (bright ** k)
        env = np.exp(-t / (tau * d))
        y += amp * env * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi))
        if k == 0 and beat_hz:
            y += 0.3 * amp * env * np.sin(2 * np.pi * (f + beat_hz) * t + rng.uniform(0, 2 * np.pi))
    # partials whose attack is shorter for the upper modes would add a 'tink'; keep one gentle ramp for all
    y *= ramp_in(n, attack)
    y = fade(y, 0.0, min(0.25, dur * 0.2))
    return vel * y / (np.abs(y).max() + 1e-12)


def unison_saw(f0, n, voices=5, spread_cents=12.0, seed=0, drift_cents=1.5, width=0.75):
    """Detuned PolyBLEP saw stack, voices spread across the stereo field. Returns stereo (2, n), ~unit RMS."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(n)) / SR
    out = np.zeros((2, int(n)))
    for v in range(voices):
        pos = (v / (voices - 1) - 0.5) * 2.0 if voices > 1 else 0.0
        det = spread_cents * pos + rng.normal(0.0, 1.2)
        drift = drift_cents * np.sin(2 * np.pi * rng.uniform(0.05, 0.17) * t + rng.uniform(0, 2 * np.pi))
        f = f0 * 2.0 ** ((det + drift) / 1200.0)
        out += pan_mono(osc_saw(f, n, phase0=rng.uniform()), pos * width)
    return out / np.sqrt(voices) / 0.577


def pad_note(f0, dur, attack=0.4, decay=1.0, sustain=0.75, release=1.2, voices=5, spread=12.0, seed=0,
             sine_mix=0.45):
    """Warm pad note: unison saws + a sine layer for body, ADSR'd. Returns stereo (2, n), n = dur + release."""
    n = int((dur + release) * SR)
    x = unison_saw(f0, n, voices, spread, seed)
    x += sine_mix * np.stack([osc_sine(f0, n, phase0=0.0)] * 2)
    env = adsr(n, attack, decay, sustain, release, gate=dur)
    return x * env


def air(n, lo=3000.0, hi=12000.0, seed=0, color="pink"):
    """Band-limited breathy noise (unit-ish RMS)."""
    x = noise(n, color, seed)
    x = butter(x, "bandpass", [lo, min(hi, 0.45 * SR)], 2)
    return x / (np.sqrt(np.mean(x * x)) + 1e-12)


def riser(dur=2.0, seed=0, f_start=260.0, f_end=7000.0, tone_root=146.83, tone_mix=0.32, semis=12.0):
    """Filtered-noise + tonal riser. Low-pass opens exponentially (late), resonance grows, a three-voice saw
    chord (root, fifth, octave) glides up `semis`; loudness climbs ~30 dB, peaks at 96 % and is shaped to 0 at the
    end (clean, no tail). Returns stereo; its sync point is the end."""
    n = int(dur * SR)
    u = np.arange(n) / n
    cut = f_start * (f_end / f_start) ** (u ** 1.7)
    q = 0.9 + 1.6 * u ** 2
    hp = 50.0 * (700.0 / 50.0) ** (u ** 1.5)
    st = np.zeros((2, n))
    for ch in range(2):
        src = 0.65 * noise(n, "pink", seed + 11 * ch) + 0.35 * noise(n, "white", seed + 11 * ch + 5)
        y = svf(src, cut, q, "lp")
        y = svf(y, hp, 0.7, "hp")
        st[ch] = y
    # mid/side: narrow at the start, wide at the end
    mid, side = 0.5 * (st[0] + st[1]), 0.5 * (st[0] - st[1])
    side *= 0.25 + 0.75 * u
    st = np.stack([mid + side, mid - side])
    # tonal chord gliding up
    glide = 2.0 ** (semis / 12.0 * u ** 1.4)
    tone = np.zeros(n)
    rng = np.random.default_rng(seed)
    for r, a in ((1.0, 1.0), (1.5, 0.7), (2.0, 0.55)):
        for det in (-7.0, 7.0):
            tone += a * osc_saw(tone_root * r * glide * 2 ** (det / 1200), n, phase0=rng.uniform())
    tone = svf(tone, np.minimum(cut * 0.8, 6000.0), 0.8, "lp")
    tone /= np.abs(tone).max() + 1e-12
    st /= np.abs(st).max() + 1e-12
    mix = st + tone_mix * np.stack([tone, tone])
    lvl = undb(-30.0 * (1.0 - u) ** 1.3)
    peak_at = 0.96
    tail = np.clip((u - peak_at) / (1.0 - peak_at), 0.0, 1.0)
    lvl *= np.cos(0.5 * np.pi * tail) ** 2
    return fade(mix * lvl, 0.004, 0.003)


def downlifter(dur=2.4, seed=0, f_start=8500.0, f_end=260.0, tone_freqs=(440.0, 587.33), semis=-7.0, tone_mix=0.18,
               decay=1.2):
    """Bright air that falls away: low-pass sweeps down, a quiet two-note tone glides down a fifth (gentle, never
    to zero, so it reads as 'settling', not a tape-stop). Soft 25 ms onset; sync point is the start."""
    n = int(dur * SR)
    u = np.arange(n) / n
    cut = f_start * (f_end / f_start) ** (u ** 0.65)
    st = np.zeros((2, n))
    for ch in range(2):
        src = 0.6 * noise(n, "pink", seed + 7 * ch) + 0.4 * noise(n, "white", seed + 7 * ch + 3)
        st[ch] = svf(src, cut, 1.0, "lp")
    mid, side = 0.5 * (st[0] + st[1]), 0.5 * (st[0] - st[1])
    side *= 1.0 - 0.8 * u
    st = np.stack([mid + side, mid - side])
    st /= np.abs(st).max() + 1e-12
    glide = 2.0 ** (semis / 12.0 * u ** 0.8)
    tone = sum(osc_sine(f * glide, n) for f in tone_freqs)
    tone /= np.abs(tone).max() + 1e-12
    env = (1.0 - u) ** 1.6 * np.exp(-decay * u)
    y = (st + tone_mix * np.stack([tone, tone])) * env
    return fade(y, 0.025, 0.05)


def sub_swell(dur=3.0, peak=1.3, f0=73.42, release_tau=0.55):
    """Gentle low swell: sine + 2nd/3rd harmonic (audible on small speakers), raised-cosine rise to `peak`
    seconds, exponential release. No punch: the rise takes > 1 s. Mono; sync point = peak."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    rise = np.clip(t / peak, 0.0, 1.0)
    env = np.where(t < peak, 0.5 - 0.5 * np.cos(np.pi * rise), np.exp(-(t - peak) / release_tau))
    y = osc_sine(f0, n) + 0.32 * osc_sine(2 * f0, n) + 0.08 * osc_sine(3 * f0, n)
    y = np.tanh(1.2 * y * env) / 1.2
    y = biquad(y, "lowpass", 600.0, 0.7)
    return fade(y, 0.01, 0.2)


def bloom_pad(notes_hz, dur=5.0, attack=0.35, hold=2.0, release=2.4, cut_points=None, seed=0, voices=5):
    """Pad chord that blooms: unison saw stack per note through a low-pass that opens then settles.
    Returns stereo (2, n)."""
    n = int(dur * SR)
    x = np.zeros((2, n))
    for k, f in enumerate(notes_hz):
        v = pad_note(f, hold, attack, 1.2, 0.7, release, voices, 10.0, seed + 31 * k)
        m = min(n, v.shape[1])
        x[:, :m] += v[:, :m] * (0.8 if f < 200 else 1.0)
    cut_points = cut_points or [(0.0, 320.0), (0.9, 3200.0), (2.5, 2200.0), (dur, 900.0)]
    cut = automation(cut_points, n)
    x = svf(x, cut, 0.85, "lp")
    x = biquad(x, "highpass", 90.0, 0.7)
    return x / (np.abs(x).max() + 1e-12)


def grain_cloud(dur=1.0, count=40, seed=0, freqs=None, peak_frac=0.35, tau=(0.05, 0.14), pan_spread=0.8):
    """Sparkle: short glass grains (pentatonic, octave 6-7), density rising to peak_frac then thinning.
    Returns stereo (2, n) with room for the grains' ring (n = dur + 0.4 s)."""
    rng = np.random.default_rng(seed)
    freqs = freqs or [PENTA[k] for k in ("D6", "E6", "F#6", "A6", "B6", "D7", "E7", "F#7", "A7")]
    w = np.array([1.0 / (1 + i * 0.35) for i in range(len(freqs))])
    w /= w.sum()
    n = int((dur + 0.5) * SR)
    out = np.zeros((2, n))
    # grain times from the density envelope (inverse-CDF sampling of a smooth bump)
    grid = np.linspace(0, 1, 512)
    dens = np.where(grid < peak_frac, np.sin(0.5 * np.pi * grid / peak_frac) ** 2,
                    np.cos(0.5 * np.pi * (grid - peak_frac) / (1 - peak_frac)) ** 1.5) + 1e-3
    cdf = np.cumsum(dens)
    cdf /= cdf[-1]
    times = np.sort(np.interp(rng.uniform(0, 1, count), cdf, grid)) * dur
    for i, t0 in enumerate(times):
        f = rng.choice(freqs, p=w) * 2 ** (rng.normal(0, 3) / 1200)
        g = glass_note(f, dur=0.45, vel=rng.uniform(0.35, 1.0) * (1.0 if f < 2000 else 0.7),
                       tau=rng.uniform(*tau) * 3.0, bright=0.5, attack=rng.uniform(0.002, 0.005),
                       beat_hz=0.0, seed=seed * 1000 + i)
        st = pan_mono(g, rng.uniform(-pan_spread, pan_spread))
        i0 = int(t0 * SR)
        m = min(st.shape[1], n - i0)
        out[:, i0:i0 + m] += st[:, :m]
    return fade(out, 0.0, 0.08)
