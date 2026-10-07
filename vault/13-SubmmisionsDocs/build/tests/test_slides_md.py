"""Audit isi: struktur 12+1 berkas md, sumber yang bisa ditelusuri, alamat kontrak = deployments/97.json, kalimat terlarang."""
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.dirname(HERE)
FOLDER = os.path.dirname(BUILD)
VAULT = os.path.dirname(FOLDER)
ROOT = os.path.dirname(VAULT)
sys.path.insert(0, BUILD)

from deckgen import build, mdparse  # noqa: E402
from deckgen.layouts import LAYOUTS  # noqa: E402

SKIP_DIRS = {"_archive", "scripts", "node_modules"}


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

# Kalimat yang dilarang untuk diri sendiri (vault/10-Submissions/01 - Claims Cheat Sheet.md, vault/06-Results/01 - Claims and Limits.md).
FORBIDDEN = [
    (r"\b(our|these|the) (signals|bots|agents|desk) (are|is) profitable", "klaim untung"),
    (r"\bprofitable (signals|bots|agents)\b", "klaim untung"),
    (r"\bguarantee[ds]? (returns?|profits?|gains?|income|results?)\b|\brisk[- ]free\b|\bpassive income\b|\bget rich\b", "janji hasil"),
    (r"\bwin[- ]?rate\b|\bROI\b|\bAPY\b|\balpha\b", "angka/jargon kinerja"),
    (r"\b(has|have|with) an edge\b|\bproven edge\b|\bour edge\b", "klaim edge"),
    (r"\btrustless\b|\bzkML\b|\bTEE\b|verifiable inference|AI (cannot|can't) cheat", "klaim validasi yang dilarang"),
    (r"BNB Agent Studio", "integrasi yang belum dibaca primer"),
    (r"\b(first|only)\b[^.\n]{0,40}\b(BNB|bnb)\b", "klaim urutan"),
    (r"used by other agents|\b(our|have) customers\b|\bpaying customers\b|sign-?ups?\b", "klaim pemakai luar"),
    (r"real-time signals (are |is )?(available|live|on sale)", "tingkat 1 masih terkunci"),
    (r"\b(live|real)[- ]money (trading|fills)\b", "uang nyata dimatikan"),
]


def _all_vault_md():
    out = {}
    for cur, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            if f.endswith(".md"):
                out.setdefault(os.path.splitext(f)[0], []).append(os.path.join(cur, f))
    return out


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, (list, tuple)):
        for x in obj:
            yield from _strings(x)
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)


