---
tags: [perkakas, "TL1"]
---

# TL1 - judge.py

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/judge.py`, `06-Results/03 - Not Yet Proven.md` #13

**Ringkas:** penilai LLM yang **boleh dicabut**. Defaultnya `none` (gerbang deterministik); kalau
dinyalakan, ia hanya boleh mengurangi ([[01-Agent/A3 - One-Way Gates]]).

**Poin kunci:**
- Rantai provider: Jev/Typesafe System-One → cadangan OpenAI-compatible → `abstain`.
- `ask_jev(state, questions)` menerima pertanyaan **dari pemanggil**. Tanpa ini, `direction.py`
  menyiapkan `side_<SYM>` tapi `judge()` mengirim pertanyaan bakunya sendiri → kolom `model` kosong
  **sambil mencetak `ok=True`** (bug nyata 25 Sep: klaim terlihat seperti sudah memanggil model).
- Pertanyaan bertipe `noul` (bahaya) dipakai **satu arah**: veto boleh membatalkan, tidak pernah
  membuka. Output mentah disimpan biar keputusan bisa direproduksi tanpa model.
- Biaya: router promo terukur $0; jalur resmi $0,042/MTok masuk, keluar gratis — angka pihak
  ketiga, bukan harga yang kami janjikan.
- Belum terbukti: kalibrasi penilai (apakah vetonya memprediksi hasil). Diukur sebagai
  `06-Results/03` #13, statusnya masih terbuka.

**Terkait:** [[04-Tools/TL2 - direction]] · [[Concepts/One-Way Gate]]
