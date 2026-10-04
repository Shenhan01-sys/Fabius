---
tags: [perkakas, "TL29", eksekusi, uang-nyata]
---

# TL29 - canary uang nyata (satu aset, <= 10 USDT, mengikuti B1)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/canary.py` (kelas `Canary`, `fills_of`, `chain_recorder`) · pembungkus `tools/operator_loop.py::Worker.canary_step` · kontrak
[[02-Contracts/C8 - ExecutionAnchor]] · web: `/bot` (lencana REAL/demo), `/status` (`EXEC_OK_REAL`) · tes `engine/tests/test_canary.py` (7) · T8
SK-E22..SK-E29 · keputusan [[00-Overview/03 - Decisions]] F-D92 (tahap S3), F-D96, F-D97 · backlog P133, P134

**Ringkas:** membuktikan MEKANISME uang nyata di Binance USDⓈ-M PROD - order, isi, fee nyata, rekonsiliasi, pencatatan publik - BUKAN kinerja B1
(B1 penuh butuh >= ±1.362 USDT; kinerjanya tetap diukur paper + kertas-venue + akun demo). Canary mengikuti keputusan B1 (bot INTI) untuk SATU aset:
B1 memegang aset itu -> canary memegang anggaran = min(plafon, ekuitas akun) x (1 - 0,2 %); B1 flat -> tutup reduce-only.

**Pagar (dari F-D96):** bawaan `EXEC_REAL=off`; kunci asli di variabel TERPISAH dari kunci demo; izin builder BERTANGGAL `EXEC_LIVE_OK=binance:sampai:YYYY-MM-DD`
(lewat tanggal = tidak ada order); kunci dicek di PROD saat start (`apiRestrictions`: tarik mati, futures hidup) dan mode hedge = berhenti; batas
keras kode 10 USDT (env lebih besar dipotong); posisi yang dimaksud > plafon = berhenti; saldo < order terkecil = `dilewati`; tidak ada order sebelum
komit bar itu di SignalAnchor; leverage 1x; id order deterministik (venue `binance-live`, beda dari demo) + `place` idempoten.

**Sakelar publik (F-D97):** `config/uang_nyata.json` `{"aktif": true|false}` (repo dikirim `false`). Uang nyata butuh variabel Railway bersenjata
DAN sakelar `true` persis. Dibaca SEKALI per bar saat bar baru dieksekusi (dibalik di tengah bar = berlaku bar berikutnya) supaya id order, kunci
ExecutionAnchor, dan ledger satu-laporan-per-bar tidak bertabrakan. MATI + datar = diam (tanpa order, tanpa laporan); MATI + posisi terbuka = bar
berikutnya ditutup reduce-only dan dilaporkan `sakelar: mati`. Bar yang sudah ada di ledger publik `binance-live` tidak dieksekusi ulang sesudah
restart. Penjaga luar `periksa` diam untuk `binance-live` hanya bila MATI + posisi terakhir datar. /status: `EXEC_OK_SWITCH_OFF` / `EXEC_OK_SWITCH_ON`.
Keluar darurat di tengah bar = tutup manual di aplikasi Binance. Worker meng-clone `config/` (sparse-checkout `ledger deployments config`).

**Publikasi:** tiap bar yang diproses -> laporan ke umpan Gist (`binance-live`, mode `live`; juga bila 0 order, karena penjaga luar menuntut laporan
tiap bar terkomit - celah ini ditemukan saat meninjau dan ditutup sebelum tayang) -> rantai GitHub menulis `ledger/eksekusi/binance-live/B1-TREND.jsonl`.
Isi yang benar-benar terisi -> SATU tx `recordBatch` ke ExecutionAnchor dari committer (`real = true`, commitId bar itu, reportHash = sha256 baris
umpan). Gagal mencatat = tertunda dan diulang tiap putaran. Selector `recordBatch` = `0x89b80d44` (dicocokkan dengan artefak forge).

**Bukti 4 Okt (lokal):** 4 tes canary lulus (bawaan off; tolak tanpa kunci/izin/izin kedaluwarsa/aset di luar universe; komit belum ada = TUNDA; ikut
B1 -> 1 order BUY 0,099 @100 = 9,9 USDT, laporan `binance-live`/`live`, catatan on-chain real=true dengan commitId benar, tidak ganda, lalu B1 flat ->
SELL tutup; saldo 4 USDT -> dilewati tetapi laporan 0 order tetap dikirim; plafon env 50 -> tetap <= 10; kunci berizin tarik -> berhenti + alert;
pencatat gagal -> tertunda lalu tercatat tanpa order ganda). Sensus 445/0; forge 67/67; T8 95 baris, 0 masalah.

**Bukti 5 Okt (lokal, F-D97):** 7 tes canary lulus (+3: sakelar dibaca per bar - MATI = tanpa order/laporan, dinyalakan di tengah bar = bar
berikutnya, dimatikan dengan posisi terbuka = SELL tutup di bar berikutnya + laporan `sakelar: mati` + catatan on-chain; bar di ledger publik tidak
dieksekusi ulang; berkas sakelar harus `true` persis, repo dikirim `false`) + 1 tes penjaga luar; sensus 449/0; T8 98 baris, 0 masalah; build web lulus.

**Menunggu langkah builder H8** (lihat [[08-Backlog/10 - Epik Eksekusi Venue]] §9).

**Terkait:** [[TL22 - eksekutor dan kertas-venue]] · [[TL27 - ledger eksekusi]] · [[TL28 - bot sementara dan data B4 B5]]
