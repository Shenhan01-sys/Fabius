"""Sekali-jalan: tutup penanda "P10 terbuka" di TradingKnowledge setelah ongkos disatukan.

Penanda itu ditulis saat dua angka round-trip (20 bps asumsi warisan vs 59 bps terukur) masih hidup
berdampingan. `tools/costs.py` + `vault/scripts/wire_costs.py` menutupnya 28 Sep: satu sumber,
default yang terukur, override tercatat sebagai `cli-override`. Catatan yang masih bilang "terbuka"
bukan lagi hati-hati - ia salah menggambarkan keadaan, dan keadaan adalah satu-satunya hal yang
boleh dilaporkan halaman itu.

Pola diganti: frasa penanda -> rujukan ke hasil hitung ulang. Yang TIDAK disentuh: baris yang
membahas 20 bps sebagai angka (ia tetap tercatat di [[Fakta Terukur]] §D sebagai asumsi warisan),
dan setiap kalimat yang membandingkan 20 vs 59 - perbandingannya masih benar, hanya status P10-nya
yang berubah.

    python -X utf8 vault/scripts/close_p10_markers.py          # jalankan
    python -X utf8 vault/scripts/close_p10_markers.py --check   # laporkan saja
"""
import glob
import io
import os
import re
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TK = os.path.join(VAULT, "TradingKnowledge")
CHECK_ONLY = "--check" in sys.argv

SWAPS = [
    (r"\*\*P10 masih terbuka\*\* — §D", "**P10 ditutup 28 Sep** (`tools/costs.py`) — §D"),
    (r"\*\*P10 masih terbuka\*\*: 20 bps belum disatukan dengan 59 bps — §D",
     "**P10 ditutup 28 Sep**: satu sumber `tools/costs.py`, default 59 bps terukur — §D"),
    (r"\*\*P10 terbuka\*\*: 20 bps belum disatukan dengan 59 bps — §D",
     "**P10 ditutup 28 Sep**: satu sumber `tools/costs.py` — §D"),
    (r"P10 masih terbuka \(§D\)", "P10 ditutup 28 Sep (`tools/costs.py`, §D)"),
    (r"P10 masih terbuka", "P10 ditutup 28 Sep (`tools/costs.py`)"),
    (r"P10 terbuka — ", "P10 ditutup 28 Sep (`tools/costs.py`) - "),
    (r"P10 terbuka \(\[\[Fakta Terukur\]\] §D\)", "P10 ditutup 28 Sep (`tools/costs.py`, §D)"),
    (r"P10, §D\)", "P10 ditutup 28 Sep, §D)"),
    (r"§D, P10 terbuka\)", "§D, P10 ditutup 28 Sep)"),
    (r"\(§D, P10\)", "(§D; P10 ditutup 28 Sep)"),
    (r"P10 masih hidup dan menyentuh keluarga ini", "P10 sudah ditutup 28 Sep; sebelum itu ia menyentuh keluarga ini"),
    (r"\(lihat P10 di \[\[Fakta Terukur\]\] §D\)", "(P10 ditutup 28 Sep; sebelum itu `RT_COST_BPS = 20` - lihat [[Fakta Terukur]] §D)"),
    (r"lihat P10 di \[\[Fakta Terukur\]\] §D", "P10 ditutup 28 Sep, lihat [[Fakta Terukur]] §D"),
    (r"sampai P10 ditutup", "setelah P10 ditutup 28 Sep"),
    (r"P10 \(§D\) masih terbuka", "P10 ditutup 28 Sep (§D)"),
]


def main():
    files = sorted(glob.glob(os.path.join(TK, "**", "*.md"), recursive=True))
    total = changed = 0
    for p in files:
        rel = os.path.relpath(p, VAULT).replace(os.sep, "/")
        t = io.open(p, encoding="utf-8").read()
        orig = t
        for pat, rep in SWAPS:
            t, n = re.subn(pat, rep, t)
            total += n
        if t != orig:
            changed += 1
            print(f"{'akan ' if CHECK_ONLY else ''}ditutup penandanya  {rel}")
            if not CHECK_ONLY:
                io.open(p, "w", encoding="utf-8", newline="\n").write(t)
    sisa = 0
    for p in files:
        t = io.open(p, encoding="utf-8").read()
        sisa += len(re.findall(r"P10 (?:masih )?terbuka", t))
    print(f"\n{len(files)} berkas · {changed} diubah · {total} penanda diganti · "
          f"sisa 'terbuka': {sisa}")
    sys.exit(1 if (CHECK_ONLY and total) else 0)


if __name__ == "__main__":
    main()
