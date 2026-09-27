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
| Aster `premiumIndex` + `openInterest` | funding + OI | **608 kontrak** (`Meme` 61, `AI` 42); funding per 4 jam: BNB +0,0000 % (mark 778,45 · OI 7.832) · ETH +0,0100 % · SOL −0,0020 % · HYPE −0,0018 % · DOGE +0,0044 % | tanpa key | wired di `tools/direction.py`: funding > 0,05 %/4 j → tolak posisi |
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
| baris snapshot universe | **65 baris**, melintasi **empat semantik skema** (tanpa kunci → 2 → 3 → 4) | [[03-Data/D5 - Record Schemas]]; `python -X utf8 vault/scripts/dump_schemas.py` (ia melaporkan **pergeseran** dan itu memang benar) |
| verifikasi sha256 per baris | **60 dari 62 lolos**; 2 baris tidak dapat dihitung ulang dan pemicunya belum diketahui | `universe/write_universe_manifest.py` → [[06-Results/03 - Not Yet Proven]] #21 |
| konsekuensi untuk analisis | setiap uji wajib menyebut **nomor skema**: `survivable_count` skema 2 **tidak sebanding** dengan skema 3 | aturan di [[03-Data/D5 - Record Schemas]] |

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
- **GDELT DOC API**: `429` di dua jaringan (laptop dengan jeda 6 detik **dan** runner GitHub) →
  klaim lama "cuma butuh pacing" resmi **dicabut**. Yang hidup: jalur berkas mentah
  (`data.gdeltproject.org/gdeltv2/lastupdate.txt` → GKG) dengan TLS sah di kedua jaringan.
  Sumber: [[06-Results/03 - Not Yet Proven]] baris 8 · [[03-Data/01 - Dataset]].
- **CryptoPanic**: `403` tanpa akun, di laptop **dan** runner — bukan soal jaringan, soal akun
  ([[06-Results/03 - Not Yet Proven]] baris 8).
- Yang **tidak** kami punya sama sekali: order book L2, footprint/tick, heatmap likuidasi,
  histori funding per-aset yang bisa ditarik mundur, jadwal unlock/vesting, MVRV/SOPR/NUPL,
  exchange reserve. Status tiap metode di `03-Sinyal/` memakai enum di [[Aturan Subtree]].

## D. Ongkos — satu-satunya bagian yang sudah kami ukur sendiri

| nama | nilai | provenance |
|---|---|---|
| round-trip di venue demo kami | **59 bps** posisi 1 unit (kurva x·y=k + fee 30 bps, **bukan** gas mainnet) | `forge test --match-test test_round_trip_...` → [[07-Testing/T3 - Execution Suite]] |
| realized round-trip nyata di 97 | **−59 bps** per putaran, dibaca dari event `Closed` | `decisions/execution-trail.jsonl` · [[Concepts/Cost Is Fixed]] |
| model biaya warisan dari proyek rujukan | 5,5 bps fee + 4,5 bps slip **per sisi** = 10 bps/sisi → **20 bps round-trip**; ambang efektifnya **2×** ongkos (gross > 40 bps) | [[06-Results/02 - Thresholds]] |
| ongkos tetap $0,05 bolak-balik pada $1 | butuh **+5 %** cuma untuk balik modal — dan tabel itu **estimasi mainnet, belum diukur di repo ini** | [[01-Agent/A4 - Trust Gating and Real-Money Rules]] |
| gas testnet 97 | **0,10 gwei** live; guard lama memakai floor **1 gwei** → menolak karena plafon sendiri | `08-Backlog` P1 |

