"""Slide 1-4: sampul, masalah (klaim setelah kejadian), celah kepercayaan, ide (komit sebelum hasil)."""
from __future__ import annotations

import math
import random

from .. import draw, iso as I, xmlfx
from ..draw import TS, add_text, card, dot, emu, halo, headline, oval, pill, polyline, rect, style
from .common import CW, H, LM, W, info_card, need, top_marker


# ───────────────────────────────────────────── 1. COVER

def cover(ctx, slide, theme, spec, mats):
    need(spec, ["title", "hook", "tagline"], "cover")
    sh = slide.shapes
    p = theme.p
    cx, cy, k = 9.6, 3.95, 0.70
    halo(sh, cx, cy + 0.1, 4.3, 3.6, "7B5CFF", 0.42, steps=30, name="Halo")
    grp = sh.add_group_shape()
    grp.name = "Scene · sealed crystal"
    iso = I.Iso(cx, cy, k)
    g = 0.045
    removed = {(2, 2, 2), (2, 1, 2), (1, 2, 2)}
    glowing = {(2, 2, 1), (1, 2, 1), (2, 1, 1), (1, 1, 2), (0, 2, 0), (2, 0, 1)}
    empty = {(0, 0, 2), (0, 1, 2), (1, 0, 2)}
    items = []
    for i in range(3):
        for j in range(3):
            for kk in range(3):
                if (i, j, kk) in removed:
                    continue
                m = mats["open"] if (i, j, kk) in glowing else mats["clear"] if (i, j, kk) in empty else mats["sealed"]
                items.append(((i + g, j + g, kk + g, i + 1 - g, j + 1 - g, kk + 1 - g), m, f"Block {i}{j}{kk}"))
    # blok yang melayang keluar: satu terbuka (SAH), satu tersegel, satu perangkat keras gelap
    items.append(((1.05, 1.05, 4.1, 1.95, 1.95, 5.0), mats["open"], "Floating block · opened"))
    items.append(((4.0, 0.7, 1.4, 4.9, 1.6, 2.3), mats["sealed"], "Floating block · sealed"))
    items.append(((-1.9, 0.3, 3.2, -0.4, 2.3, 3.45), mats["panel2"], "Floating panel"))
    items.append(((4.6, -1.9, 0.5, 6.2, -0.6, 0.78), mats["panel"], "Floating panel 2"))
    I.boxes(grp.shapes, iso, items)
    I.ring(grp.shapes, iso, 1.5, 1.5, -0.55, 4.6, p["violet2"], 0.45, 0.9, dash="dash", name="Orbit")
    I.ring(grp.shapes, iso, 1.5, 1.5, -0.55, 5.6, p["lav3"], 0.18, 0.75, name="Orbit outer")
    rnd = random.Random(7)
    for n in range(14):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(3.2, 6.2)
        z = rnd.uniform(-0.4, 5.4)
        X, Y = iso.inch(1.5 + r * math.cos(a), 1.5 + r * math.sin(a), z)
        dot(grp.shapes, X, Y, rnd.choice([0.045, 0.06, 0.035]), "C9BDF2", rnd.uniform(0.25, 0.7), name="Spark")
    # kolom teks kiri
    x, w = LM, 6.3
    add_text(sh, x, 0.7, w, 0.28, spec.get("kicker", ""), theme, style(theme, "tag"), name="Kicker", ctx=ctx, fit=False)
    headline(slide, spec["title"], x, 1.35, w, 1.45, theme, style(theme, "cover", color=theme.strong), anchor="t", ctx=ctx)
    add_text(sh, x, 2.95, w, 1.3, spec["hook"], theme, style(theme, "headline", size=34, line=1.05), name="Hook", ctx=ctx)
    add_text(sh, x, 4.4, 6.0, 1.2, spec["tagline"], theme, style(theme, "lead"), name="Tagline", ctx=ctx, balance=True)
    cx2 = x
    for c in spec.get("chips", []):
        cx2 += pill(sh, cx2, 5.85, c["text"], theme, c.get("kind", "neutral"), ctx=ctx) + 0.12
    if spec.get("url"):
        add_text(sh, x, 6.38, 6, 0.26, spec["url"], theme, style(theme, "mono", color=theme.faint), name="URL", ctx=ctx, fit=False)
    if spec.get("live"):
        add_text(sh, 7.0, 6.38, 5.7, 0.26, spec["live"], theme, style(theme, "tag", align="r", color=theme.faint), name="Live line",
                 ctx=ctx, fit=False)


