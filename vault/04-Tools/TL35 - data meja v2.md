---
tags: [perkakas, "TL35", meja, data]
---

# TL35 - data luas meja v2 (pengumpul + fitur terukur)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/meja_data.py` (`REGISTRY`, `registry_sha`, `f_binance`, `pasangan_terbaik`, `f_dex`, `f_rug`, `f_fomo`, `f_berita`, `f_bot`, `zskor`,
`Pengumpul`) · loop `data_loop` + endpoint `/desk/data` di `tools/x402_sinyal.py` · panel kesehatan data di `/desk` · tes
`engine/tests/test_meja_data.py` (5) · T8 SK-M4, SK-M5 · keputusan [[00-Overview/03 - Decisions]] F-D110 · epik [[08-Backlog/11 - Epik Meja AI v2]] §3 ·
backlog P153

## Apa

Tonggak F1 meja v2: Fabius sendiri membaca Binance (klines 5m, premiumIndex, openInterestHist, takerlongshortRatio), DexScreener (`tokens/v1` batch
per alamat), RugCheck (Solana), FOMO API (leaderboard 24h + thesis), dan berita (`tools/kabar.py`), lalu mengubahnya menjadi fitur terukur per aset
dan per bot. Tiap batas 5 menit UTC +20 s satu snapshot -> `/data/meja/fitur/<tgl>.jsonl` (sha atas isi tanpa `durasi_s`). Belum dibaca agent (F2).

## Registry alamat (dikunci, `registry_sha`)

12 token on-chain dengan perp Binance: PEPE, WIF, BONK, POPCAT, PNUT, TRUMP, FARTCOIN, MOODENG, FLOKI, SHIB, PENGU, BRETT. Alamat dari CoinGecko
`platforms` (5 Okt), chain = rantai likuiditas utama, `kali` = pengali kontrak (1000PEPE dll.). Pencarian simbol tidak dipakai: "WIF" di DexScreener
mengembalikan token tiruan di chain lain (diukur 5 Okt). Pasangan DEX dipilih menurut alamat base token = alamat registry, likuiditas terbesar.

## Anggaran per sumber (detik cache)

Binance ekstra 290 · DexScreener 290 · RugCheck 3.600 · FOMO leaderboard 7.200 · FOMO thesis 28.800 · berita 900. FOMO butuh `FOMO_API_KEY` di
layanan yang menjalankan (Railway `fabius-x402`); tanpa kunci = status "tanpa kunci", cakupan 0, tidak dikarang.

## Batas yang dicatat jujur

Gagal baca = fitur `None` (bukan "aman"/nol); z-score baru ada sesudah >= 30 titik riwayat (riwayat di memori proses, mulai dari nol tiap restart);
RugCheck hanya Solana; fitur `oi_ubah_1j`/`taker_beli_jual` hanya untuk 16 aset mayor + aset target bot (anggaran panggilan Binance).
