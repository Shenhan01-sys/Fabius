"""Captions for viewers without sound: SubRip (.srt) and WebVTT (.vtt) from the aligned script.

Each cue is at most two rows of at most 42 characters, cut at word boundaries and timed by the words themselves.

    python analysis/captions.py        (writes render/fabius-pitch.en.srt and .vtt)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LY = json.loads((ROOT / "public" / "data" / "lyrics.json").read_text(encoding="utf-8"))
ROW, ROWS = 42, 2


def ts(t, sep=","):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def cues():
    out = []
    for l in LY["lines"]:
        ws = l["words"]
        chunk, rows, row = [], [], ""
        for w in ws:
            add = (row + " " + w["w"]).strip()
            if len(add) > ROW:
                rows.append(row)
                row = w["w"]
                if len(rows) == ROWS:
                    out.append((chunk[0]["start"], chunk[-1]["end"], "\n".join(rows)))
                    chunk, rows = [], []
            else:
                row = add
            chunk.append(w)
        if row:
            rows.append(row)
        if chunk:
            out.append((chunk[0]["start"], chunk[-1]["end"], "\n".join(rows)))
    # hold each cue a little past its last word, never into the next one
    fixed = []
    for i, (a, b, txt) in enumerate(out):
        nxt = out[i + 1][0] if i + 1 < len(out) else b + 1.5
        fixed.append((a, min(nxt - 0.02, b + 0.6), txt))
    return fixed


def main():
    cs = cues()
    out = ROOT / "render"
    out.mkdir(exist_ok=True)
    srt = "\n".join(f"{i + 1}\n{ts(a)} --> {ts(b)}\n{txt}\n" for i, (a, b, txt) in enumerate(cs))
    vtt = "WEBVTT\n\n" + "\n".join(f"{ts(a, '.')} --> {ts(b, '.')}\n{txt}\n" for a, b, txt in cs)
    (out / "fabius-pitch.en.srt").write_text(srt, encoding="utf-8")
    (out / "fabius-pitch.en.vtt").write_text(vtt, encoding="utf-8")
    print(f"{len(cs)} cues -> render/fabius-pitch.en.srt, .vtt")


if __name__ == "__main__":
    main()
