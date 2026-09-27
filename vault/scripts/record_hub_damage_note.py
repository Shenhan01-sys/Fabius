"""Satu baris ke register koreksi: alat perawat vault-ku sendiri merusak dokumen, dan gerbang lama
tidak melihatnya.

Ditulis sebagai skrip dengan assert karena `python -c` multi-baris di cmd.exe diam tanpa keluaran
(sudah keenam kalinya di proyek ini), dan baris ini isinya persis tentang jangan memercayai alat
yang diam.
"""
import io
import os
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(VAULT, "00-Overview", "05 - Corrections.md")
if not os.path.isfile(P):
    sys.exit(f"tidak ada: {P}")

ANCHOR = '| 27 Sep | hipotesis "selisih 17 vs 11 itu karena'
ROW = (
    "| 27 Sep | \"perkakas perawatan vault sudah hijau, jadi aman\" | dua alatku sendiri merusak "
    "dokumen setelah gerbangnya hijau: `sync_vault.py` menelan heading `## Terkait` + `**Sumber:**` "
    "di **11 hub** (regex-nya menulis ulang sampai blok dataview), lalu `repair_hub_sections.py` "
    "mengangkat 2 gloss sah keluar dari daftar Bagian (aturannya mencari karakter pemisah di mana "
    "saja, dan `x·y=k` kebagian). `check_links.py` tetap melaporkan `Broken: 0` sepanjang itu: "
    "tautannya valid, **tempatnya** yang pindah | `scripts/hub_shape.py` (baru; 11 hub, 0 masalah) "
    "+ `scripts/restore_lifted_glosses.py`. Catatan yang tidak enak: commit `08cb049` sendiri sudah "
    "cacat, jadi `git checkout` tidak memulihkannya — bentuk harus digate, bukan diasumsikan\n"
)

t = io.open(P, encoding="utf-8").read()
if "perkakas perawatan vault sudah hijau" in t:
    print("baris sudah ada - tidak ditulis ulang")
    sys.exit(0)
if t.count(ANCHOR) != 1:
    sys.exit(f"anchor ketemu {t.count(ANCHOR)}x (harus 1) -> BERHENTI")
i = t.index(ANCHOR)
out = t[:i] + ROW + t[i:]
io.open(P, "w", encoding="utf-8", newline="\n").write(out)
print("satu baris koreksi dipasang (sebelum baris hipotesis P6b)")
