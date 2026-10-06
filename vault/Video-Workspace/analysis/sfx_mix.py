"""Sound design for the Fabius pitch (port of the kit's analysis/sfx_mix.py).

The cue sheet is derived from public/data/lyrics.json — the same word times the plates animate on — so every
effect lands on its visual event (the anchors below repeat the plates' own formulas, e.g. Lock's padlocks shut
at 'locked' - 0.04 + 0.07 s each). Effects come from the kit's ElevenLabs library (public/audio/sfx/name_N.mp3), placed by
transient ('onset'), loudest point ('peak'), end ('end') or as recorded. Effects and the music bed (out/bed.wav,
analysis/music_bed.py) are ducked under the voice; the mix is loudness-normalised to -14 LUFS.

    python -m uv run --no-project --with numpy python analysis/sfx_mix.py
Writes public/audio/mix.wav and public/audio/mix.mp3 (the composition's soundtrack) and out/sfx_cues.json.
"""
import json, re, subprocess, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SFX = ROOT / "public" / "audio" / "sfx"
SR = 48000
LYD = json.loads((ROOT / "public" / "data" / "lyrics.json").read_text(encoding="utf-8"))
LY, DUR = LYD["lines"], LYD["duration"]
fold = lambda s: s.lower().replace("’", "'").replace("“", '"').replace("”", '"')
norm = lambda s: re.sub(r"[^a-z0-9']", "", fold(s)).strip("'")


def line(q):
    return [l for l in LY if fold(q) in fold(l["text"])][0]


def W(lq, wq, nth=0):
    return [w for w in line(lq)["words"] if norm(w["w"]) == norm(wq)][nth]


def cut(q):
    l = line(q)
    i = LY.index(l)
    gap = l["start"] - LY[i - 1]["end"] if i else 1
    return l["start"] - min(0.18, max(0.04, gap * 0.45))


# ------------------------------------------------------------------ the library
MODE = {"whoosh_fast": "peak", "whoosh_soft": "peak", "reverse_suck": "end", "riser": "end",
        "spark_sizzle": "raw", "projector_run": "raw", "tape_rewind": "raw", "scan_sweep": "raw", "spark_zip": "raw",
        "falling_pieces": "onset", "paper_slide": "onset"}
_cache = {}


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def takes(name):
    if name not in _cache:
        fs = sorted(SFX.glob(f"{name}_*.mp3"))
        if not fs:
            raise FileNotFoundError(f"no takes for {name}")
        out = []
        for f in fs:
            x = decode(f)
            x = x - x.mean()
            out.append(x / (np.abs(x).max() + 1e-9) * 10 ** (-1 / 20))
        _cache[name] = out
    return _cache[name]


def onset(x):
    a = np.abs(x)
    idx = np.where(a > 0.5 * a.max())[0]
    return max(0, int(idx[0]) - int(0.008 * SR)) if len(idx) else 0


def peak_at(x):
    env = np.convolve(np.abs(x), np.ones(int(0.02 * SR)) / (0.02 * SR), mode="same")
    return int(np.argmax(env))


def resample(x, rate):
    if abs(rate - 1) < 1e-4:
        return x
    n = int(len(x) / rate)
    return np.interp(np.arange(n) * rate, np.arange(len(x)), x).astype(np.float32)


CUES, _n = [], {}


def cue(t, name, db, pan=0.0, rate=1.0, take=None, length=None, fade=0.03, mode=None):
    k = _n.get(name, 0)
    _n[name] = k + 1
    CUES.append(dict(t=float(t), name=name, db=float(db), pan=float(pan), rate=float(rate), take=take, k=k, length=length, fade=fade, mode=mode or MODE.get(name, "onset")))


def bed(name, t0, t1, db, pan=0.0, rate=1.0, fin=0.06, fout=0.12):
    CUES.append(dict(t=float(t0), name=name, db=float(db), pan=float(pan), rate=float(rate), take=1, k=0, length=float(t1 - t0), fade=fout, fin=fin, mode="bed"))


