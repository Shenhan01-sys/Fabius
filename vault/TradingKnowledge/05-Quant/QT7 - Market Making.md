---
tags: [tk, tk-quant, "QT7"]
---

# QT7 - Market Making

**Keluarga:** [[00 - Hub Quant]] · **Tahap:** eksekusi ([[PL5 - Mengeksekusi dan Keluar]])
**Sumber:** `vault/TradingKnowledge/QuantTrading/Info1.txt` §"Strategi Quant yang Populer di
Crypto" / §"Pelajari market making crypto" (daftar topik) · venue kami:
[[02-Contracts/C4 - DemoPair and DemoAsset]] · [[Fakta Terukur]] §C/§D/§H

**Ringkas:** market making menjual likuiditas: pasang beli di bawah dan jual di atas, ambil spread
yang dikutip, dan bayar dengan dua risiko — diisi duluan oleh orang yang tahu sesuatu (adverse
selection) dan posisi yang menumpuk saat harga pergi (inventory risk). Ini adalah pekerjaan yang
butuh buku order dan kecepatan. Kami tidak punya keduanya, dan di saat yang sama ada hubungan yang
tidak terduga: venue tempat Fabius mengeksekusi **adalah** sebuah meja likuiditas — pool x·y=k
dengan fee 30 bps. Setiap kali kami swap, kami berdiri di sisi lain dari meja itu dan membayarnya.

## Definisi yang bisa dihitung

```
quoted_spread := ask - bid                     (bps dari mid)
edge_pilih    := fill_t - mid_t                (markout: harga tengah geser ke arah yang salah?)
adverse_sel.  := E[ markout(Δ) | diisi ]       > 0  berarti flow yang mengisi kita tahu arah
inventory     := q_t  (posisi yang tersisa) ; biaya = q_t * pergerakan harga + ongkos rebalance
pnl_mm        := (spread terambil) - (adverse selection) - (biaya hedging) - (kuota tak terisi)
```

`markout` adalah angka yang membuat MM jujur: kalau setiap fill langsung diikuti perpindahan harga
melawan kita, "spread" yang kita ambil adalah uang pengganti, bukan keuntungan.

**Avellaneda–Stoikov** disebut di sini sebagai **nama**, bukan resep: kerangka teori yang memilih
kuotasi sebagai fungsi dari posisi persediaan dan risiko (diklaim literatur market-making; tidak
kami reproduksi, tidak kami implementasi, dan tidak kami punya bahan untuk calibratenya).

## Cara pakai yang diklaim

Klaim pendukungnya (vendor bot MM, praktisi Hummingbot, dana HFT): pendapatan stabil dari spread,
"hampir market-neutral", bisa jalan 24/7. Di crypto klaim ini bertabrakan dengan dua hal yang
terukur di halaman ini juga: jalur datanya tidak ada (§C: order book L2, tick, `TIDAK-ADA`) dan
kompetitornya adalah meja dengan colocate. Untuk Fabius, tidak ada satu pun kalimat di atas yang
boleh dibaca sebagai kemampuan.

### Hubungan yang tidak kami cari, tapi dapat

- Venue eksekusi kami adalah **pool konstanta-produk dengan fee 30 bps**; likuiditasnya dipasang
  sendiri lewat `bootstrap()`, dan setelah itu tidak bisa digeser dari luar
  ([[02-Contracts/C4 - DemoPair and DemoAsset]]).
- Ongkos round-trip satu unit di sana **terukur 59 bps** (§D) dan eksekusi nyata di chain testnet
  menghasilkan **−59 bps** per putaran (§D/§F) — prediksi dan kenyataan dikunci oleh dua angka yang
  sama.
