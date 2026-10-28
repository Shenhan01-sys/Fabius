"""Final mix for the Fabius pitch video v2: voice + music stems + SFX cues -> public/audio/mix_v2.wav + mix_v2.mp3.

    python -X utf8 -P analysis/music_v2.py && python -X utf8 -P analysis/mix_v2.py --png
    python -X utf8 -P analysis/mix_v2.py --cues out/audio/cues-demo.json --voice some.wav --out out/audio/test

Inputs: public/audio/voiceover.wav (else a 96 s silent placeholder is written to out/audio/ and used),
out/audio/music_v2_{drums,bass,harmony,motif,fx}.wav (run music_v2.py first), public/data/cues.json (else a demo
sheet is written to out/audio/cues-demo.json and used):

    {"duration": 93.746, "bpm": 120,
     "sections": [{"name": "intro", "start": 0.0}, {"name": "reveal", "start": 7.472, "land": 9.46}, ...],
     "sfx": [{"t": 10.955, "name": "glass_seal", "gain_db": -5, "pan": 0.0}, ...]}

  sfx[].t       the picture / word moment. The file's sync point (its 'anchor' in public/audio/sfx2/manifest.json:
                whoosh = peak, riser = end, chime = onset, glass_seal = the chime at 0.60 s) lands on t.
                Optional per cue: "align": "start" (file starts at t instead), "rate" (playback rate, e.g. 0.97),
                "length" (seconds, then a 30 ms fade). A cue that would start before 0 s is moved to 0 (reported).
  sfx[].name    'glass_seal' -> public/audio/sfx2/glass_seal.wav, 'remotion/whoosh' -> sfx2/remotion/whoosh.wav.
                Only whitelisted, SHA-256-pinned files are mixed (analysis/check_sfx.py); anything else stops the mix.
  sections      music only (music_v2.py); also used here for the per-section loudness report.

Chain:
  voice   high-pass 80 Hz -> split-band de-esser (when the 5-9 kHz band carries more than ~1/8 of a 2 ms frame,
          the band above 4.5 kHz is lowered, up to 6 dB) -> compressor 2.5:1 (6 / 120 ms) -> gentle air exciter
          (harmonics of the 3-7 kHz band, high-passed at 9.5 kHz: the neural TTS stops at ~11 kHz) -> -16 LUFS
  music   stems summed -> -18 LUFS -> ducked up to -9 dB under the voice (envelope follower ~80 ms attack /
          ~450 ms release, 350 ms hold so it does not pump between words, 60 ms look-ahead) + a -2.5 dB dynamic
          dip at 2.8 kHz while the voice speaks
  sfx     ducked up to -3 dB under the voice (same follower)
  master  -14 LUFS integrated (BS.1770-4 gating, numpy; cross-checked with ffmpeg ebur128) -> true-peak
          look-ahead limiter at -1.2 dBTP; the 320 kbps MP3 is decoded and re-measured and the level trimmed
          until its true peak is <= -1.0 dBTP too.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402

from check_sfx import BANNED, WHITELIST, rel, resolve_cue, sha256  # noqa: E402
from dsp_v2 import (ROOT, SR, add_at, as_stereo, balance, biquad, block_loudness, butter, compress, fade,  # noqa: E402
                    ffmpeg_ebur128, follow, hold_max, integrated_lufs, limit, loudness_range, pan_mono,
                    read_audio, resample_rate, section_loudness, short_term, spectrogram_png, todb,
                    true_peak_db, undb, write_wav)

OUT = ROOT / "out" / "audio"
AUDIO = ROOT / "public" / "audio"
CUES = ROOT / "public" / "data" / "cues.json"
STEMS = ("drums", "bass", "harmony", "motif", "fx")
VOICE_LUFS = -16.0
MUSIC_LUFS = -18.0
MUSIC_DUCK_DB = 9.0
SFX_DUCK_DB = 3.0
TARGET_LUFS = -14.0
CEILING = -1.2


# ---------------------------------------------------------------------------------------------------- inputs
def placeholder_voice(dur=96.0):
    p = OUT / "voiceover_placeholder.wav"
    if not p.exists():
        write_wav(p, np.zeros(int(dur * SR)))
    return p


def demo_cues():
    """Used only when public/data/cues.json does not exist: the brief's default layout + a handful of cues."""
    d = {"duration": 96.0, "bpm": 120,
         "sections": [{"name": n, "start": t} for n, t in (("intro", 0), ("reveal", 8), ("grooveA", 9), ("lift", 38),
                                                            ("grooveB", 40), ("breakdown", 66), ("final", 75),
                                                            ("outro", 88))],
         "sfx": [{"t": 0.6, "name": "whoosh_long", "gain_db": -12, "pan": 0.0, "align": "start"},
                 {"t": 8.0, "name": "glass_seal", "gain_db": -9, "pan": 0.0},
                 {"t": 8.0, "name": "reveal_bloom", "gain_db": -12, "pan": 0.0},
                 {"t": 15.0, "name": "ui_click_a", "gain_db": -6, "pan": 0.2},
                 {"t": 20.0, "name": "lock_click", "gain_db": -5, "pan": 0.0},
                 {"t": 38.0, "name": "riser_2s", "gain_db": -15, "pan": 0.0},
                 {"t": 53.0, "name": "notify", "gain_db": -14, "pan": 0.0},
                 {"t": 59.0, "name": "coin", "gain_db": -15, "pan": 0.0},
                 {"t": 66.0, "name": "downlifter", "gain_db": -14, "pan": 0.0},
                 {"t": 70.0, "name": "success", "gain_db": -15, "pan": 0.0},
                 {"t": 88.0, "name": "reveal_bloom", "gain_db": -10, "pan": 0.0}]}
    p = OUT / "cues-demo.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=1), encoding="utf-8")
    return p


