---
tags: [tk, tk-sinyal, "U3"]
---

# U3 - Level Likuidasi dan Cascade

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"1. Analisis Teknikal Lanjutan & Variasi"
("Liquidation Levels & liquidation cascade hunting") + §"3. CONFIRMATION LAYER" (Liquidation
Heatmap) — klaim komunitas + vendor

**Ringkas:** Likuidasi adalah penutupan paksa oleh venue ketika margin tidak lagi menutup posisi;
cascade adalah efek dominonya: penutupan paksa menekan harga, yang memicu penutupan paksa
berikutnya. Mekanismenya nyata dan penting. Tapi klaim yang dijual di `Plan.txt` — bahwa kita bisa
mengetahui **di harga berapa** cascade akan terjadi — menuntut satu benda yang tidak kami punya dan
mungkin tidak bisa dibeli: distribusi posisi nyata seluruh pasar beserta aturan margin tiap venue.
Di repo ini seluruh keluarga ini `TIDAK-ADA`.

## Definisi yang bisa dihitung

```
# satu posisi long dengan leverage L, margin awal M, maintenance margin rate m:
harga_bankrupt_long  ≈ entry × (1 - 1/L + m)
harga_likuidasi_long = fungsi venue dari (entry, size, L, m, buffer, oracle/mark price)
# cascade = proses umpan-balik:
#   likuidasi -> order jual dipaksa (taker) -> harga turun -> posisi lain kena harga_likuidasi -> ...
# "level likuidasi agregat di harga X" = SUM qty posisi yang harga_likuidasinya di sekitar X.
#   Butuh: distribusi (entry, leverage, ukuran) per posisi. Tidak ada satu pun venue yang
#   memublikasikannya; angka vendor adalah **model** dari sampel likuidasi yang mengalir keluar,
#   bukan daftar posisi orang.
```

## Cara pakai yang diklaim

Baca "ada likuiditas $Y di bawah harga" sebagai magnet harga, hindari entry tepat di atas kluster,
atau entry justru **mengarah** ke kluster — liquidity grab, lihat
[[S6 - Likuiditas Stop Hunt dan Inducement]] — dan pasang stop di luar zona kluster supaya tidak
ikut tersapu. Klaimnya berasal dari
platform penjual heatmap dan praktisi; tidak ada sumber primer di repo ini.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| level & kluster likuidasi (heatmap) | `TIDAK-ADA` | disebut eksplisit di daftar "yang tidak kami punya sama sekali" — [[Fakta Terukur]] §C |
| aliran likuidasi kejadian (stream) | `TIDAK-ADA` | tidak ada jalur di repo; venue yang biasanya menyediakannya ada di daftar mati: `api.binance.com` → `451 restricted location`, Bybit → `403 CloudFront country` (§C) |
| distribusi leverage / entry harga pasar | `TIDAK-ADA` | tidak publik di venue mana pun yang kita punya |
| aturan maintenance margin + tiering venue kita | `TIDAK-ADA` | tidak direkam; tanpanya kita sendiri tidak bisa menghitung harga likuidasi posisi kita (§C) |
| harga mark & oracle saat ini | `ADA-TAPI` | `markPrice` ikut dibaca `tools/direction.py` (§A) — satu nilai spot per baca, bukan deret |
| proxy kerumunan searah | `ADA-TAPI` | funding + OI (§A) memberi **tekanan**, bukan **level harga** |
| riwayat likuidasi jalur nyata kita | `TIDAK-ADA` | jalur nyata adalah pool demo di chain 97 (§D/§F); tidak ada likuidasi venue yang pernah terjadi di sana untuk diukur |

## Uji di Fabius

Tidak bisa. Ini halaman keluarga U yang paling jujur jatuh ke
[[GAP4 - Yang Tidak Bisa Diuji Karena Data]]: prediksinya ("cascade di harga X") berbentuk klaim
tentang distribusi yang tidak bisa diperiksa dari clone ini, jadi tidak ada run yang bisa
menaikkannya di atas `T0`. Yang **bisa** dibuat dan murah secara konseptual: catat peristiwa
pergerakan ekstrem di aset ber-perp kita dari kline yang sudah ada (`tools/bars.py`, 9.599 bar §A),
lalu periksa **setelah** kejadian apakah funding/OI saat itu berbeda — itu uji asosiasi prospektif
pada data yang kami punya, dan itu **bukan** uji level likuidasi. Jangan menjualnya sebagai yang
kedua. Ambang penilaian tetap sama: `n >= 20` non-overlap, ongkos **59 bps** (§D), BH α 0,10 (§E).

## Batas dan mode gagal

- **Narasi yang tidak bisa dibuktikan salah bukan sinyal.** "Likuiditas $800 juta menunggu di
  bawah sana" dari vendor tidak punya aturan falsifikasi yang bisa kita jalankan; kalau harga tidak
  ke sana, penjelasannya selalu tersedia (heatmap-nya diperbarui, levelnya "sudah terserap").
- **Arah kausal mudah terbalik.** Kluster likuidasi besar sering **hasil** dari pergerakan, bukan
  penyebabnya: harga yang sudah turun memaksa likuidasi yang tercatat di deret.
- **Level likuidasi kita sendiri tidak kami ketahui.** Tanpa maintenance margin venue, rencana
  stop ([[FD7 - Invalidation Stop dan Time-Stop]]) tidak bisa dibandingkan dengan harga likuidasi —
  jadi kalimat "stop kita di luar zona likuidasi" belum bisa ditulis di produk ini.
- **Risiko sebenarnya di jalur kita bukan likuidasi venue**, tapi penolakan keluar di likuiditas
  tipis ([[FD3 - Likuiditas dan Dampak Harga]]) — yang sudah punya bentuk aturan:
  `exit-size <= 1 % liq` dan time-stop 24 jam ([[01-Agent/01 - Asset Classes and Seats]]).

## Tingkat bukti

`T1` untuk mekanisme likuidasi bertingkat dan umpan-baliknya (fakta struktur produk derivatif) ·
`T0` untuk semua klaim lokasi ("cascade akan terjadi di harga X") dan semua angka heatmap · untuk
Fabius: **tidak teruji** — tidak ada satu pun berkas di `tools/` yang menyentuh kata likuidasi.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami paham mekanismenya dan tahu persis data apa yang hilang untuk memilikinya;
  sampai data itu ada, klaim lokasi likuidasi tidak kami pakai sama sekali."
- **Dilarang:** "Fabius menghindari zona likuidasi" · mengutip angka heatmap vendor sebagai data
  terukur · menyebut funding/OI tinggi sebagai "level likuidasi" · membaca penurunan tajam sebagai
  "bukti cascade" tanpa satu pun catatan likuidasi.

**Terkait:** [[U1 - Open Interest]] · [[U2 - Funding Rate dan Basis]] ·
[[U4 - Long-Short Ratio dan Skew Posisi]] · [[V4 - Order Book dan Liquidity Heatmap]] ·
[[S6 - Likuiditas Stop Hunt dan Inducement]] · [[GAP4 - Yang Tidak Bisa Diuji Karena Data]]
