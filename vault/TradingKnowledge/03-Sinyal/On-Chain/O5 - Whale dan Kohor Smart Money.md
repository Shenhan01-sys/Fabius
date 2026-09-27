---
tags: [tk, tk-sinyal, "O5"]
---

# O5 - Whale dan Kohor Smart Money

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** yang kami rekam sendiri — `universe/record_wallet_flow.py`, `tools/flow_signal.py`,
`tools/whale_cohorts.py`, `tools/maker_ledger.py`, `tools/maker_audit.py`, `tools/smartmoney_score.py`,
`tools/whale_sweep.py`, `tools/whale_report.py` · topik "Whale Wallet Tracking" dari
`vault/TradingKnowledge/Plan.txt` §"Strategi Berbasis On-Chain & Data Crypto Spesifik"

**Ringkas:** dua ide berbeda yang selalu dijual sebagai satu barang. **"Whale" adalah ukuran** —
transaksi di atas ambang; terdefinisikan tanpa opini, tidak membawa informasi arah. **"Smart money"
adalah riwayat** — dompet yang dinilai pernah benar; tiap definisi "benar" dibuat **setelah** hasilnya
diketahui. Karena itu halaman ini sebagian besar berisi larangan: satu-satunya klaim yang sudah kami
uji di data sendiri (mengikuti arah panel pada horizon jam) **terukur dan hasilnya melawan klaimnya** (§F).

## Definisi yang bisa dihitung

```
whale_tx(t, q)     = 1 jika amount_usd(t) >= kuantil-q dari distribusi amount_usd di kolam yang sama
kohor_c(t)         = himpunan maker yang **dinyatakan** anggota sebelum t, oleh aturan yang bisa dihitung ulang
net_bps(m)         = (nilai keluar − nilai masuk) / nilai masuk × 1e4 , dikurangi ongkos round-trip
kohor_per_kolam    = graf ko-occurrence maker↔token; dua token satu kolam jika >= MIN_EDGE maker sama
HHI(m)             = Σ_simbol (gross_usd(m,simbol) / gross_usd(m))²     # 1 = satu kolam, kecil = serba-macam
```

`MIN_EDGE` adalah konstanta di `tools/maker_ledger.py` (dibaca dari kode, bukan hasil ukur). Bedanya
wajib dijaga: `whale_tx` terhitung dari blok; `kohor_c` tidak — itu keputusan pembuat panel.

## Cara pakai yang diklaim

Diklaim oleh terminal kripto dan vendor panel (di proyek ini label `smartmoney`/`kol` dari GMGN,
disimpan apa adanya di field `g` tiap baris aliran, §B): pantau dompet yang benar, salin arahnya;
klaim turunannya — "mereka swing, bukan scalping" — dipakai menjelaskan kenapa hasil jangka pendeknya
jelek. Tidak ada vendor yang menerbitkan **definisi** keanggotaan panelnya, tanggal penetapan tiap
anggota, atau invalidasi; tanpa tiga hal itu "smart money" adalah merek, bukan metode.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| aliran dompet berlabel, point-in-time | `ADA` | §B: 100 transaksi/panggilan, jendela lihat 8–13 menit; run `94aead6` **18:21:16Z**: 50.285 baris · 21.907 tx · 452 maker · 1.590 token · rentang 34,33 jam (ekor terbaru lebih besar — §B menyimpan keduanya, dan keduanya basi dalam menit); **riwayat tidak bisa ditarik** (paging diabaikan) |
| kontrol "dompet biasa" dari sumber yang sama | `TIDAK-ADA` | **0 dari 607** transaksi pertama tidak bertag (0,0 %) — populasinya memang didefinisikan sebagai "yang sudah dilabeli" (§B) |
| harga forward untuk menilai hasil | `ADA` | Aster 9.599 bar ≈ 400 hari; baris `px` kami sendiri (§A/§B) |
| skor maker yang bisa dipercaya | `TIDAK-ADA` | `tools/maker_ledger.py` ada, angkanya diblokir §H |
| sejarah 90 hari panel (Uji B) | `ADA-TAPI` | `tools/whale_sweep.py` via Dune — lookahead **tidak bisa dibuang** |

## Uji di Fabius

1. Pembanding = **arah acak pada token dan jam yang sama**; hold **4 jam** dari baris `px` kami;
   **pisahkan `is_open_or_close=1` vs `=0`** — tiga kontrol yang di §B dinyatakan sebagai satu-satunya
   yang boleh dipakai (bukan "lebih baik dari trader biasa", yang mustahil tanpa kontrol).
2. Satu sampel per (wallet, token, jendela tak tumpang-tindih), `n >= 20` per wallet, BH α 0,10
   **lintas wallet**, fold terbaik dibuang, gross di atas **59 bps** (§D — bukan 20 bps asumsi).