def anchors():
    a = {}
    man = AUDIO / "sfx2" / "manifest.json"
    if man.exists():
        m = json.loads(man.read_text(encoding="utf-8"))
        for name, i in m.get("sounds", {}).items():
            a[f"sfx2/{i['file']}"] = float(i.get("anchor", 0.0))
        for f, i in m.get("remotion", {}).get("kept", {}).items():
            a[f"sfx2/remotion/{f}"] = float(i.get("anchor", 0.0))
    return a


# ---------------------------------------------------------------------------------------------------- voice
def voice_chain(v):
    v = butter(v, "highpass", 80.0, 2)
    # split-band de-esser: share of the 5-9 kHz band in 2 ms frames drives a cut on everything above 4.5 kHz
    low = butter(v, "lowpass", 4500.0, 4, zero_phase=True)
    high = v - low
    k = int(0.002 * SR)
    ker = np.ones(k) / k
    e = np.convolve(v * v, ker, mode="same") + 1e-12
    es = np.convolve(butter(v, "bandpass", [5000.0, 9000.0], 4) ** 2, ker, mode="same")
    share_db = 10 * np.log10(es / e + 1e-12)
    red = np.clip((share_db + 9.0) * 0.9, 0.0, 6.0)  # at most 6 dB: tames the TTS 's' without a lisp
    red = follow(red, 1.0, 45.0)
    v = low + high * undb(-red)
    v, gr = compress(v, thresh_db=-18.0, ratio=2.5, attack_ms=6.0, release_ms=120.0, knee_db=6.0)
    # air: odd harmonics of the 3-7 kHz band, keep only what lands above 9.5 kHz, 14 dB under the 6-9 kHz band
    band = butter(v, "bandpass", [3000.0, 7000.0], 2)
    pk = np.percentile(np.abs(band), 99.5) + 1e-9
    exc = butter(np.tanh(2.5 * band / pk) * pk, "highpass", 9500.0, 4)
    ref = np.sqrt(np.mean(butter(v, "bandpass", [6000.0, 9000.0], 4) ** 2)) + 1e-12
    exc *= undb(-14.0) * ref / (np.sqrt(np.mean(exc ** 2)) + 1e-12)
    v = v + exc
    v = v * undb(VOICE_LUFS - integrated_lufs(v))
    return v, float(np.max(red)), float(np.max(gr))


