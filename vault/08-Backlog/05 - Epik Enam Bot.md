---
tags: [backlog, epik, "enam-bot", operator, rwa]
---

# 05 - Epik Enam Bot (Fabius sebagai operator pemilih bot)

**Bagian dari:** [[08-Backlog/00 - Hub Backlog]]
**Dibuka:** 2 Okt 2026 oleh builder, dengan kata-katanya (diringkas): *Fabius akan menjadi **trading agent
operator**. Agen menganalisis dan memprediksi, tetapi untuk membuka posisi ia hanya boleh **memilih bot** yang
cocok. Satu bot = **satu parameter + satu metode**. Rencananya **enam bot** supaya agen leluasa memilih. Bot-bot
ini berisi teori kita; baru empat dan kurang oke. Carikan enam metode yang paling optimal, bebas apa pun
(imbalance order book itu hanya logika saya sendiri). Lingkup: crypto, dan RWA kalau memungkinkan. Klaim vault
yang berbeda boleh direvisi.*
**Sumber:** [[09-Inbox/Session-2026-10-02]] (keluaran, rekaman peneliti, sitasi) dan skrip di
`09-Inbox/Session-2026-10-02-skrip/` (urutan menjalankan ada di catatan sesi itu).

> **STATUS: USULAN. Bukan keputusan, bukan klaim produk.** Semua angka di halaman ini **eksploratif**: dihitung
> oleh skrip sesi yang belum menjadi alat di `tools/`, belum punya kunci pra-registrasi, dan dipilih dari ±20
> kandidat - jadi memilih pemenangnya membawa risiko seleksi yang sama dengan F-D39 (satu undian yang
> menang bukan hasil). Aturan [[Conventions]] §1 tetap: angka baru boleh dikutip keluar vault hanya setelah
> menjadi alat + kunci + uji maju. Sampai saat itu halaman ini adalah **daftar kerja supaya tidak lupa**.

> **Pembaruan 2 Okt 2026 (malam, setelah jawaban builder):** arah operator + penjualan sinyal + program penerbit bot kini **dicatat sebagai keputusan**
> di [[00-Overview/03 - Decisions]] F-D70 dan F-D71; isi halaman ini (enam bot, parameter, angka) **tetap USULAN**. Bot Fabius sendiri sudah dijalankan melalui
> gerbang seleksi yang sama dengan penerbit luar: hasilnya di [[07 - Epik Kolaborasi Bot Terbuka]] §7 (B3 dan B5 lolos; B1, B2, B6 tolak; B4 tak terukur).
>
> **KOREKSI 2 Okt 2026 (malam): mesin `engine/` (§14) memutar ulang layar di data yang sama dan menemukan tiga hal.
> Angka lama di §2-§3 TETAP dipajang di bawah; bacalah sebagai pra-koreksi.** Semua angka koreksi dicetak oleh
> `python -X utf8 -m engine.golden --data <dir>` (`<dir>` = keluaran `fetch.py`); jendela 2020-12-01 → 2026-08-31 kecuali
> disebut lain.
>
> | # | temuan | sebelum (layar) | sesudah (mesin) |
> |---|---|---|---|
> | K1 | **B2: Sharpe 1,29 = undian fase.** Layar merotasi dengan `i % 7` dari 1 Jan 2020, yang jatuh pada **Rabu**. Hari rebalance lain, data sama: Sen 0,647 · Sel 0,637 · **Rab 1,281** · Kam 1,224 · Jum 0,887 · Sab 0,289 · Min 0,466 (rentang 0,289-1,281; rerata 0,776). Mesin memakai 7 sub-buku (satu per hari-minggu) sehingga tidak ada hari yang dipilih | 1,29 (tahunan 94,6 %, MDD −61,3 %) | **0,848** (tahunan 56,0 %, MDD −70,9 %). Per tahun, sampel penuh: 2020 2,15 · 2021 1,82 · 2022 1,32 · 2023 1,29 · **2024 0,09 · 2025 −0,16 · 2026 −1,12** |
> | K1b | pindai L yang "tidak mulus" sebagian besar kebisingan fase. Tanpa undian fase, L = 7 / 10 / 14 / 21 / 28 / 42 / 56 | 0,60 · 0,53 · 1,35 · 0,64 · 1,29 · 0,68 · 0,85 | 0,31 · 0,43 · 1,06 · 0,85 · 0,85 · 0,61 · 0,72 (landasan L = 14-28) |
> | K2 | **Gabungan lima bot** di §3 memakai B2 fase Rabu dan B3 yang tercemar K3 | 1,65 · 37,8 %/th · MDD −15,2 %; 2025-01 → 2026-08: **0,42** | **1,388** · 30,0 %/th · MDD −17,5 %; 2025-01 → 2026-08: **0,071** (0,9 %/th). Korelasi antar-bot tetap: rerata 0,13, maks 0,42 |
> | K3 | **Bolong data.** Lima perp (SOL, XRP, LTC, TRX, NEAR) tidak punya bar 26-28 Feb dan 1-2 Apr 2022 di unduhan Binance Vision (penyebab tidak diselidiki; bukan klaim tentang pasar). `pandas.pct_change` menghitung return 2-3 hari sebagai satu hari → posisi dan PnL palsu (B3: −1,38 % pada 3 Apr 2022; vol B3 hanya ≈1,4-1,6 %/th sehingga Sharpe-nya hipersensitif terhadap satu hari). Mesin tidak memegang aset yang tak punya bar pada hari itu | B3: 5,61 (penuh) · 5,01 (sejak 2020-12) | 6,05 · 5,56 |
>
> **Bertahan:** B1 (mesin 1,011 vs layar 1,017, sampel penuh), B5 (1,130 vs 1,131) dan B6 (0,427 vs 0,435) berbeda ≤ 0,01. Di
> luar jendela bolong (≤ 2022-02-24 dan ≥ 2022-05-15) PnL harian mesin = layar (korelasi 1,0000; B3 0,9992 sebelum dan 1,0000
> sesudah). Perintah: `python -X utf8 run10_engine_vs_ref.py` di `09-Inbox/Session-2026-10-02-skrip/` (butuh pandas).
> **Belum dicetak ulang oleh mesin** (anggap pra-koreksi dan belum terverifikasi): pindai parameter B1/B3/B5/B6 selain nilai
> awal, deret biaya 0/15/30 bps, pemisahan rezim, kontrol selektor §2.3 (EW 1,50; acak 0,65), dan seluruh B4.

## 1. Konsep, apa adanya

- Agen (LLM) menganalisis dan memprediksi. Ia **tidak** menentukan parameter dan **tidak** mengirim order
  sendiri: ia hanya memilih satu dari enam bot (atau tidak memilih).
- Satu bot = satu metode deterministik + satu parameter. Konstanta lain terkunci di spesifikasi (bukan
  parameter yang boleh digeser agen).
- Empat teori yang ada ([[03 - Epik Teori Baru]]: T1 imbalance buku, T2 trailing, T3 signed volume, T5 microprice)
  dinilai kurang. Pencarian dibuka ke metode apa pun.
