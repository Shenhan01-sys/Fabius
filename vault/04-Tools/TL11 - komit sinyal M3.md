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

**Detail:** hidup sejak 2 Okt 12:35Z (mode rencana), mode KIRIM sejak 13:06Z, kunci dirotasi 15:50Z (F-D82). Bukti kerja pertama: komit bar 2026-10-02 (P94).

**Terkait:** [[TL9 - ledger paper maju]] · [[TL12 - m3_setup]] · [[00-Overview/03 - Decisions]] F-D80/F-D82
