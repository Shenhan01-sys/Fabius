---
tags: [tk, tk-sinyal, "S1"]
---

# S1 - Candlestick dan Price Action Murni

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"paling OP untuk berbagai situasi" — klaim komunitas
("Price Action Murni … tidak bergantung indikator, sangat fleksibel di segala situasi"); istilah
*entanglement* tidak ada di `Plan.txt` → pengetahuan standar pasar, tanpa rujukan di repo ini

**Ringkas:** Satu bar cuma empat angka (`o,h,l,c`) plus volum; seluruh keluarga candlestick menamai
hubungan di antara empat angka itu. Namanya berguna sebagai bahasa, dan tidak berguna sebagai bukti.
Masalahnya bukan "pola itu tidak ada" — pola itu deterministik dan bisa dihitung — melainkan bahwa
setiap pola jenis ini juga menyala pada jalan acak, jadi klaimnya hanya berarti kalau basis rate-nya
disebut. Catatan ini menuliskan ambang yang membuat "engulfing" jadi sebuah peristiwa, bukan selera,
dan apa yang tetap tidak bisa diberikan lilin: urutan kejadian di dalam bar.

## Definisi yang bisa dihitung

```
bullish(i) : c[i] > o[i]                    body(i) : |c[i]-o[i]|
range(i)   : h[i]-l[i]                      upper(i): h[i] - max(o[i],c[i])
lower(i)   : min(o[i],c[i]) - l[i]
hammer(i)  : lower >= 2*body dan upper <= 0,1*range      # varian komunitas: 2/3 sumbu bawah
engulf(i)  : bullish(i) dan bearish(i-1) dan c[i] > o[i-1] dan o[i] < c[i-1]
             # TANPA klausul ukuran ini terpenuhi oleh noise -> wajib: body[i] >= k * ATR(t)
             # dan: range[i] >= m * median(range, t-n..t-1)
entangle(i): ada N bar berturut-turut dengan overlap >= 0,5 * median(range)
             # = keadaan "tidak ada arah"; klaimnya ia mendahului ledakan, itu yang harus diuji
```

Empat hal wajib ditetapkan **sebelum** pola boleh disebut teruji: (1) interval (engulfing di 1 j dan
di 4 j adalah dua peristiwa berbeda di tanggal yang sama), (2) ambang ukuran (`k`, `m` di atas),
(3) varian definisi yang dipakai (`hammer` punya tiga, `doji` punya dua), (4) durasi hasil — kapan
reaksi dianggap sah, 1 bar atau 24 bar. Tanpa keempatnya, "engulfing" tidak bisa dibuktikan salah.

## Cara pakai yang diklaim

Reversal: hammer/shooting star di ujung ayunan, engulfing sebagai "konfirmasi masuk", doji sebagai
"pasaran ragu". Continuation: three methods, rising/falling three. Entry pada penutupan bar pola;
stop di ekstrem bar pola; target di "likuiditas berikutnya" ([[S6 - Likuiditas Stop Hunt dan Inducement]]).
Klaim komunitas di `Plan.txt` (daftar 20 metode) menyebut keluarga ini fleksibel di semua rezim —
itu pemilik klaimnya praktisi, bukan hasil ukur, dan tidak ada angka yang menyertainya.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| OHLC 1 jam ≥ 2.400 bar | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari — hanya aset **ber-kontrak perp** ([[Fakta Terukur]] §A) |
| volum per bar | `ADA` | `tools/bars.py` menyimpan `v` (base) dan `n` (jumlah trade) per bar |
| pemisahan pembeli/penjual dalam bar | `TIDAK-ADA` | `takerBase`/`takerQuote` dibuang `tools/bars.py` → "penolakan" tak bisa diatribusikan |
| urutan kejadian **dalam** bar (path) | `TIDAK-ADA` | butuh tick; tidak ada jalur L2/tick di repo ([[Fakta Terukur]] §C) |
| penghitung pola | `TIDAK-ADA` | tidak ada satu pun alat Fabius yang mendeteksi pola lilin |
| ATR untuk ambang ukuran | `ADA-TAPI` | `tools/direction.py` menghitung rata-rata 24 TR terakhir (bukan Wilder) |