def jitter(i, a=0.05):
    return 1.0 + a * (((i * 7919) % 101) / 50.0 - 1.0)


def typing(t0, t1, db, pan=0.0, step=0.07, name="key_click"):
    i = 0
    t = t0
    while t < t1:
        cue(t, name, db + 2 * (((i * 31) % 7) / 6 - 0.5), pan=pan, rate=jitter(i, 0.06))
        t += step * (0.8 + 0.4 * (((i * 13) % 11) / 10))
        i += 1


# ================================================================== 01 HOOK
w = lambda q: W("Over two thousand", q)
cue(0.12, "spark_ignite", -14)
cue(0.35, "pen_line", -21, length=0.6, fade=0.1)
tAx0, tAx1 = w("Over")["start"] + 0.12, w("ago,")["end"] + 0.15
cue(tAx0, "spark_zip", -18, pan=-0.6, length=tAx1 - tAx0 + 0.1, fade=0.15)
for i, q in enumerate(("kept", "losing", "Hannibal")):
    cue(w(q)["start"], "marker_strike", -13, pan=-0.6 + 0.3 * i, rate=jitter(i))
    cue(w(q)["start"] + 0.11, "pen_tick", -18, pan=-0.6 + 0.3 * i)
w = lambda q: W("So one general", q)
cue(w("refused")["start"] - 0.02, "impact_slam", -11)
cue(w("refused")["start"], "pen_line", -18, pan=0.2, length=0.45)
cue(w("refused")["start"] + 0.45, "spark_zip", -22, pan=0.4, length=w("wanted.")["end"] - w("refused")["start"] - 0.25, fade=0.2)
w = lambda q: W("His name was", q)
cue(w("Fabius.")["start"] - 0.02, "pen_line", -14, length=1.1, fade=0.2)
cue(w("Fabius.")["start"] + 0.95, "confirm_chime", -20)
cue(cut("Most trading bots"), "whoosh_fast", -13)

# ================================================================== 02 PROBLEM
w = lambda q: W("They charge in", q)
tShot = w("screenshot")["start"] + 0.1
t = cut("Most trading bots") + 0.1
i = 0
while t < tShot:  # the order wall's ticker
    cue(t, "ui_tick", -30 + 3 * (i % 3 == 0), pan=-0.7 + 1.4 * (((i * 37) % 10) / 9), rate=jitter(i, 0.12))
    t += 0.085
    i += 1
cue(w("show")["start"] - 0.15, "whoosh_soft", -17, pan=0.4)
cue(tShot, "snip", -9, pan=0.4)
cue(tShot + 0.01, "projector_click", -12, pan=0.4)
cue(tShot + 0.02, "impact_small", -17, pan=0.4)
cue(w("market")["start"], "ui_blip", -19, pan=0.3)
cue(w("moved.")["start"] + 0.15, "ui_blip", -17, pan=0.6, rate=1.2)
w = lambda q: W("You can’t check", q)
cue(w("what")["start"], "stamp", -9, pan=0.35)
cue(w("when.")["start"], "stamp", -8, pan=0.45, rate=0.95)
cue(cut("Fabius is a paper"), "riser", -16, mode="end")
cue(cut("Fabius is a paper"), "reverse_suck", -18)

# ================================================================== 03 IDEA
w = lambda q: W("Fabius is a paper", q)
tName = w("Fabius")["start"]
cue(tName - 0.1, "impact_slam", -11)
for i in range(6):
    cue(tName - 0.12 + i * 0.045 + 0.2, "impact_small", -22, pan=-0.5 + 0.2 * i, rate=jitter(i, 0.08))
cue(w("that")["start"] - 0.1, "whoosh_soft", -16)
cue(w("commits")["start"], "ui_tick", -19)
cue(w("Chain")["start"] + 0.1, "stamp", -14, pan=0.2)
cue(w("Chain")["start"] + 0.12, "confirm_chime", -17, pan=0.2)
cue(w("before")["start"], "ui_blip", -20)
w = lambda q: W("Even the decision", q)
cue(line("Even the decision")["start"] - 0.2, "whoosh_soft", -19)
cue(w("nothing.")["start"] + 0.2, "stamp", -13)
cue(cut("It starts with the rules"), "whoosh_fast", -15)

