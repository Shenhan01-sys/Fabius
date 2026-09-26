---
tags: [perkakas, "TL7"]
---

# TL7 - Measurement Harness

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/backtest.py`, `tools/flow_test.py`, `tools/whale_sweep.py`,
`_research/check_garbled.py`, `_research/panel_stats.py`

**Ringkas:** alat pengukur bukan pencetak angka cantik. Setiap alat di keluarga ini membawa pager
yang sama: ambang dari kode live (bukan disalin), 1 sampel per peristiwa non-overlap, BH,
drop-best-fold, dan **penolakan untuk menyimpulkan** kalau cakupannya runtuh.

**Poin kunci:**
- `backtest.py`: aturan live dijalankan di 400 hari × 12 aset → rugi 12/12; `--mom-only` dan
  `--flip` ada supaya "siapa yang memproduksi nol" (gerbang atau isinya) bisa dibedakan.
- `flow_test.py` / `whale_sweep.py`: **pra-registrasi dulu** (`06-Results/05`, `06-Results/06`),
  baseline = (token, jam) acak, bukan nol; bootstrap deterministik `seed=0` supaya orang lain
  mengulang dan mendapat angka yang sama.
- Pagar cakupan: kalau < 1/4 token terpetakan, alat **menolak melapor**. Penyebabnya nyata: join
  heks kapital/kecil menjatuhkan 85/86 token dan tabelnya tetap tercetak rapi.
- Truncation diucapkan, tidak dibisikkan: `LIMIT`, halaman yang hilang, dan `[TERPOTONG]` dicetak;
  hasil parsial tidak boleh menyamar sebagai hasil penuh (cache entri diberi nama rev r2/r3).
- Bug yang berulang dan cara menghukumnya: `python -c` multi-baris di cmd.exe (empat kali), `ROOT`
  dihitung tiga tingkat (dua kali — sekarang setiap alat jalur meng-assert direktorinya),
  sisipan karakter CJK ke komentar Indonesia (empat kali), BOM dari `Set-Content -Encoding UTF8`,
  `print` yang crash di cp1252. Semua itu kini punya alat: `_research/check_garbled.py`
  (CJK/Hangul/fullwidth + BOM + print tak ter-encode) dan `forge test` untuk yang di kontrak.
- Angka yang dihasilkan alat ini adalah **satu-satunya** yang boleh dikutip halaman lain
  ([[Conventions]] §2).

**Terkait:** [[06-Results/00 - Hub Results]] · [[07-Testing/01 - Test Commands]]
