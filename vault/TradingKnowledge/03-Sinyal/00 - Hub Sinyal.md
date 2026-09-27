---
tags: [tk-sinyal, hub]
---

# 00 - Hub Sinyal

**Sumber:** `vault/TradingKnowledge/03-Sinyal/`

Tiga puluh delapan metode, satu catatan per metode, satu bentuk per catatan. Keluarga inilah yang
diminta `Plan.txt` ("sebutkan semua metode trading crypto") — tapi tiap halaman di sini menjawab
pertanyaan yang tidak diminta oleh daftar itu: **dengan data apa metode ini bisa diuji oleh kami,
dan apa yang sudah kami ukur tentangnya?**

Jawaban yang paling sering muncul adalah `TIDAK-ADA`, dan itu bukan kecelakaan: sebagian besar
perkakas analisis pasar lahir di dunia yang punya order book, tick, dan histori tahunan — sedangkan
lapangan kami adalah token yang berumur hitungan jam di chain yang harganya kami catat sendiri.
Peta lengkap statusnya: [[GAP1 - Matriks Metode x Tahap]] dan
[[GAP4 - Yang Tidak Bisa Diuji Karena Data]].

## Bagian

### Struktur dan price action — semuanya dari satu deret OHLC

- [[S1 - Candlestick dan Price Action Murni]] — bentuk bar tunggal dan kombinasinya; apa yang bisa
  didefinisikan tanpa ambang tersembunyi
- [[S2 - Chart Patterns]] — kepala-pundak, double top, segitiga, bendera; deteksi otomatis vs mata
- [[S3 - Market Structure BOS dan ChoCH]] — swing high/low yang bisa dihitung; fondasi keluarga SMC
- [[S4 - Order Block dan Breaker]] — contoh mutu subtree ini: geometri jelas, klaim penyebab kabur
- [[S5 - Fair Value Gap]] — imbalance tiga bar; frekuensi penutupan tanpa mistik
- [[S6 - Likuiditas Stop Hunt dan Inducement]] — di mana stop menumpuk secara struktural, dan kapan
  narasi "buruan stop" tidak bisa dibantah
- [[S7 - Fibonacci Retracement dan Extension]] — rasio, grid yang padat, dan uji terhadap level acak
- [[S8 - Wyckoff]] — akumulasi/distribusi, spring, upthrust; skema yang berguna vs skema yang
  selalu cocok
- [[S9 - Elliott Wave dan Harmonic]] — dua keluarga yang kami perlakukan `T0`: alasannya tertulis

### Indikator — turunan dari harga yang sama

- [[I1 - Moving Average]] — SMA/EMA/WMA, lag sebagai harga smoothing; aturan arah kita sudah diuji
  dan **rugi**
- [[I2 - RSI dan Divergence]] — rumus Wilder, ambang, dan kenapa divergensi butuh definisi pivot
- [[I3 - MACD]] — dua EMA yang berpura-pura jadi informasi baru
- [[I4 - Bollinger Bands]] — pita deviasi, squeeze, "walking the band"
- [[I5 - Ichimoku Cloud]] — lima komponen, satu deret; kapan awan berarti "tidak tahu"
- [[I6 - ATR dan Jarak Ternormalisasi]] — jarak, bukan arah; penting karena kandidat kita harganya
  berbeda enam orden
- [[I7 - VWAP dan Anchored VWAP]] — harga rata-rata berbobot volum; anchor adalah tuas overfit

### Volum dan order flow — yang paling banyak dijanjikan, paling sedikit tersedia

- [[V1 - Konfirmasi Volum dan Money Flow]] — OBV/CMF/MFI; wash trading sebagai racun volum di BSC
- [[V2 - Volume Profile dan POC]] — profil dari tick vs histogram dari bar; bedanya bukan gaya
- [[V3 - CVD Delta dan Footprint]] — butuh sisi agresor; tidak ada jalur L2/tick di repo ini
- [[V4 - Order Book dan Liquidity Heatmap]] — lapisan order, kedalaman, spoofing
- [[V5 - Mikrostruktur Spread dan Adverse Selection]] — pajak bagi yang tahu lebih sedikit; sisi
  kami di meja ini

### Turunan dan futures — satu-satunya bidang on-chain-ish yang benar-benar kita punya

- [[U1 - Open Interest]] — kontrak terbuka bukan posisi long; live `ADA`, histori `TIDAK-ADA`
- [[U2 - Funding Rate dan Basis]] — carry sebagai biaya, yield, dan veto yang sudah wired
- [[U3 - Level Likuidasi dan Cascade]] — mekanisme riil, data yang tidak bisa kita baca
- [[U4 - Long-Short Ratio dan Skew Posisi]] — rasio akun vs rasio USD, dan siapa yang sebenarnya
  diukur

### On-chain dan dompet — lapangan kerja kita sendiri

- [[O1 - Exchange Inflow dan Outflow]] — definisi, tafsiran yang lemah, dan apa yang dibutuhkan
- [[O2 - MVRV SOPR dan NUPL]] — valuasi bersejarah; tidak terdefinisi untuk token berumur tiga hari
- [[O3 - Stablecoin Supply dan Likuiditas Dolar]] — amunisi, mint/burn, bridge
- [[O4 - Active Addresses dan Pemakaian Gas]] — alamat bukan manusia; kita punya bukti sendiri
- [[O5 - Whale dan Kohor Smart Money]] — catatan terpenting di subtree ini: kohor harus per-kolam,
  panel vendor tercemar, dan alat skor kita belum bisa dipercaya
- [[O6 - Konsentrasi Holder Bundler dan LP Lock]] — satu-satunya keluarga on-chain yang sudah jadi
  ambang di `tools/`, tapi ambangnya diputuskan, bukan diuji
- [[O7 - Token Unlock dan Vesting]] — tekanan yang diantisipasi, bukan yang mengejutkan
- [[O8 - MEV dan Sandwich]] — kerugian yang tidak muncul di laporan mana pun milik kita

### Narasi dan sentimen — datang belakangan, hanya boleh mengurangi

- [[M1 - Fear and Greed dan Indeks Sentimen]] — agregat yang bisa dibuat tanpa informasi baru
- [[M2 - Sentimen Sosial dan Ekstraksi LLM]] — kapan model membaca teks berguna, dan kontrol
  negatif yang wajib ada
- [[M3 - Narasi Sektar dan Rotasi]] — korelasi yang menyamar sebagai wawasan
- [[M4 - Catalyst dan Event Trading]] — listing, kemitraan, mainnet; edge yang sudah diharga
- [[M5 - Makro dan Korelasi Silang-Pasar]] — DXY, likuiditas global, dan korelasi yang naik saat stres

## Terkait

- [[00 - Hub Trading Knowledge]] · [[Aturan Subtree]] · [[Fakta Terukur]] · [[Glossary-TK]]
- [[04-Setup/00 - Hub Setup]] — kombinasi; [[06-Bukti/00 - Hub Bukti]] — cara menilai klaimnya
- [[03-Data/D3 - Price Depth]] · [[03-Data/D2 - Wallet Flow]] · [[01-Agent/01 - Asset Classes and Seats]]

```dataview
LIST FROM #tk-sinyal SORT file.name ASC
```
