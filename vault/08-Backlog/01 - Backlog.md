---
tags: [backlog, hub]
---

# Backlog

**Sumber:** keluaran perintah di `07-Testing/`, bukan perasaan. Tenggat: **30 Sep 23:59 WIB**.

| # | pekerjaan | status | yang menahan / bukti selesai |
|---|---|---|---|
| P1 | **Eksekusi nyata pertama di 97** (deploy `DemoAsset`+`DemoPair`+`ExecutionVault`, buka & tutup 1 posisi) | ✅ **selesai 27 Sep** — 2 round-trip nyata, realized −59 bps per putaran | Guard menolak kemarin karena memakai **plafon 1 gwei**, sementara testnet live **0,10 gwei**: jalur penuh = 0,0018 tBNB vs saldo agen 0,007884 → **cukup** (ukur ulang: `python -X utf8 _research/read_balances.py`). Pilih salah satu sadar: top-up 0,03 dari tower (0,214667 tersedia) supaya tidak bergantung harga gas, ATAU turunkan plafon guard + catat risikonya. Lalu `python -X utf8 -u tools/exec_deploy.py`. Selesai = ada tx `status=1` + `openPositionOf` terbaca |
| P2 | **Host gateway x402** supaya URL kartu agen bukan `127.0.0.1` | ⬜ | `agent-card.json` menunjuk URL tetap; kartu tidak lagi ditulis "LOCAL ONLY" |
| P3 | **FE dua pintu** (Vercel, oleh builder) — orang awam lihat rekaman; agen baca kartu + bayar | ⬜ | halaman + data dari chain; `--verify` dijalankan orang lain dari browser |
| P4 | `seats.py` — 5 kursi + rotasi memakai `seat_eligible` | ⬜ | aturannya sudah tertulis di [[01-Agent/01 - Asset Classes and Seats]] §3, belum jadi kode |
| P5 | Uji A (prospektif, tanpa lookahead) pada horison 24/48 jam | ⏳ butuh waktu, bukan kerja | entri setelah 26 Sep 08:01Z dinilai 27–28 Sep |
| P6 | Investigasi 2 snapshot universe yang sha-nya tidak bisa dihitung ulang | ⬜ 2 hipotesis sudah digugurkan | [[06-Results/03 - Not Yet Proven]] #21 |
| P6b | Rantai 6 entri anchor yang tidak punya baris sumber di repo (termasuk 1 `Enter`) | ⬜ baru terlihat 27 Sep | `python -X utf8 tools/verdict_counts.py` vs `python -X utf8 tools/anchor.py --verify`; selesai = kedua angka terjelaskan baris per baris |
| P7 | Putuskan: 30 hari jadi fitur (butuh dana & waktu) atau tetap hipotesis terbuka | ⬜ keputusan builder | kalimat publik sudah dikunci di [[10-Submissions/01 - Claims Cheat Sheet]] |
| P9 | Segarkan `docs/decisions/direction-latest.json` **otomatis** setiap siklus (bukan hanya saat `x8004_register.py --card`), plus pemeriksaan di CI bahwa tanggal isi <= umur siklus | ⬜ ketahuan 27 Sep: kartu menunjuk keputusan terbaru, isinya masih 25 Sep | selesai = ada baris di `01 - Test Commands` yang membuktikannya dari run, bukan dari klaim |
| P8 | **Bukti clone bersih** — `git clone` ke direktori kosong, lalu jalankan baris 1–6 registry [[07-Testing/01 - Test Commands]] | ✅ **selesai 27 Sep: 4/4**, dan tesnya menemukan dua klaim yang tadinya palsu | lihat [[07-Testing/T6 - Clean Clone Evidence]] — `--verify` gagal di clone karena alamat agen cuma ada di `.agent.env` (di-gitignore); diperbaiki lewat `deployments/97.json` + cek roster ke kontrak |
| P10 | **Satukan model ongkos** — 59 bps terukur dipakai di semua jalur uji, bukan 20 bps warisan; hitung ulang deret ledger | ⬜ **naik ke urutan 1** sejak 28 Sep, alasannya di [[TradingKnowledge/07-Peta-Fabius/GAP5 - Urutan Kerja dan Bayarnya]] | `tools/backtest.py` + `tools/ledger.py` memakai satu konstanta; [[06-Results/04 - Negative Results]] mencatat hasil hitung ulang (satu "MENANG +1,5 bps" jadi ≈ −37,5 bps kalau ongkos terukur dipakai); klaim yang mengikutinya ikut dikoreksi di `05 - Corrections` |
| P11 | **Perbaiki mekanika `tools/maker_ledger.py`** sebelum satu angka whale pun dikutip | ⬜ rem sehat masih menyala (median `|net|` 4.558 bps = distribusi mustahil) | satuan harga/USD untuk token berumur menit, arti `c` (`is_open_or_close`) ditetapkan dari baris mentah, MTM pesimistis untuk token yang hilang; selesai = blok "REM SEHAT" di [[TradingKnowledge/Fakta Terukur]] §H lolos dan `decisions/maker-scores-*.json` bisa dibuktikan ulang |
| P12 | **Uji ketujuh ambang veto terhadap hasil** (`tools/veto_study.py`, belum ditulis) | ⬜ | rancangan + syaratnya di [[TradingKnowledge/07-Peta-Fabius/GAP2 - Uji Setiap Veto Terhadap Hasil]]; selesai = tujuh baris keputusan (dipertahankan / dicabut / belum teruji) di [[06-Results/02 - Thresholds]] |
| P13 | **Mulai rekam funding + OI per jam** supaya uji carry mungkin suatu saat | ⬜ dibayar kalender, bukan jam-proses | satu berkas rekaman baru di `universe/` + manifest umur; yang boleh dilaporkan: "jalurnya hidup", **bukan** hasil |
| P14 | **Spesifikasi tunggal** untuk swing/zona/gap (satu definisi, satu implementasi) | ⬜ | tanpa ini tiap uji `S*`/`I*` mengukur hal berbeda; tempat hasilnya: satu catatan di `Concepts/` + fungsi yang dipakai semua alat |
| P15 | **Aliran ⑦ sebagai gerbang ⑧ turun-saja** (`SEARAH` / `KONTRA` / `TAK ADA DATA`) | ⬜ menahan diri pada P11 | dicatat per kejadian di `ledger.py`, dievaluasi di `winlog.py`; **tidak pernah** menaikkan keyakinan ([[Concepts/One-Way Gate]]) |

## Terkait

- [[00-Overview/06 - Roadmap]] · [[Index]] · urutan P10–P15 ditentukan di
  [[TradingKnowledge/07-Peta-Fabius/GAP5 - Urutan Kerja dan Bayarnya]]

## Bagian


<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->
```dataview
LIST FROM #backlog SORT file.name ASC
```
