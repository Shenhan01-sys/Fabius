---
tags: [tk, tk-setup, "ST3"]
---

# ST3 - Clean Price Action

**Keluarga:** [[00 - Hub Setup]]
**Anggota:** [[S3 - Market Structure BOS dan ChoCH]] · [[S4 - Order Block dan Breaker]] ·
[[S7 - Fibonacci Retracement dan Extension]] · [[FD9 - Horizon Waktu dan Multi-Timeframe]] ·
[[FD1 - Struktur Pasar dan Rezim]] · [[FD7 - Invalidation Stop dan Time-Stop]]
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"Kombinasi C – Clean Price Action" *(resep komunitas;
"tanpa terlalu banyak indikator" adalah bahasa pendukungnya, bukan hasil uji)*

**Ringkas:** versi paling hemat dari keluarga SMC: arah dari BOS/ChoCH, tempat dari order block,
pelaras dari Fibonacci, penguat dari timeframe besar. Ini **setup termurah yang bisa kita uji**:
nol API baru, nol kunci, nol vendor — satu deret `klines` yang sudah kami tarik. Murah datanya bukan
murah buktinya: semua anggotanya berasal dari deret yang sama, dan justru karena itu ia wajib diuji
sebagai satu kesatuan, bukan sebagai empat pujian.

## Resep

| tahap | aturan | catatan |
|---|---|---|
| bias | BOS di TF besar menentukan satu-satunya arah yang boleh diambil | [[S3 - Market Structure BOS dan ChoCH]] · [[FD9 - Horizon Waktu dan Multi-Timeframe]] |
| zona | OB searah bias, di sisi retracement | [[S4 - Order Block dan Breaker]] |
| pelaras | cluster Fib 0,618/0,705 yang jatuh di dalam zona | [[S7 - Fibonacci Retracement dan Extension]] |
| pemicu | ChoCH di TF kecil di dalam zona | definisi "ChoCH" belum dibakukan siapa pun — kuncikan sebelum melihat hasil |
| invalidation | ChoCH batal / harga menutup di luar zona | [[FD7 - Invalidation Stop dan Time-Stop]] — **harus terhitung sebelum masuk** |
| target | ekstrem struktur sebelum sweep, atau ekstensi | [[S6 - Likuiditas Stop Hunt dan Inducement]] |
| ukuran | plafon kontrak, bukan persentase modal yang dipilih sendiri | [[FD6 - Ukuran Posisi]]; `dailyCap` · `maxPositionQuote` (§E) |
| keluar waktu | horizon tetap, zona belum tersentuh = batal | [[FD7 - Invalidation Stop dan Time-Stop]] |

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| OHLC 1 jam ≥ 2.400 bar | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari — **hanya** aset ber-kontrak perp; C2/D mentok 1.000 bar ≈ 41,6 hari ([[Fakta Terukur]] §A) |
| deret TF kecil yang berbeda dari TF besar | `ADA-TAPI` | yang kami punya satu kolom bar; "MTF" di kode kami = lihat-balik 24 bar pada deret 1 jam yang sama (`ret24`/`sma` di `tools/direction.py`), bukan dua timeframe |
| satu definisi BOS/ChoCH/OB/Fib yang dihitung sama oleh semua alat | `TIDAK-ADA` | tidak ada satu pun baris di `tools/` yang menghitung ketiganya |
| kunci API / vendor tambahan | tidak dibutuhkan | inilah isi "clean"-nya: nol biaya data |
| tick / L2 untuk memeriksa klaim "order" di order block | `TIDAK-ADA` | §C — klaim kausal S4 tetap tidak bisa disentuh |

## Uji di Fabius

Satu-satunya setup di folder ini yang bisa diuji **dengan perkakas yang sudah ada**, dan itu alasan
untuk mendahulukannya — bukan alasan untuk mempercayaannya.

1. Tulis detektor point-in-time (bar `<= t`; [[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]])
   untuk keempat syarat sekaligus: satu event, satu nama, satu file parameter.
2. **Pra-registrasi sebelum hasil pertama dilihat** ([[EV5 - Reproduksibilitas dan Pra-Registrasi]]):
   definisi swing, ambang "impuls", panjang cluster Fib, horizon, ongkos. Empat anggota = empat tempat
   menyembunyikan parameter bebas ([[QT4 - Overfitting dan Validasi]]).