- Lingkup: crypto; RWA bila memungkinkan, kalau tidak fokus crypto.

## 2. Tiga hal yang membalik kerangka lama (semua eksploratif)

1. **Di horizon harian, biaya sekunder.** Bot RS di §3 (B2) memberi Sharpe 1,37 / 1,29 / 1,19 / 1,02 pada biaya
   0 / 7 / 15 / 30 bps **per sisi** (30 bps per sisi = 60 bps putaran, setara ruler 59 bps vault). "Biaya
   membunuh" adalah sifat skala **menit** pada memecoin tipis ([[06-Results/28 - Venue Kami Bukan Pasar]]),
   bukan sifat setiap strategi.
   ↳ **K1:** seluruh deret biaya B2 itu dihitung pada fase Rabu; belum dicetak ulang oleh mesin.
2. **Teori lama pensiun sebagai bot.** T1 (imbalance): prediksinya nyata di buku lebar tetapi `net` kalah ½-spread
   (E25, [[06-Results/29 - Buku Order, Frame Baru]]) - alat market-maker/eksekusi, bukan bot taker. T2 (trailing)
   menjadi **modul keluar**, bukan metode. T3 (signed volume): nol. T5 (microprice): alat audit fill.
3. **Selektor naif tidak mengalahkan equal-weight (EW).** Pada set uji awal 6 bot harian: EW Sharpe 1,50; pilihan
   acak harian 0,65 (p5 0,05; p95 1,24); "pilih bot dengan Sharpe 60 hari terbaik" 0,27; aturan "BTC di atas
   SMA100 → trend, selain itu → RS" 1,22. Konsekuensi: pembanding operator yang sah adalah **EW dari enam bot**,
   bukan sekadar pilihan acak (pola F-D32/E24).
   ↳ **K1/K2:** EW 1,50 dan kontrol selektor memakai B2 fase Rabu; belum dihitung ulang.

## 3. Enam bot (usulan)

Setiap bot: satu metode, satu parameter (nilai awal + rentang yang diuji), instrumen, bukti eksploratif, rezim,
risiko, tingkat, dan **pembunuh yang diusulkan** (menunggu dikunci). Dasar data: 16 perp mayor (BTC, ETH, BNB,
SOL, XRP, DOGE, ADA, LINK, LTC, AVAX, TRX, DOT, BCH, ETC, ATOM, NEAR), kline harian futures dan funding 8 jam
dari `data.binance.vision`, 2020-01 → 2026-08, **biaya 7 bps per sisi + funding nyata**; emas lewat PAXG spot
(2020-08 → 2026-08, 10 bps per sisi). Universe = aset yang masih hidup (bias penyintas menggelembungkan
buy&hold dan sisi long). Pembanding: BTC buy&hold Sharpe 0,71 (MDD −78,9 %); keranjang EW buy&hold 0,85
(MDD −76,8 %).

### B1 - TREND (momentum deret waktu, long/flat)
- **Metode:** long bila harga penutupan > penutupan N hari lalu; selain itu flat. **Parameter: N = 60 hari.**
- **Instrumen:** BTC/ETH/SOL (dalam); BNB tipis di Aster ($6,9 juta/hari).
- **Bukti:** plateau datar N = 10…120: Sharpe 0,96 / 1,09 / 1,10 / 0,89 / 1,02 / 0,92 / 0,91 (N = 10, 20, 30, 45, 60,
  90, 120); MDD sekitar −56 % vs −79 % buy&hold; positif per aset (N = 30: BTC 0,95, ETH 1,13, BNB 1,15, SOL
  1,56); biaya 0 → 30 bps per sisi: 1,15 → 0,96. Literatur: kuat jangka panjang, **meluruh sejak 2025**
  (laporan peneliti; bukti pasca Mar-2025 lemah).
- **Rezim:** BTC > SMA100: Sharpe 1,95; di bawahnya −0,76. Tahun 2025-2026: ≈ −0,1 (N = 60), −0,6…−1,4 (N = 30).
- **Risiko:** whipsaw di pasar datar; funding perp long adalah beban orde pertama.
- **Tingkat:** A−. **Pembunuh (usulan):** 12 bulan maju tanpa mengalahkan buy&hold pada MDD *dan* Sharpe; atau
  kalah dari placebo masuk-acak dengan distribusi lama tahan yang sama.

### B2 - RS (rotasi kekuatan relatif, dollar-neutral)
- **Metode:** tiap 7 hari, urutkan aset menurut return L hari; long 3 teratas, short 3 terbawah (bobot sama).
  **Parameter: L = 28 hari.**
- **Instrumen:** 10-12 perp terlikuid. Short leg = risiko lonjakan.
- **Bukti:** L = 14: 1,35; 28: 1,29; 56: 0,85, **tetapi** L = 21 dan 42 hanya 0,64 / 0,68 dan L = 7, 10: 0,60 / 0,53
  - landasannya **tidak mulus** (positif semua, tinggi-rendah ikut L). Pemisahan sampel L = 28: 1,91 (2020-09 →
  2023-06), 0,51 (2023-07 →), −0,01 (2025-01 →). Korelasi harian dengan TREND 0,22.
  ↳ **K1, K1b:** semua angka B2 di atas = fase Rabu. Tanpa undian fase (7 sub-buku): 0,85 (L = 28), 1,06 (L = 14); per tahun
  2024 0,09, 2025 −0,16, 2026 −1,12. Peluruhan sejak 2024 sudah terbaca di pemisahan sampel di atas.
- **Rezim:** BTC naik 1,86; BTC turun 0,28. Lemah sejak 2025.
- **Tingkat:** B. **Pembunuh:** net Sharpe < 0 dua kuartal beruntun, atau tidak mengalahkan placebo peringkat-acak.

### B3 - CARRY (funding, delta-neutral)
- **Metode:** saat funding rata-rata 7 hari (disetahunkan) > θ: long spot + short perp; selain itu flat. **Parameter:
  θ = 10 % per tahun.**
- **Instrumen:** perp mayor + kaki spot. **Kaki spot di Aster belum jelas** (spot BTC Aster tipis).
- **Bukti:** θ = 5 / 10 / 20 / 30 %: Sharpe 5,73 / 5,61 / 5,15 / 4,57 (hasil ≈ 6-10 % per tahun pada notional, MDD
  −0,6…−2,5 %, aktif 55 / 33 / 15 / 11 % hari). Per tahun (θ = 10 %): 2023 4,63; 2024 9,47; **2022 −1,15; 2025 −2,02;
  2026 −3,16**.
  ↳ **K3:** mesin (θ = 10 %): Sharpe 6,05 (penuh) / 5,56 (sejak 2020-12); selisih dengan layar = artefak bolong data 2022, bukan
  pasar. Vol B3 ≈1,5 %/th: Sharpe-nya bukan ukuran risiko (ekor = ADL, venue, basis).
