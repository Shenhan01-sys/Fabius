"""Sekali-jalan: semua jalur uji mengambil ongkos dari `tools/costs.py` (P10).

Enam berkas mendefinisikan round-trip sendiri: lima menulis 20 bps (asumsi warisan), satu menulis
59 bps (terukur). Deret hasil yang sama dinilai dengan dua penggaris, dan artefak tidak bilang mana
yang dipakai. Skrip ini tidak "merapikan angka": ia menghapus sumber kedua, supaya satu-satunya
tempat angka itu bisa diubah adalah `tools/costs.py`.

Perubahan per berkas: sisipkan `import costs` setelah jangkar impor lokal, ganti baris
`RT_COST_BPS = <literal>` dengan rujukan ke modul, dan (untuk `screen_universe.py`) sambungkan
`GATE_GROSS_BPS` ke fungsi yang sama. Idempoten dan berhenti kalau satu pun assert tidak cocok.

    python -X utf8 vault/scripts/wire_costs.py            # jalankan
    python -X utf8 vault/scripts/wire_costs.py --check     # laporkan saja
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "tools")
CHECK_ONLY = "--check" in sys.argv

# (berkas, jangkar sesudahnya untuk sisip import, pola baris konstanta, pengganti)
SITES = [
    ("backtest.py", r"(import direction as D[^\n]*\n)",
     r"^RT_COST_BPS = 20\.0[^\n]*\n",
     "RT_COST_BPS = costs.MEASURED_RT_BPS   # P10: satu pintu (terukur) - lihat tools/costs.py\n"),
    ("ledger.py", r"(import direction as D[^\n]*\n)",
     r"^RT_COST_BPS = 20\.0[^\n]*\n",
     "RT_COST_BPS = costs.MEASURED_RT_BPS   # P10: satu pintu (terukur) - lihat tools/costs.py\n"),
    ("smartmoney_score.py", r"(import bars[^\n]*\n)",
     r"^RT_COST_BPS = 20\.0[^\n]*\n",
     "RT_COST_BPS = costs.MEASURED_RT_BPS   # P10: satu pintu (terukur) - lihat tools/costs.py\n"),
    ("flow_test.py", r"(import bars[^\n]*\n)",
     r"^RT_COST_BPS = 20\.0[^\n]*\n",
     "RT_COST_BPS = costs.MEASURED_RT_BPS   # P10: satu pintu (terukur) - lihat tools/costs.py\n"),
    ("maker_ledger.py", r"(OUT_DIR = os\.path\.join\(ROOT, \"decisions\"\)[^\n]*\n)",
     r"^RT_COST_BPS = 59\.0[^\n]*(\n\s*#[^\n]*)?",
     "RT_COST_BPS = costs.MEASURED_RT_BPS   # P10: satu pintu (terukur) - lihat tools/costs.py\n"),
    ("screen_universe.py", r"(from collections import defaultdict[^\n]*\n)",
     r"^RT_COST_BPS = 2 \* COST_SIDE \* 1e4[^\n]*\n",
     "RT_COST_BPS = costs.MEASURED_RT_BPS   # P10: bukan lagi 20 bps warisan - tools/costs.py\n"),
]
GATE = (r"^GATE_GROSS_BPS = RT_COST_BPS \+ GATE_NET_BPS[^\n]*\n",
        "GATE_GROSS_BPS = costs.gate_gross_bps(RT_COST_BPS)   # 2x ongkos yang dipakai -> 118 bps\n")
IMPORT = "import costs  # noqa: E402  (P10: satu model ongkos untuk semua jalur uji)\n"
# maker_ledger.py dan screen_universe.py tidak pernah menyentuh sys.path (mereka tidak mengimpor
# modul tetangga): tanpa baris ini, `import costs` melempar ModuleNotFoundError saat dijalankan
# dari direktori lain. Diperiksa: keduanya sudah punya HERE dan sudah `import sys`.
IMPORT_WITH_PATH = ("sys.path.insert(0, HERE)  # noqa: E402  (modul tetangga tinggal di tools/ ini)\n"
                    + IMPORT)
NEEDS_PATH = {"maker_ledger.py", "screen_universe.py"}


def main():
    done = skipped = bad = 0
    for fname, anchor, const, repl in SITES:
        p = os.path.join(TOOLS, fname)
        if not os.path.isfile(p):
            print(f"TIDAK ADA: {fname}")
            bad += 1
            continue
        t = io.open(p, encoding="utf-8").read()
        before = t
        if "import costs" not in t:
            m = re.search(anchor, t, re.M)
            if not m:
                print(f"JANGKAR IMPOR TIDAK COCOK: {fname}")
                bad += 1
                continue
            t = t[:m.end()] + "\n" + (IMPORT_WITH_PATH if fname in NEEDS_PATH else IMPORT) + t[m.end():]
        t2, n = re.subn(const, repl, t, flags=re.M)
        if n != 1 and "costs.MEASURED_RT_BPS" not in t:
            print(f"KONSTANTA TIDAK COCOK ({n}x): {fname}")
            bad += 1
            continue
        if fname == "screen_universe.py":
            t2, g = re.subn(GATE[0], GATE[1], t2, flags=re.M)
            if g == 0 and "costs.gate_gross_bps" not in t2:
                print("GATE_GROSS_BPS TIDAK COCOK: screen_universe.py")
                bad += 1
                continue
        if t2 == before:
            print(f"sudah tersambung  {fname}")
            skipped += 1
            continue
        done += 1
        if CHECK_ONLY:
            print(f"akan disambung  {fname}")
        else:
            io.open(p, "w", encoding="utf-8", newline="\n").write(t2)
            print(f"disambung       {fname}")
    print(f"\n{len(SITES)} situs · {done} diubah · {skipped} sudah rapi · {bad} GAGAL.")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
