---
tags: [tk, tk-sinyal, "I1"]
---

# I1 - Moving Average

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** keputusan ([[PL4 - Memutuskan]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"metode trading itu ada apa aja sih?" (SMA/EMA/WMA +
Golden/Death Cross) dan §"paling OP untuk berbagai situasi" ("sederhana tapi sangat efektif untuk
tentukan tren") — klaim komunitas. **Dan ini satu-satunya keluarga sinyal yang sudah kami uji
sendiri**: aturan arah `tools/direction.py`, hasilnya di [[Fakta Terukur]] §F

**Ringkas:** Rata-rata bergerak tidak memprediksi apa pun: ia menunda. Itu bukan kekurangan, itu
definisinya — kamu membayar `~(n−1)/2` bar keterlambatan untuk membeli pengurangan noise. Karena
keterlambatan itulah kami punya satu angka langka di subtree ini: aturan arah Fabius adalah aturan
SMA, dan ia **sudah diuji dan rugi**. Catatan ini menuliskan hasilnya seukuran yang benar-benar diukur.

## Definisi yang bisa dihitung

```
SMA(n,t) : (1/n) * sum(c[t-n+1 .. t])
EMA(n,t) : a*c[t] + (1-a)*EMA(n,t-1),  a = 2/(n+1)          # tak berujung, tergantung seed awal
WMA(n,t) : sum(i * c[t-n+i]) / sum(i)                        # bobot linier
gap(n,t) : (c[t] - SMA(n,t)) / SMA(n,t)                      # yang dipakai Fabius, n = 24
crossover: SMA(f,t-1) <= SMA(s,t-1) DAN SMA(f,t) > SMA(s,t)   # f = cepat, s = lambat
lag      : respons terhadap langkah harga ~ (n-1)/2 bar untuk SMA; EMA lebih kecil tapi tidak nol
```

`n` adalah satu-satunya parameter, dan ia memilih siapa yang terlambat: `n` kecil banyak sinyal dan
banyak ongkos, `n` besar sedikit sinyal dan datang saat pergerakannya sudah selesai.

## Cara pakai yang diklaim

Golden cross (50 di atas 200) sebagai "tren naik", death cross sebaliknya; entry pada pullback ke
EMA 21; trailing stop di bawah EMA 50; kombinasi beberapa `n` sebagai "ribbon". Klaim di `Plan.txt`
("sangat efektif untuk tentukan tren") adalah klaim peran **deskriptif** yang dibacakan sebagai peran
**prediktif** — dan di situlah seluruh kegagalan keluarga ini bermula.

### Yang terukur di Fabius — dan apa yang benar-benar dikatakannya

Aturan live kami: `gap(24) > +1 %` dan `ret24 > 0` → long; `gap(24) < −1 %` dan `ret24 < 0` → short;
selain itu flat (`tools/direction.py`, bentuk yang sama dijalankan `tools/backtest.py`). Hasil
([[Fakta Terukur]] §F dan [[06-Results/04 - Negative Results]]): **net rugi di 12/12 simbol** saat
gerbang |acf| dicabut (rentang −27,9 … −0,8 bps per trade), gross hanya **+1,5 … +4,0 bps** lawan
ongkos 20 bps yang diimpor, **dibalik pun tetap kalah** (−39,2 … −12,1), dan **0/12 lolos** di
horizon 24 j. Ambangnya diimpor dari kode live, tidak di-fit di atas hasil.

Yang boleh disimpulkan: pasangan aturan `gap SMA24 ±1 % + ret24` tidak mengandung informasi arah pada
aset ber-perp yang bisa kami hargai sendiri, di horizon 4 j dan 24 j, setelah ongkos. Yang **tidak**
boleh disimpulkan: bahwa semua aturan SMA kalah di semua pasar — `n` lain, aset lain (C2/D yang tidak
bisa kami hargai sendiri), dan peran lain (filter rezim, trailing stop) **tidak diuji**. Ongkos uji
itu 20 bps warisan sementara yang terukur **59 bps** (§D, P10 ditutup 28 Sep), jadi net sebenarnya lebih
dalam; dengan gross +1,5 … +4,0 bps, selisihnya aritmetika biasa.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| penutupan 1 jam | `ADA` | `tools/bars.py` → cache per (simbol, interval); kedalaman 9.599 bar (§A) |
| `n` panjang (200 bar) untuk "golden cross" | `ADA-TAPI` | cukup di aset terdalam; mustahil di kandidat dengan `MIN_BARS_TINY=720` tersisa untuk dua MA (§A/§E) |
| aturan SMA arah | `ADA` | `tools/direction.py` (live) dan `tools/backtest.py` (uji) — sudah diuji, **negatif** |
| SMA/EMA/WMA sebagai fitur untuk metode lain | `TIDAK-ADA` | tidak ada jalur fitur; hanya satu `gap(24)` yang dipakai |

## Uji di Fabius

Sudah dijalankan, dan perintahnya ada di clone:

```
# tiga baris pertama = yang memproduksi angka §F (ongkos 20 bps warisan):
python -X utf8 tools/backtest.py --mom-only                 # aturan arah, gerbang |acf| dicabut
python -X utf8 tools/backtest.py --mom-only --flip          # sisi sebaliknya (mean reversion)
python -X utf8 tools/backtest.py --mom-only --horizon 24    # horizon 24 bar
python -X utf8 tools/backtest.py --mom-only --cost 59       # ongkos TERUKUR - belum dijalankan
```

Yang belum dan seharusnya: menguji MA dalam **peran yang tidak menuntut arah** — sebagai filter rezim
di atas hasil ⑦, atau sebagai jarak invalidasi bersama [[I6 - ATR dan Jarak Ternormalisasi]]. Syarat
naik tingkat bukti tidak berubah: `n >= 20` non-overlap, gross di atas **59 bps**, bertahan setelah
fold terbaik dibuang, lolos BH α 0,10 (§D/§E, F-D16).

## Batas dan mode gagal

- **Whipsaw di rezim menyamping** adalah mode gagal utamanya, dan ia sistematis: persilangan membeli
  setelah naik dan menjual setelah turun, jadi di rentang datar ia menjual titik terbaik berulang
  kali. Setiap putaran membayar 59 bps (§D).
- **Lag tidak bisa dibeli kembali.** Sinyal yang datang `~(n−1)/2` bar terlambat hanya berguna kalau
  pergerakan sisanya lebih besar dari keterlambatan itu; pada deret yang mendekati jalan acak
  (|acf| < 0,05, gerbang `tools/direction.py`) syaratnya tidak pernah terpenuhi.
- **Semua turunan dari deret yang sama.** `gap(24)`, `ret24`, MACD, dan "struktur" membacanya dari
  `(o,h,l,c)` yang sama: menggabungkannya bukan konfluensi, tapi satu bukti dihitung berkali
  ([[I3 - MACD]], [[S3 - Market Structure BOS dan ChoCH]], [[FD11 - Aturan Mengalahkan Intuisi]]).
- **Aset yang diuji ≠ aset yang dijual.** Yang kalah ini adalah aset ber-perp; klaim keluarga MA di
  `Plan.txt` umumnya dijual untuk memecoin yang tidak bisa kami hargai sendiri.

## Tingkat bukti

`T3 NEGATIF` untuk aturan arah `gap SMA24 ±1 % + ret24` — sudah kami uji di data sendiri dan hasilnya
melawan klaimnya ([[Fakta Terukur]] §F) · `T2` untuk MA sebagai peringkas tren dan filter rezim - disurvei di literatur (Park & Irwin 2007, DOI `10.1111/j.1467-6419.2007.00519.x`, [[Sumber dan Jangkauan]] #4) dan tidak kami reproduksi dalam peran itu · `T0` untuk "golden cross membeli masa depan".

## Boleh dibaca, dilarang dibaca

- **Boleh:** "satu-satunya keluarga sinyal yang kami uji adalah SMA, dan kami rugi di 12/12; itu
  bukti bahwa pipeline kami menutup klaim, bukan melindungi klaim."
- **Dilarang:** "Fabius memakai moving average untuk mencari arah" seolah itu terbukti · "MA tidak
  bekerja" (yang kami tunjukkan: aturan kami tidak bekerja, di data kami, pada dua horizon).

**Terkait:** [[I3 - MACD]] · [[I2 - RSI dan Divergence]] · [[I4 - Bollinger Bands]] ·
[[S3 - Market Structure BOS dan ChoCH]] · [[FD8 - Volatilitas]] · [[Fakta Terukur]]
