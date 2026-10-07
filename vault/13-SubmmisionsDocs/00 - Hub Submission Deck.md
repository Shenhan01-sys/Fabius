---
tags: [submission, hub, deck]
---

# 13 - Submission Docs: deck PPT dari markdown

**Bagian dari:** [[Index]]
**Sumber:** `13-SubmmisionsDocs/` (12 md slide + 1 md gaya + `build/`) · `web/public/data/snapshot.json` · `docs/design/landing.md`
**Dibuka:** 7 Okt 2026 atas permintaan builder: *"script untuk generate ppt, 1 md file = 1 slide, ditambah 1 md untuk design style (sesuaikan FE Fabius), 12 slide, skrip visual + narasi yang imersif dan sangat menjual"*. Alur kerja: [[Conventions]] *Alur kerja pengembangan*.

**Ringkasan:** Folder ini adalah sumber deck submission Fabius. Satu berkas md = satu slide: tiap md memuat **skrip visual** (apa yang dilihat penonton: objek, ilustrasi, cahaya), **data di slide** (kalimat, caption, angka) yang dibaca generator, **narasi** (apa yang diucapkan), dan **tabel cek klaim** (tiap kalimat kuat ditautkan ke bukti di vault/repo). Satu md terakhir, `99 - Design Style`, memegang gaya (warna, font, ukuran, aturan suara) dan blok `tokens` yang BENAR-BENAR dibaca generator. `build/build_deck.py` merakit semuanya menjadi `.pptx` dengan bentuk asli PowerPoint (bukan gambar): ilustrasi isometrik blok kaca digambar dari poligon yang bisa dipilih dan diubah.

## Cara menjalankan

```bash
pip install -r vault/13-SubmmisionsDocs/build/requirements.txt          # python-pptx, PyYAML, Pillow
python -X utf8 tools/web_snapshot.py                                    # (opsional) cetak ulang angka hidup tepat sebelum submit
python -X utf8 vault/13-SubmmisionsDocs/build/build_deck.py             # -> build/out/Fabius-Submission-Deck.pptx
python -X utf8 vault/13-SubmmisionsDocs/build/build_deck.py --check     # validasi md + guard angka, tanpa menulis
python -X utf8 vault/13-SubmmisionsDocs/build/build_deck.py --render    # + PDF dan PNG per slide (butuh LibreOffice + pdftoppm)
python -X utf8 vault/13-SubmmisionsDocs/build/build_deck.py --fonts safe  # Arial/Courier New bila Archivo/Inter/JetBrains Mono belum terpasang
python -X utf8 -m unittest discover -s vault/13-SubmmisionsDocs/build/tests -t vault/13-SubmmisionsDocs/build
```

`build/out/` tidak ikut git (aturan `.gitignore`: `out/`). Font merek: Archivo (varian variabel di `Video-Workspace/public/fonts/Archivo-VF.ttf`), Inter dan JetBrains Mono (Google Fonts, OFL); tanpa font itu PowerPoint memakai pengganti sans/mono, tata letak tetap aman.

## Peta slide

| # | berkas | layout | tema | pesan satu kalimat |
|---|---|---|---|---|
| 1 | [[01 - Cover]] | `cover` | malam | Sinyal disegel sebelum hasilnya ada; kristal kaca tersegel + tagline + chip status jujur |
| 2 | [[02 - The Problem]] | `claims_gap` | lavender | Semua rekam jejak ditulis sesudah kejadian; pembeli tak bisa memeriksa hapus / ubah / tulis mundur |
| 3 | [[03 - The Gap]] | `trust_gap` | lavender | Agen sudah bisa saling membayar; uang bergerak, bukti tidak (jembatan dengan satu bentang hilang) |
| 4 | [[04 - The Idea]] | `seal` | malam | Komit dulu, buktikan kemudian: aturan dikunci, sinyal disegel, waktu blok jadi alibi |
| 5 | [[05 - The Proof Engine]] | `rail` | malam | Lima stasiun publik dari bar tutup sampai diperiksa ulang; satu perintah tanpa kunci dan gas |
| 6 | [[06 - The Open Platform]] | `doors` | malam | Empat pintu (rule, feed, agent, code) lewat gerbang publik yang sama; belum ada pengajuan luar |
| 7 | [[07 - The AI Desk]] | `desk` | malam | Agen analis menilai, rumus tetap memilih, kode menghitung, akar siklus 5 menit disegel di DeskAnchor |
| 8 | [[08 - The Market]] | `checkout` | malam | Bayar per panggilan lewat x402 (testnet, token tanpa nilai); arus penerbit-Fabius-pembeli; status LIVE / BUILT / GATED |
| 9 | [[09 - Live Product]] | `showcase` | malam | Bukan mockup: tangkapan layar nyata + empat angka yang dicetak mesin |
| 10 | [[10 - On-Chain]] | `stack` | malam | Lima kontrak milik Fabius (SignalAnchor = alur utama), dua revert di kode, rel standar yang bukan milik kami |
| 11 | [[11 - Built to Be Doubted]] | `honesty` | malam | 0 dari 6 bot lolos uji maju; yang dibuktikan chain vs tidak; standar yang sama dipakai ke diri sendiri |
| 12 | [[12 - Roadmap and Close]] | `roadmap` | malam | Live / Built / Gated, penutup, dan tiga cara memeriksa sendiri |
| - | [[99 - Design Style]] | (gaya) | - | Gaya FE untuk deck + blok `tokens` yang dibaca generator |

