"""Sensus tes (P110): jalankan suite Python dan cetak yang DILEWATI di samping yang lulus - "OK" saja menyembunyikan tes yang tidak pernah jalan.

Masalahnya konkret: uji anvil (`test_signal_commit.AnvilEndToEndTests`, jalur penuh komit + ungkap lewat kode worker) memakai `skipUnless(anvil)`. Di mesin
tanpa anvil ia dilewati, dan `unittest` tetap mencetak `OK`. Satu-satunya tanda adalah `(skipped=N)` di ujung baris. Alat ini:
  1. SENSUS STATIS: setiap tes yang punya penanda skip (skipUnless/skipIf/skip) di kelas atau metodenya, beserta syaratnya (dibaca lewat ast);
  2. SENSUS JALAN: hasil sungguhan per golongan - lulus / DILEWATI (dikelompokkan per alasan) / GAGAL / ERROR;
  3. `--wajib-semua`: keluar 1 bila ada SATU tes pun yang dilewati. Dipakai di lingkungan yang ditetapkan (workflow `tests.yml`: anvil + forge build
     + eth-account terpasang), supaya tes bersyarat terbukti jalan setidaknya di satu tempat yang bisa diperiksa orang.

    python -X utf8 tools/test_census.py                  # sensus + jalan (dilewati dilaporkan, tidak menggagalkan)
    python -X utf8 tools/test_census.py --wajib-semua    # dilewati = gagal (CI)
    python -X utf8 tools/test_census.py --statis         # hanya sensus penanda skip, tanpa menjalankan
Keluar: 0 bersih · 1 ada GAGAL/ERROR, atau ada yang dilewati dengan --wajib-semua.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import io
import os
import sys
import time
import unittest
from collections import defaultdict
from typing import Dict, List, Tuple

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
START = "engine/tests"


def _skip_marks(node: ast.AST, src: str) -> List[str]:
    out = []
    for d in getattr(node, "decorator_list", []):
        s = ast.get_source_segment(src, d) or ""
        if ".skip" in s or s.startswith("skip"):
            out.append(" ".join(s.split()))
    return out


def static_census(start: str = START, root: str = ROOT) -> Tuple[int, List[Tuple[str, str, int]]]:
    """(jumlah metode test_*, [(berkas::Kelas[.metode], syarat, jumlah tes yang terkena)])."""
    total, marked = 0, []
    base = os.path.join(root, start)
    for name in sorted(os.listdir(base)):
        if not (name.startswith("test_") and name.endswith(".py")):
            continue
        rel = os.path.join(start, name).replace(os.sep, "/")
        with open(os.path.join(base, name), encoding="utf-8") as f:
            src = f.read()
        for cls in (n for n in ast.parse(src).body if isinstance(n, ast.ClassDef)):
            tests = [m for m in cls.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name.startswith("test_")]
            total += len(tests)
            for s in _skip_marks(cls, src):
                marked.append((f"{rel}::{cls.name}", s, len(tests)))
            for m in tests:
                for s in _skip_marks(m, src):
                    marked.append((f"{rel}::{cls.name}.{m.name}", s, 1))
    return total, marked


def run_suite(start: str = START, root: str = ROOT) -> Tuple[unittest.TestResult, float]:
    sys.path.insert(0, root)
    os.chdir(root)
    suite = unittest.defaultTestLoader.discover(start, top_level_dir=root)
    t0 = time.time()
    with contextlib.redirect_stdout(io.StringIO()):                 # cetakan tes sendiri (laporan alat yang diuji) bukan bagian sensus
        res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    return res, time.time() - t0


def grouped_skips(res: unittest.TestResult) -> Dict[str, List[str]]:
    g: Dict[str, List[str]] = defaultdict(list)
    for t, why in res.skipped:
        g[why].append(t.id())
    return dict(g)


def main() -> int:
    ap = argparse.ArgumentParser(description="Sensus tes: lulus / DILEWATI / GAGAL, dan penanda skip statis.")
    ap.add_argument("--wajib-semua", action="store_true", help="satu tes dilewati = keluar 1 (lingkungan yang ditetapkan, CI)")
    ap.add_argument("--statis", action="store_true", help="hanya sensus penanda skip, tanpa menjalankan suite")
    ap.add_argument("--start", default=START)
    a = ap.parse_args()
    total, marked = static_census(a.start)
    n_marked = sum(n for _, _, n in marked)
    print(f"SENSUS STATIS {a.start}: {total} tes, {n_marked} di bawah penanda skip ({len(marked)} penanda)")
    for where, cond, n in marked:
        print(f"  ? {where} [{n} tes] {cond}")
    if a.statis:
        return 0
    res, dur = run_suite(a.start)
    skipped = grouped_skips(res)
    n_skip = len(res.skipped)
    bad = len(res.failures) + len(res.errors)
    print(f"JALAN: {res.testsRun} tes | lulus {res.testsRun - n_skip - bad} | DILEWATI {n_skip} | GAGAL {len(res.failures)} | ERROR {len(res.errors)} | {dur:.0f} s")
    for why, ids in sorted(skipped.items()):
        print(f"  DILEWATI {len(ids)} karena \"{why}\": " + ", ".join(i.split(".")[-2] + "." + i.split(".")[-1] for i in ids[:6])
              + (" …" if len(ids) > 6 else ""))
    for t, tb in res.failures + res.errors:
        print(f"  ! {t.id()}: {tb.strip().splitlines()[-1][:200]}")
    if bad:
        print("VONIS: GAGAL")
        return 1
    if n_skip and a.wajib_semua:
        print(f"VONIS: GAGAL - {n_skip} tes dilewati di lingkungan yang seharusnya menjalankan semuanya (--wajib-semua)")
        return 1
    print("VONIS: " + ("SEMUA JALAN DAN LULUS" if not n_skip else f"LULUS, TETAPI {n_skip} TES TIDAK JALAN di mesin ini (bukan bukti untuk tes itu)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
