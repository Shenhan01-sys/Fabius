"""Tanam frontmatter (`tags:` + `aliases`) di halaman vault yang tidak punya.

Kenapa penting, bukan kosmetik: di vault ini `dataview` di setiap hub menyaring dengan `FROM
#<area>`. Halaman tanpa frontmatter tidak muncul di peta mana pun - ia ada di disk tapi tidak bisa
ditemukan, dan itu kegagalan yang tidak terdengar. 12 halaman hasil migrasi masuk ke folder baru
dengan isi utuh tapi tanpa frontmatter; itu yang dibersihkan di sini.

Skrip ini TIDAK menimpa halaman yang sudah punya frontmatter, dan tidak menulis apa pun di folder
yang di-skip (`_archive/`, `scripts/`, `Templates/`).

    python -X utf8 vault/scripts/add_frontmatter.py --dry-run
    python -X utf8 vault/scripts/add_frontmatter.py
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

# folder -> (tag area, prefiks identitas yang dipakai halaman ini)
AREA = {
    "00-Overview": ("overview", "O"),
    "01-Agent": ("agen", "A"),
    "02-Contracts": ("kontrak", "C"),
    "03-Data": ("data", "D"),
    "04-Tools": ("perkakas", "TL"),
    "05-Ecosystem": ("ekosistem", "E"),
    "06-Results": ("hasil", "R"),
    "07-Testing": ("testing", "T"),
    "08-Backlog": ("backlog", "P"),
    "09-Inbox": ("inbox", "S"),
    "10-Submissions": ("submission", "SUB"),
    "Concepts": ("concept", ""),
}
SKIP_DIRS = {"_archive", "scripts", "Templates", "Sessions", ".obsidian", ".git"}
FM = re.compile(r"^---\n.*?\n---\n", re.S)

ap = argparse.ArgumentParser()
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()

added = skipped = 0
for cur, dirs, files in os.walk(ROOT):
    dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
    rel_top = os.path.relpath(cur, ROOT).split(os.sep)[0]
    for f in sorted(files):
        if not f.endswith(".md"):
            continue
        p = os.path.join(cur, f)
        text = open(p, encoding="utf-8").read()
        if FM.match(text):
            skipped += 1
            continue
        name = f[:-3]
        area, idp = AREA.get(rel_top, ("reference", ""))
        if rel_top == "." or area == "reference":
            tags = ["reference"] if not name.startswith("_") else ["generated"]
        else:
            m = re.match(rf"^{idp}(\d+)", name) if idp else None
            tags = [area] + ([f"{idp}{m.group(1)}"] if m else [])
            if name.startswith("00 - Hub"):
                tags.append("hub")
        if rel_top in AREA and not name.startswith("00 - Hub") and not re.match(r"^\d", name) \
           and not (idp and name.startswith(idp)):
            tags.append(name.split(" ")[0])       # "Session-2026-..." tetap ter-tag jelas
        head = "---\ntags: [%s]\n---\n\n" % ", ".join(tags)
        print(f"  {'akan tanam' if a.dry_run else 'tanam   '} {os.path.relpath(p, ROOT)} -> [{', '.join(tags)}]")
        if not a.dry_run:
            open(p, "w", encoding="utf-8", newline="\n").write(head + text)
        added += 1

print(f"\n{added} halaman dapat frontmatter, {skipped} sudah punya (tidak disentuh)."
      + ("  (dry-run: tidak ada yang ditulis)" if a.dry_run else ""))
