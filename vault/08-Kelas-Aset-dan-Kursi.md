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

## 1. Enam bidang data (plane) dan apa yang benar-benar kita punya

| Bidang | Sumber terukur | Status di Fabius |
|---|---|---|
| ① deret harga | **Aster `fapi/v1/klines` (BNB-native, tanpa API key): 9.599 bar / 400 hari** di 7 halaman (`tools/bars.py`); Hyperliquid `candleSnapshot` 5.001 bar/208 hari sekali tarik; GMGN `token_kline` mentok **1.000 bar = 41,6 hari**, dan **0 bar untuk token gas**; GeckoTerminal **1.000 bar**, pool baru **30 bar** | ✅ 25 Sep: `tools/bars.py` menarik & men-cache BNB/ETH/**1000PEPE** |
| ② perilaku pembeli | GMGN `market/rank`: `bundler_rate`, `sniper_count`, `smart_degen_count`, `rug_ratio`, `top_10_holder_rate`, `lock_percent` (100 kandidat/jendela) | ✅ wired di perekam |
| ③ derivatif | **Aster `premiumIndex` + `openInterest`** (608 kontrak, `Meme` 61, `AI` 42; funding per **4 jam**: BNB +0,0000% mark 778,45 OI 7.832 · ETH +0,0100% · SOL −0,0020% · HYPE −0,0018% · DOGE +0,0044%) · Hyperliquid `metaAndAssetCtxs` 234 perp sebagai pembanding | ✅ wired di `tools/direction.py`: funding ekstrem (>0,05%/4j) = tolak posisi, karena biayanya lebih besar dari edge yang kita klaim |
| ④ keamanan kontrak | GMGN `token/security` (34 field, `is_honeypot`, `can_not_sell`); GoPlus `token_security/56` | ⬜ **belum wired** → hari ini `honeypot=0` artinya **tidak diukur**, bukan bersih |
| ⑤ perhatian/narasi | GDELT `gkg` tema + nada (602 artikel; `GOVERNMENT 203`, `REGULAT 45`, `SANCTION 17`, nada −1,005); CoinGecko trending; CoinDesk RSS | ✅ wired (skema 4) |
| ⑥ kapasitas keluar | likuiditas pool + volume: **80 dari 140** kandidat < $50.000 | ✅ terukur |
| ⑦ arus smart money (BARU) | GMGN `user/kol` & `user/smartmoney`: **100 transaksi/panggilan**, `maker`+`side`+`buy_cost_usd`+`is_open_or_close`+`timestamp` | ⬜ baru ditemukan 25 Sep, belum wired |

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

Status kursi (kita pakai ambang **korpus HeliQuant**, disebut per file - Fabius belum punya kode ini):

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

Belum ada: `security_gate.py` (④), `smartmoney_flow.py` (⑦), `seats.py` (draft+rotasi+skor), `ledger.py` (penutupan & expectancy bps bersih).

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
