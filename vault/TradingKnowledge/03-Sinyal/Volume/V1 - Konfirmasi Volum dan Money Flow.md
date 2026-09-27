---
tags: [tk, tk-sinyal, "V1"]
---

# V1 - Konfirmasi Volum dan Money Flow

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** filtering ([[PL2 - Menyaring Universe]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"20 Metode Paling Representatif & OP" — klaim
komunitas ("Volume & CVD … melihat siapa yang lebih agresif"), bukan hasil uji kami

**Ringkas:** Volum mengukur **seberapa banyak** yang berpindah, bukan **ke mana** harga pergi.
Fungsi yang sah = **syarat**: pergerakan tanpa partisipasi layak dicurigai, bukan dibeli.
OBV/CMF/MFI adalah cara membungkus arah dari volum, dan arah itu mereka beli dengan satu asumsi
murah — "bar naik = pembeli menang". Di pasar yang volumenya bisa dicetak sendiri (wash trading,
bundler), asumsi itu bukan asumsi kecil. Fabius memakai volum sebagai gerbang, bukan sebagai arah.

## Definisi yang bisa dihitung

```
# money flow klasik, semuanya dari bar OHLCV
OBV(t)  = OBV(t-1) + v(t) * sign(close[t] - close[t-1])
MLV(t)  = v(t) * ((close-low) - (high-close)) / (high-low)        # posisi close dalam range
CMF(n)  = sum(MLV, n) / sum(v, n)                                 # ~[-1, +1]
typ     = (high + low + close) / 3 ;  raw = typ * v
MFI(n)  = 100 - 100 / (1 + sum(raw | raw>raw_prev) / sum(raw | raw<raw_prev))

# yang kami pakai beneran (rasio, bukan kumulatif — tidak punya state)
vol_over_liq = volume_24h / liquidity        # veto kalau < MIN_VOL_OVER_LIQ = 0,10
```

Ketiga rumus di atas **sama-sama buta terhadap siapa yang membeli**: yang pertama memilih arah dari
tanda return, yang kedua dari posisi close, yang ketiga dari selisih typical price. Tidak ada satu
pun yang melihat sisi agresor ([[V3 - CVD Delta dan Footprint]] mencatat kenapa).

## Cara pakai yang diklaim

Klaim komunitas: breakout tanpa volum = palsu; tren sehat = volum ikut naik; divergensi
harga-vs-OBV menampilkan kelelahan. Dipakai sebagai filter entry pada horison intraday–harian.
Itu **klaim pendukungnya**, bukan prosedur yang kami setujui — tidak ada satu pun dari tiga
kalimat itu yang kami uji di data sendiri, dan tidak ada rujukan primer di repo ini yang
mengujinya.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| volum 24 jam per kandidat (satu snapshot) | `ADA` | `volume_24h` direkam `universe/record_bsc_universe.py`; ambang `MIN_VOL_OVER_LIQ` ≥ 0,10 — [[Fakta Terukur]] §E |
| volum per bar 1 jam untuk deret panjang | `ADA-TAPI` | kolom `v` ikut di-cache `tools/bars.py` (Aster 9.599 bar — §A) tapi **tidak dipakai** `tools/direction.py`/`tools/backtest.py`: `feats(closes, highs, lows, opens=None)` tidak pernah menerima volum |
| jumlah transaksi per bar (proxy perhatian) | `ADA-TAPI` | kolom `n` ikut di-cache; belum pernah dibaca satu pun alat |
| sisi agresor (siapa yang memaksa harga) | `TIDAK-ADA` | lihat [[V3 - CVD Delta dan Footprint]] · [[Fakta Terukur]] §C |
| volum bersih dari wash trading | `TIDAK-ADA` | tidak ada jalur pemisahan; yang ada cuma **proxy** |
| proxy bundler untuk menyaring volum palsu | `ADA-TAPI` | `bundler_rate` per baris universe; gerbang `MAX_BUNDLER` = 30 % (§E) — proxy pilihan pihak ketiga, bukan pengukuran wash |

## Uji di Fabius

Yang sudah tersedia dan memang untuk ini: `python -X utf8 tools/screen_universe.py` membandingkan
outcome per **alasan penolakan**, jadi `trending_without_demand` bisa dinilai isinya, bukan
dipertahankan karena sudah tertulis ([[GAP2 - Uji Setiap Veto Terhadap Hasil]]). Yang dibutuhkan
supaya V1 naik ke `T3`: event study `vol_over_liq` di kuartil → return bersih 4 jam, ambang
`n >= 20` non-overlap, BH α 0,10, gross di atas **59 bps** (ongkos terukur §D, bukan 20 bps asumsi),
positif setelah fold terbaik dibuang. Semua gerbang itu ada di [[Fakta Terukur]] §D/§E; jalurnya
`tools/backtest.py` tapi ia belum mengenal kolom volum — perlu perluasan, belum ada kodenya.

## Batas dan mode gagal

- **Volum simetris terhadap arah.** Bar naik dan bar turun sama-sama mencetak volum; rasio
  vol24/likuiditas tinggi juga berarti "orang sedang keluar dengan cepat".
- **Volum bisa dibuat tanpa modal yang berarti** di DEX: wash antar-dompet sendiri, bundler yang
  membeli dalam blok yang sama, LP yang berputar di satu kolam. `MAX_BUNDLER` menangkap sebagian
  yang **dilabeli** GMGN sebagai bundler — bukan yang tidak dilabeli.
- **Gerbang yang diam-diam tidak pernah jalan.** Terekam di komentar `universe/record_bsc_universe.py`:
  baris GMGN sempat menyimpan `"volume"` sementara veto membaca `"volume_24h"`, sehingga
  `trending_without_demand` **tidak pernah** menyala untuk baris-baris itu. Mode gagal khas filter
  berbasis satu field: namanya berubah, angkanya tidak pernah dilihat, laporannya tetap bersih.
- **Rasio volum/likuiditas bukan ukuran kapasitas keluar.** Yang membatasi keluar adalah
  `exit-size <= 1 % liq`; volum 24 jam bisa berasal dari satu menit.
- **Duplikasi sinyal:** `MFI`/`CMF` hampir kolinear dengan posisi close dalam bar — jadi ia mengukur
  geometri yang sama dengan [[I4 - Bollinger Bands]]/[[I2 - RSI dan Divergence]], hanya tanpa volum.

## Tingkat bukti

`T1` untuk "volum sebagai syarat" (praktik luas, tidak kami uji) · `T0` untuk klaim prediktif
OBV/CMF/MFI di memecoin (tidak ada sumber di repo ini) · untuk Fabius: **belum diuji terhadap
hasil** — gerbang volum `ADA` tapi empat ambang universe masih berstatus "diputuskan, belum
ditemukan" ([[Fakta Terukur]] §E).

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kita menyaring kandidat dengan rasio volum-24-jam terhadap likuiditas (≥ 0,10) dan
  punya proxy bundler ≤ 30 %; belum ada bukti kedua angka itu memprediksi hasil."
- **Dilarang:** "volum mengkonfirmasi arah" tanpa menyebut sisi agresor tidak kami miliki ·
  "Fabius membaca money flow" · "OBV/CMF/MFI wired di repo" (tidak satu pun dihitung) ·
  menyebut `MAX_BUNDLER` sebagai deteksi wash trading.

**Terkait:** [[V2 - Volume Profile dan POC]] · [[V3 - CVD Delta dan Footprint]] ·
[[O6 - Konsentrasi Holder Bundler dan LP Lock]] · [[FD3 - Likuiditas dan Dampak Harga]] ·
[[FD4 - Ongkos Perdagangan]] · [[PL2 - Menyaring Universe]] · [[GAP2 - Uji Setiap Veto Terhadap Hasil]]
