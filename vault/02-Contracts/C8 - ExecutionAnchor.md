---
tags: [kontrak, "C8"]
---

# C8 - ExecutionAnchor

**Bagian dari:** [[02-Contracts/00 - Hub Contracts]]
**Sumber:** `contracts/ExecutionAnchor.sol`, `test/ExecutionAnchor.t.sol` (4 test), alat deploy `tools/deploy_execution_anchor.py` · keputusan
[[00-Overview/03 - Decisions]] F-D96 · backlog P132

**Ringkas:** catatan ISI ORDER di venue terpusat (Binance, Aster) untuk sinyal yang sudah dikomit di [[C7 - SignalAnchor]] - satu event rinci per isi,
terutama order UANG NYATA (`real = true`; permintaan builder 4 Okt: kejadian real trade punya metadata lebih rinci di catatan on-chain). Berbeda dari
[[C3 - ExecutionVault]] (swap DEX yang terjadi DI chain): yang ini mencatat apa yang terjadi di LUAR chain.

**Metadata per isi (struct `Fill`, event `Executed`):** commitId (komit bot+bar pemicu), venue, simbol, clientOrderId deterministik, id order venue, sisi,
real/demo, waktu kirim + isi (ms), qty, harga rata-rata, fee (x 1e8) + aset fee, `reportHash` = sha256 baris laporan lengkap di `ledger/eksekusi/`.

**Yang ditegakkan kontrak:**
1. `commitId` harus komit SignalAnchor yang ADA dan pelapor = committer komit itu (`UnknownCommit`, `NotCommitter`) - eksekusi tidak bisa ditempel ke
   sinyal orang lain atau sinyal yang tidak pernah disegel.
2. **R-E1 di chain:** order yang mengaku dikirim sebelum `committedAt` ditolak (`SentBeforeCommit`); isi tidak boleh lebih awal dari kirim.
3. Satu catatan per (pelapor, venue, clientOrderId) (`AlreadyRecorded`); `recordBatch` all-or-nothing.
4. Tanpa nilai nol (qty, harga, sisi 1/2).

**Yang TIDAK dibuktikan:** bahwa venue benar-benar mengisi order (balasan venue tidak bertanda tangan) - waktu dan angka tetap klaim pelapor; yang
dijamin hanya keterikatan ke komit, urutan, dan keunikan. Tanpa pemilik, tanpa hak istimewa, tanpa dana.

**Bukti 4 Okt:** `forge test --match-contract ExecutionAnchorTest` 4 lulus; seluruh suite 67/67; runtime 2.903 B. Rencana deploy (tanpa tx):
penanda tangan = committer `0xCA9c…64A4` (bukan deployer Lencana), konstruktor = SignalAnchor `0x9B78…64f3`, perkiraan 689.653 gas (~0,00069 tBNB).
**TER-DEPLOY 4 Okt atas kata builder ("Gas"):** `0x8bfd03b73749ab2cf91129155127404fbbac4c9b`, tx `0xbe895287a9a989dd2b50e97d91a7fb6e82bb2ba7fd5ae89a97907f79cd8c904d`,
blok 134.856.983, gas 683.065; baca ulang: panjang kode = artefak, `anchor()` = SignalAnchor. Dicatat di `deployments/97.json`
(`contracts.ExecutionAnchor`, `m3.execution_anchor`).

**Terkait:** [[C7 - SignalAnchor]] · [[C6 - LockRegistry]] · [[04-Tools/TL27 - ledger eksekusi]] · [[08-Backlog/10 - Epik Eksekusi Venue]]
