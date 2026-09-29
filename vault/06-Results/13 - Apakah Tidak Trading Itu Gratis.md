---
tags: [hasil]
---

# 13 - Apakah Tidak Trading Itu Gratis

**Sumber:** `tools/mirror_test.py` + `tools/tail_test.py` (harga PERISTIWA, ongkos
59 bps dipotong) · 1.174 kejadian pada 404 token · horison 30 menit · dijalankan 28 Sep ±10:0xZ

**Ringkas:** pertanyaan builder: *"kalau dia cuma tahu kapan jangan masuk, apa bedanya dengan tidak
trade sama sekali?"* Jawabannya terukur, dan dia dua bagian. (1) **Tidak trading TIDAK gratis**:
harapan yang di-winsor (dibatasi ±2.000 bps) dari membuka posisi acak di universe yang disajikan
feed ini adalah **+82,7 bps per posisi 30 menit**, walau medianya −58,9. Datanya miring kanan
parah: **33,9 % kejadian naik ≥ +500 bps dalam 30 menit**, p90 = +8.854 bps. (2) **Tapi kami tidak
punya penyaring yang menaikkan angka itu.** Tidak satu pun aspek aliran yang kami punya menaikkan
peluang ekor di atas baseline - yang lolos BH justru naik dengan arah **minus**. Jadi yang kami
miliki hari ini adalah **rem**, bukan **gas**: kerumunan jual menurunkan P(≥+500) dari 33,9 % ke
**20,3–22,5 %**, dan kerumunan beli adalah waktu yang tepat untuk **keluar**, bukan masuk.

## 1. Bentuk datanya (dan kenapa medianku selama ini menyesatkan)

| statistik net 30 menit (bps) | nilai |
|---|---|
| median (semua kejadian) | **−58,9** (= persis ongkos round-trip: tidak bergerak) |
| % kejadian yang net-nya positif | 41,7 % |
| p75 / p90 / p99 | **+1.368** / **+8.854** / **+105.639** |
| P(net ≥ +500 bps) | **33,9 %** |
| **mean winsorized ±2.000 bps** | **+82,7 bps per posisi** |

Yang kuterbitkan sepanjang hari ini adalah median. Untuk payoff yang 1 dari 3-nya naik ≥5 % dan
ekornya sampai 1.000x, median adalah ukuran tengah yang jujur tapi **bukan** ukuran yang memutuskan
"boleh masuk tidak". [[TradingKnowledge/FD5 - Expectancy Bukan Win Rate]] sudah bilang begitu dan
aku tidak menerapkannya - itu kesalahan metode, bukan cuma angka.

Winsorizing ±2.000 bps dipasang justru supaya satu pool likuiditas kecil yang naik 10x tidak
menyamar jadi strategi: angka +82,7 bps itu harapan yang *masuk akal* untuk posisi kecil, bukan
janji. Yang tidak kami punya: **fill dan kedalaman** - dan itu membuat angka ini belum boleh
dijual sebagai PnL (lihat §4).

## 2. Tidak ada aspek yang menaikkan ekor; dua aspek menurunkannya

Fisher eksak satu arah vs baseline, BH α 0,10 (n aspek ≥ 20):

| aspek (point-in-time, hanya data ≤ t) | n | P(≥+500 bps) | p vs baseline 33,9 % | P(≥p75) | p | mean winso (CI 95 %) |
|---|---|---|---|---|---|---|
| `beli_2` (≥2 maker beli /15 m) | 201 | 30,3 % | 0,19 | 21,9 % | 0,23 | −228 [−427; −27] |
| `beli_3` | 117 | 29,9 % | 0,25 | 22,2 % | 0,36 | −325 [−596; −55] |
| `jual_2` (≥2 maker jual) | 160 | **22,5 %** | **0,0028** | 17,5 % | 0,027 | −422 [−631; −197] |
| `jual_3` | 106 | 23,6 % | **0,0211** | 18,9 % | 0,10 | −570 [−857; −290] |
| `jual_bersih` (jual ≥1,5× beli) | 74 | **20,3 %** | **0,0112** | 14,9 % | 0,038 | −484 [−799; −169] |
| `sepi_beli` (≤1 maker, <100 USD) | 555 | 29,9 % | 0,056 | 21,3 % | 0,047 | −4 [−113; +107] |
| `tarik_dari_puncak` (−30 % dari puncak 60 m) | 138 | 31,9 % | 0,42 | 26,8 % | 0,37 | −424 [−683; −158] |
| `jatuh_dalam` (−15 % dari 15 m terakhir) | 75 | 30,7 % | 0,37 | 26,7 % | 0,43 | −435 [−798; −62] |

