"""Sekali-jalan: 16 baris "histori funding/OI TIDAK-ADA" dibetulkan oleh probe 28 Sep.

Sebab: `Fakta Terukur` §C (diukur 24 Sep) menyebut "histori funding per-aset yang bisa ditarik
mundur" sebagai sesuatu yang tidak kami punya, dan 16 catatan mengutipnya sebagai `TIDAK-ADA`.
Probe 28 Sep 02:06Z dari laptop yang sama (`_research/probe_cex_depth.py`) mematahkannya:
Bybit `funding/history` 200 baris = 66,3 hari (interval 8 jam), OKX 100 baris = 33,0 hari,
Binance `openInterestHist` 500 baris = 20,8 hari - semuanya TANPA kunci.

Yang TIDAK berubah dan harus tetap tertulis di setiap baris: interval 8 jam tidak bisa jadi fitur
per-bar (horizon kami 1 j dan 4 j), jendela OI cuma 30 hari (tidak cukup untuk walk-forward
400 hari), dan angka ini **diukur dari laptop, belum dari runner** - pasangan sumber×jaringan×waktu.

Fragmen diganti satu per satu dengan assert count==1; tidak ada penggantian sebagian.

    python -X utf8 vault/scripts/patch_funding_history.py           # jalankan
    python -X utf8 vault/scripts/patch_funding_history.py --check    # laporkan saja
"""
import glob
import io
import os
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TK = os.path.join(VAULT, "TradingKnowledge")
CHECK_ONLY = "--check" in sys.argv

FUND = ("`ADA-TAPI`", "Bybit `/v5/market/funding/history` **200 baris = 66,3 hari** dan OKX "
        "`funding-rate-history` **33,0 hari**, dua-duanya tanpa kunci, interval **8 jam** — "
        "[[Fakta Terukur]] §A.5 (diukur 28 Sep dari laptop ini, BELUM dari runner). 8 jam bukan "
        "fitur per-bar: tetap veto rezim, bukan sinyal")
OI = ("`ADA-TAPI`", "Binance `futures/data/openInterestHist` **500 baris per 1 jam = 20,8 hari** "
      "(jendela API 30 hari) — [[Fakta Terukur]] §A.5. Cukup untuk uji ΔOI pendek, tidak untuk "
      "walk-forward 400 hari; diukur dari laptop, belum dari runner")

