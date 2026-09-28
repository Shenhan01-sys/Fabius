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
| P10 | **Satukan model ongkos** ✅ 28 Sep — 59 bps terukur dipakai di semua jalur uji, bukan 20 bps warisan; hitung ulang deret ledger | ✅ **selesai 28 Sep** — `tools/costs.py` + `vault/scripts/wire_costs.py` (6 jalur uji) + recompute di `06-Results/04` §5b; alasannya di [[TradingKnowledge/07-Peta-Fabius/GAP5 - Urutan Kerja dan Bayarnya]] | `tools/backtest.py` + `tools/ledger.py` memakai satu konstanta; [[06-Results/04 - Negative Results]] mencatat hasil hitung ulang (satu "MENANG +1,5 bps" jadi ≈ −37,5 bps kalau ongkos terukur dipakai); klaim yang mengikutinya ikut dikoreksi di `05 - Corrections` |
| P11 | **Perbaiki mekanika `tools/maker_ledger.py`** sebelum satu angka whale pun dikutip | 🟡 **mekanika beres 28 Sep; hipotesis kohor juga sudah diuji — yang memblokir sekarang bukan alatnya lagi.** Mekanika: `P(c=1\|b=1)=0,621` vs `P(c=1\|b=0)=0,567` → lot dibangun dari **sisi**, `c` metadata (6.704 baris terpakai); **0** lot bersatuan mustahil; MTM basi dipisah; 53 kejadian dobel dibuang. Hipotesis: `tools/flow_cluster_test.py` → **K=1 39,5 %** posisi positif vs **K≥2 39,3 %** vs K≥5 50,0 % (n=24, p=0,58) = **0 lolos BH**, cuaca 30,8 % | **Tapi angka itu belum boleh dipakai menutup pertanyaan**: **80,6 %** kandidat (3.191/3.958) tidak punya harga keluar — yang terbuang itulah yang kemungkinan mati. Sisa P11 = **P17**, lalu uji ulang. Rincian [[06-Results/09 - Whale Cluster Test]] + [[TradingKnowledge/Fakta Terukur]] §F/§H |
| P17 | **Perekam harga keluar (watchlist)** — token yang tercatat belinya tetap ditarik `px`-nya sampai 24 jam walaupun keluar daftar panas | ⬜ **ini alasan Fabius belum bisa "tahu kapan dia boleh bicara"**: 4 dari 5 kejadian buta di sisi keluar, jadi setiap persentase "whale untung/rugi" yang kami cetak adalah statistik di antara pemenang | satu berkas `universe/*` baru + satu langkah di workflow perekam yang sudah ada (tanpa kunci, tanpa dana). Selesai = `flow_cluster_test` jalan lagi dengan sensor < 20 % dan perbandingan K=1 vs K≥2 pada sampel yang tidak dipilih oleh nasib |
| P18 | **Presisi harga rekaman** — simpan harga persis seperti dikirim feed | ⬜ **21,6 %** kejadian punya gross **persis 0,0 bps** ("harga diam"): edge yang kita cari (±1–4 bps sebelum ongkos) berada DI BAWAH noise floor data kami sendiri — tabel median = −ongkos adalah batas alat, bukan hasil pasar | telusuri dulu: pembulatan terjadi di feed GMGN atau di penyimpanan kita (`universe/record_wallet_flow.py`); kalau di feed, pilih jalur harga lain (Aster/GeckoTerminal per token) dan sebut di §A |
| P12 | **Uji ketujuh ambang veto terhadap hasil** (`tools/veto_study.py`, belum ditulis) | ⬜ **dan jangan mulai dari nol: perbandingannya sudah pernah dihitung.** `tools/screen_universe.py` → `tools/out/screen_report.json` (765 pasangan forward, 545 token) membandingkan kohort lolos vs ditolak: **lolos** n=52 mean **+148,0** / median **+35,9** vs **ditolak** n=713 mean **+353,7** / median **−44,4** — arah yang tidak mendukung nilai veto kita. Report-nya sendiri memakai `RT_COST_BPS = 20` (bukan 59 terukur), dan `n` per alasan **tumpang tindih** (704+318+105+91+55+17+4 = 1.294 > 713) | rancangan + syaratnya di [[TradingKnowledge/07-Peta-Fabius/GAP2 - Uji Setiap Veto Terhadap Hasil]]; selesai = tujuh baris keputusan (dipertahankan / dicabut / belum teruji) di [[06-Results/02 - Thresholds]], **dengan ongkos 59 bps dan median + bootstrap**, bukan mean report lama |
| P13 | **Sedot mundur funding + OI, lalu uji carry** (berubah bentuk 28 Sep: bukan lagi "tunggu kalender") | ✅ **selesai 28 Sep** — `universe/record_funding_history.py` menarik **5.963 baris** (OKX 97,7 hari · Bybit 66,3 · OI Binance 20,8), `tools/carry_study.py` mengujinya | hasilnya di [[06-Results/08 - Carry Study]]: veto funding kena **0 dari 2.963** settlement, **0 dari 12 uji** arah 24 jam lolos BH, carry 1,3–2,2 bps/hari (= 27–45 hari untuk satu round-trip 59 bps). Artefak `decisions/carry-study-*.json` + `universe/funding-history-manifest.txt` |
| P16 | **Putuskan nasib veto funding** — terukur tidak pernah menyala di enam basis besar | ✅ **diputuskan 28 Sep = F-D26**: ambangnya TETAP, perannya diganti jadi **pemutus rezim**, bukan gerbang keamanan dan bukan sinyal | Alasannya angka, bukan selera: 0/2.963 settlement, maksimum 0,0256 %/8 jam, 0/12 uji arah lolos BH, dan kandidat kita (memecoin) tidak punya funding sama sekali. Menurunkan ambang supaya "pernah menyala" = memilih angka dari noise. Dampak dokumen: 8 tempat di `TradingKnowledge` + komentar `tools/direction.py` kini berbunyi pemutus rezim (`vault/scripts/relabel_funding_gate.py`). Yang belum dijawab: ambang universe lain (P12) |
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
