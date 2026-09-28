---
tags: [tk, referensi]
---

# Fakta Terukur — lembar angka yang boleh dikutip subtree ini

**Sumber:** `vault/03-Data/`, `vault/06-Results/`, `vault/07-Testing/`, `tools/`, `universe/`
**Dibaca terakhir:** 28 Sep 2026 01:58 WIB = **2026-09-27T18:58Z**
(`tools/anchor.py --verify`, `tools/verdict_counts.py`, `tools/winlog.py`,
`git fetch` + `git show origin/master:universe/wallet-flow-manifest.txt`).
Jam vault = UTC: tanggal lokal dan tanggal UTC sedang berbeda hari di halaman ini, dan itu alasan
kenapa setiap angka di bawah menyebut sumbernya, bukan "kemarin".

**Aturan pakai:** satu-satunya tempat di `TradingKnowledge/` yang boleh menjadi sumber angka
tentang produk ini. Angka lain yang menyebut Fabius harus ditulis *(belum diukur)*. Setiap baris
punya tautan ke halaman yang memikulnya — kalau halaman itu dan run terbaru berbeda, **run yang
menang** ([[Conventions]] §1).

## A. Deret harga dan metrik pasar yang bisa kami baca sendiri

| sumber | apa yang diberikan | kedalaman / isi | kunci | peran |
|---|---|---|---|---|
| Aster `fapi/v1/klines` | OHLCV perp BNB-native | **9.599 bar 1 jam ≈ 400 hari** | tanpa API key | harga forward untuk backtest & penilaian ⑦ |
| Aster `premiumIndex` + `openInterest` | funding + OI | **608 kontrak** (`Meme` 61, `AI` 42); funding per 4 jam: BNB +0,0000 % (mark 778,45 · OI 7.832) · ETH +0,0100 % · SOL −0,0020 % · HYPE −0,0018 % · DOGE +0,0044 % | tanpa key | pemutus rezim, BUKAN gerbang keamanan: `\|funding\| > 0,05 %/4 j` menolak posisi baru. Terukur 0/2.963 kejadian dalam 97 hari (F-D26) |
| Hyperliquid `candleSnapshot` | OHLCV (chain sendiri, bukan BNB) | 5.001 bar ≈ 208 hari | tanpa key | pembanding silang |
| Hyperliquid `metaAndAssetCtxs` | funding + OI | **234 perp**; BNB OI 65.047, funding 0,004781 %/jam | tanpa key | kontrol silang untuk baris Aster |
| GMGN `token_kline` | OHLCV per token | mentok **1.000 bar ≈ 41,6 hari**; **0 bar untuk token gas** | privat | tidak cukup untuk walk-forward |
| GeckoTerminal pools | universe + likuiditas pool | 1.000 bar; **pool baru ±30 bar** | demo/privat | universe & likuiditas, bukan deret harga |

- Kapasitas server: **1.500 bar/panggilan** (limit 3.000/5.000 ditolak `code -1130`); kedalaman
  datang dari **paging**, bukan dari satu permintaan besar. Rinci di [[03-Data/D3 - Price Depth]].
- Ambang yang mengikat uji: `NEED_BARS=2400` (5-fold walk-forward) · `MIN_BARS_TINY=720`
  (30 hari = layak dinilai, **tidak** layak diklaim sebagai edge).

### A.2 Dune — riwayat yang boleh diminta, tapi tidak boleh jadi saksi waktu

| hal | angka terukur | sumber |
|---|---|---|
| lag BSC | **±1 jam** (jam berjalan 18 swap vs jam penuh 205.875) → bukan jalur keputusan horizon 4 jam | [[03-Data/D4 - Dune]] |
| populasi `dex.trades` chain `bnb` | **5.274.783 swap** dalam 1 jam terakhir; **205.875 swap / 20.607 wallet** di jam penuh terakhir | `tools/whale_sweep.py` + `_research/probe_dune_*.py` |
| biaya kredit | agregat 90 hari dengan join `tokens.erc20` = **1,259 kredit / ±11 detik**; kueri 10 hari **yang mengirim baris** = 503 detik → yang mahal itu mengangkut baris, bukan berpikir | `execution_cost_credits` di endpoint status |
| status metodologisnya | barisnya punya `_updated_at` → masa lalunya **bisa disusulkan**: sah untuk statistik, tidak sah sebagai saksi waktu | [[Concepts/Point-in-Time vs Retro-updatable]] |

Bacaan yang wajib ikut disebut: **20.607 wallet dalam satu jam penuh** vs **454 maker** di bidang ⑦
(§B). Selisih itu bukan "whale sedikit" — itu **saringan vendor**, dan itu pembatas setiap kalimat
tentang "dompet pintar".

### A.3 Integritas dataset sendiri

