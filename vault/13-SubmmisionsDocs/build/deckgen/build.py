"""Orkestrasi build: folder md (1 berkas = 1 slide) + Design Style + snapshot -> .pptx."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field

from . import draw, facts as factsmod, iso as isomod, theme as thememod
from .draw import Ctx
from .layouts import LAYOUTS, SpecError
from .mdparse import Doc, MdError, md_to_plain, parse_file, wikilinks

SLIDE_FILE = re.compile(r"^(\d{2}) - .+\.md$")
STYLE_NAME = "99 - Design Style.md"
VALID_MODES = ("night", "lavender")


class BuildError(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


@dataclass
class Report:
    out: str | None
    n_slides: int
    warnings: list = field(default_factory=list)
    facts: dict = field(default_factory=dict)
    guards: list = field(default_factory=list)


def collect(folder: str) -> tuple[list[Doc], Doc | None]:
    """Slide = berkas `NN - Judul.md` dengan NN 01..98 (00 = hub, 99 = gaya). Diurutkan lewat `slide:` di front matter."""
    docs, style = [], None
    errors = []
    for name in sorted(os.listdir(folder)):
        if name == STYLE_NAME:
            style = parse_file(os.path.join(folder, name))
            continue
        m = SLIDE_FILE.match(name)
        if not m or m.group(1) in ("00", "99"):
            continue
        try:
            d = parse_file(os.path.join(folder, name))
        except MdError as e:
            errors.append(str(e))
            continue
        if "slide" not in d.data:
            errors.append(f"{name}: bagian `## Slide` dengan blok ```yaml tidak ada")
            continue
        try:
            declared = int(d.front.get("slide", -1))
        except (TypeError, ValueError):
            errors.append(f"{name}: front matter slide={d.front.get('slide')!r} bukan bilangan bulat")
            continue
        if declared != int(m.group(1)):
            errors.append(f"{name}: front matter slide={declared} tidak sama dengan nomor berkas {m.group(1)}")
        docs.append(d)
    if errors:
        raise BuildError(errors)
    docs.sort(key=lambda d: int(d.front["slide"]))
    nums = [int(d.front["slide"]) for d in docs]
    if nums != list(range(1, len(nums) + 1)):
        raise BuildError([f"nomor slide harus berurutan 1..N tanpa bolong, ditemukan: {nums}"])
    return docs, style


def load_tokens(style: Doc | None) -> dict:
    """Token dibaca dari blok ```yaml di berkas Design Style (kunci tingkat atas `tokens:`), apa pun judul bagiannya."""
    over = {}
    for block in (style.data.values() if style else []):
        if isinstance(block, dict) and isinstance(block.get("tokens"), dict):
            over = block["tokens"]
    return thememod.merge(thememod.DEFAULT_TOKENS, over)


def notes_text(doc: Doc, n: int, spec: dict, facts: dict) -> str:
    parts = [f"SLIDE {int(doc.front['slide']):02d}/{n:02d} · {doc.title or doc.name}"]
    for key, label in (("scene", "VISUAL SCRIPT"), ("narration", "NARRATION")):
        txt = doc.sections.get(key, "").strip()
        if txt:
            parts.append(f"{label}\n{factsmod.render(md_to_plain(txt), facts, doc.name)}")
    srcs = [os.path.basename(x) for x in wikilinks(doc.sections.get("sources", "") + " " + doc.body.split("## ")[0])
            if not os.path.basename(x).startswith("00 - Hub")]
    extra = []
    for c in spec.get("contracts", []) or []:
        extra.append(f"{c['name']}: {c['addr']}")
    if extra:
        parts.append("ADDRESSES (BNB Smart Chain testnet, 97)\n" + "\n".join(extra))
    if srcs:
        parts.append("SOURCES (vault)\n" + "\n".join(dict.fromkeys(srcs)))
    parts.append(f"NUMBERS AS OF {facts['asof']} · web/public/data/snapshot.json")
    return "\n\n".join(parts)


def build(folder: str, out_path: str | None = None, *, snapshot: str | None = None, font_profile: str | None = None,
          only: set[int] | None = None, check_only: bool = False) -> Report:
    docs, style = collect(folder)
    tokens = load_tokens(style)
    snap_path = snapshot or factsmod.find_snapshot(folder)
    if not snap_path or not os.path.isfile(snap_path):
        raise BuildError([f"snapshot tidak ditemukan ({snap_path or 'web/public/data/snapshot.json'}); beri --snapshot PATH"])
    facts = factsmod.compute(factsmod.load(snap_path))
    errors, guards = [], []
    specs = []
    for d in docs:
        where = d.name
        try:
            raw = dict(d.data["slide"])
            raw.setdefault("section", d.front.get("section", ""))
            spec = factsmod.render_tree(raw, facts, where)
            for g in d.front.get("guards", []) or []:
                ok, msg = factsmod.check_guard(g, facts)
                guards.append((where, msg, ok))
                if not ok:
                    errors.append(f"{where}: guard gagal, kalimat naratif tidak lagi benar: {msg}. Perbarui slide ini.")
            if d.front.get("layout") not in LAYOUTS:
                errors.append(f"{where}: layout '{d.front.get('layout')}' tidak dikenal (ada: {', '.join(LAYOUTS)})")
            if d.front.get("theme", "night") not in VALID_MODES:
                errors.append(f"{where}: theme harus salah satu dari {VALID_MODES}")
            specs.append(spec)
        except (factsmod.FactError, KeyError) as e:
            errors.append(f"{where}: {e}")
            specs.append({})
    if errors:
        raise BuildError(errors)
    n = len(docs)
    rep = Report(out=None, n_slides=n, facts=facts, guards=guards)
    if check_only:
        return rep
    ctx = Ctx(tokens=tokens, facts=facts, base_dir=os.path.join(folder, "assets"), font_profile=font_profile, n_slides=n)
    prs = draw.base_presentation(tokens, font_profile)
    footer_left = f"{tokens['deck']['footer']} · {facts['asof_date']}"
    for d, spec in zip(docs, specs):
        num = int(d.front["slide"])
        if only and num not in only:
            continue
        ctx.slide_no = num
        theme = ctx.theme(d.front.get("theme", "night"))
        mats = isomod.materials(theme.p)
        slide = draw.new_slide(prs, theme)
        try:
            LAYOUTS[d.front["layout"]](ctx, slide, theme, spec, mats)
        except (SpecError, FileNotFoundError) as e:
            errors.append(f"{d.name}: {e}")
            continue
        draw.footer(slide, theme, n, footer_left, ctx)
        draw.set_transition(slide, d.front.get("transition", tokens["deck"].get("transition")))
        draw.set_notes(slide, notes_text(d, n, spec, facts))
    if errors:
        raise BuildError(errors)
    out_path = out_path or os.path.join(folder, "build", "out", "Fabius-Submission-Deck.pptx")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    prs.save(out_path)
    rep.out, rep.warnings = out_path, ctx.warnings
    return rep


def _hapus_basi(out_dir: str, pdf: str) -> None:
    """Buang PNG dan PDF dari render sebelumnya: deck yang menyusut atau `--only` tidak boleh mewariskan slide lama ke pemeriksaan visual."""
    for f in os.listdir(out_dir):
        if re.fullmatch(r"slide-\d+\.png", f):
            os.remove(os.path.join(out_dir, f))
    if os.path.isfile(pdf):
        os.remove(pdf)


def render_images(pptx: str, out_dir: str, dpi: int = 110) -> list[str]:
    """Opsional (QA): .pptx -> PDF (LibreOffice) -> PNG (pdftoppm). Mengembalikan daftar PNG; kosong bila alat tidak ada."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    pdftoppm = shutil.which("pdftoppm")
    if not soffice or not pdftoppm:
        return []
    os.makedirs(out_dir, exist_ok=True)
    pdf = os.path.join(out_dir, os.path.splitext(os.path.basename(pptx))[0] + ".pdf")
    _hapus_basi(out_dir, pdf)
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", out_dir, pptx], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
    prefix = os.path.join(out_dir, "slide")
    subprocess.run([pdftoppm, "-png", "-r", str(dpi), pdf, prefix], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
    return sorted(os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.startswith("slide") and f.endswith(".png"))