# ================================================================== 04 LOCK
L8 = line("It starts with the rules")
for i in range(6):  # six glass tablets land
    cue(L8["start"] + 0.12 + 0.1 * i, "impact_small", -23, pan=-0.6 + 0.6 * (i % 3), rate=jitter(i, 0.08))
typing(L8["start"] + 0.05, L8["start"] + 0.95, -28, pan=0.0)
w = lambda q: W("Each of our six", q)
for i in range(6):
    cue(w("six")["start"] + 0.07 * i, "ui_tick", -23, pan=-0.6 + 0.6 * (i % 3), rate=jitter(i))
cue(w("hashed")["start"] - 0.12, "scan_sweep", -19, length=0.85)
typing(w("hashed")["start"] + 0.1, w("hashed")["start"] + 0.75, -27, pan=0.3)
for i in range(6):  # padlocks drop and snap shut
    cue(w("locked")["start"] - 0.04 + 0.07 * i, "stamp", -15, pan=-0.6 + 0.6 * (i % 3), rate=jitter(i, 0.06))
cue(w("on-chain.")["start"] - 0.1, "whoosh_soft", -18)
cue(w("on-chain.")["start"] + 0.12, "whoosh_soft", -17, pan=-0.3)
L10 = line("A strategy that")
cue(L10["start"] - 0.1, "reverse_suck", -22)
w = lambda q: W("A strategy that", q)
tGo, tHit = w("locked")["start"], w("can’t")["start"] + 0.05
cue(tGo, "paper_slide", -16, pan=-0.3, length=tHit - tGo + 0.1, fade=0.08)
cue(tHit, "impact_slam", -12, pan=0.2)
cue(tHit + 0.32, "stamp", -12, pan=0.3)
cue(cut("Every bar, a bot"), "whoosh_fast", -13)

# ================================================================== 05 COMMIT
w = lambda q: W("Every bar, a bot", q)
for i in range(4):
    cue(cut("Every bar, a bot") + 0.04 * i + 0.1, "ui_tick", -27, pan=-0.8 + 0.1 * i)
cue(w("bar,")["start"], "ui_blip", -18, pan=-0.5)
cue(w("bar,")["start"] + 0.02, "impact_small", -22, pan=-0.5)
for i in range(4):  # the signals leave the candle and land as blocks
    cue(w("signals")["start"] - 0.05 + 0.09 * i, "ui_tick", -16, pan=-0.6 + 0.15 * i, rate=1 + 0.08 * i)
    cue(w("signals")["start"] + 0.5 + 0.09 * i, "impact_small", -22, pan=-0.5 + 0.2 * i, rate=jitter(i, 0.08))
cue(w("become")["start"], "pen_line", -20, length=0.7, fade=0.15)
cue(w("become")["start"] + 0.1, "spark_zip", -24, length=0.9, fade=0.2)
cue(w("root,")["start"], "confirm_chime", -18)
cue(w("committed")["start"], "whoosh_soft", -17, pan=0.4)
cue(w("97.")["start"] + 0.15, "impact_small", -14, pan=0.5)
cue(w("97.")["start"] + 0.16, "stamp", -19, pan=0.5)
w = lambda q: W("Late commits are", q)
cue(w("Late")["start"] - 0.25, "whoosh_fast", -18, pan=0.7)
cue(w("rejected.")["start"] + 0.02, "impact_small", -14, pan=0.5)
cue(w("rejected.")["start"] + 0.12, "stamp", -10, pan=0.4)
cue(w("reveal")["start"], "spark_ignite", -15)
cue(w("checked")["start"] - 0.1, "scan_sweep", -18, length=0.6)
cue(w("root.")["start"] + 0.12, "confirm_chime", -15)
w = lambda q: W("Anyone can rerun", q)
tTerm = line("Anyone can rerun")["start"] - 0.45
cue(tTerm, "whoosh_soft", -18)
typing(tTerm + 0.2, tTerm + 1.6, -26, pan=0.3)
cue(w("needed.")["start"], "ui_blip", -17)
cue(cut("On top runs the AI desk"), "whoosh_fast", -13)
cue(cut("On top runs the AI desk"), "riser", -20, mode="end")

