"""Slide 5-8: rel bukti (satu sinyal), pintu platform terbuka, meja AI, kasir x402 + arus bisnis."""
from __future__ import annotations

import math

from .. import draw, iso as I, measure, xmlfx
from ..draw import TS, add_text, card, dot, emu, halo, headline, oval, pill, polyline, rect, style
from .common import CW, H, LM, W, common_size, info_card, need, top_marker


def _lines(spec_text):
    return spec_text if isinstance(spec_text, (list, tuple)) else [spec_text]


# ───────────────────────────────────────────── 5. RAIL

def rail(ctx, slide, theme, spec, mats):
    need(spec, ["headline", "stations", "lock_note", "verify_cmd"], "rail")
    sh, p = slide.shapes, theme.p
    top_marker(ctx, slide, theme, mats, spec["section"])
    headline(slide, spec["headline"], LM, 0.95, 9.0, 0.8, theme, style(theme, "title", size=40), ctx=ctx)
    if spec.get("sub"):
        add_text(sh, LM, 1.68, CW, 0.4, spec["sub"], theme, style(theme, "lead", size=17), name="Sub", ctx=ctx)
    pill(sh, LM, 2.12, spec["lock_note"], theme, "live", h=0.34, ctx=ctx)

    st = spec["stations"]
    n = len(st)
    gap = 0.25
    cw = (CW - gap * (n - 1)) / n
    ry = 4.08
    k = 0.38
    x0 = LM + cw / 2
    x1 = LM + (n - 1) * (cw + gap) + cw / 2
    halo(sh, (x0 + x1) / 2, 3.45, 5.4, 1.6, "6E4BFF", 0.14, steps=22, name="Halo")
    polyline(sh, [(x0 - 0.3, ry), (x1 + 0.45, ry)], p["lav3"], 0.5, 2.2, tail="triangle", name="Rail")
    grp = sh.add_group_shape()
    grp.name = "Scene · rail of blocks"
    title_sz = common_size(ctx, [s["title"] for s in st], cw - 0.1, 0.56, style(theme, "card_title", size=17, align="c", line=1.05), where="rail titles")
    text_sz = common_size(ctx, [s["text"] for s in st], cw - 0.1, 1.0, style(theme, "card", size=13.5, align="c"), where="rail texts")
    for i, s in enumerate(st):
        cx = LM + i * (cw + gap) + cw / 2
        state = s.get("state", "sealed")
        size = (1.35, 1.35, 1.35)
        by = 3.2
        if state == "clear":
            I.place(grp.shapes, cx, by, size, k, mats["clear"], f"Station {i + 1} · empty bar")
        elif state == "sealed":
            I.place(grp.shapes, cx, by, size, k, mats["sealed"], f"Station {i + 1} · sealed")
        elif state == "root":
            I.place(grp.shapes, cx, by, size, k, mats["sealed"], f"Station {i + 1} · sealed")
            I.place(grp.shapes, cx, by - 0.62, (0.9, 0.9, 0.14), k, mats["open"], f"Station {i + 1} · seal")
        elif state == "committed":
            I.place(grp.shapes, cx, by + 0.34, (1.6, 1.6, 0.22), k, mats["panel2"], f"Station {i + 1} · chain")
            I.place(grp.shapes, cx, by + 0.13, (1.6, 1.6, 0.22), k, mats["panel"], f"Station {i + 1} · chain")
            I.place(grp.shapes, cx, by - 0.36, size, k, mats["sealed"], f"Station {i + 1} · committed")
        else:
            I.place(grp.shapes, cx, by, size, k, mats["open"], f"Station {i + 1} · opened")
        dot(sh, cx, ry, 0.16, "F6F2FF" if state == "open" else p["violet2"], 1.0, glow=(p["violet2"], 7, 0.55), name=f"Node {i + 1}")
        add_text(sh, cx - cw / 2, ry + 0.2, cw, 0.24, s["time"], theme, style(theme, "tag", align="c"), name=f"Time {i + 1}", ctx=ctx, fit=False)
        add_text(sh, cx - cw / 2 + 0.05, ry + 0.5, cw - 0.1, 0.56, s["title"], theme, style(theme, "card_title", size=title_sz, align="c", line=1.05), name=f"Title {i + 1}", ctx=ctx, fit=False)
        add_text(sh, cx - cw / 2 + 0.05, ry + 1.06, cw - 0.1, 1.0, s["text"], theme, style(theme, "card", size=text_sz, align="c"), name=f"Text {i + 1}", ctx=ctx, fit=False)
        if s.get("tag"):
            add_text(sh, cx - cw / 2, ry + 2.14, cw, 0.22, s["tag"], theme, style(theme, "mono", size=10.5, align="c", color=theme.faint), name=f"Contract {i + 1}", ctx=ctx, fit=False)
    cmd_y = 6.55
    card(sh, LM, cmd_y - 0.02, CW, 0.42, theme, radius=0.21, name="Verify strip")
    add_text(sh, LM + 0.25, cmd_y - 0.02, 7.2, 0.42, "`" + spec["verify_cmd"] + "`", theme, style(theme, "mono", size=12, color=theme.text), anchor="m", name="Verify command", ctx=ctx, fit=False)
    chips = list(spec.get("verify_chips", []))
    widths = [measure.text_width_in(c.upper(), 10, False, True, 1.0) + 0.3 for c in chips]
    cx = LM + CW - 0.2 - sum(widths) - 0.1 * max(0, len(chips) - 1)
    for c, wd in zip(chips, widths):
        pill(sh, cx, cmd_y + 0.05, c, theme, "neutral", h=0.28, size=10, dot_on=False, ctx=ctx)
        cx += wd + 0.1


