---
tags: [tk, tk-sinyal, "I4"]
---

# I4 - Bollinger Bands

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"metode trading itu ada apa aja sih?" (Bollinger Bands
disebut di daftar indikator standar) — klaim komunitas; tidak ada rujukan yang bisa kami periksa di
repo ini

**Ringkas:** Tiga garis: rata-rata, dan dua pita pada `k` simpangan baku di atas dan bawahnya. Pita
itu **mengukur** sebaran harga terkini, tidak memprediksinya — saat volatilitas meledak, pita melebar
karena rumusnya memanggil volatilitas itu sendiri, bukan karena ia menubuatkan ledakan. Sebagian
besar gunanya terletak di mode gagal: pita yang menempel = pasar tanpa arah; harga yang menempel di
pita = tren, tempat trading "kembali ke rata-rata" justru rugi.

## Definisi yang bisa dihitung

```
mid[t]  : SMA(c, n, t)                              # konvensi SMA, bukan EMA
sd[t]   : simpangan baku c[t-n+1 .. t]              # WAJIB disebut: sampel (n-1) atau populasi (n)
up[t]   : mid[t] + k*sd[t]            lo[t] = mid[t] - k*sd[t]      # default (n, k) = (20, 2)
%B[t]   : (c[t] - lo[t]) / (up[t] - lo[t])          # ternormalisasi, lintas-aset -> lihat I6
bw[t]   : (up[t] - lo[t]) / mid[t]                  # ukuran volatilitas relatif
squeeze : bw[t] <= persentil_p(bw, jendela W)       # p dan W = dua parameter lagi
touch_lo(t) : low[t] <= lo[t]        revert(t) : close[t+1..t+H] kembali ke dalam pita
```

Dua hal yang mengubah kesimpulan dan jarang disebut: **konvensi simpangan baku** (berbeda ± beberapa
persen, cukup untuk memindahkan "sentuhan") dan **apakah sentuhan dihitung dari `low` atau `close`**
— sama seperti perdebatan close-vs-wick di [[S3 - Market Structure BOS dan ChoCH]].

## Cara pakai yang diklaim

Beli saat harga menyentuh pita bawah di dalam rentang, jual di mid-line atau pita atas ("mean
reversion"); `squeeze` sebagai peringatan pergerakan besar akan datang; pelebaran pita sebagai
konfirmasi breakout. Pemilik klaim: komunitas indikator dan pembuatnya. Perhatikan bahwa dua klaim
pertama **saling bertentangan** tentang rezim yang sama: yang satu mengandaikan harga akan kembali,
yang lain mengandaikan harga akan pergi. Memilih di antaranya setelah melihat chart adalah seluruh
kesalahannya.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| penutupan 1 jam | `ADA` | `tools/bars.py`; 9.599 bar pada aset ber-perp (§A) |
| penghitung SMA/sd/pita | `TIDAK-ADA` | tidak ada alat Fabius yang menghitung simpangan baku bergulir |
| `n`, `k`, konvensi sd yang dibakukan | `TIDAK-ADA` | belum ada; tanpa itu tidak ada yang bisa direproduksi |
| distribusi `%B` per aset kami | `TIDAK-ADA` | belum diukur *(belum diukur)* — dan ini pertanyaan pertama yang harus dijawab |
| jalur uji peristiwa→hasil | `ADA-TAPI` | `tools/backtest.py` hanya mengeksekusi aturan arah SMA/ret24 |

## Uji di Fabius

Urutan yang jujur, semuanya dari deret yang sudah ada di repo:

1. **Deskriptif dulu:** histogram `%B` dan rentang `bw` per simbol. Kalau `P(low <= pita bawah)`
   tinggi di hampir semua aset (dan pada `k = 2` itu memang terjadi), klaim "sentuhan pita" bukan
   peristiwa langka dan tidak otomatis menarik.
2. Uji dua hipotesis yang berlawanan secara terpisah, bukan digabung jadi "baca konteksnya":
   (a) reversion — long setelah sentuhan pita bawah; (b) continuation — long setelah penutupan di
   atas pita atas dari kondisi squeeze. Horizon 4 j/24 j dengan `tools/backtest.py --horizon`,
   plus jalur kena stop.
3. Null untuk (a) dan (b): level acak dengan **jumlah sentuhan sama** pada simbol dan jam yang sama
   (pola yang sama dengan [[S7 - Fibonacci Retracement dan Extension]]). Ini penting: pita adalah
   fungsi dari deret, jadi "setelah sentuhan" berkorelasi dengan "setelah bar bergerak jauh", dan
   itulah yang harus dibersihkan, bukan dirawat.
4. Laporkan ongkos dua nilai — 20 bps warisan (§D) supaya sebanding dengan §F, dan **59 bps**
   terukur. Sisanya standar: `n >= 20` non-overlap, fold terbaik dibuang, BH α 0,10 (§E).

## Batas dan mode gagal

- **Pita melebar setelah fakta.** Saat volatilitas melompat, `sd` ikut naik dan pita bergerak
  menjauh: harga bisa jatuh 30 % tanpa pernah "keluar" dari pita bawah. Menafsirkan ini sebagai
  "masih di dalam normal" adalah kesalahan struktural, bukan kesalahan parameter.
- **Walking the band** adalah kebalikan dari klaim reversion: di tren kuat harga menutup di luar
  pita berhari-hari. Ini bukan pengecualian kecil; ini rezim tempat uang besar berpindah.
- **Reversi vs momentum bukan selera.** Kami sudah punya satu terukur: aturan momentum kami rugi,
  dan **dibalik pun rugi** (−39,2 … −12,1 bps, §F). Artinya pada universe kami, keduanya bukan
  jalan keluar; pita tidak mengubah itu.
- **Empat parameter terselubung** (`n`, `k`, konvensi sd, persentil squeeze) dengan satu deret
  masukan: ruang untuk membuat apa pun terlihat berhasil ([[QT4 - Overfitting dan Validasi]]).
- **Alternative yang lebih jujur:** pita berbasis jarak ternormalisasi ATR (Keltner-style) tidak
  bergantung pada konvensi sd dan sudah lebih dekat ke yang benar-benar kami pakai
  ([[I6 - ATR dan Jarak Ternormalisasi]], [[FD8 - Volatilitas]]).
- **Ketipisan.** Di aset dengan likuiditas di bawah ambang, harga menyentuh pita lalu tidak bisa
  keluar pada harga itu ([[FD3 - Likuiditas dan Dampak Harga]]).

## Tingkat bukti

`T1` untuk pita sebagai ringkasan volatilitas bergulir (perhitungan baku, dipakai luas) · `T0` untuk
sentuhan pita sebagai pemicu beli/jual, dan untuk `squeeze` sebagai penentu arah · untuk Fabius:
**belum diuji**, tidak ada jalur kodenya.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "pita Bollinger mengukur sebaran harga terakhir; ia berguna justru untuk mengenali
  kapan reversion tidak boleh dipakai; belum kami uji pada data kami."
- **Dilarang:** "harga keluar pita jadi akan kembali" (tanpa horizon, tanpa null) · "Fabius menyaring
  dengan Bollinger" · menyebut `squeeze` sebagai prediksi arah.

**Terkait:** [[I1 - Moving Average]] · [[I2 - RSI dan Divergence]] ·
[[I6 - ATR dan Jarak Ternormalisasi]] · [[FD8 - Volatilitas]] · [[S4 - Order Block dan Breaker]] ·
[[ST4 - Range dan Mean Reversion]] · [[Fakta Terukur]]
