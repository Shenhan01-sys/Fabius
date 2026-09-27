---
tags: [tk, tk-fondasi, "FD6"]
---

# FD6 - Ukuran Posisi

**Keluarga:** [[00 - Hub Fondasi]] · **Tahap:** keputusan ([[PL4 - Memutuskan]]), eksekusi ([[PL5 - Mengeksekusi dan Keluar]])
**Sumber:** [[Fakta Terukur]] §D (ongkos tetap) · §E (plafon kontrak, F-D16) · [[02-Contracts/C3 - ExecutionVault]] · `tools/execute_live.py` · `tools/direction.py`

**Ringkas:** Ukuran adalah satu-satunya variabel trading yang sepenuhnya di tangan kita, dan karena
itu paling jarang dibicarakan jujur. Di Fabius yang **mengikat** bukan rumus ukuran, melainkan
plafon kontrak: `dailyCap`, `maxPositionQuote`, `HARD_CEILING`. Angka risiko persentase memang
dicetak lapisan analisis, tapi tidak ada jalur kode yang mengubahnya menjadi ukuran.

## Definisi yang bisa dihitung

```
fixed fractional : notional = f * ekuitas / jarak_stop   -> risiko per trade = f * ekuitas
Kelly binary     : f* = p - (1-p)/b   (b = W/L)          -> maksimum pertumbuhan log
fraksional       : f_agen = kappa * f*,  kappa ~ 0,25-0,5
vol targeting    : notional = target_vol / vol_forecast * ekuitas
batas keluar     : notional <= exit_cap (kapasitas likuiditas yang bisa ditutup)
```

Tiga alasan `kappa < 1`, dan semuanya berlaku untuk agen: `p` dan `b` **diestimasi** (kesalahan
estimasi membuat Kelly penuh terlalu besar), ekornya gemuk dan tidak stasioner, dan urutan masa
depan bukan urutan masa lalu. Yang paling kasar: Kelly penuh meminta angka negatif berarti
"short besar"; versi yang tahan kesalahan estimasi menjawab "nol", bukan "kecil".

## Cara pakai yang diklaim

Praktisi: risiko 1–2 % ekuitas per posisi, turunkan setelah rugi beruntun, naikkan setelah
konfirmasi. Klaim itu mengandaikan (a) ada ekuitas yang bisa dibaca, (b) ada riwayat expectancy
yang cukup, (c) ada jaminan ukuran itu bisa keluar. Fabius baru punya (c) sebagai gerbang.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| plafon yang benar-benar ditegakkan | `ADA` | `dailyCap` default 5 unit · `maxPositionQuote` 1 unit · `HARD_CEILING = 10` (naikkan ke 1.000 tetap dipotong ke 10) · `killSwitch` — [[Fakta Terukur]] §E |
| satu posisi per aset (larang pyramiding) | `ADA` | `AlreadyOpen` di `contracts/ExecutionVault.sol` |
| ukuran dari kapasitas keluar | `ADA-TAPI` | `tools/direction.py` mencetak `exit_cap_1pct_liq_usd` = 1 % likuiditas pool (§E); angka itu **tidak** dipakai sebagai plafon di jalur eksekusi |
| risiko persentase yang dieksekusi | `TIDAK-ADA` | `tools/direction.py` menulis `risk_pct` 0,5 %/1,0 %, tapi `tools/execute_live.py` mengambil ukuran dari plafon kontrak — tidak ada yang menghubungkan keduanya |
| ekuitas / saldo sebagai basis persen | `TIDAK-ADA` | pencatatan settlement belum jadi (lihat [[01-Agent/A4 - Trust Gating and Real-Money Rules]]) |
| distribusi hasil untuk Kelly | `TIDAK-ADA` | `n = 2` yang jatuh tempo (§F) dan `tools/maker_ledger.py` rusak struktural (§H) |
| ramalan vol untuk vol-targeting | `TIDAK-ADA` | `vol_annual` dihitung `tools/direction.py` dan tidak dirujuk di mana pun (lihat [[FD8 - Volatilitas]]) |

