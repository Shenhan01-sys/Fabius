---
tags: [tk, tk-sinyal, "I2"]
---

# I2 - RSI dan Divergence

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"metode trading itu ada apa aja sih?" (RSI) dan
§"paling OP untuk berbagai situasi" ("RSI + Divergence … bagus untuk overbought/oversold dan potensi
reversal") — klaim komunitas, tanpa pemilik hasil ukur

**Ringkas:** RSI mengubah deret penutupan menjadi satu angka 0–100: berapa besar rata-rata kenaikan
dibanding rata-rata penurunan dalam `n` bar. Ia bounded, jadi mudah dibaca lintas aset — dan justru
karena ia bounded, ia **tidak bisa** membedakan "sudah turun jauh" dari "akan berhenti turun".
Divergensi, bagian yang membuat keluarga ini terdengar dalam, adalah klaim tentang dua puncak di
dua deret berbeda — dan ia tidak bisa diuji sama sekali sebelum puncak didefinisikan. Belum ada satu
pun alat Fabius yang menghitung RSI.

## Definisi yang bisa dihitung

```
r[i]     : c[i] - c[i-1] ;  up = max(r,0) ; dn = max(-r,0)
avgUp,avgDn : rata-rata Wilder (RMA): x[t] = x[t-1] + (v[t] - x[t-1])/n     # BUKAN rata-rata biasa
RS       : avgUp / avgDn                    RSI = 100 - 100/(1 + RS)
garis    : RSI > 70 = "overbought" ; RSI < 30 = "oversold"    # ambang konvensi, bukan konstanta
pivot(i) : RSI[i] = max(RSI[i-N .. i+N])                     # divergensi TANPA ini tidak terdefinisi
div_bull : c[i] > c[j] DAN RSI[i] < RSI[j]  untuk dua pivot-up i, j dengan jarak <= m bar
```

Tiga hal yang harus disebut sebelum "divergensi" jadi peristiwa: `n` (periode), **pivot rule**
(`N` dan konfirmasi `+N` bar ke depan), dan **pasangan pivot mana** yang dibandingkan. Tanpa ketiganya
kalimat itu tidak bisa dibuktikan salah. Catatan: RSI dengan RMA Wilder dan RSI dengan SMA biasa
berbeda nilainya secara sistematis pada deret pendek — bukan gaya, tapi dua indikator berbeda.

## Cara pakai yang diklaim

Beli saat RSI keluar dari bawah 30, jual saat keluar dari atas 70; gunakan divergensi sebagai
"pelemahan tren"; kombinasikan dengan struktur sebagai filter searah. Klaim di `Plan.txt` menyebutnya
filter — dan sebagai filter (menolak melawan momentum ekstrem) ia masih masuk akal; sebagai pemicu
reversal ia berada di level `T0`.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| penutupan 1 jam | `ADA` | `tools/bars.py`; kedalaman 9.599 bar untuk aset ber-perp (§A) |
| penghitung RSI | `TIDAK-ADA` | tidak ada satu pun alat Fabius yang menghitung RSI/Wilder RMA |
| penentu pivot untuk divergensi | `TIDAK-ADA` | tidak ada deteksi ayunan sama sekali ([[S3 - Market Structure BOS dan ChoCH]]) |
| RSI lintas aset non-perp (memecoin C2/D) | `TIDAK-ADA` | `MIN_BARS_TINY=720` + deret mentok 1.000 bar / 0 bar token gas (§A) |
| ambang 70/30 yang terkalibrasi per aset | `TIDAK-ADA` | belum diukur per aset, termasuk distribusi RSI kami sendiri *(belum diukur)* |

### Mengapa RSI diam lama di oversold saat harga jatuh tajam

Mekanisme murni aritmetika, dan ini bagian yang paling sering salah dipahami: saat penurunan
berlanjut, `avgUp` menyusut mendekati nol sementara `avgDn` tetap besar, jadi `RS → 0` dan
`RSI → 0`. RSI yang menempel di 20 selama tiga hari **bukan** sinyal "jenuh dan akan berbalik"; itu
deskripsi bahwa tidak ada kenaikan yang berarti dalam rentang itu — dan RMA Wilder menahan nilai lama
karena bobot eksponensialnya. Pada aset yang kami tolak pun arahnya sama: di deret yang mendekati
jalan acak (|acf| < 0,05, gerbang `tools/direction.py`) tidak ada "pelemahan" untuk dideteksi, dan
terukur MARSCOIN berada di zona abu-abu 0,075 (§F). Konsekuensi praktis: **jual karena RSI > 70**
di objek yang sedang naik tajam adalah cara membayar ongkos dua kali.

## Uji di Fabius

Semua bagian dari bentuk uji ini sudah ada jalurnya kecuali detektornya:

1. Tetapkan `(n, N, m, ambang)` dan tulis sebelum hasil dilihat ([[EV5 - Reproduksibilitas dan Pra-Registrasi]]).
2. Event = silang ambang **dan** divergensi, dua-duanya dilaporkan terpisah; hasil = return bersih
   horizon 4 j/24 j (`tools/backtest.py --horizon`), plus jalur kena stop.
3. Null: (a) arah acak pada simbol & jam yang sama; (b) untuk divergensi — **pivot acak dengan jumlah
   sama**, karena klaim divergensi adalah klaim tentang pasangan puncak, bukan tentang harga.
4. Laporkan distribusi RSI per aset lebih dulu: di aset yang sedang turun berkepanjangan, "oversold"
   mungkin status default, bukan peristiwa langka. Angka itu *(belum diukur)* dan ia gratis.
5. Gerbang tidak berubah: `n >= 20` non-overlap, gross di atas **59 bps** terukur (§D), fold terbaik
   dibuang, BH α 0,10 (§E). Jalur kode RSI belum ditulis.

## Batas dan mode gagal

- **Tertinggal dua kali.** RSI adalah fungsi dari penutupan yang sudah lewat; divergensi butuh pivot
  yang baru sah `N` bar kemudian. Total keterlambatan jarang disebut oleh siapa pun yang menjualnya.
- **Ambang 70/30 tidak lintas-rezim.** Di tren kuat RSI > 70 bertahan berminggu-minggu; di rentang
  sempit RSI tidak pernah menyentuh keduanya. Satu angka untuk semua aset salah secara konstruksi,
  apalagi untuk aset yang harganya berbeda enam orden (lihat [[I6 - ATR dan Jarak Ternormalisasi]]).
- **Divergensi tidak falsifiable setelah kejadian**: tidak terbentuk = "belum ada divergensi
  sejati"; gagal = "divergensi batal". Dua-duanya menjelaskan apa pun
  ([[EV2 - Jebakan Backtest]]).
- **Bounded ≠ probabilitas.** RSI 80 bukan "80 % peluang turun"; ia tidak punya tafsir frekuentis
  sampai seseorang mengukur `P(turun | RSI = 80)` pada data kami.
- **Turunan dari deret yang sama.** RSI, `ret24`, momentum SMA: semuanya `(o,h,l,c)` — menggabungkan
  ketiganya bukan tiga konfirmasi ([[I3 - MACD]], [[I1 - Moving Average]]).
- **Ongkos.** Oscillator menghasilkan lebih banyak pergantian posisi daripada aturan tren; pada 59
  bps per putaran, frekuensi adalah kerugian itu sendiri (§D, [[FD4 - Ongkos Perdagangan]]).

## Tingkat bukti

`T1` untuk RSI sebagai ringkasan momentum ternormalisasi (dipakai luas, perhitungannya baku) · `T0`
untuk divergensi sebagai prediksi pembalikan (definisinya tidak pernah dibakukan, klaimnya tidak
pernah bisa disalahkan) · untuk Fabius: **belum diuji**, tidak ada jalurnya di `tools/`.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "RSI adalah momentum yang dipetakan ke 0–100; ia murah dihitung dan bisa diuji terhadap
  null pivot acak; divergensi belum bisa diuji apa pun sebelum pivotnya dibakukan."
- **Dilarang:** "RSI oversold = beli" · "divergensi menunjukkan tren melemah" · "Fabius menyaring
  dengan RSI" · ambang 70/30 sebagai angka keramat alih-alih sebagai default Wilder.

**Terkait:** [[I3 - MACD]] · [[I1 - Moving Average]] · [[I4 - Bollinger Bands]] ·
[[S3 - Market Structure BOS dan ChoCH]] · [[V1 - Konfirmasi Volum dan Money Flow]] ·
[[EV6 - Kalibrasi Ambang Terhadap Hasil]] · [[Fakta Terukur]]