# ───────────────────────────────────────────── 2. PROBLEM

def _rising_line(w, h, seed=11, n=28):
    rnd = random.Random(seed)
    pts = []
    for i in range(n):
        t = i / (n - 1)
        y = 0.88 - 0.78 * (t ** 1.35) + rnd.uniform(-0.035, 0.035) * (1 - 0.3 * t)
        pts.append((t * w, max(0.04, min(0.96, y)) * h))
    return pts


def claims_gap(ctx, slide, theme, spec, mats):
    need(spec, ["headline", "lead", "shown_label", "shown_caption", "holes", "closing"], "claims_gap")
    sh, p = slide.shapes, theme.p
    top_marker(ctx, slide, theme, mats, spec["section"])
    headline(slide, spec["headline"], LM, 1.05, 5.75, 2.2, theme, style(theme, "title", size=42, line=1.02), ctx=ctx)
    add_text(sh, LM, 3.4, 5.25, 2.5, spec["lead"], theme, style(theme, "lead", color=theme.muted, after=10), name="Lead", ctx=ctx)
    add_text(sh, LM, 5.85, 5.4, 0.9, spec["closing"], theme, style(theme, "card_title", size=19, color=theme.strong, line=1.2), name="Closing", ctx=ctx)

    # kartu "tangkapan layar": garis naik tanpa sumbu dan tanpa angka (gambar gaya, bukan data)
    x0, y0, w0, h0 = 6.55, 0.95, 6.1, 2.75
    card(sh, x0, y0, w0, h0, theme, radius=0.28, name="Screenshot card")
    add_text(sh, x0 + 0.3, y0 + 0.24, 4, 0.22, spec["shown_label"], theme, style(theme, "tag"), name="Shown label", ctx=ctx, fit=False)
    pill(sh, x0 + w0 - 1.85, y0 + 0.2, spec.get("shown_chip", "AFTER THE MOVE"), theme, "gated", h=0.28, size=10, dot_on=False, ctx=ctx)
    cx0, cy0, cw0, ch0 = x0 + 0.35, y0 + 0.75, w0 - 0.7, h0 - 1.4
    for gy in (0.2, 0.5, 0.8):
        polyline(sh, [(cx0, cy0 + ch0 * gy), (cx0 + cw0, cy0 + ch0 * gy)], p["violet"], 0.12, 0.75, dash="dash", name="Grid")
    pts = [(cx0 + a, cy0 + b) for a, b in _rising_line(cw0, ch0)]
    polyline(sh, pts, p["violet"], 0.95, 2.5, glow=(p["violet"], 5, 0.25), name="Equity curve (stylised)")
    dot(sh, pts[-1][0], pts[-1][1], 0.17, p["violet"], 1.0, glow=(p["violet2"], 8, 0.5), name="Curve end")
    add_text(sh, x0 + 0.3, y0 + h0 - 0.46, w0 - 0.6, 0.28, spec["shown_caption"], theme, style(theme, "mono", color=theme.muted), name="Shown caption",
             ctx=ctx, fit=False)

    # tiga "lubang" = semua yang tidak terlihat pembeli (merah hanya untuk bolong, aturan FE)
    holes = spec["holes"]
    n = len(holes)
    gap = 0.14
    rh = 0.86
    hy0 = y0 + h0 + 0.3
    for i, hole in enumerate(holes):
        hy = hy0 + i * (rh + gap)
        card(sh, x0, hy, w0, rh, theme, radius=0.2, name=f"Hole card {i + 1}", border=(p["gap"], 0.55), dash="dash",
             fill=[(0, p["gap"], 0.08), (100, "FFFFFF", 0.30)] if not theme.night else None)
        grp = sh.add_group_shape()
        grp.name = f"Hole icon {i + 1}"
        isoh = I.Iso(x0 + 0.62, hy + 0.58, 0.27)
        I.box(grp.shapes, isoh, (-0.5, -0.5, 0, 0.5, 0.5, 1.0), mats["gap"], "Missing block")
        a, b = isoh.inch(0.1, -0.5, 1.0)
        c2, d2 = isoh.inch(-0.1, 0.3, 0.45)
        polyline(grp.shapes, [(a, b), (a - 0.05, b + 0.14), (c2 + 0.04, d2 - 0.04), (c2 - 0.03, d2 + 0.1)], p["gap"], 0.95, 1.4, name="Crack")
        add_text(sh, x0 + 1.15, hy + 0.12, w0 - 1.4, 0.3, hole["title"], theme, style(theme, "card_title", size=16, line=1.05), name=f"Hole title {i + 1}", ctx=ctx)
        add_text(sh, x0 + 1.15, hy + 0.45, w0 - 1.4, 0.34, hole["text"], theme, style(theme, "card", size=13), name=f"Hole text {i + 1}", ctx=ctx)


