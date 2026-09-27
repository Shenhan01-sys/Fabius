---
tags: [tk, tk-sinyal, "O3"]
---

# O3 - Stablecoin Supply dan Likuiditas Dolar

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"Strategi Berbasis On-Chain & Data Crypto Spesifik"
(baris "Stablecoin Supply Ratio / Exchange Reserve") — daftar topik, bukan fakta; status Fabius dari
[[Fakta Terukur]] §C/§E

**Ringkas:** idenya: stablecoin adalah **amunisi** — dolar yang sudah berada di dalam ekosistem dan
tinggal menunggu dipindahkan ke aset berisiko. Supply naik = daya beli bertambah; supply turun =
sedang dipakai atau ditarik. Sebagai akuntansi ia benar; sebagai sinyal waktu ia lemah, karena
mint/burn dilakukan untuk alasan yang tidak ada hubungannya dengan niat beli (treasury, OTC,
redemption, rebalancing custodian). Untuk Fabius: tidak ada seri supply sama sekali, dan yang bisa
kami hitung sendiri adalah **likuiditas yang sudah berbentuk dolar di pool**, itu lain hal.

## Definisi yang bisa dihitung

```
supply_chain(t)        = Σ balance(stable) pada kontrak yang diakui di chain itu, per jam
growth(t)              = supply_chain(t) − supply_chain(t-1)            # delta, bukan level
SSR(t)                 = market_cap_aset_induk / stablecoin_supply_total(t)
mint_burn(t)           = Σ event Mint − Σ event Burn pada kontrak stable, per penerbit
dollar_available(t)    = Σ likuiditas USD pada sisi stable dari pool yang diperdagangkan
```

SSR memakai **level** sehingga sensitif terhadap satu peristiwa mint besar; `growth` lebih stabil
tapi lebih lambat. `dollar_available` adalah satu-satunya dari keempatnya yang bisa kami hitung dari
data yang ada di repo hari ini (kolom likuiditas snapshot universe), dan dia bukan supply — dia
kedalaman.

## Cara pakai yang diklaim

Diklaim oleh analis likuiditas global: stablecoin supply tumbuh + SSR turun = bahan bakar bullish;
mint besar di exchange = dana siap dipakai; depeg atau penyusutan cepat = risiko likuiditas
menyeluruh. Dipakai di horizon harian–mingguan pada BTC sebagai "risk-on gauge". Tidak ada dari
klaim ini yang menyebut invalidasi; tidak ada yang menyebut ukuran posisi. Sebagai prosedur
perdagangan bentuknya belum lengkap — klaim pemiliknya adalah **korelasi level**, bukan aturan masuk.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| seri supply stablecoin per chain, point-in-time | `TIDAK-ADA` | §C menyebut exchange reserve; tidak ada satu pun `tools/` yang menyentuh stable supply |
| event mint/burn per penerbit | `TIDAK-ADA` | tidak ada jalur di repo; butuh kueri agregat per jam + definisi "penerbit yang diakui" |
| pembeda supply native vs bridged | `TIDAK-ADA` | belum ada; tanpa ini satu dolar yang sama terbaca di beberapa chain |
| likuiditas USD per pool (proxy daya-beli-tunggu) | `ADA-TAPI` | ikut snapshot universe; sudah dipakai sebagai **veto** `MIN_LIQ_USD` 50.000 USD (§E), belum pernah sebagai sinyal |
| riwayat harga untuk menilai hasil | `ADA` | Aster 9.599 bar ≈ 400 hari (§A) |
| Dune sebagai sumber agregat | `ADA-TAPI` | dialek Trino + lag **±1 jam** di BSC ([[03-Data/D4 - Dune]]) → cukup untuk statistik kelompok, tidak untuk keputusan 4 jam |

