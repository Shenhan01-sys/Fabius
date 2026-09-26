"""Tambahkan `tags:` ke frontmatter yang sudah ada tapi tidak punya tag area.

Kasus Konkret: lima halaman hasil migrasi (`01 - Asset Classes and Seats`, `02 - Deployed on 97`,
`04/05/06` di Results) sudah punya frontmatter lama — `type:`, `status:`, `diukur:`, `alat:` — jadi
`add_frontmatter.py` melewatinya dengan benar. Masalahnya: hub menyaring dengan `FROM #<area>`, jadi
halaman tanpa tag tidak muncul di peta mana pun. Yang ditulis sekarang cuma satu baris `tags:`,
kunci lama dibiarkan utuh — frontmatter itu catatan asal-usul angka, bukan metadata belaka.

Sekalian: satu baris di `04 - Negative Results.md` berawal dengan SPASI (` artefak:`), yang membuat
YAML-nya tidak valid. Itu dibetulkan di sini karena penyebabnya tipe yang sama dengan bug yang sudah
pernah menghanguskan berkas di repo ini (baris yang terbaca normal di layar, tidak normal di parser).

    python -X utf8 vault/scripts/tag_legacy_frontmatter.py --dry-run
    python -X utf8 vault/scripts/tag_legacy_frontmatter.py
"""
import argparse
import os
import re
import sys
# Windows: cmd.exe default cp1252 dan glyph yang kami cetak (`①④⑥` di arah, `⚠` di laporan)
# bukan bagian dari yang di-hash - jadi encoding stdout yang disetel, bukan stringnya.
# Tanpa ini, `print` bisa pecah DI TENGAH tabel dan separuh hasilnya terbaca seperti laporan penuh.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # stdout tanpa reconfigure (mis. tertangkap harness) = biarkan apa adanya

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isdir(os.path.join(ROOT, "00-Overview")):
    sys.exit(f"ROOT bukan folder vault: {ROOT}")

AREA = {"00-Overview": "overview", "01-Agent": "agen", "02-Contracts": "kontrak",
        "03-Data": "data", "04-Tools": "perkakas", "05-Ecosystem": "ekosistem",
        "06-Results": "hasil", "07-Testing": "testing", "08-Backlog": "backlog",
        "09-Inbox": "inbox", "10-Submissions": "submission", "Concepts": "concept"}
FM = re.compile(r"^---\n(.*?)\n---\n", re.S)

ap = argparse.ArgumentParser()
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()

touched = clean = 0
for folder, tag in AREA.items():
    d = os.path.join(ROOT, folder)
    for f in sorted(os.listdir(d)):
        if not f.endswith(".md"):
            continue
        p = os.path.join(d, f)
        text = open(p, encoding="utf-8").read()
        m = FM.match(text)
        if not m:
            continue
        block = m.group(1)
        if re.search(r"^tags:", block, re.M):
            continue
        # kunci yang diwarisi frontmatter lama tetap dibaca manusia; tag ditambahkan di awal
        new_block = f"tags: [{tag}]" + "\n" + block
        new = "---\n" + new_block + text[m.end(1):]
        # YAML tidak boleh punya kunci yang menjorok tanpa induk. `.lstrip()` pada "\n artefak:"
        # akan menempelkan baris itu ke baris sebelumnya - jadi buang indentasinya saja.
        fixed = re.sub(r"\n +([A-Za-záéíóúñü][^:\n]*):", r"\n\1:", new)
        if fixed != new:
            for mm in re.finditer(r"\n +([A-Za-z][^:\n]*):", new):
                print(f"  strip indent YAML {folder}/{f}: {mm.group(1).strip()!r}")
            new = fixed
        print(f"  {'akan tag' if a.dry_run else 'tag     '} {folder}/{f} -> [{tag}]")
        if not a.dry_run:
            open(p, "w", encoding="utf-8", newline="\n").write(new)
        touched += 1

print(f"\n{touched} frontmatter lama dapat tag area."
      + ("  (dry-run: tidak ada yang ditulis)" if a.dry_run else ""))
print("Lanjutkan: python -X utf8 vault/scripts/sync_vault.py && python -X utf8 vault/scripts/check_links.py")
