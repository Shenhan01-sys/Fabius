---
tags: [perkakas, "TL3"]
---

# TL3 - security_gate.py

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/security_gate.py`, `06-Results/03` #17

**Ringkas:** mengukur bidang ④ (honeypot / bisa dijual) untuk kandidat arah, dari **dua sumber**,
dengan empat status — dan `UNMEASURED` tidak dihitung bersih.

**Poin kunci:**
- Kenapa baru sekarang layak: jalur screen butuh 40 alamat/snapshot (terbukti tak terbayar); jalur
  arah ≤ 5 kandidat → 10 panggilan per siklus. Skala mengubah kesimpulan.
- GMGN `token/security` membalas 200 dengan `is_honeypot` **boolean** dan `can_not_sell`; GoPlus
  **tidak punya `can_not_sell`** sama sekali — dicatat sebagai ketiadaan field, bukan nol.
- Empat status: `OK` / `BLOCKED` / `DISAGREE` / `UNMEASURED`. `UNMEASURED` terpicu nyata
  (satu kandidat `is_honeypot=null`) → hak kursi dicabut.
- Dua sumber bisa **tidak sepakat** soal pajak jual (0,03 vs 0,0): ambang `DISAGREE` di ≥5 %,
  jadi kasus 3 % ini tetap `OK` **tapi tercatat** sebagai perbedaan sumber.
- Bentuk join heks antar sumber adalah sumber bug: `to_hex()` Trino kapital, perekar kecil
  (lihat [[04-Tools/TL7 - measurement harness]]).
- Yang **tidak** dibuktikan ④: honeypot adalah milik **token spot**; ia membuktikan dasar harga
  perp tidak bisa disandera, bukan bahwa posisi perp bisa ditutup di venue-nya.

**Terkait:** [[Concepts/Unmeasured Is Not Clean]] · [[06-Results/03 - Not Yet Proven]]
