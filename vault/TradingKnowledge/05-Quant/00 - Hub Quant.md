---
tags: [tk-quant, hub]
---

# 00 - Hub Quant

**Sumber:** `vault/TradingKnowledge/05-Quant/` · daftar topiknya dari
`vault/TradingKnowledge/QuantTrading/Info1.txt` (transkrip, bukan sumber fakta)

Cara mengubah sebuah ide trading jadi sesuatu yang bisa dimatikan. Fabius **adalah** proyek quant
dalam bentuk paling telanjang: keputusan kami harus bisa dihitung ulang dari rekaman, dan hasilnya
harus bisa membuktikan bahwa kami salah. Folder ini adalah rumah bagi aturan itu — plus daftar
jujur tentang strategi quant yang **tidak** bisa kami mainkan (arbitrase dua kaki, market making,
strategi CEX) dan mengapa bukan karena kami belum mau.

Yang sudah benar-benar berjalan di repo: `tools/backtest.py` (400 hari × 12 aset, ambang diimpor
bukan di-fit) dan `tools/ledger.py`. Yang sudah berjalan itu **menghasilkan vonis negatif** —
lihat [[Fakta Terukur]] §F.

## Bagian

- [[QT1 - Dari Ide ke Strategi yang Bisa Diuji]] — mengubah "kalau X maka beli" jadi aturan
  deterministik + null hypothesis + ukuran sampel
- [[QT2 - Backtesting yang Jujur]] — asumsi fill, biaya, non-overlap, walk-forward; yang sudah kami
  punya dan yang tidak
- [[QT3 - Data Fitur dan Label]] — fitur vs label vs horizon, kebocoran, dan normalisasi lintas aset
  yang harganya berbeda enam orden
- [[QT4 - Overfitting dan Validasi]] — parameter vs sampel, data snooping, kontrol acak, dan aturan
  kami: ambang tidak disetel setelah melihat hasil
- [[QT5 - Statistical Arbitrage dan Pairs Trading]] — korelasi vs kointegrasi, spread & half-life;
  syarat yang tidak bisa kita penuhi
- [[QT6 - Funding dan Basis Arbitrage]] — cash-and-carry, delta-netral, dan kenapa "yield funding"
  bukan angka bebas risiko
- [[QT7 - Market Making]] — spread vs adverse selection, risiko inventaris; dan kenyataan bahwa
  venue demo kami adalah sisi lawan dari meja ini
- [[QT8 - Machine Learning untuk Trading]] — SNR rendah, purging/embargo, non-stationarity; status
  Fabius: tidak ada satu pun model terlatih di repo
- [[QT9 - LLM sebagai Pembaca Narasi]] — peran sah model: mengekstrak & memveto di bawah data,
  bukan meramal harga; kontrol negatif wajib
- [[QT10 - Eksekusi Algoritmik]] — TWAP/VWAP/iceberg/SOR; kenapa notional sekecil kita tetap butuh
  batas kapasitas keluar, bukan penjadwalan
- [[QT11 - Portofolio Strategi]] — korelasi antar-strategi, alokasi risiko, dan aturan mematikan
  aturan yang edge-nya mati
- [[QT12 - Stack Data dan Perkakas]] — apa yang benar-benar hidup dari mesin ini (terukur), pustaka
  mana yang pengetahuan umum tapi belum diverifikasi

## Terkait

- [[00 - Hub Trading Knowledge]] · [[06-Bukti/00 - Hub Bukti]] · [[Fakta Terukur]] §A/§C
- [[04-Tools/TL7 - measurement harness]] · [[04-Tools/TL5 - ledger]] · [[03-Data/D4 - Dune]]
- [[01-Agent/A2 - Decision Spine]] — tahap yang memakai hasil folder ini

```dataview
LIST FROM #tk-quant SORT file.name ASC
```
