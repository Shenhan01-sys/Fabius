---
tags: [tk, tk-sinyal, "S9"]
---

# S9 - Elliott Wave dan Harmonic

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"metode trading itu ada apa aja sih?" (keduanya muncul
di daftar "Pendekatan Lain") — klaim komunitas tanpa pemilik hasil ukur

**Ringkas:** Satu catatan untuk dua keluarga, karena alasan kami memperlakukannya sebagai `T0`
identik: keduanya punya **aturan pelabelan yang cukup longgar untuk mengakomodasi chart apa pun**.
Elliott membagi deret menjadi gelombang berderajat; harmonic menumpuk rasio Fibonacci pada empat
titik. Keduanya menghasilkan prediksi yang spesifik **kalau** labellingnya tetap — dan labellingnya
tidak pernah tetap: derajat boleh dinaikkan, koreksi boleh diganti jenisnya, dan count yang batal
dibaca ulang sebagai "bagian dari gelombang yang lebih besar". Yang tersisa bukan hipotesis, tapi
bahasa untuk menarasikan masa lalu.

## Definisi yang bisa dihitung

```
Elliott  : impuls 5 (1-2-3-4-5) + koreksi 3 (A-B-C); derajat bersarang; aturan:
           (i) 3 tidak pernah terpendek ; (ii) 2 dan 4 tidak tumpang-tindih dalam derajat sama ;
           (iii) alternation. Tiga aturan ini tidak memilih satu count pun pada deret nyata.
Harmonic : empat titik X-A-B-C dengan kendala rasio retracement/extension antar-segmen:
           Gartley  : B = 0,618·XA ; C = 0,382–0,886·AB ; D = 0,786·XA
           Bat      : B = 0,382–0,50·XA ; C = 0,382–0,886·AB ; D = 0,886·XA
           Butterfly: B = 0,786·XA ; D = 1,27–1,618·XA  # extension di luar A
           Crab     : B = 0,382–0,618·XA ; D = 1,618·XA
           semua dengan toleransi w; PRZ = pita tempat D dicari
swing(i,N) : sama dengan [[S3 - Market Structure BOS dan ChoCH]] -> X,A,B,C harus fractal yang SAH
```

Semua angka di atas adalah **kisi [[S7 - Fibonacci Retracement dan Extension]] pada ayunan yang
dipilih [[S3 - Market Structure BOS dan ChoCH]]**: tidak ada informasi baru di luar `(o,h,l,c)`, yang
bertambah hanyalah jumlah parameter — empat titik × enam rasio × toleransi.

## Cara pakai yang diklaim

Elliott: hitung derajat, jual di akhir wave 5, target wave 3 extension. Harmonic: tunggu harga masuk
PRZ, entry di 0,786/0,886, stop di luar X, target 0,382/0,618 dari CD. Pemilik klaim: komunitas pola
dan pembukunya; klaim "akurasi tinggi" yang beredar tidak disertai definisi count yang bisa
direproduksi — dan itu bukan kekurangan penulisan, itu intinya.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| OHLC 1 jam ≥ 2.400 bar | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari; hanya aset ber-perp ([[Fakta Terukur]] §A) |
| pelabel ayunan deterministik | `TIDAK-ADA` | tidak ada alat Fabius yang mendeteksi ayunan, apalagi count atau rasio |
| penentu count tanpa melihat masa depan | `TIDAK-ADA` | dan ini syarat mutlak, bukan kosmetik (lihat § Uji) |
| pencatatan prediksi sebelum hasil | `ADA-TAPI` | ada untuk keputusan arah (`tools/ledger.py`, `tools/anchor.py`) — **belum** ada untuk label grafik |

## Uji di Fabius

Supaya keluarga ini bisa dibuktikan salah, enam hal harus dibakukan lebih dulu. Tanpa keenamnya,
tidak ada uji yang mungkin:

1. **Pelabel deterministik**: `X,A,B,C` adalah fractal yang sah pada saat `t` (tanpa revisi mundur).
2. **Aturan pemilihan count** tanpa melihat hasil: mis. window ayunan tetap + tie-break indeks bar
   terkecil. "Ambil count yang paling masuk akal" = kebocoran masa depan.
