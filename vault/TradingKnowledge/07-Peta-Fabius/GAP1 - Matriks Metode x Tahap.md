---
tags: [tk, tk-peta, "GAP1"]
---

# GAP1 - Matriks Metode x Tahap

**Keluarga:** [[00 - Hub Peta Fabius]] · **Tahap:** penilaian ([[PL6 - Menilai Hasil]])
**Sumber:** `Fakta Terukur.md` §A/§C/§E/§H · daftar metode: `vault/TradingKnowledge/Plan.txt` +
`vault/TradingKnowledge/QuantTrading/Info1.txt`

**Ringkas:** satu tabel untuk semua pertanyaan "metode X boleh dipakai Fabius tidak?". Kolomnya:
tahap tempat ia bekerja, status datanya di repo ini, apakah sudah ada yang mengujinya, dan apa
bayarnya kalau kita menutup lubangnya. Isinya **bukan** peringkat kualitas — tidak ada peringkat di
lapisan ini, karena urutan kualitas hanya bisa datang dari sebuah run.

## Definisi yang bisa dihitung

Cara membaca tiap baris:

| kolom | arti |
|---|---|
| **Tahap** | tempat metode itu mengubah keputusan (`filtering` = boleh menolak, `analisis` = boleh memberi bobot, `keputusan` = boleh menentukan arah/ukuran, `penilaian` = dipakai setelah hasil) |
| **Data** | enum status di [[Aturan Subtree]]: `ADA` · `ADA-TAPI` · `TIDAK-ADA` · `MATI-DARI-MESIN-INI` |
| **Diuji** | `BELUM` (belum pernah ada yang menjalankan) · `NEGATIF` (sudah, hasilnya melawan) · `SEBAGIAN` (bagian mekaniknya diuji, kesatuannya belum) |
| **Bayar** | apa yang harus dibayar untuk memindahkannya ke kolom yang lebih baik: `nol` (sudah ada bahannya), `jam-proses` (perlu alat + satu siklus data), `kalender` (butuh waktu prospektif), `uang` (butuh langganan/data berbayar), `mustahil` (strukturnya melarang) |

## Cara pakai yang diklaim

Cara pakai yang sah: **menolak pekerjaan**, bukan memilih yang menarik. Baris dengan `Data:
TIDAK-ADA` tidak boleh masuk backlog dengan alasan "kelihatan keren di demo"; baris `Bayar:
kalender` tidak boleh dijanjikan selesai dalam sehari. Tabel ini juga alat penunjuk duplikasi:
kalau dua metode `Tahap`-nya sama dan `Data`-nya sama, mereka biasanya mengukur hal yang sama
(lihat `## Konfluensi atau gaung` di tiap catatan setup).

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| bar OHLCV 1 j untuk aset ber-perp | `ADA` | Aster 9.599 bar ≈ 400 hari — [[Fakta Terukur]] §A |
| funding + OI **spot saat ini** | `ADA` | Aster 608 kontrak, Hyperliquid 234 perp (§A) |
| funding + OI **historis per aset** | `TIDAK-ADA` | gerbang carry di `tools/direction.py` hanya bisa dipakai live, tidak bisa diuji surut (§E, §F) |
| aliran dompet point-in-time | `ADA-TAPI` | bidang ⑦: 100 tx/panggilan, jendela 8–13 menit, tanpa riwayat (§B) |
| volum per bar | `ADA-TAPI` | ikut `klines`; belum pernah dipakai menyaring apa pun |
| tick / L2 / delta agresor | `TIDAK-ADA` | tidak ada jalur di repo (§C) → V2/V3/V4/V5 tidak bisa dijalankan apa adanya |
| level likuidasi & heatmap | `TIDAK-ADA` | U3 |
| MVRV/SOPR/NUPL, exchange reserve, stablecoin supply | `TIDAK-ADA` | bisa dirakit dari Dune tapi mahal kredit + lag BSC ±1 jam (§A/§C, [[03-Data/D4 - Dune]]) |
| jadwal unlock/vesting | `TIDAK-ADA` | O7 |
| data CEX (Binance/Bybit/OKX/Bitget) | `MATI-DARI-MESIN-INI` | 451 / 403 / TLS terpotong — properti **pasangan** sumber×jaringan (§C) |

## Uji di Fabius

