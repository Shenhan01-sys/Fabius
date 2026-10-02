---
tags: [backlog, epik, riset, ambang, kalibrasi, "anti-snooping"]
---

# 08 - Riset Optimasi Ambang (kunci v1 → v2: aturan main ditulis sebelum angka)

**Bagian dari:** [[08-Backlog/00 - Hub Backlog]]
**Dibuka:** 2 Okt 2026 oleh builder, kata-katanya: *"Sementara ini oke, nanti kita coba riset lagi untuk mengoptimalkan itu (catat di vault)"* - jawaban atas pertanyaan
"kunci ambang v1 sekarang?" ([[00-Overview/03 - Decisions]] F-D73).
**Sumber:** kode `engine/gates.py` (`GateParams`), `engine/kpi.py` (`KpiParams`), `engine/slots.py` (`SlotParams`), `engine/economics.py`, `engine/locks.py`; garis dasar
`09-Inbox/Session-2026-10-02-skrip/run13_null_calibration.py` dan `run14_power_arithmetic.py`; konteks [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] §0, §9.

> **STATUS: USULAN - rencana, bukan hasil.** Satu-satunya angka terukur di halaman ini: garis dasar §3 (dunia sintetik tanpa edge) dan aritmetika daya §1. **Tidak ada ambang yang diubah.**
> Kunci v1 tetap berlaku sampai ada kunci v2 yang disetujui builder. Belum ada riset yang dijalankan selain garis dasar; garis dasar itu sendiri **eksploratif** (tidak dipra-registrasi,
> dijalankan sesudah v1 dikunci dan sesudah saya tahu hasil dogfood).

## 0. Kenapa halaman ini ada

- Ambang v1 = angka yang saya pilih dengan penilaian, **bukan hasil optimasi**. Empat gerbang diubah setelah saya melihat hasil enam bot sendiri (epik 07 §0); itu sebabnya v1 dikunci sekarang dan riset
  ditunda: mengunci tidak berarti angkanya benar, hanya berarti ia berhenti bergeser diam-diam.
- Risiko terbesar riset ini adalah **mengulang kesalahan yang sama dalam bentuk lebih canggih**: menyetel ambang sampai bot yang kita sukai lolos. Karena itu aturan main (§2) ditulis lebih dulu, dan
  yang menentukan arah riset adalah anggaran kesalahan (§1), bukan nasib enam bot.
- Dogfood menolak 4 dari 5 bot yang bisa dinilai; itu bisa berarti ambang terlalu ketat atau bot-nya lemah, dan **data yang sama tidak bisa membedakannya** (§1, plafon daya). Riset ini ada untuk memisahkan
  keduanya tanpa memakai enam bot itu sebagai penguji.

## 1. Apa arti "optimal" (usulan; builder memutuskan, **sebelum** hasil terlihat)

**Kerugian tidak simetris.** Penerimaan palsu = Fabius menjual sinyal tanpa edge (melanggar "kami tidak mengklaim edge", F-D16, dan menambah risiko hukum); penolakan palsu = kehilangan satu bot
yang masih bisa dikirim ulang setelah masa tunggu 30 hari (`slots.can_submit`). Maka bingkainya Neyman-Pearson: **tetapkan anggaran positif-palsu dulu, lalu maksimalkan daya** di bawahnya.

