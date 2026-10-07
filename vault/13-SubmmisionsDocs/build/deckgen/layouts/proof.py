"""Slide 9-12: produk hidup (tangkapan layar + angka snapshot), kontrak Fabius, kejujuran, peta jalan + penutup."""
from __future__ import annotations

import os

from .. import draw, iso as I, measure, xmlfx
from ..draw import TS, add_text, card, dot, halo, headline, oval, picture, pill, polyline, rect, style
from ..facts import short_addr
from .common import CW, H, LM, W, info_card, need, top_marker


def _asset(ctx, name: str) -> str:
    path = os.path.normpath(os.path.join(ctx.base_dir, name))
    if not os.path.isfile(path):
        raise FileNotFoundError(f"gambar tidak ditemukan: {path}")
    return path


# ───────────────────────────────────────────── 9. LIVE PRODUCT

def _device(ctx, shapes, theme, x, y, w, h, img, kind: str):
    p = theme.p
    bez = card(shapes, x, y, w, h, theme, radius=0.28 if kind == "phone" else 0.22, name=f"{kind} frame",
               fill=[(0, "FFFFFF", 0.14), (100, "FFFFFF", 0.04)], border=("FFFFFF", 0.24), shadow=False)
    xmlfx.effects(bez, shadow=(p["deep"], 40, 18, 0.55))
    if kind == "phone":
        inset = 0.09
        picture(shapes, _asset(ctx, img["file"]), x + inset, y + inset, w - 2 * inset, h - 2 * inset, radius=0.22, alt=img["alt"], name="Phone screen", anchor="top",
                crop=img.get("crop"))
    else:
        top = 0.36
        for i, c in enumerate(("FF5A6E", "C9BDF2", "9D86FF")):
            dot(shapes, x + 0.24 + i * 0.17, y + 0.19, 0.095, c, 0.9, name="Window dot")
        if img.get("caption"):
            add_text(shapes, x + 1.0, y + 0.08, w - 2.0, 0.22, img["caption"], theme, style(theme, "mono", size=10, align="c", color=theme.faint), anchor="m", name="URL bar", ctx=ctx, fit=False)
        picture(shapes, _asset(ctx, img["file"]), x + 0.12, y + top, w - 0.24, h - top - 0.12, radius=0.1, alt=img["alt"], name="Desktop screen", anchor="top",
                crop=img.get("crop"))


def showcase(ctx, slide, theme, spec, mats):
    need(spec, ["headline", "images", "stats", "asof"], "showcase")
    sh, p = slide.shapes, theme.p
    top_marker(ctx, slide, theme, mats, spec["section"])
    headline(slide, spec["headline"], LM, 0.98, 11.5, 0.8, theme, style(theme, "title", size=40), ctx=ctx)
    if spec.get("sub"):
        add_text(sh, LM, 1.7, 11.5, 0.4, spec["sub"], theme, style(theme, "lead", size=17), name="Sub", ctx=ctx)
    halo(sh, 4.3, 4.4, 4.6, 2.6, "6E4BFF", 0.2, steps=22, name="Halo")
    imgs = spec["images"]
    desk = next(i for i in imgs if i.get("kind", "desktop") == "desktop")
    _device(ctx, sh, theme, LM, 2.3, 7.0, 3.8, desk, "desktop")
    ph = next((i for i in imgs if i.get("kind") == "phone"), None)
    if ph:
        _device(ctx, sh, theme, 6.95, 2.72, 1.92, 3.98, ph, "phone")
    # angka hidup dari snapshot
    sx, sw = 9.15, W - LM - 9.15
    stats = spec["stats"]
    n = len(stats)
    gap = 0.12
    h = (4.15 - gap * (n - 1)) / n
    for i, s in enumerate(stats):
        y = 2.3 + i * (h + gap)
        card(sh, sx, y, sw, h, theme, radius=0.2, name=f"Stat {i + 1}")
        add_text(sh, sx + 0.22, y, 1.0, h, str(s["value"]), theme, style(theme, "stat_s", size=38, color=theme.strong, align="l"), anchor="m", name=f"Stat value {i + 1}", ctx=ctx)
        add_text(sh, sx + 1.25, y + 0.06, sw - 1.45, h - 0.12, s["label"], theme, style(theme, "card", size=12.5, line=1.25), anchor="m", name=f"Stat label {i + 1}", ctx=ctx)
    add_text(sh, LM, 6.62, CW, 0.26, spec["asof"], theme, style(theme, "mono", size=10.5, color=theme.faint), anchor="m", name="As-of line", ctx=ctx, fit=False)


