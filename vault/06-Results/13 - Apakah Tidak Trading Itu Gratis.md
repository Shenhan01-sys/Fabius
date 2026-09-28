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

