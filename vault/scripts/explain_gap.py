"""Cetak baris tempat sebuah identifier muncul, penugasan didahulukan.

Dipakai setelah `fact_coverage.py`: daftar "belum disebut vault" harus diurutkan oleh
_signifikansi_, dan satu-satunya cara menilai tanpa menebak adalah melihat barisnya - konstanta
bernilai adalah klaim yang harus punya halaman; variabel lokal bukan.

Ditulis sebagai berkas, bukan `python -c` multi-baris, karena di cmd.exe bentuk inline itu diam
tanpa keluaran (sudah lima kali terjadi di proyek ini; lihat [[04-Tools/TL7 - measurement harness]]).

    python -X utf8 vault/scripts/explain_gap.py RT_COST_BPS BH_ALPHA snapshot_utc
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

FAB = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.isfile(os.path.join(FAB, "foundry.toml")):
    sys.exit(f"FAB bukan akar Fabius: {FAB}\n     harus berisi foundry.toml - berhenti, jangan menebak.")

NEEDLES = sys.argv[1:]
if not NEEDLES:
    sys.exit(" sebutkan minimal satu identifier")

FILES = (sorted(glob.glob(os.path.join(FAB, "tools", "*.py")))
         + sorted(glob.glob(os.path.join(FAB, "universe", "*.py")))
         + sorted(glob.glob(os.path.join(FAB, "contracts", "*.sol")))
         + sorted(glob.glob(os.path.join(FAB, "test", "*.sol")))
         + sorted(glob.glob(os.path.join(FAB, ".github", "workflows", "*.yml")))
         + [os.path.join(FAB, "docs", "agent-card.json"), os.path.join(FAB, "README.md")])

ASSIGN_HINTS = ("=", '"%s":', "'%s':", "getenv", "environ")
for n in NEEDLES:
    rows = []
    for p in FILES:
        if not os.path.isfile(p):
            continue
        rel = os.path.relpath(p, FAB).replace(os.sep, "/")
        for i, line in enumerate(io.open(p, encoding="utf-8", errors="replace"), 1):
            if n not in line:
                continue
            s = line.strip()
            score = 0
            if s.startswith(n):
                score += 3
            if "=" in s:
                score += 2
            if '"' + n + '"' in s or "'" + n + "'" in s:
                score += 2
            if "getenv" in s or "environ" in s:
                score += 2
            rows.append((score, rel, i, s[:120]))
    rows.sort(key=lambda r: (-r[0], r[1]))
    print(f"\n### {n}   ({len(rows)} kemunculan; yang paling mirip definisi di atas)")
    for score, rel, i, s in rows[:5]:
        print(f"   [{score}] {rel}:{i}  {s}")
    if not rows:
        print("    tidak muncul di berkas produk mana pun")
