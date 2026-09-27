---
tags: [tk, tk-sinyal, "O1"]
---

# O1 - Exchange Inflow dan Outflow

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"Strategi Berbasis On-Chain & Data Crypto Spesifik"
(baris "Exchange Inflow/Outflow") — **daftar topik**, bukan fakta; status Fabius dari [[Fakta Terukur]] §C

**Ringkas:** metrik ini menghitung token yang berpindah **masuk** ke alamat yang dilabeli bursa dan
yang keluar darinya; ceritanya: inflow = niat jual, outflow = akumulasi. Yang benar-benar diukur
adalah **perpindahan kustodi**, bukan niat — dan niat itu bahkan bukan milik satu pemilik dompet.
Untuk Fabius statusnya jelas dan tercatat: tidak ada jalur reserve exchange sama sekali (§C), jadi
catatan ini bukan "metode yang kami pakai", melainkan "metode yang sampai hari ini tidak bisa kami
jalankan".

## Definisi yang bisa dihitung

```
inflow(t, aset)  = Σ amount(x)  untuk transfer x pada (t-1, t] dengan to  ∈ LabelExchange
outflow(t, aset) = Σ amount(x)  untuk transfer x pada (t-1, t] dengan from ∈ LabelExchange
netflow(t)       = inflow(t) − outflow(t)
reserve(t)       = saldo on-chain seluruh alamat berlabel bursa  (kumulatif, bukan selisih)
```

Tiga hal yang membuat rumus di atas tidak boleh ditulis sembarangan: (a) `LabelExchange` adalah
**peta alamat → bursa** yang dibuat vendor, bukan fakta on-chain; (b) perpindahan antar dua alamat
bursa sendiri (`inflow` sekaligus `outflow`) harus dibuang atau dilaporkan terpisah, kalau tidak
rebalancing internal terbaca sebagai distribusi; (c) angka harus dalam **USD pada saat kejadian**,
bukan USD hari ini — kalau tidak, satu pergerakan yang sama berubah nilai setiap kali harga berubah.

## Cara pakai yang diklaim

Diklaim oleh vendor data on-chain dan praktisi yang membacanya di dashboard: naikkan `reserve` →
pasokan yang bisa dijual membesar → tekanan jual; turun → akumulasi. Dipakai di BTC/ETH pada
skala harian, biasanya sebagai konfirmasi arah, dengan `netflow` 1–24 jam. **Tidak ada** pemilik
klaim yang menyebutkan invalidasi, horizon tetap, atau ongkos — jadi sebagai prosedur perdagangan
bentuknya belum lengkap. `Plan.txt` memasukkannya ke "edge khas crypto yang tidak dimiliki pasar
lain"; itu kalimat superlatif tanpa sumber (`T0`).

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| seri reserve/netflow exchange di BNB Chain | `TIDAK-ADA` | §C mencatat "exchange reserve" sebagai yang **tidak** kami punya sama sekali |
| peta label alamat bursa point-in-time | `TIDAK-ADA` | tidak ada jalur di repo; tidak ada satu pun berkas `tools/` yang menyebut label alamat |
| feed transfer ERC-20 mentah (event `Transfer`) | `TIDAK-ADA` | `universe/record_wallet_flow.py` merekam **swap yang sudah dilabeli GMGN** (maker, side, harga), bukan transfer antar dompet — dua hal berbeda |
| riwayat harga untuk menilai hasil | `ADA` | Aster 9.599 bar 1 jam ≈ 400 hari — [[Fakta Terukur]] §A |
| Dune sebagai jalan pintas agregat | `ADA-TAPI` | Trino, lag **±1 jam** di BSC ([[03-Data/D4 - Dune]]) → tidak bisa jadi jalur keputusan untuk horizon kami (4 jam) |

**Yang dibutuhkan kalau nanti dibuat:** satu kueri agregat di Dune yang menjembatani event transfer
ke peta label alamat bursa, dihitung per jam. **Nama tabel labelnya belum kami verifikasi dari repo
ini**, jadi catatan ini sengaja tidak menulis SQL-nya — menuliskannya berarti mengarang endpoint.
Biaya kreditnya terbaca (`execution_cost_credits` di respons status); kalibrasi yang benar sebelum
membeli apa pun: `python tools/dune_flow.py --window 3`. Angka hasil kalibrasi dicatat di
[[03-Data/D4 - Dune]], **bukan** di [[Fakta Terukur]] — jangan dikutip dari halaman ini sebagai angka produk.

