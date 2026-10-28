"""Shared DSP for the v2 sound pass of the Fabius pitch video (sfx_synth.py, music_v2.py, mix_v2.py, check_sfx.py).

numpy + scipy + soundfile. numba, when installed, compiles the few per-sample loops (time-varying state-variable
filter, compressor gain computer, limiter release); without numba the same code runs as plain Python, only slower.

Conventions: mono = shape (n,), stereo = shape (2, n), float64, 48 kHz unless a function says otherwise.
Loudness follows ITU-R BS.1770-4 / EBU R128 (K-weighting, 400 ms blocks, 75 % overlap, -70 LUFS absolute gate,
-10 LU relative gate); true peak = 4x polyphase oversampling.
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal
from scipy.ndimage import minimum_filter1d

try:  # numba is optional
    from numba import njit
except Exception:  # pragma: no cover - fallback keeps the code runnable without numba
    def njit(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]
        return lambda f: f

SR = 48000
ROOT = Path(__file__).resolve().parent.parent  # vault/Video-Workspace


# ----------------------------------------------------------------------------------------------- units
def undb(d):
    return 10.0 ** (np.asarray(d, dtype=np.float64) / 20.0)


def todb(x, floor=1e-12):
    return 20.0 * np.log10(np.maximum(np.abs(np.asarray(x, dtype=np.float64)), floor))


def midi_hz(m):
    return 440.0 * 2.0 ** ((np.asarray(m, dtype=np.float64) - 69.0) / 12.0)


def secs(n, sr=SR):
    return np.arange(int(n)) / sr


# ----------------------------------------------------------------------------------------------- I/O
def write_wav(path, x, sr=SR, subtype="PCM_24"):
    """Write mono (n,) or stereo (2, n). PCM subtypes are clipped to [-1, 1]; FLOAT is written as is."""
    x = np.asarray(x, dtype=np.float64)
    data = x.T if x.ndim == 2 else x
    if subtype.startswith("PCM"):
        data = np.clip(data, -1.0, 1.0)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), data, sr, subtype=subtype)


def read_audio(path, sr=SR, mono=False):
    """Read any audio file -> float64 (n,) for mono files (or mono=True), (ch, n) otherwise, resampled to sr.
    WAV/FLAC/OGG through soundfile; anything else (mp3, m4a ...) decoded by ffmpeg."""
    path = Path(path)
    try:
        data, fs = sf.read(str(path), dtype="float64", always_2d=True)
        x = data.T.copy()
    except Exception:
        probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels",
                                "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
        ch = int(probe.stdout.strip().split(",")[0] or 1)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-acodec", "pcm_f32le",
                              "-ar", str(sr), "-"], capture_output=True, check=True).stdout
        x = np.frombuffer(raw, dtype=np.float32).astype(np.float64).reshape(-1, ch).T.copy()
        fs = sr
    if fs != sr:
        g = math.gcd(int(fs), int(sr))
        x = signal.resample_poly(x, sr // g, int(fs) // g, axis=-1)
    if mono or x.shape[0] == 1:
        return x.mean(axis=0)
    return x


def as_stereo(x):
    x = np.asarray(x, dtype=np.float64)
    return np.stack([x, x]) if x.ndim == 1 else x


# ----------------------------------------------------------------------------------------------- filters
def rbj(kind, f0, q=0.7071, gain_db=0.0, sr=SR):
    """RBJ audio-EQ-cookbook biquad -> (b, a). kind: lowpass, highpass, bandpass (0 dB peak), peak, lowshelf,
    highshelf, notch."""
    f0 = min(max(float(f0), 1.0), 0.49 * sr)
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * math.pi * f0 / sr
    cw, sw = math.cos(w0), math.sin(w0)
    alpha = sw / (2.0 * q)
    if kind == "lowpass":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]; a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "highpass":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]; a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "bandpass":
        b = [alpha, 0.0, -alpha]; a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "notch":
        b = [1.0, -2 * cw, 1.0]; a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "peak":
        b = [1 + alpha * A, -2 * cw, 1 - alpha * A]; a = [1 + alpha / A, -2 * cw, 1 - alpha / A]
    elif kind in ("lowshelf", "highshelf"):
        s = 2.0 * math.sqrt(A) * alpha
        if kind == "lowshelf":
            b = [A * ((A + 1) - (A - 1) * cw + s), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - s)]
            a = [(A + 1) + (A - 1) * cw + s, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - s]
        else:
            b = [A * ((A + 1) + (A - 1) * cw + s), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - s)]
            a = [(A + 1) - (A - 1) * cw + s, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - s]
    else:
        raise ValueError(kind)
    b = np.asarray(b) / a[0]
    a = np.asarray(a) / a[0]
    return b, a


def biquad(x, kind, f0, q=0.7071, gain_db=0.0, sr=SR):
    b, a = rbj(kind, f0, q, gain_db, sr)
    return signal.lfilter(b, a, x, axis=-1)


def butter(x, kind, f, order=2, sr=SR, zero_phase=False):
    """Butterworth (kind: lowpass/highpass/bandpass/bandstop). zero_phase=True runs it forward + backward."""
    sos = signal.butter(order, f, btype=kind, fs=sr, output="sos")
    return signal.sosfiltfilt(sos, x, axis=-1) if zero_phase else signal.sosfilt(sos, x, axis=-1)


@njit(cache=True)
def _svf(x, fc, q, mode, sr):
    # Zavalishin TPT state-variable filter: stable under fast cutoff modulation (no zipper, no blow-up)
    n = x.shape[0]
    y = np.empty(n)
    ic1 = 0.0
    ic2 = 0.0
    nf = fc.shape[0]
    nq = q.shape[0]
    for i in range(n):
        f = fc[i] if nf > 1 else fc[0]
        if f > 0.45 * sr:
            f = 0.45 * sr
        if f < 5.0:
            f = 5.0
        g = math.tan(math.pi * f / sr)
        qq = q[i] if nq > 1 else q[0]
        k = 1.0 / qq
        a1 = 1.0 / (1.0 + g * (g + k))
        a2 = g * a1
        a3 = g * a2
        v0 = x[i]
        v3 = v0 - ic2
        v1 = a1 * ic1 + a2 * v3
        v2 = ic2 + a2 * ic1 + a3 * v3
        ic1 = 2.0 * v1 - ic1
        ic2 = 2.0 * v2 - ic2
        if mode == 0:
            y[i] = v2
        elif mode == 1:
            y[i] = k * v1
        elif mode == 2:
            y[i] = v0 - k * v1 - v2
        else:
            y[i] = v0 - k * v1
    return y


_SVF_MODES = {"lp": 0, "bp": 1, "hp": 2, "notch": 3}


def svf(x, fc, q=0.7071, mode="lp", sr=SR):
    """Time-varying TPT state-variable filter. fc and q: scalars or per-sample arrays (same length as x).
    mode: lp, bp (unity gain at fc), hp, notch. Works on mono (n,) or stereo (2, n)."""
    m = _SVF_MODES[mode]
    fc = np.ascontiguousarray(np.atleast_1d(np.asarray(fc, dtype=np.float64)))
    q = np.ascontiguousarray(np.atleast_1d(np.asarray(q, dtype=np.float64)))
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 2:
        return np.stack([_svf(np.ascontiguousarray(c), fc, q, m, float(sr)) for c in x])
    return _svf(np.ascontiguousarray(x), fc, q, m, float(sr))


def exp_curve(n, a, b, shape=1.0):
    """n samples from a to b, exponential in value (for frequencies); shape > 1 bends late, < 1 bends early."""
    u = np.linspace(0.0, 1.0, int(n)) ** shape
    return a * (b / a) ** u


def automation(points, n, sr=SR, log=True):
    """Piecewise automation from [(t_sec, value), ...] -> per-sample array of length n (log-interpolated for
    frequencies when log=True)."""
    pts = sorted(points)
    t = np.arange(int(n)) / sr
    ts = np.array([p[0] for p in pts], dtype=np.float64)
    vs = np.array([p[1] for p in pts], dtype=np.float64)
    if log:
        return np.exp(np.interp(t, ts, np.log(vs)))
    return np.interp(t, ts, vs)


# ----------------------------------------------------------------------------------------------- oscillators
def _phase(freq, n, sr=SR, phase0=0.0):
    f = np.broadcast_to(np.asarray(freq, dtype=np.float64), (int(n),))
    inc = f / sr
    ph = phase0 + np.concatenate(([0.0], np.cumsum(inc[:-1])))
    return np.mod(ph, 1.0), np.maximum(inc, 1e-9)


def _blep(t, dt):
    y = np.zeros_like(t)
    m = t < dt
    u = t[m] / dt[m]
    y[m] = u + u - u * u - 1.0
    m = t > 1.0 - dt
    u = (t[m] - 1.0) / dt[m]
    y[m] = u * u + u + u + 1.0
    return y


def osc_saw(freq, n, sr=SR, phase0=0.0):
    """Band-limited (PolyBLEP) sawtooth, freq scalar or per-sample array."""
    t, dt = _phase(freq, n, sr, phase0)
    return 2.0 * t - 1.0 - _blep(t, dt)


def osc_square(freq, n, sr=SR, phase0=0.0, pw=0.5):
    """Band-limited (PolyBLEP) pulse wave with pulse width pw."""
    t, dt = _phase(freq, n, sr, phase0)
    y = np.where(t < pw, 1.0, -1.0)
    y = y + _blep(t, dt) - _blep(np.mod(t + (1.0 - pw), 1.0), dt)
    return y


def osc_tri(freq, n, sr=SR, phase0=0.0):
    """Triangle from a leaky-integrated PolyBLEP square (band-limited corners)."""
    t, dt = _phase(freq, n, sr, phase0)
    sq = np.where(t < 0.5, 1.0, -1.0) + _blep(t, dt) - _blep(np.mod(t + 0.5, 1.0), dt)
    y = signal.lfilter([1.0], [1.0, -0.9995], 4.0 * dt * sq)
    return y - signal.lfilter([0.0005], [1.0, -0.9995], y)  # remove the integrator's slow drift


def osc_sine(freq, n, sr=SR, phase0=0.0):
    t, _ = _phase(freq, n, sr, phase0)
    return np.sin(2.0 * np.pi * t)


# ----------------------------------------------------------------------------------------------- noise
def noise(n, color="white", seed=0):
    """Gaussian noise, unit RMS. color: white, pink (-3 dB/oct), brown (-6 dB/oct), blue (+3 dB/oct)."""
    rng = np.random.default_rng(seed)
    n = int(n)
    w = rng.standard_normal(n)
    if color == "white":
        return w
    spec = np.fft.rfft(w)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    f[0] = f[1] if n > 1 else 1.0
    tilt = {"pink": -0.5, "brown": -1.0, "blue": 0.5}[color]
    spec *= (f / 1000.0) ** tilt
    y = np.fft.irfft(spec, n)
    y -= y.mean()
    return y / (np.sqrt(np.mean(y * y)) + 1e-12)


# ----------------------------------------------------------------------------------------------- envelopes
def raised_cos(n):
    n = int(n)
    if n <= 0:
        return np.zeros(0)
    return 0.5 - 0.5 * np.cos(np.pi * np.arange(n) / n)


def adsr(n, a=0.01, d=0.1, s=0.7, r=0.2, gate=None, sr=SR, curve=5.0):
    """Sample-accurate ADSR of n samples: raised-cosine attack, exponential decay to s, held until gate (seconds,
    default n/sr - r), exponential release that lands exactly on 0 at gate + r."""
    n = int(n)
    t = np.arange(n) / sr
    gate = (n / sr - r) if gate is None else gate
    a = max(a, 1.0 / sr)
    env = np.where(t < a, 0.5 - 0.5 * np.cos(np.pi * np.minimum(t / a, 1.0)), 0.0)
    dec = t >= a
    env[dec] = s + (1.0 - s) * np.exp(-curve * (t[dec] - a) / max(d, 1e-4))
    if gate < n / sr:
        g_i = int(gate * sr)
        lvl = env[min(g_i, n - 1)]
        u = (t[g_i:] - gate) / max(r, 1e-4)
        shape = (np.exp(-curve * np.minimum(u, 1.0)) - math.exp(-curve)) / (1.0 - math.exp(-curve))
        env[g_i:] = lvl * np.clip(shape, 0.0, 1.0)
    return env


def fade(x, fin=0.0, fout=0.0, sr=SR):
    """Raised-cosine fade in/out (seconds); the first/last sample becomes exactly 0 when the fade is > 0."""
    x = np.array(x, dtype=np.float64, copy=True)
    n = x.shape[-1]
    i = min(n, int(round(fin * sr)))
    if i > 0:
        x[..., :i] *= raised_cos(i)
    o = min(n, int(round(fout * sr)))
    if o > 0:
        x[..., n - o:] *= raised_cos(o)[::-1]  # ends on exactly 0
    return x


# ----------------------------------------------------------------------------------------------- placement
def pan_mono(x, pan):
    """Constant-power pan of a mono signal (pan -1 .. 1, scalar or array) -> (2, n)."""
    th = (np.clip(np.asarray(pan, dtype=np.float64), -1, 1) + 1.0) * np.pi / 4.0
    return np.stack([x * np.cos(th), x * np.sin(th)])


def balance(x, pan):
    """Balance a stereo signal: pan 0 leaves it untouched, +1 = right only."""
    th = (float(np.clip(pan, -1, 1)) + 1.0) * np.pi / 4.0
    gl, gr = min(1.0, math.sqrt(2) * math.cos(th)), min(1.0, math.sqrt(2) * math.sin(th))
    return np.stack([x[0] * gl, x[1] * gr])


def add_at(bus, x, t, sr=SR):
    """Add x (same channel layout as bus) into bus starting at time t (seconds); clipped at both ends."""
    i0 = int(round(t * sr))
    n = bus.shape[-1]
    m = x.shape[-1]
    j0 = max(0, -i0)
    i0 = max(0, i0)
    k = min(m - j0, n - i0)
    if k > 0:
        bus[..., i0:i0 + k] += x[..., j0:j0 + k]
    return bus


def resample_rate(x, rate):
    """Playback-rate change (pitch + time together) by linear interpolation; rate 1.0 = unchanged."""
    if abs(rate - 1.0) < 1e-6:
        return x
    n = x.shape[-1]
    m = int(n / rate)
    pos = np.arange(m) * rate
    if x.ndim == 1:
        return np.interp(pos, np.arange(n), x)
    return np.stack([np.interp(pos, np.arange(n), c) for c in x])


# ----------------------------------------------------------------------------------------------- effects
def chorus(x, sr=SR, voices=3, base_ms=12.0, depth_ms=2.6, rates=(0.13, 0.21, 0.29), mix=0.45, seed=0):
    """Stereo chorus: modulated fractional delays (linear interpolation), voices spread L/R. Returns stereo."""
    x = as_stereo(x)
    n = x.shape[1]
    t = np.arange(n) / sr
    rng = np.random.default_rng(seed)
    wet = np.zeros_like(x)
    idx = np.arange(n, dtype=np.float64)
    for v in range(voices):
        rate = rates[v % len(rates)]
        d = (base_ms + depth_ms * np.sin(2 * np.pi * rate * t + rng.uniform(0, 2 * np.pi))) * sr / 1000.0
        pos = idx - d
        i0 = np.floor(pos).astype(np.int64)
        fr = pos - i0
        ok = i0 >= 0
        i0c = np.clip(i0, 0, n - 2)
        side = v % 2 if voices > 1 else 0
        for c in (0, 1):
            src = x[c] if (c == side or voices == 1) else x[1 - c]
            s = src[i0c] * (1.0 - fr) + src[i0c + 1] * fr
            s[~ok] = 0.0
            wet[c] += s * (0.85 if c == side else 0.35)
    wet /= max(1.0, voices / 2.0)
    return (1.0 - 0.5 * mix) * x + mix * wet


def pingpong(x, delay_s, feedback=0.4, echoes=6, lp_hz=3200.0, hp_hz=250.0, sr=SR):
    """Ping-pong delay, wet only: echo k (k = 1 ..) has gain feedback**(k-1), alternates L/R and is low-passed once
    more per repeat (darker each time). Mono or stereo in, stereo out."""
    mono = x.mean(axis=0) if np.asarray(x).ndim == 2 else np.asarray(x, dtype=np.float64)
    n = len(mono)
    d = int(round(delay_s * sr))
    wet = np.zeros((2, n))
    e = butter(mono, "highpass", hp_hz, 2, sr)
    b, a = rbj("lowpass", lp_hz, 0.6, sr=sr)
    g = 1.0
    for k in range(1, echoes + 1):
        e = signal.lfilter(b, a, e)
        sh = k * d
        if sh >= n:
            break
        wet[(k - 1) % 2, sh:] += g * e[:n - sh]
        g *= feedback
    return wet


def make_ir(rt60=2.2, length=None, predelay=0.018, hf_ratio=0.35, damp_hz=4500.0, lf_ratio=1.1, bright_hz=9000.0,
            er_count=16, er_gain=0.55, er_span=0.08, low_cut=140.0, build=0.025, seed=0, sr=SR):
    """Synthesised stereo impulse response, (2, L), unit energy per channel.

    Early reflections: er_count sparse taps over er_span seconds (random sign, decaying, each softened).
    Late tail: decorrelated L/R Gaussian noise shaped in the STFT domain so every frequency decays with its own
    RT60 (highs die faster: rt60 * hf_ratio above damp_hz, lows rt60 * lf_ratio), a soft build-up (build seconds),
    low cut + bright_hz roll-off. Pre-delay in front."""
    length = length or min(rt60 * 1.25 + 0.25, 7.0)
    n = int(length * sr)
    rng = np.random.default_rng(seed)
    ir = np.zeros((2, n))
    nper = 1024
    for ch in range(2):
        nz = rng.standard_normal(n + nper)
        f, tt, Z = signal.stft(nz, fs=sr, nperseg=nper, noverlap=nper * 3 // 4)
        rtf = rt60 * (hf_ratio + (1.0 - hf_ratio) / (1.0 + (f / damp_hz) ** 2))
        rtf *= 1.0 + (lf_ratio - 1.0) / (1.0 + (f / 250.0) ** 2)
        G = np.exp(-6.9078 * tt[None, :] / rtf[:, None])
        G *= (1.0 / np.sqrt(1.0 + (f / bright_hz) ** 4))[:, None]
        G *= (1.0 / np.sqrt(1.0 + (low_cut / np.maximum(f, 1.0)) ** 4))[:, None]
        _, tail = signal.istft(Z * G, fs=sr, nperseg=nper, noverlap=nper * 3 // 4)
        tail = np.asarray(tail[:n], dtype=np.float64)
        if len(tail) < n:
            tail = np.pad(tail, (0, n - len(tail)))
        tail *= 1.0 - np.exp(-np.arange(n) / (build * sr))
        tail /= np.sqrt(np.sum(tail ** 2)) + 1e-12
        er = np.zeros(n)
        times = np.sort(rng.uniform(0.003, er_span, er_count))
        for tk in times:
            i = int(tk * sr)
            er[i] += (1.0 - tk / (er_span * 1.3)) * rng.uniform(0.4, 1.0) * rng.choice([-1.0, 1.0])
        er = biquad(er, "lowpass", 6500.0, 0.6, sr=sr)
        er = biquad(er, "highpass", low_cut, 0.7, sr=sr)
        er /= np.sqrt(np.sum(er ** 2)) + 1e-12
        ir[ch] = tail + er_gain * er
        ir[ch] /= np.sqrt(np.sum(ir[ch] ** 2)) + 1e-12
    pre = int(predelay * sr)
    return np.concatenate([np.zeros((2, pre)), ir], axis=1)


def convolve(x, ir, keep_tail=True):
    """Convolve mono/stereo x with a stereo IR (2, L) -> stereo; channel c of the output uses ir[c]."""
    x = as_stereo(x)
    out = np.stack([signal.oaconvolve(x[c], ir[c]) for c in (0, 1)])
    return out if keep_tail else out[:, : x.shape[1]]


def reverb(x, ir, wet=0.25, dry=1.0):
    """Dry/wet convolution reverb with the output trimmed to the input length (pad your input for tails)."""
    x = as_stereo(x)
    w = convolve(x, ir, keep_tail=False)
    return dry * x + wet * w


@njit(cache=True)
def _follow(x, att, rel):
    n = x.shape[0]
    y = np.empty(n)
    s = 0.0
    for i in range(n):
        v = x[i]
        c = att if v > s else rel
        s = c * s + (1.0 - c) * v
        y[i] = s
    return y


def follow(x, attack_ms, release_ms, sr=SR):
    """Attack/release envelope follower (one pole each way) on a non-negative signal."""
    att = math.exp(-1.0 / max(attack_ms * 1e-3 * sr, 1e-9))
    rel = math.exp(-1.0 / max(release_ms * 1e-3 * sr, 1e-9))
    return _follow(np.ascontiguousarray(np.asarray(x, dtype=np.float64)), att, rel)


@njit(cache=True)
def _hold_max(x, hold):
    # running max over the last `hold` samples (peak hold), O(n * small) via monotone deque emulation
    n = x.shape[0]
    y = np.empty(n)
    dq = np.empty(n, dtype=np.int64)
    head = 0
    tail = 0
    for i in range(n):
        while tail > head and x[dq[tail - 1]] <= x[i]:
            tail -= 1
        dq[tail] = i
        tail += 1
        if dq[head] <= i - hold:
            head += 1
        y[i] = x[dq[head]]
    return y


def hold_max(x, hold_s, sr=SR):
    return _hold_max(np.ascontiguousarray(np.asarray(x, dtype=np.float64)), max(1, int(hold_s * sr)))


@njit(cache=True)
def _gain_computer(level_db, thresh, ratio, knee, att, rel):
    n = level_db.shape[0]
    gr = np.empty(n)
    s = 0.0
    for i in range(n):
        over = level_db[i] - thresh
        if 2.0 * over < -knee:
            red = 0.0
        elif 2.0 * abs(over) <= knee:
            red = (1.0 - 1.0 / ratio) * (over + knee / 2.0) ** 2 / (2.0 * knee)
        else:
            red = (1.0 - 1.0 / ratio) * over
        c = att if red > s else rel
        s = c * s + (1.0 - c) * red
        gr[i] = s
    return gr


def compress(x, thresh_db=-18.0, ratio=2.0, attack_ms=10.0, release_ms=150.0, knee_db=6.0, makeup_db=0.0,
             rms_ms=8.0, sidechain=None, sr=SR):
    """Feed-forward compressor (stereo-linked, RMS detector over rms_ms, soft knee, smoothed gain reduction).
    Returns (output, gain_reduction_db)."""
    x = np.asarray(x, dtype=np.float64)
    sc = x if sidechain is None else np.asarray(sidechain, dtype=np.float64)
    p = sc * sc if sc.ndim == 1 else np.mean(sc * sc, axis=0)
    a = math.exp(-1.0 / max(rms_ms * 1e-3 * sr, 1.0))
    p = signal.lfilter([1.0 - a], [1.0, -a], p)
    level = 10.0 * np.log10(np.maximum(p, 1e-14)) + 3.0103  # RMS of a full-scale sine reads 0 dB
    att = math.exp(-1.0 / max(attack_ms * 1e-3 * sr, 1.0))
    rel = math.exp(-1.0 / max(release_ms * 1e-3 * sr, 1.0))
    gr = _gain_computer(np.ascontiguousarray(level), thresh_db, ratio, knee_db, att, rel)
    g = undb(makeup_db - gr)
    return x * g, gr


@njit(cache=True)
def _release(h, rel):
    n = h.shape[0]
    r = np.empty(n)
    s = h[0]
    for i in range(n):
        s = 1.0 - (1.0 - s) * rel  # recover towards unity
        if h[i] < s:
            s = h[i]  # instant attack (the look-ahead window has already started the ramp)
        r[i] = s
    return r


def true_peak(x, os=4):
    """Linear true peak (max |x| after os-times polyphase oversampling)."""
    x2 = np.atleast_2d(np.asarray(x, dtype=np.float64))
    up = signal.resample_poly(x2, os, 1, axis=-1)
    return float(max(np.abs(up).max(), np.abs(x2).max()))


def true_peak_db(x, os=4):
    return float(todb(true_peak(x, os)))


def limit(x, ceiling_db=-1.0, lookahead_ms=5.0, release_ms=120.0, sr=SR, os=4):
    """True-peak look-ahead limiter. Gain = min over a look-ahead window of ceiling / true-peak, recovered with an
    exponential release, then box-smoothed over the window, so the gain always reaches its target before the peak.
    Returns (output, gain)."""
    x2 = np.atleast_2d(np.asarray(x, dtype=np.float64))
    n = x2.shape[1]
    up = signal.resample_poly(x2, os, 1, axis=-1)[:, : n * os]
    if up.shape[1] < n * os:
        up = np.pad(up, ((0, 0), (0, n * os - up.shape[1])))
    pk = np.abs(up).max(axis=0).reshape(n, os).max(axis=1)
    pk = np.maximum(pk, np.abs(x2).max(axis=0))
    greq = np.minimum(1.0, undb(ceiling_db) / np.maximum(pk, 1e-12))
    L = max(2, int(lookahead_ms * 1e-3 * sr))
    # forward-looking minimum over [i, i + L - 1]
    padded = np.concatenate([greq, np.ones(L)])
    h = minimum_filter1d(padded, size=L, origin=-(L // 2), mode="nearest")[:n]
    r = _release(np.ascontiguousarray(h), math.exp(-1.0 / (release_ms * 1e-3 * sr)))
    s = np.convolve(np.concatenate([np.full(L - 1, r[0]), r]), np.ones(L) / L, mode="valid")
    y = x2 * s[None, :]
    tp = true_peak(y, os)
    lim = undb(ceiling_db)
    if tp > lim:  # interpolation residue: trim statically
        y *= lim / tp
    y = y[0] if np.asarray(x).ndim == 1 else y
    return y, s


def soft_clip(x, drive=1.0):
    """Gentle tanh saturation normalised so small signals pass at unity gain."""
    return np.tanh(drive * x) / drive


# ----------------------------------------------------------------------------------------------- loudness
_K1 = (np.array([1.53512485958697, -2.69169618940638, 1.19839281085285]),
       np.array([1.0, -1.69065929318241, 0.73248077421585]))
_K2 = (np.array([1.0, -2.0, 1.0]), np.array([1.0, -1.99004745483398, 0.99007225036621]))


def k_weight(x, sr=SR):
    x = np.atleast_2d(np.asarray(x, dtype=np.float64))
    if sr != 48000:
        g = math.gcd(int(sr), 48000)
        x = signal.resample_poly(x, 48000 // g, int(sr) // g, axis=-1)
    y = signal.lfilter(_K1[0], _K1[1], x, axis=-1)
    return signal.lfilter(_K2[0], _K2[1], y, axis=-1)


def _block_power(y, win, hop):
    """Sum over channels of the mean square in windows of `win` samples every `hop` samples."""
    c = np.concatenate([np.zeros((y.shape[0], 1)), np.cumsum(y * y, axis=1)], axis=1)
    n = y.shape[1]
    if n < win:
        return np.array([np.sum(c[:, -1]) / max(win, 1)])
    starts = np.arange(0, n - win + 1, hop)
    return np.sum(c[:, starts + win] - c[:, starts], axis=0) / win


def block_loudness(x, sr=SR, block=0.4, hop=0.1):
    """Momentary-style loudness per block (LUFS), K-weighted, ungated. Returns (block_start_times, lufs)."""
    y = k_weight(x, sr)
    win, hp = int(block * 48000), int(hop * 48000)
    p = _block_power(y, win, hp)
    return np.arange(len(p)) * hop, -0.691 + 10.0 * np.log10(np.maximum(p, 1e-15))


def integrated_lufs(x, sr=SR):
    """BS.1770-4 integrated loudness (gated). -inf-ish (-120) for silence."""
    y = k_weight(x, sr)
    p = _block_power(y, int(0.4 * 48000), int(0.1 * 48000))
    lk = -0.691 + 10.0 * np.log10(np.maximum(p, 1e-15))
    keep = lk > -70.0
    if not np.any(keep):
        return -120.0
    rel = -0.691 + 10.0 * np.log10(np.mean(p[keep])) - 10.0
    keep &= lk > rel
    if not np.any(keep):
        return -120.0
    return float(-0.691 + 10.0 * np.log10(np.mean(p[keep])))


def short_term(x, sr=SR, hop=0.1):
    """Short-term loudness (3 s windows) every hop seconds -> (window_end_times, lufs)."""
    y = k_weight(x, sr)
    win, hp = int(3.0 * 48000), int(hop * 48000)
    p = _block_power(y, win, hp)
    return 3.0 + np.arange(len(p)) * hop, -0.691 + 10.0 * np.log10(np.maximum(p, 1e-15))


def loudness_range(x, sr=SR):
    """EBU Tech 3342 LRA (LU): 10th..95th percentile of gated short-term loudness."""
    _, st = short_term(x, sr, hop=0.1)
    st = st[st > -70.0]
    if len(st) == 0:
        return 0.0
    rel = -0.691 + 10 * np.log10(np.mean(10 ** ((st + 0.691) / 10))) - 20.0
    st = st[st > rel]
    return float(np.percentile(st, 95) - np.percentile(st, 10)) if len(st) else 0.0


def ffmpeg_ebur128(path):
    """Cross-check with ffmpeg's own EBU R128 meter: returns dict(I, LRA, TP)."""
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    tail = out[out.rfind("Summary:"):]
    res = {}
    for line in tail.splitlines():
        s = line.strip()
        if s.startswith("I:"):
            res["I"] = float(s.split()[1])
        elif s.startswith("LRA:"):
            res["LRA"] = float(s.split()[1])
        elif s.startswith("Peak:"):
            res["TP"] = float(s.split()[1])
    return res


