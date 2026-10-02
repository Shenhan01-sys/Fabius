---
tags: [perkakas, "TL15"]
---

# TL15 - lock_spec

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/lock_spec.py`

**Ringkas:** mem-pin satu berkas kunci (`engine/locks/*.lock.json`) ke [[02-Contracts/C6 - LockRegistry]]: botId = label ASCII, specSha = sha kunci. Jam yang
berlaku untuk kunci = `lockedAt` (waktu blok), bukan `dikunci` di berkas (jam laptop) - pola yang sama dengan kunci ambang v1 (F-D74).

**Poin kunci:**
- Bawaan rencana (tanpa kunci, tanpa gas); `--verify` membaca ulang `lockedAt`; `--send` mengirim SATU `lock()` dari committer M3.
- Alamat kunci HARUS sama dengan `deployments/97.json` -> `m3.committer`; uri = berkas pada commit HEAD (push dulu supaya tautannya ada).
- Hasil dicatat di `deployments/97.json` -> `m3.pins`.

**Yang ia TOLAK lakukan:** mengirim bila sha berkas tidak sama dengan sha(params) (berkas rusak), bila kunci bukan committer, atau bila label sudah di-pin (idempoten);
mencetak kunci.

**Detail:** dipakai pertama 3 Okt WIB untuk `FABIUS-FD16-MAJU-v1` (F-D84): tx `0x6bf7d51201…`, blok 134475778, gas 123.050, `lockedAt` 2026-10-02T17:10:57Z.

**Terkait:** [[TL10 - kunci dan anchor kunci]] · [[TL8 - engine]] · [[00-Overview/03 - Decisions]] F-D84
