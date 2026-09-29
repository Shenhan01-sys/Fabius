---
tags: [hasil, "venue", "E20", "E26", "likuiditas", "retraction"]
---

# 28 - Venue Kami Bukan Pasar (E20 + E26)

**Bagian dari:** [[06-Results/00 - Hub Results]] · [[06-Results/19 - Umur Posisi]] §3 ·
[[08-Backlog/02 - Epik Alasan Masuk]] §3g
**Alat:** `tools/perp_liveness.py` · `tools/perp_bump.py` · pembanding: `tools/venue_bridge.py`,
`tools/horizon_decay.py` · **Jam:** 29 Sep 2026 ±13:55Z; **diperbarui 14:12Z oleh P59** - cache 1 m jadi 3 hari, yang mengubah n E26 dari 15 jadi 31 dan membatalkan besaran versi pertama (§4)

## 1. Kenapa halaman ini ada

Tembok yang kami kutip sejak F-D43 adalah **keberadaan**: hanya 3,1 % kabar beli ⑦ terjadi di token
yang ada di venue perp kami. Hari ini tembok itu diukur ulang dan ternyata bukan keberadaan - itu
**kehidupan**. Dan begitu itu diukur, pertanyaan "apakah bump E11 bisa kami ambil di substrate yang
bisa dieksekusi" akhirnya punya jawaban, bukan asumsi.

## 2. Parser lama membuang 17 entri daftar - dan itu mengubah dua angka yang selama ini dipakai satu

`tools/venue_bridge.py` memotong sufiks kuotasi dengan daftar tetap (`USDT`, `USDC`, `PERP`). Daftar
Aster punya entri yang tidak cocok pola itu: `BTCU`, `BTCUSD1`, `ETHUSD1`, `SKHYNIXUSD1`, `MUUSD1` -
**17 dari 584**. Basis yang dihasilkan parser lama adalah string utuh (`BTCUSD1`), jadi kabar "BTC"
tidak pernah ketemu.

```text
kabar beli 1 hari: 13.293 kejadian pada 1.172 simbol
   reachable sebagai ASET yang sama (BTC/ETH/SOL ikut): 41 simbol, 779 kabar (5,86 %)
   reachable sebagai PASANGAN yang stringnya ketemu parser lama: 301 kabar (2,26 %)
```

**Angka ini jendela bergulir 24 jam, jadi ia bergerak sepanjang hari**: 13:50Z = 2,26 % / 5,86 %; 14:17Z = **2,40 % / 6,30 %** (865 kabar, `decisions/e20-perp-liveness-20260929T141703Z.json`). Yang tetap adalah **rasio antara keduanya** dan kelas simbolnya (HIDUP 5 / TIPIS 17 / MATI 17 pada kedua run). Kutip selalu jam + berkasnya.

Ini dua pertanyaan berbeda dan **tidak boleh saling menggantikan**: "bisakah saya memiliki pandangan
atas aset ini di venue kami" (5,86 %) vs "bisakah saya memperdagangkan pasangan yang persis sama dengan
yang diberitakan" (2,26 %). F-D57. Angka 3,1 % yang selama ini dikutip adalah ukuran all-time dari
parser yang salah ini - ia bukan salah arah, tapi bukan angka yang seharusnya.

## 3. E20 - dari yang reachable, berapa yang harganya bergerak pada resolusi menit

41 simbol reachable, 1 m klines 24 jam terakhir (`tools/perp_liveness.py`):

```text
HIDUP 5 (3,3 % dari kabar) | TIPIS 17 (25,0 %) | MATI 17 (70,6 %)
yang HIDUP: MARSCOINUSDT(13), ZECUSDT(7), DOGEUSDT(4), ASTERUSDT(1), LINKUSDT(1)
```

Isi kelas MATI bukan pendapat, tapi baris datanya: `BNCUSD1` - simbol dengan kabar **paling banyak**
(478 dari 779) - punya **96,0 % menit tanpa transaksi**, 41 harga berbeda sepanjang hari, dan run
tanpa perubahan harga terpanjang **446 menit**. `CUSDT` 99,6 % / beku 671 m. `PEOPLEUSDT` 99,5 % /
619 m. Kelas TIPIS punya median **77,9 %** menit nol volume.