def normalize_loudness(x, target_lufs, ceiling_db=-1.0, sr=SR, iters=4, release_ms=120.0):
    """Gain to target integrated loudness, then true-peak limit to ceiling; repeat so the limiter's loss is made
    up. Returns (y, lufs, true_peak_db)."""
    y = np.asarray(x, dtype=np.float64)
    for _ in range(iters):
        cur = integrated_lufs(y, sr)
        y = y * undb(target_lufs - cur)
        y, _ = limit(y, ceiling_db, release_ms=release_ms, sr=sr)
        if abs(integrated_lufs(y, sr) - target_lufs) < 0.05:
            break
    return y, integrated_lufs(y, sr), true_peak_db(y)


def section_loudness(x, bounds, sr=SR):
    """[(name, t0, t1)] -> [(name, t0, t1, integrated LUFS within the window, peak short-term LUFS)]."""
    out = []
    xs = np.atleast_2d(x)
    for name, t0, t1 in bounds:
        seg = xs[:, int(t0 * sr): int(t1 * sr)]
        if seg.shape[1] < int(0.5 * sr):
            out.append((name, t0, t1, float("nan"), float("nan")))
            continue
        _, bl = block_loudness(seg, sr)
        out.append((name, t0, t1, integrated_lufs(seg, sr), float(np.max(bl))))
    return out