# ───────────────────────────────────────────── 10. CONTRACTS

def stack(ctx, slide, theme, spec, mats):
    need(spec, ["headline", "contracts", "enforced", "external", "foot"], "stack")
    sh, p = slide.shapes, theme.p
    top_marker(ctx, slide, theme, mats, spec["section"])
    headline(slide, spec["headline"], LM, 0.98, 11.5, 0.8, theme, style(theme, "title", size=40), ctx=ctx)
    if spec.get("sub"):
        add_text(sh, LM, 1.7, 11.5, 0.4, spec["sub"], theme, style(theme, "lead", size=17), name="Sub", ctx=ctx)
    rows = spec["contracts"]
    n = len(rows)
    y0, rh, gap = 2.3, 0.78, 0.1
    lw = 7.75
    for i, r in enumerate(rows):
        y = y0 + i * (rh + gap)
        main = bool(r.get("main"))
        card(sh, LM, y, lw, rh, theme, radius=0.2, name=f"Contract {r['name']}",
             border=(p["violet2"], 0.9) if main else None, fill=[(0, p["violet"], 0.30), (100, p["violet"], 0.08)] if main else None, shadow=False)
        grp = sh.add_group_shape()
        grp.name = f"Icon {r['name']}"
        m = mats["open"] if main else mats["sealed"] if r.get("kind", "") != "token" else mats["panel2"]
        I.place(grp.shapes, LM + 0.55, y + rh / 2 + 0.02, (1.5, 1.5, 0.55), 0.33, m, f"{r['name']} slab")
        add_text(sh, LM + 1.1, y + 0.1, 3.6, 0.3, r["name"], theme, style(theme, "card_title", size=17, line=1.0), name=f"{r['name']} name", ctx=ctx)
        add_text(sh, LM + 1.1, y + 0.42, 5.0, 0.3, r["role"], theme, style(theme, "card", size=12, line=1.1), name=f"{r['name']} role", ctx=ctx)
        add_text(sh, LM + lw - 2.35, y + 0.1, 2.15, 0.26, short_addr(r["addr"]), theme, style(theme, "mono", size=11, align="r", color=theme.text), name=f"{r['name']} address", ctx=ctx, fit=False)
        if main:
            pill(sh, LM + lw - 1.62, y + 0.42, "MAIN FLOW", theme, "live", h=0.26, size=9.5, dot_on=False, ctx=ctx)
        elif r.get("flag"):
            add_text(sh, LM + lw - 2.35, y + 0.44, 2.15, 0.24, r["flag"], theme, style(theme, "mono", size=10, align="r", color=theme.faint), name=f"{r['name']} flag", ctx=ctx, fit=False)
    # kanan: yang ditegakkan kontrak + rel standar
    rx = LM + lw + 0.3
    rw = W - LM - rx
    en = spec["enforced"]
    card(sh, rx, y0, rw, 2.05, theme, radius=0.22, name="Enforced card")
    add_text(sh, rx + 0.25, y0 + 0.2, rw - 0.5, 0.24, en["title"], theme, style(theme, "tag"), name="Enforced tag", ctx=ctx, fit=False)
    cx = rx + 0.25
    for c in en["errors"]:
        cx += pill(sh, cx, y0 + 0.58, c, theme, "gap", h=0.3, size=10.5, dot_on=False, ctx=ctx, caps=False) + 0.1
    add_text(sh, rx + 0.25, y0 + 1.0, rw - 0.5, 1.0, en["text"], theme, style(theme, "card", size=13), name="Enforced text", ctx=ctx)
    ex = spec["external"]
    ey = y0 + 2.05 + 0.15
    eh = y0 + n * (rh + gap) - gap - ey
    card(sh, rx, ey, rw, eh, theme, radius=0.22, name="External card", dash="dash", border=(theme.faint, 0.6), shadow=False)
    add_text(sh, rx + 0.25, ey + 0.2, rw - 0.5, 0.24, ex["title"], theme, style(theme, "tag", color=theme.faint), name="External tag", ctx=ctx, fit=False)
    add_text(sh, rx + 0.25, ey + 0.55, rw - 0.5, eh - 0.7, ex["items"], theme, style(theme, "card", size=12.5, after=5), name="External items", ctx=ctx)
    add_text(sh, LM, 6.62, CW, 0.26, spec["foot"], theme, style(theme, "mono", size=10.5, color=theme.faint), anchor="m", name="Foot", ctx=ctx, fit=False)