**BH α 0,10 untuk "ekor di atas baseline": TIDAK ADA.** Yang lolos BH adalah ekor yang **turun**:
`jual_2`, `jual_3`, `jual_bersih`. Membeli saat kerumunan beli tidak menaikkan peluang jackpot
(30,3 % vs 33,9 % baseline, p=0,19) dan harapan yang di-winsor justru minus.

## 3. Jadi Fabius punya apa hari ini

| yang diukur | angka | artinya untuk agen |
|---|---|---|
| kerumunan **jual** dalam 15 m | P(≥+500) turun ke **20,3–22,5 %** (p=0,003–0,02, lolos BH) | **VETO masuk.** Ini gerbang ⑧ versi yang benar: `KONTRA`/`JANGAN` saat maker ramai keluar |
| kerumunan **beli** dalam 15 m | net absolut −78,2 vs baseline −58,7; berpasangan **−313 CI [−1041; −11]** | **waktu keluar**, bukan waktu masuk: memegang 30 menit lagi sesudah kerumunan masuk lebih buruk daripada keluar sekarang |
| membuka posisi tanpa penyaring | +82,7 bps winso/posisi, median −58,9 | "tidak trading" memang tidak gratis - tapi ini **universe feed**, bukan hasil seleksi kami; menjualnya sebagai edge kami = bohong |
| cermin "jual ramai -> harga naik" (yang kuhipotesiskan pagi ini) | **SALAH**: jual_2 = −690 bps vs baseline | hipotesis fade tidak terbukti di sisi masuk; jangan dibangun apa pun di atasnya |

Yang **belum** bisa kami jawab dan itu batas produk, bukan malu-malu: **kapan boleh masuk**.
Jawabannya tidak akan datang dari aspek aliran yang sudah kami punya (semuanya sudah dites di atas,
dan tidak ada yang menaikkan ekor). Kandidat yang masuk akal dan belum diukur: posisi dalam
**siklus hidup pool** (umur, likuiditas, volum 1 jam, buys/sells rasio dari `wp`), bukan kerumunan
maker - dan itu P26, yang butuh rekaman pantau yang sudah berumur.

## 3b. Tiga kebijakan, bukan dua - dan ini jawaban untuk "apa bedanya dengan orang penakut"

`tools/policy_test.py` (horison 30 m, harga peristiwa, ongkos 59 bps sudah dipotong, mean
winsorized ±2.000, bootstrap 4.000):

| kebijakan | n dipakai | mean winso (CI 95 %) | median | P(≥+500) | total bps |
|---|---|---|---|---|---|
| **A** tidak pernah masuk ("orang penakut") | 0 | **0,0** (tetap) | 0,0 | 0,0 % | 0 |
| **B** masuk semua kejadian feed | 1.174 (100 %) | **+82,7** [+5,0; +159,1] | −58,9 | 33,9 % | 97.091 |
| **C** B + veto kerumunan jual | 1.014 (86,4 %) | **+162,3** [+80,4; +243,0] | −57,0 | 35,7 % | 164.555 |
| **D** C + keluar saat kerumunan beli | - | **TIDAK DIUJI** (butuh harga per detik saat keluar) | | | |

Pada horison 60 m arahnya sama, lebih kecil: B **+112,1** → C **+153,6** (+41,5 bps/kejadian,
10,6 % kejadian dilewati).

Tiga hal yang harus dibaca bersama tabel ini:

- **Yang dibandingkan bukan "Fabius vs tidak trading".** Orang yang tidak berani masuk memilih A,
  dan A itu **0**, bukan "sama-sama aman". Di universe ini baseline buta (B) sudah **+82,7
  bps/posisi**; rem kami menaikkan itu ke **+162,3** dengan melewatkan hanya 13,6 % kejadian.
  Jadi rem yang kami punya **bukan** rasa takut yang dibungkus - ia berbayar, dan terukur.
- **Tapi B itu milik universe, bukan alpha kami**, dan C pun masih seleksi minus satu arah. Angka
  +162,3 tidak berarti "Fabius tahu kapan masuk"; ia berarti "Fabius tahu 1 dari 7 jenis posisi
  yang harus dilewati". Sisanya masih pertanyaan terbuka (§3).
- **Mean ≠ bisa diambil.** Tanpa kedalaman dan fill, +162,3 bps adalah harapan per kejadian pada
  harga peristiwa, bukan PnL pada ukuran posisi tertentu. Satu pool $6k yang naik 10x menaikkan
  mean tanpa pernah bisa kami masuki sebesar itu.