# ───────────────────────────────────────────── 3. GAP

def trust_gap(ctx, slide, theme, spec, mats):
    need(spec, ["headline", "points", "pay_label", "proof_label", "gap_label"], "trust_gap")
    sh, p = slide.shapes, theme.p
    top_marker(ctx, slide, theme, mats, spec["section"])
    headline(slide, spec["headline"], LM, 0.98, 11.2, 1.6, theme, style(theme, "title", size=38, line=1.02), ctx=ctx)

    # jembatan: dua menara, tujuh lempeng (satu HILANG). Tiap blok ditaruh di posisi layar sendiri -> komposisi mendatar.
    band_y = 3.92
    k = 0.40
    grp = sh.add_group_shape()
    grp.name = "Scene · broken bridge"
    tower = (1.7, 1.7, 2.3)
    tile = (1.55, 1.55, 0.32)
    ax, bx = 1.55, W - 1.55
    I.place(grp.shapes, ax, band_y - 0.12, tower, k, mats["ink"], "Tower · agent A")
    I.place(grp.shapes, bx, band_y - 0.12, tower, k, mats["ink"], "Tower · agent B")
    n_span = 7
    x_first, x_last = ax + 1.2, bx - 1.2
    step = (x_last - x_first) / (n_span - 1)
    gap_i = 3
    gap_x = x_first + gap_i * step
    for i in range(n_span):
        sx = x_first + i * step
        I.place(grp.shapes, sx, band_y + 0.45, tile, k, mats["gap"] if i == gap_i else mats["lav"], "Missing span" if i == gap_i else f"Span {i + 1}")
    # garis pembayaran (melengkung, lolos) dan garis bukti (putus, jatuh di celah)
    top_y = band_y - 1.1
    arc = []
    for i in range(41):
        t = i / 40
        arc.append((ax + 0.2 + (bx - ax - 0.4) * t, top_y - 0.5 * 4 * t * (1 - t) + 0.25))
    polyline(grp.shapes, arc, p["violet"], 0.95, 2.4, tail="triangle", glow=(p["violet"], 5, 0.25), name="Payment path")
    dot(grp.shapes, ax + 0.2, arc[0][1], 0.44, p["violet"], 1.0, glow=(p["violet2"], 8, 0.5), name="Coin")
    add_text(sh, ax + 0.2 - 0.3, arc[0][1] - 0.15, 0.6, 0.3, "402", theme, TS("mono", 12, "FFFFFF", True, align="c", line=1.0), anchor="m", name="Coin label", ctx=ctx, fit=False)
    add_text(sh, (ax + bx) / 2 - 1.6, top_y - 0.5 - 0.1, 3.2, 0.26, spec["pay_label"], theme, style(theme, "tag", align="c"), name="Payment label", ctx=ctx, fit=False)
    proof = [(ax + 0.7, band_y - 0.2), (gap_x - 0.6, band_y - 0.2), (gap_x, band_y + 0.25), (gap_x, band_y + 0.62)]
    polyline(grp.shapes, proof, p["gap"], 0.9, 1.7, dash="dash", name="Proof path (breaks)")
    add_text(sh, gap_x - 0.2, band_y + 0.5, 0.4, 0.4, "✕", theme, TS("body", 18, p["gap"], True, align="c", line=1.0), anchor="m", name="Break mark", ctx=ctx, fit=False)
    add_text(sh, gap_x - 1.6, band_y + 0.98, 3.2, 0.5, spec["gap_label"], theme, style(theme, "tag", align="c", color=p["gap"]), name="Gap label", ctx=ctx, fit=False)
    add_text(sh, ax + 0.7, band_y - 0.62, 2.8, 0.26, spec["proof_label"], theme, style(theme, "mono", size=11, color=p["gap"]), name="Proof label", ctx=ctx, fit=False)

    pts = spec["points"]
    n = len(pts)
    gap_x2 = 0.28
    cw = (CW - gap_x2 * (n - 1)) / n
    y = 5.22
    for i, pt in enumerate(pts):
        info_card(ctx, sh, LM + i * (cw + gap_x2), y, cw, 1.62, theme, pt["title"], pt["text"], tag=pt.get("tag"), name=f"Point {i + 1}", title_size=16, text_size=13.5)


