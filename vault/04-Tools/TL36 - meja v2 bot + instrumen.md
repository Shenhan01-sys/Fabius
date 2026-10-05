---
tags: [perkakas, "TL36", meja, llm, desk]
---

# TL36 - meja v2: AI memilih bot + instrumen, aturan terkunci menentukan arah

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/meja2.py` (`Pasar2`, `arah`, `fitur_aturan`, `nama_fitur`, `prompt2`, `parse2`, `konsensus2`, `posisi`, `siklus2`) · loop gerbang
`meja_loop` + `gabung_v2` + `Gate.data_tunggu` + `Gate.meja_view` di `tools/x402_sinyal.py` · panel v2 di `/desk` (`web/src/components/desk/DeskView.tsx`)
· tes `engine/tests/test_meja2.py` (7) · T8 SK-M6..SK-M10, SK-M14..SK-M17 · keputusan [[00-Overview/03 - Decisions]] F-D110 diubah F-D112 · epik
[[08-Backlog/11 - Epik Meja AI v2]] · backlog P154, P155 · data masukan [[04-Tools/TL35 - data meja v2]] · meja v1 [[04-Tools/TL34 - meja AI 5 menit]]

## Apa

Tiap siklus 5 menit, di samping meja v1 (24 jam berdampingan, lalu v1 dipensiunkan atas laporan pembanding), tiga agent rumah menulis keputusan v2
dalam format baku: `bot` + `skor_bot` keenam bot (-100..100) + `instrumen` (maks 8, tiap entri aset + keyakinan + faktor) + `eksposur` + `veto_aset`
+ `faktor`. AI **tidak** menentukan arah: kode menjalankan aturan bot terkunci (`engine.bots.REGISTRY[bot]`, spec yang sama, universe = instrumen
terpilih) pada candle harian Binance yang sudah tutup, lalu posisi = bobot aturan / max(1, gross aturan) x eksposur, maks 25 % per aset, gross 1x.

## Rumus terkunci (`PARAMS2`, sha ikut di `/desk` sebagai `params_v2_sha`)

- **Universe:** 50 perp USDT teratas menurut volume kuotasi 24 jam (`/fapi/v1/ticker/24hr`, cache 10 menit) + 12 token registry TL35 + BTCUSDT +
  PAXGUSDT. Di luar itu = `ditolak` (SK-M14).
- **Bot dominan:** argmax rata-rata (keyakinan x skor_bot) atas agent sah; pindah bot hanya bila unggul >= 15 poin DAN bot sekarang sudah dipegang
  >= 3 siklus (SK-M8). Kurang dari 2 agent sah = tahan bot + eksposur sebelumnya (SK-M7).
- **Instrumen:** jumlah keyakinan per aset; masuk bila dipilih >= 2 agent atau skor >= 1,2; maks 8.
- **Veto:** >= 2 agent, atau dari data terukur: RugCheck `rug_bahaya` atau likuiditas DEX < 50.000 USD (SK-M9).
- **Rem rugi harian:** buku v2 <= -3 % sejak 00:00 UTC = datar sampai 00:00 UTC (SK-M10).

## Masukan aturan per instrumen (dihitung kode, bukan AI)

`fitur_aturan` membaca candle harian (cache 1 jam, 8 paralel) dan memberi tiap instrumen `tren_60h` (= c / c[-60] - 1, rumus B1), `r_28h` (B2),
`z_10h` (ddof=1, B6), `umur_listing_h` (B4, dari `onboardDate`), `hari_data`. Ditambahkan sesudah uji kering pertama 5 Okt 12:15Z: tanpa masukan ini
ketiga agent menulis "tidak ada fitur 60/28/10 hari" dan semuanya lari ke B5 (instrumennya tetap). Sesudahnya (12:20Z) ketiganya memilih B1 pada
instrumen yang trennya positif (Test Commands #78).

## Kecocokan aturan (SK-M15)

B1/B2/B6 memakai universe -> bisa diterapkan (B2 butuh >= 8 aset); **B3** butuh kaki spot + funding -> meja perp-only = datar dengan alasan; **B4**
hanya untuk perp yang listing <= 14 hari; **B5** terkunci BTC + emas (PAXG perp sebagai proksi spot) -> instrumen pilihan agent diabaikan. Instrumen
yang datar menurut aturan dicatat di `arah_alasan` (contoh: "rule gives flat").

## Waktu dalam siklus

v2 menunggu snapshot data siklusnya sendiri sampai t0+75 s (biasanya ±t0+30 s; kalau belum ada = snapshot terakhir, `data_t` tercatat, SK-M17), lalu
model dibatasi sampai t0+265 s, dihitung SESUDAH data aturan + harga dibaca. v2 bekerja di salinan buku; hasilnya digabung ke rekaman v1 dan masuk
SATU Merkle root yang dikomit ke DeskAnchor. v2 yang belum selesai sebelum komit tidak masuk root dan buku v2 tidak berubah (SK-M16).

## Batas yang dicatat jujur

Hasil meja v2 = strategi baru (universe pilihan AI + aturan terkunci), BUKAN rekam jejak bot harian; uji maju F-D16 tidak disentuh. Aturan harian
dievaluasi tiap 5 menit pada candle harian yang sama, jadi arah biasanya baru berubah sesudah 00:00 UTC; yang bergerak tiap siklus adalah pilihan
bot/instrumen/eksposur. Panggilan model ±2x selama v1 dan v2 berdampingan (model `:free` xkiro bisa kena batas -> `gagal`). Teks publik rekaman v2
berbahasa Inggris (direkam + di-hash apa adanya).
