"""Laporan struktur vault: halaman per folder, halaman tanpa frontmatter, halaman tanpa tag area.

Kenapa perkakas ini ada di repo dan bukan `python -c` sekali pakai: di cmd.exe, `python -c` yang
berbaris banyak diam tanpa keluaran (sudah terjadi lima kali di proyek ini, tercatat di
[[04-Tools/TL7 - measurement harness]]). Alat yang bisu saat gagal tidak bisa dipakai membuktikan
apa pun — jadi ia ditulis ke berkas, diberi assert jalur, dan exit non-zero kalau strukturnya tidak
sesuai yang diklaim `Conventions.md`.

    python -X utf8 vault/scripts/structure_report.py
    python -X utf8 vault/scripts/structure_report.py --json
"""
import argparse
import collections
import json
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
    sys.exit(f"ROOT bukan folder vault: {ROOT}\n     (harus berisi 00-Overview/)")

SKIP = {"_archive", "scripts", "Sessions", "Templates"}
AREA = re.compile(r"^---\n(?:tags:\s*\[([^\]]*)\]\n)?---", re.M)

ap = argparse.ArgumentParser()
ap.add_argument("--json", action="store_true")
a = ap.parse_args()

folders = collections.OrderedDict()
no_front, no_area = [], []
for cur, dirs, files in os.walk(ROOT):
    dirs[:] = sorted(d for d in dirs if not d.startswith("."))
    rel = os.path.relpath(cur, ROOT).replace(os.sep, "/")
    top = rel == "."
    key = "(root)" if top else rel.split("/")[0]
    mds = [f for f in sorted(files) if f.endswith(".md")]
    folders.setdefault(key, [])
    for f in mds:
        p = os.path.join(cur, f)
        folders[key].append(f[:-3])
        text = open(p, encoding="utf-8", errors="replace").read(600)
        has_fm = re.match(r"^---\n.*?\n---\n", text, re.S)
        if not has_fm:
            no_front.append(f"{key}/{f} (tidak ada blok YAML sama sekali)")
            continue
        if key in SKIP or top:
            continue
        # Dua kegagalan yang berbeda dan butuh kata yang berbeda: tanpa YAML vs YAML yang tidak
        # punya `tags:`. Yang kedua tidak kelihatan di editor dan membuat halaman hilang dari peta
        # dataview - jadi ia dilaporkan dengan namanya sendiri.
        if not re.search(r"^tags:", has_fm.group(0), re.M):
            no_area.append(f"{key}/{f}")

total = sum(len(v) for v in folders.values())
if a.json:
    print(json.dumps({"total": total, "folders": folders, "no_frontmatter": no_front,
                      "no_area_tag": no_area}, indent=1, ensure_ascii=False))
else:
    for k, v in folders.items():
        print(f"{k:16} {len(v):3}  " + " | ".join(v[:8]) + (" …" if len(v) > 8 else ""))
    print(f"\ntotal halaman: {total} · tanpa YAML: {len(no_front)} · YAML tanpa `tags:`: {len(no_area)}")
    for x in no_front[:8]:
        print("  tanpa YAML   :", x)
    for x in no_area[:8]:
        print("  tanpa tag    :", x)
sys.exit(1 if no_front or no_area else 0)
