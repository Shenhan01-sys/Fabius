"""Audit graf vault Fabius: tautan mati, halaman tanpa penunjuk, folder yang tidak terpetakan.

    python scripts/check_links.py            # ringkas; exit 1 kalau ada yang rusak
    python scripts/check_links.py --verbose  # daftar penuh tiap temuan

Tiga pemeriksaan ini ada karena satu alasan: vault yang tidak terhubung dengan benar bukan dokumentasi,
itu tumpukan berkas — dan perbedaannya baru kelihatan saat orang lain mencoba memverifikasi kita.
"""
import argparse
import collections
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
WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
SKIP = {"_archive", "scripts"}


def md_all():
    out = []
    for cur, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
        out += [os.path.join(cur, f) for f in files if f.endswith(".md")]
    return sorted(out)


def main(verbose):
    files = md_all()
    index = collections.defaultdict(list)
    for p in files:
        index[os.path.splitext(os.path.basename(p))[0]].append(p)
    targets = set(index)

    broken = []
    incoming = collections.defaultdict(list)
    for p in files:
        text = open(p, encoding="utf-8", errors="replace").read()
        text = re.sub(r"```.*?```", "", text, flags=re.S)          # blok kode bukan rujukan
        text = re.sub(r"`[^`\n]*`", "", text)                      # inline code = contoh sintaks
        for m in WIKILINK.finditer(text):
            t = m.group(1).strip()
            base = os.path.basename(t.replace("\\", "/"))
            if base in targets:
                if os.path.abspath(index[base][0]) != os.path.abspath(p):
                    incoming[base].append(p)
            else:
                broken.append((os.path.relpath(p, ROOT).replace(os.sep, "/"), t))

    # halaman yang tidak ditunjuk dari berkas mana pun (kecuali arsip pindah & folder sesi)
    orphans = []
    exempt = {"_Auto-Index", "Index", "START-HERE", "README", "Conventions", "Dashboard",
              "Quick-Reference", "Log-Keputusan", "Pending-Tasks"}
    for p in files:
        b = os.path.splitext(os.path.basename(p))[0]
        rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
        if b in exempt or rel.startswith("Sessions/") or "DIARSIPKAN" in open(
                p, encoding="utf-8", errors="replace").read()[:400] or rel.startswith("Templates/"):
            continue
        if not incoming.get(b):
            orphans.append(rel)

    # folder yang belum punya hub
    # Dikecualikan dengan alasan, bukan diam-diam:
    #   08-Backlog  -> satu-satunya halamannya sudah berupa peta (P1..P8), hub cuma salinan indeks
    #   Concepts    -> catatan lintas-lapis yang dirujuk dari part note; tidak punya "bagian"
    #   Templates   -> dibaca oleh manusia yang menulis halaman baru, bukan untuk dinavigasi
    # Ketiganya tetap masuk pemeriksaan orphan: halaman yang tidak ditunjuk siapa pun tetap salah.
    NOHUB_OK = {"08-Backlog", "Concepts", "Templates"}
    nohub = []
    for d in sorted(x for x in os.listdir(ROOT)
                    if os.path.isdir(os.path.join(ROOT, x)) and x not in SKIP
                    and not x.startswith(".") and not x.startswith("_")):
        subs = [f for f in os.listdir(os.path.join(ROOT, d)) if f.endswith(".md")]
        if subs and not any(f.startswith("00 - Hub") for f in subs) and d not in NOHUB_OK:
            nohub.append(d)

    print(f"berkas .md: {len(files)} · target unik: {len(targets)}")
    print(f"Broken: {len(broken)}")
    if broken and verbose:
        for src, t in broken:
            print(f"  {src}  ->  [[{t}]]")
    elif broken:
        for src, t in sorted(set(broken))[:8]:
            print(f"  {src}  ->  [[{t}]]")
    print(f"Tanpa penunjuk (orphan): {len(orphans)}")
    for o in (orphans if verbose else orphans[:8]):
        print(f"  {o}")
    print(f"Folder tanpa hub: {len(nohub)}" + ("".join(f"\n  {d}" for d in nohub) if nohub else ""))
    return 1 if broken or nohub else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    sys.exit(main(ap.parse_args().verbose))
