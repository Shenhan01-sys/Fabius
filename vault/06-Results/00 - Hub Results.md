---
tags: [hasil, hub]
---

# Results

**Sumber:** `06-Results/`

Tempat angka tinggal. Dua jenis halaman di sini: **ambang** (apa yang harus dilewati, ditulis
sebelum hasil) dan **vonis** (apa yang terjadi). Halaman pra-registrasi tidak boleh diedit setelah
hasil keluar — koreksi lewat halaman baru, supaya urutannya bisa dipertanggungjawabkan.

## Bagian

- [[01 - Claims and Limits]] — yang terbukti vs yang tidak
- [[02 - Thresholds]] — MIN_TRADES, BH α, ongkos (20 bps sebelum, **59 bps sejak P10 28 Sep**), asal tiap angka
- [[03 - Not Yet Proven]] — daftar hidup yang belum kami buktikan
- [[04 - Negative Results]] — aturan arah mati; smart money vs kerumunan
- [[05 - Pre-registration Flow]] — uji aliran kerumunan, terkunci sebelum hasil
- [[06 - Pre-registration Horizon]] — uji horison whale + vonisnya
- [[07 - Matured Outcomes]] — hasil pertama prediksi yang di-anchor
- [[08 - Carry Study]] — veto funding kena 0 dari 2.963 settlement; 0 dari 12 uji arah lolos BH;
  carry 1,3–2,2 bps/hari vs round-trip 59 bps
- 🔴 **[[09 - Whale Cluster Test]] - DICABUT oleh [[12 - Harga Masuk yang Benar]]**: K>=2
  +393,4 CI [+5; +1012] p=0,0008 hidup di sisi **harga masuk**, bukan di pasar. Isi halaman
  dibiarkan (urutan koreksinya +508 -> +363,6 -> +393,4 adalah bagian dari hasilnya).
- 🔴 **[[10 - Evidence Stack]] - DICABUT oleh [[12 - Harga Masuk yang Benar]]**. Semua angkanya
  (lima aspek lulus sendiri, tumpukan +481 CI [+23; +977], kombinasi +748,8) memakai `px`
  sebagai **harga masuk**, dan harga itu tangga beku: di kejadian yang sama, pairing yang sama,
  hanya sumur harga yang berganti, **+93,0 (p=0,0066) menjadi +0,1 (p=0,53)**; pada harga
  peristiwa tidak ada aspek yang lolos BH. Yang tetap berdiri dari halaman ini justru yang
  dibuang: `fresh_token` +7.708 adalah artefak kebijakan pull kami sendiri.
- [[11 - Pra-Registrasi Hari Kedua]] - halaman yang bisa **membatalkan** 09 dan 10: parameter
  dikunci (sha256 blok spesifikasi + `t_kunci` 06:13:38Z), hanya kejadian setelah kunci yang
  dinilai, dan `tools/day2_replicate.py` menolak mencetak angka sampai rekaman baru >= 12 jam.
  Dijuji: sunting spesifikasinya -> `exit=1` ("yang berubah bukan datanya, aturan mainnya").
  **Sejak F-D30: MOOT untuk keputusan produk** - `sumber_harga: gmgn` di dalamnya memakai harga
  masuk yang terbukti cacat instrumen; run-nya nanti dicatat sebagai demonstrasi efek hantu.
- [[12 - Harga Masuk yang Benar]] - **yang membatalkan 09 dan 10**, dan sebabnya: `px` kami
  bukan ticker (71,7 % baris mengulang nilai; umur median harga 8,7 menit, p90 42 menit),
  kejadian berkerumun punya deret yang lebih segar, dan kesegaran itu masuk ke **definisi
  keuntungan**. Pada `tx->tx`: `cluster_ge2` **+0,3 CI [-7; +516] p=0,35**, nol aspek lolos
  BH; pada 908 kejadian `--px txevent` malah **−491,4 bps, CI [−1319; −205]**, cuma 30,5 % positif.
  Spesifikasi yang hidup dikunci di sini: `--halaman 12`, `spec_sha256=0x6f69e100...`,
  `t_kunci` 09:38:44Z, syarat 12 jam rekaman baru. Hipotesis fade **tidak dijual**.
  **TERJALAN 28 Sep 21:45Z: TIDAK ADA REPLIKASI** - `uji_primer` K≥2 = median **−1.518,5 bps**
  CI **[−7.379; −3]** (n=40), `stack≥2` **−1.124,3** CI [−3.310; −3]. Arahnya terbalik dan CI-nya
  tidak menyentuh nol, tapi aturan halaman itu menutup **dua** arah: fade tidak boleh dijual
  tanpa kuncinya sendiri. Sensor: 7.294 beli dibuang tanpa harga keluar -> P33.
