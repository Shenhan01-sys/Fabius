---
tags: [results]
---

# 10 - Evidence Stack

**Sumber:** `tools/evidence_stack.py` → `decisions/evidence-stack-20260928T073717Z.json`
(`rows_sha256=0x9f31f56bb76acf…`) · bahan: rekaman ⑦ + `px` kami sendiri · ongkos dari
`tools/costs.py` (59 bps, `measured-own-venue`)

**Determinisme:** artefak `072728Z` (07:27Z) dan `073717Z` (07:37Z) punya **`rows_sha256` identik**
- dua puluh menit kemudian, dengan berkas rekaman yang bertambah terus, baris hasilnya tidak
bergeser. Itu bukan kebetulan: kedua run sudah memakai `dedupe_px()` yang sama, jadi "satu bentuk
data" yang jadi syarat di §0 memang bisa dibuktikan, bukan cuma diumumkan.

**Ringkas:** satu aspek (kerumunan maker) terlalu tipis untuk jadi dasar membuka posisi. Halaman
ini adalah upaya pertama menambahkan aspek lain **dengan uji yang sama persis** - bukan dengan bobot
perasaan. Hasil: **lima aspek memisahkan sendirian, tumpukannya memisahkan lebih kuat, dan satu
yang kelihatan paling hebat justru bukan** - `fresh_token` memberi +7.708 bps yang hampir pasti
artefak cara kita menarik harga, jadi dia dibuang dari tumpukan; ditumpukan tanpa dia, hasilnya
tetap hidup (+481 bps, CI [+23; +977]).

## 0. Harga duplikat: penyebab dua alat kami memberi angka berbeda

Sebelum apa pun: `flow_cluster_test` bilang K≥2 = **+363,6 bps**; `evidence_stack` bilang **+649,8**
- kejadian sama, token sama, n sama. Kucari bedanya alih-alih memilih yang enak: **5.355 baris `px`
berbagi stempel waktu yang sama untuk token yang sama** (±19 % dari deret harga kami), karena
`smartmoney` dan `kol` melihat pool yang sama dalam satu siklus. Selama duplikat dibiarkan, "harga
masuk" ditentukan oleh **cara mengurutkan**, bukan oleh data: `.sort()` pada tuple memakai harga
sebagai pemecah seri, `.sort(key=t)` tidak.

Aturan kanonik sekarang ada di satu tempat - `flow_cluster_test.dedupe_px()`: satu harga per
(token, stempel) = median harga pada stempel itu - dan **dipakai oleh kedua alat**. Setelah itu
keduanya sepakat: K≥2 = **+393,4 bps** (CI [+5; +1012]).

Pelajarannya lebih besar dari bug-nya: kalau dua alat yang jujur memberi angka berbeda, yang salah
bukan statistiknya - datanya belum punya satu bentuk.

## 1. Frekuensi aspek (807 kejadian yang bisa dinilai)

Lima aspek diuji **berpasangan di dalam token yang sama** (acuan = kejadian pada token yang sama
yang TIDAK memicu aspek itu), median + bootstrap 4.000 + BH α 0,10:

| aspek | definisi (point-in-time, hanya data ≤ t) | % kejadian | median selisih | CI 95 % | % positif | p | BH |
|---|---|---|---|---|---|---|---|
| `cluster_ge2` | ≥2 maker berbeda beli dalam 15 m | 54,2 % | **+393,4** | [+5; +1012] | 60,9 % | 0,0008 | **LOLOS** |
| `cluster_ge3` | ≥3 maker berbeda | 33,1 % | +592,6 | [+0; +1562] | 59,3 % | 0,0192 | **LOLOS** |
| `repeat_maker` | maker yang sama beli >1 kali di jendela | 33,8 % | +222,8 | [+0; +862] | 57,2 % | 0,0482 | **LOLOS** |
| `money_spread` | beli terbesar ≤ 60 % dari USD beli di jendela | 41,0 % | **+552,7** | [+16; +1225] | 62,5 % | 0,0007 | **LOLOS** |
| `buy_usd_ge_1k` | total beli ≥ 1.000 USD | 18,0 % | +601,0 | [+2; +1040] | 63,6 % | 0,0069 | **LOLOS** |
| `no_exit_flow` | tidak ada jual-banding-beli di jendela | 79,8 % | −0,3 | [−4; +4] | 48,9 % | 0,662 | **tidak** |
| `wide_flow` | gabungan lebar + USD + tanpa jual | 10,3 % | +0,5 | [−37; +180] | 50,0 % | 0,553 | **tidak** |
| `fresh_token` | token baru muncul di rekaman ≤ 2× jendela | 36,6 % | +7.708,8 | [+4.594; +12.414] | 80,8 % | 0,0000 | **DIBUANG - lihat §3** |

