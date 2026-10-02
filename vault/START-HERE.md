---
tags: [entry]
---

# START-HERE — vault Fabius

> **BN-PIVOT - 2 Okt 2026.** Arah proyek bergeser: Fabius menjadi **operator pemilih bot** yang kelak menjual **sinyal
> berbukti** dan membuka slot bot untuk penerbit luar ([[00-Overview/03 - Decisions]] F-D70 dan F-D71). Halaman ini
> menggambarkan keadaan **sebelum** pivot dan tetap benar untuk apa yang **sudah dibangun**; arah baru masih **usulan dan kode
> awal** ([[08-Backlog/05 - Epik Enam Bot]], [[08-Backlog/06 - Epik Gerbang Sinyal]], [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]]).
> Jangan memakai halaman ini untuk menyangkal arah baru, dan jangan menyebut arah baru sebagai fitur yang sudah ada.

> **STATUS 2 Okt malam (dicetak ulang):** arah baru bukan lagi sekadar usulan. Ledger paper maju B1-TREND + B3-CARRY hidup (M2, F-D75..F-D78); kontrak
> `LockRegistry` + `SignalAnchor` ter-deploy di chain 97 (M3, F-D79/F-D80); worker Railway mengomit tiap tick (F-D80; committer dirotasi, F-D82); perekam
> wallet-flow dihentikan (F-D81); data REST = data Vision untuk engine (F-D83). Semua tetap **paper**: tanpa uang nyata, tanpa klaim edge.
> Status per item: [[08-Backlog/01 - Backlog]] bagian *Arah operator*.

**Baca dulu ini, tiga baris:**

1. Fabius adalah agen riset BNB Chain yang **menerbitkan keputusan yang bisa dibuktikan salah**.
   Dia bukan bot yang menjanjikan untung — tiga jalur sinyal sudah kami uji dan dua kami kubur
   ([[06-Results/04 - Negative Results]], [[06-Results/06 - Pre-registration Horizon]]).
2. Setiap angka di vault ini punya perintah yang mencetaknya. Kalau halaman dan hasil run berbeda,
   **yang menang run-nya** ([[Conventions]] §2).
3. Yang boleh dikutip publik ada di [[10-Submissions/01 - Claims Cheat Sheet]]; yang dilarang
   juga di sana, beserta kalimat penggantinya.

## Siapa membaca apa

| kamu | mulai dari |
|---|---|
| juri / orang baru | [[00-Overview/01 - Briefing]] → [[10-Submissions/02 - Project Detail]] |
| yang mau menjalankan | [[00-Overview/04 - Run It]] (semua perintah, sekali copy) |
| yang mengaudit klaim | [[06-Results/01 - Claims and Limits]] + [[07-Testing/01 - Test Commands]] |
| agen lanjutan (sesi berikutnya) | [[09-Inbox/00 - Hub Inbox]] terakhir + [[08-Backlog/01 - Backlog]] |
| yang mau menambah metode analisis | [[TradingKnowledge/00 - Hub Trading Knowledge]] lalu matriksnya: [[TradingKnowledge/07-Peta-Fabius/GAP1 - Matriks Metode x Tahap]] |
| yang cari angka | [[Quick-Reference]] (alamat, hash, gas, tanggal, semua bersumber) |

## Peta lapisan

| # | Modul | Satu baris |
|---|---|---|
| 00 | [[00-Overview/00 - Hub Overview]] | produk, proses bisnis, keputusan, koreksi, cara menjalankan |
| 01 | [[01-Agent/00 - Hub Agent]] | apa yang agen putuskan, gerbang satu-arah, kursi & rotasi |
| 02 | [[02-Contracts/00 - Hub Contracts]] | kontrak di chain 97: anchor, vault eksekusi, venue, vendor x402 |
| 03 | [[03-Data/00 - Hub Data]] | perekam point-in-time, aliran wallet ⑦, kedalaman harga, Dune |
| 04 | [[04-Tools/00 - Hub Tools]] | satu catatan per perkakas, dengan apa yang ia tolak lakukan |
| 05 | [[05-Ecosystem/00 - Hub BNB Ecosystem]] | identitas ERC-8004, pembayaran x402, penemuan antar-agen |
| 06 | [[06-Results/00 - Hub Results]] | angka yang diukur, ambang terkunci, dan apa yang belum terbukti |
| 07 | [[07-Testing/00 - Hub Testing]] | rumah semua angka: perintah + keluaran aslinya |
| 08 | [[08-Backlog/01 - Backlog]] | sisa kerja, risiko, yang kami tunda dan alasannya |
| 09 | [[09-Inbox/00 - Hub Inbox]] | catatan sesi bertanggal (bahan mentah, belum terstruktur) |
| 10 | [[10-Submissions/01 - Claims Cheat Sheet]] | kalimat submission, alamat kontrak, angka publik |
| 11 | [[11-Notes/00 - Hub Notes]] | catatan pendukung bertopik |
| TK | [[TradingKnowledge/00 - Hub Trading Knowledge]] | pengetahuan trading per metode — setiap klaim metode wajib lewat [[TradingKnowledge/Fakta Terukur]] dulu |

Lihat juga [[Index]] (semua halaman), [[Conventions]] (aturan menulis), [[Dashboard]].