**0,20 %** - itu bagian dari 13.293 kabar beli hari ini yang terjadi pada simbol yang harga perp-nya
benar-benar bergerak di resolusi menit (26 dari 13.293; dengan pemetaan aset 26/779 = 3,3 %).

Batas yang tidak boleh dilewati: klines mencatat transaksi yang **terjadi**, bukan kedalaman buku.
"HIDUP" di sini = layak diuji pada horison menit; **bukan** "layak dieksekusi ukuran besar".

## 4. E26 - di yang HIDUP pun, bump-nya tidak ada di harga perp

**Koreksi dalam jam yang sama (P59).** Angka pertama di bawah lahir dari cache 1 m selama 24 jam: 32
kejadian, tapi hanya **15** yang jendelanya lengkap - 17 terbuang di tepi seri. Cache diperpanjang ke
3 hari (mengubah **n**, bukan harganya), dan sekarang 31 dari 33 kejadian dinilai. Kedua versi
dicetak, karena yang satu membatalkan klaim besaran yang lain:

```text
versi n=15 (cache 24 jam; 17 kejadian hilang) - TIDAK BOLEH DIKUTIP LAGI:
   @2 m mean  +2,0 | @5 m mean  -7,3 | @30 m mean -34,4 | placebo +0,7 / +6,9 / -9,6
   berpasangan 5m-vs-30m: median -0,5 bps | menang 7 kalah 8 | p=0,696

versi n=31 (cache 3 hari, P59 - yang dipakai):
   @2 m mean  -2,6 median +2,1 | masuk +1 m  -4,2 | placebo  +3,3
   @5 m mean +15,2 median +2,1 | masuk +1 m +11,4 | placebo +10,7
   @30 m mean +18,1 median +6,9 | masuk +1 m  +9,8 | placebo  -8,1
   berpasangan 5m-vs-30m: median +14,8 bps | menang 16 kalah 15 | p=0,50000
```

Dua hal, dan keduanya harus disebut bersama:

1. **Kesimpulannya tidak berubah: tidak ada bump yang bisa dibedakan dari nol.** Mean horison pendek
   sekarang +15,2 bps - tapi placebo-nya +10,7, jadi selisihnya 4,5 bps; dan tanda-uji berpasangan
   5m-vs-30m memberi **p=0,50** (16 menang, 15 kalah). Sebagai pembanding, E11 di deret spot memberi
   +202,6 dengan placebo **datar −180**. Di substrate kami: tidak ada apa-apa.
2. **Tanda dan besar mean bergerak bersama jendela pengukuran.** −7,3 → +15,2 hanya karena 16 kejadian
   yang tadinya terbuang sekarang ikut dinilai. Ini F-D51 (artefak budget) dalam wujud lain: **n bukan
   hiasan, n itu alat**. Angka E26 mana pun yang dikutip tanpa menyebut panjang cache-nya tidak boleh
   dipercaya - termasuk yang di halaman ini.

Sensitivitas kelas TIPIS tetap kalimat paling jujur yang bisa kita dapat: pada n=39, median return
**tepat 0,0 bps di @2, @5, dan @30 m** - deretnya beku, jadi tidak ada yang terjadi untuk diukur. Itu
bukan hasil nol; itu tidak ada pengukuran.

## 5. Apa yang boleh dan tidak boleh disimpulkan

**Boleh:** (a) tembok eksekusi kami hari ini adalah **likuiditas pada resolusi menit**, bukan
kelengkapan daftar; (b) klaim "agen kami bisa mengambil bump dua menit" **tidak punya dukungan** di
substrate tempat agen kami bisa mengirim order, dan sekarang ada angkanya; (c) E11 tetap sahih sebagai
pengukuran deret spot - ia tidak dibatalkan, hanya dipindahkan ke tempatnya: observasi, bukan peluang.

