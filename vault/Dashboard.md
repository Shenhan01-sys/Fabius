---
tags: [dashboard]
---

# Dashboard

Pertanyaan proyek dalam bentuk tabel. Semua barisnya diambil dari perintah yang ada di repo;
kolom "diperbarui" adalah tanggal run, bukan tanggal edit halaman.

| pertanyaan | jawaban sekarang | dibuktikan oleh | diperbarui |
|---|---|---|---|
| Produknya apa? | agen yang menerbitkan keputusan yang bisa dibuktikan salah | [[00-Overview/01 - Briefing]] | 2026-09-27 |
| Kenapa tidak "bot trading"? | tiga jalur sinyal diuji; dua mati, satu ditahan karena lookahead | [[06-Results/04 - Negative Results]] | 2026-09-27 |
| BNB-nya di mana? | kontrak 97 · identitas ERC-8004 · pembayaran x402 · venue & vault eksekusi | [[05-Ecosystem/00 - Hub BNB Ecosystem]] | 2026-09-27 |
| Bisa dijalankan orang lain? | ya: `forge test`, `anchor.py --verify` (tanpa kunci), `ledger.py` | [[07-Testing/01 - Test Commands]] | 2026-09-27 |
| Angka paling jujur yang kami punya | −72,4 bps rata-rata dari 2 posisi jatuh tempo (n=2) | [[06-Results/07 - Matured Outcomes]] | 2026-09-27 |
| Yang paling lemah sekarang | eksekusi nyata belum terjadi di 97; gateway belum di-host | [[08-Backlog/01 - Backlog]] | 2026-09-27 |
| Berapa sisa waktu | tenggat 30 Sep 23:59 **WIB** | [[00-Overview/06 - Roadmap]] | 2026-09-27 |

```dataview
TABLE WITHOUT ID file.folder AS folder, file.name AS halaman
FROM "09-Inbox" SORT file.name DESC
```
