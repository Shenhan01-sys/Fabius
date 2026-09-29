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

## 6. Yang berubah karena ini

- Keputusan: **F-D56** (E20), **F-D57** (parser & dua angka reachable), **F-D58** (E26, bump tidak
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

Lihat juga: [[06-Results/26 - Masuk Segar, Terukur Benar]] · [[06-Results/27 - Masuk Terpilih vs Masuk Acak]] · [[03-Data/D2 - Wallet Flow]] · [[07-Peta-Fabius/GAP4 - Yang Tidak Bisa Diuji Karena Data]].