**Tidak boleh:** (a) menyebut n=15/39 vonis - ini satu hari, lima simbol hidup, dua di antaranya
menyumbang sebagian besar kejadian; (b) membaca MATI sebagai "tidak bisa diisi sama sekali" -
kedalaman buku ⑨ baru direkam untuk 26 simbol dan belum kita bacakan per simbol ini; (c) menyimpulkan
"pindah venue" sebagai perbaikan - venue lain punya tembok sendiri dan itu perlu diukur, bukan
diharapkan; (d) 17 dari 32 kejadian hilang karena jendela seri (cache 1 m 24 jam) - dicatat sebagai
kehilangan, dan itu sudah diperbaiki 14:12Z (**P59**) - lihat §4, yang menelan angka versi pertama.

## 7. Ternyata bukan cuma kami - dan ini membalik sebagian tuduhan saya (P61, F-D59)

Sebelum menerima kesimpulan §3 sebagai "nasib long-tail perp", saya ukur venue pembanding dengan
**penggaris yang sama persis** (`tools/gate_liveness.py` mengimpor `suhu()`/`kelas()` E20; tidak ada
salinan rumus) pada **daftar simbol yang sama**:

```text
35 dari 41 simbol reachable kami juga terdaftar di Gate Futures
   HIDUP  gate 14 simbol / 157 kabar | aster  5 simbol /  27 kabar
   TIPIS  gate 21 simbol / 102 kabar | aster 14 simbol / 191 kabar
   MATI   gate  0 simbol /   0 kabar | aster 14 simbol /  32 kabar
   HIDUP di Gate tapi tidak di Aster: Q, USELESS, 牛来, O, TRX, GWEI, UB, BOME, PEOPLE  (9 simbol)
   HIDUP di Aster tapi tidak di Gate: tidak ada
   kelas sama di kedua venue: 15 dari 35
```

Jadi buku beku itu **sebagian besar milik venue kami**, bukan milik kelas asetnya: pada kontrak yang sama,
venue pembanding tidak punya satu pun simbol MATI dan punya 5,8× lebih banyak kabar di simbol yang hidup.
Satu kecelakaan alatku sendiri ikut memperbaikinya: kontrak non-Latin (`牛来_USDT`) membuat URL saya
melempar `UnicodeEncodeError`, dan itu sempat tercatat sebagai "TIDAK-ADA-DATA" - sesudah query diquote,
dua simbol itu ternyata TIPIS/HIDUP. Kehilangan yang saya banggakan "jujur" itu ternyata bug pemetaan
(F-D47 sekali lagi: yang salah hampir selalu ada di sisi kita).

Catatan skala yang tidak boleh hilang: `v` di Gate adalah **jumlah kontrak**, bukan USD atau unit basis.
Yang dipakai di halaman ini hanya "nol vs bukan nol" dan "berapa lama harga tidak berubah" - dua-duanya
tidak bergantung skala. Membandingkan besar volume antar venue butuh konversi lebih dulu dan belum saya
lakukan.

## 8. Tapi buku yang hidup TIDAK menyelamatkan bump-nya (E27, F-D60)

Ini yang menentukan, karena §7 memberi kesempatan terakhir bagi hipotesis "venue kami terlalu beku
untuk menunjukkan bump". `tools/gate_bump.py` menguji 31 kejadian pada 14 simbol HIDUP di venue
pembanding - matematikanya diimpor dari E26, deretnya dari venue itu:

```text
HIDUP (n=31, 14 simbol, 0 hilang):
   @2 m asli  +4,7 | median +0,7 | masuk +1 m  -1,7 | placebo  -2,8
   @5 m asli  +2,0 | median +4,6 | masuk +1 m  -4,1 | placebo  -7,4
   @30m asli  -3,2 | median +12,1| masuk +1 m  -7,7 | placebo  -3,4
   berpasangan 5m vs 30m: median -9,0 bps | menang 14 kalah 17 | p=0,76344
TIPIS (n=40, 21 simbol):
   @2 m +9,3 (placebo +2,5) | @5 m +13,2 (placebo +4,9) | @30 m +0,8 (placebo +12,1)
   berpasangan: +8,8 bps | menang 21 kalah 19 | p=0,43731
```

