---
tags: [inbox, "S-07-okt-deck"]
---

# Session 7 Okt 2026 (deck) - generator PPT dari markdown, 12 slide, gaya FE

**Bagian dari:** [[09-Inbox/00 - Hub Inbox]]
**Sumber:** keluaran perintah di bawah (dijalankan 7 Okt 2026 UTC di container cloud tanpa rahasia; RPC chain dan host deploy ditolak proxy egress). Hasilnya hidup di [[13-SubmmisionsDocs/00 - Hub Submission Deck]]; halaman ini = bahan mentah.
**Halaman permanen:** [[13-SubmmisionsDocs/00 - Hub Submission Deck]] (cara menjalankan, peta slide) · [[13-SubmmisionsDocs/99 - Design Style]] (gaya + token yang dibaca generator).

## 1. Yang terjadi, berurutan

1. Builder meminta skrip yang membuat PPT dengan **satu berkas md = satu slide** (12 slide), ditambah satu md terakhir berisi gaya desain (disesuaikan dengan FE Fabius). Tiap md memuat skrip visual yang imersif, penyampaian narasi, dan caption, dan harus terasa sangat meyakinkan supaya Fabius terlihat serius dan bernilai tinggi. Folder baru bernama `13-SubmmisionsDocs` di `vault/` (ejaan "Submmisions" dipertahankan persis seperti yang diketik builder), lalu push ke cabang baru yang namanya mewakili tugas.
2. Riset fakta: vault inti, `docs/design/*`, `web/src/app/globals.css`, `web/src/lib/copy.ts`, `web/public/data/snapshot.json`. Sub-agen memeriksa 13 klaim terhadap kode dan vault; koreksi yang diambil: SelectionAnchor = pilihan harian dan DeskAnchor = akar 5 menit yang hanya diterima selama siklus, MCP gratis baca-saja (yang berbayar mati), FAB bukan penjualan sinyal ([[00-Overview/03 - Decisions]] F-D98), jumlah agen yang memilih tidak disebut, dan kata *publisher* (di vault *builder* = pemilik proyek).
3. Cabang `claude/submission-deck-md2pptx` dari `origin/master` (`4178f61`). Generator `build/` (python-pptx; bentuk asli PowerPoint, bukan gambar), 12 layout, 12 md slide + `99 - Design Style`, dua tangkapan layar nyata dari build lokal `web/` pada master.
4. Builder menyela ("slidenya udh jadi semua?") lalu meminta PNG-nya; 12 PNG dan PPTX dikirim untuk ditinjau **sebelum** push. Sampai commit ini belum ada balasan builder atas PNG itu.
5. **Master maju di tengah sesi** (`4178f61` -> `1285302`): F-D130 / F-D131 (peninjau LLM: bot aktif 8/8, agent tetap mati 5/6) dan P166 (agent luar UJI 2573 milik builder lewat pintu agent). Dua kalimat deck jadi usang (§3); cabang di-fast-forward dan slide 6 dan 11 ditulis ulang.
6. Tes, validasi paket, render, gerbang vault (§2), commit dengan identitas builder tanpa trailer ([[00-Overview/03 - Decisions]] F-D22), `git push -u origin claude/submission-deck-md2pptx`. Tidak ada PR (belum diminta). `build/out/` tidak ikut git.

## 2. Bukti (perintah dan keluarannya)

| perintah | hasil |
|---|---|
| `python -X utf8 -m unittest discover -s vault/13-SubmmisionsDocs/build/tests -t vault/13-SubmmisionsDocs/build` | **59 tes OK** (dengan `DECK_RENDER=1` tanpa dilewati, ±42 s; tanpa itu 1 dilewati: render opt-in); juga bersih dengan `-W error::ResourceWarning` |
| `python -X utf8 vault/13-SubmmisionsDocs/build/build_deck.py --check` | "12 slide dibaca · angka per 7 Okt 2026 · 10:08 UTC (commit 22, terverifikasi 22, alarm 0)"; 7 guard ok |
| `python -X utf8 vault/13-SubmmisionsDocs/build/build_deck.py --render` | PPTX 12 slide (±430 KB) + PDF + 12 PNG; nol peringatan teks (menyusut / meluap) |
| `validate.py` dari skill pptx (`office/validate.py`) atas `build/out/Fabius-Submission-Deck.pptx` | `All validations PASSED!` |
| `python -X utf8 tools/peninjau_llm.py status` | bot: DIKALIBRASI, aktif ya (8/8); agent: KALIBRASI GAGAL, aktif TIDAK (5/6) |

