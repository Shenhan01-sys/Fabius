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

## 28 Sep — dihitung ulang dengan ongkos yang benar (P10)

Tabel di atas masih sah sebagai rekaman **run 25/26 Sep**, tapi net-nya memakai asumsi 20 bps.
Dengan round-trip **59 bps** yang benar-benar kami ukur di venue sendiri, tidak ada satu pun
keputusan paper yang tersisa sebagai pemenang:

| masuk (bar) | due | gross | net @20 | **net @59** | hasil |
|---|---|---|---|---|---|
| 24 Sep 16:00Z | 25 Sep 17:00Z | +21,5 | +1,5 | **−37,5** | RUGI |
| 24 Sep 17:00Z | 25 Sep 18:00Z | −126,3 | −146,3 | **−185,3** | RUGI |
| 27 Sep (E2E) | 27 Sep 18:00Z | −426,3 | *(belum jatuh tempo)* | **−485,3** | RUGI (stop kena) |

`PAPER: n=3 · WR 0 % · net rata-rata −236,0 bps · total −708,1 bps` — dibaca ulang
`python -X utf8 tools/ledger.py` lalu `python -X utf8 tools/winlog.py`.

Dua koreksi sekalian, karena bullet di atas menulis hal yang tidak bisa dipertahankan:

- **"Dua menit berbeda" salah.** Dua keputusan itu dibuat berjarak **±12 menit** (18:51Z dan 19:03Z
  waktu generasi), dengan due-time **1 jam** berbeda. Poin substansinya tetap hidup — dua tebakan
  berurutan pada aset yang sama menghasilkan tanda yang berlawanan — tapi tidak dengan angka itu.
- **"Yang menang pun tidak menutupi ongkos" sekarang lebih keras:** yang tadinya +1,5 bps itu
  bukan "untung tipis", dia **rugi 37,5 bps** begitu ongkos nyata dipakai. Persis kelas kesalahan
  yang ditahan [[Concepts/Cost Is Fixed]].

Perubahan ini tercatat sebagai koreksi di [[00-Overview/05 - Corrections]]; `tools/winlog.py`
mencetak perselisihan antar artefak (`2 decisionHash dengan net berbeda`) supaya jejaknya kelihatan,
 bukan hilang.