**Efeknya di venue hidup: +2 sampai +13 bps di menit ke-5.** E11 memberi +202,6 di deret spot BSC; ongkos
round-trip kami **59 bps**. Jadi bahkan di tempat bukunya benar-benar bergerak, horison pendek (a) satu
ordo lebih kecil dari yang kami klaim, dan (b) **habis sebelum ongkos**, dan (c) tanda-uji berpasangan
melawan horison panjang tetap nondeterministik (p=0,76 dan p=0,44).

Rangkaiannya sekarang lengkap, dan tiga alat berbeda sepakat:

| dugaan kenapa "edge 2 menit" tidak jadi uang | diuji dengan | jawab |
|---|---|---|
| kami terlalu lambat | `fast_lane.py --report` (F-D54) | **salah** - umur keputusan 61 d |
| venue kami terlalu beku | `gate_liveness.py` + `gate_bump.py` (F-D59, F-D60) | **salah** - di venue hidup pun tinggal +2..+13 bps |
| harga masuk kami bukan harga yang dilihat sinyal | `fill_gap.py` (E21) + `fast_lane` (F-D54) | **benar dan cukup** - `i` +245 bps; `entry_px` di atas harga whale pada 16/25 |

Yang tersisa bukan "maka tinggal ganti venue": ganti venue memperbaiki **eksekusi** (fill, slippage,
probabilitas isi), bukan **alasan masuk**. Itu perbedaan yang harus disebut dengan benar di depan juri,
dan itu juga yang membuat keputusan produk berikutnya menjadi pertanyaan builder, bukan pertanyaan
backtest (P62).

## 9. Yang mati bukan kutipannya - tapi bukunya dalam 10 bps pertama (P60, sebagian)

`tools/book_stale.py` membaca ⑨ yang **sudah** terekam (daftar pantau tidak disentuh - F-D53 masih
berlaku sampai vonis E16), 26 simbol, ~67-78 snapshot masing-masing, rentang 4,7 jam:

```text
              spread median   ±10 bps depth   ±50 bps depth   kutipan beku
BTCUSDT             0,01 bps      1.584.224       1.584.224        0,0 %
ETHUSDT             0,04 bps        668.423         668.423        0,0 %
SOLUSDT             0,83 bps      1.658.575       2.285.152        5,2 %
ASTERUSDT           2,75 bps         47.903         172.172        6,0 %
BOMEUSDT           15,12 bps          1.000          10.498        1,5 %
CAKEUSDT            7,73 bps         1.212           7.647        1,5 %
AIUSDT             66,27 bps              0              27       13,4 %
BREWUSDT          139,26 bps              0               0       12,1 %
4STOCKUSDT        310,03 bps              0               0        7,5 %
ASTEROIDUSDT      550,83 bps              0               0       22,4 %
B-MONEYUSDT       654,21 bps              0               0       48,5 %
```

Tiga hal yang sebelumnya tercampur sekarang terpisah:

1. **Kutipan umumnya HIDUP.** Yang beku kutipannya cuma B-MONEY (48,5 % snapshot identik). Sisanya
   0-13 % - jadi "tidak ada transaksi" (E20) **bukan** karena market maker berhenti mengutip.
2. **Tapi tidak ada yang bisa dibeli di dekat harga.** Untuk AI/BREW/4STOCK/ASTEROID/B-MONEY, kedalaman
   dalam ±10 bps = **nol**: order market apa pun harus naik 66-654 bps lebih dulu sebelum bertemu
   volume. Ini mekanisme yang selama ini cuma saya asumsikan di `i` (E21, +245 bps) dan di kerugian
   F-D54 (-519 bps) - sekarang ada angkanya per simbol, bukan sebagai model.
