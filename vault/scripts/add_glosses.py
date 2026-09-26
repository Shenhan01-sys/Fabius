"""Pasang penjelasan (gloss) untuk baris hub yang masuk sebagai tautan polos.

Alat `sync_vault.py` sengaja append-only: ia menambah berkas baru ke peta tanpa komentar, karena
ia tidak boleh mengarang penjelasan tentang isi halaman yang tidak ditulusnya. Yang menulis
penjelasan itu manusia (atau aku di sesi ini) - dan tanpa langkah ini, halaman baru muncul di peta
tanpa keterangan, yang merupakan cara paling rapi untuk membuat orang tidak membukanya.

Setiap pasangan wajib ketemu tepat satu kali. Yang tidak ketemu dilaporkan dan skripnya keluar
non-zero, bukan dilewati diam-diam.

    python -X utf8 vault/scripts/add_glosses.py
"""
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
if not os.path.isdir(os.path.join(VAULT, "00-Overview")):
    sys.exit(f"VAULT bukan folder vault: {VAULT}")

GLOSS = [
    ("00-Overview/00 - Hub Overview.md", "- [[07 - Ecosystem Positioning]]",
     "- [[07 - Ecosystem Positioning]] — jawaban terukur atas \"ini jangan-jangan cuma project trading?\""),
    ("01-Agent/00 - Hub Agent.md", "- [[A4 - Trust Gating and Real-Money Rules]]",
     "- [[A4 - Trust Gating and Real-Money Rules]] — kapan agen boleh menyentuh uang, berapa, "
     "dan kenapa metriknya harapan bersih bukan win-streak"),
    ("03-Data/00 - Hub Data.md", "- [[D5 - Record Schemas]]",
     "- [[D5 - Record Schemas]] — field tiap rekaman + riwayat skema 1→4; tanpa ini hash tidak "
     "bisa dihitung ulang orang lain"),
]

bad = []
for rel, old, new in GLOSS:
    p = os.path.join(VAULT, rel.replace("/", os.sep))
    t = io.open(p, encoding="utf-8").read()
    # cari sebagai baris utuh (bukan substring) supaya gloss yang sudah ada tidak digandakan
    lines = t.split("\n")
    hits = [i for i, l in enumerate(lines) if l.strip() == old]
    if len(hits) != 1:
        bad.append(f"{rel}: {len(hits)} baris persis '{old}'")
        continue
    lines[hits[0]] = new
    io.open(p, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    print("ok  ", rel)

if bad:
    print("\n".join("!! " + b for b in bad))
    sys.exit(f"{len(bad)} gloss tidak dipasang — periksa barisnya di hub, jangan dipaksakan.")
print("\nsemua baris baru sudah punya penjelasan.")
