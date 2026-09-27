---
tags: [tk, tk-quant, "QT5"]
---

# QT5 - Statistical Arbitrage dan Pairs Trading

**Keluarga:** [[00 - Hub Quant]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/QuantTrading/Info1.txt` §"Bedah strategi statistical arbitrage" /
§"Strategi Quant yang Populer di Crypto" — daftar topik, **bukan** hasil · ambang:
[[Fakta Terukur]] §A/§C/§E · `vault/06-Results/02 - Thresholds.md` (`STABLE_BASES`)

**Ringkas:** dua harga yang bergerak bersama bukan berarti selisihnya akan menutup. Pairs trading
yang benar bergantung pada **kointegrasi** (kombinasi linier keduanya stasioner), bukan korelasi,
dan uangnya diambil dari konvergensi selisih itu. Catatan ini menyimpan rumusnya supaya bisa
diuji dengan bar yang kami punya — dan sekaligus mencatat bahwa **uji yang lengkap tidak bisa
dijalankan di repo ini**, karena kaki pendeknya tidak punya jalur eksekusi dan penangkapan selisih
butuh book yang tidak bisa kami baca.

## Definisi yang bisa dihitung

```
spread_t   := log(p_A[t]) - beta * log(p_B[t])        # beta dari estimasi in-sample yang DIBEKUKAN
z_t        := (spread_t - mean_w) / std_w             # jendela w tetap, hanya baris <= t
entry      := |z_t| >= z_in                           # dua kaki dibuka bersamaan
exit       := |z_t| <= z_out   atau  t + H  (waktu)    # atau |z_t| >= z_stop (konvergensi gagal)
half_life  := ln(2) / (-ln(phi))   dari AR(1): dspread = (phi-1)*spread + eps
```

| istilah | apa yang sebenarnya diuji | jebakan |
|---|---|---|
| korelasi | apakah keduanya naik bersama | dua aset yang berkorelasi 0,9 bisa menjauh permanen |
| kointegrasi | apakah **selisih ternormalisasi** kembali (diklaim literatur: uji Engle–Granger / Johansen — tidak kami reproduksi) | hasilnya tergantung jendela dan urutan data; dua jendela berbeda = dua jawaban |
| half-life | berapa lama konvergensi rata-rata terjadi | dipakai **menentukan** `H`; kalau `H` dipilih setelah hasil, ini tuas overfit |
| z-score | kapan masuk/keluar | `mean_w`/`std_w` yang dihitung di seluruh sejarah = lookahead |

## Cara pakai yang diklaim

Klaim pemilik praktik (penelitian akademik dan dana relatif-value; bentuk yang paling sering
dijual ke ritel adalah "spread melebar 2 simpangan, buka dua kaki"): edge-nya kecil, frekuensinya
tinggi, dan sumber keuntungannya adalah konvergensi, bukan arah pasar. Untuk crypto, pasangan yang
lazim disebut adalah stablecoin ↔ stablecoin, wrapped ↔ aslinya (BTCB/WBTC), dan dua L1 yang
bergerak bersama. Semua itu **klaim pendukungnya**, bukan apa yang kami setujui — dan edge kelas
ini menyebar cepat: begitu banyak pihak menghitung z-score yang sama, sisa selisihnya hilang sebelum
kaki kedua terisi.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| bar 1 jam dua kaki untuk aset ber-kontrak perp | `ADA` | Aster 9.599 bar ≈ 400 hari untuk BNB/ETH/SOL/DOGE/HYPE dkk — §A |
| kaki **pendek** yang bisa dieksekusi | `TIDAK-ADA` | tidak ada jalur pinjam-aset/short di repo ini; pairs tanpa kaki kedua = spekulasi arah berganti nama |
| order book L2 / harga bid-ask sungguhan | `TIDAK-ADA` | §C — konvergensi tipis tidak bisa ditangkap tanpa tahu sisi mana yang terisi |
| histori funding kedua kaki | `TIDAK-ADA` | §C; carry adalah bagian dari PnL pairs, bukan catatan kaki |
| kandidat mayor/peg sebagai pasangan | `ADA-TAPI` | `STABLE_BASES` menolak USDT/USDC/BUSD/FDUSD/DAI/TUSD/USD1/USDD/USDE + BTCB/WBNB/BNB/ETH sebagai **aset yang bisa dipilih** (`vault/06-Results/02 - Thresholds.md`) — pasangan paling "bersih" justru bukan kandidat |
| ongkos dua kaki | `ADA-TAPI` | satu round-trip di venue kami **59 bps** terukur (§D); empat kaki untuk dua round-trip → kami belum pernah mengukur angka itu *(belum diukur)* |

## Uji di Fabius

Yang bisa dihitung hari ini dan **belum** dihitung: matriks `half-life` dan z-score untuk pasangan
ber-kontrak perp, dengan beta dan jendela dibekukan lebih dulu, lalu dilaporkan **sebagai statistik
deskriptif** — bukan sebagai strategi, karena kaki pendeknya tidak ada.

Perintah yang dibutuhkan: `tools/pairs_study.py` — **belum ditulis**. Bentuk uji yang sah sesudah
itu: pra-registrasi (`vault/06-Results/05 - Pre-registration Flow.md`), `n >= 20` non-overlap, BH
α 0,10, fold terbaik dibuang (§E), dan gross di atas ongkos **4 kaki**, bukan 2.

Yang tidak boleh dilakukan: menyamakan "spread kami kembali" dengan "strategi kami untung". Tanpa
kaki kedua dan tanpa book, kembali-nya spread tidak bisa dibeli siapa pun.

## Batas dan mode gagal

- **Regime break dibayar sebagai mean-reversion.** Kointegrasi di 400 hari bukan jaminan di 30 hari
  berikutnya; [[FD1 - Struktur Pasar dan Rezim]] berlaku dua kali lipat di sini.
- **Risiko kaki tunggal.** Kalau hanya satu kaki yang bisa diisi, "pairs" berubah jadi arah — dan
  arah sudah kami uji: rugi di 12/12 setelah ongkos (§F).
- **Edge menyebar cepat.** Ini kelas strategi yang hasilnya bergantung pada tidak ada orang lain
  yang menghitung hal yang sama; venue ritel crypto adalah tempat paling ramai untuk itu.
- **Pasangan di universe kami bukan pasangan institusi.** 608 kontrak perp (§A) berisi meme dan
  L1; hubungan fundamental BTCB/WBTC tidak bisa kita pakai sebagai kandidat karena screener kami
  sendiri menolaknya sebagai aset yang bisa dipilih.
- **Duplikasi sinyal:** z-score pairs dan [[S4 - Order Block dan Breaker]] sama-sama mengukur
  "harga menyimpang lalu kembali"; kalau keduanya masuk, itu satu ide dihitung dua kali.

## Tingkat bukti

`T1` untuk kerangka kointegrasi/z-score (pengetahuan standar pasar) · `T2` untuk uji formal
kointegrasi yang namanya disebut di literatur dan tidak kami reproduksi · untuk Fabius:
**belum diuji sama sekali** — tidak ada satu pun baris di `tools/` yang menghitung spread dua
aset, dan kaki pendeknya tidak tersedia (`T0` untuk setiap kalimat yang menyiratkan sebaliknya).

## Boleh dibaca, dilarang dibaca

- **Boleh:** "Fabius bisa menghitung spread dan half-life antara dua aset ber-kontrak perp dari bar
  miliknya sendiri, tapi tidak bisa memperdagangkan pasangan itu karena tidak punya kaki pendek,
  tidak punya order book, dan tidak punya histori funding."
- **Dilarang:** "kami menjalankan stat-arb" · "pairs trading low-risk karena market-neutral"
  (netral terhadap arah ≠ netral terhadap risiko kaki) · "stablecoin pair = yield gratis".

**Terkait:** [[QT6 - Funding dan Basis Arbitrage]] · [[QT7 - Market Making]] ·
[[FD10 - Korelasi dan Risiko Keranjang]] · [[U2 - Funding Rate dan Basis]] ·
[[O6 - Konsentrasi Holder Bundler dan LP Lock]] · [[PL3 - Menganalisis]]