- [[20 - Keluar Cepat, Terkunci]] - E12: kunci kelima, dipasang 29 Sep **08:04:56Z** setelah E11
  dilihat dan sebelum satu pasangan pun dihitung. Arm kebijakan = keluar di menit ke-5, arm kontrol =
  tahan sampai menit ke-30 **pada posisi yang sama**, empat syarat serentak termasuk syarat baru F-D41
  (laporkan umur baris harga keluar + `P(ada harga keluar)` atau angkanya tidak masuk vault). Vonis
  **20:04:56Z**.
- [[23 - Gerbang Trailing]] - algebra "jangan sampai rugi" diukur pada jalur harga kami sendiri.
- [[24 - Trailing pada Bar yang Salah]] - E17 dieksekusi di posisi yang sama dengan placebo yang sah, dan kesimpulannya metodologis: **25 dari 28 lengan punya delta median tepat 0,0** - pada 1-4 bar per jam sebagian besar posisi tidak pernah melihat level stopnya. Saat bar dijarangkan, keunggulan +105,2 bps runtuh ke -83,9 sementara baseline diam: yang saya hampir umumkan sebagai kebijakan adalah resolusi sampel. P49 -> BLOCKED-BY-DATA.
- [[25 - Rem, Terkunci Prospectif]] - E22: untuk pertama kalinya aturan rem ditulis **sebelum** ada datanya (kunci 12:08:15Z saat `kejadian pasca-kunci: 0`). Empat syarat serentak, dua kontrol arah sekaligus (Mann-Whitney + placebo label), dan syarat cakupan + umur baris harga keluar. Vonis 20:08:15Z. Kalau gagal: "rem memperbaiki hasil" turun jadi klaim in-sample - dan itu akan tetap tertulis di halaman ini.
- [[26 - Masuk Segar, Terukur Benar]] - koreksi besar 29 Sep: umur kabar kami **61 d**, bukan 808 d; **0 dari 58** lengan 5 m rejim lama mengukur masa depan; angka sah pertama n=25: **−519,4 bps**
- [[27 - Masuk Terpilih vs Masuk Acak]] - E24: kontrol acak dipasang di jalur cepat, kunci 13:19:04Z dengan **0 kejadian pasca-kunci**; yang harus dikalahkan bukan nol (F-D8)
- [[28 - Venue Kami Bukan Pasar]] - E20/E26: dari 41 simbol reachable hanya **5** yang harga perp-nya bergerak di resolusi menit, dan di 5 itu bump E11 **tidak ada** (placebo di atas yang asli); dua angka reachable dipakai bersama sekarang (2,26 % pasangan vs 5,86 % aset)
  Hasilnya **membantah dugaan saya**: lock bersyarat justru umum (63 % kejadian punya puncak di paruh
  awal yang melewati ambang 2s+i+C) - yang tidak kami punya adalah **resolusi** (pada 5 menit 69 %
  kejadian tidak punya dua baris harga sama sekali), dan stop mengubah bentuk distribusi, bukan drift.
- [[21 - Rem di Horison Cepat]] - E13: satu-satunya hal yang **masuk** di horison tempat kabar hidup
  adalah menolak. Di menit ke-5 `BOLEH` **+285,5 bps** (median **+79,8**) vs `VETO` **−230,3**
  (median −377,8); selisih +515,8 melawan CI atas placebo +397,2. Eksplorasi tanpa kunci, dan
  VETO-nya bukan kelompok acak - batas itu menempel pada angkanya.
- [[22 - Buku Order, Terkunci Lebih Dulu]] - teori builder (imbalance buku order + trailing stop).
  Ditulis jadi dua hal yang bisa diuji; T1 dikunci **sebelum** ada datanya (09:37:45Z, vonis
  21:37:45Z) dengan lima pembacaan "variasi harga" yang direkam semua karena frasa aslinya ambigu -
  dan snapshot pertama sudah membuktikan: `bi1` dan `bi20` pada simbol yang sama bisa berlawanan
  tanda. Timeframe dijawab dengan tiga lapis: kabar hidup ±2 menit, buku kami terlihat tiap ±200
  detik, jadi yang diuji adalah versi lambat teori itu.
- [[19 - Umur Posisi]] - untuk pertama kalinya ada angka **positif yang lolos placebo**: harapan
  +192,7 bps di menit ke-2 dan +202,6 di menit ke-5, lalu meluruh jadi −182,5 di menit ke-30
  (placebo asal-mula: datar −180). Tapi menunda masuk **2 menit** saja sudah membalik mediannya,
  dan mesin keputusan kami bangun tiap 4 jam - jadi yang menahan bukan sinyal, tapi jalur.
