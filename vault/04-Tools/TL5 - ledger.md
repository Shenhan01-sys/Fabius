---
tags: [perkakas, "TL5"]
---

# TL5 - ledger.py

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/ledger.py`, `06-Results/07 - Matured Outcomes.md`

**Ringkas:** menilai prediksi yang sudah di-anchor — menang, rugi, `AMBIGU`, atau **belum waktunya**
— tanpa memberi alat ini cara untuk me-rebase masa lalu.

**Poin kunci:**
- `entry_ref` dibaca dari **rekaman** (ikut terikat `decisionHash` di chain), tidak dihitung ulang.
- `BELUM JATUH TEMPO` punya status sendiri + sisa jam dicetak, dan **tidak ikut agregat**.
- Stop vs target dicari **urutan sentuh**-nya; kalau keduanya mungkin di satu bar yang sama →
  `AMBIGU`, tidak dipilih yang menguntungkan.
- Dedupe pada **level peristiwa** (simbol, sisi, entry, bar masuk, horizon), bukan pada hash: hash
  beda tiap siklus karena memuat waktu generasi → tanpa pagar ini satu peristiwa pasar terhitung
  5 posisi dan `n` laporan membengkak tanpa informasi.
- Ongkos 20 bps RT dipakai sejak awal dan yang dilaporkan `net`.
- Hasil pertama (26 Sep): dua short MARSCOIN → **+1,5 bps MENANG** dan **−146,3 bps RUGI**;
  `WR 50 %`, rata-rata **−72,4 bps**, **n=2** → tidak ada uji statistik yang boleh dijalankan.

**Terkait:** [[06-Results/07 - Matured Outcomes]] · [[06-Results/02 - Thresholds]]
