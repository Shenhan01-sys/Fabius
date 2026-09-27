---
tags: [tk, tk-sinyal, "I7"]
---

# I7 - VWAP dan Anchored VWAP

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"Coba eksplor lagi" ("Volume Weighted Average Price
(VWAP) + Anchored VWAP") — klaim komunitas, tanpa pemilik hasil ukur

**Ringkas:** VWAP menjawab satu pertanyaan legit yang jarang diucapkan dengan benar: *rata-rata di
harga berapa uang benar-benar dibayar di jendela ini?* Itu benchmark **eksekusi**, bukan ramalan
arah. Anchored VWAP menambahkan satu kata yang berbahaya: "anchor". Anchor yang sah adalah waktu yang
sudah kamu ketahui sebelum hasilnya ada (buka hari, bar pertama aset, jam snapshot kami). Anchor yang
dipilih setelah chart terbentuk adalah [[S7 - Fibonacci Retracement dan Extension]] dengan kostum
baru: satu derajat kebebasan lagi, dan klaim yang tidak bisa disalahkan.

## Definisi yang bisa dihitung

```
VWAP(t0..t)   : sum(P[i] * V[i]) / sum(V[i])          # P = harga transaksi sungguhan; tanpa tick,
P[i]          : (h[i] + l[i] + c[i]) / 3               #   proxy = typical price (disebut, bukan disembunyikan)
anchor        : t0 WAJIB ditetapkan sebelum hasil; kandidat sah:
                - buka hari UTC (dari `t` bar, `tools/bars.py` menyimpan openTime ms)
                - bar pertama aset yang kita lihat (listing) -> untuk pool berumur 30 bar: whole life
                - timestamp keputusan/snapshot kita sendiri (sudah diketahui ex ante)
deviasi       : (close - VWAP) / ATR_pct              # ternormalisasi -> [[I6 - ATR dan Jarak Ternormalisasi]]
"di atas VWAP": harga di atas rata-rata tertimbang volume sejak anchor, tanpa klaim apa pun
```

Yang **bukan** VWAP, walau sering disamakan: volume profile ([[V2 - Volume Profile dan POC]]) —
VWAP adalah satu angka dari rata-rata waktu, profile adalah distribusi volum per level harga (POC =
modusnya). Pertanyaannya berbeda: "di harga berapa rata-rata dibayar" vs "di harga berapa paling
banyak diperdagangkan".

## Cara pakai yang diklaim

Trader: beli saat harga kembali ke VWAP sesi dari sisi bawah, jual saat menjauh; "institutional
average cost" sebagai support dinamis; AVWAP dari peristiwa (listing, puncak, peluncuran) sebagai
garis yang "dihormati". Institusi: VWAP sebagai **target eksekusi** — membeli di bawah VWAP periode
itu prestasi, bukan prediksi. Dua penggunaan terakhir ini sah dan tidak bertentangan; penggunaan
pertama (VWAP sebagai magnet) adalah klaim prediktif yang tidak punya bukti di pihak kami.

### Yang benar-benar bisa dilakukan Fabius hari ini

Benchmark, bukan sinyal. Kami punya tiga putaran nyata di chain 97 dengan net rata-rata **−59,0 bps**
dan volum pool kami sendiri tanpa arus luar ([[Fakta Terukur]] §F): untuk kasus itu VWAP adalah
tautologi, tidak ada pihak lain yang membayar harga rata-rata apa pun. Gunanya baru muncul kalau ada
eksekusi di venue dengan arus pasar — dan itu **belum ada** *(belum diukur)*.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| volum per bar untuk tertimbang | `ADA` | `tools/bars.py` menyimpan `v` (base) per bar; cache per (simbol, interval) |
| harga transaksi sungguhan (tick) | `TIDAK-ADA` | tanpa tick, `P[i]` hanya proxy typical price |
| volum taker beli/jual | `TIDAK-ADA` | `quoteVol`, `takerBase`, `takerQuote` **dibuang** oleh `tools/bars.py` padahal server mengirimnya |
| keaslian volum (wash vs nyata) | `TIDAK-ADA` | tidak ada jalur verifikasi; di venue tipis volum bukan bukti ([[O6 - Konsentrasi Holder Bundler dan LP Lock]]) |
| alat penghitung VWAP | `TIDAK-ADA` | tidak ada satu pun alat Fabius yang menghitung VWAP |

## Uji di Fabius

Dua hal terpisah, dan yang pertama nyaris gratis:

1. **Deskriptif:** untuk setiap aset di cache, bandingkan penutupan terakhir dengan VWAP seumur
   jendela (30 / 240 / 9.599 bar) dan dengan median. Ini menguji klaim "VWAP = harga rata-rata
   terberat" sebelum dipakai sebagai apa pun; distribusinya belum pernah kami ringkas
   *(belum diukur)*.
2. **Sebagai null untuk kualitas eksekusi**, bukan untuk arah: untuk setiap `Enter` yang jatuh
   tempo, laporkan selisih fill terhadap VWAP jendela yang sama — anchor ditetapkan **sebelum**
   hasil, ikut masuk yang di-hash (`tools/ledger.py` membaca dari rekaman, bukan ingatan).
   Ambang yang berlaku tidak berubah: net > 0 setelah ongkos **59 bps** terukur, `n >= 20`
   non-overlap, BH α 0,10, fold terbaik dibuang (§D/§E, F-D16).
3. **Kalau** mau menguji "harga kembali ke VWAP": null-nya pita rata-rata bergerak dengan jumlah
   sentuhan sama (bentuk uji yang sama dengan [[I4 - Bollinger Bands]] dan
   [[S7 - Fibonacci Retracement dan Extension]]) — VWAP akan "dipantul" oleh deret yang sama yang
   memantulkan semua rata-rata.

## Batas dan mode gagal

- **Anchor-shopping = pemilihan ayunan yang menyamar.** Anchor bisa digeser ke setiap puncak,
  lembah, listing, atau berita; dengan puluhan kandidat, selalu ada satu yang "cocok"
  ([[QT4 - Overfitting dan Validasi]]).
- **Di aset berumur 30 bar, VWAP ≈ mean yang didominasi bar peluncuran.** Volum terbesar sebuah
  pool biasanya ada di jam-jam pertama, jadi rata-rata tertimbang itu lebih dekat ke "harga saat
  orang pertama masuk" daripada ke biaya rata-rata peserta sekarang.
- **Volum bukan bukti niat.** Tanpa pemisahan taker dan tanpa verifikasi keaslian, "harga di atas
  VWAP institusi" bisa berarti apa pun (§C).
- **Benchmark ≠ edge.** Membeli di bawah VWAP sesi tidak membuatmu benar; itu membuatmu murah relatif
  terhadap rata-rata periode itu — dan periode itu adalah pilihanmu sendiri.
- **Duplikasi dengan I1 dan I4.** VWAP adalah rata-rata berbobot: deret yang sama, tidak ada informasi baru di luar `(o,h,l,c,v)` ([[I1 - Moving Average]]).
- **Ongkos mendahului semuanya.** Selisih tipikal antara harga dan VWAP-nya pada horizon jam-an
  jarang melebihi 59 bps (§D); klaim "beli di VWAP" harus menjelaskan dari mana margin itu datang.

## Tingkat bukti

`T1` untuk VWAP sebagai benchmark eksekusi (baku di praktik buy-side; tidak teruji oleh kami karena
putaran nyata kami terjadi di pool tanpa arus luar) · `T0` untuk "AVWAP = level yang dihormati
institusi" · untuk Fabius: **belum diuji**; alatnya belum ada.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "VWAP adalah yardstick ongkos yang jujur asalkan anchornya ditetapkan sebelum hasil; ia
  tidak memberi arah dan belum kami hitung di data kami."
- **Dilarang:** "harga akan kembali ke VWAP" · "di atas VWAP = institusi sedang menahan" · "Fabius
  memakai anchored VWAP" · memakai AVWAP dengan anchor yang dipilih setelah chart terbentuk.

**Terkait:** [[V2 - Volume Profile dan POC]] · [[V1 - Konfirmasi Volum dan Money Flow]] ·
[[I1 - Moving Average]] · [[I4 - Bollinger Bands]] · [[I6 - ATR dan Jarak Ternormalisasi]] · [[Fakta Terukur]]