## Uji di Fabius

Bentuk uji yang sah, dan satu-satunya yang membuat bagian ini berarti:

1. Detektor hanya membaca bar `<= t` (point-in-time, [[Concepts/Point-in-Time vs Retro-updatable]]).
2. Laporkan **tiga** angka, bukan satu: base rate pola, `P(naik | pola)`, dan `P(naik)` tanpa syarat.
   Selisih dua yang terakhir adalah seluruh isinya.
3. Pembanding: pemicu acak dengan **jumlah pemicu sama** pada simbol dan jam yang sama
   (kontrol yang sama dengan yang dipakai untuk ⑦ — [[Fakta Terukur]] §B).
4. `n >= 20` non-overlap, gross vs ongkos **59 bps** terukur (§D) — bukan 20 bps asumsi;
   `MIN_BARS_TINY=720` menyaring kandidat berumur pendek sebelum uji apa pun (§A/§E).

Runner yang sudah ada (`tools/backtest.py`) hanya mengeksekusi aturan arah SMA/ret24; jalur pola
lilin **belum ditulis**. Jangan menulis perintah `--pattern …` seolah ada: flag itu tidak ada.

## Batas dan mode gagal

- **Interval-dependence.** "Pola muncul" bukan kalimat lengkap sebelum intervalnya disebut, dan ia
  menentukan berapa banyak peristiwa yang kamu punya.
- **Basis rate adalah null-nya.** Di deret acak setiap pertidaksamaan pada `(o,h,l,c)` menyala dengan
  laju positif. "70 % engulfing disusul higher high" tanpa menyebut `P(higher high)` = nol informasi.
- **Sumbu tidak menceritakan penolakan.** Wick panjang bisa berarti tiga hal berbeda tergantung
  urutan sentuhan — dan urutan itu hilang permanen di data kline kami.
- **Multiplicity.** 12 nama pola × 3 horizon × 12 simbol = ratusan tembakan; tanpa BH α 0,10
  ([[EV3 - Signifikansi dan Multiple Testing]]) selalu ada sesuatu yang "terbukti".
- **Ongkos menghapus sisanya.** Kalau pun ekspektasi kondisional +5 bps, 59 bps round-trip membuat
  net-nya negatif — aritmetika dari [[Fakta Terukur]] §D, bukan opini.
- **Rezim.** Pola reversi paling sering "benar" di rentang sempit dan paling sering salah di tren
  kuat; tanpa klasifikasi rezim ([[FD1 - Struktur Pasar dan Rezim]]) hasilnya campuran yang tak
  bisa diinterpretasi.
- **Duplikasi.** Pola dua-bar adalah ringkasan satu peristiwa yang diukur [[S3 - Market Structure BOS dan ChoCH]]
  pada rentang yang lebih panjang; dan satu baris lilin tidak menambahkan apa pun yang tidak ada di
  `h,l` — volum adalah saudaranya, bukan saksi ([[V1 - Konfirmasi Volum dan Money Flow]]).
- **Survivorship kanon.** Buku pola berisi pola yang terlihat pada chart yang diingat orang.

## Tingkat bukti

`T1` untuk geometri dan penamaannya (dipakai luas, definisinya tidak dibakukan siapa pun) · `T0`
untuk klaim "fleksibel di segala situasi" (tanpa pemilik, tanpa angka) · **belum diuji oleh Fabius**:
tidak ada jalur kodenya.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "setiap pola lilin bisa dihitung deterministik, dan karena itu bisa diuji terhadap null
  acak pada deret kami; belum pernah kami uji."
- **Dilarang:** "engulfing memprediksi arah" (tanpa interval, ambang, base rate) · "Fabius membaca
  price action" · "sangat fleksibel di segala situasi" sebagai kalimat kami.

**Terkait:** [[S2 - Chart Patterns]] · [[S3 - Market Structure BOS dan ChoCH]] ·
[[S5 - Fair Value Gap]] · [[S4 - Order Block dan Breaker]] · [[FD8 - Volatilitas]] ·
[[V1 - Konfirmasi Volum dan Money Flow]] · [[GAP4 - Yang Tidak Bisa Diuji Karena Data]] ·
[[Fakta Terukur]]
