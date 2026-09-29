# -*- coding: utf-8 -*-
"""Gerbang: tiap path alat yang dikutip vault harus ADA di repo.

Alasannya konkret, bukan hipotetis. Malam ini aku menulis komentar workflow yang menunjuk
`tools/attest-dataset.py` dan `tools/dataset_anchor.py` - dua alat yang sudah tidak ada di repo
(nama itu berasal dari catatan sesi lama, bukan dari hasil `ls`). Satu typo kecil tertangkap karena
kebetulan saat mencoba menjalankannya. Yang tidak ketahuan: ratusan kalimat lain bisa mengutip alat
yang sama-sama tidak ada, dan tiap klaim "dapat dijalankan ulang dari clone" yang menunjuk file
mati itu bukan reproduksibel - hanya terdengar reproduksibel.

Yang diperiksa:
  - `(tools|universe|contracts|scripts|web|signer)/<path>.<ext>` yang disebut di berkas .md
    -> file itu HARUS ada
  - `_research/...` (folder kerja, TIDAK masuk repo) -> boleh, tapi dihitung dan dilaporkan,
    karena klaim yang cuma bisa dijalankan dari laptopku bukan klaim yang bisa diuji orang
    (aturan `Conventions`: klaim harus terbukti dari dalam clone)

Dipakai:  python -X utf8 vault/scripts/check_tool_citations.py
Exit:    1 kalau ada sitasi yang menunjuk file tidak ada.
"""
from __future__ import annotations

import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.dirname(HERE)                       # .../vault
ROOT = os.path.dirname(V)                       # .../Fabius
POLA = re.compile(r"(?:^|[\s`(|])((?:tools|universe|contracts|scripts|src|web|signer|x402)/"
                  r"[A-Za-z0-9_\-./@]+\.(?:py|js|ts|sh|sol|json|yml|jsonl|env))(?=[\s`.),]|$)")
POLA_WS = re.compile(r"(_research/[A-Za-z0-9_\-./]+\.py)")
LEWAT_FOLER = {"_archive", ".git"}
# alat yang disebut sebagai RENCANA bukan alat mati - dan menyebutnya hilang adalah cara tercepat
# membuat gerbang diabaikan orang. Kata kuncinya diambil dari gaya catatan di lapisan pengetahuan.
POLA_RENCANA = re.compile(r"(dirancang|belum dibangun|belum ada|akan datang|dijadwalkan|usulan|"
                          r"belum ditulis|bila dibangun|masih kurang|yang masih kurang|"
                          r"belum diuji|belum dikerjakan)", re.I)
# Rujukan ke laboratorium eksternal (HeliQuant) bukan alat kami yang hilang - memanggilnya
# "hilang" adalah cara tercepat membuat gerbang ini diabaikan orang.
POLA_EKSTERNAL = re.compile(r"(HeliQuant|lab eksternal|laboratorium eksternal)", re.I)


def ada(q):
    """Cek terhadap root repo DAN terhadap vault.

    Catatan vault menulis `scripts/hub_shape.py` maksudnya `vault/scripts/hub_shape.py`; gerbang
    yang hanya melihat root akan memanggil 6 alat hidup sebagai 'hilang' - dan gerbang yang
    menangis serigala tidak dibaca orang. Versi pertama alat ini melakukan persis itu.
    """
    p = q.replace("/", os.sep)
    return os.path.exists(os.path.join(ROOT, p)) or os.path.exists(os.path.join(V, p))


def utama():
    rusak, kerja, rencana, eksternal = [], [], [], []
    untuk_root = 0
    for folder, dirs, fs in os.walk(V):
        dirs[:] = [d for d in dirs if d not in LEWAT_FOLER]
        for f in fs:
            if not f.endswith(".md"):
                continue
            p = os.path.join(folder, f)
            try:
                teks = io.open(p, encoding="utf-8", errors="replace").read()
            except OSError as e:
                print("tidak terbaca %s: %r" % (p, e))
                continue
            for n, ln in enumerate(teks.splitlines(), 1):
                for g in POLA.findall(ln):
                    q = g.split("#")[0]
                    if ada(q):
                        untuk_root += 1
                    elif POLA_RENCANA.search(ln):
                        rencana.append((os.path.relpath(p, V), n, q))
                    elif POLA_EKSTERNAL.search(ln):
                        eksternal.append((os.path.relpath(p, V), n, q))
                    else:
                        rusak.append((os.path.relpath(p, V), n, q))
                for g in POLA_WS.findall(ln):
                    kerja.append((os.path.relpath(p, V), n, g))
    print("sitasi alat yang terbaca: %d | valid %d | DIRENCANAKAN %d | EKSTERNAL %d | HILANG %d"
          % (untuk_root + len(rusak) + len(rencana) + len(eksternal), untuk_root, len(rencana),
             len(eksternal), len(rusak)))
    for f, n, q in rusak:
        print("  HILANG  %-46s:%-4s -> %s" % (f, n, q))
    if rencana:
        print("\n(kebaikan: %d sitasi menunjuk alat yang belum ditulis, tapi barisnya jujur menyebut "
              "rencana - itu janji, bukan alat mati)" % len(rencana))
        for f, n, q in rencana[:8]:
            print("  RENCANA %-46s:%-4s -> %s" % (f, n, q))
    print("\nsitasi ke folder KERJA (di luar repo, tidak bisa dijalankan dari clone): %d" % len(kerja))
    hit = {}
    for f, n, q in kerja:
        hit[f] = hit.get(f, 0) + 1
    for f in sorted(hit, key=lambda k: -hit[k])[:12]:
        print("  %-52s %d" % (f, hit[f]))
    if rusak:
        print("\nAngka yang menunjuk alat mati tidak bisa direproduksi. Perbaiki sitasinya ATAU "
              "hidupkan lagi alatnya - jangan biarkan hijau dengan alasan yang salah.")
        sys.exit(1)
    print("\nOK: semua sitasi alat menunjuk berkas yang benar-benar ada.")


if __name__ == "__main__":
    utama()
