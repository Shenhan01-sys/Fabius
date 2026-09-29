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
| "ada edge dua menit, jadi kami hampir bisa" | "bump **+192,7 → +202,6 bps** pada menit 2-5 lolos placebo - **pada deret harga spot BSC**. Di substrate tempat kami bisa mengirim order, hari ini sudah diuji dan **tidak ada**: pada 5 simbol venue yang harganya benar-benar bergerak di resolusi menit, @5 m mean **+15,2** melawan placebo **+10,7**, berpasangan 5m-vs-30m **+14,8 bps, p=0,50** (n=31 dari 33 sesudah P59; dengan cache pendek mean-nya −7,3 - sebut n-nya selalu); dan dari 41 simbol yang reachable, hanya **5** yang harganya hidup di resolusi menit (sisanya 96-99 % menit tanpa transaksi). Kami juga masuk pada umur kabar **61 d** (F-D54), jadi kecepatan bukan lagi alasannya" | E11 `tools/horizon_decay.py` · E26 `tools/perp_bump.py` · E20 `tools/perp_liveness.py` · F-D54 `tools/fast_lane.py --report` · F-D57 `tools/venue_bridge.py` |
| "karenanya agen ini siap uang asli" | "yang lolos semua kontrol kami cuma **rem** (`jual_*`); paper pada budget kontrak tidak mengalahkan control acaknya (F-D51); dan uji substrate (E20/E26, F-D56-58) menemukan bahwa **venue kami sebagian besar tidak punya harga yang bergerak** pada horison yang kami klaim. `promote-after` paper→real masih kosong" | `python -X utf8 tools/paper_book.py --per-day 5`, `python -X utf8 tools/perp_liveness.py`, `python -X utf8 tools/perp_bump.py`, [[06-Results/28 - Venue Kami Bukan Pasar]] · F-D51/F-D58 |
| "hasil uji prospectif kami menunjukkan…" (sebelum jamnya) | "kunci E9 dipasang 05:13:25Z (vonis 17:13:25Z) dan E12 08:04:56Z (vonis 20:04:56Z); sebelum jam itu halaman hasilnya **sengaja kosong**" | `tools/vol_ab.py --status`, `tools/hold_ab.py --status` — dan kekosongan itu yang membuktikan urutannya, bukan angka di dalamnya |
| "+188,3 bps/posisi dari buku paper" tanpa menyebut varian dampak **maupun budgetnya** | "net of ongkos 59 bps RT dan hampir nol dampak - karena `haircut()` kami membagi BNB dengan USD; kalau satuannya dibetulkan dan pool di bawah $1.000 dibuang, mean buku jadi **−87,8 bps**, bukan +75,9" | F-D46 (`tools/impact_audit.py`) **dan F-D51: pada peristiwa yang sama control-nya +165,7 @200/hari, -100,2 @24/hari, -26,7 @5/hari - di budget kontrak tidak ada arm yang menang**(`tools/paper_book.py --per-day 5`). Kode belum diubah karena E9/E12 terkunci pada definisi yang dicatat - dan itu justru alasan angkanya wajib disebut dengan varian, bukan dibuang |

Lihat juga: [[06-Results/01 - Claims and Limits]] · [[00-Overview/02 - Business Process]]

**Satu kalimat yang boleh dipakai kalau semua di atas dicabut.** *Kami membangun
agen yang menerbitkan keputusannya ke chain sebelum hasilnya ada, lalu memakai mekanisme itu untuk
membatalkan klaim kami sendiri empat kali dalam empat hari - dan masih menjalankan dua uji yang
sudah dikunci sebelum tenggat.* Itu bukan permintaan maaf; itu satu-satunya hal yang bisa dibuktikan
orang lain tanpa percaya kepada kami.
### Baris yang ditambahkan 29 Sep 14:4xZ setelah F-D59/F-D60

| Kalimat yang sekarang **dilarang** | Kenapa (alat + jam) | Kalimat yang boleh dipakai |
|---|---|---|
| "edge dua menit kami tinggal dieksekusi" / "kalau venue-nya lebih hidup, edge-nya kembali" | `tools/gate_bump.py` 14:36:08Z: di venue pembanding dengan 14 simbol HIDUP, efek @5 m **+2,0** (placebo −7,4) dan **+13,2** di kelas TIPIS (placebo +4,9); berpasangan 5m-vs-30m p=0,76 / p=0,44 - satu ordo di bawah E11 (+202,6) dan di bawah ongkos terukur kami (59 bps) | "kami menguji apakah bump yang kami ukur di deret spot bisa dipindahkan ke substrate tempat kami benar-benar bertransaksi. Di dua venue perp jawabnya tidak, dan efeknya tinggal satu ordo di bawah ongkos round-trip kami." |
| "buku beku itu sifat long-tail perp, jadi bukan salah venue kami" | `tools/gate_liveness.py` 14:31:24Z: pada 35 kontrak yang sama - Gate HIDUP 14 / MATI 0, Aster HIDUP 5 / MATI 14; 9 simbol hidup hanya di Gate, nol hanya di kami | "sebagian besar kebuntuan eksekusi kami adalah sifat venue yang kami pakai, dan kami bisa menunjuk buktinya - tapi memindah venue memperbaiki eksekusi, bukan memberi alasan masuk" |
| "kami sudah selesai mengukur sebabnya" | tiga alat, tiga sebab yang tersisa setelah yang lain dicabut: F-D54 (umur keputusan 61 d - bukan kecepatan), F-D60 (bukan hidup/tidaknya venue), E21 + F-D54 (`i` +245 bps dan `entry_px` di atas harga whale pada 16/25 - **titik masuk**) | "yang tersisa setelah kecepatan dan venue kami buang adalah selisih antara harga yang dilihat sinyal dan harga yang benar-benar bisa kami bayar; itu terukur, bukan diasumsikan" |

**Satu kalimat untuk juri, kalau cuma boleh satu:** *"Kami tidak punya edge yang bisa dieksekusi hari
ini - dan kami bisa menunjukkan pengukuran yang membunuh tiap penjelasan alternatif, di dua venue,
dengan n, jam, dan perintah yang mencetaknya."*


