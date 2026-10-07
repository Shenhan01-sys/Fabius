"""Forced alignment of a known script against speech, with pocketsphinx (offline; its US English acoustic
model and dictionary ship inside the wheel, so nothing is downloaded).

align_line(samples, sr, text) -> [{ w, start, end, syl? }] in seconds from the start of `samples`.
Display tokens that are said as several words (ERC-8004, x402, 97 …, see script.SPOKEN) get `syl` spans,
one per spoken word, so each part can light up when it is said. Word edges are tightened to the voiced
frames inside each aligned span (the decoder hands trailing silence to the word before it).
"""
import subprocess
import numpy as np

import script as S

SR16 = 16000
FRAME = 0.01  # pocketsphinx frames are 10 ms


def to16k(samples: np.ndarray, sr: int) -> bytes:
    if sr == SR16 and samples.dtype == np.int16:
        return samples.tobytes()
    x = np.asarray(samples, np.float32)
    return subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", "-ar", str(SR16), "-f", "s16le", "-"],
        input=x.tobytes(), capture_output=True, check=True,
    ).stdout


def voiced_mask(pcm16: bytes) -> np.ndarray:
    y = np.frombuffer(pcm16, np.int16).astype(np.float32) / 32768
    n = len(y) // 160
    db = 20 * np.log10(np.sqrt((y[: n * 160].reshape(n, 160) ** 2).mean(1) + 1e-12) + 1e-9)
    return db > np.percentile(db, 99) - 32


def decoder():
    from pocketsphinx import Decoder
    d = Decoder(samprate=SR16)
    for w, ph in S.EXTRA_DICT.items():
        if d.lookup_word(w) is None:
            d.add_word(w, ph, True)
    return d


def segments(pcm16: bytes, words: list[str], dec=None):
    """Aligned (word, start_s, end_s) for `words` (lower-case dictionary words, in order)."""
    d = dec or decoder()
    missing = [w for w in words if d.lookup_word(w) is None]
    if missing:
        raise KeyError(f"not in the aligner's dictionary: {missing} (add them to script.EXTRA_DICT)")
    d.set_align_text(" ".join(words))
    d.start_utt()
    d.process_raw(pcm16, full_utt=True)
    d.end_utt()
    out = []
    for s in d.seg():
        w = s.word.split("(")[0]
        if w in ("<s>", "</s>", "<sil>") or w.startswith("["):
            continue
        out.append((w, s.start_frame * FRAME, (s.end_frame + 1) * FRAME))
    got = [w for w, _, _ in out]
    if got != words:
        raise RuntimeError(f"alignment did not follow the script:\n want {words}\n  got {got}")
    return out


def tighten(segs, voiced):
    """Trim each span to its voiced frames, then close unvoiced gaps shorter than 90 ms."""
    res = []
    for w, a, b in segs:
        i0, i1 = int(round(a / FRAME)), int(round(b / FRAME))
        v = np.where(voiced[i0:i1])[0]
        if len(v) and (v[-1] - v[0] + 1) * FRAME >= 0.05:
            a, b = (i0 + v[0]) * FRAME, (i0 + v[-1] + 1) * FRAME
        res.append([w, a, b])
    for k in range(len(res) - 1):
        if 0 < res[k + 1][1] - res[k][2] < 0.09:
            res[k][2] = res[k + 1][1]
    return res


def to_display(text: str, segs) -> list[dict]:
    out, k = [], 0
    for tok in text.split(" "):
        n = len(S.spoken(tok))
        parts = segs[k:k + n]
        k += n
        if not parts:
            out.append({"w": tok, "start": None, "end": None})
            continue
        wd = {"w": tok, "start": round(parts[0][1], 3), "end": round(parts[-1][2], 3)}
        if n > 1:
            wd["syl"] = [[round(a, 3), round(b, 3)] for _, a, b in parts]
        out.append(wd)
    for i, wd in enumerate(out):  # unspoken tokens sit in the pause between their neighbours
        if wd["start"] is None:
            prev = next((x for x in reversed(out[:i]) if x["start"] is not None), None)
            nxt = next((x for x in out[i + 1:] if x["start"] is not None), None)
            wd["start"] = prev["end"] if prev else (nxt["start"] if nxt else 0)
            wd["end"] = nxt["start"] if nxt else wd["start"]
    return out


def align_line(samples, sr, text, dec=None):
    pcm = to16k(samples, sr)
    words = [w for tok in text.split(" ") for w in S.spoken(tok)]
    return to_display(text, tighten(segments(pcm, words, dec), voiced_mask(pcm)))
