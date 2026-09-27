---
tags: [tk, tk-sinyal, "M5"]
---

# M5 - Makro dan Korelasi Silang-Pasar

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"5. Pendekatan Fundamental & Sentiment (Crypto
Native)" ("Macro + Crypto correlation (DXY, interest rate, ETF flow)") — klaim komunitas

**Ringkas:** Crypto diperdagangkan sebagai aset beta tinggi: dolar menguat dan likuiditas global
menarik diri biasanya berarti aset berisiko tertekan. Mengetahui ini benar **tidak** memberi
Fabius jalur data: sampai halaman ini ditulis, tidak ada satu pun deret makro di repo ini — bukan
yang mati, yang memang belum pernah dicoba. Karena itu catatan ini bukan tentang cara memakai
makro, tapi tentang apa yang harus ada sebelum kata "rezim makro" boleh muncul di keputusan agen,
dan tentang pengganti yang **sudah** kami punya untuk risiko yang sama.

## Definisi yang bisa dihitung

```
objek yang dimaksud:
rho_AB(jendela)   = korelasi return harian A vs B pada jendela bergulir w
beta_terhadap_BTC = cov(r_aset, r_BTC) / var(r_BTC) pada jendela bergulir
# hipotesis yang diuji keluarga ini: rho(crypto vs makro) dan rho(antar-aset) NAIK saat stres.
# Uji yang sah (dan murah dengan data kami): bandingkan matriks korelasi antar simbol kita pada
# decile volatilitas terendah vs tertinggi. Ini mengukur "diversifikasi saat dibutuhkan",
# tanpa satu pun angka makro.
```

Perhatikan apa yang hilang dari kotak di atas: **semua nama variabel makro**. Bukan karena tidak
penting, karena belum ada jalurnya — dan menuliskan DXY/Fed funds seolah kami punya adalah persis
yang dilarang di subtree ini ([[Aturan Subtree]]).

## Cara pakai yang diklaim

Klaim komunitas: indeks dolar (DXY) sebagai cermin risiko crypto; keputusan suku bunga dan likuiditas
global sebagai "banjir/kering"; flow ETF sebagai permintaan institusi. Dipakai luas sebagai penjelas
setelah fakta. Tidak ada rujukan primer di repo ini, dan klaim "DXY memprediksi BTC" adalah klaim
milik siapa pun yang menuliskannya, bukan milik kami.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| deret DXY / indeks dolar | `TIDAK-ADA` | tidak ada jalur; belum pernah diukur sebagai pasangan sumber×jaringan (§C) |
| suku bunga kebijakan / imbal hasil obligasi | `TIDAK-ADA` | sama; tidak ada satu pun berkas di `tools/`/`universe/` yang menyebutnya |
| likuiditas global (M2 / neraca bank sentral) | `TIDAK-ADA` | angka publiknya ada, jalur kita tidak |
| flow ETF (emisi/penebusan BTC/ETH) | `TIDAK-ADA` | diterbitkan pihak ketiga; tidak ada jalur, dan waktu terbitnya sendiri jadi masalah ([[M2 - Sentimen Sosial dan Ekstraksi LLM]]) |
| deret harga untuk menguji **konsekuensi** makro | `ADA-TAPI` | kline Aster 9.599 bar ≈ 400 hari (§A) + Hyperliquid 5.001 bar (chain sendiri) — hanya aset ber-perp |
| proxy rezim tanpa makro (volatilitas, korelasi, breadth) | `ADA-TAPI` | `atr_pct`/`vol_annual` sudah dihitung `tools/direction.py`; korelasi antar simbol belum pernah dihitung siapa pun |

## Uji di Fabius

Dua hal berbeda dan jangan ditukar:

1. **Makro sebagai data** — perlu pekerjaan yang belum dimulai: satu jalur yang hidup di **dua**
   jaringan (aturan §C), dengan tanggal/waktu sumber tercatat (waktu kebenaran di sini bukan jam
   laptop, lihat [[03-Data/D3 - Price Depth]] tentang paging + meta), lalu diuji terhadap hasil kita
   dengan ambang biasa: `n >= 20` non-overlap, gross di atas **59 bps** (§D), BH α 0,10 (§E).
   Sebelum itu, statusnya `TIDAK-ADA` — bukan `MATI-DARI-MESIN-INI`, karena kita belum pernah bertanya.
2. **Makro sebagai hipotesis tentang risiko keranjang** — sudah bisa diuji sekarang tanpa data baru:
   matriks korelasi antar simbol ter-cache pada jendela volatilitas rendah vs tinggi. Kalau korelasi
   naik saat stres, konsekuensinya langsung nyata untuk ukuran posisi ([[FD6 - Ukuran Posisi]],
   [[FD10 - Korelasi dan Risiko Keranjang]]) — dan itu adalah cara yang benar untuk memakai pengetahuan
   makro yang datanya tidak kami punya.

## Batas dan mode gagal

- **Korelasi ≠ jalur sebab, dan ≠ peluang trading.** "DXY dan BTC berkorelasi negatif" tidak
  memberi siapa pun order yang menutup ongkos 59 bps; ia memberi alasan untuk tidak menumpuk
  risiko searah.
- **Jendela satu tahun bukan siklus makro.** 400 hari (§A) tidak memuat satu pun rezim bunga penuh;
  apa pun yang kita sebut "kontrol rezim" pada deret sepanjang itu adalah label, bukan temuan
  ([[FD1 - Struktur Pasar dan Rezim]]).
- **Frekuensi tidak cocok.** Makro harian/bulanan vs keputusan kami per 4 jam: memakai angka makro
  untuk keputusan 4 jam hampir selalu berarti memakai angka yang lebih tua dari posisimu —
  masalah umur data yang sama yang sudah kami hash di jalur harga
  ([[01-Agent/01 - Asset Classes and Seats]]).
- **Risiko duplikasi paling tinggi di keluarga ini:** semua "efek makro" sudah masuk ke portofolio
  kami lewat volatilitas dan korelasi antar simbol; menambah DXY tanpa data = menambah satu
  derajat kebebasan untuk menjelaskan apa yang sudah dijelaskan ([[QT4 - Overfitting dan Validasi]]).

## Tingkat bukti

`T1` untuk "crypto adalah aset beta tinggi dan korelasi naik saat stres" (dikenal luas; tidak kami
reproduksi) · `T0` untuk setiap angka korelasi DXY/BTC yang dikutip tanpa paper · untuk Fabius:
**tidak ada datanya sama sekali**, jadi tidak ada satu pun kalimat di halaman ini yang boleh dibaca
sebagai kemampuan agen.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami tidak punya jalur data makro; yang bisa kami pakai untuk risiko yang sama adalah
  volatilitas dan korelasi antar aset yang sudah kami punya, dan itu belum pernah dihitung."
- **Dilarang:** "Fabius menyesuaikan diri ke rezim makro" · menyebut DXY/suku bunga/ETF flow sebagai
  input agen · memakai kenaikan korelasi saat stres sebagai alasan menambah posisi · mengklaim
  korelasi lintas pasar pada deret 400 hari sebagai temuan.

**Terkait:** [[M1 - Fear and Greed dan Indeks Sentimen]] · [[M3 - Narasi Sektar dan Rotasi]] ·
[[M4 - Catalyst dan Event Trading]] · [[FD10 - Korelasi dan Risiko Keranjang]] ·
[[FD1 - Struktur Pasar dan Rezim]] · [[GAP4 - Yang Tidak Bisa Diuji Karena Data]]
