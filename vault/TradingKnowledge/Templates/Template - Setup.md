---
tags: [template, tk]
---

# Template - Setup (TradingKnowledge)

> Dipakai untuk catatan di `04-Setup/`: **resep** yang menggabungkan beberapa metode jadi satu
> keputusan. Catatan setup bukan tempat mendefinisikan ulang metodenya — dia tempat menjawab
> "berapa konfirmasi yang benar-benar independen?".

````markdown
---
tags: [tk, tk-setup, "<ST#>"]
---

# ST# - <Nama setup>

**Keluarga:** [[00 - Hub Setup]]
**Anggota:** [[<S# ...>]] · [[<I# ...>]] · [[<V# ...>]] · [[<FD# ...>]]
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"<nama kombinasi>" *(resep komunitas, bukan hasil uji kami)*

**Ringkas:** 3–5 kalimat: setup ini mencari apa, di aset seperti apa, dan pada horizon berapa.

## Resep

| tahap | aturan | catatan |
|---|---|---|
| bias | <arah dari timeframe besar> | <metode yang memaksa> |
| zona | <di mana harga boleh dibalik> | <OB/FVG/S-R/POC> |
| pemicu | <kapan masuk> | <ChoCH, divergence, retest> |
| invalidation | <level yang membatalkan> | **harus bisa dihitung sebelum masuk** |
| target | <di mana keluar sebagian/habis> | <ekstensi, likuiditas lawan> |
| ukuran | <berapa besar> | lihat [[FD6 - Ukuran Posisi]] — bukan selera |
| keluar waktu | <kapan setup dianggap mati tanpa kena stop/target> | lihat [[FD7 - Invalidation Stop dan Time-Stop]] |

## Butuh data

Tabel status per anggota (enum di [[Aturan Subtree]]). **Satu setup tidak lebih kuat daripada
anggota yang paling tidak bisa diukur**: kalau satu anggota `TIDAK-ADA`, setup-nya belum bisa
dijalankan, apa pun kata resepnya.

## Uji di Fabius

Setup diuji sebagai **satu kesatuan** (bukan tiap anggota dipuji sendiri): event study pada
trigger yang terdefinisi, horizon tetap, ongkos **59 bps** ([[Fakta Terukur]] §D), ambang
`MIN_SAMPLES=20` non-overlap + BH α 0,10 + fold terbaik dibuang.

## Konfluensi atau gaung

Isi wajib. Sebut pasangan anggota yang **mengukur hal yang sama** (mis. dua osilator momentum,
atau "harga di atas EMA" + "EMA miring ke atas"). Konfluensi yang sah = anggota yang datanya
berbeda (harga vs volum vs aliran dompet vs funding). Kalau semua anggota berasal dari deret OHLC
yang sama, jumlah konfirmasi tidak menambah informasi — hanya menambah keyakinan.

## Batas dan mode gagal

<rezim di mana setup ini diam-diam berubah jadi rugi; apa yang terjadi saat likuiditas hilang;
siapa yang menjadi lawan kita di sisi order>

## Tingkat bukti

`T0`–`T3` (+ `NEGATIF` / `TERCEMAR`). Untuk hampir semua setup di folder ini jawabannya jujur:
`T0` — resep komunitas yang belum pernah kami jalankan.

## Boleh dibaca, dilarang dibaca

- **Boleh:** <…>
- **Dilarang:** <"setup X punya win rate tinggi" tanpa n dan tanpa ongkos>

**Terkait:** [[ST7 - Checklist Keputusan]] · [[FD5 - Expectancy Bukan Win Rate]]
````

## Aturan bentuk

- Bagian `## Konfluensi atau gaung` **wajib** — itu satu-satunya bagian yang membedakan catatan
  setup dari brosur.
- Jangan menulis ukuran posisi sebagai persentase modal tanpa menyebut [[FD6 - Ukuran Posisi]]:
  di Fabius yang mengikat adalah plafon kontrak (`dailyCap`, `maxPositionQuote`) — lihat
  [[Fakta Terukur]] §E.
