---
tags: [hasil]
---

# 16 - Harga Keluar yang Hilang

**Sumber:** `tools/censor_bound.py` · horison 30 menit · harga peristiwa · 28 Sep ±15:5xZ
**Alat pembanding:** `tools/technic_lab.py` (halaman 15) memakai pool yang sama TANPA memperbaiki ini

**Ringkas:** halaman 15 menemukan bahwa harapan positif universe ini tinggal di kohort token **muda**
(deret < 30 baris: mean **+450,8 bps**, P(≥+500) 47,5 %) sementara kohort matang negatif (−67,9).
Pertanyaan yang harus diajukan ke angka seperti itu bukan "cara apa yang menungganginya", tapi
**"berapa yang tidak kembali"**. Jawabannya: di kohort muda, **80,6 % kejadian tidak punya satu pun
baris harga dalam jendela keluar** (2.267 dari 2.814). Dan persentil-5 dari yang *kembali* sudah
menyentuh lantai winsor (−2.000 bps). Jadi +450,8 itu bukan temuan - itu **angka korban selamat**.

## 1. Bound, bukan tebakan

| kohort | teramati keluar | hilang | mean hanya-yang-teramati (CI 90 %) | mean bila yang hilang = p05 teramati | break-even |
|---|---|---|---|---|---|
| **MUDA** (deret < 30 baris) | 547 (**19,4 %**) | **2.267 (80,6 %)** | **+249,3** [+146,8; +354,8] · P≥500 42,4 % | **−1.562,8** | **0** dari 2.267 |
| **MATANG** (deret ≥ 30) | 476 (59,8 %) | 320 (40,2 %) | −86,6 [−189,7; +16,5] · P≥500 30,0 % | −855,8 | 0 dari 320 |

`break-even = 0` bukan typo: karena persentil-5 yang teramati sudah **di** lantai (−2.000 bps),
memberi harga "seburuk yang kita pernah lihat" ke kejadian yang hilang sudah cukup untuk membalik
mean kohort muda dari +249 ke −1.563. Tidak perlu mengarang skenario buruk - distribusi kita
sendoh sudah menyimpannya.

## 2. Kenapa kejadian bisa tidak punya harga keluar

`px`/deret peristiwa kita bergerak **hanya saat ada transaksi** (§B lembar fakta: 71,7 % barisnya
bahkan hanya pengulangan nilai). Untuk token yang ditinggalkan pembeli dalam 30 menit, "tidak ada
baris keluar" itu bukan lubang data - itu **beritanya**: tidak ada yang membeli lagi. Membuangnya
sama dengan menghitung hanya pool yang masih hidup dan menyebut hasilnya harapan.

Dua jalan keluar yang jujur, dan belum satu pun kita punya:
1. **Survival-pull**: pantau pool tempat kita membuka posisi sampai horison lewat sumber yang tidak
   bergantung pada transaksi (cadangan pool / `is_stopped` / kehadiran pair), sehingga "pool hilang"
   tercatat sebagai kejadian, bukan sebagai baris yang tidak ada. `wp` (P17) adalah fondasinya tapi
   jendela pantau kita 2 jam dan ditarik **seragam** - ia belum menyimpan token yang kita
   *beli secara keputusan*.
2. **Bound yang dilaporkan**: setiap kali menyebut mean, sebut juga `P(ada harga keluar)`. Alat ini
   sudah mencetaknya; sekarang tinggal kewajiban menuliskannya di tiap halaman hasil.

## 3. Konsekuensinya untuk tiga kandidat fine-tuning (P32)

- **Volatilitas terealisasi** tetap kandidat terkuat - tapi alasannya berubah: ia satu-satunya fitur
  yang justru *mendeteksi* penyakit ini. Kuintil terbawah (median 0,079 %/bar) punya
  **P(≥+500) = 0,0 % dan P(≤−500) = 0,0 %**: tidak bergerak sama sekali, dan sebagian besarnya pasti
  tidak punya baris keluar. Fitur ini memisahkan "hidup" dari "kosong" sebelum kita bertanya arah.
- **Jarak dari puncak (breakout)** tetap masuk sebagai rem, bukan gas.
- **RSI** turun prioritas: di kohort tempat ia bisa dihitung (matang), mean-nya negatif dan
  tanda-nya berubah tiap horison.
- Dan yang paling penting: **teknik klasik tidak akan pernah teruji di kohort tempat harapan
  tinggal**, sampai pengukuran keluar diperbaiki. Urutan kerjanya jadi P33 → P32, bukan sebaliknya.

Baca ulang: `python -X utf8 tools/censor_bound.py` · `python -X utf8 tools/censor_bound.py --horizon 60`

**Terkait:** [[06-Results/15 - Teknikal Klasik Diuji]] · [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] · [[06-Results/04 - Negative Results]] · [[03-Data/D2 - Wallet Flow]] ·
[[TradingKnowledge/EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]] ·
[[TradingKnowledge/EV2 - Jebakan Backtest]] · [[TradingKnowledge/FD5 - Expectancy Bukan Win Rate]]

