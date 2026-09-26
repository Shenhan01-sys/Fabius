"""Ambil kembali indentasi badan dokumen yang kuhapus oleh regexku sendiri.

Kejadian 27 Sep: `tag_legacy_frontmatter.py` bermaksud memperbaiki satu baris YAML yang menjorok
(` artefak:`) dan memakai pola yang mencari "\n +kunci:" di **seluruh berkas**, bukan di blok
frontmatter saja. Akibatnya leading space pada daftar bertingkat di badan 5 halaman ikut ter-strip.
Format markdown list bertingkat itu bagian dari artinya (syarat ke-2 di bawah syarat ke-1 bukan
hiasan), jadi ini kerusakan nyata, bukan kosmetik.

Cara memulihkan: blob sebelum migrasi ada di git (`git show HEAD:vault/<nama lama>`), dan migrasi
hanya menulis ulang teks tautan tanpa mengubah jumlah baris. Jadi baris bisa disejajarkan by index;
indentasi asal dikembalikan **hanya** kalau isi baris (tanpa spasi) identik — baris yang isinya
memang berubah tidak disentuh, dan blok frontmatter dibiarkan dalam bentuk barunya yang valid.

    python -X utf8 vault/scripts/repair_indent.py --dry-run
    python -X utf8 vault/scripts/repair_indent.py
"""
import argparse
import os
import subprocess
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
REPO = os.path.dirname(ROOT)
if not os.path.isdir(os.path.join(ROOT, "00-Overview")):
    sys.exit(f"ROOT bukan folder vault: {ROOT}")

# (jalur baru, jalur lama di HEAD) - sama dengan MOVES di migrate_vault.py, yang ke-5 rusak
PAIRS = [
    ("01-Agent/01 - Asset Classes and Seats.md", "vault/08-Kelas-Aset-dan-Kursi.md"),
    ("02-Contracts/02 - Deployed on 97.md", "vault/07-Deploy-97.md"),
    ("06-Results/04 - Negative Results.md", "vault/09-Uji-Arah-Tidak-Ada-Edge.md"),
    ("06-Results/05 - Pre-registration Flow.md", "vault/10-Pra-Registrasi-Uji-Aliran.md"),
    ("06-Results/06 - Pre-registration Horizon.md", "vault/11-Pra-Registrasi-Uji-Horison-Whale.md"),
]

ap = argparse.ArgumentParser()
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()


def fm_end(lines):
    """Index baris pertama setelah blok frontmatter (baris `---` kedua)."""
    if not lines or lines[0].strip() != "---":
        return 0
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return i + 1
    return 0


total_fixed = 0
for new_rel, old_rel in PAIRS:
    p = os.path.join(ROOT, *new_rel.split("/"))
    orig = subprocess.run(["git", "-C", REPO, "show", f"HEAD:{old_rel}"],
                          capture_output=True, text=True, encoding="utf-8").stdout
    if not orig:
        print(f"  ! {new_rel}: blob HEAD tidak ada ({old_rel}) - lewati, jangan mengarang")
        continue
    o = orig.replace("\r\n", "\n").split("\n")
    c = open(p, encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    delta = len(c) - len(o)
    start = fm_end(c)
    # Frontmatter yang kutambah + blok asal bisa beda tinggi; sisanya harus 1:1 dengan HEAD.
    tail_c, tail_o = c[start:], o[fm_end(o):]
    if len(tail_c) != len(tail_o):
        print(f"  ! {new_rel}: badan tidak sejajar ({len(tail_c)} vs {len(tail_o)} baris, "
              f"seluruh berkas {len(c)} vs {len(o)}) - TIDAK kusentuh, periksa manual")
        continue
    fixed = 0
    out = c[:start]
    for co, oo in zip(tail_c, tail_o):
        if co.strip() == oo.strip() and co != oo:
            lead_new = len(co) - len(co.lstrip())
            lead_old = len(oo) - len(oo.lstrip())
            if lead_old > lead_new:
                out.append(" " * lead_old + co.lstrip())
                fixed += 1
            else:
                out.append(co)
        else:
            out.append(co)
    print(f"  {'akan restores' if a.dry_run else 'restore  '}: {new_rel}  "
          f"({fixed} baris dapat indentasinya kembali, delta frontmatter {delta})")
    if fixed and not a.dry_run:
        open(p, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    total_fixed += fixed

print(f"\n{total_fixed} baris dipulihkan indentasinya."
      + ("  (dry-run: tidak ada yang ditulis)" if a.dry_run else ""))
