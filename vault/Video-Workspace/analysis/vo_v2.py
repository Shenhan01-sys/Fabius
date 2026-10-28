"""Voiceover v2: the script line by line -> one neural TTS read per line -> trimmed, joined with chosen pauses ->
public/audio/voiceover.wav (48 kHz) + public/data/vo.json (word timings straight from the TTS word boundaries, so the
words are the script's own words: no recognition step that could mishear them).

TTS = edge-tts (Microsoft neural voices through Edge's read-aloud service). USULAN: the voice and the service are the
builder's call (LB20) - the licence for publishing that service's audio is a grey area; Kokoro (Apache-2.0) is the
fallback. Lines are cached in out/vo-cache by (voice, rate, text), so re-running only fetches changed lines.

  python -X utf8 analysis/vo_v2.py [--voice en-US-AndrewMultilingualNeural] [--rate +0%] [--samples]
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(ROOT, "out", "vo-cache")
SR = 48_000

# (id, scene, text shown in captions, spoken form or None, pause AFTER the line in seconds)
SCRIPT: list[tuple[str, str, str, str | None, float]] = [
    ("hook1", "hook", "Every trading bot has a perfect track record.", None, 0.45),
    ("hook2", "hook", "The catch? It's always written after the market moves.", None, 0.85),
    ("rev1", "reveal", "So we built the opposite.", None, 0.40),
    ("rev2", "reveal", "Meet Fabius. It seals every signal on BNB Chain, before the market answers.", None, 0.80),
    ("rule1", "rules", "First, the rules.", None, 0.30),
    ("rule2", "rules", "Each bot's strategy is locked on-chain, so it can't be quietly rewritten after a bad day.", None, 0.70),
    ("seal1", "seal", "Every day, the candle closes, the bot makes its call,", None, 0.15),
    ("seal2", "seal", "and Fabius seals it with a timestamp no one can change. Not even us.", None, 0.80),
    ("desk1", "desk", "Who picks the bot? A desk of AI agents.", None, 0.35),
    ("desk2", "desk", "Every five minutes, analysts with their own on-chain identities make their picks,", None, 0.15),
    ("desk3", "desk", "and a locked formula turns them into one paper portfolio, sealed before the cycle ends.", None, 0.80),
    ("use1", "use", "Want today's signal?", None, 0.25),
    ("use2", "use", "Get it on the web, in Telegram, or let your AI agent fetch it over MCP.", None, 0.30),
    ("use3", "use", "Pay per signal with x402. No gas, no subscription, and it arrives with its proof.",
     "Pay per signal with x-four-oh-two. No gas, no subscription, and it arrives with its proof.", 0.80),
    ("ver1", "verify", "Then check it yourself.", None, 0.25),
    ("ver2", "verify", "Pick any bot, any day. Fabius rebuilds the signal from public data and the chain.", None, 0.30),
    ("ver3", "verify", "No key. No gas.", None, 0.75),
    ("open1", "open", "Got your own bot, or your own agent? Bring it.", None, 0.25),
    ("open2", "open", "It faces the same public gates as ours.", None, 0.80),
    ("end1", "honest", "No profit promises. It's paper money on testnet,", None, 0.15),
    ("end2", "honest", "and zero of six bots have passed the forward test yet.", None, 0.45),
    ("end3", "end", "Fabius waits for proof.", None, 0.55),
    ("end4", "end", "Don't trust. Check it.", None, 0.0),
]
LEAD_IN = 0.60  # silence before the first word
TAIL = 4.20  # end card after the last word


FORMAT = "audio-24khz-96kbitrate-mono-mp3"  # the library asks for 48 kbit/s; the service also serves 96 kbit/s (tested 7 Oct)


def key(voice: str, rate: str, text: str) -> str:
    return hashlib.sha256(f"{voice}|{rate}|{FORMAT}|{text}".encode()).hexdigest()[:16]


def _swap(code, old: str, new: str):
    """Replace a string constant inside a (nested) code object - used to change the library's fixed output format."""
    import types
    consts = []
    for c in code.co_consts:
        if isinstance(c, str) and old in c:
            consts.append(c.replace(old, new))
        elif isinstance(c, types.CodeType):
            consts.append(_swap(c, old, new))
        else:
            consts.append(c)
    return code.replace(co_consts=tuple(consts))


async def tts(voice: str, rate: str, text: str) -> tuple[bytes, list[dict]]:
    import edge_tts
    import edge_tts.communicate as cm
    fn = cm.Communicate._Communicate__stream
    fn.__code__ = _swap(fn.__code__, "audio-24khz-48kbitrate-mono-mp3", FORMAT)  # idempotent
    com = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    audio, words = bytearray(), []
    async for ch in com.stream():
        if ch["type"] == "audio":
            audio += ch["data"]
        elif ch["type"] == "WordBoundary":
            words.append({"w": ch["text"], "start": ch["offset"] / 1e7, "end": (ch["offset"] + ch["duration"]) / 1e7})
    return bytes(audio), words


