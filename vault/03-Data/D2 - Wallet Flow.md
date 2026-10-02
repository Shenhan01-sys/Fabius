---
tags: [data, "D2"]
---

# D2 - Wallet Flow (bidang ⑦)

> **DIHENTIKAN 2 Okt 2026 15:06Z (F-D81).** `wallet-flow.yml` + `wallet-flow-watchdog.yml` `disabled_manually` sebelum berkas datanya lewat batas 100 MB GitHub (watch-prices 65,8 MB / wallet-flow 60,9 / book-depth 28,8 saat berhenti). Data lama tetap terbaca; klaim yang butuh data sesudah 15:05Z = tak terukur.

**Bagian dari:** [[03-Data/00 - Hub Data]]
**Sumber:** `universe/record_wallet_flow.py`, `.github/workflows/wallet-flow.yml`,
`_research/panel_stats.py`

**Ringkas:** perekam aliran smart money & KOL di BSC. Ini satu-satunya bidang yang **tidak bisa**
disusulkan, jadi ia diperlakukan sebagai aset yang menetes tiap jam.

**Poin kunci:**
- Sumber: GMGN `user/smartmoney` + `user/kol`. Terukur: **100 transaksi per panggilan**, jendela
  lihat **8–13 menit**, dan **semua parameter paging diabaikan server** (`offset`/`page`/`end_ts`
  → head yang sama, overlap 98/100). Kesimpulan pentingnya: **tidak ada riwayat**; yang lewat = hilang.
- Field yang disimpan: maker (dompet), `base_address`, side, `is_open_or_close`, `buy_cost_usd`,
  `price_usd`, `timestamp`, `transaction_hash`, `maker_info.tags` — tag panel ikut disimpan karena
  **keanggotaan panel adalah pilihan GMGN**, dan itu bias yang harus bisa ditunjuk.
- Cadence: loop ±4,6 jam, commit tiap ±4 menit. Versi pertama (25–26 Sep) ditulis sebagai
  **"rantai yang menghidupi dirinya sendiri"**: `workflow_dispatch` di akhir + `schedule`
  penyelamat di berkas yang sama. **Klaim itu salah dan baru ketahuan 28 Sep 08:2xZ** - dua sebab,
  keduanya mekanis: (1) langkah sambung-rantai memanggil `.../workflows/<id>/dispatch` padahal
  endpoint REST-nya `.../dispatches` dengan body `{"ref":…,"inputs":{…}}` → 404 → **dispatch-diri
  tidak pernah berhasil sekali pun**; yang menghidupi rantai selama ini cuma cron. (2) cron yang
  sama + `cancel-in-progress: true` = tiap tembakan per-jam **membatalkan** rantai yang sedang
  merekam - terukur run #11/#12/#13 `conclusion=cancelled` pada jarak yang persis mengikuti jadwal
  cron. Jadi penyelamatnya membunuh pasiennya, dan daftar run tetap terlihat "hidup tiap jam".
- Bentuk sekarang: `schedule` **dihapus** dari workflow perekam, `cancel-in-progress: false`
  (yang macet dipotong `timeout-minutes: 330`, bukan dibatalkan), dan penyelamat pindah ke
  `.github/workflows/wallet-flow-watchdog.yml` (cron per-30 menit, grup concurrency sendiri).
  Yang ditanya watchdog bukan "kapan terakhir run" tapi **"berapa umur
  `universe/wallet-flow-manifest.txt`"** - untuk bidang tanpa riwayat, umur berkas adalah satu-satunya
  tanda hidup yang tidak bisa berbohong.
- `cancel-in-progress: true` dan `actions: write` bukan hiasan: tanpanya satu jalanan menggantung
  mengantrikan sisanya, dan dispatch-diri gagal diam-diam (terukur, `conclusion=failure`).
- Status 27 Sep 03:5x WIB (= 26 Sep 20:5xZ), dari `python -X utf8 _research/panel_stats.py`:
  **8.053 transaksi unik / 348 maker / 643 token / 11,82 jam**; **116 maker ≥20 tx** (57 ≥40).
  Sepuluh jam sebelumnya angka ini 7.137 / 322 / 604 / 10,14 — perekam menetes, jadi setiap angka
  panel di vault ini wajib punya tanggal run, bukan dianggap tetap. Rekamannya di
  `universe/wallet-flow.jsonl`, berantai lewat `universe/wallet-flow-manifest.txt`
  (sha256 berkas + ekor + `usia_aliran_jam`).
