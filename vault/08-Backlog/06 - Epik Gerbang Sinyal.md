---
tags: [backlog, epik, "gerbang-sinyal", x402, mcp, kontrak]
---

# 06 - Epik Gerbang Sinyal (kirim sinyal bot lewat x402 V2 + MCP, dan kontrak yang masuk akal)

**Bagian dari:** [[08-Backlog/00 - Hub Backlog]]
**Dibuka:** 2 Okt 2026 (malam) oleh builder, kata-katanya (diringkas): *setelah mesin oke, FE dibuat sebagai gateway untuk
jualan sinyal, agent-to-agent atau agent-to-user; dibungkus MCP supaya plug-and-play (baca sinyal lalu buka posisi yang sama);
user berlangganan via x402 V2 yang memakai session dan tiap sinyal dikirim ke Gmail; agen membayar per sinyal via x402 dan
sinyal dikirim lewat MCP yang memicu agen lain. Saya masih bingung kontraknya selain meng-anchor tiap sinyal supaya
auditable: apakah ada lagi?*
**Sumber:** [[08-Backlog/05 - Epik Enam Bot]] §14 (mesin, `engine/sinyal.py`), [[02-Contracts/01 - DecisionAnchor]],
[[02-Contracts/C3 - ExecutionVault]], [[05-Ecosystem/02 - x402 Payment]], [[05-Ecosystem/01 - ERC-8004 Identity]],
[[00-Overview/03 - Decisions]] F-D16 - F-D19. Fakta tentang x402 V2, MCP, Pyth/Chainlink di BNB Chain, fungsi registri ERC-8004 dan
batas Gmail berasal dari riset sesi 2 Okt dan **tidak dibaca ulang untuk halaman ini**: verifikasi sebelum dibangun (§7).

> **STATUS: USULAN rancangan. Belum ada satu baris kontrak, belum ada gerbang.** Halaman ini menjawab pertanyaan builder dan
> menyimpan jawabannya supaya tidak hilang di chat. Tidak ada kalimat di sini yang boleh dikutip keluar vault sebagai klaim produk.

## 1. Doktrin yang berbenturan (baca dulu)

Menjual sinyal **membalik** kalimat yang sekarang tertulis: *"Fabius menjual bukti yang bisa diperiksa, bukan sinyal"*
([[00-Overview/02 - Business Process]]) dan *"Kami tidak menjual sinyal"* ([[10-Submissions/02 - Project Detail]]). Ini pivot kedua
sesudah konsep operator ([[05 - Epik Enam Bot]]), jadi perlu keputusan tercatat (kelas F-D70) dan banner, bukan penyuntingan diam-diam.
Aturan yang tetap mengikat:

- **F-D16:** tidak ada klaim "harapan" di atas sampel yang tidak cukup (net > 0 setelah ongkos nyata, n ≥ 20, tetap positif tanpa
  fold terbaik, BH 0,10, di luar sampel). Hari ini tidak ada bot yang punya satu pun sinyal maju (K1-K3 di [[05 - Epik Enam Bot]]:
  B2 tinggal 0,85 dan 2024-26 ≤ 0,09; gabungan 2025-01 → 2026-08 = 0,071).
- **F-D17:** tidak ada fee-on-profit yang diambil dari wallet pengguna; yang boleh: harga tetap yang ditandatangani pengguna sendiri
  per kejadian, dibatasi di muka, bisa dicabut. **F-D18:** kurva "awal untung lebih besar" ditolak; potongan harga untuk pembeli awal
  boleh (sisi biaya). **F-D19:** satu angka, satu sumber (halaman manusia tidak menghitung ulang apa yang dibaca agen dari chain).
- Tanpa custody, tanpa deposit, tanpa kolam dana. Mengirim "buka posisi yang sama" ke pihak lain berarti **sinyal**, bukan pengelolaan
  dana; yang mengeksekusi selalu pihak penerima dengan kuncinya sendiri.

