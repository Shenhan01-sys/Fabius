---
title: TL40 - peninjau LLM (agent pemilik Fabius)
tags: [tools, P168, peninjau, llm, pengajuan, agent-luar]
---

# TL40 - peninjau LLM "agent pemilik Fabius" (P168a bot + P168b agent)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `engine/peninjau.py` (logika murni, stdlib) · `tools/peninjau_llm.py` (panggilan xkiro, putaran gerbang, kait kursi, tarikan GitHub, CLI kalibrasi) · `tools/peninjau_kasus.py` (pembangkit set kalibrasi) ·
`engine/kalibrasi_peninjau/` (8 kasus bot + 6 kasus agent) · `engine/tests/test_peninjau.py` · cabang `tools/analis.py::call_model` (`EFFORT_BAWAAN`) · kait `tools/meja2.py::kursi_evaluasi` (`tahan`) ·
`engine/cli.py::_book_epoch` · `web/src/components/submit/OwnerReview.tsx`. Spesifikasi mengikat: [[08-Backlog/12 - Epik Pengajuan Terbuka dan Peninjau LLM]] §2, §5, §6 (F-D122, F-D125).
**Peta saudara:** [[04-Tools/TL37 - jalur pengajuan bot]] (tahap 1 bot) · [[04-Tools/TL38 - agent luar di meja (pull)]] (tahap 1 agent, kursi) · [[04-Tools/TL39 - aturan deklaratif (rule)]] (jenis `rule`).

**Ringkasan:** TAHAP 2 sesudah tahap teknis lolos. Model xkiro `z-ai/glm-5.3`, effort BAWAAN (`reasoning_effort` dihilangkan), brief bot / agent disalin PERSIS dari epik 12 (sha dikunci tes),
keluaran satu JSON berskema ketat. Peninjau HANYA MEMBATASI: gagal teknis tidak dibalik, LANJUT bukan slot, LLM mati / skema gagal = TAHAN. **Keadaan 7 Okt: BELUM DIKALIBRASI = TIDAK DI JALUR**
(`python -X utf8 tools/peninjau_llm.py status`): gerbang tidak memanggil model dan tidak menahan apa pun sampai rekaman kalibrasi model sungguhan lulus.

**Poin kunci:**
- **Brief + skema = teks persis vault.** `BRIEF_BOT` sha `0xb72e1e77…ed331`, `BRIEF_AGENT` sha `0xe66fb05a…02702` (UTF-8, isi blok tanpa pagar); skema §5.3 dikirim apa adanya bersama masukan (sha `0x2d064b19…9b03`).
  `BriefTests` membandingkan kode dengan blok di epik 12 byte-per-byte. Mengubah brief = sha baru = kalibrasi lama tidak berlaku (kunci jalur memeriksa `brief_sha`).
- **Masukan:** bagian TEPERCAYA (buatan bot teknis kami: `stage1`, `gates.G1..K5`, `attribution` = paparan + korelasi + beta vs BTC dari target mesin, `fabius_bots`, `book`) + bagian TAK TEPERCAYA
  `{"submission": formulir tanpa kontak}` (agent: kartu + sampel 24 jawaban) di dalam `<submission>...</submission>`; `<` `>` `&` di-escape `<` sehingga pembungkus tidak bisa ditutup dari dalam.
  `evidence_key` = jalur bertitik ke objek itu (`gates.G5.value`, `submission.answers.0.reason`).