# ================================================================== 06 DESK
L15 = line("Every five minutes")
w = lambda q: W("Every five minutes", q)
cue(cut("On top runs the AI desk") + 0.15, "spark_ignite", -18)
d0, d1 = w("Every")["start"], W("And its root must", "up.")["start"] + 0.1
bed("projector_run", d0, d1, -31)
for i in range(5):
    cue(w("analysts,")["start"] + 0.12 * i, "ui_blip", -20, pan=-0.8 + 0.4 * i, rate=1 + 0.05 * i)
    cue(w("ERC-8004")["start"] + 0.08 * i, "ui_tick", -24, pan=-0.8 + 0.4 * i)
    cue(w("vote")["start"] + 0.28 * i, "paper_slide", -18, pan=-0.8 + 0.4 * i, rate=jitter(i))
    cue(w("vote")["start"] + 0.28 * i + 0.72, "ui_tick", -21, rate=1.2)
w = lambda q: W("A locked formula", q)
cue(w("formula")["start"] - 0.1, "impact_small", -13)
cue(w("formula")["start"], "confirm_chime", -18)
for i in range(5):  # the five slots of the book light in turn
    cue(w("book.")["start"] + 0.2 + 0.09 * i, "ui_blip", -21, rate=1 + 0.06 * i)
tCommit = d0 + 0.84 * (d1 - d0)
cue(tCommit - 0.45, "spark_zip", -16, length=0.5, fade=0.1)
cue(tCommit, "confirm_chime", -13)
cue(d1 + 0.25, "stamp", -11, pan=0.4)
cue(cut("The AI picks the rulebook"), "impact_slam", -13)

# ================================================================== 07 SPLIT
w = lambda q: W("The AI picks the rulebook", q)
cue(w("picks")["start"], "whoosh_soft", -17, pan=-0.5)
typing(w("Code")["start"] - 0.3, w("Code")["start"] + 0.6, -25, pan=0.5)
cue(w("position.")["start"], "impact_small", -13, pan=0.5)
cue(cut("And the desk is open"), "whoosh_fast", -13)

# ================================================================== 08 OPEN
w = lambda q: W("And the desk is open", q)
cue(w("open.")["start"] - 0.05, "whoosh_soft", -13, rate=0.8)
cue(w("open.")["start"], "spark_ignite", -19)
w = lambda q: W("Bring your own bot", q)
cue(w("Bring")["start"] - 0.1, "whoosh_soft", -17, pan=-0.5)
cue(w("plug")["start"] - 0.1, "whoosh_soft", -17, pan=0.5)
L21 = line("Every bot runs the same")
w = lambda q: W("Every bot runs the same", q)
tG = L21["start"] - 0.35
for i in range(11):  # the portals rise
    cue(tG + 0.15 + 0.04 * i, "ui_tick", -24, pan=-0.8 + 0.16 * i)
r0, r1 = w("runs")["start"] - 0.1, w("verdict")["start"] + 0.1
for i in range(11):
    k = ((i - 5) * 150 + 960) / 1920  # the bot's x = lerp(-960, 960, inOutCubic(u)): invert the ease for its pass time
    u = (k / 4) ** (1 / 3) if k < 0.5 else 1 - ((2 - 2 * k) ** (1 / 3)) / 2
    cue(r0 + (r1 - r0) * u, "ui_blip", -21, pan=-0.8 + 0.16 * i, rate=1 + 0.03 * i)
cue(w("reason.")["start"] - 0.2, "stamp", -9)
cue(w("reason.")["start"] - 0.18, "impact_small", -15)
cue(cut("Signals sell over"), "whoosh_fast", -13)

