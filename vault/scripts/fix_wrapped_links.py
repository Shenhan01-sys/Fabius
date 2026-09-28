# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""Sambung tautan yang terbelah baris di SELURUH vault (alat perbaikan, bukan gerbang).

Gerbangnya tetap `check_links.py` - dia yang menemukan korbannya; alat ini yang membereskan.
Dulunya penyapu seperti ini hanya memindai `TradingKnowledge` padahal yang paling sering kusunting
ada di `06-Results`/`00-Overview` - jadi kelas kesalahan yang sama kutambal manual tiga kali dalam
sehari (halaman 10, F-D31, halaman 15).

Konservatif: hanya menggabung bila baris MEMBUKA `[[` tanpa menutupnya, dan baris berikutnya bukan
bullet/tabel/heading/kutipan. Pemeriksaan setelah jalan bukan "berkas menyusut" (menyambung baris
tanpa indentasi mengganti \\n dengan satu spasi = panjang sama), tapi "tidak ada lagi penyebabnya".

Dipakai:  python -X utf8 vault/scripts/fix_wrapped_links.py
"""
import io
import os
import re

V = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # .../vault
AWAL = ("-", "|", "#", ">", "!", "```")
POLA = re.compile(r"\[\[[^\]]*$")
BATAS_JOIN = 6


def terbuka(l):
    return bool(POLA.search(l)) and l.count("[[") > l.count("]]")


def boleh_sambung(l):
    s = l.strip()
    return bool(s) and not s.startswith(AWAL)


def satu(p):
    s = io.open(p, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    L = s.split(nl)
    out, i, kena = [], 0, 0
    while i < len(L):
        g, naik = L[i], 0
        while i + 1 < len(L) and terbuka(g) and boleh_sambung(L[i + 1]) and naik < BATAS_JOIN:
            g = g + " " + L[i + 1].strip()
            i += 1
            naik += 1
            kena += 1
        out.append(g)
        i += 1
    if not kena:
        return 0
    baru = nl.join(out)
    sisa = sum(1 for x in baru.split(nl) if terbuka(x))
    if sisa:
        raise SystemExit("MASIH ADA %d baris membuka [[ tanpa menutup di %s - periksa manual, "
                         "jangan dipaksa" % (sisa, os.path.relpath(p, V)))
    assert baru.count("[[") == s.count("[[") and baru.count("]]") == s.count("]]"), p
    io.open(p, "w", encoding="utf-8", newline="").write(baru)
    return kena


def main():
    ubah = join = 0
    for root, dirs, fs in os.walk(V):
        dirs[:] = [d for d in dirs if d not in ("_archive", ".git")]
        for f in fs:
            if not f.endswith(".md"):
                continue
            k = satu(os.path.join(root, f))
            if k:
                print("sambung %-54s (%d join)" % (os.path.relpath(os.path.join(root, f), V), k))
                ubah += 1
                join += k
    print("selesai: %d join di %d berkas" % (join, ubah))


if __name__ == "__main__":
    main()
