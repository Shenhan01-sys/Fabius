---
tags: [perkakas, "TL9"]
---

# TL9 - ledger paper maju

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `engine/ledger.py`, `engine/funding_est.py`, `tools/feed_bars.py`, `tools/paper_tick.py`, `.github/workflows/paper-ledger.yml` + `paper-ledger-watchdog.yml`, `ledger/`

**Ringkas:** ledger paper maju (M2): satu berkas JSONL berantai hash per bot. Tick EX-ANTE paling lambat 12 jam sesudah penutupan bar; hari yang terlewat dicatat `gap` dan tidak pernah diisi belakangan; `settle` EX-POST dihitung ulang oleh `replay()` yang sama dengan gerbang.

**Poin kunci:**
- Penulis TUNGGAL: rantai GitHub `paper-ledger` yang menyambung dirinya sendiri + watchdog tiap 20 menit (F-D78). Worker Railway hanya membaca.
- Data: zip Vision harian (terbit ±08:40-09:40Z) -> tick ±9-10 jam sesudah penutupan; funding final dari zip bulanan; estimasi funding (P92) hanya untuk laporan PROVISIONAL dan target B3.
- Siapa pun bisa memeriksa: `python -X utf8 -m engine.cli ledger verify` menghitung ulang tiap tick dan settle dari `ledger/bars`.

**Yang ia TOLAK lakukan:** membuat tick lewat 12 jam (jadi `gap`); tick bila aset hilang, BTC basi, atau funding B3 hari itu belum ada; menulis apa pun bila rantai rusak.

**Detail:** keadaan 2 Okt malam: B1-TREND dan B3-CARRY masing-masing genesis + satu tick (bar 2026-10-01, dibuat runner). Bukti tick tanpa tangan manusia: 3 Okt (P93).

**Langkah ke-5 sejak 3 Okt (P111):** sesudah tick beres, rantai menjalankan penjaga luar worker ([[04-Tools/TL18 - worker_watch]]) tiap putaran sampai tick hari itu terbukti dikomit + diungkap.

**Langkah ke-4 sejak 3 Okt (P108):** sesudah tick hari itu beres, rantai yang sama menjalankan `engine.cli book epoch --write` + `book verify` dan meng-commit `ledger/book` bila epoch baru ([[03-Data/D8 - Buku Slot Hidup]]). Gagal di langkah ini tidak menghentikan rantai ledger.

**Terkait:** [[03-Data/D7 - Ledger Bars]] · [[TL11 - komit sinyal M3]] · [[00-Overview/03 - Decisions]] F-D75..F-D78
