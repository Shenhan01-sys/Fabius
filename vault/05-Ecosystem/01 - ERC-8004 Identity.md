---
tags: [ekosistem, "E1"]
---

# 01 - ERC-8004 Identity

**Bagian dari:** [[05-Ecosystem/00 - Hub BNB Ecosystem]]
**Sumber:** `tools/x8004_register.py`, `docs/upstream-8004/`, `docs/agent-card.json`

**Ringkas:** agen Fabius terdaftar sebagai identitas **pada registry resmi BNB Chain**, bukan pada
tabel internal kami. Ini jawaban teknis untuk pertanyaan "bagaimana agen lain tahu kamu ada".

**Poin kunci:**
- Registry `IdentityRegistry` chain 97 = `0x8004A818BFB912233c491871b3d84c89A494BD9e`
  (`name()` = `AgentIdentity`, terverifikasi ada kode; 130 B = proxy).
- Varian `register()` ada tiga di upstream; kami **simulasikan lewat `eth_call` dulu** untuk tahu
  mana yang kontrak terima, baru kirim tx: `register(string)` → tokenId berikutnya **2494**
  (konsisten dengan penghitung indexer 8004scan ±2.452 agen di 97).
- Tx nyata: `0x33f47391…` `status=1`, gas 200.844. Verifikasi tidak percaya tx:
  `getAgentWallet(2494)` dan `ownerOf(2494)` dibaca dari registry → sama dengan alamat agen.
- Parser event kami sempat melaporkan `tokenId 0` untuk tx yang **sukses** — fallback "log pertama,
  topics[1]" mengambil `Transfer(from=0x0)`. Sekarang topik dihitung dari ABI vendor dan
  **tidak ada fallback**: kalau event tak ketemu, alatnya berhenti.
- ABI vendor: `docs/upstream-8004/` (`erc-8004/erc-8004-contracts @ b9e466c2…`, sha256 tercatat).
- Kartu agen `docs/agent-card.json` menunjuk endpoint x402 + berkas keputusan; berkas yang ditunjuk
  **benar-benar ditulis alatnya** (pernah menunjuk ke path yang tidak ada — kelas bug yang sama
  dengan pointer `docs/upstream-x402`).

- **Koreksi 5 Okt 2026 (dibaca ulang dari chain 97 hari itu):** `ReputationRegistry` `0x8004B663056A597Dffe9eCcC1965A193B7388713` dan `ValidationRegistry` `0x8004Cb1BF31DAf7788923b405b754f57acEB4272` ADA di chain 97 - proxy 130 B, `getVersion()` = "2.0.0", `getIdentityRegistry()` = IdentityRegistry kami `0x8004A818…`, implementasi 10.491 B / 5.876 B; agen 2494: `getClients` = [], `getAgentValidations` = []. Kalimat "tidak ada di chain mana pun" di bawah = keadaan saat ditulis, BASI. Rencana pakai: [[08-Backlog/01 - Backlog]] P136 (F-D98).

**Terkait:** [[05-Ecosystem/03 - Discovery Gap]] · [[04-Tools/TL6 - x402 gate and client]]