## 3c. Percobaan pertama "kapan boleh masuk": menyortir 5 posisi/hari - dan ia TIDAK BISA dimenangkan dengan data ini

`tools/select_test.py` (28 Sep ±10:2xZ). Agen punya `dailyCap` 5, jadi pertanyaannya: dari kandidat
yang lolos gerbang, 5 yang mana? Yang disortir: **10 kolom siklus hidup pool** dari snapshot universe
kita sendiri, dengan aturan point-in-time (hanya snapshot `epoch <= t` yang boleh dipakai).

| kebijakan | posisi | mean winso (bps) |
|---|---|---|
| first-5 (tanpa sortir) | 15 | **−379,0** |
| random-5 (4.000 undian) | 15 | −27,0 |
| **CI 95 % acak** | | **[−440,1; +411,4]** |
| `top-5 lock_percent` / `bundler_rate` | 15 | +133,6 / +179,0 → **seri** |
| 8 fitur lainnya | 15 | −24,0 s/d −165,7 → **seri semua** |

**Tidak ada satu pun fitur yang keluar dari pita acak.** Tapi jangan baca ini sebagai "tidak ada
efek": ini soal **daya**, dan daya itu bisa dihitung. Dari lebar pita acak (±425 bps pada 15 posisi),
simpangan per posisi ≈ **841 bps**, jadi untuk memutuskan perbedaan sebesar:

| resolusi yang diinginkan | posisi yang dibutuhkan | pada 5 posisi/hari |
|---|---|---|
| ±200 bps | ≈ 68 | **±14 hari** |
| ±100 bps | ≈ 272 | **±55 hari** |

Tenggat kami 30 Sep. Artinya jujur: **"kapan boleh masuk" tidak akan pernah bisa diuji dalam budget
5 posisi/hari sebelum demo.** Yang TIDAK tunduk pada batas itu adalah pertanyaan "mana yang jangan"
(veto, n=1.174, CI di §3b) - dan karena itu §3b tetap berdiri sedang §3c tidak akan berdiri
tepat waktu.

## 3d. Uji kuintil TANPA budget harian: satu kandidat muncul, dan satu perangkap ketahuan

`tools/quintile_test.py` (28 Sep ±10:4xZ): 1.014 kejadian yang lolos gerbang, dikelompokkan ke
kuintil fitur siklus hidup pool (point-in-time: hanya snapshot `epoch <= t`). Alat ini lahir karena
kesalahan pertamanya: `flow_cluster_test.fisher_p` membandingkan probabilitas tabel dengan yang
teramati (ekor **dua-arah**), jadi kuintil yang justru jauh lebih buruk pun mengembalikan p ≈ 0 -
`volume_24h` "lolos" dengan P(≥+500) **0,0 % vs 31,4 %**. Sudah diganti dengan ekor hipergeometrik
satu arah (`ekor_hipergeo`), dan kolomnya sekarang konsisten dengan arahnya.

> **⚠ KOREKSI 29 Sep 2026 - kolom "MW p" di tabel di bawah DICABUT.** `mann_whitney_p` kami
> menyusun daftar peringkat dengan `sorted(a) + sorted(b)` (dua kelompok terurut, digabung - bukan
> digabung lalu diurut) dan menjumlah peringkat ties sebagai `avg × ukuran kelompok`. Efeknya
> terukur, bukan dugaan: pada dua kelompok yang jelas terpisah (A = +120…+144, B = −300…−324) alat
> lama mengembalikan **p = 1,000000** (arah terbalik), dan pada tumpang tindih ringan
> **0,022311** vs yang benar **0,999995**. Jalur lama-vs-baru:
> `python -X utf8 _research/mw_lama_baru.py`.
>
> Dijalankan ulang 29 Sep 05:14Z dengan fungsi yang dibetulkan (`tools/flow_cluster_test.py`
> sekarang punya `mw_self_test()`): **kolom Mann-Whitney kehilangan semua "lolos"-nya** -
> `lock_percent` **0,6441** (bukan 0,0000), `n_maker_jendela` 0,2066, `usd_b_jendela` 0,4027,
> `sniper_count` 0,2801, `bundler_rate` 0,3288; BH pada harapan winso = **TIDAK ADA fitur**. Yang
> tetap berdiri adalah uji Fisher satu arah (`ekor_hipergeo`) pada P(≥+500): `lock_percent`,
> `n_maker_jendela`, `sniper_count`, `usd_b_jendela`. Jadi klaim "bertahan dari DUA uji berbeda"
> turun jadi **satu uji** - dan itu bukan detail redaksi, itu separuh dayanya.
>
> Angka kuintil di bawah adalah run 28 Sep; run 29 Sep (1.763 kejadian, 1.531 lolos gerbang, 398
> berfitur = 26,0 %, baseline berfitur **−61,3 bps**, P(≥+500) **16,8 %**, median −59,2) memberi
> `lock_percent` Q1 −137,3 → Q5 −52,1 - **dua-duanya minus**, sedangkan 28 Sep −60,1 → +66,0.
> Kandidatnya bergeser turun bahkan sebelum koreksi alat; setelah koreksi, dia tinggal satu uji.

