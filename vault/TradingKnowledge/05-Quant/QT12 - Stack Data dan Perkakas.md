---
tags: [tk, tk-quant, "QT12"]
---

# QT12 - Stack Data dan Perkakas

**Keluarga:** [[00 - Hub Quant]] · **Tahap:** fetching ([[PL1 - Mengumpulkan Data]])
**Sumber:** [[Fakta Terukur]] §A/§C/§H (satu-satunya sumber angka) · `vault/03-Data/D3 - Price Depth.md` ·
`vault/03-Data/D4 - Dune.md` · `vault/04-Tools/TL7 - measurement harness.md` ·
`vault/TradingKnowledge/QuantTrading/Info1.txt` §"Tech Stack" (daftar topik, bukan verifikasi)

**Ringkas:** catatan praktis: apa yang benar-benar bisa kami baca dari mesin ini, dengan kunci apa,
sedalam apa, dan atas syarat apa. Yang mudah tertukar: **sumber yang hidup** dan **sumber yang bisa
dipakai membuktikan sesuatu**. Dan "hidup" adalah properti **pasangan** sumber × jaringan, bukan sifat
sumber: sumber yang sama membalas `200` di runner dan terpotong TLS di laptop (§C).

## Definisi yang bisa dihitung

Cara memeriksa sebuah jalur data, supaya kesimpulannya bukan dari satu respons:

```
hidup     := meminta deret PANJANG dan mendapat baris yang tuntas (paging + meta sha256), bukan HTTP 200
berguna   := kedalamannya >= ambang uji (NEED_BARS=2400) ATAU dia memang jalur point-in-time
saksi-waktu := barisnya tidak bisa di-update retro (Dune punya `_updated_at` -> statistik, bukan saksi)
terpasang := ada di `tools/` dan bisa dijalankan dari clone; selain itu = belum ada
```

Setiap baris wajib membawa tanggal baca; "ADA" yang tidak dicabut sebulan bukan fakta, itu kebiasaan ([[Aturan Subtree]]).

## Cara pakai yang diklaim

Klaim pemilik praktik (roadmap di `Info1.txt` §"Rekomendasi Mulai"): kuasai Python + Pandas + CCXT,
backtest dengan vectorbt atau Freqtrade, ambil data gratis dari Binance, tambah on-chain dari tier
gratis Glassnode/CryptoQuant. Tidak ada satu pun langkah itu yang kami verifikasi di mesin ini —
`CCXT`, `pandas`/`numpy`, `vectorbt`, `freqtrade`, `nautilus_trader`, `qlib`, `TA-Lib` berstatus
**pengetahuan standar, belum diverifikasi di mesin ini**: belum dipasang, belum dicoba, tidak ada
klaim versi atau hasil. Yang benar-benar kami pakai dan bisa diulang dari clone: tarik deret panjang
dengan paging jujur dan cache bermeta (`tools/bars.py`), saring universe (`tools/screen_universe.py`),
rekam aliran **sebelum** hasilnya ada (`universe/record_wallet_flow.py`), ukur (`tools/backtest.py`,
`tools/winlog.py`, `tools/ledger.py`), buktikan jejaknya (`tools/anchor.py --verify`).

## Butuh data

Terukur dan dibaca 28 Sep 2026 ([[Fakta Terukur]] §A/§C):

| sumber | apa yang diberikan | kedalaman / isi | kunci |
|---|---|---|---|
| Aster `fapi/v1/klines` | OHLCV perp BNB-native | 9.599 bar 1 j ≈ 400 hari; **1.500 bar/panggilan**, sisanya paging (limit besar ditolak `code -1130`) | tanpa API key |
| Aster `premiumIndex`/`openInterest` | funding + OI | 608 kontrak (`Meme` 61, `AI` 42), funding per 4 jam | tanpa key |
| Hyperliquid `candleSnapshot` / `metaAndAssetCtxs` | OHLCV + funding/OI, chain sendiri | 5.001 bar ≈ 208 hari; 234 perp | tanpa key |
| GMGN `token_kline`, `user/smartmoney`, `user/kol` | deret per token + aliran dompet | mentok 1.000 bar ≈ 41,6 hari, 0 bar token gas; aliran 100 tx/panggilan, jendela 8–13 menit | privat (demo key melayani rute aliran) |
| GeckoTerminal / DexScreener / GoPlus | universe, likuiditas, keamanan | 1.000 bar; pool baru ±30 bar | demo/privat |
| CoinGecko | trending & referensi | bukan deret untuk uji | tanpa key; kuota tier kami *(belum diukur)* |
| Berkas GDELT | tema + nada artikel | jalur berkas mentah yang hidup dari mesin ini (§C) — bukan deret harga | tanpa key |
| Dune | riwayat transaksi + agregat aliran | `dex.trades` BSC; **lag ±1 jam**; kredit terbaca; dialek **Trino** | API key + kredit |

