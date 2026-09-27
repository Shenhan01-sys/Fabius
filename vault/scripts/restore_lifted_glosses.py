"""Kembalikan baris bagian yang kutangkat salah, dan persempit aturan pengangkatannya.

Kejadian: `repair_hub_sections.py` mengangkat "baris `·`" dari daftar `## Bagian` karena mengira itu
bullet `## Terkait` yang terseret. Padahal dua di antaranya gloss yang sah dan kebetulan memakai
karakter pemisah di dalam teksnya (`C4 - DemoPair and DemoAsset` dan `TL7 - measurement harness`).
Akibatnya gloss mereka hilang dari peta dan `sync_vault` menambahkan entri baru tanpa penjelasan -
persis kebalikan dari yang harus dilakukan alat itu.

Aturan yang benar: angkat HANYA baris yang seluruh isinya tautan yang dipisahkan `·` (pola
`## Terkait`), bukan baris yang punya penjelasan setelah tanda pisah.

    python -X utf8 vault/scripts/restore_lifted_glosses.py
"""
import glob
import io
import os
import re
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isdir(os.path.join(VAULT, "00-Overview")):
    sys.exit(f"VAULT bukan folder vault: {VAULT}")

BLOCK = re.compile(r"^## Bagian\n(.*?)(?=^##\s|^```|\Z)", re.M | re.S)
TERKAIT = re.compile(r"^## Terkait\n(.*?)(?=^##\s|^```|\Z)", re.M | re.S)
# baris Terkait sejati: hanya [[tautan]] yang dipisah · (boleh diawali '- '), TANPA penjelasan
PURE_LINKS = re.compile(r"^(?:-\s*)?\[\[[^\]]+\]\](?:\s*·\s*\[\[[^\]]+\]\])+\s*$")

# 1) persempit aturan di alat yang merusak
SCRIPT = os.path.join(VAULT, "scripts", "repair_hub_sections.py")
t = io.open(SCRIPT, encoding="utf-8").read()
old = 'DOTLINE = re.compile(r"^-\s*\\[\\[[^\\]]+\\]\\][^\\n]*·[^\\n]*$", re.M)'
new = ('# Dulu: "^-\\s*\\[\\[...\\]\\][^\\n]*·[^\\n]*$" - terlampau rakus, ia ikut mengangkat gloss sah\n'
       '# yang memakai pemisah di dalam teksnya. Sekarang hanya baris yang MURNI daftar tautan.\n'
       'DOTLINE = re.compile(r"^(?:-\\s*)?\\[\\[[^\\]]+\\]\\](?:\\s*·\\s*\\[\\[[^\\]]+\\]\\])+\\s*$", re.M)')
if t.count(old) == 1:
    io.open(SCRIPT, "w", encoding="utf-8", newline="\n").write(t.replace(old, new, 1))
    print("aturan DOTLINE dipersempit di repair_hub_sections.py")
elif "MURNI daftar tautan" in t:
    print("aturan sudah dipersempit (tidak diulang)")
else:
    sys.exit(f"pola DOTLINE tidak ketemu (count={t.count(old)}) - perbaiki manual, jangan menebak")

# 2) kembalikan baris yang salah angkat
repaired = 0
for f in sorted(glob.glob(os.path.join(VAULT, "**", "00 - Hub*.md"), recursive=True)):
    rel = os.path.relpath(f, VAULT).replace(os.sep, "/")
    folder = rel.split("/")[0]
    parts = {os.path.splitext(os.path.basename(x))[0]
             for x in glob.glob(os.path.join(VAULT, folder, "*.md"))}
    t = io.open(f, encoding="utf-8").read()
    mk = TERKAIT.search(t)
    mb = BLOCK.search(t)
    if not (mk and mb):
        continue
    keep, back = [], []
    for line in mk.group(1).splitlines():
        s = line.strip()
        if not s.startswith("-"):
            keep.append(line)
            continue
        mlink = re.match(r"^-\s*\[\[([^\]|]+)", s)
        name = os.path.basename(mlink.group(1).strip()) if mlink else ""
        # bagian dari folder ini DAN bukan baris tautan murni -> salah angkat, kembalikan
        if name in parts and not PURE_LINKS.match(s):
            back.append(line)
        else:
            keep.append(line)
    if not back:
        continue
    body = mb.group(1).rstrip("\n")
    # hilangkan entri gundul yang ditambahkan sync_vault untuk halaman yang sama
    for line in back:
        name = re.match(r"^-\s*\[\[([^\]|]+)", line.strip()).group(1).strip()
        body = re.sub(r"(?m)^-\s*\[\[" + re.escape(name) + r"\]\]\s*←.*$\n?", "", body)
    newblk = body + "\n" + "\n".join(back) + "\n"
    out = t[:mb.start()] + "## Bagian\n" + newblk + t[mb.end():]
    m2 = TERKAIT.search(out)
    out = out[:m2.start()] + "## Terkait\n" + ("\n".join(keep) if keep else
             "\n- [[Quick-Reference]] · [[Index]] · [[Conventions]]") + "\n" + out[m2.end():]
    out = re.sub(r"\n{3,}", "\n\n", out)
    io.open(f, "w", encoding="utf-8", newline="\n").write(out)
    print(f"  {rel}: {len(back)} gloss dikembalikan ke Bagian")
    repaired += len(back)

print(f"\n{repaired} baris gloss dikembalikan.")
