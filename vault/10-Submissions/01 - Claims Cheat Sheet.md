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

| "Fabius tahu kapan masuk" | "sepuluh fitur diuji terhadap kontrol terpilih dari kandidat siklus yang sama; **tidak ada yang melewati kontrol itu** setelah pembandingnya dibuat setara - dan dua uji prospectif sedang berjalan dengan kunci tertanggal" | F-D39 (`tools/topk_test.py`): pemenang pertama (+132,9 vs CI atas +116,1) ternyata SATU UNDIAN; dengan median 40 pengulangan jadi +112,7 vs CI atas **+137,5** |
| "Fabius tahu kapan keluar" | "klaim keluar kami gugur saat kontrolnya dibetulkan jadi 'keluar di waktu acak pada jendela yang sama' (64 menang / 50 kalah, p=0,112); yang tersisa cuma memotong umur posisi" | F-D40 (`tools/exit_control.py`) |
| "ada edge dua menit, jadi kami hampir bisa" | "bump **+192,7 → +202,6 bps** pada menit 2-5 lolos placebo asal-mula (datar −180) - lalu tiga tembok mengurungnya: **3,1 %** kabar ada di token yang bisa kita perdagangkan; umur kabar **saat kami memutuskan** = median **808 d (13,5 menit)** - batas atas, F-D50 - sementara bump-nya hidup ±2 menit; dan saat level stop terlewat di antara dua rekaman kami sudah **+245 bps** di bawahnya (E21)" | E11 `tools/horizon_decay.py` · F-D43 `tools/venue_bridge.py` · F-D50 `tools/fast_lane.py --report` · E21 `tools/fill_gap.py`. Empat-empatnya disebut bersama: yang satu bikin kami kelihatan pintar, tiga lainnya bikin kami tidak boleh berbohong |
| "karenanya agen ini siap uang asli" | "yang lolos semua kontrol kami cuma **rem** (`jual_*`), dan itupun **belum lolos di paper pada budget kontrak**: pada 5 posisi/hari tidak ada satu arm pun yang mengalahkan control acaknya (F-D51). `promote-after` paper→real masih kosong - yang tertambat pada angka adalah empat kunci tertanggal, bukan keberanian kami" | `python -X utf8 tools/paper_book.py --per-day 5`, `tools/policy_test.py`, [[06-Results/14 - Buku Paper]], P30 · F-D51/F-D52 |
| "hasil uji prospectif kami menunjukkan…" (sebelum jamnya) | "kunci E9 dipasang 05:13:25Z (vonis 17:13:25Z) dan E12 08:04:56Z (vonis 20:04:56Z); sebelum jam itu halaman hasilnya **sengaja kosong**" | `tools/vol_ab.py --status`, `tools/hold_ab.py --status` — dan kekosongan itu yang membuktikan urutannya, bukan angka di dalamnya |
| "+188,3 bps/posisi dari buku paper" tanpa menyebut varian dampak **maupun budgetnya** | "net of ongkos 59 bps RT dan hampir nol dampak - karena `haircut()` kami membagi BNB dengan USD; kalau satuannya dibetulkan dan pool di bawah $1.000 dibuang, mean buku jadi **−87,8 bps**, bukan +75,9" | F-D46 (`tools/impact_audit.py`) **dan F-D51: pada peristiwa yang sama control-nya +165,7 @200/hari, -100,2 @24/hari, -26,7 @5/hari - di budget kontrak tidak ada arm yang menang**(`tools/paper_book.py --per-day 5`). Kode belum diubah karena E9/E12 terkunci pada definisi yang dicatat - dan itu justru alasan angkanya wajib disebut dengan varian, bukan dibuang |

Lihat juga: [[06-Results/01 - Claims and Limits]] · [[00-Overview/02 - Business Process]]

**Satu kalimat yang boleh dipakai kalau semua di atas dicabut.** *Kami membangun
agen yang menerbitkan keputusannya ke chain sebelum hasilnya ada, lalu memakai mekanisme itu untuk
membatalkan klaim kami sendiri empat kali dalam empat hari - dan masih menjalankan dua uji yang
sudah dikunci sebelum tenggat.* Itu bukan permintaan maaf; itu satu-satunya hal yang bisa dibuktikan
orang lain tanpa percaya kepada kami.