**Cara mendamaikannya (usulan):** produknya tetap *bukti*; yang berubah adalah apa yang dibuktikan - bukan "keputusan kami benar"
melainkan **"sinyal ini sudah ada sebelum hasilnya, dihasilkan oleh aturan yang dikunci sebelum datanya, dan semua yang kami terbitkan
dibuka pada waktunya"**. Tiga tingkat:

| tingkat | isi | syarat | harga |
|---|---|---|---|
| 0 - umpan bukti | komit sinyal on-chain + pembukaan tertunda + rekam jejak paper; tanpa klaim keuntungan | boleh sekarang (setelah M2-M3) | gratis atau murah (kurva di sisi biaya saja) |
| 1 - sinyal waktu-nyata | muatan sinyal sebelum pembukaan publik, lewat x402/MCP | hanya untuk bot yang lolos gerbang F-D16 pada data maju ter-anchor **dan** telaah hukum (P80) | tetap per sinyal atau per periode; `NONE` gratis |
| 2 - eksekusi | mengeksekusi untuk orang lain | **tidak dijual** | pengguna menjalankan sendiri; pagar on-chain milik pengguna (§3 C-C) |

Catatan jujur: bot harian bukan bisnis yang peka-waktu (bar menutup 00:00 UTC, sinyal berlaku sehari). Pembeli membayar untuk
**kepercayaan dan kemudahan**, bukan keunggulan kecepatan, dan muatan yang sudah dibeli bisa dijual ulang atau bocor. Kalau tingkat 1 ingin
bernilai, nilainya ada di rekam jejak yang bisa diperiksa, bukan di rahasianya.

## 2. Jawaban singkat: kontrak selain "anchor tiap sinyal"

**Ya, ada.** Dan **jangan** menaruh sinyal mentah on-chain: terbuka di explorer (produk bocor ke semua orang pada detik pertama),
membengkakkan gas, dan menghapus tingkat 1. Yang masuk chain adalah **komitmen**, lalu **pembukaan** setelah kedaluwarsa.

Lapisan kontrak berdasarkan pekerjaan yang hanya chain yang bisa lakukan: **(A) bukti** (kapan, aturan mana, tidak dipilih-pilih),
**(B) niaga** (opsional; pembayaran sudah dikerjakan fasilitator x402), **(C) pagar** (menegakkan "agen hanya boleh memilih dari enam bot"
pada uang pengguna), **(D) identitas/reputasi** (pakai yang sudah ada).

## 3. Kontrak, satu per satu

