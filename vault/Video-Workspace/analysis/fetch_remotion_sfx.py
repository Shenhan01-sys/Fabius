"""Take the clean ones from @remotion/sfx into public/audio/sfx2/remotion/ (and record why the rest were left out).

    python -X utf8 -P analysis/fetch_remotion_sfx.py

The URLs are the ones exported by node_modules/@remotion/sfx (dist/esm/index.mjs). Remotion's docs: "All files can
be used without attribution"; licence per sound on its detail page (www.remotion.dev/docs/sfx/<name>). Each kept
file is downloaded into a fresh temporary folder, its SHA-256 compared with the pin below (a changed upstream file
stops the script), screened with analysis/check_sfx.py, then conformed to the sfx2 format: 48 kHz 24-bit, DC
removed, 2 ms / 12 ms raised-cosine edge fades (the originals start / end mid-signal), peak -1.5 dBFS. The original
hash, the processing and the licence go to public/audio/sfx2/remotion/SOURCES.json.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402

from check_sfx import screen  # noqa: E402
from dsp_v2 import ROOT, SR, butter, fade, read_audio, true_peak_db, undb, write_wav  # noqa: E402

DEST = ROOT / "public" / "audio" / "sfx2" / "remotion"

KEEP = {
    "whoosh": dict(
        url="https://remotion.media/whoosh.wav",
        sha256="d98f010fa5f03fd3f4f77418f8ba6a962d36e63357265772771c4ac69c1a63a7",
        source="1bob, freesound.org/s/831936 (via @remotion/sfx `whoosh`)",
        license="CC0 1.0 (Remotion detail page)",
        use="very short (0.15 s) low air swish: a quick cut, a small card flick; darker than sfx2 whooshes",
    ),
}
SKIP = {
    "mouse-click": "screen: HF_HEAVY (100 % of energy > 4 kHz) - thin, sharp double click; sfx2/ui_click_a/b instead",
    "switch": "screen: HF_HEAVY (71 % > 4 kHz), starts/ends mid-signal - plasticky click; sfx2/ui_click_b instead",
    "ding": "licence: Remotion says it is 'not explicitly released under a free license' (myinstants) - also 97 % "
            "of its energy in 2-6 kHz; sfx2/glass_chime_* instead",
    "shutter-modern": "screen: NOISY_HF + HARSH_ONSET + CRACKLE - mechanical clatter",
    "page-turn": "screen: HF_HEAVY (72 % > 4 kHz); the file is actually Kenney 'Draw Knife 1' (blade scrape)",
    "whip": "briefed out (a whip crack); the file is a racquet swish with a sharp crack transient",
    "snapchat-notification / mac-quack": "brand / meme sounds - not ours to borrow for a product launch",
    "vine-boom / bone-crack / record-scratch / windows-xp-error / ...": "meme, impact, crack or error sounds - banned "
            "by the client rule (screen: THUMP / CRACKLE / PITCH_DIVE / ABRUPT_END)",
}


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    kept = {}
    for name, meta in KEEP.items():
        with tempfile.TemporaryDirectory(prefix=f"remotion_{name}_") as tmp:
            req = urllib.request.Request(meta["url"], headers={"User-Agent": "Mozilla/5.0 (fabius-video sfx fetch)"})
            raw = urllib.request.urlopen(req, timeout=60).read()  # the CDN refuses Python's default agent
            h = sha256(raw)
            if h != meta["sha256"]:
                raise SystemExit(f"{name}: upstream file changed (sha256 {h}) - re-screen and re-pin before use")
            src = Path(tmp) / f"{name}.wav"
            src.write_bytes(raw)
            before = screen(src)
            x = read_audio(src)
        x = butter(x, "highpass", 22.0, 2)
        x = fade(x, 0.002, 0.012)
        x = x * undb(-1.5) / (np.abs(x).max() + 1e-12)
        tp = true_peak_db(x)
        if tp > -1.05:
            x *= undb(-1.1 - tp)
        out = DEST / f"{name}.wav"
        write_wav(out, x)
        after = screen(out)
        kept[f"{name}.wav"] = dict(
            source=meta["source"], url=meta["url"], license=meta["license"], use=meta["use"],
            original_sha256=h, processing="48 kHz 24-bit, DC high-pass 22 Hz, 2 ms / 12 ms raised-cosine edge fades, "
                                          "peak -1.5 dBFS",
            notes=f"original flags {sorted(before['flags']) or 'none'} -> after conforming {sorted(after['flags']) or 'none'}",
            sha256=sha256(out.read_bytes()), duration=round(x.shape[-1] / SR, 3), anchor=0.0)
        print(f"kept {name}: {kept[f'{name}.wav']['notes']}")
    doc = dict(kept=kept, skipped=SKIP,
               policy="Taken only if CC0 / free, screened clean (analysis/check_sfx.py) and in the glassy-soft brief.")
    (DEST / "SOURCES.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    # keep the library manifest + README in step
    man_p = DEST.parent / "manifest.json"
    if man_p.exists():
        import sfx_synth
        man = json.loads(man_p.read_text(encoding="utf-8"))
        man["remotion"] = doc
        man_p.write_text(json.dumps(man, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        sfx_synth.write_readme(man)
    print(f"{len(kept)} kept, {len(SKIP)} groups skipped -> {DEST}")


if __name__ == "__main__":
    main()
