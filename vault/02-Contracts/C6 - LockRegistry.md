---
tags: [kontrak, "C6"]
---

# C6 - LockRegistry

**Bagian dari:** [[02-Contracts/00 - Hub Contracts]]
**Sumber:** `contracts/LockRegistry.sol`, `test/SignalAnchor.t.sol` (24 test bersama C7), `script/DeploySignalAnchor.s.sol`, `tools/m3_setup.py`

**Ringkas:** pra-registrasi yang tidak bisa digeser: "spesifikasi bot X sudah ada pada blok ini". Satu kunci per (pengunci, botId, specSha), ditulis sekali,
jamnya = waktu blok.

**Poin kunci:**
- `lock(botId, specSha, uri)`; nilai nol ditolak (`ZeroValue`); kunci yang sama dua kali ditolak (`AlreadyLocked`).
- Kunci milik ALAMAT yang mengunci: orang lain bisa mengunci botId yang sama, tetapi itu id lain dengan jam lain - tidak ada yang bisa mendahului lalu
  mengklaim jam kunci kami.
- `lockedAt(locker, botId, specSha)` dibaca [[02-Contracts/C7 - SignalAnchor]]: komit hanya untuk spesifikasi yang dikunci pengirimnya sebelum bar.
- Tidak ada yang bisa menghapus atau mengubah kunci, termasuk kami - karena itu kunci committer lama tetap tercatat sesudah rotasi (F-D82).
- `uri` hanya penunjuk di event, tidak disimpan.

**Detail:** ter-deploy 2 Okt 13:04Z di `0xcF6fBF95fc04DEd8d670512CEc0723a2246Fbb0C` (blok 134442907), kode 1.313 B byte-sama dengan artefak build lokal
(`tools/m3_setup.py`). `lockCount()` = 4 (dibaca `cast`): B1-TREND + B3-CARRY oleh committer pertama (13:04Z, PENSIUN) dan oleh committer aktif
`0xCA9c…64A4` (`lockedAt` 1790956160 / 1790956165 = 15:49:20Z / 15:49:25Z). Gas `lock` median 137.756 di EVM lokal (`forge test --gas-report`); angka chain belum dicatat.

**Yang TIDAK dibuktikan:** bahwa spesifikasinya bagus atau dijalankan dengan jujur - hanya keberadaan dan urutan waktu.

**Terkait:** [[02-Contracts/C7 - SignalAnchor]] · [[02-Contracts/02 - Deployed on 97]] · [[00-Overview/03 - Decisions]] F-D79/F-D80/F-D82 · [[Quick-Reference]]