3. Keanggotaan dicatat dengan timestamp. `tools/flow_signal.py` memisahkan aliran semua maker, maker
   bertag, dan tak bertag, dan menolak menyebut yang kedua "prediktif"; yang tidak tampak di jendela
   ditulis **TAK ADA DATA**, bukan nol atau netral ([[Concepts/Unmeasured Is Not Clean]]).

**Yang sudah terukur** (§F): panel pada horison per jam punya **win rate 69,8 % tapi −10,4 bps per
jam** — menang sering, kalah lebih mahal: mengejar dompet bukan mengejar expectancy
([[FD5 - Expectancy Bukan Win Rate]]).

**Yang belum boleh dikutip sebagai temuan (§H):** struktural `tools/whale_cohorts.py` (median **2
maker/simbol**, **49,8 %** simbol cuma punya 1 maker, HHI median **0,347**) — dilaporkan sebagai
*breadth*, kokohnya belum diuji terhadap hasil; skor `tools/maker_ledger.py` (median `|net|`
**4.558,3 bps**, 71 % lot > 2000 bps, maks **1.222.045,4**) — mekanikanya belum beres; artefak
`decisions/whale-sweep-90d.json` dengan `cost_bps_applied = 0.0` (semua angka horison di sana GROSS)
dan `p_boot` identik di 4 horison yang belum terjelaskan. Verifikasi-ulang: `tools/whale_report.py`
dan `tools/maker_audit.py`.

## Batas dan mode gagal

- **Ukuran dicampur riwayat.** Transfer besar bisa berasal dari kas internal, custodian, atau bot yang
  berputar; dompet "pintar" bisa saja sekadar besar. Menyebut keduanya "whale" = mengira ia sudah tahu.
- **Kohor harus per-kolam — dan kolam kami rapuh.** Dompet yang benar di BTC tidak punya hak bicara di
  memecoin BSC. Arah strukturalnya sudah kami ukur (`tools/whale_cohorts.py`), tapi angkanya
  §H-blocked: yang boleh dikatakan baru **indikasi** bahwa cohort per-aset tidak akan punya cukup
  maker — pengukuran yang belum kami sertifikatkan, bukan opini.
- **Panel = pilihan retroaktif vendor → `TERCEMAR`.** Koreksinya satu arah: label yang diberikan
  setelah sejarah terjadi hanya bisa membuat sejarah itu terlihat lebih baik
  ([[Concepts/Lookahead Bound]]). Karena itu hasil positif pada horison panjang di
  [[06-Results/06 - Pre-registration Horizon]] tidak dijual sebagai edge; Uji A (prospektif) yang
  menentukan, dan datanya belum matang.
- **Alat skor kami sendiri belum bisa dipercaya**, dan sebabnya diketahui: §H merinci mekanikanya
  (satuan harga, arti `is_open_or_close`, mark-to-market token yang hilang, lot terbuka tak dinilai).
  Membaca angkanya sebagai "maker kami cuan" adalah klaim palsu.
- **Survivorship dan duplikasi.** Yang bisa kami hargai sendiri hanya token yang punya kontrak perp —
  yang selamat (lihat halaman pra-registrasi tadi). Memakai panel ini sebagai konfirmasi cerita
  "institusi meninggalkan jejak" di [[S4 - Order Block dan Breaker]] = menyamakan dua hal berbeda.

## Tingkat bukti

`T3` + **NEGATIF** untuk "mengikuti arah panel pada horizon jam" (sudah diuji di data kami sendiri,
hasilnya melawan klaimnya — §F) · `TERCEMAR` untuk angka panel di horison panjang (anggota dipilih
setelah sejarahnya ada) · `T1` definisi whale/kohor · `T0` klaim vendor "smart money profitable" ·
`maker_ledger.py`/`whale_cohorts.py`: angkanya **belum boleh dipakai sebagai temuan** (§H).

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami merekam aliran dompet berlabel secara point-in-time, punya satu hasil uji yang negatif
  yang bisa diulang (69,8 % menang, −10,4 bps/jam), dan penilai maker kami sedang rusak karena sebab
  yang kami ketahui."
- **Dilarang:** "kami menemukan whale yang menguntungkan" · "smart money menang di 30 hari" (angka
  §H/gross + lookahead) · "Fabius menyalin arah whale" · "452 maker = 452 orang yang benar".

**Terkait:** [[S4 - Order Block dan Breaker]] · [[V5 - Mikrostruktur Spread dan Adverse Selection]] ·
[[FD5 - Expectancy Bukan Win Rate]] · [[GAP3 - Yang Punya Data Tapi Belum Diuji]] · [[PL3 - Menganalisis]]
