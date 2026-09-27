"""Sekali-jalan: klaim yang masih menyebut 20 bps sebagai ongkos yang dipakai (dampak P10).

P10 ditutup 28 Sep: satu model ongkos di `tools/costs.py`, default **59 bps terukur**, override
tercatat `cli-override`. Beberapa halaman masih menulis "20 bps dipakai sejak awal" atau menarik
kesimpulan dari angka itu. Angka lama TIDAK dihapus (doktrin vault: run yang menang, yang kalah
tetap terbaca) - yang berubah hanya status kalimatnya: dari "inilah ongkos kami" menjadi "inilah
yang dipakai sebelum 28 Sep, dan inilah hasil hitung ulangnya".

Setiap aturan wajib menemukan fragmennya **persis satu kali**; kalau tidak, skrip berhenti dan
melaporkan. Tidak ada penggantian sebagian yang bisa tampak sukses.

    python -X utf8 vault/scripts/patch_p10_claims.py           # jalankan
    python -X utf8 vault/scripts/patch_p10_claims.py --check    # laporkan saja
"""
import io
import os
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK_ONLY = "--check" in sys.argv

RULES = [
    ("01-Agent/01 - Asset Classes and Seats.md",
     "2. **Ongkos 20 bps RT** dipakai sejak awal",
     "2. **Ongkos 20 bps RT** dipakai sampai 27 Sep (asumsi warisan); sejak **P10 28 Sep** jalur uji "
     "memakai **59 bps terukur** (`tools/costs.py`)"),
    ("06-Results/05 - Pre-registration Flow.md",
     "- **ongkos 20 bps round-trip** (5,5 taker + 4,5 spread/slip per sisi) — klaim lolos hanya kalau "
     "**net > 0**, dan gross harus > 40 bps seperti di `06-Results/02 - Thresholds.md`",
     "- **ongkos round-trip**: uji lama memakai 20 bps asumsi (5,5 taker + 4,5 spread/slip per sisi); "
     "sejak **P10 28 Sep** yang dipakai **59 bps terukur** (`tools/costs.py`), jadi ambang gross naik "
     "dari > 40 menjadi **> 118 bps** — lihat `06-Results/02 - Thresholds.md` dan "
     "`06-Results/04` §5b"),
    ("06-Results/05 - Pre-registration Flow.md",
     "satu pun bidang yang kami punya yang menyisakan edge di atas 20 bps pada horizon 4 jam.",
     "satu pun bidang yang kami punya yang menyisakan edge di atas 20 bps pada horizon 4 jam — dan "
     "dengan ongkos terukur 59 bps (P10, 28 Sep) ambangnya naik, tidak turun."),
    ("06-Results/03 - Not Yet Proven.md",
     "dua `Enter` yang sudah jatuh tempo menghasilkan **+1,5 / −146,3 bps net** (n=2,",
     "dua `Enter` yang sudah jatuh tempo menghasilkan **+1,5 / −146,3 bps net** (n=2; **hitung ulang "
     "28 Sep dengan ongkos terukur: −37,5 / −185,3**, plus satu keputusan 27 Sep −485,3 → **PAPER n=3, "
     "WR 0 %**),"),
    ("Quick-Reference.md",
     "| hasil uji aturan arah | rugi setelah ongkos **12/12**; dibalik tetap kalah | "
     "[[06-Results/04 - Negative Results]] |",
     "| hasil uji aturan arah | rugi setelah ongkos **12/12**; dibalik tetap kalah. Hitung ulang 28 "
     "Sep (P10, 59 bps): tetap 12/12, kini −39,8…−66,9 bps | [[06-Results/04 - Negative Results]] §1/§5b |"),
    ("Quick-Reference.md",
     "| biaya round-trip venue demo | **59 bps** | `forge test --match-test test_round_trip_...` |",
     "| biaya round-trip venue demo | **59 bps** — default SEMUA jalur uji sejak **P10 28 Sep** "
     "(`tools/costs.py`) | `forge test --match-test test_round_trip_...` |"),
    ("00-Overview/05 - Corrections.md",
     "| eksekusi nyata | posisi nyata dibuka lalu ditutup di chain 97",
     "| ongkos | jalur uji menutup dengan 20 bps **asumsi warisan**, padahal venue kami menghasilkan "
     "59 bps | **P10 ditutup 28 Sep** (`tools/costs.py`: satu sumber, default terukur, override "
     "berlabel `cli-override`). Hitung ulang: aturan arah tetap **12/12 rugi** (kini −39,8…−66,9 "
     "bps/trade, gross tidak berubah); **satu-satunya \"MENANG +1,5 bps\" di seri paper menjadi "
     "−37,5 bps** dan PAPER kini n=3 WR 0 %. Angka lama tetap terbaca di `06-Results/04` §1–§4 dan "
     "`06-Results/07`, dengan hasil hitung ulang di sampingnya | "
     "`python -X utf8 tools/costs.py` · `tools/backtest.py --mom-only` · `tools/ledger.py` · "
     "`tools/winlog.py` → [[06-Results/04 - Negative Results]] §5b |\n"
     "| eksekusi nyata | posisi nyata dibuka lalu ditutup di chain 97"),
    ("08-Backlog/01 - Backlog.md",
     "| P10 | **Satukan model ongkos**",
     "| P10 | **Satukan model ongkos** ✅ 28 Sep"),
    ("08-Backlog/01 - Backlog.md",
     "⬜ **naik ke urutan 1** sejak 28 Sep, alasannya di",
     "✅ **selesai 28 Sep** — `tools/costs.py` + `vault/scripts/wire_costs.py` (6 jalur uji) + "
     "recompute di `06-Results/04` §5b; alasannya di"),
    ("TradingKnowledge/07-Peta-Fabius/GAP5 - Urutan Kerja dan Bayarnya.md",
     "| 1 | **P10** — satu model ongkos |",
     "| 1 | **P10** — satu model ongkos ✅ 28 Sep |"),
    ("TradingKnowledge/04-Setup/ST6 - Aliran On-Chain Fabius.md",
     "**P10 tertutup 28 Sep (`tools/costs.py`) —",
     "**P10 ditutup 28 Sep (`tools/costs.py`) —"),
]


def find(rel):
    for cand in (os.path.join(VAULT, rel.replace("/", os.sep)),
                 os.path.join(VAULT, "TradingKnowledge", rel.replace("/", os.sep))):
        if os.path.isfile(cand):
            return cand
    return None


def main():
    total = bad = 0
    for rel, old, new in RULES:
        p = find(rel)
        if p is None:
            print(f"TIDAK ADA BERKAS: {rel}")
            bad += 1
            continue
        t = io.open(p, encoding="utf-8").read()
        n = t.count(old)
        if n != 1:
            print(f"FRAGMEN {n}x (harus 1x): {rel} :: {old[:58]}")
            bad += 1
            continue
        total += 1
        short = os.path.relpath(p, VAULT).replace(os.sep, "/")
        if CHECK_ONLY:
            print(f"akan ditambal   {short}")
            continue
        io.open(p, "w", encoding="utf-8", newline="\n").write(t.replace(old, new))
        print(f"ditambal        {short}")
    print(f"\n{len(RULES)} aturan · {total} diterapkan · {bad} bermasalah.")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
