---
tags: [tk, tk-sinyal, "S2"]
---

# S2 - Chart Patterns

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"metode trading itu ada apa aja sih?" — daftar topik
dari transkrip; klaimnya ("sangat akurat", "sangat kuat") bukan hasil ukur

**Ringkas:** "Pola chart" adalah nama untuk bentuk yang dikenali mata pada jendela beberapa puluh
bar: head & shoulders, double top/bottom, triangle, flag, cup & handle. Semua bisa ditulis sebagai
pertidaksamaan pada ayunan, jadi semuanya bisa diuji — dan justru di situ masalahnya muncul: sebuah
detektor butuh sekitar enam parameter bebas sebelum ia bisa menyebut sesuatu "H&S", dan jumlah itu
cukup untuk menyesuaikan pola ke hasil mana pun. Catatan ini memisahkan **pola sebagai ringkasan**
(ia meringkas struktur + volum dengan satu kata) dari **pola sebagai penyebab** (ia tidak
menyebabkan apa pun; yang bergerak adalah order, dan order tidak kita punya).

## Definisi yang bisa dihitung

Pola = himpunan ayunan + relasi di antaranya + aturan pecah. Ayunan dihitung dengan fractal
([[S3 - Market Structure BOS dan ChoCH]]):

```
swing_high(i)  : h[i] = max(h[i-N .. i+N])            # N = parameter #1; baru SAH di i+N
H&S              : tiga ayunan tinggi dengan t2 < t1 < t3? tidak: t1 tertinggi,
                   t2 dan t3 setinggi-tingginya (1 - d) * t1      # d = toleransi #2
neckline         : garis dua low antara bahu           # kemiringan: parameter #3
break(t)         : close[t] < neckline(t) - b * ATR    # close-vs-wick: parameter #4
symmetry         : |t3 - t2| / t1 <= s                 # #5
durasi & kedalaman: (t3 - t1) dalam bar, dan Retracement maksimum dari ayunan   # #6
double top       : H&S dengan bahu hilang (dua high, toleransi d)  # bukan pola lain, kasus degenerate
flag / pennant   : impuls >= q * ATR dalam p bar, lalu rentang menyempit r bar, lalu pecah
cup & handle     : butuh cekung-parabola + pegang; paling banyak parameter, paling sedikit definisi
```

**Sebuah pola terdeteksi otomatis** hanya kalau keenam angka itu ditulis sebelum hasil dilihat dan
tidak diubah sesudahnya. Yang membedakan "studi objektif" dari "mata manusia" persis di sini:
detektor dipaksa memilih satu definisi dan membayarnya dengan jumlah sampel.

## Cara pakai yang diklaim

Entry pada penembusan garis leher / batas rentang; stop di balik ayunan terakhir; target = tinggi
pola diproyeksikan dari titik pecah. Pemilik klaimnya buku pola dan praktisi. Ada literatur yang
pernah mengukur ini secara algoritmik (nama yang biasa dikutip untuk deteksi pola berbasis regresi
kernel dan penyandingan kemiripan antarsesi, awal 2000-an) — **tidak pernah kami reproduksi, dan
angka apa pun darinya tidak kami kutip** karena tidak bisa dijalankan dari clone ini.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| OHLC 1 jam, ≥ 2.400 bar | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari, hanya aset ber-perp ([[Fakta Terukur]] §A) |
| ayunan yang terdefinisi point-in-time | `ADA-TAPI` | butuh `N` bar ke depan untuk konfirmasi → label selalu tertinggal `N` bar |
| volum per bar (untuk flag vs cup, breakout "asli") | `ADA` | `v` per bar di cache `tools/bars.py`; belum pernah dipakai untuk menyaring breakout |
| pemisahan aggresor beli/jual | `TIDAK-ADA` | kolom taker dibuang `tools/bars.py` |
| detektor pola | `TIDAK-ADA` | tidak ada satu pun alat Fabius yang mendeteksi pola |
| deret cukup panjang untuk pola multi-minggu | `ADA-TAPI` | `MIN_BARS_TINY=720` (30 hari) terlalu pendek; H&S mingguan tidak terwakili di kandidat pendek |

