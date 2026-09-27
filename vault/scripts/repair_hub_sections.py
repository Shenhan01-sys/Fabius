"""Perbaiki bentuk 11 hub: kembalikan `**Sumber:**`, angkat baris `·` keluar dari daftar Bagian,
dan pasang `## Terkait` yang tertelan `sync_vault.py`.

Kenapa harus dibangun ulang dan tidak bisa dipulihkan dari git: kerusakan terjadi SEBELUM commit
`08cb049`, jadi HEAD pun sudah cacat (dibuktikan: `git show "HEAD:vault/05-Ecosystem/00 - Hub BNB
Ecosystem.md" | findstr Terkait` kosong). Ini catatan yang layak disimpan — commit yang "sudah rapi"
tidak otomatis berarti commit yang benar.

Yang dilakukan, per hub:
  1. kalau `**Sumber:**` tidak ada -> pasang setelah judul, menunjuk direktori yang ia petakan
     (aturan Lencana yang kutiru: sumber sebuah hub = folder yang ia dokumen, bukan berkas)
  2. baris `- [[A]] · [[B]]` yang terseret ke dalam `## Bagian` -> dipindah ke `## Terkait`
     (isinya tidak diubah, hanya tempatnya; menghapus tautan itu justru membuat halaman hilang)
  3. `## Terkait` tidak ada -> dibuat, diisi hasil (2) atau rujukan baku vault

Gerbangnya sesudah ini: `python -X utf8 vault/scripts/hub_shape.py` (harus 0 masalah).

    python -X utf8 vault/scripts/repair_hub_sections.py --dry-run
    python -X utf8 vault/scripts/repair_hub_sections.py
"""
import argparse
import glob
import io
import os
import re
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isdir(os.path.join(VAULT, "00-Overview")):
    sys.exit(f"VAULT bukan folder vault: {VAULT}")

BLOCK = re.compile(r"^## Bagian\n(.*?)(?=^##\s|^```|\Z)", re.M | re.S)
# Dulu: "^-\s*\[\[...\]\][^\n]*·[^\n]*$" - terlampau rakus, ia ikut mengangkat gloss sah
# yang memakai pemisah di dalam teksnya. Sekarang hanya baris yang MURNI daftar tautan.
DOTLINE = re.compile(r"^(?:-\s*)?\[\[[^\]]+\]\](?:\s*·\s*\[\[[^\]]+\]\])+\s*$", re.M)

ap = argparse.ArgumentParser()
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()

fixed = 0
for f in sorted(glob.glob(os.path.join(VAULT, "**", "00 - Hub*.md"), recursive=True)):
    rel = os.path.relpath(f, VAULT).replace(os.sep, "/")
    t = io.open(f, encoding="utf-8").read()
    out = t
    notes = []

    # 1. **Sumber:**
    if "**Sumber:**" not in out:
        folder = rel.split("/")[0]
        src = f"`{folder}/`" if folder != "Concepts" else "`Concepts/`"
        if "08-Backlog" in rel:
            src = "`vault/08-Backlog/`"
        out = re.sub(r"(?m)^(# .+\n)", r"\1\n**Sumber:** " + src + "\n", out, count=1)
        notes.append(f"**Sumber:** {src} dipasang")

    # 2. baris `·` yang terseret ke daftar Bagian -> angkat
    moved = []
    m = BLOCK.search(out)
    if m:
        body = m.group(1)
        for line in DOTLINE.findall(body):
            moved.append(line)
        if moved:
            out = out[:m.start()] + "## Bagian\n" + DOTLINE.sub("", body) + out[m.end():]
            out = re.sub(r"\n{3,}", "\n\n", out)
            notes.append(f"{len(moved)} baris `·` diangkat keluar dari Bagian")

    # 3. ## Terkait
    if "## Terkait" not in out:
        tail = "\n".join(moved) if moved else "- [[Quick-Reference]] · [[Index]] · [[Conventions]]"
        fence = ""
        mf = re.search(r"```dataview.*?```", out, re.S)
        if mf:
            out = out[:mf.end()] + "\n\n## Terkait\n\n" + tail + "\n" + out[mf.end():]
        else:
            out = out.rstrip() + "\n\n## Terkait\n\n" + tail + "\n"
        notes.append("`## Terkait` dibuat " + ("(dari baris yang diangkat)" if moved else "(rujukan baku)"))

    if notes:
        print(f"  {'akan ' if a.dry_run else ''}{rel}")
        for n in notes:
            print(f"      - {n}")
        if not a.dry_run:
            io.open(f, "w", encoding="utf-8", newline="\n").write(out)
        fixed += 1

print(f"\n{fixed} hub diperbaiki." + ("  (dry-run: tidak ada yang ditulis)" if a.dry_run else ""))