- **Skema ketat** (`cek_skema`): kunci tepat (tanpa tambahan / kekurangan / ganda), tipe + rentang, kosakata tag (agent menambah HERDING, BOILERPLATE, HALLUCINATION, OVERCONFIDENCE, INSTABILITY; MANIPULATION sudah ada),
  severity, panjang teks, >= 3 keberatan kecuali `no_objection_reason`. Satu pagar ```` ```json ```` di sekeliling objek ditoleransi dan dicatat; teks lain di luar objek = gagal.
- **Paksaan mesin sesudah diurai (hanya LANJUT -> TAHAN, dicatat di `hasil.paksa`):** `injection_findings` tidak kosong; pemindai pola instruksi mesin (`pindai_injeksi`, lapis kedua yang bisa diakali, hanya menahan);
  `data_gaps` tidak kosong (aturan brief); keberatan `blocking` (definisi LANJUT); `evidence_key` yang tidak ada di masukan (angka karangan). Vonis model asli tetap tercatat (`vonis_model`).
- **Hanya membatasi:** `keputusan_bot` tidak punya medan slot; gagal tahap 1 = vonis tahap 1 apa pun jawaban model; peninjau aktif + laporan belum ada / TAHAN / TOLAK / tidak lolos periksa ulang = bot BUKAN
  penantang epoch buku (`tahan_bot`, dicetak di `_book_epoch`). Jam maju bayangan tetap berjalan (bukti murah, deterministik) - **USULAN implementasi**: titik tahan = penantang slot + status publik, bukan jam maju.
- **Gagal = TAHAN:** galat panggilan apa pun (HTTP 402 saldo, 429, batas waktu 600 s, jaringan, kunci tidak ada) -> rekaman `gagal_panggilan`; dicoba lagi maks 3 percobaan, lalu tetap TAHAN. Pesan galat dibersihkan dari kunci.
  Batas biaya: <= 30 panggilan per hari UTC (`PARAMS.maks_panggilan_hari`).
- **Kunci jalur** (`status_kalibrasi`): aktif hanya bila rekaman TERBARU `ledger/peninjau/kalibrasi/*-<jenis>.json` untuk brief + skema + model + `PARAMS` + set kasus yang sama lulus saat DINILAI ULANG
  dari jawaban mentahnya; bendera "lulus" yang tertulis tidak dipercaya; rekaman sebagian / < 3 jalan / gagal tidak membuka jalur. Bot dan agent dikunci terpisah.
- **P168b agent:** `tahap1_agent` atas N = 288 siklus PERTAMA kursi uji (identitas + tanda tangan, % sah, keyakinan per ember vs hasil buku agent itu ke siklus berikutnya, kesamaan bot dengan konsensus dan
  konsensus siklus sebelumnya, korelasi skor, keragaman teks, keyakinan / eksposur 100, kontrafaktual bot teratas dengan vs tanpa agent, sampel 24 jawaban + fitur yang dibaca). Latensi TIDAK terekam di
  rekaman meja (dinyatakan di masukan). Kait `kursi_evaluasi(tahan=...)`: hanya MENAHAN calon yang sudah memenuhi aturan numerik F-D113 (peristiwa `promotion held` ikut rekaman `kursi` yang dikomit);
  agent rumah tidak ditinjau; `PARAMS_KURSI` tidak berubah.
- **Jejak publik:** rekaman (sha brief, sha masukan, sha prompt, jawaban mentah + sha, vonis, paksaan, meta usage / finish_reason) di volume gerbang `<data>/peninjau/<jenis>/<kunci>.json`; `GET /bots/analysis[/<sha>]`,
  `GET /desk/external/review[/<kunci>]`; tinjauan harian GitHub (`bot-review.yml` -> `tinjau_pengajuan.py` -> `peninjau_llm.tarik`) memeriksa ulang (`periksa_rekaman`: sha + mengurai ulang jawaban mentah ->
  vonis sama; bot: tahap 1 di masukan = laporan publik di repo) lalu menulis `ledger/pengajuan/analisis/<jenis>/<kunci>.json`. Jenis `code` dan laporan agent yang jendelanya belum lewat penundaan publik
  meja (24 jam) keluar sebagai RINGKASAN tanpa teks bebas model. `/submit` menampilkan kartu (`owner_review`) sebagai teks biasa.

**Detail - cara memakai:**
- Status kunci jalur (tanpa kunci API): `python -X utf8 tools/peninjau_llm.py status`.
- Uji pipa tanpa biaya (model palsu, tidak ditulis ke ledger): `python -X utf8 tools/peninjau_llm.py kalibrasi --jenis bot --palsu`.
- **Kalibrasi sungguhan (builder, berbiaya xkiro; 8 x 3 + 6 x 3 = 42 panggilan):** `railway run --service fabius-x402 python -X utf8 tools/peninjau_llm.py kalibrasi --jenis bot` lalu `--jenis agent`.
  Menulis `ledger/peninjau/kalibrasi/<UTC>-<jenis>.json` (jawaban mentah + sha + usage + perkiraan USD dari harga 6 Okt); commit + push -> gerbang membacanya dari klon repo. Kode keluar 0 = LULUS.
- Set kasus berubah (mis. bentuk masukan berubah): `python -X utf8 tools/peninjau_kasus.py --tulis` (tanpa `--tulis` = periksa saja); sha set kasus ikut rekaman, jadi kalibrasi harus diulang.
- Tes: `python -X utf8 -m unittest engine.tests.test_peninjau`. Semantik kegagalan: [[07-Testing/T8 - Semantik Kegagalan Operator]] SK-N1..SK-N14.

**Detail - yang TIDAK dibuktikan / belum:**
- Model sungguhan BELUM pernah menjalankan brief ini: tidak ada rekaman kalibrasi; semua tes memakai model palsu. Apakah GLM 5.3 lulus set kalibrasi (termasuk kasus baik tidak ditolak) belum diketahui.
- Biaya per tinjauan belum diukur (epik 12 §5.1 masih asumsi); rekaman kalibrasi pertama akan mencatat usage nyata.
- Belum di-deploy (gerbang `fabius-x402`, Vercel); belum ada pengajuan LOLOS_SHADOW nyata maupun agent luar sungguhan di kursi uji.
- Pemindai injeksi mesin = daftar pola; bisa diakali. Ia lapis kedua; lapis utama = brief + skema + paksaan + set kalibrasi.
- Pemicu tinjau ulang manual (sesudah penerbit / pemilik agent memperbaiki) belum ada: bot = pengajuan baru; agent = masa uji baru (kunci `agent-<id>-<sejak>`).
- Kode jenis `code` (P167b) belum punya penyimpanan privat di gerbang: `calon_bot` menerima pembaca kode lewat argumen `kode`; tanpa itu bot `code` tidak ditinjau (tetap ditahan bila peninjau aktif).

**Terkait:** [[00-Overview/03 - Decisions]] F-D122 · F-D125 · F-D113 · F-D121 · [[08-Backlog/12 - Epik Pengajuan Terbuka dan Peninjau LLM]] · [[04-Tools/TL33 - agent analis]] · [[04-Tools/TL32 - gerbang x402 per sinyal]]