- **Dorman sekarang:** funding BTC (Hyperliquid) rata-rata 24,1 % (2024) → 10,6 % (2025) → 5,1 % (2026 YTD); θ = 15 %
  aktif 0 % hari di 2026 (laporan peneliti, hitung sendiri dari API publik). Ekor ADL: 10 Okt 2025 > $19 miliar
  terlikuidasi (sumber sekunder).
- **Tingkat:** A secara historis, **tidak aktif** hari ini. **Pembunuh:** hasil hedged negatif tiga bulan berjalan
  saat aktif, atau satu kejadian ADL pada kaki perp.

### B4 - LISTING-FADE (guncangan pasokan, short token baru)
- **Metode:** short perp token yang baru listing pada penutupan hari-1; tutup setelah H hari. **Parameter: H = 14
  hari.** Ukuran kecil (≤ 2 % ekuitas per trade), margin isolated, tanpa leverage tinggi.
- **Bukti (arah, kuat):** 451 listing USDT Binance 2020 → 2026-07 (volume hari-1 ≥ $2 juta): return hari-1 → hari-7 /
  14 / 30 setelah dikurangi BTC = −17,7 / −24,0 / −31,4 % (t −10,2 / −12,0 / −12,0), 75-77 % turun, **negatif di setiap
  tahun** (hari-30: 2020 −44,9; 2021 −24,9; 2022 −19,5; 2023 −20,0; 2024 −14,0; 2025 −52,4; 2026 −26,8 %). Pop hari-1
  (buka → tutup): +52…+177 % per tahun. **Versi perp nyata di Aster** (106 listing, onboard 2025-01 → 2026-08, volume
  hari-1 ≥ $1 juta): −14,4 / −23,2 / −33,4 % (t −3,3 / −4,8 / −5,9).
- **Bukti (bisa di-trade, lemah):** short masuk di penutupan hari-1, biaya 1 % putaran diasumsikan: H = 14 **tanpa stop**
  +14,4 % per trade (t 3,5; menang 75 %; trade terburuk −182 % notional); stop 90 % +7,4 % (t 1,6); **stop 30 % −0,4 %,
  stop 50 % +1,7 % (t ≤ 0,4; ±36-50 % trade tersapu lonjakan)**. H = 30 tanpa stop +19,7 % (t 3,2; terburuk −340 %).
  Simulasi portofolio 106 trade (kerugian dibatasi −100 % notional - **asumsi yang tidak berlaku tanpa margin
  isolated**): 2 % per trade, H = 14: CAGR 20,6 %, MDD −3,5 %.
- **Ketersediaan perp:** untuk token yang listing di Binance spot sejak 2024-06 dan punya perp Aster (n = 125), selisih
  onboard perp − listing spot: median 141 hari; 46 % dalam ≤ 7 hari; 40 % perp lebih dulu.
- **Risiko:** ekor squeeze tak terbatas; buku perp baru tipis; funding bisa berbalik; ramai ditiru.
- **Tingkat:** B− (arah paling kuat yang pernah kami ukur; ekspektasi yang bisa di-trade bergantung pada
  manajemen ekor). **Pembunuh:** 20 listing maju dengan rata-rata PnL short ≤ 0, atau satu trade lebih buruk dari
  −100 % notional, atau fade mati dalam sampel maju. Butuh pipeline event (P73) sebelum bisa diuji maju.

### B5 - CORE-RWA (risk parity BTC + emas)
- **Metode:** bobot BTC dan emas ∝ 1/σ (σ = deviasi baku return harian L hari); rebalance bulanan. **Parameter: L =
  90 hari.** Emas lewat XAUUSDT (Aster) atau XAUT/PAXG.
- **Bukti:** L = 30 / 60 / 90 / 180: Sharpe 0,94 / 1,04 / 1,13 / 1,31; MDD −33,0 / −32,2 / −30,1 / −30,0 % (BTC spot
  −76,6 %). 50/50 statis 1,01. Per tahun (L = 90): 2022 −0,93; 2025 1,75; 2026 0,08. Emas buy&hold (PAXG) Sharpe
  0,82, MDD −28,1 %. Alternatif satu-parameter: rotasi BTC↔emas menurut rasio vs SMA(N): N = 50 / 100 / 150 / 200: 1,45 /
  1,07 / 0,92 / 0,25.
- **Risiko:** sebagian besar hasil = reli emas 2024-25; lemah di 2022. Korelasi harian emas-BTC 0,14.
- **Tingkat:** B. **Pembunuh:** Sharpe < BTC buy&hold *dan* MDD tidak lebih baik dari −50 % dalam 12 bulan maju.

### B6 - BOUNCE (mean-reversion, long/flat)
- **Metode:** beli bila z-score harga (vs rerata dan deviasi N hari) < −2; keluar saat z ≥ 0. **Parameter: N = 10 hari.**
- **Bukti:** N = 10 / 20 / 50: Sharpe 0,44 / 0,31 / 0,30 (MDD −40 / −51 / −55 %). Per aset (N = 10): BNB 0,44, DOGE 0,46,
  LINK 0,44, ADA 0,39, SOL 0,30, XRP 0,20, **BTC 0,07, ETH 0,00**. Sendiri lemah; **korelasi 0,01** dengan EW empat bot
  lain, menaikkan Sharpe EW 1,36 → 1,43 dan MDD −27,7 % → −19,5 % (basis: trend, RS, carry, rotasi emas).
- **Tingkat:** C (literatur lemah/kontroversial). **Pembunuh:** sinyal maju tidak menaikkan Sharpe EW, atau n ≥ 20 sinyal
  dengan rata-rata net ≤ 0.

### Gabungan lima bot harian (B1, B2, B3, B5, B6)
EW 2020-12 → 2026-08: Sharpe 1,65, tahunan 37,8 %, MDD −15,2 %; korelasi rata-rata 0,13 (maks 0,42). Per tahun:
2021 3,42; 2022 −0,15; 2023 2,03; 2024 1,51; 2025 1,23; 2026 (s.d. Agu) −0,78. **Jendela 2025-01 → 2026-08: EW 0,42**
(B1 −0,10; B2 −0,01; B3 −2,12; B5 0,85; B6 0,38). Sebagian besar hasil historis datang dari 2020-24. B4 berbasis event,
dihitung terpisah.
↳ **K2:** mesin (B2 tanpa undian fase): EW 1,388; **2025-01 → 2026-08: 0,071**. Per tahun: 2021 2,92 · 2022 −0,06 · 2023 1,84 ·
2024 1,14 · 2025 0,92 · 2026 −1,26 (s.d. Agu).

## 4. Diuji dan ditolak (eksploratif)

