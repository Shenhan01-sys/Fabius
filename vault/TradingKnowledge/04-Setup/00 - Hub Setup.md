---
tags: [tk-setup, hub]
---

# 00 - Hub Setup

**Sumber:** `vault/TradingKnowledge/04-Setup/` · daftar kombinasi aslinya dari
`vault/TradingKnowledge/Plan.txt` §"Kombinasi Paling OP (Siap Pakai)"

Resep yang menggabungkan beberapa metode jadi satu keputusan. Folder ini justru yang paling
berbahaya di subtree ini, karena kombinasi mudah terdengar lebih ilmiah daripada satu metode —
padahal lima konfirmasi yang semuanya berasal dari deret harga yang sama bukan lima informasi,
melainkan satu informasi diucapkan lima kali. Karena itu tiap catatan setup di sini **wajib** punya
bagian `## Konfluensi atau gaung`.

Status jujurnya: tidak ada satu pun setup di folder ini yang pernah dijalankan Fabius sebagai
kesatuan. Yang punya bahan paling lengkap adalah setup terakhir.

## Bagian

- [[ST1 - All-Rounder]] — struktur HTF + SMC + Fibonacci + volume profile + risk; resep "paling
  direkomendasikan" dari transkrip, dibedah asumsi konfluensinya
- [[ST2 - Futures Hunter]] — struktur + liquidity grab + OI + funding + heatmap likuidasi + CVD;
  mayoritas anggotanya `TIDAK-ADA` di repo ini
- [[ST3 - Clean Price Action]] — BOS/ChoCH + order block + Fibonacci + MTF; setup termurah data,
  tersisa satu deret OHLC
- [[ST4 - Range dan Mean Reversion]] — POC + ekstrem range + divergensi; setup yang berubah jadi
  mesin rugi saat rezim berganti
- [[ST5 - Trend Rider]] — tren HTF + pullback + volum + trailing; satu-satunya keluarga yang arah
  garis besarnya **sudah kami uji dan rugi**
- [[ST6 - Aliran On-Chain Fabius]] — setup yang bahannya benar-benar kita rekam sendiri: arah +
  kohor dompet per-kolam + filter keamanan + kapasitas keluar + ongkos terukur
- [[ST7 - Checklist Keputusan]] — satu halaman yang harus bisa dijawab mesin sebelum menerbitkan
  keputusan; baris yang tidak terjawab ditandai sebagai lubang, bukan dihapus

## Terkait

- [[00 - Hub Trading Knowledge]] · [[03-Sinyal/00 - Hub Sinyal]] · [[Fakta Terukur]]
- [[FD5 - Expectancy Bukan Win Rate]] · [[FD6 - Ukuran Posisi]] · [[FD7 - Invalidation Stop dan Time-Stop]]
- [[EV2 - Jebakan Backtest]] · [[01-Agent/A3 - One-Way Gates]]

```dataview
LIST FROM #tk-setup SORT file.name ASC
```