| hal | angka | sumber / cara baca ulang |
|---|---|---|
| baris snapshot universe | **penghitungnya bertambah tiap jam** — 65 saat [[03-Data/D5 - Record Schemas]] ditulis, 68 di `universe/manifest.txt` pada hari yang sama. Yang tetap: deretnya melintasi **empat semantik skema** (tanpa kunci → 2 → 3 → 4) | baca ulang: `python -X utf8 vault/scripts/dump_schemas.py` (ia melaporkan **pergeseran**, dan itu memang benar) + baris pertama `universe/manifest.txt` |
| verifikasi sha256 per baris | **60 dari 62 lolos**; 2 baris tidak dapat dihitung ulang dan pemicunya belum diketahui | `universe/write_universe_manifest.py` → [[06-Results/03 - Not Yet Proven]] #21 |
| konsekuensi untuk analisis | setiap uji wajib menyebut **nomor skema**: `survivable_count` skema 2 **tidak sebanding** dengan skema 3 | aturan di [[03-Data/D5 - Record Schemas]] |
| lubang penggabungan sumber | satu jendela terukur (23 Sep, 03:00Z, **90 baris**): **37** baris tidak punya satu pun field perilaku, dan **13** di antaranya gugur *tanpa satu pun alasan risiko*; join GeckoTerminal↔GMGN hanya mempertemukan **3 dari 40** baris pool — dan melebarkan `market/rank` (100/200/500) **tidak** mengubahnya | [[06-Results/02 - Thresholds]] · [[06-Results/03 - Not Yet Proven]] #12 |
| akibat yang sudah ditanggung | `tools/decide.py` memulangkan **dua daftar** (`risk_vetoes` vs `data_gaps`) dan `ENTER` mensyaratkan keduanya kosong — jadi "ditolak" dan "tidak bisa dinilai" sudah terpisah di kode, bukan di niat | `tools/decide.py` |
| umur kandidat (diukur 28 Sep pada snapshot kanonik `2026-09-27T08:03:04Z`, skema 4, 140 baris) | **121 baris berumur < 24 jam**, 19 baris ≥ 24 jam, 0 tanpa umur → `survivable_count` **15**, `fully_evaluated_count` **1**. Alasan penolakan pada jendela itu: `age<threshold` 121 · `trending_without_demand` 73 · `liq<threshold` 76 · `top10>45 %` 15 · `lock<threshold` 5 · `bundler>30 %` 3 · `no_liquidity_data` 2 | dibaca dari `universe/bsc-universe.jsonl` (baris per jam, terus bertambah); alatnya `python -X utf8 tools/screen_universe.py --windows` · `python -X utf8 universe/write_universe_manifest.py` |

## B. Bidang ⑦ — aliran dompet (rekaman kami sendiri)

| hal | angka | dari |
|---|---|---|
| sumber | GMGN `user/smartmoney` + `user/kol` | [[03-Data/D2 - Wallet Flow]] |
| tebar per panggilan | **100 transaksi**, jendela lihat **8–13 menit** | terukur |
| paging | **semua parameter diabaikan server** (`offset`/`page`/`end_ts` → head sama, overlap 98/100) → **tidak ada riwayat; yang lewat = hilang** | terukur |
| ekor rekaman di `origin/master` | **2026-09-27T18:58:26Z** (hash HEAD berubah tiap ±3 menit — jangan disalin, baca ulang: `git log -1 --format="%h %cd" origin/master`) | timestamp server GitHub, bukan jam laptop |
| isi pada ekor itu | **51.260 baris · 22.322 transaksi · 454 maker · 1.607 token · rentang 34,95 jam** | `universe/wallet-flow-manifest.txt` (`git show origin/master:...`) |
| run 37 menit sebelumnya | `94aead6` **18:21:16Z** = 50.285 baris · 21.907 transaksi · 452 maker · 1.590 token · rentang 34,33 jam | baris ini dibiarkan sebagai pembanding: catatan lain mengutip angka itu, dan selisih 37 menit sudah cukup untuk terlihat seperti kesalahan |
| baris harga sendiri (`px`) | **27.886 baris / 1.607 token unik** | dihitung dari `git show origin/master:universe/wallet-flow.jsonl` lewat `_research/count_flow.py` *(workspace — angka ini keadaan rekaman, bukan klaim produk)* |
| tebar maker | **219 maker ≥20 tx** · 151 ≥40 · 63 ≥100 · **40 maker cuma 1 transaksi** | tiga yang pertama: `python -X utf8 tools/whale_report.py` (di clone yang sudah `git pull`); yang keempat dari skrip workspace yang sama. `maker_ge20` = jumlah **tx**, bukan lot selesai — jangan dipanggil `n` |
| cadence perekam | commit tiap **202 detik** pada ekor (3,37 menit); rata-rata 526 commit / 34,95 jam ≈ **4,0 menit** | `git log --format=%cd origin/master -- universe/wallet-flow.jsonl` |
| kontrol | **0 dari 607 transaksi pertama tidak bertag (0,0 %)** → aliran ini *didefinisikan* sebagai "dompet yang sudah dilabeli" | manifest ⑦ |
| pembanding yang sah | (a) arah acak pada token & jam yang sama · (b) hold 4 jam dari baris `px` kami · (c) pisahkan `is_open_or_close=1` vs `=0` — **bukan** "lebih baik dari trader biasa" | manifest ⑦ |

