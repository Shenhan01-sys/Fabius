---
tags: [hasil, "retraction", "jalur-cepat", "F-D54"]
---

# 26 - Masuk Segar, Terukur Benar - dan ternyata kalah

**Bagian dari:** [[06-Results/00 - Hub Results]] · [[06-Results/19 - Umur Posisi]] ·
[[08-Backlog/02 - Epik Alasan Masuk]]
**Alat:** `tools/fast_lane.py --report` · `tools/feed_latency.py --kedatangan` ·
`tools/horizon_decay.py` · **Jam:** 29 Sep 2026 ±12:55Z (semua angka di bawah dicetak hari ini)

## 1. Yang kukira tembok ketiga, ternyata tembokku sendiri

Halaman 19 §2b dan cheat sheet menulis: umur kabar **saat kami memutuskan = median 808 d (13,5
menit)**, sementara bump E11 hidup ±2 menit. Simpulan yang kutarik: sinyalnya mati sebelum kami
selesai membacanya.

Itu **salah alamat**. Perbaikan urutan kandidat di `beli_baru()` (commit `b990ab5`, 11:22:56Z -
sebelumnya alat mengambil "12 teratas dari urutan berkas", dan satu muatan GMGN membentang puluhan
menit, jadi yang terpilih sistematis yang paling TUA) mengukur dirinya sendiri:

```text
umur kabar saat memutuskan [terbaru-dulu]: median 61 d | p90 89 | max 842 | n=182 | <180 d 97%
umur kabar saat memutuskan [urutan-berkas]: median 812 d | p90 869 | max 899 | n=252 | <180 d 0%
PERBAIKAN TERUKUR: 812 d -> 61 d (92% lebih muda) pada alat yang sama, hanya karena urutan
pilihannya dibetulkan - BUKAN karena sumbernya berubah
```

Umur kabar **sebelum kami menyentuhnya** (cap `arr` di tiap baris ⑦, 1.736 baris): median **120 d**,
p90 206 d. Pada baris yang benar-benar kami putuskan setelah 11:30Z: median **24 d** saat tiba.
Jadi kabar ⑦ memang muda - yang tua adalah caraku mengambilnya. **F-D50 tetap berdiri** (ia
membetulkan "0,2 menit" menjadi "808 d"), tapi 808 d sekarang berstatus **deskripsi rejim lama**,
bukan keadaan alat.

## 2. Retraction: 58 dari 58 lengan 5 m rejim lama mengukur MASA LALU

Jendela arm 5 m adalah `kejadian + 5 m ± 3 m` - mulai di **kejadian + 120 d** - sedangkan harga masuk
kami adalah harga **pada saat keputusan**. Kalau keputusan tiba 812 d sesudah kejadian, jendela itu
sudah lewat sebelum kami masuk. Yang selama ini kutampilkan sebagai "hasil masuk di menit ke-5"
adalah **selisih antara masa lalu dan harga kami**, bukan hasil keputusan.

Alatnya sekarang menyaring itu dan mencetak jumlah yang tertolak, bukan diam-diam:

```text
arm  5m: 86 tercatat -> terbaru-dulu: 25 sah, 3 mengukur MASA LALU | urutan-berkas: 0 sah, 58 mengukur MASA LALU
arm 30m: 3 tercatat -> urutan-berkas: 3 sah, 0 mengukur MASA LALU
pairing: 3 slot DIBUANG karena salah satu armnya menilai SEBELUM kami memutuskan (F-D54); 0 tersisa
```

**Dicabut:** seluruh blok PAIRING jalur cepat (`5m −59,0` / `30m +139,3` / `delta −17,5`, n=3) dan
baris `PROSPEKTIF ... 5m mean winso −112,1 (n=86)` - yang terakhir itu gabungan dua rejim; yang sah
25. Status baru **`DI LUAR JENDEL`** sekarang mencatat keputusan telat sebagai penolakan, bukan nol.

## 3. Angka pertama yang boleh dipakai

