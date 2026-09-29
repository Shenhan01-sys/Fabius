---
tags: [results]
---

# 10 - Evidence Stack

> **DICABUT 28 Sep 09:4xZ - lihat [[06-Results/12 - Harga Masuk yang Benar]].**
> Efek yang halaman ini klaim hidup di **sisi harga masuk**, bukan di pasar: pada kejadian yang sama
> persis, mengganti `px` (harga transaksi lama yang di-stamp waktu kami menarik) dengan harga
> transaksi itu sendiri mengubah **+93,0 bps (p=0,0066) menjadi +0,1 (p=0,53)**, dan tidak ada
> aspek yang lolos BH. Angka di bawah dibiarkan utuh karena **urutan bagaimana kami sampai ke sana**
> adalah bagian dari hasilnya - tapi tidak satu pun dari angka itu boleh dikutip sebagai bukti.

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

Semua baris dihitung oleh `tools/evidence_variants.py` (28 Sep 07:40Z) di atas kejadian yang sama:

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
| 1 | **Yang bisa dinilai 807 dari 11.631 beli = 6,9 %** (12,7 % dari kandidat) | corong penuh run `081806Z`: 11.631 beli → **5.258** dibuang karena tumpang tindih dengan beli lain di token yang sama (< 1 horison) → **6.373** kandidat → **5.085** tanpa harga ≤10 m sebelum beli + **481** tanpa harga keluar → **807** |
| 2 | Satu jendela, satu rezim | umur rekaman 43 jam; belum ada hari kedua |
| 3 | Panel pilihan vendor | maker = yang ditampilkan GMGN; kerumunan tak terlihat = batas bawah |
| 4 | Bukan PnL | belum ada fill nyata, belum ada biaya keluar, belum ada ukuran posisi; ini probabilitas 30 menit |
| 5 | Kelas bersarang | `ge2`/`ge3`/`ge5` bukan tiga replikasi |

Baris 1 itulah yang P17 kerjakan; tanpa dia, angka di halaman ini tetap jadi statistik di antara
yang masih kelihatan akhirnya.

## 4b. Sumur harga: dua sumber, dan satu kejadian hanya boleh pakai satu

Alat sekarang membaca dua deret: `px` (GMGN, harga pool saat tarik) dan `wp` (DexScreener, pantau
2 jam dari P17). Aturannya bukan "mana yang ada". **KOREKSI 28 Sep 21:3xZ:** angka yang kutulis di bawah
("±0,16 %–0,40 %, empat sampel pertama") salah satu orde besaran. Pada **n=4.022 pasangan** berimpit
(`|dt| <= 5 m`, `tools/prices.py --report`): median **bertanda +10,1 bps**, tetapi **median absolut
899 bps**, p5 **−3.884**, p95 **+6.576**, maksimum **+106.724**. Jadi dua sumur ini berbeda puluhan
persen pada menit yang sama, dan 400 bps tempat efek §1 hidup itu **di bawah** noise-nya. Itu
membuat aturan satu-sumber justru lebih wajib, dengan alasan yang lebih keras: bukan cuma
"menciptakan angka yang tidak ada di pasar mana pun", tapi menciptakan angka yang **lebih besar
dari yang sedang diukur**. Yang berlaku: **masuk dan keluar wajib satu sumber**; kalau tidak ada satu pun sumber yang
mengcover kedua ujung, kejadian itu dibuang dan dihitung.

Keadaan `wp` juga berubah sejak halaman ini ditulis: **11.592 baris / 396 token / rentang
14,22 jam** (28 Sep 21:3xZ) setelah rantai #17/#18 menjalankan definisi baru. Cakupannya per kejadian
beli (horison 30 m, aturan satu sumber): `gmgn` **49,7 %**, `watch` **6,9 %**, keduanya 6,1 %,
**tak terpenuhi 49,5 %** - jadi sumur kedua menambah titik pengamatan, bukan mengganti yang lama. Simulasi atas data yang ada (`tools/watch_value_sim.py`):
**83,9 %** kejadian beli punya kemunculan token yang sama ≤ 2 jam sebelumnya, jadi batas 12,7 % itu
bukan batas pasar - itu batas sambungan kita.