| # | kontrak | apa yang ditegakkan | kenapa harus on-chain | status usulan |
|---|---|---|---|---|
| C-A | **`LockRegistry`** | `lock(botId, specSha, param)` ditulis sekali, tak bisa diubah; `lockedAt` = cap waktu blok. Sinyal menunjuk `specSha`; kontrak (atau verifier) menolak sinyal yang `specSha`-nya dikunci setelah sinyal itu | pra-registrasi ber-sha selama ini bergantung pada cap waktu commit git (F-D29/F-D68); di chain cap waktunya tak bisa digeser oleh siapa pun, termasuk kami. Mengubah parameter = `specSha` baru = bot baru, n mulai dari nol | **inti**, kecil |
| C-B | **`SignalAnchor` v2** (komit-ungkap) | `commit(botId, specSha, asof, expiry, root)` dengan `root` = akar Merkle dari `H(muatan ‖ salt)` semua sinyal bar itu; `reveal(...)` setelah `expiry` wajib dilakukan sebelum tenggat; yang tidak diungkap **tercatat sebagai tidak-diungkap** dan dihitung di statistik | membuktikan sinyal sudah ada **sebelum** hasilnya tanpa membocorkan isinya; pengungkapan wajib menutup cara curang yang paling umum pada penjual sinyal (hanya menunjukkan yang menang). Pembeli memeriksa muatan yang diterimanya terhadap root di chain, jadi dua pembeli yang diberi muatan berbeda (equivocation) terdeteksi. Satu transaksi per bar untuk semua bot (gas belum diukur) | **inti** |
| C-C | **`OperatorGuard`** (ExecutionVault v2, milik pengguna) | ruang aksi tertutup `{NONE, B1…B6}` sebagai bitmap; eksekusi hanya bila ada anchor yang cocok, belum kedaluwarsa, bot ada di himpunan yang diizinkan; plafon per bot hanya bisa **turun**; kill switch hanya menutup | menjadikan "agen hanya memilih bot" **aturan kontrak**, bukan janji. Sekaligus menutup temuan audit: `ExecutionVault` sekarang **hanya menolak hash nol** dan tidak memeriksa anchor (P72). Non-custodial: dompet/akun cerdas milik pengguna sendiri, bukan kolam kami | **inti untuk konsep operator**; tidak dijual (tingkat 2) |
| C-D | **`TrackRecord` / siklus hidup bot** | v1: hanya menyimpan hitungan (komit, ungkap, tidak-diungkap, kedaluwarsa); PnL **dihitung ulang di luar chain** oleh siapa pun dari muatan terbuka + harga publik (pola "run menang atas halaman"). v2: penyelesaian dengan oracle harga (Pyth `parsePriceFeedUpdates` pada jendela waktu bar) untuk bot sederhana; `retire(botId)` tanpa izin saat syarat pembunuh terpenuhi secara objektif (mis. 20 sinyal maju dengan rata-rata net ≤ 0) | syarat pembunuh yang diusulkan di [[05 - Epik Enam Bot]] menjadi **kode**, bukan janji | v2, ditunda |
| C-E | **`EntitlementPass`** (opsional) | hak akses terikat dompet dengan kedaluwarsa (token tak-dapat-dipindahtangankan atau ERC-1155 berkedaluwarsa); server x402 memeriksa `balanceOf` selain sesi | sesi x402 V2 ada di **server** (di luar chain); pass menjadikan hak akses bisa dibawa dan diperiksa agen lain tanpa mengenal server kami. Tanpa ini sesi saja cukup | opsional, setelah M4 |
| C-F | **Escrow / bond** (opsional) | escrow: pembayaran lepas ke penerbit hanya bila pembukaan masuk tepat waktu dan cocok dengan komit. Bond: dipotong **hanya** untuk pelanggaran objektif (tidak mengungkap, terlambat dari `asof`), **tidak** untuk rugi pasar | memberi pembeli jaminan pengiriman tanpa mempercayai kami. Bond yang dipotong karena rugi = asuransi/produk keuangan: jangan | ditunda; berisiko hukum |
| C-G | **Reputasi** | pakai `ReputationRegistry` ERC-8004 resmi (identitas kita sudah ada: token 2494); jangan menulis registri sendiri. Sisi baca hanya menghitung umpan balik dari dompet yang memegang pass/kuitansi bayar | registri resmi dibaca oleh pemindai dan agen lain; registri itu **tidak** memfilter klien, jadi filter ada di pembaca (sybil) | pakai ulang |
| C-H | **`BotRegistry` + `RevenueSplitter`** (satu klon per bot) | `BotRegistry`: botId → (penerbit, specSha, splitter, status). `RevenueSplitter` = `payTo` x402 untuk sinyal bot itu: `release(token)` bersifat pull, bagian Fabius hanya boleh turun, saldo terkumpul tak bisa disita | **inilah kontrak pembayaran yang baru dibutuhkan**: x402 hanya memindahkan token ke SATU alamat `payTo`; membagi uang ke beberapa pihak (penerbit bot luar + Fabius) harus dilakukan kontrak penerima | dengan program penerbit ([[07 - Epik Kolaborasi Bot Terbuka]] §8); ditunda sampai ada penerbit |

**Yang sengaja tidak di chain:** muatan sinyal sebelum kedaluwarsa; email dan data pribadi (UU PDP; selalu di luar chain, dikaitkan
ke dompet di basis data kami); pembayaran (fasilitator x402 sudah menyelesaikannya); PnL v1.