# ───────────────────────────────────────────── 11. HONESTY

def honesty(ctx, slide, theme, spec, mats):
    need(spec, ["headline", "stat", "proves", "not_proves", "evidence", "ribbon"], "honesty")
    sh, p = slide.shapes, theme.p
    top_marker(ctx, slide, theme, mats, spec["section"])
    headline(slide, spec["headline"], LM, 0.98, 11.5, 0.8, theme, style(theme, "title", size=40), ctx=ctx)
    st = spec["stat"]
    halo(sh, 2.7, 3.6, 3.0, 1.9, "6E4BFF", 0.26, steps=22, name="Halo")
    add_text(sh, LM, 2.0, 4.3, 1.7, st["value"], theme, style(theme, "stat", size=112, color=theme.strong, line=0.9), name="Big number", ctx=ctx)
    add_text(sh, LM, 3.78, 4.0, 0.62, st["label"], theme, style(theme, "card_title", size=19, color=theme.strong, line=1.15), name="Big label", ctx=ctx)
    add_text(sh, LM, 4.5, 4.3, 0.62, st["sub"], theme, style(theme, "mono", size=11, color=theme.faint, line=1.35), name="Big sub", ctx=ctx)
    # dua kolom: apa yang dibuktikan / tidak
    cx = 5.0
    cw = (W - LM - cx - 0.25) / 2
    for j, (title, items, glyph, col) in enumerate((("WHAT THE CHAIN PROVES", spec["proves"], "✓", theme.accent), ("WHAT IT DOES NOT PROVE", spec["not_proves"], "—", theme.muted))):
        x = cx + j * (cw + 0.25)
        card(sh, x, 2.0, cw, 3.1, theme, radius=0.22, name=f"Column {j + 1}", dash=None if j == 0 else "dash", border=None if j == 0 else (theme.faint, 0.6))
        add_text(sh, x + 0.25, 2.2, cw - 0.5, 0.24, title, theme, style(theme, "tag", color=col), name=f"Column {j + 1} tag", ctx=ctx, fit=False)
        y = 2.6
        for it in items:
            add_text(sh, x + 0.25, y, 0.3, 0.3, glyph, theme, TS("body", 16, col, True, line=1.0), name="Glyph", ctx=ctx, fit=False)
            hh = measure.block_height_in(it, cw - 1.0, 14.5, 1.3)[0]
            add_text(sh, x + 0.62, y, cw - 0.9, hh + 0.05, it, theme, style(theme, "card", size=14.5, line=1.25, color=theme.text if j == 0 else theme.muted), name="Item", ctx=ctx)
            y += hh + 0.2
    # evidencia: tiga kartu
    ev = spec["evidence"]
    n = len(ev)
    gap = 0.22
    ew = (CW - gap * (n - 1)) / n
    for i, e in enumerate(ev):
        info_card(ctx, sh, LM + i * (ew + gap), 5.25, ew, 1.3, theme, e["title"], e["text"], name=f"Evidence {i + 1}", title_size=15, text_size=13)
    add_text(sh, LM, 6.62, CW, 0.26, spec["ribbon"], theme, style(theme, "tag", color=theme.accent, size=10.5, track=1.4), anchor="m", name="Ribbon", ctx=ctx, fit=False)


