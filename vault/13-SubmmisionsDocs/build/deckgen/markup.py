"""Penanda inline untuk teks slide: `**tebal**`, `*aksen*` (tebal-miring berwarna), `` `mono` ``; "\\n" = baris baru."""
from __future__ import annotations

import re
from dataclasses import dataclass

_TOKEN = re.compile(r"(\*\*[^*]+?\*\*|\*[^*\n]+?\*|`[^`\n]+?`)")


@dataclass(frozen=True)
class Run:
    text: str
    bold: bool = False
    accent: bool = False
    mono: bool = False


def parse_line(line: str) -> list[Run]:
    runs: list[Run] = []
    for part in _TOKEN.split(line):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            runs.append(Run(part[2:-2], bold=True))
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            runs.append(Run(part[1:-1], accent=True))
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            runs.append(Run(part[1:-1], mono=True))
        else:
            runs.append(Run(part))
    return runs


def parse(text: str) -> list[list[Run]]:
    """Daftar baris; tiap baris = daftar run."""
    return [parse_line(ln) for ln in str(text).split("\n")]


def plain(text: str) -> str:
    return "\n".join("".join(r.text for r in line) for line in parse(text))
