---
tags: [tk, tk-pipeline, "PL3"]
---

# PL3 - Menganalisis

**Keluarga:** [[00 - Hub Pipeline]] · **Tahap:** analisis · sebelumnya [[PL2 - Menyaring Universe]] ·
sesudahnya [[PL4 - Memutuskan]]
**Sumber:** `tools/direction.py`, `tools/backtest.py`, `tools/flow_signal.py` ·
[[04-Tools/TL2 - direction]] · [[Fakta Terukur]] §A/§C/§F

**Ringkas:** Analisis adalah **pemetaan data → hipotesis yang bisa salah**, bukan penguat kesimpulan
yang sudah kita pegang. Bedanya operasional: pembacaan yang sah menyebut angka yang akan
membantahnya, dan pembacaan yang tidak sah selalu cocok dengan apa pun yang terjadi. Di tahap ini
enam keluarga metode (struktur, indikator, volum/order-flow, turunan, on-chain, narasi) bersaing
untuk mendapat perhatian — dan yang paling menentukan bukanlah keluarga mana yang paling pintar,
melainkan keluarga mana yang datanya benar-benar kami punya.

## Definisi yang bisa dihitung

```
analisis(x, t) -> (hipotesis, arah, besaran, kondisi_salah)      # hanya data dengan waktu <= t
kondisi_salah  : harga/nilai di mana hipotesis ini dinyatakan batal, ditetapkan SEBELUM hasil
terbaca(t)     : keluarga yang datanya ada pada t  -- kalau tidak, outputnya bukan analisis tapi wishful
```

| keluarga | mengukur apa | berubah arti menjadi | contoh catatan |
|---|---|---|---|
| struktur / price action | di mana transaksi terjadi dan level mana yang dijaga | bahasa bebas-diinterpretasi setelah harga bergerak | [[S3 - Market Structure BOS dan ChoCH]] · [[S4 - Order Block dan Breaker]] |
| indikator | ringkasan statistis deret sendiri | tersesat tanpa rezim: MA di range = bising, oscillator di tren = jenuh selamanya | [[I1 - Moving Average]] · [[I2 - RSI dan Divergence]] |
| volum & order-flow | siapa memaksa harga bergerak | tidak terukur sama sekali tanpa tick/L2 | [[V1 - Konfirmasi Volum dan Money Flow]] · [[V3 - CVD Delta dan Footprint]] |
| turunan (funding/OI/likuidasi) | biaya dan posisi terbuka | snapshot bukan deret: tidak bisa diuji mundur | [[U1 - Open Interest]] · [[U2 - Funding Rate dan Basis]] |
| on-chain | siapa memindahkan nilai | agregat yang bisa disusulkan = statistik, bukan saksi | [[O1 - Exchange Inflow dan Outflow]] · [[O5 - Whale dan Kohor Smart Money]] |
| narasi / sentimen | ke mana perhatian pergi | prediktif atau cuma mengikuti — belum kami bedakan | [[M2 - Sentimen Sosial dan Ekstraksi LLM]] · [[M3 - Narasi Sektar dan Rotasi]] |

## Cara pakai yang diklaim

Klaim komunitas (T1, tanpa pemilik yang bisa diperiksa): makin banyak keluarga yang **sepakat**
("konfluensi"), makin kuat pembacaan. Itu benar hanya bila inputnya saling bebas — dan biasanya tidak:
SMA, MACD, dan ichimoku semuanya fungsi dari deret penutupan yang sama, jadi lima "konfirmasi" bisa
jadi satu pengukuran yang diulang lima kali ([[V1 - Konfirmasi Volum dan Money Flow]],
[[FD11 - Aturan Mengalahkan Intuisi]]). Pemakaian yang sah di Fabius: satu pembacaan dinyatakan sebagai
fitur dengan ambang tetap, lalu **diuji terhadap hasil forward** — bukan dinyatakan sebagai alasan lalu
dicari pendukungnya.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| bar 1 jam ≥ 2.400 untuk menguji sebuah fitur | `ADA-TAPI` | Aster 9.599 bar, tetapi hanya aset **ber-kontrak perp** — [[Fakta Terukur]] §A |
| bar ≥ 720 untuk sekadar "layak dinilai" | `ADA-TAPI` | `MIN_BARS_TINY=720` = 30 hari: layak dinilai, **tidak** layak diklaim sebagai edge — §A |
| funding + OI sebagai fitur hidup | `ADA-TAPI` | terpasang di `tools/direction.py` sebagai **pemutus rezim** (funding > 0,05 %/4 j menolak posisi; 0 kejadian terukur, F-D26); **historinya sekarang ada** (`universe/funding-history.jsonl`, 8 jam × 97 hari — [[03-Data/D6 - Funding and OI History]]) tapi tetap bukan per-bar — §A.5 |
| tick / L2 / footprint | `TIDAK-ADA` | §C — seluruh keluarga order-flow berhenti di `T1` |
| aliran dompet point-in-time | `ADA-TAPI` | 100 transaksi/panggilan, jendela 8–13 menit, tanpa riwayat — §B |
| narasi (tema + nada) ikut ter-hash | `ADA-TAPI` | jalur berkas GDELT hidup; belum diuji sebagai prediktor — §C |
| satu definisi fitur yang sama di semua alat | `ADA-TAPI` | tidak ada konsep "zona"/profile di jalur arah — [[04-Tools/TL2 - direction]] |

