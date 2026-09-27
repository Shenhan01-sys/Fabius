---
tags: [klaim, "OI-CS"]
---

# Claims Cheat Sheet — kalimat yang kami larang untuk diri sendiri

**Bagian dari:** [[10-Submissions/00 - Hub Submissions]]
**Sumber:** `README.md`, `06-Results/`, `07-Testing/`

Aturannya sederhana: kalau kalimatnya tidak bisa ditunjukkan ke satu baris keluaran perintah, dia
tidak masuk materi. Yang di bawah ini bukan saran gaya — ini penahan agar submission kami tidak
runtuh saat ada juri yang tahu x402.

| ❌ jangan | ✅ ganti dengan | kenapa |
|---|---|---|
| "agen trading yang menguntungkan" | "agen yang menerbitkan keputusan yang bisa dibuktikan salah" | 3 jalur sinyal diuji; rugi setelah ongkos (`06-Results/04`) |
| "edge tervalidasi di 30 hari" | "satu horison tempat whale > baseline acak — dan kami tidak mengklaimnya, karena panelnya dipilih oleh label pasca-sejarah" | batas atas lookahead (`06-Results/06` §2) |
| "verifiable / tamper-proof / siapa pun bisa memverifikasi" sebagai pembeda | "keputusannya ter-anchor **sebelum** hasilnya ada, dan `anchor.py --verify` membacanya tanpa kunci" | "verifiable" itu table stakes; yang langka urutannya |
| "terhubung ke ekosistem agen BNB" (tanpa lanjutannya) | "identitas ERC-8004 tokenId 2494 di `0x8004A818…` + pembayaran x402 lewat proxy kanonis di 97" | harus ada alamat & tx, bukan kategori |
| "endpoint publik kami" | "endpoint di mesin kami (belum di-host); URL berubah tiap run" | `agent-card.json` menuliskan itu; jangan menghapus katanya |
| "62 snapshot tervalidasi sha256" | "60 dari 62; 2 tidak bisa dihitung ulang dan pemicunya belum diketahui" | `write_universe_manifest.py` |
| "sistem kami sudah diperdagangkan" | "dua round-trip nyata dieksekusi on-chain di 97 lewat vault ber-cap, masing-masing −59 bps — di venue demo kami sendiri, bukan di pasar" | `decisions/execution-trail.jsonl`, [[02-Contracts/C3 - ExecutionVault]] |
| "agent kami untung dari trading" | "yang untung di jalur ini baru biaya pool; posisi pertama kami rugi 59 bps dan itu angka yang diprediksi test suite" | sama |
| "data real-time" | "aliran live GMGN (jendela 8–13 menit) untuk keputusan; Dune punya lag ±1 jam dan dipakai untuk sejarah" | `03-Data/D4` |
| angka win-rate apa pun dengan n < 20 | "n=2, satu menang +1,5 bps / satu rugi −146,3 bps; belum membuktikan apa pun" | `MIN_TRADES=20` (`06-Results/02`) |

Lihat juga: [[06-Results/01 - Claims and Limits]] · [[00-Overview/02 - Business Process]]
