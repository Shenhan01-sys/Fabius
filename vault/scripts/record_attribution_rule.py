"""Catat keputusan atribusi commit (F-D22) + aturan yang menempelnya di Conventions.

Ditulis sebagai skrip dengan assert karena dua suntingan manualku hari ini salah arah dan
meninggalkan berkas yang tetap lolos compile tapi strukturnya rusak. Untuk teks, cara mengamannya
sama: pola wajib ketemu tepat satu kali, dan tambahan ditulis di tempat yang benar - F-D22
DITEMPEL DI AKHIR log (chronological), bukan disisipkan sebelum F-D21.
"""
import io
import os
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(VAULT, "00-Overview", "03 - Decisions.md")
C = os.path.join(VAULT, "Conventions.md")

DEC_NEW = """## F-D22 — Atribusi commit: builder saja, tanpa trailer AI · 27 Sep 2026

Builder mengoreksi keras setelah commit kami membawa `Co-Authored-By: Claude`:
*"sejak kapan kita build bareng claude? … Kita gaada build sama sekali dengan claude."* Aturannya:
**tidak ada trailer atribusi AI di pesan commit manapun**, dan author git tetap identitas builder
yang sudah terkonfigurasi (`Hans Gunawan <hansgunawan775@gmail.com>`).

Ini bukan soal gaya. Repo ini publik dan dibaca sebagai bukti kerja siapa: klaim kontribusi adalah
klaim faktual, dan trailer yang salah tidak netral - ia memindahkan kredit ke pihak yang tidak
memegang arah pekerjaan.

**Yang dilakukan (terukur, bukan dirasa):** trailer ditemukan di **2** commit Fabius (`08cb049`
restructure vault, `5e4468f` P1+P8). Menghapus yang lama berarti menulis ulang **147 commit** -
termasuk ±143 commit perekam `wallet flow` yang sudah publik - karena hash rantai. Builder memilih
menulis ulang yang terbaru saja: **3 hash berubah** (`5e4468f` → `1f0faec` + dua turunannya),
diverifikasi `git diff` kosong terhadap tip origin sebelumnya (`defa461`) sehingga **isi tidak berubah
sedikit pun**; commit perekam yang masuk di tengah rewrite dipetik dulu sebelum
`--force-with-lease`, supaya tidak ada jendela aliran yang hilang; ref cadangan
`backup/pra-strip-trailer` ditinggalkan di repo lokal.

Konsekuensi yang diterima sadar: satu commit lama (`08cb049`) tetap menampilkan trailer itu. Kalau
suatu hari rentang 147 commit itu jadi murah (mis. riwayat di-squash untuk submission), yang
tersisa tinggal menghapusnya sekali lagi.

**Terkait:** [[00-Overview/05 - Corrections]] · [[Conventions]] §Turunan ·
[[09-Inbox/Session-2026-09-27-siang]]
"""

CONV_ANCHOR = "- **Gerbang bentuk, bukan hanya gerbang tautan.**"
CONV_NEW = """- **Commit bukan tempat kredit alat.** Author = builder; tidak ada `Co-Authored-By:` AI dan
  tidak ada "dibangun bersama" siapa pun di pesan commit (F-D22 di [[00-Overview/03 - Decisions]]).
  Kalau peran alat perlu dicatat, itu isi dokumen - bukan metadata yang dibaca orang sebagai klaim
  kontribusi. Alat yang menghapus trailer dari riwayat juga wajib menghitung **biayanya** lebih
  dulu (`git rev-list --count <base>..HEAD`): satu commit lama bisa menyeret ratusan.
"""

if not os.path.isfile(D) or not os.path.isfile(C):
    sys.exit("path vault tidak ketemu")

t = io.open(D, encoding="utf-8").read()
if "F-D22" in t:
    print("  F-D22 sudah ada - tidak diulang")
else:
    if "## F-D21 " not in t:
        sys.exit("F-D21 tidak ketemu sebagai dasar urutan - berhenti, jangan menempel buta")
    io.open(D, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n\n" + DEC_NEW)
    print("  F-D22 ditambahkan di akhir log keputusan")

c = io.open(C, encoding="utf-8").read()
if "Commit bukan tempat kredit alat" in c:
    print("  aturan Conventions sudah ada")
elif c.count(CONV_ANCHOR) != 1:
    sys.exit(f"anchor Conventions ketemu {c.count(CONV_ANCHOR)}x (harus 1)")
else:
    io.open(C, "w", encoding="utf-8", newline="\n").write(c.replace(CONV_ANCHOR, CONV_NEW + CONV_ANCHOR, 1))
    print("  aturan atribusi dipasang di Conventions (sebelum gerbang bentuk)")
