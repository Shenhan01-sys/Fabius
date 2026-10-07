"""Pembaca berkas md slide: front matter YAML + bagian `##` + blok ```yaml (data di slide) -> `Doc`."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

import yaml

_FRONT = re.compile(r"\A﻿?---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n", re.S)
_H2 = re.compile(r"^##[ \t]+(.+?)[ \t]*$", re.M)
_FENCE = re.compile(r"```ya?ml[ \t]*\r?\n(.*?)\r?\n```", re.S)


class MdError(Exception):
    pass


@dataclass
class Doc:
    path: str
    front: dict
    sections: dict = field(default_factory=dict)   # judul (huruf kecil) -> teks
    data: dict = field(default_factory=dict)       # judul (huruf kecil) -> dict dari blok yaml pertama di bagian itu
    title: str = ""
    body: str = ""

    @property
    def name(self) -> str:
        return os.path.basename(self.path)


def parse_text(text: str, path: str = "<memory>") -> Doc:
    text = text.replace("\r\n", "\n")
    m = _FRONT.match(text)
    if not m:
        raise MdError(f"{path}: front matter YAML (--- ... ---) tidak ditemukan di awal berkas")
    try:
        front = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise MdError(f"{path}: front matter bukan YAML valid: {e}") from e
    if not isinstance(front, dict):
        raise MdError(f"{path}: front matter harus berupa pemetaan kunci: nilai")
    body = text[m.end():]
    t = re.search(r"^#[ \t]+(.+?)[ \t]*$", body, re.M)
    doc = Doc(path=path, front=front, title=t.group(1).strip() if t else "", body=body)
    marks = list(_H2.finditer(body))
    for i, h in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        key = re.sub(r"^\d+[.)]\s*", "", h.group(1).strip().lower())
        chunk = body[h.end():end].strip("\n")
        doc.sections[key] = chunk
        fm = _FENCE.search(chunk)
        if fm:
            try:
                val = yaml.safe_load(fm.group(1)) or {}
            except yaml.YAMLError as e:
                raise MdError(f"{path}: blok yaml di bagian '{h.group(1).strip()}' tidak valid: {e}") from e
            if not isinstance(val, dict):
                raise MdError(f"{path}: blok yaml di bagian '{h.group(1).strip()}' harus berupa pemetaan")
            doc.data[key] = val
            doc.sections[key] = (chunk[:fm.start()] + chunk[fm.end():]).strip("\n")
    return doc


def parse_file(path: str) -> Doc:
    with open(path, encoding="utf-8") as f:
        return parse_text(f.read(), path)


_WIKI = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]*))?\]\]")


def md_to_plain(text: str) -> str:
    """Teks catatan pembicara: buang penanda md, biarkan tanda hubung daftar."""
    t = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    t = _WIKI.sub(lambda m: (m.group(2) or os.path.basename(m.group(1).strip())), t)
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"\1", t)
    t = re.sub(r"`([^`]+)`", r"\1", t)
    t = re.sub(r"^>[ \t]?", "", t, flags=re.M)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def wikilinks(text: str) -> list[str]:
    return [m.group(1).strip() for m in _WIKI.finditer(text)]
