---
tags: [tk, tk-pipeline, "PL1"]
---

# PL1 - Mengumpulkan Data

**Keluarga:** [[00 - Hub Pipeline]] · **Tahap:** fetching (halaman ini) · sesudahnya [[PL2 - Menyaring Universe]]
**Sumber:** `tools/bars.py`, `universe/record_bsc_universe.py`, `universe/record_wallet_flow.py` · [[Fakta Terukur]] §A–§C

**Ringkas:** Tahap pertama bukan "ambil data", tapi **memilih saksi**: angka pasar baru bernilai
setelah kita tahu siapa mencatat waktunya dan apakah angka itu masih bisa diambil kembali nanti.
Fabius memisahkan dua peran sejak awal — deret harga (bisa ditarik mundur → bukan saksi waktu) dan
aliran transaksi (tidak bisa ditarik mundur → wajib direkam sebelum dibutuhkan). Sebagian besar
pekerjaan tahap ini adalah jujur tentang yang tidak kita punya: tidak ada order book L2 dan tidak ada
tick di repo ini, jadi seluruh keluarga analisis order-flow tidak bisa dinaikkan bukti di sini.

## Definisi yang bisa dihitung

Satu rekaman yang layak dipercaya punya dua waktu yang berbeda, dan hanya salah satunya membuktikan urutan:

```
rekaman = (sumber, nilai, t_saksi, t_tarik, skema, hash)
  t_saksi : waktu yang diberikan pihak ketiga (commit GitHub, epoch respons, nomor blok)
  t_tarik : waktu kita bertanya -- kalau hanya ini yang tersisa, rekaman itu bukan bukti urutan
```

| kelas data | bisa disusulkan belakangan? | boleh jadi saksi waktu? | contoh di repo |
|---|---|---|---|
| deret harga OHLCV | ya, selama server melayani `startTime` | **tidak** | Aster `klines`, Hyperliquid `candleSnapshot` |
| aliran transaksi dompet | **tidak** (paging diabaikan server → tanpa riwayat) | ya, commit-nya ber-timestamp pihak ketiga | `universe/wallet-flow.jsonl` |
| agregat on-chain ber-`_updated_at` | ya, dan berubah diam-diam | **tidak** | Dune `dex.trades` ([[03-Data/D4 - Dune]]) |
| keputusan kami sendiri | tidak, setelah di-hash | ya | `decisionHash` di chain ([[PL7 - Kontrak Antar-Tahap]]) |

```
uji_terbuka(horizon) : kedalaman_bar * interval >= NEED_BARS  dan  interval <= horizon
                       NEED_BARS = 2400 (5-fold walk-forward) -- [[Fakta Terukur]] §A
# 1 bar 1 jam tidak menguji klaim 5 menit; 1.000 bar 4 jam tidak menguji intraday
```

## Cara pakai yang diklaim

Klaim yang beredar di literatur praktisi (T1, pemiliknya jarang disebut): "makin granular makin
baik" — tick > L2 > OHLCV, ditambah funding/OI, arus on-chain, aliran dompet, narasi. Arahnya benar
sebagai prinsip (butir lebih halus memperlihatkan yang tidak terlihat di bar), tapi tidak berlaku
umum: resolusi yang tidak bisa kamu kunci pada saat ia terjadi hanya menambah permukaan bug. Batas
minimum yang kami pakai untuk menyebut sebuah tahap fetch selesai: harga + volum, umur data, siapa
penerbit angkanya, dan seberapa dalam dibanding horizon keputusan ([[FD9 - Horizon Waktu dan Multi-Timeframe]]).

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| bar 1 jam ≥ 2.400 untuk aset ber-kontrak perp | `ADA` | Aster 9.599 bar ≈ 400 hari; cap 1.500 bar/panggilan → dalam karena **paging** — [[Fakta Terukur]] §A |
| bar untuk aset tanpa kontrak perp | `ADA-TAPI` | GMGN `token_kline` mentok 1.000 bar ≈ 41,6 hari; **0 bar** untuk token gas — §A |
| funding + OI | `ADA-TAPI` | hidup (608 kontrak Aster · 234 Hyperliquid) + **histori bisa disedot mundur**: Bybit 66,3 hari per 8 jam, OKX 33,0, OI Binance 20,8 hari per 1 jam — §A.5; interval 8 jam tetap bukan fitur per-bar |
| order book L2 · tick · footprint · heatmap likuidasi | `TIDAK-ADA` | tidak ada jalurnya di repo ini — §C |
| aliran transaksi dompet | `ADA` | 100 transaksi/panggilan, jendela lihat 8–13 menit, tanpa riwayat — §B |
| narasi (tema + nada) | `ADA-TAPI` | jalur berkas mentah GDELT hidup; DOC API 429 di dua jaringan; belum diuji sebagai prediktor — §C |
| CEX langsung (Binance/Bybit/OKX/Bitget) | `MATI-DARI-MESIN-INI` | `451 restricted location` · `403 CloudFront country` · TLS terpotong, terukur 24 Sep — §C |
| unlock/vesting · MVRV/SOPR/NUPL · exchange reserve | `TIDAK-ADA` | §C |

