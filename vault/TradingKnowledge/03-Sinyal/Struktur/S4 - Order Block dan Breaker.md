---
tags: [tk, tk-sinyal, "S4"]
---

# S4 - Order Block dan Breaker

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"Bedah detail SMC & Order Block" — klaim komunitas
praktisi, **bukan** hasil uji kami

**Ringkas:** "Order block" adalah candle terakhir berlawanan arah sebelum pergerakan kuat yang
meninggalkan levelnya; ceritanya: order besar yang belum terisi akan menarik harga kembali ke
candle itu, jadi zona tersebut tempat menunggu dengan risiko terukur. Sebagai aturan geometri ia
jelas; sebagai klaim kausal ("ini jejak institusi") ia tidak pernah diuji oleh siapa pun yang bisa
kita periksa. Catatan ini memisahkan kedua hal itu — dan itu satu-satunya gunanya.

## Definisi yang bisa dihitung

Varian yang dipakai komunitas minimal tiga (candle berlawanan terakhir · candle berlawanan terakhir
**sebelum** *break of structure* · candle dengan volum terbesar dalam impuls). Kami membakukan yang
pertama; varian lain **harus** jadi parameter terpisah saat diuji, bukan jadi "sama saja".

```
bullish_ob(i)  : bar i turun (close[i] < open[i]) dan
                 ada j > i dengan close[j] - high[i] >= K * ATR(t)  # impuls
                 -> zona = [low[i], high[i]]
bearish_ob(i)  : cerminnya (bar naik sebelum impuls turun), zona = [low[i], high[i]]
touch(t)       : low[t] <= zona.atas dan harga sebelumnya di atas zona   # sentuhan pertama
reaction(t)    : close[t] > zona.atas setelah touch                      # "reaksi"
breaker(i)     : bullish_ob yang zona.atas-nya jebol ke bawah, lalu dibaca
                 dari sisi sebaliknya (support jadi resistance)
```

**Ambang `K` dan definisi "reaksi" wajib ditetapkan sebelum hasil dilihat.** Tanpa itu, zona apa pun
bisa dinyatakan "terkonfirmasi" setelah harga bergerak — dan metode ini kehilangan kemampuan
membuktikan apa pun ([[EV6 - Kalibrasi Ambang Terhadap Hasil]]).

## Cara pakai yang diklaim

Entry pada sentuhan pertama zona setelah impuls; stop di bawah `low[i]`; target di likuiditas
berikutnya (high/low yang belum tersentuh — lihat [[S6 - Likuiditas Stop Hunt dan Inducement]]);
filter arah dari timeframe besar ([[FD9 - Horizon Waktu dan Multi-Timeframe]]). Klaimnya: rasio
risiko-imbalan baik karena zonanya sempit. Itu benar **secara geometri** — dan geometri bukan edge.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| OHLC 1 jam, ≥ 2.400 bar | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari — tapi hanya untuk aset **ber-kontrak perp** ([[Fakta Terukur]] §A) |
| jejak order sesungguhnya (yang diklaim membentuk zona) | `TIDAK-ADA` | tidak ada jalur L2/tick di repo ini ([[Fakta Terukur]] §C) |
| volum per bar untuk seleksi zona | `ADA-TAPI` | ikut `klines`, belum pernah kami pakai untuk menyaring zona |
| satu definisi baku yang dipakai semua alat | `TIDAK-ADA` | `tools/direction.py` tidak punya konsep zona sama sekali |
| aliran dompet untuk menguji "ini institusi?" | `ADA-TAPI` | bidang ⑦ point-in-time, jendela lihat 8–13 menit, tanpa riwayat ([[Fakta Terukur]] §B) |

## Uji di Fabius

Bentuk uji yang sah (belum ada yang menjalankan ini — perintahnya belum ditulis):

1. Deteksi zona hanya dengan bar `<= t` (point-in-time, [[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]).
2. Event = sentuhan pertama; hasil = return bersih pada horizon tetap (24 j) **dan** pada kena
   stop, dua-duanya dilaporkan.
3. Pembanding: **arah acak pada token dan jam yang sama** — bukan "tidak ada zona". Alasannya di
   [[Fakta Terukur]] §B: kontrol "trader biasa" mustahil secara struktural pada data kita.
4. Lolos kalau: `n >= 20` non-overlap, gross di atas **59 bps** (ongkos terukur kami, bukan 20 bps
   asumsi), tetap positif setelah fold terbaik dibuang, lolos BH α 0,10. Jalur yang sudah ada untuk
   bentuk uji ini: `tools/backtest.py` (lihat [[06-Results/04 - Negative Results]] untuk apa yang
   terjadi waktu kami melakukan ini pada aturan arah — **12/12 rugi**).

Perintah yang dibutuhkan: `tools/ob_study.py` — **belum ditulis**. Jangan mengutip catatan ini
seolah-olah ada hasilnya.

## Batas dan mode gagal

- **Subjektivitas pasca-hasil.** Zona hanya terlihat jelas di chart yang sudah bergerak. Ini
  penyakit utamanya, dan ia tidak bisa dihilangkan dengan memperhalus aturan visual.
- **Parameter bebas bersembunyi di "impuls".** `K`, panjang ATR, dan definisi reaksi = tiga tuas
  yang bisa menaikkan hasil apa pun di backtest ([[QT4 - Overfitting dan Validasi]]).
- **Aset yang kami bisa uji bukan aset yang diklaim.** Cerita order block lahir di memecoin;
  yang bisa kami hargai sendiri adalah 608 kontrak perp. Menguji S4 pada BNB lalu menjualnya sebagai
  "ilmu meme" = klaim yang melebihi yang diukur.
- **"Smart money" di SMC ≠ dompet yang kami rekam.** Yang pertama cerita tentang institusi; yang
  kedua = daftar GMGN yang keanggotaannya adalah pilihan vendor ([[O5 - Whale dan Kohor Smart Money]]).
  Menyamakan keduanya adalah lompatan yang membuat seluruh keluarga SMC terdengar lebih berbukti
  daripada kenyataannya.
- Zona sempit = stop sempit. Di aset dengan likuiditas setipis memecoin BSC, penolakan keluar
  lebih sering terjadi daripada pantulan dari zona ([[FD3 - Likuiditas dan Dampak Harga]]).

## Tingkat bukti

`T1` untuk geometri (dipakai luas, definisinya tidak dibakukan siapa pun) · `T0` untuk klaim
penyebabnya ("institusi meninggalkan jejak") · untuk Fabius: **belum diuji** — tidak ada satu pun
baris di `tools/` yang menghitung zona.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "zona yang ditinggalkan impuls besar adalah tempat tunggu yang masuk akal **kalau**
  definisinya dibakukan sebelum melihat hasil; belum kami uji."
- **Dilarang:** "institusi meninggalkan jejak yang bisa dibaca dari candlestick" · "Fabius
  memakai SMC/order block" · "SMC paling powerful di crypto 2023–2026" (kalimat dari `Plan.txt`,
  tanpa sumber, tanpa definisi "powerful").

**Terkait:** [[S3 - Market Structure BOS dan ChoCH]] · [[S5 - Fair Value Gap]] ·
[[S6 - Likuiditas Stop Hunt dan Inducement]] · [[S1 - Candlestick dan Price Action Murni]] ·
[[FD2 - Support Resistance dan Level Psikologis]] · [[O5 - Whale dan Kohor Smart Money]] ·
[[PL3 - Menganalisis]]
