#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Gerbang: repo tidak boleh merakit path dengan backslash atau drive absolut.

Alasannya terjadi 29 Sep 2026, bukan hipotetis: `tools/mirror_test.py` merakit jalur berkasnya
dengan menggabungkan konstanta root dan raw-string berisi pemisah Windows. Di mesin penulis itu
jalan; di runner Linux pemisah itu menjadi bagian dari NAMA berkas, dan job `paper-book.yml` mati
di langkah pertama dengan FileNotFoundError. Bug semacam ini secara harfiah tidak bisa terlihat
dari mesin yang menulisnya - jadi ia harus ditangkap pemeriksaan, bukan oleh keberuntungan OS.

Dua pola yang dipanggil (sengaja tanpa contoh literal, supaya gerbang ini tidak menangkap
dokumentasinya sendiri):
  A) penggabungan path: tanda `+` diikuti raw-string yang berawalan pemisah berkas lalu sebuah
     nama segmen dan pemisah lagi - pola regex biasa seperti `\b` atau `\]\]` tidak kena
  B) drive absolut di dalam raw-string - tidak akan pernah ada di mesin orang lain

Exit 1 kalau ada yang tersisa.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.dirname(HERE)
ROOT = os.path.dirname(V)
# Hanya tangkap CUAN PATH (`+ r"\segmen\..."`). Versi pertama memanggil 5 hal - termasuk `r"\b"`,
# `r"\]\]"`, dan contoh di docstring-nya sendiri - dan gerbang yang menghasilkan positif-palsu
# akan dimatikan orang, bukan dipatuhi.
P_GABUNG = re.compile(r'\+\s*r"\\+[A-Za-z0-9_.\-]+\\')
P_DRIVE = re.compile(r'r"[A-Za-z]:\\')
LEWAT = {".git", "node_modules", "__pycache__", ".qwen", "vendor", "references", "Fabius",
         "AgenticTrack"}


def utama():
    salah, dicek = [], 0
    for folder, dirs, fs in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in LEWAT]
        for f in fs:
            if not f.endswith(".py"):
                continue
            p = os.path.join(folder, f)
            try:
                teks = io.open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            for n, ln in enumerate(teks.splitlines(), 1):
                dicek += 1
                st = ln.strip()
                if st.startswith("#") or '"""' in ln or "re.compile" in ln:
                    continue
                if P_GABUNG.search(ln) or P_DRIVE.search(ln):
                    salah.append((os.path.relpath(p, ROOT), n, st[:120]))
    print("baris python dipindai: %d | path tidak portabel: %d" % (dicek, len(salah)))
    for f, n, t in salah[:20]:
        print("  %-46s:%-4d %s" % (f, n, t))
    if salah:
        print("\nPath dirakit dengan backslash/drive: alat ini hidup di satu mesin dan mati di "
              "runner. Ganti dengan os.path.join.")
        sys.exit(1)
    print("OK: semua perakitan path portabel (lintas OS).")


if __name__ == "__main__":
    utama()
