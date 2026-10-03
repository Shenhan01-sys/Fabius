# -*- coding: utf-8 -*-
"""Gerbang tabel semantik kegagalan operator (P109): `vault/07-Testing/T8 - Semantik Kegagalan Operator.md`.

Tabel yang tidak diperiksa membusuk diam-diam: fungsi diganti nama, frasa pesan diubah, tes dihapus, dan barisnya tetap terdengar benar. Gerbang ini
membuat setiap baris menunjuk sesuatu yang ADA:
  - ARAH harus salah satu kosakata tetap (TUNDA / TOLAK / PERTAHANKAN / UNGKAPKAN);
  - jangkar kode `berkas::fungsi` (boleh `Kelas.metode`) harus ada (dibaca lewat ast, bukan grep) dan frasa berkutipnya harus ada DI BADAN fungsi itu;
  - jangkar tes `berkas::Kelas.tes` harus ada dan badannya punya assert (tes tanpa assert = hampa, ditolak);
  - tes yang bersyarat (skipUnless/skipIf) dilaporkan beserta syaratnya: tes itu bisa dilewati diam-diam di mesin lain;
  - baris `BELUM DIBANGUN` dihitung dan dicetak (rencana, bukan beres); ID ganda ditolak.
Dengan `--run`, semua tes jangkar juga dijalankan, dan hasilnya dicetak sebagai lulus / DILEWATI / GAGAL (dilewati tidak dihitung lulus).

Dipakai:  python -X utf8 vault/scripts/check_failure_semantics.py [--run]
Exit:     0 bersih · 1 ada jangkar mati / arah tak dikenal / tes hampa / tes gagal.
"""
from __future__ import annotations

import argparse
import ast
import io
import os
import re
import sys
import unittest

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.dirname(HERE)
ROOT = os.path.dirname(V)
NOTE = os.path.join(V, "07-Testing", "T8 - Semantik Kegagalan Operator.md")
ARAH = ("TUNDA", "TOLAK", "PERTAHANKAN", "UNGKAPKAN")
RENCANA = "BELUM DIBANGUN"
ANCHOR = re.compile(r"`([^`:]+)::([A-Za-z_][\w.]*)`(?:\s+\"([^\"]+)\")?")


def rows(path: str):
    with open(path, encoding="utf-8") as f:
        for n, ln in enumerate(f, 1):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")] if ln.startswith("| SK-") else None
            if cells:
                yield n, cells


def find(tree: ast.AST, qual: str):
    node, parts = tree, qual.split(".")
    for p in parts:
        body = getattr(node, "body", [])
        node = next((x for x in body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and x.name == p), None)
        if node is None:
            return None
    return node


_trees = {}


def load(rel: str):
    if rel not in _trees:
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            _trees[rel] = None
        else:
            with open(p, encoding="utf-8") as f:
                src = f.read()
            _trees[rel] = (src, ast.parse(src))
    return _trees[rel]


def has_assert(fn: ast.AST) -> bool:
    for x in ast.walk(fn):
        if isinstance(x, ast.Assert):
            return True
        if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr.startswith("assert"):
            return True
    return False


def skip_conditions(tree: ast.AST, qual: str, src: str):
    out, node = [], tree
    for p in qual.split("."):
        node = next(x for x in node.body if getattr(x, "name", None) == p)
        for d in getattr(node, "decorator_list", []):
            s = ast.get_source_segment(src, d) or ""
            if "skip" in s:
                out.append(s.split("(", 1)[-1][:80].rstrip(")"))
    return out


def check(path: str = NOTE):
    errs, plans, conditional, tests, ids = [], [], [], [], set()
    for n, c in rows(path):
        if len(c) != 6:
            errs.append(f"baris {n}: {len(c)} kolom, harus 6")
            continue
        rid, _, arah, _, kode, tes = c
        if rid in ids:
            errs.append(f"{rid}: ID ganda")
        ids.add(rid)
        if arah.strip("`") not in ARAH:
            errs.append(f"{rid}: arah {arah!r} bukan kosakata tetap {ARAH}")
        if kode.startswith(RENCANA) or tes.startswith(RENCANA):
            plans.append(f"{rid} ({kode})")
            continue
        m = ANCHOR.fullmatch(kode)
        if not m or not m.group(3):
            errs.append(f"{rid}: jangkar kode harus `berkas::fungsi` \"frasa\", dapat {kode!r}")
        else:
            got = load(m.group(1))
            node = find(got[1], m.group(2)) if got else None
            if node is None:
                errs.append(f"{rid}: {m.group(1)}::{m.group(2)} tidak ada")
            elif m.group(3) not in (ast.get_source_segment(got[0], node) or ""):
                errs.append(f"{rid}: frasa \"{m.group(3)}\" tidak ada di badan {m.group(2)}")
        m = ANCHOR.fullmatch(tes)
        if not m or m.group(3) or not m.group(2).count("."):
            errs.append(f"{rid}: jangkar tes harus `berkas::Kelas.tes`, dapat {tes!r}")
            continue
        got = load(m.group(1))
        node = find(got[1], m.group(2)) if got else None
        if node is None:
            errs.append(f"{rid}: tes {m.group(1)}::{m.group(2)} tidak ada")
            continue
        if not has_assert(node):
            errs.append(f"{rid}: tes {m.group(2)} tanpa assert (hampa)")
        for cond in skip_conditions(got[1], m.group(2), got[0]):
            conditional.append(f"{rid}: {m.group(2)} bersyarat [{cond}]")
        tests.append((rid, m.group(1)[:-3].replace("/", ".") + "." + m.group(2)))
    return errs, plans, conditional, tests, len(ids)


def run_tests(tests):
    sys.path.insert(0, ROOT)
    os.chdir(ROOT)
    names = sorted({t for _, t in tests})
    suite = unittest.defaultTestLoader.loadTestsFromNames(names)
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    return res, len(names)


def main() -> int:
    ap = argparse.ArgumentParser(description="Gerbang tabel semantik kegagalan operator (P109).")
    ap.add_argument("--run", action="store_true", help="jalankan juga semua tes jangkar")
    ap.add_argument("--note", default=NOTE)
    a = ap.parse_args()
    errs, plans, cond, tests, n = check(a.note)
    print(f"baris {n} | berjangkar {len(tests)} | rencana (BELUM DIBANGUN) {len(plans)} | tes bersyarat {len(cond)} | masalah {len(errs)}")
    for e in errs:
        print("  ! " + e)
    for p in plans:
        print("  ~ rencana " + p)
    for c in cond:
        print("  ? " + c)
    bad = bool(errs)
    if a.run and tests:
        res, k = run_tests(tests)
        skipped = [(str(t).split(" ")[0], why) for t, why in res.skipped]
        failed = len(res.failures) + len(res.errors)
        print(f"--run: {k} tes jangkar | lulus {res.testsRun - failed - len(skipped)} | DILEWATI {len(skipped)} | GAGAL {failed}")
        for t, why in skipped:
            print(f"  ? DILEWATI {t}: {why}")
        for t, tb in res.failures + res.errors:
            print(f"  ! GAGAL {t}: {tb.strip().splitlines()[-1][:160]}")
        bad = bad or failed > 0
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
