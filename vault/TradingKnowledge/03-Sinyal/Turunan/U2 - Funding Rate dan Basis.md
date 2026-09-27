---
tags: [tk, tk-sinyal, "U2"]
---

# U2 - Funding Rate dan Basis

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** keputusan ([[PL4 - Memutuskan]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"3. CONFIRMATION LAYER" (Futures-Specific: "Funding
Rate") + §"3. Strategi Berbasis On-Chain & Data Crypto Spesifik" ("Funding Rate Arbitrage & Basis
Trading") — klaim komunitas

**Ringkas:** Funding adalah pembayaran berkala antar pemegang perp untuk menarik harga perp ke
harga spot: yang menang bayar yang kalah. Basis = selisih harga perp terhadap spot. Ini keluarga
turunan yang **sudah wired sebagai gerbang di jalur arah** (`tools/direction.py`) — dan justru karena
itu batasnya harus ditulis telanjang: gerbangnya belum ikut teruji, karena histori
funding per aset tidak bisa kami tarik mundur.

## Definisi yang bisa dihitung

```
basis(t)        = (P_perp - P_spot) / P_spot                 # mark vs indeks
funding_rate(t) ≈ fungsi monotonaik dari premium (basis), dengan cap + smoothing
                  # rumus-persisnya milik venue; kami membaca hasil akhirnya (`lastFundingRate`)
biaya_carry     = nilai_posisi × funding_rate × jumlah_interval_tertahan
annualisasi_kasar ≈ funding_per_interval × interval_per_tahun   # aritmetika, bukan model
# cash-and-carry (basis trade): long spot + short perp dengan ukuran sama
#   -> netral arah, menerima funding; risikonya bukan arah tapi: likuidasi kaki perp,
#      ongkos masuk-keluar, dan funding yang berbalik tanda saat posisi sudah terbuka.
```

## Cara pakai yang diklaim

Klaim komunitas: funding positif besar = kerumunan long (bahan squeeze ke atas), funding negatif
ekstrem = kerumunan short (bahan squeeze ke bawah); basis tinggi = harga "terlalu mahal terhadap
spot"; carry trade = "edge bebas risiko". Yang terakhir itu perlu dikoreksi dengan angka kami
sendiri: pada biaya round-trip **59 bps** (§D), dua putaran memakan 59 bps, sementara funding
0,0100 %/4 jam (§A, ETH pada tanggal baca) = 10 bps per kaki 4 jam. "Bebas risiko" dalam arti
"netral arah", bukan "netral terhadap ongkos dan eksekusi".

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| funding **saat ini** per kontrak perp | `ADA` | Aster `premiumIndex` untuk 608 kontrak; bacaan §A: BNB +0,0000 % · ETH +0,0100 % · SOL −0,0020 % · HYPE −0,0018 % · DOGE +0,0044 % per **4 jam** |
| periode funding | `ADA-TAPI` | 4 jam di Aster (§A); Hyperliquid membalas per jam (BNB 0,004781 %/jam) — dua venue, dua periodisitas: menggabungkannya dalam satu kolom deret = salah (§C) |
| histori funding per aset | `TIDAK-ADA` | disebut eksplisit di [[Fakta Terukur]] §C: "histori funding per-aset yang bisa ditarik mundur" tidak kami punya |
| harga spot/indeks untuk menghitung basis sendiri | `TIDAK-ADA` | yang kami punya harga perp (kline) dan `markPrice`; indeks resmi venue tidak direkam |
| gerbang keputusan yang memakainya | `ADA` | `tools/direction.py`: `\|funding\|` > 0,05 %/4 jam → tolak posisi, karena biayanya lebih besar dari edge yang kami klaim (§A) |
| funding venue lain untuk kontrol silang | `MATI-DARI-MESIN-INI` | OKX funding membalas `200` di runner tapi **terpotong TLS di laptop** (§C) |

## Uji di Fabius

Yang **sudah** wired tapi belum teruji, dan ini ditulis di kodenya sendiri: docstring
`tools/backtest.py` menyatakan "funding historic tidak ada di jalur ini → gerbang funding ekstrem
live tidak ikut diuji". Jadi hasil **12/12 rugi** (§F) adalah vonis untuk aturan **harga**
(SMA/ret24 + gerbang `|acf|`), bukan untuk gerbang funding. Untuk menaikkan U2 ke `T3` dibutuhkan:
(1) perekaman `premiumIndex` per (simbol, interval) sebagai deret sendiri — tidak bisa disusulkan,
sama seperti ⑦ (§B); (2) uji ulang aturan arah dengan gerbang funding ikut bekerja, ambang tidak
di-fit, `n >= 20` non-overlap, gross di atas 59 bps, drop-best-fold, BH α 0,10 (§D/§E);
(3) baru setelah itu carry trade layak disebut strategi — bentuk uji dan risiko kakinya ada di
[[QT6 - Funding dan Basis Arbitrage]].

## Batas dan mode gagal

- **Funding mengukur biaya, bukan arah.** Tanda funding memberi tahu siapa membayar; ia tidak
  memberi tahu siapa yang benar. Kerumunan yang salah arah bisa tetap salah arah sambil membayar
  selama berhari-hari.
- **Ambang 0,05 %/4 jam = 5 bps per kaki 4 jam ≈ 30 bps per hari** (aritmetika dari §A/§E). Pada
  ongkos nyata 59 bps, aturan itu menahan posisi yang hold-nya lebih mahal dari putaran — itu
  alasan gerbangnya ada, bukan alasan dia memprediksi hasil.
- **Funding ekstrem adalah hasil dari leverage yang sama yang belum kami ukur**
  ([[U1 - Open Interest]], [[U3 - Level Likuidasi dan Cascade]]).
- **Periode berbeda, deret berbeda.** 4 jam dan 1 jam bukan cuma beda skala: dua-duanya hidup di
  daftar sumber yang sama tapi tidak bisa mengisi kolom yang sama di tengah deret (aturan §C).
- Carry trade menuntut dua kaki dieksekusi di ukuran yang sama; kapasitas keluar kita dibatasi
  `exit-size <= 1 % liq` ([[01-Agent/01 - Asset Classes and Seats]] §3) — *(belum diukur untuk dua kaki)*.

## Tingkat bukti

`T1` untuk mekanisme funding/basis (standar produk derivatif) · `T0` untuk "funding ekstrem
memprediksi reversal" · **tidak ada `T3` di keluarga ini**: yang teruji di repo ini hanya aturan
harga, dan hasilnya negatif 12/12 (§F) — gerbang funding tidak ikut diuji karena historinya tidak
ada. Status gerbang carry: **ADA tapi belum diuji** — bukan lolos, bukan gagal: belum.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "Fabius menolak kandidat yang funding-nya di atas 0,05 %/4 jam karena biaya carry
  melampaui edge yang kami klaim; gerbang ini belum pernah diuji terhadap hasil karena histori
  funding tidak ada."
- **Dilarang:** "hasil 12/12 menguji seluruh aturan agen" (funding tidak ikut) · "funding tinggi =
  pasar akan turun" · "carry trade bebas risiko" · menyebut basis belum dihitung padahal indeks
  spot tidak kami rekam.

**Terkait:** [[U1 - Open Interest]] · [[U3 - Level Likuidasi dan Cascade]] ·
[[U4 - Long-Short Ratio dan Skew Posisi]] · [[QT6 - Funding dan Basis Arbitrage]] ·
[[FD4 - Ongkos Perdagangan]] · [[04-Tools/TL2 - direction]]
