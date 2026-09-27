---
tags: [tk, tk-sinyal, "V2"]
---

# V2 - Volume Profile dan POC

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"3. CONFIRMATION LAYER (Lapisan Konfirmasi)"
(Volume Profile, POC, VAH/VAL, HVN/LVN) — klaim komunitas, termasuk "sangat akurat untuk
support/resistance dinamis" di §"20 Metode Paling Representatif & OP"

**Ringkas:** Volume profile adalah histogram volum **menurut harga**, bukan menurut waktu: di harga
berapa paling banyak transaksi terjadi (POC), di mana 70 % volum menumpuk (value area), dan mana
buku yang tipis (LVN). Janjinya: level tempat banyak orang berganti tangan = level yang punya
memori. Catatan ini menahan satu hal: profil yang dibangun dari bar OHLCV adalah **aproksimasi
yang distribute volume secara diandaikan**, dan menyebutnya "volume profile" tanpa data tick adalah
klaim yang lebih besar dari yang dihitung.

## Definisi yang bisa dihitung

```
# versi tick (yang asli): setiap print (p_i, v_i) -> bucket b(p_i)  ; V_b = sum v_i
# versi bar OHLCV (yang BISA kami buat): volum satu bar harus disebar ke bucket
#   dalam [low, high] dengan bobot W(p) yang MERUPAKAN ANDAAN, bukan data.
bobot merata    : W(p) = 1/(high-low)                untuk p di [low, high]
bobot OHLC      : puncak segitiga di close (high/low dapat bagian lebih kecil)
POC  = argmax_b V_b
VAL/VAH = batas bawah/atas interval terkecil yang memuat 70 % sum(V_b), di sekitar POC
HVN/LVN = bucket di atas/di bawah median V_b (definisi komunitas ambigu; bakukan satu)
```

Tiga hal yang harus ditulis sebelum profil apa pun dipakai: lebar bucket, aturan sebar, dan
jendela waktu. Mengubah salah satunya mengubah POC — dan itu tiga parameter gratis per grafik.

## Cara pakai yang diklaim

Harga ditarik ke POC (magnet), memantul di VAH/VAL, menembus cepat lewat LVN ("rechurn" di HVN,
"rejection" di LVN); dipakai di setup range ([[ST4 - Range dan Mean Reversion]]) dan sebagai
support/resistance dinamis. Klaimnya datang dari praktisi dan dari platform yang menjual datanya
(Profil/heatmap dari vendor), bukan dari studi yang bisa kami periksa di repo ini.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| bar OHLCV 1 jam untuk membangun profil **aproksimasi** | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari (§A) — hanya untuk aset **ber-kontrak perp**; Hyperliquid 5.001 bar sebagai pembanding |
| print per harga (tick) — syarat menyebutnya profil asli | `TIDAK-ADA` | tidak ada jalur tick di repo ini ([[Fakta Terukur]] §C) |
| volum rupiah per bucket harga untuk spot/memecoin | `TIDAK-ADA` | `GMGN token_kline` mentok 1.000 bar ≈ 41,6 hari; pool baru ±30 bar (§A) — terlalu pendek untuk profil yang mau dijual |
| jumlah transaksi per bar (bobot alternatif) | `ADA-TAPI` | kolom `n` di-cache `tools/bars.py`, tidak dibaca alat mana pun |
| kode pembentuk profil | `TIDAK-ADA` | tidak ada satu pun fungsi histogram harga di `tools/` |

## Uji di Fabius

Uji yang sah = event study, bukan estetika: untuk tiap bar, hitung jarak ke POC jendela
**<= t** (point-in-time, [[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]), lalu
bandingkan return bersih 4 jam setelah "sentuhan POC" dengan **arah acak pada token dan jam yang
sama** (kontrol yang benar menurut [[Fakta Terukur]] §B). Lolos: `n >= 20` non-overlap, gross di
atas **59 bps** (§D), tetap positif setelah fold terbaik dibuang, lolos BH α 0,10.
Perintah yang dibutuhkan: `tools/vp_study.py` — **belum ditulis**; `tools/backtest.py` belum
mengenal kolom volum sama sekali, jadi jangan menuliskannya sebagai jalur yang ada.

## Batas dan mode gagal

- **Profil dari bar bukan profil dari transaksi.** Kalau sebuah bar 1 jam bergerak `low → high →
  close` dalam satu dorongan, merata-melewati-range menaruh volum di harga yang hampir tidak
  pernah diperdagangkan. POC hasil itu adalah artefak aturan sebar, dan bisa berpindah penuh hanya
  karena aturan sebar diganti — padahal grafiknya terlihat sama.
- **Bucket = parameter gratis.** Lebar bucket + jendela + aturan sebar = tiga tuas yang bisa
  memunculkan level apa pun yang diinginkan ([[QT4 - Overfitting dan Validasi]]).
- **Aset yang diklaim ≠ aset yang bisa diuji.** Cerita POC hidup di memecoin spot; yang bisa kita
  hargai sendiri adalah aset ber-perp. Menguji profil di BNB lalu menjualnya sebagai "ilmu meme"
  melebihi yang diukur.
- **Level yang dilihat semua orang bisa kosong.** Setelah jadi S/R populer, ia jadi tempat order
  berhenti, bukan tempat transaksi berganti tangan — efeknya berbalik arah terhadap klaim aslinya.
- Duplikasi: POC/VAH/VAL adalah [[FD2 - Support Resistance dan Level Psikologis]] dengan baju
  volum; kalau V1/I4/V2 dipakai bersamaan, itu satu informasi dihitung tiga kali.

## Tingkat bukti

`T1` untuk bentuk geometrinya (dipakai luas) · `T0` untuk "sangat akurat" dan untuk klaim HVN/LVN
sebagai magnet/rejection (klaim vendor, tanpa sumber di repo ini) · untuk Fabius: **belum diuji,
dan belum ada kodenya** — tidak ada satu baris pun di `tools/` yang membentuk histogram harga.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "dari bar OHLCV kita bisa membuat **aproksimasi** distribusi volum menurut harga;
  belum diuji, dan belum ada kodenya."
- **Dilarang:** menyebut hasilnya "volume profile" tanpa keterangan aproksimasi · "Fabius membaca
  POC/value area" · "POC adalah tempat transaksi benar-benar berganti tangan" (itu butuh tick yang
  tidak kami punya) · menjual profil aset perp sebagai profil token spot.

**Terkait:** [[V1 - Konfirmasi Volum dan Money Flow]] · [[V3 - CVD Delta dan Footprint]] ·
[[FD2 - Support Resistance dan Level Psikologis]] · [[ST4 - Range dan Mean Reversion]] ·
[[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]] · [[PL3 - Menganalisis]]
