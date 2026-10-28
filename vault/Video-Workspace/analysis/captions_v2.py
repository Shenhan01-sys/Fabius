"""Caption files for the v2 video from the voiceover timings (public/data/vo.json): English .srt + .vtt (the words of the
read) and an Indonesian .srt (USULAN translation, same cue times). One cue per voiceover line; long lines split at the
sentence boundary.

  python -X utf8 analysis/captions_v2.py
"""
from __future__ import annotations

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VO = json.load(open(os.path.join(ROOT, "public", "data", "vo.json"), encoding="utf-8"))

# USULAN: Indonesian subtitles (builder may edit); keys = voiceover line ids
ID = {
    "hook1": "Setiap bot trading punya rekam jejak sempurna.",
    "hook2": "Masalahnya? Selalu ditulis setelah pasar bergerak.",
    "rev1": "Jadi kami membuat kebalikannya.",
    "rev2": "Kenalkan Fabius. Setiap sinyal disegel di BNB Chain, sebelum pasar menjawab.",
    "rule1": "Pertama, aturannya.",
    "rule2": "Strategi tiap bot dikunci on-chain, jadi tidak bisa diam-diam diubah setelah hari yang buruk.",
    "seal1": "Setiap hari, candle ditutup, bot mengambil keputusan,",
    "seal2": "dan Fabius menyegelnya dengan cap waktu yang tidak bisa diubah siapa pun. Bahkan kami.",
    "desk1": "Siapa yang memilih botnya? Sebuah meja berisi agen AI.",
    "desk2": "Setiap lima menit, analis dengan identitas on-chain masing-masing menentukan pilihan,",
    "desk3": "lalu rumus yang terkunci mengubahnya menjadi satu portofolio simulasi, disegel sebelum siklus berakhir.",
    "use1": "Mau sinyal hari ini?",
    "use2": "Ambil di web, di Telegram, atau biarkan agen AI-mu mengambilnya lewat MCP.",
    "use3": "Bayar per sinyal dengan x402. Tanpa gas, tanpa langganan, dan sinyal datang bersama buktinya.",
    "ver1": "Lalu periksa sendiri.",
    "ver2": "Pilih bot mana pun, hari mana pun. Fabius menyusun ulang sinyalnya dari data publik dan chain.",
    "ver3": "Tanpa kunci. Tanpa gas.",
    "open1": "Punya bot atau agen sendiri? Bawa saja.",
    "open2": "Bot itu melewati gerbang publik yang sama dengan milik kami.",
    "end1": "Tanpa janji untung. Ini uang simulasi di testnet,",
    "end2": "dan belum ada satu pun dari enam bot yang lolos uji maju.",
    "end3": "Fabius menunggu bukti.",
    "end4": "Jangan percaya. Periksa.",
}


def ts(t: float, sep: str) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def cues(text_of) -> list[tuple[float, float, str]]:
    out = []
    for l in VO["lines"]:
        txt = text_of(l)
        words = l["words"]
        # split long lines at a sentence end that falls near the middle (by word count)
        sents = [s for s in re.split(r"(?<=[.?!])\s+", txt) if s]
        if len(sents) > 1 and len(txt) > 60 and len(sents) == len(re.split(r"(?<=[.?!])\s+", l["text"])):
            n_first = len(re.split(r"(?<=[.?!])\s+", l["text"])[0].split())
            cut_t = words[min(n_first, len(words) - 1)]["start"]
            out.append((l["start"], cut_t - 0.02, sents[0]))
            out.append((cut_t, l["end"], " ".join(sents[1:])))
        else:
            out.append((l["start"], l["end"], txt))
    return out


def write(path: str, cs, vtt: bool) -> None:
    sep = "." if vtt else ","
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        if vtt:
            f.write("WEBVTT\n\n")
        for i, (a, b, txt) in enumerate(cs, 1):
            if not vtt:
                f.write(f"{i}\n")
            f.write(f"{ts(a, sep)} --> {ts(b, sep)}\n{txt}\n\n")
    print("wrote", os.path.relpath(path, ROOT), len(cs), "cues")


def main() -> None:
    os.makedirs(os.path.join(ROOT, "render"), exist_ok=True)
    en = cues(lambda l: l["text"])
    idn = cues(lambda l: ID[l["id"]])
    write(os.path.join(ROOT, "render", "fabius-pitch-v2.en.srt"), en, False)
    write(os.path.join(ROOT, "render", "fabius-pitch-v2.en.vtt"), en, True)
    write(os.path.join(ROOT, "render", "fabius-pitch-v2.id.srt"), idn, False)


if __name__ == "__main__":
    main()
