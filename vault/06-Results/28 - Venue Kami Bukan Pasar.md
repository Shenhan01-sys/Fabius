---
tags: [hasil, "venue", "E20", "E26", "likuiditas", "retraction"]
---

# 28 - Venue Kami Bukan Pasar (E20 + E26)

**Bagian dari:** [[06-Results/00 - Hub Results]] · [[06-Results/19 - Umur Posisi]] §3 ·
[[08-Backlog/02 - Epik Alasan Masuk]] §3g
**Alat:** `tools/perp_liveness.py` · `tools/perp_bump.py` · pembanding: `tools/venue_bridge.py`,
`tools/horizon_decay.py` · **Jam:** 29 Sep 2026 ±13:55Z (semua angka dicetak hari ini)

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

32 kejadian (dedupe 30 m/simbol), 15 yang jendelanya lengkap; masuk diukur **dari harga kejadian** dan
**dari harga satu menit kemudian** (karena umur keputusan nyata kami 58-61 d, F-D54):

```text
@2  m | n=15 | dari harga kejadian: mean    +2,0 median    +5,0 | masuk +1 m: mean   -3,8 | placebo   +0,7
@5  m | n=15 | dari harga kejadian: mean    -7,3 median    +4,7 | masuk +1 m: mean   -9,3 | placebo   +6,9
@30 m | n=15 | dari harga kejadian: mean  -34,4 median    +6,9 | masuk +1 m: mean  -33,4 | placebo   -9,6
berpasangan 5 m vs 30 m pada posisi yang sama: median delta -0,5 bps | menang 7 kalah 8 | p=0,69638
```

Placebo (@2 m +0,7 vs asli +2,0; @5 m +6,9 vs asli −7,3) dan tanda-uji p=0,70 menjawab dengan satu
kata: **tidak ada**. Bump E11 (+192,7 → +202,6 bps, placebo datar −180) hidup di **deret harga spot
BSC**, dan ia **tidak pindah** ke harga perp dari aset yang sama - bahkan ketika masuk di harga
kejadian, yang paling murah yang bisa dibayangkan.

Sensitivitasnya justru yang membuka mata: pada 39 kejadian di kelas TIPIS, **median return = 0,0 bps
di SEMUA horison** (@2/@5/@30), karena deretnya beku. Itu bukan "hasil nol", itu **tidak ada
pengukuran** yang menyamar sebagai hasil - bentuk paling bersih dari aturan "unmeasured is not clean".

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
kehilangan, dan itu yang P59 perbaiki sebelum angka ini dipakai di depan juri.

## 6. Yang berubah karena ini

- Keputusan: **F-D56** (E20), **F-D57** (parser & dua angka reachable), **F-D58** (E26, bump tidak
  pindah ke perp).
- Koreksi terlihat di: halaman 19 §3 (tembok venue), `TradingKnowledge/Fakta Terukur.md`,
  `10-Submissions/01 - Claims Cheat Sheet.md` (baris "edge dua menit" + frasa yang dilarang),
  `07-Testing/01 - Test Commands.md` baris 48 (ukuran F-D43 yang lama), registry baris 64-65.
- Backlog: **P41** dijawab (E26) dengan batasnya, **P59** (cache 1 m ≥ 3 hari supaya jendela tidak
  bolong), **P60** (baca kedalaman ⑨ untuk 5 simbol HIDUP sebelum bicara ukuran posisi), **P61**
  (venue pembanding: ukur hal yang sama di venue lain, jangan berharap).
- Epik: pertanyaan "alasan masuk" sekarang punya batas atas yang terukur, dan itu yang menentukan
  urutan kerja berikutnya.

Lihat juga: [[06-Results/26 - Masuk Segar, Terukur Benar]] · [[06-Results/27 - Masuk Terpilih vs Masuk Acak]] · [[03-Data/D2 - Wallet Flow]] · [[07-Peta-Fabius/GAP4 - Yang Tidak Bisa Diuji Karena Data]].