- [[17 - Pra-Registrasi Watch]] - spesifikasi KETIGA, ditulis dan dikunci sebelum satu angka pun dilihat (29 Sep 03:0xZ, `spec_sha256=0xc4105c17…`, `t_kunci=02:59:06Z`): uji kerumunan pada **`wp`** - satu-satunya deret yang berdetak tanpa menunggu transaksi. Yang membuatnya bukan pengulangan: pada `wp`, token yang mendatar TETAP punya keluaran, jadi "tidak bergerak" dihitung, bukan dibuang (penyensoran yang membunuh halaman 12/16). Umur datanya dibaca dari berkas `wp` sendiri, bukan dari jam aliran.
- [[13 - Apakah Tidak Trading Itu Gratis]] - jawaban terukur untuk "apa gunanya kalau cuma tahu
  jangan masuk": tidak trading **tidak gratis** (harapan winso **+82,7 bps/posisi**, **33,9 %**
  kejadian naik ≥+500 bps dalam 30 m, walau median −58,9) - **tapi tidak ada aspek aliran kami yang
  menaikkan peluang itu di atas baseline**. Yang lolos BH justru penurunan: `jual_2/3/bersih`
  menurunkan P(≥+500) ke **20,3–22,5 %** -> **veto masuk**; `beli_2` = waktu **keluar** (berpasangan
  −313 CI [−1041; −11]). Yang belum bisa dijawab: kapan boleh masuk.
- [[14 - Buku Paper]] - builder meluruskan: yang diminta paper trading, bukan order. Buku jalan,
  556 posisi: **random+veto +188,3** vs **tanpa-gerbang +95,1** *(net of 59 bps dan hampir nol dampak - satuannya salah ±600x, F-D46 - dan **artefak budget**: control yang sama −100,2 @24/hari dan −26,7 @5/hari, F-D51)* (≈ +93 bps dari menolak kerumunan
  jual), median tetap −59 (=ongkos, jadi yang hidup ekor), dan kandidat `lock_percent` **mati
  sebagai kebijakan**: +109,7 < acak, dan −51,2 di 1 BNB - karena menyortirnya memaksa kami memilih
  subset "yang bisa dideskripsikan", yang baseline-nya −64,7. Naik 0,01 -> 1,00 BNB memangkas
  ~70-90 bps/posisi dari dampak harga; 454/556 posisi bahkan tidak punya angka likuiditas.
- [[15 - Teknikal Klasik Diuji]] - builder bertanya "Fibonacci/swing/scalping/MA kepakai tidak?".
  Jawabannya sekarang angka, bukan pengakuan: **12 fitur teknikal pada 1.054 kejadian harga
  peristiwa - nol di atas control acak, nol lolos BH**, dan `breakout` **−587,9 CI [−951,9; −201,4]
  dengan P(≥+500) 3,7 %** (vs pool 39,8 %). Catatan penting: bar kami = deret transaksi, jadi ini
  ADAPTASI; `04-Setup` (7 persona) memang belum punya satu pun perintah alat, dan Fibonacci tidak
  punya catatan sendiri - dia disebut 15 catatan sebagai konsep.
- [[16 - Harga Keluar yang Hilang]] - yang memotong halaman 15: pada kohort token muda (mean +450,8) hanya **19,4 %** kejadian punya baris harga keluar (547/2.814; **2.267 hilang**); memberi yang hilang nilai seburuk p05 teramati (-2.000, yang memang sudah di lantai) membalik mean ke **-1.562,8**, dan `break-even = 0`. Untuk memecoin, "tidak ada transaksi lagi 30 menit kemudian" bukan lubang data - itu beritanya.
- [[17 - Pra-Registrasi Watch]] - kunci ketiga dipasang 29 Sep 02:59:06Z, dan **diukur dari berkas
  `wp` sendiri, bukan dari jam aliran**: flow bisa hidup sementara pantau mati. Matang ±14:59Z;
  selama umurnya kurang, alatnya mencetak **nol angka hasil** dan itu perilaku yang benar.
- [[18 - Kandidat Pertama, Diuji Hidup]] - untuk pertama kalinya ada satu fitur yang melewati
  kontrolnya sendiri (`vol_rendah` **+132,9** vs acak-siklus CI atas **+116,1**), dan untuk pertama
  kalinya pula itu **tidak dijual**: sepuluh uji sekaligus berarti Bonferroni 0,25. Yang dijalankan
  sekarang dua lengan paper pada data yang belum terjadi; vonis 17:13Z.
- [[09 - Whale Cluster Test]] — **DICABUT sebagian (F-D30)**: headline `px→px` +93,0 bps ternyata artefak harga masuk beku; `tx→px` +0,1 bps (p=0,53). Halaman tetap berdiri sebagai tempat banner pencabutan, dan baris `ttx`/`px` di ⑦ adalah warisannya
- [[10 - Evidence Stack]] — **DICABUT (F-D30)**: tumpukan bukti yang tampak menguatkan 'kerumunan beli = sinyal' disusun dari sumber harga yang sama; yang bertahan dari kerumunan hanya sisi **jual** (halaman 13, F-D31)

<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->
```dataview
LIST FROM #hasil SORT file.name ASC
```

## Terkait

- [[Quick-Reference]] · [[Index]] · [[Conventions]]

