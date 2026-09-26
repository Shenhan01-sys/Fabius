---
tags: [agen, "A2"]
---

# A2 - Decision Spine

**Bagian dari:** [[01-Agent/00 - Hub Agent]]
**Sumber:** `tools/direction.py`, `tools/decide.py`, `tools/anchor.py`, `tools/ledger.py`

**Ringkas:** lima tahap yang selalu berurutan, dan setiap tahap menghasilkan artefak yang bisa
dibaca orang lain — bukan log di kepala agen. Rekam → saring → putuskan → anchor → nilai.

**Poin kunci:**
1. **Rekam**: `universe/bsc-universe.jsonl` + `universe/wallet-flow.jsonl`, sha256 per baris,
   timestamp commit GitHub ([[03-Data/01 - Dataset]], [[03-Data/D2 - Wallet Flow]]).
2. **Saring**: gerbang ① riwayat bar, ④ keamanan, ⑥ kapasitas keluar — hasilnya
   `seat_eligible` + `seat_blockers` dan ikut masuk `gatesHash` (`direction.apply_gates`).
3. **Putuskan**: `side`/entry/stop/target/ukuran/horizon + dua rezim keluar
   ([[04-Tools/TL2 - direction]]).
4. **Anchor**: `decisionHash` + `gatesHash` + `snapshotHash` ke `DecisionAnchor` di 97; umur snapshot
   ikut di-hash supaya keputusan di atas data basi tetap terbaca basi.
5. **Nilai**: `ledger.py` menutup dari rekaman (bukan dihitung ulang), memisah `BELUM JATUH TEMPO`
   dan `AMBIGU` ([[04-Tools/TL5 - ledger]]).

**Detail:**
- Urutan tidak bisa diputar: tidak ada jalur di mana hasil tahap 5 mengubah tahap 4 (anchor tidak
  pernah ditarik/ditulis ulang — itu satu-satunya fungsi angka ini).
- Model LLM ada di tahap 3 tapi posisinya **di bawah** gerbang ([[Concepts/One-Way Gate]]).
- Sebagian besar keputusan agen adalah `ABSTAIN`: **3 Enter + 14 Abstain** dari `anchorCount()` = 17, dibaca langsung lewat `countByVerdict` (`tools/verdict_counts.py`, 27 Sep). Itu keluaran gerbang, bukan kegagalan.

**Terkait:** [[01-Agent/A3 - One-Way Gates]] · [[Concepts/Anchored Before Outcome]]
