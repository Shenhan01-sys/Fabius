---
tags: [tk, tk-sinyal, "I5"]
---

# I5 - Ichimoku Cloud

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"metode trading itu ada apa aja sih?" (Ichimoku Cloud
disebut di daftar indikator) — klaim komunitas; asal-usul parameternya tidak punya rujukan di repo ini

**Ringkas:** Lima garis yang semuanya turunan dari **titik tengah rentang ekstrem** pada tiga
panjang jendela, plus dua pergeseran sumbu waktu. Desainnya pra-computer — konvensi yang beredar
menyebutnya digambar tangan selama bertahun-tahun sebelum diterbitkan — dan itu menjelaskan bentuknya:
satu gambar yang harus menjawab arah, momentum, support, dan target sekaligus. Hasilnya sebuah sistem
yang **koheren sebagai deskripsi** dan berat sebagai sinyal: lima belas konstanta window/shift untuk
satu deret penutupan, high, low.

## Definisi yang bisa dihitung

```
tenkan(t)  : (max(h, 9) + min(l, 9)) / 2                     # jendela 9 bar
kijun(t)   : (max(h, 26) + min(l, 26)) / 2
senkouA(t) : (tenkan(t) + kijun(t)) / 2, digambar di t + 26   # leading: dari data lalu ke depan
senkouB(t) : (max(h, 52) + min(l, 52)) / 2, digambar di t + 26
chikou(t)  : close[t] digambar di t - 26                      # lagging: dibandingkan dgn 26 bar lalu
cloud(t)   : [min(senkouA, senkouB), max(senkouA, senkouB)]
aturan     : harga di atas awan = boleh long; di bawah = boleh short; di dalam = tidak ada arah
             tenkan×kijun cross = pemicu; chikou bebas dari harga 26 bar lalu = "konfirmasi"
```

Konstruksinya bukan rata-rata penutupan melainkan **tengah dua ekstrem** — lebih tahan satu lonjakan
dan lebih lambat terhadap perubahan, karena satu bar ekstrem bisa mendominasi jendela 52.

## Cara pakai yang diklaim

Sebagai "sistem lengkap": arah dari posisi harga terhadap awan, entry dari persilangan tenkan/kijun
di luar awan, target dari awan sisi lain, invalidasi di luar kijun. Klaim komunitas menyebutnya
"semua dalam satu gambar". Sebagai deskripsi satu layar, itu benar; sebagai mesin prediksi, ia
menyembunyikan tiga pertanyaan berbeda (arah, pemicu, batas) di bawah satu nama, dan itu menyulitkan
atribusi saat ia salah.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| OHLC 1 jam, ≥ 78 bar untuk hangat penuh | `ADA-TAPI` | Aster 9.599 bar pada aset ber-perp (§A); awan ke depan butuh 26 bar lagi |
| kandidat berumur jam | `TIDAK-ADA` | pool baru ±30 bar dan `MIN_BARS_TINY=720` → jendela 52 + shift 26 tidak pernah terisi (§A/§E) |
| penghitung lima komponen | `TIDAK-ADA` | tidak ada satu pun alat Fabius yang menghitung tenkan/kijun/awan |
| konvensi shift yang dibakukan | `TIDAK-ADA` | platform berbeda menggeser ke baris berbeda; ini mengubah level yang "disinggahi" |
| jalur uji peristiwa→hasil | `ADA-TAPI` | `tools/backtest.py` hanya menjalankan aturan arah SMA/ret24 |

## Uji di Fabius

1. Perlakukan tiap aturan sebagai **hipotesis terpisah** (harga-atas-awan; tenkan×kijun; chikou
   bebas): kalau diuji bersama sebagai "sistem", kamu tidak akan pernah tahu bagian mana yang
   menyumbang, termasuk saat ia rugi ([[QT1 - Dari Ide ke Strategi yang Bisa Diuji]]).
2. Semua komponen hanya dari bar `<= t`; **jangan** memakai awan yang digambar ke depan sebagai
   support di masa lalu — itu nilai dari data lalu yang digeser, bukan pengetahuan tentang masa
   depan, dan memakai posisinya di chart sebagai "level yang akan datang" adalah lookahead berbalut
   visual ([[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]).
3. Null: arah acak pada simbol dan jam yang sama; pembanding kedua: **aturan satu garis** — `close >
   max(h,l window 52)/2` — karena jika awan tidak mengalahkan satu level tengah, lima komponen itu
   tidak membeli apa pun.
4. Horizon 4 j dan 24 j (`tools/backtest.py --horizon`), hasil bersih **dan** kena stop; ongkos
   59 bps terukur (§D); `n >= 20` non-overlap, fold terbaik dibuang, BH α 0,10 (§E). Belum ada
   jalur kodenya: perintahnya harus ditulis, bukan dibayangkan.

## Batas dan mode gagal

- **Awan kosong/tipis = tidak ada informasi**, dan itu membacaan yang benar: saat senkouA dan
  senkouB bersilangan, sistem sendiri menyatakan tidak ada arah. Fabius sudah punya padanannya
  secara formal — `side: flat` dan rezim `efficient` saat |acf| < 0,05 (`tools/direction.py`).
  Yang tidak boleh: memaksa posisi saat sistemnya sendiri diam.
- **Lambat tiga kali.** Ekstrem jendela 52, dihaluskan jadi titik tengah, lalu digeser 26 bar:
  total keterlambatan jauh di atas `gap(24)` kami — dan `gap(24)` saja sudah rugi di 12/12 (§F).
- **Enam window + dua shift = delapan tuas.** Parameter 9/26/52 adalah konvensi, bukan hasil ukur
  kami; menyetelnya di data kami adalah overfitting dengan nama Jepang
  ([[QT4 - Overfitting dan Validasi]]).
- **Duplikasi struktural.** Semua komponennya fungsi monotonal dari `h,l,c` yang sama:
  tidak ada informasi baru di atas [[I1 - Moving Average]] atau [[I3 - MACD]] — hanya lebih banyak
  cara menuliskan keterlambatan.
- **Tafsir "level awan" sebagai magnet harga** adalah klaim kausal tanpa mekanisme yang bisa
  diperiksa: tidak ada order book di repo ini (§C), jadi tidak ada yang tahu siapa yang menunggu di
  sana.
- **Ongkos & ketipisan.** Awan berubah bentuk pelan, jadi invalidasi "di luar kijun" bisa berjarak
  ratusan bps; di aset tipis itu melewati batas keluar yang masuk akal
  ([[FD6 - Ukuran Posisi]], [[FD3 - Likuiditas dan Dampak Harga]]).

## Tingkat bukti

`T1` untuk lima komponennya sebagai deskripsi tren satu layar · `T0` untuk klaim bahwa persilangan
atau batas awan memprediksi arah, dan untuk asal-usul "dirancang lewat trial puluhan tahun" (tidak
ada pemilik hasil yang bisa kami periksa) · untuk Fabius: **belum diuji**, tidak ada jalurnya.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "Ichimoku adalah ringkasan tren yang lengkap tapi berat; bagian paling jujurnya adalah
  saat ia bilang tidak ada arah — dan itu sudah kami punya lewat gerbang |acf|."
- **Dilarang:** "harga akan dipantulkan awan" · "Fabius memakai Ichimoku" · membaca awan yang
  digambar ke depan sebagai cara mengetahui masa depan.

**Terkait:** [[I1 - Moving Average]] · [[I3 - MACD]] · [[I4 - Bollinger Bands]] ·
[[FD9 - Horizon Waktu dan Multi-Timeframe]] · [[S3 - Market Structure BOS dan ChoCH]] ·
[[Fakta Terukur]]
