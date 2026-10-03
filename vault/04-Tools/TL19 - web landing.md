---
tags: [perkakas, "TL19"]
---

# TL19 - web landing (FE tingkat 0)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `web/` (Next.js 16, React 19, three.js lewat @react-three/fiber + drei + postprocessing, motion) · data `tools/web_snapshot.py` ->
`web/public/data/snapshot.json` · brief `docs/design/landing.md`

**Ringkas:** landing page untuk pembeli/pelanggan sinyal, baik manusia maupun agen. Mengikuti FE Doctrine: halaman MEWAKILI prosesnya, tidak sekadar
menjelaskannya. Objek inti = blok kaca (satu blok = satu komitmen), dan agen Fabius = kristal komitmen 3D.

**Poin kunci:**
- Hero: kristal 3x3x3 bergerak (masuk = blok terbang lalu mengunci; berdenyut; tiap ~3,4 s satu blok aturan keluar dan chip-nya menampilkan kunci on-chain itu).
  Jumlah blok per warna = data snapshot (indigo = aturan terkunci, putih = sinyal SAH, bening = slot kosong).
- 01 satu sinyal: sumbu waktu dengan blok yang berjalan mengikuti scroll (tutup lilin -> putusan -> segel Merkle -> komit -> buka + SAH).
- 02 umpan bukti: kalender hari x bot dari ledger + vonis chain, hari bolong tampil retak; tabung F-D16 per bot.
- 03 buku slot: 10 slot, B1 identitas, B3 dengan cincin bayangan hari-hidup/60, rantai 7 kunci on-chain (tautan ke BscScan).
- 04 dua pintu: tingkat 0 terbuka (manusia + agen/MCP), tingkat 1 TERKUNCI dengan cincin syarat (uji maju dari data, telaah hukum 0, mulai 0).
- EN/ID; kanvas 3D berhenti me-render saat hero di luar layar.

**Yang ia TOLAK lakukan:** menampilkan klaim keuntungan atau angka kinerja yang belum bermakna; menjual tingkat 1; mengetik angka dengan tangan (semua dari snapshot).

**Cara menjalankan:** `cd web && npm install && npm run dev` lalu buka http://localhost:3000; data baru: `python -X utf8 tools/web_snapshot.py`.

**Revisi 3 Okt sore (builder: "3D cubenya terlalu cerah, turunin glownya"):** emisi inti 3,2 -> 1,15, blok terbukti 1,8 -> 0,75, lampu dalam 14 -> 5,5, lampu detak 22 -> 9, bloom 0,55 -> 0,22 (ambang 0,82 -> 0,92), pantulan kaca 1,7 -> 1,05, Lightformer turun sekitar 35 %, dan kaca kosong lebih ungu. ContactShadows dibuang: bidangnya ikut berputar/miring dan tampil sebagai pita abu-abu di belakang judul; diganti elips gradien radial di bawah kubus.

**Deploy Vercel:** import repo, **Root Directory = `web`**, tanpa env var (lihat `web/README.md`). Data diperbarui lewat `tools/web_snapshot.py` + push.

**Pelajaran 3 Okt (sebelum deploy):** dua pola `.gitignore` akar repo diam-diam menelan berkas FE. `data/` (cache harga) menelan `web/public/data/snapshot.json`, dan `lib/` (pustaka Foundry) menelan `web/src/lib/`. Build lokal lulus karena berkasnya ada di disk; build dari clone bersih GAGAL (`Can't resolve '@/lib/copy'`). Diperbaiki dengan `!web/public/data/` + `!web/src/lib/`; simulasi clone bersih -> `npm ci` -> `npm run build` lulus. Aturan: sebelum menyatakan siap deploy, build dari clone bersih, bukan dari folder kerja.

**HIDUP 3 Okt 13:15Z: https://fabius-one.vercel.app.** Project Vercel `fabius` dibuat lewat `vercel api` (POST `/v11/projects`): framework nextjs,
Root Directory `web`, tersambung repo GitHub `Shenhan01-sys/Fabius` (branch produksi `master`), perintah lewati-build `git diff --quiet HEAD^ HEAD -- .`
(commit bot ledger/universe yang tidak menyentuh `web/` tidak memicu build). Deploy pertama dipicu dari commit `4cb8b8ac` lewat POST `/v13/deployments`
(`gitSource`), `dpl_6c9NZRp8PjRLiBik2sqMbHAa1MfU`, landing 200.

**Aturan deploy (3 Okt):** JANGAN `vercel deploy` dari akar repo. CLI mengunggah folder kerja apa adanya, dan `.env`, `.agent.env`, `.committer.env`,
`.deployer.env` TIDAK ada di daftar abaikan bawaan Vercel, jadi kunci privat ikut terunggah ke build. Jalur yang benar: push ke GitHub; Vercel membangun
dari clone repo, yang hanya berisi berkas ter-track. Di Git Bash, `vercel api /v11/...` harus diawali `MSYS_NO_PATHCONV=1` (kalau tidak, path diubah
jadi path Windows: `Endpoint must start with /`).

**Belum:** snapshot otomatis, penampung daftar tunggu (P115). Server MCP (P114) hidup di deploy yang sama -> [[TL20 - server MCP]].

**Terkait:** [[TL14 - verify_signals]] · [[03-Data/D8 - Buku Slot Hidup]] · [[00-Overview/03 - Decisions]] F-D70/F-D72 · [[08-Backlog/06 - Epik Gerbang Sinyal]]
