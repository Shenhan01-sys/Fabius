"""ORIGINAL procedural music bed for the Fabius pitch video v2 - composed and synthesised here, owned outright (no
samples, loops or licences).

    python -X utf8 analysis/music_v2.py              # layout from public/data/cues.json (else the built-in default)
    python -X utf8 analysis/music_v2.py --cues F     # another cue sheet
    python -X utf8 analysis/music_v2.py --png        # + out/audio/music_v2_spectrogram.png

Writes out/audio/music_v2.wav (24-bit, mastered: -15 LUFS integrated, true peak <= -1 dBTP), the stems
out/audio/music_v2_{drums,bass,harmony,motif,fx}.wav (32-bit float, pre-master, same gain as the bed: they sum to
the bed before its 28 Hz high-pass, bus compressor and limiter; mix_v2.py mixes from them) and
out/audio/music_v2_report.json (layout as snapped, per-section loudness, band balance, skipped fx).

Style: warm, optimistic tech-launch bed at 120 BPM, D major / B minor colour. Chords Dmaj9 - Bm11 - Gmaj7#11 - A6sus
(voiced F#3-A4 / B4 / C#5 tops, roots D2 B1 G1 A1), unison PolyBLEP-saw pads with a sine body through a resonant
TPT low-pass, chorus and a synthetic hall; sub bass ducked to a soft four-on-the-floor kick (sidechain-style);
roomy soft clap on 2 and 4, humanised + slightly swung 16th hats; a plucky syncopated arpeggio motif with a
ping-pong delay; a glass-bell motif that answers the 'seal' cues; filtered intro, risers / downlifters where the
cue sheet has none; a real ending (final Dmaj9 + bell figure + hall tail).

Re-timeable: section starts come from cues.json, snapped to the nearest beat of a 120 BPM grid whose phase is
chosen to minimise the snapping error (so the cuts land on beats). Scene names map to musical treatments
(intro / reveal / pulse / groove / groove2 / breakdown / build / sincere / outro, see KIND_OF); a section may also
say {"music": "<treatment>"}. Optional extras a section may carry: "land" (reveal: when the lift lands; default =
the start of its 2nd voice line from public/data/vo.json) and "resolve" (outro: when the final chord lands;
default = its last glass_seal cue, else the last word + 0.3 s).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402

from dsp_v2 import (ROOT, SR, add_at, adsr, automation, band_energy_db, biquad, butter, chorus, compress,  # noqa: E402
                    fade, integrated_lufs, make_ir, midi_hz, noise, normalize_loudness, osc_saw, osc_sine,
                    osc_square, pan_mono, pingpong, section_loudness, spectrogram_png, svf, true_peak_db, undb,
                    write_wav)
from voices_v2 import downlifter, glass_note, grain_cloud, pad_note, ramp_in, riser, sub_swell  # noqa: E402

OUT = ROOT / "out" / "audio"
CUES = ROOT / "public" / "data" / "cues.json"
VO = ROOT / "public" / "data" / "vo.json"
TARGET_LUFS = -15.0

DEFAULT = {  # the voiceover's scene layout (coordinator, 7 Oct) - used only when no cue sheet exists
    "duration": 93.746, "bpm": 120,
    "sections": [{"name": "intro", "start": 0.0}, {"name": "reveal", "start": 7.5}, {"name": "rules", "start": 16.0},
                 {"name": "seal", "start": 24.0}, {"name": "desk", "start": 32.6}, {"name": "use", "start": 48.0},
                 {"name": "verify", "start": 62.1}, {"name": "open", "start": 72.2},
                 {"name": "honest", "start": 78.7}, {"name": "end", "start": 85.7}],
    "accents": [{"t": 28.8, "type": "seal"}],
    "sfx": [],
}

KIND_OF = {"intro": "intro", "hook": "intro", "problem": "intro", "reveal": "reveal", "rules": "pulse",
           "seal": "pulse", "desk": "groove", "use": "groove2", "verify": "breakdown", "open": "build",
           "honest": "sincere", "end": "outro",
           "groovea": "groove", "groove": "groove", "grooveb": "groove2", "groove2": "groove2", "final": "groove2",
           "lift": "build", "build": "build", "breakdown": "breakdown", "bridge": "breakdown", "outro": "outro",
           "ending": "outro", "pulse": "pulse", "sincere": "sincere"}

# chord voicings (MIDI): root = sub bass, pad = sustained voicing, arp = motif tones, bass = pluck bass
CH = {
    "Dmaj9": dict(root=38, pad=[54, 57, 61, 64, 69], arp=[62, 66, 69, 73, 76, 78], bass=50),
    "Bm11": dict(root=35, pad=[54, 57, 62, 64, 71], arp=[59, 62, 66, 69, 71, 76], bass=47),
    "Gmaj7#11": dict(root=31, pad=[54, 59, 62, 66, 73], arp=[62, 66, 67, 71, 73, 78], bass=43),
    "A6sus": dict(root=33, pad=[52, 57, 62, 66, 71], arp=[57, 62, 64, 66, 69, 71], bass=45),
    "FINAL": dict(root=38, pad=[50, 54, 57, 61, 64, 69, 76], arp=[62, 66, 69, 73, 76, 78], bass=50),
}
PROG = {"intro": ["Bm11", "Bm11", "Gmaj7#11", "A6sus"], "main": ["Dmaj9", "Bm11", "Gmaj7#11", "A6sus"],
        "bright": ["Dmaj9", "A6sus", "Bm11", "Gmaj7#11"], "breakdown": ["Bm11", "Gmaj7#11", "Dmaj9", "A6sus"],
        "build": ["Gmaj7#11", "A6sus"], "sincere": ["Bm11", "Gmaj7#11", "Dmaj9", "A6sus"],
        "outro": ["Gmaj7#11", "A6sus"]}
ENDS_ON_A = {"intro", "breakdown", "build", "sincere", "outro"}

# treatment parameters
P = {
    "intro": dict(pad=0.85, att=1.4, cut=(420, 1300), sub=0.0, drone=0.7, kick=0, clap=0, hats=0, ohat=0, shaker=0,
                  arp="pulse", arp_lvl=0.72, bright=0.45, glassy=0, oct=0, bpluck=0, bells=0, prog="intro", bpc=1, air=1),
    "reveal": dict(pad=0.82, att=0.25, cut=(2700, 2900), sub=0.9, drone=0, kick=0.72, clap=0, hats=8, ohat=0,
                   shaker=0.5, arp="main", arp_lvl=0.75, bright=0.8, glassy=0, oct=0, bpluck=0, bells=1, prog="main",
                   bpc=1, air=0.3),
    "pulse": dict(pad=0.68, att=0.3, cut=(2300, 2300), sub=0.85, drone=0, kick=0.62, clap=0, hats=8, ohat=0,
                  shaker=0.5, arp="main", arp_lvl=0.85, bright=1.0, glassy=1, oct=0, bpluck=0, bells=0.6,
                  prog="main", bpc=1, air=0, shine=0),
    "groove": dict(pad=0.78, att=0.2, cut=(2100, 2300), sub=1.0, drone=0, kick=1.0, clap=1.0, hats=16, ohat=0,
                   shaker=0, arp="main", arp_lvl=1.0, bright=0.85, glassy=0, oct=0, bpluck=0.85, bells=0,
                   prog="main", bpc=1, air=0),
    "groove2": dict(pad=1.0, att=0.2, cut=(3500, 3800), sub=1.0, drone=0, kick=1.0, clap=1.0, hats=16, ohat=1.0,
                    shaker=0, arp="main", arp_lvl=1.0, bright=1.1, glassy=0, oct=0.42, bpluck=0.9, bells=1.0,
                    prog="bright", bpc=1, air=0, shine=0.4),
    "breakdown": dict(pad=0.85, att=0.7, cut=(1500, 1900), sub=0.75, drone=0, kick=0, clap=0, hats=0, ohat=0,
                      shaker=0.55, arp="eighths", arp_lvl=0.62, bright=0.6, glassy=0, oct=0, bpluck=0, bells=0.7,
                      prog="breakdown", bpc=2, air=0.8),
    "build": dict(pad=0.85, att=0.3, cut=(1600, 5200), sub=0.85, drone=0, kick="rise", clap=0, hats="roll", ohat=0,
                  shaker=0, arp="main", arp_lvl=0.9, bright=(0.55, 1.2), glassy=0, oct=0, bpluck=0, bells=0,
                  prog="build", bpc=1, air=0),
    "sincere": dict(pad=0.85, att=1.0, cut=(1300, 1300), sub=0.6, drone=0, kick=0, clap=0, hats=0, ohat=0, shaker=0,
                    arp="quarters", arp_lvl=0.62, bright=0.5, glassy=0, oct=0, bpluck=0, bells=0.6, prog="sincere",
                    bpc=1, air=0.7),
    "outro": dict(pad=0.8, att=0.6, cut=(1800, 2400), sub=0.7, drone=0, kick=0, clap=0, hats=0, ohat=0, shaker=0,
                  arp="quarters", arp_lvl=0.42, bright=0.6, glassy=0, oct=0, bpluck=0, bells=1.0, prog="outro",
                  bpc=1, air=0.6),
}
ARP = {
    "main": [(0, 0, 1.0), (2, 2, 0.55), (3, 1, 0.8), (5, 3, 0.5), (6, 2, 0.85), (8, 4, 0.95), (10, 2, 0.5),
             (11, 3, 0.8), (13, 5, 0.55), (14, 4, 0.75)],
    "pulse": [(k, 1, 0.62 if k % 8 == 0 else (0.48 if k % 4 == 0 else 0.34)) for k in range(0, 16, 2)],
    "eighths": [(k, i, 0.6 if k % 4 == 0 else 0.5) for k, i in zip(range(0, 16, 2), [0, 2, 3, 2, 4, 2, 3, 1])],
    "quarters": [(0, 0, 0.65), (4, 2, 0.5), (8, 3, 0.55), (12, 2, 0.45)],
}
GATE = {"main": 0.2, "pulse": 0.12, "eighths": 0.3, "quarters": 0.7}
HAT_ACC = (0.55, 0.3, 0.75, 0.35)
PHRASE = [(0.0, 78, 0.8), (1.5, 81, 0.6), (4.0, 76, 0.75), (6.0, 74, 0.6), (8.0, 78, 0.7), (9.5, 83, 0.55),
          (12.0, 81, 0.75)]  # beats: F#5 A5 | E5 D5 | F#5 B5 | A5  (D major pentatonic: safe over all four chords)
SEAL_FIG = [(0.0, 86, 0.75), (0.5, 81, 0.6), (2.0, 78, 0.35)]   # D6 -> A5 ... F#5: 'closed, settled'
LAND_FIG = [(0.0, 81, 0.6), (0.5, 86, 0.8)]                      # A5 -> D6: 'arrived'
FINAL_FIG = [(0.0, 78, 0.5), (0.5, 81, 0.6), (1.0, 86, 0.8), (3.0, 93, 0.3)]  # F#5 A5 D6 ... A6
TRANSITION_SFX = ("riser", "downlifter", "whoosh_long")

# loudness each instrument is calibrated to (gated integrated LUFS over its own active span, dry, pre-master)
TARGET = dict(kick=-24.0, clap=-30.0, hats=-30.5, shaker=-35.0, sub=-25.0, bpluck=-28.5, pad=-21.0, arp=-23.0,
              bells=-25.0, fx=-25.0, air=-41.0)


# ================================================================================================ layout
@dataclass
class Sec:
    name: str
    kind: str
    t0: float
    t1: float
    land: float | None = None
    resolve: float | None = None
    idx: int = 0


@dataclass
class Layout:
    duration: float
    bpm: float
    beat: float
    offset: float
    sections: list
    seals: list
    sfx: list
    source: str


def load_layout(path=None):
    p = Path(path) if path else (CUES if CUES.exists() else None)
    d = json.loads(p.read_text(encoding="utf-8")) if p and p.exists() else DEFAULT
    src = str(p.relative_to(ROOT)) if p and p.exists() and p.is_relative_to(ROOT) else (str(p) if p else "default")
    vo = json.loads(VO.read_text(encoding="utf-8")) if VO.exists() else None
    dur = float(d.get("duration") or (vo or {}).get("duration") or 93.746)
    bpm = float(d.get("bpm", 120))
    beat = 60.0 / bpm
    raw = sorted(d["sections"], key=lambda s: float(s["start"]))
    sfx = list(d.get("sfx", []))
    seal_t = sorted([float(c["t"]) for c in sfx if "seal" in str(c.get("name", ""))] +
                    [float(a["t"]) for a in d.get("accents", []) if a.get("type") == "seal"])
    lines = (vo or {}).get("lines", [])
    words = [w for ln in lines for w in ln.get("words", [])]
    secs = []
    for i, s in enumerate(raw):
        t0 = float(s["start"])
        t1 = float(raw[i + 1]["start"]) if i + 1 < len(raw) else dur
        name = str(s["name"])
        kind = s.get("music") or KIND_OF.get(name.lower().replace(" ", "").replace("_", "").replace("-", ""), "groove")
        sec = Sec(name, kind, t0, t1)
        if kind == "reveal":
            if "land" in s:
                sec.land = float(s["land"])
            else:
                inside = [ln for ln in lines if t0 - 0.2 <= ln["start"] < t1]
                sec.land = inside[1]["start"] if len(inside) > 1 and inside[1]["start"] - t0 >= 1.0 else t0 + 2 * beat * 4
        if kind == "outro":
            if "resolve" in s:
                sec.resolve = float(s["resolve"])
            else:
                seals_in = [t for t in seal_t if t0 <= t < t1]
                last_w = max([w["end"] for w in words if t0 <= w["start"] < t1], default=None)
                sec.resolve = seals_in[-1] if seals_in else (last_w + 0.3 if last_w else t0 + 3.5)
            sec.resolve = min(sec.resolve, dur - 3.0)
        secs.append(sec)
    # grid phase: minimise weighted squared snapping error of cuts (1), lands / resolves (3), seal accents (0.5)
    pts = [(s.t0, 1.0) for s in secs[1:]] + [(s.land, 3.0) for s in secs if s.land] + \
          [(s.resolve, 3.0) for s in secs if s.resolve] + [(t, 0.5) for t in seal_t]
    offs = np.arange(0.0, beat, 0.005)
    cost = [sum(w * ((t - o) - beat * round((t - o) / beat)) ** 2 for t, w in pts) for o in offs]
    off = float(d.get("grid_offset", offs[int(np.argmin(cost))]))

    def snap(t):
        return off + beat * round((t - off) / beat)

    for i, s in enumerate(secs):
        s.idx = i
        s.t0 = 0.0 if i == 0 else snap(s.t0)
        if s.land:
            s.land = max(snap(s.land), s.t0)
        if s.resolve:
            s.resolve = snap(s.resolve)
    for i, s in enumerate(secs):
        s.t1 = secs[i + 1].t0 if i + 1 < len(secs) else dur
    return Layout(dur, bpm, beat, off, secs, seal_t, sfx, src)


# ================================================================================================ instruments
_cache = {}


def kick_wave():
    if "kick" not in _cache:
        n = int(0.5 * SR)
        t = np.arange(n) / SR
        f = 52.0 + 73.0 * np.exp(-t / 0.032)  # 125 -> 52 Hz pitch drop: round, not clicky
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.2) * ramp_in(n, 0.0015)
        y = np.tanh(1.6 * y) / np.tanh(1.6)
        y = biquad(y, "lowpass", 2500.0, 0.7)
        _cache["kick"] = fade(y / np.abs(y).max(), 0.0, 0.05)
    return _cache["kick"]


def clap_wave(seed):
    key = ("clap", seed % 3)
    if key not in _cache:
        n = int(0.5 * SR)
        t = np.arange(n) / SR
        x = noise(n, "white", 300 + seed % 3)
        env = np.zeros(n)
        for dt, a in ((0.0, 0.55), (0.009, 0.75), (0.018, 1.0)):
            u = t - dt
            m = u >= 0
            env[m] += a * (1 - np.exp(-u[m] / 0.0006)) * np.exp(-u[m] / 0.0035)
        u = t - 0.018
        m = u >= 0
        env[m] += 0.5 * (1 - np.exp(-u[m] / 0.002)) * np.exp(-u[m] / 0.09)
        y = x * env
        y = 0.8 * biquad(y, "bandpass", 1250.0, 0.9) + 0.45 * biquad(y, "bandpass", 2300.0, 1.3)
        y = biquad(biquad(y, "lowpass", 6000.0, 0.7), "highpass", 400.0, 0.7)
        _cache[key] = fade(y / np.abs(y).max(), 0.0, 0.05)
    return _cache[key]


def hat_wave(seed, open_=False, soft=False):
    key = ("hat", seed % 6, open_, soft)
    if key not in _cache:
        n = int((0.25 if open_ else 0.08) * SR)
        t = np.arange(n) / SR
        x = noise(n, "white", 400 + seed % 6)
        x = butter(x, "highpass", 5200.0 if soft else 7000.0, 2)
        x = biquad(x, "peak", 10500.0, 1.0, 3.0)
        tau = 0.075 if open_ else (0.03 if soft else 0.014)
        y = x * ramp_in(n, 0.003 if soft else 0.0006) * np.exp(-t / tau)
        y = biquad(y, "lowpass", 13000.0, 0.7)
        _cache[key] = fade(y / np.abs(y).max(), 0.0, 0.01)
    return _cache[key]


def pluck_wave(f0, vel, gate, bright, seed, glassy=False):
    n = int((gate + 0.45) * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    x = 0.55 * osc_saw(f0 * 2 ** (4 / 1200), n, phase0=rng.random()) \
        + 0.55 * osc_saw(f0 * 2 ** (-4 / 1200), n, phase0=rng.random()) \
        + 0.3 * osc_square(f0 * 0.5, n, phase0=rng.random(), pw=0.42)
    cut = np.minimum(1.4 * f0 + (900.0 + 2600.0 * vel) * bright * np.exp(-t / 0.07), 12000.0)
    y = svf(x, cut, 1.1, "lp")
    y *= adsr(n, 0.002, 0.32, 0.0, 0.12, gate=gate, curve=4.0)
    if glassy:  # a quiet glass partial an octave up: the 'glassy' pulse of rules / seal
        y += 0.22 * glass_note(2 * f0, dur=n / SR, vel=1.0, tau=0.35, bright=0.4, beat_hz=0.0, seed=seed)[:n]
    return vel * y


def sub_wave(f0, dur, att=0.02, rel=0.12):
    n = int((dur + rel) * SR)
    y = osc_sine(f0, n) + 0.38 * osc_sine(2 * f0, n) + 0.08 * osc_sine(3 * f0, n)  # 2nd harmonic: laptops hear it
    return np.tanh(1.3 * y) / 1.3 * adsr(n, att, 0.3, 0.92, rel, gate=dur)


# ================================================================================================ arrangement
class Score:
    def __init__(self):
        self.chords, self.subs, self.kicks, self.claps, self.hats, self.shakers = [], [], [], [], [], []
        self.arps, self.bplucks, self.bells, self.fx, self.cut, self.drone = [], [], [], [], [], []
        self.air = []


def bars_of(a, b, bar):
    out = []
    t = a
    while t < b - 1e-6:
        e = min(t + bar, b)
        if b - e < 0.49 and e < b:  # merge a sliver (< 1 beat) into this bar
            e = b
        out.append((t, e))
        t = e
    return out


def transition_sfx_near(layout, t, win=1.0):
    for c in layout.sfx:
        nm = str(c.get("name", ""))
        if any(k in nm for k in TRANSITION_SFX) and abs(float(c["t"]) - t) <= win:
            return nm
    return None


def arrange(L: Layout, rng):
    S = Score()
    beat, bar, s16 = L.beat, 4 * L.beat, L.beat / 4
    groove_kinds = {"groove", "groove2", "pulse", "reveal"}
    skipped = []
    for si, sec in enumerate(L.sections):
        p = P[sec.kind]
        a, b = sec.t0, sec.t1
        nxt = L.sections[si + 1] if si + 1 < len(L.sections) else None
        # ---------------------------------------------------------------- reveal: build up to the land
        if sec.kind == "reveal" and sec.land and sec.land - a >= 0.75:
            S.chords.append(dict(t0=a, t1=sec.land, ch="A6sus", att=0.6, lvl=0.8, kind="lift"))
            S.subs.append(dict(t0=a, t1=sec.land, root=CH["A6sus"]["root"], lvl=0.5))
            S.cut += [(a, 1400.0), (sec.land - 0.05, 3600.0)]
            k = 0
            t = a
            while t < sec.land - 0.01:  # soft 16th hats, crescendo
                u = (t - a) / (sec.land - a)
                S.hats.append((t, 0.1 + 0.4 * u, False, False))
                t += s16
                k += 1
            near = transition_sfx_near(L, sec.land, 0.6)
            if near:
                skipped.append(f"riser into the reveal land ({near} in the cue sheet)")
            else:
                S.fx.append(dict(t=sec.land, type="riser", dur=min(4.0, sec.land - a), lvl=0.55))
            S.fx.append(dict(t=sec.land, type="sub_swell", lvl=0.45))
            for bt, m, v in LAND_FIG:
                S.bells.append((sec.land + bt * beat, m, v * p["bells"], 0.15))
            a = sec.land
        # ---------------------------------------------------------------- outro: lead-in then the final chord
        end_a = b
        if sec.kind == "outro" and sec.resolve and sec.resolve > a:
            end_a = sec.resolve
        bl = bars_of(a, end_a, bar)
        prog = PROG[p["prog"]]
        names = [prog[(i // p["bpc"]) % len(prog)] for i in range(len(bl))]
        if sec.kind in ENDS_ON_A and names:
            names[-1] = "A6sus"
        # pad filter automation
        c0, c1 = p["cut"]
        if sec.kind == "build":
            S.cut += [(a + 0.05, c0), (end_a - 0.05, c1)]
        elif sec.kind == "intro":
            S.cut += [(a, c0), (end_a - 0.05, c1)]
        else:
            S.cut += [(a + 0.3, c0), (end_a - 0.05, c1)]
        n_bars = len(bl)
        for bi, ((tb, te), chn) in enumerate(zip(bl, names)):
            ch = CH[chn]
            prev = S.chords[-1] if S.chords else None
            same_kind = prev is not None and prev["kind"] == sec.kind
            if prev and prev["ch"] == chn and abs(prev["t1"] - tb) < 1e-6 and (same_kind or bi > 0):
                prev["t1"] = te
                if prev.get("sub") is not None:
                    S.subs[prev["sub"]]["t1"] = te
                elif p["drone"] and bi >= 1:  # the intro's drone enters under a held chord
                    S.subs.append(dict(t0=tb, t1=te, root=ch["root"], lvl=p["drone"] * 0.6))
                    prev["sub"] = len(S.subs) - 1
            else:
                S.chords.append(dict(t0=tb, t1=te, ch=chn, att=p["att"], lvl=p["pad"], kind=sec.kind, sub=None,
                                     shine=p.get("shine", 0)))
                if p["sub"] or (p["drone"] and bi >= 1):
                    S.subs.append(dict(t0=tb, t1=te, root=ch["root"], lvl=p["sub"] or p["drone"] * 0.6))
                    S.chords[-1]["sub"] = len(S.subs) - 1
            u_sec = (tb - a) / max(end_a - a, 1e-6)
            # drums -----------------------------------------------------------------------------------
            last_bar = bi == n_bars - 1
            for k in range(4):
                t = tb + k * beat
                if t >= te - 0.01:
                    break
                kv = p["kick"]
                if kv == "rise":
                    if last_bar and t >= te - 2 * beat - 1e-6:
                        continue  # the build lets go before the pull-back
                    kv = 0.45 + 0.45 * ((t - a) / max(end_a - a, 1e-6))
                if kv:
                    S.kicks.append((t, kv * rng.uniform(0.95, 1.0)))
                if p["clap"] and k in (1, 3):
                    S.claps.append((t + 0.004 + rng.normal(0, 0.002), p["clap"] * rng.uniform(0.85, 1.0)))
            for k in range(16):
                t = tb + k * s16
                if t >= te - 0.01:
                    break
                sw = 0.008 if (k % 2 and sec.kind in groove_kinds) else 0.0
                th = t + sw + float(np.clip(rng.normal(0, 0.0025), -0.006, 0.006))
                hv = p["hats"]
                if hv == 16:
                    S.hats.append((th, HAT_ACC[k % 4] * rng.uniform(0.85, 1.0), False, False))
                elif hv == 8 and k % 4 == 2:
                    S.hats.append((th, 0.6 * rng.uniform(0.85, 1.0), False, False))
                elif hv == "roll":
                    if not (last_bar and t >= te - beat):
                        S.hats.append((th, 0.12 + 0.55 * ((t - a) / max(end_a - a, 1e-6)), False, False))
                if p["ohat"] and k % 4 == 2:
                    S.hats.append((th, 0.33 * p["ohat"] * rng.uniform(0.85, 1.0), True, False))
                if p["shaker"]:
                    S.shakers.append((th, p["shaker"] * (0.42, 0.22, 0.32, 0.22)[k % 4] * rng.uniform(0.8, 1.0)))
            # bass pluck (offbeat 8ths)
            if p["bpluck"]:
                for k in (2, 6, 10, 14):
                    t = tb + k * s16
                    if t < te - 0.01:
                        S.bplucks.append((t, ch["bass"], 0.8 * p["bpluck"] * rng.uniform(0.9, 1.0)))
            # arp motif
            br = p["bright"]
            if isinstance(br, tuple):
                br = br[0] + (br[1] - br[0]) * u_sec
            pat = ARP[p["arp"]]
            for k, ti, v in pat:
                t = tb + k * s16
                if t >= te - 0.01:
                    continue
                if sec.kind == "build" and last_bar and t >= te - beat:
                    continue
                sw = 0.004 if (k % 2 and sec.kind in groove_kinds) else 0.0
                m = ch["arp"][ti]
                vel = v * p["arp_lvl"] * rng.uniform(0.9, 1.0)
                S.arps.append((t + sw, m, vel, GATE[p["arp"]], br, bool(p["glassy"])))
                if p["oct"] and v >= 0.8:
                    S.arps.append((t + sw, m + 12, vel * p["oct"], GATE[p["arp"]], br * 0.8, False))
            # bells
            if p["bells"]:
                if sec.kind == "groove2" and bi % 4 == 0 and n_bars - bi >= 2:
                    S.bells += [(tb + bt * beat, m, v * p["bells"], ((m % 5) - 2) * 0.15) for bt, m, v in PHRASE]
                elif sec.kind == "pulse" and bi == 0:
                    S.bells += [(tb + bt * beat, m, 0.7 * v * p["bells"], ((m % 5) - 2) * 0.15)
                                for bt, m, v in PHRASE[:4]]
                elif sec.kind == "breakdown" and bi == 1:
                    S.bells += [(tb + bt * beat, m, 0.75 * v * p["bells"], ((m % 5) - 2) * 0.15) for bt, m, v in PHRASE]
                elif sec.kind == "sincere" and bi in (0, 2):
                    S.bells.append((tb, (81, 78)[bi // 2], 0.4 * p["bells"], 0.0))
        if p["air"]:
            S.air.append((a, end_a if sec.kind != "outro" else L.duration, p["air"]))
        # ---------------------------------------------------------------- outro final chord
        if sec.kind == "outro" and sec.resolve:
            r = sec.resolve
            S.chords.append(dict(t0=r, t1=L.duration, ch="FINAL", att=0.12, lvl=0.95, kind="final"))
            S.subs.append(dict(t0=r, t1=L.duration, root=CH["FINAL"]["root"], lvl=0.75, final=True))
            S.cut += [(r, 2600.0), (r + 0.6, 3200.0), (L.duration, 1100.0)]
            for (bt, m, v), pan in zip(FINAL_FIG, (-0.2, 0.0, 0.15, 0.3)):
                S.bells.append((r + bt * beat, m, v, pan))
            S.fx.append(dict(t=r, type="sub_swell", lvl=0.5))
            S.fx.append(dict(t=r + 0.1, type="shimmer", lvl=0.35))
        # ---------------------------------------------------------------- transitions into the next section
        if nxt is not None:
            nb = nxt.t0
            near = transition_sfx_near(L, nb, 1.0)
            if nxt.kind == "groove2" and sec.kind != "groove2":
                if near:
                    skipped.append(f"riser into {nxt.name} ({near} in the cue sheet)")
                else:
                    S.fx.append(dict(t=nb, type="riser", dur=2.0, lvl=0.6))
            if nxt.kind == "breakdown":
                if near:
                    skipped.append(f"downlifter into {nxt.name} ({near} in the cue sheet)")
                else:
                    S.fx.append(dict(t=nb, type="downlifter", lvl=0.6))
        if sec.kind == "build":
            S.fx.append(dict(t=b, type="riser", dur=min(6.5, b - sec.t0), lvl=0.75))
    # seal answers (bell figure a little after each seal cue, never on top of a land / the final chord)
    lands = [s.land for s in L.sections if s.land] + [s.resolve for s in L.sections if s.resolve]
    eighth = beat / 2
    for t in L.seals:
        if any(abs(t - x) < 0.8 for x in lands):
            continue
        tt = L.offset + eighth * math.ceil((t + 0.3 - L.offset) / eighth)
        S.bells += [(tt + bt * beat, m, v, -0.1) for bt, m, v in SEAL_FIG]
    return S, skipped


# ================================================================================================ render
def place_mono(bus, x, t, pan=0.0, gain=1.0):
    add_at(bus, pan_mono(x * gain, pan), t)


def render(L: Layout, seed=7, verbose=True):
    rng = np.random.default_rng(seed)
    S, skipped = arrange(L, rng)
    n = int(round(L.duration * SR))
    N = n + int(4.0 * SR)
    I = {k: np.zeros((2, N)) for k in ("kick", "clap", "hats", "shaker", "sub", "bpluck", "pad", "arp", "bells",
                                        "fx", "air")}
    t_start = time.time()
    # drums
    for t, v in S.kicks:
        place_mono(I["kick"], kick_wave(), t, 0.0, v)
    for i, (t, v) in enumerate(S.claps):
        place_mono(I["clap"], clap_wave(i), t, (-0.08, 0.08)[i % 2], v)
    for i, (t, v, op, soft) in enumerate(S.hats):
        place_mono(I["hats"], hat_wave(i, op, soft), t, 0.22 if not op else -0.18, v)
    for i, (t, v) in enumerate(S.shakers):
        place_mono(I["shaker"], hat_wave(i + 3, False, True), t, -0.3, v)
    # sub bass (legato chord roots)
    for sp in S.subs:
        f = float(midi_hz(sp["root"]))
        rel = 2.4 if sp.get("final") else 0.12
        dur = sp["t1"] - sp["t0"] - (rel if sp.get("final") else 0.0) + (0.03 if not sp.get("final") else 0.0)
        w = sub_wave(f, max(dur, 0.1), 0.02, rel)
        place_mono(I["sub"], w, sp["t0"], 0.0, sp["lvl"] * min(1.0, (f / 62.0) ** 0.8))  # G1 / A1 a touch lower
    for i, (t, m, v) in enumerate(S.bplucks):
        f = float(midi_hz(m))
        nn = int(0.45 * SR)
        tt = np.arange(nn) / SR
        x = 0.7 * osc_saw(f, nn, phase0=0.1 * i % 1) + 0.5 * osc_square(f * 0.5, nn, pw=0.45)
        y = svf(x, 1.2 * f + 700.0 * np.exp(-tt / 0.05), 0.9, "lp") * adsr(nn, 0.003, 0.18, 0.0, 0.08, gate=0.16)
        place_mono(I["bpluck"], y, t, 0.0, v)
    # pad chords
    for ci, c in enumerate(S.chords):
        final = c["kind"] == "final"
        rel = 2.6 if final else 1.0
        dur = c["t1"] - c["t0"] - (rel + 0.25 if final else 0.0)
        voicing = list(CH[c["ch"]]["pad"])
        notes = [(m, 1.0) for m in voicing] + [(m + 12, c.get("shine", 0)) for m in voicing[-2:] if c.get("shine")]
        for k, (m, lv) in enumerate(notes):
            w = pad_note(float(midi_hz(m)), max(dur, 0.2), attack=c["att"], decay=1.4, sustain=0.82, release=rel,
                         voices=5, spread=11.0, seed=1000 * ci + k, sine_mix=0.4)
            add_at(I["pad"], w * c["lvl"] * lv * (0.85 if m < 52 else 1.0), c["t0"])
    cut = automation(sorted(S.cut) or [(0.0, 2500.0)], N)
    I["pad"] = svf(I["pad"], cut, 0.75, "lp")
    I["pad"] = biquad(I["pad"], "highpass", 140.0, 0.7)
    I["pad"] = biquad(I["pad"], "highshelf", 5000.0, 0.7, -3.0)
    # arp motif
    for i, (t, m, v, g, br, gl) in enumerate(S.arps):
        w = pluck_wave(float(midi_hz(m)), v, g, br, seed=5000 + i, glassy=gl)
        place_mono(I["arp"], w, t, (-0.28, 0.28)[i % 2] * (0.6 if m < 66 else 1.0), 1.0)
    I["arp"] = svf(I["arp"], np.minimum(cut * 2.2, 16000.0), 0.7, "lp")
    I["arp"] = biquad(I["arp"], "highpass", 220.0, 0.7)
    # bells
    for i, (t, m, v, pan) in enumerate(S.bells):
        w = glass_note(float(midi_hz(m)), dur=3.2, vel=v, tau=1.3, bright=0.75, seed=7000 + i)
        place_mono(I["bells"], w, t, pan, 1.0)
    # fx
    for e in S.fx:
        if e["type"] == "riser":
            x = riser(e["dur"], seed=int(e["t"] * 10), tone_mix=0.25)
            add_at(I["fx"], x * e["lvl"], e["t"] - x.shape[1] / SR)
        elif e["type"] == "downlifter":
            add_at(I["fx"], downlifter(2.4, seed=int(e["t"] * 10), f_start=7000.0, f_end=650.0, semis=-5.0,
                                       tone_mix=0.12, decay=1.5) * e["lvl"], e["t"])
        elif e["type"] == "sub_swell":
            place_mono(I["fx"], sub_swell(3.0, 1.3), e["t"] - 1.3, 0.0, e["lvl"])
        elif e["type"] == "shimmer":
            add_at(I["fx"], grain_cloud(1.2, 26, seed=int(e["t"] * 10)) * e["lvl"] / 3.0, e["t"])
    for a, b, lvl in S.air:
        m = int((b - a) * SR)
        tt = np.arange(m) / SR
        x = np.stack([butter(noise(m, "pink", int(a * 10) + c), "bandpass", [2500.0, 11000.0], 2) for c in (0, 1)])
        mod = 0.75 + 0.25 * np.sin(2 * np.pi * 0.11 * tt)  # slow breathing
        add_at(I["air"], fade(x * mod * lvl, 1.0, 1.5), a)
    if verbose:
        print(f"  synthesised {len(S.chords)} chords, {len(S.arps)} arp notes, {len(S.kicks)} kicks, "
              f"{len(S.hats)} hats, {len(S.bells)} bells, {len(S.fx)} fx in {time.time() - t_start:.1f}s")
    # ---------------------------------------------------------------- level calibration (per instrument)
    gains = {}
    for k, x in I.items():
        if np.abs(x).max() < 1e-9:
            gains[k] = 0.0
            continue
        lu = integrated_lufs(x)
        gains[k] = float(undb(TARGET[k] - lu))
        I[k] = x * gains[k]
    # ---------------------------------------------------------------- sidechain-style ducking to the kick
    def duck_curve(depth, release):
        g = np.ones(N)
        m = int(0.45 * SR)
        tt = np.arange(m) / SR
        shape = 1.0 - depth * (1.0 - np.exp(-tt / 0.003)) * np.exp(-tt / release)
        shape[: int(0.003 * SR)] = np.minimum(shape[: int(0.003 * SR)], 1.0)
        for t, v in S.kicks:
            i0 = int(t * SR)
            k = min(m, N - i0)
            if k > 0:
                g[i0:i0 + k] = np.minimum(g[i0:i0 + k], 1.0 - (1.0 - shape[:k]) * min(1.0, v))
        return g
    I["sub"] *= duck_curve(0.6, 0.11)
    I["bpluck"] *= duck_curve(0.35, 0.09)
    I["pad"] *= duck_curve(0.3, 0.16)
    I["arp"] *= duck_curve(0.12, 0.1)
    # ---------------------------------------------------------------- stems with their own spaces
    hall = make_ir(rt60=2.3, predelay=0.022, hf_ratio=0.38, damp_hz=4800.0, bright_hz=11000.0, seed=21)
    room = make_ir(rt60=1.1, predelay=0.012, hf_ratio=0.45, damp_hz=5000.0, er_gain=0.7, seed=22)
    dotted8 = 0.75 * L.beat
    stems = {}
    drums = I["kick"] + I["clap"] + I["hats"] + I["shaker"]
    stems["drums"] = drums + 0.32 * _conv(I["clap"], room) + 0.1 * _conv(I["hats"] + I["shaker"], room)
    stems["bass"] = I["sub"] + I["bpluck"]
    pad = biquad(I["pad"], "peak", 320.0, 0.9, -2.5)  # clear the 250-400 Hz 'mud' band the voice's warmth lives in
    pad = chorus(pad, voices=3, base_ms=12.0, depth_ms=2.4, mix=0.45, seed=3)
    stems["harmony"] = pad + 0.3 * _conv(pad, hall)
    motif = I["arp"] + I["bells"]
    stems["motif"] = motif + 0.22 * pingpong(I["arp"], dotted8, 0.38, 6, 3000.0, 300.0) \
        + 0.18 * pingpong(I["bells"], dotted8 * 2, 0.35, 4, 4000.0, 400.0) + 0.32 * _conv(motif, hall)
    stems["fx"] = I["fx"] + I["air"] + 0.25 * _conv(I["fx"], hall)
    return stems, S, skipped, gains, n


def _conv(x, ir):
    from scipy.signal import oaconvolve
    return np.stack([oaconvolve(x[c], ir[c])[: x.shape[1]] for c in (0, 1)])


def master(stems, n):
    mix = butter(sum(stems.values()), "highpass", 28.0, 2)  # nothing useful lives below 28 Hz
    glued, gr = compress(mix, thresh_db=-17.0, ratio=1.5, attack_ms=30.0, release_ms=250.0, knee_db=8.0)
    glued = glued[:, :n]
    # a real ending: the final chord + bell tail decay naturally; a last 0.6 s raised-cosine only guarantees 0
    glued = fade(glued, 0.02, 0.6)
    pre = integrated_lufs(glued)
    out, lufs, tp = normalize_loudness(glued, TARGET_LUFS, ceiling_db=-1.0)
    gain = float(undb(lufs - pre))  # applied to the stems too, so they sum to the bed before compression
    return out, lufs, tp, gain, float(np.max(gr))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cues", help="cue sheet (default public/data/cues.json, else the built-in layout)")
    ap.add_argument("--png", action="store_true", help="write out/audio/music_v2_spectrogram.png")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    t0 = time.time()
    L = load_layout(a.cues)
    print(f"layout from {L.source}: {L.duration:.3f}s, {L.bpm:g} BPM, beat grid offset {L.offset:.3f}s")
    for s in L.sections:
        extra = (f"  land {s.land:.2f}" if s.land else "") + (f"  resolve {s.resolve:.2f}" if s.resolve else "")
        print(f"  {s.name:8s} -> {s.kind:9s} {s.t0:6.2f} - {s.t1:6.2f}{extra}")
    stems, S, skipped, gains, n = render(L, a.seed)
    for s in skipped:
        print("  skipped:", s)
    bed, lufs, tp, g, gr = master(stems, n)
    OUT.mkdir(parents=True, exist_ok=True)
    write_wav(OUT / "music_v2.wav", bed)
    for k, x in stems.items():
        write_wav(OUT / f"music_v2_{k}.wav", x[:, :n] * g, subtype="FLOAT")
    bounds = [(s.name, s.t0, s.t1) for s in L.sections]
    secl = section_loudness(bed, bounds)
    bands = band_energy_db(bed, [(20, 60), (60, 200), (200, 500), (500, 2000), (2000, 6000), (6000, 12000),
                                 (12000, 20000)])
    print(f"music_v2.wav: {lufs:.2f} LUFS integrated, true peak {tp:.2f} dBTP, bus GR max {gr:.1f} dB, "
          f"{n / SR:.3f}s  ({time.time() - t0:.0f}s)")
    for name, s0, s1, il, mx in secl:
        print(f"  {name:8s} {s0:6.2f}-{s1:6.2f}  {il:6.1f} LUFS (max momentary {mx:6.1f})")
    print("  long-term band energy (dB re total):", {k: round(v, 1) for k, v in bands.items()})
    rep = dict(source=L.source, duration=L.duration, bpm=L.bpm, grid_offset=L.offset,
               sections=[dict(name=s.name, kind=s.kind, start=round(s.t0, 3), end=round(s.t1, 3),
                              land=s.land, resolve=s.resolve) for s in L.sections],
               seal_answers=L.seals, skipped_fx=skipped, instrument_gain_db={k: round(float(20 * np.log10(v)), 1)
                                                                              if v else None for k, v in gains.items()},
               lufs=round(lufs, 2), true_peak_dbtp=round(tp, 2), bus_gain_reduction_max_db=round(gr, 1),
               section_lufs={nm: round(il, 1) for nm, _, _, il, _ in secl}, band_energy_db=bands,
               stems={k: f"out/audio/music_v2_{k}.wav" for k in stems})
    (OUT / "music_v2_report.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    if a.png:
        spectrogram_png(bed, OUT / "music_v2_spectrogram.png", f"music_v2.wav - {lufs:.1f} LUFS, TP {tp:.1f} dBTP",
                        marks=[(s.t0, s.name) for s in L.sections],
                        vlines=[x for x in [s.land for s in L.sections if s.land] +
                                [s.resolve for s in L.sections if s.resolve]])
        print("  spectrogram -> out/audio/music_v2_spectrogram.png")


if __name__ == "__main__":
    main()