- Artinya: kurva x·y=k adalah **kita yang menjadi LP**. Kami tidak mengambil spread; kami
  menyediakan harga yang diambil. Bagian spread yang kami bayar (59 bps) adalah pendapatan meja di
  sisi sebaliknya, dan kerugian karena harga bergerak setelah diisi adalah penyakit adverse
  selection yang sama, hanya dibaca dari sisi penyedia likuiditas.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| order book L2 (bid/ask terpasang) | `TIDAK-ADA` | §C — tanpa book, "spread yang dikutip" tidak pernah terdefinisi untuk kami |
| tick / waktu antar-fill (markout) | `TIDAK-ADA` | §C; bar 1 jam tidak bisa menjawab "apa yang terjadi 200 ms setelah fill" |
| latency & penempatan order | `TIDAK-ADA` | tidak ada jalur order-placement di repo ini; venue kami hanya menerima swap langsung ke kurva |
| arus fill di pool kami sendiri | `ADA` | event `Closed` di jejak eksekusi membaca realized −59 bps (§D) |
| skor "maker mana yang menambah informasi" | `ADA-TAPI` | `tools/maker_ledger.py` ada dan bekerja dari rekaman ⑦, tapi distribusinya belum masuk akal (§H: median 4.558,3 bps, 71 % lot > 2000 bps, maks 1.222.045,4) → angkanya **tidak boleh dikutip** |

## Uji di Fabius

Tidak ada uji market-making di repo ini. Yang ada baru dua hal: (a) pengukuran ongkos di venue
sendiri (§D) dan (b) alat yang merekonstruksi lot dari aliran dompet (§H, belum beres mekanikanya).
Bentuk uji yang sah, kalau suatu saat ada book: kutip dua sisi, catat setiap fill dengan waktu, lalu
laporkan **markout** 1 s / 1 m / 1 j per fill sebelum melaporkan PnL apa pun — karena PnL tanpa
markout hanya membuktikan spread pernah ada. Ambang yang tetap berlaku: `n >= 20` non-overlap,
BH α 0,10, fold terbaik dibuang, ongkos nyata (§E).

## Batas dan mode gagal

- **Menyediakan likuiditas di pool = short gamma.** Kita kehilangan saat harga bergerak cepat
  melawan, dan itu bukan peristiwa langka di memecoin BSC.
- **Tebakan spread tanpa book.** Histogram bar 1 jam bukan "order book"; menjualnya sebagai
  microstructure adalah salah label.
- **Risiko satu-satunya LP.** Pool kami di-bootstrap sekali dan tidak ada pihak lain yang bisa
  menggeser likuiditas (C4) — praktis: tidak ada lawan transaksi yang bisa disalahkan, dan tidak
  ada volume organik yang bisa diharapkan.
- **Alat yang angkanya belum waras** (§H) adalah pengingat terbaik bahwa mekanika (satuan harga,
  arti `is_open_or_close`, MTM token) lebih dulu menentukan daripada interpretasi hasil.

## Tingkat bukti

`T1` untuk kerangka spread/adverse-selection/inventory (pengetahuan standar pasar) · `T2` untuk
Avellaneda–Stoikov sebagai rujukan yang tidak kami reproduksi · yang terukur di sini hanya **ongkos**
(**59 bps**, §D), bukan uji metode MM — jadi tidak ada `T3` untuk catatan ini.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "Fabius bukan market maker; ia taker di pool x·y=k miliknya sendiri, dan ia mengukur
  bahwa menjadi taker di sana berbiaya 59 bps round-trip."
- **Dilarang:** "kami menyediakan likuiditas" · "bot MM kami" · "spread 30 bps = margin kami" ·
  mengutip angka `tools/maker_ledger.py` sebagai hasil (§H: itu laporan alat yang sedang rusak).

**Terkait:** [[QT5 - Statistical Arbitrage dan Pairs Trading]] · [[QT10 - Eksekusi Algoritmik]] ·
[[V4 - Order Book dan Liquidity Heatmap]] · [[V5 - Mikrostruktur Spread dan Adverse Selection]] ·
[[FD3 - Likuiditas dan Dampak Harga]] · [[02-Contracts/C4 - DemoPair and DemoAsset]]
