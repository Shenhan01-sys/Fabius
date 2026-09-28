"""Sekali-jalan (P16): veto funding diberi nama yang benar, bukan dihapus.

Diukur 28 Sep (`tools/carry_study.py`, bahan `universe/funding-history.jsonl`):

- ambang `FUNDING_EXTREME = 0,05 %/4 jam` dilewati **0 dari 2.963** settlement pada enam basis
  besar, 66-97 hari. maksimum yang terlihat cuma **0,0256 %/8 jam** (= ~0,0128 %/4 jam),
  jadi ambangnya ~4x di atas apa pun yang pernah terjadi;
- menurunkan ambang bukan jalan keluar: uji arah 24 jam atas funding ekstrem menghasilkan
  **0 lolos dari 12 uji** (median + bootstrap + BH). Memilih angka supaya gerbangnya "pernah
  menyala" = membuat sinyal dari noise, hal yang persis dilarang `QT4`/`EV2`;
- dan kandidat kita yang sebenarnya (memecoin BSC) **tidak punya funding sama sekali**, jadi
  gerbang ini tidak akan pernah menimbang mereka - status keamanannya nol, dulu dan sekarang.

Yang tersisa adalah satu-satunya peran yang bisa dipertahankan jujur: **pemutus rezim** - kalau
funding pernah melewati 4x maksimum yang kami lihat, kita tidak lagi berada di dunia tempat
parameter ini dipilih, dan menolak posisi baru saat itu benar tanpa perlu prediktif. Sama
pola pikirnya dengan `killSwitch`. Maka yang diganti di seluruh dokumen adalah NAMANYA, bukan
ambangnya, dan ambangnya tidak dihapus diam-diam (aturan [[Concepts/One-Way Gate]]).

Assert per aturan: persis satu kecocokan di satu berkas.

    python -X utf8 vault/scripts/relabel_funding_gate.py          # jalankan
    python -X utf8 vault/scripts/relabel_funding_gate.py --check    # laporkan
"""
import glob
import io
import os
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(VAULT)
CHECK_ONLY = "--check" in sys.argv

# (carian, penggantian, daftar folder yang boleh disentuh)
RULES = [
    ("wired di `tools/direction.py`: funding > 0,05 %/4 j → tolak posisi |",
     "pemutus rezim, BUKAN gerbang keamanan: `|funding| > 0,05 %/4 j` menolak posisi baru. "
     "Terukur 0/2.963 kejadian dalam 97 hari (F-D26) |",
     ["TradingKnowledge"]),
    ("| funding + OI sebagai fitur hidup | `ADA-TAPI` | terpasang di `tools/direction.py` (funding > 0,05 %/4 j menolak posisi);",
     "| funding + OI sebagai fitur hidup | `ADA-TAPI` | terpasang di `tools/direction.py` "
     "sebagai **pemutus rezim** (funding > 0,05 %/4 j menolak posisi; 0 kejadian terukur, F-D26);",
     ["TradingKnowledge"]),
    ("| funding sebagai penolak posisi | `ADA` | funding > 0,05 %/4 j tolak posisi (biaya > edge yang kami klaim) — §A |",
     "| funding sebagai penolak posisi | `ADA` | **pemutus rezim**, bukan prediktor: "
     "> 0,05 %/4 j menolak posisi baru; 0 dari 2.963 settlement melewatinya (§A.5, F-D26) |",
     ["TradingKnowledge"]),
    ("| `premiumIndex` 608 kontrak; wired di `tools/direction.py`: funding > 0,05 %/4 j → **tolak posisi** (§A) |",
     "| `premiumIndex` 608 kontrak; wired di `tools/direction.py` sebagai **pemutus rezim**: "
     "funding > 0,05 %/4 j → tolak posisi baru (0 kejadian terukur, F-D26) (§A) |",
     ["TradingKnowledge"]),
    ("| gerbang keputusan yang memakainya | `ADA` | `tools/direction.py`: `\\|funding\\|` > 0,05 %/4 jam → tolak posisi,"
     " karena biayanya lebih besar dari edge yang kami klaim (§A) |",
     "| gerbang keputusan yang memakainya | `ADA` | `tools/direction.py`: `\\|funding\\|` > 0,05 %/4 jam → tolak posisi "
     "baru - **perannya pemutus rezim, bukan prediktor dan bukan gerbang keamanan**: 0 kejadian dari 2.963 settlement, "
     "dan 0 dari 12 uji arah lolos BH (§A.5, F-D26) |",
     ["TradingKnowledge"]),
    ("| funding/carry | gerbang: `> 0,05 %/4 j` menolak posisi | wired di `tools/direction.py` — §A |",
     "| funding/carry | **pemutus rezim**: `> 0,05 %/4 j` menolak posisi baru (0 kejadian terukur, F-D26) "
     "| wired di `tools/direction.py` — §A |",
     ["TradingKnowledge"]),
    ("| biaya | posisi long di aset yang premium membayar terus | gerbang: `\\|funding\\| > 0,05 %/4 jam` → **tolak posisi** (`tools/direction.py`, §A) |",
     "| biaya | posisi long di aset yang premium membayar terus | pemutus rezim: `\\|funding\\| > 0,05 %/4 jam` → "
     "**tolak posisi baru** (`tools/direction.py`, §A; 0 kejadian terukur, F-D26) |",
     ["TradingKnowledge"]),
    ("- **Boleh:** \"Fabius menolak kandidat yang funding-nya di atas 0,05 %/4 jam karena biaya carry",
     "- **Boleh:** \"Fabius menolak posisi BARU kalau funding melewati 0,05 %/4 jam - itu pemutus "
     "rezim, bukan klaim prediktif: 0 kejadian dari 2.963 settlement dan 0 dari 12 uji arah lolos BH \"\n  \"(F-D26). Versi lama kalimat ini - bahwa penolakan itu karena biaya carry",
     ["TradingKnowledge"]),
]


def files_for(roots):
    out = []
    for r in roots:
        base = os.path.join(VAULT, r) if not os.path.isabs(r) else r
        out += sorted(glob.glob(os.path.join(base, "**", "*.md"), recursive=True))
    return out


def main():
    done = bad = 0
    for old, new, roots in RULES:
        pool = files_for(roots)
        hits = [p for p in pool if old in io.open(p, encoding="utf-8").read()]
        if len(hits) != 1:
            print("FRAGMEN %dx: %s" % (len(hits), old[:70]))
            bad += 1
            continue
        p = hits[0]
        rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
        # BACA DULU, baru buka untuk tulis. Versi pertama melakukan
        # `io.open(p,"w").write(io.open(p).read().replace(...))` - "w" mengosongkan berkas SEBELUM
        # isinya dibaca, dan 7 berkas jadi 0 byte (diselamatkan `git checkout --`). Sekarang dibaca
        # dulu, dan dua assert menjaga: hasil yang menyusut atau berkas kosong = gagal, bukan diam.
        before = io.open(p, encoding="utf-8").read()
        after = before.replace(old, new)
        assert len(after) >= len(before), "%s menyusut: %d -> %d" % (rel, len(before), len(after))
        done += 1
        if CHECK_ONLY:
            print("akan diberi nama baru  %s" % rel)
            continue
        with io.open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(after)
        assert os.path.getsize(p) > 0, "berkas kosong setelah ditulis: " + rel
        print("diberi nama baru       %s" % rel)
    print("\n%d aturan · %d diterapkan · %d bermasalah." % (len(RULES), done, bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
