---
tags: [tk, referensi]
---

# Glossary-TK

**Sumber:** istilah yang hidup di catatan `TradingKnowledge/` · dipakai supaya satu kata tidak punya
dua arti antar-halaman

Satu baris per istilah: artinya, lalu halaman yang memikulnya. Tidak ada penjelasan panjang di sini
— kalau sebuah istilah butuh paragraf, tempatnya di catatan sendiri, dan baris ini harus menunjuk ke
sana. Istilah yang **tidak** kami pakai sengaja tidak didaftar.

## Struktur dan price action

| istilah | arti singkat | halaman |
|---|---|---|
| market structure | susunan high/low yang naik atau turun (HH-HL / LH-LL) | [[FD1 - Struktur Pasar dan Rezim]] |
| BOS | Break of Structure — level ekstrem ditembus, tren berlanjut | [[S3 - Market Structure BOS dan ChoCH]] |
| ChoCH | Change of Character — pelanggaran pertama yang mengubah arah | [[S3 - Market Structure BOS dan ChoCH]] |
| SMC | Smart Money Concept — keluarga aturan zona/likuiditas, bukan bukti | [[03-Sinyal/00 - Hub Sinyal]] |
| ICT | varian SMC dengan istilah sendiri; satu keluarga dengan baris di atas | [[S4 - Order Block dan Breaker]] |
| order block | candle berlawanan terakhir sebelum impuls | [[S4 - Order Block dan Breaker]] |
| breaker | zona yang kebobolan lalu dibaca dari sisi sebaliknya | [[S4 - Order Block dan Breaker]] |
| FVG / imbalance | celah tiga bar yang tidak terisi lawan | [[S5 - Fair Value Gap]] |
| liquidity grab / stop hunt | pergerakan ke tumpukan stop lalu berbalik | [[S6 - Likuiditas Stop Hunt dan Inducement]] |
| inducement | gerbang palsu yang memancing entry sebelum zona sejati | [[S6 - Likuiditas Stop Hunt dan Inducement]] |
| premium / discount | separuh atas/bawah dari ayunan yang dipilih | [[S7 - Fibonacci Retracement dan Extension]] |
| spring / upthrust | palsu ke bawah/atas dalam skema Wyckoff | [[S8 - Wyckoff]] |
| harmonic / Elliott | keluarga pola berbasis rasio & hitungan gelombang | [[S9 - Elliott Wave dan Harmonic]] |

## Indikator dan jarak

| istilah | arti singkat | halaman |
|---|---|---|
| SMA / EMA / WMA | rata-rata bergerak (sederhana, eksponensial, berbobot) | [[I1 - Moving Average]] |
| RSI | osilator kekuatan relatif, 0–100 | [[I2 - RSI dan Divergence]] |
| divergence | harga membuat ekstrem baru, osilator tidak | [[I2 - RSI dan Divergence]] |
| MACD | selisih dua EMA + garis sinyal | [[I3 - MACD]] |
| Bollinger Bands | SMA ± k · deviasi standar | [[I4 - Bollinger Bands]] |
| Ichimoku | lima garis + "awan" dari dua yang digeser | [[I5 - Ichimoku Cloud]] |
| ATR | rata-rata true range; ukuran jarak, bukan arah | [[I6 - ATR dan Jarak Ternormalisasi]] |
| VWAP | harga rata-rata berbobot volum sejak sesi dibuka | [[I7 - VWAP dan Anchored VWAP]] |
| anchored VWAP | VWAP dari satu titik yang dipilih tangan | [[I7 - VWAP dan Anchored VWAP]] |

## Volum, order flow, turunan

| istilah | arti singkat | halaman |
|---|---|---|
| OBV / CMF / MFI | garis volum kumulatif dan varian uang-masuk | [[V1 - Konfirmasi Volum dan Money Flow]] |
| POC / VAH / VAL | harga dengan volum terbanyak; batas atas/bawah area nilai | [[V2 - Volume Profile dan POC]] |
| HVN / LVN | simpul volum tinggi/rendah | [[V2 - Volume Profile dan POC]] |
| CVD / delta | selisih volum agresif beli vs jual yang diakumulasikan | [[V3 - CVD Delta dan Footprint]] |
| footprint | trades per level harga per interval | [[V3 - CVD Delta dan Footprint]] |
| L2 / order book | lapisan kuotasi bid-ask | [[V4 - Order Book dan Liquidity Heatmap]] |
| adverse selection | rugi karena lawanmu tahu sesuatu | [[V5 - Mikrostruktur Spread dan Adverse Selection]] |
| maker / taker | penyedia likuiditas vs pemakan likuiditas | [[V5 - Mikrostruktur Spread dan Adverse Selection]] |
| OI | open interest — kontrak terbuka, bukan posisi long | [[U1 - Open Interest]] |
| funding rate | pembayaran antar sisi perpetual untuk menempel ke spot | [[U2 - Funding Rate dan Basis]] |
| basis | selisih harga futures/perp terhadap spot | [[U2 - Funding Rate dan Basis]] |
| liquidation cascade | likuidasi bertingkat yang memicu likuidasi baru | [[U3 - Level Likuidasi dan Cascade]] |
| long/short ratio | rasio akun (bukan USD) yang posisi searah | [[U4 - Long-Short Ratio dan Skew Posisi]] |

