---
tags: [agen, "A3"]
---

# A3 - One-Way Gates

**Bagian dari:** [[01-Agent/00 - Hub Agent]]
**Sumber:** `tools/judge.py` §1, `tools/direction.py::apply_gates`, `contracts/ExecutionVault.sol`

**Ringkas:** aturan tunggal — komponen penilai hanya boleh mengurangi. Tertulis di tiga lapisan
sekaligus supaya tidak bisa dibypass di hilir.

**Poin kunci:**
- `judge.py`: model hanya boleh memveto/mengecilkan; kalau model bilang arah berbeda dari data,
  hasilnya turun ke `OBSERVASI` dan `conf` dipotong, bukan posisi dibuka.
- `direction.apply_gates`: ④ `BLOCKED` → `side=flat` (satu-satunya hak mematikan arah);
  `UNMEASURED/DISAGREE` → kehilangan hak kursi, arah boleh tetap tertulis.
- `ExecutionVault`: menolak `decisionHash`/`snapshotHash` kosong; menolak saat `killSwitch`;
  menolak melebihi cap — dan `HARD_CEILING` **memotong** perintah pemilik, bukan menolaknya.
- Bukti perilaku, bukan niat: saat Jev bilang `short` untuk dua kandidat yang `bar < 720`,
  keputusannya tetap `flat` dan itu tercetak di keluaran (`06-Results/04`).

**Detail:** kebalikan yang harus diwaspadai — kegagalan pengukur yang diperlakukan seperti hasil
bersih ([[Concepts/Unmeasured Is Not Clean]]).

**Terkait:** [[Concepts/One-Way Gate]] · [[04-Tools/TL3 - security_gate]]