# (fragmen yang harus ada persis sekali di SATU berkas di bawah TK, penggantian)
PAIRS = [
    ("| histori funding per aset | `TIDAK-ADA` | disebut eksplisit di [[Fakta Terukur]] §C:",
     "| histori funding per aset | %s | %s |" % FUND),
    ("| histori funding/OI per aset | `TIDAK-ADA` | tidak bisa ditarik mundur (§C) → fitur carry tidak bisa jadi label-uji |",
     "| histori funding/OI per aset | %s | %s |" % FUND),
    ("| histori funding per aset untuk menguji gerbang carry | `TIDAK-ADA` | hanya funding terkini yang bisa dibaca (§A/§C) → §F menyebut ini sebagai batas yang masih tersisa |",
     "| histori funding per aset untuk uji gerbang carry | %s | %s — §F masih menyebutnya batas, sekarang batasnya bergeser: ada data, tidak ada interval |" % FUND),
    ("| histori funding kedua kaki | `TIDAK-ADA` | §C; carry adalah bagian dari PnL pairs, bukan catatan kaki |",
     "| histori funding kedua kaki | %s | %s; carry tetap bagian dari PnL pairs, bukan catatan kaki |" % FUND),
    ("| histori funding/OI sebagai fitur | `TIDAK-ADA` | §C |",
     "| histori funding/OI sebagai fitur | %s | %s |" % FUND),
    ("| histori funding/OI per aset untuk rezim derivatif | `TIDAK-ADA` | yang ada hanya pembacaan saat ini; riwayat tidak bisa ditarik mundur — §C |",
     "| histori funding/OI per aset untuk rezim derivatif | %s | %s |" % FUND),
    ("| korelasi funding/OI lintas aset | `TIDAK-ADA` | funding & OI hanya pembacaan saat ini, tanpa histori per aset — §C |",
     "| korelasi funding/OI lintas aset | %s | funding ±66 hari per 8 jam, OI ±20,8 hari per 1 jam "
     "(§A.5) — cukup untuk korelasi antar-aset besar, tidak untuk lintas siklus meme |" % FUND[0]),
    ("| funding **historis** yang bisa ditarik mundur | `TIDAK-ADA` | dinyatakan absent di §C → tanpa ini tidak ada satu pun uji funding |",
     "| funding **historis** yang bisa ditarik mundur | %s | §A.5: Bybit 66,3 hari / OKX 33,0 hari per 8 jam — uji funding mungkin, tapi bukan per-bar |" % FUND[0]),
    ("| funding + OI | `ADA-TAPI` | snapshot hidup (608 kontrak Aster · 234 Hyperliquid); **histori funding per-aset tidak bisa ditarik mundur** → tidak ter-backtest — §A, §C |",
     "| funding + OI | `ADA-TAPI` | hidup (608 kontrak Aster · 234 Hyperliquid) + **histori bisa disedot mundur**: Bybit 66,3 hari per 8 jam, OKX 33,0, OI Binance 20,8 hari per 1 jam — §A.5; interval 8 jam tetap bukan fitur per-bar |"),
    ("| riwayat funding/OI sebagai proksi aktivitas bot | `TIDAK-ADA` | §C: histori funding per-aset yang bisa ditarik mundur tidak kami punya |",
     "| riwayat funding/OI sebagai proksi aktivitas bot | %s | §A.5 — tapi proksi "
     "\"bot aktif\" dari funding per 8 jam itu lemah: resolusinya lebih kasar daripada peristiwa yang mau dijelaskan |" % FUND[0]),
    ("| histori OI (syarat ΔOI) | `TIDAK-ADA` | tidak ada sumber yang bisa ditarik mundur; yang tersisa hanya OI yang **kami** simpan per siklus (`funding_and_oi()` di `tools/direction.py` menyimpan `oi` ke baris kandidatnya) — sparse, ≤5 kandidat/siklus |",
     "| histori OI (syarat ΔOI) | %s | Binance `futures/data/openInterestHist` 500 baris per 1 jam "
     "= 20,8 hari ke belakang (§A.5, belum diverifikasi dari runner); selain itu ada juga OI yang "
     "**kami** simpan per siklus (`funding_and_oi()` di `tools/direction.py` menyimpan `oi` ke baris "
     "kandidatnya) — sparse, ≤5 kandidat/siklus |" % OI[0]),
    ("| 4 | **funding + OI live** — Aster 608 kontrak / Hyperliquid 234 perp ([[Fakta Terukur]] §A); veto funding > 0,05 %/4 j **sudah wired** di `tools/direction.py` | `ADA-TAPI` (hidup saja, tanpa histori) |",
     "| 4 | **funding + OI** — live (Aster 608 kontrak / Hyperliquid 234 perp, §A) + **histori** Bybit 66,3 hari per 8 jam, OI Binance 20,8 hari per 1 jam (§A.5); veto funding > 0,05 %/4 j sudah wired di `tools/direction.py` | `ADA-TAPI` (historinya 8 jam, bukan per-bar) |"),
    ("| **K2 histori hilang** | jalurnya ada sekarang, masa lalunya tidak bisa diminta | ⑦ (jendela lihat 8–13 menit, paging diabaikan server), funding per jam |",
     "| **K2 histori hilang** | jalurnya ada sekarang, masa lalunya tidak bisa diminta, atau bisa tapi sempit | ⑦ (jendela lihat 8–13 menit, paging diabaikan server) = K2 murni; funding/OI turun jadi **K2-sebagian** sejak 28 Sep: 66,3 hari ke belakang, per 8 jam (§A.5) |"),
    ("| perekaman funding per jam | `TIDAK-ADA` tapi bisa dimulai sekarang | kelas K2 di [[GAP4 - Yang Tidak Bisa Diuji Karena Data]] — P13 |",
     "| histori funding (Bybit/OKX, tanpa kunci) | `ADA-TAPI` (8 jam, ±66 hari, belum dari runner) | §A.5 — dan ini mengganti bentuk P13: sedot mundur dulu, baru rekam |"),
]
PROSE = [
    ("Fabius: **belum diuji, dan belum bisa diuji** — tidak ada histori OI di repo",
     "Fabius: **belum diuji** — jendela histori OI baru 20,8 hari (§A.5), jauh di bawah `NEED_BARS`"),
    ("tidak punya order book, dan tidak punya histori funding",
     "tidak punya order book; histori funding ada tapi 8 jam (§A.5), jadi uji surut carry terbatas"),
    ("histori funding per aset yang bisa ditarik mundur `TIDAK-ADA` (§C)",
     "histori funding per aset kini `ADA-TAPI` (Bybit 66,3 hari per 8 jam, §A.5) - resolusinya 8 jam, "
     "sementara horizon uji kami 1 j dan 4 j"),
    ("Yang `TIDAK-ADA` sama sekali (§C): order book L2, tick/footprint, heatmap likuidasi, histori funding",
     "Yang tetap `TIDAK-ADA` (§C): order book L2, tick/footprint, heatmap likuidasi. Yang berubah 28 Sep: "
     "histori funding"),
]


def main():
    files = sorted(glob.glob(os.path.join(TK, "**", "*.md"), recursive=True))
    texts = {p: io.open(p, encoding="utf-8").read() for p in files}
    bad = 0
    for old, new in PAIRS + PROSE:
        hits = [p for p, t in texts.items() if old in t]
        if len(hits) != 1:
            print("FRAGMEN %dx: %s" % (len(hits), old[:70]))
            bad += 1
            continue
        p = hits[0]
        texts[p] = texts[p].replace(old, new)
        print(f"{'akan ' if CHECK_ONLY else ''}dibetalkan  {os.path.relpath(p, VAULT).replace(os.sep, '/')}  :: {old[:56]}")
    for p, t in texts.items():
        if not CHECK_ONLY and t != io.open(p, encoding="utf-8").read():
            io.open(p, "w", encoding="utf-8", newline="\n").write(t)
    print(f"\n{len(PAIRS) + len(PROSE)} aturan · {bad} bermasalah · "
          f"{'hanya laporan' if CHECK_ONLY else 'ditulis'}.")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