3. **BOME adalah kasus yang memisahkan dua penjelasan.** Kutipannya hidup (spread 15,1 bps, beku 1,5 %)
   tapi klines-nya 96,9 % menit tanpa transaksi (E20). Jadi yang mati di sana **minat**, bukan kuotasi -
   dan itu tidak bisa diperbaiki dengan venue lain yang lebih ramai kutipan.

**Untuk trailing stop (E17/F-D48), ini bagian yang menentukan:** algebra saya menahan sebuah stop hanya
kalau `pi > 2s + i + C`. Pada 4STOCK/ASTEROID/B-MONEY, `s` (setengah spread) sudah 155-327 bps, dan `i`
tidak bisa di bawah selisih itu karena tidak ada likuiditas di dalam 10 bps. Jadi jawaban atas
"trailing kok tidak menolong" bukan lagi "belum cukup data 1 menit" - pada separuh buku yang kami pantau,
**tidak ada angka `d` yang memenuhi**, dan alat E17-gate menghitung 63-66 % kejadian berjendela sah
karena ia memakai spread median 0,04 bps dari level teratas, bukan persebaran per simbol seperti ini.

Belum terukur (masih P60 utuh): MARSCOIN/ZEC/DOGE/LINK tidak ada di ⑨, jadi hanya 3 dari 5 simbol HIDUP
yang bisa dibaca bukunya; menambah daftar itu adalah P54, sesudah E16 divonis.

## 10. Diukur ulang 29 Sep 22:31-22:32Z - dan angka E27 bergerak, yang membongkar alatnya sendiri

Langkah P54 menyuruhku mengukur ulang dua hal yang tidak terkunci dan menuliskannya sebagai koreksi,
bukan penimpaan. Ini hasilnya - dan isinya lebih banyak tentang **alat** daripada tentang pasar.

**E20 (`tools/perp_liveness.py`, artefak `decisions/e20-perp-liveness-20260929T223147Z.json`):**

```text
kabar beli 24 jam        13.293 -> 15.034 kejadian (1.172 -> 1.201 simbol)
reachable ASET            5,86 % -> 7,41 %  (41 -> 45 simbol; 779 -> 1.114 kabar)
reachable PASANGAN        2,26 % -> 2,16 %  (301 -> 324 kabar)
kelas                   HIDUP 5 / TIPIS 17 / MATI 17  ->  HIDUP 8 / TIPIS 17 / MATI 19
HIDUP                     MARSCOIN, ZEC, DOGE, ASTER, LINK
                       -> MARSCOIN, AI, ZEC, DOGE, SOON, ASTER, SPCXUSD1, LINK
```

Yang berubah bukan pasarnya sendirian - jendela 24 jam **bergeser**, dan kelas ikut bergeser bersamanya:
`AIUSDT` naik dari 66,3 bps spread menjadi nol-volume 9,5 % / 861 harga berbeda seharian (TIPIS →
**HIDUP**), dan `SOON`/`SPCXUSD1` masuk. Kelas `MATI` membesar 17 → 19.

**E27 (`tools/gate_bump.py`, artefak `decisions/e27-gate-bump-20260929T223206Z.json`) - dan inilah
yang harus ditulis dengan tangan gemetar:**

```text
                     21:15Z                         22:32Z
n                    31                             31 (0 hilang)
@5 m  asli/placebo   +2,0 /  -7,4                   -9,8 / -12,2
@30m  asli/placebo   -3,2 /  -3,4                  +15,1 / -36,0
berpasangan 5-30 m   -9,0 bps | 14M/17K | p=0,763  -29,4 bps | 9M/22K | p=0,995
```

Delapan puluh menit, n yang sama, satu-satunya yang berubah adalah **deret harga yang dipakai
mendefinisikan populasinya**. Angka +2,0 jadi −9,8; p=0,763 jadi p=0,995.

**Kesimpulan yang kucabut dan yang tetap berdiri.**

