---
tags: [tk, tk-quant, "QT6"]
---

# QT6 - Funding dan Basis Arbitrage

**Keluarga:** [[00 - Hub Quant]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/QuantTrading/Info1.txt` §"Strategi Quant yang Populer di
Crypto" (daftar topik) · angka snapshot: [[Fakta Terukur]] §A · ambang: `tools/direction.py` /
[[Fakta Terukur]] §E

**Ringkas:** cash-and-carry = beli spot, jual kontrak perp dengan ukuran sama, dan biarkan delta
netral; pendapatannya adalah funding yang dibayar pihak long, dikurangi ongkos empat kaki. Ini satu
-satunya jalur "yield" di crypto yang **bukan** janji arah harga — dan justru karena itu ia punya
syarat yang keras: dua kaki yang bisa dieksekusi bersamaan, margin yang tidak dipaksa tutup, dan
pihak lawan yang tidak kabur. Fabius hari ini membaca funding, memakai sebagai **penolakan**, dan
tidak punya satu pun syarat eksekusi di atas. Angka di catatan ini adalah besaran, bukan prospek.

## Definisi yang bisa dihitung

```
basis_t      := harga_perp_t - harga_spot_t                (atau rasio, dinyatakan bps)
carry_per_4h := funding_4h_pct   (long membayar kalau positif)
net_carry    := carry - ongkos_empat_kaki - biaya_pinjam - premi_margin
delta_netral := |notional_perp| ~= |notional_spot|  dan  tidak ada korelasi tersisa
```

Funding sebagai **dua hal berbeda** yang sering dicampur:

| sebagai | berarti | dipakai di Fabius sebagai |
|---|---|---|
| yield | sisi long membayar sisi short saat kontrak premium | **tidak dipakai sebagai yield** — tidak ada jalur eksekusinya |
| biaya | posisi long di aset yang premium membayar terus | gerbang: `\|funding\| > 0,05 %/4 jam` → **tolak posisi** (`tools/direction.py`, §A) |
| sinyal kerumunan | funding ekstrem = sisi yang sama berdesakan | dipakai hanya sebagai alasan menolak, bukan memilih arah |

Besaran terukur **satu pembacaan pada satu waktu** (§A, funding per 4 jam): BNB `+0,0000 %`
(mark 778,45 · OI 7.832) · ETH `+0,0100 %` · SOL `−0,0020 %` · HYPE `−0,0018 %` · DOGE `+0,0044 %`.
Rentang lintas aset yang terbaca: −0,0020 … +0,0100 % per 4 jam. Aritmetika lugasnya: ETH
+0,0100 %/interval × 6 interval/hari ≈ 0,06 %/hari — **kalau** interval itu berulang, dan itu tidak
bisa kami periksa: histori funding per aset kini `ADA-TAPI` (Bybit 66,3 hari per 8 jam, §A.5) - resolusinya 8 jam, sementara horizon uji kami 1 j dan 4 j. Angka
+0,06 %/hari bukan yield yang bisa dijanjikan; dia contoh satuan, bukan prospek.

Pembanding silang: Hyperliquid membalas BNB `0,004781 %/jam` dengan OI 65.047 (§A). Intervalnya
berbeda (per jam vs per 4 jam) — mengalikannya dengan 4 hanyalah konversi satuan, dan dua venue
mengukur basis yang tidak identik, jadi kedua angka itu **tidak** boleh dibaca sebagai selisih.

## Cara pakai yang diklaim

Klaim pemilik praktik (pedagang derivatif dan penerbit dana basis trade): carry yang stabil saat
basis positif, dengan risiko utama pada margin/depeg, bukan pada harga. Di BNB Chain narasi yang
sama dijual sebagai "yield tanpa arah". Yang kami setujui hanya definisinya; tidak ada satu pun
run di repo ini yang menghasilkan angka carry teruji.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| funding + OI terkini, lintas aset | `ADA` | Aster `premiumIndex`/`openInterest` 608 kontrak; Hyperliquid 234 perp — §A |
| histori funding per aset | `ADA` (di repo sendiri) | `universe/funding-history.jsonl`: Bybit **66,3 hari** dan OKX **97,7 hari**, keduanya **interval 8 jam**, tanpa kunci — [[Fakta Terukur]] §A.5 (laptop, belum runner). Uji surut carry jadi mungkin pada horison harian; **tidak** pada fitur per-bar 1 j/4 j, jadi §F masih benar soal gerbang carry-nya — yang berubah cuma ambang "bisa diuji apa tidak" |
| harga spot kaki pertama | `ADA-TAPI` | GeckoTerminal/DexScreener memberi likuiditas & deret pendek (§A/§C), bukan buku order |
| eksekusi dua kaki bersamaan | `TIDAK-ADA` | jalur eksekusi kami satu kaki, spot, di pool demo ([[02-Contracts/C4 - DemoPair and DemoAsset]]) |
| margin/likuidasi di venue pihak ketiga | `TIDAK-ADA` | tidak ada akun, tidak ada batas, tidak ada angka — *(belum diukur)* |
| ongkos empat kaki | `TIDAK-ADA` | yang terukur satu round-trip **59 bps** di venue kami (§D); empat kaki belum pernah dihitung |

## Uji di Fabius

Yang **sudah** jalan: funding sebagai gerbang pengurang, bukan sebagai strategi — `tools/direction.py`
menolak posisi saat `|funding|` ekstrem, dan gerbang itu ikut masuk ke keputusan yang di-hash
([[01-Agent/A3 - One-Way Gates]]). Karena itu satu-satunya klaim sah tentang funding di repo ini
berbunyi "kami menolak", bukan "kami memanen".

Yang belum dan bentuknya harus begini: sebuah alat yang mengambil satu pembacaan funding, mengikat
kedua kaki di ukuran yang sama, lalu menilai `net_carry` setelah ongkos nyata — **pra-registrasi
dulu** (`vault/06-Results/05 - Pre-registration Flow.md`), `n >= 20` non-overlap, BH α 0,10,
fold terbaik dibuang (§E). Perintahnya: `tools/carry_study.py` — **belum ditulis**, dan ia juga
butuh jalur data funding historis yang tidak ada (§C).

## Batas dan mode gagal

- **Funding flip.** Carry hari ini adalah biaya besok; tanpa histori, "stabil" adalah tebakan.
- **Basis bisa terlepas tanpa harga bergerak** — dua kaki bisa rugi di saat yang sama kalau
  likuiditas kaki spot mengering ([[FD3 - Likuiditas dan Dampak Harga]]).
- **Risiko depeg** pada kaki "stabil": stablecoin bukan uang bebas risiko, dan universe kami
  menolak basis stabil sebagai kandidat justru karena itu likuiditas, bukan aset
  (`STABLE_BASES`, `vault/06-Results/02 - Thresholds.md`).
- **Risiko venue**: dana di pihak ketiga, margin dipaksa tutup, penarikan ditunda. Tidak ada angka
  untuk ini di repo ini *(belum diukur)* dan tidak boleh ditulis sebagai "termitigasi".
- **Gerbang funding kami belum diuji terhadap hasil** — ia diputuskan, bukan dikalibrasi (§E,
  [[GAP2 - Uji Setiap Veto Terhadap Hasil]]).

## Tingkat bukti

`T1` untuk kerangka cash-and-carry/basis (pengetahuan standar pasar) · **belum diuji sebagai
strategi** di repo ini, dan tidak ada angka §F untuk jalur carry · `T0` untuk setiap kalimat yang
menyebut yield yang bisa kami panen. Yang terukur hanyalah **datanya**: pembacaan funding §A dan
gerbang yang memakainya (§E) — data tersedia bukan bukti metode.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami bisa melihat funding 4-jam di 608 kontrak BNB-native dan memakainya untuk
  menolak posisi; histori funding baru ±66 hari dan per 8 jam (§A.5), jadi uji surut carry hanya
  mungkin pada horison harian - dan dua kaki tetap tidak punya jalur eksekusi di repo ini."
- **Dilarang:** "Fabius menghasilkan yield dari funding" · kalimat penjual "+X % per hari" tanpa
  *kalau* (bukan angka kami, dan tidak pernah kami ukur) · "delta-netral berarti tanpa risiko" ·
  menyamakan pembacaan per-jam Hyperliquid dengan pembacaan per-4-jam Aster.

**Terkait:** [[QT5 - Statistical Arbitrage dan Pairs Trading]] · [[QT12 - Stack Data dan Perkakas]] ·
[[U2 - Funding Rate dan Basis]] · [[FD4 - Ongkos Perdagangan]] ·
[[01-Agent/A3 - One-Way Gates]] · [[U1 - Open Interest]]
