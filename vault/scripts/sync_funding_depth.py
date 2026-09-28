"""Sekali-jalan: angka histori funding di lapisan TradingKnowledge disamakan dengan dataset yang ada.

Sebab: `patch_funding_history.py` menulis "OKX 33,0 hari" berdasar probe satu halaman (100 baris).
Perekam yang benar (`universe/record_funding_history.py`, 4 halaman) menarik **1.763 baris = 97,7
hari** per basis OKX. Angka lama bukan salah hitung, cuma **sepotong** - dan vault ini punya
riwayat panjang soal angka yang benar tapi tidak lengkap (lihat `05 - Corrections`).

Juga: baris `EV5` yang masih menyebut seri paper `n=2 / WR 50 % / -72,4 bps` - itu keadaan sebelum
P10; kini n=3, WR 0 %, rata-rata -236,0 bps. Diganti dengan yang tercetak `tools/winlog.py` hari ini.

    python -X utf8 vault/scripts/sync_funding_depth.py           # jalankan
    python -X utf8 vault/scripts/sync_funding_depth.py --check     # laporkan
"""
import glob
import io
import os
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TK = os.path.join(VAULT, "TradingKnowledge")
CHECK_ONLY = "--check" in sys.argv

SWAPS = [
    ("33,0 hari", "97,7 hari"),
    ("OKX 33,0", "OKX 97,7"),
    ("| histori funding per aset | `ADA-TAPI` | Bybit `…/funding/history` **66,3 hari** dan OKX",
     "| histori funding per aset | `ADA` (di repo sendiri) | `universe/funding-history.jsonl`: Bybit **66,3 hari** dan OKX"),
    ("ditarik tanpa kunci (Bybit `…/funding/history` **200 baris = 66,3 hari**, OKX **100 baris = 97,7 hari**,",
     "ditarik dan disimpan sendiri (`universe/record_funding_history.py`: Bybit **66,3 hari**, OKX **97,7 hari**,"),
    ("`PAPER n=2 · WR 50 % · net rata-rata -72,4 bps`",
     "`PAPER n=3 · WR 0 % · net rata-rata -236,0 bps` (sebelum P10: n=2, WR 50 %, -72,4)"),
    ("PAPER n=2 · WR 50 % · net rata-rata -72,4 bps",
     "PAPER n=3 · WR 0 % · net rata-rata -236,0 bps (sebelum P10: n=2 · WR 50 % · -72,4)"),
]


def main():
    files = sorted(glob.glob(os.path.join(TK, "**", "*.md"), recursive=True))
    total = 0
    touched = 0
    for p in files:
        t = io.open(p, encoding="utf-8").read()
        orig = t
        n = 0
        for old, new in SWAPS:
            c = t.count(old)
            if c:
                t = t.replace(old, new)
                n += c
        if n:
            total += n
            touched += 1
            rel = os.path.relpath(p, VAULT).replace(os.sep, "/")
            print(f"{'akan ' if CHECK_ONLY else ''}disamakan {rel} ({n})")
            if not CHECK_ONLY:
                io.open(p, "w", encoding="utf-8", newline="\n").write(t)
    sisa = sum(io.open(p, encoding="utf-8").read().count("33,0 hari") for p in files)
    print(f"\n{len(files)} berkas · {touched} disamakan · {total} penggantian · sisa '33,0 hari': {sisa}")


if __name__ == "__main__":
    main()