Matriks ini sendiri diuji dengan satu pertanyaan: **apakah ada metode yang `Data: ADA` tapi
`Diuji: BELUM`?** Kalau ya, itu lubang malapraktik, bukan kekurangan data. Jawabannya sekarang:
**ya, dan itu bidang ⑦** — satu-satunya bahan yang tidak bisa disusulkan justru yang paling lama
kita rekam dan belum diuji sebagai kesatuan (lihat [[GAP3 - Yang Punya Data Tapi Belum Diuji]]).
Perintah pembuka jalurnya sudah ada: `python -X utf8 tools/flow_signal.py --overlap`,
`python -X utf8 tools/winlog.py`.

## Batas dan mode gagal

- Tabel ini basi lebih cepat daripada catatan metodenya: kolom `Data` adalah keadaan **sekarang**,
  dan perekam berhenti = status berubah. Baca ulang dengan `python -X utf8 tools/whale_report.py`
  + cek `universe/wallet-flow-manifest.txt` sebelum menyimpulkan apa pun dari kolom itu.
- `Bayar: nol` bukan berarti `Boleh dijual`. Semua `NEGATIF` di [[Fakta Terukur]] §F datang dari
  baris yang biayanya nol — itu justru gunanya.
- Baris tidak pernah lebih tinggi nilainya daripada tingkat bukti metode penyusunnya
  ([[EV1 - Tingkat Bukti]]).

## Isi tabelnya

Keluarga; bukan 38 baris, karena yang mengikat adalah **status data keluarga**, bukan selera per
metode. Metode individual ada di [[00 - Hub Sinyal]].