**Angka yang dicetak deck** (semua `{{token}}` dari snapshot 10:08Z, tidak diketik): commit 22, terverifikasi 22, alarm 0, terlewat 0, hari diam 15, bot pada jam maju 6, lock 11, jeda komit 8,7-11,2 jam, slot 10, bot lolos F-D16 maju 0 dari 6, gerbang menolak 4 / tak terukur 1 / bayangan 1. Guard di front matter (`fd16_passed == 0`, `alarms == 0`, ...) menggagalkan build bila kalimat naratifnya berhenti benar.

**Pratinjau:** LibreOffice 24.2.7 + `pdftoppm`; font Inter dan Archivo terpasang, JetBrains Mono tidak (pengganti monospace). Belum dibuka di PowerPoint asli: yang terukur hanya validasi skema paket + render LibreOffice.

## 3. Yang ditemukan di jalan

- **Blok token di Design Style tidak terbaca** (judul bagian bernomor "9. Tokens" + kunci bersarang `tokens:`): deck memakai bawaan kode, bukan md. Diperbaiki (`mdparse` menormalkan judul, `load_tokens` memindai semua blok yaml) dan dikunci tes "mengubah token di Design Style mengubah deck".
- **Hitungan chip hero di tangkapan layar** ("4 rules locked") menghitung blok kubus, bukan lock (11): chip dan navigasi dipotong dari gambar (`crop`).
- **Halaman `/buy`, `/submit`, `/verify`** di build lokal menampilkan "Failed to fetch" (RPC diblokir proxy): tidak dipakai; hanya beranda desktop dan halaman bot mobile.
- **Teks:** pengukur teks sengaja konservatif (tanpa berkas font); peringatan menyusut (<88 %) memaksa beberapa kartu dipersingkat; judul tanpa `balance` meninggalkan satu kata yatim.
- **Tinjauan diff sendiri (audit, [[Conventions]]):** lima celah kecil di generator ditutup dan diberi tes: cap waktu berkas di properti PPTX tadinya beku di 7 Okt 12:00Z (tetap sama di build kapan pun), kini waktu build atau `SOURCE_DATE_EPOCH`; guard pada fakta yang bukan bilangan bulat kini galat yang jelas (bukan `TypeError`), `slide:` non-angka di front matter dilaporkan sebagai galat build, sisa PNG / PDF dari render sebelumnya dibuang (deck yang menyusut atau `--only` tidak mewarisi slide lama), dan `--only` yang salah atau kegagalan LibreOffice memberi pesan, bukan traceback. File yang dibuka tanpa `with` di tes juga dirapikan.
- **Peninjau LLM (slide 11):** teks awal "peninjau LLM gagal kalibrasi, mati" sudah tidak benar sesudah F-D131. Kriteria "2 dari 3 jalan" dipilih asisten sesi lain tanpa pilihan eksplisit builder, jadi deck tidak memakai "lulus kalibrasi" sebagai bukti; ia hanya menyebut yang kokoh: peninjau hanya bisa menahan atau menolak (`engine/peninjau.py::keputusan_bot` tidak punya keluaran yang memberi slot) dan versi untuk agen tetap mati.
- **Pintu agen (slide 6):** "belum ada pengajuan luar" tetap benar untuk pihak ketiga, tetapi agent uji milik builder (2573) sudah mendaftar, duduk di kursi uji, dan jawaban pertamanya diterima ([[07-Testing/01 - Test Commands]] #139); slide menyebut keduanya.
- **Sumber basi di tempat lain (tidak diubah, dicatat di hub):** `docs/agent-card.json`, bagian "Sekarang (3 Okt)" di `README.md`, "dua round-trip" di [[10-Submissions/01 - Claims Cheat Sheet]] baris 36 (rantai mencatat tiga), [[02-Contracts/02 - Deployed on 97]] belum memuat SelectionAnchor / DeskAnchor / FAB, LB5 / LB6 di [[08-Backlog/13 - Langkah Builder Tertunda]] belum mengikuti F-D131.

## 4. Batas yang dijaga

Tidak ada klaim untung, edge, "pertama / satu-satunya", trustless / zkML / TEE; semua uang = paper dan token tanpa nilai; sinyal waktu-nyata berbayar tetap GATED. Tes `test_slides_md.py` memindai semua slide + narasi untuk kalimat terlarang dari [[10-Submissions/01 - Claims Cheat Sheet]] dan [[06-Results/01 - Claims and Limits]]. Kalimat "sell it to humans and AI via x402 + MCP" di tagline adalah arah, bukan klaim penjualan; slide 8 dan 12 menyatakan statusnya (kasir testnet, belum ada pembeli luar, sinyal berbayar terkunci).

**Terkait:** [[13-SubmmisionsDocs/00 - Hub Submission Deck]] · [[13-SubmmisionsDocs/99 - Design Style]] · [[07-Testing/01 - Test Commands]] DK1 · [[08-Backlog/13 - Langkah Builder Tertunda]] LB15 · [[00-Overview/03 - Decisions]] F-D22