Median net mutlak (bukan selisih) juga bergerak: K=1 **−59,0** (seharga ongkos; tidak ke mana-mana)
vs K≥2 **+478,6**, dan "% posisi positif" naik dari **35,9 %** (sendirian) ke **56,3 %** (berkerumun),
melawan **27,7 %** untuk "cuaca" (semua pasangan harga di token yang sama).

**Kenapa angka `cluster_ge3` di sini (+592,6) beda dari `09 - Whale Cluster Test` (+393,4) padahal
kejadiannya sama.** Acuannya beda, dan itu harus disebut, bukan disamakan: halaman 09 membandingkan
K≥k hanya lawan **K=1** ("kerumunan vs satu dompet"), halaman ini membandingkannya lawan **semua
kejadian lain di token yang sama** (termasuk K=2). Untuk `ge2` kedua definisi jatuh pada angka yang
sama persis (+393,4) karena lawan ge2 memang hanya K=1; untuk `ge3` mereka berbeda. Angka manapun
yang dipakai, jangan memetik satu dan menyebutnya "uji yang sama".

## 2. Tumpukan: aspek yang lulus diuji lagi sebagai kombinasi

Semua baris dihitung oleh `_research/stack_final.py` (28 Sep 07:40Z) di atas kejadian yang sama:

| kombinasi | token | n | median selisih | CI 95 % | % positif | p |
|---|---|---|---|---|---|---|
| ≥2 dari lima aspek lulus, **termasuk** fresh | 87 | 207 | +681,1 | [+180; +1225] | 66,2 % | 0,0000 |
| ≥2 dari lima aspek lulus, **tanpa** `fresh_token` | 78 | 194 | **+481,0** | **[+23; +977]** | 62,9 % | 0,0002 |
| ≥2 dari tiga aspek aliran (`ge2`+`repeat`+`spread`) | 76 | 172 | +374,6 | [+5; +915] | 61,0 % | 0,0023 |
| **`cluster_ge2` DAN `money_spread`** | 69 | 146 | **+748,8** | [+12; +1574] | 63,0 % | 0,0010 |
| `ge2` DAN `money_spread` DAN `repeat_maker` | 61 | 121 | +691,1 | [+1; +1373] | 61,2 % | 0,0072 |
| `ge2` DAN `buy_usd_ge_1k` | 46 | 88 | +601,0 | [+2; +1040] | 63,6 % | 0,0069 |
| `ge2` **ATAU** `money_spread` (gerbang longgar) | 84 | 310 | +407,8 | [+1; +921] | 60,0 % | 0,0040 |
| tepat 0 aspek lulus | 137 | 246 | −59,0 | [−63; −59] | 34,6 % | 1,0000 |
| tepat 1 aspek lulus | 133 | 216 | +154,1 | [−94; +425] | 53,7 % | 0,2107 |
| tepat 2 aspek lulus | 78 | 187 | **+598,8** | [+80; +1162] | 62,0 % | 0,0004 |
| tepat 3 aspek lulus | 33 | 46 | +737,4 | [−41; +1630] | 63,0 % | 0,0764 |
| tepat 4 aspek lulus | 5 | 6 | +1.263,3 | — | 83,3 % | 0,1250 |
| `cluster_ge3` **tanpa** `fresh_token` | 49 | 103 | −3,2 | [−791; +50] | 49,5 % | 0,5781 |
| `fresh_token` DAN `cluster_ge2` | 71 | 71 | +7.813,1 | [+4.512; +14.451] | 80,3 % | 0,0000 |

**Cara membaca empat baris terakhir.** `fresh DAN ge2` adalah alasan `fresh_token` dibuang: dia
menyuntik ±7.000 bps ke kombinasi mana pun dan tidak ada mekanisme pasar yang menjelaskannya (§3).
`ge3 tanpa fresh` adalah bukti kelas bersarang bukan replikasi - begitu fresh keluar, ≥3 dompet
**tidak** berbeda dari acuannya. Baris "tepat N aspek" naik monotik sampai 2-3 aspek lalu **sampel
habis** (4 aspek = 6 kejadian, CI tidak terisi): yang boleh dipakai adalah **"≥2 aspek"**, bukan
cerita "makin banyak makin benar".