| keluarga | Tahap | Data | Diuji | Bayar | catatan |
|---|---|---|---|---|---|
| Struktur / price action (`S1 S2 S3`) | analisis | `ADA-TAPI` | BELUM | jam-proses | semua turun dari bar yang sama; definisi swing harus dibakukan dulu ([[S3 - Market Structure BOS dan ChoCH]]) |
| SMC (`S4 S5 S6`) | analisis | `ADA-TAPI` | BELUM | jam-proses | zona bisa dihitung dari OHLC; klaim penyebabnya tidak bisa diuji tanpa L2 ([[S4 - Order Block dan Breaker]]) |
| Fibonacci (`S7`) | analisis | `ADA` | BELUM | jam-proses | uji wajib vs null level acak, bukan vs "tanpa level" |
| Wyckoff / Elliott / Harmonic (`S8 S9`) | analisis | `ADA-TAPI` | BELUM | mustahil-sebagian | skemanya bisa mengakomodasi chart apa pun → tidak falsifiable seperti dipakai sekarang ([[S9 - Elliott Wave dan Harmonic]]) |
| Indikator trend/momentum (`I1 I3 I4 I5`) | analisis | `ADA` | **NEGATIF** untuk arah garis besar | kalender untuk membangun ulang | aturan arah `direction.py` = rugi di 12/12 aset setelah ongkos (§F) — jangan diulang dengan nama lain |
| Osilator / jarak (`I2 I6`) | analisis | `ADA` | BELUM | jam-proses | ATR dipakai untuk jarak & ukuran, bukan arah ([[I6 - ATR dan Jarak Ternormalisasi]]) |
| Keluar dinamis: trailing / time-stop / shaped-exit (`FD7`, `I6`, `FD9`) | eksekusi | **ADA-TAPI terlalu jarang** (1-4 bar/jam) | **TIDAK BISA DINILAI** (E17: 25/28 lengan ber-delta median 0,0) | butuh bar 1 menit | algebra lock sudah diukur dan **lolak** (63-66 % kejadian punya jendela `d` sah) - yang gagal adalah resolusinya, bukan idenya; stop juga hanya mengubah **bentuk**, bukan harapan (Lei & Li 2009) ([[06-Results/24 - Trailing pada Bar yang Salah]]) |
| VWAP (`I7`) | analisis | `ADA-TAPI` | BELUM | jam-proses | butuh volum yang benar; VWAP anchored = tuas overfit kalau anchor dipilih setelah hasil |
| Volum dasar & money flow (`V1`) | analisis | `ADA-TAPI` | BELUM | jam-proses | belum satu pun alat kami memakai kolom volum; risiko wash-trade nyata di BSC |
| Profil volum / delta / L2 (`V2 V3 V4 V5`) | analisis | **ADA-TAPI terbatas** (⑦ print + sisi agresor; ⑨ L2 26 simbol @±200 d) | **V3 NEGATIF** (E18: 5 pembacaan rasio berimbang, semua di dalam placebo, BH kosong); V4 **belum divonis** (E16 terkunci, 21:37:45Z) | selesai-sebagian | ⑦ memberi klasifikasi agresor betulan (bukan label candle) tapi di **spot AMM**, ⑨ memberi buku order di **perp** - irisannya 3,1 %. Batas yang tidak boleh dilupakan: snapshot = **state**, OFI = **aliran**, dan yang terakhir tidak dapat dipulihkan dari dua potret ([[V4 - Order Book dan Liquidity Heatmap]]) |
| Turunan: OI & funding live + histori (`U1 U2`) | keputusan (veto) | `ADA` | **SEBAGIAN → diuji 28 Sep: 0/12 lolos BH, veto kena 0/2.963** | kalender (untuk funding per-jam venue sendiri) | hasil lengkapnya [[06-Results/08 - Carry Study]]; yang belum tersentuh = memecoin, yang tidak punya funding |
| Likuidasi & rasio posisi (`U3 U4`) | analisis | `TIDAK-ADA` | BELUM | uang | klaimnya spesifik pada data yang tidak bisa kita baca |
| On-chain valuasi (`O1 O2 O3 O4`) | analisis | `TIDAK-ADA` | BELUM | uang + jam-proses | Dune bisa merakit sebagian; untuk aset berumur 3 hari metriknya tidak terdefinisi — dan itu kasus utama kita |
| Kohor dompet (`O5`) | keputusan (bobot) | `ADA-TAPI` | BELUM | jam-proses + kalender | bahan ada, alat skornya belum bisa dipercaya (§H) — **lubang nomor satu kita** |
| Keamanan/konsentrasi (`O6`) | filtering | `ADA` | BELUM | jam-proses | ambang diputuskan, belum diuji → [[GAP2 - Uji Setiap Veto Terhadap Hasil]] |
| Unlock & MEV (`O7 O8`) | keputusan (hazard) | `TIDAK-ADA` | BELUM | uang | bukan "nice to have": tanpa `O8` kita tidak tahu siapa yang mengambil bagian dari fill kita |
| Sentimen & narasi (`M1 M2 M3 M4 M5`) | analisis | `ADA-TAPI` | BELUM | jam-proses | berkas GDELT hidup (§C); tapi sentimen terbit setelah harga bergerak → hanya boleh mengurangi ([[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]) |
| Quant relatif-value (`QT5 QT6 QT7`) | strategi | `TIDAK-ADA` sebagian besar | BELUM | uang + izin | butuh dua kaki, shorting/pinjam aset, dan major yang **ditolak** `STABLE_BASES` (§E) |
| Evaluasi (`QT1 QT2 QT3 QT4`, `EV*`) | penilaian | `ADA` | SEBAGIAN | jam-proses | keluarga yang mekanismenya **punya run** di repo — bukan peringkat, lihat kolom "Diuji" |

## Tingkat bukti

`T1` sebagai peta keadaan (kolom datanya dari angka terukur §A–§C; kolom "Diuji" dari §F dan §H) ·
bukan `T3`: memetakan tidak membuktikan satu pun metode.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "Fabius punya bar 1 jam 400 hari + funding/OI live + aliran dompet point-in-time, dan
  belum menguji sebagian besar bahan itu; yang butuh tick/L2/histori-on-chain tidak bisa dijalankan
  dari repo ini hari ini."
- **Dilarang:** "kami sudah memilih metode terbaik" (tidak ada satu pun metode yang lolos `T3`
  sebagai penghasil arah) · "kolom `TIDAK-ADA` tinggal beli langganan" (sebagian besar jawabannya
  kalender atau mustahil, bukan kartu kredit).

**Terkait:** [[GAP3 - Yang Punya Data Tapi Belum Diuji]] · [[GAP4 - Yang Tidak Bisa Diuji Karena Data]] ·
[[GAP5 - Urutan Kerja dan Bayarnya]] · [[ST7 - Checklist Keputusan]] · [[03-Data/D3 - Price Depth]]
