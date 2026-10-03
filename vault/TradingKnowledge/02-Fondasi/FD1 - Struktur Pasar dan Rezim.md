---
tags: [tk, tk-fondasi, "FD1"]
---

# FD1 - Struktur Pasar dan Rezim

> **BN-SKOP - 3 Okt 2026 (P76).** Vonis NEGATIF trend/momentum di halaman ini berlaku untuk SATU aturan yang diuji: SMA24 ± 1 % + ret24 pada bar
> 1 jam, horison 4/24 bar, ongkos 20/59 bps, 12 perp (`tools/direction.py`). Itu BUKAN vonis untuk keluarga trend. B1-TREND (momentum deret waktu
> HARIAN, N = 60, 16 perp, long/flat) adalah bot terpisah dengan spesifikasi terkunci yang sedang diuji maju ([[06-Results/30 - Spesifikasi Bot dan Kunci]]).

**Keluarga:** [[00 - Hub Fondasi]] · **Tahap:** analisis ([[PL3 - Menganalisis]]), mengikat keputusan ([[PL4 - Memutuskan]])
**Sumber:** [[Fakta Terukur]] §A (apa yang bisa kita hargai sendiri), §E (ambang yang masih perlu diuji), §F (hasil uji arah) · sisanya pengetahuan standar pasar — tidak ada rujukannya di repo ini

**Ringkas:** Rezim = keadaan pasar yang menentukan aturan mana yang berlaku. Indikator yang sama
membaca hal berbeda di rezim berbeda, jadi "sinyal" tanpa label rezim adalah kalimat tanpa subjek.
Proxy kami cuma satu (autokorelasi return) dan ia lebih sering berkata "tidak ada arah".

## Definisi yang bisa dihitung

Struktur naik/turun hanya berarti kalau "swing" dibakukan. Varian komunitas (swing beruntun ·
SMA di atas/bawah · ADX) tidak identik; memilih satu = menambah parameter.

```
pivot_high(i) : high[i] == max(high[i-k .. i+k])     # k = lebar, wajib ditetapkan
pivot_low(i)  : min pada jendela yang sama
HH/HL         : pivot tinggi dan pivot rendah berikutnya keduanya naik  -> struktur naik
LH/LL         : keduanya turun                                          -> struktur turun
range         : tidak ada HH/HL maupun LH/LL selama m swing berturut     # m juga parameter
```

Ukuran rezim yang bersifat statistik, bukan visual:

```
ADF        : H0 = ada unit root (deret level = jalan acak). butuh uji, bukan grafik
Hurst H    : H > 0,5 berkelanjutan (tren bisa ditunggangi) · H < 0,5 reversi · H ~ 0,5 acak
kedalaman  : |cumulative return| / sum |return per bar|  -> 0 bolak-balik, 1 satu arah
ATR ratio  : ATR_pendek / ATR_panjang -> >1 vol sedang naik, <1 vol mengempis
```

Proxy yang benar-benar ada di produk: `tools/direction.py` merata-ratakan `|autocorrelation|` return
log pada lag 1, 6, 24 bar; `< 0,05` = `efficient` (keputusan dipaksa `flat`), `>= 0,10` = pola
terukur, antaranya zona abu-abu — contoh terukur MARSCOIN `0,075` ([[Fakta Terukur]] §F).

## Cara pakai yang diklaim

Klaim praktisi (bukan hasil uji kami): tentukan rezim di timeframe besar, lalu hanya pakai aturan
yang cocok di rezim itu — tren untuk *trend rider*, reversi untuk *range*, matikan sisanya. Vendor
indikator menjual "regime switch" sebagai penyebab naiknya win rate. Yang tidak ikut dijual:
berapa banyak varian aturan×rezim dicoba sebelum yang satu ini dipilih.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| bar 1 jam ≥ 2.400 untuk melabeli rezim per segmen | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari, hanya aset **ber-kontrak perp** — [[Fakta Terukur]] §A |
| deret untuk aset tanpa perp (memecoin spot, peluncuran baru) | `ADA-TAPI` | GMGN mentok 1.000 bar ≈ 41,6 hari; tidak cukup walk-forward — §A |
| volum per bar (untuk ATR ratio / kedalaman berbasis dolar) | `ADA-TAPI` | ikut `klines`; belum pernah dipakai melabeli rezim |
| uji stasioneritas (ADF) atau estimasi Hurst | `TIDAK-ADA` | tidak ada satu pun implementasinya di `tools/` |
| histori funding/OI per aset untuk rezim derivatif | `ADA-TAPI` | Bybit `/v5/market/funding/history` **200 baris = 66,3 hari** dan OKX `funding-rate-history` **97,7 hari**, dua-duanya tanpa kunci, interval **8 jam** — [[Fakta Terukur]] §A.5 (diukur 28 Sep dari laptop ini, BELUM dari runner). 8 jam bukan fitur per-bar: tetap veto rezim, bukan sinyal |
| label rezim eksternal (indeks bull/bear, klasifikasi vendor) | `TIDAK-ADA` | tidak ada sumbernya di repo ini |