↳ **Koreksi kata (2 Okt malam, atas pertanyaan builder: "tidak ada SC untuk pembayaran? x402 tidak perlu SC?").** Kalimat "pembayaran di luar chain" di atas
menyesatkan. Pembayaran x402 **memang** berjalan lewat kontrak: token ERC-20 (dengan EIP-2612), Permit2, dan proxy x402 kanonis `0x402085c2…` yang dipanggil
fasilitator (`settleWithPermit`; klien hanya menandatangani dan tidak mengirim transaksi). Di chain 97 itu sudah terbukti ([[05-Ecosystem/02 - x402 Payment]]: tx `0xb6093e59…`;
[[07-Testing/T4 - x402 Fork Suite]]: 9 tes fork, 15 tes token). Yang saya maksud adalah **kita tidak perlu menulis kontrak pembayaran sendiri**. Kontrak baru hanya
dibutuhkan di sisi **penerima** bila uangnya harus dibagi (C-H).

**Urutan bangun kontrak (M3 / P78):** C-A + C-B lebih dulu (dua kontrak kecil, nilai terbesar, satu-satunya yang dibutuhkan tingkat 0),
lalu C-C (menutup P72), lalu C-D. C-E/C-F hanya bila pembeli nyata meminta.

**Satu keputusan teknis yang menunggu (M3):** mesin sekarang memakai **sha256 atas JSON kanonik** (paritas dengan
`tools/direction.py`; `engine/sinyal.py`). Untuk verifikasi pengungkapan **di dalam kontrak** perlu penyandian `abi.encode` dan
`keccak256` (atau `sha256` precompile). Dua varian bisa hidup berdampingan (`id` JSON untuk paritas lama, komit ABI untuk chain) -
tetapi pilih satu sebelum menulis `SignalAnchor`.

**DIPUTUSKAN dan DITERAPKAN 2 Okt malam (builder: "menurutmu bagus yang mana? terapkan itu").** Komit on-chain = **`keccak256(abi.encode(struct, salt))` + akar Merkle
gaya OpenZeppelin**; hash spesifikasi dan hash data tetap sha256 JSON. Alasan: (1) kontrak bisa memverifikasi pengungkapan dan kelak menyelesaikan PnL karena struct
punya bidang bertipe (JSON tidak bisa di-parse di EVM); (2) `MerkleProof.verify` OpenZeppelin memakai keccak256, jadi tanpa kode verifier khusus; (3) hash spesifikasi
hanya dibandingkan kesamaannya sebagai bytes32 dan lebih mudah diperiksa orang dengan `sha256sum`. Biayanya: pustaka standar Python tidak punya keccak256
(`hashlib.sha3_256` BUKAN keccak) - `engine/chain.py` mengimplementasikannya murni dan diuji silang dengan `cast keccak`, `cast abi-encode`, dan `eth_utils` (panjang
0-600 byte). Struct: `(uint8 v, bytes32 botId, bytes32 specSha, uint64 asof, bytes32 asset, uint8 aksi, int256 bobotLama, int256 bobotBaru, uint256 hargaRef,
bytes32 dataHash)`; bobot ×1e-9, harga ×1e-8 (0 = tak ada); akar nol = "bot diam" yang dikomit; satu salt acak per sinyal. Dicoba: `engine.cli emit` lalu
`engine.cli verify` pada data nyata (9 dari 9 cocok), `leaf` dan `id` dicocokkan ulang dengan `cast keccak`.

## 4. Alur satu sinyal (komit-ungkap)

1. Bar harian menutup 00:00 UTC. Mesin menghitung (guard basi aktif: bar belum tertutup atau > 12 jam ditolak) → `Signal` dengan
   `spec_sha`, `data_hash`, `harga_ref` (referensi, bukan harga isi).
2. Mesin memilih `salt` acak **per sinyal** dan membangun daun `H(muatan ‖ salt)`; akar Merkle semua sinyal bar itu di-`commit` ke chain
   bersama `botId`, `specSha`, `asof`, `expiry`.
