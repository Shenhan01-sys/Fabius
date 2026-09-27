---
tags: [tk, tk-setup, "ST1"]
---

# ST1 - All-Rounder

**Keluarga:** [[00 - Hub Setup]]
**Anggota:** [[FD9 - Horizon Waktu dan Multi-Timeframe]] · [[S3 - Market Structure BOS dan ChoCH]] ·
[[S4 - Order Block dan Breaker]] · [[S5 - Fair Value Gap]] · [[S7 - Fibonacci Retracement dan Extension]] ·
[[V2 - Volume Profile dan POC]] · [[FD6 - Ukuran Posisi]] · [[FD7 - Invalidation Stop dan Time-Stop]]
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"Kombinasi A – All Rounder (Paling direkomendasikan)"
*(resep yang ditulis model di dalam transkrip; "paling direkomendasikan" adalah klaimnya, bukan temuan kami)*

**Ringkas:** resep komunitas paling lengkap: arah dari timeframe besar, zona dari SMC, level dari
Fibonacci, bobot dari profil volum, pembatas dari manajemen risiko. Dijanjikan sebagai "konfluensi
lima konfirmasi". Setelah dibedah: yang tersisa adalah **sumber yang sama dibaca lima kali**, plus
satu calon sumber (tick) yang tidak kita punya, plus satu aturan (ukuran posisi) yang memang tidak
punya pendapat tentang arah. Catatan ini ada supaya angka "lima" itu tidak ikut terjual.

## Resep

| tahap | aturan | catatan |
|---|---|---|
| bias | arah ayunan terakhir di TF lebih tinggi (HH/HL vs LH/LL) | [[FD9 - Horizon Waktu dan Multi-Timeframe]] · [[S3 - Market Structure BOS dan ChoCH]] |
| zona | OB atau FVG yang berada di sisi bias | [[S4 - Order Block dan Breaker]] · [[S5 - Fair Value Gap]] |
| pelaras | retracement ke 0,618 / 0,705 di dalam zona | [[S7 - Fibonacci Retracement dan Extension]] |
| bobot | zona berdekatan POC / HVN | [[V2 - Volume Profile dan POC]] |
| pemicu | penolakan pada sentuhan pertama | definisi "penolakan" wajib dikunci sebelum hasil dilihat ([[EV6 - Kalibrasi Ambang Terhadap Hasil]]) |
| invalidation | di luar zona + satu jarak ternormalisasi | [[FD7 - Invalidation Stop dan Time-Stop]] · [[I6 - ATR dan Jarak Ternormalisasi]] |
| target | ekstrema likuiditas berikutnya / ekstensi Fib | [[S6 - Likuiditas Stop Hunt dan Inducement]] |
| ukuran | dari plafon kontrak, bukan dari selera | [[FD6 - Ukuran Posisi]]; `dailyCap` 5 unit · `maxPositionQuote` 1 unit · `HARD_CEILING = 10` ([[Fakta Terukur]] §E) |
| keluar waktu | horizon tetap; mati tanpa kena stop/target = keluar | [[FD7 - Invalidation Stop dan Time-Stop]] |

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| OHLC 1 jam ≥ 2.400 bar (bias + zona + Fib + stop) | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari, **hanya** untuk aset ber-kontrak perp; C2/D mentok 1.000 bar ≈ 41,6 hari ([[Fakta Terukur]] §A) |
| profil volum sejati (distribusi harga intra-bar / tick) | `TIDAK-ADA` | tidak ada tick/footprint di repo ini ([[Fakta Terukur]] §C) |
| volum per bar (profil kasar) | `ADA-TAPI` | ikut `klines`; belum dipakai satu pun alat keputusan sebagai penyaring |
| satu definisi OB/FVG yang dipakai semua alat | `TIDAK-ADA` | `tools/direction.py` tidak punya konsep zona |
| umur snapshot saat keputusan dibuat | `ADA` | `universe_age_h` ikut masuk hash ([[01-Agent/A2 - Decision Spine]]) |

## Uji di Fabius

Setup diuji sebagai **satu kesatuan** — dan itu bukan formalitas, itu satu-satunya cara menjawab
judul catatan ini.

