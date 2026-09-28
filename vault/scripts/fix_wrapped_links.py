# -*- coding: utf-8 -*-
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sambung tautan yang terbelah baris di SELURUH vault (alat perbaikan, bukan gerbang).

Gerbangnya tetap `check_links.py` - dia yang menemukan korbannya. Alat ini yang membereskan,
dan dulunya hanya memindai `TradingKnowledge` sementara yang paling sering kusunting ada di
`06-Results`/`00-Overview`. Konservatif: hanya menggabung bila baris membuka `[[` tanpa menutup
`]]`, dan baris berikutnya bukan bullet/tabel/heading/kutipan.

Ini ketiga kalinya hari ini aku menambal kasus yang sama manual (halaman 10, F-D31, halaman 15).
Alat `fix_tk_wrapped_links.py` lama hanya memindai `TradingKnowledge`, padahal yang paling sering
kusunting adalah `06-Results` dan `00-Overview`. Jadi: cakupan diperluas, dan batas aman dipasang -
hanya menyambung bila baris berikutnya adalah LANJUTAN tanpa tanda `-`/`|` di awal (baris tabel
dan bullet tidak boleh dimakan).
"""
import io
import os
import re

V = r"C:\Users\hansg\HansProject\Bnb-Indonesia-Hackathon\Fabius\vault"
POLA = re.compile(r"\[\[[^\]]*\n[^\]]*\]\]")
ubah = 0
for root, _, fs in os.walk(V):
    if "_archive" in root:
        continue
    for f in fs:
        if not f.endswith(".md"):
            continue
        p = os.path.join(root, f)
        s = io.open(p, encoding="utf-8", newline="").read()
        nl = "\r\n" if "\r\n" in s else "\n"
        L = s.split(nl)
        out, i, kena = [], 0, 0
        while i < len(L):
            g = L[i]
            # hanya gabung kalau baris ini MENUTUP setengah wikilink dan baris berikut melanjutkannya
            while i + 1 < len(L) and g.count("[[") > g.count("]]") and L[i + 1].strip() \
                    and not L[i + 1].lstrip().startswith(("-", "|", "#", ">", "!", " ")) \
                    and "]" not in g.split("[[")[-1]:
                g = g + " " + L[i + 1].strip()
                i += 1
                kena += 1
            out.append(g)
            i += 1
        if kena:
            baru = nl.join(out)
            assert len(baru) < len(s), p          # menyambung baris = berkas sedikit menyusut
            io.open(p, "w", encoding="utf-8", newline="").write(baru)
            print("sambung %-52s (%d join)" % (os.path.relpath(p, V), kena))
            ubah += 1
print("berkas disentuh: %d" % ubah)
