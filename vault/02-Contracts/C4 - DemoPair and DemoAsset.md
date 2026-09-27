---
tags: [kontrak, "C4"]
---

# C4 - DemoPair and DemoAsset

**Bagian dari:** [[02-Contracts/00 - Hub Contracts]]
**Sumber:** `contracts/DemoPair.sol`, `contracts/DemoAsset.sol`

**Ringkas:** venue x·y=k (fee 30 bps) plus aset demo 6 desimal. Dibikin sendiri dengan alasan
spesifik, bukan karena malas memakai DEX.

**Poin kunci:**
- Kenapa bukan pooltestnet orang: kalau kami swap ke likuiditas asing lalu menulis "ini slippage
  kami", angka itu bukan milik kami — bisa habis, kosong, atau digeser pihak lain.
- Yang **tidak** diklaim: kurva ini mewakili pasar meme sungguhan. Yang dibuktikan: proses eksekusi
  (harga dari kontrak, bukan dari kami) dan **besarnya ongkos** — dan sejak 27 Sep yang kedua punya
  dua angka yang saling mengunci: test suite memprediksi **59 bps**, eksekusi nyata di 97 menghasilkan
  **−59 bps** realized per round-trip. Prediksi dan kenyataan bertemu di angka yang sama; itu property
  yang tidak bisa direkayasa dengan mengedit salah satunya.
- Biaya round-trip terukur di sini: **59 bps** pada posisi 1 unit (`test_round_trip_...`, mencetak
  `BIAYA ROUND-TRIP TERUKUR`). Ini angka yang menjawab "$5 layak tidak" dari sisi ongkos.
- `costOfBuy(want)` dan `spotPrice()` view → laporan bisa memprediksi dampak sebelum masuk;
  `bootstrap()` sekali saja, setelah itu likuiditas tidak bisa digeser dari luar.
- `DemoAsset` sengaja ERC20 polos, bukan token ber-permit: OZ 5 menarik `Bytes.sol` (`mcopy`,
  Cancun) lewat jalur permit, dan itu akan memaksa seluruh proyek naik target EVM — padahal
  `DecisionAnchor` sengaja ditahan di `shanghai` karena klaim bytecodenya terikat ke sana.

**Terkait:** [[02-Contracts/C3 - ExecutionVault]] · [[09-Inbox/Session-2026-09-26-27]]
