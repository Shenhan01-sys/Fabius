"""Pindahkan 12 penunjuk `⚠️ DIARSIPKAN` dari root vault ke `_archive/`, plus tabel lama->baru.

Kenapa tidak dihapus: orang yang menyimpan jalur lama (`vault/07-Deploy-97.md`, disebut di pesan
commit dan di komentar kode) harus tetap menemukan jalurnya. Kenapa tidak dibiarkan di root: root
adalah pintu masuk; 12 berkas redirect di depan pintu membuat vault terbaca seperti bekas
pindahan, bukan dokumentasi. `_archive/` sengaja di-skip `sync_vault.py` dan `check_links.py`.

    python scripts/archive_stubs.py            # jalan
    python scripts/archive_stubs.py --dry-run  # lihat saja
"""
import argparse
import io
import os
import re
import shutil
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
ARCH = os.path.join(VAULT, "_archive")
if not os.path.isdir(os.path.join(VAULT, "00-Overview")):
    sys.exit(f"VAULT bukan folder vault: {VAULT}")

MAP = [
    ("00-Mulai.md", "00-Overview/01 - Briefing.md"),
    ("01-Klaim-Dan-Batas.md", "06-Results/01 - Claims and Limits.md"),
    ("02-Ambang.md", "06-Results/02 - Thresholds.md"),
    ("03-Dataset.md", "03-Data/01 - Dataset.md"),
    ("04-Kontrak.md", "02-Contracts/01 - DecisionAnchor.md"),
    ("05-Belum-Terbukti.md", "06-Results/03 - Not Yet Proven.md"),
    ("06-Keputusan.md", "00-Overview/03 - Decisions.md"),
    ("07-Deploy-97.md", "02-Contracts/02 - Deployed on 97.md"),
    ("08-Kelas-Aset-dan-Kursi.md", "01-Agent/01 - Asset Classes and Seats.md"),
    ("09-Uji-Arah-Tidak-Ada-Edge.md", "06-Results/04 - Negative Results.md"),
    ("10-Pra-Registrasi-Uji-Aliran.md", "06-Results/05 - Pre-registration Flow.md"),
    ("11-Pra-Registrasi-Uji-Horison-Whale.md", "06-Results/06 - Pre-registration Horizon.md"),
]

ap = argparse.ArgumentParser()
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()

moved = 0
for old, new in MAP:
    src = os.path.join(VAULT, old)
    if not os.path.isfile(src):
        print(f"  tidak ada  {old}")
        continue
    text = io.open(src, encoding="utf-8").read()
    if "DIARSIPKAN" not in text:
        print(f"  BUKAN penunjuk, ditinggalkan: {old} (175 B?) — periksa manual")
        continue
    if os.path.isfile(os.path.join(VAULT, new.replace("/", os.sep))) is False:
        print(f"  ! tujuan tidak ada ({new}) — jangan pindahkan penunjuk yang menggantung")
        continue
    print(f"  arsip  {old}  ->  _archive/{old}")
    if not a.dry_run:
        os.makedirs(ARCH, exist_ok=True)
        shutil.move(src, os.path.join(ARCH, old))
    moved += 1

rows = "\n".join(f"| `{o}` | [[{n[:-3]}]] |" for o, n in MAP)
readme = f"""---
tags: [archive]
---

# _archive — jalur lama vault Fabius

Isi folder ini **sudah pindah**. Berkasnya ditinggalkan sebagai penunjuk supaya orang yang
menyimpan jalur lama (pesan commit, komentar kode, bookmark) tetap menemukan tempat barunya.
Jangan menulis di sini; jangan menaut dari halaman lain.

Dipindahkan 27 Sep 2026 oleh `scripts/migrate_vault.py` (konten utuh, tidak disalin dari ingatan)
dan digulung ke sini oleh `scripts/archive_stubs.py`. Keduanya adalah alat sekali-jalan:
dijalankan ulang di vault yang sudah rapi tidak menghasilkan apa pun selain peringatan.

| jalur lama | sekarang |
|---|---|
{rows}

Yang tidak ada di tabel ini tapi pernah disebut `vault/NN-...`: komentar di `contracts/` dan
`tools/` yang mengutip nomor halaman lama. Komentarnya sengaja tidak kusunting — komentar itu
menyertai angka yang diucapkannya saat ditulis; yang berubah adalah tempat angkanya tinggal.
"""
if not a.dry_run:
    os.makedirs(ARCH, exist_ok=True)
    io.open(os.path.join(ARCH, "README.md"), "w", encoding="utf-8", newline="\n").write(readme)
    print(f"tulis _archive/README.md ({len(MAP)} baris tabel)")
print(f"\n{moved} penunjuk diarsipkan." + (" (dry-run: tidak ada yang bergerak)" if a.dry_run else ""))