def fetch(voice: str, rate: str, text: str) -> tuple[np.ndarray, list[dict]]:
    os.makedirs(CACHE, exist_ok=True)
    k = key(voice, rate, text)
    mp3, js = os.path.join(CACHE, k + ".mp3"), os.path.join(CACHE, k + ".json")
    if not (os.path.exists(mp3) and os.path.exists(js)):
        data, words = asyncio.run(tts(voice, rate, text))
        if not data or not words:
            raise SystemExit(f"TTS returned nothing for: {text!r}")
        open(mp3, "wb").write(data)
        json.dump(words, open(js, "w", encoding="utf-8"))
    wav = os.path.join(CACHE, k + ".wav")
    if not os.path.exists(wav):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ar", str(SR), "-ac", "1", "-c:a", "pcm_f32le", wav], check=True)
    x, sr = sf.read(wav, dtype="float32")
    assert sr == SR
    return x, json.load(open(js, encoding="utf-8"))


def trim(x: np.ndarray, words: list[dict]) -> tuple[np.ndarray, float]:
    """Cut leading/trailing silence (keeps 40 ms before the first and 120 ms after the last audible sample).
    Returns the trimmed audio and the seconds removed at the start (word times shift by that)."""
    env = np.convolve(np.abs(x), np.ones(240) / 240, mode="same")
    thr = max(1e-4, 0.02 * float(env.max()))
    idx = np.nonzero(env > thr)[0]
    a = max(0, int(idx[0]) - int(0.04 * SR))
    b = min(len(x), int(idx[-1]) + int(0.12 * SR))
    # never cut into a word the TTS says is there
    a = min(a, int(max(0.0, words[0]["start"] - 0.02) * SR))
    b = max(b, int((words[-1]["end"] + 0.05) * SR))
    y = x[a:b].copy()
    f = int(0.008 * SR)
    y[:f] *= np.linspace(0, 1, f, dtype=np.float32)
    y[-f:] *= np.linspace(1, 0, f, dtype=np.float32)
    return y, a / SR


def build(voice: str, rate: str, out_wav: str, out_json: str) -> dict:
    parts, lines = [np.zeros(int(LEAD_IN * SR), np.float32)], []
    t = LEAD_IN
    for lid, scene, text, spoken, gap in SCRIPT:
        x, words = fetch(voice, rate, spoken or text)
        y, cut0 = trim(x, words)
        shown = text.split()
        ws = [{"w": w["w"], "start": round(t + w["start"] - cut0, 3), "end": round(t + w["end"] - cut0, 3)} for w in words]
        if spoken:  # map spoken tokens back to the shown words (same count except the spelled-out token)
            sp = (spoken or "").split()
            if len(sp) == len(shown):
                for w, s in zip(ws, shown):
                    w["w"] = s.strip(".,?!")
            else:
                for w in ws:
                    if w["w"].lower().startswith("x-four") or w["w"].lower() in ("x", "four", "oh", "two"):
                        w["w"] = "x402"
        lines.append({"id": lid, "scene": scene, "text": text, "start": round(t, 3), "end": round(t + len(y) / SR, 3), "words": ws})
        parts.append(y)
        t += len(y) / SR
        if gap:
            parts.append(np.zeros(int(gap * SR), np.float32))
            t += gap
    parts.append(np.zeros(int(TAIL * SR), np.float32))
    audio = np.concatenate(parts)
    peak = float(np.abs(audio).max())
    audio = audio * (10 ** (-1.0 / 20) / peak)  # -1 dBFS peak; loudness is set in the mix
    os.makedirs(os.path.dirname(out_wav), exist_ok=True)
    sf.write(out_wav, audio, SR, subtype="PCM_24")
    meta = {"voice": voice, "rate": rate, "sr": SR, "duration": round(len(audio) / SR, 3), "lead_in": LEAD_IN, "tail": TAIL,
            "tts": "edge-tts (Microsoft neural, Edge read-aloud service) - USULAN, builder's call (LB20)", "lines": lines}
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    json.dump(meta, open(out_json, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return meta


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--voice", default="en-US-AvaMultilingualNeural")
    ap.add_argument("--rate", default="+0%")
    ap.add_argument("--samples", action="store_true", help="also render the whole read with alternative voices into out/vo-samples/")
    a = ap.parse_args()
    meta = build(a.voice, a.rate, os.path.join(ROOT, "public", "audio", "voiceover.wav"), os.path.join(ROOT, "public", "data", "vo.json"))
    nw = sum(len(l["words"]) for l in meta["lines"])
    print(f"voiceover.wav {meta['duration']} s | {len(meta['lines'])} lines | {nw} words | voice {a.voice} rate {a.rate}")
    for l in meta["lines"]:
        print(f"  {l['start']:6.2f}-{l['end']:6.2f}  {l['id']:6s} {l['text']}")
    if a.samples:
        for v in ("en-US-AvaMultilingualNeural", "en-US-EmmaMultilingualNeural", "en-US-BrianMultilingualNeural"):
            m = build(v, a.rate, os.path.join(ROOT, "out", "vo-samples", f"{v}.wav"), os.path.join(ROOT, "out", "vo-samples", f"{v}.json"))
            print(f"sample {v}: {m['duration']} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
