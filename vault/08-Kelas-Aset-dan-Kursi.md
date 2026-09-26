---
type: spec
status: draft-untuk-dikerjakan
ditulis: 2026-09-25 (H-5)
sumber-angka: korpus lama HeliQuant (disebutkan per file) + hasil ukur Fabius
---

# 08 — Kelas aset, kursi, dan cara agen menganalisis

Dua keputusan builder yang jadi dasar dokumen ini (24–25 Sep):
1. agen **bebas memilih aset**, maksimal **5 kursi**, kursi dilepas kalau jelek dan diisi kandidat lain;
2. arah wajib ada: **long/short, kapan, seberapa banyak, seberapa lama** - bukan cuma "enter".

Yang TIDAK ada di dokumen ini: angka win-rate atau janji profit. Registry boleh dan kemungkinan
besar akan tetap kosong; itu hasil, bukan kegagalan.

## 1. Tujuh bidang data (plane) dan apa yang benar-benar kita punya

| Bidang | Sumber terukur | Status di Fabius |
|---|---|---|
| ① deret harga | **Aster `fapi/v1/klines` (BNB-native, tanpa API key): 9.599 bar / 400 hari** di 7 halaman (`tools/bars.py`); Hyperliquid `candleSnapshot` 5.001 bar/208 hari sekali tarik; GMGN `token_kline` mentok **1.000 bar = 41,6 hari**, dan **0 bar untuk token gas**; GeckoTerminal **1.000 bar**, pool baru **30 bar** | ✅ 25 Sep: `tools/bars.py` menarik & men-cache BNB/ETH/**1000PEPE** |
| ② perilaku pembeli | GMGN `market/rank`: `bundler_rate`, `sniper_count`, `smart_degen_count`, `rug_ratio`, `top_10_holder_rate`, `lock_percent` (100 kandidat/jendela) | ✅ wired di perekam |
| ③ derivatif | **Aster `premiumIndex` + `openInterest`** (608 kontrak, `Meme` 61, `AI` 42; funding per **4 jam**: BNB +0,0000% mark 778,45 OI 7.832 · ETH +0,0100% · SOL −0,0020% · HYPE −0,0018% · DOGE +0,0044%) · Hyperliquid `metaAndAssetCtxs` 234 perp sebagai pembanding | ✅ wired di `tools/direction.py`: funding ekstrem (>0,05%/4j) = tolak posisi, karena biayanya lebih besar dari edge yang kita klaim |
| ④ keamanan kontrak | GMGN `token/security` (terukur **28 field**, `is_honeypot` boolean, `can_not_sell`, `can_sell`, `buy_tax`, `sell_tax`); GoPlus `token_security/56` (TIDAK punya `can_not_sell`) | ✅ 25 Sep wired di **jalur arah** lewat `tools/security_gate.py` — 5/5 kandidat membalas GMGN 200 dan 5/5 GoPlus 200. Catatan yang membuat ini berguna: `vault/05` #12 (jalur SCREEN) tetap mati karena beban 40 alamat/snapshot; jalur arah cuma **≤5 kandidat** jadi 10 panggilan/siklus. Dua sumber **tidak sepakat** soal pajak jual (MARSCOIN & ASTEROID: GMGN 3 % vs GoPlus 0 %) — aturannya selisih ≥5 % menurunkan status ke `DISAGREE`, jadi 3 % ini tetap `OK` TAPI tercatat sebagai perbedaan sumber, bukan kesepakatan. Kandidat dengan field kunci null jadi `UNMEASURED` (contoh terukur: pPOLY `is_honeypot=None`) dan **tidak** dihitung bersih |
| ⑤ perhatian/narasi | GDELT `gkg` tema + nada (602 artikel; `GOVERNMENT 203`, `REGULAT 45`, `SANCTION 17`, nada −1,005); CoinGecko trending; CoinDesk RSS | ✅ wired (skema 4) |
| ⑥ kapasitas keluar | likuiditas pool + volume: **80 dari 140** kandidat < $50.000 | ✅ terukur |
| ⑦ arus smart money | GMGN `user/kol` & `user/smartmoney`: **100 transaksi/panggilan** dengan `maker`, `side`, `is_open_or_close`, `buy_cost_usd`, `price_usd`, `base_address`, `timestamp`, `maker_info.tags` | ✅ **25 Sep wired & berdetak**: `universe/record_wallet_flow.py` + `.github/workflows/wallet-flow.yml` (cron `*/10 * * * *`, 2 tarikan berjarak 5 menit per jalanan). Sifat aliran yang WAJIB dibaca sebelum siapa pun mengandalkan datanya: jendela lihatnya **8-13 menit** dan **semua parameter paging diabaikan server** (`offset`/`page`/`page_no`/`end_ts` → head yang sama, overlap 98/100, baris baru 1) — yang tidak terekam **hilang permanen**, berbeda total dari kline Aster yang bisa ditarik 400 hari. Demo key publik sudah melayani rute ini (200, isi identik dgn kunci privat) → Actions **tanpa secret**. Kelompok **kontrol TIDAK tersedia**: cuma **1 dari 199** baris tanpa tag `smart_degen`/`launchpad_smart`/`kol`, jadi pembandingnya diganti lewat desain (§7), bukan dengan menambah data |

## 2. Delapan kelas aset

| Kelas | Contoh | Bidang yang ADA | Yang boleh dinyatakan | Cara mati | Short? |
|---|---|---|---|---|---|
| A Mayor | BTC ETH SOL BNB | ①③⑤⑥⑦ | arah + vol-target + carry | rezim berubah | ✅ perp |
| B Blue-chip eco / L1-L2 / DeFi | CAKE SUI HYPE DOGE LTC | ①③⑤⑥⑦ (+unlock schedule, belum ada sumbernya) | arah, carry, spread | narasi mati, dump unlock | ✅ perp |
| C1 Memecoin **ber-perp** | 61 kontrak terukur: `1000PEPE`, `DOGE`, `1000SHIB`, `1000FLOKI`, `WIF`, `CAT` | ①③②⑤⑥⑦ (① 9.599 bar) | arah penuh: long/short + carry, horizon 4 jam, stop di struktur | basis terlepas; funding flip; likuiditas jauh lebih tipis dari A/B | ✅ perp |
| C2 Memecoin **spot-only** | token jam–hari di `trending_pools` tanpa kontrak | ②④⑤⑥⑦, ① pendek (≤1.000 bar) | **kelayakan masuk/keluar**, bukan arah | LP ditarik; 10 wallet dominan | ❌ |
| D Peluncuran baru | `new_pools` (menit) | ④⑤⑥ | **veto saja** | 0 bar = tidak ada yang bisa diuji | ❌ |
| E Token fundamental | TVL/fee/revenue | ⑤ + TVL | tesis nilai, horizon panjang | metrik telat/dimanipulasi | ❌ |
| F Stable/collateral | USDT USDC | ⑤⑥ | mesin risiko (depeg = matikan kursi) | depeg | ❌ |
| G Wrapped/pasangan stabil | BTCB WBNB USDT | — | **bukan aset yang bisa dipilih** (`not_a_choosable_asset`, terukur 4/jendela) | — | — |
| H Token peristiwa | politik/"AI"/tren X | ⑤②⑥ | attention-driven; sinyal terbaik = **attention berhenti** | attention habis | ❌ |

## 3. Kursi: 5 seat, per kelas, dengan status

```
DRAFT harian (maks 5)
  gerbang masuk  : ① >=480 bar  · ④ terukur (honeypot/can_not_sell TIDAK null)
                   · ⑥ liq>=50k dan exit-size <= 1% liq  · spread masuk akal
  skor           : |autocorrelation| (inefisiensi) + funding/OI + vol + arus ⑦ (maker beli vs jual)
                   + 1 panggilan Jev bertipe: side{long|short|flat} + exit_risk(noul)
  keluaran       : 5 kursi + alasan tiap kursi -> anchor("DRAFT")
