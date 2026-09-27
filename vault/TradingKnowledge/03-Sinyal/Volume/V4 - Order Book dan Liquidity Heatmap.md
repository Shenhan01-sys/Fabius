---
tags: [tk, tk-sinyal, "V4"]
---

# V4 - Order Book dan Liquidity Heatmap

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"1. Analisis Teknikal Lanjutan & Variasi"
("Liquidity Heatmap (dari platform seperti Hyblock, Coinglass, dll)", "Order Flow & Footprint
Charts") — klaim komunitas + nama vendor, tanpa sumber primer

**Ringkas:** Buku order (L2) adalah daftar harga dan antrian yang **siap** dieksekusi; heatmap
likuiditas adalah riwayatnya, ditumpuk menurut waktu. Bedanya dengan OHLCV mendasar: yang satu
mencatat niat, yang lain mencatat apa yang benar-benar terjadi. Ini keluarga sinyal paling
 informatif di pasar terpusat dan keluarga yang paling **kosong** di repo ini: tidak ada satu pun
jalur L2, tidak ada riwayat antrian, tidak ada level likuidasi. Yang kami punya cuma kurva AMM
milik sendiri — dan di sana tidak ada antrian sama sekali.

## Definisi yang bisa dihitung

```
# dari snapshot L2 pada waktu t:
bid_depth(p_lo..p_hi)  = sum qty di sisi bid dalam rentang harga
ask_depth(p_lo..p_hi)  = sum qty di sisi ask
imbalance(w)           = (bid_depth(w) - ask_depth(w)) / (bid_depth(w) + ask_depth(w))
spread                 = best_ask - best_bid
# heatmap = Matriks(t, p) dari ask_depth/bid_depth pada setiap rekaman t   <- butuh Kumpulan rekaman
# level likuidasi (versi vendor): harga tempat posisi pada leverage L kena
#   maintenance margin; dihitung dari **distribusi leverage pasar** yang tidak publik,
#   jadi angka vendor = model mereka, bukan pengukuran.
```

`imbalance` dari **satu** snapshot tidak bisa dibedakan dari spoofing. Yang membedakan adalah
riwayat: order yang hilang sebelum harga mendekati = niat palsu; itu persis alasan benda ini harus
direkam terus-menerus, bukan diambil sekali saat butuh.

## Cara pakai yang diklaim

Tebok likuiditas di bawah/atas kluster order besar; hindari entry saat sisi kita kosong; baca
"absorption" saat dinding ask bertahan; heatmap dipakai untuk meramalkan arah cascade
([[U3 - Level Likuidasi dan Cascade]]). Klaimnya milik vendor yang menjual heatmap-nya dan
praktisi order-flow; di repo ini tidak ada satu pun artefak yang mengujinya.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| snapshot L2 (bid/ask depth) | `TIDAK-ADA` | daftar "yang tidak kami punya sama sekali" membuka dengan order book L2 — [[Fakta Terukur]] §C |
| riwayat antrian (bahan heatmap) | `TIDAK-ADA` | tidak ada perekam buku order; dan tidak bisa disusulkan (lihat "Batas") |
| level & kluster likuidasi | `TIDAK-ADA` | "heatmap likuidasi" disebut eksplisit di §C |
| kedalaman **venue yang jalurnya hidup di jaringan kita** | `TIDAK-ADA` | Hyperliquid ada di daftar jalur-hidup-dua-jaringan §C, tapi repo ini hanya memakai `candleSnapshot` + `metaAndAssetCtxs` — belum ada satu pun panggilan kedalaman yang diukur |
| kedalaman venue publik besar | `MATI-DARI-MESIN-INI` | terukur di **runner**: `api.binance.com` → `451 restricted location`, Bybit → `403 CloudFront country` (§C). Endpoint kedalamannya sendiri belum pernah dicoba dari laptop, jadi ini pasangan sumber×jaringan yang belum lengkap |
| "kedalaman" di venue eksekusi kita | `ADA-TAPI` | pool kami x·y=k dengan fee 30 bps (§D): kedalamannya kurva, bukan antrian — dampak harga langsung terhitung, tidak ada spoofing, tidak ada queue |

## Uji di Fabius

Tidak ada yang bisa diuji dari clone ini — ini halaman keluarga V yang jatuh ke
[[GAP4 - Yang Tidak Bisa Diuji Karena Data]]. Berapa harga memiliki-nya, dan ini perkiraan
biayanya (bukan angka hasil ukur): **bukan** bandwidth atau disk, tapi **jam tembakan yang bisa
dijamin**.
Heatmap = matriks rekaman; satu jam bolong = satu kolom hilang, dan kolom itu tidak bisa ditarik
mundur. Pelajaran itu sudah kami bayar mahal di bidang ⑦: server mengabaikan parameter paging,
sehingga "yang lewat = hilang" ([[Fakta Terukur]] §B, [[03-Data/D2 - Wallet Flow]]), sementara
pemicu Actions di repo ini terukur **tidak bisa dijadwalkan sebagai jaminan**
([[01-Agent/01 - Asset Classes and Seats]]). Menambah satu perekam buku order = menambah satu
deret yang bolongnya akan dibaca orang sebagai deret utuh. Rekomendasi yang jujur: **jangan**
dibangun untuk hackathon ini; vendor berbayar memindahkan masalah ke uang dan ke ketergantungan
pada model orang lain.

## Batas dan mode gagal

- **Niat bisa ditarik gratis.** Sinyal L2 paling kuat justru yang paling cepat berubah; dari
  snapshot tunggal yang bisa dibaca sebagai "tebok" bisa dibaca sebagai "dinding yang tidak ada
  niatnya berdiri di sana".
- **Heatmap vendor bukan pengukuran.** Ia model distribusi leverage milik penerbitnya; memakai
  angkanya lalu menyebutnya "data" adalah pencucian klaim (aturan `T0` di [[Aturan Subtree]]).
- **AMM tidak punya buku order.** Memakai bahasa L2 (bid, ask, queue, spoof) untuk kolam x·y=k
  adalah salah kategori; bahasa yang benar ada di [[V5 - Mikrostruktur Spread dan Adverse Selection]].
- **Deret yang tampak utuh lebih berbahaya dari yang bolong.** Pola ini sudah tercatat di vault:
  metadata provenance yang salah lebih buruk daripada kosong (catatan `save()` di `tools/bars.py`).

## Tingkat bukti

`T1` untuk mekanisme L2/heatmap sebagai bahasa pasar terpusat (standar, tidak teruji oleh kami) ·
`T0` untuk klaim prediktif "heatmap memprediksi arah" dan untuk semua angka vendor · untuk Fabius:
**tidak dapat diuji** — `TIDAK-ADA` di baris paling banyak dibanding catatan keluarga V lain.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "order flow L2 adalah keluarga sinyal yang belum bisa kami miliki; blocker-nya
  perekaman berkelanjutan yang bisa dijamin, bukan analisis."
- **Dilarang:** "Fabius melihat kedalaman likuiditas" · menyebut heatmap vendor sebagai data
  terukur · menyamakan likuiditas pool (USD di kurva) dengan kedalaman buku order · menjual
  "liquidity grab" dari heatmap yang tidak kami punya ([[S6 - Likuiditas Stop Hunt dan Inducement]]).

**Terkait:** [[V3 - CVD Delta dan Footprint]] · [[V5 - Mikrostruktur Spread dan Adverse Selection]] ·
[[U3 - Level Likuidasi dan Cascade]] · [[FD3 - Likuiditas dan Dampak Harga]] ·
[[GAP4 - Yang Tidak Bisa Diuji Karena Data]] · [[03-Data/D2 - Wallet Flow]]