def presence(v):
    """0..1 'the voice is speaking' curve: 10 ms RMS mapped from 22 dB below the median speech level (0) to 10 dB
    below it (1), held 350 ms, advanced 60 ms (look-ahead)."""
    k = int(0.010 * SR)
    lv = 10 * np.log10(np.convolve(v * v, np.ones(k) / k, mode="same") + 1e-14)
    act = lv > lv.max() - 45
    med = np.median(lv[act]) if act.any() else -30.0
    p = np.clip((lv - (med - 22.0)) / 12.0, 0.0, 1.0)
    p = hold_max(p, 0.35)
    la = int(0.060 * SR)
    return np.concatenate([p[la:], np.full(la, p[-1])]), med


# ---------------------------------------------------------------------------------------------------- mix
def load_music(n):
    xs = []
    for k in STEMS:
        p = OUT / f"music_v2_{k}.wav"
        if not p.exists():
            raise SystemExit(f"missing {p.relative_to(ROOT)} - run analysis/music_v2.py first")
        x = as_stereo(read_audio(p))
        xs.append(np.pad(x, ((0, 0), (0, max(0, n - x.shape[1]))))[:, :n])
    return sum(xs)


def place_sfx(cues, n, guard=True):
    bus = np.zeros((2, n))
    anc = anchors()
    cache, notes, rows = {}, [], []
    for c in cues:
        name = str(c["name"])
        p = resolve_cue(name)
        if guard:
            if BANNED.search(name):
                raise SystemExit(f"cue '{name}' at {c['t']}: banned name (client rule)")
            if not p.exists():
                raise SystemExit(f"cue '{name}' at {c['t']}: missing file {p}")
            r_ = rel(p)
            if r_ not in WHITELIST or WHITELIST[r_][0] != sha256(p):
                raise SystemExit(f"cue '{name}' at {c['t']}: {r_} is not whitelisted / pinned in check_sfx.py "
                                 f"(review it, or run with --no-guard for a private test)")
        key = str(p)
        if key not in cache:
            cache[key] = read_audio(p)
        x = cache[key]
        rate = float(c.get("rate", 1.0))
        x = resample_rate(x, rate)
        if c.get("length"):
            x = fade(x[..., : int(float(c["length"]) * SR)], 0.0, 0.03)
        pan = float(c.get("pan", 0.0))
        st = pan_mono(x, pan) if x.ndim == 1 else balance(x, pan)
        st = st * undb(float(c.get("gain_db", 0.0)))
        a = anc.get(rel(p), 0.0) / rate
        t = float(c["t"])
        start = t if c.get("align") == "start" else t - a
        if start < 0:
            notes.append(f"{name} at t={t:.3f}: would start at {start:.3f}s, moved to 0.000 (sync point now at {a:.3f})")
            start = 0.0
        add_at(bus, st, start)
        rows.append(dict(t=t, name=name, start=round(start, 3), gain_db=float(c.get("gain_db", 0.0)), sig=st,
                         i0=int(start * SR)))
    return bus, rows, notes