| metode | hasil | catatan |
|---|---|---|
| pairs ETH/BTC (N = 20 / 60 / 120) | Sharpe −0,62 / −0,21 / 0,08 | BNB/BTC −0,7…−0,8; SOL/ETH −0,74 / −0,11 / −0,14 |
| reversal lintas aset (long pecundang, short pemenang) | −1,68 / −1,28 / −0,97 / −0,94 (N = 1, 3, 5, 7) | momentum bertahan di horizon pendek |
| low-vol L/S | −0,43 (N = 14, 30, 60) | positif hanya 2025-26 |
| funding kontrarian (arah) | −0,29 / −0,19 (p = 0,90 / 0,95) | konsisten dengan [[06-Results/08 - Carry Study]] |
| squeeze breakout | 0,33 / 0,46 / 0,50 | lemah; korelasi 0,29 ke basis |
| vol-managed BTC | 0,61 / 0,59 / 0,57 (T = 30 / 40 / 60 %) < buy&hold 0,71 | **aturan ukuran**, bukan bot |
| trend short-only | −0,13 | |
| musiman hari-minggu BTC | Sen +43,6; Rab +47,1; Kam −18,4 bps/hari | **kuriositas**: dipilih setelah melihat 7 hari |
| **weekend-gold (kontinuasi)** | Aster XAUUSDT 46 akhir pekan: +24,5 bp/4 jam (t 1,94; p ≈ 0,3 setelah 10 uji); **PAXG 314 akhir pekan 2020-26: −8,1 bp (t −2,5), tanda berbalik tiap rezim** (2021-25 negatif semua; 2026 +27,6) | bukan bot; lihat Inbox |
| saham/ETF RWA | likuid hanya jam bursa (akhir pekan $14-76/jam) | lihat §6 |
| on-chain/stablecoin, seasonality jam | bukti lemah (laporan peneliti) | tidak diuji sendiri |

## 5. Lapisan operator (aturan usulan)

- **Ruang aksi tertutup:** `{NONE, B1…B6}` (atau himpunan bagian dengan anggaran risiko tetap). Gerbang deterministik
  hanya boleh **mempersempit** (bot dibuang, atau plafon dikecilkan). Tidak ada komponen - model maupun pemilik -
  yang boleh menambah bot, mengubah parameter, atau menaikkan plafon tanpa perubahan kontrak yang terlihat. Ini
  pengganti [[Concepts/One-Way Gate]] untuk operator (versi lama tetap dipajang).
- **Tetap satu arah:** plafon turun saja (`HARD_CEILING`, `dailyCap`, per-bot); kill switch hanya menutup; spesifikasi
  bot ber-sha (ubah = bot baru dengan n mulai nol); `NONE` selalu sah dan gratis; keluaran model = enum + confidence,
  tak valid/timeout = `NONE` (F-D11); promosi paper → nyata oleh F-D16 dalam kode, bukan oleh model.
- **Evaluasi pemilih:** kontrol = **EW enam bot** + pilihan acak + "bot terbaik 60 hari"; skor Brier prediksi rezim
  **sebelum** PnL; BH lintas enam bot; jeda minimum antar-pergantian (pergantian = ongkos).
- **Peringatan literatur (laporan peneliti):** agen LLM trading tidak punya alpha persisten dan sering salah
  pro-siklikal; backtest di dalam masa latihan model **terkontaminasi** (harga terhafal) - hanya keputusan maju
  yang ter-anchor sebelum hasil yang sah (itu persis tugas `DecisionAnchor`).

## 6. Venue, RWA, dan jalur uji

**Dari jaringan builder (Indosat), 2 Okt 2026:** `agent.binance.com`, `www.binance.com`, `developers.binance.com`
tidak bisa dijangkau (sertifikat yang disajikan `*.ioh.co.id`). Terjangkau: Aster (mainnet + testnet), Hyperliquid
(mainnet + testnet), PancakeSwap, testnet Binance (spot dan futures), GitHub, mirror dokumen `developers.binance.info`.

| jalur | apa | cocok untuk | catatan |
|---|---|---|---|
| **Paper** (mesin sendiri) | simulasi isi di atas harga/buku publik; tanpa akun venue | semua bot, tahap pertama | tidak perlu venue sama sekali |
| Binance **futures testnet** | 741 simbol termasuk XAUUSDT, XAGUSDT, TSLAUSDT, NVDAUSDT, QQQUSDT | uji pipa order perp | likuiditas palsu; terjangkau |
| Aster futures testnet | 18 simbol (BTC/ETH/BNB/SOL…); tanpa RWA | uji pipa BNB-native | spot testnet juga ada |
| Hyperliquid testnet | perp + HIP-3 | uji pipa | |
| **Aster mainnet** | perp crypto + 115 STOCK, 14 ETF, 11 komoditas | jalur uang nyata BNB-native | T&C §6.2(e): bot hanya lewat API resmi (agent wallet) |
| Hyperliquid mainnet | HIP-3: 129 pasar, ≈6× volume RWA Aster | alternatif RWA | |
| **Binance Agentic Wallet** | wallet MPC tanpa kunci; swap DEX, limit order, DeFi, prediksi; BSC/ETH/Base/Solana (SKILL.md juga Arbitrum, Polygon, Robinhood Chain) | **hanya bot long-only on-chain** (B1, B6, B5 lewat XAUT) | **tanpa perintah futures/perp; tanpa testnet/paper di dokumen**; batas swap $50 ribu, DeFi $100 ribu, x402 $20 per hari |
| Binance **Agent OS/MCP** | sub-akun Agentic: Spot, Margin, Convert, USDⓈ-M & COIN-M Futures; tanpa scope tarik | semua bot, secara teknis | order menunggu "ya" per transaksi; endpoint terblokir dari jaringan builder |

- **Binance AI Pro tidak disebut sebagai prasyarat** di dokumen Agentic Wallet (halaman docs, `SKILL.md`,
  `preflight.md`); berita menyebut pengguna lain memasang skill sendiri: `npx skills add
  https://github.com/binance/binance-skills-hub --skill binance-agentic-wallet`, CLI `npm install -g
  @binance/agentic-wallet`, login `baw auth signin` → `baw auth verify` (pairing kode di app Binance Wallet). AI Pro
  adalah langganan terpisah (beta $9,99/bulan; reguler $29,99; uji 7 hari - sumber berita) yang membawa wallet itu
  bawaan. Dokumen **tidak menyebut** syarat KYC/negara/versi aplikasi; berita: tersedia "di wilayah yang sudah bisa
  mengakses Binance Wallet". Belum bisa diuji dari jaringan builder.
- **RWA di Aster (diukur 1 Okt 2026, ±19:00 UTC; peneliti):** kelas 24/7 hanya **XAUUSDT** (spread 0,02 bp; kedalaman ±10 bp
  $478 ribu; dampak $10 ribu 0,6 bp) dan **CLUSDT** (1,1 bp; $388 ribu; 0,7 bp). Volume RWA $508 juta/hari: **86 % = enam
  pair USD1** yang disubsidi program reward sampai 31 Des 2026 (risiko tebing). Saham/ETF likuid hanya jam bursa (akhir
  pekan median $14-76/jam); 85 dari 134 simbol RWA < $0,1 juta/hari. Tidak ada edge khas-RWA yang lolos; BNBUSDT hanya
  $6,9 juta/hari (tipis dibanding BTC $520 juta, ETH $362 juta, SOL $81 juta).
