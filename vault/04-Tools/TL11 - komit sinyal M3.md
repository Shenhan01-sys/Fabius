---
tags: [perkakas, "TL11"]
---

# TL11 - komit sinyal M3

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/signal_commit.py`, `tools/operator_loop.py`, `tools/evm.py`, `tools/gen_signal_vectors.py`, `tools/railway_up.py`, `railway/Dockerfile`; tes `engine/tests/test_signal_commit.py` (19, termasuk jalur penuh di anvil) + `engine/tests/test_signal_vectors.py`

**Ringkas:** worker Railway tahap 1. Tiap 5 menit: tarik `ledger/` + `deployments/` dari GitHub (clone sparse), hitung ulang sinyal tiap tick dari bar yang di-commit, komit akar Merkle ke [[02-Contracts/C7 - SignalAnchor]] dalam batas 12 jam, lalu ungkap tiap sinyal. Salt = HMAC deterministik dari kunci committer.

**Poin kunci:**
- Railway: proyek `fabius-engine`, service `fabius-engine`, region Singapura, SATU replika (dua replika = dua penanda tangan), `RAILWAY_DOCKERFILE_PATH=railway/Dockerfile`.
- Deploy kode: `python -X utf8 tools/railway_up.py` (git archive HEAD - berkas yang tidak di-commit, termasuk kunci, tidak mungkin ikut).
- Log: `railway logs --service fabius-engine --lines 40`. JANGAN `railway environment config --json` / `railway variable list --json|--kv`: keduanya mencetak kunci (F-D82).
- Rencana tanpa kunci: `python -X utf8 tools/signal_commit.py --committer 0xCA9c7322210E9a7F7d0953c862d4Ef60cC0D64A4`.

**Yang ia TOLAK lakukan:** mengomit tick yang tidak bisa direproduksi PERSIS dari bar (ALARM); menimpa komit yang akarnya beda (ALARM); memaksa komit yang lewat batas (TERLEWAT); mengirim selama ada transaksi tertunda; menulis ledger (penulisnya tetap rantai GitHub).

**Detail:** hidup sejak 2 Okt 12:35Z (mode rencana), mode KIRIM sejak 13:06Z, kunci dirotasi 15:50Z (F-D82). Bukti kerja pertama: komit bar 2026-10-02 (P94) -> **terjadi 3 Okt**: worker 08:43:49Z melihat tick; komit B1 akar nol n=0 tx `0x66dc323c1282…` blok 134600162 gas 169.576, komit B3 n=1 tx `0xe26a8d6e2c26…` blok 134600169 gas 172.760, ungkap B3 "DOTUSDT KELUAR" tx `0x4073f53c9fd8…` blok 134600186 gas 67.038 (08:44:04Z); `terkirim: 2 komit, 1 ungkap, 0 gagal`; `commitCount()` 0 -> 2; `python -X utf8 tools/verify_signals.py` 08:44:16Z (blok 134600218): B1-TREND 2026-10-02 SAH (akar nol, 0/0), B3-CARRY 2026-10-02 SAH (1/1), 2026-10-01 keduanya SEBELUM KUNCI; ALARM 0.

**Semantik kegagalan (P109, 3 Okt):** tiap titik gagal worker + `evm.py` punya baris di [[07-Testing/T8 - Semantik Kegagalan Operator]] (SK-W1..W13, SK-V1); putaran worker kini lewat `guarded_round` (galat apa pun dicatat "putaran GAGAL", worker hidup, tidak ada rencana/kiriman dari putaran itu).

**Terkait:** [[TL9 - ledger paper maju]] · [[TL12 - m3_setup]] · [[00-Overview/03 - Decisions]] F-D80/F-D82 · [[07-Testing/T8 - Semantik Kegagalan Operator]]
