---
tags: [perkakas, "TL10"]
---

# TL10 - kunci dan anchor kunci

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `engine/locks.py`, `engine/locks/review.lock.json`, `python -X utf8 -m engine.cli lock`, `tools/anchor_lock.py`, `engine/locks/anchors/`

**Ringkas:** kunci ambang peninjau-bot v1 (sha `0xf145b70abd251b9fcf421bfb811bcf3788dade347c37b3bea331a09fedfe5f32`) dan pemetaannya ke SATU baris DecisionAnchor (verdict ABSTAIN sebagai pemetaan, bukan keputusan dagang).

**Poin kunci:**
- `tools/anchor_lock.py` bawaannya rencana; `--send` mengirim satu transaksi dari agen; `--verify` membaca ulang tanpa kunci dan tanpa gas.
- Jam yang berlaku = `anchoredAt` 2026-10-02T08:17:48Z (waktu blok), bukan `dikunci` di berkas (jam laptop).

**Yang ia TOLAK lakukan:** mengirim bila agen tidak aktif, bila kunci bukan alamat agen terdaftar, atau bila kode tidak cocok dengan berkas kunci; mencetak kunci.

**Detail:** mengubah satu ambang = kunci baru lewat `lock --write --supersede` (P90).

**Terkait:** [[TL8 - engine]] · [[08-Backlog/08 - Riset Optimasi Ambang]] · [[00-Overview/03 - Decisions]] F-D73/F-D74