# ================================================================== 09 BNB
w = lambda q: W("Signals sell over", q)
cue(line("Signals sell over")["start"] - 0.4, "ui_blip", -20, pan=0.5)   # /buy B2-RS sent
cue(w("over")["start"], "ui_blip", -18, pan=0.5, rate=1.15)            # the bot replies
cue(w("x402,")["start"] + 0.1, "impact_slam", -11, pan=-0.4)
for i, dt in enumerate((-0.1, 0.35)):
    cue(w("x402,")["start"] + dt, "ui_tick", -19, pan=-0.5)
cue(w("buyer")["start"] - 0.15, "ui_tick", -19, pan=-0.5)
cue(w("buyer")["start"] + 0.1, "confirm_chime", -17, pan=0.5)          # the signal image arrives
cue(w("gas.")["start"] - 0.1, "ui_tick", -19, pan=-0.5)
cue(w("gas.")["start"] + 0.2, "ui_blip", -16, pan=0.0)
w = lambda q: W("All on testnet", q)
for q in ("testnet,", "token."):
    cue(w(q)["start"], "ui_tick", -19)
cue(w("No")["start"] + 0.12, "mouse_click", -9)
cue(w("No")["start"] + 0.3, "ui_tick", -17)
cue(w("No")["start"] + 0.44, "impact_small", -15)
cue(w("design.")["start"], "stamp", -9)
cue(cut("Because here"), "riser", -17, mode="end")

# ================================================================== 10 HONEST
w = lambda q: W("Because here", q)
cue(w("profit.")["start"], "impact_small", -12)
cue(w("profit.")["start"] + 0.45, "marker_strike", -6)
bed("projector_run", w("profit.")["start"] + 0.5, line("The forward clock")["start"] - 0.2, -31)
w = lambda q: W("The forward clock", q)
cue(line("The forward clock")["start"] - 0.3, "whoosh_soft", -17)
cue(w("October")["start"], "ui_blip", -16)
w = lambda q: W("To pass, a bot needs", q)
for i, q in enumerate(("signals,", "days,", "months,", "confidence")):
    cue(w(q)["start"] - 0.1, "ui_blip", -16, rate=1 + 0.1 * i)
for i in range(6):
    cue(line("Today, zero of six")["start"] + 0.06 * i, "ui_tick", -22, rate=jitter(i))
cue(W("Today, zero of six", "passed.")["start"] + 0.05, "stamp", -7)
cue(W("Today, zero of six", "passed.")["start"] + 0.06, "impact_slam", -14)
cue(cut("So Fabius does what"), "whoosh_fast", -15)

# ================================================================== 11 END
tw = line("So Fabius does what")["start"]
t = tw + 0.2
i = 0
hero = line("Fabius. Refuse")["start"] - 0.45
while t < hero - 0.2:  # the clock ring, one tick per half second
    cue(t, "pen_tick", -21 if i % 2 else -18, pan=0.0, rate=1.0 if i % 2 else 0.85)
    t += 0.5
    i += 1
cue(hero + 0.8, "riser", -15, mode="end")
cue(hero + 0.8, "reverse_suck", -17)
w = lambda q: W("Fabius. Refuse", q)
for i in range(6):
    cue(w("Fabius.")["start"] - 0.1 + i * 0.05 + 0.15, "impact_small", -19, pan=-0.5 + 0.2 * i, rate=jitter(i, 0.08))
for i in range(3):
    cue(hero + 0.6 + 0.2 * i, "whoosh_soft", -21, pan=-0.6 + 0.6 * i)
cue(w("Prove")["start"], "confirm_chime", -14)
cue(DUR - 1.2, "spark_sizzle", -26, length=1.0, fade=0.6)