Yang bertahan dari **dua** uji berbeda (Mann-Whitney pada harapan winso + Fisher satu arah pada
P(≥+500 bps)), BH α 0,10 - **kolom MW dicabut 29 Sep, lihat kotak di atas**:

| fitur | Q1 → Q5 harapan winso (bps) | P(≥+500) Q5 vs Q1 | MW p | Fisher p |
|---|---|---|---|---|
| **`lock_percent`** (LP dikunci) | −60,1 → **+66,0** | **36,0 % vs 0,0 %** | **0,0000** | **0,0010** |
| `usd_b_jendela` (ukuran beli) | −78,6 → −64,5 (dua-duanya minus) | 11,8 % vs 0,0 % | 0,0000 | 0,0134 |
| `sniper_count` | −60,1 → −32,3 | 24,0 % vs 0,0 % | 0,55 | 0,0127 |
| `bundler_rate` | −63,5 → **+188,4** | 20,0 % vs 20,8 % | 0,0035 | 0,66 |

**Kenapa ini belum boleh dijual.** Kuintilnya berisi 24–51 kejadian; satu pool yang naik 10x bisa
memindahkan mean puluhan bps. Dan `bundler_rate` adalah contoh baiknya: kuintil teratasnya +188,4
bps - angka yang **bertentangan dengan veto kita sendiri** (`bundler>30%` sudah menyingkirkan
token di universe). Bacaan yang jujur: itu noise, bukan temuan. Yang tinggal sebagai *kandidat*:
**likuiditas yang dikunci** (`lock_percent`) sebagai syarat masuk, bukan kerumunan maker - dan ia
harus melewati hari-hari berikutnya, bukan meyakinkan kita malam ini.

## 3e. Dan perangkap yang lebih penting dari semua itu: yang bisa kami deskripsikan justru yang paling buruk

Baseline **pada subset yang punya snapshot universe point-in-time** adalah **−64,7 bps** harapan
winso dan P(≥+500) **14,5 %** - padahal baseline semua kejadian yang boleh **+82,7 bps** dan
**33,9 %**. Bedanya bukan nasib: **cakupan itu sendiri terpilih**. Snapshot universe kami berasal
dari daftar `trending_pools`/`new_pools`, jadi token yang bisa kami deskripsikan dengan kolom
siklus hidup adalah token yang **sudah panas** pada jam kami mengambilnya - yaitu kelompok yang
peluang jackpotnya paling tipis.

Konsekuensinya langsung untuk produk: **fitur apa pun yang kami temukan pada 25,1 % kejadian ini
berlaku pada subpopulasi terburuk, dan tidak otomatis berlaku pada 74,9 % sisanya.** Itu sebabnya
P26 tidak cukup "cari fitur" - ia butuh cakupan yang tidak dipilih oleh panasnya pool, dan satu-
satunya jalur ke sana adalah `wp` (ditarik seragam untuk semua token yang pernah lewat, bukan yang
sedang naik daun).

## 4. Yang menahan halaman ini

Satu jendela 49 jam, satu rezim. Belum ada fill, belum ada kedalaman: P(≥+500 bps) dihitung pada
harga peristiwa tanpa bertanya apakah ukuran posisi kami bisa masuk ke pool itu - dan `liq_usd` baru
kita rekam sejak hari ini. Winsor ±2.000 bps menahan satu 10x tapi bukan seluruhnya. Angka
terkecil di sini n=74 (satu aspek) - cukup untuk tanda, tidak untuk keputusan.

Baca ulang: `python -X utf8 tools/mirror_test.py` · `python -X utf8 tools/tail_test.py`

**Terkait:** [[06-Results/12 - Harga Masuk yang Benar]] · [[06-Results/04 - Negative Results]] ·
[[06-Results/08 - Carry Study]] · [[03-Data/D2 - Wallet Flow]] ·
[[TradingKnowledge/FD5 - Expectancy Bukan Win Rate]] · [[TradingKnowledge/FD6 - Ukuran Posisi]] ·
[[TradingKnowledge/QT4 - Overfitting dan Validasi]] · [[TradingKnowledge/ST6 - Aliran On-Chain Fabius]]