# ───────────────────────────────────────────── 4. IDEA

def seal(ctx, slide, theme, spec, mats):
    need(spec, ["headline", "sub", "stations", "principles", "closing"], "seal")
    sh, p = slide.shapes, theme.p
    top_marker(ctx, slide, theme, mats, spec["section"])
    headline(slide, spec["headline"], LM, 1.0, 6.2, 2.2, theme, style(theme, "title", size=64, line=0.98), ctx=ctx)
    add_text(sh, LM, 3.3, 5.6, 1.3, spec["sub"], theme, style(theme, "lead"), name="Sub", ctx=ctx)
    halo(sh, 9.6, 2.95, 4.2, 2.5, "7B5CFF", 0.34, steps=28, name="Halo")
    grp = sh.add_group_shape()
    grp.name = "Scene · decision before outcome"
    k = 0.46
    st = spec["stations"]
    xs = [7.55, 9.65, 11.75]
    ry = 4.28
    # sumbu waktu
    polyline(sh, [(6.75, ry), (12.55, ry)], p["lav3"], 0.55, 1.4, tail="triangle", name="Time axis")
    for x in xs:
        dot(sh, x, ry, 0.12, p["violet2"], 1.0, glow=(p["violet2"], 5, 0.5), name="Axis node")
    # 1) keputusan tersegel  2) garis tutup bar  3) hasil belum ada
    I.place(grp.shapes, xs[0], 2.85, (1.9, 1.9, 1.9), k, mats["sealed"], "Sealed decision")
    I.place(grp.shapes, xs[0], 1.7, (1.2, 1.2, 0.16), k, mats["open"], "Seal")
    I.place(grp.shapes, xs[1], 2.65, (0.28, 2.2, 3.3), k, mats["open"], "Bar close wall")
    I.place(grp.shapes, xs[2], 2.85, (1.9, 1.9, 1.9), k, mats["clear"], "Outcome (not yet)")
    for i, x in enumerate(xs):
        lab, sub = (st[i] + "|").split("|")[:2]
        add_text(sh, x - 1.0, ry + 0.2, 2.0, 0.26, lab, theme, style(theme, "tag", align="c", color=theme.strong if i == 1 else theme.accent), name=f"Station {i + 1}", ctx=ctx, fit=False)
        if sub:
            add_text(sh, x - 1.0, ry + 0.48, 2.0, 0.24, sub, theme, style(theme, "mono", align="c", color=theme.faint), name=f"Station {i + 1} sub", ctx=ctx, fit=False)
    n = len(spec["principles"])
    gx = 0.25
    cw = (CW - gx * (n - 1)) / n
    for i, pr in enumerate(spec["principles"]):
        info_card(ctx, sh, LM + i * (cw + gx), 5.12, cw, 1.32, theme, pr["title"], pr["text"], name=f"Principle {i + 1}", title_size=15, text_size=13)
    add_text(sh, LM, 6.56, CW, 0.42, spec["closing"], theme, style(theme, "lead", size=19, color=theme.text), name="Closing", ctx=ctx)
