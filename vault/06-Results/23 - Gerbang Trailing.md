---
tags: [hasil, "E17", trailing, exit, biaya]
---

# 23 - Gerbang Trailing: apakah "mengunci untung" pernah mungkin di jalur kami

**Alat:** `python -X utf8 tools/trailing_gate.py` · **Artefak:**
`decisions/trailing-gate-20260929T101210Z.json` · **Dijalankan:** 29 Sep 2026 ±10:12Z
**Bagian dari:** [[08-Backlog/03 - Epik Teori Baru]] T2 · **Status:** gerbang kelayakan, **belum**
uji strategi

## 1. Kenapa ada gerbang sebelum uji

Builder mengusulkan trailing stop yang "pokoknya jangan sampai rugi", dengan jarak sudah menghitung
spread + fee. Sebelum menghabiskan satu backtest, algebra-nya ditagih dulu:

```
  trigger bid <= H - d         fill  F = H - d - s - i         PnL = pi - d - s - i - C
  LOCK >= 0            <=>     pi >= d + s + i + C                        ... (1)
  tidak dipicu bounce  <=>     d > s                                      ... (2)
  (1)+(2)  syarat perlu:       pi > 2s + i + C
  jendela d yang sah:           s < d <= pi - s - i - C   (kosong jika pi <= 2s+i+C)
  "jangan sampai rugi" selalu:  butuh d <= -(s+i+C)  -> TIDAK ADA solusi d >= 0
```

C = **59,0 bps** (ongkos round-trip terukur di venue kami, `tools/costs.py`). `s` diambil dari
**spread yang kami rekam di ⑨**, bukan diasumsikan. `i` satu-satunya yang belum terukur, jadi
dilaporkan dua nilai (i=0 optimis, i=s pesimis), bukan dipilih.

## 2. Hasil - dan dia membantah dugaan saya sendiri

Resolusi ticker `wp` (baris per jendela, per kejadian): **5 m: 150/482 (31 %) · 30 m: 403/482 (84 %)
· 60 m: 404/482 (84 %)**. Pada 5 menit kami **bahkan tidak melihat puncak** - jendela puncak
dipakai 60 m.

```
   pi        (puncak seluruh jendela): median +1.122,0 | p75 +4.234,0 | p90 +10.474,5 | max +827.665,0
   pi_awal   (puncak paruh awal     ): median   +747,1 | p75 +3.158,8 | p90  +9.459,5 | max +699.798,5
   spread TERUKUR di venue (⑨): 44 snapshot, 14 simbol | p50 0,04 bps | p90 13,54 bps | max 519,48
```

| s (bps) | i | ambang pi | P(pi ≥ ambang) | **P(pi_awal ≥ ambang)** | jendela d tipikal |
|---|---|---|---|---|---|
| 0,04 (p50) | 0 | 59,1 | 66,1 % | **63,0 %** | 0..1063 |
| 13,5 (p90) | s | 99,6 | 64,9 % | **61,5 %** | 14..1036 |
| 21,0 | 0 | 101,0 | 64,9 % | 61,5 % | 21..1042 |
| 60,0 | s | 239,0 | 62,4 % | 58,8 % | 60..943 |
| 200,0 | s | 659,0 | 55,7 % | **51,9 %** | 200..663 |

**Bacaan yang benar.** (a) "jangan sampai rugi" tetap mustahil - itu bukan soal data, itu
algebra. (b) Tapi **lock bersyarat justru lazim di jalur kami**: ~63 % kejadian punya puncak di
paruh awal yang melewati ambang, bahkan pada spread p90. Jadi dugaan awal saya ("jendelanya kosong")
**salah**, dan alatnya yang mengoreksi saya - bukan sebaliknya. (c) Yang benar-benar membatasi
bukan aritmatika trailing, tapi tiga hal lain:

1. **Resolusi.** Puncak terlihat di 30-60 m; pada 5 m 69 % kejadian tidak punya dua baris pun.
   Kami tidak bisa menaruh trigger di tempat kabar itu hidup.
2. **Waktu.** `pi_awal` adalah proksi "cukup awal untuk dikunci"; ia bukan replika trigger - untuk
   itu perlu tick rapat (P41 butuh 1m-klines; ⑨ baru 200 detik).
3. **Drift.** Yang diubah stop adalah **bentuk distribusi**, bukan arah. Di pool kami puncak besar
   *lalu jatuh di bawah masuk* (E11: −182,5 bps @30 m). Trailing yang memotong jalan menuju puncak
   akan memotong tepat bagian yang membuat harapan kami positif (E13: median +79,8 bps @5 m).

## 3. Apa yang boleh dan tidak boleh ditulis

- Boleh: *"kunci bersyarat mungkin di substrate kami (~63 % kejadian), tapi kami tidak punya
  resolusi untuk mengeksekusinya, dan yang diubahnya adalah bentuk distribusi, bukan harapan."*
- Tidak boleh: "trailing stop membuat posisi tidak rugi" (mustahil secara algebra, dan
  `i` belum terukur), dan tidak boleh "hasil gate menunjukkan trailing menaikkan harapan" -
  alat ini **tidak** menghitung harapan sama sekali.

## 4. Desain E17 yang dipaksanya (belum dibangun)

Arm di **posisi yang sama**, hanya aturan exit yang beda: A fixed-horizon (5 m), B stop statis,
C trailing dengan grid d (kelipatan 1,5x/3x/6x rentang tick), D TP 5 %, E trailing vol-scaled,
F parsial ½ di TP/2. Wajib ada: (i) **random-barrier placebo** - level stop digambar dari distribusi
yang sama tanpa berjangkar ke puncak (kalau hasilnya sama, yang bekerja adalah distribusi puncak,
bukan trailing); (ii) jam digeser acak 30-90 m; (iii) **% trigger yang termakan dalam N baris pertama
saat pi_awal < 2s** (pembunuh senyap di tick jarang); (iv) fill dari **bid**, bukan mid, dan
distribusi gap fill−trigger (p50/p95/p99); (v) vonis = perubahan `P(net ≤ −X)` dan median, **bukan**
mean saja, karena literatur dan algebra sama-sama meramalkan yang berubah adalah ekor.

**Terkait:** [[08-Backlog/03 - Epik Teori Baru]] §3 · [[06-Results/19 - Umur Posisi]] ·
[[06-Results/21 - Rem di Horison Cepat]] · [[00-Overview/03 - Decisions]] F-D48 ·
[[08-Backlog/04 - Riset Teori (Sitasi)]] S6-S9 · [[TradingKnowledge/FD7 - Invalidation Stop dan Time-Stop]]