- **Untuk tahap paper venue tidak perlu dipilih.** Pilihan venue baru mengikat saat gerbang uang nyata F-D16.
- **Keputusan builder 2 Okt malam:** paper penuh sampai builder sendiri yakin mengeluarkan uang; venue uang nyata kelak kemungkinan besar **Binance Agentic Wallet**.
  Konsekuensi yang perlu dilihat sejak sekarang: Agentic Wallet = on-chain, **tanpa perp/short**, jadi hanya bot long-only yang bisa dieksekusi di sana (B1, B6, B5
  lewat BTC + token emas); B2 (kaki short), B3 (kaki perp short), dan B4 (short) butuh venue lain (Agent OS/Aster/Hyperliquid) atau tetap paper/sinyal saja.
  Bot identitas yang diusulkan (B5-CORE-RWA, [[07 - Epik Kolaborasi Bot Terbuka]] §10) kebetulan long-only.

**Venue lokal berizin OJK (3 Okt malam; dibaca dari dokumen resmi + API publik):** Tokocrypto punya API trading SPOT terbuka untuk pemegang akun
(`/open/v1/orders`, HMAC; 16/16 aset B1 punya pasangan USDT aktif); futures belum ada (target akhir 2026). Pintu hanya API mitra Pintu Pro (permohonan
kemitraan; contoh resmi spot). Akibatnya: B1-TREND (long/flat) bisa dijalankan di venue lokal berizin; B3-CARRY (short perp) belum punya venue lokal.

**Agentic Wallet dicek ulang (3 Okt malam, sumber primer):** `skills/binance-web3/binance-agentic-wallet/SKILL.md` di `binance/binance-skills-hub` (commit terakhir 2026-09-09) memuat perintah `baw`: swap pasar, limit order beli/jual, kirim, DeFi, pasar prediksi, x402, serta `contract-call` dan `sign-message` umum. **Tidak ada perintah perp/futures/short/leverage.** Binance Wallet versi WEB kini punya perpetual "provided by Aster" (pengumuman Binance), tetapi itu antarmuka manusia, bukan perintah agen. Jadi lewat Agentic Wallet resmi: long/flat on-chain saja (B1, B6), sama seperti Tokocrypto spot; B3 (short perp) tetap butuh API Aster (agent wallet, `approveAgent`) atau Agent OS (konfirmasi "ya" per order). Akses: domain Binance terblokir dari jaringan builder (2 Okt), dan login `baw` dipasangkan lewat aplikasi Binance Wallet.

**Leverage (3 Okt malam, sumber primer):** **Aster API**: `POST /fapi/v3/leverage`, leverage awal per simbol bilangan bulat 1-125 (dibatasi braket notional per simbol), tipe margin isolated/cross; agent wallet didaftarkan dengan izin terpisah `canSpotTrade` / `canPerpTrade` / `canWithdraw` + kedaluwarsa + daftar IP (wajib bila `canWithdraw`) - repo `asterdex/api-docs`, `V3(Recommended)/EN/aster-finance-futures-api-v3.md`, commit terakhir 2026-09-23. **Binance Agent OS** (diluncurkan 20 Agu 2026): sub-akun Agentic bisa Spot, Margin, Convert, USDⓈ-M + COIN-M Futures (jadi leverage ada), tanpa izin tarik ke luar; batas leverage yang bisa disetel pengguna TIDAK disebut di sumber yang dibaca. **Belum pasti:** catatan 2 Okt menulis order menunggu "ya" per transaksi, sedangkan berita (crypto.news) menggambarkan agen jalan otonom di dalam batas sub-akun dengan ToS yang menyarankan meninjau tiap order; diuji saat ada akses. Untuk Fabius: semua sinyal dan uji maju diukur TANPA leverage (bobot <= 1; B2 gross 2); memakai leverage = spesifikasi baru = kunci baru ([[Conventions]] "pivot = kunci baru").

## 7. Penggaris biaya (menggantikan "59 bps untuk semuanya")

59 bps = fee DemoPair (2 × 30 bps) pada 1 unit - ruler **venue demo**, bukan venue nyata (`tools/costs.py:13,35`).
Ruler per venue = fee + ½-spread buku + dampak + funding. Terbaca/terukur (peneliti, Aster): taker crypto 4 bp; taker
RWA 1,25 bp, maker 0 (sejak 2026-09-07, dokumen + berita); spread BTC 0,01, ETH 0,04, SOL 0,84, BNB 0,65, XAUUSDT 0,02 bp;
putaran $10 ribu ≈ 8 bp di BTC, ≈ 3,7 bp di XAUUSDT. Label angka "10-15 bps" sebagai `assumed-builder` sampai terukur
(jangan ulangi kisah 20 bps, F-D24).

**Biaya per jalur eksekusi (3 Okt malam, atas pertanyaan builder "apakah mereka ada admin feenya? misal spread"; bahan P69).** Tidak satu pun jalur
memungut "biaya admin/langganan" terpisah untuk agen yang ditemukan; biayanya = fee trading + spread/slippage + funding (perp) + gas (on-chain).
Level: *primer* = dokumen resmi dibaca langsung; *sekunder* = ringkasan pencarian/ulasan (situs resmi tak terjangkau dari jaringan kita).

| jalur | fee trading (VIP 0, per sisi) | biaya lain | level |
|---|---|---|---|
| Tokocrypto spot, pasangan USDT | maker 0,10 % / taker 0,10 % (diskon s.d. 25 % bila bayar TKO; VIP 9: 0,036 / 0,048 %) | spread buku; tanpa funding. Pasangan IDR: taker 0,20 % / maker 0,10 % + PPN + pungutan bursa (CFX/ICEx) | sekunder (halaman dukungan Tokocrypto membalas 403) |
| Binance Agentic Wallet (swap DEX di BSC) | biaya layanan Web3 Wallet: 0 % untuk token utama/stablecoin (sering promosi), hingga ±0,5 % token lain; plus fee pool (PancakeSwap v2 0,25 %, v3 0,01-1 %) | gas BSC, slippage + dampak harga AMM, proteksi MEV (bawaan aktif) | skill resmi menunjuk FAQ biaya Binance (`market-order.md`), FAQ itu tak terjangkau; angka sekunder |
| Aster perp (Pro, order book) | maker 0 % / taker 0,04 % (crypto umum); grup B taker 0,10 %; RWA taker 0,0125 % (sejak 2026-09-07) | funding (bayar/terima), spread, risiko likuidasi | primer (docs.asterdex.com, fees) |
| Binance Agent OS (futures USDⓈ-M) | maker ±0,02 % / taker 0,04-0,05 % (sumber berbeda); spot 0,10 %; diskon BNB 10 % futures / 25 % spot | funding, spread; sub-akun biasa ikut tier akun induk (khusus sub-akun Agentic belum terkonfirmasi) | sekunder (binance.com tak terjangkau) |
| Pintu Pro (mitra) | tidak publik | - | - |

