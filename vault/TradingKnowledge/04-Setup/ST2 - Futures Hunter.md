---
tags: [tk, tk-setup, "ST2"]
---

# ST2 - Futures Hunter

**Keluarga:** [[00 - Hub Setup]]
**Anggota:** [[S3 - Market Structure BOS dan ChoCH]] · [[S6 - Likuiditas Stop Hunt dan Inducement]] ·
[[U1 - Open Interest]] · [[U2 - Funding Rate dan Basis]] · [[U3 - Level Likuidasi dan Cascade]] ·
[[V4 - Order Book dan Liquidity Heatmap]] · [[V3 - CVD Delta dan Footprint]] · [[U4 - Long-Short Ratio dan Skew Posisi]]
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"Kombinasi B – Futures Hunter" *(resep komunitas; nama
vendor yang muncul di transkrip — Coinglass, Hyblock — adalah pemberi data versi mereka, bukan hasil uji kami)*

**Ringkas:** setup derivatif: tunggu penyalakan likuiditas, baca posisi terbuka dan funding, sasar
cluster likuidasi, konfirmasi dengan delta agresif. Ditulis apa adanya: **setup ini tidak bisa
dijalankan Fabius hari ini.** Dari delapan anggota, dua bisa kami baca tanpa kunci dan **nol** bisa
diuji — yang membuat seorang "hunter" adalah jejak order, dan jejak order tepat yang tidak ada sama
sekali di repo ini. Ini bukan rencana yang tertunda; ini daftar lubang.

## Resep

| tahap | aturan | catatan |
|---|---|---|
| bias | struktur TF besar masih berlaku | [[S3 - Market Structure BOS dan ChoCH]] |
| pemicu | sweep ekstrem lalu balik (stop hunt) | [[S6 - Likuiditas Stop Hunt dan Inducement]] |
| kondisi | OI naik sambil harga naik → posisi baru, bukan cermin | [[U1 - Open Interest]] |
| carry | funding searah = kamu membayar untuk masuk | [[U2 - Funding Rate dan Basis]] |
| magnet | harga tertarik ke cluster likuidasi terdekat | [[U3 - Level Likuidasi dan Cascade]] · [[V4 - Order Book dan Liquidity Heatmap]] |
| konfirmasi | CVD/footprint: siapa agresif | [[V3 - CVD Delta dan Footprint]] |
| invalidation | balik ke dalam range yang baru disapu | [[FD7 - Invalidation Stop dan Time-Stop]] |
| ukuran | plafon kontrak, bukan keyakinan | [[FD6 - Ukuran Posisi]]; `HARD_CEILING = 10` ([[Fakta Terukur]] §E) |
| keluar waktu | horizon tetap; cascade yang tidak datang = batal | [[FD7 - Invalidation Stop dan Time-Stop]] |

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| OHLC 1 jam ≥ 2.400 bar | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari, hanya aset ber-kontrak perp ([[Fakta Terukur]] §A) |
| funding **terkini** per kontrak | `ADA` | `premiumIndex` 608 kontrak; wired di `tools/direction.py`: funding > 0,05 %/4 j → **tolak posisi** (§A) |
| funding **historis** yang bisa ditarik mundur | `ADA-TAPI` | §A.5: Bybit 66,3 hari / OKX 97,7 hari per 8 jam — uji funding mungkin, tapi bukan per-bar |
| OI terkini | `ADA-TAPI` | `openInterest` terbaca per kontrak (§A); apakah seri historisnya bisa ditarik mundur **tidak terdokumentasi** — jawab dengan panggilan, bukan dengan optimisme |
| level & nominal likuidasi | `TIDAK-ADA` | §C: tidak ada jalur data likuidasi |
| heatmap likuidasi | `TIDAK-ADA` | §C; yang memilikinya adalah vendor, dan vendor bukan jalur repo ini |
| footprint / delta / tick | `TIDAK-ADA` | §C: tidak ada tick di repo ini |
| order book L2 | `TIDAK-ADA` | §C |
| long/short ratio (rute `api.binance.com`) | `MATI-DARI-MESIN-INI` | terukur 24 Sep: `451 restricted location` di runner (§C) |
| funding pembanding (rute OKX) | `MATI-DARI-MESIN-INI` | balas `200` di runner tapi **terpotong TLS di laptop** (§C) |

**Vonis:** 8 anggota → 2 bisa dibaca (satu cuma sebagai veto), 5 `TIDAK-ADA`, 2 `MATI-DARI-MESIN-INI`.
Setup tidak bisa dijalankan. Titik. Jangan dibaca sebagai "tinggal pasang API".

