"""Mechanical guard for the client's rule: no sound that gives an impression of a crash or something broken.

    python -X utf8 analysis/check_sfx.py                      # full check (exit 1 on any failure)
    python -X utf8 analysis/check_sfx.py --cues out/audio/cues-demo.json
    python -X utf8 analysis/check_sfx.py --screen FILE...     # acoustic screen only, any files (review aid)
    python -X utf8 analysis/check_sfx.py --print-whitelist    # SHA-256 of every file now on disk, ready to paste

What fails (exit code 1):
 (a) an audio file anywhere under public/audio/sfx*/ that is not on WHITELIST, or whose SHA-256 differs from its
     pin (so a file cannot be swapped under an approved name);
 (b) a file name, folder name or cue name matching BANNED (crash|impact|slam|fall|debris|break|shatter|smash|
     glitch|static|crackle|sizzle|zap|distort|rewind|tape|suck|scratch|snip|stamp);
 (c) a cue in public/data/cues.json (sfx[].name) that does not resolve to a whitelisted file (when that file does
     not exist yet the check falls back to out/audio/cues-demo.json and says so);
 (d) acoustic screen flags on a whitelisted file that its whitelist entry does not acknowledge. The screen measures
     true peak, clipping runs, edge clicks, crest factor, the spectral flatness / >2 kHz share of every sharp onset
     (impacts, snips, stamps), the share of noisy high-frequency frames (static, sizzle, hiss), micro-transient
     density (crackle) and abrupt endings (reverse sucks, cut-offs). A flag means "a human listens and decides";
     approval is written into WHITELIST as {FLAG: note}, so the decision is reviewed in git.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
from scipy import signal  # noqa: E402
from scipy.ndimage import median_filter, minimum_filter1d  # noqa: E402

from dsp_v2 import ROOT, SR, read_audio, todb, true_peak_db  # noqa: E402

AUDIO = ROOT / "public" / "audio"
CUES = ROOT / "public" / "data" / "cues.json"
CUES_DEMO = ROOT / "out" / "audio" / "cues-demo.json"
AUDIO_EXT = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac", ".aif", ".aiff", ".opus", ".webm"}

BANNED = re.compile(r"crash|impact|slam|fall|debris|break|shatter|smash|glitch|static|crackle|sizzle|zap|distort|"
                    r"rewind|tape|suck|scratch|snip|stamp", re.I)

# --------------------------------------------------------------------------------------------------- WHITELIST
# path relative to public/audio -> (sha256, {acknowledged screen flag: reviewer note})
# Regenerate pins with --print-whitelist AFTER a human has listened to the changed file.
WHITELIST: dict[str, tuple[str, dict[str, str]]] = {
    # --- sfx2: synthesised by analysis/sfx_synth.py (deterministic; re-pin after a deliberate change) -----------
    "sfx2/coin.wav": ("b37878eea084d8f124ce8b2b23a458006e975004c68c56b16bbddff056b8537d", {}),
    "sfx2/data_blip_a.wav": ("291b8d7800502246b39154fbe5a5b59bef10e3ebfa6498c9b722714136683d76", {}),
    "sfx2/data_blip_b.wav": ("7e11c1ccb264c705eda673849d79bd9164d8e577ab1b683a1010fd247571235c", {}),
    "sfx2/downlifter.wav": ("b90c21d6c8305a978d9179ad1a0d82bf7ceac6e1b21f03f9006028fc6eae943d", {
        "PITCH_DIVE": "designer review 7 Oct (by numbers, not yet by ear): a filtered-AIR sweep 7 kHz -> 650 Hz "
                      "fading out, its quiet tone only eases down 5 semitones and never towards zero - a "
                      "downlifter, not a tape-stop. Builder: listen once; delete the file if it reads as a "
                      "power-down."}),
    "sfx2/glass_chime_a.wav": ("f6d5c9fdc9b6412f31ca4ba23cd08420e8191870218ca775ce87538f7399e573", {}),
    "sfx2/glass_chime_b.wav": ("77fe3dd490a1484154ef7812276677644cd36a070887db7c93d81f07f78cbd58", {}),
    "sfx2/glass_chime_c.wav": ("f0d8ff8180e344ff8e69885d9d794ea1eb705e35bcb19c674971e4c7ecc1b7fe", {}),
    "sfx2/glass_seal.wav": ("f2c7b0e3e06544b2ed2e3bdaec91e933151d8ab394153dcc76a31adca15d3465", {}),
    "sfx2/key_soft_a.wav": ("810084c949cc2835b191983c3db6f8adefa13fce8a4067c9a19b79bb16060426", {}),
    "sfx2/key_soft_b.wav": ("1bb44878a2bec90ef8196d94a56b6edcd85391560202c313e33f1eeea02dbd9a", {}),
    "sfx2/key_soft_c.wav": ("9b029ea6d4941d6cf00ac8ab90abe32b85e6705968f1478103762e286d04822d", {}),
    "sfx2/key_soft_d.wav": ("0d09e5a746942bba7a45e173671845c9cddd519267dd08d3dbb2af94c404c0ac", {}),
    "sfx2/lock_click.wav": ("0ad037780694ff19ddd5cd5ccd1477393333e12660083c6aba338f271ce2555e", {}),
    "sfx2/notify.wav": ("6c82a3eb200977d1c0e461a398904992a962f8136d73d77c8692737b04a912e0", {}),
    "sfx2/reveal_bloom.wav": ("c0546b1245bd4e8c6fa844fda72da4b93f2267368c512b7a34fa0717123a4495", {}),
    "sfx2/riser_2s.wav": ("b2e895b70ed561e949c852d7604ba88b3c6a65e9b3871080cd63ff58e71354a8", {}),
    "sfx2/riser_4s.wav": ("ed334ab85f4ce832d4a8735a7efb7499a6a478b0efb11de3d9cfc94be2876f9b", {}),
    "sfx2/shimmer.wav": ("3d75c554e17c97222b69377f210b5795a6e83e2692b5e83766564e5742e37a2a", {}),
    "sfx2/sub_swell.wav": ("963d78f8c01161757def8fd881baa59fa342fd547fa1cb0501f01c1df4155fea", {}),
    "sfx2/success.wav": ("0df1321937ca652367e07314426cbf3fafe5d586f81ce5c23cfb2283432c3742", {}),
    "sfx2/swipe_up.wav": ("79e60e3c094ab471d478b02c57adb70886becdcb49113b47cec048c98a6fd6b9", {}),
    "sfx2/ui_click_a.wav": ("30367cffe79f081fd08a549049da258e74a46a09ef9a4eb5e0dbbc5dfc3540c5", {}),
    "sfx2/ui_click_b.wav": ("58a483677d3223cb87673cc59bf976420f3d88bae53202241c510790ac852bc7", {}),
    "sfx2/ui_hover.wav": ("69dabdfb1360d6aa0a9b0358bd0cd19616db4eff09a87f8e91d08d46b687e794", {}),
    "sfx2/ui_pop.wav": ("86d65da044af5f270be68f666f8bbfc550e2407eac5f4b0da9d07d1fad202bde", {}),
    "sfx2/ui_tick.wav": ("e771007ab038447a23a581d3d1fef1a0450eeaac4bc56853b4f3a56fd1366a66", {}),
    "sfx2/whoosh_long.wav": ("65cdd56cfab7e442ce60a980e7432b97198ffaf9d7be8f367e9d99cec8ebfa51", {}),
    "sfx2/whoosh_soft_a.wav": ("22da43e7dc12bc2f354b6e42e810c6254d5f66e4961762a05d101faa0e2c5d02", {}),
    "sfx2/whoosh_soft_b.wav": ("e8ee16c779e7b506bca8017715bfa57b7b5574f3e1458a09c1a5f471dd6e325b", {}),
    "sfx2/whoosh_soft_c.wav": ("939e6f65da4a0c587da643ba06097920f1aae2c8bd1296ad208ca58bd460bc97", {}),
    # --- sfx2/remotion: CC0 from @remotion/sfx, conformed by analysis/fetch_remotion_sfx.py -------------------------
    "sfx2/remotion/whoosh.wav": ("ef6ff1f46c0568733a20764db850ee5db87a3bcd260149735e7b043f3d78c818", {}),
    # --- sfx (v1 kit, ElevenLabs takes): only the two that pass the screen ------------------------------------------
    "sfx/pen_tick_1.mp3": ("21d9661a3eb973f0315d01f8729b9b8364a500f5ddbbf06d86db7c6f38a3ae30", {}),
    "sfx/key_click_1.mp3": ("6fa4a795b103543c6157d3647abe07b2e9492edd5b652eae68aad4f8bd866265", {
        "EDGE": "-57 dB re peak at the file edge: inaudible; soft key, otherwise clean (designer review 7 Oct)"}),
    # NOT whitelisted, recommended for removal (screen 7 Oct): confirm_chime_1 (68 % > 4 kHz, starts mid-signal),
    # enter_key_1 (+1.1 dBTP: clips on playback), key_click_2 (starts mid-signal, -15 dB step = click),
    # mouse_click_1 (86 % > 4 kHz), paper_slide_1 (60 % flat HF noise = hiss, + pitch dive), pen_line_1 (crackle),
    # riser_1 (+1.4 dBTP), scan_sweep_1 (100 % > 4 kHz whistle), typewriter_1 (hiss + harsh broadband onset),
    # typewriter_2 (+1.4 dBTP, HF-heavy), ui_blip_1 / ui_blip_2 (99 % > 4 kHz), ui_tick_1 (80 % > 4 kHz),
    # whoosh_fast_1 / whoosh_fast_2 / whoosh_soft_1 (over 0 dBTP and start/end mid-signal).
}

# --------------------------------------------------------------------------------------------------- screen limits
LIM = dict(
    tp_dbtp=-1.0,          # HOT: true peak above this
    edge_db=-60.0,         # EDGE: first / last sample louder than this re peak (click at start / end)
    onset_rise_db=24.0,    # an onset = envelope rise of >= this within 6 ms ...
    onset_level_db=-12.0,  # ... reaching within 12 dB of the file's peak
    onset_flat=0.30,       # HARSH_ONSET: onset spectrum this flat (noise-like) ...
    onset_hf=0.45,         # ... with this share of its energy above 2 kHz
    onset_low=0.45,        # THUMP: onset whose first 40 ms has this share below 500 Hz ...
    ring_db=-18.0,         # ... and whose < 500 Hz body 60-80 ms later is still above this re its first 10 ms
    noisy_frac=0.30,       # NOISY_HF: share of active energy in frames that are flat (> 0.30) and HF (> 0.35)
    crackle_rate=6.0,      # CRACKLE: micro-transients per active second
    abrupt_db=30.0,        # ABRUPT_END: drop of >= this within 10 ms from within 6 dB of peak
    hf_heavy=0.50,         # HF_HEAVY: share of all energy above 4 kHz
    dive_oct=2.5,          # PITCH_DIVE: centroid fall (octaves) within 1 s at near-full level
)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path):
    return Path(path).resolve().relative_to(AUDIO.resolve()).as_posix()


def audio_files():
    out = []
    for d in sorted(AUDIO.glob("sfx*")):
        if d.is_dir():
            out += [p for p in sorted(d.rglob("*")) if p.is_file() and p.suffix.lower() in AUDIO_EXT]
    return out


def resolve_cue(name):
    """Cue name -> path under public/audio. 'glass_seal' -> sfx2/glass_seal.wav; 'remotion/whoosh' ->
    sfx2/remotion/whoosh.wav; an explicit relative path ('sfx2/x.wav') is taken as is."""
    name = str(name).strip().replace("\\", "/")
    cands = []
    if "." in Path(name).name:
        cands += [AUDIO / name, AUDIO / "sfx2" / name]
    else:
        cands += [AUDIO / "sfx2" / f"{name}.wav", AUDIO / "sfx2" / "remotion" / f"{name}.wav", AUDIO / f"{name}.wav"]
    for c in cands:
        if c.exists():
            return c
    return cands[0]


# --------------------------------------------------------------------------------------------------- screen
def screen(path):
    """Measure one file; returns a dict of features + 'flags'."""
    x = read_audio(path)
    xs = np.atleast_2d(x)
    mono = xs.mean(axis=0)
    n = len(mono)
    pk = float(np.abs(xs).max()) + 1e-12
    r = dict(file=str(path), dur=round(n / SR, 3), peak_dbfs=round(float(todb(pk)), 2),
             tp_dbtp=round(true_peak_db(xs), 2))
    flags = {}
    if r["tp_dbtp"] > LIM["tp_dbtp"]:
        flags["HOT"] = f"true peak {r['tp_dbtp']} dBTP > {LIM['tp_dbtp']}"
    # clipping: >= 3 consecutive samples pinned at the (near full-scale) maximum
    if pk >= 0.98:
        pinned = (np.abs(xs) >= 0.999 * pk).any(axis=0).astype(np.int8)
        runs = np.diff(np.concatenate(([0], pinned, [0])))
        lens = np.nonzero(runs == -1)[0] - np.nonzero(runs == 1)[0]
        if np.any(lens >= 3):
            flags["CLIP"] = f"{int(np.sum(lens >= 3))} flat-topped runs at {r['peak_dbfs']} dBFS"
    edge = max(np.abs(xs[:, 0]).max(), np.abs(xs[:, -1]).max())
    r["edge_db"] = round(float(todb(edge / pk)), 1)
    if r["edge_db"] > LIM["edge_db"]:
        flags["EDGE"] = f"starts/ends {r['edge_db']} dB re peak (click risk)"
    # frame spectra
    f, _, Z = signal.stft(mono, fs=SR, nperseg=1024, noverlap=768)
    P = np.abs(Z) ** 2
    fp = P.sum(axis=0) + 1e-20
    act = fp > fp.max() * 1e-5
    band = (f >= 150) & (f <= 16000)
    flat = np.exp(np.mean(np.log(P[band] + 1e-20), axis=0)) / (np.mean(P[band], axis=0) + 1e-20)
    hf = P[f >= 4000].sum(axis=0) / fp
    harsh = P[(f >= 2000) & (f < 6000)].sum(axis=0) / fp
    w = fp * act
    r["flat_w"] = round(float(np.sum(flat * w) / np.sum(w)), 3)
    r["hf4k_w"] = round(float(np.sum(hf * w) / np.sum(w)), 3)
    r["band2_6k_w"] = round(float(np.sum(harsh * w) / np.sum(w)), 3)
    noisy = act & (flat > 0.30) & (hf > 0.35)
    r["noisy_hf"] = round(float(np.sum(fp[noisy]) / np.sum(fp[act])), 3)
    if r["noisy_hf"] > LIM["noisy_frac"]:
        flags["NOISY_HF"] = f"{r['noisy_hf']:.0%} of the energy is flat high-frequency noise (static/sizzle/hiss)"
    # envelope (0.5 ms hops) and crest factor
    hop = 24
    m = n // hop
    env = np.abs(mono[: m * hop]).reshape(m, hop).max(axis=1) + 1e-12
    edb = todb(env / pk)
    act_s = env > pk * 10 ** (-50 / 20)
    rms_act = np.sqrt(np.mean(mono[: m * hop].reshape(m, hop)[act_s] ** 2)) if act_s.any() else 1e-12
    r["crest_db"] = round(float(todb(pk / rms_act)), 1)
    # sharp onsets: rise of >= onset_rise_db within 6 ms (silence assumed before the file start, so a file that
    # starts mid-transient counts), reaching within onset_level_db of the peak
    pad = np.concatenate([np.full(12, -200.0), edb])
    prev_min = np.lib.stride_tricks.sliding_window_view(pad[:-1], 12).min(axis=1)[:m]
    on = np.nonzero((edb >= LIM["onset_level_db"]) & (edb - prev_min >= LIM["onset_rise_db"]))[0]
    onsets, last = [], -10 ** 9
    for i in on:
        if i - last > 40:
            onsets.append(i)
            last = i
    r["onsets"] = len(onsets)
    worst = None
    low = None
    for i in onsets:
        seg = mono[i * hop: i * hop + int(0.010 * SR)]
        if len(seg) < 64:
            continue
        sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), 2048)) ** 2
        ff = np.fft.rfftfreq(2048, 1 / SR)
        b = (ff >= 150) & (ff <= 16000)
        fl = float(np.exp(np.mean(np.log(sp[b] + 1e-20))) / (np.mean(sp[b]) + 1e-20))
        h2 = float(sp[ff >= 2000].sum() / (sp.sum() + 1e-20))
        seg40 = mono[i * hop: i * hop + int(0.040 * SR)]
        sp40 = np.abs(np.fft.rfft(seg40 * np.hanning(len(seg40)), 4096)) ** 2
        f40 = np.fft.rfftfreq(4096, 1 / SR)
        lo = float(sp40[f40 < 500].sum() / (sp40.sum() + 1e-20))
        if worst is None or fl * h2 > worst[0] * worst[1]:
            worst = (fl, h2, lo, i * hop / SR)
        if fl > LIM["onset_flat"] and h2 > LIM["onset_hf"]:
            flags["HARSH_ONSET"] = (f"noise-like broadband onset at {i * hop / SR:.3f}s (flatness {fl:.2f}, "
                                    f"{h2:.0%} above 2 kHz)")
        if lo > LIM["onset_low"]:
            # an impact's low body rings: the < 500 Hz RMS 60-80 ms after the hit is within ring_db of its first 10 ms
            # (calibrated: banned impacts / stamp / boom >= -14 dB, soft key and UI clicks <= -22 dB)
            if low is None:
                low = signal.sosfilt(signal.butter(4, 500, "lowpass", fs=SR, output="sos"), mono)
                w10 = int(0.010 * SR)
                q10 = len(low) // w10
                low_top = np.sqrt(np.max(np.mean(low[: q10 * w10].reshape(q10, w10) ** 2, axis=1))) if q10 else 1e-12
            s0 = i * hop
            a0 = np.sqrt(np.mean(low[s0: s0 + int(0.010 * SR)] ** 2)) + 1e-12
            b0 = low[s0 + int(0.060 * SR): s0 + int(0.080 * SR)]
            ring = 20 * np.log10(np.sqrt(np.mean(b0 ** 2)) / a0 + 1e-12) if len(b0) else -99.0
            if a0 < low_top * 10 ** (-12 / 20):  # the hit itself carries little low energy (a tick on a tail)
                continue
            r["ring_db"] = round(float(max(ring, r.get("ring_db", -99.0))), 1)
            if ring >= LIM["ring_db"]:
                flags["THUMP"] = (f"impact-like hit at {i * hop / SR:.3f}s ({lo:.0%} of its first 40 ms below 500 Hz, "
                                  f"low body still at {ring:.0f} dB 60-80 ms later)")
    if worst:
        r["onset_flat"], r["onset_hf2k"], r["onset_low500"] = round(worst[0], 3), round(worst[1], 3), round(worst[2], 3)
    if r["hf4k_w"] > LIM["hf_heavy"]:
        flags["HF_HEAVY"] = f"{r['hf4k_w']:.0%} of the energy above 4 kHz (thin / hissy / sibilant)"
    # pitch dive (tape-stop-like): spectral centroid falls > dive_oct octaves within 1 s at near-full level
    lvl = 10 * np.log10(fp / fp.max())
    cen = np.sum(P * f[:, None], axis=0) / fp
    fr_hop = 256 / SR
    loud_fr = lvl > -12.0
    span = int(1.0 / fr_hop)
    best = 0.0
    idx = np.nonzero(loud_fr)[0]
    for j in idx[::4]:
        k2 = idx[(idx > j) & (idx <= j + span)]
        if len(k2):
            drop = np.log2(cen[j] / max(cen[k2].min(), 20.0))
            best = max(best, drop)
    r["centroid_drop_oct"] = round(float(best), 2)
    loud_span = (idx[-1] - idx[0]) * fr_hop if len(idx) else 0.0
    if best > LIM["dive_oct"] and loud_span >= 0.35:  # clicks (highs decay before the body) are not dives
        flags["PITCH_DIVE"] = f"spectral centroid falls {best:.1f} octaves within 1 s at near-full level (tape-stop?)"
    # crackle: 1 ms micro-transients in the > 3 kHz band, 15 dB over their local median
    hp = signal.sosfilt(signal.butter(4, 3000, "highpass", fs=SR, output="sos"), mono)
    k = int(0.001 * SR)
    q = len(hp) // k
    if q > 40:
        e = np.mean(hp[: q * k].reshape(q, k) ** 2, axis=1) + 1e-20
        med = median_filter(e, size=31, mode="nearest")
        loud = e > (pk ** 2) * 10 ** (-45 / 10)
        spikes = np.nonzero((e > med * 10 ** 1.5) & loud)[0]
        cnt = int(np.sum(np.diff(np.concatenate(([-5], spikes))) > 3)) if len(spikes) else 0
        act_sec = max(float(np.sum(act_s)) * hop / SR, 0.05)
        r["crackle_per_s"] = round(cnt / act_sec, 2)
        if cnt >= 4 and r["crackle_per_s"] > LIM["crackle_rate"]:
            flags["CRACKLE"] = f"{cnt} micro-transients ({r['crackle_per_s']}/s) in the >3 kHz band"
    # abrupt ending: after a sustained loud passage (>= 50 ms within 6 dB of peak in the 150 ms before), a fall of
    # >= abrupt_db within 10 ms - or the file simply stops while still loud. Clicks (loud for 1-3 ms) are exempt.
    loud_i = np.nonzero(edb >= -6.0)[0]
    if len(loud_i):
        j = loud_i[-1]
        sustained = np.sum(edb[max(0, j - 300): j + 1] >= -6.0) >= 100
        after = edb[j: j + 21]
        if sustained and len(after) == 21 and after.min() < -6.0 - LIM["abrupt_db"]:
            flags["ABRUPT_END"] = f"falls {(-6.0 - after.min()):.0f}+ dB within 10 ms at {j * hop / SR:.3f}s"
        elif len(after) < 21 and j * hop / SR > 0.05:
            flags["ABRUPT_END"] = "file ends while still within 6 dB of its peak"
    r["flags"] = flags
    return r


def fmt(r):
    keys = ("dur", "tp_dbtp", "edge_db", "crest_db", "flat_w", "hf4k_w", "band2_6k_w", "noisy_hf", "onsets",
            "onset_flat", "onset_hf2k", "onset_low500", "ring_db", "crackle_per_s", "centroid_drop_oct")
    return " ".join(f"{k}={r.get(k, '-')}" for k in keys)


# --------------------------------------------------------------------------------------------------- checks
def load_cues(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return d.get("sfx", []) if isinstance(d, dict) else d


def run(cues_path=None, verbose=False):
    fails, notes = [], []
    files = audio_files()
    on_disk = {rel(p): p for p in files}
    # (a) whitelist + pins
    for r_, p in on_disk.items():
        if r_ not in WHITELIST:
            fails.append(f"(a) not whitelisted: public/audio/{r_}")
        elif WHITELIST[r_][0] != sha256(p):
            fails.append(f"(a) content changed since review (SHA-256 mismatch): public/audio/{r_}")
    for r_ in WHITELIST:
        if r_ not in on_disk:
            notes.append(f"whitelisted but absent (fine): {r_}")
    # (b) banned names (files and folders)
    for r_ in on_disk:
        for part in Path(r_).parts:
            if BANNED.search(Path(part).stem):
                fails.append(f"(b) banned name: public/audio/{r_} ('{BANNED.search(Path(part).stem).group(0)}')")
                break
    # (c) cue sheet
    cp = Path(cues_path) if cues_path else (CUES if CUES.exists() else CUES_DEMO)
    if cp.exists():
        if not cues_path and cp == CUES_DEMO:
            notes.append(f"public/data/cues.json not written yet - checked the demo sheet {cp.relative_to(ROOT)}")
        cues = load_cues(cp)
        for c in cues:
            nm = str(c.get("name", ""))
            if BANNED.search(nm):
                fails.append(f"(b) banned cue name '{nm}' at t={c.get('t')}")
            p = resolve_cue(nm)
            if not p.exists():
                fails.append(f"(c) cue '{nm}' at t={c.get('t')} -> missing file {p.relative_to(ROOT)}")
            elif rel(p) not in WHITELIST:
                fails.append(f"(c) cue '{nm}' at t={c.get('t')} -> not whitelisted {rel(p)}")
        notes.append(f"{len(cues)} cues checked in {cp.relative_to(ROOT) if cp.is_relative_to(ROOT) else cp}")
    else:
        notes.append("no cue sheet found (public/data/cues.json or out/audio/cues-demo.json)")
    # (d) acoustic screen
    for r_, p in on_disk.items():
        res = screen(p)
        ack = WHITELIST.get(r_, ("", {}))[1]
        open_flags = {k: v for k, v in res["flags"].items() if k not in ack}
        if verbose or res["flags"]:
            state = "ack" if res["flags"] and not open_flags else ("FLAG" if open_flags else "ok")
            print(f"  [{state:4s}] {r_:38s} {fmt(res)}")
            for k, v in res["flags"].items():
                print(f"         {k}: {v}" + (f"   <- acknowledged: {ack[k]}" if k in ack else ""))
        if r_ in WHITELIST and open_flags:
            fails.append(f"(d) unreviewed screen flags on {r_}: {', '.join(open_flags)}")
    return fails, notes, len(on_disk)


def print_whitelist():
    print("WHITELIST = {")
    for p in audio_files():
        r_ = rel(p)
        res = screen(p)
        ack = WHITELIST.get(r_, ("", {}))[1]
        fl = {k: ack.get(k, "TODO reviewer note: " + v) for k, v in res["flags"].items()}
        ban = " # BANNED NAME" if any(BANNED.search(Path(x).stem) for x in Path(r_).parts) else ""
        print(f'    "{r_}": ("{sha256(p)}", {json.dumps(fl, ensure_ascii=False)}),{ban}')
    print("}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cues", help="cue sheet to check (default public/data/cues.json, else the demo sheet)")
    ap.add_argument("--screen", nargs="+", help="screen these files only (no whitelist checks)")
    ap.add_argument("--print-whitelist", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true", help="print the screen line for every file")
    a = ap.parse_args()
    if a.screen:
        bad = 0
        for f in a.screen:
            r = screen(f)
            print(f"{'FLAG' if r['flags'] else 'ok  '} {Path(f).name:34s} {fmt(r)}")
            for k, v in r["flags"].items():
                print(f"       {k}: {v}")
            bad += bool(r["flags"])
        print(f"{bad} of {len(a.screen)} flagged")
        return 0
    if a.print_whitelist:
        print_whitelist()
        return 0
    fails, notes, n = run(a.cues, a.verbose)
    for s in notes:
        print("note:", s)
    if fails:
        print(f"\nFAIL - {len(fails)} problem(s) in {n} audio files under public/audio/sfx*:")
        for s in fails:
            print("  ", s)
        return 1
    print(f"\nPASS - {n} audio files whitelisted, pinned, clean names, cues resolve, screen clean or reviewed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
