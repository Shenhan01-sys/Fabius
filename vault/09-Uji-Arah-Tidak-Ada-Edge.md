---
type: hasil-ukur
status: final-untuk-siklus-ini
diukur: 2026-09-24 (19:2x-19:5x UTC) / 25 Sep WIB
alat: Fabius/tools/backtest.py (ambang DIIMPOR dari direction.py, tidak di-fit di sini)
 artefak: decisions/backtest-20260924Z-h4.json, -h4-momonly.json, -h4-momonly-flip.json, -h24-momonly.json
---

# 09 — Uji arah: aturan kita TIDAK punya edge setelah ongkos, di horizon mana pun

Pertanyaan yang dijawab halaman ini adalah pertanyaan yang paling mungkin membuat kami terlihat
bohong: kalau agen sudah bisa bilang "short, masuk di sini, stop di sini, 24 jam" — apakah itu
lebih baik daripada lemparan koin? Jawabannya, seperti terukur di bawah: **tidak, belum.**

Angka di bawah bukan hiasan. Semuanya dari **deret harga yang benar-benar ada di repo**
(Aster 1h, 400 hari, non-overlap) dan aturan yang **sama** dengan yang dipakai live.

## 1. Aturan live apa adanya (gerbang |acf| >= 0,05 + momentum SMA24/ret24)

| simbol | bar | trade | keputusan |
|---|---|---|---|
| BNB ETH SOL DOGE WIF FLNC | 2.908–9.599 | **0** | momentum menyala 240–1.068 titik, **100 % dipadamkan gerbang `\|acf\|`** |
| XRP | 9.599 | 1 | di bawah MIN_TRADES |
| TAC | 3.701 | 8 | di bawah MIN_TRADES |
| HYPE | 8.814 | 30 | net **−16,0** bps · WR 46,7 % · drop-best-fold **−38,7** |
| CAKE | 9.599 | 42 | net **−18,5** · WR 42,9 % · drop-best **−45,7** |
| SUI | 9.599 | 105 | net **−29,2** · WR 41,9 % · drop-best **−35,9** |
| 1000PEPE | 9.599 | 111 | net **−16,4** · WR 44,1 % · drop-best **−19,8** |
| MARSCOIN | 1.225 | — | `bar < 2.400`, tidak dinilai |

**0 dari 4** simbol yang bisa dinilai lolos; keempat-empatnya rugi **setelah** ongkos walaupun
gross-nya masih positif kecil (+1,5 … +4,0 bps). Persis kegagalan yang ambang "gross > 40 bps"
(vault/08 §3) dirancang untuk tangkap — bedanya, kali ini ambangnya yang menangkap, bukan kami.

## 2. Gerbang dimatikan (`--mom-only`) — siapa yang memproduksi nol?

Semua 9.599-bar titik keputusan (240–1.216 trade per simbol) dijalankan tanpa gerbang |acf|:

| | rentang di 12 simbol |
|---|---|
| trade | 240 – 1.216 |
| win-rate | 19,2 % – 47,4 % (mayoritas 37–45 %) |
| gross bps/trade | **−7,9 … +19,2** |
| net bps/trade (sesudah 20 bps RT) | **−27,9 … −0,8** |
| t-stat | −4,84 … −0,02 (tidak satu pun positif) |
| drop-best-fold | **negatif di 12 dari 12** (−34,8 … −17,3) |
| net bps | **negatif di 12 dari 12**, tanpa pengecualian |

Jadi gerbang |acf| bukan penyebabnya: dia **menolak 100 % sinyal** pada aset yang paling dalam
history-nya (BNB/ETH/SOL/DOGE), dan ketika penolakan itu dicabut, hasilnya rugi di semua simbol
yang diukur. Yang salah adalah **isinya**, bukan pagar-pagarnya.

## 3. Kebalikannya juga kalah (`--mom-only --flip`)

Kalau momentum rugi, masuk akal mengira ini pasar yang sebenarnya mean-reverting. Diuji, bukan
dinarasikan: arah aturan yang sama dibalik.

| horizon 4 bar | momentum (bagian 2) | dibalik (bagian 3) |
|---|---|---|
| net bps/trade, rentang 12 simbol | −27,9 … −0,8 | **−39,2 … −12,1** |
| BNB | −13,3 | **−26,7** |
| 1000PEPE | −13,4 | **−26,6** |
| SUI | −18,4 | **−21,6** |

Membalikkan sinyal tidak menyelamatkan apa pun — malah lebih dalam minusnya. Artinya
pasang-aturan `gap SMA24 ± 1%` + `ret24` **tidak mengandung informasi arah** di horison ini;
ia hanya menghasilkan perputaran yang membayar 20 bps tiap round-trip.

## 4. Horizon 24 jam (`--mom-only --horizon 24`) — satu-satunya tempat gross positif muncul