## Uji di Fabius

```
python -X utf8 tools/backtest.py            # aturan live di 400 hari x 12 aset, ambang DIIMPOR bukan di-fit
python -X utf8 tools/flow_signal.py --signal MARSCOIN   # aliran point-in-time: buang baris setelah as_of
```

Ambang kelulusan sebuah analisis: gross di atas **59 bps** (ongkos terukur kami, bukan 20 bps
asumsi), `n >= 20` non-overlap, BH α 0,10, tetap positif setelah fold terbaik dibuang
([[Fakta Terukur]] §D/§E). Sudah dijalankan pada aturan arah kami sendiri dan hasilnya **net rugi di
12/12 simbol**; arah dibalik pun tetap kalah ([[06-Results/04 - Negative Results]]). Itu jawaban
akhir untuk lapisan ini hari ini, dan ia tercatat sebagai hasil, bukan sebagai kegagalan proses.
Bentuk uji yang jujur: [[QT2 - Backtesting yang Jujur]] · [[QT4 - Overfitting dan Validasi]] ·
[[EV2 - Jebakan Backtest]].

## Batas dan mode gagal

- **Analisis yang jadi pengacara.** Kalau sebuah pembacaan hanya berfungsi saat ia benar, ia tidak
  mengukur apa pun; kondisi salah wajib ditulis sebelum hasil ([[EV5 - Reproduksibilitas dan Pra-Registrasi]]).
- **Kedalaman tanpa struktur.** Deret terdalam pun bisa mendekati jalan acak: `|acf|` 0,075 masih
  **zona abu-abu** (0,05–0,10 = belum tahu) dan yang di bawah itu tidak menjual apa pun
  ([[Fakta Terukur]] §F); contoh kandidat berriwayat terpanjang yang justru tetap `flat` ada di
  [[01-Agent/01 - Asset Classes and Seats]].
- **Rezim berubah lebih cepat daripada ambang.** Fitur yang di-fit pada 400 hari bisa jadi mengukur
  rezim yang sudah mati ([[FD1 - Struktur Pasar dan Rezim]]).
- **Duplikasi pengukuran:** keluarga yang berbeda dengan input yang sama menghasilkan ilusi
  konfirmasi ([[QT3 - Data Fitur dan Label]]).
- **Label pihak ketiga membawa lookahead.** Memakai keanggotaan panel hari ini untuk menilai
  transaksi masa lalu hanya bisa membuat angkanya terlihat **lebih baik**
  ([[Concepts/Lookahead Bound]]); `tools/flow_signal.py` karena itu melaporkan aliran semua maker dan
  aliran maker ber-tag sebagai dua angka yang berbeda.
- **Yang tidak terukur tidak netral:** ketiadaan L2 bukan "analisis kurang detail", ia penolakan
  atas seluruh klaim order-flow ([[03-Data/01 - Dataset]]).

## Tingkat bukti

`T3` untuk jalur pengukurannya sendiri (ada run yang bisa diulang dari clone: `tools/backtest.py`) —
dengan flag `NEGATIF` untuk aturan arah yang dihasilkannya. `T1` untuk enam keluarga metode di atas
(dipakai luas, tidak kami uji). `T0` untuk klaim konfluensi ("gabungkan banyak sinyal = lebih
akurat") — tidak ada pemiliknya, tidak ada pembandingnya.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "tiap pembacaan di tahap ini wajib menyebut data yang membatasinya dan angka yang akan
  membantahnya; sebagian besar keluarga belum kami uji karena datanya tidak ada."
- **Dilarang:** "Fabius menganalisis order flow / on-chain / sentimen secara prediktif" ·
  "konfluensi menaikkan probabilitas" (belum diukur di sini) · "aturan arah kami memberi edge"
  — yang terukur justru sebaliknya.

**Terkait:** [[PL2 - Menyaring Universe]] · [[PL4 - Memutuskan]] · [[PL6 - Menilai Hasil]] ·
[[S4 - Order Block dan Breaker]] · [[FD1 - Struktur Pasar dan Rezim]] · [[QT3 - Data Fitur dan Label]] ·
[[M2 - Sentimen Sosial dan Ekstraksi LLM]] · [[GAP1 - Matriks Metode x Tahap]]
