---
tags: [dashboard]
---

# Dashboard

> **BN-PIVOT - 2 Okt 2026.** Arah proyek bergeser: Fabius menjadi **operator pemilih bot** yang kelak menjual **sinyal
> berbukti** dan membuka slot bot untuk penerbit luar ([[00-Overview/03 - Decisions]] F-D70 dan F-D71). Halaman ini
> menggambarkan keadaan **sebelum** pivot dan tetap benar untuk apa yang **sudah dibangun**; arah baru masih **usulan dan kode
> awal** ([[08-Backlog/05 - Epik Enam Bot]], [[08-Backlog/06 - Epik Gerbang Sinyal]], [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]]).
> Jangan memakai halaman ini untuk menyangkal arah baru, dan jangan menyebut arah baru sebagai fitur yang sudah ada.

Pertanyaan proyek dalam bentuk tabel. Semua barisnya diambil dari perintah yang ada di repo;
kolom "diperbarui" adalah tanggal run, bukan tanggal edit halaman.

| pertanyaan | jawaban sekarang | dibuktikan oleh | diperbarui |
|---|---|---|---|
| Produknya apa? | agen yang menerbitkan keputusan yang bisa dibuktikan salah | [[00-Overview/01 - Briefing]] | 2026-09-27 |
| Kenapa tidak "bot trading"? | tiga jalur sinyal diuji; dua mati, satu ditahan karena lookahead | [[06-Results/04 - Negative Results]] | 2026-09-27 |
| BNB-nya di mana? | kontrak 97 · identitas ERC-8004 · pembayaran x402 · venue & vault eksekusi | [[05-Ecosystem/00 - Hub BNB Ecosystem]] | 2026-09-27 |
| Bisa dijalankan orang lain? | ya: `forge test`, `anchor.py --verify` (tanpa kunci), `ledger.py` | [[07-Testing/01 - Test Commands]] | 2026-09-27 |
| Angka paling jujur yang kami punya | −72,4 bps rata-rata dari 2 posisi jatuh tempo (n=2) | [[06-Results/07 - Matured Outcomes]] | 2026-09-27 |
| Yang paling lemah sekarang | **sinyal**: nol jalur arah yang lolos uji setelah ongkos (rugi 12/12); alat skor ⑦ belum bisa dipercaya; gateway belum di-host | [[08-Backlog/01 - Backlog]] P10–P15 | 2026-09-28 |
| Ilmunya di mana? | lapisan pengetahuan trading per metode, dengan status data & tingkat bukti tiap catatan | [[TradingKnowledge/00 - Hub Trading Knowledge]] · [[TradingKnowledge/Fakta Terukur]] | 2026-09-28 |
| Berapa sisa waktu | tenggat 30 Sep 23:59 **WIB** | [[00-Overview/06 - Roadmap]] | 2026-09-27 |

```dataview
TABLE WITHOUT ID file.folder AS folder, file.name AS halaman
FROM "09-Inbox" SORT file.name DESC
```
