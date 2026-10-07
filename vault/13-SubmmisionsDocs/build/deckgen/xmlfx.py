"""Pembantu XML DrawingML: isi (solid/gradien dengan alfa), garis, cahaya, bayangan.

python-pptx tidak menyediakan alfa, gradien multi-henti, atau cahaya; semuanya ditulis langsung ke `spPr`
dengan URUTAN anak yang diminta skema (xfrm, geometri, isi, ln, efek) supaya PowerPoint tidak minta "perbaiki".
"""
from __future__ import annotations

from lxml import etree
from pptx.oxml.ns import qn

_FILL_TAGS = ("a:noFill", "a:solidFill", "a:gradFill", "a:blipFill", "a:pattFill", "a:grpFill")
_ORDER = ["a:xfrm", "a:custGeom", "a:prstGeom"] + [_FILL_TAGS] + ["a:ln", "a:effectLst", "a:effectDag", "a:scene3d", "a:sp3d", "a:extLst"]


def _el(tag, **attrs):
    e = etree.Element(qn(tag))
    for k, v in attrs.items():
        e.set(k, str(v))
    return e


def _rank(el):
    t = el.tag
    for i, item in enumerate(_ORDER):
        names = item if isinstance(item, tuple) else (item,)
        if any(qn(n) == t for n in names):
            return i
    return len(_ORDER)


def _put(spPr, new):
    """Sisipkan `new` di posisi skema yang benar; buang elemen sekelompok yang lama (isi menggantikan isi)."""
    fills = [qn(n) for n in _FILL_TAGS]
    group = fills if new.tag in fills else [new.tag]
    for child in list(spPr):
        if child.tag in group:
            spPr.remove(child)
    r = _rank(new)
    for i, child in enumerate(list(spPr)):
        if _rank(child) > r:
            spPr.insert(i, new)
            return new
    spPr.append(new)
    return new


def color(hexv: str, alpha: float | None = None):
    c = _el("a:srgbClr", val=hexv.lstrip("#").upper())
    if alpha is not None and alpha < 0.999:
        c.append(_el("a:alpha", val=int(round(max(0.0, alpha) * 100000))))
    return c


def _sppr(shape):
    return shape._element.spPr


def solid(shape, hexv: str, alpha: float | None = None):
    f = _el("a:solidFill")
    f.append(color(hexv, alpha))
    _put(_sppr(shape), f)


def no_fill(shape):
    _put(_sppr(shape), _el("a:noFill"))


def gradient(shape, stops, angle: float = 90.0, radial: bool = False):
    """stops = [(pos 0..100, hex, alpha|None)]. angle em derajat (90 = atas ke bawah)."""
    g = _el("a:gradFill", rotWithShape=1)
    lst = _el("a:gsLst")
    for pos, hexv, al in stops:
        gs = _el("a:gs", pos=int(round(pos * 1000)))
        gs.append(color(hexv, al))
        lst.append(gs)
    g.append(lst)
    if radial:
        p = _el("a:path", path="circle")
        p.append(_el("a:fillToRect", l=50000, t=50000, r=50000, b=50000))
        g.append(p)
    else:
        g.append(_el("a:lin", ang=int(round(angle * 60000)), scaled=0))
    _put(_sppr(shape), g)


def line(shape, hexv: str | None, width_pt: float = 0.75, alpha: float | None = None, dash: str | None = None,
         cap_round: bool = True, head: str | None = None, tail: str | None = None):
    ln = _el("a:ln", w=int(round(width_pt * 12700)))
    if cap_round:
        ln.set("cap", "rnd")
    if hexv is None:
        ln.append(_el("a:noFill"))
    else:
        f = _el("a:solidFill")
        f.append(color(hexv, alpha))
        ln.append(f)
        if dash:
            ln.append(_el("a:prstDash", val=dash))
        ln.append(_el("a:round"))
        if head:
            ln.append(_el("a:headEnd", type=head, w="med", len="med"))
        if tail:
            ln.append(_el("a:tailEnd", type=tail, w="med", len="med"))
    _put(_sppr(shape), ln)


def effects(shape, glow: tuple | None = None, shadow: tuple | None = None):
    """glow = (hex, raio_pt, alfa); shadow = (hex, blur_pt, jarak_pt, alfa). Urutan skema: glow lalu outerShdw."""
    sp = _sppr(shape)
    for x in sp.findall(qn("a:effectLst")):
        sp.remove(x)
    if not glow and not shadow:
        return
    ef = _el("a:effectLst")
    if glow:
        hexv, rad, al = glow
        g = _el("a:glow", rad=int(round(rad * 12700)))
        g.append(color(hexv, al))
        ef.append(g)
    if shadow:
        hexv, blur, dist, al = shadow
        s = _el("a:outerShdw", blurRad=int(round(blur * 12700)), dist=int(round(dist * 12700)), dir=5400000, algn="t", rotWithShape=0)
        s.append(color(hexv, al))
        ef.append(s)
    _put(sp, ef)


def set_descr(shape, text: str, name: str | None = None):
    """Teks alternatif (aksesibilitas) + nama di panel seleksi."""
    el = shape._element
    for tag in ("p:nvSpPr", "p:nvPicPr", "p:nvGrpSpPr", "p:nvCxnSpPr"):
        nv = el.find(qn(tag))
        if nv is not None:
            c = nv.find(qn("p:cNvPr"))
            if text is not None:
                c.set("descr", text)
            if name:
                c.set("name", name)
            return
