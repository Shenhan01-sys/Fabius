---
tags: [tk, tk-sinyal, "U1"]
---

# U1 - Open Interest

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"3. CONFIRMATION LAYER (Lapisan Konfirmasi)"
(Futures-Specific: "Open Interest (OI)") — klaim komunitas

**Ringkas:** Open interest = **jumlah kontrak yang sedang terbuka**, bukan jumlah orang yang
long. Setiap kontrak punya dua pihak, jadi total long = total short = OI, dan OI hanya berubah
kalau **kedua** pihak membuka atau menutup bersamaan. Nilai sebuah OI bukan pada besarannya tapi
pada **perubahannya bersama harga** — dan justru perubahan itu yang tidak bisa kami hitung, karena
repo ini tidak punya histori OI. Yang kami punya: satu angka per tanggal baca, di dua venue.

## Definisi yang bisa dihitung

```
OI          = sum(kontrak terbuka)                    # bukan "posisi long"
ΔOI(t)      = OI(t) - OI(t-1)                         # butuh dua pembacaan pada jam yang sama
OI_nilai    = OI × harga_mark                          # satuan: belum kami validasi (lihat tabel)
# bacaan 2x2 yang beredar (KLAIM komunitas, bukan hukum):
#  harga naik + OI naik = tren baru (long baru masuk)
#  harga naik + OI turun = penutupan short (short squeeze) - naik tanpa bensin baru
#  harga turun + OI naik = tren turun baru
#  harga turun + OI turun = long menyerah
# "siapa yang masuk" TIDAK terbaca dari OI sendirian; ia terbaca dari tanda Δposisi per pihak,
# dan itu data yang tidak ada di jalur mana pun di repo ini.
```

## Cara pakai yang diklaim

OI naik dianggap "uang baru masuk", OI turun dianggap "posisi mulai menutup"; dikombinasi dengan
funding untuk mendeteksi kerumunan searah dan potensi squeeze ([[U2 - Funding Rate dan Basis]],
[[U3 - Level Likuidasi dan Cascade]]). Dipakai luas di futures crypto. Klaim prediktifnya tidak
punya sumber di repo ini.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| OI **spot** saat ini, aset ber-perp | `ADA-TAPI` | Aster `openInterest` untuk **608 kontrak** (§A); pembacaan 28 Sep: BNB OI 7.832 dengan mark 778,45 · Hyperliquid `metaAndAssetCtxs` 234 perp, BNB OI 65.047 |
| histori OI (syarat ΔOI) | `TIDAK-ADA` | tidak ada sumber yang bisa ditarik mundur; yang tersisa hanya OI yang **kami** simpan per siklus (`funding_and_oi()` di `tools/direction.py` menyimpan `oi` ke baris kandidatnya) — sparse, ≤5 kandidat/siklus |
| ΔOI sebagai fitur uji | `TIDAK-ADA` | `tools/backtest.py` mengulang aturan **harga** saja; OI tidak masuk |
| OI untuk memecoin spot-only / pool baru | `TIDAK-ADA` | tidak ada kontrak perp = tidak ada OI; dan deretnya mentok 1.000 bar (§A) |
| OI per pihak (long vs short) | `TIDAK-ADA` | venue tidak memberi pembagian ini di jalur kita |

## Uji di Fabius

Yang bisa dibeli tanpa uang: **mulai merekam OI per (simbol, jam) sekarang**, karena benda ini tidak
bisa disusulkan — sifat yang sama persis dengan aliran ⑦ (§B: "yang lewat = hilang"). Setelah
deretnya cukup, uji standarnya sama dengan keluarga lain: event ΔOI vs return bersih 4 jam, kontrol
**arah acak pada token dan jam yang sama** (§B), `n >= 20` non-overlap, gross di atas **59 bps**
(§D), drop-best-fold, BH α 0,10 (§E). Perintah `tools/oi_study.py` **belum ditulis**, dan
`tools/direction.py` memang menyimpan `oi` di baris kandidatnya tapi bukan sebagai perekam
periodik — jadi yang terkumpul baru sisa-sisa siklus yang kebetulan dijalankan, bukan deret.
Sampai itu ada,
U1 berada di sisi [[GAP3 - Yang Punya Data Tapi Belum Diuji]] yang paling jujur: datanya baru ada
sejak hari ia mulai disimpan.

## Batas dan mode gagal

- **Satuan belum divalidasi.** 7.832 (Aster, mark 778,45) dan 65.047 (Hyperliquid) untuk aset yang
  sama tidak bisa dibandingkan sebelum kita tahu apakah keduanya kontrak, aset dasar, atau USD.
  Memakai rasionya sebagai "likuiditas relatif antar venue" = klaim yang melebihi yang diukur —
  *(belum diukur)*.
- **OI tidak menyebut pihak.** Bacaan 2×2 di atas membutuhkan asumsi siapa yang membuka; satu angka
  tidak cukup untuk dua ketidak-tahuan.
- **OI tinggi ≠ pasar dalam.** Pada aset yang kontraknya bisa dipakai lindung nilai pasar spot tipis,
  OI bisa besar karena arb, bukan spekulasi.
- **Hanya aset ber-perp.** Seluruh keluarga U buta terhadap kelas C2/D (memecoin spot-only dan
  peluncuran baru) — padahal di sanalah cerita naratifnya paling sering dijual
  ([[01-Agent/01 - Asset Classes and Seats]] §2). Ini survivorship struktural, bukan kurang data.
- **Duplikasi:** OI + funding mengukur hal yang sama dari dua sisi (berapa besar dan ke arah mana
  posisi terbuka). Memakainya sebagai dua "konfirmasi" menaikkan keyakinan tanpa menambah informasi.

## Tingkat bukti

`T1` untuk definisi dan mekanismenya · `T0` untuk tabel bacaan 2×2 sebagai aturan prediktif · untuk
Fabius: **belum diuji, dan belum bisa diuji** — tidak ada histori OI di repo; hasil negatif 12/12
(§F) adalah hasil aturan harga, bukan aturan OI.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami bisa membaca OI saat ini untuk 608 kontrak dan menyimpannya per siklus; ΔOI baru
  bisa diuji setelah deret kami sendiri cukup panjang."
- **Dilarang:** "OI naik = uang masuk" · "Fabius memakai open interest dalam keputusan" (tidak ada
  satu pun gerbang keputusan yang membaca `oi`) · membandingkan OI antar venue tanpa satuan yang
  divalidasi · menjual OI aset perp sebagai ukuran perhatian ke memecoin spot.

**Terkait:** [[U2 - Funding Rate dan Basis]] · [[U3 - Level Likuidasi dan Cascade]] ·
[[U4 - Long-Short Ratio dan Skew Posisi]] · [[V4 - Order Book dan Liquidity Heatmap]] ·
[[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]] ·
[[GAP3 - Yang Punya Data Tapi Belum Diuji]]