Cerita disampaikan lewat cahaya: slide 2-3 (dunia klaim) terang dan datar, slide 4 membalik ke malam dan semua objek menyala; sampul dan penutup sama-sama malam.

## Cara kerja generator (satu paragraf)

`mdparse` membaca front matter + bagian `##` + blok ```yaml `## Slide`; `facts` mengganti `{{kunci}}` dengan angka dari `web/public/data/snapshot.json` dan mengevaluasi `guards` (build GAGAL bila kalimat naratif tidak lagi benar, mis. "0 dari 6 bot lolos" padahal satu bot sudah lolos); `layouts` (12 fungsi) menggambar dengan primitif `draw` + `iso`; catatan pembicara berisi skrip visual + narasi + sumber + waktu snapshot. Pengukur teks sengaja konservatif (tanpa berkas font, hasilnya sama di semua mesin) dan memberi peringatan bila teks menyusut atau hampir meluap.

## Alur kerja pengembangan (rekap)

1. **Rencana.** Cabang baru `claude/submission-deck-md2pptx` dari `origin/master` terbaru (master sudah memuat kerja sesi 7 Okt, jadi status LIVE / BUILT / GATED dibaca dari sana). Master maju di tengah sesi (F-D130 dan F-D131 untuk peninjau LLM, P166 agent uji): cabang digeser maju (fast-forward) ke `1285302` dan slide 6 dan 11 ditulis ulang agar cocok dengan keadaan baru. Keputusan desain: python-pptx (satu bahasa dengan perkakas repo), bentuk asli bukan gambar, fakta dari snapshot, gaya dari md.
2. **Eksekusi.** Riset fakta: seluruh vault + `docs/design/*` + `web/src/lib/copy.ts`; verifikasi 13 klaim oleh sub-agen terhadap kode dan vault (hasil: koreksi desk, MCP, SelectionAnchor, sifat "penjualan", detail di bagian *Temuan audit klaim*); tangkapan layar UI baru dari build lokal master; generator, 12 layout, 12 md + Design Style.
3. **Tes unit + ujung-ke-ujung.** `build/tests/` (`unittest`): penanda teks, pengukur, pembaca md, fakta + guard, urutan XML DrawingML (efek setelah garis setelah isi), build penuh 12 slide dari md (judul asli per slide, catatan, teks tidak keluar slide, font hanya dari token, teks alternatif gambar, field nomor slide, transisi), varian (`--fonts safe`, guard gagal, layout tak dikenal, nomor bolong, token fakta tak dikenal, gambar hilang, **mengubah token di Design Style benar-benar mengubah deck**), dan audit isi (sumber dan wikilink ada, path yang dikutip ada, alamat kontrak ada di `deployments/97.json`, nama error ada di `SignalAnchor.sol`, kalimat terlarang oleh Claims Cheat Sheet tidak muncul). Hasil dan perintahnya di [[07-Testing/01 - Test Commands]] baris DK1.
4. **Audit.** Validasi paket PPTX (`validate.py` skill pptx: skema, relasi, tipe isi), render LibreOffice -> PNG dan pemeriksaan visual tiap slide, gerbang vault (`sync_vault`, `check_links`, `hub_shape`, `check_tool_citations`), `prepush_check`. Tes menemukan satu cacat nyata sebelum kirim: blok `tokens` di Design Style tadinya tidak terbaca (judul bagian bernomor); sudah diperbaiki dan dikunci dengan tes.
5. **Rekap.** Halaman ini, [[09-Inbox/Session-2026-10-07-deck]], baris DK1 di Test Commands, baris LB15 di [[08-Backlog/13 - Langkah Builder Tertunda]], baris folder di [[Index]] dan [[Conventions]], tautan dari [[10-Submissions/00 - Hub Submissions]].
6. **Kirim.** Commit tanpa atribusi AI dan memakai identitas builder (F-D22), `prepush_check`, push ke cabang baru. Tidak ada PR (belum diminta).

