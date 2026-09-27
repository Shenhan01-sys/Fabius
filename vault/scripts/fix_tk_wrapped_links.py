"""Sekali-jalan: sambungkan `[[wikilink]]` yang patah ke baris baru di TradingKnowledge.

Kenapa perlu: sebagian catatan ditulis dengan wrap ±100 kolom, dan tautan yang panjang ikut terbelah
(`[[EV5 - Reproduksibilitas dan` + baris baru + `Pra-Registrasi]]`). Obsidian tidak merender tautan
dengan newline di dalam kurung siku ganda, dan `check_links.py` resolve berdasarkan basename —
newline membuat target tidak pernah cocok, jadi tautannya dilaporkan rusak tanpa pernah terbaca
sebagai salah tempat.

Kerja skrip ini satu hal: menyatukan `[[ ... ]]` yang terbelah oleh SATU baris baru (pola yang
benar-benar terjadi). Ia idempoten: dijalankan ulang di vault yang sudah rapi = nol perubahan dan
berhenti dengan laporan. Baris yang membuka `[[` tanpa pernah menutup TIDAK disentuh — itu rusak
dengan sebab lain dan harus dibaca manusia.

    python -X utf8 vault/scripts/fix_tk_wrapped_links.py           # perbaiki
    python -X utf8 vault/scripts/fix_tk_wrapped_links.py --check   # laporkan saja (exit 1 kalau ada)
"""
import glob
import io
import os
import re
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TK = os.path.join(VAULT, "TradingKnowledge")
CHECK_ONLY = "--check" in sys.argv

SPLIT = re.compile(r"\[\[([^\]\n|]+)\n([^\]\n|]*)\]\]")
UNCLOSED = re.compile(r"\[\[[^\]\n]*$")
MAX_PASS = 4


def fix_text(text):
    """Sambung tautan yang terbelah satu baris baru, sampai tidak ada sisanya.

    `text = new` bukan hiasan: versi pertama skrip ini lupa menugaskan hasilnya, jadi `while True`
    tidak pernah selesai pada berkas yang mengandung satu pun tautan terbelah - ia menggantung
    tanpa mencetak apa pun dan terbaca seperti data yang besar, bukan bug. `MAX_PASS` dipasang
    supaya kegagalan seperti itu berhenti dengan suara, tidak diam-diam.
    """
    n = 0
    for _ in range(MAX_PASS):
        new, k = SPLIT.subn(lambda m: "[[%s %s]]" % (m.group(1).rstrip(), m.group(2).lstrip()), text)
        text = new
        n += k
        if k == 0:
            return text, n
    print("  ! batas %d lintasan tercapai - ada yang tidak selesai, periksa manual" % MAX_PASS)
    return text, n


def main():
    if not os.path.isdir(TK):
        sys.exit(f"tidak ada {TK}")
    files = sorted(glob.glob(os.path.join(TK, "**", "*.md"), recursive=True))
    total = changed = dangling = 0
    for f in files:
        text = io.open(f, encoding="utf-8").read()
        new, n = fix_text(text)
        rel = os.path.relpath(f, VAULT).replace(os.sep, "/")
        left = sum(1 for ln in new.split("\n") if UNCLOSED.search(ln))
        dangling += left
        if n:
            total += n
            changed += 1
            if CHECK_ONLY:
                print(f"akan disambung {rel}: {n} tautan")
            else:
                io.open(f, "w", encoding="utf-8", newline="\n").write(new)
                print(f"diperbaiki {rel}: {n} tautan disambung")
        if left:
            print(f"  ! {rel}: {left} baris membuka `[[` yang tidak pernah ditutup - tidak disentuh")
    print(f"\n{len(files)} berkas · {changed} berkas diubah · {total} tautan disambung · "
          f"{dangling} `[[` menggantung.")
    sys.exit(1 if (CHECK_ONLY and total) else 0)


if __name__ == "__main__":
    main()
