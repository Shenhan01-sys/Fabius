---
tags: [concept, "one-way-gate"]
---

# One-Way Gate — gerbang yang hanya boleh mengurangi

> **BN-PIVOT - 2 Okt 2026 (konsep operator).** Untuk operator pemilih bot, "gerbang yang hanya boleh mengurangi" mengambil bentuk
> **ruang aksi tertutup** `{NONE, bot terdaftar}`: model hanya boleh memilih dari himpunan itu, menolak, atau mengecilkan; tidak
> pernah menambah bot atau menaikkan plafon. Peninjau pengajuan bot juga satu arah (hanya menolak atau meminta info; yang menerima
> adalah gerbang deterministik). Lihat [[00-Overview/03 - Decisions]] F-D70/F-D71 dan [[08-Backlog/05 - Epik Enam Bot]] §5. Isi di
> bawah tetap utuh untuk jalur yang sudah dibangun.

**Ringkas.** Di seluruh Fabius, komponen apa pun yang menilai suatu kandidat (model LLM, keamanan
kontrak ④, kapasitas keluar ⑥, plafon eksekusi) boleh **membatalkan** atau **mengecilkan**, tidak
pernah membuka posisi yang sudah ditolak gerbang lain.

**Kenapa ini bukan gaya bahasa.** Kalau satu komponen boleh membuka, maka setiap angka negatif dari
komponen lain jadi bisa ditawar, dan "disiplin" berubah jadi kosmetik. Doktrin ini yang membuat
kalimat "agen kami menolak 14 dari 17 keputusan" bisa dipercaya: penolakan tidak bisa dibalik oleh
siapa pun di hilir, termasuk kami.

**Di mana ditegakkan.** `tools/judge.py` (veto satu-arah, keputusan §1), `tools/direction.py::apply_gates`
(④ `BLOCKED` → `flat`; `UNMEASURED` mencabut hak kursi, bukan memberi),
`contracts/ExecutionVault.sol` (posisi ditolak tanpa `decisionHash`/`snapshotHash`, plafon di
byte-code, `HARD_CEILING` memotong perintah pemilik).

**Kebalikannya yang harus diwaspadai:** kegagalan pengukur **tidak** boleh diperlakukan seperti hasil
bersih — lihat [[Unmeasured Is Not Clean]].

Lihat: [[01-Agent/A3 - One-Way Gates]] · [[04-Tools/00 - Hub Tools]]
