---
tags: [tk, tk-setup, "ST5"]
---

# ST5 - Trend Rider

**Keluarga:** [[00 - Hub Setup]]
**Anggota:** [[FD9 - Horizon Waktu dan Multi-Timeframe]] · [[I1 - Moving Average]] · [[S4 - Order Block dan Breaker]] ·
[[S7 - Fibonacci Retracement dan Extension]] · [[V1 - Konfirmasi Volum dan Money Flow]] · [[FD7 - Invalidation Stop dan Time-Stop]] · [[FD8 - Volatilitas]]
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"Trend Rider" + klaim transkrip "Salah satu expectancy tertinggi
dalam jangka panjang" *(klaim model, tanpa sumber, tanpa angka — jangan dipindah ke halaman ini karena halamannya rapi)*

**Ringkas:** searah tren besar, masuk saat tarik-napas (retrace ke MA / OB / Fib), tambah posisi kalau volum
mengkonfirmasi, biarkan berjalan dengan trailing stop. Ini **satu-satunya keluarga setup di folder ini yang
arahnya sudah kami uji dan hasilnya rugi**: aturan momentum pada deret harga kami net-nya negatif di 12 dari
12 aset setelah ongkos ([[Fakta Terukur]] §F). Yang belum terbukti bukan resepnya — **bahannya**.

## Resep

| tahap | aturan | catatan |
|---|---|---|
| bias | tren HTF: harga di atas MA panjang dan MA menanjak | [[I1 - Moving Average]] · [[FD9 - Horizon Waktu dan Multi-Timeframe]] |
| zona | retrace ke MA / OB / cluster Fib di sisi tren | [[S4 - Order Block dan Breaker]] · [[S7 - Fibonacci Retracement dan Extension]] |
| pemicu | pemulihan arah + volum ikut | [[V1 - Konfirmasi Volum dan Money Flow]] |
| invalidation | struktur pembalik di bawah ayunan terakhir | [[FD7 - Invalidation Stop dan Time-Stop]] |
| target | tidak ada target tetap — inilah "runner"-nya | ekstensi atau trailing; dua-duanya harus terhitung sebelum masuk |
| trailing | stop naik mengikuti ekstrema yang sudah terjadi | path-dependency: lihat ## Batas |
| ukuran | plafon kontrak; menambah posisi = menambah eksposur ke plafon yang sama | [[FD6 - Ukuran Posisi]] · [[FD8 - Volatilitas]] |
| keluar waktu | tren hilang dalam horizon = keluar | [[FD7 - Invalidation Stop dan Time-Stop]] |

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| OHLC 1 jam ≥ 2.400 bar | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari, hanya aset ber-kontrak perp ([[Fakta Terukur]] §A); C2/D ≤ 1.000 bar ≈ 41,6 hari |
| aturan arah yang sudah terimplementasi | `ADA` | `tools/direction.py` (`sma_gap_pct` + `ret24` + gerbang `\|acf\|`) — hasilnya terdokumentasi di §F |
| volum per bar sebagai penyaring entry | `ADA-TAPI` | ikut `klines`; belum pernah dipakai sebagai filter di satu jalur keputusan pun |
| definisi "retrace selesai" | `TIDAK-ADA` | tidak ada di kode; tanpa itu pemicunya subjektif |
| jalur fill intra-bar untuk trailing stop | `TIDAK-ADA` | kami punya `high`/`low` per jam, bukan urutan di dalamnya (§C tanpa tick) — trailing di backtest terlihat lebih baik daripada aslinya ([[EV2 - Jebakan Backtest]]) |
| deret tren pada aset yang diklaim | `ADA-TAPI` | 608 kontrak perp; memecoin spot-only tidak punya masa lalu yang cukup |

## Uji di Fabius

Sudah diuji, sebagian — dan itu keuntungannya: **ini bukan resep tak dikenal, ini resep yang satu anggotanya
sudah kami cetak hasilnya.** Rinciannya di [[06-Results/04 - Negative Results]]; angka yang boleh dikutip ada
di [[Fakta Terukur]] §F:

- aturan arah apa adanya, ambang diimpor (tidak di-fit), 400 hari × 12 aset: **net rugi di 12/12** (−27,9 …
  −0,8 bps/trade) saat gerbang `|acf|` dicabut; gross-nya cuma **+1,5 … +4,0 bps** vs 20 bps model warisan.
- **Dibalik pun tetap kalah** (−39,2 … −12,1 bps) — ini bukan "salah tanda"; horizon 24 jam: **0/12** lolos syarat §E.

Uji yang belum ada dan harus ditulis untuk resep ini apa adanya:

1. Rebus resep jadi aturan yang dijalankan mesin: tren = `sma_gap_pct` bertanda; retrace = jarak dari MA
   dalam ATR; pemicu = close memulihkan arah; trailing = stop mengikuti `high`/`low`. Semua konstanta
   dikunci sebelum hasil ([[EV6 - Kalibrasi Ambang Terhadap Hasil]]).
2. Bandingkan dengan **baseline yang sudah kalah** di atas. Pertanyaannya bukan "bagus tidak?", tapi **dari mana
   gross tambahan sebesar itu datang**: jarak antara gross yang kami ukur (+1,5 … +4,0 bps) dan ongkos terukur
   (**59 bps**, §D) harus diproduksi tiga aturan yang belum diuji — trailing hanya memindahkan ekor.
3. Ambang naik kelas: `n >= 20` non-overlap, BH α 0,10, positif setelah fold terbaik dibuang, dihitung di
   luar sampel (§E, F-D16). Hasil uji resep penuh: *(belum diukur)*.

## Konfluensi atau gaung

Keluarga tren paling rentan gaung **waktu**, bukan gaung variabel:

| anggota | input sebenarnya |
|---|---|
| tren HTF (MA) | `close`, window panjang |
| "harga di atas MA" + "MA menanjak" | dua kalimat atas satu deret; slope = selisih window |
| retrace ke MA/OB/Fib | deviasi dari MA yang sama, window pendek |
| konfirmasi volum | kolom `volume` pada bar yang sama (bukan sumber baru) |
| trailing stop | fungsi dari `high`/`low` yang sudah terjadi — **tidak pernah** berisi informasi baru, hanya aturan keluar |

Kelima anggota bergerak **berurutan** pada satu vektor: tren, lalu deviasi, lalu pemulihan — terasa seperti tiga
konfirmasi karena datang di tiga waktu berbeda, padahal tidak ada sumber independen kedua di dalamnya. Yang bisa
jadi sumber baru hanya volum, dan itu butuh pembeda dari harga (delta/tick) yang `TIDAK-ADA` di repo ini (§C).

## Batas dan mode gagal

- **Rezim pembaliknya nyata.** Pada deret yang sama, aturan yang dibalik rugi **lebih dalam** (§F):
  bukan berarti "maka tren-lah jawabannya" — kedua arah sudah dicoba pada bahan ini.
- **Trailing pada bar 1 jam = fill yang dibayar di belakang.** Stop yang bergeser tidak bisa
  direproduksi tanpa urutan di dalam bar; hasil backtest-nya cenderung ramah, bukan jujur.
- **Scaling in memperbesar ongkos, bukan edge.** Setiap tambahan posisi membayar putaran: 59 bps per
  putaran di venue demo kami (§D), dan jalur eksekusi nyata mencetak **−59,0 bps** rata-rata pada 3
  putaran (§F) — itu ongkos, bukan sinyal.
- **Tren paling "bersih" ada di aset yang tidak bisa kami jual.** Kursi butuh gerbang ⑥ kapasitas keluar
  (`MIN_LIQ_USD` 50.000 USD, §E); aset yang bergerak paling keras justru sering gagal syarat ini tepat
  ketika kita ingin keluar ([[FD3 - Likuiditas dan Dampak Harga]]).
- **Beberapa peristiwa besar menyamar sebagai aturan.** Penyakit yang sudah kami tangkap sekali: satu fold
  baik menghasilkan angka yang kelihatan hidup (§F, [[QT4 - Overfitting dan Validasi]]).

## Tingkat bukti

`T0` untuk resep kombinasi ini (belum pernah dijalankan sebagai kesatuan) · `NEGATIF` untuk satu-satunya
anggota yang sudah kami uji pada data sendiri: aturan arah (`tools/direction.py`, hasil di §F).
Gabungannya: bahan teruji kalah, tambalannya belum teruji.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami sudah menguji aturan arah pada deret harga kami sendiri dan rugi di 12/12 setelah
  ongkos; Trend Rider menambahkan tiga aturan yang belum diuji di atas fondasi yang sudah kalah."
- **Dilarang:** "trend following punya expectancy tertinggi" (kalimat transkrip, tanpa sumber) ·
  "trailing stop memperbaiki hasil" (belum diukur) · "Fabius mengikuti tren" · membaca win-rate di
  [[06-Results/04 - Negative Results]] sebagai "hampir untung", padahal §F mencatat net negatif di 12/12.

**Terkait:** [[ST7 - Checklist Keputusan]] · [[ST3 - Clean Price Action]] · [[FD5 - Expectancy Bukan Win Rate]] ·
[[06-Results/04 - Negative Results]] · [[QT2 - Backtesting yang Jujur]]