| simbol | trade | gross | net | t | drop-best | folds |
|---|---|---|---|---|---|---|
| BNB | 143 | +34,9 | **+14,9** | 0,61 | **−8,7** | +110 −99 +24 +41 +0 |
| WIF | 47 | +46,9 | +26,9 | 0,34 | −20,9 | −62 +69 +223 −130 +40 |
| TAC | 82 | +111,3 | **+91,3** | 0,31 | +15,3 | +114 +298 −197 +381 −153 |
| sisanya (ETH SOL XRP DOGE HYPE CAKE SUI 1000PEPE FLNC) | 37–214 | −57 … +11 | **negatif semua** | < 0 | negatif | — |

**0 dari 12 lolos** (syaratnya: n≥20, net>0, drop-best-fold>0, p lolos BH α=0,10).

Yang harus dibaca dari tabel ini, karena ini bagian yang paling mudah dijual salah:
satu-satunya `net` positif yang bertahan setelah fold terbaik dibuang adalah **TAC**, dengan
`t = 0,31` dan lima fold `+114 +298 −197 +381 −153`. Itu **bukan** edge — itu distribusi yang
didorong beberapa peristiwa besar, dan statistik mana pun yang jujur akan bilang "belum tahu".
BNB +14,9 bps juga mati di drop-best-fold (−8,7): satu segmen waktu baik menyamar sebagai aturan
yang baik. Persis penyakit yang lab lama sudah namai (HYPE +92 % OOS yang ternyata 65 % dari satu
fold, `edge_lab.py` temuan #20).

## 4b. Hasil PERTAMA dari prediksi yang di-anchor — 26 Sep 08:23Z

Dua posisi MARSCOIN short yang kami anchor pada 24 Sep (blok 132955030 dan 132955788) sudah lewat
horizon 24 jam. `tools/ledger.py` membacanya dari **rekaman** (`entry_ref` ikut `decisionHash`),
bukan dari ingatan, lalu menutupnya dengan ongkos 20 bps RT:

| masuk dari bar | entry | jatuh tempo | keluar | gross | **NET** | hasil |
|---|---|---|---|---|---|---|
| 24 Sep 16:00Z | 0,11605 | 25 Sep 17:00Z | exit di horizon (time-stop) | **+21,5** | **+1,5 bps** | **MENANG** |
| 24 Sep 17:00Z | 0,11564 | 25 Sep 18:00Z | exit di horizon (time-stop) | −126,3 | **−146,3 bps** | **RUGI** |

`WR 50 % · net rata-rata −72,4 bps · total −144,8 bps · rugi bersih 1`
Artefak: `decisions/ledger-20260926Z.jsonl`.

Tiga hal yang harus dibaca beserta angkanya, karena godaan memolesnya besar:

1. **Dua menit berbeda, hasilnya berlawanan 148 bps.** Ini bukan "sekali benar, sekali salah";
   ini konfirmasi langsung dari bagian 1 halaman ini: sinyal yang kita pakai tidak membedakan dua
   jam berturut-turut pada aset yang sama. Membuang yang rugi dengan alasan "noise" adalah cara
   paling umum membuat laporan terlihat bagus.
2. **Yang menang pun tidak menutupi ongkosnya.** +1,5 bps net = arah kami benar dan pasar membayar
   biaya nyaris persis nol. Contoh terukur dari "gross kecil mati oleh 20 bps".
3. **n = 2.** Tidak ada uji statistik yang boleh dijalankan, tidak ada klaim win-rate, tidak ada
   `MIN_TRADES=20` yang terpenuhi. Yang boleh dikatakan hanyalah: **prediksi kami sudah jatuh
   tempo dan jejaknya masih ada untuk diperiksa.** Itu memang target sebenarnya dari anchor ini,
   bukan untung.

## 4c. ⑦ juga mati: menyalin smart money TIDAK lebih baik daripada menyalin kerumunan · 26 Sep 09:4xZ

Alat: `tools/smartmoney_score.py`. Entri dari **Dune** `dex.trades` (`blockchain='bnb'`, 10 hari,
`amount_usd > 500`, `ORDER BY block_time ASC`, 51.863 baris, halaman lengkap tanpa yang hilang);
harga forward dari **kline Aster yang kami tarik sendiri** (bukan dari Dune — barisnya punya
`_updated_at`, jadi boleh jadi statistik tapi tidak boleh jadi saksi waktu). 9 token uji = yang
punya alamat BSC di universe **dan** kontrak perp di Aster. 1 sampel per (wallet, token, jendela
4 jam), ongkos 20 bps RT.

Angka mentahnya, yang justru harus ditulis lebih dulu karena inilah yang bikin orang salah simpulkan:

| kelompok | n | wallet | WR | net rata-rata | median |
|---|---|---|---|---|---|
| panel (berlabel GMGN) | 53 | 21 | 69,8 % | **+680,7 bps** | +1.015,6 |
| kontrol (semua dompet lain) | 8.324 | 2.842 | 55,8 % | **+336,4 bps** | +122,2 |

Dibaca setengah hati, ini "bukti whale 2x lebih jago". Salah, dan salahnya sistematis: baseline
seorang pembeli bukan nol dan bukan rugi — baseline-nya **apa yang terjadi pada semua pembeli
token itu di jam itu**. +336 bps pada 8.324 transaksi kerumunan berarti **tokennya sedang naik**,
bukan rakyat jelata jago.

Jadi ujiannya dibuat **berpasangan per (token, jendela 4 jam)**; drift token terbuang oleh konstruksi:

```
jendela terpasang (panel DAN kontrol terisi): 34   dari 355 jendela total
selisih net panel - kontrol : -10,4 bps      median: 0,0 bps
p (sign-flip permutation, 20.000, seed 0)   : 0,568      -> TIDAK berbeda dari kerumunan
wallet dengan n>=20: 54 - LOLOS BH: 0       (panel: 0 wallet mencapai n>=20)
```

Ini jawaban **kedua dari arah yang berbeda** atas pertanyaan yang sama. Yang pertama aturan harga
(`vault/09` §1-4: rugi setelah ongkos di 12/12). Yang kedua: ikut-ikutan dompet yang dilabeli
pintar pun tidak menghasilkan apa-apa setelah biaya.

**Dan -10,4 ini adalah batas ATAS yang ramah ke panel**, bukan angka jujur mentah. Keanggotaan
panel kita datang dari label GMGN **hari ini**, sementara transaksinya diambil dari 10 hari ke
belakang: sebuah dompet boleh jadi dilabeli "smart" justru karena sejarah yang mau kita uji.
Itu lookahead label — persis penyakit yang bikin label sewaan terlihat hebat. Koreksi yang benar
butuh keanggotaan yang dicatat SEBELUM entri, dan itu baru mungkin sejak `wallet-flow.jsonl`
berdetak (26 Sep 08:15Z ke depan). Artinya: dengan bias yang membela panel sekalipun hasilnya nol,
jadi versi bersihnya kecil kemungkinan berbalik menjadi "edge".

## 5. Apa yang berubah di produk setelah halaman ini

1. **Registry tetap kosong, dan sekarang ada alasannya.** Bukan "belum sempat dites": aturan arah
   sudah dites di 400 hari × 12 aset × 3 varian, dan kalah ongkos di semuanya.
2. **`Enter` yang sudah di-anchor TETAP dibiarkan hidup** (MARSCOIN short, blok 132955030/132955788).
   Menariknya kembali anchor = menghancurkan nilai buktinya. Yang kita lakukan: prediksi itu
   dibiarkan jatuh tempo dan dinilai nanti oleh `ledger.py`, dengan halaman ini sebagai konteks
   bahwa kami **tahu** aturannya belum terbukti sebelum prediksi itu dibuat.
3. **Klaim yang boleh ditulis di README/submission**: "agen menyimpan keputusan yang bisa dibuktikan
   salah, dan menolak 100 % sinyal arah pada aset dalam karena derivatifnya mendekati jalan acak" —
   BUKAN "agen memperdagangkan meme dengan edge".
4. **Jangan panggil ini walk-forward fitted.** Tidak ada satu parameter pun yang dipilih dengan
   melihat hasil di atas; jadi yang dilakukan adalah tes bersegmen + sensitivitas. Menyebutnya
   walk-forward akan menjual sesuatu yang tidak kita beli.

## 6. Batas yang masih tersisa (jangan dibaca sebagai "sudah selesai")

- **Funding historis belum ikut** — aturan live punya gerbang funding ekstrem yang di sini absen.
  Arah kesalahannya tidak netral: aset yang kami tolak karena carry mungkin justru satu-satunya
  yang punya sesuatu untuk diukur. Perlu jalur data funding 4-jam yang bisa ditarik mundur.
- **Bidang ④ (honeypot / `can_not_sell`) tetap tidak diukur** di jalur arah — jadi semua angka di
  atas mengasumsikan kita bisa keluar, yang justru belum dibuktikan untuk memecoin.
- **Korelasi silang antar-simbol tidak dibetulkan.** BH diterapkan per token; 12 token ini bergerak
  dengan satu pasar yang sama, jadi "0 dari 12" tidak boleh dibaca sebagai 12 percobaan bebas.
- **Satu siklus live = satu titik waktu.** Hasil di atas adalah deret 400 hari, tapi keputusan
  yang benar-benar kami anchor lahir dari satu snapshot; kualitas snapshot (5 gap > 2 jam) ikut
  membatasi apa yang bisa disimpulkan dari 11 anchor itu.