Run `--px both` saat ini memberi **`rows_sha256` identik** dengan mode baku (`0x9f31f56bb76acf…`):
menambah sumber tidak menggeser satu angka pun, persis seperti yang seharusnya terjadi saat sumber
keduanya belum berisi.

## 4c. Batas yang ketemu SETELAH halaman ini ditulis: deret harga kami adalah tangga beku

Pembacaan ulang terhadap alatku sendiri (28 Sep 09:19-09:2xZ) menemukan sesuatu yang lebih dalam
dari semua ambang di §4: baris `px` yang kupakai sebagai "harga" **bukan ticker**. Ia membawa
`price_usd` dari transaksi terakhir token itu, tapi di-stamp dengan waktu tarikan
(`universe/record_wallet_flow.py` baris 113 + 132). Tidak ada transaksi baru = nilai lama dengan
stempel baru. Terukur: **71,7 % baris mengulang nilai sebelumnya**; kalau pengulangan itu dibuang,
deret menyusut 35.304 → 11.546 baris (−67,3 %).

Ini memukul dua kalimat di halaman ini, dan aku menulis koreksinya, bukan menghapusnya:

- "K=1 **−59,0** (seharga ongkos; tidak ke mana-mana)" - sebagian dari −59 itu adalah **lantai
  pengukuran**, bukan nasib pasar: harga keluar yang sama persis dengan harga masuk menghasilkan
  net = −ongkos secara aritmetis. Pada dataset kini "gross persis 0" terjadi 8,1 % (K=1) dan
  11,0 % (K≥2).
- "dua venue berbeda 0,16–0,40 %" - ternyata ada kejadian yang lebih besar: pada 25 token irisan,
  **8 di antaranya diam di GMGN sementara DexScreener bergerak**, dengan selisih nilai sampai
  ±20 %. Keduanya mengukur benda yang berbeda (harga transaksi terakhir vs harga pool kini).

**Yang tidak berubah - dan ini yang membuat koreksi ini bisa ditanggung.** Efek K≥2 diuji ulang
pada deret yang **pengulangan nilainya dibuang**: **+353,7 bps, CI [+2; +922], p=0,0009** (61 token,
n=192) versus **+334,8 CI [+2; +763] p=0,0016** pada deret apa adanya. Arah, besar, dan
signifikansinya sama, jadi kerumunan **bukan** artefak baris yang diulang. Nilai kanonik di §0/§1
(+393,4) adalah pembacaan pada dataset 43 jam; dataset ini sudah 49 jam dan efeknya mengecil ke
+334,8 - itu justru berita baik: angkanya bergerak bersama data, bukan tersandera satu run.

Konsekuensinya untuk sebuah agen yang harus **bertindak**, bukan cuma mencatat - terukur pada
41.119 baris yang sama: umur "harga kini" kami adalah **8,7 menit (median)**, **42 menit di p90**,
dan **2,6 jam pada maksimumnya**. Jadi saat alat kami berkata "harga dalam 10 menit terakhir",
itu berarti harga yang **kita lihat** dalam 10 menit terakhir, bukan harga yang **terjadi** dalam
10 menit terakhir - 45,7 % dari harga kami lebih tua dari itu di pasar. Ini tidak membatalkan uji
berpasangan (kedua ujung pakai aturan yang sama, di token yang sama), tapi membatalkan satu kalimat
yang lebih ambisius: **horison keputusan 30 menit tidak bisa ditebus dengan feeder berumur 42 menit
di ekornya.**

Yang sekarang jadi syarat, bukan pilihan: outcome yang dijual publik harus diukur pada sumur yang
**berdetak sendiri** (`wp` dari P17), dan itu P23. Perekam `px` juga harus ikut membawa waktu
transaksinya (`ttx`) supaya konsumen bisa menyaring kesegaran - itu P24, dan berkas datanya sudah
memiliki bahan bakunya (`tx.t`), jadi ini pekerjaan satu baris, bukan satu hari.

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
