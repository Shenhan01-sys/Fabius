"""Perbaiki `hub_body()` supaya hanya menyentuh blok `## Bagian` - dan pulihkan 11 hub yang ia rusak.

Dua cacat di alat ini (beban buktinya: `vault/scripts/hub_shape.py` melaporkan 24 masalah bentuk):

1. Pengumpul baris daftar memakai `re.finditer` pada SELURUH isi hub, jadi bullet di `## Terkait`
   ikut dianggap bagian modul dan diseret masuk ke `## Bagian`.
2. Pengganti bloknya `## Bagian.*?(?=```dataview|\Z)` - yaitu sampai blok dataview. Semua yang
   berada di antara keduanya (termasuk heading `## Terkait`) ditimpa, bukan dibiarkan.

Keduanya bentuk kegagalan yang sama: alat yang menulis ulang lebih banyak dari yang ia pahami.
Perbaikannya: ambil satu blok (`## Bagian` sampai heading ``` atau `## ` berikutnya), kerjakan
hanya blok itu, tempel kembali ekornya utuh. Lalu `hub_shape.py` dipasang sebagai gerbang supaya
kerusakan bentuk berikutnya tidak menunggu seseorang membacanya.

    python -X utf8 vault/scripts/fix_hub_body_scope.py
"""
import io
import os
import re
import subprocess
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(VAULT, "scripts", "sync_vault.py")
if not os.path.isfile(SCRIPT):
    sys.exit(f"tidak ada: {SCRIPT}")

OLD = '''    listed = set()
    lines_out = []
    if text:
        for m in re.finditer(r"^-\s*\\[\\[([^\\]|]+)(?:\\|[^\\]]*)?\\]\\]([^\\n]*)$", text, flags=re.M):
            name = m.group(1).strip()
            listed.add(os.path.basename(name))
            lines_out.append(f"- [[{name}]]{m.group(2).rstrip()}")'''
NEW = '''    listed = set()
    lines_out = []
    # SATU blok saja. Versi sebelumnya memindai seluruh berkas sehingga bullet `## Terkait`
    # diseret masuk ke daftar bagian, dan mengganti sampai blok dataview sehingga heading
    # `## Terkait` tertimpa. Keduanya: alat yang menulis ulang lebih banyak dari yang ia pahami.
    block = re.search(r"^## Bagian\\n(.*?)(?=^##\\s|^```|\\Z)", text or "", flags=re.M | re.S)
    if block:
        for m in re.finditer(r"^-\s*\\[\\[([^\\]|]+)(?:\\|[^\\]]*)?\\]\\]([^\\n]*)$",
                             block.group(1), flags=re.M):
            name = m.group(1).strip()
            listed.add(os.path.basename(name))
            lines_out.append(f"- [[{name}]]{m.group(2).rstrip()}")'''

OLD2 = '''    new = re.sub(r"## Bagian.*?(?=```\\ndataview|\\Z)", "\\n".join(body) + "\\n", text, flags=re.S)
    return new'''
NEW2 = '''    blk = "\\n".join(body)
    if block:
        new = text[:block.start()] + blk.rstrip("\\n") + "\\n" + text[block.end():]
    else:
        new = text.rstrip() + "\\n\\n" + blk
    return new'''

t = io.open(SCRIPT, encoding="utf-8").read()
for label, old in (("pengumpul baris", OLD), ("penulis blok", OLD2)):
    if t.count(old) != 1:
        sys.exit(f"pola {label} ketemu {t.count(old)}x (harus 1) -> BERHENTI, jangan memaksa")
t = t.replace(OLD, NEW, 1).replace(OLD2, NEW2, 1)
io.open(SCRIPT, "w", encoding="utf-8", newline="\n").write(t)
print("sync_vault: blok Bagian sekarang ber-scoped, ekor hub utuh")

# 2) pulihkan 11 hub dari commit terakhir yang masih utuh bentuknya
hubs = [p for p in subprocess.run(["git", "-C", os.path.dirname(VAULT), "ls-files", "vault"],
                                  capture_output=True, text=True).stdout.split("\n")
        if p.rstrip().endswith("00 - Hub.md") or "00 - Hub " in p]
hubs = sorted({h for h in hubs if h.strip()})
print(f"hub ter-track: {len(hubs)}")
r = subprocess.run(["git", "-C", os.path.dirname(VAULT), "checkout", "HEAD", "--"] + hubs,
                   capture_output=True, text=True)
if r.returncode != 0:
    sys.exit("git checkout gagal: " + (r.stderr or "").strip()[:300])
print("pulihkan dari HEAD (hub di HEAD masih punya `## Terkait`; kerusakan cuma di working tree)")

# 3) jalankan sync yang sudah dibetulkan -> ia hanya MENAMBAH halaman baru
s = subprocess.run([sys.executable, "-X", "utf8", os.path.join(VAULT, "scripts", "sync_vault.py")],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print((s.stdout or "").strip()[:1200])
h = subprocess.run([sys.executable, "-X", "utf8", os.path.join(VAULT, "scripts", "hub_shape.py")],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print((h.stdout or "").strip()[-900:])
sys.exit(h.returncode)