# ───────────────────────────────────────────── 6. DOORS

def _portal(shapes, x, y, w, h, theme, live: bool, name: str):
    """Lengkung kaca (pintu): live = tepi bercahaya violet, gated = putus-putus."""
    p = theme.p
    r = w / 2
    pts = []
    for i in range(0, 25):
        a = math.pi - math.pi * i / 24
        pts.append((x + r + r * math.cos(a), y + r - r * math.sin(a)))
    pts += [(x + w, y + h), (x, y + h)]
    sh = polyline(shapes, pts, p["violet2"] if live else theme.faint, 0.95 if live else 0.8, 1.6, closed=True, dash=None if live else "dash",
                  glow=(p["violet2"], 7, 0.35) if live else None,
                  fill=((p["violet"], 0.22) if live else ("FFFFFF", 0.04)), name=name)
    return sh


def doors(ctx, slide, theme, spec, mats):
    need(spec, ["headline", "sub", "doors", "pipeline"], "doors")
    sh, p = slide.shapes, theme.p
    top_marker(ctx, slide, theme, mats, spec["section"])
    headline(slide, spec["headline"], LM, 0.95, 11.5, 0.8, theme, style(theme, "title", size=40), ctx=ctx)
    add_text(sh, LM, 1.7, CW, 0.5, spec["sub"], theme, style(theme, "lead", size=17), name="Sub", ctx=ctx)
    ds = spec["doors"]
    n = len(ds)
    gap = 0.22
    cw = (CW - gap * (n - 1)) / n
    y, h = 2.45, 3.45
    title_sz = common_size(ctx, [d["title"] for d in ds], cw - 0.5, 0.36, style(theme, "card_title", size=18, line=1.05), where="door titles")
    text_sz = common_size(ctx, [d["text"] for d in ds], cw - 0.5, 0.95, style(theme, "card", size=13, line=1.25), where="door texts")
    for i, d in enumerate(ds):
        x = LM + i * (cw + gap)
        live = d.get("status", "live") == "live"
        card(sh, x, y, cw, h, theme, radius=0.24, name=f"Door card {i + 1}", dash=None if live else "dash", border=None if live else (theme.faint, 0.6))
        grp = sh.add_group_shape()
        grp.name = f"Portal {i + 1} · {d['kind']}"
        px, py, pw, ph = x + 0.28, y + 0.26, 0.86, 1.08
        if live:
            halo(grp.shapes, px + pw / 2, py + ph * 0.6, 0.85, 0.85, "6E4BFF", 0.30, steps=14, name="Portal glow")
        _portal(grp.shapes, px, py, pw, ph, theme, live, "Portal")
        I.place(grp.shapes, px + pw / 2, py + ph - 0.4, (1.0, 1.0, 1.0), 0.34, mats["open"] if live else mats["clear"], "Block entering")
        pill(sh, x + cw - 1.15 - 0.2, y + 0.28, d.get("chip", "LIVE"), theme, "live" if live else "gated", h=0.28, size=10, ctx=ctx)
        add_text(sh, x + 0.28, y + 1.52, cw - 0.5, 0.24, d["kind"], theme, style(theme, "tag"), name=f"Door kind {i + 1}", ctx=ctx, fit=False)
        add_text(sh, x + 0.28, y + 1.8, cw - 0.5, 0.36, d["title"], theme, style(theme, "card_title", size=title_sz, line=1.05), name=f"Door title {i + 1}", ctx=ctx, fit=False)
        add_text(sh, x + 0.28, y + 2.22, cw - 0.5, 1.1, d["text"], theme, style(theme, "card", size=text_sz, line=1.25), name=f"Door text {i + 1}", ctx=ctx, fit=False)
    pl = spec["pipeline"]
    m = len(pl)
    py = 6.18
    pw = (CW - 0.25 * (m - 1)) / m
    for i, st in enumerate(pl):
        x = LM + i * (pw + 0.25)
        card(sh, x, py, pw, 0.62, theme, radius=0.31, name=f"Pipeline {i + 1}", shadow=False)
        add_text(sh, x + 0.2, py + 0.07, pw - 0.4, 0.28, st["label"], theme, style(theme, "tag", align="c", color=theme.strong), name=f"Stage {i + 1}", ctx=ctx, fit=False)
        add_text(sh, x + 0.2, py + 0.33, pw - 0.4, 0.24, st.get("sub", ""), theme, style(theme, "mono", size=10.5, align="c", color=theme.faint), name=f"Stage sub {i + 1}", ctx=ctx, fit=False)
        if i < m - 1:
            polyline(sh, [(x + pw + 0.03, py + 0.31), (x + pw + 0.22, py + 0.31)], p["violet2"], 0.9, 1.5, tail="triangle", name="Stage arrow")


