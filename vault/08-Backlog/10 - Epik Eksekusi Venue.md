---
tags: [backlog, epik, prd, eksekusi, venue]
---

# 10 - Epik Eksekusi Venue (PRD): sinyal Fabius -> order sungguhan di Binance Agent OS, Aster, Tokocrypto

**Bagian dari:** [[08-Backlog/00 - Hub Backlog]]
**Dibuka:** 4 Okt 2026 (WIB) oleh builder: *"Binance Agent OS + Aster gas + Tokocrypto, kita implementasikan, tapi prioritas no1 itu binance agent OS dulu, lalu aster,
baru kalau sempet itu Tokocrypto, gas buat planningnya di vault, workflownya sesuaikan di vault juga agar PRDnya jelas + terukur"* -> [[00-Overview/03 - Decisions]] F-D91.
**Bahan:** [[08-Backlog/05 - Epik Enam Bot]] §6 (venue, leverage) dan §7 (biaya per jalur) · F-D90 (venue lokal, compliance ditunda) · [[07-Testing/T8 - Semantik Kegagalan Operator]]

> **STATUS: RENCANA (PRD v1).** Belum ada kode eksekusi, belum ada akun venue, belum ada kunci. Angka ambang di §6 adalah **usulan** sampai builder
> menyetujui PRD ini; sesudah itu ia dikunci seperti ambang lain (mengubahnya = keputusan baru yang terlihat). **Uang nyata hanya atas kata builder per venue**
> (saklar `live`, §5 R-E7); "paper penuh sampai builder yakin" (F-D73) tetap berlaku sampai kata itu ada.


## 0a. Revisi v1.1 (4 Okt): modal nyata maksimal 10 USDT, kertas WAJIB sebelum uang nyata (F-D92)

Builder: *"Terkait dana awalan pastinya sangat terbatas maksimal hanya ada di 10 usdt, eksekusi aja prdnya sebagian yg paling posible tapi minimal mencakup
50% dari PRD. Pastikan konsep paper sebagai awalan test akurasi tetap ada sebelum open posisi uang asli ya"*.

**Akibat yang terukur:** B1 penuh (16 aset x 6,25 %) butuh >= ±80 USDT di Aster dan >= ±800 USDT di Binance (min notional per aset, snapshot
`ledger/kertas/filter/`). Dengan 10 USDT tiap aset hanya 0,625 USDT, jadi **tidak satu pun posisi B1 bisa dibuka**. Itu tercatat sebagai `dilewati`, bukan
dipotong diam-diam. Maka tahapnya menjadi:

| tahap | apa | uang nyata | gerbang keluar |
|---|---|---|---|
| **S0** paper | ledger resmi (sudah ada) | tidak | - |
| **S1** kertas-venue | keputusan yang sama dieksekusi di atas kertas: harga 1m sesudah komit, lot + min notional + fee venue; modal virtual 2.000 dan 10 USDT; jadwal `komit` (kenyataan) dan `p99` (andaian) | tidak | >= 10 hari bursa; tracking error dalam ambang §6 pada jadwal yang akan dipakai live |
| **S2** testnet pipa | adaptor mengirim order sungguhan ke testnet (kunci testnet, tanpa dana nyata) | tidak | 10 tick: 0 order ganda, selisih posisi 0, 100 % sesudah komit |
| **S3** canary pipa | **1 aset, <= 10 USDT**: order buka + tutup mengikuti keputusan B1 untuk aset itu. Membuktikan MEKANISME (isi, fee nyata, rekonsiliasi, latihan mati), BUKAN kinerja B1 | ya, atas kata builder | 5 siklus tanpa pelanggaran keselamatan; fee + slippage nyata tercatat |
| S4 skala | B1 penuh | ya | modal >= batas venue + kata builder |

**Cakupan yang dibangun 4 Okt (>= 50 % PRD):**

| butir | status |
|---|---|
| R-E1 bukti dulu | ✅ kertas: tick tanpa komit = TUNDA, lebih tua dari kunci = SEBELUM_KUNCI (eksekutor live memakai fungsi yang sama) |
| R-E2 idempoten | ✅ client id deterministik + `place` mencari id dulu |
| R-E3 rekonsiliasi | 🟡 fungsi deteksi; turun ke dry = eksekutor live |
| R-E4 rencana | ✅ lot, min notional, ubah kecil, tutup reduce-only |
| R-E5 pagar | ✅ universe, long-only, notional <= modal x 1, batas per order; batas rugi: fungsi (berhenti = live) |
| R-E6 izin kunci | ✅ cek izin (fungsi + panggilan prod `apiRestrictions`), belum pernah dipakai dengan kunci sungguhan |
| R-E7 saklar | ⬜ bagian eksekutor live (P118) |
| R-E8 semantik kegagalan | ✅ T8 SK-E1..SK-E9 berjangkar kode + tes |
| R-E9 rahasia | ✅ env, disamarkan di galat (diuji) |
| R-E10 ledger eksekusi | 🟡 ledger kertas berantai hash + verify; ledger dari riwayat trade venue menunggu order sungguhan |