**Angka blok B basi dalam hitungan menit, bukan hari.** Jangan menyalinnya ke catatan lain sebagai
keadaan tetap: kutip **perintahnya** dan jalankan. Yang boleh dipertahankan dari blok ini hanyalah
yang struktural (jendela 8–13 menit, tanpa riwayat, 0 % tanpa tag).

Baca ulang sebelum mengutip: `python -X utf8 tools/whale_report.py`.

## C. Yang mati, dan itu properti pasangan sumber × jaringan

Terukur 24 Sep ([[06-Results/03 - Not Yet Proven]] baris 15): di **runner** `api.binance.com` →
`451 restricted location`, Bybit → `403 CloudFront country`; **OKX funding** dan **Bitget contracts**
membalas `200` di runner tapi **terpotong TLS di laptop**. Karena itu "bisa diakses" tidak pernah
sifat sebuah sumber, melainkan sifat **sumber + jaringan tempat kamu bertanya**.

- Jalur yang hidup di **kedua** jaringan: GMGN, GeckoTerminal, DexScreener, GoPlus, Hyperliquid,
  CoinGecko, berkas GDELT.
- **Yang "mati" pada 24 Sep hidup lagi pada 28 Sep - dan itu membatalkan satu rencana.** Dibaca dari
  laptop ini 28 Sep 02:03–02:06Z (`_research/probe_tk_sources.py` + `_research/probe_cex_depth.py`,
  tiap panggilan diulang sampai 3x sebelum divonis): `api.binance.com` **200**,
  `fapi.binance.com` histori OI **200**, Bybit funding history **200**, OKX funding history **200**,
  `data.binance.vision` (listing S3) **200**. Yang tetap tidak bisa dipakai: **Hyblock**
  (`URLError` timeout 42,5 s), **Coinglass** (`404` di dua path yang *saya* tebak - itu path salah,
  bukan layanan mati, jadi tidak boleh ditulis sebagai bukti kematiannya), **Glassnode** `401` dan
  **CryptoQuant** `401` = **hidup tapi butuh akun** → statusnya `TIDAK-ADA`, bukan
  `MATI-DARI-MESIN-INI`.
  Pelajarannya bukan "CEX ternyata hidup", tapi: matriks egress ini adalah properti
  **sumber × jaringan × waktu**, dan klaim kita berumur empat hari. Baca ulang sebelum mengutip §C.
- **GDELT DOC API**: `429` di dua jaringan (laptop dengan jeda 6 detik **dan** runner GitHub) →
  klaim lama "cuma butuh pacing" resmi **dicabut**. Yang hidup: jalur berkas mentah
  (`data.gdeltproject.org/gdeltv2/lastupdate.txt` → GKG) dengan TLS sah di kedua jaringan.
  Sumber: [[06-Results/03 - Not Yet Proven]] baris 8 · [[03-Data/01 - Dataset]].
- **CryptoPanic**: `403` tanpa akun, di laptop **dan** runner — bukan soal jaringan, soal akun
  ([[06-Results/03 - Not Yet Proven]] baris 8).
- Yang **tidak** kami punya sama sekali: order book L2, footprint/tick, heatmap likuidasi,
  jadwal unlock/vesting, MVRV/SOPR/NUPL, exchange reserve. Status tiap metode di `03-Sinyal/`
  memakai enum di [[Aturan Subtree]]. *(Dulu baris ini juga menyebut "histori funding per-aset";
  itu gugur 28 Sep - lihat §A.5.)*

### A.5 Histori funding/OI — sekarang PUNYA kami sendiri (`universe/funding-history.jsonl`)

Ditarik 28 Sep 02:26Z oleh `universe/record_funding_history.py` (tanpa kunci), **5.963 baris / 934 KB**:

| sumber | jenis | baris | rentang nyata | interval |
|---|---|---|---|---|
| OKX `funding-rate-history` | funding 6 basis | 1.763 | **97,7 hari** (22 Jun → 28 Sep) | 8 jam |
| Bybit `funding/history` | funding 6 basis | 1.200 | **66,3 hari** (23 Jul → 28 Sep) | 8 jam |
| Binance `openInterestHist` | OI + nilai OI | 3.000 | **20,8 hari** (7 Sep → 28 Sep) | 1 jam |

Yang TIDAK berubah oleh ini: interval 8 jam tetap bukan fitur per-bar (horizon uji kita 1 j dan
4 j), jendela OI tetap ±30 hari, dan order book/tick/likuidasi tetap tidak ada. Yang berubah:
**veto funding bisa diukur** - hasilnya 0 dari 2.963 settlement melewati ambang ([[06-Results/08 - Carry Study]] §A),
dan satu uji arah 24 jam menghasilkan **0 lolos dari 12 uji** (§B). Baca ulang:
`python -X utf8 universe/record_funding_history.py --report` lalu `python -X utf8 tools/carry_study.py`.

Sebelum 28 Sep, blok ini mencatat "histori funding per-aset tidak bisa ditarik mundur" (dari probe
24 Sep). Itu gugur: yang tidak bisa adalah **menarik mundur funding per-jam venue kami sendiri** -
karena kami belum merekamnya. Rinciannya di [[03-Data/D6 - Funding and OI History]].

