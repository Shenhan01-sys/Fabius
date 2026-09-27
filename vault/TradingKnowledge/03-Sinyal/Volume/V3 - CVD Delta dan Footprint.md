---
tags: [tk, tk-sinyal, "V3"]
---

# V3 - CVD Delta dan Footprint

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"3. CONFIRMATION LAYER (Lapisan Konfirmasi)"
(CVD / Delta Volume / Footprint) — klaim komunitas; §"20 Metode..." menyebutnya "melihat siapa yang
lebih agresif", dan itulah klaim yang belum bisa kami penuhi

**Ringkas:** Delta = volum agresor beli dikurangi agresor jual; CVD = akumulasi delta. Nilainya
datang dari satu hal yang tidak ada di bar OHLCV: **sisi agresor tiap transaksi**. Footprint
memecah delta itu per harga per bar. Keduanya menjawab pertanyaan yang bagus — siapa yang memaksa
harga bergerak — dan di repo ini keduanya tidak punya bahan bakunya. Catatan ini menamai
**pendekatan termurah yang masih bisa dihitung dari bar** dan menuliskan dengan jelas bahwa
pendekatan itu **bukan delta**.

## Definisi yang bisa dihitung

```
delta(t) = V_buy_aggressor(t) - V_sell_aggressor(t)      # butuh klasifikasi per print
CVD(t)   = CVD(t-1) + delta(t)
# klasifikasi yang dipakai venue tick: harga print == ask -> beli; == bid -> jual
# (uptick/downtick rule = varian lama; dua-duanya butuh barisan print, bukan satu bar)

# --- YANG BISA dihitung dari bar, dan namanya bukan delta ---
up_vol(t)   = v(t) jika close[t] >= open[t] else 0       # seluruh volum dicap "beli"
range_vol(t)= v(t) * (close[t]-low[t])/(high[t]-low[t])  # bobot posisi close dalam range
delta_bar   = 2*up_vol - v(t)  # HANYA sahih bila satu-satunya transaksi di bar itu searah
```

`delta_bar` adalah **label yang ditempel dari tanda candle**, bukan hasil klasifikasi. Dua bar
dengan delta asli berbeda bisa memberi `delta_bar` yang sama, dan satu bar dengan harga naik bisa
sepenuhnya digerakkan penjual yang panik di sisi bid.

## Cara pakai yang diklaim

Divergensi CVD-vs-harga dibaca sebagai penyerapan (harga naik tapi CVD turun = seller limit
menyerap); footprint dipakai untuk melihat level tempat delta membalik; diklaim sebagai inti
"order flow" dan pasangan tetap [[V4 - Order Book dan Liquidity Heatmap]]. Klaimnya milik praktisi
order-flow dan vendor datanya; tidak ada rujukan di repo ini.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| riwayat print + sisi agresor (tick) | `TIDAK-ADA` | "footprint/tick" tidak kami punya sama sekali — [[Fakta Terukur]] §C |
| delta per bar 1 jam | `TIDAK-ADA` | tidak ada jalur klasifikasi sisi di repo |
| volum beli-agresor per bar yang **sudah dikirim tapi dibuang** | `ADA-TAPI` | pemetaan kolom di `tools/bars.py` mencatat baris mentah `[openTime, o, h, l, c, volume, closeTime, quoteVol, trades, takerBase, takerQuote, ignore]`, tapi cache hanya menyimpan `t,o,h,l,c,v,n` — kolom taker dibuang |
| arti pasti kolom `takerBase`/`takerQuote` di venue ini | `TIDAK-ADA` | konvensi yang diharapkan belum divalidasi silang ke sumber kedua — *(belum diukur)* |
| footprint per harga | `TIDAK-ADA` | butuh tick **dan** bucket harga; dua-duanya belum ada |

## Uji di Fabius

Dua langkah, dan langkah pertama belum selesai:

1. **Perbaiki bahan baku, lalu buktikan artinya.** Simpan kolom taker di cache
   (`tools/bars.py`), lalu uji identitas yang harus berlaku: `0 <= takerBase <= volume` setiap bar,
   dan `sum(takerQuote)/sum(quoteVol)` berada di rentang yang masuk akal. Kalau identitasnya sudah
   benar, `delta_bar2 = 2*takerBase - v` adalah delta **agregat per bar** — bukan footprint.
   Perintah validasi ini belum ditulis.
2. **Baru uji klaimnya.** Event study divergensi (harga vs delta_bar2) dengan arah acak sebagai
   kontrol (aturan kontrol di [[Fakta Terukur]] §B); `n >= 20` non-overlap, gross di atas
   **59 bps** (§D), drop-best-fold, BH α 0,10 (§E).

## Batas dan mode gagal

- **Menempel label "CVD" pada angka dari candle** adalah mode gagal utamanya, dan ia mudah sekali
  terjadi karena grafiknya terlihat sama. Yang membedakan bukan tampilan, tapi apakah ada
  klasifikasi agresor.
- **Agregat per bar menyembunyikan struktur.** Bar 1 jam dengan +50 delta bisa terdiri dari
  pembelian agresif di awal dan penyerahan di akhir — justru bagian yang ingin dibaca order flow.
- **Kolom taker milik venue, bukan milik kebenaran.** Kalau Aster mengisi kolom itu dengan
  konvensi berbeda (atau nol), seluruh turunan di atas terlihat valid dan kosong isinya —
  pola kegagalan yang sama dengan `UNMEASURED` yang dibaca bersih ([[Concepts/Unmeasured Is Not Clean]]).
- **CVD tidak menambah informasi kalau hanya dipakai sebagai penanda arah** — ia akan berkorelasi
  dengan return bar itu sendiri (definisi `up_vol` memakai close vs open). Uji kolinearitas dulu.
- Order flow asli lahir di venue terpusat dengan buku order; memakainya di kolam AMM
  (x·y=k) adalah kategori yang salah — di sana "kedalaman" adalah kurva ([[V5 - Mikrostruktur Spread dan Adverse Selection]]).

## Tingkat bukti

`T1` untuk mekanismenya (klasifikasi agresor = praktik standar di venue tick) · `T0` untuk klaim
prediktif divergensi CVD di memecoin (tanpa sumber) · untuk Fabius: **belum ada bahan bakunya**,
jadi tidak ada tingkat apa pun selain "belum bisa diuji".

## Boleh dibaca, dilarang dibaca

- **Boleh:** "delta per bar bisa didekati dari kolom taker yang sudah dikirim venue tapi kami buang
  di `tools/bars.py`; sampai kolom itu disimpan dan artinya divalidasi, kami tidak punya delta."
- **Dilarang:** menyebut `up_vol`/`range_vol` sebagai CVD · "Fabius membaca order flow" ·
  "divergensi CVD memprediksi reversal" · mengklaim footprint dari data bar.

**Terkait:** [[V2 - Volume Profile dan POC]] · [[V4 - Order Book dan Liquidity Heatmap]] ·
[[V5 - Mikrostruktur Spread dan Adverse Selection]] · [[V1 - Konfirmasi Volum dan Money Flow]] ·
[[QT3 - Data Fitur dan Label]] · [[Concepts/Unmeasured Is Not Clean]]