Tonggak: E0 ✅ · E1 ✅ kode (keluar "5 tick sungguhan" = 5 catatan kertas berturut, menyusul otomatis) · E2 🟡 adaptor tanpa testnet · E3 🟡 kertas + metrik ·
E4-E6 ⬜. Hitungan: 7 dari 10 kebutuhan ✅, 2 🟡, 1 ⬜.

## 1. Masalah dan tujuan

Hari ini sinyal Fabius hanya paper: target bobot B1/B3 dihitung, ditulis ke ledger, dan disegel ke SignalAnchor, tetapi tidak ada order. Tujuan epik ini:
sebuah **eksekutor** yang menyelaraskan posisi akun venue dengan target bot, dengan:

1. **Bukti dulu, order kemudian:** tidak ada order untuk target yang komitmennya belum ada di chain (urutan waktu bisa diperiksa publik).
2. **Kesetiaan terukur ke paper:** selisih hasil eksekusi vs paper (tracking error, slippage, fee) diukur harian dan punya ambang.
3. **Pagar keras:** tanpa izin tarik, leverage 1x, batas modal per venue, saklar mati, dan gagal-tertutup (T8).

**Bukan tujuan (non-goals):** menjual sinyal (tingkat 1 tetap terkunci, F-D72); leverage > 1x (= spesifikasi baru, epik 05 §6); menarik dana; keputusan
diskresioner; model bahasa di jalur order (eksekutor deterministik, sama seperti engine).

## 2. Lingkup per venue (urutan = prioritas builder)

| # | venue | produk | bot yang bisa | catatan terukur |
|---|---|---|---|---|
| 1 | **Binance Agent OS** (sub-akun Agentic) | USDⓈ-M futures + spot | **B1** (perp long/flat = persis basis harga paper); **B3** (spot long + perp short, keduanya di satu sub-akun) | lingkungan `prod/testnet/demo` ada (`binance-cli`, skill resmi); min notional TESTNET: BTC 50, ETH 20, lainnya 5 USDT -> modal B1 penuh >= ±800 USDT (prod diukur di E1); domain prod terblokir dari jaringan builder |
| 2 | **Aster** (API V3, agent wallet) | perp (+ spot) | **B1**; B3 setelah likuiditas spot Aster diukur | min notional 5 USDT semua aset B1 (dibaca 4 Okt) -> modal B1 penuh >= ±80 USDT; agent wallet `canPerpTrade` tanpa `canWithdraw`; testnet ada |
| 3 | **Tokocrypto** (bila sempat) | spot | **B1** saja (long/flat) | 16/16 aset B1 punya pasangan USDT (F-D90); tanpa testnet: dry-run lalu canary kecil; selisih harga spot vs perp paper harus diukur |

Bot lain (B2, B4, B5, B6) tidak di epik ini.

## 3. Aktor

- **Builder:** pemilik akun dan kunci; satu-satunya yang menyalakan `live` dan menaikkan batas modal.
- **Eksekutor** (service Railway baru `fabius-exec`, terpisah dari worker komit): memegang kunci TRADE tanpa izin tarik; tidak menulis repo.
- **Penulis ledger eksekusi** (rantai GitHub, penulis tunggal `ledger/eksekusi/`): memegang kunci READ-ONLY; membaca riwayat trade dari venue.
- **Publik:** memeriksa urutan komit -> order dan selisih eksekusi vs paper.

## 4. Alur kerja harian (workflow target)

```
00:00Z bar tutup
  -> tick resmi (rantai GitHub, ±08:40Z; kelak REST ±00:05Z, P99/P100)
  -> worker komit + ungkap di SignalAnchor (fabius-engine)
  -> EKSEKUTOR (fabius-exec), per venue x bot:
       1. baca tick dari ledger publik + pastikan komitnya ADA di chain        (R-E1)
       2. baca posisi + saldo venue (sumber kebenaran posisi = venue)          (R-E3)
       3. rencana order = target bobot x modal venue - posisi sekarang,
          dibulatkan ke lot; ubah kecil di bawah ambang dilewati             (R-E4)
       4. pagar risiko: daftar simbol, batas notional, leverage 1x, rugi harian (R-E5)
       5. kirim order (clientOrderId = hash(signal_id, venue, kaki, bar))     (R-E2)
       6. tunggu isi / batas waktu -> rekonsiliasi posisi                     (R-E3)
       7. log + alert (Telegram) bila ada yang menyimpang                     (R-E8)
  -> PENULIS LEDGER EKSEKUSI (rantai GitHub, kunci read-only):
       riwayat trade venue -> ledger/eksekusi/<venue>/<bot>.jsonl (berantai hash)
       -> metrik harian: slippage vs hargaRef, fee, tracking error vs paper     (§6)
  -> PENJAGA LUAR: tick dikomit tetapi tidak ada order dalam X menit = ALARM   (perluasan P111)
```