## Uji di Fabius

Bentuk uji yang sah, belum ada kodenya — perintahnya **belum ditulis**:

1. `netflow(t)` dihitung hanya dari transfer dengan waktu `<= t` ([[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]);
   baris Dune yang bisa di-*update* retro tidak boleh jadi saksi waktu ([[Concepts/Point-in-Time vs Retro-updatable]]).
2. Hasil = return bersih 4 jam dari bar harga **kami sendiri**, bukan dari sumber yang sama.
3. Pembanding: **arah acak pada token dan jam yang sama** ([[Fakta Terukur]] §B). "Tidak ada inflow"
   bukan kontrol — itu cuma sampel lain dari dunia yang sama.
4. Lolos kalau `n >= 20` non-overlap, gross di atas **59 bps** (ongkos terukur §D, bukan 20 bps
   asumsi), tetap positif setelah fold terbaik dibuang, lolos BH α 0,10.

Sampai ada `reserve` point-in-time, tidak ada satu pun langkah di atas bisa dijalankan. Itu
**lubang data**, bukan metode yang gagal ([[GAP4 - Yang Tidak Bisa Diuji Karena Data]]).

## Batas dan mode gagal

- **Kustodi ≠ deposit.** Token masuk ke hot wallet bursa bisa berarti "siap dijual", "settlement
  internal", "penarikan ke dompet dingin milik bursa itu sendiri", atau "custodian memindahkan
  brankas". Dari on-chain keempatnya identik.
- **Penambang vs ritel bukan detail.** Arus penambang masuk ke bursa adalah pengeluaran biaya
  listrik bulanan dengan periode tetap; ia menciptakan inflow yang berulang tanpa informasi apa pun
  tentang arah besok. Membacanya sebagai "paus keluar" adalah salah satu cara paling murah
  menghasilkan sinyal palsu.
- **Lag pelabelan alamat.** Sebuah dompet baru diketahui milik bursa setelah labelnya dibuat.
  Memakai peta label **hari ini** pada arus **tahun lalu** = pilihan retroaktif; koreksinya satu
  arah (hanya bisa membuat historinya terlihat rapi) — penyakit yang sama persis dengan panel
  di [[O5 - Whale dan Kohor Smart Money]] ([[Concepts/Lookahead Bound]]).
- **Agregat menutupi satu nama.** Di BSC sebagian kecil alamat mendominasi `reserve`; satu
  pergerakan satu bursa mengubah angka seluruh pasar dan bisa membalik tanda `netflow`.
- **Duplikasi sinyal:** `outflow` + beli di DEX pada akhirnya adalah permintaan yang sama dengan
  yang sudah tertangkap volume/price action ([[V1 - Konfirmasi Volum dan Money Flow]]); menambah
  keduanya tidak menambah informasi kalau sumber peristiwanya satu.

## Tingkat bukti

`T1` untuk definisi metrik (dipakai luas oleh vendor, bentuknya tidak dibakukan siapa pun) · `T0`
untuk klaim waktu "inflow menjual besok" (tidak ada pemilik klaim yang bisa kami periksa) · untuk
Fabius: **belum diuji dan tidak bisa diuji** — jalurnya `TIDAK-ADA` (§C), jadi tidak ada tingkat
bukti produk di sini sama sekali.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami tidak punya reserve exchange, dan alasan mekanisnya tercatat; catatan ini
  berisi bentuk uji yang akan dipakai kalau jalur itu dibeli."
- **Dilarang:** "Fabius memantau exchange inflow" · "arus keluar berarti whale akumulasi" ·
  "netflow negatif bulan ini memprediksi pantulan" — kalimat pertama salah fakta, tiga sisanya
  menjual interpretasi sebagai pengukuran.

**Terkait:** [[O3 - Stablecoin Supply dan Likuiditas Dolar]] · [[O5 - Whale dan Kohor Smart Money]] ·
[[O7 - Token Unlock dan Vesting]] · [[FD3 - Likuiditas dan Dampak Harga]] · [[PL3 - Menganalisis]]
