---
tags: [tk, tk-sinyal, "S3"]
---

# S3 - Market Structure BOS dan ChoCH

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"Buatkan panduan prioritas belajar SMC" (fase 1,
daftar komunitas); klaimnya "inti dari modern price action, sangat jelas untuk tentukan arah"

**Ringkas:** Ini bagian keluarga SMC yang paling bisa dipertanggungjawabkan, karena objeknya
bukan niat siapa pun: ayunan tinggi/rendah dan fakta bahwa harga menutup di luarnya. Tidak ada
"institusi" di dalamnya — hanya empat angka per bar dan satu aturan pemilihan titik. Justru karena
ia sederhana, sisanya adalah soal definisi: ayunan belum sah sampai `N` bar lewat, dan `N` itu adalah
**harga** dari metode ini. Catatan ini membakukan satu definisi, menyebut berapa lama ia tertinggal,
dan menandai bahwa di repo kami sendiri kata "struktur" belum pernah jadi kode.

## Definisi yang bisa dihitung

```
swing_high(i,N) : h[i] >= h[j] untuk semua j dalam (i-N .. i+N), j != i   # baru SAH di i+N
swing_low(i,N)  : cerminnya
HH / HL / LH / LL : bandingkan swing_high/low yang SAH berturut-turut
break_up(t)     : close[t] > h[s]  dengan s = swing_high terakhir yang belum patah   # close-based
break_up_wick   : high[t] > h[s]                                                   # wick-based
BOS(t)          : break yang meneruskan urutan (HH->HH, LL->LL)  # = "tren berlanjut"
ChoCH(t)        : break yang mematahkan urutan (sedang HH/HL lalu break_down, atau sebaliknya)
```

**BOS dan ChoCH adalah primitif yang sama** dengan rujukan berbeda (ekstrem searah vs ekstrem
berlawanan). Menamainya dua hal membuat keluargannya terdengar lebih berstruktur daripada
kenyataannya: yang berubah hanya level mana yang kamu jadikan acuan.

Tiga keputusan definisi yang wajib ditulis sebelum uji: `N` (panjang ayunan), **close vs wick**,
dan apakah sebuah ayunan boleh **direvisi** kalau bar setelahnya membuat ekstrem baru. Varian
ketiga inilah yang memproduksi tuduhan "structure-nya berubah lagi": bukan datanya yang berubah,
definisi tidak ditetapkan.

## Cara pakai yang diklaim

Bias arah dari timeframe besar, tunggu ChoCH di timeframe kecil sebagai "konfirmasi pembalikan",
masuk pada retracement pertama setelah ChoCH, invalidasi di balik ayunan yang baru patah
([[S4 - Order Block dan Breaker]], [[S7 - Fibonacci Retracement dan Extension]]). Pemilik klaim:
praktisi SMC/ICT di `Plan.txt`. Tidak ada satu pun dari mereka yang menyertakan `N`, toleransi,
atau base rate — jadi klaimnya ada di level cerita, bukan level protocol.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| OHLC 1 jam ≥ 2.400 bar | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari — hanya aset ber-perp ([[Fakta Terukur]] §A) |
| OHLC untuk kandidat berumur jam | `ADA-TAPI` | `MIN_BARS_TINY=720` (30 hari) membuat mayoritas kandidat BSC tidak layak dinilai sama sekali (§A/§E) |
| multi-timeframe (bias HTF) | `ADA-TAPI` | per-bar 1 j tersedia; interval lain belum ditarik `tools/bars.py` |
| penghitung ayunan / pemutus struktur | `TIDAK-ADA` | tidak ada alat Fabius yang mendeteksi ayunan |
| order yang membentuk ayunan | `TIDAK-ADA` | tidak ada L2/tick di repo ini ([[Fakta Terukur]] §C) |

Satu ketidakcocokan yang menipu pembaca kode: docstring `tools/direction.py` menyebut stop "di
struktur (ATR/swing)", tetapi `decide_one()` memasang `stop = harga ± 1,5 × ATR` dan
`target = ± 3,0 × ATR`. Tidak ada jalur swing yang diimplementasikan — kata "struktur" di sana adalah
niat, bukan kemampuan.

