---
tags: [backlog, epik, "kolaborasi-bot", "penerbit-bot", seleksi]
---

# 07 - Epik Kolaborasi Bot Terbuka (penerbit bot luar, sepuluh slot, peninjau-bot ber-KPI, rolling)

**Bagian dari:** [[08-Backlog/00 - Hub Backlog]]
**Dibuka:** 2 Okt 2026 (malam) oleh builder, kata-katanya (diringkas): *Fabius bisa membuka kolaborasi lewat bot ini: siapa pun boleh
mengajukan ide bot, tetapi teorinya harus terbukti kualitasnya lebih dulu (field-nya atur saja); identitas penerbit, terutama
dompetnya, harus jelas supaya penerbit mendapat bagian kalau botnya menghasilkan. Seleksi harus ketat dan bot yang masuk
benar-benar menguntungkan Fabius. Maksimal 10 bot: minimal 1 milik Fabius sebagai identitas, 9 slot bebas. Kalau sudah 10 dan
ada bot baru yang kualitasnya terbukti, lakukan rolling: buang bot dengan winrate/PnL terendah.* Putaran kedua (jawaban builder atas
pertanyaan saya): *60/40 setuju; bot identitas kalau bisa yang trading crypto biar kelihatan beneran trading; template dulu; tidak
ada biaya pengajuan; **meninjau bot kiriman lebih baik pakai bot, bukan agen: beri logika KPI minimal supaya Fabius juga untung saat
memakai bot itu**; tingkat 0 (umpan bukti) boleh duluan.* Putaran ketiga (F-D73): *"1. Betul 2. Yg pnting tradenya instrument crypto saya gas 3. Sementara ini oke, nanti kita coba riset lagi untuk mengoptimalkan itu (catat di vault)"* - basis 60/40 = pendapatan, bot identitas = B1-TREND, ambang v1 terkunci sementara, riset optimasi dijadwalkan ([[08-Backlog/08 - Riset Optimasi Ambang]]).
**Sumber:** keputusan [[00-Overview/03 - Decisions]] F-D70, F-D71, F-D72, F-D73; kode `engine/submission.py`, `gates.py`, `kpi.py`, `review.py`,
`slots.py`, `book.py`, `locks.py`, `economics.py`, `chain.py`; keluaran `python -X utf8 -m engine.cli gate --data <dir> --bot ALL`
(`<dir>` = keluaran `fetch.py` di `09-Inbox/Session-2026-10-02-skrip/`); mentah di [[09-Inbox/Session-2026-10-02]] §8 dan §9.

> **STATUS: USULAN rancangan + kode awal berdiri sendiri.** Belum ada penerbit luar, bot terkunci, kontrak (7 Okt: `BotRegistry` + `RevenueSplitter` ditulis + diuji lokal, BELUM di-deploy - P81), FE. Ambang di halaman ini
> adalah **v1, DIKUNCI sementara (F-D73)**: `python -X utf8 -m engine.cli lock` mencetak `TERKUNCI` dan sha `0xf145b70a…fe5f32` (~~bawaan di kode, belum dikunci: `BELUM_DIKUNCI`~~ - keadaan sebelum 2 Okt 07:40Z;
> ~~berkas kunci belum di-commit dan belum di-anchor~~ **kunci ter-anchor di chain 97 pada 2026-10-02T08:17:48Z (F-D74; `python -X utf8 tools/anchor_lock.py --verify`) dan di-commit bersama catatan ini**; ambang belum teroptimasi: [[08-Backlog/08 - Riset Optimasi Ambang]]). Semua angka dalam-sampel dan dicetak ulang oleh perintah di atas; bukan klaim edge.

## 0. Riwayat revisi halaman ini (dipajang, bukan dihapus)

| kapan | apa yang berubah | kenapa |
|---|---|---|
| 2 Okt sore | versi pertama: peninjau = "agen yang hanya boleh menolak"; enam gerbang G1-G11; B3 dan B5 lolos | rancangan awal |
| 2 Okt malam #1 | G8 untuk bot alokasi: placebo waktu → benchmark buy&hold BTC (B5 lolos) | lari pertama menggagalkan B5 lewat placebo yang tak bermakna; **diubah setelah melihat hasil** |
| 2 Okt malam #2 | G8 memvonis dengan **batas atas 95 %** p-value, bukan titik taksir | p B1 berfluktuasi antar seed 0,040-0,109 (`run12_seed_robustness.py`); **diubah setelah melihat hasil** |
| 2 Okt malam (F-D72) | **tidak ada agen peninjau**: peninjau = bot deterministik + KPI K1-K5; template saja; 60/40; tanpa biaya pengajuan | jawaban builder |
| 2 Okt malam (tinjauan keamanan) | 12 temuan diukur oleh peninjau independen; sebagian besar diperbaiki (§9); G8 alokasi diperketat jadi dua uji → **B5 kini TOLAK** | temuan #10 peninjau: benchmark tunggal terhadap BTC tidak menguji aturan B5 |
| 2 Okt (putaran 3, F-D73) | **ambang v1 DIKUNCI sementara** (sha `0xf145b70a…fe5f32`); bot identitas = **B1-TREND** (`engine/book.py`; buku genesis = B1 saja); basis 60/40 = **pendapatan** (dikonfirmasi); petahana G10 bawaan di `intake`/`review` = buku genesis (`--incumbents six` = perilaku lama); riset optimasi ambang dijadwalkan (epik 08) | jawaban builder ("Betul" / "saya gas" / "sementara ini oke, nanti riset lagi"); **bukan perubahan angka gerbang** - dogfood dicetak ulang sesudah kunci: vonis dan angka identik |
| 2 Okt (putaran 4, F-D74) | kunci v1 **di-anchor** di chain 97 (`tools/anchor_lock.py`; tx `0xf09d61e6…`, `anchoredAt` 2026-10-02T08:17:48Z; asset `FABIUS-LOCK/review-v1`, verdict Abstain sebagai pemetaan) dan di-commit | jawaban builder: "Anchor sekarang gapapa sih" / "Commit"; **angka tidak berubah** |
| 7 Okt (P81) | kontrak C-H **ditulis + diuji lokal, belum di-deploy**: [[02-Contracts/C9 - BotRegistry]] + [[02-Contracts/C10 - RevenueSplitter]]; §8 diberi catatan pembaruan dengan butir USULAN (a)-(g) | kerja backlog P81; **angka gerbang tidak berubah**, 60/40 = `economics.split` apa adanya |

