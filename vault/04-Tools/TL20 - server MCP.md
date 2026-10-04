---
tags: [perkakas, "TL20"]
---

# TL20 - server MCP (pintu agen, tingkat 0)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `web/src/app/mcp/route.ts` (route `/mcp` di app `web/` yang sama dengan landing) · `web/src/lib/mcp-tools.ts` (8 alat) ·
`web/src/lib/fabius-chain.ts` (pembaca chain 97, tanpa kunci) · paket `mcp-handler` 2.2 + `@modelcontextprotocol/server` 2.3 + `viem` 2.57 + `zod` 4

**Ringkas:** agen (Claude, Cursor, agen lain) membaca bukti Fabius sebagai alat MCP: Streamable HTTP, stateless, hanya baca, gratis. Ini tingkat 0
(F-D72). Tingkat 1 (sinyal waktu-nyata berbayar lewat x402) TIDAK punya alat di sini: terkunci sampai bot lolos F-D16 dan telaah hukum (P80).

**Alat:**
- `fabius_overview` - mulai di sini: batas kejujuran, tingkat, kontrak, daftar alat, cara memeriksa sendiri.
- `fabius_list_bots` - enam spesifikasi terkunci + buku slot (dari snapshot build).
- `fabius_track_record {bot}` - ledger maju LIVE dari GitHub raw: tick, settle final, hari bolong (tidak dihitung nol), kemajuan F-D16.
- `fabius_proof_feed` - vonis per (bot, bar) dari snapshot build.
- `fabius_locks` - semua kunci on-chain berurutan + tautan BscScan.
- `fabius_signals {bot, bar}` - LIVE dari SignalAnchor: komit (bot, bar) di bawah committer resmi + setiap sinyal yang diungkap.
- `fabius_latest_signals` - bar terakhir tiap bot berjam maju + komit + sinyalnya (pintu masuk biasa untuk agen pengikut).
- `fabius_verify {bot, bar}` - pemeriksaan publik penuh: leaf dan id dihitung ulang dari payload on-chain dengan encoding ABI engine, id dicocokkan ke
  tick ledger. Vonis SAH hanya kalau jumlah, leaf, dan id semua cocok; SEALED_NOT_YET_REVEALED; ALARM dengan alasannya.

**Hash = engine:** `commitId = keccak256(abi.encode(committer, botId, specSha, asof))`, `leaf = keccak256(abi.encode(Signal, salt))`,
`id = keccak256(abi.encode(Signal))`, asof = penutupan bar (detik). Dihitung ulang di TypeScript, tidak disalin dari engine; cocok dengan chain dan ledger
(bukti di bawah).

**Yang ia TOLAK lakukan:** menganggap gagal baca sebagai "tidak ada" (RPC/GitHub mati = `isError` dengan alasan, T8); menerima bot di luar daftar atau
tanggal yang bukan tanggal kalender (`2026-13-99`, `2026-02-30` -> galat validasi masukan); menjual atau menyiratkan tingkat 1; memakai kunci apa pun.

**Status komit yang mungkin:** BEFORE_LOCK (bar sebelum spesifikasi dikunci on-chain), BAR_NOT_CLOSED, AWAITING_COMMIT (masih dalam `maxLag` kontrak),
NOT_COMMITTED (lewat `maxLag` tanpa komit = pelanggaran yang terlihat publik).

**Bukti 3 Okt (lokal, `next start` + chain 97 live):** `initialize` -> serverInfo `fabius 0.1.0`; `tools/list` 8 alat; `fabius_verify B3-CARRY
2026-10-02` -> `SAH (1/1 revealed, all ids match the ledger)` (DOTUSDT EXIT, bobot 0,0625 -> 0, harga acuan 1,1535, `leaf_recomputes` true,
`in_ledger_tick` true); B1-TREND 2026-10-02 -> SAH (akar nol, 0/0); `fabius_signals B1-TREND 2026-10-01` -> BEFORE_LOCK; `2030-01-01` ->
BAR_NOT_CLOSED; `fabius_latest_signals` -> B1/B3 2026-10-02, 2 komit di chain. Klien resmi: `npx @modelcontextprotocol/inspector --cli
http://localhost:3006/mcp --transport http --method tools/list` -> 8 alat; `tools/call fabius_verify` B1 -> SAH.

**Pintu agen di landing:** potongan konfigurasi menampilkan asal halaman + `/mcp` (dibaca di klien sesudah hidrasi; server merender penampung).
Status pintu: "MCP server · live · tier 0".

**Cara menjalankan lokal:** `cd web && npm run build && npx next start -p 3006`, lalu POST JSON-RPC ke `http://localhost:3006/mcp` dengan header
`accept: application/json, text/event-stream`. Sesudah deploy Vercel: `https://<host>/mcp`; Claude Code: `claude mcp add --transport http fabius https://<host>/mcp`.

**Pelajaran 3 Okt:** menghentikan tugas latar `npx next start` di Windows mematikan pembungkus shell, BUKAN proses node anaknya; port 3006 tetap dipegang
build lama dan uji berikutnya diam-diam mengenai kode lama (validasi tanggal "masih gagal"). Sebelum uji ulang, pastikan port kosong
(`Get-NetTCPConnection -LocalPort 3006`) dan server baru mencetak `Ready`.

**HIDUP 3 Okt (builder: "kan bisa trigger deploy via vercel cli"):** `https://fabius-one.vercel.app/mcp`. Produksi diuji dengan JSON-RPC:
`initialize` -> `fabius 0.1.0`; `fabius_verify B3-CARRY 2026-10-02` -> `SAH (1/1 revealed, all ids match the ledger)`; `fabius_latest_signals` -> B1/B3
2026-10-02, 2 komit; `fabius_track_record B1-TREND` -> 2 tick, 0 sinyal; `2026-02-30` -> galat validasi. Endpoint ini jadi endpoint PERTAMA di
`docs/agent-card.json` (ditulis `python -X utf8 tools/x8004_register.py --card`, tanpa tx; kartu ERC-8004 token 2494 menunjuk berkas itu di repo publik).
Claude Code: `claude mcp add --transport http fabius https://fabius-one.vercel.app/mcp`.

**Sejak 4 Okt:** logika `fabius_verify` + `fabius_signals` dipindah ke `web/src/lib/verify.ts`, dipakai bersama halaman /verify ([[TL24 - halaman verify]]): satu kode untuk agen dan manusia. Bentuk keluaran MCP dipertahankan; `fabius_verify` kini juga memuat salt, leaf, dan blok tiap sinyal.

**Sejak 4 Okt (alat ke-9):** `fabius_status` - kesehatan operasi hari ini (tick, komit, ungkap, kertas, gas, detak rantai GitHub), kode sama dengan halaman /status (`web/src/lib/status.ts`, [[TL26 - halaman status]]); `fabius_overview` ikut mendaftarkannya. Lokal: `tools/list` -> 9 alat.

**Belum:** tingkat 1 x402 (terkunci); snapshot otomatis (P113).

**Terkait:** [[TL19 - web landing]] · [[TL14 - verify_signals]] · [[02-Contracts/C7 - SignalAnchor]] · [[07-Testing/T8 - Semantik Kegagalan Operator]] ·
[[00-Overview/03 - Decisions]] F-D70/F-D72 · [[08-Backlog/06 - Epik Gerbang Sinyal]]
