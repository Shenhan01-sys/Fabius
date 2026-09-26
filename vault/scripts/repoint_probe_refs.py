"""Samakan rujukan probe verdict setelah kepindahannya ke `tools/` (di dalam repo).

Kenapa dipindah: nama `_research/` dipakai dua hal yang berbeda di workspace ini — folder riset di
luar repo produk DAN (sejak tadi) folder di dalam Fabius. Rujukan yang ambigu begitu membuat orang
yang meng-clone Fabius mencari berkas yang tidak ada. Setelah pindah ke `tools/`, semua
`_research/...` di vault berarti satu hal saja: alat workspace, di luar clone.

Setiap pasangan wajib ketemu tepat satu kali; yang tidak ketemu dilaporkan, bukan dilewati.
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
PAIRS = [
    ("01-Agent/A2 - Decision Spine.md",
     "`_research/vault_verdict_counts.py`, 27 Sep", "`tools/verdict_counts.py`, 27 Sep"),
    ("07-Testing/T2 - Anchor Verify.md",
     "  `python _research/vault_verdict_counts.py`. Dijadikan item terbuka",
     "  `python -X utf8 tools/verdict_counts.py`. Dijadikan item terbuka"),
    ("08-Backlog/01 - Backlog.md",
     "`python _research/vault_verdict_counts.py` vs `anchor.py --verify`",
     "`python -X utf8 tools/verdict_counts.py` vs `anchor.py --verify`"),
    ("Quick-Reference.md",
     "Yang **tidak** masuk blok itu dengan sengaja: `panel_stats.py`, `check_garbled.py`,\n"
     "`vault_verdict_counts.py` — apa pun di `_research/`. Itu alat workspace, bukan bagian clone;",
     "Yang **tidak** masuk blok itu dengan sengaja: `panel_stats.py`, `check_garbled.py` — apa pun\n"
     "di `_research/` root workspace. Itu alat di luar clone, jadi ia ditandai *(workspace)* di tiap\n"
     "halaman yang mengutip angkanya dan tidak pernah dipakai sebagai bukti produk."
     " `tools/verdict_counts.py` pindah ke dalam repo 27 Sep justru karena namanya sebelumnya\n"
     "`_research/vault_verdict_counts.py`, dan `_research` punya dua arti di workspace ini."),
]

fails = []
for rel, old, new in PAIRS:
    p = os.path.join(VAULT, rel.replace("/", os.sep))
    t = io.open(p, encoding="utf-8").read()
    if t.count(old) != 1:
        fails.append(f"{rel}: {t.count(old)}x untuk {old[:44]!r}")
        continue
    io.open(p, "w", encoding="utf-8", newline="\n").write(t.replace(old, new))
    print("ok  ", rel)

if fails:
    print("\n".join("!! " + f for f in fails))
    sys.exit(1)
print("\nrujukan seragam: `_research/` = workspace, `tools/` = clone.")