3. **Target berbentuk angka**, bukan nama gelombang: tanda dan besar return pada horizon `H`
   (4 j / 24 j, seperti `tools/backtest.py --horizon`), bukan "selanjutnya wave 3".
4. **Null ganda**: (a) label diacak di antara pemicu dengan jumlah sama pada simbol & jam yang sama
   ([[Fakta Terukur]] §B); (b) pita Fibonacci vs pita acak (lihat [[S7 - Fibonacci Retracement dan Extension]]) — harmonic harus melewati keduanya.
5. **Pra-registrasi** parameter (N, toleransi, rasio yang dipakai) ditulis sebelum hasil dilihat
   ([[EV5 - Reproduksibilitas dan Pra-Registrasi]]).
6. **Anchor label sebelum jatuh tempo.** Yang paling murah dan paling menentukan: mesinnya sudah ada
   (`tools/anchor.py --verify`, [[Concepts/Anchored Before Outcome]]). Sebuah count yang di-anchor dan
   dibiarkan jatuh tempo adalah satu-satunya bentuk bukti keluarga ini yang kami terima; count yang
   ditulis setelah chart selesai bukan bukti, berapa pun meyakinkan tampilannya.

Setelah itu gerbangnya tidak berubah: `n >= 20` non-overlap, gross vs **59 bps** (§D), fold terbaik
dibuang, BH α 0,10 (§E). Tidak ada satu langkah pun di atas yang sudah dijalankan.

## Batas dan mode gagal

- **Derajat = jalan keluar tak terbatas.** Setiap count yang batal bisa dipindah ke derajat di
  atasnya: metode ini tidak bisa salah, dan yang tidak bisa salah tidak bisa diandalkan.
- **Aturan Elliott tidak menentukan satu pun count.** Tiga aturan itu menyaring sedikit kandidat dan
  meninggalkan banyak; pemilihan di antaranya dilakukan dengan estetika.
- **PRZ adalah kisi + toleransi = penambatan.** Empat titik dari ribuan ayunan, enam rasio, pita
  selebar `w·ATR` → probabilitas "harga masuk PRZ" mendekati satu; yang dijanjikan adalah di mana ia
  **berhenti**, dan itu tidak dijamin apa pun.
- **Semua keluarga ini bersaing di peristiwa yang sama** (satu ayunan, satu penembusan) dengan nama
  berbeda: sampelnya tidak bebas, konfluensinya bukan konfirmasi ([[EV3 - Signifikansi dan Multiple Testing]],
  [[FD11 - Aturan Mengalahkan Intuisi]]).
- **Kandidat kami tidak punya masa lalu yang cukup untuk punya "gelombang":** pada `MIN_BARS_TINY=720`
  dan pool berumur ±30 bar, lima gelombang berderajat tidak terwakili (§A).
- **Ongkos tidak peduli pada keindahan label.** Pola semahal apa pun tetap harus gross di atas 59
  bps (§D); seluruh keluarga S belum menunjukkan satu pun angka itu *(belum diukur)*.

## Tingkat bukti

`T0` untuk keduanya sebagai metode prediksi (aturan pelabelannya mengakomodasi semua hasil) · `T1`
untuk kegunaannya sebagai latihan mendeskripsikan deret — itu bahasa, bukan sinyal · untuk Fabius:
**belum diuji**, dan sebelum ada pelabel deterministik, **belum bisa diuji**.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "belum ada bentuk Elliott/harmonic yang bisa dibuktikan salah; syaratnya sudah kami
  tulis di atas dan belum terpenuhi."
- **Dilarang:** "kami sedang di wave 3" · "pola Bat punya win rate tinggi" · "Fabius mengenali
  struktur gelombang" · membaca catatan ini sebagai penolakan menguji: yang kami tolak adalah uji
  yang tidak menetapkan aturannya lebih dulu.

**Terkait:** [[S7 - Fibonacci Retracement dan Extension]] · [[S3 - Market Structure BOS dan ChoCH]] ·
[[S2 - Chart Patterns]] · [[S8 - Wyckoff]] · [[FD11 - Aturan Mengalahkan Intuisi]] ·
[[GAP4 - Yang Tidak Bisa Diuji Karena Data]] · [[Fakta Terukur]]