Yang `TIDAK-ADA` sama sekali (§C): order book L2, tick/footprint, heatmap likuidasi, histori funding
per aset yang bisa ditarik mundur, jadwal unlock/vesting, MVRV/SOPR/NUPL, exchange reserve. Yang
`MATI-DARI-MESIN-INI` per jaringan (§C): `api.binance.com` → `451 restricted location` dan Bybit →
`403 CloudFront country` di runner; OKX funding dan Bitget contracts `200` di runner tapi **terpotong
TLS di laptop**. Sumber yang disebut roadmap (data.binance.vision, CryptoQuant, Glassnode, Kaiko,
Tardis) tidak pernah diverifikasi dari repo ini: *(belum diukur)* — dan "berbayar" tidak otomatis
berarti "cukup".

## Uji di Fabius

Perintah untuk memeriksa ulang tabel di atas, bukan mempercayainya:

```
python -X utf8 tools/bars.py BNBUSDT --days 300     # deret panjang + paging + meta
python -X utf8 tools/bars.py --list                 # apa yang benar-benar ter-cache
python -X utf8 tools/backtest.py --horizon 4        # apakah kedalamannya cukup untuk diuji
python -X utf8 tools/winlog.py                      # keadaan hasil (blok ini basi dalam hitungan jam)
```

Kalau server memotong limit: turunkan limit, lanjut paging — bukan menyimpulkan datanya tidak ada (`tools/bars.py`).

## Batas dan mode gagal

- **Hidup hari ini ≠ bisa direproduksi.** Jalur tanpa kunci bisa berubah kebijakan, jalur privat punya
  kuota tak terukur, dan status tidak ikut berpindah kalau proyek pindah perangkat. Satu respons juga
  bukan kematian: kesimpulan "mati" wajib menyebut kode, body, dan riwayat.
- **Data mahal ≠ data sah.** Dune menjawab pertanyaan sejarah, bukan pertanyaan "kapan kami tahu"
  ([[Concepts/Point-in-Time vs Retro-updatable]]).
- **Alat dengan satuan salah lebih berbahaya daripada tidak ada alat:** distribusi
  `tools/maker_ledger.py` belum masuk akal (§H) dan alatnya sendiri mencetak rem.

## Tingkat bukti

`T1` untuk daftar pustaka umum (pengetahuan standar, belum diverifikasi di mesin ini) · keadaan jalur
data kami sendiri terukur langsung (§A/§C, tanggal baca 28 Sep 2026) — tidak ada metode di catatan ini
yang sudah diuji, jadi tidak ada `T3` · `T0` untuk kalimat "sudah terpasang".

## Boleh dibaca, dilarang dibaca

- **Boleh:** "empat sumber tanpa API key memberi kami deret 400 hari + funding/OI live + aliran dompet
  point-in-time; Dune memberi sejarah dengan lag ±1 jam; CEX besar mati atau terpotong tergantung
  jaringan; belum ada pustaka quant umum yang kami verifikasi di mesin ini."
- **Dilarang:** "stack data kami lengkap" · "CCXT/vectorbt dipakai Fabius" · "tinggal beli Glassnode"
  · mengutip §G/§H sebagai hasil (blok itu angka yang basi atau angka alat yang rusak).

**Pertanyaan terbuka sebelum catatan ini naik tingkat:** apa yang perlu kami **pasang** supaya metode
yang hari ini `TIDAK-ADA` benar-benar terbuka — tick/L2 untuk [[QT7 - Market Making]] dan
[[V4 - Order Book dan Liquidity Heatmap]]; histori funding/OI untuk [[QT6 - Funding dan Basis Arbitrage]]
dan [[U1 - Open Interest]]; unlock/vesting untuk [[O7 - Token Unlock dan Vesting]]; jalur MEV untuk
[[O8 - MEV dan Sandwich]]; dan pustaka mana (kalau ada) yang memotong kerja, bukan menambah nama README?

**Terkait:** [[QT2 - Backtesting yang Jujur]] · [[QT3 - Data Fitur dan Label]] · [[QT9 - LLM sebagai Pembaca Narasi]]
· [[GAP4 - Yang Tidak Bisa Diuji Karena Data]] · [[GAP5 - Urutan Kerja dan Bayarnya]] · [[03-Data/D4 - Dune]]