3. Pelanggan menerima `muatan + salt + bukti Merkle` lewat kanal berbayar (§5). Ia memeriksa sendiri terhadap root di chain
   (`engine.cli verify`; di kode `Signal.leaf` + `chain.merkle_verify`). Ini yang membuat "sinyal dikirim ke saya" **bisa diperiksa**, bukan "percayalah".
4. Setelah `expiry` (+ jeda), penerbit mengungkap publik (peristiwa/IPFS + penunjuk di chain). Semua orang bisa menghitung ulang
   rekam jejak; komit tanpa pengungkapan tepat waktu dihitung **tidak-diungkap** dan tampil di statistik.
5. Pembukaan posisi oleh pelanggan: urusan pelanggan (tingkat 2 tidak dijual). Pagar C-C milik pelanggan bila ia memakainya.

## 5. Pengiriman: x402 V2 + MCP + email

*(Semua butir ini dari riset sesi 2 Okt; verifikasi §7 sebelum dibangun.)*

- **x402 V2:** identitas berbasis dompet (SIWx / CAIP-122) dan **sesi** (bayar sekali, akses berulang tanpa membayar tiap permintaan);
  sesi disimpan **di server**, bukan di chain. Header: `PAYMENT-REQUIRED` / `PAYMENT-SIGNATURE` / `PAYMENT-RESPONSE`; ekstensi
  Discovery/Bazaar untuk ditemukan agen; `payTo` bisa dinamis. Langganan = bayar → sesi terikat dompet → tiap permintaan ditandatangani
  SIWx. Bayar-per-sinyal = jalur 402 biasa (pola `GET /vault/latest` yang sudah ada).
- **MCP (Streamable HTTP):** alat `list_bots`, `get_latest_signal(bot_id)`, `verify_signal(id)`, `get_track_record(bot_id)`,
  `subscribe(...)`. `resources/subscribe` + `notifications/resources/updated` hanya bekerja **selama klien tersambung**; agen yang
  sedang mati butuh pemicu lain: **webhook bertanda tangan**, push notification A2A, atau peristiwa chain `SignalCommitted` sebagai
  pemicu lalu agen menarik muatan lewat MCP. Peristiwa chain saja tidak memuat muatan (itu intinya).
- **Email:** berguna untuk pelanggan manusia, tapi **bukan Gmail pribadi** untuk produksi (batas kirim harian rendah, deliverability,
  ToS); pakai penyedia transaksional dengan domain sendiri (SPF/DKIM/DMARC), persetujuan eksplisit dan tautan berhenti berlangganan
  (UU PDP), dan jangan menaruh alamat email di chain. Email = ringkasan terbaca manusia + tautan/lampiran muatan bertanda tangan.
- **Ditemukan:** kartu agen (`docs/agent-card.json`), berkas registrasi ERC-8004, ekstensi Discovery x402, kartu server MCP.
- **Bentuk sinyal bagi pengikut:** target bobot per bar (mis. B2 menghasilkan 5-7 perubahan kecil **tiap hari**), jadi "buka posisi
  yang sama" berarti menyelaraskan target dengan anggaran sendiri. Keputusan §8 #1.

## 6. Urutan kerja (M2-M4) dan gerbang

| tahap | isi | prasyarat |
|---|---|---|
| M2 (P77) | pengunduh dengan guard umur bar, paper ledger append-only, replay B4 dari event | - ; **DIBANGUN 2 Okt (F-D75):** `engine/ledger.py`, `tools/feed_bars.py`, `tools/paper_tick.py`, workflow `paper-ledger.yml` (dipush 2 Okt; lari manual pertama sukses, run 36987654079; funding REST 451 dari runner; **P92/F-D76: funding direkonstruksi dari indeks premium untuk laporan PROVISIONAL, settle final tetap menunggu aktual**; **B3 aktif sejak bar 2026-10-01, F-D77**); **replay B4 belum**; jam maju B1 dimulai di bar 2026-10-01 |
| M3 (P78) | C-A, C-B (lalu C-C) di testnet 97; satu kunci per bot | keputusan §8 #2 (varian hash) |
| M4 (P79) | gerbang: x402 V2 + MCP + webhook (+ email); lalu FE | tingkat 1 hanya setelah P75/P80 dan gerbang F-D16 |