**Yang dibutuhkan kalau ini mau dibeli:** kueri agregat per jam (bukan pengiriman baris mentah —
yang mahal itu mengangkut baris, lihat kalibrasi di [[03-Data/D4 - Dune]]), daftar kontrak stable
yang diakui, dan cara menyingkirkan saldo milik penerbit/custodian sendiri dari "supply yang
beredar".
Kalibrasi biaya lebih dulu: `python tools/dune_flow.py --window 3`; angka kreditnya tinggal di
halaman itu, **tidak** di [[Fakta Terukur]], jadi jangan dikutip sebagai angka produk.

## Uji di Fabius

Perintah uji **belum ditulis**. Bentuk yang sah:

1. Fitur = `growth(t)` dan `SSR(t)` yang dihitung hanya dari event `<= t`; sumbernya tidak boleh
   tabel yang bisa di-*update* retro untuk klaim waktu ([[Concepts/Point-in-Time vs Retro-updatable]]).
2. Hasil = return bersih 4 jam pada aset ber-perp dari **bar kami sendiri**, bukan dari sumber fitur.
3. Pembanding = **arah acak pada token dan jam yang sama** ([[Fakta Terukur]] §B), karena kontrol
   "trader biasa" mustahil secara struktural pada data kami.
4. Ambang klaim: `n >= 20` non-overlap, gross di atas **59 bps** (§D), tetap positif setelah fold
   terbaik dibuang, BH α 0,10; satu sampel per (token, jendela tak tumpang-tindih).

Karena pasokan stable berubah per jam dan keputusan kami per 4 jam, fitur ini **harus** diuji pada
pergeseran waktu yang tetap; menguji "supply hari ini vs harga besok" dengan data hari ini adalah
lookahead dengan sepatu yang rapi.

## Batas dan mode gagal

- **Mint ≠ niat beli.** Penerbit mencetak untuk memenuhi penebusan, untuk OTC, atau untuk
  ditempatkan di kas custodian. Semua itu menaikkan "amunisi" tanpa satu pun pembeli.
- **Bridge menghitung ganda.** Dolar yang sama muncul di beberapa chain; tanpa sisi bridge yang
  dinetaskan, `supply_total` adalah penjumlahan ilusi.
- **SSR memakai aset induk yang bukan aset kami.** Definisi standarnya rasio BTC/stable; menjualnya
  sebagai ukuran daya beli untuk memecoin BSC adalah lompatan yang tidak dibuat siapa pun.
- **Level vs delta.** Level naik karena satu alamat kustodian memindahkan brankas; delta lebih
  jujur, dan keduanya sering disalahartikan di dashboard yang sama.
- **Duplikasi:** `dollar_available` adalah sisi pasif dari apa yang diukur
  [[FD3 - Likuiditas dan Dampak Harga]] dan sudah jadi veto di [[O6 - Konsentrasi Holder Bundler dan LP Lock]];
  memakainya dua kali membuat satu fakta terlihat seperti dua konfirmasi.
- **Depeg** mengubah seluruh aritmetika USD: semua angka jadi tidak berskala, dan itu kasus gagal
  yang paling mahal, bukan kasus tepi.

## Tingkat bukti

`T1` untuk definisi mint/burn & supply (akuntansi on-chain, dimiliki siapa pun yang membaca event) ·
`T0` untuk klaim waktu ("supply naik = pasar naik") · untuk Fabius: **belum diukur**, dan tidak ada
jalur datanya (§C), jadi tidak ada klaim produk yang bisa ditopang halaman ini.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "yang bisa kami ukur sendiri hanyalah dolar yang sudah ada di pool (likuiditas), dan itu
  sudah kami pakai sebagai penolakan, belum sebagai sinyal."
- **Dilarang:** "Fabius memantau stablecoin supply" · "SSR rendah berarti memecoin BSC akan naik" ·
  "mint USDT jam ini adalah amunisi masuk" — yang terakhir bahkan tidak bisa dibedakan dari
  penebusan tanpa melihat peristiwa di sisi lain.

**Terkait:** [[O1 - Exchange Inflow dan Outflow]] · [[O4 - Active Addresses dan Pemakaian Gas]] ·
[[FD3 - Likuiditas dan Dampak Harga]] · [[M5 - Makro dan Korelasi Silang-Pasar]] · [[PL3 - Menganalisis]]
