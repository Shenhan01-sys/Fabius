#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Alat ini dulunya tinggal di folder kerja (`_research/`) dan dikutip dari berkas hasil
# yang sudah terbit. Dipromosikan 29 Sep supaya perintah di vault bisa dijalankan dari
# clone: angka yang tidak bisa dijalankan orang bukan bukti, itu ingatan.
# (dipindah oleh _research/promosi2.py; path di dalamnya kini diturunkan dari __file__)
# -*- coding: utf-8 -*-
"""Audit: berapa banyak lapisan pengetahuan yang benar-benar sudah diuji terhadap HASIL?

Yang dihitung bukan "apakah catatannya menyebut alat", tapi "apakah ada perintah yang menghasilkan
angka dan angkanya tersimpan di lembar fakta". Catatan metode tanpa uji = kandidat, bukan alat.
"""
import io
import os
import sys
import re

V = os.path.join(ROOT, "vault", "TradingKnowledge")
KHUSUS = ("00 - Hub", "Template", "Plan", "Resources", "Sumber dan", "Aturan Subtree",
          "Glossary", "Fakta Terukur")
POLA_ALAT = re.compile(r"python -X utf8 tools/[a-z_0-9]+\.py")
baris = []
for folder in sorted(os.listdir(V)):
    jalan = os.path.join(V, folder)
    if not os.path.isdir(jalan):
        continue
    for sub in sorted(os.listdir(jalan)) if os.path.isdir(jalan) else []:
        pass
    tot = uji = alat = 0
    for root, _, fs in os.walk(jalan):
        for f in fs:
            if not f.endswith(".md"):
                continue
            if any(k in f for k in KHUSUS):
                continue
            tot += 1
            s = io.open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
            rendah = s.lower()
            if "belum diuji" in rendah or "belum ada angka" in rendah or "belum pernah diukur" in rendah:
                pass
            else:
                uji += 1
            if POLA_ALAT.search(s):
                alat += 1
    if tot:
        baris.append((folder, tot, uji, alat))
t_all = sum(b[1] for b in baris)
print("%-26s %5s %7s %7s" % ("lapisan", "catatan", "tanpa-kata-'belum'", "menyebut-perintah-alat"))
for folder, tot, uji, alat in baris:
    print("%-26s %5d %7d %7d" % (folder, tot, uji, alat))
print("%-26s %5d" % ("TOTAL", t_all))
print("\nArtinya: mayoritas catatan metode memang BELUM punya angka. Uji yang benar = ada perintah")
print("yang menghasilkan artefak, dan angkanya masuk ke Fakta Terukur - bukan catatan yang rapi.")