3. Jalankan sebagai kesatuan, lalu **ablasi**: bias saja → +zona → +pelaras → +penguat TF besar.
   Yang dicari adalah **kenaikan marjinal expectancy per syarat**, bukan daftar syarat.
4. Ambang: `n >= 20` non-overlap, ongkos **59 bps** (§D), positif setelah fold terbaik dibuang,
   BH α 0,10 (§E). Perintah paling dekat: `tools/backtest.py` — sekarang dia menjalankan aturan arah
   `direction.py`, yang hasilnya sudah tercatat rugi 12/12 (§F).

Sampel yang tersisa setelah empat syarat serentak: *(belum diukur)*.

## Konfluensi atau gaung

Empat anggota, satu sumber. Tabel ini bagian terpenting dari catatan ini:

| anggota | input sebenarnya |
|---|---|
| bias BOS/ChoCH | urutan `high`/`low` |
| zona OB | `low`/`high` bar yang sama, window geser |
| level Fib | dua titik dari `high`/`low` yang sama, dikali konstanta |
| penguat TF besar | agregasi (resampling) dari bar yang sama |

Jadi empat "konfirmasi" ini adalah **empat transformasi atas satu vektor**. Menyetujui keempatnya
tidak mungkin menghasilkan informasi yang tidak ada di vektor itu; yang pasti dihasilkan adalah
keyakinan yang lebih besar dengan event yang lebih sedikit. Konfluensi yang sah butuh anggota kedua
yang datanya berbeda (volum, aliran dompet, funding) — di ST3 itu tidak ada, dan itulah bedanya
dengan [[ST6 - Aliran On-Chain Fabius]].

Yang tetap boleh diperjuangkan: **geometrinya murah dan bisa dibuktikan salah.** Pertanyaan "apakah
sentuhan zona menghasilkan return bersih > 59 bps pada 24 j" adalah pertanyaan yang bisa dijawab
dengan data yang ada; jawabannya hari ini belum ada, dan bukan karena datanya kurang.

## Batas dan mode gagal

- **Konfluensi sebagai pengurang n.** Empat syarat serentak = sedikit event. Setup yang "paling bersih"
  adalah setup yang paling sering tidak memenuhi `MIN_SAMPLES=20` — kegagalan statistik, bukan kegagalan pasar.
- **Zona yang terlihat hanya setelah harga bergerak** (penyakit utama S4). Tanpa definisi terkunci,
  setup ini tidak bisa salah — dan yang tidak bisa salah tidak bisa dipakai.
- **Bias arah kami sudah diuji dan kalah.** Anggota "arah" pada bentuk terdekatnya (gap SMA + ret24)
  net-nya rugi di 12/12 aset setelah ongkos, gross cuma +1,5 … +4,0 bps (§F). Menumpuk tiga syarat
  geometri di atasnya belum terbukti menambah 55 bps yang hilang.
- **Rezim.** [[FD1 - Struktur Pasar dan Rezim]]: ChoCH berulang di pasar sideways = mesin rugi-rugi
  kecil; di pasar satu arah, "retrace ke 0,618" bisa berarti baru mulai.
- **Likuiditas keluar.** Zona sempit + stop sempit di aset tipis: yang mematikan bukan levelnya,
  tapi kemampuan keluar padanya (§E gerbang ⑥, [[FD3 - Likuiditas dan Dampak Harga]]).

## Tingkat bukti

`T0` — resep komunitas, belum pernah dijalankan sebagai kesatuan. Catatan penting untuk pembaca
cepat: `T0` di sini berarti **belum diuji**, bukan **tidak bisa diuji** — ST3 adalah yang paling
murah untuk diuji di antara semua setup di folder ini.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "setup ini hanya butuh OHLC yang sudah kami punya; keempat anggotanya fungsi dari deret
  yang sama; belum diuji sebagai kesatuan; pengujinya sudah bisa ditulis hari ini."
- **Dilarang:** "price action bersih lebih andal karena minim indikator" · " empat konfluensi
  probabilitas tinggi" · "Fabius membaca struktur pasar" (tidak ada kodenya).

**Terkait:** [[ST7 - Checklist Keputusan]] · [[ST1 - All-Rounder]] · [[EV5 - Reproduksibilitas dan Pra-Registrasi]] ·
[[QT2 - Backtesting yang Jujur]] · [[GAP3 - Yang Punya Data Tapi Belum Diuji]]
