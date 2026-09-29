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
   **Sebagian sudah dijalankan 28 Sep:** `tools/flow_cluster_test.py` memakai pembanding K=1 +
   "cuaca" (semua `px→px` pada token yang sama). Hasilnya: **kerumunan tidak memisahkan**
   (K≥2 39,3 % vs K=1 39,5 % posisi positif; K≥5 50 % pada n=24, p=0,58) → **0 lolos BH**;
   `is_open_or_close` memang tidak ditentukan oleh sisi, jadi ia tidak dipakai sebagai penanda
   pembukaan. Yang menahan kesimpulan: **80,6 %** kandidat tidak punya harga keluar
   ([[06-Results/09 - Whale Cluster Test]]) — kolaborasi diuji hanya pada yang akhirnya masih kelihatan.
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

## 29 Sep 20:26Z - "banyak dompet beli bersamaan" akhirnya diuji prospectif, dan tiga kali gagal

Halaman ini lama memperlakukan kerumunan maker (≥2 dompet berbeda membeli dalam satu jendela) sebagai
sinyal yang "tinggal dieksekusi". malam ini pernyataan itu tidak bisa dipertahankan:

| pembacaan | sumber harga | hasil |
|---|---|---|
| in-sample 28 Sep (`evidence_stack`) | ticker `px` (harga transaksi terakhir yang kami tarik) | `cluster_ge2` **+393,4**, `money_spread` **+552,7** - lulus BH |
| decomposisi 28 Sep (`entry_decomposition`) | harga **peristiwa** (`tx.p`) | **+0,1 CI [−14; +198] p=0,53** → nol; `--px txevent` malah **−491,4** |
| replikasi 28 Sep 21:24Z (halaman 11, terkunci) | ticker | `uji_primer`/`uji_kedua` **SAMPEL TIDAK CUKUP**, `stack≥2` GAGAL di CI |
| replikasi 28 Sep 21:45Z (halaman 12, terkunci) | harga peristiwa | `uji_primer` median **−1.518,5**, arahnya **terbalik** |
| **replikasi 29 Sep 20:26Z (halaman 17, terkunci)** | harga peristiwa, n=**156** | median **−21,3 bps**, CI [−543,9; +2,8], p=**0,936** → **GAGAL**; `money_spread` n=123 median 0,0 p=0,706 → **GAGAL** |

**Yang berubah bukan "sinyalnya melemah", tapi statusnya:** kerumunan maker **tidak punya satu pun
pengukuran prospectif yang berhasil**, dan satu-satunya angka positif yang pernah kita punya (in-sample,
sumber harga ticker) sudah dijelaskan sebagai artefak sumber harga (V5/F-D30) - bukan sebagai efek dompet.

**Yang tidak boleh dilakukan dari sini** (aturan halaman 11/12, diulang di F-D63): **tidak** membalik
jadi "jual saat kerumunan beli" - dua replikasi dengan arah terbalik sudah muncul, dan membalik tanda
setelah melihat hasil adalah gerakan yang sama yang membunuh +393,4 pagi tadi. Hipotesis fade butuh
kunci sendiri, jendela sendiri, dan n sendiri.

**Yang tetap hidup dari halaman ini:** fakta bahwa `maker`/`smart_degen` dari feed ⑦ berguna sebagai
**rem** (E13/E14: `jual_*` memisahkan +285,5 dari −230,3 di menit ke-5; 16/16 grid ambang), bukan
sebagai alasan masuk. Membedakan dua peran itu adalah seluruh isi catatan ini.

Lihat: [[06-Results/17 - Pra-Registrasi Watch]] §4-§5 · [[06-Results/12 - Harga Masuk yang Benar]] ·
[[06-Results/10 - Evidence Stack]] · F-D63 · halaman 21.

