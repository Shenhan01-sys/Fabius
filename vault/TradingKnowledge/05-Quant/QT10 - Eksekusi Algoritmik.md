---
tags: [tk, tk-quant, "QT10"]
---

# QT10 - Eksekusi Algoritmik

**Keluarga:** [[00 - Hub Quant]] · **Tahap:** eksekusi ([[PL5 - Mengeksekusi dan Keluar]])
**Sumber:** `vault/TradingKnowledge/QuantTrading/Info1.txt` §"Komponen Utama Quant Trading"
(Eksekusi/Infrastructure) — daftar topik · pagar nyata: [[Fakta Terukur]] §C/§D/§E/§F,
`tools/direction.py`, `tools/security_gate.py`

**Ringkas:** eksekusi algoritmik adalah ilmu memecah perintah besar supaya tidak menghancurkan harga
tempat ia ingin keluar. Untuk notional sebesar Fabius, sebagian besar ilmunya tidak relevan — dan
sebagian kecilnya justru menentukan: batas kapasitas keluar. Bedanya sederhana: kami tidak butuh
penjadwalan karena perintah kami kecil; kami tetap butuh membuktikan bahwa perintah itu bisa
**dibalik**, karena satu-satunya kerugian yang sudah kami ukur di rantai adalah ongkos, bukan arah.

## Definisi yang bisa dihitung

```
participation := notional_order / notional_likuid_tersedia      # makin tinggi, makin bocor & makin dalam dampak
exit_cap      := ukuran maksimum yang masih bisa keluar tanpa mengubah hasil secara material
slippage(q)   := harga_rata_rata(q) - harga_acuan              # fungsi dari q, bukan konstanta
```

Empat teknik penjadwalan yang jadi pengetahuan standar pasar — **tidak** kami pasang dan tidak kami
perlukan pada ukuran kami:

| teknik | yang dikerjakan | risiko yang dibelinya |
|---|---|---|
| TWAP | pecah rata menurut waktu | mudah dikenali; tidak peduli pada likuiditas |
| VWAP | pecah mengikuti profil volum | butuh profil volum yang benar (punya kami hanya bar 1 jam, belum pernah dipakai) |
| iceberg | bagian kecil order tampil di book | butuh book & urutan antrean — `TIDAK-ADA` (§C) |
| smart order routing | cari harga terbaik antar-venue | butuh beberapa venue hidup; jalur CEX kami mati/terpotong (§C) |

## Cara pakai yang diklaim

Klaim pemilik praktik (vendor eksekusi, desks institusi): penjadwalan menurunkan biaya dan kebocoran
informasi. Itu benar pada ukuran yang dampaknya nyata. Pada ukuran kami yang terdokumentasi justru
dua angka yang saling mengunci: satu round-trip **1 unit** di venue kami berbiaya **59 bps** terukur
(§D), dan tiga putaran nyata di chain testnet menghasilkan rata-rata **−59 bps** dengan win rate 0 %
(§D/§F) — angka itu **ongkos**, bukan sinyal. Menjadwalkan perintah seharga satu unit hanya menambah
jejak dan biaya.

Pagar yang benar-benar terpasang di Fabius, bukan wacana:

| pagar | nilai | asal |
|---|---|---|
| plafon quotes per posisi | `maxPositionQuote` 1 unit | [[Fakta Terukur]] §E |
| cap harian | `dailyCap` default 5 unit | §E |
| plafon keras | `HARD_CEILING = 10` — perintah di atasnya **dipotong**, bukan dilayani; `killSwitch` | §E |
| kapasitas keluar | gerbang ⑥ dengan `MIN_LIQ_USD` 50.000 (§E) + field `exit_cap_1pct_liq_usd` yang ikut keputusan (`tools/direction.py`) | kode |

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| harga acuan dari kontrak, bukan dari kami | `ADA` | venue demo x·y=k; `costOfBuy`/`spotPrice` dipakai memprediksi dampak sebelum masuk ([[02-Contracts/C4 - DemoPair and DemoAsset]]) |
| likuiditas pool untuk menghitung kapasitas keluar | `ADA` | GeckoTerminal/DexScreener (§A/§C) + gerbang ⑥ (§E) |
| bisa **menjual** sama sekali (honeypot / `can_not_sell`) | `ADA-TAPI` | `tools/security_gate.py`; terukur 5/5 kandidat membalas — 4 `OK` + 1 `UNMEASURED` (`is_honeypot=None` tidak dihitung bersih) — §F |
| book L2 / antrean order untuk iceberg | `TIDAK-ADA` | §C |
| multi-venue untuk routing | `MATI-DARI-MESIN-INI` | `api.binance.com` 451 dan Bybit 403 di runner; OKX/Bitget hidup di runner tapi terpotong TLS di laptop (§C) |
| gas sebagai bagian biaya nyata | `ADA-TAPI` | 0,10 gwei live di testnet 97; guard lama memakai floor 1 gwei → menolak karena plafon sendiri (§D) — di mainnet angkanya lain dan **belum diukur** |

## Uji di Fabius

Yang bisa dijalankan dari clone dan sudah pernah memproduksi angka:

```
python -X utf8 tools/winlog.py            # siapa yang menutup posisi, dengan ongkos realized
python -X utf8 tools/anchor.py --verify   # prediksi kami benar-benar ada sebelum hasilnya tiba
```

Yang dibutuhkan untuk menutup lubang kapasitas keluar secara kuantitatif: satu laporan yang
membandingkan `exit_cap` tiap kandidat dengan **hasil** trade-nya, supaya ambang 50.000 USD (§E)
diuji, bukan dipertahankan ([[GAP2 - Uji Setiap Veto Terhadap Hasil]]). Bentuknya tetap sama:
`n >= 20` non-overlap, BH α 0,10, net setelah ongkos nyata (§E).

## Batas dan mode gagal

- **Keluar lebih sulit daripada masuk**, dan di memecoin BSC penolakan jual (honeypot, `can_sell`
  false, pajak jual) adalah risiko utama — itu sebabnya ④ ikut menentukan kursi (§F).
- **Ongkos tetap tidak ikut menyusut bersama ukuran**: pada $1, ongkos tetap $0,05 bolak-balik
  menuntut +5 % hanya untuk balik modal — dan tabel itu estimasi mainnet, **belum diukur di repo ini** (§D).
- **Penjadwalan tidak gratis**: TWAP menambah jejak dan waktu terpapar; pada horizon 4 jam, menunda
  masuk = mengubah posisi yang dijanjikan.
- **Dampak di pool x·y=k bersifat deterministik**: tidak ada "fill sebagian" yang bisa
  disalahartikan sebagai eksekusi jelek — kurva memberi harganya, dan 59 bps itu konsekuensi,
  bukan kegagalan.
- Jangan membaca `HARD_CEILING` sebagai fitur risiko penuh: dia memotong **perintah**, jadi ia juga
  bisa memotong niat yang benar.

## Tingkat bukti

`T1` untuk TWAP/VWAP/iceberg/SOR dan participation rate (pengetahuan standar, tidak kami pasang) ·
`T3` hanya untuk angka §F: rata-rata **−59,0 bps** pada tiga putaran nyata (win rate 0 %) · ongkos
**59 bps** (§D) adalah hasil `forge test` di venue kami sendiri · `T0` untuk slippage pasar nyata.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "notional Fabius terlalu kecil untuk penjadwalan order; yang kami pasang adalah plafon
  kontrak, batas ukuran, dan gerbang kapasitas keluar — dan biaya nyata dari memutar posisi di venue
  kami sudah terukur."
- **Dilarang:** "kami punya smart order routing" · "59 bps adalah slippage market" · "TWAP kami
  menurunkan biaya" · "likuiditas pool = kami bisa keluar kapan pun" (belum dibuktikan per token).

**Terkait:** [[QT7 - Market Making]] · [[FD3 - Likuiditas dan Dampak Harga]] ·
[[FD4 - Ongkos Perdagangan]] · [[FD6 - Ukuran Posisi]] · [[O8 - MEV dan Sandwich]] ·
[[02-Contracts/C3 - ExecutionVault]]