**Dibanding asumsi paper (7 bps per sisi, `engine/spec.py` penggaris B1/B3):** Aster perp (4 bps taker + spread BTC ±0,01 bp) dan Binance futures (±5 bps)
masih di bawah 7; Tokocrypto spot 10 bps (+43 %); Agentic Wallet untuk koin non-utama bisa 25-50 bps + gas + slippage (3,5-7x asumsi). Akibatnya hasil
paper B1 hanya bisa dipindah ke Tokocrypto/Agentic Wallet sesudah penggaris per venue (P69) mengukur ulang biayanya; untuk bot berputaran rendah
(B1) selisihnya kecil per tahun, untuk bot berputaran tinggi (B2) bisa menghapus hasil.

## 8. Dari usulan ke bot yang boleh dipercaya

1. **Satu kunci per bot** (pola F-D29/F-D68): aturan + parameter + **daftar simbol** (P67) + penggaris + horizon + kontrol +
   syarat vonis, di-sha sebelum satu data maju pun dibaca.
2. **Syarat vonis:** F-D16 (net > 0 setelah ongkos nyata, n ≥ 20, tetap positif setelah fold terbaik dibuang, BH α 0,10,
   di luar sampel) + **plateau ±50 % parameter** + kontrol placebo masuk-acak dengan distribusi lama tahan yang sama +
   BH lintas enam bot.
3. **Urutan:** mesin paper → pipa testnet (Binance/Aster/Hyperliquid) → uang nyata kecil (Agentic Wallet untuk long-only
   on-chain; Aster/lainnya untuk perp) **hanya** setelah F-D16.
4. **Perbaiki dulu** temuan audit 2 Okt yang menyentuh bot: bar basi di `direction.py` (P71), pemeriksaan "ter-anchor" di
   `execute_live.py` yang tak pernah menyala dan `ExecutionVault` yang hanya menolak hash nol (P72).

## 9. Klaim vault yang berbenturan (audit 2 Okt; **belum ada yang diubah**)

Aturan repo: koreksi dipajang, tidak dihapus ([[Conventions]]; [[00-Overview/05 - Corrections]]). Halaman lama tetap utuh
sampai builder memberi kata; usulan penggantinya ada di Inbox. Nomor baris dibawa dari audit peneliti dan baru
sebagian saya cek sendiri (README.md:9-11, :66, :72 cocok); **cek ulang dengan `Grep -n` sebelum menyunting**.

| lokasi | yang dikatakan | masalah di bawah konsep operator |
|---|---|---|
| README.md:9-11; START-HERE.md:10 | "bukan bot ... firma riset yang menahan diri" | operator memilih bot berposisi |
| README.md:72; Claims and Limits:28-29 | "paper on purpose, tidak ada order" | sudah salah: 3 putaran nyata di testnet 97 |
| One-Way Gate; A3:10; F-D11 | "model hanya boleh membatalkan/mengecilkan" | aksi utama operator = memilih; lihat §5 |
| GAP1:80; ST5; EV1:34; 04-Negative Results:10,66-68 | "trend/momentum NEGATIF, jangan diulang" | satu aturan (SMA24 ± 1 % + ret24, bar 1 jam, 4/24 bar, 20/59 bps, 12 perp); keluarga trend **belum diuji sebagai bot** |
| Concepts/Cost Is Fixed; Thresholds:46; costs.py:13,33-62 | "59 bps; gross harus > 118 bps" | 59 = fee DemoPair; 118 salah turunan (net > 59 butuh gross > 59) |
| README.md:66; F-D69 | "net −45,12 ≈ ongkos 59 bps ≈ 4× efek" | `ret_net` = return − ½-spread buku memecoin (`book_prereg.py:254-255`), bukan 59 bps |
| F-D09; Thresholds:21; direction.py:280-291 | BTCB/WBNB/ETH "bukan aset yang bisa dipilih"; ④⑥ → `seat_eligible=False` | gerbang BSC-token menolak major/RWA secara struktural; butuh status `N/A` per kelas aset |
| GAP1:41,48; GAP4:44,45,49; Fakta Terukur:24,123 | funding historis `TIDAK-ADA`; CEX `MATI`; L2 `TIDAK-ADA` | basi (funding-history.jsonl ada; ⑨ merekam L2; Binance mainnet kini terblokir ISP) |
| C3:19; Project Detail:41 | "posisi tidak bisa lahir dari keputusan yang tidak di-anchor" | kontrak hanya menolak hash nol; pemeriksaan ada di alat dan **tidak menyala** |
| docs/agent-card.json:30; Cheat Sheet:16,22-23,27-30 | "20 bps"; "agen trading"; "dua round-trip" | basi / bertentangan begitu proyek berkata "operator yang trading" |
| (tidak disebut) | 115 perp STOCK, 14 ETF, 11 komoditas di Aster | RWA belum punya kelas aset di [[01-Agent/01 - Asset Classes and Seats]] |

**Doktrin yang tetap:** anchor sebelum hasil; kunci pra-registrasi; gerbang uang nyata F-D16; belum diukur ≠ bersih (tambah
`N/A`); run menang atas halaman; plafon dan rem hanya turun; tanpa custody; string API = input musuh; bayar per keputusan,
gratis saat abstain (NONE). **Set suntingan minimal 12** (F-D70 + banner BN-PIVOT/BN-SKOP + penggaris per venue + status
data bertanggal + kelas aset RWA + klaim publik) tercatat di Inbox, menunggu kata builder.

**Status eksekusi (2 Okt malam; builder: "dicatat dulu dan kalau bisa dikerjakan sekarang").** DIKERJAKAN: (1) F-D70 dan F-D71 + banner BN-PIVOT; (7) banner di START-HERE,
Briefing, Business Process, Ecosystem Positioning, Hub Agent, Claims and Limits, Dashboard; (8) banner di README, Claims Cheat Sheet (+ blok kalimat terlarang), Project
Detail; (2) One-Way Gate hanya diberi banner (isinya belum ditulis ulang). BELUM: (3) tanda NEGATIF per-instance; (4) Cost Is Fixed, `costs.py`, Fakta Terukur §D;
(5) status data bertanggal; (6) kelas aset RWA; (8) `docs/agent-card.json`; (9) halaman `06-Results/30`; (10) banner backlog P31/Epik Alasan Masuk; (11) klaim kontrak;
(12) catatan Conventions. Semua banner aditif: tidak ada kalimat lama yang dihapus (`git diff` pada berkas terlacak: 0 baris dihapus).

## 10. Risiko hukum dan operasional (dibaca peneliti; belum diverifikasi ulang)

- **Aster T&C (2026-02-25):** negara terlarang tidak mencantumkan Indonesia; §6.2(e) melarang bot tanpa izin tertulis; jalur sah =
  API resmi (agent wallet, `approveAgent`).
