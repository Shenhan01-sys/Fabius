"""Perkiraan lebar teks (tanpa berkas font, supaya hasilnya sama di setiap mesin).

Angka em-per-karakter dikalibrasi dengan PIL terhadap Inter dan Archivo (kalibrasi: huruf kecil Inter 0,483, Archivo 0,446, kapital
0,60) lalu DINAIKKAN ±7 % agar pengganti font (Arial, Calibri) yang lebih lebar tetap muat. Perkiraan ini dipakai untuk menyusutkan
ukuran huruf dan memberi peringatan ketika teks hampir pasti meluap; pemeriksaan akhirnya tetap render nyata (LibreOffice -> gambar).
"""
from __future__ import annotations

import math

from .markup import Run, parse

_NARROW = set(" .,;:'!|iltIj()[]/\\-—’‘\"`")


def char_em(ch: str, bold: bool, mono: bool) -> float:
    if mono:
        return 0.62
    if ch == " ":
        return 0.30
    if ch in _NARROW:
        return 0.32 if not bold else 0.34
    if ch.isdigit():
        return 0.60
    if ch.isupper():
        return 0.71 if bold else 0.68
    if ch in "mwMW":
        return 0.80
    return 0.55 if bold else 0.52


def text_width_in(text: str, size_pt: float, bold: bool = False, mono: bool = False, tracking_pt: float = 0.0) -> float:
    em = sum(char_em(c, bold, mono) for c in text)
    return (em * size_pt + tracking_pt * len(text)) / 72.0


def _words(runs: list[Run], base_bold: bool, base_mono: bool):
    out = []
    for r in runs:
        bold = base_bold or r.bold or r.accent
        mono = base_mono or r.mono
        for i, w in enumerate(r.text.split(" ")):
            out.append((w, bold, mono, i > 0))
    return out


def wrap_line_count(markup_line: str, width_in: float, size_pt: float, bold: bool = False, mono: bool = False, tracking_pt: float = 0.0) -> int:
    """Jumlah baris hasil pembungkusan satu baris-logis (greedy, per kata)."""
    runs = parse(markup_line)[0] if markup_line else []
    words = _words(runs, bold, mono)
    if not words:
        return 1
    lines, cur = 1, 0.0
    space = text_width_in(" ", size_pt, bold, mono, tracking_pt)
    for w, b, m, _ in words:
        ww = text_width_in(w, size_pt, b, m, tracking_pt)
        add = ww if cur == 0 else space + ww
        if cur > 0 and cur + add > width_in:
            lines += 1
            cur = ww
        else:
            cur += add
        while cur > width_in and ww > width_in:  # kata tunggal lebih lebar dari kotak
            lines += 1
            cur -= width_in
    return lines


def block_height_in(markup: str, width_in: float, size_pt: float, line_h: float = 1.2, bold: bool = False, mono: bool = False,
                    tracking_pt: float = 0.0, para_gap_pt: float = 0.0) -> tuple[float, int]:
    """(tinggi dalam inci, jumlah baris) untuk teks berpenanda dengan "\\n" sebagai baris baru."""
    n = 0
    for ln in str(markup).split("\n"):
        n += wrap_line_count(ln, width_in, size_pt, bold, mono, tracking_pt)
    return (n * size_pt * line_h + para_gap_pt * max(0, n - 1)) / 72.0, n


def fit_size(markup: str, width_in: float, height_in: float, max_pt: float, min_pt: float, line_h: float = 1.2, bold: bool = False,
             mono: bool = False, tracking_pt: float = 0.0) -> tuple[float, bool]:
    """Ukuran terbesar <= max_pt yang muat; (ukuran, muat?). Turun 0,5 pt per langkah."""
    s = float(max_pt)
    while s >= min_pt - 1e-9:
        h, _ = block_height_in(markup, width_in, s, line_h, bold, mono, tracking_pt)
        if h <= height_in + 1e-9:
            return s, True
        s -= 0.5
    return float(min_pt), False


def balance(text: str, width_in: float, size_pt: float, bold: bool = False, mono: bool = False, tracking_pt: float = 0.0) -> str:
    """Bila teks akan membungkus jadi dua baris, sisipkan satu baris-baru di spasi yang membuat kedua baris paling seimbang
    (menghindari kata yatim di baris kedua dan pemenggalan di tanda hubung seperti "on-\nchain")."""
    if "\n" in text or wrap_line_count(text, width_in, size_pt, bold, mono, tracking_pt) != 2:
        return text
    words = text.split(" ")
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        wa = text_width_in(a, size_pt, bold, mono, tracking_pt)
        wb = text_width_in(b, size_pt, bold, mono, tracking_pt)
        if max(wa, wb) <= width_in * 0.98 and (best is None or abs(wa - wb) < best[0]):
            best = (abs(wa - wb), a, b)
    return f"{best[1]}\n{best[2]}" if best else text


def lines_for(markup: str, width_in: float, size_pt: float, **kw) -> int:
    return block_height_in(markup, width_in, size_pt, **kw)[1]


def ceil_half(x: float) -> float:
    return math.ceil(x * 2) / 2