Anggaran yang saya usulkan (**belum diputuskan**; builder menetapkannya sebelum hasil riset dilihat - aturan §2 #5):

| kode | anggaran | status |
|---|---|---|
| A1 | peluang bot **tanpa edge** lolos semua gerbang pada **satu pengajuan jujur** ≤ 1 % | usulan |
| A2 | penambang yang mengirim banyak konfigurasi: rata-rata penerimaan palsu **per keluarga penerbit per tahun** ≤ 0,1 pada batas antrean (`queue_max_per_family`, `cooldown_days`) | usulan |
| A3 | daya minimum pada edge tertentu | **tidak diusulkan angka**: ditetapkan setelah R2, dan tidak boleh melampaui plafon di bawah |

**Plafon aritmetika daya** (`python -X utf8 09-Inbox/Session-2026-10-02-skrip/run14_power_arithmetic.py`; pendekatan: Sharpe taksiran ~ Normal(s, (1 + s²/2)/T), satu uji satu-sisi 5 %, hasil iid,
**tanpa gerbang lain** - gerbang lain hanya bisa menurunkan daya; ini plafon, bukan perkiraan):

| Sharpe sebenarnya s | daya pada T = 3,0 th | 3,8 th | 6,7 th | tahun riwayat untuk daya 80 % |
|---|---|---|---|---|
| 0,50 | 23,1 % | 26,4 % | 37,0 % | 25,8 |
| 1,00 | 52,8 % | 59,8 % | 77,9 % | 7,2 |
| 1,50 | 74,3 % | 81,0 % | 93,8 % | 3,7 |

(3,0 th = syarat minimum G2 `min_bars` 1095 hari; 3,8 th = 1400 hari = dunia sintetik garis dasar; 6,7 th = 2434 hari = riwayat nyata B1 menurut G2.)

**Akibatnya:** edge sedang (Sharpe ≤ 0,5) tidak mungkin dipisahkan dari noise oleh riwayat beberapa tahun **apa pun gerbangnya**. Daya lebih besar butuh **lebih banyak data** (riwayat lebih panjang,
frekuensi lebih tinggi, lebih banyak bot independen), bukan ambang lebih longgar. Kalau R2 menunjukkan daya pada edge yang masuk akal kecil, kesimpulan jujurnya mungkin "v1 sudah sekitar
yang diizinkan data; jangan disetel" dan penentunya data maju (R8).

### 1a. Penjelasan dengan bahasa biasa (jawaban atas "maksudnya apa?", F-D74)

Penyaring bot kita (gerbang + KPI) bisa salah dengan **dua cara**, dan keduanya punya harga:

1. **Bot jelek lolos (positif-palsu).** Bot yang sebenarnya tidak punya keunggulan, tetapi kebetulan tampak bagus di data lama, diterima. Akibatnya: Fabius menjual sinyal tanpa keunggulan, pelanggan rugi,
   dan klaim "kami tidak mengklaim edge" jadi bohong. *Contoh:* anggaran 1 % berarti dari 100 bot tanpa keunggulan yang masing-masing mengirim sekali, **paling banyak 1** boleh lolos.
2. **Bot bagus tertolak (daya kurang).** Bot yang sungguhan bagus gagal lolos karena datanya terlalu pendek untuk meyakinkan. Akibatnya: Fabius kehilangan satu bot yang sebenarnya menguntungkan
   (penerbit boleh mengirim ulang setelah 30 hari). *Contoh:* daya 60 % berarti dari 10 bot yang sungguh bagus, sekitar 6 lolos dan 4 tertolak keliru.

Keduanya **tarik-menarik**: makin ketat penyaringnya, makin sedikit bot jelek yang lolos, tetapi makin banyak bot bagus ikut tertolak. Tidak ada setelan yang membuat keduanya nol. Yang bisa dipilih hanyalah
**seberapa besar tiap kesalahan masih kita relakan** - dan itu bukan soal teknis melainkan selera risiko, jadi **keputusan builder**. "Anggaran" = batas itu, ditulis sebelum riset mulai.

**Kenapa harus dipilih sebelum hasil terlihat:** kalau angkanya dipilih sesudah melihat hasil, gampang sekali memilih angka yang kebetulan membenarkan ambang yang sudah kita sukai - itulah jebakan "menyetel sampai lolos".

**Usulan saya (boleh diterima apa adanya):** A1 - peluang bot tanpa keunggulan lolos pada satu pengajuan jujur ≤ 1 %; A2 - penambang yang mengirim banyak konfigurasi, rata-rata penerimaan palsu ≤ 0,1 per keluarga penerbit per tahun;
daya **belum diberi angka**, karena riwayat beberapa tahun sendiri membatasi seberapa kecil keunggulan yang mungkin terdeteksi (tabel plafon di atas). Tidak perlu dijawab sekarang: riset belum jalan.

## 2. Aturan anti-snooping (dipasang sebelum riset; setiap pelanggaran dipajang, bukan dihapus)

1. **Vonis enam bot Fabius bukan target dan bukan kriteria pilih.** Tidak ada keputusan ambang yang boleh dibenarkan dengan "supaya B2 lolos". Mereka boleh dilaporkan **sesudah** keputusan,
   berlabel "dalam-sampel; sudah dipakai menyetel v1 empat kali".
2. **Bahan kalibrasi hanya:** (a) dunia sintetik (tanpa edge dan edge-diketahui); (b) data nyata **hanya untuk sifat deskriptif** yang membuat dunia sintetik realistis (autokorelasi, klaster volatilitas, ekor,
   biaya, funding) - tidak pernah untuk menentukan lolos/gagal; (c) data maju (shadow) kelak, dengan rencana analisis ditulis sebelum data pertama dilihat.
3. **Pra-registrasi.** Sebelum menjalankan tiap R: tulis protokol (dunia, grid, benih, metrik, aturan keputusan, kriteria berhenti), cetak sha256-nya di halaman hasil; penyimpangan dipajang. Sha protokol boleh
   di-anchor bila builder mau (doktrin: anchor sebelum hasil).
4. **Set menyetel ≠ set mengonfirmasi** (benih dan keluarga generatif berbeda); yang dilaporkan sebagai hasil = set konfirmasi.
5. **Anggaran (§1) ditetapkan builder sebelum hasil terlihat**, tidak boleh dipilih mundur untuk membenarkan sebuah ambang.
6. **Presisi dinyatakan di muka.** Positif-palsu ≈ 1 % dengan galat ±0,3 poin butuh ≈ 1.100 **pasar independen** (n ≈ p(1−p)/SE² = 0,0099/0,000009). Konfigurasi dalam satu pasar saling bergantungan
   dan **bukan** sampel independen (garis dasar A hanya 17 deret).
7. **Hasil negatif dipublikasikan** ("v1 sudah mendekati yang bisa dicapai data" atau "v1 terlalu longgar"); tidak ada hasil yang disembunyikan.
8. **Setiap perubahan = kunci baru:** `python -X utf8 -m engine.cli lock --write --supersede --note "<alasan, protokol, sha lama → baru>"` (yang lama pindah ke `engine/locks/history/`), dengan keputusan builder
   (F-D##). Berlaku untuk kandidat **baru**; petahana tidak otomatis dinilai ulang (grandfather) kecuali builder memutuskan lain.
9. **Tidak menyetel dengan melihat kandidat luar yang sedang antre**; bila ada, riset dibekukan sampai vonisnya jatuh. (Saat ini: nol kandidat luar.)
10. **Di luar cakupan:** F-D16 (pagar uang nyata), F-D17, F-D18, dan basis pendapatan 60/40 tidak dilonggarkan oleh riset ini; R10 hanya informatif.

## 3. Garis dasar (dicetak 2 Okt 2026)

**3.1 Kunci v1** (`python -X utf8 -m engine.cli lock`: `TERKUNCI`, sha `0xf145b70abd251b9fcf421bfb811bcf3788dade347c37b3bea331a09fedfe5f32`; **ter-anchor di chain 97 pada 2026-10-02T08:17:48Z**, F-D74, `python -X utf8 tools/anchor_lock.py --verify`):

```
gerbang: Sharpe >= 0.5 (+deflasi N percobaan), bootstrap p5 > 0, placebo p <= 0.05 (200 acak), plateau (0.5, 0.75, 1.25, 1.5), biaya 2.0x, dSharpe EW >= 0.05, korelasi <= 0.7, seed 20261002
KPI: tahunan net >= 6% (hurdle 4% + margin 2%), Calmar >= 0.5, sinyal >= 12/tahun dan >= 20 total, basis bagi hasil: pendapatan
slot: shadow 60 hari, masa tenggang 60 hari, jendela skor 90 hari, margin 100 bps + t >= 2, 1 penggantian per epoch (30 hari)
ekonomi: penerbit 60% / Fabius 40% dari pendapatan penjualan sinyal
```

Hurdle 4 % adalah **asumsi saya, belum diukur** terhadap imbal hasil bebas-risiko yang bisa dipakai pengguna (R3). Angka lain di baris ini juga pilihan penilaian.

**3.2 Dogfood v1** (`python -X utf8 -m engine.cli gate --data <dir> --bot ALL`, dicetak ulang sesudah kunci ditulis; vonis dan angka **identik** dengan epik 07 §7): B3 LOLOS_SHADOW; B1 TOLAK (G8, G10); B2 TOLAK (G4);
B5 TOLAK (G8); B6 TOLAK (G3, G8, G10, K2); B4 tak terukur. **Bukan target riset** (aturan #1).

**3.3 Kalibrasi NOL** (`python -X utf8 09-Inbox/Session-2026-10-02-skrip/run13_null_calibration.py --workers 10`, ±2 menit; **dua lari menghasilkan hitungan identik**, benih tetap).
Dunia: random-walk gaussian tanpa drift aritmetik, volatilitas konstan 3 %/hari, 1.400 hari, 17 simbol; ongkos tetap dibayar (harapan PnL ≤ 0). Vonis memakai `GateParams`/`KpiParams` terkunci.
**A (penambang):** satu pasar, B1-TREND dan B6-BOUNCE × 10 parameter × 17 universe satu-simbol = 340 konfigurasi. **B (satu kali):** 60 pasar independen, satu konfigurasi B1 (N = 60) per pasar.

| gerbang (lolos = PASS atau TB) | A: 340 konfigurasi, satu pasar | B: 60 pasar independen |
|---|---|---|
| G3 NET (Sharpe + deflasi + p5) | 12 | 5 |
| G4 RECENT | 114 | 27 |
| G5 PLATEAU | 34 | 15 |
| G7 FOLD | 50 | 12 |
| G8 NULL (placebo) | 13 | 3 |
| G9 COST | 92 | 23 |
| K1 ANN_NET | 68 | 21 |
| K2 CALMAR | 38 | 9 |
| K3 AKTIVITAS | 202 | 59 |
| Sharpe net mentah ≥ 0,5 saja | 25 (7,4 %; Wilson 5,0-10,6 %) | 12 (20,0 %; Wilson 11,8-31,8 %) |
| **semua gerbang, N = 1 (penambang diam)** | **4 (1,2 %; Wilson 0,5-3,0 %)** | **0 (Wilson 0,0-6,0 %)** |
| **semua gerbang, N = 340 (percobaan diakui)** | **0 (Wilson 0,0-1,1 %)** | - |

G1, G2, G6, G10, K4, K5 lolos/tidak berlaku secara trivial di dunia ini (data bersih, tanpa petahana dan klaim) dan tidak informatif; G11 NA menurut rancangan.

**Pembacaan jujur:**
- **Penyaring awal bekerja:** dari 340 konfigurasi tanpa edge, Sharpe mentah ≥ 0,5 meloloskan 25; seluruh gerbang menurunkannya ke 4 (N = 1) dan 0 (N = 340).
- **Tetapi N diisi sendiri oleh penerbit.** Penambang yang diam lolos 4 dari 340 (≈ satu per 85 konfigurasi), dan setiap konfigurasi gratis diuji sendiri karena kode gerbang publik: **oracle** (epik 07 §9 #1).
  Penangkalnya (penghitung percobaan global P83, seed rahasia, tahan 12 bulan terakhir) diukur di R4; sampai itu ada, shadow maju adalah satu-satunya penyaring yang tidak bisa diakali dengan percobaan gratis.
- **Empat yang lolos hanyalah paling banyak dua kejadian berbeda:** tiga parameter bertetangga B1 (20, 30, 45) pada satu deret sintetik dan satu B6 pada deret lain. Selang Wilson pada A terlalu sempit
  karena konfigurasi bergantungan; B (0 dari 60) tidak bisa menyingkirkan positif-palsu 6 %. Itu alasan R1 butuh ≈ 1.100 pasar (aturan #6).
- **Dunia ini ramah:** gaussian iid, volatilitas konstan, hanya B1 dan B6 satu-simbol, G10 tak diuji. Ekor tebal, klaster volatilitas, autokorelasi, dan faktor bersama belum diuji (R1).
- Ini **bukan replikasi** angka peninjau keamanan (476 konfigurasi; G3 meloloskan 5,3 %, dua lolos semua gerbang; epik 07 §9 #1) - ia dijalankan pada gerbang versi sore sebelum diperketat. Angka saya di gerbang
  v1: G3 12 dari 340 (3,5 %) dan semua gerbang 4 dari 340 pada N = 1.

## 4. Pertanyaan riset (R1-R11)

| ID | pertanyaan | metode | bisa mengubah |
|---|---|---|---|
| **R1** | Berapa peluang bot **tanpa edge** lolos (per gerbang dan gabungan) di dunia realistis? Gerbang mana yang sungguh menahan beban? | ≥ 1.100 pasar independen per dunia; dunia: iid, klaster volatilitas (GARCH), ekor-t, rezim tanpa drift, faktor bersama antar simbol, biaya dan funding nyata; template B1/B2/B3/B6 × universe 1/4/16 × grid parameter; **leave-one-gate-out** (G4 dan G9 lolos 33 %/27 % di noise A: apakah penyaring atau sekadar kebersihan?) | `GateParams` mana yang diperketat/dihapus |
| **R2** | Berapa peluang bot **beredge diketahui** lolos? Apakah "terlalu ketat atau botnya lemah" terjawab? | suntik prediktabilitas dengan Sharpe sebenarnya s ∈ {0,5; 0,75; 1; 1,5; 2} setelah biaya; daya per gerbang dan gabungan vs panjang riwayat; bandingkan dengan plafon §1 | `min_bars`, `min_net_sharpe`, `boot_q`, `recent_*`; atau kesimpulan "jangan setel" |
| **R3** | Dari mana hurdle KPI seharusnya datang? | **ukur** imbal hasil bebas-risiko yang bisa dipakai pengguna (stablecoin on-chain, T-bill, suku bunga lokal; sumber publik dengan tanggal ukur); margin = k × galat baku taksiran tahunan (≈ σ/√T) alih-alih 2 % tetap; K1 sebagai **batas bawah bootstrap ≥ hurdle** alih-alih titik taksir; Calmar dari toleransi MDD pelanggan; K3 dari n ≥ 20 (F-D16) dan retensi (R10) | `KpiParams` (hurdle, margin, `min_calmar`, `min_signals_*`) |
| **R4** | Apakah deflasi percobaan `expected_max_z`/`min_sharpe_for_trials` memberi tingkat kesalahan nominal, dan seberapa bocor bila N diumumkan terlalu kecil? Apa penangkal oracle yang terbaik? | simulasi: N jujur vs diumumkan ¼, ½ dari sebenarnya; bandingkan N-sendiri / penghitung global per keluarga (P83) / BH lintas kandidat / seed rahasia dari hash blok / hold-out 12 bulan tersembunyi | kebijakan `n_trials`, kode `review.py`, P83 |
| **R5** | Bentuk G5 (plateau) dan G6 (fase) mana yang punya rasio positif-palsu/daya terbaik? | tetangga di grid vs pengali; leave-one-out universe; fase penuh untuk semua template (`PHASE_VARIANTS`) | G5/G6, P89 |
| **R6** | Placebo G8 mana yang paling kuat dan stabil? | geser-melingkar vs sinyal acak ber-eksposur/turnover sama vs benchmark universe-matched + bootstrap (bot alokasi); kestabilan p antar seed (B1: 0,040-0,109 pada v1) | `placebo_n`, `placebo_max_p`, G8 alokasi |
| **R7** | Apakah bootstrap blok tetap 20 hari menutupi selang yang dijanjikan pada deret autokorelasi/klaster? | blok tetap vs stationary (Politis-Romano) vs panjang blok otomatis (Politis-White); cakupan di dunia R1 | `boot_block`, `boot_n`, G3 |
| **R8** | Apakah skor saat-gerbang meramal hasil maju, dan berapa penyusutannya? | **butuh M2**: bandingkan Sharpe saat-gerbang dengan Sharpe maju per bot; rencana analisis ditulis sebelum data pertama; n kecil → selang lebar yang dikatakan | penyusutan G3/G4, `shadow_days` |
| **R9** | Parameter slot mana yang memberi churn rendah dan penggantian benar? | simulasi buku: bot sintetik edge-diketahui masuk bertahap; ukur churn, peluang bot terbaik bertahan, penggantian salah, waktu menyingkirkan bot mati | `SlotParams` |
| **R10** | Berapa pelanggan berbayar yang membuat 40 % Fabius menutup biaya satu bot, dan apakah 60 % cukup menarik bagi penerbit? | model titik-impas dengan **asumsi berlabel** (harga, konversi, churn, biaya operasi; belum ada data pelanggan) → tabel skenario, **bukan ambang** | informatif; mungkin `min_signals_year`, jenjang harga |
| **R11** | Apakah **klon-berpilihan** lolos G10 dan dedupe? | contoh `engine/examples/submission.example.json` (B1, universe ETH+BNB, N = 30) lolos terhadap buku genesis dengan korelasi **+0,69** < 0,7 dan ΔSharpe EW +0,28 - bukan karena isinya beda, tetapi karena Sharpe-nya lebih tinggi **setelah dipilih** sesudah melihat data. Ukur di dunia sintetik dengan varian yang dipilih sesudah melihat data; alternatif: korelasi 0,5, uji ortogonal (residu atas petahana), dedupe fingerprint lintas-universe | `marginal_max_corr`, `marginal_min_dsharpe`, kode G10/dedupe |

## 5. Urutan kerja

0. **Selesai (2 Okt):** aturan §2, plafon §1, garis dasar §3.
1. **Builder menetapkan anggaran A1-A2** (§1) - sebelum hasil riset apa pun.
2. **Protokol R1+R2** → sha → jalankan dengan parameter terkunci (bukan `GateParams.fast()`, yang mengubah gerbangnya sendiri). Biaya (ekstrapolasi linear dari garis dasar: 400 konfigurasi = ±2 menit pada 10 pekerja;
   **belum diukur**): 1.100 pasar × 1 konfigurasi ≈ ±6 menit; 1.100 pasar × 60 konfigurasi ≈ 66.000 konfigurasi ≈ ±6 jam per dunia. Dunia ini dipakai ulang oleh langkah 3-6.
3. R4, R7, R6, R5 (mesin statistik). 4. R3 dan R10 (ekonomi; data eksternal bertanggal) - bisa paralel. 5. R11 sesudah R1. 6. R9 sesudah R1/R2.
7. **R8 menunggu** M2 (ledger paper per bot, jam maju) dan ≥ 90 hari shadow. **Update F-D75:** M2 dibangun; jam maju B1-TREND dimulai di bar 2026-10-01, jadi 90 hari tercapai paling cepat akhir Desember 2026 (bila tidak ada hari bolong); `settle` bisa tertunda oleh funding (lihat `ledger/README.md`).
8. Sintesis → usulan **kunci v2 atau "tetap v1"** → keputusan builder (F-D##) → `lock --write --supersede`.

**Backlog:** **P90** = riset ini (R1-R11). **P91** = meng-anchor sha kunci v1 dan meng-commit `engine/` + vault - ~~kata builder, belum dikerjakan~~ **selesai di F-D74** (anchor 2026-10-02T08:17:48Z; push: lihat F-D74 #5).
**Kriteria berhenti** (dinyatakan di muka): kurva positif-palsu vs daya mendatar (kenaikan daya < 2 poin per 0,5 poin positif-palsu) atau anggaran waktu habis; **tidak ada "sekali lagi"**.

## 6. Hasil yang harus siap kita terima

- **v1 hampir yang terbaik untuk data sepanjang ini** → tidak diubah.
- **v1 terlalu longgar di dunia realistis** → diperketat; sebagian bot (termasuk B3, satu-satunya yang lolos hari ini) bisa jatuh.
- **v1 terlalu ketat untuk edge yang masuk akal (daya rendah)** → solusinya bukan melonggarkan ambang, melainkan lebih banyak data atau mengandalkan shadow maju.
- **Tidak bisa dioptimasi tanpa data maju** → menunggu R8; v1 tetap, dengan label "sementara".

## 7. Batas

- Rencana, belum ada hasil riset. Dunia sintetik ≠ pasar; satu sumber data nyata (16 penyintas, 2020-2026, dengan bolong). Tidak ada klaim edge.
- Garis dasar §3.3 eksploratif; presisinya rendah (aturan #6) dan hanya dua template, satu simbol per universe.
- Anggaran A1-A2 adalah usulan saya; belum ada kata builder (builder bertanya "maksudnya apa?" - dijelaskan di §1a; keputusan menunggu).

**Terkait:** [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] · [[08-Backlog/05 - Epik Enam Bot]] · [[08-Backlog/06 - Epik Gerbang Sinyal]] · [[00-Overview/03 - Decisions]] (F-D73, F-D72, F-D71, F-D16) ·
[[Concepts/One-Way Gate]] · [[Concepts/Unmeasured Is Not Clean]] · [[Concepts/Anchored Before Outcome]] · [[09-Inbox/Session-2026-10-02]]