# ----------------------------------------------------------------------------------------------- analysis
def band_energy_db(x, bands, sr=SR):
    """Long-term energy per band (dB, relative to total) from a Welch PSD."""
    mono = np.atleast_2d(x).mean(axis=0)
    f, p = signal.welch(mono, fs=sr, nperseg=8192)
    tot = np.sum(p) + 1e-20
    return {f"{lo}-{hi}": float(10 * np.log10(np.sum(p[(f >= lo) & (f < hi)]) / tot + 1e-20)) for lo, hi in bands}


def spectrogram_png(x, path, title, sr=SR, marks=None, vlines=None, fmin=30.0, fmax=20000.0, dyn=100.0):
    """Spectrogram (log frequency) + level lanes (sample-peak envelope, short-term LUFS, momentary LUFS) -> PNG.
    marks: [(t, label)] drawn as section lines; vlines: extra thin lines (e.g. cue times)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    xs = np.atleast_2d(np.asarray(x, dtype=np.float64))
    mono = xs.mean(axis=0)
    dur = len(mono) / sr
    f, t, S = signal.spectrogram(mono, fs=sr, window="hann", nperseg=4096, noverlap=4096 - 1024, scaling="spectrum")
    Sdb = 10 * np.log10(S + 1e-20) + 3.0  # full-scale sine ~ 0 dB
    rows = np.geomspace(fmin, fmax, 480)
    img = np.empty((len(rows), Sdb.shape[1]))
    for j in range(Sdb.shape[1]):
        img[:, j] = np.interp(rows, f, Sdb[:, j])
    fig, (a0, a1) = plt.subplots(2, 1, figsize=(18, 9), gridspec_kw={"height_ratios": [3, 1.2]}, sharex=True)
    top = max(-6.0, float(np.percentile(img, 99.9)))
    im = a0.imshow(img, origin="lower", aspect="auto", cmap="magma", vmin=top - dyn, vmax=top,
                   extent=[t[0], t[-1], 0, len(rows)])
    ticks = [50, 100, 200, 500, 1000, 2000, 4000, 6000, 10000, 16000]
    a0.set_yticks([np.argmin(np.abs(rows - v)) for v in ticks])
    a0.set_yticklabels([f"{v // 1000}k" if v >= 1000 else str(v) for v in ticks])
    for v, c in ((200, "#7fd1ff"), (2000, "#ffd27f"), (6000, "#ffd27f")):
        a0.axhline(np.argmin(np.abs(rows - v)), color=c, lw=0.6, ls=":")
    a0.set_ylabel("Hz")
    a0.set_title(title)
    fig.colorbar(im, ax=a0, pad=0.005, fraction=0.02, label="dB")
    # level lanes
    hop = int(0.01 * sr)
    m = len(mono) // hop
    pk = np.abs(xs[:, : m * hop]).max(axis=0).reshape(m, hop).max(axis=1)
    a1.plot(np.arange(m) * 0.01, todb(pk), color="#888", lw=0.5, label="sample peak dBFS")
    ts, st = short_term(xs, sr)
    a1.plot(ts, st, color="#6e4bff", lw=1.4, label="short-term LUFS (3 s)")
    tb, mb = block_loudness(xs, sr)
    a1.plot(tb + 0.4, mb, color="#ff5a6e", lw=0.5, alpha=0.6, label="momentary LUFS (0.4 s)")
    a1.axhline(-1.0, color="k", lw=0.6, ls="--")
    a1.set_ylim(-60, 3)
    a1.set_xlim(0, dur)
    a1.set_ylabel("dB / LUFS")
    a1.set_xlabel("seconds")
    a1.grid(alpha=0.25)
    a1.legend(loc="lower left", fontsize=7, ncol=3)
    for tv in vlines or []:
        a0.axvline(tv, color="#9d86ff", lw=0.4, alpha=0.7)
    for tv, lab in marks or []:
        for ax in (a0, a1):
            ax.axvline(tv, color="w" if ax is a0 else "k", lw=0.8, alpha=0.8)
        a0.text(tv + 0.2, len(rows) - 18, lab, color="w", fontsize=8, va="top")
    fig.tight_layout()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(path), dpi=100)
    plt.close(fig)
