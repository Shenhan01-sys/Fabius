---
tags: [tk, tk-fondasi, "FD2"]
---

# FD2 - Support Resistance dan Level Psikologis

**Keluarga:** [[00 - Hub Fondasi]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** [[Fakta Terukur]] §A/§C (yang bisa dan tidak bisa kita lihat) · sisanya pengetahuan standar pasar — tidak ada rujukannya di repo ini

**Ringkas:** "Level" adalah harga yang dipercaya orang punya daya pantul. Ada tiga jenis yang berbeda
sifatnya — statis (swing/POC), dinamis (MA/VWAP), dan angka bulat — dan hanya jenis ketiga yang punya
alasan mekanis untuk bekerja. Sisanya sering berupa artefak penglihatan: garis yang kelihatan jelas
setelah harga memantul, bukan sebelum.

## Definisi yang bisa dihitung

```
statis_swing : high/low pivot pada bar <= t (definisi pivot di [[FD1 - Struktur Pasar dan Rezim]])
statis_poc   : harga dengan volum baris terbesar pada jendela -> [[V2 - Volume Profile dan POC]]
dinamis_ma   : nilai SMA/EMA periode p pada bar t            -> [[I1 - Moving Average]]
dinamis_vwap : sum(typical_price * vol) / sum(vol) sejak jangkar yang ditentukan DI MUKA
round_number : harga yang membuat |harga / 10^k| mendekati bulat, k dari satuan quote
```

Tiga hal yang wajib ditetapkan sebelum level boleh disebut "teruji": **sumbernya** (bar mana saja),
**toleransi sentuh** (berapa jauh harga dianggap menyentuh — biasanya dalam
[[FD8 - Volatilitas|ATR]]), dan **umurnya** (level berapa jam masih dipakai orang). Ketiganya adalah
parameter, bukan detail.

## Cara pakai yang diklaim

Praktisi: beli di support, jual di resistance, stop di luar level, target di level berikutnya;
semakin sering disentuh semakin "kuat". Angka bulat diklaim ramai karena order manusia dan
take-profit memang ditulis bulat. Tidak ada satu pun sumber yang kami bisa periksa yang mengukur
daya pantul level pada memecoin BSC — jadi seluruh paragraf ini berstatus klaim
(`T0`/`T1`), bukan temuan.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| OHLC 1 jam ≥ 2.400 bar | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari, hanya aset ber-kontrak perp — [[Fakta Terukur]] §A |
| order book L2 (order yang benar-benar antre di level) | `TIDAK-ADA` | tidak ada jalurnya di repo ini — §C |
| volum per bar untuk POC / volume profile | `ADA-TAPI` | ikut `klines`; belum pernah dipakai menghitung profil |
| level harga yang tersimpan di artefak keputusan | `TIDAK-ADA` | `tools/direction.py` tidak punya konsep level: stop/target = jarak ATR dari harga terakhir |
| deret untuk aset tanpa perp | `ADA-TAPI` | GMGN mentok 1.000 bar ≈ 41,6 hari — level dari ±41 hari bukan level institusional |

## Uji di Fabius

Uji yang sah, dan belum ada perintahnya (`tools/sr_study.py` — **belum ditulis**):

1. Bangun level hanya dari bar `<= t` dan bekukan daftarnya per titik keputusan
   ([[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]).
2. Event = sentuhan pertama setelah level berusia ≥ X bar; hasil = return bersih pada horizon tetap
   **dan** hasil kalau kena stop — dua-duanya dilaporkan.
3. Kontrol yang benar: **level palsu** — harga yang sama-sama bulat tetapi tidak pernah jadi pivot,
   dan **arah acak pada token dan jam yang sama** (pembanding yang tersedia bagi kami, §B).
   Tanpa kontrol level-palsu, apa pun yang mirip level akan terlihat bekerja.
4. Lolos: `n >= 20` non-overlap, gross di atas **59 bps** ([[Fakta Terukur]] §D), tetap positif
   setelah fold terbaik dibuang, BH α 0,10 (§E). Jalur yang ada: `tools/backtest.py`.

## Batas dan mode gagal

- **Self-fulfilling vs penglihatan.** Angka bulat punya jalur kausal yang bisa dibayar: order
  manusia ditulis bulat, jadi antreannya sungguh ada. Swing high/low tidak — ia hanya jadi nyata
  setelah harga kembali ke sana. Membedakan keduanya butuh data order, dan data itu `TIDAK-ADA` di
  repo ini (§C). Jadi catatan ini **tidak** bisa bilang "level itu nyata", hanya "level X punya
  alasan mekanis; level Y tidak".
- **Survivorship visual.** Pantulan yang gagal tidak ditandai di chart; yang ditandai cuma yang
  berhasil. Tidak ada mekanisme di gambar yang menahan itu.
- **Semakin banyak sentuhan semakin lemah, bukan semakin kuat** — klaim komunitas yang paling
  sering terbalik: tiap sentuhan menyerap order di sisi yang sama.
- **Level adalah jarak, bukan risiko.** Jarak stop ke level tidak sama dengan kemungkinan kena stop;
  itu urusan [[FD7 - Invalidation Stop dan Time-Stop]] dan [[FD3 - Likuiditas dan Dampak Harga]].
- **Duplikasi.** POC, VWAP, dan "level volum tertinggi" mengukur hal yang sama dengan bobot berbeda
  — memakainya bertiga sebagai tiga konfirmasi = satu informasi dihitung tiga kali.

## Tingkat bukti

`T1` untuk round number (dipakai luas, ada mekanisme yang plausibel) · `T0` untuk daya pantul
swing/SMA pada memecoin BSC (tidak ada sumber yang bisa kami periksa) · untuk Fabius: **belum
diuji** — tidak ada satu baris pun di `tools/` yang menghitung level.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "angka bulat satu-satunya jenis level yang punya alasan mekanis yang bisa kita
  bayangkan; yang lain harus diuji sebagai peristiwa, dan kami belum mengujinya."
- **Dilarang:** "harga memantul di support" · "Fabius memakai level support/resistance" ·
  "semakin sering disentuh, semakin kuat" (kebalikannya yang masuk akal).

**Terkait:** [[S1 - Candlestick dan Price Action Murni]] · [[S6 - Likuiditas Stop Hunt dan Inducement]] ·
[[V2 - Volume Profile dan POC]] · [[I7 - VWAP dan Anchored VWAP]] · [[FD8 - Volatilitas]] ·
[[FD3 - Likuiditas dan Dampak Harga]] · [[PL3 - Menganalisis]]