1. Satu detektor point-in-time untuk resep penuh (hanya bar `<= t`; [[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]).
2. Event = pemicu; hasil = return bersih pada horizon tetap **dan** pada kena stop. Ongkos **59 bps**
   ([[Fakta Terukur]] §D). Semua jalur uji sudah memakai angka itu sejak P10 (28 Sep); yang tersisa
   adalah menyebut basis di tiap artefak — `cost_basis` mencatat `measured-own-venue` atau
   `cli-override`.
3. **Ablasi wajib:** jalankan resep penuh, lalu buang satu anggota pada satu waktu. Kalau melepas Fib
   tidak menggeser expectancy, Fib tidak mengkonfirmasi apa pun — dia cuma menunda entry.
4. Lolos kalau `n >= 20` non-overlap, tetap positif setelah fold terbaik dibuang, lolos BH α 0,10
   ([[Fakta Terukur]] §E). Perkakas yang paling dekat: `tools/backtest.py` — tapi yang dia jalankan
   sekarang adalah aturan arah `direction.py`, **bukan** resep ini.

Status: belum pernah dijalankan. Hasil ablasi pada data kami: *(belum diukur)*.

## Konfluensi atau gaung

Pasangan anggota yang **mengukur hal yang sama** — semuanya fungsi dari satu deret `close/high/low`:

| pasangan | kenapa ini gaung |
|---|---|
| bias HTF ↔ struktur penanda zona | dua pembacaan atas ayunan yang sama; [[S3 - Market Structure BOS dan ChoCH]] hanya menamai ulang ekstrem yang dipakai [[FD9 - Horizon Waktu dan Multi-Timeframe]] |
| OB ↔ "impuls" yang melahirkannya | zona didefinisikan oleh pergerakan besar, lalu pergerakan besar dipakai sebagai konfirmasi zona: premis yang diputar lewat dua nama |
| Fib 0,618 ↔ "zona premium" SMC | keduanya menyatakan "harga sudah mundur ±60 % dari ayunan"; satu angka, dua kosakata |
| stop & target ↔ deret harga | `tools/direction.py` menghitung jarak dari ATR deret yang sama — ia mengubah **besarnya** risiko, bukan menambah informasi |
| volum per bar ↔ bar itu sendiri | satu kolom `volume` yang menempel pada OHLC yang sama |

Hitungan jujurnya: **sumber informasi berbeda yang benar-benar ada di repo = 1** (OHLC perp).
Satu-satunya anggota yang berjanji menambah informasi baru adalah profil volum — dan profil yang
bisa kami hitung dari `klines` tidak lebih dari proyeksi bar yang sama; yang sejati butuh tick yang
`TIDAK-ADA` (§C). Manajemen risiko bukan konfirmasi: ia tidak bisa menyetujui atau membatalkan arah,
jadi memasukkannya ke tally menaikkan jumlah tanpa menaikkan pengetahuan. "Lima konfluensi" pada
resep ini = satu deret + satu aturan ukuran.

## Batas dan mode gagal

- **Mode gagal utamanya: tren tipis.** Kelima anggota setuju persis ketika harga sudah pergi jauh —
  mereka semua fungsi dari pergerakan itu. Resep ini paling meyakinkan tepat saat ia paling terlambat.
- **Konfluensi memotong sampel.** Empat syarat serentak mengurangi event; `MIN_SAMPLES=20` non-overlap
  (§E) bisa tidak tercapai justru pada setup yang paling "bersih" secara visual.
- **Gross-nya belum sampai ongkos.** Aturan arah pada 400 hari × 12 aset: gross +1,5 … +4,0 bps vs
  ongkos 20 bps, net **rugi di 12/12** ([[Fakta Terukur]] §F). Lima konfirmasi di atas aturan itu belum
  terbukti membeli selisihnya.
- **Aset yang diuji ≠ aset yang dijual.** Yang bisa kami hargai adalah 608 kontrak perp (§A); cerita
  resep ini lahir di memecoin spot-only yang masa lalunya mentok 41,6 hari.
- **Lawan di sisi order tidak terlihat.** Tanpa L2 tidak ada cara memeriksa klaim "order institusi di
  zona itu" ([[V5 - Mikrostruktur Spread dan Adverse Selection]]).

## Tingkat bukti

`T0` — resep komunitas dari transkrip, belum pernah dijalankan sebagai kesatuan, dan tidak satu pun
anggotanya punya definisi baku yang sudah diuji di repo ini. Bukan `T1`: yang dipakai luas itu
metode-metodenya sendiri, bukan kombinasi ini.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "resep lima konfirmasi ini, pada data kami, cuma punya satu sumber yang benar-benar ada;
  profil volum (satu-satunya penambah informasi) tidak bisa kami hitung; kesatuannya belum diuji."
- **Dilarang:** "All-Rounder setup paling direkomendasikan" · "lima konfluensi = probabilitas tinggi"
  (tanpa n, tanpa ongkos, tanpa ablasi) · "Fabius memakai SMC + Fibonacci + Volume Profile".

**Terkait:** [[ST7 - Checklist Keputusan]] · [[ST3 - Clean Price Action]] · [[FD5 - Expectancy Bukan Win Rate]] ·
[[QT4 - Overfitting dan Validasi]] · [[GAP3 - Yang Punya Data Tapi Belum Diuji]]