Empat perubahan gerbang setelah melihat hasil pada bot sendiri adalah alasan kuat untuk **mengunci** gerbang sebelum ada kandidat luar (§10 #3).

## 1. Koreksi atas ide awal (dan alasannya)

1. **Metrik rolling = PnL net setelah ongkos, bukan win-rate.** F-D16 sudah mematikan win-rate sebagai ukuran (panel whale WR 69,8 % tetapi
   −10,4 bps; satu posisi MARSCOIN menang dengan +1,5 bps). Strategi ekor-tebal (fade listing: menang 75 %, trade terburuk −182 %
   notional) menang di peringkat win-rate dan merusak di PnL. Win-rate tetap dicetak sebagai diagnostik (`slots.win_rate_diag`).
2. **"Fee kalau profit" menjadi bagi hasil dari penjualan sinyal bot itu (60/40)**, bukan bagian dari profit dompet pengikut (F-D17) dan bukan
   bagian dari profit trading Fabius. Alasan kedua ini terukur: K5 (§5) menunjukkan bahwa kalau penerbit mengambil 60 % dari bulan yang untung
   tanpa menanggung bulan yang rugi, **B1 yang untung +50,2 %/tahun membuat Fabius −1,6 %/tahun** (B2 −8,3 %, B6 −2,6 %). Basis profit tanpa
   bagi-rugi merugikan Fabius; basis pendapatan penjualan tidak.
3. **Tidak ada agen peninjau (F-D72).** Builder: lebih baik pakai bot. Peninjau = `engine/review.py`: validasi → identitas → G1-G11 → K1-K5 →
   laporan ber-sha, semuanya deterministik. Konsekuensi yang harus dikatakan terus terang: **teks teori (`theory.*`) tidak dinilai kualitasnya
   oleh mesin**. Ia wajib sebagai pengungkapan (untuk pembaca manusia, FE, dan audit); yang menentukan adalah **bukti terukur** (gerbang + KPI)
   dan konsistensi mekanis (skema, klaim vs terukur, rujukan wajib ada dan berformat URL publik). Manusia hanya boleh **memveto** (menolak);
   tidak ada jalur manusia atau model untuk menerima di luar vonis bot (satu arah, F-D11). Pemeriksaan keberadaan URL rujukan (jaringan) belum ada.
4. **Kode pihak luar tidak pernah dijalankan otomatis.** Penerbit memilih metode yang SUDAH ada di mesin (`template`), SATU parameter, dan
   universe. **Dibuka dulu: `template` saja** (`submission.ENABLED_KINDS`); `method_pr` dan `feed` ada di skema tetapi ditolak `validate`.

## 2. Tiga jenis bot (hanya `template` yang dibuka)

| `kind` | siapa menjalankan | bukti yang bisa kami periksa | status |
|---|---|---|---|
| `template` | **mesin kami** (replay penuh, deterministik) | replay di data dan penggaris kami + shadow maju | **DIBUKA**; penerbit hanya memberi `bot_id`, satu parameter, universe |
| `method_pr` | mesin kami, **setelah** kode digabung | sama, setelah tinjauan manusia | ditutup; wajib kelak: fungsi murni `targets()`, tes PIT dan determinisme, `NULL_KIND`, `PHASE_VARIANTS` |
| `feed` | penerbit (bot sendiri) | **hanya** rekam jejak maju ter-anchor ([[08-Backlog/06 - Epik Gerbang Sinyal]] §4) | ditutup; wajib `komit_maju`; masa shadow lebih panjang (belum dikode) |

Catatan jujur dari tinjauan keamanan: hanya ada 6 template × 1 parameter, jadi **setiap bot `template` luar adalah reparametrisasi bot Fabius atau bot luar lain**.
Pertahanannya: `BotSpec.fingerprint()` (dedupe efektif: ganti nama atau kalimat tidak membuat bot baru) dan G10 (korelasi ≤ 0,7 terhadap buku). Nilai tambah
nyata dari penerbit luar baru muncul bila `method_pr` dibuka.

## 3. Formulir (skema tertutup; `python -X utf8 -m engine.cli schema` mencetaknya sebagai JSON untuk FE)

Contoh yang lolos validasi: `engine/examples/submission.example.json` (diuji; sengaja tidak mengklaim apa pun).
`python -X utf8 -m engine.cli intake --file <berkas> [--data <dir>]` memvalidasi dan menjalankan gerbang; `... review ...` menjalankan peninjau-bot penuh.

| bagian | field | tujuan |
|---|---|---|
| `kind`, `spec` | `bot_id`, `metode`, `template`, `param_nama`, `param`, `konstanta`, `universe`, `horizon` | satu metode + SATU parameter; awalan `B<angka>-` dan nama yang memuat "fabius/official/resmi" dicadangkan; `param_nama` tak boleh juga jadi konstanta |
| `identity` | `issuer_wallet`, `payout_wallet` (EIP-55 ketat), `handle`, `contact`, `entity_type`, `erc8004_agent_id`, `conflicts` | pengajuan ditandatangani EIP-712 oleh dompet penerbit; **dompet payout yang berbeda wajib ikut menandatangani**; kontak tidak pernah ke chain dan **tidak ikut hash** |
| `theory` | `mekanisme_jenis`, `mekanisme`, `pihak_seberang`, `kapasitas_usd`, `referensi[]`, `rezim`, `mode_gagal`, `peluruhan`, `pembunuh` | pengungkapan; `pembunuh` = {metrik, pembanding, ambang **berbatas per metrik**, jendela sinyal} sehingga bisa ditegakkan kode (`slots.killer_triggered`) |
| `evidence` | `sumber_data`, periode, `percobaan`, `klaim{...}`, `komit_maju[]` | semua = **KLAIM**; `percobaan` (jujur) **menaikkan ambang Sharpe G3**; K4 menolak klaim yang melebihi terukur |
| `declarations` | lima pernyataan wajib `true`, `lisensi` | `izin_publikasi` = hasil evaluasi (termasuk yang buruk) boleh dipublikasikan |

Pengerasan (diuji, termasuk uji fuzz pada setiap field): skema tertutup; teks diperiksa dengan **daftar-izin kategori Unicode** (tolak Cc/Cf/Cs/Co/Cn/Zl/Zp,
spasi non-ASCII, pemilih-varian, pengisi tak terlihat; panjang dihitung setelah NFKC dari karakter TERLIHAT); pesan masalah tidak memantulkan teks mentah; URL rujukan
harus https publik (ditolak: localhost, IP, userinfo, port non-standar, host non-ASCII); angka berbatas (int raksasa tak boleh meledakkan `float()`/`json.dumps`);
`validate()` tidak pernah melempar dan mengembalikan paling banyak 50 masalah. FE tetap wajib meng-escape semua string.

## 4. Alur seleksi

| tahap | isi | oleh |
|---|---|---|
| S0 intake | `validate` (template saja) + tanda tangan EIP-712: nonce, deadline dengan TTL maksimum 1 jam, dompet payout ikut menandatangani | kode |
| S1 kunci | `spec_sha` ditulis ke `LockRegistry` sebelum data evaluasi disentuh ([[08-Backlog/06 - Epik Gerbang Sinyal]] §3 C-A) | kode |
| S2 peninjau-bot | `review.review()`: gerbang G1-G11 + KPI K1-K5 pada data dan penggaris kami; laporan ber-sha (di-anchor); **tanpa agen** | kode |
| S3 shadow | jalan maju ter-anchor, paper, minimal 60 hari, PnL net shadow > 0 | mesin |
| S4 slot | `slots.decide`: laporan harus dibuat terhadap **buku yang sama dengan sekarang** (`book_sha`); admit bila ada slot kosong, selain itu rolling (§6) | kode |
| S5 imbalan | kontrak pemisah milik bot (60/40, §8) menjadi `payTo` x402 untuk sinyal bot itu | kontrak |
| S6 rolling dan pembunuh | skor bergulir tanggal-kalender; `pembunuh` terstruktur ditegakkan `killer_triggered` | kode |

Slot ≠ uang nyata. **Slot adalah status paper berhak-rendah, bukan bukti edge**: 60 hari shadow tidak bisa membuktikan edge yang realistis (t-stat 60 hari untuk Sharpe 1
tahunan ≈ 0,4). Hak tinggi - sinyal berbayar dan bagi hasil nyata - menuntut F-D16 pada data maju (n ≥ 20, harapan net > 0, batas bawah CI > 0, BH 0,10, di luar sampel)
**dan** telaah hukum (P75/P80). Pemeriksa F-D16 untuk jalur ini belum dikode (P88). Venue uang nyata kelak kemungkinan Binance Agentic Wallet; sekarang paper penuh.

## 5. Gerbang validitas (G) dan KPI "Fabius juga untung" (K)

Bawaan di kode: `python -X utf8 -m engine.cli lock` mencetak ringkasannya; `GateParams()`, `KpiParams()`, `SlotParams()` mencetak semuanya.

| # | apa yang diuji | ambang bawaan | catatan |
|---|---|---|---|
| G1 PIT | memotong data di hari D tidak mengubah target hari D (11 hari dipilih dari seed + hari terakhir) + hasil berulang identik | semua identik | deteksi look-ahead; tes menyuntikkan bot yang mengintip bar besok |
| G2 DATA | riwayat dan bolong bar | ≥ 1095 hari-pnl; bolong gabungan ≤ 1 % **dan per seri ≤ 5 %** | satu seri bolong tak boleh tenggelam di antara yang bersih (K3 di Epik 05) |
| G3 NET | Sharpe net + bootstrap blok | Sharpe ≥ **max(0,5; ambang terdeflasi untuk N percobaan)** dan persentil-5 > 0 | N = percobaan dideklarasikan + riwayat pengajuan keluarga + 1; enam bot Fabius N = 20 → ambang 0,74-0,78 |
| G4 RECENT | 24 bulan terakhir | Sharpe > 0 **dan ≥ ¼ Sharpe penuh**; 12 bulan negatif = PERINGATAN | peluruhan dari 3 ke 0,01 tak boleh lolos |
| G5 PLATEAU | parameter ×0,5 / 0,75 / 1,25 / 1,5 **dari nilai kandidat** (tipe parameter template dihormati) | ≥ 3 varian BERBEDA, ≥ 3 di antaranya ≥ 0,5 × dasar dan > 0 | parameter kecil (mis. 2) tak punya cukup varian → gagal; varian yang melempar = gagal |
| G6 PHASE | semua fase jadwal (hari-minggu B2; tanggal B5) | rerata ≥ 0,5 dan fase terburuk > 0 | `TB` untuk bot tanpa jadwal berfase |
| G7 FOLD | tahun kalender terbaik dibuang | Sharpe > 0 | F-D16 |
| G8 NULL | bot timing: pergeseran waktu melingkar 200×; **bot alokasi: DUA uji** - buy&hold aset risiko utama (Sharpe dan MDD) **dan** placebo bobot yang sama | batas atas 95 % dari p ≤ 0,05 | campuran saja tak cukup, ATURANNYA harus menambah nilai |
| G9 COST | semua biaya (kunci `*bps*`, `*pct*`) 2× | Sharpe > 0 | penggaris milik kami |
| G10 MARGINAL | menambah bot ke EW petahana (**buku slot sekarang + antrean**) | ΔSharpe ≥ +0,05 dan korelasi maks ≤ 0,7 | `TB` bila buku kosong |
| G11 CAPACITY | kapasitas/likuiditas per venue | **NA** | satu-satunya gerbang yang boleh NA; menghalangi uang nyata |
| K1 ANN_NET | imbal hasil tahunan net | ≥ hurdle 4 % + margin 2 % = **6 %** | pembanding = T-bill token/stablecoin berimbal (asumsi; laporan peneliti 3,1-3,6 %, belum diverifikasi ulang) |
| K2 CALMAR | tahunan net / \|MDD\| | ≥ **0,5** | skala-bebas; semula "MDD ≥ −50 %", **diganti Calmar setelah melihat B1 −58 %** (MDD absolut bergantung ukuran posisi): dicatat |
| K3 AKTIVITAS | sinyal yang akan diterbitkan | ≥ 12/tahun dan ≥ 20 total | tanpa sinyal tak ada yang dijual/diikuti (n ≥ 20 = F-D16) |
| K4 KLAIM | klaim penerbit vs terukur | Sharpe klaim ≤ terukur + 0,5; \|MDD\| klaim ≥ terukur − 10 poin | `TB` tanpa klaim (bot Fabius sendiri) |
| K5 BAGI-LABA | skenario TERBURUK bagi Fabius bila basis = profit | informatif (basis dipilih = pendapatan); menjadi gerbang hanya bila `fee_base="profit"` | selalu dicetak: menunjukkan KENAPA basis profit ditolak |

Status: PASS, FAIL, NA (tak terukur), TB (tidak berlaku secara struktural). **Vonis gagal-tertutup**: semua gerbang wajib harus ada dan PASS/TB; gerbang yang melempar = FAIL;
NA pada gerbang inti memblokir (`TIDAK_TERUKUR`); gerbang hilang = `TIDAK_VALID`. Lolos = `LOLOS_SHADOW` = boleh shadow maju, bukan slot, bukan uang nyata.

**Keterbatasan yang diukur peninjau keamanan:** gerbang deterministik dan publik, jadi penerbit bisa menjalankannya di luar berulang kali dan hanya mengirim pemenang. Pada 476
konfigurasi random-walk tanpa edge, G3 meloloskan 5,3 % dan dua konfigurasi lolos SEMUA gerbang. Karena itu gerbang adalah **penyaring awal**, bukan bukti: (1) ambang G3 naik menurut N;
(2) satu-satunya uji di luar sampel yang sungguhan adalah shadow maju; (3) hak tinggi menuntut F-D16; (4) antrean dibatasi per keluarga (`can_submit`). Yang belum ada: seed rahasia
dari hash blok setelah pengajuan (hook `epoch_seed` sudah ada), BH lintas kandidat, G5 leave-one-out universe (§9).

## 6. Slot dan rolling (`engine/slots.py`; fungsi murni, diuji)

- Kapasitas **10**; wajib ≥ **1 bot identitas** milik Fabius, kebal rolling; hanya keluar lewat pembunuhnya sendiri (`killer_triggered`) dan hanya bila bot identitas lain sudah ditunjuk.
- Penerbit luar ≤ **2** slot; "penerbit" = keluarga: yang berbagi dompet payout digabung (union-find). Penerbit luar wajib punya alamat EIP-55 dan payout EIP-55; `admitted_s` wajib (bawaan 0 melewati masa tenggang).
- Penantang masuk bila: `LOLOS_SHADOW`, **laporan dibuat terhadap buku yang sama** (`book_sha`), shadow ≥ 60 hari, PnL net shadow > 0 (hingga), `fingerprint` belum ada di buku.
- Penuh → rolling: penantang menggantikan penghuni **terlemah yang boleh digusur** hanya bila selisih **berpasangan pada jendela yang sama** ≥ **100 bps dan t ≥ 2** (noise tidak menggusur
  apa pun). Penghuni tak terukur sesudah masa tenggang 60 hari + jendela 90 hari = basi/mati, boleh digantikan penantang sah mana pun. Seri diputus hash (`fingerprint`, epoch), bukan nama.
  Semua penantang dinilai sekaligus per epoch 30 hari (`decide_epoch`): **satu perubahan per epoch**, yang terkuat menang.
- Skor = PnL net bps pada **jendela hari kalender** (bukan jumlah baris): bot yang berhenti tidak mewarisi jendela lama. **Tak terukur ≠ lemah**, sampai masa tenggang + jendela lewat.
- Antrean tanpa biaya pengajuan: ≤ 2 pengajuan berjalan per keluarga dan masa tunggu 30 hari setelah penolakan (`can_submit`).
- Bagi hasil: `economics.split` (§8).

## 7. Dogfood: bot Fabius sendiri melewati peninjau yang sama (hasil 2 Okt 2026, data berakhir 2026-08-31, N = 20)

`python -X utf8 -m engine.cli gate --data <dir> --bot ALL` (petahana G10 = bot lain yang bisa di-replay; `KUNCI PARAMETER: BELUM_DIKUNCI` saat tabel dicetak; **kini TERKUNCI v1 (F-D73)** dan dicetak ulang: vonis dan angka identik):

| bot | vonis | gerbang gagal | KPI (tahunan net / Calmar / sinyal per tahun / K5 informatif) | catatan terukur |
|---|---|---|---|---|
| B1-TREND | TOLAK | G8, G10 | +50,2 % / 0,86 / 313 / Fabius −1,6 %/th | placebo p = 0,090, batas atas 0,123 (lima seed lain: 0,062-0,146, semuanya > 0,05); ΔSharpe EW +0,04; 12 bulan −0,42 |
| B2-RS | TOLAK | G4 | +61,7 % / 0,87 / 1695 / −8,3 %/th | 24 bulan terakhir −0,28; sisanya lulus (placebo p = 0,005; fase rerata +0,87, rentang +0,44..+1,30) |
| B3-CARRY | **LOLOS_SHADOW** | - | +9,4 % / 8,40 / 154 / +3,6 %/th | Sharpe +6,05 (vol ≈ 1,6 %/th); 12 bulan terakhir **−3,64** (peringatan; dorman) |
| B4-LISTING-FADE | TIDAK_TERUKUR | - | - | replay menunggu pipeline event (P73) |
| B5-CORE-RWA | **TOLAK** | G8 | +23,8 % / 0,79 / 23 / +0,1 %/th | (a) lulus: Sharpe +1,13 vs +0,84, MDD −30,1 % vs −76,6 % BTC; (b) **gagal**: placebo p = 0,299, batas atas 0,352 |
| B6-BOUNCE | TOLAK | G3, G8, G10, K2 | +15,9 % / 0,40 / 236 / −2,6 %/th | Sharpe +0,43 < ambang 0,74; Calmar 0,40 < 0,5 |

Pembacaan: (a) **hanya satu dari lima yang bisa dinilai lolos (B3), dan ia sedang dorman dan negatif 12 bulan**; (b) B5 yang lolos pada versi sore **kini gagal**: nilainya adalah
campuran BTC+emas, bukan aturan inverse-vol-nya (placebo bobot yang sama p = 0,299) - itu temuan #10 peninjau keamanan, dan ia benar; (c) kegagalan B1 sangat dekat ambang
(p, ΔSharpe) - tanda ambang, bukan bukti B1 palsu; (d) KPI tidak mengubah satu pun vonis sebelumnya kecuali menambah K2 pada B6; (e) 12 bulan terakhir negatif untuk semua bot kecuali B5;
(f) K5: basis profit tanpa bagi-rugi membuat Fabius rugi pada B1, B2, B6 meski bot-nya untung; hanya B3 yang aman.

**Bot identitas (permintaan builder: yang trading crypto, biar kelihatan beneran trading).** Hanya B1-TREND yang memenuhi "trading kripto yang kelihatan" dan "bisa jalan di Binance
Agentic Wallet" (long-only on-chain): B2/B3/B6 butuh short atau perp atau sedang diam, B5 bukan trading kripto murni. **Catatan jujur:** B1 **gagal dua gerbang secara tipis** (G8, G10) dan
12 bulan terakhir −0,42. Identitas = **penunjukan**, bukan kelulusan: ia kebal rolling tetapi catatannya tampil dengan gerbang yang gagal, ia mati lewat pembunuhnya sendiri
("12 bulan maju tanpa mengalahkan buy&hold pada MDD dan Sharpe"), dan F-D16 tetap berlaku sebelum uang nyata. ~~Menunggu satu kata builder (§10 #2).~~ **Dikonfirmasi (F-D73): "Yang penting tradenya instrumen kripto, saya gas."** Dikode di `engine/book.py` (`trades_crypto_only`; buku genesis = B1 saja; bot Fabius lain lewat gerbang → shadow → slot).

## 8. Imbalan dan kontrak (60/40; rancangan, ~~tidak ada kontrak yang ditulis~~ kontrak ditulis + diuji lokal 7 Okt, belum di-deploy)

- **Penerbit 60 % / Fabius 40 % dari pendapatan penjualan sinyal bot itu** (keputusan builder; `engine/economics.py`: `split` tepat bilangan bulat, debu pembulatan ke Fabius, jumlah selalu sama dengan masukan;
  `share_change_allowed`: bagian Fabius hanya boleh **turun**). Bot Fabius sendiri 100 % Fabius. Basis = pendapatan (bukan profit trading) - lihat K5.
- Satu `RevenueSplitter` per bot (klon EIP-1167, alamat dihitung dulu lewat CREATE2 supaya server x402 bisa menawarkan `payTo` sebelum klon dipasang). Pembeli membayar ke klon itu lewat x402;
  `release(token)` bersifat *pull*; tidak ada yang bisa menyita saldo yang sudah terkumpul; keluar dari slot hanya menghentikan `payTo` baru. `economics.split` adalah rujukan dan vektor uji untuk Solidity.
- **`BotRegistry`**: `botId → (penerbit, specSha, splitter, status {SHADOW, AKTIF, TERGUSUR, PENSIUN})`; transisi menunjuk `report_sha` yang sudah di-anchor supaya siapa pun bisa menghitung ulang keputusan.
- Identitas on-chain hanya alamat dompet; kontak dan data pribadi di luar chain (UU PDP) dan di luar hash/tanda tangan. Identitas ERC-8004 penerbit opsional (kepemilikannya belum diverifikasi).
- Pembayaran x402 **memang** lewat kontrak (token ERC-20 + Permit2 + proxy x402 kanonis `0x402085c2…`, sudah dipakai di 97); yang baru hanya penerima (`payTo`) berupa kontrak pemisah.
  Kalkulator `economics.break_even_subscribers` (asumsi harga dan biaya operasi, bukan gerbang): pelanggan berbayar yang dibutuhkan agar 40 % Fabius menutup biaya operasi satu bot.

**Pembaruan 7 Okt (P81): kontrak DITULIS + DIUJI lokal, BELUM di-deploy** - [[02-Contracts/C9 - BotRegistry]] dan [[02-Contracts/C10 - RevenueSplitter]]. Yang mengikuti teks di atas: satu klon EIP-1167 per bot lewat CREATE2 (alamat yang dihitung `engine/splitter.py` sama dengan klon yang benar-benar di-deploy di EVM uji Foundry); `release(token)` bersifat pull; pembagian persis `economics.split` (98 vektor split sampai 2^256-1, 70 vektor `share_change_allowed`, 8 skenario release bertahap / tarif turun); bagian Fabius hanya turun, hanya oleh Fabius; tidak ada penyitaan; status tidak menyentuh splitter; transisi menunjuk laporan yang di-pin di LockRegistry. **USULAN yang melampaui teks ini (builder boleh menolak):** (a) salt CREATE2 mengikat penerbit + payout + specSha; (b) `deploySplitter` tanpa izin, supaya uang di alamat prediksi tidak bergantung pada pendaftaran; (c) tabel transisi enam panah (SHADOW → AKTIF/PENSIUN, AKTIF → TERGUSUR/PENSIUN, TERGUSUR → AKTIF/PENSIUN, PENSIUN final); (d) "sudah di-anchor" ditegakkan sebagai pin `anchorer` di LockRegistry, dan kunci spesifikasi tidak boleh lebih baru dari laporan pendaftarannya; (e) aturan segmen saat tarif turun: saldo yang belum di-checkpoint ikut tarif baru (bisa 1 wei di bawah versi ber-checkpoint, ditemukan fuzz); (f) `releaseIssuer` / `releaseFabius` per pihak; (g) dompet Fabius bisa diganti Fabius. Uji: `forge test --offline` 117/117 (BotRegistry 18, RevenueSplitter 21); `python -X utf8 -m unittest engine.tests.test_splitter` 11 OK. Belum: deploy (kata builder), gerbang x402 yang menawarkan `payTo` klon, perkakas operator untuk mendaftar / transisi, dan telaah hukum (P75/P80).

## 9. Risiko dan hasil tinjauan keamanan independen (12 temuan, diukur oleh peninjau; status per akhir 2 Okt malam)

| # | temuan | tingkat | status |
|---|---|---|---|
| 1 | gerbang = oracle publik deterministik tanpa kontrol uji-berganda; `percobaan` tak dibaca; 476 konfigurasi noise: G3 meloloskan 5,3 %, dua lolos semua gerbang | kritis | **sebagian**: ambang G3 dideflasi menurut N (percobaan + riwayat keluarga + 1); hook `epoch_seed`; batas antrean. **Terbuka:** seed rahasia dari hash blok, BH lintas kandidat, G5 leave-one-out, tahan 12 bulan terakhir |
| 2 | G10 hanya terhadap enam bot Fabius; `decide` percaya string vonis lama tanpa ikatan | tinggi | **sebagian**: `book_sha` mengikat laporan ke buku, laporan basi ditolak. **Terbuka:** orkestrator yang membangun `incumbents` dari buku hidup + antrean (CLI masih enam bot Fabius) **Update F-D73:** `intake`/`review` kini memakai buku genesis (B1 saja; `engine/book.py`) sebagai petahana bawaan, `--incumbents six` = perilaku lama; `gate` dogfood tetap enam bot. Terbuka: antrean dan buku hidup |
| 3 | kunci dedupe = sha seluruh spesifikasi (nama, kalimat, urutan universe, `60` vs `60.0`) | tinggi | **diperbaiki**: `BotSpec.fingerprint()` dipakai di slot. **Terbuka:** dedupe korelasi PnL terhadap antrean, gabung keluarga lewat sumber dana |
| 4 | uji admit/gusur tak bermakna statistik (PnL +0,01 bps lolos; margin 100 bps ≈ 0,1 sd; kuota "siapa cepat"; seri oleh nama) | tinggi | **diperbaiki** untuk gusur (selisih berpasangan + t ≥ 2, jendela sama, `decide_epoch`, seri hash). Admit tetap lemah **dan dikatakan** (slot = paper berhak-rendah); hak tinggi menunggu F-D16 (P88) |
| 5 | bot lemah/mati menduduki slot selamanya; `pembunuh` tak ditegakkan; ambang tak berbatas | tinggi | **diperbaiki**: jendela tanggal, basi/mati bisa digantikan, `killer_triggered`, ambang berbatas. **Terbuka:** orkestrator yang memanggilnya |
| 6 | pertahanan teks tersembunyi = daftar-hitam 5 rentang (Tag block, pemilih-varian, C1, pengisi lolos; surrogat; ESC dipantulkan; URL localhost/IP/userinfo) | tinggi | **diperbaiki** (daftar-izin kategori Unicode, NFKC, echo aman, URL publik, nama dicadangkan) + tes |
| 7 | vonis fail-open (`verdict([])` = lolos; G3 NA lolos; CLI rc 0 tanpa gerbang) | sedang | **diperbaiki** (gagal-tertutup, status TB, per-gerbang try/except, `intake` rc 2 tanpa `--data`) |
| 8 | NaN lolos (`NaN <= 0` False) dan membekukan rolling; bawaan fail-open; "FABIUS" string bebas | sedang | **diperbaiki** (`kw_only` wajib, finite, issuer EIP-55, payout wajib) |
| 9 | G5 menyusut diam-diam (param kecil, tipe float jadi int, varian melempar dibuang) | sedang | **diperbaiki** + **cacat saya sendiri** (varian dari nilai bawaan template, bukan nilai kandidat) ditangkap tes. **Terbuka:** leave-one-out universe |
| 10 | null per-template lemah (B5 vs BTC buy&hold lolos tanpa sinyal; G6 dilewati) | sedang | **sebagian**: G8 alokasi = dua uji (B5 kini TOLAK). **Terbuka:** benchmark universe-matched + bootstrap; entri `NULL_KIND`/fase eksplisit untuk semua template |
| 11 | klaim identitas melebihi penegakan (kontak ikut hash publik = oracle tebak-kontak; tanpa TTL/nonce; payout tak terautentikasi) | sedang | **sebagian**: kontak keluar dari hash, TTL 1 jam, `used_nonces`, payout ikut menandatangani, `verify_identity` dipanggil `review`. **Terbuka:** penyimpanan nonce server, `ownerOf` ERC-8004 |
| 12 | dokumen gerbang melebihi kode (G4, G9, G2, G1; bootstrap non-iid; vonis tanpa param/data hash) | rendah-sedang | **sebagian**: G4 rasio, G9 semua kunci biaya, G2 per seri, G1 11 hari, laporan memuat sha parameter dan data. **Terbuka:** bootstrap untuk non-iid |

**Demonstrasi hidup dari temuan #1 dan #3.** Contoh formulir di repo (`engine/examples/submission.example.json`: B1-TREND, N = 30, universe hanya ETH + BNB; angka `percobaan: 6` di contoh itu
**fiktif**) dijalankan lewat `python -X utf8 -m engine.cli review --file engine/examples/submission.example.json --data <dir>` pada data nyata dan **LOLOS_SHADOW**: Sharpe +1,35 (p5 +0,64; ambang 0,54
untuk N = 7), placebo p = 0,010 (batas atas 0,021), ΔSharpe EW +0,11 dengan korelasi maks **+0,69** terhadap petahana (ambang 0,7 - lolos tipis), K1-K4 lulus, `mengikat: false` (identitas dan kunci belum ada).
Itu bukan bukti edge: itu persis kebebasan memilih universe dan parameter yang diukur peninjau - varian dua-aset B1 tampak lebih baik dari B1 enam-belas-aset (+1,01) **karena dipilih sesudah melihat data**.
Satu-satunya yang membedakan nasib bot semacam ini dari noise adalah shadow maju. (Jalankan ulang dengan `--placebo-n 60 --boot-n 100` memberi vonis yang sama; lari penuh di atas.) **Dicetak ulang 2 Okt (F-D73) terhadap buku genesis (B1 saja), kunci TERKUNCI:** vonis tetap LOLOS_SHADOW; G10 ΔSharpe EW +0,28 dan korelasi maks +0,69 (1 petahana); K1 +72,2 %/th, K2 Calmar 1,33; `mengikat: TIDAK` (identitas belum terverifikasi); `report_sha 0x4a178e16…196c`. Klon-berpilihan B1 (universe ETH+BNB, N = 30) lewat dengan korelasi 0,69 terhadap bot identitas - masuk riset (epik 08 R11).

Risiko lain: **Sybil** (banyak dompet satu orang): sebagian lewat keluarga payout dan G10, belum ada KYC. **Hukum (tidak diketahui):** membayar penerbit pihak ketiga (KYC/AML, pajak), status "nasihat investasi" untuk sinyal, UU PDP untuk kontak (P75/P80).
**Apakah ada yang mau mengajukan?** Tidak diketahui; insentif kecil bila bot harian tidak peka-waktu. **Manipulasi lewat sinyal** pada `feed` (aset tipis): `feed` ditutup. **Ambang sewenang-wenang dan satu sampel** (16 aset, 2020-2026, satu sumber data):
hasil dogfood menolak 4 dari 5 bot yang bisa dinilai - bisa berarti terlalu ketat atau botnya lemah; keduanya informatif.

## 10. Keputusan builder dan yang masih menunggu

**Sudah dijawab (2 Okt malam, F-D72):** (1) bagi hasil **60/40**; (2) bot identitas **bot trading kripto** (kandidat konkret: B1-TREND, menunggu konfirmasi karena catatannya di §7 → **dikonfirmasi di F-D73**);
(4) **`template` dulu**; (5) **tanpa biaya pengajuan** (antrean dibatasi, §6); (6) **peninjau = bot ber-KPI, bukan agen**; (7) tingkat 0 (umpan bukti) **boleh duluan**.

**Dijawab di putaran 3 (2 Okt, F-D73):** (1) basis 60/40 = **pendapatan penjualan sinyal** ("Betul"); (2) bot identitas = **B1-TREND** ("Yg pnting tradenya instrument crypto saya gas"); (3) dan (4) ambang v1 - gerbang, KPI, slot, 60/40 - **dikunci sementara** ("Sementara ini oke, nanti kita coba riset lagi untuk mengoptimalkan itu"); riset: [[08-Backlog/08 - Riset Optimasi Ambang]].

**Menunggu (sisa):** ~~(a) meng-anchor sha kunci v1; (b) meng-commit `engine/` + vault~~ **(a) dan (b) selesai di F-D74**; (c) anggaran riset: positif-palsu dan daya (epik 08 §1, dijelaskan di §1a; belum diputuskan).

~~**Menunggu:**~~ (daftar sebelum F-D73, dipajang; keempatnya sudah dijawab di atas):
1. **Basis 60/40**: pendapatan penjualan sinyal (asumsi saya; §1 #2 menunjukkan basis profit merugikan Fabius) - mohon konfirmasi.
2. **Konfirmasi bot identitas** (usul B1-TREND, dengan catatan gerbang yang gagal tampil terbuka), atau bot lain.
3. **Kunci ambang**: `python -X utf8 -m engine.cli lock --write --note "<siapa, kapan>"` menetapkan semua angka (gerbang, KPI, slot, 60/40) dan mencetak sidik jarinya; mengubah satu angka sesudahnya = kunci baru yang terlihat.
   Perlu kata builder; sebelumnya vonis peninjau hanya indikatif (`mengikat: false`).
4. Ambang KPI (hurdle 4 % + margin 2 %, Calmar 0,5, 12 sinyal/tahun) - usul saya, belum pernah ditinjau builder.

## 11. Backlog usulan

> Sejak 2 Okt malam status tiap item ada di [[08-Backlog/01 - Backlog]] bagian *Arah operator*; kolom catatan di bawah tetap sebagai riwayat.

| ID | kerja | catatan |
|---|---|---|
| P81 | `BotRegistry` + `RevenueSplitter` (klon per bot, pull-payment, bagian Fabius hanya turun, `economics.split` sebagai vektor uji) | M3; [[08-Backlog/06 - Epik Gerbang Sinyal]] §3 → **7 Okt: ditulis + diuji lokal, BELUM di-deploy** ([[02-Contracts/C9 - BotRegistry]], [[02-Contracts/C10 - RevenueSplitter]]; status di [[08-Backlog/01 - Backlog]]) |
| P82 | ~~peninjau agen~~ **DIGANTI (F-D72): peninjau-bot** - kode selesai (`review.py`); sisa: FE/antrean, penyimpanan nonce, pemeriksa URL rujukan | bawaan tanpa model |
| P83 | penghitung percobaan global + BH lintas kandidat + seed rahasia dari hash blok + tahan 12 bulan terakhir | menutup sisa temuan #1 -> **penghitung global + alpha A1/k dibangun 3 Okt malam** (`engine/registri.py`, F-D88 #7); BH lintas kandidat, seed rahasia, tahan 12 bulan menunggu R4 |
| P84 | jalur `method_pr` (templat PR, pemeriksaan statis, tes wajib) | ditutup sampai ada keperluan |
| P85 | ledger shadow maju per bot (anchor) + skor bergulir + statistik berpasangan yang memberi makan `slots.decide` | bergantung M2 (P77): **ledger paper maju dibangun (F-D75)**; skor bergulir, statistik berpasangan, dan anchor kepala ledger belum → kepala ledger kini dikomit per tick lewat SignalAnchor oleh worker Railway (F-D80, P94); skor bergulir + statistik berpasangan tetap belum → **dibangun 3 Okt WIB (P85, `engine/forward.py`, `engine.cli ledger skor`); angka SlotParams kunci v1, tidak ada angka baru; status di [[08-Backlog/01 - Backlog]]** |
| P86 | **kunci** `GateParams`/`KpiParams`/`SlotParams` (`engine.cli lock --write`) + banner | sebelum kandidat luar pertama; ~~**perlu kata builder**~~ **selesai sementara (F-D73): v1 terkunci; ter-anchor dan di-commit (F-D74, P91)** |
| P87 | orkestrator buku hidup: membangun `incumbents`, memanggil `killer_triggered`, mengelola epoch | menutup sisa temuan #2 dan #5 → **dibangun 3 Okt WIB (F-D85): buku hidup `ledger/book/buku.jsonl`, petahana G10 = buku sekarang, epoch 690 tercatat + di-pin; pembunuh terstruktur hanya untuk penerbit luar (B1/B3 teks: P107)** |
| P88 | pemeriksa F-D16 pada data maju (n ≥ 20, harapan net > 0, CI bawah > 0, BH) sebagai syarat hak tinggi | ~~belum dikode~~ **dibangun 2 Okt (`engine/fd16.py`); parameter usulan di bawah tabel; status di [[08-Backlog/01 - Backlog]]** |
| P89 | G5 leave-one-out universe; G8 alokasi universe-matched + bootstrap; `NULL_KIND`/`PHASE_VARIANTS` eksplisit tiap template | temuan #9/#10 |
| P90 | **riset optimasi ambang** R1-R11 (aturan anti-snooping, pra-registrasi, kunci v2 hanya lewat `lock --write --supersede`) | [[08-Backlog/08 - Riset Optimasi Ambang]] |
| P91 | meng-anchor sha kunci v1 (satu transaksi) + meng-commit `engine/` dan vault | ~~**kata builder**; belum dikerjakan~~ **selesai (F-D74): anchor 2026-10-02T08:17:48Z, commit; push: lihat F-D74 #5** |

**P88 - parameter pemeriksa F-D16 maju (ditulis 2 Okt sebelum settle maju pertama ada; DIKUNCI 3 Okt WIB atas kata builder, F-D84, `engine/locks/fd16.lock.json`, di-pin LockRegistry):** dinilai per bot atas
`settle` final (funding aktual) dan sinyal maju dari tick. S1 sinyal maju >= 20; S2 rerata net harian > 0; S3 batas bawah CI 95 % rerata > 0 (bootstrap blok
melingkar 5 hari, 10.000 tarikan, benih = ujung rantai ledger - siapa pun mendapat angka yang sama); S4 rerata tetap > 0 sesudah bulan kalender (UTC) dengan
jumlah net terbesar dibuang (butuh >= 2 bulan dan >= 20 hari); S5 p satu sisi (bootstrap terpusat) lolos Benjamini-Hochberg alpha 0,10 lintas semua bot yang
punya p. Vonis LOLOS / BELUM CUKUP DATA / TIDAK LOLOS. Batas: ongkos = penggaris spesifikasi (fee per sisi), spread + dampak belum (P69); LOLOS bukan izin
uang nyata (P75/P80) dan bukan klaim edge.

## 12. Batas

- Satu sampel (16 penyintas, 2020-2026, satu sumber data dengan bolong); gerbang menilai **masa lalu**; shadow maju adalah satu-satunya bukti yang berarti.
- B4 belum bisa dinilai; `method_pr`/`feed` ditutup; G11 NA; tidak ada penerbit luar, kontrak (C-H ditulis + diuji lokal 7 Okt, belum di-deploy), FE, atau orkestrator buku hidup.
- Teks teori tidak dinilai mesin (keputusan: tanpa agen). Peninjau tidak memeriksa keberadaan URL rujukan.
- Kunci v1 = ambang yang disetujui **sementara**, bukan ambang teroptimasi; riset di [[08-Backlog/08 - Riset Optimasi Ambang]]. ~~Berkas kunci belum di-commit dan belum di-anchor (jam `dikunci` = jam laptop).~~ Kunci ter-anchor (F-D74); jam yang berlaku = `anchoredAt` 2026-10-02T08:17:48Z, bukan `dikunci`.
- Plafon daya: dengan riwayat beberapa tahun, edge Sharpe ≤ 0,5 tidak terpisahkan dari noise oleh gerbang apa pun (`09-Inbox/Session-2026-10-02-skrip/run14_power_arithmetic.py`); hanya data maju yang menjawab.

**Terkait:** [[05 - Epik Enam Bot]] · [[06 - Epik Gerbang Sinyal]] · [[00-Overview/03 - Decisions]] (F-D70, F-D71, F-D72, F-D73, F-D16, F-D17, F-D18, F-D11) · [[08-Backlog/08 - Riset Optimasi Ambang]] ·
[[Concepts/One-Way Gate]] · [[Concepts/Unmeasured Is Not Clean]] · [[Concepts/Anchored Before Outcome]] · [[09-Inbox/Session-2026-10-02]]