def mp3_true_peak(path):
    return ffmpeg_ebur128(path).get("TP", 99.0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cues", help="cue sheet (default public/data/cues.json, else a demo sheet)")
    ap.add_argument("--voice", help="voice file (default public/audio/voiceover.wav, else a silent placeholder)")
    ap.add_argument("--out", default=str(AUDIO / "mix_v2"), help="output path without extension")
    ap.add_argument("--png", action="store_true", help="write out/audio/mix_v2_spectrogram.png")
    ap.add_argument("--no-guard", action="store_true", help="mix cues even if not whitelisted (private tests only)")
    a = ap.parse_args()

    cp = Path(a.cues) if a.cues else (CUES if CUES.exists() else demo_cues())
    sheet = json.loads(cp.read_text(encoding="utf-8"))
    vp = Path(a.voice) if a.voice else (AUDIO / "voiceover.wav" if (AUDIO / "voiceover.wav").exists()
                                        else placeholder_voice())
    print(f"cues  {cp}\nvoice {vp}")
    v = read_audio(vp, mono=True)
    dur = float(sheet.get("duration") or len(v) / SR)
    n = int(round(dur * SR))
    v = np.pad(v, (0, max(0, n - len(v))))[:n]
    silent = np.abs(v).max() < 1e-6

    # voice
    if silent:
        vproc, deess, vgr, p, med = v, 0.0, 0.0, np.zeros(n), -99.0
        print("voice: silent placeholder - no ducking")
    else:
        vproc, deess, vgr = voice_chain(v)
        p, med = presence(vproc)
        print(f"voice: de-ess max {deess:.1f} dB, compressor max GR {vgr:.1f} dB, median speech level "
              f"{med:.1f} dBFS (10 ms RMS) -> {integrated_lufs(vproc):.1f} LUFS")
    # ducking curve (dB of reduction for the music; SFX get a third of it)
    duck = follow(MUSIC_DUCK_DB * p, 80.0, 450.0)
    g_music = undb(-duck)
    g_sfx = undb(-duck * SFX_DUCK_DB / MUSIC_DUCK_DB)

    # music
    music = load_music(n)
    music *= undb(MUSIC_LUFS - integrated_lufs(music))
    dip = biquad(music, "peak", 2800.0, 1.0, -2.5)
    music = music + (dip - music) * (duck / MUSIC_DUCK_DB)[None, :]
    music *= g_music[None, :]

    # sfx
    cues = sheet.get("sfx", [])
    sfx, rows, notes = place_sfx(cues, n, guard=not a.no_guard)
    sfx *= g_sfx[None, :]
    for s in notes:
        print("note:", s)

    mix = as_stereo(vproc) + music + sfx
    # master: loudness to -14 LUFS with a true-peak limiter, then make sure the MP3 holds -1 dBTP as well
    pre = integrated_lufs(mix)
    trim = 0.0
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    for it in range(4):
        y = mix * undb(TARGET_LUFS - pre)
        for _ in range(3):
            y, _g = limit(y, CEILING - trim, lookahead_ms=5.0, release_ms=150.0)
            cur = integrated_lufs(y)
            if abs(cur - TARGET_LUFS) < 0.05:
                break
            y = y * undb(TARGET_LUFS - cur)
        y, _g = limit(y, CEILING - trim, lookahead_ms=5.0, release_ms=150.0)
        y = fade(y, 0.005, 0.05)
        write_wav(out.with_suffix(".wav"), y)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out.with_suffix(".wav")), "-c:a", "libmp3lame",
                        "-b:a", "320k", "-ar", str(SR), str(out.with_suffix(".mp3"))], check=True)
        tp_mp3 = mp3_true_peak(out.with_suffix(".mp3"))
        if tp_mp3 <= -1.0:
            break
        trim += tp_mp3 + 1.0 + 0.05
        print(f"  mp3 true peak {tp_mp3:.2f} dBTP > -1.0: lowering the limiter ceiling by {trim:.2f} dB and redoing")
    lufs, tp = integrated_lufs(y), true_peak_db(y)
    ff_wav = ffmpeg_ebur128(out.with_suffix(".wav"))
    ff_mp3 = ffmpeg_ebur128(out.with_suffix(".mp3"))
    print(f"\n{out.with_suffix('.wav').name}: {lufs:.2f} LUFS integrated, true peak {tp:.2f} dBTP, "
          f"LRA {loudness_range(y):.1f} LU   (ffmpeg ebur128: I {ff_wav.get('I')} LUFS, TP {ff_wav.get('TP')} dBTP)")
    print(f"{out.with_suffix('.mp3').name}: ffmpeg ebur128 I {ff_mp3.get('I')} LUFS, TP {ff_mp3.get('TP')} dBTP "
          f"(320 kbps)")

    # report: voice vs music, sections, sfx against the voice
    gain_all = undb(lufs - pre)
    vo_l = integrated_lufs(as_stereo(vproc) * gain_all) if not silent else float("nan")
    mu_l = integrated_lufs(music * gain_all)
    print(f"voice {vo_l:.1f} LUFS, music (ducked) {mu_l:.1f} LUFS, sfx {integrated_lufs(sfx * gain_all):.1f} LUFS "
          f"in the master")
    bounds = []
    secs = sorted(sheet.get("sections", []), key=lambda s: s["start"])
    for i, s in enumerate(secs):
        bounds.append((s["name"], float(s["start"]), float(secs[i + 1]["start"]) if i + 1 < len(secs) else dur))
    for name, s0, s1, il, mx in section_loudness(y, bounds):
        mus = integrated_lufs((music * gain_all)[:, int(s0 * SR): int(s1 * SR)])
        print(f"  {name:8s} {s0:6.2f}-{s1:6.2f}  mix {il:6.1f} LUFS (max momentary {mx:6.1f})   music under it {mus:6.1f}")
    # each cue's loudest 400 ms in the master vs the voice's loudness around it
    tv, vb = block_loudness(as_stereo(vproc) * gain_all) if not silent else (np.array([0.0]), np.array([-99.0]))
    hot = []
    for r in rows:
        sig = r["sig"] * gain_all
        seg_g = g_sfx[r["i0"]: r["i0"] + sig.shape[1]]
        sig = sig[:, : len(seg_g)] * seg_g[None, :]
        if sig.shape[1] < int(0.4 * SR):
            sig = np.pad(sig, ((0, 0), (0, int(0.4 * SR) - sig.shape[1])))
        _, mb = block_loudness(sig)
        m = float(np.max(mb))
        near = (tv >= r["t"] - 1.5) & (tv <= r["t"] + 1.0)
        vref = float(np.max(vb[near])) if near.any() else -99.0
        r["mmax"], r["vref"] = m, vref
        if vref > -60 and m > vref - 4.0:
            hot.append(r)
    if hot:
        print("cues within 4 dB of the voice around them (momentary max in the master; consider lowering):")
        for r in hot:
            print(f"  t={r['t']:7.3f} {r['name']:14s} gain {r['gain_db']:+5.1f} dB -> {r['mmax']:6.1f} LUFS vs voice "
                  f"{r['vref']:6.1f}  (suggest {r['gain_db'] - (r['mmax'] - (r['vref'] - 6.0)):+.0f} dB)")
    rep = dict(cues=str(cp), voice=str(vp), lufs=round(lufs, 2), true_peak_dbtp=round(tp, 2),
               ffmpeg_wav=ff_wav, ffmpeg_mp3=ff_mp3, lra=round(loudness_range(y), 1), voice_lufs=round(vo_l, 1),
               music_lufs=round(mu_l, 1), notes=notes,
               hot_cues=[dict(t=r["t"], name=r["name"], gain_db=r["gain_db"], mmax=round(r["mmax"], 1),
                              voice=round(r["vref"], 1)) for r in hot])
    (OUT / f"{out.name}_report.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    if a.png:
        png = OUT / f"{out.name}_spectrogram.png"
        spectrogram_png(y, png, f"{out.with_suffix('.wav').name} - {lufs:.1f} LUFS, TP {tp:.1f} dBTP",
                        marks=[(s0, nm) for nm, s0, _ in bounds], vlines=[float(c["t"]) for c in cues])
        # a second picture: the ducking at work (voice, music gain)
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(18, 4))
        hop = int(0.01 * SR)
        m_ = n // hop
        ax.plot(np.arange(m_) * 0.01, todb(np.abs(vproc[: m_ * hop]).reshape(m_, hop).max(axis=1) * gain_all),
                color="#6e4bff", lw=0.4, label="voice peak (dBFS, master)")
        ax.plot(np.arange(n)[::hop] / SR, -duck[::hop], color="#ff5a6e", lw=1.2, label="music ducking (dB)")
        ts, stm = short_term(music * gain_all)
        ax.plot(ts, stm, color="#15122b", lw=1.0, label="music short-term LUFS (master)")
        ax.set_ylim(-60, 3)
        ax.set_xlim(0, dur)
        ax.grid(alpha=0.3)
        ax.legend(loc="lower left", fontsize=8)
        for nm, s0, _ in bounds:
            ax.axvline(s0, color="k", lw=0.6)
            ax.text(s0 + 0.2, 1, nm, fontsize=8)
        fig.tight_layout()
        fig.savefig(str(OUT / f"{out.name}_ducking.png"), dpi=90)
        plt.close(fig)
        print(f"pictures -> {png.relative_to(ROOT)}, out/audio/{out.name}_ducking.png")


if __name__ == "__main__":
    main()