## Uji di Fabius

Bentuk uji yang sah — dan paling murah di seluruh keluarga S, karena tidak butuh data baru:

1. Deteksi ayunan hanya dengan bar `<= t`; **wajib** pakai `swing_high(i,N)` yang sah di `i+N`
   (point-in-time, [[Concepts/Point-in-Time vs Retro-updatable]]). Uji juga varian yang melihat `N`
   bar ke depan dan laporkan selisihnya — selisih itu mengukur seberapa banyak hasil keluarga ini
   berasal dari masa depan.
2. Event = break/ChoCH; hasil = return bersih pada horizon 4 j dan 24 j, **dan** pada kena stop.
3. Null: arah acak pada simbol dan jam yang sama; pembanding kedua: break pada level acak dengan
   jumlah pemicu yang sama ([[Fakta Terukur]] §B, [[S7 - Fibonacci Retracement dan Extension]]).
4. Lolos: `n >= 20` non-overlap, gross di atas **59 bps** terukur (bukan 20 bps asumsi), tetap
   positif setelah fold terbaik dibuang, lolos BH α 0,10 (§D/§E). Bentuk bersegmen + drop-best
   sudah ada di `tools/backtest.py` untuk aturan arah; jalur struktur belum ditulis.

## Batas dan mode gagal

- **Tertinggal `N` bar, dan itu bukan detail.** Sebuah ChoCH tidak bisa diketahui pada bar yang
  sama dengan ayunan yang mematahkannya. Klaim "sangat jelas untuk tentukan arah" benar secara
  visual dan salah secara waktu: kejelasannya datang setelah fakta.
- **`N` menentukan rezim, bukan cuma detail.** `N` kecil = struktur berisik (puluhan break per hari,
  semua membayar ongkos); `N` besar = hampir tidak ada sampel. Keduanya sah; yang tidak sah adalah
  memilih `N` setelah melihat hasil ([[QT4 - Overfitting dan Validasi]]).
- **Wick vs close mengubah populasi peristiwa** secara besar di aset tipis: satu sumbu 400 bps
  mematahkan struktur tanpa mengubah penutupan apa pun ([[FD8 - Volatilitas]]).
- **Aset yang diuji ≠ aset yang diklaim.** Cerita struktur lahir di memecoin BSC berumur beberapa
  jam; yang bisa kami hargai sendiri 608 kontrak perp (§A). Membuktikan S3 pada BNB lalu menjualnya
  sebagai ilmu meme = klaim melebihi yang diukur.
- **Tidak ada pembanding "tanpa struktur" yang jujur.** Semua aturan pada deret yang sama membaca
  `h,l,c`; ChoCH hampir pasti berkorelasi dengan momentum sederhana — dan momentum sederhana itu
  **sudah kami uji dan rugi di 12/12** ([[Fakta Terukur]] §F, lihat [[I1 - Moving Average]]).
- **Efficient-regime gate tetap di depan.** Pada |acf| < 0,05 arah apa pun ditolak
  `tools/direction.py` sebelum struktur bicara; terukur MARSCOIN 0,075 = zona abu-abu (§F).

## Tingkat bukti

`T1` untuk primitifnya (definisi ayunan dipakai luas, tidak dibakukan siapa pun) · `T0` untuk klaim
prediktif ChoCH/BOS dan narasi "smart money memindahkan harga" · **belum diuji oleh Fabius**.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "struktur dapat dihitung tanpa asumsi tentang siapa yang berdagang; itu menjadikannya
  kandidat uji terbaik di keluarga SMC. Belum kami uji."
- **Dilarang:** "ChoCH memberi arah sebelum harga bergerak" · "Fabius memakai market structure" ·
  "SMC membaca niat institusi".

**Terkait:** [[S4 - Order Block dan Breaker]] · [[S5 - Fair Value Gap]] ·
[[S6 - Likuiditas Stop Hunt dan Inducement]] · [[S2 - Chart Patterns]] · [[I1 - Moving Average]] ·
[[FD9 - Horizon Waktu dan Multi-Timeframe]]