Dua hal yang harus dibaca bersama tabel ini:

- **Kelasnya bersarang** (`ge3` ⊂ `ge2`), jadi baris-baris di §1 bukan uji bebas - dan bukti paling
  jujur untuk itu ada di baris terakhir: `cluster_ge3` **tanpa** `fresh_token` justru **nol**. Jangan
  bangun cerita "makin ramai makin benar" dari angka yang bersarang.
- Kombinasi terkuat yang bersih adalah **"≥2 dompet DAN uangnya tidak dari satu dompet"**
  (+748,8 bps, CI [+12; +1574], p=0,001). Itu bukan "lebih banyak whale", itu **struktur dana**:
  kerumunan yang sebenarnya, bukan satu paus yang dipecah jadi beberapa transaksi.

## 3. Kenapa `fresh_token` dibuang, bukan dipakai

+7.708 bps (80,8 % positif) terlalu besar untuk jadi efek pasar dan bentuknya mencurigakan secara
mekanis: "token ini baru saja masuk ke rekaman kami" = **kita baru mulai menarik harganya**. Untuk
pool x·y=k, saat pertama masuk kita menangkap bagian tengah pump; token yang masuk lalu mati
keburu punya sedikit titik harga, jadi tidak ikut dihitung. Yaitu kebijakan pull kami sendiri yang
menyaring sampel - persis sensor yang sedang kuburu lewat P17. Karena itu dia **tidak boleh** masuk
gerbang apa pun, dan tumpukan diuji ulang tanpanya (§2 baris 2) untuk membuktikan sisanya berdiri
sendiri.

## 4. Yang menahan semua ini (dibaca sebelum memakai angka di atas)

| № | batas | angka |
|---|---|---|
| 1 | **Kami baru bisa menilai 12,7 % dari kandidat** | 807 dari ~6.373 kejadian terukur; 5.085 dibuang karena tidak ada harga ≤10 menit sebelum beli, 481 karena tidak ada harga keluar |
| 2 | Satu jendela, satu rezim | umur rekaman 43 jam; belum ada hari kedua |
| 3 | Panel pilihan vendor | maker = yang ditampilkan GMGN; kerumunan tak terlihat = batas bawah |
| 4 | Bukan PnL | belum ada fill nyata, belum ada biaya keluar, belum ada ukuran posisi; ini probabilitas 30 menit |
| 5 | Kelas bersarang | `ge2`/`ge3`/`ge5` bukan tiga replikasi |

Baris 1 itulah yang P17 kerjakan; tanpa dia, angka di halaman ini tetap jadi statistik di antara
yang masih kelihatan akhirnya.

## 5. Apakah ini mengubah gerbang Fabius? Belum - dan itu keputusan, bukan kelambatan

Yang berubah: untuk pertama kalinya ada **dua aspek independen** (kerumunan + sebaran dana) yang
masing-masing lolos uji yang sama dan bersama-sama memisahkan lebih kuat. Itu kandidat nyata untuk
gerbang ⑧ (`SEARAH`), dan P15 tinggal menunggu satu hal: **data hari kedua** dengan spesifikasi yang
sudah dikunci sebelum dilihat. Kalau hari kedua tidak memisahkan, halaman ini dicabut - bukan
"diperluas dengan penjelasan".

Baca ulang: `python -X utf8 tools/evidence_stack.py` ·
`python -X utf8 tools/flow_cluster_test.py --horizon 30 --window 15`

**Terkait:** [[06-Results/09 - Whale Cluster Test]] · [[06-Results/08 - Carry Study]] ·
[[03-Data/D2 - Wallet Flow]] · [[03-Data/D6 - Funding and OI History]] ·
[[TradingKnowledge/O5 - Whale dan Kohor Smart Money]] ·
[[TradingKnowledge/FD5 - Expectancy Bukan Win Rate]] ·
[[TradingKnowledge/EV3 - Signifikansi dan Multiple Testing]] ·
[[TradingKnowledge/GAP3 - Yang Punya Data Tapi Belum Diuji]]