## D. Ongkos — satu-satunya bagian yang sudah kami ukur sendiri

| nama | nilai | provenance |
|---|---|---|
| round-trip di venue demo kami | **59 bps** posisi 1 unit (kurva x·y=k + fee 30 bps, **bukan** gas mainnet) | `forge test --match-test test_round_trip_...` → [[07-Testing/T3 - Execution Suite]] |
| realized round-trip nyata di 97 | **−59 bps** per putaran, dibaca dari event `Closed` | `decisions/execution-trail.jsonl` · [[Concepts/Cost Is Fixed]] |
| model biaya warisan dari proyek rujukan | 5,5 bps fee + 4,5 bps slip **per sisi** = 10 bps/sisi → **20 bps round-trip**; ambang efektifnya **2×** ongkos (gross > 40 bps) | [[06-Results/02 - Thresholds]] — **sudah bukan default lagi**, lihat P10 di bawah |
| ongkos tetap $0,05 bolak-balik pada $1 | butuh **+5 %** cuma untuk balik modal — dan tabel itu **estimasi mainnet, belum diukur di repo ini** | [[01-Agent/A4 - Trust Gating and Real-Money Rules]] |
| gas testnet 97 | **0,10 gwei** live; guard lama memakai floor **1 gwei** → menolak karena plafon sendiri | `08-Backlog` P1 |
| **isi** dari 59 bps itu | dua sisi fee 30 bps yang berkomposisi = `1 − (1 − 0,003)²` = **59,9 bps** → pada 1 unit, **≈ 0 bps** sisa untuk dampak kurva | `python -X utf8 tools/costs.py --self-test` · [[FD3 - Likuiditas dan Dampak Harga]] |
| ambang gross yang berlaku sekarang | **118 bps** = 2 × 59 (satu round-trip untuk dipilih, satu untuk keluar) | `python -X utf8 tools/costs.py` |

**P10 ditutup 28 Sep 2026** (`tools/costs.py` + `vault/scripts/wire_costs.py`): satu model ongkos
untuk semua jalur uji — `backtest.py`, `ledger.py`, `screen_universe.py`, `smartmoney_score.py`,
`flow_test.py`, `maker_ledger.py` semuanya menarik dari modul yang sama, default = **59 bps yang
terukur** (basis `measured-own-venue`), dan override `--cost` dicatat di artefak sebagai
`cli-override` supaya tidak bisa menyamar sebagai angka ukur. 20 bps tetap ada sebagai label
**asumsi warisan**, tidak lagi menyetir angka.

Konsekuensinya dicatat di [[06-Results/04 - Negative Results]] §6 dan
[[00-Overview/05 - Corrections]]: deret yang dihitung ulang **memburuk**, bukan membaik — satu-satunya
"MENANG" di seri paper (+1,5 bps) menjadi **−37,5 bps**, dan seri itu kini WR 0 %.
`python -X utf8 tools/costs.py --self-test` mengikat 59 ke fee pool (dua sisi 30 bps berkomposisi =
59,9), jadi kalau suatu hari angkanya tidak lagi berasal dari mana pun, gerbangnya yang berteriak.

## E. Ambang yang berlaku sekarang

| gerbang | nilai | asal |
|---|---|---|
| `MIN_LIQ_USD` | 50.000 USD | diputuskan (belum diuji terhadap hasil) |
| `MIN_AGE_SEC` | 24 jam | aritmetika jendela data |
| `MAX_TOP10` | 45 % supply | diputuskan |
| `MIN_LOCK` | 20 % LP terlock | diputuskan |
| `MAX_BUNDLER` | 30 % | diputuskan |
| `MIN_HOLDER` | 60 alamat | diputuskan |
| `MIN_VOL_OVER_LIQ` | vol24/likuiditas ≥ 0,10 | diputuskan |
| kursi / `apply_gates` | ① riwayat bar · ④ keamanan · ⑥ kapasitas keluar → `seat_eligible` + `seat_blockers` (ikut **di-hash**) | [[01-Agent/A3 - One-Way Gates]], [[04-Tools/TL2 - direction]] |
| sampel statistik | `MIN_SAMPLES` 20 trade OOS non-overlap · BH-FDR α 0,10 · p satu arah aproksimasi **normal** (pada n=20–40 p **sistematis terlalu kecil**) | [[06-Results/02 - Thresholds]] |
| gerbang uang nyata (F-D16) | `net expectancy > 0` **setelah ongkos nyata di ukuran itu**, `n ≥ 20`, tetap positif setelah fold terbaik dibuang, lolos BH α 0,10, dihitung **di luar sampel** | F-D16 di [[00-Overview/03 - Decisions]] |
| ukuran risiko yang ditulis keputusan | `RISK_SAFE` 0,005 (0,5 %) saat `conf < 0,6` · `RISK_WARM` 0,010 (1 %) sisanya → masuk field `risk_pct` | dibaca dari kode: `tools/direction.py:76-77` dan `:242` — konstanta, **bukan** hasil uji |
| plafon kontrak | `dailyCap` default 5 unit · `maxPositionQuote` 1 unit · `HARD_CEILING = 10` (naikkan ke 1.000 tetap dipotong ke 10) · `killSwitch` · `NoAnchorHash` menolak hash **nol** | [[02-Contracts/C3 - ExecutionVault]] |

