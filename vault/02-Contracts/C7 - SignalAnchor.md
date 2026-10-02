---
tags: [kontrak, "C7"]
---

# C7 - SignalAnchor

**Bagian dari:** [[02-Contracts/00 - Hub Contracts]]
**Sumber:** `contracts/SignalAnchor.sol`, `test/SignalAnchor.t.sol` (24 test), vektor `test/fixtures/signal_vectors.json` (`tools/gen_signal_vectors.py`),
`tools/signal_commit.py`

**Ringkas:** komit-ungkap sinyal per bot per bar. Saat komit hanya akar Merkle yang masuk chain; sinyalnya diungkap belakangan dan dicek terhadap akar itu.

**Poin kunci:**
- daun = `keccak256(abi.encode(Signal, salt))`, Signal = (v, botId, specSha, asof, asset, aksi, bobotLama, bobotBaru, hargaRef, dataHash) = skema `engine/sinyal.py`;
  pohon pasangan terurut (OpenZeppelin `MerkleProof`). Kecocokan engine ↔ kontrak dibuktikan vektor lintas bahasa, bukan diasumsikan.
- `commit` ditolak bila: spesifikasi belum dikunci pengirim (`NotLocked`), kunci lebih baru dari bar (`LockedAfterBar`), bar belum tutup (`BarNotClosed`),
  lewat `maxLag` (`TooLate`), bar sudah dikomit (`AlreadyCommitted`), akar nol tidak sama dengan n nol (`EmptyMismatch`).
- `reveal` diverifikasi ke akar (`BadProof`); daun tidak dihitung dua kali; `n` yang dikecilkan tidak bisa menyembunyikan daun.
- `markMissed` sesudah `revealWindow`: komit yang tidak diungkap penuh ditandai permanen (cara curang paling umum penjual sinyal: hanya membuka yang menang).
- id komit = `keccak256(abi.encode(committer, botId, specSha, asof))`. Komit SAH Fabius hanya dari `m3.committer` di `deployments/97.json`; komit atas nama
  alamat lain (termasuk committer lama `0xE12e…812a`) bukan dari Fabius.

**Detail:** ter-deploy 2 Okt 13:04Z di `0x9B78200beFbbBe836585d31bd5b6dB32587064f3` (blok 134442917); dibaca `cast`: `registry()` = C6, `maxLag()` 43200,
`revealWindow()` 604800, kode 4.400 B, `commitCount()` 0. Komit pertama diharapkan untuk bar 2026-10-02 sesudah tick 3 Okt ([[08-Backlog/01 - Backlog]] P94).
Gas di EVM lokal (`forge test --gas-report`, median): commit 189.848, reveal 67.807 per sinyal, markMissed 26.690 - angka chain menunggu transaksi nyata.

**Yang TIDAK dibuktikan:** bahwa sinyal bagus, menguntungkan, atau harga referensinya bisa didapat. PnL dihitung ulang di luar chain
(`python -X utf8 -m engine.cli ledger verify`).

**Terkait:** [[02-Contracts/C6 - LockRegistry]] · [[04-Tools/TL11 - komit sinyal M3]] · [[08-Backlog/06 - Epik Gerbang Sinyal]] §3-§4 · [[00-Overview/03 - Decisions]] F-D79/F-D80/F-D82
