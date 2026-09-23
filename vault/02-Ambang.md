# 02 — Ambang

Setiap angka di sini punya asal. Yang tidak punya `asal` atau `diverifikasi` bukan ambang — itu
dugaan, dan jangan dipakai di kode atau di submission.

## Gerbang penolakan (veto) — dipakai perekam universe

| Ambang | Nilai | Alasan yang bisa diucapkan | Asal | Diverifikasi |
|---|---|---|---|---|
| `MIN_LIQ_USD` | 50.000 USD | di bawah ini ukuran posisi apa pun menghancurkan harga keluar | diputuskan, bukan diukur | 22 Sep 2026 |
| `MIN_AGE_SEC` | 24 jam | token lebih muda tidak punya satu pun bar untuk diuji; menolak = jujur, meloloskan = tebakan | konsekuensi aritmetika jendela data | 22 Sep |
| `MAX_TOP10` | 45% supply | satu keputusan bisa menghapus pasar | diputuskan | 22 Sep |
| `MIN_LOCK` | 20% LP terlock | di bawah ini likuiditas bisa ditarik kapan saja | diputuskan | 22 Sep |
| `MAX_BUNDLER` | 30% | "volume" itu satu orang berpakaian banyak topeng | diputuskan | 22 Sep |
| `MIN_HOLDER` | 60 alamat | di bawah ini "jumlah pemegang" belum berarti | diputuskan | 22 Sep |
| `MIN_VOL_OVER_LIQ` | vol24/likuiditas ≥ 0,10 | trending tanpa permintaan nyata | diputuskan | 22 Sep |
| `STABLE_BASES` | USDT/USDC/BUSD/FDUSD/DAI/TUSD/USD1/USDD/USDE + BTCB/WBNB/BNB/ETH | base-nya bukan aset yang bisa dipilih; pool `USDT/WBNB` adalah likuiditas stablecoin, bukan kandidat | terukur: 4 baris/window tersaring | 22 Sep |

Empat angka pertama **masih perlu diuji terhadap hasil**, bukan dipertahankan karena sudah ditulis.
Cara mengujinya sudah ada: bandingkan outcome token yang kena tiap veto vs yang lolos
(`tools/screen_universe.py`, dan keputusan per-jendela di `tools/decide.py`). Kalau sebuah veto
ternyata tidak memprediksi hasil yang lebih buruk, ia harus dicabut dan itu dicatat di sini.

**Syarat sebelum kalibrasi itu boleh dijalankan: pisahkan "ditolak" dari "tidak bisa dinilai".**
Terukur 23 Sep pada jendela 03:00Z, dari 90 baris: **37** tidak punya field perilaku sama sekali
(`top10`/`lock`/`bundler`/`holders_unmeasured`), dan **13** di antaranya gugur *tanpa satu pun
alasan risiko*. Kalau kelompok ini dihitung sebagai "penolakan yang benar", kita sedang
mengkalibrasi ambang risiko di atas angka yang sebenarnya mengukur **kegagalan penggabungan
GeckoTerminal ↔ GMGN** — terukur cuma **5 dari 40** baris pool yang ketemu baris GMGN. Karena itu
`decide.py` memulangkan dua daftar (`risk_vetoes` vs `data_gaps`) dan `ENTER` mensyaratkan
keduanya kosong; `05-Belum-Terbukti.md` baris 12 adalah lubang yang harus ditutup lebih dulu.

## Model biaya — dirujuk dari kode, bukan dari prosa

| Nama | Nilai | Satuan | Asal |
|---|---|---|---|
| `FEE_SIDE` | 0,00055 | 5,5 bps **per sisi** (taker) | `HeliQuant agents/firm/edge_lab.py:23` |
| `SLIP_SIDE` | 0,00045 | 4,5 bps **per sisi** (spread+slippage) | `edge_lab.py:24` |
| `COST_SIDE` | 0,0010 | 10 bps per sisi = jumlah keduanya | `edge_lab.py:28` |
| round-trip | 20,0 bps | 2 kaki | `edge_lab.py:110,123` |
| **ambang edge** | net > 20 bps ⇒ **gross > 40 bps** | per trade horizon 24 jam | `edge_lab.py:121,125` |

Dua catatan yang wajib ikut kalau angka ini dikutip siapa pun:

1. **"cost-aware ~20 bps" di dokumen itu BIAYA-nya, bukan ambangnya.** `avg_bps` sudah dikurangi
   `2*COST`, lalu gerbangnya meminta `avg_bps > rt_fee_bps` — jadi ambang efektifnya dua kali
   biaya. Spanduk `scripts/59_onboard_asset.py:39` salah cetak (memakai `FEE` → 11 bps) sementara
   gerbang sejatinya memakai `COST` → 20. Satu run mencetak dua angka ambang.
2. **jalur backtest OHLC tidak memakai model biaya yang sama.** `scripts/15_validate_universe.py:40,96`
   = 10 bps/sisi **fee-only, nol slippage**, dan `LOOKAHEAD = 8` artinya horizon **8 jam cooldown**,
   bukan non-overlap 24 jam. Angka dari jalur itu tidak sebanding dengan angka `edge_lab` dan tidak
   boleh dikutip dengan label yang sama.

## Kontrol statistik yang akan dipakai

| Nama | Nilai | Asal / catatan |
|---|---|---|
| `MIN_SAMPLES` | 20 trade OOS non-overlap | `edge_lab.py:30,126` |
| BH-FDR `alpha` | 0,10 | `edge_lab.py:67` — step-up-nya benar; **keluarganya di kode rujukan hanya per-aset (m ≤ 4)**. Yang tidak ada padanan kodenya di sana: koreksi **lintas aset**. Fabius wajib satu-tes-per-token. |
| p-value | satu arah, aproksimasi **normal** | `edge_lab.py:57,61-64`. Pada n=20–40 ini membuat p **sistematis terlalu kecil**. Kami mewarisi bentuknya supaya sebanding, dan menulis kelemahannya, bukan memolesnya. |
| lifecycle | `candidate` → `validated` butuh konfirmasi pada siklus **data baru** berurutan | rujukan: `scripts/60_self_learn.py:38-39,136-142` — di sana konfirmasi pertama **gratis** dan `consecutive` **tidak ditegakkan** (tidak ada reset penghitung). Fabius menegakkan keduanya. |

## Yang secara sengaja TIDAK kami pakai

- **`payoff > 0`** sebagai syarat: `edge_lab.py:120,126` membuat edge dengan **win rate 100%**
  justru **gagal** (tidak ada trade rugi ⇒ `payoff = 0.0`). Bug, bukan fitur. Fabius memisah
  "tidak terhitung" dari "nol".
- **`isnan` untuk menyaring sinyal**: `pct_change` atas basis nol menghasilkan `inf`, dan
  `isnan(inf)` itu False ⇒ posisi diambil dari sinyal sampah, dan `inf >= p80` selalu benar.
  Pakai `isfinite`.
- **`VOL_HI = 0.60`** (`firm/asset_efficiency.py:30`): konstanta mati, tidak pernah dirujuk.
  Volatilitas tidak pernah jadi gerbang di sana, hanya pengeras skor lewat angka lain (0,5).
- **"drop the best fold" yang bersyarat**: `edge_lab.py:180` hanya membuang fold terbaik bila
  ada ≥ 4 fold terisi — dengan data 80–120 window, hampir selalu 3, jadi gerbang ketahanan
  itu tidak jalan sambil tetap mencetak kolom "ex-best-fold". Fabius membuang floor trade per
  fold dan mewajibkan trimming.