## Uji di Fabius

Bentuk uji yang sah, belum dijalankan:

1. Label rezim **hanya dari bar ≤ t** ([[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]) dan
   tetapkan `k`, `m`, ambangnya **sebelum** hasil dilihat ([[EV5 - Reproduksibilitas dan Pra-Registrasi]]).
2. Jalankan aturan yang sama di tiap sel (rezim × aturan) dengan `tools/backtest.py`; tiap sel =
   satu percobaan, jadi koreksi ganda wajib ikut ([[EV3 - Signifikansi dan Multiple Testing]]).
3. Kontrol: bukan "tanpa filter", tapi **filter acak pada segmen yang sama**. Kalau filter acak
   memberi hasil sama, label rezimnya tidak berisi informasi.
4. Lolos kalau `n >= 20` non-overlap per sel, net di atas **59 bps** terukur ([[Fakta Terukur]] §D),
   tetap positif setelah fold terbaik dibuang, lolos BH α 0,10 (§E).

Yang **sudah** terjadi: `tools/backtest.py` menjalankan 5 segmen waktu tanpa label rezim dan gerbang
`|acf|` dicabut sebagai uji sensitivitas — net rugi di **12/12** simbol (§F). Jadi penolaknya bukan
penyebab rugi; itu belum membuktikan label rezim membantu. Perintah uji berlabel yang dibutuhkan:
`tools/regime_study.py` — **belum ditulis**.

## Batas dan mode gagal

- **Deteksi rezim bisa di-overfit sebelum aturan apa pun diuji.** `k`, `m`, ambang ADF/Hurst,
  jumlah rezim = empat tuas; ruang hipotesis mengembang, dan koreksi ganda harus ikut ([[QT4 - Overfitting dan Validasi]]).
- **Hampir semua label rezim lahir pasca-hasil.** Di chart yang sudah bergerak, trennya jelas;
  dihitung pada `t`, ia punya lag struktural — harga berpindah sebelum label berubah.
- **Rezim dan horizon bisa saling menyangkal.** "Tren" pada 1 jam dan pada 1 hari boleh berlawanan;
  tanpa horizon yang dikunci lebih dulu, perdebatannya tidak pernah selesai ([[FD9 - Horizon Waktu dan Multi-Timeframe]]).
- **Duplikasi.** `|acf|`, Hurst, dan "kedalaman tren" pada dasarnya mengukur autokorelasi: tiga
  nama, satu derajat kebebasan. Memakai ketiganya sebagai konfirmasi terpisah = menghitung satu
  hal tiga kali.
- **Survivorship.** Yang bisa kita hargai sendiri = yang punya kontrak perp; rezimnya adalah rezim
  aset yang selamat (§A).
- **Ongkos tidak ikut berganti rezim.** Edge tipis di rezim terbaik tetap mati oleh ongkos
  ([[FD4 - Ongkos Perdagangan]]).

## Tingkat bukti

`T1` untuk HH/HL dan ATR ratio (dipakai luas, tidak kami uji) · `T2` untuk ADF/Hurst sebagai
perkakas statistik (literaturnya ada, tidak kami reproduksi) · untuk Fabius: **belum diuji**,
dengan flag `NEGATIF` pada klaim "menyaring rezim menciptakan edge" — uji yang paling dekat
(12/12 rugi dengan dan tanpa gerbang) tidak mendukungnya.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "sebelum bertanya 'apakah indikator ini bekerja', tanya 'di keadaan pasar apa';
  Fabius menuliskan satu proxy keadaan pasar ke dalam hash keputusan, dan proxy itu paling sering
  berkata tidak ada arah."
- **Dilarang:** "Fabius mengenali rezim pasar" · "filter rezim menaikkan win rate" · "HH/HL
  membuktikan tren" (tanpa `k` dan `m` yang dibakukan, itu hanya deskripsi chart).

**Terkait:** [[FD8 - Volatilitas]] · [[FD9 - Horizon Waktu dan Multi-Timeframe]] ·
[[S3 - Market Structure BOS dan ChoCH]] · [[I2 - RSI dan Divergence]] ·
[[ST4 - Range dan Mean Reversion]] · [[ST5 - Trend Rider]] · [[GAP2 - Uji Setiap Veto Terhadap Hasil]]