## Temuan audit klaim (basi di sumber lain; TIDAK dipakai deck)

Sub-agen pemeriksa menemukan beberapa kalimat yang sudah usang di tempat lain. Deck memakai versi yang benar; halaman sumbernya belum diubah (di luar lingkup tugas ini), jadi dicatat di sini supaya tidak terlupa:

- `docs/agent-card.json` masih menyebut 9 alat MCP dan endpoint localhost; server MCP kini punya 19 alat baca-saja.
- [[08-Backlog/13 - Langkah Builder Tertunda]] baris LB5 dan LB6 masih mencatat peninjau LLM "GAGAL, tidak aktif" (bot 2 dari 8, agent 0 dari 6). Sesudah F-D131 (7 Okt sore) peninjau bot AKTIF (8 dari 8) dan peninjau agent tetap mati (5 dari 6); keadaan hidup dibaca dengan `python -X utf8 tools/peninjau_llm.py status`.
- Aktifnya peninjau bot memakai kriteria "2 dari 3 jalan" yang dipilih asisten sesi lain tanpa pilihan eksplisit builder (F-D131: "bisa dibalik builder"). Karena itu deck TIDAK memakai "peninjau lulus kalibrasi" sebagai bukti; ia hanya memakai bagian yang kokoh: peninjau hanya bisa menahan atau menolak (tidak pernah memberi slot) dan versi untuk agen tetap mati (slide 11).
- [[04-Tools/TL40 - peninjau LLM]] baris 54 ("belum ada ... agent luar sungguhan di kursi uji") mendahului P166: satu agent luar UJI milik builder (ERC-8004 2573) sudah di kursi uji sejak 7 Okt sore ([[07-Testing/01 - Test Commands]] #139). Slide 6 menyebutnya apa adanya dan tetap mengatakan belum ada pihak ketiga.
- `README.md` bagian "Sekarang (3 Okt)" masih menyebut dua bot; kini enam bot punya ledger maju.
- [[10-Submissions/01 - Claims Cheat Sheet]] baris 36 menyebut "dua round-trip"; `decisions/execution-trail.jsonl` dan [[Quick-Reference]] mencatat tiga.
- [[02-Contracts/02 - Deployed on 97]] belum memuat SelectionAnchor, DeskAnchor, dan FAB (alamatnya ada di [[Quick-Reference]] dan `deployments/97.json`).
- Daftar agen di `/desk` (FE) masih menampilkan tiga agen; manifes menyebut lima agen rumah dengan identitas ERC-8004. Deck sengaja tidak menyebut jumlah agen yang memilih.
- Meja AI mengunci rumus dengan hash yang diterbitkan di repo dan `/desk` (`params_v2_sha`), bukan lewat LockRegistry; deck memakai kata "fixed, published formula", bukan "locked on-chain".

## Bagian

- [[01 - Cover]] — sampul: kristal kaca tersegel, tagline, chip status, detak chain
- [[02 - The Problem]] — rekam jejak ditulis sesudah kejadian; tiga lubang yang tak terlihat pembeli
- [[03 - The Gap]] — jembatan dengan bentang hilang: uang bergerak, bukti tidak
- [[04 - The Idea]] — komit dulu, buktikan kemudian; bukti waktu, bukan bukti untung
- [[05 - The Proof Engine]] — lima stasiun dari bar tutup sampai diperiksa ulang
- [[06 - The Open Platform]] — empat pintu masuk, satu koridor gerbang yang sama
- [[07 - The AI Desk]] — meja agen: menilai, memilih lewat rumus, menyegel tiap 5 menit
- [[08 - The Market]] — kasir x402 per panggilan dan arus bisnis, dengan status jujur
- [[09 - Live Product]] — tangkapan layar nyata dan angka yang dicetak mesin
- [[10 - On-Chain]] — lima kontrak milik Fabius dan apa yang bukan milik kami
- [[11 - Built to Be Doubted]] — 0 dari 6, yang dibuktikan vs tidak, standar pada diri sendiri
- [[12 - Roadmap and Close]] — live / built / gated dan penutup
- [[99 - Design Style]] — gaya FE untuk deck + token yang dibaca generator

<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->
```dataview
LIST FROM #deck SORT file.name ASC
```

## Terkait

- [[10-Submissions/00 - Hub Submissions]] · [[10-Submissions/01 - Claims Cheat Sheet]] · [[Quick-Reference]] · [[Index]] · [[Conventions]]