Empat ambang universe pertama **masih perlu diuji terhadap hasil**, bukan dipertahankan karena
sudah tertulis. Cara mengujinya ada di [[07-Peta-Fabius/GAP2 - Uji Setiap Veto Terhadap Hasil]].

## F. Hasil uji yang sudah ada (dan sebagian besar negatif)

| apa | hasil | halaman |
|---|---|---|
| aturan arah `direction.py`, 400 hari × 12 aset, ambang diimpor (tidak di-fit) | **net rugi di 12/12** saat gerbang `\|acf\|` dicabut (−27,9…−0,8 bps/trade); gross hanya +1,5…+4,0 bps vs ongkos 20 bps; **dibalik tetap kalah** (−39,2…−12,1); horizon 24 j **0/12** lolos | [[06-Results/04 - Negative Results]] |
| **hitung ulang 28 Sep dengan ongkos terukur (P10)** | masih **12/12 negatif**, sekarang **−39,8 … −66,9 bps**/trade (gross tidak berubah: −7,9 … +19,2 — yang berubah cuma penggarisnya); dengan gerbang `\|acf\|` hidup: **4 simbol dinilai, 0 lolos** | `python -X utf8 tools/backtest.py --mom-only` dan tanpa flag → `decisions/backtest-20260927Z-h4-momonly.json`, `...-h4.json` |
| panel whale GMGN, horison per jam | **win rate 69,8 % tapi −10,4 bps per jam** | F-D16 di [[00-Overview/03 - Decisions]] |
| smart money vs kerumunan, berpasangan per (token, jendela 4 j) | mentah: panel **+680,7 bps** vs kontrol **+336,4 bps** (51.863 entri swap BSC, 10 hari, ongkos 20 bps). Berpasangan & drift terbuang: **selisih −10,4 bps, p=0,568** → tidak berbeda dari kerumunan; 54 wallet capai n≥20, **0 lolos BH** | `tools/smartmoney_score.py` → [[06-Results/04 - Negative Results]] §4c |
| dua `Enter` yang jatuh tempo | **+1,5 bps** dan **−146,3 bps** net (n=2) | [[06-Results/03 - Not Yet Proven]] baris 16 |
| **hitung ulang 28 Sep (P10, ongkos 59 bps)** | ketiga keputusan paper yang jatuh tempo: **−37,5**, **−185,3**, **−485,3 bps** net → **WR 0 %**; satu-satunya "MENANG" yang pernah kami catat adalah artefak penggaris 20 bps | `python -X utf8 tools/ledger.py` lalu `tools/winlog.py` |
| jalur eksekusi nyata | 3 putaran chain, **WR 0 %**, net −59,0 bps rata-rata — dan itu memang **ongkos**, bukan sinyal (pool kami sendiri tanpa arus luar) | `tools/winlog.py` |
| `\|acf\|` MARSCOIN | 0,075 → **zona abu-abu** (0,05–0,10 = belum tahu) | [[06-Results/03 - Not Yet Proven]] |
| **uji arah dari funding ekstrem (P13 dibalik, 28 Sep)** | **0 dari 12 uji lolos BH** (6 basis × 2 venue, horizon 24 j, ongkos 59 bps); median positif di 4 baris (BTC/bybit +60,2 · ETH/bybit +51,0 · XRP/bybit +54,9 · DOGE/bybit +29,0) tapi CI-nya memotong nol dan mean-nya negatif semua | `python -X utf8 tools/carry_study.py` → [[06-Results/08 - Carry Study]] §B |
| **veto funding `> 0,05 %/4j`** | **0 dari 2.963 settlement** melewatinya dalam 66–97 hari pada enam basis besar → veto itu tidak pernah punya kesempatan menyala di aset ini (bukan di memecoin, yang memang tidak punya funding) | §A halaman yang sama; bahan: [[03-Data/D6 - Funding and OI History]] |
| **carry vs ongkos** | 1,3–2,2 bps/hari → **27–45 hari** cuma untuk menutup satu round-trip 59 bps, dengan asumsi arah netral yang tidak ada jalur eksekusinya di repo ini (kaki pendek `TIDAK-ADA`) | §C halaman yang sama |
| `security_gate` pada kandidat arah | 5/5 membalas: 4 `OK` + 1 `UNMEASURED` (`pPOLY is_honeypot=None` tidak dihitung bersih) | [[04-Tools/TL3 - security_gate]] |
| **kohor maker vs maker tunggal (hipotesis builder, 28 Sep)** | horizon 60 m, ongkos 59 bps: **% posisi positif** K=1 **39,5** (n=661) · K≥2 **39,3** (n=61) · K≥3 38,1 (n=21) · K≥5 50,0 (n=24, p=0,58, CI median [−1044; +1808]) · cuaca (semua px→px) **30,8** (n=12.195) → **0 kelompok lolos BH** | `python -X utf8 tools/flow_cluster_test.py` → `decisions/flow-cluster-*.json` · [[06-Results/09 - Whale Cluster Test]] |
| **kohor maker vs maker tunggal — berpasangan DALAM TOKEN YANG SAMA (06:22Z, satu sumber harga)** | ⚠ baris ini dulu tertulis "K≥2 +508,2 bps" padahal bucket-nya **EKSAK**: yang terukur adalah "**tepat 2 dompet**", dan kejadian K=4 / K≥6 dibuang (53 dari 2.592 = 2,0 %). Setelah kelas dijadikan kumulatif yang benar (`bucket_of`): K≥2 **83 token, n=215, median selisih +363,6 bps, CI [+0; +772]**, 58,1 % positif, p=0,0101 → lolos BH. **(Nilai ini digantikan baris KANONIK di bawahnya: +393,4 CI [+5; +1012] p=0,0008, setelah 5.355 baris `px` dobel dilebur.)** K≥5 (33 token, n=64) +864,4 CI [+43; +4.148] p=0,0164 → lolos BH. K≥3 (62 token, n=127) **+7,6 CI [−222; +772], p=0,19 → TIDAK** | `python -X utf8 tools/flow_cluster_test.py --horizon 30 --window 15 --entry px` (kelas kumulatif) · run bersejarah yang salah label: `decisions/flow-cluster-20260928T062246Z.json` |
| **berpasangan dalam token yang sama, harga KANONIK (28 Sep 07:37Z)** | horison 30 m / jendela 15 m: **K≥2 = +393,4 bps** CI [+5; +1012], 60,9 % positif, p=0,0008 **lolos BH**; K≥3 +393,4 CI [+0; +1182] p=0,0252 lolos; K≥5 +2.412 CI [+570; +6.333] p=0,0018 lolos — **kelas bersarang, bukan tiga uji bebas**. Acuan = kejadian K=1 pada TOKEN yang sama (370 kejadian, median −59,0) | `python -X utf8 tools/flow_cluster_test.py --horizon 30 --window 15` → `decisions/flow-cluster-20260928T073714Z.json` · [[06-Results/09 - Whale Cluster Test]] |
| **stack bukti lintas aspek (P19, 28 Sep)** | lima aspek lulus sendiri: `cluster_ge2` **+393,4** · `cluster_ge3` **+592,6** (acuan = semua kejadian lain di token, termasuk K=2 — karena itu beda dari baris di atas dan itu harus disebut) · `repeat_maker` **+222,8** · `money_spread` **+552,7** · `buy_usd_ge_1k` **+601,0**; TIDAK lulus: `no_exit_flow` −0,3 (p=0,66) dan `wide_flow` +0,5 (p=0,55). Tumpukan ≥2 aspek lulus **+481,0** CI [+23; +977] p=0,0002; **≥2 dompet DAN uang tersebar +748,8** CI [+12; +1574] p=0,0010; `cluster_ge3` TANPA fresh **−3,2** (bukti kelas bersarang) | `python -X utf8 tools/evidence_stack.py` → `decisions/evidence-stack-20260928T073717Z.json` · varian: `_research/stack_final.py` · [[06-Results/10 - Evidence Stack]] |
| **`fresh_token` ditolak sebagai bukti** | +7.708 bps (80,8 % positif) pada 295 kejadian — terlalu besar untuk efek pasar dan mekanismenya mekanis: "token baru di rekaman" = "kami baru mulai menarik harganya". Gabungan `fresh DAN K≥2` = +7.813 → dia menyuntik apa pun yang dia sentuh | §3 [[06-Results/10 - Evidence Stack]] |
| **5.355 baris `px` berbagi stempel waktu** (±19 % deret harga kami) | penyebab dua alat jujur memberi angka berbeda untuk kejadian identik (+363,6 vs +649,8): harga masuk jadi tergantung **urutan**, bukan data. Aturan kanonik: satu harga per (token, stempel) = median → `flow_cluster_test.dedupe_px()`, dipakai kedua alat, dan keduanya sekarang sepakat di +393,4 | `tools/flow_cluster_test.py` (docstring `load()`) · §0 [[06-Results/10 - Evidence Stack]] |
| **corong penuh: 807 dari 11.631 beli = 6,9 %** (12,7 % dari kandidat) | run `081806Z`: 11.631 beli → **5.258** tumpang tindih (< 1 horison di token sama) → 6.373 kandidat → **5.085** tanpa harga ≤10 m sebelum beli, **481** tanpa harga keluar → **807** dinilai. Setiap angka di halaman 09/10 adalah statistik di antara yang masih kelihatan akhirnya | `python -X utf8 tools/evidence_stack.py` (baris `sensor:`) |
| **dua sumur harga, satu sumber per kejadian** | `px` (GMGN) vs `wp` (DexScreener) berbeda **±0,16 %–0,40 %** pada menit yang sama (4 sampel pertama) = 16–40 bps×10, seukuran efek yang dicari; aturan: masuk+keluar satu sumber, selain itu dibuang dan dihitung. `--px both` memberi `rows_sha256` identik dengan mode baku selama `wp` belum berisi (**123 baris, rentang 0,00 jam**) | `python -X utf8 tools/prices.py --report` · `python -X utf8 tools/evidence_stack.py --px both` · §4b [[06-Results/10 - Evidence Stack]] |
| **83,9 % beli punya kemunculan token yang sama ≤ 2 jam sebelumnya** | simulasi atas data yang ada: batas 12,7 % itu **bukan** batas pasar, tapi batas sambungan alat ke perekam pantau; yang dibutuhkan cuma waktu rekaman (rantai harus jalan dengan workflow baru) | `python -X utf8 _research/sim_watch_value.py 120` |
| **dan jangan membaca tiga baris itu sebagai tiga replikasi** | kelasnya **bersarang**: K≥5 ⊂ K≥3 ⊂ K≥2. Kalau yang tengah gagal sedangkan dua ujung "lulus", itu bukan bukti monotonicity - itu beberapa kejadian yang menggerakkan median pada n kecil. Satu-satunya angka yang berarti sebagai uji adalah yang terluas (K≥2), dan **batas bawah CI-nya +0,0** | lihat `## Batas` di [[06-Results/09 - Whale Cluster Test]] |
| **tapi jangan buru-buru memakainya sebagai sinyal** | satu jendela rekaman (±36 jam), satu rezim, panel pilihan GMGN, dan `maker_ledger` tetap §H. Angka ini adalah **hak untuk punya opinion**, bukan PnL: belum ada fill nyata di pool ini, belum ada biaya keluar, belum ada hari kedua | lihat bagian "Apa yang TIDAK berubah" di halaman yang sama |
| **sensor yang membatalkan run 06:05Z** | dari **3.958** kandidat beli, **3.191 (80,6 %)** dibuang karena tidak ada harga `px` pada jendela keluar; yang terbuang = token yang keluar dari sorotan (dugaan keras: yang mati). Dan **21,6 %** kejadian pembanding punya gross **persis 0,0 bps** (resolusi harga). Run 06:22Z dengan `px` di kedua ujung + horison 30 m menurunkan sensor jadi **4,3 %** | angka dicetak alat yang sama (`skip` + kolom `proporsi_harga_diam`) |
| **corong penyaringan vs hasil** (sudah dihitung!) | kohort **lolos** n=52: mean **+148,0** · median **+35,9** · best **+2.804,2** / worst **−2.399,5** · **kohort ditolak** n=713: mean **+353,7** · median **−44,4** · best **+213.686,5** / worst **−9.131,7**. Per alasan (mean/median bps): `age<thr` +360,2/−44,4 (n=704) · `liq<thr` +817,1/−407,2 (n=318) · `trending_without_demand` +49,5/0,0 (n=105) · `top10>45 %` +26,3/+13,2 (n=91) · **`bundler>30 %` −44,7/−16,2 (n=55)** · `lock<thr` −20,6/+21,7 (n=17) · `holders<thr` −1344,5/−0,5 (n=4). Keluarga tes 105, BH α 0,10, **5 lolos** (nama kelima tes itu TIDAK dicetak — bagian dari P12) | `python -X utf8 tools/screen_universe.py` → `tools/out/screen_report.json` (765 pasangan forward, 545 token). **`out/` di-gitignore**: artefaknya tidak ada di clone, perintahnya ada |
| ⚠ yang TIDAK ada di artefak itu | berkasnya **tidak punya** field `pct_negative` maupun `overlap`. Dua angka ("42,3 % / 53,0 % negatif") dan satu ("overlap 156") pernah tertulis di halaman vault dan **tidak bisa ditunjuk** di berkas mana pun — semuanya sudah dicabut 28 Sep. Yang boleh dikutip dari corong ini hanya: `n`, mean, median, best, worst, `fdr.family_tests/passed`, `forward_pairs`, `distinct_tokens`, dan `constants` | dibaca langsung dengan `python -X utf8 _research/read_funnel.py` *(workspace)* atau `type tools\out\screen_report.json` |

