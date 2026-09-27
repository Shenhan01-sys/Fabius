---
tags: [tk, tk-sinyal, "S6"]
---

# S6 - Likuiditas, Stop Hunt dan Inducement

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** keputusan ([[PL4 - Memutuskan]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"paling OP untuk berbagai situasi": "Liquidity Grab /
Stop Hunt Awareness … Sangat OP di crypto karena market sering dimanipulasi" (klaim komunitas)

**Ringkas:** Bagian paling benar dari keluarga ini adalah bagian paling membosankan: stop orang
mengumpul di tempat yang sama, karena orang memakai aturan yang sama. Bagian yang tidak bisa
dipertahankan adalah kata "hunt": bahwa ada pihak yang **mengetahui** letak stop itu dan
**memutuskan** mengambilnya. Klaim pertama bisa dihitung; klaim kedua butuh data yang tidak kami
punya, dan setelah kejadian ia menjelaskan apa saja — termasuk kebalikannya. Memisahkan keduanya
adalah gunanya: tempat memasang stop datang dari klaim yang pertama.

## Definisi yang bisa dihitung

```
kumpulan stop di atas  : setiap swing_high yang belum patah -> stop short massal di h + epsilon
kumpulan stop di bawah : cerminnya (stop long)
level konvensi         : round number (multiple 10^k dari harga), high/low hari kemarin,
                         high/low sesi, open harian, low/high minggu   # semua dari deret kami
sweep(t, b)            : high[t] > level + b * ATR  DAN  close[t] < level   # "ambil lalu balik"
raid_only(t)           : high[t] > level + b * ATR  TANPA syarat close     # cuma tembus biasa
inducement             : swing_minor yang terbentuk setelah sweep dan patah dalam <= m bar
```

`epsilon` dan `b` wajib disebut. Tanpa keduanya, "likuiditas diambil" berarti "harga menyentuh sebuah
level", dan itu terjadi terus-menerus di aset ber-volatilitas tinggi. *Inducement* bahkan tidak punya
definisi yang sama antar-penjualnya; baris di atas adalah versi catatan ini, bukan versi kanon.

## Cara pakai yang diklaim

Tunggu harga menembus kumpulan stop lalu kembali (sweep), masuk searah balikannya, stop di luar
sumbu; target = kumpulan stop di sisi sebaliknya. Klaimnya di crypto "sangat OP karena market sering
dimanipulasi" (`Plan.txt`). Yang memilikinya: praktisi dan vendor alat likuiditas; **bukan** hasil
ukur publik yang bisa kami periksa. Konsekuensi praktis yang **boleh** diambil tanpa percaya
ceritanya: jangan menaruh stop persis di tempat aturanmu menaruhnya, karena aturan itu sama dengan
aturan orang lain ([[FD7 - Invalidation Stop dan Time-Stop]]).

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| level konvensi (round number, high/low kemarin) | `ADA-TAPI` | dihitung dari deret yang ada; **belum** ada alat yang menghitungnya |
| OHLC 1 jam ≥ 2.400 bar untuk peristiwa | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari; hanya aset ber-perp ([[Fakta Terukur]] §A) |
| order book L2 (tempat stop & likuiditas tinggal) | `TIDAK-ADA` | tidak ada jalur di repo ini ([[Fakta Terukur]] §C) |
| feed likuidasi / heatmap likuidasi historis | `TIDAK-ADA` | tidak ada sumbernya; lihat [[U3 - Level Likuidasi dan Cascade]] |
| Open Interest & funding untuk menduga posisi | `ADA-TAPI` | **snapshot saat ini saja**, tidak bisa ditarik mundur (§A/§C) → tidak ada uji masa lalu |
| aliran dompet sebagai saksi "siapa yang menjual" | `ADA-TAPI` | BSC spot, jendela lihat 8–13 menit, tanpa riwayat, dan **bukan** token perp yang sama (§B) |

Kesimpulan statusnya jujur dan keras: **mekanismenya tidak teramati oleh kami sama sekali.** Yang
tersisa hanyalah bentuk harga, dan bentuk harga dimiliki semua hipotesis yang saling bertentangan.

## Uji di Fabius

Uji yang mungkin dijalankan (belum ada satu pun yang dijalankan — perintahnya belum ditulis):

1. Bangun himpunan level **hanya dari bar `<= t`** dan bekukan; jumlah level per hari wajib
   dilaporkan, karena ia adalah ukuran berapa banyak tembakan acak yang kamu punya.
2. Null-nya bukan "tidak ada pemburu", melainkan **ekor dari deret yang sama**: seberapa sering
   `high > level + b·ATR` terjadi tanpa asumsi tentang maksud. Bandingkan `sweep` vs `raid_only` vs
   level acak dengan jumlah pemicu sama (pola yang sama dengan [[S5 - Fair Value Gap]] dan
   [[S7 - Fibonacci Retracement dan Extension]]).
3. Hasil = return bersih pada horizon 4 j/24 j setelah sweep, dua jalur keluar (horizon tetap dan
   kena stop), ongkos **59 bps** terukur (§D).
4. Ambang lolos: `n >= 20` non-overlap, BH α 0,10, tetap positif setelah fold terbaik dibuang
   (§E, F-D16). Gerbang |acf| `tools/direction.py` tetap berdiri di depan: pada deret yang mendekati
   jalan acak, "pemburuan" dan "kebetulan" secara statistik tidak terbedakan — dan itu bukan
   metafora, itu hasil uji kami ([[Fakta Terukur]] §F).

## Batas dan mode gagal

- **Tidak falsifiable setelah kejadian** — penyakit utamanya. Harga menembus level lalu berbalik =
  "stop hunt"; menembus lalu lanjut = "breakout sejati"; tidak menembus = "likuiditasnya masih
  mengintai". Tiga kalimat yang menjelaskan tiga hasil berbeda tidak memprediksi apa pun
  ([[EV5 - Reproduksibilitas dan Pra-Registrasi]] adalah obatnya, dan ia harus diminum sebelum hasil).
- **Inti yang benar dibungkus narasi yang salah.** Perataan stop di level konvensi itu nyata
  sebagai konsekuensi aturan bersama; tidak perlu ada dalang untuk membuatnya terjadi.
- **Korelasi dengan S3/S4/S5.** Satu sumbu yang sama bisa disebut sweep, ChoCH gagal, zona yang
  ditembus, dan gap yang terisi. Empat nama, satu peristiwa, satu sampel
  ([[FD11 - Aturan Mengalahkan Intuisi]]).
- **Arah risiknya asimetris dan terbalik dari klaimnya.** Yang terjadi pada kita di posisi yang
  sama: **kita** yang jadi likuiditasnya. Stop adalah order pasar di saat order book paling tipis
  ([[FD3 - Likuiditas dan Dampak Harga]], [[V5 - Mikrostruktur Spread dan Adverse Selection]]).
- **Venue yang salah.** Cerita ini lahir dari perp dan likuidasi; data dompet kami adalah spot BSC
  dengan jendela 8–13 menit yang tidak bisa ditarik mundur (§B) — tidak ada jalur untuk menguji
  motif di peristiwa yang lewat.

## Tingkat bukti

`T1` untuk "stop mengumpul di level konvensi" (inferensi wajar dari aturan bersama; tidak kami amati)
· `T0` untuk klaim niat "ada pihak yang memburu stop" dan untuk *inducement* · untuk Fabius: **belum
diuji**, dan mekanisme penjelasnya **tidak bisa diuji** dengan data yang ada
([[GAP4 - Yang Tidak Bisa Diuji Karena Data]]).

## Boleh dibaca, dilarang dibaca

- **Boleh:** "level konvensi adalah tempat stop orang berkumpul karena aturan yang sama; hindari
  menaruh invalidasi persis di sana, dan jangan jual cerita pemburuan sebagai sesuatu yang kami ukur."
- **Dilarang:** "Fabius mendeteksi stop hunt" · "likuiditas diambil sebelum bergerak ke target" ·
  "market crypto dimanipulasi di level-level itu" sebagai kalimat kami.

**Terkait:** [[S3 - Market Structure BOS dan ChoCH]] · [[S5 - Fair Value Gap]] ·
[[S4 - Order Block dan Breaker]] · [[U3 - Level Likuidasi dan Cascade]] ·
[[V4 - Order Book dan Liquidity Heatmap]] · [[FD7 - Invalidation Stop dan Time-Stop]] ·
[[Fakta Terukur]]