# ───────────────────────────────────────────── 7. DESK

def desk(ctx, slide, theme, spec, mats):
    need(spec, ["headline", "steps", "agents", "hub_label", "tower_label", "stats"], "desk")
    sh, p = slide.shapes, theme.p
    top_marker(ctx, slide, theme, mats, spec["section"])
    headline(slide, spec["headline"], LM, 0.98, 5.6, 1.9, theme, style(theme, "title", size=38, line=1.02), ctx=ctx)
    # langkah-langkah (kiri)
    y = 3.1
    for i, s in enumerate(spec["steps"]):
        add_text(sh, LM, y, 0.5, 0.4, f"{i + 1:02d}", theme, style(theme, "tag", size=13), name=f"Step {i + 1} n", ctx=ctx, fit=False)
        add_text(sh, LM + 0.55, y - 0.02, 4.55, 0.3, s["title"], theme, style(theme, "card_title", size=17, line=1.05), name=f"Step {i + 1} title", ctx=ctx)
        add_text(sh, LM + 0.55, y + 0.3, 4.55, 0.62, s["text"], theme, style(theme, "card", size=13), name=f"Step {i + 1} text", ctx=ctx)
        y += 1.08
    # adegan (kanan): meja agent -> hub berformula -> menara blok
    halo(sh, 9.5, 4.0, 4.0, 2.7, "6E4BFF", 0.22, steps=24, name="Halo")
    grp = sh.add_group_shape()
    grp.name = "Scene · AI desk"
    hub = (9.3, 4.35)
    ay = [2.5, 3.9, 5.3]
    ax = 6.75
    bus_x = 8.2
    polyline(sh, [(bus_x, ay[0] + 0.08), (bus_x, ay[-1] + 0.08)], p["violet2"], 0.55, 1.2, name="Flow bus")
    polyline(sh, [(bus_x, hub[1]), (hub[0] - 0.95, hub[1])], p["violet2"], 0.7, 1.4, tail="triangle", name="Flow to formula")
    for i, a in enumerate(spec["agents"][:3]):
        cy = ay[i]
        polyline(sh, [(ax + 1.05, cy + 0.08), (bus_x, cy + 0.08)], p["violet2"], 0.55, 1.2, name=f"Flow line {i + 1}")
        I.place(grp.shapes, ax, cy + 0.2, (1.5, 0.9, 0.34), 0.40, mats["panel2"], f"Desk {i + 1}")
        I.place(grp.shapes, ax + 0.08, cy - 0.15, (0.12, 0.95, 0.62), 0.40, mats["open"], f"Monitor {i + 1}")
        I.place(grp.shapes, ax - 0.42, cy - 0.12, (0.6, 0.6, 0.6), 0.40, mats["violet"], f"Analyst {i + 1}")
        add_text(sh, ax - 0.95, cy + 0.55, 2.3, 0.24, a["name"], theme, style(theme, "tag", size=10.5, color=theme.strong), name=f"Analyst name {i + 1}", ctx=ctx, fit=False)
        add_text(sh, ax - 0.95, cy + 0.78, 2.3, 0.24, a.get("role", ""), theme, style(theme, "mono", size=10, color=theme.faint), name=f"Analyst role {i + 1}", ctx=ctx, fit=False)
    # hub: cincin + inti
    hi = I.Iso(hub[0], hub[1] + 0.35, 0.34)
    for r, al in ((3.4, 0.2), (2.5, 0.35), (1.6, 0.6)):
        I.ring(grp.shapes, hi, 0, 0, 0, r, p["violet2"], al, 1.2, name="Hub ring")
    I.place(grp.shapes, hub[0], hub[1] - 0.2, (1.4, 1.4, 1.4), 0.34, mats["open"], "Formula core")
    add_text(sh, hub[0] - 1.3, hub[1] + 1.15, 2.6, 0.24, spec["hub_label"], theme, style(theme, "tag", size=10.5, align="c", color=theme.strong), name="Hub label", ctx=ctx, fit=False)
    # menara 12 blok
    tx, tb = 11.3, 5.55
    polyline(sh, [(hub[0] + 0.7, hub[1] + 0.0), (tx - 0.9, tb - 0.55)], p["violet2"], 0.6, 1.3, tail="triangle", name="Commit line")
    n = int(spec.get("tower_blocks", 12))
    for i in range(n):
        m = mats["open"] if i >= n - 3 else mats["sealed"] if i % 2 == 0 else mats["panel2"]
        I.place(grp.shapes, tx, tb - i * 0.255, (1.7, 1.7, 0.3), 0.34, m, f"Tower block {i + 1}")
    add_text(sh, tx - 1.7, tb + 0.42, 3.4, 0.24, spec["tower_label"], theme, style(theme, "tag", size=10.5, align="c", color=theme.strong), name="Tower label", ctx=ctx, fit=False)
    # statistik
    sx = LM
    for s in spec["stats"]:
        sx += pill(sh, sx, 6.52, s, theme, "neutral", h=0.3, size=10.5, dot_on=False, ctx=ctx) + 0.12
    if spec.get("note"):
        add_text(sh, 7.0, 6.52, 5.7, 0.3, spec["note"], theme, style(theme, "mono", size=10.5, align="r", color=theme.faint), anchor="m", name="Note", ctx=ctx, fit=False)