```text
5m HANYA yang sah (memutuskan <= 120 d): mean winso -519,4 | median -76,4 | n=25 dari 86
mean mentah -1.016,6 | positif 5 dari 25 (20%) | <=-1.000 bps: 9 | >=+500 bps: 3
umur keputusan: min 42 d | median 58 d | maks 96 d          (24 token berbeda, tak ada yang mendominasi)
umur baris harga masuk: median 38 d
```

Ini jawaban langsung atas pertanyaan builder ("Fabius sudah lihai open posisi belum?") dengan alat
yang benar: kami masuk rata-rata **58 detik** sesudah transaksi whale - bukan 13 menit lagi - pada
24 token berbeda, dan 5 menit kemudian rata-ratanya **−519 bps** (winsor ±2.000 seperti E11),
mediannya **−76 bps**, dengan **9 dari 25** jatuh lebih dari 1.000 bps.

## 4. Kenapa ini bukan sekadar "E11 diulang dan gagal"

E11 (`tools/horizon_decay.py`) men-scan penundaan masuk pada kejadian **yang dibatasi jangkar kabar**:
`delay 0` → **+202,6** mean@5m, `delay 2 m` → **+47,3**, `delay 5 m` → **−166,4**. Pada umur keputusan
58 d kami, kurva itu menjanjikan **positif**. Yang hidup memberi **−519,4**. Dua sebab, dan keduanya
terukur:

- **Populasinya beda.** E11 = kejadian ber-jangkar kabar (n=393); jalur cepat = SETIAP baris beli ⑦
  yang lolos rem (n=25 sah). "Setelah kabar" bukan "setelah whale beli".
- **Titik masuknya beda.** E11 mengukur dari harga **saat kejadian**; kami membayar harga **saat kami
  bisa membeli**: `entry_px − tx_p` median **+25,7 bps**, p90 **+1.199,6**, dan pada **16 dari 25**
  posisi harga kami sudah DI ATAS harga transaksi whale. Ini kasus khusus dari kontrol yang sudah
  ditulis E11 sendiri (`bump MENYUSUT −23,9..−41,1 bps begitu harga masuk diganti sumber`).

Jadi yang patah bukan "kabar punya bump" - itu tetap hasil E11 yang lolos placebo. Yang patah adalah
**penerjemahan bump itu jadi posisi kami**, dan sekarang ada angkanya, bukan ada dugaannya.

## 5. Batas halaman ini (baca sebelum mengutip)

n=25, **satu lengan**, tanpa kontrol acak sejawat (F-D8), dan angkanya **retrospektif terhadap
perbaikan alatnya sendiri** - jadi tidak bisa dijual sebagai vonis, hanya sebagai pengukuran pertama
yang sah. Yang TIDAK diuji di sini: memegang lebih lama pada rejim segar (0 pasangan sah), isi
order-book saat masuk (⑨ belum cukup umur per simbol), dan apakah 9 bencana itu berasal dari satu
jenis token. Lihat [[06-Results/19 - Umur Posisi]] §3 untuk dua tembok lain yang tidak berubah
(venue **3,1 %**, `i` **+245 bps**).

## 6. Yang berubah karena ini

- `tools/fast_lane.py`: `nilai_arm()` mengembalikan `sah` + `umur_keputusan_d`; laporan memisah dua
  rejim dan memberi angka HANYA-yang-sah; median gabungan diberi label **TIDAK BOLEH DIKUTIP**;
  self-test mengunci semuanya (5 assert baru).
- Keputusan: **F-D54** (`00-Overview/03 - Decisions.md`) + koreksi baris 808 d di halaman 19 §2b,
  README, `07-Testing/01 - Test Commands.md` baris 46/58, `TradingKnowledge/Fakta Terukur.md`,
  `10-Submissions/01 - Claims Cheat Sheet.md`.
- Backlog: **P55** (uji prospektif "masuk ≤2 m vs ≤15 m pada kejadian yang sama + kontrol acak
  sejawat"), **P56** (sumber harga masuk: `entry_px` vs `tx_p` vs microprice ⑨ - karena §4 menunjuk
  titik masuk sebagai penyebab, dan itu belum pernah diisolasi), **P57** (laporkan `DI LUAR JENDEL`
  ke `winlog` supaya kehilangan ini terlihat di buku paper juga).