FE paling akhir (pola F-D20: bukti dulu, permukaan sesudahnya). Tingkat 0 bisa jalan lebih awal karena tidak menjual apa pun.

## 7. Belum diverifikasi / tidak diketahui

- Rincian x402 V2 (sesi, SIWx, nama header, `payTo` dinamis), semantik `resources/subscribe` MCP, push notification A2A: dari riset
  sesi, belum dibaca ulang. **Bukan** dari kode atau dokumen yang dibuka untuk halaman ini.
- Pyth: `parsePriceFeedUpdates` ada di BNB Chain dan mencakup 16 aset universe? **Tidak dicek.** Chainlink XAU/USD di BNB Chain: dari riset.
- Fungsi `ReputationRegistry` (`giveFeedback`, `getSummary`, `readAllFeedback`, `getClients`…): dari riset; cocokkan dengan ABI yang
  ter-deploy sebelum dipakai.
- Hukum: apakah menjual sinyal/sinyal-berlangganan di Indonesia memerlukan izin (OJK; F-D17 menyebut nasihat investasi/pool dana),
  pajak, UU PDP untuk email: **tidak diketahui** (P75/P80). Tidak menyarankan menembus blokir apa pun.
- Pembeli asing sampai hari ini: nol. Satu-satunya pembayaran x402 nyata adalah klien kami sendiri ([[05-Ecosystem/02 - x402 Payment]]).
- Biaya gas komit/ungkap: **belum diukur** (jangan menyebut angka sebelum transaksi nyata).

## 8. Keputusan yang menunggu builder

1. Bentuk sinyal: target bobot per bar atau event diskret ([[05 - Epik Enam Bot]] §11 #8).
2. Varian hash untuk komit on-chain: `abi.encode` + `keccak256` (verifikasi di kontrak) atau tetap sha256 JSON (verifikasi di luar).
3. Apakah tingkat 0 (umpan bukti gratis) dibangun lebih dulu, dan tingkat 1 baru setelah gerbang F-D16 + telaah hukum.
4. Apakah pivot "menjual sinyal" ditulis sebagai F-D70+ dengan banner di README/Project Detail/Business Process sebelum kode apa pun.

**Dijawab builder 2 Okt malam:** #1 → "yang penting open posisi, selama masih masuk scope open posisi": sinyal = niat posisi (masuk, keluar, sesuaikan ukuran), tidak
perlu event diskret murni; pengikut boleh mengabaikan penyesuaian kecil di sisinya. #2 → diputuskan dan diterapkan (lihat §3). #4 → dicatat sebagai F-D70 dan dikerjakan
(banner BN-PIVOT di halaman masuk). **#3 dijawab "Boleee" (2 Okt malam, F-D72): tingkat 0 (umpan bukti gratis: komit + pembukaan tertunda + rekam jejak paper, tanpa klaim keuntungan) boleh lebih dulu**;
tingkat 1 tetap menunggu F-D16 pada data maju dan telaah hukum. Yang dibutuhkan tingkat 0: M2 (pengunduh + ledger paper harian) dan M3 (`LockRegistry` + `SignalAnchor` v2). Tambahan: paper penuh sampai builder yakin; venue uang nyata kelak kemungkinan
Binance Agentic Wallet (long-only on-chain; [[05 - Epik Enam Bot]] §6).

**Terkait:** [[05 - Epik Enam Bot]] · [[02-Contracts/01 - DecisionAnchor]] · [[02-Contracts/C3 - ExecutionVault]] ·
[[05-Ecosystem/02 - x402 Payment]] · [[05-Ecosystem/01 - ERC-8004 Identity]] · [[05-Ecosystem/03 - Discovery Gap]] ·
[[00-Overview/03 - Decisions]] · [[10-Submissions/01 - Claims Cheat Sheet]] · [[Concepts/Anchored Before Outcome]]
