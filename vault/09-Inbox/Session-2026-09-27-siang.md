---
tags: [inbox, "S-27-b"]
---

# Session 27 Sep (siang) — P1 jalan, dan tes clone membantah satu klaim kami

**Bagian dari:** [[09-Inbox/00 - Hub Inbox]]
**Sumber:** keluaran perintah di bawah; yang bukan hasil run ditandai *(belum diukur)*.

## Yang terjadi, berurutan

1. Pertanyaan builder: *"top-up tBNB untuk agen untuk apa? di trade kah?"*. Jawabannya berubah jadi
   temuan: **tBNB cuma untuk gas** (posisi memakai token demo), dan guard `exec_deploy.py` menolak
   kemarin karena memakai **plafon 1 gwei** sementara testnet live **0,10 gwei**. Jalur penuh
   = 0,0018 tBNB vs saldo 0,007884 -> **dananya cukup**; yang menahan adalah taksiran konservatif.
2. Builder memilih sumber dana: pakai tBNB deployer di `app/.env`. Tower
   `0xAEc63F6c…c8361` (0,214667 tBNB) mengirim 0,03 -> agen **0,037884**
   (tx `0x37489064…`, `status=1`, blok 133.419.795, receipt dibaca ulang).
3. **P1 selesai.** Deploy `DemoAsset`/`DemoPair`/`ExecutionVault` + 7 tx seeding/config, lalu
   `tools/execute_live.py` (berkas yang sebelumnya *disuruh* dijalankan oleh `exec_deploy.py`
   padahal tidak pernah ada): dua round-trip nyata di bawah anchor `0x0f5ff29e327902eb…` —
   realized **−59 bps** per putaran, sama dengan prediksi test suite. Guard-nya terbukti sendiri:
   `--open-long BREWUSDT` **ditolak** karena keputusan itu `ABSTAIN`.
4. Probe clone (`_research/probe_clone_paths.py`) memulainya 3/4: `anchor.py --verify` **gagal**
   karena `AGENT_ADDRESS` cuma ada di `.agent.env` yang di-gitignore. Jadi kalimat "nol kunci,
   siapa pun bisa periksa" selama ini sebenarnya berarti "punya salinan kerja kami".
   Perbaikan: `deployments/97.json` (ter-track, 8 alamat, bytecode dicek ke chain) + roster
   dicetak dari `getAgent()`/`countByAgent()`. Hasil: **4/4**.
5. Satu hipotesis kuukur dan gugur sendiri: mengira selisih 17 vs 11 itu karena cakupan verifier
   sempit. Perluasan malah menyeret 301 baris kandidat `screen` -> "11/312 cocok". Cakupan
   dikembalikan, dan `--verify` sekarang **mencetak peringatan** kalau `anchorCount()` != jumlah
   baris terpelacak. P6b tetap terbuka.

## Angka baru yang resmi tinggal di halaman ini

| hal | nilai | halaman pemilik |
|---|---|---|
| agen 0x4bb3…69c862 | 0,034220 tBNB setelah 4 tx eksekusi | [[Quick-Reference]] |
| posisi nyata | 2 round-trip, −59 bps tiap putaran | [[02-Contracts/C3 - ExecutionVault]] |
| gas nyata | open 258.008/295.443 · close 123.216/150.576 | [[Concepts/Cost Is Fixed]] |
| jalur pemeriksaan dari clone | 4/4 hidup pada HEAD `304fe4f` | [[07-Testing/T6 - Clean Clone Evidence]] |

## Yang belum diukur *(jangan dikutip sebagai angka)*

- slippage pasar sungguhan — venue kita tetap pool x·y=k milik sendiri
- apakah agen **asing** mau membayar — endpoint masih lokal (P2)
- win-rate dengan `n ≥ 20` — yang dinilai masih 2 posisi

**Terkait:** [[09-Inbox/Session-2026-09-26-27]] · [[08-Backlog/01 - Backlog]] · [[START-HERE]]
