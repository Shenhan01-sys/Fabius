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
| ekor rekaman di `origin/master` | **2026-09-28T09:24:22Z** (commit `d73c1ad` 09:24:23Z) — **71.656 baris · 28.467 transaksi · 497 maker · 2.256 token · rentang 49,38 jam**. Pembacaan 27 Sep 18:58Z (51.260/22.322/454/1.607/34,95 jam) dibiarkan di baris berikutnya sebagai pembanding riwayat. Hash HEAD berubah tiap ±3 menit — jangan disalin, baca ulang: `git log -1 --format="%h %cd" origin/master` | timestamp server GitHub, bukan jam laptop; `universe/wallet-flow-manifest.txt` |
| **DERET `px` KAMI ADALAH TANGGA BEKU — bukan ticker** | **71,7 %** baris `px` (23.758 dari 33.125 transisi) mengulang nilai baris sebelumnya pada token yang sama; buang pengulangan itu dan deret menyusut **35.304 -> 11.546 baris (-67,3 %)**. Sebabnya mekanis dan ada di kode kita sendiri: `px` membawa `price_usd` dari **transaksi terakhir** token itu tapi di-stamp **waktu tarikan** (`universe/record_wallet_flow.py` baris 113 + 132) -> tidak ada transaksi baru = nilai yang sama dengan stempel baru. Ini juga menjelaskan P18: "harga diam" bukan pembulatan feed, dan bukan pula pasar yang diam | `python -X utf8 tools/price_frozen.py` (workspace) · `universe/record_wallet_flow.py` |
| **dan efek K>=2 TIDAK berasal dari baris berulang** | berpasangan dalam token yang sama, dataset kini: deret apa adanya **K>=2 = +334,8 bps CI [+2; +763] p=0,0016** (85 token, n=223); deret tanpa pengulangan nilai **+353,7 CI [+2; +922] p=0,0009** (61 token, n=192). Arah dan signifikansi sama -> efeknya bukan counting artifact. K=1 tetap mendarat di **-59,0 / -58,3** = persis lantai ongkos, yang sekarang punya sebab alat | alat yang sama (`tools/price_frozen.py`), memakai `tools/evidence_stack.py` tanpa perubahan |
| **"harga kini" kami sebenarnya berumur 8,7 MENIT (median)** | Dijadwalkan dari data yang ada: untuk tiap baris `px`, umur = waktu_tarikan - waktu transaksi terakhir token itu sebelumnya. **p10 44 dtk · p25 2,9 mnt · p50 8,7 mnt · p75 20,7 mnt · p90 42,0 mnt · p99 107,5 mnt · maks 2,6 jam** (41.119 baris). **87,7 %** harga kami lebih tua dari 1 menit dan **45,7 %** lebih tua dari 10 menit - padahal aturan masuk alat kami justru "harga <= 10 menit" | `python -X utf8 tools/price_age.py` (workspace; memakai `tx.t` yang memang tersimpan) |
| **harga GMGN vs harga venue lain pada detik yang sama beda sampai +-20 %** | terukur 28 Sep 09:19-09:21Z pada 25 token irisan: 8 di antaranya **diam di GMGN tapi bergerak di DexScreener**; contoh `0xfedf19759b` GMGN `0.00018855428262944804` (dua tarikan identik) vs DEX `0.0002257 -> 0.0002211`. Ini menjelaskan sebagian selisih dua sumur di §F (0,16-0,40 %) yang tadinya kukira soal presisi: **keduanya mengukur benda yang berbeda** - harga transaksi terakhir vs harga pool kini | `python -X utf8 tools/px_cache_probe.py` (workspace; dua tarikan berjarak 90 s + DexScreener batch) |
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