- **Satu harga per (token, stempel waktu)** — terukur 28 Sep: **5.355 baris `px` berbagi
  stempel yang sama untuk token yang sama** (±19 % deret kami), karena `smartmoney` dan `kol`
  melihat pool yang sama dalam satu siklus. Selama duplikat dibiarkan, "harga masuk" ditentukan
  urutan, bukan data — dan dua alat kami mencetak angka berbeda untuk kejadian identik. Bentuk
  kanoniknya ada di satu tempat: `flow_cluster_test.dedupe_px()` (median per stempel).
- **Kontingen `px` kedua (P17):** `universe/record_watch_prices.py` menarik harga lewat
  **DexScreener** `tokens/v1/bsc/<30 alamat>` (terukur 200 @401 ms, satu panggilan = 30 token)
  untuk token yang sudah keluar dari daftar panas, jendela **2 jam** (terukur: 136 token pantau =
  5 panggilan/siklus; 24 jam akan jadi 927 token = 31 panggilan). Barisnya `{"k":"wp",...}` di
  `universe/watch-prices.jsonl` - berisi `priceUsd`, likuiditas, FDV, volum, dan **jumlah
  beli/jual dalam 1 jam dari venue**, yaitu jawaban atas "tidak ada riwayat" di atas.
- **Garis darah berkas data (28 Sep):** ekor `wallet-flow.jsonl` ditulis mesin tiap 3,4 menit,
  jadi commit manusia ke berkas yang sama = mesin itu konflik tiap siklus. Kini
  `.gitattributes` memakai `merge=union` untuk `universe/*.jsonl` dan `merge=ours` untuk
  `*-manifest.txt`, dan loop perekam memulihkan dirinya (`rebase --abort` + `reset --hard
  origin/<branch>`) lalu MENGERIAK kalau 3x push gagal. Sengaja tidak ada `*.json merge=union`:
  JSON hasil union tidak bisa di-parse, dan artefak keputusan harus bertabrakan, bukan diam-diam
  digabung.
- Jangan ulangi kesalahan 27 Sep: jumlah baris di **disk lokalmu** bukan keadaan sistem —
  `git fetch` dulu ([[Concepts/Stale Local Copy]]).

## Yang dipertimbangkan sebagai sumber, lalu tidak dipakai

Ditulis supaya sesi berikutnya tidak membeli perjalanan yang sama dua kali. Semua keputusan ini
diambil di luar repo produk (alat workspace), jadi bukti mentahnya ada di `../_research/` dan
`../Vault/` — **bukan** sesuatu yang bisa dijalankan orang dari clone Fabius.

| kandidat | hasil terukur | keputusan |
|---|---|---|
| **GMGN skill CLI** (`npx skills add …`) | route privat butuh `timestamp` + `client_id` + kunci bertanda tangan; isinya tetap bisa dibaca lewat HTTP biasa | **tidak dipasang** — memasang CLI pihak ketiga kalau yang dibutuhkan cuma baca endpoint = menambah permukaan kunci demi nol kemampuan baru |
| **FOMO API** | `GET /health` → `{"ok":true,"traders":8,"uptime":2779.6}`; `dataset` → `traders: 8` | **bukan jalur kritis.** Bukan karena buruk, karena populasinya 8 dompet — tidak bisa jadi bahan statistik apa pun (`06-Results/02` minta `n ≥ 20` per kelompok) |
| **Dune MCP** (`api.dune.com/mcp/v1`) | tidak diukur sebagai alternatif; jalur REST `/api/v3/execute` sudah memberi kredit terbaca + hasil ber-baris | **REST saja** — alasan pilihan, bukan hasil ukur. MCP menambah konfigurasi klien tanpa menambah kemampuan yang kami pakai |
| **Hugging Face Spaces / tempat TimesFM** | ditanyakan builder 26 Sep karena laptopnya mati saat tidur | **bukan tempatnya perekam.** Yang jalan: GitHub Actions (`universe-hourly.yml`, `wallet-flow.yml`) — commit diberi timestamp oleh server pihak ketiga, yang justru bagian dari klaimnya. Sebuah Space yang menulis dataset-nya sendiri tidak menghasilkan saksi independen |

**Terkait:** [[03-Data/D4 - Dune]] · [[03-Data/D5 - Record Schemas]] ·
[[06-Results/06 - Pre-registration Horizon]] · [[04-Tools/TL7 - measurement harness]]