## Uji di Fabius

Yang sudah diuji: perilaku plafon — kenaikan `dailyCap` ke 1.000 dipotong ke 10, dan itu keluaran
suite forge ([[Fakta Terukur]] §E; [[07-Testing/T3 - Execution Suite]]). Ukuran nyata yang pernah
dijalankan: posisi 1 unit, round-trip **−59 bps** (§D/§F).

Yang belum dan diperlukan supaya ukuran jadi keputusan, bukan kebetulan:

1. Kurva ukuran→dampak: jalankan round-trip pada beberapa ukuran, baca `entryPx18`/`exitPx18` dari
   event; butuh keputusan builder karena plafon hari ini membatasi di 1 unit per posisi.
2. expectancy per ukuran (`tools/ledger.py`), lalu Kelly fraksional hanya kalau `E > 0` dan
   `n >= 20` (§E). Dengan `E <= 0` jawaban rumusnya adalah **0** — dan itu bukan penundaan sopan,
   itu isi perhitungannya.
3. Uji ketahanan: dua posisi simultan di aset berbeda yang ternyata satu taruhan
   ([[FD10 - Korelasi dan Risiko Keranjang]]) — `dailyCap` menjumlah notional, tidak bertanya.

## Batas dan mode gagal

- **Ilusi "modal kecil = ukuran kecil = aman".** Ongkos tetap tidak ikut mengecil; pada posisi $1,
  ±$0,05 bolak-balik menuntut **+5 %** hanya untuk balik modal (§D, estimasi mainnet — **belum
  diukur di repo ini**). Ukuran kecil tidak mengubah tanda expectancy, ia hanya memperburuknya.
- **Plafon mutlak tidak merasakan mengecilnya modal.** Pada modal sangat kecil, `maxPositionQuote`
  1 unit tidak pernah jadi pengikat — yang mengikat adalah ongkos, dan itu tidak ada di kontrak.
- **`HARD_CEILING` memotong, tidak menolak.** Perintah pemilik diubah diam-diam menjadi angka
  lain; aman untuk bahaya, menyesatkan untuk pembaca laporan: yang tercatat adalah cap yang
  berlaku, bukan yang diminta.
- **Angka yang dicetak bukan angka yang ditegakkan.** Selama `risk_pct` tidak masuk jalur
  eksekusi, setiap kalimat "ukuran posisi kami 0,5 % ekuitas" adalah klaim tanpa gerbang.
- **Short ≠ long di sini.** Di venue kami short = menjual inventaris sendiri lalu membeli kembali
  (`NeedInventory`), jadi plafon dihitung dalam **quote**, bukan jumlah token — satuan yang pernah
  disamakan dan itu bug nyata (`contracts/ExecutionVault.sol`).

## Tingkat bukti

`T3` untuk perilaku plafon kontrak (teruji suite) · `T1` untuk fixed fractional / Kelly fraksional /
vol targeting sebagai kerangka · untuk Fabius: **kebijakan ukuran belum diuji** — tidak ada
expectancy positif pada `n >= 20` yang bisa dimasukkan ke rumus apa pun (§E/§F).

## Boleh dibaca, dilarang dibaca

- **Boleh:** "yang membatasi ukuran di Fabius adalah plafon kontrak dan kapasitas keluar; rumus
  ukuran butuh expectancy positif dan itu belum ada, jadi jawabannya sampai hari ini: tidak ada posisi."
- **Dilarang:** "kami memakai Kelly" · "risiko 0,5 % per posisi ditegakkan kode" · "modal kecil
  membuat strategi ini aman dicoba".

**Terkait:** [[FD4 - Ongkos Perdagangan]] · [[FD5 - Expectancy Bukan Win Rate]] ·
[[FD3 - Likuiditas dan Dampak Harga]] · [[FD7 - Invalidation Stop dan Time-Stop]] ·
[[02-Contracts/C3 - ExecutionVault]] · [[QT10 - Eksekusi Algoritmik]] · [[PL5 - Mengeksekusi dan Keluar]]