**P10 masih terbuka:** menyatukan 59 bps terukur dengan 20 bps asumsi di seluruh jalur uji.
Angka mana pun yang digabungkan dengan 20 bps harus menyebut bahwa ongkos terukur kami 3× lipat.

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
| panel whale GMGN, horison per jam | **win rate 69,8 % tapi −10,4 bps per jam** | F-D16 di [[00-Overview/03 - Decisions]] |
| smart money vs kerumunan, berpasangan per (token, jendela 4 j) | mentah: panel **+680,7 bps** vs kontrol **+336,4 bps** (51.863 entri swap BSC, 10 hari, ongkos 20 bps). Berpasangan & drift terbuang: **selisih −10,4 bps, p=0,568** → tidak berbeda dari kerumunan; 54 wallet capai n≥20, **0 lolos BH** | `tools/smartmoney_score.py` → [[06-Results/04 - Negative Results]] §4c |
| dua `Enter` yang jatuh tempo | **+1,5 bps** dan **−146,3 bps** net (n=2) | [[06-Results/03 - Not Yet Proven]] baris 16 |
| jalur eksekusi nyata | 3 putaran chain, **WR 0 %**, net −59,0 bps rata-rata — dan itu memang **ongkos**, bukan sinyal (pool kami sendiri tanpa arus luar) | `tools/winlog.py` |
| `\|acf\|` MARSCOIN | 0,075 → **zona abu-abu** (0,05–0,10 = belum tahu) | [[06-Results/03 - Not Yet Proven]] |
| `security_gate` pada kandidat arah | 5/5 membalas: 4 `OK` + 1 `UNMEASURED` (`pPOLY is_honeypot=None` tidak dihitung bersih) | [[04-Tools/TL3 - security_gate]] |

## G. Keadaan hidup saat halaman ini ditulis (28 Sep 2026)

```
python -X utf8 tools/anchor.py --verify   -> anchorCount() = 19 | 13 baris terpelacak | 13/13 COCOK
python -X utf8 tools/winlog.py            -> PAPER n=2 WR 50,0 % net rata2 -72,4 bps (total -144,8)
                                             CHAIN n=3 WR 0,0 % net rata2 -59,0 bps (total -177,0)
                                             streak chain: 3 KALAH | terpanjang menang 0
                                             gerbang F-D16: n>=20 -> BELUM (kurang 17)
git fetch origin                          -> lokal 1 commit di depan, 188 di belakang
git log --oneline HEAD..origin/master     -> SEMUANYA commit data ("wallet flow" / "snapshot
                                             universe"): nol commit non-data di antaranya
```

`19 vs 13` itu lubang yang tercatat (P6b di [[08-Backlog/01 - Backlog]]), bukan keberhasilan.
Angka blok G basi dalam hitungan jam: jangan mengutipnya dari halaman ini, jalankan perintahnya.

## H. Alat yang angkanya **belum boleh** dikutip

| alat | kenapa belum | rem yang sudah terpasang |
|---|---|---|
| `tools/maker_ledger.py` | distribusi `\|net\|` per lot tidak masuk akal: median **4.558,3 bps**, p90 **23.989,3**, maks **1.222.045,4**, **71,0 %** lot di atas 2000 bps → mekanika (satuan harga, arti `is_open_or_close`, MTM token hilang) belum beres. Dibaca ulang 28 Sep: **6.704 dari 13.999** baris jatuh ke kombinasi `(b,c)` yang tidak dipakai alatnya, **902** jual yatim, **3.818** lot masih terbuka saat dinilai-taup | alatnya sendiri mencetak "REM SEHAT … Mean di bawah jangan dikutip"; jalankan: `python -X utf8 tools/maker_ledger.py` |
| `tools/whale_cohorts.py` | struktural (median **2 maker/simbol**, **49,8 %** simbol cuma 1 maker, HHI median **0,347**) — kokohnya belum diuji terhadap hasil | dilaporkan sebagai **breadth**, bukan sebagai skor |
| `decisions/whale-sweep-90d.json` | `cost_bps_applied = 0.0` → **SEMUA** angka horison di berkas itu GROSS; dan `p_boot` identik `0,00024993751562109475` di 4 horizon **belum terjelaskan** | `tools/whale_report.py` mencetak `cost_bps_applied` paling awal |

Angka blok H dikutip sebagai " Kami menemukan …" = klaim palsu. Boleh dikutip hanya sebagai
"alat kami sedang rusak karena sebab yang diketahui: …".

**Terkait:** [[Aturan Subtree]] · [[03-Data/D2 - Wallet Flow]] · [[03-Data/D3 - Price Depth]] ·
[[06-Results/02 - Thresholds]] · [[06-Results/04 - Negative Results]] · [[Quick-Reference]]