Mode eksekutor (`EXEC_MODE`): `off` -> `dry` (hitung rencana, tidak mengirim) -> `testnet` -> `live` (butuh `EXEC_LIVE_OK=<venue>:<tanggal>` dari builder).
Alarm apa pun menurunkan mode ke `dry` sampai builder menyalakan lagi.

## 5. Kebutuhan fungsional (setiap butir punya cara ukur)

| ID | kebutuhan | diukur dengan |
|---|---|---|
| R-E1 | tidak ada order untuk target yang komitnya belum ada di SignalAnchor | rekonsiliator: waktu order > `committedAt` untuk 100 % order |
| R-E2 | idempoten: tick yang sama diproses dua kali = 0 order ganda | tes + cek harian `clientOrderId` unik |
| R-E3 | posisi venue = posisi yang dimaksud sesudah tiap tick (selisih <= 1 lot) | rekonsiliator harian; selisih = ALARM |
| R-E4 | rencana order = target x modal - posisi; ubah < max(min notional, 10 % target) dilewati dan DICATAT | tes rencana; jumlah lewatan di log |
| R-E5 | pagar: simbol = universe bot; leverage 1x; notional total <= modal; rugi harian > batas = berhenti + alert | tes pagar; uji paksa di testnet |
| R-E6 | kunci tanpa izin tarik DIPERIKSA saat start (Binance `apiRestrictions.enableWithdrawals = false`; Aster agent `canWithdraw = false`; Tokocrypto: kunci tanpa centang tarik, dibuktikan builder) - gagal = tidak jalan | tes start; log start |
| R-E7 | saklar: `EXEC_MODE` + `EXEC_LIVE_OK`; tanpa keduanya tidak ada order prod | tes; dicoba sekali per venue (latihan mati <= 1 tick) |
| R-E8 | semantik kegagalan per baris T8 (SK-E*, ditulis sebelum kode) | `check_failure_semantics.py --run` |
| R-E9 | rahasia: kunci hanya di variabel Railway/GitHub yang dipasang builder; tidak pernah di chat, repo, log | `prepush_check` + pemindai log |
| R-E10 | ledger eksekusi berantai hash, ditulis penulis tunggal (rantai GitHub, kunci read-only) dari riwayat trade venue | `engine.cli` verify eksekusi (dibangun di E1) |

## 6. Metrik dan kriteria lulus (USULAN, dikunci saat PRD disetujui)

| metrik | definisi | ambang usulan |
|---|---|---|
| tracking error harian | \|return eksekusi - return paper\| per bot per hari, bps modal | median <= 10 bps, p95 <= 30 bps (20 hari bursa) |
| slippage | harga isi rata-rata vs `hargaRef` sinyal (penutupan bar), bps, bertanda | median <= 5 bps (aset besar perp); dilaporkan per aset |
| fee | fee nyata per sisi, bps | <= asumsi paper 7 bps (Binance/Aster); Tokocrypto dilaporkan apa adanya (10 bps) |
| latensi | ungkap -> semua order terkirim | p95 <= 10 menit |
| kelengkapan | tick dikomit yang dieksekusi penuh | 100 % (kecuali TUNDA yang tercatat) |
| keselamatan | order di luar aturan R-E1/R-E5/R-E6 | **0** (satu saja = mode `dry` + tinjauan) |
| latihan mati | saklar -> tidak ada order baru | <= 1 tick, sekali per venue sebelum `live` |

Aturan naik modal: sesudah 20 hari bursa `live` di dalam semua ambang, builder BOLEH menaikkan batas modal (kata builder; tidak pernah otomatis).

## 7. Tonggak (milestone) dan gerbang keluar