## Uji di Fabius

Tahap ini diuji dengan mengukur jalurnya, bukan dengan memuji hasilnya:

```
python -X utf8 tools/bars.py BNBUSDT --days 300      # kedalaman nyata + meta sumber/halaman
python -X utf8 tools/whale_report.py                 # kesehatan aliran; cost_bps_applied dicetak duluan
python -X utf8 universe/record_bsc_universe.py       # satu snapshot, tanpa --loop, menutup lubang jendela
```

Yang wajib lolos sebelum angkanya dipakai di hilir: meta cache lengkap (endpoint, halaman, sha256) dan
tidak ada pertentangan internal di dalamnya; truncation **diucapkan** (`LIMIT`, `[TERPOTONG]`), bukan
dibisikkan ([[04-Tools/TL7 - measurement harness]]); setiap angka panel punya tanggal run
([[03-Data/D2 - Wallet Flow]]). Yang belum diuji dan karena itu tidak boleh diklaim: apakah merekam
lebih banyak bidang menaikkan kualitas keputusan *(belum diukur)*.

## Batas dan mode gagal

- **Perekam yang berhenti = pengetahuan yang hilang.** Untuk harga kita bisa kembali kemarin; untuk
  jendela 8 menit tidak ada "kemarin". Karena itu kegagalan perekam diperlakukan lebih serius daripada
  hasil buruk: alat yang gagal diam-diam lebih berbahaya dari alat yang gagal keras ([[04-Tools/00 - Hub Tools]]).
- **Jam laptop bukan saksi** — ia pernah melompat setelah laptop tidur; sumber waktu = timestamp pihak
  ketiga ([[Concepts/Stale Local Copy]]). Semua penanda waktu disimpan UTC; pernah sebuah berkas
  bernama lokal berisi data hari sebelumnya ([[04-Tools/TL2 - direction]]).
- **Satu penulis per berkas append-only.** Dua penulis di satu JSONL sudah dua kali memicu konflik union ([[03-Data/D2 - Wallet Flow]]).
- **Kegagalan join menyamar sebagai "tidak ada aktivitas"**: paging yang diabaikan, `limit` yang
  dipotong server, penggabungan dua sumber yang hampir tidak bertemu ([[06-Results/03 - Not Yet Proven]] baris 12).
- **"Bisa diakses" bukan sifat sumber**, melainkan sifat pasangan sumber × jaringan ([[Fakta Terukur]] §C).
- **Kedalaman tidak membeli struktur:** aset dengan riwayat terdalam justru bisa paling tak menarik
  ([[PL3 - Menganalisis]]). **Survivorship lahir di sini:** yang punya masa panjang hanyalah yang selamat ([[03-Data/D3 - Price Depth]]).

## Tingkat bukti

`T3` untuk kedalaman tiap sumber dan untuk daftar "yang mati" — keduanya diukur alat di repo ini dan
tercatat di [[Fakta Terukur]] §A–§C. `T1` untuk daftar bidang yang lazim direkam (praktik umum tanpa
pemilik). Untuk klaim "resolusi lebih tinggi = keputusan lebih baik": `T1`, belum pernah kami uji, dan
sebagian besar tidak bisa diuji karena datanya `TIDAK-ADA`.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami tahu persis seberapa jauh kami bisa menghargai sebuah aset sendiri, dan sumber mana
  yang tidak bisa dijadikan saksi waktu."
- **Dilarang:** "Fabius punya data pasar yang lengkap" · "semua sumber bisa ditarik mundur kapan pun"
  · "jam mesin kami cukup untuk membuktikan urutan" · "makin banyak feed, makin baik keputusan".

**Terkait:** [[PL2 - Menyaring Universe]] · [[PL7 - Kontrak Antar-Tahap]] · [[PL6 - Menilai Hasil]] ·
[[03-Data/D3 - Price Depth]] · [[03-Data/D4 - Dune]] · [[Concepts/Point-in-Time vs Retro-updatable]] ·
[[QT12 - Stack Data dan Perkakas]] · [[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]