| **harapan posisi MELURUH cepat setelah buy kerumunan pintar - dan kabar itu mati dalam ±2 menit** | `tools/horizon_decay.py` 29 Sep 07:58Z (393 kejadian, jendela E7): mean winso **+192,7 @2m -> +202,6 @5m -> +45,0 @10m -> -42,0 @15m -> -182,5 @30m**; berpasangan vs 30m pada posisi yang sama **5/5 horison pendek menang** (median +120,8 s/d +5,3; p<=0,00002); **placebo asal digeser 30-90 m: datar -184,7..-113,9** (jadi kemiringan milik peristiwa, bukan jam); P(ada harga keluar) 84-85% rata; kalau masuk ditunda 2 m, median@5m jadi **-56,2**, ditunda 5 m -> **-166,4**; latensi feed kami sendiri **median 0,2 menit** (stempel commit) | `python -X utf8 tools/horizon_decay.py` - [[06-Results/19 - Umur Posisi]] · F-D41. **Bukan** klaim bisa trading: median +20..+60 bps, harapan di ekor kanan, bump menyusut -24..-41 bps kalau harga masuk dari `tx.p`, dan tanpa kedalaman (P33) tidak bisa dinyatakan bisa diambil || **DUA "latensi" yang sempat kutukar - dan yang benar menghukum SUMBERNYA, bukan kodemu** | `lag = commit − t(baris TERBARU)` = median **0,2 menit** (`tools/feed_latency.py 25`): itu umur potongan paling segar dalam satu muatan. `latensi_keputusan_detik` yang dicatat CI untuk tiap keputusan nyata = **median 808 d (13,5 menit)**, min 534, p90 874, max 899 (276 baris, jam 09-11Z, `tools/fast_lane.py --report`). Yang berhak dibandingkan dengan umur kabar 2 menit (E11) adalah yang kedua | `python -X utf8 tools/fast_lane.py --report` · `python -X utf8 tools/feed_latency.py 25` - F-D50, halaman 19 §2b, P50. Percobaan ketiga (merekonstruksi umur dari selisih himpunan baris antar-commit) memberi median **1494 MENIT** dan **tidak** kami kutip: alatnya sendiri sekarang mencetak "TIDAK BOLEH DIKUTIP" di jalur itu |
| **umur kabar saat memutuskan itu 61 d, bukan 808 d - dan lengan yang telat BUKAN 'hasil masuk'** | `tools/fast_lane.py --report` 29 Sep 12:5xZ: rejim `terbaru-dulu` median **61 d** (n=182, p90 89, 97 % < 180 d) vs rejim `urutan-berkas` **812 d** (n=252) - alat yang sama, hanya urutan pilihannya dibetulkan (`b990ab5`, 11:22:56Z). Cap `arr` di baris ⑦ (1.736 baris): umur saat tiba median **120 d**, dan pada baris yang kami putuskan **24 d** | `python -X utf8 tools/fast_lane.py --report` · `python -X utf8 tools/feed_latency.py --kedatangan` - [[06-Results/26 - Masuk Segar, Terukur Benar]] §1-2 · F-D54 (menggantikan baris 808 d sebagai deskripsi alat yang berjalan) |
| **latensi FEED bagus, latensi KEPUTUSAN dulu 812 d - dan yang salah adalah alatku (F-D50 lalu F-D54)** | tiga angka, jangan dicampur: (a) `commit − t(baris TERBARU)` = **0,2 menit** - umur potongan paling segar dalam satu muatan; (b) `arr − t` pada baris ⑦ = umur kabar **sebelum kami sentuh**: median **120 d** (1.736 baris), **24 d** pada baris yang benar-benar kami putuskan; (c) `latensi_keputusan_detik` = umur kabar **saat kami memutuskan**, dan ini DUA REJIM: `urutan-berkas` **812 d** (n=252) vs `terbaru-dulu` **61 d** (n=182, p90 89 d, 97 % < 180 d). Yang 772/808 d yang dulu kupetik di halaman 19 adalah rejim lama + salinan lokal yang tertinggal; jangan dikutip sebagai keadaan alat | `python -X utf8 tools/feed_latency.py 25` · `python -X utf8 tools/feed_latency.py --kedatangan` · `python -X utf8 tools/fast_lane.py --report` - [[06-Results/26 - Masuk Segar, Terukur Benar]] §1 · F-D50, F-D54 |
| **venue, bukan sinyal, yang membatasi agen ini - dan ukurannya lebih sempit dari yang dikira (F-D43 → F-D56/57)** | `tools/venue_bridge.py` 29 Sep 08:3xZ mengukur irisan **61 simbol = 3,1 % dari 25.050 kabar beli**, tapi parsernya hanya mengenal sufiks USDT/USDC/PERP dan membuang 17 entri daftar (`BTCU`, `BTCUSD1`, `SKHYNIXUSD1`). Kabar 24 jam yang reachable: **2,26 %** sebagai pasangan yang sama, **5,86 %** sebagai aset yang sama - dua pertanyaan berbeda. Dan dari 41 simbol reachable itu, yang harga perp-nya **bergerak di resolusi menit cuma 5** (kelas MATI median 97,4 % menit tanpa transaksi; `BNCUSD1` = 96,0 % dan beku 446 m) sehingga kabar pada simbol yang bisa diuji horison menit = **0,20 %** | `python -X utf8 tools/venue_bridge.py` · `python -X utf8 tools/perp_liveness.py` - `decisions/e20-perp-liveness-*.json` · [[06-Results/28 - Venue Kami Bukan Pasar]] · F-D43, F-D56, F-D57 |
| **bump E11 TIDAK pindah ke harga perp - diujinya hari ini, jawabnya tidak** | E26 (`tools/perp_bump.py`) 29 Sep 13:54Z, 5 simbol kelas HIDUP, n=15 jendela lengkap dari 32 kejadian: mean winso @2 m **+2,0**, @5 m **−7,3**, @30 m **−34,4**; placebo **+0,7 / +6,9 / −9,6**; berpasangan 5m-vs-30m median delta **−0,5 bps** (menang 7 kalah 8, p=0,696). Sensitivitas kelas TIPIS (n=39): median **tepat 0,0 di semua horison** karena deretnya beku | `python -X utf8 tools/perp_bump.py` · `decisions/e26-perp-bump-*.json` · [[06-Results/28 - Venue Kami Bukan Pasar]] §4 · F-D58. Batas: satu hari, n kecil, klines bukan kedalaman - ini memindahkan pertanyaan, bukan memvonis |
| **rem ⑦ (`jual_*`) tetap bekerja - dan lebih tajam - di horison cepat** | `tools/veto_expectancy.py` 29 Sep 08:43Z, 482 kejadian: pada menit ke-5 `BOLEH` mean **+285,5** (median **+79,8**) vs `VETO` **−230,3** (median **−377,8**); selisih **+515,8** melawan CI atas placebo **+397,2**; sama di 2 m (+450,3 vs +294,5) dan 30 m (+487,5 vs +405,1). `BOLEH 378 / VETO 104 / TAK ADA DATA 0` | `python -X utf8 tools/veto_expectancy.py --draws 200` - [[06-Results/21 - Rem di Horison Cepat]]. **EKSPLORASI tanpa kunci**; VETO bukan kelompok acak (pisau jatuh), jadi ini asosiasi terarah. Batas venue 3,1 % (F-D43) dan batas latensi 2 menit (F-D41) tidak bergerak |
| **rem ⑦ bertahan di SELURUH grid ambang - tidak ada tebing** | `tools/veto_sensitivity.py` 29 Sep 08:5xZ: pemindaian ulang status **identik dengan `flow_gate.state()` untuk 677/677 kejadian**; grid maker 1..4 x rasio 1,25..3,0 = **16/16 kombinasi melewati placebo**, selisih mean(BOLEH)-mean(VETO) di menit ke-5 bergerak **+260,0 … +399,7 bps** vs CI atas acak **+170,2 … +254,4**; titik terpasang (2; 1,5) = **+395,1 vs +202,4** | `python -X utf8 tools/veto_sensitivity.py --draws 200` - [[06-Results/21 - Rem di Horison Cepat]] §4. Bukan penyetelan: alatnya tidak mengubah `flow_gate.py`. Populasinya 677 (harga keluar 5 m ada) vs 482 di E13 (harus ada di 30 m) - berbeda karena censoring, bukan karena dua hasil berbeda |
| **teori "sisi mana lebih agresif" tidak hidup di substrate kami - dan kebisingan pembagian 10x efeknya** | `tools/flow_variasi.py` 29 Sep 09:45Z, 396 kejadian, 5 pembacaan (usd 15 m, usd 5 m, jumlah transaksi, jumlah maker, bucket VPIN-style): selisih mean kuantil atas-bawah di menit ke-5 = **−41,4 / −15,0 / +9,6 / −24,8 / −14,9 bps**, semuanya di dalam placebo dua ekor (p2 0,75-0,93), BH KOSONG. Yang lebih penting dari angkanya: sebar antar-pembagian **±200-470 bps** - sekitar 10x sebesar efek yang diklaim | `python -X utf8 tools/flow_variasi.py --draws 200` - [[08-Backlog/03 - Epik Teori Baru]] T3. Ini bukan "teori trader itu salah di HFT": kami mengukur versi lambat dari teorinya pada cadence yang kami punya, dan itu yang hasilnya nol |
| **"trailing jangan sampai rugi" mustahil secara algebra, TAPI kunci bersyarat lazim di jalur kami** | `tools/trailing_gate.py` 29 Sep 10:12Z: syarat `pi > 2s+i+C` (C=59,0 bps terukur + spread terukur ⑨ p50 0,04 / p90 13,5 bps); puncak median **+1.122 bps** dan di paruh awal jendela **+747 bps** → **63-66 % kejadian punya jendela d sah**; pada s=200 bps dengan i=s masih 51,9 % | `python -X utf8 tools/trailing_gate.py` - [[06-Results/23 - Gerbang Trailing]] · F-D48. Batas: stop mengubah **bentuk** distribusi, bukan drift (Lei & Li 2009, S6; Osler 2002: respons stop > take-profit, S7), dan pada 5 m resolusi kami tidak melihat puncak (31 % kejadian punya ≥2 baris) - jadi ini gerbang kelayakan, bukan hasil uji strategi |
| **jarak "menyentuh level" vs "terisi" akhirnya terukur, dan lebih besar dari edge kami** | `tools/fill_gap.py` 29 Sep 11:0xZ: ⑨ (170 pasangan bar, level 25 bps di bawah mid) **11,2 % dilompati sebelum terlihat**, gap median +9,2 / p90 +39,3 bps; `wp` tempat kabar hidup (21.895 pasangan, 40 simbol) **13,6 % dilompati**, gap **median +245,3 bps**, p90 **+752,4**, maks +1.580 - lawan harapan median terbaik kami +79,8 bps (E13) | `python -X utf8 tools/fill_gap.py` - [[06-Results/24 - Trailing pada Bar yang Salah]] §4 · F-D49 · P45. Ini **batas bawah**: angka itu bukan realisasi fill, dan agregatnya lintas simbol (median per simbol), bukan distribusi satu peristiwa |
| **masuk 58 d sesudah whale beli = −519 bps di menit ke-5 (25 lengan sah, 24 token)** | `tools/fast_lane.py --report` 29 Sep 12:5xZ: mean winso **−519,4** | median **−76,4** | mean mentah −1.016,6 | positif 5/25 | ≤−1.000 bps: 9 | `entry_px − tx_p` median **+25,7 bps**, p90 **+1.199,6**, sudah di atas harga whale pada **16/25** | `python -X utf8 tools/fast_lane.py --report` - [[06-Results/26 - Masuk Segar, Terukur Benar]] §3-4 · F-D54. Batas: n=25, satu lengan, tanpa kontrol acak, retrospektif terhadap perbaikan alatnya (P55/P56) |
| **harapan buku paper bukan properti strategi - dia properti BUDGET** | berkas peristiwa sama (1.884 kesempatan, 4 hari, ongkos 59 bps), hanya `--per-day` yang berubah: control `random` = **+165,7** @200/hari (n=800) · **−100,2** @24/hari (n=96, yang CI tulis) · **−26,7** @5/hari (n=20, budget kontrak). `lock` +79,4 / −160,8 / −161,5. Di 24/hari alat mencetak `BELUM LAYAK - belum di atas control` dengan CI bawah **−382,8**; di 5/hari **tidak ada arm yang mengalahkan control-nya**; median control tetap di −54,4 … +201,1 (n=20), persen positif 35-50 % | `python -X utf8 tools/paper_book.py --per-day 5` (lalu 24, 200) - F-D51 · P52. Konsekuensi: angka buku tanpa `--per-day` dan `n` bukan hasil. Dan peringatan yang sudah dipasang SEBELUM vonis: lengan E9 berbalik arah antar-budget, jadi n=26 pada satu budget paling banyak membuktikan "26 posisi" |
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
| **stack bukti lintas aspek (P19, 28 Sep)** | lima aspek lulus sendiri: `cluster_ge2` **+393,4** · `cluster_ge3` **+592,6** (acuan = semua kejadian lain di token, termasuk K=2 — karena itu beda dari baris di atas dan itu harus disebut) · `repeat_maker` **+222,8** · `money_spread` **+552,7** · `buy_usd_ge_1k` **+601,0**; TIDAK lulus: `no_exit_flow` −0,3 (p=0,66) dan `wide_flow` +0,5 (p=0,55). Tumpukan ≥2 aspek lulus **+481,0** CI [+23; +977] p=0,0002; **≥2 dompet DAN uang tersebar +748,8** CI [+12; +1574] p=0,0010; `cluster_ge3` TANPA fresh **−3,2** (bukti kelas bersarang) | `python -X utf8 tools/evidence_stack.py` → `decisions/evidence-stack-20260928T073717Z.json` · varian: `tools/evidence_variants.py` · [[06-Results/10 - Evidence Stack]] |
| **`fresh_token` ditolak sebagai bukti** | +7.708 bps (80,8 % positif) pada 295 kejadian — terlalu besar untuk efek pasar dan mekanismenya mekanis: "token baru di rekaman" = "kami baru mulai menarik harganya". Gabungan `fresh DAN K≥2` = +7.813 → dia menyuntik apa pun yang dia sentuh | §3 [[06-Results/10 - Evidence Stack]] |
| **5.355 baris `px` berbagi stempel waktu** (±19 % deret harga kami) | penyebab dua alat jujur memberi angka berbeda untuk kejadian identik (+363,6 vs +649,8): harga masuk jadi tergantung **urutan**, bukan data. Aturan kanonik: satu harga per (token, stempel) = median → `flow_cluster_test.dedupe_px()`, dipakai kedua alat, dan keduanya sekarang sepakat di +393,4 | `tools/flow_cluster_test.py` (docstring `load()`) · §0 [[06-Results/10 - Evidence Stack]] |
| **REPLIKASI TERKUNCI PERTAMA: TIDAK ADA REPLIKASI - klaim 09/10 dicabut oleh pengujiannya sendiri** | dijalankan 28 Sep 21:24Z, `spec_sha` tetap `0x03aa212f…` (alat menolak kalau berubah), rekaman baru 15,12 jam, bahan **275 kejadian setelah `t_kunci`**: `uji_primer` K>=2 dan `uji_kedua` `money_spread` = **SAMPEL TIDAK CUKUP** (n<12 pasangan); `uji_ketiga` stack>=2 = median **+219,2 CI [-18; +2138] p=0,0490** -> **GAGAL** di syarat CI. Sign test-nya nominal lolos; yang memotong adalah batas bawah CI | `python -X utf8 tools/day2_replicate.py` -> `decisions/day2-20260928T212437Z.json` · [[06-Results/11 - Pra-Registrasi Hari Kedua]] HASIL |
| **setelah 15 jam rekaman tambahan, cakupan sisi masuk TIDAK membaik** | sensor run replikasi: **8.090** beli tanpa `px` <= 10 m (vs 8.391 tumpang tindih, 778 tanpa keluaran, 275 dinilai). Yang membaik adalah sumur kedua: `wp` **11.426 baris / 109 stempel / rentang 14,00 jam** | `decisions/day2-20260928T212437Z.json` (`sensor`) · `python -X utf8 tools/prices.py --report` |
| **buku kehadiran: harapan kohort muda tidak bertahan setelah yang berhenti dijawab dihitung** | 1.439 kejadian lolos veto (harga peristiwa): ADA 489 → mean +141,3 · HILANG 375 → +140,5 · TIDAK-JELAS 575 → +229,0. Bound dengan bukti: 1.064 teramati (+188,7) + 375 HILANG dianggap rugi penuh = **−381,7 bps/posisi**. Tiga cacat yang harus dibetulkan untuk sampai sini: jendela pantau dipakai sebagai bukti kematian (74 % 'HILANG' = keluar daftar kami), `--max-batches 6` membuat 400-900 token tak pernah ditanya, dan guard dedupe `r["tk"]` membuat perekam melapor 'mencatat 11' tanpa menulis apa pun | `python -X utf8 tools/presence_ledger.py` · `python -X utf8 universe/record_watch_prices.py --watch-min 120 --max-batches 40` · F-D36 |
| **ketiadaan mulai tercatat sebagai data (P33 tahap 1)** | siklus 28 Sep 22:0xZ: 45 token pantau -> 42 harga + **3 kehilangan tercatat** (2 `answered-no-price`, 1 `answered-no-pair`) = tertanggung semua; sebelum perbaikan, 3 token itu tidak masuk hitungan mana pun. Batch gagal (429/timeout) TIDAK pernah dihitung sebagai kehilangan - diuji langsung `429/403/0/500 -> []` | `python -X utf8 universe/record_watch_prices.py --watch-min 120 --max-batches 3` |
| **corong penuh: 807 dari 11.631 beli = 6,9 %** (12,7 % dari kandidat) | run `081806Z`: 11.631 beli → **5.258** tumpang tindih (< 1 horison di token sama) → 6.373 kandidat → **5.085** tanpa harga ≤10 m sebelum beli, **481** tanpa harga keluar → **807** dinilai. Setiap angka di halaman 09/10 adalah statistik di antara yang masih kelihatan akhirnya | `python -X utf8 tools/evidence_stack.py` (baris `sensor:`) |
| **EFEK K>=2 ADALAH ARTEFAK HARGA MASUK - klaim 09/10 DICABUT** | 557 kejadian dengan kedua sumur, pairing identik: `px→px` **+93,0 CI [+1; +825] p=0,0066** (yang terbit) → `tx→px` **+0,1 CI [−14; +198] p=0,53** → `tx→tx` **+0,3 CI [−7; +516] p=0,35**. **Tidak ada aspek lolos BH pada harga peristiwa.** Pada populasi lebih besar (`--px txevent`, 908 kejadian) arahnya malah **negatif**: `cluster_ge2` **−491,4 CI [−1319; −205]**, 30,5 % positif. Yang berubah satu hal: harga masuk = harga transaksi itu sendiri | `python -X utf8 tools/entry_decomposition.py` → `decisions/entry-decomposition-20260928T094547Z.json` (`rows_sha256=0x2c96b4f17374c8…`) · [[06-Results/12 - Harga Masuk yang Benar]] |
| **bentuk payoff 30 menit: median menipu, ekornya yang menentukan** | 1.174 kejadian harga peristiwa: median **−58,9** bps (=ongkos) tapi **P(≥+500 bps) = 33,9 %**, p90 +8.854, p99 +105.639; **mean winsorized ±2.000 = +82,7 bps/posisi**; 41,7 % positif | `tools/tail_test.py` · [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] §1 |
| **tidak ada aspek aliran yang menaikkan ekor; kerumunan jual MENURUNKANNYA** | vs baseline 33,9 %: `jual_2` 22,5 % (p=0,0028) · `jual_3` 23,6 % (p=0,021) · `jual_bersih` 20,3 % (p=0,011) - **ketiganya lolos BH ke arah minus**; `beli_2` 30,3 % (p=0,19) dan `beli_3` 29,9 % (p=0,25) = **tidak** menaikkan; `sepi_beli` 29,9 % (p=0,056, tidak lolos) | sama · §2 halaman 13 · Fisher eksak + BH α 0,10 |
| **TIGA kebijakan: penakut = 0, buta = +82,7, dengan veto = +162,3 bps/posisi** | mean winsoresed ±2.000 bps, horison 30 m, harga peristiwa, ongkos 59 bps dipotong: A tidak pernah masuk **0,0**; B masuk semua **82,7 CI [+5,0; +159,1]** (n=1.174); C B+veto kerumunan jual **162,3 CI [+80,4; +243,0]** (n=1.014, hanya 13,6 % kejadian dilewati). Horison 60 m: 112,1 → 153,6 | `python -X utf8 tools/policy_test.py` [--horizon 60] · [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] §3b |
| **penyortiran 5 posisi/hari TIDAK terputuskan oleh data kami - dan itu bisa dihitung** | 10 fitur siklus hidup pool (point-in-time dari `bsc-universe`), 3 hari, 15 posisi: CI rata-rata acak **[−440,1; +411,4]** bps; semua fitur "seri" (terbaik `bundler_rate` +179,0). Simpangan per posisi ≈ 841 bps -> butuh ±68 posisi untuk resolusi 200 bps (**±14 hari**) dan ±272 untuk 100 bps (**±55 hari**) - melewati tenggat 30 Sep | `python -X utf8 tools/select_test.py` · [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] §3c |
| **KOHORT YANG MEMBAWA HARAPAN Justru YANG TIDAK BISA DIUKUR (penyensoran sisi keluar)** | horison 30 m, harga peristiwa: kohort MUDA (deret < 30 baris) hanya **19,4 %** kejadian punya baris harga keluar (547/2.814; **2.267 hilang**); mean yang teramati **+249,3** CI90 [+146,8; +354,8] -> bila yang hilang diberi nilai p05 teramati (-2.000, sudah di lantai winsor) mean jadi **-1.562,8**; `break-even = 0`. Kohort MATANG: 59,8 % teramati, mean **-86,6** [-189,7; +16,5] | `python -X utf8 tools/censor_bound.py` · [[06-Results/16 - Harga Keluar yang Hilang]] |
| **TEKNIKAL KLASIK DIUJI pada instrumen kita: tidak ada yang di atas control; breakout FATAL** | 1.054 kejadian horison 30 m (deret harga peristiwa), pool mean winso +218,0 / P(>=+500) 39,8 %: `ma_tren` n=136 **-186,5**, `rsi_jenuh_jual` n=87 +15,3, `macd_bull` n=97 -225,7, `fib_pullback` n=24 **-548,3** (median -1.265,5), `breakout` n=27 **-587,9 CI [-951,9; -201,4]** dengan P(>=500) **3,7 %**, `vol_spikes` n=26 -558,0. Horison 120 m mengulang: nol di atas control. BH kosong | `python -X utf8 tools/technic_lab.py` -> `decisions/technic-lab-20260928T155227Z.json`, spec terkunci `prereg-technic-lock.json` `0x6032bda0…` · [[06-Results/15 - Teknikal Klasik Diuji]] |
| **lapisan pengetahuan kami sebagian besar belum punya angka - sekarang terukur, bukan diduga** | audit `tools/coverage_knowledge_audit.py`: 86 catatan metode, 31 tanpa penanda "belum diuji", dan `04-Setup` (7 setup) menyebut NOL perintah alat. Satu aturan teknikal pernah diuji sebelumnya (`tools/backtest.py`: gap SMA24 +-1 % searah ret24, bar hourly majors) dan hasilnya nol - momentum dipadamkan gerbang \|acf\| | `python -X utf8 tools/coverage_knowledge_audit.py` (workspace) |
| **kandidat "kapan boleh masuk" pertama = `lock_percent`, BUKAN kerumunan maker** — **dikoreksi 29 Sep: tinggal SATU uji, bukan dua** | run 28 Sep (n=255 berfitur): Q1 -60,1 -> Q5 **+66,0** bps dan P(>=+500) 36,0 % vs 0,0 % (Fisher satu arah p=0,0010). Jalur 29 Sep 05:14Z dengan `mann_whitney_p` yang **dibetulkan**: MW `lock_percent` **0,6441** (yang dikutip 0,0000 adalah alat, bukan pasar), Q1 -137,3 -> Q5 -52,1 (**dua-duanya minus**), BH harapan winso = **TIDAK ADA**. Yang tersisa cuma Fisher satu arah pada ekor - dan `bundler_rate` Q5 +188,4 tetap contoh noise yang harus dipercaya sebagai noise (dia menentang veto `bundler>30%` kami sendiri) | `python -X utf8 tools/quintile_test.py` · `tools/instrument_proof.py` (workspace) - [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] §3d |
| **dua distribusi IDENTIK diberi p=0,000000 oleh Mann-Whitney lama** | `tools/instrument_proof.py` mencetak 5 kasus dan **3 di antaranya mengubah VONIS** (bukan cuma angka): A terpisah menang 1,0->0,0; tumpang tindih ringan 0,0223->0,99999; dua distribusi identik 0,000000->0,5 - kasus terakhir ini yang paling memalukan, karena tidak ada perbedaan apa pun antara A dan B | `python -X utf8 tools/instrument_proof.py` - [[00-Overview/03 - Decisions]] F-D37 |
| **alat statistik kami sendiri pernah membalik arah - dan itu terukur, bukan pengakuan** | `mann_whitney_p` (dipakai `quintile_test`, `entry_lab`, `technic_lab`, `flow_cluster_test`) menyusun peringkat dari `sorted(a) + sorted(b)`: tiga dari empat kasus uji salah arah. Kasus terpisah total: lama **p=1,000000**, benar **p≈0**; tumpang tindih ringan: lama 0,0223, benar 0,99999; ties penuh: lama 0,0000, benar 0,0128. Semua p yang dikutip dari fungsi ini **wajib dihitung ulang** - dan sudah: BH teknikal tetap kosong, E5 tetap mati, kolom MW kuintil dicabut | `python -X utf8 -c "import sys;sys.path.insert(0,'tools');import flow_cluster_test as FC;FC.mw_self_test()"` (4 kasus) · run pembanding: `tools/instrument_proof.py` |
| **cakupan fitur = cakupan yang TERPILIH, dan terpilihnya ke arah buruk** | baseline semua kejadian yang boleh **+82,7** bps / P(>=+500) **33,9 %**; pada 25,1 % yang punya snapshot universe point-in-time: **-64,7** bps / **14,5 %**. Snapshot kami berasal dari `trending_pools`/`new_pools`, jadi yang bisa dideskripsikan = yang sudah panas | sama - §3e |
| **BUKU PAPER: veto bernilai ~+93 bps/posisi; penyortiran tidak** | 556 posisi paper, harga peristiwa, 59 bps RT, 3 hari: random+veto **+188,3** · first+veto +140,9 · `lock`+veto +109,7 · **tanpa veto +95,1**; median SEMUA kebijakan −59 (=ongkos); naik 0,01 -> 1,00 BNB memangkas ~70-90 bps/posisi (dampak 2s/L dua kaki), dan 454/556 posisi tidak punya angka likuiditas -> haircut-nya nol. **Dikoreksi 29 Sep 08:56Z: satuannya juga salah (BNB dibagi USD, ±600x) - jadi angka tabel ini adalah net of 59 bps dan HAMPIR NOL dampak**, bukan net of dampak. Tiga varian terukur: tercatat **+75,9** / satuan-dibetulkan **-715,7** / hanya-liq-sah **-87,8** bps (`tools/impact_audit.py`, `decisions/impact-audit-20260929T085648Z.json`) - kata "dampak" tanpa menyebut varian tidak masuk vault lagi (F-D46) | `python -X utf8 tools/paper_book.py --per-day 200 --size-quote 0.01` (dan `1.0`) · [[06-Results/14 - Buku Paper]] |
| **kandidat `lock_percent` MATI sebagai kebijakan** | di uji kuintil dia lolos dua uji (Q5 +66,0 vs Q1 −60,1); di buku paper dia **kalah dari acak** (+109,7 vs +188,3) dan satu-satunya yang negatif di 1 BNB (−51,2). Sebabnya = perangkap cakupan: menyortir pada `lock_percent` memilih pool yang punya data, dan subset itu baseline-nya −64,7 bps | `tools/paper_book.py` vs `tools/quintile_test.py` · §1 halaman 14 |
| **`fisher_p` kami dua-arah dan tidak bisa dipakai untuk "lebih baik"** | percobaan pertama `quintile_test` meloloskan `volume_24h` dengan P(>=+500) **0,0 % vs 31,4 %** - arah terbalik, p tetap ~0, karena ia membandingkan probabilitas tabel dengan yang teramati. Sekarang pakai `ekor_hipergeo` (satu arah, eksak lewat lgamma) | `tools/quintile_test.py` (docstring `ekor_hipergeo`) |
| **vonis pertama lab alasan masuk: belum ada yang layak** | pool 789 kejadian (tanpa kerumunan jual), mean winso **+290,8**, P(>=+500) 41,7 %; E2 risk-on n=156 mean **+368,4** CI [+144,9; +587,7] median **+146,5** tapi **di bawah CI atas control acak (+487,5)** dan ekor tidak naik (Fisher p=0,33); E3 sepi n=537 +275,6, juga di bawah control; **E1 hanya 17 kejadian (2,2 %) -> n<20, TIDAK DIUJI**; BH ekor: kosong | `python -X utf8 tools/entry_lab.py` -> `decisions/entry-lab-20260928T113208Z.json`, spesifikasi terkunci `prereg-entry-lock.json` `0x3ecad842…` · [[08-Backlog/02 - Epik Alasan Masuk]] §3b |
| **REPLIKASI KEDUA (harga peristiwa, terkunci 12 jam sebelumnya): TIDAK ADA REPLIKASI, dan arahnya terbalik** | 265 kejadian setelah `t_kunci` 09:38:44Z, `spec_sha=0x6f69e100…`: `uji_primer` K≥2 median **−1.518,5 bps CI [−7.379; −3]** (n=40, p=0,99); `uji_kedua` money_spread −747,9 CI [−2.694; +77]; `uji_ketiga` stack≥2 −1.124,3 CI [−3.310; −3]. Alat MENOLAK jalan di 11,99 jam dan baru jalan di 12,05 jam. **Fade tidak dikejar**: aturan halaman 12 menutup dua arah; membalik tanda setelah melihat hasil = gerakan yang membunuh +393,4 pagi tadi | `python -X utf8 tools/day2_replicate.py --halaman 12` -> `decisions/day2h-20260928T214502Z.json` · [[06-Results/12 - Harga Masuk yang Benar]] §1b |
| **hipotesis cermin (fade) gugur di sisi masuk** | kalau kerumunan jual meramalkan kenaikan, `jual_2` harusnya di atas baseline: terukur **−690 bps CI [−1209; −11]** vs baseline, dan 26,9 % positif. Jadi "jual ramai" = **jangan masuk**, bukan "masuk" | `tools/mirror_test.py` · [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] §3 |
| **dua sumur harga, satu sumber per kejadian - ANGKA LAMANYA SALAH SATU ORDE** | `px` vs `wp` pada **n=4.022** pasangan berimpit (\|dt\|<=5 m, `--report`): median bertanda **+10,1 bps**, tetapi **median absolut 899 bps**, p5 -3.884 / p95 +6.576 / maks +106.724. Angka "±0,16 %-0,40 % (4 sampel pertama)" yang kutulis lebih dulu salah satu orde besaran - dan koreksinya justru MENGUATKAN aturannya: 400 bps tempat efek §F hidup berada DI BAWAH noise antar-sumur, jadi masuk+keluar wajib satu sumber. `--px both` tetap memberi `rows_sha256` identik dengan mode baku selama `wp` belum berisi (saat itu: 123 baris, rentang 0,00 jam) | `python -X utf8 tools/prices.py --report` · §4b [[06-Results/10 - Evidence Stack]] |
| **cakupan dua sumur, pembacaan 28 Sep 21:3xZ** | `gmgn` 52.185 baris / 2.839 token / 61,30 jam (7.129 stempel dobel dilebur); `watch` **11.592 baris / 396 token / 14,22 jam**; per kejadian beli horison 30 m, aturan satu-sumber: `gmgn` **49,7 %** | `watch` **6,9 %** | keduanya 6,1 % | **tak terpenuhi 49,5 %** - sumur kedua menambah titik pengamatan, bukan mengganti yang lama | `python -X utf8 tools/prices.py --report` |
| **83,9 % beli punya kemunculan token yang sama ≤ 2 jam sebelumnya** | simulasi atas data yang ada: batas 12,7 % itu **bukan** batas pasar, tapi batas sambungan alat ke perekam pantau; yang dibutuhkan cuma waktu rekaman (rantai harus jalan dengan workflow baru) | `python -X utf8 tools/watch_value_sim.py 120` |
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
git fetch origin + rebase                 -> 28 Sep 08:2xZ: 0 di belakang, 8 di depan
                                             (pembacaan PAGI: "1 di depan, 188 di belakang";
                                              penghitung ini bergerak - jangan dikutip sebagai
                                              keadaan, jalankan perintahnya)
git log --oneline HEAD..origin/master     -> SEMUANYA commit data ("wallet flow" / "snapshot
                                             universe"): nol commit non-data di antaranya
universe/wallet-flow-manifest.txt         -> generated_utc 2026-09-28T06:13:38Z; TIDAK ADA commit
                                             aliran setelah itu (jam rujukan: header server GitHub
                                             08:24:37Z) -> BIDANG ⑦ MATI ~2 jam 10 menit
python -X utf8 tools/day2_replicate.py --status
                                          -> terkunci 08:30:38Z | spec 0x03aa212fccdf5b9f |
                                             t_kunci 06:13:38Z | "BELUM SAH - kurang 12.0 jam"
                                             (alatnya menolak mencetak angka; sunting spesifikasi
                                             setelah dikunci -> exit 1, itu diuji, bukan dipercaya)
git push + gh run list                    -> 09:0xZ: aliran ⑦ HIDUP LAGI (commit 08:43:36 /
                                             08:47:00 / 08:50:24Z; rentang 48,81 jam), dan
                                             watchdog terbukti men-dispatch: run #2 `force=1`
                                             -> "WATCHDOG: rantai di-dispatch" -> run #16
                                             `pending` (mengantri, tidak membatalkan #15)
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
