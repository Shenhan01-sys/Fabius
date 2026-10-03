---
tags: [perkakas, "TL21"]
---

# TL21 - waitlist (penampung daftar tunggu tingkat 1)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/waitlist.py` (stdlib) · uji `engine/tests/test_waitlist.py` (8) · dijalankan rantai GitHub `.github/workflows/paper-ledger.yml` tiap putaran

**Ringkas:** tombol "Masuk daftar tunggu" dan "Kabari saya di Telegram" di landing membuka bot `@FabiusTradingAgent_Bot` dengan asal tautan
(`?start=tingkat1`, `?start=pintu_manusia`). Telegram hanya menyimpan update yang belum diambil selama 24 jam, jadi tanpa pembaca, pendaftar hilang
besok. Alat ini membacanya tiap 5 menit sepanjang hari (rantai `paper-ledger` hidup terus). Penampungnya adalah **chat builder**
(`ALERT_TELEGRAM_CHAT`): tiap pendaftar dikabarkan ke sana dengan nama, @username, chat id, dan asal tautan. Riwayat chat itu privat dan permanen; tidak
ada data pribadi yang masuk repo publik.

**Perintah pengunjung:** `/start [asal]` masuk daftar tunggu (balasan: tingkat 1 TERKUNCI sampai F-D16 + telaah hukum, paper, tanpa janji keuntungan,
tautan bukti + MCP) · `/bukti` vonis terbaru per bot dari snapshot web · `/stop` keluar (dikabarkan ke builder sebagai -1) · teks lain = bantuan.
Chat builder sendiri yang menekan `/start` mendapat status penampung, bukan entri daftar.

**Konfirmasi tanpa berkas keadaan:** update dikonfirmasi dengan `getUpdates` offset = id terakhir + 1. Konfirmasi itu disimpan di server Telegram, jadi
restart atau runner baru tidak mengulang pendaftar lama.

**Yang ia TOLAK lakukan (T8 SK-P2..SK-P5):**
- kabar ke builder gagal -> berhenti, update itu dan sesudahnya TIDAK dikonfirmasi (TUNDA, diulang 5 menit lagi), supaya tidak ada pendaftar yang hilang diam-diam;
- `getUpdates` tak terbaca atau crash sendiri -> keluar 3, bukan "tidak ada pendaftar"; rantai ledger tetap jalan (peringatan saja);
- mencetak nama, username, chat id, isi pesan, atau token ke log: log Actions repo ini PUBLIK, jadi lognya hanya hitungan;
- menahan antrean karena satu pengunjung memblokir bot (dihitung `balasan_gagal`).

**Batas yang jujur:** daftar = riwayat chat builder, bukan basis data. Pendaftar yang menekan `/start` dua kali muncul dua kali, dan `/stop` hanya
dikabarkan (tidak ada daftar yang dihapus otomatis). Balasan datang paling lambat ±5 menit (jeda putaran rantai), bukan seketika.

**Cara menjalankan manual:** `python -X utf8 tools/waitlist.py --poll` dengan `ALERT_TELEGRAM_TOKEN` + `ALERT_TELEGRAM_CHAT` di lingkungan (keluar 0
beres, 2 tanpa kanal, 3 TUNDA). Jangan dijalankan bersamaan dengan rantai untuk alasan selain uji: dua pembaca saling mengambil update.

**Terkait:** [[TL19 - web landing]] · [[TL18 - worker_watch]] · [[07-Testing/T8 - Semantik Kegagalan Operator]] · [[00-Overview/03 - Decisions]] F-D72