```

Gerbang di atas **sudah jadi kode** sejak 25 Sep: `direction.apply_gates()` menegakkan ①+④+⑥ dan
menulis hasilnya ke `seat_eligible` + `seat_blockers`, yang ikut masuk `gatesHash`. Contoh nyata
dari siklus 19:06:58Z: `GENIUSUSDT` ④ bersih dan ① 3.940 bar, tapi kursinya **ditolak** karena
`⑥liq=$19.388 < $50.000` — persis alasan kolom ini tidak boleh disamakan dengan "honeypot-nya
bersih". (Versi pertama fungsi ini bernama `apply_security` dan menetapkan `seat_eligible` dari ④
saja; itu salah klaim, jadi syaratnya yang disamakan ke namanya, bukan sebaliknya.)

Status kursi (kita pakai ambang **korpus HeliQuant**, disebut per file - Fabius belum punya kode rotasinya, `seats.py` masih kosong):

| Peristiwa | Tindakan | Ambang & asal |
|---|---|---|
| baru diisi | `OBSERVASI`: ukuran kecil, **tidak ikut statistik**, tidak boleh klaim apa pun | - |
| rugi 1 kali | **kecilkan** ×`ASSET_COLD_FADE=0,5`, bukan pecat | `Mantle-Hackathon/agents/firm/campaign.py:76-81` |
| n>=8 & WR<0,42 & net<0 | **cold -> lepas kursi**, isi dari peringkat | idem (`ASSET_MIN_N`, `ASSET_COLD_WR`) |
| n>=8 & WR>=0,55 & net>0 | warm ×1,3 ; WR>=0,66 ×1,6 | idem (tetap di bawah ×2) |
| n>=20 cost-aware OOS + stability + **2 siklus data baru beruntun** | `VALIDATED` → ×2 dibuka | `edge_lab.py:30,126` + `scripts/60_self_learn.py:38-39,136-142` |
| drawdown akun >= 0,20 | semua kursi paksa SAFE | `trade_ticket.py:41` |
| biaya | 5,5 bps taker + 4,5 bps spread/slippage **per sisi** = 20 bps round-trip; syarat edge net>20 bps ⇒ **gross>40 bps** | `edge_lab.py:23,24,28,121,125` |

Kenapa "1 rugi ≠ lepas" - angkanya: win-rate SUI di korpus lama **58,2%** ⇒ peluang satu trade rugi ≈ 42%; dengan 5 kursi aturan itu membuang ~2 kursi/hari **karena noise**. Lab HeliQuant sudah menamai penyakit ini: HYPE **+92% OOS** → **65% dari satu fold** → buang fold terbaik = **+1,9%** (`scripts/59_onboard_asset.py` + `edge_lab.py`, temuan #20).

## 4. Horizon: 4 jam, dan alasannya jujur

Ambang 20 penutupan per kursi ÷ 6 hari tersisa ⇒ horizon 24 jam hanya menghasilkan ~5 penutupan/kursi (tidak pernah lolos `ASSET_MIN_N` pun). Horizon **4 jam** ⇒ ~30 penutupan/kursi. Semua klaim "edge" di dokumen ini karena itu memakai horizon 4 jam dan akan ditulis begitu di README, bukan diam-diam.

Catatan kedalaman (dikoreksi 25 Sep): sebelumnya kutulis "hanya deret Hyperliquid yang bisa
walk-forward" - itu salah, dan sumber kesalahannya adalah aku membatasi permintaanku sendiri
(`startTime=700 jam`), bukan server. Terukur lewat `tools/bars.py`: **Aster memberi 9.599 bar
hourly = 400 hari** untuk `BNBUSDT`, `ETHUSDT`, dan **`1000PEPEUSDT`**. Jadi `5-fold walk-forward`
(≥2.400 bar) sekarang terbuka untuk **A, B, dan C1 (meme ber-perp)** dari venue BNB-native, dengan
Hyperliquid sebagai pembanding silang. Yang **tetap** tidak bisa divalidasi: **C2 dan D** - tanpa
kontrak perp, deretnya mentok 41,6 hari, dan memecoin berumur beberapa jam tidak punya masa lalu
yang bisa diuji.

Kebetulan yang menguntungkan dan akan kucatat sebagai kebetulan, bukan sebagai desain: funding
Aster dihitung per **4 jam**, sama dengan horizon keputusan kita - jadi fitur carry dan horizon
saling cocok tanpa penyesuaian.

## 5. Yang belum ada di kode (jangan dibaca sebagai kemampuan)

Belum ada (per 25 Sep, 20:30Z): `seats.py` (draft + rotasi + skor), `smartmoney_score.py` (penilai ⑦ — datanya sudah mulai direkam, alat penilainya belum), `gateway/` x402 (jualan keluaran), `verify_8004.py` (baca ulang identitas agen dari registry resmi).

SUDAH ada sejak dicoret di baris ini: `security_gate.py` (④, 25 Sep), `ledger.py` (penutupan & expectancy bps bersih, 25 Sep), `universe/record_wallet_flow.py` + `.github/workflows/wallet-flow.yml` (⑦, 25 Sep).

**Sudah ada per 25 Sep:** `bars.py` (①), `direction.py` (①③ + arah via Jev), `decide.py` (veto + hash), `judge.py` (penilai, veto satu arah, + `ask_jev()` utk pertanyaan per-kandidat), `DecisionAnchor` + 21 test + verifikasi chain 97, perekam universe.

Hasil siklus pertama `direction.py` (25 Sep, universe 2026-09-24T14:10:36Z, 140 baris): **9** kandidat ternyata punya kontrak perp di Aster, **3** layak kursi (≥720 bar), **5** dibuang karena sejarah pendek. Keluarannya:

| simbol | bar | \|acf\| | funding 4j | model | veto | keputusan |
|---|---|---|---|---|---|---|
| MARSCOINUSDT | 1.224 | 0,075 | +0,0050% | short | 0,40 | **short**, time-stop 24j, risiko 0,5%, entry 0,11605 stop 0,12237 target 0,10341, exit-cap ≤ $17.288 (1% liq) |
| TACUSDT | 3.700 | 0,029 | +0,0097% | flat | 0,47 | **flat** — rezim `efficient`: \|acf\| < 0,05 = mendekati jalan acak |
| FLNCUSDT | 2.908 | 0,016 | +0,0000% | flat | 0,28 | **flat** — `efficient` |

Dua hal yang harus dibaca dari tabel ini, karena keduanya bukan kosmetik:
1. **Model pernah bilang "short" untuk kandidat yang kita tolak.** BREWUSDT dan GSTOCKUSDT dapat jawaban `short` dari Jev, tapi `bar=422`/`99 < 720` → keputusannya tetap `flat`. Itulah bukti gerbang menentukan dan model hanya boleh mengurangi (doktrin `judge.py` §1), bukan bukti di komentar.
2. **Yang sejarahnya paling dalam justru tidak bisa diperdagangkan.** `TAC` (3.700 bar) dan `FLNC` (2.908 bar) lolos ambang walk-forward 2.400 tapi \|acf\| 0,029/0,016 artinya deretnya mendekati jalan acak — jadi *kedalaman tanpa struktur tidak membeli apa pun*. Yang lolos ke keputusan malah yang 1.224 bar, dan itu pun ditandai "layak dinilai, TIDAK layak diklaim sebagai edge".

Biaya siklus: **6 pertanyaan = 3 kursi × (arah + exit-risk) dalam SATU panggilan** → 958 token masuk / 186 keluar, 1,2 s, **$0 lewat router** (angka promo pihak ketiga, bukan harga Jev; jalur berbayar Typesafe terukur $0,042/MTok masuk, output gratis).

**Siklus kedua, 19:06:58Z** (setelah perekam dijalankan ulang secara lokal — lihat catatan cron di
bawah): **12** kandidat punya kontrak perp (naik dari 9 karena daftar asetnya yang segar, bukan
karena kodenya berubah), **11** dinilai, **4** layak kursi, **7** dibuang karena bar < 720.
8 pertanyaan → 1.177/250 token, 6,4 s. Keputusan dari siklus pertama (7 baris) **sudah masuk
chain 97** lewat `tools/anchor.py`: `anchorCount()` 2 → 9, `Enter=1` / `Abstain=8`, semua cocok
word-per-word saat dibaca ulang (rinci di `07-Deploy-97.md`).

## Cron GitHub: yang terjadi sebenarnya (dan koreksi atas kalimatku sendiri)

Versi pertama bagian ini menyimpulkan "cron tidak dipersenjatai" karena
`GET /actions/workflows/{id}/schedule` membalas **404** sementara `state=active`. Kesimpulan itu
**salah**, dan dibantalkan oleh fakta yang terjadi selagi kalimatnya ditulis: Actions mengirim
snapshotnya sendiri, commit `f721768` = `snapshot universe 2026-09-24T19:04:48Z [skip ci]`.
Endpoint 404 itu tidak melayani repo ini; ia bukan bukti jadual mati. (Pola kesalahan yang sama
pernah kulakukan pada GDELT: menyimpulkan "mati" dari satu respons, bukan dari riwayat.)

Yang benar, dari `gh api .../workflows/365677926/runs` + `manifest.txt`:

| | |
|---|---|
| cron yang ditulis | `9 * * * *` (setiap jam di menit 9) |
| jam tembakan yang tercatat | 08:22:05Z · 14:10:27Z · 19:04:48Z |
| cocok dengan menit-9? | **tidak satupun** |
| jam yang hilang total | 15:00–19:00 (gap terbesar antar-snapshot **16,31 jam**; 5 gap > 2 jam dari 54 snapshot) |

Jadi pemicunya **hidup tapi tidak bisa dijadwalkan sebagai jaminan**. Untuk proyek yang klaim
utuhnya adalah "kami merekam sebelum tahu hasilnya", itu bukan detail operasional: satu jam yang
dilewati = satu jendela yang hilang untuk selamanya, dan tidak bisa disusulkan (GMGN/Hyperliquid
tidak mengembalikan apa yang tidak kita ambil saat itu).

Dua hal yang menahan kegagalannya sekarang, bukan niat:
1. **`direction.py` mengukur dan menyimpan umur snapshot.** Baris `UMUR x jam` + `PERINGATAN`
   muncul di layar, dan `universe_age_h`/`universe_utc` ikut masuk ke objek yang di-hash →
   keputusan di atas data basi tetap terlihat basi **sampai ke `snapshotHash`-nya**, jadi tidak
   bisa disajikan kemudian sebagai "kami tahu lebih awal".
2. **Perekam boleh dijalankan sekali** (`python universe/record_bsc_universe.py`, ±8 detik,
   tanpa `--loop`) untuk menutup lubang. Itulah yang mengubah siklus 14:10:36Z (9 kandidat
   ber-perp, 3 kursi) jadi 19:06:58Z (12 kandidat, 4 kursi) — buktinya bukan kode yang berubah.

Yang masih terbuka dan harus ditulis apa adanya: penulis jam ini tetap **satu-satunya** (Actions
atau laptop, jangan keduanya — dua penulis di satu JSONL sudah dua kali memicu konflik union),
dan sampai ada pemicu yang bisa dijamin, dataset kita akan terus punya lubang yang tercatat di
`manifest.txt`.

## 6. Cara menilai ⑦: kontrol tidak tersedia, jadi pembandingnya yang diganti

Rencana awalnya: bandingkan hasil wallet `smart_degen` dengan wallet biasa dari aliran yang sama,
sebagai kontrol. **Terukur 25 Sep: kontrol itu tidak ada.** Dari 199 transaksi pertama, hanya
**1** baris yang tidak membawa tag `smart_degen`/`launchpad_smart`/`kol`. Aliran ini memang
didefinisikan sebagai "dompet yang sudah dilabeli pintar oleh GMGN" — jadi membandingkannya dengan
"dompet biasa dari sumber yang sama" mustahil secara struktural, bukan soal kurang data.

Kalau begitu jangan dilepas tanpa pembanding, dan jangan dicari-cari. Pembanding yang sah dan bisa
dihitung dari data yang SUDAH kita rekam:

| pembanding | definisinya di alat nanti | apa yang boleh disimpulkan |
|---|---|---|
| **waktu yang sama, token yang sama, arah acak** | harapan arah acak = 0, jadi selisih rata-rata `net_bps` sebuah wallet vs 0 adalah pertanyaan "arahnya lebih baik dari lemparan koin *pada saat dia masuk*?" | ini satu-satunya kontrol yang benar-benar bebas dari label pihak ketiga |
| **hold token 4 jam** | `price_usd` kita sendiri di `t` dan di `t+4h` (baris `px`), TANPA memilih arah | memisahkan "pintar milih arah" dari "token lagi naik" |
| **`is_open_or_close=1` vs `=0`** | kelompok di dalam aliran yang sama | apakah yang dia lakukan itu membuka posisi atau menutup — dua hal berbeda yang jangan dicampur rata-ratanya |

Yang **tidak** akan kita klaim, dan ini bagian yang paling goda: "smart money menang" hanya karena
rata-ratanya positif. Dengan ±217 transaksi unik setelah dua tarikan, satu wallet paling sering cuma
muncul belasan kali, dan `MIN_TRADES=20` per wallet akan lolos untuk **sebagian kecil** dompet.
Karena itu:

1. **SATU tes per wallet**, lalu **Benjamini–Hochberg α=0,10 lintas wallet** (aturan `vault/02`;
   tanpa ini, dari 500 wallet selalu ada ~25 yang "signifikan" karena nasib).
2. **Ongkos 20 bps RT** dipakai sejak awal — `vault/09` sudah menunjukkan gross kecil mati oleh ongkos.
3. **Hasil negatif ditampilkan**, bukan dibuang. Kalau panel smart money juga tidak mengalahkan
   lemparan koin setelah ongkos, itu Temuan #1 untuk Fabius dan justru membuat x402 feed kita
   berharga: orang membayar untuk *mengetahui*, bukan untuk *dijanjikan*.
4. **Anggota panel dicatat dengan timestamp.** Keanggotaan hari ini tidak boleh dipakai menilai
   transaksi minggu lalu — itu lookahead yang sama yang membuat label sewaan terlihat hebat.
   Beruntungnya, untuk aliran ini memang mustahil menarik mundur, jadi kelicikan itu tertutup
   oleh fisika datanya, bukan oleh kesadaran kami. Ini harus ditulis begitu di submission.

Ambang klaim yang diizinkan: `n>=20` per wallet **dan** `net>0` **dan** lolos BH **dan** stabil
setelah fold terbaik dibuang — persis ambang yang membuat registry kita kosong (`vault/09`).
