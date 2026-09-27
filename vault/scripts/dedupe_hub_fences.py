"""Bersihkan blok dataview yang menumpuk di hub + tambahkan pemeriksaannya ke `hub_shape.py`.

Sebabnya ada di komentar `sync_vault.py`: blok baru selalu ditempel, sementara wilayah penggantiannya
berhenti DI DEPAN blok lama. Sekali tidak masalah; enam belas hub x beberapa run = tiap hub punya
banyak salinan `LIST FROM #...`. Tidak ada tautan yang rusak, jadi `check_links` tetap hijau -
persis tipe kerusakan yang cuma kelihatan kalau bentuk ikut diperiksa.

    python -X utf8 vault/scripts/dedupe_hub_fences.py
"""
import glob
import io
import os
import re
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isdir(os.path.join(VAULT, "00-Overview")):
    sys.exit(f"VAULT bukan folder vault: {VAULT}")

FENCE = re.compile(r"```dataview\n(?:[^\n]*\n)?```\n*", re.S)

n_files = n_removed = 0
for f in sorted(glob.glob(os.path.join(VAULT, "**", "00 - Hub*.md"), recursive=True)):
    t = io.open(f, encoding="utf-8").read()
    blocks = FENCE.findall(t)
    if len(blocks) <= 1:
        continue
    keep = blocks[0]
    t2 = FENCE.sub("", t)
    # sisipkan kembali SATU blok: tepat sebelum `## Terkait` kalau ada, kalau tidak di akhir berkas
    if "\n## Terkait" in t2:
        t2 = t2.replace("\n## Terkait", "\n" + keep + "\n## Terkait", 1)
    else:
        t2 = t2.rstrip() + "\n\n" + keep
    t2 = re.sub(r"\n{3,}", "\n\n", t2)
    rel = os.path.relpath(f, VAULT).replace(os.sep, "/")
    io.open(f, "w", encoding="utf-8", newline="\n").write(t2)
    print(f"  {rel}: {len(blocks)} blok -> 1")
    n_files += 1
    n_removed += len(blocks) - 1

print(f"\n{n_files} hub dibersihkan, {n_removed} blok duplikat dihapus.")

# --- tambahkan pemeriksaannya ke gerbang bentuk ------------------------------------------------
P = os.path.join(VAULT, "scripts", "hub_shape.py")
s = io.open(P, encoding="utf-8").read()
ANCHOR = '''    if "**Sumber:**" not in t:'''
NEW = '''    dups = len(re.findall(r"```dataview", t))
    if dups > 1:
        problems.append(f"{dups} blok dataview duplikat (alat penulisan meninggalkan salinan)")
    if "**Sumber:**" not in t:'''
if "dataview duplikat" in s:
    print("hub_shape sudah memeriksa duplikasi")
elif s.count(ANCHOR) != 1:
    sys.exit(f"anchor hub_shape ketemu {s.count(ANCHOR)}x (harus 1) - periksa manual")
else:
    io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(ANCHOR, NEW, 1))
    print("hub_shape sekarang memeriksa blok dataview duplikat")