**Cara membaca baris corong itu, dan apa yang dilarang darinya.** `n` per alasan **saling tumpang
tindih** — 704 + 318 + 105 + 91 + 55 + 17 + 4 = **1.294** untuk 713 token yang ditolak, karena satu
token boleh kena beberapa veto sekaligus. Jadi angka antar-alasan **tidak bisa dibandingkan satu
sama lain**; yang sebanding hanya dua kohort teratas (lolos vs ditolak), dan itu pun mean-nya
digerakkan ekor (`best_bps` **+213.686,5** untuk satu token). Report itu sendiri mencetak batasnya:
"bukan trade yang bisa dieksekusi · tanpa slippage nyata · tanpa ukuran posisi · bukan prediksi
return" — dan `constants` di dalamnya masih `RT_COST_BPS = 20.0` dengan `GATE_GROSS_BPS = 40.0`
(gross harus di atas 2× ongkos warisan itu) — jadi angka-angkanya bukan "setelah ongkos kita":
dengan 59 bps terukur, ambang gross yang sepadan adalah **118 bps**, dan pada ambang itu hampir
tidak ada kandidat yang lolos (§F baris aturan arah: gross maksimum yang pernah kami lihat
+4,0 bps).

## G. Keadaan hidup saat halaman ini ditulis (28 Sep 2026)
```
python -X utf8 tools/anchor.py --verify   -> anchorCount() = 19 | 13 baris terpelacak | 13/13 COCOK
python -X utf8 tools/verdict_counts.py    -> countByVerdict: Enter 4 / Abstain 15  (4 + 15 = 19)
python -X utf8 tools/winlog.py            -> PAPER n=3 WR 0,0 % net rata2 -236,0 bps (total -708,1)
                                             streak paper: 3 KALAH | terpanjang menang 0
                                             CHAIN n=3 WR 0,0 % net rata2 -59,0 bps (total -177,0)
                                             streak chain: 3 KALAH | terpanjang menang 0
                                             gerbang F-D16: n>=20 -> BELUM (kurang 17)
                                             ! 2 decisionHash dengan net berbeda antar artefak:
                                               (1,5 -> -37,5) dan (-146,3 -> -185,3)  <- ganti ongkos P10
git fetch origin                          -> lokal 1 commit di depan, 188 di belakang
                                             (169 pada pembacaan pertama 40 menit sebelumnya -
                                              penghitung ini bergerak, jangan dikutip sebagai keadaan)
git log --oneline HEAD..origin/master     -> SEMUANYA commit data ("wallet flow" / "snapshot
                                             universe"): nol commit non-data di antaranya
```