## Uji di Fabius

1. Tetapkan `(N, d, s, b, q, r, p)` dan horizon (4 j dan 24 j) **sebelum** melihat hasil; tulis di
   `06-Results/05 - Pre-registration Flow.md` alur pra-registrasinya.
2. Event = penembusan; hasil = return bersih sampai horizon **dan** sampai kena stop, dua-duanya.
3. Null yang benar bukan "tidak ada pola", melainkan **penembusan acak dengan jumlah sama** pada
   simbol dan jam yang sama ([[Fakta Terukur]] §B). Pola yang mengalahkan null-hnya sendiri
   barulah klaim.
4. Gerbang: `n >= 20` non-overlap, BH α 0,10, tetap positif setelah fold terbaik dibuang, gross vs
   **59 bps** (§D/§E). `tools/backtest.py` sudah punya bentuk bersegmen + drop-best-fold-nya untuk
   aturan arah; jalur pola belum ada dan harus ditulis sebagai fitur, bukan sebagai narasi.

## Batas dan mode gagal

- **Pola belum menjadi pola saat kamu butuh.** Bahu kiri hanya sah setelah bahu kanan terbentuk;
  membaca H&S di bahu pertama adalah melihat masa lalu dengan mata masa kini ([[Concepts/Lookahead Bound]]).
- **Enam parameter = enam tuas naikkan hasil.** Ini penyakit utama, dan ia tidak hilang dengan
  "pengalaman membaca chart" ([[QT4 - Overfitting dan Validasi]]).
- **Degenerasi kelas.** Double top = H&S tanpa bahu; triangle = rentang dengan ambang miring; kalau
  definisi boleh melonggar saat tidak cocok, keluarga ini tidak bisa disalahkan oleh data apa pun —
  itu status `T0`-nya, bukan `T1`.
- **Proyeksi target mengasumsikan kelanjutan yang sama rata.** Target "setinggi pola" adalah
  geometri, bukan distribusi; di aset dengan likuiditas setipis kandidat kami, penembusan bisa
  membeli 40 bps lalu menyerahkan 400 bps ([[FD3 - Likuiditas dan Dampak Harga]]).
- **Ongkos.** Breakout = masuk saat spread dan dampak paling besar, tepat ketika volum meledak.
  Semua edge tipis di keluarga ini mati lebih dulu oleh 59 bps (§D).
- **Survivorship buku.** Yang dibukukan adalah pola yang selesai; pola yang gagal membentuk apa pun
  tidak punya nama, jadi frekuensi "keberhasilan" di kanon bukan estimasi.
- **Duplikasi.** Setiap pola chart adalah ringkasan dari [[S3 - Market Structure BOS dan ChoCH]] +
  volum; menambah namanya tidak menambah informasinya — hanya menambah parameter
  ([[V1 - Konfirmasi Volum dan Money Flow]], [[V2 - Volume Profile dan POC]]).

## Tingkat bukti

`T2` untuk klaim "pernah diukur secara algoritmik di pasar lain" (ada literatur, tidak kami
reproduksi, tidak kami kutip angkanya) · `T1` untuk kegunaan sebagai bahasa/deskripsi · `T0` untuk
klaim prediktif yang beredar di komunitas · untuk Fabius: **belum diuji**, tidak ada detektornya.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "pola chart dapat dihitung dan karena itu dapat diuji terhadap penembusan acak dengan
  jumlah pemicu sama; kami belum pernah menjalankan uji itu."
- **Dilarang:** "H&S punya akurasi X %" (angka dari luar, tidak direproduksi) · "pola menunjukkan
  bahwa smart money sedang accumulating" · "Fabius mendeteksi pola chart".

**Terkait:** [[S1 - Candlestick dan Price Action Murni]] · [[S3 - Market Structure BOS dan ChoCH]] ·
[[S8 - Wyckoff]] · [[FD2 - Support Resistance dan Level Psikologis]] ·
[[EV2 - Jebakan Backtest]] · [[Fakta Terukur]]
