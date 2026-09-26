---
tags: [hasil, "R7"]
---

# 07 - Matured Outcomes

**Bagian dari:** [[06-Results/00 - Hub Results]]
**Sumber:** `tools/ledger.py`, `decisions/ledger-20260926Z.jsonl`

**Ringkas:** prediksi yang kami anchor sudah ada yang jatuh tempo. Inilah angka pertama yang
bukan tentang proses, tapi tentang kebenaran tebakan — dan angkanya tidak enak.

| masuk (bar) | entry | jatuh tempo | keluar | gross | **net** | hasil |
|---|---|---|---|---|---|---|
| 24 Sep 16:00Z | 0,11605 | 25 Sep 17:00Z | di horizon (time-stop) | +21,5 | **+1,5 bps** | MENANG |
| 24 Sep 17:00Z | 0,11564 | 25 Sep 18:00Z | di horizon (time-stop) | −126,3 | **−146,3 bps** | RUGI |

`WR 50 % · net rata-rata −72,4 bps · total −144,8 bps · rugi bersih 1`

**Poin kunci:**
- Dua menit berbeda, hasil berlawanan 148 bps — konfirmasi langsung bahwa sinyal ini tidak
  membedakan dua jam berturut pada aset yang sama (`06-Results/04`).
- Yang menang pun tidak menutupi ongkos: +1,5 bps net = arah benar, pasar membayar biaya nyaris
  persis nol.
- `n = 2`: tidak ada klaim win-rate, tidak ada uji statistik, `MIN_TRADES = 20` jauh dari terpenuhi.
- Yang boleh dikatakan: **prediksinya jatuh tempo dan jejaknya masih utuh untuk diperiksa.**
  Bukan "kami untung", bukan "kami rugi secara statistik" — dua-duanya melebihi sampel.
- Untuk dapat sampel, horizon harus turun ke 4 jam (`06-Results/02` §4) dan itu membuka pintu ke
  Uji A ([[06-Results/06 - Pre-registration Horizon]]).

**Terkait:** [[04-Tools/TL5 - ledger]] · [[06-Results/02 - Thresholds]]
