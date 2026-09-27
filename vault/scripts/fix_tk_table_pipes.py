"""Sekali-jalan: escape pipa di dalam `inline code` pada BARIS TABEL TradingKnowledge.

Sebabnya konkret: `|acf|` dan `|net|` adalah nama field yang kami pakai di mana-mana. Di paragraf
tidak masalah; di dalam baris tabel markdown setiap `|` adalah pemisah sel, jadi sel yang berisi
`|acf|` pecah dan tabelnya rusak — sementara `check_links.py` dan gerbang bentuk sama-sama tidak
melihat itu karena teksnya tetap terbaca sah.

Aturan: hanya baris yang dimulai dengan `|` yang disentuh, dan hanya pipa yang berada di dalam
span backtick yang belum di-escape. Idempoten.

    python -X utf8 vault/scripts/fix_tk_table_pipes.py          # perbaiki
    python -X utf8 vault/scripts/fix_tk_table_pipes.py --check   # laporkan saja
"""
import glob
import io
import os
import re
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TK = os.path.join(VAULT, "TradingKnowledge")
CHECK_ONLY = "--check" in sys.argv
SPAN = re.compile(r"`[^`]*`")
PIPE = re.compile(r"(?<!\\)\|")


def fix_line(line):
    """Escape pipa di dalam span backtick, tapi hanya pada baris tabel."""
    if not line.lstrip().startswith("|"):
        return line, 0
    out = SPAN.sub(lambda m: PIPE.sub(r"\\|", m.group(0)), line)
    return out, out.count("\\|") - line.count("\\|")


def main():
    files = sorted(glob.glob(os.path.join(TK, "**", "*.md"), recursive=True))
    total = changed_files = 0
    for p in files:
        text = io.open(p, encoding="utf-8").read()
        out, n = [], 0
        for line in text.split("\n"):
            nl, k = fix_line(line)
            n += k
            out.append(nl)
        if n:
            total += n
            changed_files += 1
            rel = os.path.relpath(p, VAULT).replace(os.sep, "/")
            print(f"{'akan ' if CHECK_ONLY else ''}di-escape {rel}: {n} pipa dalam tabel")
            if not CHECK_ONLY:
                io.open(p, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print(f"\n{len(files)} berkas · {changed_files} berkas diubah · {total} pipa di-escape.")
    sys.exit(1 if (CHECK_ONLY and total) else 0)


if __name__ == "__main__":
    main()