| tonggak | isi | keluar bila (terukur) | backlog |
|---|---|---|---|
| **E0** rencana | PRD ini + skema konfigurasi + baris T8 SK-E* (BELUM DIBANGUN) | builder menyetujui PRD (kata) | P116 |
| **E1** inti eksekutor | rencana order, pagar, idempotensi, rekonsiliasi, mode `dry` (tanpa venue) | tes inti lulus; `dry` pada 5 tick sungguhan berturut: rencana = selisih target, 0 beda | P117 |
| **E2** adaptor Binance (Agent OS) testnet | REST futures + spot, cek izin kunci, rencana -> order testnet | 10 tick testnet berturut: 0 order ganda, selisih posisi 0, 100 % order sesudah komit; min notional PROD terukur dari Railway | P118 |
| **E3** ledger eksekusi + metrik | penulis GitHub (read-only), verify, metrik §6 harian, alert penjaga luar | metrik tercetak 5 hari berturut dari data testnet | P119 |
| **E4** Binance live canary | akun Agentic + kunci (builder), modal kecil (builder), 20 hari | semua ambang §6 terpenuhi 20 hari; 0 pelanggaran keselamatan | P120 |
| **E5** Aster testnet -> live canary | agent wallet EIP-712, adaptor perp | sama dengan E2/E4 untuk Aster | P121, P122 |
| **E6** Tokocrypto (bila sempat) | adaptor spot, dry-run, canary kecil | sama, plus basis spot vs perp terukur | P123 |

## 8. Alur kerja pengembangan (berlaku untuk setiap tonggak)

1. **Tulis dulu:** baris T8 (SK-E*) + kriteria keluar di sini; baris backlog berstatus.
2. **Kode + tes** (stdlib + `eth-account` bila perlu tanda tangan; tanpa SDK venue yang tidak bisa diperiksa) -> sensus `--wajib-semua` + T8 `--run` lulus, CI hijau.
3. **`dry` pada tick sungguhan** (tidak ada order) -> bukti di Test Commands.
4. **Testnet** -> bukti.
5. **Kata builder** -> `live` canary dengan batas modal -> 20 hari metrik.
6. **Vault seirama di setiap langkah:** backlog + catatan TL + Inbox + Test Commands + Dashboard/Run It sebelum langkah berikutnya.

## 9. Langkah builder (tidak bisa dikerjakan asisten)

| ID | langkah | dibutuhkan untuk |
|---|---|---|
| H1 | pastikan akun Binance bisa dipakai dari Indonesia + Agent OS tersedia untuk akunmu (aplikasi; tanpa VPN, F-D90) | E4 |
| H2 | buat sub-akun Agentic: Futures + Spot, **tanpa izin tarik**; transfer modal canary | E4 |
| H3 | buat kunci API sub-akun; pasang di variabel Railway `fabius-exec` lewat dashboard (JANGAN lewat chat) | E2 (testnet) / E4 (prod) |
| H4 | tetapkan modal canary per venue | E4, E5 |
| H5 | kata "live <venue>" | E4, E5, E6 |
| H6 | Aster: dompet + agent wallet (`canPerpTrade` saja) | E5 |

## 10. Risiko dan pertanyaan terbuka

- **Akses Binance dari Indonesia** dan ketersediaan Agent OS untuk akun builder: tidak diketahui (H1). Bila tertutup: Aster naik ke prioritas 1 (keputusan builder).
- **IP Railway (Singapura)** untuk endpoint trading Binance prod: ~~belum diuji~~ **TERUKUR 4 Okt ±01:3x WIB** dari dalam container `fabius-probe` (IP keluar SG, AS400940 Railway): testnet `/fapi/v1/time` 200, `/fapi/v1/order` tanpa kunci 401 `-2014 API-key format invalid`; prod `fapi.binance.com` `/fapi/v1/time` 200, `/fapi/v1/order` 401 `-2014`; `api.binance.com/sapi/v1/account/apiRestrictions` 400 `-2014`; Aster `/fapi/v1/time` 200. Artinya endpoint trading terjangkau (balasan dari lapisan otentikasi, bukan blokir wilayah 451/403). Dari perangkat builder testnet butuh Cloudflare WARP; dari Railway tidak. Min notional PROD belum dibaca (E2).
- **Agent OS: konfirmasi "ya" per order** - catatan 2 Okt vs berita: belum pasti (epik 05 §6). Kalau benar wajib, eksekusi otomatis penuh tidak mungkin lewat jalur itu.
- **Modal minimum:** B1 penuh di Binance >= ±800 USDT (testnet; prod mungkin lebih tinggi), di Aster >= ±80 USDT. Canary di bawahnya = sebagian aset tidak bisa
  dibuka = bukan B1 lagi (jangan diam-diam memotong universe).
- **Perubahan bobot kecil** (B1 sama rata 1/n) memicu order kecil di bawah min notional: dilewati (R-E4) dan dihitung sebagai tracking error.
- **Biaya Railway gratis** (restart ON_FAILURE x10) untuk service ketiga; upgrade sebelum ±1 Nov sudah direncanakan.
- **Hukum:** ditunda atas kata builder (F-D90 #5); uang nyata pribadi builder, bukan penjualan sinyal.

**Terkait:** [[00-Overview/03 - Decisions]] F-D90 / F-D91 · [[08-Backlog/01 - Backlog]] P116-P123 · [[08-Backlog/06 - Epik Gerbang Sinyal]] · [[04-Tools/TL18 - worker_watch]]
