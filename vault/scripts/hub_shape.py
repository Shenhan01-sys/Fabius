"""Periksa BENTUK setiap hub, bukan hanya tautannya.

Alasannya konkret dan terjadi hari ini: `sync_vault.py` versi append-only menyalin ulang blok
`## Bagian` dan pola penggantinya melahap seluruh ekor berkas sampai blok `dataview`. Akibatnya
heading `## Terkait` **hilang** di beberapa hub dan baris `- [[A]] · [[B]]` ikut terserap ke dalam
daftar bagian. `check_links.py` tidak melihat itu: tautannya tetap valid, hanya tempatnya yang
pindah. Jadi graf hijau bisa menyembunyikan dokumen yang rusak - dan ini alat yang sama sekali
tidak memeriksa bentuk.

Dipakai sebagai gerbang: `python -X utf8 vault/scripts/hub_shape.py` -> exit non-zero kalau ada
hub yang bentuknya tidak lengkap.
"""
import glob
import io
import os
import re
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isdir(os.path.join(VAULT, "00-Overview")):
    sys.exit(f"VAULT bukan folder vault: {VAULT}")

BUTUH = ("**Bagian dari:**", "**Sumber:**")   # hub pakai **Sumber:** ke direktori
BAD = []
n = 0
for f in sorted(glob.glob(os.path.join(VAULT, "**", "00 - Hub*.md"), recursive=True)):
    n += 1
    rel = os.path.relpath(f, VAULT).replace(os.sep, "/")
    t = io.open(f, encoding="utf-8").read()
    problems = []
    if "## Bagian" not in t:
        problems.append("tidak ada `## Bagian`")
    if "## Terkait" not in t:
        problems.append("`## Terkait` HILANG")
    m = re.search(r"## Bagian\n(.*?)(?=\n## |\n```|\Z)", t, flags=re.S)
    # Baris yang MURNI daftar tautan ([[A]] · [[B]]) = terserap. Gloss yang kebetulan
    # memakai pemisah di dalam teksnya (C4: “x·y=k”) adalah isi yang sah, bukan kerusakan.
    if m and re.search(r"(?:-\s*)?\[\[[\]]+\]\](?:\s*·\s*\[\[[\]]+\]\])+\s*$", m.group(1), re.M):
        problems.append("baris tautan murni terserap ke dalam daftar Bagian")
    if "```dataview" not in t:
        problems.append("tidak ada blok dataview (peta tidak akan pernah jujur sendiri)")
    dups = len(re.findall(r"```dataview", t))
    if dups > 1:
        problems.append(f"{dups} blok dataview duplikat (alat penulisan meninggalkan salinan)")
    if "**Sumber:**" not in t:
        problems.append("tidak ada **Sumber:** (hub wajib menunjuk direktori yang ia dipetakan)")
    print(f"{'ok  ' if not problems else 'RUSAK'} {rel}")
    for p in problems:
        print(f"      - {p}")
        BAD.append(f"{rel}: {p}")

print(f"\n{n} hub diperiksa, {len(BAD)} masalah bentuk.")
sys.exit(1 if BAD else 0)
