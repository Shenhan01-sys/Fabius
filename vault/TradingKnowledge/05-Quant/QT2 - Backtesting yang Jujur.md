---
tags: [tk, tk-quant, "QT2"]
---

# QT2 - Backtesting yang Jujur

**Keluarga:** [[00 - Hub Quant]] · **Tahap:** penilaian ([[PL6 - Menilai Hasil]])
**Sumber:** `vault/TradingKnowledge/QuantTrading/Info1.txt` §"Komponen Utama Quant Trading" /
§"Analisis backtest strategi" (daftar topik) · angka hasil: [[Fakta Terukur]] §D/§F ·
mekanik: `vault/04-Tools/TL7 - measurement harness.md`

**Ringkas:** backtest jujur adalah simulasi yang **sengaja merugikan dirinya sendiri**: harga fill
yang tidak optimis, ongkos yang dipakai sebelum hasil dilihat, sampel yang tidak tumpang tindih, dan
tidak satu pun informasi masa depan yang boleh masuk ke keputusan. Kami sudah punya mesin dengan
bentuk itu (`tools/backtest.py`), ambangnya DIIMPOR dari kode live — bukan di-fit di atas hasil — dan
sekali dijalankan ia menjawab pertanyaan kami dengan **12/12 rugi**. Jujur di sini bukan nada rendah
hati, tapi daftar keputusan pemilih yang bisa dibaca orang lain.

## Definisi yang bisa dihitung

Satu putaran yang sah:

```
untuk tiap bar t (naik waktu):
  state   := hanya baris dengan waktu <= t
  side    := aturan(state)                  # ambang dari kode live, bukan dari hasil
  entry   := open bar t+1                    # bukan close bar tempat keputusan dibuat
  exit    := close bar t+h, h tetap          # + aturan keluar kalau kena stop lebih dulu
  net_bps := gross_bps - ongkos_round_trip
  cooldown: baris berikutnya yang jendelanya [t, t+h] tumpang tindih DIBUANG
```

Empat dosa yang harus dinyatakan eksplisit di tiap laporan:

| dosa | bentuknya di crypto | pager yang kami punya |
|---|---|---|
| fill optimis | "terisi di mid" padahal book tipis | `entry = open t+1`; ongkos RT dipotong sejak awal |
| lookahead | label/riwayat yang terbit setelah kejadian | ambang diimpor, fitur `<= t`, lihat [[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]] |
| ongkos salah | fee saja, tanpa spread/dampak/gas | dua angka yang saling mengunci: 20 bps RT (asumsi warisan) vs **59 bps** terukur di venue kami — §D |
| sampel ganda | satu token satu jam dihitung 3 kali karena 3 aturan | 1 sampel per (token, jam), non-overlap — §E |

Walk-forward: deret dibagi segmen waktu, `NEED_BARS=2400` untuk 5 fold (§A); fold terbaik dibuang
dan sisanya harus tetap positif. Alasannya terdokumentasi: satu segmen bagus bisa menyamar sebagai
aturan bagus (BNB +14,9 bps di horizon 24 jam mati tepat di drop-best-fold — baris 74 di
[[06-Results/04 - Negative Results]]).

## Cara pakai yang diklaim

Pustaka generik (vectorbt, backtrader, nautilus, freqtrade) menjual bentuk yang sama dengan default
yang lebih ramah — fill di close, ongkos opsional, satu baris masuk beberapa trade; angka "Sharpe
2,4" lahir dari default itu. Pemilik klaim bentuk bersihnya adalah literatur backtest overfitting
(didaftar di `Info1.txt` §"Buku", mis. López de Prado) — tidak kami reproduksi.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| deret 1 jam 400 hari untuk harga forward | `ADA` | Aster 9.599 bar, dijawab sendiri lewat `tools/bars.py` — §A |
| pembanding silang deret | `ADA` | Hyperliquid 5.001 bar ≈ 208 hari (§A) — chain sendiri, bukan BNB |
| ongkos nyata per fill di pasar sungguhan | `TIDAK-ADA` | 59 bps kami adalah venue demo x·y=k + fee 30 bps, **bukan** pasar meme — §D |
| histori funding per aset untuk menguji gerbang carry | `TIDAK-ADA` | hanya funding terkini yang bisa dibaca (§A/§C) → §F menyebut ini sebagai batas yang masih tersisa |
| bar untuk aset tanpa kontrak perp | `ADA-TAPI` | GMGN 1.000 bar ≈ 41,6 hari, 0 bar untuk token gas (§A) → tidak menyentuh `NEED_BARS` |
| tick / book untuk model fill yang benar | `TIDAK-ADA` | §C |

