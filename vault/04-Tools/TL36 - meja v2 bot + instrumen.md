---
tags: [perkakas, "TL36", meja, llm, desk]
---

# TL36 - meja v2: AI memilih bot + instrumen, aturan terkunci menentukan arah

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/meja2.py` (`Pasar2`, `arah`, `fitur_aturan`, `nama_fitur`, `prompt2`, `parse2`, `konsensus2`, `posisi`, `siklus2`) · loop gerbang
`meja_loop` + `gabung_v2` + `Gate.data_tunggu` + `Gate.meja_view` di `tools/x402_sinyal.py` · panel v2 di `/desk` (`web/src/components/desk/DeskView.tsx`)
· tes `engine/tests/test_meja2.py` (12) · T8 SK-M6..SK-M10, SK-M14..SK-M17, SK-M19..SK-M22 · keputusan [[00-Overview/03 - Decisions]] F-D110 diubah F-D112 · epik
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

## Kursi aktif / uji (P160, F-D113)

Maks 7 kursi **aktif** + 3 kursi **uji**; state di `_v2_kursi` buku meja (ikut `buku.json`). `kursi_daftar`: agent yang ada saat state kursi masih
kosong = aktif (agent awal), agent baru = uji, kursi uji penuh = `antre` (tidak dijalankan, tanpa biaya model, SK-M19). Agent uji tetap menjawab, rekamannya
di-hash + dikomit dan bukunya hidup, tetapi suaranya tidak masuk konsensus (SK-M20). `kursi_catat` menyimpan jendela 288 siklus (jawaban sah 1/0 +
ekuitas buku v2). `kursi_evaluasi` hanya di siklus 00:00 UTC (SK-M21): turun bila sah < 80 % (SK-M22); naik bila >= 288 siklus di kursi uji, sah >= 95 %
dan hasil jendela >= median aktif; bila 7 aktif penuh, tukar dengan aktif terburuk (yang sudah >= 288 siklus) hanya bila unggul >= 0,5 pp. Tiap
perubahan = rekaman `kursi` (peristiwa + kursi sekarang + `params_kursi_sha`) di Merkle root siklus itu. `PARAMS_KURSI` DIKUNCI 5 Okt malam
(sha `0xf370c011…`, Decisions F-D113). Ambang konsensus `ambang(n_aktif)`: kuorum max(2, ceil(n/2)), instrumen + veto max(2, ceil(n/3)) agent, skor instrumen
0,4 n - untuk n = 3 sama persis dengan nilai v1 (2 / 2 / 1,2). Lantai `/desk`: meja uji berlabel TRIAL / UJI, kursi lav-2, kabel ke hub redup tanpa
denyut (suaranya belum mengalir); Rules menampilkan ambang untuk n aktif sekarang + aturan kursi.

**Koreksi 5 Okt malam (PARAMS2 v2):** instrumen konsensus kini hanya dari agent yang memilih bot AKHIR; tanpa pemilih + bot ditahan = instrumen siklus
lalu. Ditemukan di produksi 16:25Z dan 16:30Z: B2-RS ditahan hysteresis (B5 unggul 30,0 / 27,7 poin tetapi baru dipegang 1-2 siklus) sementara
instrumennya BTC + PAXG pilihan agent B5 -> aturan B2 (butuh >= 8 aset) datar, buku v2 diam. Tercatat di [[00-Overview/05 - Corrections]].

**Koreksi 6 Okt (PARAMS2 v3 `0x7e3b37f1…`):** bot akhir dengan `min_aset` (B2-RS: 8) diisi skor tertinggi pemilih bot itu sampai minimum; pilihan agent B2 dengan < 8 instrumen dicatat di `ditolak`. Ditemukan di siklus produksi 16:55Z ([[00-Overview/05 - Corrections]]).

**Agent dinonaktifkan + keputusan kursi builder (6 Okt):** agent `nonaktif` di config kehilangan kursinya (`keluar`, SK-M23) dan antrean naik; `analis.py kursi --slug <s> --ke aktif|uji|antre --alasan "..."` menulis keputusan builder ke `kursi_builder` yang diterapkan sekali oleh gerbang dan dikomit sebagai peristiwa `kursi` (SK-M24). Dipakai pertama untuk F-D114.

**Penamaan (F-D115):** di web meja ini = "Fabius" (tanpa "v2"), revisi rumus ditulis r1/r2/r3 (= `PARAMS2.v`); buku per agent = "Rapor agent". Meja v1 tidak ditampilkan (`V1_TAMPIL = False`), mesinnya masih berjalan sampai builder memutuskan.

## Replay perputaran (P163)

`GET /desk/arsip/<YYYY-MM-DD>` (`Gate.meja_arsip`, baca saja): rekaman konsensus Fabius (agent `v2`, lengkap: bot, target, isi, ekuitas, dasar) + harga isi v2 per siklus (`harga_v2` dari berkas siklus) untuk satu hari UTC - isinya sudah publik lewat `/desk` + `/desk/proof`, hanya dikumpulkan. `python -X utf8 tools/meja_replay.py --dari <tgl> --sampai <tgl>`: (1) fee TERCATAT dipecah per sebab tiap isi (ganti bot > rem rugi > instrumen masuk/keluar > balik arah > ubah ukuran); (2) replay `meja.isi` yang sama pada target aturan per siklus + harga tercatat; kebijakan r3 harus mengulang ekuitas tercatat (bukti replay setia) sebelum kebijakan lain dibandingkan. Kebijakan hanya mengubah target sebelum diisi (aturan bot tidak disentuh): `pita_ukuran` (posisi searah tidak diubah bila selisih < 50 % ukurannya), `lekat_instrumen` (instrumen yang hilang dari pilihan tetap dipegang n siklus, bot sama), `jeda` (ubah posisi tiap >= n siklus kecuali ganti bot / rem). Rem rugi harian (SK-M10) dihitung ulang dari ekuitas replay. **Batas replay:** siklus yang tercatat datar karena rem tidak menyimpan target aturan, jadi tetap datar di semua kebijakan; sampel ±1 hari - kebijakan dipilih menurut prinsip biaya, bukan dicocokkan ke sampel.

## Batas yang dicatat jujur

Hasil meja v2 = strategi baru (universe pilihan AI + aturan terkunci), BUKAN rekam jejak bot harian; uji maju F-D16 tidak disentuh. Aturan harian
dievaluasi tiap 5 menit pada candle harian yang sama, jadi arah biasanya baru berubah sesudah 00:00 UTC; yang bergerak tiap siklus adalah pilihan
bot/instrumen/eksposur. Panggilan model ±2x selama v1 dan v2 berdampingan (model `:free` xkiro bisa kena batas -> `gagal`). Teks publik rekaman v2
berbahasa Inggris (direkam + di-hash apa adanya).
