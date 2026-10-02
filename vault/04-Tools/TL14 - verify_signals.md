---
tags: [perkakas, "TL14"]
---

# TL14 - verify_signals

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/verify_signals.py`; tes `engine/tests/test_verify_signals.py` (7) + `test_signal_commit.AnvilEndToEndTests.test_public_verifier_reads_back_sah`

**Ringkas:** pemeriksa PUBLIK komit sinyal Fabius (P106) - untuk pembeli dan pemeriksa, bukan untuk operator. Membaca SignalAnchor + LockRegistry di chain 97
tanpa kunci dan tanpa gas, lalu mencocokkan tiap komit dengan ledger paper dan bar yang di-commit di repo. Ia tidak percaya pada worker, log, atau halaman kami.

**Poin kunci:**
- Lima pemeriksaan per (bot, bar): kunci sebelum bar; komit dalam `maxLag` dengan akar nol hanya bila n = 0; semua n sinyal terungkap; daun tiap event
  `Revealed` dihitung ulang dari muatan + salt dengan skema `engine/sinyal.py`; id sinyal terungkap = `signal_ids` tick, dan tick itu sendiri direproduksi
  PERSIS dari bar.
- Vonis: SAH · BELUM DIUNGKAP · TIDAK DIUNGKAP · MENUNGGU KOMIT · TIDAK DIKOMIT · SEBELUM KUNCI · ALARM. Keluar 1 bila ada ALARM.
- Komit dari ALAMAT LAIN untuk bot kita dihitung (`komit_alamat_lain_untuk_bot_kita`) dan tidak pernah dianggap milik Fabius; yang resmi hanya
  `deployments/97.json` -> `m3.committer`.
- Daftar komit lewat `commitCount()` / `commitIdAt(i)` / `getCommit(id)` (tanpa log); muatan ungkap lewat `eth_getLogs` dari blok deploy, dipotong per 5.000
  blok dan diperkecil bila RPC menolak. "Sekarang" = waktu blok terakhir, bukan jam laptop.

**Yang ia TOLAK lakukan:** memvonis SAH bila satu saja daun tidak bisa dihitung ulang, bila ada sinyal terungkap yang tidak ada di tick, atau bila tick tidak
bisa direproduksi dari bar; menganggap komit alamat lain sebagai bukti Fabius.

**Detail:** run pertama di chain 97 (2 Okt 16:50:39Z, blok 134473069): B1-TREND dan B3-CARRY bar 2026-10-01 = SEBELUM KUNCI, 0 komit, 0 ALARM. Vonis SAH
pertama yang sungguhan menunggu komit bar 2026-10-02 (P94). Di anvil, jalur penuh (deploy -> lock -> komit + ungkap lewat kode worker -> pemeriksa) = SAH
untuk kedua bot.

**Terkait:** [[02-Contracts/C7 - SignalAnchor]] · [[TL11 - komit sinyal M3]] · [[TL9 - ledger paper maju]] · [[08-Backlog/01 - Backlog]] P106
