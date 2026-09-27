"""Sekali-jalan: rujuk blok ongkos dengan benar di TradingKnowledge.

Temuan audit 28 Sep: beberapa catatan mengutip **59 bps** (biaya round-trip terukur) dengan label
`§A/§C` atau `§A/§D`, padahal angka itu tinggal di `§D. Ongkos` lembar fakta — `§A` itu deret harga,
`§C` itu sumber yang mati. Salah label terlihat sepele sampai seseorang mencari angkanya di blok
yang salah dan menyimpulkan angkanya tidak ada — persis cara "sumbernya ada" berubah menjadi
"sumbernya tidak bisa ditunjuk".

Aturan penggantian: HANYA baris yang menyebut `59 bps` DAN memakai label `§A/§C` atau `§A/§D`
diganti menjadi `§D`. Idempoten: dijalankan lagi tidak mengubah apa pun.

    python -X utf8 vault/scripts/fix_tk_cost_cite.py           # perbaiki
    python -X utf8 vault/scripts/fix_tk_cost_cite.py --check    # laporkan saja
"""
import glob
import io
import os
import re
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TK = os.path.join(VAULT, "TradingKnowledge")
CHECK_ONLY = "--check" in sys.argv
LINE = re.compile(r"§A/[CD]\b")


def main():
    files = sorted(glob.glob(os.path.join(TK, "**", "*.md"), recursive=True))
    n = 0
    for p in files:
        rel = os.path.relpath(p, TK).replace(os.sep, "/")
        if rel == "Fakta Terukur.md":
            continue                      # lembar fakta menyebut bloknya sendiri dengan benar
        text = io.open(p, encoding="utf-8").read()
        out, hits = [], 0
        for line in text.split("\n"):
            if "59 bps" in line and LINE.search(line):
                line = LINE.sub("§D", line)
                hits += 1
            out.append(line)
        if hits:
            n += hits
            print(f"{'akan ' if CHECK_ONLY else ''}diperbaiki {rel}: {hits} baris")
            if not CHECK_ONLY:
                io.open(p, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print(f"\n{len(files)} berkas diperiksa · {n} rujukan ongkos {'akan diperbaiki' if CHECK_ONLY else 'diperbaiki'}.")
    sys.exit(1 if (CHECK_ONLY and n) else 0)


if __name__ == "__main__":
    main()