# ───────────────────────────────────────────── 8. CHECKOUT

def checkout(ctx, slide, theme, spec, mats):
    need(spec, ["headline", "flow", "triangle", "status"], "checkout")
    sh, p = slide.shapes, theme.p
    top_marker(ctx, slide, theme, mats, spec["section"])
    headline(slide, spec["headline"], LM, 0.98, 8.2, 1.2, theme, style(theme, "title", size=38, line=1.02), ctx=ctx)
    lanes = spec.get("lanes", [])
    lx = W - LM
    for lane in reversed(lanes):
        w = measure.text_width_in(lane.upper(), 10.5, False, True, 1.0) + 0.5
        lx -= w
        pill(sh, lx, 1.08, lane, theme, "neutral", h=0.3, size=10.5, dot_on=False, ctx=ctx)
        lx -= 0.12
    # alur 5 langkah
    fl = spec["flow"]
    n = len(fl)
    gap = 0.34
    cw = (CW - gap * (n - 1)) / n
    y, h = 2.5, 2.05
    t_sz = common_size(ctx, [f['title'] for f in fl], cw - 0.4, 0.56, style(theme, 'card_title', size=16, line=1.05), where='flow titles')
    x_sz = common_size(ctx, [f['text'] for f in fl], cw - 0.4, 0.95, style(theme, 'card', size=12.5, line=1.25), where='flow texts')
    for i, f in enumerate(fl):
        x = LM + i * (cw + gap)
        last = i == n - 1
        card(sh, x, y, cw, h, theme, radius=0.22, name=f"Flow {i + 1}",
             border=(p["violet2"], 0.75) if last else None, fill=[(0, p["violet"], 0.30), (100, p["violet"], 0.10)] if last else None)
        add_text(sh, x + 0.2, y + 0.18, cw - 0.4, 0.22, f"{i + 1:02d} · {f['tag']}", theme, style(theme, "tag", size=10.5), name=f"Flow tag {i + 1}", ctx=ctx, fit=False)
        add_text(sh, x + 0.2, y + 0.5, cw - 0.4, 0.56, f["title"], theme, style(theme, "card_title", size=t_sz, line=1.05), name=f"Flow title {i + 1}", ctx=ctx, fit=False)
        add_text(sh, x + 0.2, y + 1.08, cw - 0.4, 0.95, f["text"], theme, style(theme, "card", size=x_sz, line=1.25), name=f"Flow text {i + 1}", ctx=ctx, fit=False)
        if i < n - 1:
            polyline(sh, [(x + cw + 0.04, y + h / 2), (x + cw + gap - 0.04, y + h / 2)], p["violet2"], 0.95, 1.8, tail="triangle", glow=(p["violet2"], 4, 0.3), name="Flow arrow")
    # arus bisnis: pembangun -> Fabius -> pembeli
    tri = spec["triangle"]
    by = 5.6
    xs = [1.65, 4.25, 6.85]
    k = 0.36
    grp = sh.add_group_shape()
    grp.name = "Scene · business flow"
    I.place(grp.shapes, xs[0], by, (1.6, 1.6, 1.6), k, mats["violet"], "Builders")
    I.place(grp.shapes, xs[1], by, (1.9, 1.9, 1.9), k, mats["open"], "Fabius")
    I.place(grp.shapes, xs[2], by, (1.6, 1.6, 1.6), k, mats["clear"], "Buyers")
    labs = [tri["builders"], tri["fabius"], tri["buyers"]]
    for x, l in zip(xs, labs):
        add_text(sh, x - 1.15, by + 0.72, 2.3, 0.26, l["title"], theme, style(theme, "tag", size=10.5, align="c", color=theme.strong), name=f"{l['title']} label", ctx=ctx, fit=False)
        add_text(sh, x - 1.15, by + 0.98, 2.3, 0.5, l["text"], theme, style(theme, "mono", size=10, align="c", color=theme.faint, line=1.2), name=f"{l['title']} text", ctx=ctx)
    for (a, b, lab) in ((xs[0], xs[1], tri.get("arrow_in", "")), (xs[1], xs[2], tri.get("arrow_out", ""))):
        polyline(sh, [(a + 0.78, by - 0.18), (b - 0.82, by - 0.18)], p["violet2"], 0.9, 1.8, tail="triangle", name="Business arrow")
        add_text(sh, a + 0.5, by - 0.5, b - a - 0.7, 0.24, lab, theme, style(theme, "mono", size=10, align="c", color=theme.muted), name="Arrow label", ctx=ctx, fit=False)
    polyline(sh, [(xs[2] - 0.78, by + 0.12), (xs[1] + 0.82, by + 0.12)], p["lav3"], 0.7, 1.4, tail="triangle", name="Payment arrow")
    polyline(sh, [(xs[1] - 0.82, by + 0.12), (xs[0] + 0.78, by + 0.12)], p["lav3"], 0.55, 1.4, tail="triangle", dash="dash", name="Share arrow (built)")
    # status jujur
    sx = 7.95
    sw = W - LM - sx
    sy = 4.8
    for i, s in enumerate(spec["status"]):
        yy = sy + i * 0.74
        card(sh, sx, yy, sw, 0.64, theme, radius=0.18, name=f"Status {i + 1}", shadow=False)
        pw = pill(sh, sx + 0.14, yy + 0.17, s["chip"], theme, s.get("kind", "neutral"), h=0.3, size=10, ctx=ctx)
        add_text(sh, sx + 0.14 + pw + 0.14, yy + 0.04, sw - pw - 0.4, 0.56, s["text"], theme, style(theme, "card", size=12, line=1.2), anchor="m", name=f"Status text {i + 1}", ctx=ctx)
