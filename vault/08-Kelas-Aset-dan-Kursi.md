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
| ① deret harga hourly | Hyperliquid `candleSnapshot` BNB = **5.001 bar / 208,3 hari**; GMGN `token_kline` mentok **1.000 bar = 41,6 hari** dan **0 bar untuk token gas**; GeckoTerminal **1.000 bar**, pool baru **30 bar** | ⬜ belum ditarik ke kode |
| ② perilaku pembeli | GMGN `market/rank`: `bundler_rate`, `sniper_count`, `smart_degen_count`, `rug_ratio`, `top_10_holder_rate`, `lock_percent` (100 kandidat/jendela) | ✅ wired di perekam |
| ③ derivatif | Hyperliquid `metaAndAssetCtxs`: **234 perp**, funding + OI (BNB: OI 66.736, funding 0,001250 %/jam) | ⬜ belum wired |
| ④ keamanan kontrak | GMGN `token/security` (34 field, `is_honeypot`, `can_not_sell`); GoPlus `token_security/56` | ⬜ **belum wired** → hari ini `honeypot=0` artinya **tidak diukur**, bukan bersih |
| ⑤ perhatian/narasi | GDELT `gkg` tema + nada (602 artikel; `GOVERNMENT 203`, `REGULAT 45`, `SANCTION 17`, nada −1,005); CoinGecko trending; CoinDesk RSS | ✅ wired (skema 4) |
| ⑥ kapasitas keluar | likuiditas pool + volume: **80 dari 140** kandidat < $50.000 | ✅ terukur |
| ⑦ arus smart money (BARU) | GMGN `user/kol` & `user/smartmoney`: **100 transaksi/panggilan**, `maker`+`side`+`buy_cost_usd`+`is_open_or_close`+`timestamp` | ⬜ baru ditemukan 25 Sep, belum wired |

## 2. Delapan kelas aset

| Kelas | Contoh | Bidang yang ADA | Yang boleh dinyatakan | Cara mati | Short? |
|---|---|---|---|---|---|
| A Mayor | BTC ETH SOL BNB | ①③⑤⑥⑦ | arah + vol-target + carry | rezim berubah | ✅ perp |
| B Blue-chip eco / L1-L2 / DeFi | CAKE SUI HYPE DOGE LTC | ①③⑤⑥⑦ (+unlock schedule, belum ada sumbernya) | arah, carry, spread | narasi mati, dump unlock | ✅ perp |
| C Memecoin mapan | umur jam–hari, ada pool history | ②④⑤⑥⑦, ① pendek | **kelayakan keluar/masuk**, bukan arah | LP ditarik, 10 wallet dominan | ❌ |
| D Peluncuran baru | `new_pools` | ④⑤⑥ | **veto saja** | 0 bar = tak teruji | ❌ |
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

Catatan: `5-fold walk-forward` butuh ~2.400 bar hourly = 100 hari; bar GMGN mentok 41 hari, jadi **hanya deret Hyperliquid (208 hari) yang bisa dipakai walk-forward** - dan itu berarti hanya kelas A/B. Sekali lagi: **kelas C/D tidak akan pernah "lulus validasi"**, dan tidak akan kami klaim begitu.

## 5. Yang belum ada di kode (jangan dibaca sebagai kemampuan)

`security_gate.py` (④), `direction.py` (①③+Jev side), `smartmoney_flow.py` (⑦), `seats.py` (draft+rotasi+skor), `ledger.py` (penutupan & expectancy bps bersih). Saat dokumen ini ditulis, **fabius baru punya**: `decide.py` (veto + hash), `judge.py` (penilai, veto satu arah), `DecisionAnchor` + 21 test + verifikasi chain 97, perekam universe (52 snapshot / 32 jendela jam).