- **OJK:** UU P2SK mengalihkan pengawasan kripto ke OJK; POJK 27/2024 dan POJK 23/2025; posisi resmi: trading hanya lewat
  pihak berizin OJK (daftar putih 19-12-2025: 26 PAKD; nama yang dilaporkan peneliti antara lain Indodax, Tokocrypto,
  Pintu, Pluang, Upbit, Luno - **daftar lengkap tidak dibaca**, jadi "Binance tidak tercantum" belum terbukti; satu
  media melaporkan Binance di antara platform yang dihentikan, belum diverifikasi). Posisi OJK soal DEX/perp asing dan
  aset ter-tokenisasi: **tidak diketahui**.
- **Pajak PMK 50/2025:** PPh final 1 % untuk transaksi lewat platform asing (0,21 % domestik). Apakah berlaku pada notional
  perp: tidak diketahui - bila berlaku, **lebih besar dari semua edge di halaman ini**.
- **Menembus blokir ISP** (VPN) untuk mengakses platform tak berizin: risiko hukum dan ToS di tangan builder; halaman ini tidak
  menyarankannya. Butuh telaah hukum sebelum uang nyata ([[06-Results/03 - Not Yet Proven]] #10).

## 11. Keputusan yang menunggu builder

1. Venue untuk tahap uang-nyata: Aster saja, atau + Hyperliquid? (Binance mainnet: terblokir dari jaringan ini.)
2. Testnet/paper saja, atau uang nyata kecil setelah F-D16 (dan telaah hukum)?
3. Apakah B4 (event, ekor squeeze) dan B6 (tier C) tetap di enam, atau diganti.
4. Apakah F-D70 + banner (set suntingan minimal) ditulis sekarang.
5. Apakah skrip sesi dipindah menjadi alat di `tools/` (P70).
6. Mesin M1 tinggal di `engine/` (paket baru, stdlib) atau dipindah ke `tools/`? (§14)
7. B2 memakai 7 sub-buku (tanpa pilihan hari) sebagai bawaan? (K1)
8. Bentuk sinyal yang kelak dijual: **target bobot** per penutupan bar (B2 menghasilkan perubahan kecil tiap hari) atau **event
   diskret** (masuk/keluar)? Menentukan seberapa berisik tiruan oleh pengikut ([[06 - Epik Gerbang Sinyal]]).
9. Apakah [[06 - Epik Gerbang Sinyal]] dilanjutkan, dan apakah F-D16 dijadikan syarat menjual apa pun (saran: ya).

**Dijawab builder 2 Okt malam (dicatat di F-D70):** #6 → tetap `engine/`. #7 → ya, 7 sub-buku. #8 → "yang penting open posisi": sinyal = niat posisi (masuk, keluar,
sesuaikan ukuran), bukan jenis order. #9 → dicatat sebagai F-D70, dikerjakan sekarang (banner BN-PIVOT di halaman masuk; `docs/agent-card.json` **belum disentuh**:
ia dibaca mesin dan memuat klaim yang perlu ditinjau terpisah, P76). Pertanyaan hash di Epik 06 §8 #2 → keccak256/ABI/Merkle, sudah diterapkan. Venue → bagian §6 di atas.

## 12. Backlog usulan (belum masuk tabel [[01 - Backlog]])

> Sejak 2 Okt malam semua item ini MASUK [[01 - Backlog]] bagian *Arah operator* dengan status per item; kolom catatan di bawah tidak lagi menjadi tempat status.

| ID | kerja | catatan |
|---|---|---|
| P68 | registry enam bot: satu metode + satu parameter, tes unit, hash | **M1 ada di `engine/`** (2 Okt malam, belum di-commit; §14) → **di-commit dan dipush 2 Okt** (F-D73/F-D74) |
| P69 | penggaris per venue di `tools/costs.py` (fee + ½-spread + dampak + funding); 59 berlabel `demo-AMM` | F-D24 |
| P70 | porting skrip sesi ke `tools/` + satu berkas kunci per bot | menjadikan angka §3 klaim yang sah; sebagian dikerjakan oleh `engine/` (K1-K3 lahir dari sini) |
| P71 | guard umur bar di `direction.py`/bot | temuan: stop MARSCOIN 27 Sep sudah tersentuh 8 jam sebelum anchor. Guard sudah ada di `engine/freshness.py`; **`tools/direction.py` belum diperbaiki** |
| P72 | pemeriksaan ter-anchor yang benar (`execute_live.py:117` tak pernah menyala; vault v2) | `ExecutionVault` hanya menolak hash nol |
| P73 | pipeline event B4: kalender listing/unlock, ketersediaan perp | unlock API berbayar (HTTP 402) |
| P74 | lapisan pemilih + evaluasi (EW/acak/trailing, skor Brier, jeda minimum) | |
| P75 | telaah hukum/ToS sebelum uang nyata (§10) | |
| P76 | suntingan minimal 12 pada klaim yang berbenturan | menunggu builder -> **selesai 3 Okt** (status di [[01 - Backlog]]) |
| P77 | M2 mesin: pengunduh dengan guard umur bar + paper ledger append-only + replay B4 dari event | **dibangun 2 Okt (F-D75..F-D78)**; replay B4 belum |
| P78 | M3 kontrak: `LockRegistry`, anchor sinyal v2 (commit-reveal + akar Merkle), `OperatorGuard` | [[06 - Epik Gerbang Sinyal]] §3; **C-A/C-B ter-deploy chain 97 2 Okt (F-D80); `OperatorGuard` belum** |
| P79 | M4 gerbang: x402 V2 + MCP + webhook/email | [[06 - Epik Gerbang Sinyal]] §4-§5; **setelah** P75 |
| P80 | telaah hukum menjual sinyal (OJK, UU PDP) | bagian dari P75; lebih berat dari trading sendiri |
| P81-P89 | program penerbit bot: `BotRegistry`/`RevenueSplitter`, ~~peninjau agen~~ → peninjau-bot (F-D72: tanpa agen), penghitung percobaan, jalur `method_pr`, ledger shadow, kunci ambang, orkestrator buku, pemeriksa F-D16 | [[07 - Epik Kolaborasi Bot Terbuka]] §11 |

## 13. Batas

- Satu rezim (2020-2026), 16 penyintas, satu sumber harga (Binance), tanpa kunci pra-registrasi; 2025-26 menunjukkan
  peluruhan di B1-B3. Jangan kutip angka halaman ini sebagai "edge".
- B4 mengukur harga **spot** untuk 451 listing; tidak semua punya perp saat itu. Versi perp (106) hanya 20 bulan, satu rezim
  altcoin melemah.
- B5 memakai PAXG sebagai proksi emas; XAUUSDT Aster baru sejak 2025-11.
- Angka literatur dan RWA berasal dari laporan peneliti (tingkat sumber di Inbox); hanya yang ditandai "diukur sendiri"
  yang saya jalankan.

## 14. Mesin M1 (`engine/`, 2 Okt 2026 malam) - kode, bukan klaim

