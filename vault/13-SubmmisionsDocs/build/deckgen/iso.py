"""Perkakas isometrik: balok kaca 3 sisi dari poligon asli PowerPoint (freeform), bahasa visual blok FE (`docs/design/landing.md`).

Tiga keadaan blok FE: kosong (kaca berkabut), tersegel (indigo pekat), terbuka + SAH (putih-violet bercahaya).
Proyeksi: layar-x = (x - y)·cos30·k ; layar-y = (x + y)·0,5·k - z·k  (pandangan dari +x +y +z; sisi terlihat: atas, x1, y1).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

from . import xmlfx

IN = 914400
C30 = math.cos(math.pi / 6)

Col = tuple  # (hex, alpha)


@dataclass(frozen=True)
class Mat:
    top: Col
    right: Col   # sisi x1
    left: Col    # sisi y1
    edge: Col = ("ECE8FA", 0.25)
    edge_w: float = 0.75
    glow: tuple | None = None        # (hex, radius_pt, alpha)
    dash: str | None = None


def materials(p: dict) -> dict[str, Mat]:
    """Material turunan dari palet FE."""
    return {
        # kaca berkabut: slot kosong / masa depan
        "clear": Mat(("FFFFFF", 0.10), ("C9BDF2", 0.07), ("C9BDF2", 0.05), edge=("C9BDF2", 0.55), edge_w=1.0),
        # tersegel: indigo pekat
        "sealed": Mat(("4A38C8", 0.98), ("2F2290", 0.98), ("1D1560", 0.98), edge=("9D86FF", 0.45), edge_w=0.75),
        # terbuka + SAH: putih-violet bercahaya
        "open": Mat(("F6F2FF", 0.97), ("C9BDF2", 0.96), ("9D86FF", 0.96), edge=("FFFFFF", 0.85), edge_w=0.75, glow=("9D86FF", 9, 0.38)),
        # perangkat keras gelap melayang
        "panel": Mat(("2E2A48", 1.0), ("1B1830", 1.0), ("121022", 1.0), edge=("ECE8FA", 0.17), edge_w=0.5),
        "panel2": Mat(("3C3760", 1.0), ("231F3E", 1.0), ("171428", 1.0), edge=("ECE8FA", 0.24), edge_w=0.5),
        # bolong: merah hanya untuk gap (aturan FE)
        "gap": Mat(("FF5A6E", 0.10), ("FF5A6E", 0.07), ("FF5A6E", 0.05), edge=("FF5A6E", 0.85), edge_w=1.0, dash="dash"),
        # mode terang: kaca putih di atas lavender
        "lav": Mat(("FFFFFF", 0.95), ("E6DFFB", 0.95), ("D3C9F5", 0.95), edge=("FFFFFF", 0.9), edge_w=0.75),
        "ink": Mat(("3A3270", 1.0), ("261F52", 1.0), ("15122B", 1.0), edge=("15122B", 0.5), edge_w=0.5),
        "violet": Mat(("8E75FF", 0.98), ("6E4BFF", 0.98), ("4B2FD6", 0.98), edge=("FFFFFF", 0.5), edge_w=0.75, glow=("6E4BFF", 8, 0.35)),
    }


class Iso:
    """Proyeksi isometrik ke koordinat slide (EMU). (cx, cy) = posisi layar titik (0,0,0); k = inci per satuan."""

    def __init__(self, cx_in: float, cy_in: float, k_in: float):
        self.cx, self.cy, self.k = cx_in * IN, cy_in * IN, k_in * IN

    def p(self, x: float, y: float, z: float):
        return ((x - y) * C30 * self.k + self.cx, (x + y) * 0.5 * self.k - z * self.k + self.cy)

    def inch(self, x: float, y: float, z: float):
        X, Y = self.p(x, y, z)
        return X / IN, Y / IN


def _poly(shapes, pts, name=None):
    fb = shapes.build_freeform(int(round(pts[0][0])), int(round(pts[0][1])), scale=1.0)
    fb.add_line_segments([(int(round(x)), int(round(y))) for x, y in pts[1:]], close=True)
    sh = fb.convert_to_shape()
    if name:
        sh.name = name
    return sh


def _paint(sh, col: Col, mat: Mat):
    xmlfx.solid(sh, col[0], col[1])
    xmlfx.line(sh, mat.edge[0], mat.edge_w, mat.edge[1], dash=mat.dash)
    if mat.glow:
        xmlfx.effects(sh, glow=mat.glow)


def box(shapes, iso: Iso, b, mat: Mat, name: str = "Block"):
    """b = (x0,y0,z0,x1,y1,z1). Tiga muka: kiri-bawah (y1), kanan-bawah (x1), atas (z1)."""
    x0, y0, z0, x1, y1, z1 = b
    P = iso.p
    faces = [
        ([P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)], mat.left, "kiri"),
        ([P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1)], mat.right, "kanan"),
        ([P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)], mat.top, "atas"),
    ]
    out = []
    for pts, col, tag in faces:
        sh = _poly(shapes, pts, f"{name} · {tag}")
        _paint(sh, col, mat)
        out.append(sh)
    return out


def depth_key(b):
    return (b[0] + b[3]) / 2 + (b[1] + b[4]) / 2 + (b[2] + b[5]) / 2


def boxes(shapes, iso: Iso, items, name: str = "Block"):
    """items = [(bounds, Mat)] atau [(bounds, Mat, nama)]; digambar dari belakang ke depan (algoritma pelukis)."""
    ordered = sorted(items, key=lambda it: depth_key(it[0]))
    for i, it in enumerate(ordered):
        b, mat = it[0], it[1]
        nm = it[2] if len(it) > 2 else f"{name} {i + 1}"
        box(shapes, iso, b, mat, nm)


def plane_poly(shapes, iso: Iso, pts3, mat_fill: Col, edge: Col | None = None, edge_w: float = 0.75, dash: str | None = None,
               glow: tuple | None = None, name: str = "Plane"):
    """Poligon datar di ruang 3D (mis. lantai, layar, jembatan tipis)."""
    sh = _poly(shapes, [iso.p(*q) for q in pts3], name)
    xmlfx.solid(sh, mat_fill[0], mat_fill[1])
    if edge:
        xmlfx.line(sh, edge[0], edge_w, edge[1], dash=dash)
    else:
        xmlfx.line(sh, None)
    if glow:
        xmlfx.effects(sh, glow=glow)
    return sh


def ring(shapes, iso: Iso, cx: float, cy: float, z: float, r: float, color: str, alpha: float = 0.6, width: float = 1.0,
         dash: str | None = None, n: int = 72, name: str = "Ring", fill: Col | None = None):
    """Lingkaran pada bidang datar (xy) pada tinggi z: poligon tertutup n sisi, tampil sebagai elips isometrik."""
    pts = [iso.p(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), z) for i in range(n)]
    sh = _poly(shapes, pts, name)
    if fill:
        xmlfx.solid(sh, fill[0], fill[1])
    else:
        xmlfx.no_fill(sh)
    xmlfx.line(sh, color, width, alpha, dash=dash)
    return sh


def seg3(shapes, iso: Iso, pts3, color: str, alpha: float = 0.8, width: float = 1.25, dash: str | None = None, name: str = "Line",
         glow: tuple | None = None, tail: str | None = None):
    """Garis patah di ruang 3D (terbuka, tanpa isi)."""
    pts = [iso.p(*q) for q in pts3]
    fb = shapes.build_freeform(int(round(pts[0][0])), int(round(pts[0][1])), scale=1.0)
    fb.add_line_segments([(int(round(x)), int(round(y))) for x, y in pts[1:]], close=False)
    sh = fb.convert_to_shape()
    sh.name = name
    xmlfx.no_fill(sh)
    xmlfx.line(sh, color, width, alpha, dash=dash, tail=tail)
    if glow:
        xmlfx.effects(sh, glow=glow)
    return sh


def mini_cube(shapes, x_in: float, y_in: float, size_in: float, mats: dict[str, Mat], kind: str = "open", name: str = "Marker"):
    """Kubus kecil (penanda FE 'blok kaca kecil') berpusat di (x,y) inci."""
    k = size_in / 2.2
    iso = Iso(x_in, y_in + size_in * 0.55, k)
    box(shapes, iso, (-0.5, -0.5, 0, 0.5, 0.5, 1.0), mats[kind], name)


def place(shapes, cx_in: float, cy_in: float, size, k_in: float, mat: Mat, name: str = "Block"):
    """Balok berukuran size=(w,d,h) satuan yang TITIK BERATNYA jatuh di (cx,cy) inci pada layar.

    Cara menyusun adegan mendatar (rel, jembatan, garis waktu) tanpa sumbu isometrik panjang: tiap blok ditaruh di posisi layar sendiri,
    seperti ikon kubus di FE (`IsoCube`), jadi komposisi tetap horizontal dan bahasa bentuknya tetap isometrik.
    """
    w, d, h = size
    xc, yc, zc = w / 2, d / 2, h / 2
    iso = Iso(cx_in - (xc - yc) * C30 * k_in, cy_in - ((xc + yc) * 0.5 * k_in - zc * k_in), k_in)
    return box(shapes, iso, (0, 0, 0, w, d, h), mat, name)


def footprint_in(size, k_in: float):
    """(lebar, tinggi) inci bidang layar yang dipakai balok size=(w,d,h)."""
    w, d, h = size
    return ((w + d) * C30 * k_in, (w + d) * 0.5 * k_in + h * k_in)
