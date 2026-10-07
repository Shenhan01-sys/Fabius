---
tags: [kontrak, "C9"]
---

# C9 - BotRegistry

**Bagian dari:** [[02-Contracts/00 - Hub Contracts]]
**Sumber:** `contracts/BotRegistry.sol`, `test/BotRegistry.t.sol` (18 test), `script/DeployBotRegistry.s.sol`, prediksi alamat di Python `engine/splitter.py`
(`engine/tests/test_splitter.py`, 11 tes), vektor `test/fixtures/splitter_vectors.json` (`tools/gen_splitter_vectors.py`) · backlog P81 ·
[[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] §8 · [[08-Backlog/06 - Epik Gerbang Sinyal]] §3 C-H
**Peta:** [[02-Contracts/C9 - BotRegistry]] (daftar bot + pabrik splitter) · [[02-Contracts/C10 - RevenueSplitter]] (penerima `payTo` per bot, bagi hasil)

> **STATUS: DITULIS + DIUJI LOKAL (7 Okt 2026), BELUM DI-DEPLOY.** Tidak ada alamat chain, tidak ada transaksi, dan tidak ada kunci di sesi yang
> menulisnya. Deploy menunggu kata builder.

**Ringkas:** daftar bot program penerbit, `botId → (penerbit, specSha, splitter, status)` dengan status SHADOW / AKTIF / TERGUSUR / PENSIUN, sekaligus
pabrik klon [[02-Contracts/C10 - RevenueSplitter]] (CREATE2, sehingga alamatnya bisa dihitung sebelum klon ada). Setiap transisi menunjuk laporan yang
sudah di-pin di [[02-Contracts/C6 - LockRegistry]], jadi siapa pun bisa mencari laporannya dan menghitung ulang keputusannya. Kontrak ini TIDAK menilai bot,
tidak membuktikan isi laporan benar, tidak memegang uang, dan tidak menyimpan data pribadi: identitas di chain hanya alamat dompet.

**Poin kunci:**
- Operator = pemilik (`Ownable2Step`) = alamat Fabius. Pemilik yang sama juga "Fabius" bagi setiap splitter (dibaca langsung lewat `registry.owner()`).
- `register(botId, issuer, issuerPayee, specSha, reportLabel, reportSha)` (pemilik saja). Syaratnya: (botId, specSha) sudah dikunci `anchorer` di
  LockRegistry (`SpecNotLocked`); laporan sudah di-pin `anchorer` (`ReportNotAnchored`); kunci spesifikasi tidak lebih baru dari pin laporannya
  (`SpecLockedAfterReport`, yaitu tahap S1 sebelum S2); satu kali per botId (`AlreadyRegistered`). Event: `Registered` + `StatusChanged(NONE → SHADOW)`.
- `setStatus(botId, to, reportLabel, reportSha)` (pemilik saja): hanya panah yang ada di tabel (`BadTransition`), dan setiap transisi wajib punya pin
  `lockedAt(anchorer, reportLabel, reportSha) != 0`. Label + sha ikut di event.
- Tabel transisi (**USULAN**: epik hanya menyebut empat status, bukan panahnya): SHADOW → AKTIF | PENSIUN; AKTIF → TERGUSUR | PENSIUN; TERGUSUR → AKTIF |
  PENSIUN; PENSIUN final; NONE → SHADOW hanya lewat `register`. Uji 5×5 penuh: tepat enam panah.
- Alamat splitter: salt = `keccak256(abi.encode(botId, issuer, issuerPayee, specSha))`, klon EIP-1167 lewat `Clones.cloneDeterministic`. `predictSplitter` =
  alamat yang boleh ditawarkan gerbang x402 SEBELUM pendaftaran. Salt mengikat penerbit, payout, dan spesifikasi (**USULAN**), jadi operator tidak bisa
  memasang klon untuk penerbit atau payout lain di alamat yang sudah ditawarkan (diuji).
- `deploySplitter` tanpa izin dan idempoten (**USULAN**, di luar teks epik): uang yang sudah dibayar ke alamat prediksi tetap bisa dikeluarkan ke pihak
  yang terikat salt, walaupun operator tidak pernah mendaftarkan botnya.
- Status tidak pernah menyentuh splitter. TERGUSUR / PENSIUN hanya menghentikan tawaran `payTo` baru (di luar chain). Diuji: sesudah PENSIUN, `release`
  tetap membayar 900 / 600 dari 1.500.

**Detail:**
- "Laporan sudah di-anchor" ditegakkan sebagai pin di LockRegistry oleh `anchorer` (bawaan skrip: committer M3 `0xCA9c…64A4`), dengan label bebas
  (**USULAN**: epik menyebut "sudah di-anchor" tanpa mekanisme). Keputusan buku bisa memakai pin yang sudah ada (`FABIUS-BUKU-E<epoch>` + `book_sha`,
  lihat C6). Konvensi label untuk laporan peninjau belum ada di perkakas; uji memakai `FABIUS-LAPORAN`.
- Pin dari alamat lain tidak dihitung (diuji untuk kunci spesifikasi dan pin laporan). Setelah `setAnchorer`, pin anchorer lama tidak dihitung lagi untuk
  transisi baru (diuji); transisi lama tetap tercatat di event.
- `initialFabiusBps` immutable (skrip: 4000 = `economics.FABIUS_SHARE_BPS`, kunci v1 F-D73). `anchorer` dan `fabiusPayee` (khusus splitter BARU) bisa
  diganti pemilik, dengan event. Bot Fabius sendiri didaftarkan dengan `issuer` = dompet Fabius dan `issuerPayee` = kas Fabius: hasilnya 100 % ke Fabius
  tanpa tarif khusus.
- Lintas bahasa, dua arah: (a) 4 vektor create2 dari Python diperiksa di forge dengan `Clones.predictDeterministicAddress` + `splitterSalt`; (b) klon yang
  BENAR-BENAR di-deploy `register` di EVM uji Foundry dicetak `test_vektor_evm_dicetak`, diambil `tools/gen_splitter_vectors.py --evm` dari `forge test --json`,
  lalu dihitung ulang di Python (`PredictTests.test_prediction_matches_the_clone_forge_actually_deployed`). `create2_address` juga cocok dengan contoh
  EIP-1014. Masukan yang akan ditolak kontrak tidak diberi alamat oleh helper Python (T8 SK-H1).
- Ukuran (artefak `out/`): runtime 4.996 B, initcode 10.499 B (konstruktornya memasang implementasi `RevenueSplitter`). Gas di EVM lokal
  (`forge test --match-path test/BotRegistry.t.sol --gas-report`, median atas campuran uji): deploy 2.315.014; `register` 348.717 (termasuk klon +
  inisialisasi); `setStatus` 50.335; `deploySplitter` 190.431. Angka chain menunggu transaksi nyata.
- Skrip deploy `script/DeployBotRegistry.s.sol` (env `DEPLOYER_PRIVATE_KEY`, `BOT_REGISTRY_OWNER`, `LOCK_REGISTRY`, `BOT_REGISTRY_ANCHORER`, `FABIUS_PAYEE`,
  `FABIUS_BPS`): berhenti bila LockRegistry tidak punya kode, lalu membaca ulang semua parameter. `run()` hanya pernah dijalankan di EVM uji
  (`test_skrip_deploy_jalan_dan_membaca_ulang`).

**Yang TIDAK dibuktikan / belum ada:** kebenaran isi laporan (yang dibuktikan hanya bahwa laporan itu publik sebelum transisi); kejujuran keputusan slot;
deploy, alamat chain, gas chain; perkakas operator untuk `register` / `setStatus` / pin laporan; gerbang x402 yang menawarkan `predictSplitter` sebagai
`payTo` (sekarang masih `payTo` gerbang); telaah hukum untuk membayar penerbit pihak ketiga (P75/P80). Slot tetap status paper berhak-rendah.

**Terkait:** [[02-Contracts/C10 - RevenueSplitter]] · [[02-Contracts/C6 - LockRegistry]] · [[02-Contracts/C7 - SignalAnchor]] ·
[[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] · [[08-Backlog/06 - Epik Gerbang Sinyal]] · [[07-Testing/T8 - Semantik Kegagalan Operator]] SK-H1 ·
[[00-Overview/03 - Decisions]] F-D72/F-D73
