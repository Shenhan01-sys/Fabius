"""Samakan bentuk perintah Python di seluruh vault: `python -X utf8 -u …`.

Kenapa `-u` saja tidak cukup: `-u` mengatur buffer, bukan encoding. Beberapa string yang dicetak
perkakas kami (`①④⑥` di `direction.py`) ikut terserap `decisionHash` sehingga tidak bisa diganti
ke ASCII, sementara cp1252 tidak mengenalnya — di terminal Windows `print`-nya bisa pecah di
TENGAH laporan. Kenapa `-X utf8` saja tidak cukup: `-u` dibutuhkan saat output dialihkan ke berkas
supaya log siklus tidak muncul telat satu buffer penuh.

Skrip ini melaporkan kalau tidak ada yang berubah (berarti halaman sudah seragam), bukan diam.
"""
import glob
import io
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

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isdir(os.path.join(VAULT, "00-Overview")):
    sys.exit(f"VAULT bukan folder vault: {VAULT}")

PAT = re.compile(r"python (?!-X utf8)(?:-u )?([A-Za-z_][\w./-]*\.py)")
tot = 0
files = 0
for f in sorted(glob.glob(os.path.join(VAULT, "**", "*.md"), recursive=True)):
    t = io.open(f, encoding="utf-8").read()
    new, n = PAT.subn(lambda m: "python -X utf8 -u " + m.group(1), t)
    if n:
        io.open(f, "w", encoding="utf-8", newline="\n").write(new)
        print(f"  {os.path.relpath(f, VAULT).replace(os.sep, '/')}  ({n} perintah)")
        tot += n
        files += 1
print(f"\n{tot} perintah disamakan di {files} berkas.")
if not tot:
    print("Tidak ada yang berubah — cek pola reviewer-nya, jangan langsung simpulkan 'sudah seragam'.")