`19 vs 13` itu lubang yang tercatat (P6b di [[08-Backlog/01 - Backlog]]), bukan keberhasilan.
Angka blok G basi dalam hitungan jam: jangan mengutipnya dari halaman ini, jalankan perintahnya.

## H. Alat yang angkanya **belum boleh** dikutip

| alat | kenapa belum | rem yang sudah terpasang |
|---|---|---|
| `tools/maker_ledger.py` | **mekanikanya dibetulkan 28 Sep; angkanya tetap tidak boleh dikutip.** Run 27 Sep: median `\|net\|` **4.558,3 bps**, maks **1.222.045,4**, `6.704/13.999` baris jatuh ke kombinasi `(b,c)` yang tidak dipakai alatnya. Run 28 Sep, tiga guard masuk (lot dibangun dari **sisi** dengan `c` sebagai metadata; MTM basi dipisah; **53** kemunculan ekstra `(hash, maker, token, sisi)` dibuang): median **2.644,6**, p90 **15.731,0**, maks **927.377,9**, **56,9 %** lot > 2000 bps, dan **0** lot dengan rasio keluar/masuk di luar 1:100 → sisanya **bukan** bug satuan: median ≈ 26× per lot mungkin nyata pada peluncuran; yang tidak sah adalah **memakainya sebagai rata-rata** (populasi terseleksi dua kali: dompet berlabel + token yang sedang di sorotan) | `python -X utf8 tools/maker_ledger.py` — remnya sekarang berbunyi begitu, bukan "ini mustahil" |
| **kenapa skor maker tidak akan pernah bisa dibaca "terampil" dari feed ini** | populasinya diseleksi pada hasil: dompet yang GMGN tampilkan di daftar smart-money/KOL, **pada token yang sedang panas**. Flip 20–100 × normal di sana; yang tidak panas tidak direkam. Diukur 28 Sep: **2.302 dari 2.936** lot terbuka dinilai dengan harga basi (> 30 menit) — dan memperbaikinya justru **mengubah tanda bacaan**: **+4.859** bps (semua lot) vs **+6.898** bps (yang terukur saja), jadi asumsi harga basi di sini pesimistis, bukan penggembira. Dan `+6,9%` per flip itu tetap bukan mean yang sah: 187 dari 219 maker "positif" = distribusi ekor-gemuk pada sampel terpilih, bukan keterampilan | tiga bacaan dicetak alatnya (`hanya flip selesai` / `semua lot` / `yang TERUKUR saja`) + lebar kohor di `tools/whale_cohorts.py` |
| `tools/whale_cohorts.py` | struktural (median **2 maker/simbol**, **49,8 %** simbol cuma 1 maker, HHI median **0,347**) — kokohnya belum diuji terhadap hasil | dilaporkan sebagai **breadth**, bukan sebagai skor |
| `decisions/whale-sweep-90d.json` | `cost_bps_applied = 0.0` → **SEMUA** angka horison di berkas itu GROSS; dan `p_boot` identik `0,00024993751562109475` di 4 horizon **belum terjelaskan** | `tools/whale_report.py` mencetak `cost_bps_applied` paling awal |

Angka blok H dikutip sebagai " Kami menemukan …" = klaim palsu. Boleh dikutip hanya sebagai
"alat kami sedang rusak karena sebab yang diketahui: …".

**Terkait:** [[Aturan Subtree]] · [[03-Data/D2 - Wallet Flow]] · [[03-Data/D3 - Price Depth]] ·
[[06-Results/02 - Thresholds]] · [[06-Results/04 - Negative Results]] · [[Quick-Reference]]