## Uji di Fabius

Tidak ada yang bisa diuji sekarang, dan bentuk ujiannya harus tetap ditulis supaya kelak tidak palsu:

1. Butuh **perekam** yang menyimpan funding/OI per kontrak secara kronologis dan di-commit; jalur hari
   ini membaca nilai saat itu juga, bukan menyimpan riwayat.
2. Setelah ada seri: event = sweep + reversal; hasil = return bersih pada horizon tetap dengan ongkos
   **59 bps** ([[Fakta Terukur]] §D); `n >= 20` non-overlap, BH α 0,10, fold terbaik dibuang (§E).
3. Funding historis wajib ikut. [[06-Results/04 - Negative Results]] mencatat absennya funding sebagai
   batas yang tersisa, dan arah kesalahannya tidak netral: aset yang kami tolak karena carry bisa jadi
   justru satu-satunya yang punya sesuatu untuk diukur.
4. Berapa lama rekaman sampai `n >= 20` tercapai: *(belum diukur)*. Yang jelas penghalangnya waktu
   rekaman, bukan jumlah panggilan API.

## Konfluensi atau gaung

Ironinya: ini **satu-satunya** setup di folder ini yang daftar konfluensinya benar-benar multi-sumber —
harga, buku posisi, buku order. Masalahnya bukan gaung, tapi keabsenan. Yang bisa kami baca pun masih
punya pasangan gaungnya:

| pasangan | status |
|---|---|
| OI ↔ funding ↔ long/short ratio | **satu buku posisi di venue yang sama**, dihitung tiga cara (kontrak, dolar carry, akun). Bukan tiga konfirmasi |
| "OI naik" ↔ "harga naik" | sering kalimat yang sama dengan dua variabel; OI turunan harga × posisi, bukan pengukuran bebas |
| sweep ↔ cluster likuidasi | yang kedua menjelaskan yang pertama tanpa bisa diamati → klaim, bukan data, selama heatmap `TIDAK-ADA` |
| CVD ↔ struktur | **akan** benar-benar independen (level order vs deret) — dan itu tepat yang tidak kami punya |

Satu hal yang wajib tidak salah disebut: funding yang wired di `tools/direction.py` **bukan sinyal
masuk**. Ia gerbang penolak ([[01-Agent/A3 - One-Way Gates]]): komponen penilai hanya boleh mengurangi.
Menempatkannya di kolom "konfirmasi" akan membalik doktrin produk ini lewat sebuah tabel.

## Batas dan mode gagal

- **Mode gagal nyata saat ini: nol.** Yang gagal bukan setupnya, klaimnya — tidak ada jalur di repo
  yang bisa memproduksi keputusannya.
- Kalau someday dijalankan pada venue yang cuma kami baca nilai sesaatnya: setiap anggota kehilangan
  jejak masa lalu, jadi hasilnya tidak bisa direproduksi ([[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]).
- Cluster likuidasi adalah **properti vendor**, bukan properti pasar: bentuknya ikut metode
  interpolasi siapa yang menjualnya. Pemilik klaim: penyedia yang disebut di `Plan.txt` — `T0`.
- Likuidasi memicu volatilitas yang menghancurkan eksekusi kita sendiri; tanpa L2 slip tidak bisa
  diperkirakan sebelum masuk, dan 59 bps (§D) sudah cukup untuk membunuh gross tipis.
- Aset yang bisa kami baca funding/OI-nya = 608 kontrak perp (§A); sebagian besar cerita setup ini
  berlatar token yang tidak ada di daftar itu.

## Tingkat bukti

`T0` — resep komunitas yang **tidak pernah dan belum bisa** kami jalankan. Bukan `T1`: kami tidak punya
bahan untuk mencoba satu pun anggotanya yang inti.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "Fabius membaca funding dan OI saat ini tanpa API key; funding dipakai sebagai penolak
  posisi. Heatmap likuidasi, CVD, dan L2 tidak ada jalurnya, jadi setup ini tidak bisa dijalankan."
- **Dilarang:** "Futures Hunter sedang dipakai Fabius" · "OI + funding + heatmap = tiga konfirmasi
  independen" · setiap angka win-rate untuk setup ini · membaca tabel status di atas sebagai
  "tinggal integrasi".

**Terkait:** [[ST7 - Checklist Keputusan]] · [[GAP4 - Yang Tidak Bisa Diuji Karena Data]] ·
[[U2 - Funding Rate dan Basis]] · [[FD4 - Ongkos Perdagangan]] · [[Fakta Terukur]]
