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
- Uji lama menutup dengan 20 bps RT dan yang dilaporkan `net`. **Sejak P10 (28 Sep)** angka itu
  datang dari `tools/costs.py` (59 bps terukur); `tools/winlog.py` mencetak `decisionHash` yang
  net-nya berbeda antar artefak — itu jejak penggantian penggaris, bukan dua peristiwa berbeda.
- Hasil pertama (25-26 Sep, penggaris 20 bps): dua short MARSCOIN → **+1,5 bps MENANG** dan
  **−146,3 bps RUGI**; `WR 50 %`, rata-rata **−72,4 bps**, **n=2**. **Dihitung ulang 28 Sep dengan
  59 bps: keduanya RUGI** (−37,5 / −185,3), dan satu keputusan 27 Sep ikut jatuh tempo (−485,3) →
  **PAPER n=3, WR 0 %, rata-rata −236,0 bps**. Rinciannya [[06-Results/07 - Matured Outcomes]].

**Terkait:** [[06-Results/07 - Matured Outcomes]] · [[06-Results/02 - Thresholds]]