# ------------------------------------------------------------------ render the mix
def main():
    n = int(DUR * SR)
    bus = np.zeros((2, n), np.float32)
    report = []
    for c in CUES:
        tk = takes(c["name"])
        x = tk[(c["take"] - 1) % len(tk)] if c["take"] else tk[c["k"] % len(tk)]
        x = resample(x, c["rate"])
        mode = c["mode"]
        if mode == "onset":
            x = x[onset(x):]
            start = c["t"]
        elif mode == "peak":
            start = c["t"] - peak_at(x) / SR
        elif mode == "end":
            start = c["t"] - len(x) / SR
        else:
            start = c["t"]
        if mode == "bed":
            L = int(c["length"] * SR)
            x = np.tile(x, int(np.ceil(L / len(x))) + 1)[:L].copy()
            fi = int(c.get("fin", 0.06) * SR)
            if fi:
                x[:fi] *= np.linspace(0, 1, fi)
        if c.get("length") and mode != "bed":
            x = x[: int(c["length"] * SR)].copy()
        fo = min(len(x), int(c["fade"] * SR))
        if fo > 1:
            x[-fo:] *= np.linspace(1, 0, fo)
        g = 10 ** (c["db"] / 20)
        a = (c["pan"] + 1) * np.pi / 4
        i0 = int(round(start * SR))
        j0 = max(0, -i0)
        i0 = max(0, i0)
        seg = x[j0:]
        m = min(len(seg), n - i0)
        if m <= 0:
            continue
        bus[0, i0:i0 + m] += seg[:m] * g * np.cos(a)
        bus[1, i0:i0 + m] += seg[:m] * g * np.sin(a)
        report.append({**{k: c[k] for k in ("t", "name", "db", "pan", "rate", "mode")}, "start": round(start, 3)})
    vop = ROOT / "public" / "audio" / "voiceover.wav"
    vo = decode(vop if vop.exists() else vop.with_suffix(".mp3"))[:n]
    vo = np.pad(vo, (0, n - len(vo)))
    # the music bed
    musicp = ROOT / "out" / "bed.wav"
    music = np.zeros((2, n), np.float32)
    if musicp.exists():
        with wave.open(str(musicp)) as f:
            raw = np.frombuffer(f.readframes(f.getnframes()), "<i2").reshape(-1, 2).T.astype(np.float32) / 32768
        m = min(n, raw.shape[1])
        music[:, :m] = raw[:, :m]
    # ducking: a one-pole follower on the voice; effects dip up to 7 dB, the bed up to 9 dB
    hop = int(0.005 * SR)
    env = np.sqrt(np.convolve(vo ** 2, np.ones(hop * 4) / (hop * 4), mode="same"))
    env = env / (np.percentile(env, 99) + 1e-9)
    sm = np.zeros_like(env)
    a_att, a_rel = np.exp(-1 / (0.010 * SR)), np.exp(-1 / (0.220 * SR))
    prev = 0.0
    for i in range(0, n, hop):
        e = float(env[i])
        coef = (a_att if e > prev else a_rel) ** hop
        prev = coef * prev + (1 - coef) * e
        sm[i:i + hop] = prev
    duck_fx = 10 ** (-7 * np.clip(sm, 0, 1) / 20)
    duck_bed = 10 ** (-9 * np.clip(sm, 0, 1) / 20)
    bed_gain = 10 ** (-17 / 20)
    mix = bus * duck_fx[None, :] + music * bed_gain * duck_bed[None, :] + vo[None, :]
    peak = np.abs(mix).max()
    if peak > 0.99:
        mix *= 0.99 / peak
    out_dir = ROOT / "out"
    out_dir.mkdir(exist_ok=True)
    raw_wav = out_dir / "mix_raw.wav"
    with wave.open(str(raw_wav), "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((np.clip(mix.T, -1, 1) * 32767).astype("<i2").tobytes())
    (out_dir / "sfx_cues.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(f"{len(report)} cues; mix peak {20 * np.log10(peak + 1e-9):.1f} dBFS")
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw_wav), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(meas[meas.rindex("{"): meas.rindex("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
          f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    mix_wav = ROOT / "public" / "audio" / "mix.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw_wav), "-af", af, "-ar", str(SR), str(mix_wav)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mix_wav), "-c:a", "libmp3lame", "-b:a", "256k", str(ROOT / "public" / "audio" / "mix.mp3")], check=True)
    print(f"input {j['input_i']} LUFS -> -14 LUFS; wrote public/audio/mix.wav + mix.mp3")


if __name__ == "__main__":
    main()
