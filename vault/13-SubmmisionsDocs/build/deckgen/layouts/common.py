"""Pembantu bersama layout: geometri kanvas, penanda bagian, kartu info, dan aturan validasi."""
from __future__ import annotations

from .. import draw, iso as isomod, measure
from ..draw import Ctx, TS, add_text, card, emu, headline, marker, pill, style

W, H = 13.333, 7.5
LM = 0.65
CW = W - 2 * LM
FOOT_Y = H - 0.42


class SpecError(Exception):
    pass


def need(spec: dict, keys, where: str):
    miss = [k for k in keys if k not in spec]
    if miss:
        raise SpecError(f"{where}: kunci wajib hilang di blok `slide`: {', '.join(miss)}")


def split_section(text: str) -> tuple[str, str]:
    """'01 — The problem' -> ('01', 'The problem')."""
    for sep in ("—", "–", " - "):
        if sep in text:
            a, b = text.split(sep, 1)
            return a.strip(), b.strip()
    return "", text.strip()


def top_marker(ctx: Ctx, slide, theme, mats, section: str, y: float = 0.52):
    num, label = split_section(section)
    marker(slide.shapes, LM, y, num, label, theme, mats, ctx)


def info_card(ctx: Ctx, shapes, x, y, w, h, theme, title: str, text: str, *, tag: str | None = None, icon=None, pad: float = 0.22,
              title_size: float | None = None, text_size: float | None = None, name: str = "Card"):
    """Kartu kaca: judul tebal + teks; `tag` = mono kapital kecil di atas; `icon(shapes, cx, cy)` opsional di kiri atas."""
    card(shapes, x, y, w, h, theme, name=name)
    ix = x + pad
    iw = w - 2 * pad
    cy = y + pad
    if tag:
        add_text(shapes, ix, cy, iw, 0.22, tag, theme, style(theme, "tag"), name=f"{name} tag", ctx=ctx, fit=False)
        cy += 0.3
    ts = style(theme, "card_title", size=title_size or theme.size("card_title"))
    th = measure.block_height_in(title, iw, ts.size, 1.15, True)[0]
    add_text(shapes, ix, cy, iw, th + 0.04, title, theme, ts, name=f"{name} title", ctx=ctx)
    cy += th + 0.1
    tsz = text_size or theme.size("card")
    add_text(shapes, ix, cy, iw, y + h - cy - pad * 0.45, text, theme, style(theme, "card", size=tsz), name=f"{name} text", ctx=ctx)


def common_size(ctx: Ctx, texts, w: float, h: float, st: TS, floor: float | None = None, where: str = "") -> float:
    """Satu ukuran huruf untuk sekelompok kotak sejenis (kartu sejajar tidak boleh punya ukuran berbeda-beda)."""
    fl = floor or max(10.0, st.size * 0.6)
    best = st.size
    ok_all = True
    for t in texts:
        src = t.upper() if st.caps else t
        s, ok = measure.fit_size(src, w, h, st.size, fl, st.line * (1.05 if st.role == "display" else 1.2), st.bold, st.role == "mono", st.track)
        best = min(best, s)
        ok_all = ok_all and ok
    if not ok_all:
        ctx.warn(f"teks mungkin meluap di grup '{where}' (turun ke {best:g} pt)")
    return best