class SlidesMarkdown(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs, cls.style = build.collect(FOLDER)
        cls.vault_md = _all_vault_md()
        cls.deployments = _read(os.path.join(ROOT, "deployments", "97.json")).lower()

    def test_structure_twelve_slides_plus_style(self):
        self.assertEqual([int(d.front["slide"]) for d in self.docs], list(range(1, 13)))
        self.assertIsNotNone(self.style)
        self.assertTrue(any("tokens" in v for v in self.style.data.values()), "blok tokens di Design Style tidak terbaca")
        self.assertTrue(os.path.isfile(os.path.join(FOLDER, "00 - Hub Submission Deck.md")))

    def test_front_matter_is_valid(self):
        seen = set()
        for d in self.docs:
            self.assertIn(d.front["layout"], LAYOUTS, d.name)
            self.assertIn(d.front.get("theme", "night"), ("night", "lavender"), d.name)
            self.assertIn("submission", d.front["tags"], d.name)
            self.assertNotIn(d.front["id"], seen, f"id ganda di {d.name}")
            seen.add(d.front["id"])

    def test_light_slides_are_the_world_of_claims(self):
        light = [int(d.front["slide"]) for d in self.docs if d.front.get("theme") == "lavender"]
        self.assertEqual(light, [2, 3], "hanya slide masalah yang terang; slide 4 membalik ke malam (lihat Design Style §3)")

    def test_each_slide_has_scene_narration_sources_and_claims_table(self):
        for d in self.docs:
            scene, narr = d.sections.get("scene", ""), d.sections.get("narration", "")
            self.assertGreaterEqual(len(scene.split()), 80, f"{d.name}: skrip visual terlalu tipis")
            self.assertGreaterEqual(len(narr.split()), 60, f"{d.name}: narasi terlalu pendek")
            self.assertLessEqual(len(narr.split()), 300, f"{d.name}: narasi terlalu panjang untuk satu slide")
            self.assertIn("**Sumber:**", d.body, d.name)
            self.assertIn("**Bagian dari:**", d.body, d.name)
            rows = [ln for ln in d.sections.get("claims check", "").splitlines() if ln.startswith("|") and not set(ln) <= set("|- ")]
            self.assertGreaterEqual(len(rows), 4, f"{d.name}: tabel Claims check harus punya header + minimal 3 klaim")
            for ln in rows[1:]:
                cells = [c.strip() for c in ln.strip("|").split("|")]
                self.assertEqual(len(cells), 3, f"{d.name}: baris klaim harus punya 3 kolom: {ln[:60]}")
                self.assertTrue(all(cells), f"{d.name}: sel kosong di tabel klaim: {ln[:60]}")

    def test_wikilinks_resolve_inside_the_vault(self):
        for d in self.docs + [self.style]:
            for link in mdparse.wikilinks(d.body):
                base = os.path.basename(link.replace("\\", "/"))
                self.assertIn(base, self.vault_md, f"{d.name}: [[{link}]] tidak ada di vault")

    def test_cited_repo_paths_exist(self):
        pat = re.compile(r"^[A-Za-z0-9_.\-/]+\.(py|sol|json|ts|tsx|md|mjs|yml|css|ttf)(:[0-9,\-]+)?$")
        missing = []
        for d in self.docs + [self.style]:
            for span in re.findall(r"`([^`\n]+)`", d.body):
                tok = span.strip().split()[-1] if span.strip().startswith("python") else span.strip()
                if "…" in tok or "*" in tok or "{{" in tok or not pat.match(tok):
                    continue
                path = re.sub(r":[0-9,\-]+$", "", tok)
                if not (os.path.exists(os.path.join(ROOT, path)) or os.path.exists(os.path.join(VAULT, path))):
                    missing.append(f"{d.name}: {path}")
        self.assertEqual(missing, [], "path yang dikutip tidak ada di repo")

    def test_contract_addresses_match_deployments(self):
        d = next(x for x in self.docs if x.front["id"] == "onchain")
        contracts = d.data["slide"]["contracts"]
        self.assertEqual(len(contracts), 5)
        addrs = [c["addr"] for c in contracts]
        self.assertEqual(len(set(a.lower() for a in addrs)), 5)
        for c in contracts:
            self.assertRegex(c["addr"], r"^0x[0-9a-fA-F]{40}$", c["name"])
            self.assertIn(c["addr"].lower(), self.deployments, f"{c['name']} {c['addr']} tidak ada di deployments/97.json")
        self.assertEqual([c["name"] for c in contracts if c.get("main")], ["SignalAnchor"])
        for err in d.data["slide"]["enforced"]["errors"]:
            src = _read(os.path.join(ROOT, "contracts", "SignalAnchor.sol"))
            self.assertIn(f"error {err}(", src, f"error {err} tidak ada di SignalAnchor.sol")

    def test_no_forbidden_claims_in_slides_or_narration(self):
        hits = []
        for d in self.docs:
            blob = "\n".join(list(_strings(d.data["slide"])) + [d.sections.get("narration", ""), d.sections.get("scene", "")])
            for rx, why in FORBIDDEN:
                m = re.search(rx, blob, flags=re.I)
                if m:
                    hits.append(f"{d.name}: '{m.group(0)}' ({why})")
        self.assertEqual(hits, [], "kalimat terlarang oleh Claims Cheat Sheet")

    def test_every_strong_claim_slide_names_its_limit(self):
        """Slide yang menyebut penjualan/pembayaran harus menyebut statusnya (testnet / tanpa nilai / terkunci)."""
        for d in self.docs:
            blob = "\n".join(_strings(d.data["slide"])).lower()
            if "x402" in blob and d.front["id"] not in ("gap", "cover"):
                self.assertTrue(any(w in blob for w in ("testnet", "no-value", "gated", "locked", "not deployed")), f"{d.name}: x402 tanpa status")
        cover = next(d for d in self.docs if d.front["id"] == "cover")
        chips = " ".join(c["text"] for c in cover.data["slide"]["chips"]).lower()
        self.assertIn("testnet", chips)
        self.assertIn("no real", chips)

    def test_tagline_is_single_sourced(self):
        tag = build.load_tokens(self.style)["deck"]["tagline"]
        for d in self.docs:
            if "tagline" in d.data["slide"]:
                self.assertEqual(d.data["slide"]["tagline"], tag, f"{d.name}: tagline berbeda dari Design Style")

    def test_tokens_in_design_style_match_code_defaults(self):
        from deckgen import theme
        over = build.load_tokens(self.style)
        for k in ("palette", "type"):
            self.assertEqual({a: str(b) for a, b in over[k].items()}, {a: str(b) for a, b in theme.DEFAULT_TOKENS[k].items()}, k)


if __name__ == "__main__":
    unittest.main()
