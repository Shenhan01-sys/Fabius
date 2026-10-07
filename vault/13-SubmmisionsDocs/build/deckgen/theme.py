"""Token desain deck = token FE Fabius (`docs/design/landing.md`, `web/src/app/globals.css`), dibaca dari berkas md Design Style.

Berkas md memegang nilainya; kode hanya menyimpan bawaan supaya build tetap jalan kalau satu kunci dihapus.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field

DEFAULT_TOKENS: dict = {
    "deck": {
        "title": "Fabius: Submission Deck",
        "subject": "Open platform for bots and AI agents: every signal committed on BNB Chain before the outcome, sold per call over x402 and MCP.",
        "author": "Fabius",
        "keywords": "Fabius, BNB Chain, x402, MCP, ERC-8004, commit-reveal, AI agents, paper trading",
        "tagline": "Plug in your bot or agent, prove every call on-chain, sell it to humans and AI via x402 + MCP.",
        "footer": "FABIUS · SUBMISSION DECK",
        "transition": "fade",
        "language": "en-US",
        "size_in": [13.333, 7.5],
    },
    "palette": {
        "night": "0F0B26", "night2": "1A1442", "deep": "07051A", "ink": "15122B",
        "lav": "ECE8FA", "lav2": "DDD5F6", "lav3": "C9BDF2", "page": "F6F4FD",
        "violet": "6E4BFF", "violet2": "9D86FF", "violet_dark": "3B22B8", "indigo": "2A1F7A",
        "mist": "8B86A6", "dim": "5B5680", "gap": "FF5A6E", "white": "FFFFFF",
    },
    "fonts": {
        "profile": "brand",
        "brand": {"display": "Archivo", "body": "Inter", "mono": "JetBrains Mono"},
        "safe": {"display": "Arial", "body": "Arial", "mono": "Courier New"},
    },
    "type": {  # pt
        "cover": 96, "title": 44, "headline": 40, "sub": 20, "lead": 18, "body": 16, "card_title": 18, "card": 14,
        "caption": 12, "tag": 11, "mono": 11, "stat": 84, "stat_s": 44, "footer": 10,
    },
}


def merge(base: dict, over: dict | None) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = v
    return out


@dataclass
class Theme:
    tokens: dict
    mode: str = "night"           # night | lavender
    font_profile: str | None = None
    p: dict = field(init=False)
    fonts: dict = field(init=False)

    def __post_init__(self):
        self.p = self.tokens["palette"]
        prof = self.font_profile or self.tokens["fonts"].get("profile", "brand")
        self.fonts = self.tokens["fonts"][prof]

    # --- ukuran
    def size(self, key: str) -> float:
        return float(self.tokens["type"][key])

    # --- warna menurut mode
    @property
    def night(self) -> bool:
        return self.mode == "night"

    @property
    def bg_stops(self):
        p = self.p
        if self.night:
            return [(0, "181038", None), (55, p["night"], None), (100, p["deep"], None)]
        return [(0, p["lav"], None), (100, p["page"], None)]

    @property
    def text(self) -> str:
        return self.p["lav"] if self.night else self.p["ink"]

    @property
    def strong(self) -> str:
        return self.p["white"] if self.night else self.p["ink"]

    @property
    def muted(self) -> str:
        return self.p["lav3"] if self.night else self.p["dim"]

    @property
    def faint(self) -> str:
        return self.p["mist"] if self.night else self.p["mist"]

    @property
    def accent(self) -> str:
        return self.p["violet2"] if self.night else self.p["violet"]

    @property
    def accent_fill(self) -> str:
        return self.p["violet"]

    @property
    def card_stops(self):
        if self.night:
            return [(0, "FFFFFF", 0.10), (100, "FFFFFF", 0.025)]
        return [(0, "FFFFFF", 0.78), (100, "FFFFFF", 0.42)]

    @property
    def card_border(self):
        return ("FFFFFF", 0.16) if self.night else ("FFFFFF", 0.9)

    @property
    def card_shadow(self):
        return None if self.night else (self.p["violet_dark"], 28, 10, 0.16)

    @property
    def rule(self):
        """Garis tipis pembatas."""
        return (self.p["lav3"], 0.22) if self.night else (self.p["violet"], 0.20)

    def font(self, role: str) -> str:
        return self.fonts[role]


def for_mode(tokens: dict, mode: str, font_profile: str | None = None) -> Theme:
    return Theme(tokens=tokens, mode=mode, font_profile=font_profile)
