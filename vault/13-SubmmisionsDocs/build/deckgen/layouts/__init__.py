"""Registri layout: nama `layout` di front matter -> fungsi penggambar."""
from __future__ import annotations

from .common import SpecError  # noqa: F401
from . import engine, intro, proof

LAYOUTS = {
    "cover": intro.cover,
    "claims_gap": intro.claims_gap,
    "trust_gap": intro.trust_gap,
    "seal": intro.seal,
    "rail": engine.rail,
    "doors": engine.doors,
    "desk": engine.desk,
    "checkout": engine.checkout,
    "showcase": proof.showcase,
    "stack": proof.stack,
    "honesty": proof.honesty,
    "roadmap": proof.roadmap,
}