## Uji di Fabius

```
python -X utf8 tools/backtest.py                       # aturan live apa adanya
python -X utf8 tools/backtest.py --mom-only            # gerbang |acf| dimatikan
python -X utf8 tools/backtest.py --mom-only --flip     # aturan yang sama, arahnya dibalik
python -X utf8 tools/backtest.py --mom-only --horizon 24
python -X utf8 tools/backtest.py --cost 59             # ongkos TERUKUR, bukan asumsi
```

Tiga varian itu ada supaya pertanyaan "siapa yang memproduksi nol — gerbang atau isinya?" bisa
dijawab, bukan sebagai fitur demo. Yang terukur (§F): dengan gerbang hidup, nol trade di enam aset
terdalam; gerbang dicabut → net −27,9 … −0,8 bps/trade dan **negatif di 12/12**; dibalik →
−39,2 … −12,1 dan tetap kalah; horizon 24 jam → **0/12 lolos**. Naik tingkat bukti berikutnya
butuh dua hal yang belum ada: slippage nyata per ukuran, dan ongkos 59 bps yang disatukan dengan
asumsi 20 bps (lubang P10 di [[08-Backlog/01 - Backlog]]).

## Batas dan mode gagal

- **Survivorship**: yang bisa dihargai sendiri hanya aset **ber-kontrak perp** — token yang sudah
  selamat. Untuk C2/D (memecoin jam–hari) backtest tidak mungkin, bukan "belum sempat".
- **Satu rezim**: 400 hari adalah satu sejarah, bukan empat ratus percobaan rezim.
- **Ongkos adalah satu angka, bukan fungsi**: dampak nyata naik bersama ukuran, dan di venue kami
  satu unit sudah berbiaya 59 bps (§D); gas testnet 0,10 gwei menambah ongkos tetap yang tidak
  ikut dalam model 20 bps.
- **Hasil parsial yang tampak penuh**: pemotong halaman dan `LIMIT` wajib diucapkan, lihat
  `vault/04-Tools/TL7 - measurement harness.md`.
- Backtest **tidak bisa** membuktikan sebuah aturan hidup; dia hanya membuktikan aturan itu mati
  pada data dan ongkos yang dipakai.

## Tingkat bukti

`T3` + flag `NEGATIF` untuk aturan arah di `tools/backtest.py` (angka §F, bisa diulang dari clone) ·
`T1` untuk daftar default yang harus diwaspadai di pustaka generik · `T2` untuk literatur backtest
overfitting yang namanya disebut di `Info1.txt` dan tidak kami reproduksi.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami menjalankan aturan live kami di 400 hari × 12 aset dengan ongkos, tanpa menyetel
  satu parameter pun setelah melihat hasil, dan hasilnya rugi di semua aset yang diukur."
- **Dilarang:** "backtest kami menunjukkan potensi untung" · "angka Sharpe" (tidak ada satu pun di
  repo ini) · "59 bps adalah slippage kami di pasar nyata" (itu venue demo) · "belum diuji" dibaca
  sebagai "nanti pasti lolos".

**Terkait:** [[QT1 - Dari Ide ke Strategi yang Bisa Diuji]] · [[QT4 - Overfitting dan Validasi]] ·
[[EV2 - Jebakan Backtest]] · [[EV3 - Signifikansi dan Multiple Testing]] · [[FD4 - Ongkos Perdagangan]] ·
[[Concepts/Cost Is Fixed]] · [[03-Data/D3 - Price Depth]]
