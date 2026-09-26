"""Cari sebuah permintaan/istilah di seluruh vault dan laporkan HALAMAN mana yang menaunginya.

Bedanya dengan `check_links.py`: itu memeriksa graf antar-halaman, ini memeriksa **apakah sesuatu
ada di mana pun**. Dipakai untuk audit sesi: setiap permintaan pengguna yang tidak muncul di halaman
mana pun adalah kerja yang akan diulang (atau dilanggar) sesi berikutnya - dan itu tidak bisa dilihat
dari daftar berkas, hanya dari pencarian isi.

Aturan pelaporan: yang MISS dicetak dengan sumbernya (file yang memintanya), supaya "tidak ada di
vault" bisa dibedakan dari "tidak pernah diminta".

    python -X utf8 vault/scripts/ask_coverage.py vercel winstreak "bayar dari profit"
"""
import glob
import io
import os
import sys
# Windows: cmd.exe default cp1252 dan glyph yang kami cetak (`①④⑥` di arah, `⚠` di laporan)
# bukan bagian dari yang di-hash - jadi encoding stdout yang disetel, bukan stringnya.
# Tanpa ini, `print` bisa pecah DI TENGAH tabel dan separuh hasilnya terbaca seperti laporan penuh.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # stdout tanpa reconfigure (mis. tertangkap harness) = biarkan apa adanya

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAB = os.path.dirname(VAULT)
if not os.path.isdir(os.path.join(VAULT, "00-Overview")):
    sys.exit(f"VAULT bukan folder vault: {VAULT}")

NEEDLES = sys.argv[1:]
if not NEEDLES:
    sys.exit(" sebutkan minimal satu istilah yang dicari")

pages = {}
for f in glob.glob(os.path.join(VAULT, "**", "*.md"), recursive=True):
    pages[os.path.relpath(f, VAULT).replace(os.sep, "/")] = \
        io.open(f, encoding="utf-8", errors="replace").read().lower()

hit = miss = 0
for n in NEEDLES:
    ln = n.lower()
    found = [p for p, t in pages.items() if ln in t]
    if found:
        hit += 1
        print(f"ADA  {n:26} -> {len(found)} halaman | {', '.join(found[:3])}"
              + (" …" if len(found) > 3 else ""))
    else:
        miss += 1
        print(f"MISS {n:26} -> tidak ada di {len(pages)} halaman vault mana pun")
print(f"\n{hit} ditemukan, {miss} tidak. Halaman vault diperiksa: {len(pages)}.")
sys.exit(1 if miss else 0)
