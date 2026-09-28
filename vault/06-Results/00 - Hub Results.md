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
- [[13 - Apakah Tidak Trading Itu Gratis]] - jawaban terukur untuk "apa gunanya kalau cuma tahu
  jangan masuk": tidak trading **tidak gratis** (harapan winso **+82,7 bps/posisi**, **33,9 %**
  kejadian naik ≥+500 bps dalam 30 m, walau median −58,9) - **tapi tidak ada aspek aliran kami yang
  menaikkan peluang itu di atas baseline**. Yang lolos BH justru penurunan: `jual_2/3/bersih`
  menurunkan P(≥+500) ke **20,3–22,5 %** -> **veto masuk**; `beli_2` = waktu **keluar** (berpasangan
  −313 CI [−1041; −11]). Yang belum bisa dijawab: kapan boleh masuk.
- [[14 - Buku Paper]] - builder meluruskan: yang diminta paper trading, bukan order. Buku jalan,
  556 posisi: **random+veto +188,3** vs **tanpa-gerbang +95,1** (≈ +93 bps dari menolak kerumunan
  jual), median tetap −59 (=ongkos, jadi yang hidup ekor), dan kandidat `lock_percent` **mati
  sebagai kebijakan**: +109,7 < acak, dan −51,2 di 1 BNB - karena menyortirnya memaksa kami memilih
  subset "yang bisa dideskripsikan", yang baseline-nya −64,7. Naik 0,01 -> 1,00 BNB memangkas
  ~70-90 bps/posisi dari dampak harga; 454/556 posisi bahkan tidak punya angka likuiditas.
- [[09 - Whale Cluster Test]] ← tulis penjelasannya
- [[10 - Evidence Stack]] ← tulis penjelasannya

<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->
```dataview
LIST FROM #hasil SORT file.name ASC
```

## Terkait

- [[Quick-Reference]] · [[Index]] · [[Conventions]]