# ───────────────────────────────────────────── 12. ROADMAP + CLOSE

def roadmap(ctx, slide, theme, spec, mats):
    need(spec, ["headline", "columns", "closing", "cta"], "roadmap")
    sh, p = slide.shapes, theme.p
    top_marker(ctx, slide, theme, mats, spec["section"])
    headline(slide, spec["headline"], LM, 0.98, 11.5, 0.8, theme, style(theme, "title", size=40), ctx=ctx)
    cols = spec["columns"]
    n = len(cols)
    gap = 0.24
    cw = (CW - gap * (n - 1)) / n
    y, h = 1.95, 3.05
    kinds = {"live": ("open", "live"), "built": ("sealed", "built"), "gated": ("clear", "gated")}
    for i, c in enumerate(cols):
        x = LM + i * (cw + gap)
        mk, pk = kinds[c["state"]]
        card(sh, x, y, cw, h, theme, radius=0.22, name=f"Column {c['state']}", dash="dash" if c["state"] == "gated" else None,
             border=(theme.faint, 0.6) if c["state"] == "gated" else None, shadow=False)
        grp = sh.add_group_shape()
        grp.name = f"Icon {c['state']}"
        I.place(grp.shapes, x + 0.55, y + 0.52, (1.2, 1.2, 1.2), 0.30, mats[mk], f"{c['state']} block")
        pill(sh, x + 1.0, y + 0.22, c["chip"], theme, pk, h=0.3, size=10.5, ctx=ctx)
        add_text(sh, x + 1.0, y + 0.6, cw - 1.2, 0.5, c["title"], theme, style(theme, "card_title", size=16, line=1.05), name=f"Column {i + 1} title", ctx=ctx)
        add_text(sh, x + 0.28, y + 1.18, cw - 0.5, h - 1.3, c["items"], theme, style(theme, "card", size=13, after=5, line=1.22, color=theme.text if c["state"] == "live" else theme.muted), name=f"Column {i + 1} items", ctx=ctx)
    # penutup
    by = 5.28
    card(sh, LM, by, CW, 1.5, theme, radius=0.26, name="Closing band", fill=[(0, p["violet"], 0.34), (100, p["violet"], 0.10)], border=(p["violet2"], 0.6), shadow=False)
    add_text(sh, LM + 0.35, by + 0.12, 7.2, 0.8, spec["closing"], theme, style(theme, "headline", size=25, line=1.08, color=theme.strong), name="Closing line", ctx=ctx, fit=False)
    add_text(sh, LM + 0.35, by + 0.96, 6.6, 0.5, spec.get("tagline", ""), theme, style(theme, "card", size=12.5, line=1.1), name="Tagline", ctx=ctx, balance=True)
    cx = LM + CW - 0.3
    cy = by + 0.28
    for c in spec["cta"]:
        label = c["text"]
        w = measure.text_width_in(label.upper() if not c.get("raw") else label, 11, False, True, 0.0 if c.get("raw") else 1.0) + 0.55
        w = min(w, 4.4)
        pill(sh, cx - w, cy, label, theme, c.get("kind", "neutral"), h=0.34, size=10.5, dot_on=c.get("kind") == "live", min_w=w, ctx=ctx, caps=not c.get("raw"))
        cy += 0.42