Paket baru di akar repo (**belum di-commit**; `engine/` vs `tools/` ~~menunggu kata builder, §11 #6~~ **dijawab: tetap `engine/` (F-D70)**). Hanya stdlib. Satu jalur kode
untuk replay dan sinyal hidup: bot = fungsi murni `targets(spec, data) -> [Target]`, tanpa keadaan tersimpan.

| berkas | isi |
|---|---|
| `spec.py` | `BotSpec` (satu metode + satu parameter + konstanta terkunci + universe + penggaris); `sha()` = sha256 JSON kanonik, konvensi `tools/direction.py`. Mengubah apa pun = bot baru. `python -X utf8 -m engine.cli specs` mencetak enam sha: **sidik jari hari ini, bukan kunci** |
| `bots/b1…b6` | enam bot murni (B4: target saja; replay B4 menunggu pengunduh event, P73) |
| `sinyal.py` | `Signal` = niat per penutupan bar, bukan order. `id()` = sha kanonik; `commit(salt)` = sha256 dari {sinyal, salt} untuk commit-reveal; `data_hash` = sidik jari seluruh riwayat data yang dipakai; `signals_at()` menolak (`StaleBars`) bila tak ada target tepat pada bar asof |
| `freshness.py` | guard umur bar: bar belum tertutup atau > 12 jam sejak penutupan ditolak |
| `quality.py` | laporan bolong bar (K3) |
| `replay.py`, `report.py` | PnL harian dengan konvensi layar: sinyal di penutupan bar i, posisi untuk return bar i+1, biaya per sisi × turnover, funding nyata |
| `cli.py` | `specs`, `replay`, `emit`, `gaps`; tidak menyentuh jaringan, kunci, atau chain |
| `golden.py` | mencetak ulang semua angka K1-K3, sensitivitas fase B2/B5, dan invarian point-in-time |
| `tests/` | `python -X utf8 -m unittest discover -s engine/tests -t .` (49 tes lulus saat bagian ini ditulis; **pembaruan di bawah**: 169; **174 dicetak ulang 2 Okt, F-D73**; **221 sesudah M2 dan alat anchor, F-D74/F-D75; 239 sesudah P92, F-D76**), termasuk tes yang membuktikan bot yang mengintip bar besok tertangkap |
| `chain.py` | (pembaruan malam) keccak256 murni, `abi.encode` statis, pohon Merkle gaya OpenZeppelin, checksum EIP-55; diuji silang dengan `cast keccak`, `cast abi-encode`, `eth_utils` |
| `submission.py` | (pembaruan malam) skema formulir penerbit tertutup, validasi gagal-tertutup, `to_botspec`, pesan EIP-712 dan pemulihan penanda tangan (butuh `eth-account`) |
| `gates.py`, `slots.py` | (pembaruan malam) gerbang seleksi G1-G11 dan buku sepuluh slot dengan rolling; lihat [[07 - Epik Kolaborasi Bot Terbuka]] |
| `ledger.py` | (M2, F-D75) ledger paper maju: catatan `genesis`/`tick`/`gap`/`settle` berantai-hash, tick EX-ANTE ≤ 12 jam, settle EX-POST lewat `replay()` yang sama dengan gerbang; `python -X utf8 -m engine.cli ledger verify|report` menghitung ulang dari `ledger/bars` |
| `funding_est.py` | (P92, F-D76) rekonstruksi funding Binance dari indeks premium 1 menit: ESTIMASI (MAE 0,056 bps/peristiwa luar-sampel), hanya untuk laporan PROVISIONAL dan target B3; `settle` final tetap dari funding aktual; `engine/data.py` `funding_view` |
| `tools/feed_bars.py`, `tools/paper_tick.py` | (M2, F-D75) pengunduh bar harian + funding (satu-satunya bagian M2 yang menyentuh jaringan) dan runner harian; workflow `.github/workflows/paper-ledger.yml` (dipush 2 Okt; dijalankan sekali manual, run 36987654079, sukses); `tools/anchor_lock.py` (F-D74) |
| `kpi.py`, `review.py`, `locks.py`, `economics.py`, `book.py` | (pembaruan 2 Okt, F-D72/F-D73) KPI K1-K5, peninjau-bot, kunci ambang (**v1 TERKUNCI sementara**; ter-anchor 2026-10-02T08:17:48Z, F-D74; `tools/anchor_lock.py`), bagi hasil 60/40, buku genesis (bot identitas = B1-TREND); riset optimasi ambang: [[08 - Riset Optimasi Ambang]] |

Yang diperiksa dan hasilnya (semua dicetak ulang oleh perintahnya hari ini):
- **Point-in-time:** memotong data di hari D tidak mengubah target hari D (5 hari per bot, 5 bot: identik).
- **Guard basi:** `engine.cli emit --now 2026-10-02T09:00:00Z` pada data yang berhenti 31 Agu → ditolak ("tertutup 753.0 jam lalu"),
  kode keluar 2, tanpa sinyal. `--now 2026-09-01T14:00:00Z` (14 jam setelah penutupan) → ditolak; 3 jam setelah → sah.
- **Lawan rujukan pandas:** K1-K3 di atas; `run10_engine_vs_ref.py`.
- **Catatan desain:** B2 dengan 7 sub-buku mengubah bobot sedikit **tiap hari**: `engine.cli emit --bot ALL --asof 2026-08-31`
  mencetak 7 sinyal B2 (5 `UBAH_BOBOT`, 1 `KELUAR`, 1 `MASUK_SHORT`), 1 sinyal B1, 1 sinyal B3, 0 sinyal B5/B6. Sinyal yang dijual
  berupa target bobot, bukan "buka/tutup" - keputusan §11 #8.
- **Milestone berikut:** M2 (P77) pengunduh + paper ledger; M3 (P78) kontrak; M4 (P79) gerbang. M3/M4 dirancang di
  [[06 - Epik Gerbang Sinyal]].
- **Pembaruan malam (jawaban builder):** komit sinyal kini = keccak256 atas `abi.encode(struct, salt)` + akar Merkle per bot per bar; `engine.cli emit` mencetak baris
  `batch` (akar) dan sinyal (muatan + salt + bukti); `engine.cli verify` = sisi pembeli (diuji: muatan diubah → GAGAL, tanpa traceback). Perintah baru: `gate`,
  `schema`, `intake`. `BotSpec` mendapat field `template` (bot penerbit = varian metode yang ada; sha enam bot awal tidak berubah).

**Terkait:** [[03 - Epik Teori Baru]] · [[04 - Riset Teori (Sitasi)]] · [[02 - Epik Alasan Masuk]] · [[06 - Epik Gerbang Sinyal]] ·
[[09-Inbox/Session-2026-10-02]] · [[00-Overview/03 - Decisions]] · [[06-Results/28 - Venue Kami Bukan Pasar]] ·
[[06-Results/29 - Buku Order, Frame Baru]] · [[Concepts/One-Way Gate]] · [[Conventions]]
