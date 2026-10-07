"""Bangun deck PPTX dari folder ini: satu berkas md = satu slide (`NN - Judul.md`), gaya dari `99 - Design Style.md`.

    python -X utf8 vault/13-SubmmisionsDocs/build/build_deck.py                 # -> build/out/Fabius-Submission-Deck.pptx
    python -X utf8 vault/13-SubmmisionsDocs/build/build_deck.py --check         # validasi md + guard angka, tanpa menulis
    python -X utf8 vault/13-SubmmisionsDocs/build/build_deck.py --render        # + PDF/PNG untuk memeriksa tampilan (LibreOffice + pdftoppm)
    python -X utf8 vault/13-SubmmisionsDocs/build/build_deck.py --fonts safe    # Arial/Courier New bila Archivo/Inter/JetBrains Mono belum terpasang
    python -X utf8 vault/13-SubmmisionsDocs/build/build_deck.py --only 5,6      # hanya slide tertentu (uji cepat)

Butuh: pip install -r vault/13-SubmmisionsDocs/build/requirements.txt (python-pptx, PyYAML, Pillow).
Angka di slide ditulis `{{kunci}}` dan diisi dari web/public/data/snapshot.json; `guards` di front matter menggagalkan build bila
kalimat naratif tidak lagi benar. Keluar: 0 bersih · 1 md/guard salah · 2 masukan hilang.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from deckgen import build as B  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--folder", default=os.path.dirname(HERE), help="folder md (bawaan: folder induk build/)")
    ap.add_argument("--out", default=None, help="berkas .pptx keluaran")
    ap.add_argument("--snapshot", default=None, help="snapshot.json (bawaan: web/public/data/snapshot.json di akar repo)")
    ap.add_argument("--fonts", choices=["brand", "safe"], default=None, help="brand = Archivo/Inter/JetBrains Mono (FE); safe = Arial/Courier New")
    ap.add_argument("--only", default="", help="nomor slide dipisah koma, mis. 5,6")
    ap.add_argument("--check", action="store_true", help="validasi saja")
    ap.add_argument("--render", action="store_true", help="juga hasilkan PDF + PNG di build/out/png (butuh soffice + pdftoppm)")
    a = ap.parse_args(argv)
    try:
        only = {int(x) for x in a.only.split(",") if x.strip()} or None
    except ValueError:
        ap.error("--only: nomor slide harus bilangan bulat dipisah koma, mis. 5,6")
    try:
        rep = B.build(a.folder, a.out, snapshot=a.snapshot, font_profile=a.fonts, only=only, check_only=a.check)
    except B.BuildError as e:
        print("BUILD GAGAL:", file=sys.stderr)
        for line in e.errors:
            print("  - " + line, file=sys.stderr)
        return 1
    except (OSError, KeyError) as e:
        print(f"masukan hilang: {e}", file=sys.stderr)
        return 2
    print(f"{rep.n_slides} slide dibaca · angka per {rep.facts['asof']} (commit {rep.facts['commits']}, terverifikasi {rep.facts['verified']}, alarm {rep.facts['alarms']})")
    for where, msg, ok in rep.guards:
        print(f"  guard {'ok  ' if ok else 'GAGAL'} {where}: {msg}")
    if a.check:
        print("validasi bersih (tidak menulis berkas).")
        return 0
    for w in rep.warnings:
        print("  peringatan:", w)
    print(f"ditulis: {rep.out}")
    if a.render:
        try:
            imgs = B.render_images(rep.out, os.path.join(os.path.dirname(rep.out), "png"))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"render gagal: {e}", file=sys.stderr)
            return 1
        print(f"PNG: {len(imgs)} berkas" if imgs else "render dilewati: soffice/pdftoppm tidak ada")
    return 0


if __name__ == "__main__":
    sys.exit(main())
