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
| P8 | **Bukti clone bersih** — `git clone` ke direktori kosong, lalu jalankan baris 1–6 registry [[07-Testing/01 - Test Commands]] | ✅ **selesai 27 Sep: 4/4**, dan tesnya menemukan dua klaim yang tadinya palsu | lihat [[07-Testing/T6 - Clean Clone Evidence]] — `--verify` gagal di clone karena alamat agen cuma ada di `.agent.env` (di-gitignore); diperbaiki lewat `deployments/97.json` + cek roster ke kontrak |

## Terkait

- [[00-Overview/06 - Roadmap]] · [[Index]]

## Bagian


<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->

```dataview
LIST FROM #backlog SORT file.name ASC
```
```dataview
LIST FROM #backlog SORT file.name ASC
```
```dataview
LIST FROM #backlog SORT file.name ASC
```
```dataview
LIST FROM #backlog SORT file.name ASC
```
