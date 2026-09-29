---
tags: [hasil, "E17", trailing, exit, resolusi]
---

# 24 - Trailing pada Bar yang Salah

**Alat:** `python -X utf8 tools/trailing_policy.py --gap 0,100` · **Artefak:**
`decisions/trailing-policy-20260929T103945Z.json` · **Dijalankan:** 29 Sep 2026 ±10:39Z
**Lanjut dari:** [[06-Results/23 - Gerbang Trailing]] (gerbang algebra) · **Bagian dari:**
[[08-Backlog/03 - Epik Teori Baru]] T2

## 1. Yang ditest

Semua lengan dieksekusi pada **posisi yang sama** (332 posisi dengan jalur >= 1 bar), hanya aturan
keluarnya yang beda, dengan `C` = 59,0 bps ongkos round-trip terukur dipotong di semua lengan dan
`gap` (fill menembus level) dijalankan 0 dan 100 bps:

| lengan | mean winso | median | P(≥+500) | **P(≤−200)** | positif | delta med vs A2 | CI delta |
|---|---|---|---|---|---|---|---|
| A2 tanpa aturan (ujung jalur) - **baseline pairing** | −175,1 | −104,2 | 32,8 % | 46,4 % | 40,4 % | - | - |
| A tahan 30 m - referensi | −182,5 | −79,6 | 31,6 % | 46,1 % | 41,6 % | - | - |
| C trailing 60 bps (terus-armed) | −1,6 | −76,8 | 31,3 % | 43,1 % | 42,5 % | **+73,4** | −1350..+428 |
| C trailing 120 bps | −16,1 | −75,4 | 31,6 % | 44,3 % | 42,2 % | +53,1 | −1375..+402 |
| **D trailing 120 BERSYARAT** (baru armed setelah menutup ongkos) | **+105,2** | **+34,0** | 37,3 % | **35,2 %** | **51,8 %** | +0,0 | −1072..+358 |
| E statis −60 dr masuk (placebo C) | −309,4 | −321,9 | 22,9 % | 56,6 % | 28,6 % | +0,0 | −1314..+142 |
| F statis-arm≥biaya (placebo D) | −243,3 | −224,4 | 26,8 % | 52,1 % | 33,7 % | +0,0 | −326..+61 |
| G d + armed diacak (placebo gabungan) | +42,6 | −59,0 | 35,4 % | 40,4 % | 45,5 % | - | - |
| B keluar waktu **acak** (kontrol F-D40) | −110,8 | −66,6 | 33,1 % | 44,1 % | 43,1 % | tak berpasangan | |

## 2. Angka yang paling penting di halaman ini bukan di tabel

**25 dari 28 lengan punya delta median tepat 0,0.** Artinya: pada **1-4 bar per jam**, sebagian
besar posisi **tidak pernah melihat level stopnya** - harga menembus ke bawah di antara dua rekaman
kami, dan bar berikutnya sudah jauh di bawah. Aturan yang tidak bisa tersentuh oleh data tidak bisa
dinilai dengan data itu.

Diagnosisnya dijalankan langsung di alatnya (jalur dijarangkan tiap baris ke-k):

| step | A tahan 30 m | C trailing 120 | D BERSYARAT | D − C |
|---|---|---|---|---|
| 1 (density kami sekarang) | −182,5 | −16,1 | **+105,2** | +121,3 |
| 2 (setengah bar) | −183,2 | −89,1 | **+9,2** | +98,3 |
| 4 (seperempat bar) | −183,0 | −184,1 | **−83,9** | +100,2 |

Baseline tidak bergerak (−183) karena ia hanya menyentuh dua titik; dua lengan yang bergantung pada
**menangkap puncak di tengah** runtuh ke baseline saat bar dijarangkan. Jadi keunggulan yang tampak
di baris D adalah **keunggulan resolusi**, bukan keunggulan kebijakan - dan urutan relatif
(D > C > A) tetap ada karena kedua lengan berbagi kelemahan yang sama.

## 3. Vonis

- **Tidak ada yang boleh dijual.** Vonis mekanis alat: BERSYARAT memang mengalahkan placebo-nya dan
  kontrol waktu-acak, tapi **CI bawah delta vs baseline = −1072 bps** (tidak > 0), dan mayoritas
  delta tepat nol karena levelnya tidak pernah terlihat.
- Yang *boleh* dikatakan, dan itu sesuai literatur: stop **mengubah bentuk** distribusi (P(≤−200)
  46,4 % → 35,2 %; persen posisi positif 40,4 % → 51,8 %) - bukan harapan. Lei & Li 2009:
  risikonya yang turun, return-nya tidak.
- **P49 berubah status: BLOCKED-BY-DATA.** E17 tidak butuh "belum sempat", ia butuh bar yang lebih
  rapat dari 1-4/jam. Itu pekerjaan yang sama dengan P40 (jalur kabar→order dalam 2 menit): tanpa
  tick/streaming, semua uji exit-dinamis di repo ini adalah simulasi atas data yang tidak bisa
  menyentuh aturannya.
- Batas yang menempel: `gap` 0/100 bps adalah parameter (belum ada `i` terukur - P45), jendela jalur
  60 m, dan harga dari ticker `wp` (bukan tick bursa).

## 4. Cara menjalankan

```bash
python -X utf8 tools/trailing_policy.py --self-test    # memotong kejatuhan, TIDAK memotong tren,
                                                       # deterministik (tanpa intip masa depan)
python -X utf8 tools/trailing_policy.py --gap 0,100
python -X utf8 tools/trailing_gate.py                  # gerbang algebra (F-D48)
```

**Terkait:** [[06-Results/23 - Gerbang Trailing]] · [[06-Results/19 - Umur Posisi]] ·
[[06-Results/21 - Rem di Horison Cepat]] · [[08-Backlog/04 - Riset Teori (Sitasi)]] S6/S7 ·
[[00-Overview/03 - Decisions]] F-D48/F-D49 · [[TradingKnowledge/FD7 - Invalidation Stop dan Time-Stop]]