- **Dicabut sebagai besaran:** dua tabel E27 di §8 tidak lagi boleh dikutip sebagai "efek di venue
  hidup = +2,0 bps". Yang bertahan adalah kalimat kualitatifnya: efek pada horison menit di venue
  pembanding berada dalam **orde ±10 bps** - di bawah 59 bps ongkos round-trip kami - dan tidak
  pernah bergerak searah dengan yang dibutuhkan klaim "bump-nya ada, venue kami yang beku". Kalau
  seseorang butuh angka tunggal untuk kutipan, angka yang jujur adalah **rentang**, bukan titik.
- **Kebobolan alat yang kunyatakan terang-terangan:** `gate_bump.py` (dan `perp_bump.py`) mendefinisikan
  populasinya sebagai "simbol yang kelasnya HIDUP **saat ini dijalankan**". Kelas itu dihitung dari
  jendela 24 jam yang bergulir, jadi **satu percobaan yang sama bisa menguji dua kumpulan kejadian yang
  berbeda**. Itulah sebabnya E27 bergerak 12 bps dalam 80 menit tanpa ada yang mengubah kodenya.
  Perbaikan masuk **P67**: kunci daftar simbol di waktu-kunci (ditulis ke artefak kunci), bukan
  diturunkan dari kelas saat runtime.
- **Yang tetap tidak berubah dari halaman ini:** §3 (buku beku di venue kami), §7 (venue pembanding
  lebih hidup pada kontrak yang sama), §9 (kedalaman nol dalam ±10 bps pada 5 dari 26 simbol), dan
  tabel tiga dugaan di §8 - kelimanya sudah diukur dengan alat yang salah satu di antaranya baru saja
  ketahuan tidak stabil, jadi angka titik mana pun dari halaman ini wajib disebut bersama jam
  pembuatannya.

Lihat juga: `00-Overview/03 - Decisions.md` F-D68 · [[08-Backlog/01 - Backlog]] P67 ·
halaman 22 §6 (non-overlap E25 adalah reaksi terhadap penyakit yang sama: jendela yang bergeser).

## 6. Yang berubah karena ini

- Keputusan: **F-D56** (E20), **F-D57** (parser & dua angka reachable), **F-D61** (yang mati bukan kutipan, tapi buku dalam 10 bps), **F-D59** (venue pembanding lebih hidup - dugaan 'nasib long-tail' dibantah), **F-D60** (bump tetap mati di venue hidup - dugaan 'venue terlalu beku' dibantah), **F-D58** (E26, bump tidak
  pindah ke perp).
- Koreksi terlihat di: halaman 19 §3 (tembok venue), `TradingKnowledge/Fakta Terukur.md`,
  `10-Submissions/01 - Claims Cheat Sheet.md` (baris "edge dua menit" + frasa yang dilarang),
  `07-Testing/01 - Test Commands.md` baris 48 (ukuran F-D43 yang lama), registry baris 64-65.
- Backlog: **P41** dijawab (E26) dengan batasnya; **P59 terpasang 14:12Z** (cache 1 m → 3 hari,
  dan `perp_liveness.suhu()` dipatok ke jendela 24 jam supaya cache yang memanjang tidak
  mengubah kelasnya - F-D54), **P60** (baca kedalaman ⑨ untuk 5 simbol HIDUP sebelum bicara ukuran posisi), **P61**
  (venue pembanding: ukur hal yang sama di venue lain, jangan berharap).
- Epik: pertanyaan "alasan masuk" sekarang punya batas atas yang terukur, dan itu yang menentukan
  urutan kerja berikutnya.

- Alat baru: `tools/gate_liveness.py` (P61) dan `tools/gate_bump.py` (E27) - keduanya **mengimpor** penggaris E20/E26, tidak menyalin rumus, karena dua salinan rumus berarti dua angka yang tidak sebanding.

Lihat juga: [[06-Results/26 - Masuk Segar, Terukur Benar]] · [[06-Results/27 - Masuk Terpilih vs Masuk Acak]] · [[03-Data/D2 - Wallet Flow]] · [[07-Peta-Fabius/GAP4 - Yang Tidak Bisa Diuji Karena Data]].
