"""Synthesise the clean SFX library for the v2 pitch video -> public/audio/sfx2/ (48 kHz, 24-bit WAV).

    python -X utf8 analysis/sfx_synth.py             # every sound + manifest.json + README.md
    python -X utf8 analysis/sfx_synth.py --sheet     # + out/audio/sfx2_sheet.png (spectrogram contact sheet)
    python -X utf8 analysis/sfx_synth.py --only glass_seal,success

Client rule (7 Oct): never a sound that gives an impression of a crash or something broken - no impacts, slams,
debris, falling pieces, shattering glass, glitches, static, crackle, sizzle, zaps, distortion, tape-stops, rewinds,
reverse sucks, scratches, snips, stamps. Everything here is built from sine partials, band-limited (PolyBLEP) saws
and filtered noise; every attack is a raised-cosine ramp, every file starts and ends on exactly 0, peaks are
normalised to -1.5 dBFS with the true peak kept <= -1 dBTP. Deterministic (fixed seeds): re-running gives the same
bytes, so analysis/check_sfx.py can pin each file's SHA-256.

manifest.json records, per sound, its sync point ('anchor', seconds from the file start): the moment that should
land on the picture event (a whoosh's peak, a riser's end, a chime's onset, the seal's chime). mix_v2.py places a
cue so that anchor == cue time.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402

from dsp_v2 import (ROOT, SR, as_stereo, biquad, block_loudness, butter, fade, integrated_lufs, make_ir,  # noqa: E402
                    noise, osc_saw, osc_sine, pan_mono, reverb, svf, todb, true_peak_db, undb, write_wav)
from voices_v2 import (PENTA, air, bloom_pad, downlifter, glass_note, grain_cloud, ramp_in, riser,  # noqa: E402
                       sub_swell)

OUT = ROOT / "public" / "audio" / "sfx2"
PEAK_DBFS = -1.5
TP_MAX = -1.0

# shared spaces (synthetic impulse responses)
ROOM = make_ir(rt60=0.32, predelay=0.004, er_count=12, er_span=0.03, hf_ratio=0.5, seed=7)
HALL = make_ir(rt60=1.9, predelay=0.016, hf_ratio=0.35, damp_hz=4200, seed=8)
BIG = make_ir(rt60=2.8, predelay=0.024, hf_ratio=0.3, damp_hz=3800, seed=9)

SOUNDS: dict[str, dict] = {}


def sound(name, use, how, target_lufs):
    """Register a generator. target_lufs = momentary-max loudness the cue should reach in a mix whose voice sits
    at -16 LUFS integrated (before the master gain); the manifest turns it into a suggested cue gain."""
    def deco(fn):
        SOUNDS[name] = dict(fn=fn, use=use, how=how, target=target_lufs)
        return fn
    return deco


def rms(x):
    return float(np.sqrt(np.mean(np.asarray(x) ** 2)) + 1e-12)


def verb(x, ir, wet, tail_s):
    """Pad with room for the tail, then dry + wet convolution (stereo out)."""
    x = as_stereo(x)
    # the dry buffer must already be at rest when it ends, or its truncation becomes a click inside the reverb
    x = fade(x, 0.0, float(np.clip(0.08 * x.shape[1] / SR, 0.004, 0.12)))
    x = np.pad(x, ((0, 0), (0, int(tail_s * SR))))
    return reverb(x, ir, wet=wet, dry=1.0)


def place(dst, x, t):
    i0 = int(round(t * SR))
    m = min(x.shape[-1], dst.shape[-1] - i0)
    if m > 0:
        dst[..., i0:i0 + m] += x[..., :m]
    return dst


def decay_tone(f, tau, n, attack=0.0004, phase=0.0):
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t + phase) * np.exp(-t / tau) * ramp_in(n, attack)


def decay_noise(center, q, tau, n, seed, attack=0.0003):
    t = np.arange(n) / SR
    x = biquad(noise(n, "white", seed), "bandpass", center, q)
    return x / rms(x) * np.exp(-t / tau) * ramp_in(n, attack)


# =========================================================================================== whooshes
def whoosh(dur, peak, f_lo, f_hi, f_end, q, air_amt, tone_amt, pan_a, pan_b, seed, sub=0.0):
    """Filtered-noise air with a Doppler-like filter arc (rises into the peak, falls away after it), a faint
    resonant 'pitch' band riding the same arc, decorrelated L/R air on top, eased pan."""
    n = int(dur * SR)
    u = np.arange(n) / n
    rise = np.clip(u / peak, 0, 1)
    fall = np.clip((u - peak) / (1 - peak), 0, 1)
    amp = np.where(u < peak, np.sin(0.5 * np.pi * rise) ** 2.2, np.cos(0.5 * np.pi * fall) ** 1.7)
    fc = np.where(u < peak, f_lo * (f_hi / f_lo) ** (rise ** 1.3), f_hi * (f_end / f_hi) ** (fall ** 0.8))
    body = svf(0.7 * noise(n, "pink", seed) + 0.3 * noise(n, "white", seed + 1), fc, q, "bp")
    body /= rms(body)
    tone = svf(noise(n, "white", seed + 4), fc * 0.98, 9.0, "bp")
    tone /= rms(tone)
    pan = pan_a + (pan_b - pan_a) * (0.5 - 0.5 * np.cos(np.pi * u))
    st = pan_mono((body + tone_amt * tone) * amp, pan)
    airs = []
    for s in (seed + 2, seed + 3):
        a = svf(noise(n, "white", s), np.minimum(fc * 2.6, 9000.0), 0.9, "bp")
        airs.append(a / rms(a))
    st += air_amt * np.stack(airs) * amp ** 1.3
    if sub:
        st += sub * np.stack([osc_sine(46.0, n)] * 2) * amp ** 1.5
    st = biquad(st, "lowpass", 9500.0, 0.7)
    st = biquad(st, "highpass", 60.0 if sub else 90.0, 0.7)
    return st, peak * dur


@sound("whoosh_soft_a", "quick card / panel slide, short camera nudge (peak at 0.32 s)",
       "pink+white noise through a TPT band-pass arcing 380->1900->700 Hz (Q 1.4), faint resonant pitch band, "
       "decorrelated air, pan L->R", -24)
def s_whoosh_soft_a():
    return whoosh(0.55, 0.58, 380, 1900, 700, 1.4, 0.30, 0.10, -0.35, 0.35, seed=101)


@sound("whoosh_soft_b", "page-to-page move, UI card lifting out of the page (peak at 0.44 s)",
       "as whoosh_soft_a, slower and darker: band-pass 300->1500->520 Hz (Q 1.2), pan R->L", -24)
def s_whoosh_soft_b():
    return whoosh(0.8, 0.55, 300, 1500, 520, 1.2, 0.28, 0.09, 0.4, -0.4, seed=202)


@sound("whoosh_soft_c", "bigger camera move / scene transition (peak at 0.69 s)",
       "as whoosh_soft_a, longest of the three: band-pass 240->1250->420 Hz (Q 1.0), wide pan", -24)
def s_whoosh_soft_c():
    return whoosh(1.15, 0.6, 240, 1250, 420, 1.0, 0.26, 0.08, -0.55, 0.55, seed=303)


@sound("whoosh_long", "2 s camera fly-through (corridor, into the 3D scene); peak at 1.2 s",
       "two noise layers (low body 150->700->260 Hz and high air 1.2->4.2->1.6 kHz), a quiet 46 Hz pressure "
       "swell, full L->R eased pan", -23)
def s_whoosh_long():
    low, pk = whoosh(2.1, 0.58, 150, 700, 260, 0.9, 0.0, 0.07, -0.85, 0.85, seed=404, sub=0.10)
    high, _ = whoosh(2.1, 0.6, 1200, 4200, 1600, 1.2, 0.20, 0.0, -0.7, 0.7, seed=405)
    return low + 0.45 * high, pk


@sound("swipe_up", "upward swipe / card flicked up / panel rising (peak at 0.30 s)",
       "noise band-pass rising 650 Hz -> 5.2 kHz (Q 1.6) with a quiet sine glide 520 -> 1560 Hz under it", -25)
def s_swipe_up():
    dur, peak = 0.42, 0.72
    n = int(dur * SR)
    u = np.arange(n) / n
    rise = np.clip(u / peak, 0, 1)
    fall = np.clip((u - peak) / (1 - peak), 0, 1)
    amp = np.where(u < peak, np.sin(0.5 * np.pi * rise) ** 2, np.cos(0.5 * np.pi * fall) ** 1.5)
    fc = 650.0 * (5200.0 / 650.0) ** (u ** 1.1)
    body = svf(0.6 * noise(n, "pink", 51) + 0.4 * noise(n, "white", 52), fc, 1.6, "bp")
    body /= rms(body)
    glide = osc_sine(520.0 * 3.0 ** (u ** 1.2), n)
    y = (body + 0.22 * glide) * amp
    y = biquad(biquad(y, "lowpass", 9000.0, 0.7), "highpass", 150.0, 0.7)
    return y, peak * dur


# =========================================================================================== UI
@sound("ui_click_a", "cursor click on a button / link (crisp, soft)",
       "damped sines 1.75 kHz + 620 Hz with a 0.3 ms raised-cosine onset + a 2 ms band-passed noise tick at "
       "3.2 kHz, low-passed 8 kHz, touch of small room", -27)
def s_ui_click_a():
    n = int(0.09 * SR)
    y = 0.8 * decay_tone(1750.0, 0.006, n) + 0.6 * decay_tone(620.0, 0.010, n) \
        + 0.35 * decay_noise(3200.0, 1.2, 0.0022, n, 61)
    y = biquad(y, "lowpass", 8000.0, 0.7)
    return verb(y, ROOM, 0.10, 0.15), 0.0004


@sound("ui_click_b", "rounder click: toggle, select a bot / date, confirm a choice",
       "damped sines 1.15 kHz + 380 Hz + 2.4 kHz noise tick, low-passed 6.5 kHz, small room", -27)
def s_ui_click_b():
    n = int(0.1 * SR)
    y = 0.7 * decay_tone(1150.0, 0.007, n) + 0.7 * decay_tone(380.0, 0.014, n) \
        + 0.3 * decay_noise(2400.0, 1.0, 0.0025, n, 62)
    y = biquad(y, "lowpass", 6500.0, 0.7)
    return verb(y, ROOM, 0.10, 0.15), 0.0004


@sound("ui_tick", "tiny tick: counter step, list item, cursor hover tick, timestamp digit",
       "damped sine 2.35 kHz (D7) + quiet octave + 1 ms noise tick at 5.2 kHz, 0.3 ms onset", -30)
def s_ui_tick():
    n = int(0.05 * SR)
    y = 0.8 * decay_tone(2349.32, 0.0035, n, 0.0003) + 0.15 * decay_tone(4698.6, 0.0018, n, 0.0003) \
        + 0.12 * decay_noise(5200.0, 2.0, 0.0012, n, 63)
    y = biquad(y, "lowpass", 10000.0, 0.7)
    return verb(y, ROOM, 0.06, 0.1), 0.0003


@sound("ui_hover", "tiny airy blip: hover over a card, a pill lighting up",
       "sine gliding E6 -> F#6 over 50 ms with 6 ms onset + breathy band-passed noise, small room", -29)
def s_ui_hover():
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    f = PENTA["E6"] + (PENTA["F#6"] - PENTA["E6"]) * (1 - np.exp(-t / 0.018))
    env = ramp_in(n, 0.006) * np.exp(-t / 0.035)
    y = 0.7 * osc_sine(f, n) * env
    br = biquad(noise(n, "white", 64), "bandpass", 3600.0, 1.5)
    y += 0.12 * br / rms(br) * ramp_in(n, 0.004) * np.exp(-t / 0.03)
    return verb(y, ROOM, 0.18, 0.2), 0.006


@sound("ui_pop", "soft bubble: an agent raises its cube, a chip/badge appears, a dot lands",
       "sine with a fast upward pitch glide 280 -> 920 Hz (bubble resonance), 2 ms onset, 28 ms decay, "
       "quiet 2nd harmonic, low-passed 3.5 kHz", -27)
def s_ui_pop():
    n = int(0.14 * SR)
    t = np.arange(n) / SR
    f = 280.0 + 640.0 * (1 - np.exp(-t / 0.010))
    env = ramp_in(n, 0.002) * np.exp(-t / 0.028)
    y = (osc_sine(f, n) + 0.12 * osc_sine(2 * f, n)) * env
    y = biquad(y, "lowpass", 3500.0, 0.7)
    return verb(y, ROOM, 0.12, 0.15), 0.002


def keypress(seed, f_th, f_cl, f_r, rel_t, lvl=1.0):
    n = int(0.17 * SR)
    y = 0.55 * decay_tone(f_th, 0.012, n, 0.0008) + 0.5 * decay_noise(f_cl, 1.1, 0.004, n, seed) \
        + 0.25 * decay_tone(f_r, 0.005, n, 0.0004)
    bottom = 0.45 * decay_tone(f_th * 0.85, 0.008, n, 0.0008)
    y = place(y, bottom, 0.009)
    rel = 0.07 * decay_noise(f_cl * 1.15, 1.2, 0.003, int(0.03 * SR), seed + 1)  # release ~14 dB under the press
    y = place(y, rel, rel_t)
    y = biquad(biquad(y, "lowpass", 6500.0, 0.7), "highpass", 90.0, 0.7)
    return verb(lvl * y, ROOM, 0.08, 0.12), 0.0008


@sound("key_soft_a", "gentle keyboard typing (use a..d in rotation, 60-110 ms apart, +-1.5 dB)",
       "laptop-key model: low thump (damped sine ~210 Hz) + soft plastic tick (noise band-pass ~1.9 kHz, 4 ms) "
       "+ keycap ring, bottom-out 9 ms later, faint release tick ~80 ms later; low-passed 6.5 kHz", -31)
def s_key_a():
    return keypress(71, 210.0, 1900.0, 1150.0, 0.078)


@sound("key_soft_b", "typing, variant b", "as key_soft_a with thump 240 Hz, tick 2.3 kHz, release at 86 ms", -31)
def s_key_b():
    return keypress(72, 240.0, 2300.0, 1320.0, 0.086)


@sound("key_soft_c", "typing, variant c (slightly darker; good for the space bar / enter)",
       "as key_soft_a with thump 190 Hz, tick 1.7 kHz, release at 95 ms", -31)
def s_key_c():
    return keypress(73, 190.0, 1700.0, 990.0, 0.095)


@sound("key_soft_d", "typing, variant d", "as key_soft_a with thump 260 Hz, tick 2.1 kHz, release at 72 ms", -31)
def s_key_d():
    return keypress(74, 260.0, 2100.0, 1240.0, 0.072)


# =========================================================================================== glass + tones
def chime(f0, seed, tau=1.25, bright=0.9, wet=0.22, dur=3.0):
    y = glass_note(f0, dur=dur, vel=1.0, tau=tau, bright=bright, seed=seed)
    return verb(y, HALL, wet, 1.6), 0.0025


@sound("glass_chime_a", "clean glass chime, A5 (880 Hz): a station lights up, a block settles, a soft accent",
       "additive glass partials 1 / 2 / 3.01 / 4.18 / 5.43 / 6.79 with per-partial decay (upper ones die fast), "
       "slow-beating twin fundamental, 2.5 ms raised-cosine onset, synthetic hall (RT60 1.9 s)", -24)
def s_chime_a():
    return chime(PENTA["A5"], 81)


@sound("glass_chime_b", "clean glass chime, D6 (1175 Hz) - the tonic; pairs with a and c (D major pentatonic)",
       "as glass_chime_a on D6", -24)
def s_chime_b():
    return chime(PENTA["D6"], 82, tau=1.1)


@sound("glass_chime_c", "clean glass chime, F#6 (1480 Hz) - brightest of the three",
       "as glass_chime_a on F#6, slightly darker partial balance", -24)
def s_chime_c():
    return chime(PENTA["F#6"], 83, tau=1.0, bright=0.8)


@sound("glass_seal", "HERO 'committed / sealed on-chain' moment. Sync point = the chime at 0.60 s",
       "0-0.6 s: air swell (noise band-pass sweeping 1.2 -> 4.2 kHz) and a warm sub swell (D2 + D3 sines, slow "
       "raised-cosine rise) leading in; at 0.6 s a strummed glass chord D5-A5-D6-F#6 (16 ms apart), a soft warm "
       "body (D4 + A4, 25 ms onset) and three tiny sparkles; big synthetic hall (RT60 2.8 s). No transient.", -19)
def s_glass_seal():
    T = 0.6
    dur = 4.2  # long enough for the sub (tau 0.9 s) to be ~-40 dB before the dry part ends
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros((2, n))
    # air swell into the moment
    u = np.clip(t / T, 0, 1)
    fc = 1200.0 * (4200.0 / 1200.0) ** u
    sw = np.where(t < T, (0.5 - 0.5 * np.cos(np.pi * np.clip((t - 0.05) / (T - 0.05), 0, 1))) ** 1.6,
                  np.exp(-(t - T) / 0.12))
    for ch in range(2):
        a = svf(noise(n, "pink", 90 + ch), fc, 1.1, "bp")
        out[ch] += 0.16 * a / rms(a) * sw
    # warm sub swell (peaks just after the chime, decays)
    rise = np.clip((t - 0.12) / (T + 0.06 - 0.12), 0, 1)
    senv = np.where(t < T + 0.06, 0.5 - 0.5 * np.cos(np.pi * rise), np.exp(-(t - T - 0.06) / 0.9))
    sub = (osc_sine(73.42, n) + 0.35 * osc_sine(146.83, n)) * senv
    out += 0.55 * np.stack([sub, sub])
    # glass chord, strummed
    for k, (note, v, pan) in enumerate((("D5", 0.55, -0.25), ("A5", 0.75, 0.1), ("D6", 0.8, -0.05),
                                        ("F#6", 0.55, 0.25))):
        g = glass_note(PENTA[note], dur=dur - T, vel=v, tau=1.6, bright=0.85, seed=900 + k)
        out = place(out, pan_mono(g, pan), T + 0.016 * k)
    # warm body
    m = n - int(T * SR)
    tb = np.arange(m) / SR
    body = (osc_sine(293.66, m) + osc_sine(440.0, m)) * ramp_in(m, 0.025) * np.exp(-tb / 1.0)
    out = place(out, 0.22 * np.stack([body, body]), T)
    # sparkles
    for k, (note, dt) in enumerate((("A6", 0.03), ("D7", 0.07), ("F#6", 0.12))):
        g = glass_note(PENTA[note], dur=0.6, vel=0.07, tau=0.25, bright=0.5, beat_hz=0.0, seed=950 + k)
        out = place(out, pan_mono(g, (-0.5, 0.5, 0.0)[k]), T + dt)
    out = biquad(out, "lowpass", 12000.0, 0.7)
    out = fade(out, 0.0, 0.6)
    return verb(out, BIG, 0.30, 2.2), T


@sound("lock_click", "small precise latch: a padlock / lock icon closes, a rule is locked (sync = 2nd click, 32 ms)",
       "two micro-clicks 32 ms apart (engage + seat), each damped sines (2.9/1.5 kHz, then 2.3/1.2 kHz) over a "
       "small body (650/520 Hz, 7-9 ms), 0.25 ms onsets, tiny room", -26)
def s_lock_click():
    n = int(0.12 * SR)
    c1 = 0.5 * decay_tone(2900.0, 0.003, n, 0.00025) + 0.35 * decay_tone(1500.0, 0.006, n, 0.00025) \
        + 0.4 * decay_tone(650.0, 0.007, n, 0.0005) + 0.3 * decay_noise(3500.0, 1.5, 0.0015, n, 101)
    c2 = 0.4 * decay_tone(2300.0, 0.003, n, 0.00025) + 0.35 * decay_tone(1200.0, 0.007, n, 0.00025) \
        + 0.5 * decay_tone(520.0, 0.009, n, 0.0005) + 0.25 * decay_noise(2800.0, 1.5, 0.0015, n, 102)
    y = np.zeros(int(0.16 * SR))
    y = place(y, 0.75 * c1, 0.0)
    y = place(y, c2, 0.032)
    y = biquad(y, "lowpass", 9000.0, 0.7)
    return verb(y, ROOM, 0.10, 0.15), 0.032


@sound("success", "3-note rising chime: verification passed, all stations lit, task done",
       "glass notes A5 -> D6 -> F#6, 100 ms apart, rising velocity, hall (RT60 1.9 s)", -22)
def s_success():
    dur = 2.0
    out = np.zeros((2, int(dur * SR)))
    for k, (note, v, pan) in enumerate((("A5", 0.75, -0.2), ("D6", 0.85, 0.0), ("F#6", 1.0, 0.2))):
        g = glass_note(PENTA[note], dur=dur - 0.2, vel=v, tau=0.75, bright=0.85, seed=110 + k)
        out = place(out, pan_mono(g, pan), 0.10 * k)
    return verb(out, HALL, 0.20, 1.4), 0.0025


@sound("notify", "a chat message arrives (Telegram reply, agent answer), soft",
       "two short 'glass-marimba' notes B5 -> E6 85 ms apart (fast-decaying partials) + a soft puff of air", -24)
def s_notify():
    dur = 0.9
    out = np.zeros(int(dur * SR))
    parts = ((1.0, 1.0, 1.0), (3.0, 0.12, 0.25), (4.0, 0.05, 0.12))
    for k, (note, v) in enumerate((("B5", 0.8), ("E6", 1.0))):
        g = glass_note(PENTA[note], dur=0.7, vel=v, tau=0.32, bright=1.0, beat_hz=0.0, seed=120 + k,
                       partials=parts)
        out = place(out, g, 0.085 * k)
    n = len(out)
    t = np.arange(n) / SR
    puff = biquad(noise(n, "pink", 125), "bandpass", 2500.0, 1.0)
    out += 0.10 * puff / rms(puff) * ramp_in(n, 0.003) * np.exp(-t / 0.025)
    return verb(out, ROOM, 0.15, 0.3), 0.0025


@sound("coin", "payment confirmed (x402 pay-per-signal), soft and pleasant",
       "two bright glass notes D6 -> A6 75 ms apart with a faint inharmonic 2.76x 'coin' partial, then a few soft "
       "sparkle grains; hall", -22)
def s_coin():
    dur = 1.5
    out = np.zeros((2, int(dur * SR)))
    parts = ((1.0, 1.0, 1.0), (2.0, 0.3, 0.5), (2.76, 0.08, 0.3), (3.0, 0.08, 0.3), (4.18, 0.03, 0.12))
    for k, (note, v, tau) in enumerate((("D6", 0.75, 0.5), ("A6", 1.0, 0.7))):
        g = glass_note(PENTA[note], dur=1.2, vel=v, tau=tau, bright=1.0, seed=130 + k, partials=parts)
        out = place(out, pan_mono(g, (-0.1, 0.1)[k]), 0.075 * k)
    out = place(out, 0.10 * grain_cloud(0.3, 6, seed=131, freqs=[PENTA[k] for k in ("A6", "B6", "D7", "E7")],
                                        peak_frac=0.4), 0.05)
    return verb(out, HALL, 0.20, 1.2), 0.0025


@sound("data_blip_a", "tiny high data ping: a row updates, a packet arrives, a counter ticks over",
       "sine D7 (2349 Hz) with 1.5 ms onset and 16 ms decay over a quiet A6", -29)
def s_blip_a():
    n = int(0.1 * SR)
    t = np.arange(n) / SR
    env = ramp_in(n, 0.0015) * np.exp(-t / 0.016)
    y = (osc_sine(PENTA["D7"], n) + 0.25 * osc_sine(PENTA["A6"], n)) * env
    return verb(y, ROOM, 0.08, 0.1), 0.0015


@sound("data_blip_b", "double data ping (A6 -> E7): a request + its answer, a chain confirmation",
       "two sine pips 45 ms apart, 1 ms onsets, 10-12 ms decays", -29)
def s_blip_b():
    n = int(0.14 * SR)
    t = np.arange(int(0.08 * SR)) / SR
    y = np.zeros(n)
    y = place(y, osc_sine(PENTA["A6"], len(t)) * ramp_in(len(t), 0.001) * np.exp(-t / 0.010), 0.0)
    y = place(y, 0.9 * osc_sine(PENTA["E7"], len(t)) * ramp_in(len(t), 0.001) * np.exp(-t / 0.012), 0.045)
    return verb(y, ROOM, 0.08, 0.1), 0.001


@sound("shimmer", "1 s sparkle on glass: crystal glints, a card turns into light, the logo catches light",
       "granular cloud of ~42 short glass grains on D-major-pentatonic notes (1.2-3.5 kHz, weighted low), "
       "density rising to 0.35 s then thinning, random pan, faint high air, hall (RT60 1.9 s)", -25)
def s_shimmer():
    out = grain_cloud(1.0, 42, seed=141)
    n = out.shape[1]
    t = np.arange(n) / SR
    env = np.where(t < 0.35, np.sin(0.5 * np.pi * t / 0.35) ** 2, np.exp(-(t - 0.35) / 0.3))
    a = np.stack([air(n, 6000, 14000, 142), air(n, 6000, 14000, 143)])
    out = out / (np.abs(out).max() + 1e-12) + 0.035 * a * env
    return verb(out, HALL, 0.35, 1.4), 0.0


@sound("riser_2s", "2 s build into a cut / reveal (sync point = END of file)",
       "pink+white noise through a TPT low-pass opening 260 Hz -> 7 kHz (late curve) with growing resonance and "
       "rising high-pass, + D3/A3/D4 saw chord gliding up an octave; ~30 dB rise, peaks at 96 %, shaped to 0", -23)
def s_riser_2():
    x = riser(2.0, seed=151)
    return x, x.shape[1] / SR


@sound("riser_4s", "4 s build (section lift, 'open' build) - sync point = END of file",
       "as riser_2s over 4 s", -23)
def s_riser_4():
    x = riser(4.0, seed=152)
    return x, x.shape[1] / SR


@sound("downlifter", "settle after a peak: bright air falling away, a quiet two-note tone easing down a fourth",
       "noise low-pass sweeping 7 kHz -> 650 Hz, quiet A4 + D5 sines easing down 5 semitones (never to zero, so "
       "not a tape-stop), narrowing stereo, 25 ms soft onset; sync point = start", -25)
def s_downlifter():
    return downlifter(2.4, seed=161, f_start=7000.0, f_end=650.0, semis=-5.0, tone_mix=0.12, decay=1.5), 0.0


@sound("sub_swell", "gentle low swell under a big moment (no punch); sync point = its peak at 1.3 s",
       "D2 sine + 2nd/3rd harmonics (so laptops hear it), 1.3 s raised-cosine rise, 0.55 s release", -24)
def s_sub_swell():
    return sub_swell(3.0, 1.3), 1.3


@sound("reveal_bloom", "airy pad bloom for the logo / headline reveal; sync point = start",
       "Dmaj9 pad (D3 A3 C#4 E4 F#4 A4, 5-voice detuned PolyBLEP saws + sine body) through a low-pass that "
       "blooms 320 Hz -> 3.2 kHz in 0.9 s then settles, high air, two glass notes (D6, A6), big hall (RT60 2.8 s)", -21)
def s_reveal_bloom():
    notes = [146.83, 220.0, 277.18, 329.63, 369.99, 440.0]
    dur = 5.0
    pad = bloom_pad(notes, dur=dur, attack=0.35, hold=2.0, release=2.4, seed=171)
    n = pad.shape[1]
    t = np.arange(n) / SR
    aenv = np.where(t < 0.6, np.sin(0.5 * np.pi * t / 0.6) ** 2, np.exp(-(t - 0.6) / 1.4))
    a = np.stack([air(n, 5000, 13000, 172), air(n, 5000, 13000, 173)]) * aenv
    out = pad + 0.05 * a
    for k, (note, dt) in enumerate((("D6", 0.15), ("A6", 0.32))):
        g = glass_note(PENTA[note], dur=3.0, vel=0.16, tau=1.2, bright=0.7, seed=175 + k)
        out = place(out, pan_mono(g, (-0.3, 0.3)[k]), dt)
    return verb(out, BIG, 0.35, 2.5), 0.0


# =========================================================================================== finish + write
def trim_tail(x, thresh_db=-70.0, keep=0.03):
    """Cut the tail where it has decayed below thresh_db re peak (plus `keep` seconds)."""
    x2 = np.atleast_2d(x)
    env = np.abs(x2).max(axis=0)
    pk = env.max()
    idx = np.nonzero(env > pk * undb(thresh_db))[0]
    end = min(x2.shape[1], (idx[-1] if len(idx) else x2.shape[1]) + int(keep * SR))
    return x[..., :end]


def finish(x):
    x = np.asarray(x, dtype=np.float64)
    x = butter(x, "highpass", 22.0, 2)  # DC / sub-sonic clean-up
    x = trim_tail(x)
    dur = x.shape[-1] / SR
    x = fade(x, 0.0005, float(np.clip(0.2 * dur, 0.008, 0.35)))
    x = x * undb(PEAK_DBFS) / (np.abs(x).max() + 1e-12)
    tp = true_peak_db(x)
    if tp > TP_MAX - 0.05:
        x *= undb(TP_MAX - 0.1 - tp)
    return x


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def describe(x):
    x2 = np.atleast_2d(x)
    _, mom = block_loudness(x2) if x2.shape[1] >= int(0.4 * SR) else (None, np.array([integrated_lufs(
        np.pad(x2, ((0, 0), (0, int(0.4 * SR) - x2.shape[1]))))]))
    return dict(peak_dbfs=round(float(todb(np.abs(x2).max())), 2), true_peak_dbtp=round(true_peak_db(x2), 2),
                momentary_max_lufs=round(float(np.max(mom)), 1))


def render(names=None):
    OUT.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    manifest.setdefault("sounds", {})
    for name, spec in SOUNDS.items():
        if names and name not in names:
            continue
        x, anchor = spec["fn"]()
        x = finish(x)
        path = OUT / f"{name}.wav"
        write_wav(path, x)
        info = dict(file=f"{name}.wav", duration=round(x.shape[-1] / SR, 3), channels=1 if x.ndim == 1 else 2,
                    anchor=round(float(anchor), 4), use=spec["use"], how=spec["how"], sha256=sha256(path),
                    **describe(x))
        info["target_lufs"] = spec["target"]
        info["suggested_gain_db"] = round(spec["target"] - info["momentary_max_lufs"])
        manifest["sounds"][name] = info
        print(f"{name:15s} {info['duration']:5.2f}s ch{info['channels']} anchor {info['anchor']:5.3f}s "
              f"peak {info['peak_dbfs']:6.2f} dBFS  TP {info['true_peak_dbtp']:6.2f} dBTP  "
              f"Mmax {info['momentary_max_lufs']:6.1f} LUFS  gain {info['suggested_gain_db']:+d} dB")
    manifest["format"] = "48 kHz, 24-bit PCM WAV; peak -1.5 dBFS, true peak <= -1 dBTP; anchor = sync point (s)"
    manifest["generator"] = "analysis/sfx_synth.py"
    src = OUT / "remotion" / "SOURCES.json"
    if src.exists():
        manifest["remotion"] = json.loads(src.read_text(encoding="utf-8"))
    manifest_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    write_readme(manifest)
    return manifest


def write_readme(manifest):
    s = manifest["sounds"]
    lines = [
        "# sfx2 - clean SFX library for the Fabius pitch video v2",
        "",
        "Synthesised by `analysis/sfx_synth.py` (numpy/scipy, fixed seeds - re-running gives identical files): no",
        "samples, no licences, owned outright. 48 kHz, 24-bit PCM WAV, every file starts and ends on exactly 0,",
        "peak -1.5 dBFS (true peak <= -1 dBTP).",
        "",
        "**Client rule:** nothing that sounds like a crash or something broken - no impacts, slams, debris,",
        "falling pieces, shattering glass, glitches, static, crackle, sizzle, zaps, distortion, tape-stops, rewinds,",
        "reverse sucks, scratches, snips, stamps. `analysis/check_sfx.py` enforces it mechanically (whitelist with",
        "SHA-256 pins, banned-name patterns, cue-sheet check, acoustic screen); run it before every render.",
        "",
        "**Sync point (`anchor`)**: the moment inside the file that should land on the picture event (whoosh = its",
        "peak, riser = its end, chime = its onset, glass_seal = the chime at 0.60 s). `analysis/mix_v2.py` places a",
        "cue so that the anchor lands on the cue time `t`. `gain` = a starting cue gain (dB) for a -14 LUFS mix",
        "with voice; files are peak-normalised, so short sounds need less cut than long ones.",
        "",
        "| file | length | ch | anchor | gain | use | how it is made |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, i in s.items():
        lines.append(f"| `{i['file']}` | {i['duration']:.2f} s | {i['channels']} | {i['anchor']:.3f} s | "
                     f"{i['suggested_gain_db']} | {i['use']} | {i['how']} |")
    rem = manifest.get("remotion")
    if rem:
        lines += ["", "## remotion/ - picked from `@remotion/sfx` (CC0, attribution not required)", "",
                  "Fetched by `analysis/fetch_remotion_sfx.py` from https://remotion.media/ (the URLs exported by",
                  "`node_modules/@remotion/sfx`); the original's SHA-256 is pinned there (a changed upstream file stops",
                  "the script) and recorded in `remotion/SOURCES.json`. Admitted only if CC0 and clean on the acoustic",
                  "screen, then conformed to the sfx2 format (48 kHz 24-bit, edge fades, peak -1.5 dBFS).", "",
                  "| file | source | licence | use | screen notes |", "|---|---|---|---|---|"]
        for f, r in rem.get("kept", {}).items():
            lines.append(f"| `remotion/{f}` | {r['source']} | {r['license']} | {r['use']} | {r['notes']} |")
        if rem.get("skipped"):
            lines += ["", "Not taken: " + "; ".join(f"`{k}` ({v})" for k, v in rem["skipped"].items()) + "."]
    lines += ["", "Regenerate: `python -X utf8 analysis/sfx_synth.py` then `python -X utf8 analysis/check_sfx.py`",
              "(if a sound was changed on purpose, review it, then refresh its pin with",
              "`python -X utf8 analysis/check_sfx.py --print-whitelist`).", ""]
    (OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def sheet(manifest, path):
    """Contact sheet: one small spectrogram + waveform per sound (visual QA without ears)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy import signal as ss
    from dsp_v2 import read_audio
    names = list(manifest["sounds"].keys())
    cols = 5
    rows = int(np.ceil(len(names) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4.2, rows * 2.6))
    for ax, name in zip(axes.flat, names):
        x = read_audio(OUT / manifest["sounds"][name]["file"])
        mono = x.mean(axis=0) if x.ndim == 2 else x
        nper = 512 if len(mono) < SR * 0.5 else 1024
        f, t, S = ss.spectrogram(mono, fs=SR, nperseg=nper, noverlap=nper * 7 // 8)
        ax.pcolormesh(t, f / 1000, 10 * np.log10(S + 1e-16), shading="auto", cmap="magma",
                      vmin=10 * np.log10(S.max() + 1e-16) - 90, vmax=10 * np.log10(S.max() + 1e-16))
        ax.set_ylim(0, 16)
        tt = np.arange(len(mono)) / SR
        ax2 = ax.twinx()
        ax2.plot(tt, mono, color="#9fe3ff", lw=0.3, alpha=0.7)
        ax2.set_ylim(-1, 1)
        ax2.set_yticks([])
        ax.axvline(manifest["sounds"][name]["anchor"], color="#00ff9c", lw=0.8)
        ax.set_title(f"{name}  ({len(mono) / SR:.2f}s)", fontsize=8)
        ax.tick_params(labelsize=6)
    for ax in list(axes.flat)[len(names):]:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(str(path), dpi=80)
    plt.close(fig)
    print(f"sheet -> {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", default="", help="comma-separated sound names")
    ap.add_argument("--sheet", action="store_true", help="also write out/audio/sfx2_sheet.png")
    a = ap.parse_args()
    names = [s.strip() for s in a.only.split(",") if s.strip()] or None
    manifest = render(names)
    if a.sheet:
        sheet(manifest, ROOT / "out" / "audio" / "sfx2_sheet.png")
    print(f"{len(manifest['sounds'])} sounds -> {OUT}")


if __name__ == "__main__":
    main()
