"""Sekali-jalan: catat seri paper yang berubah oleh P10 di catatan yang masih menyebut n=2.

`tools/winlog.py` hari ini mencetak PAPER n=3 · WR 0 % · rata-rata -236,0 bps (sebelumnya n=2,
WR 50 %, -72,4). Yang berubah bukan peruntungannya: keputusan 27 Sep ikut jatuh tempo, dan ongkos
yang dipakai kini 59 bps terukur, bukan 20 bps warisan (P10). Catatan yang masih menulis "n=2" atau
"WR 50 %" tanpa tanggal kini terbaca salah, bukan konservatif.

Bentuk perbaikannya seragam: angka baru + keterangan "(sebelum P10: ...)" supaya jejak lamanya tetap
kelihatan - aturan [[Conventions]]: koreksi berjalan append-only, run yang menang, yang kalah tetap
terbaca.

    python -X utf8 vault/scripts/sync_paper_series.py           # jalankan
    python -X utf8 vault/scripts/sync_paper_series.py --check    # laporkan
"""
import glob
import io
import os
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TK = os.path.join(VAULT, "TradingKnowledge")
CHECK_ONLY = "--check" in sys.argv

SWAPS = [
    ("`tools/winlog.py`: PAPER n=2 WR 50 % net rata2 −72,4 bps · CHAIN n=3 WR 0 % −59,0 bps",
     "`tools/winlog.py`: PAPER n=3 WR 0 % net rata2 −236,0 bps · CHAIN n=3 WR 0 % −59,0 bps "
     "(sebelum P10 seri paper n=2 WR 50 % −72,4)"),
    ("seri sekarang: PAPER n=2, CHAIN n=3 (G)",
     "seri sekarang: PAPER n=3 WR 0 % (−236,0 rata-rata), CHAIN n=3 (G)"),
    ("klaim pada n=2. Yang terukur di kami: dua `Enter` jatuh tempo = +1,5 dan −146,3 bps (§F) — dua",
     "klaim pada n=3. Yang terukur di kami: tiga `Enter` jatuh tempo = +1,5 / −146,3 / −485,3 bps "
     "pada ongkos 20 bps, menjadi −37,5 / −185,3 / −485,3 pada 59 bps (§F) — tidak satu pun"),
    ("butuh keputusan jatuh tempo dalam jumlah; yang terukur baru n=2 (§F)",
     "butuh keputusan jatuh tempo dalam jumlah; yang terukur baru n=3, semuanya rugi (§F)"),
    ("2. **Dua `Enter` yang jatuh tempo: +1,5 bps dan −146,3 bps net** (§F, n=2). WR-nya 50 % — angka",
     "2. **Tiga `Enter` yang jatuh tempo: +1,5 / −146,3 / −485,3 bps** pada ongkos 20 bps; pada ongkos "
     "terukur 59 bps menjadi **−37,5 / −185,3 / −485,3** (§F, §5b). WR-nya 0 % — angka"),
    ("yang terdengar \"setengah bagus\" — sementara rata-ratanya **−72,4 bps** (aritmetika dari dua angka",
     "yang tidak akan dipakai siapa pun sebagai bukti — rata-ratanya **−236,0 bps** (sebelum P10: −72,4; aritmetika dari angka"),
    ("**Dilarang:** \"win rate kami 50 %\" (n=2)",
     "**Dilarang:** \"win rate kami 50 %\" (n=2, dan sudah jadi 0 % di n=3)"),
]


def main():
    files = sorted(glob.glob(os.path.join(TK, "**", "*.md"), recursive=True))
    done = miss = 0
    for old, new in SWAPS:
        hits = [(p, io.open(p, encoding="utf-8").read()) for p in files]
        found = [(p, t) for p, t in hits if old in t]
        if len(found) != 1:
            print("FRAGMEN %dx: %s" % (len(found), old[:64]))
            miss += 1
            continue
        p, t = found[0]
        rel = os.path.relpath(p, VAULT).replace(os.sep, "/")
        done += 1
        if CHECK_ONLY:
            print("akan disamakan %s" % rel)
            continue
        io.open(p, "w", encoding="utf-8", newline="\n").write(t.replace(old, new))
        print("disamakan      %s" % rel)
    print(f"\n{len(SWAPS)} aturan · {done} diterapkan · {miss} bermasalah.")
    sys.exit(1 if miss else 0)


if __name__ == "__main__":
    main()
