---
tags: [perkakas, "TL2"]
---

# TL2 - direction.py

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/direction.py`, `06-Results/04 - Negative Results.md`

**Ringkas:** penghasil keputusan arah lengkap — `side`, entry, stop, target, ukuran risiko, horizon
— plus dua rezim keluar. Ia juga tempat gerbang kursi ditegakkan dan umur snapshot di-hash.

**Poin kunci:**
- Arah ditentukan **data kami sendiri** (gap SMA24 ± 1% searah ret24), bukan oleh model; model hanya
  boleh memveto/mengecilkan.
- Dua rezim: `stop-loss` hanya saat yakin (conf ≥ 0,6 dan |acf| terstruktur); sisanya `time-stop`
  keras 24 jam + exit-size ≤ 1% likuiditas. Alasan "jual saja saat 0" ditolak dengan ukuran: saat
  rug jualannya **ditolak kontrak** — dan itu sekarang diukur (`04-Tools/TL3`), bukan diandaikan.
- `apply_gates` menegakkan ①+④+⑥ → `seat_eligible` + `seat_blockers` (nama awalnya `apply_security`
  dan menetapkan kursi dari ④ saja → kolom "kursi" membesar; syaratnya yang disamakan ke namanya).
- Konsekuensi yang tidak terduga dari bentuk `seat_blockers`: string `①bar=` / `④` / `⑥liq=` ikut
  masuk `decision` → ikut **di-hash** menjadi `decisionHash` (`direction.py:424-438`). Jadi glyph
  itu tidak bisa "diganti ASCII" tanpa mengubah hash keputusan siklus berikutnya — sementara `①④⑥`
  tidak ada di cp1252. Yang disetel bukan stringnya tapi terminalnya: semua perintah Python di vault
  ini ditulis `python -X utf8`. Tanpa itu `print` tabel bisa melempar `UnicodeEncodeError` **di
  tengah** laporan, dan kegagalan di tengah lebih buruk dari kegagalan di awal: separuh angkanya
  sudah tercetak dan terbaca seperti hasil penuh.
- Temuan 27 Sep (`_research/check_print_glyphs.py`, 6 baris di seluruh repo): yang di `direction.py`
  dibiarkan dengan alasan di atas; yang di perkakas vault kuubah ke ASCII karena tidak meng-hash apa
  pun.
- Umur snapshot (`universe_age_h`) masuk `snapshotHash`: keputusan di atas data basi tetap terbaca
  basi **sampai ke hash-nya** — ini yang membuat klaim point-in-time tidak bisa disamarkan.
- Berkas keluar `decisions/direction-<UTC>Z.jsonl`; nama file pakai UTC (pernah lokal WIB sehingga
  "20260925" berisi data "2026-09-24T18:00Z").
- Status penting: **aturan yang dihasilkan alat ini sudah diuji dan rugi setelah ongkos**
  ([[06-Results/04 - Negative Results]]) — jangan kutip keluarannya seolah sinyal.

**Terkait:** [[01-Agent/A2 - Decision Spine]] · [[04-Tools/TL5 - ledger]]