## On-chain dan dompet

| istilah | arti singkat | halaman |
|---|---|---|
| exchange inflow / outflow | transfer ke/dari dompet bursa | [[O1 - Exchange Inflow dan Outflow]] |
| MVRV | nilai pasar dibagi nilai perolehan (realized) | [[O2 - MVRV SOPR dan NUPL]] |
| SOPR | profit ratio saat output dihabiskan | [[O2 - MVRV SOPR dan NUPL]] |
| NUPL | untung/rugi belum terealisasi agregat | [[O2 - MVRV SOPR dan NUPL]] |
| SSR | perbandingan stablecoin terhadap kapitalisasi BTC | [[O3 - Stablecoin Supply dan Likuiditas Dolar]] |
| active addresses | alamat unik yang bertransaksi — bukan manusia | [[O4 - Active Addresses dan Pemakaian Gas]] |
| whale | dompet besar; "besar" harus disebut satuannya | [[O5 - Whale dan Kohor Smart Money]] |
| smart money (versi vendor) | label penyedia data, bukan hasil uji kami | [[O5 - Whale dan Kohor Smart Money]] |
| kohor | kelompok dompet untuk satu kolam, bukan panel global | [[O5 - Whale dan Kohor Smart Money]] |
| top-10 concentration | share supply di sepuluh alamat teratas | [[O6 - Konsentrasi Holder Bundler dan LP Lock]] |
| bundler | satu pengendali berpakaian banyak alamat | [[O6 - Konsentrasi Holder Bundler dan LP Lock]] |
| LP lock | likuiditas yang dikunci supaya tidak bisa ditarik | [[O6 - Konsentrasi Holder Bundler dan LP Lock]] |
| honeypot | token yang bisa dibeli tapi tidak bisa dijual | [[O6 - Konsentrasi Holder Bundler dan LP Lock]] |
| cliff / vesting | jadwal pelepasan token | [[O7 - Token Unlock dan Vesting]] |
| MEV / sandwich | nilai yang diambil dari urutan transaksi orang lain | [[O8 - MEV dan Sandwich]] |
| bidang ⑦ | nama kami untuk rekaman aliran dompet sendiri | [[03-Data/D2 - Wallet Flow]] |

## Sentimen, narasi, dan cara uji

| istilah | arti singkat | halaman |
|---|---|---|
| Fear & Greed | indeks komposit sentimen publik | [[M1 - Fear and Greed dan Indeks Sentimen]] |
| narrative / sektor rotation | aliran perhatian ke tema (AI, RWA, DePIN, meme) | [[M3 - Narasi Sektar dan Rotasi]] |
| catalyst | peristiwa terjadwal atau tidak (listing, unlock, mainnet) | [[M4 - Catalyst dan Event Trading]] |
| lookahead | memakai informasi yang belum ada saat keputusan dibuat | [[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]] |
| point-in-time | data yang membeku seperti keadaannya saat itu | [[03-Data/D5 - Record Schemas]] |
| survivorship | sampel yang hanya berisi yang masih bertahan | [[EV2 - Jebakan Backtest]] |
| walk-forward | validasi bergulir di luar sampel | [[QT4 - Overfitting dan Validasi]] |
| OOS | out-of-sample — di luar data yang dipakai menyetel | [[EV3 - Signifikansi dan Multiple Testing]] |
| BH-FDR | koreksi banyak tes (Benjamini–Hochberg), α 0,10 di kami | [[EV3 - Signifikansi dan Multiple Testing]] |
| bootstrap | distribusi nol dengan mensampel ulang data yang ada | [[EV3 - Signifikansi dan Multiple Testing]] |
| expectancy | rata-rata tertimbang hasil per trade **setelah ongkos** | [[FD5 - Expectancy Bukan Win Rate]] |
| Kelly / vol targeting | aturan ukuran posisi | [[FD6 - Ukuran Posisi]] |
| time-stop | keluar karena umur posisi, bukan karena harga | [[FD7 - Invalidation Stop dan Time-Stop]] |
| tingkat bukti `T0`–`T3` | siapa yang menguji, dan di data siapa | [[EV1 - Tingkat Bukti]] |
| konfluensi vs gaung | konfirmasi dari sumber berbeda vs sumber sama diulang | [[04-Setup/00 - Hub Setup]] |

**Terkait:** [[00 - Hub Trading Knowledge]] · [[Aturan Subtree]] · [[Fakta Terukur]] ·
[[Quick-Reference]] (alamat, hash, dan angka produk — bukan istilah)
