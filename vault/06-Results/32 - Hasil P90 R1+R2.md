---
tags: [results, "P90"]
---

# 32 - Hasil P90 R1+R2 (gerbang v1 pada pasar sintetik)

**Bagian dari:** [[06-Results/00 - Hub Results]]
**Pra-registrasi:** [[06-Results/31 - Pra-Registrasi P90 R1+R2]] · sha protokol `0xce2f814e334244f8e43c3d9d862b8e654896f3ba1772d20c9e4397e89f2820bd` (sama; dikunci tes)
**Perintah:** `python -X utf8 tools/riset_p90.py r1 | r2 | ringkas` · data mentah `riset/p90/r1.jsonl` (5.500 pasar), `riset/p90/r2.jsonl` (18.000), `riset/p90/ringkasan.json`,
`riset/p90/kalibrasi.json` · lari 3 Okt 14:56Z - 4 Okt ±01:00 WIB (R1 ±32 menit, R2 ±150 menit, 14 pekerja)

> Dunia sintetik. Ini mengukur PERILAKU GERBANG v1, bukan pasar nyata dan bukan bot Fabius. Tidak ada ambang yang berubah karena halaman ini.

## R1 - bot jelek lolos? (positif-palsu; aturan keputusan pra-registrasi)

| jenis pasar | lolos / 1.100 | positif-palsu | Wilson 95 % | vonis |
|---|---|---|---|---|
| W1 normal iid | 9 | 0,82 % | 0,43-1,55 % | **A1 TERPENUHI** |
| W2 GARCH | 9 | 0,82 % | 0,43-1,55 % | **A1 TERPENUHI** |
| W3 ekor tebal t3 | 13 | 1,18 % | 0,69-2,01 % | **A1 TERPENUHI** |
| W4 faktor bersama + GARCH + t4 | 9 | 0,82 % | 0,43-1,55 % | **A1 TERPENUHI** |
| W5 rezim volatilitas | 10 | 0,91 % | 0,49-1,67 % | **A1 TERPENUHI** |

**Vonis global (aturan pra-registrasi): v1 memenuhi A1 (<= 5 %) di semua jenis pasar** - batas atas tertinggi 2,01 %. Pemeriksa vonis ulang vs `gates.verdict`: 0 beda.

**Gerbang mana yang menyaring (buang satu gerbang):** hanya **G8 (placebo)** yang tergolong *penyaring* - tanpa G8 positif-palsu naik ke 1,91-2,45 %.
G3, G4, G5, K1-K3 *kecil* (tanpa G3: 1,00-1,64 %); G1, G2, G6, G7, G9, G10, K4, K5 *tidak menahan beban* di dunia ini (G10 memang tidak diuji: tanpa
petahana). Lolos per gerbang sendirian: G3 3,4-4,0 %, G8 3,0-3,5 % pasar.

## R2 - bot bagus lolos? (daya B1 N = 60, keunggulan terkalibrasi)

Kalibrasi (sebelum lari): Sharpe yang tercapai pada benih segar meleset 0,00-0,05 dari target (W4 sedikit di bawah, <= 1,8 galat baku) - `kalibrasi.json`.

Daya pada riwayat 6,7 tahun (2.434 hari; = riwayat B1 nyata), 300 pasar per sel:

| Sharpe sebenarnya | W1, 1 aset | W1, 4 aset | W4, 1 aset | W4, 4 aset | plafon aritmetika |
|---|---|---|---|---|---|
| 0,5 | 7,7 % | 9,3 % | 6,3 % | 10,0 % | 36,9 % |
| 0,75 | 15,0 % | 18,7 % | 10,0 % | 20,0 % | 60,2 % |
| 1,0 | 24,0 % | 33,3 % | 20,3 % | 38,7 % | 77,8 % |
| 1,5 | 35,3 % | 69,7 % | 27,0 % | 71,3 % | 93,7 % |
| 2,0 | 30,7 % | 91,3 % | 15,3 % | 88,7 % | 97,9 % |

Riwayat 3,8 tahun (1.400 hari), Sharpe 1,0: 11,7 / 24,7 / 6,3 / 23,3 % (plafon 60,1 %).

**Vonis (aturan pra-registrasi): *gerbang memakan daya*** - efisiensi (daya / plafon) < 0,5 pada s >= 1 dan 6,7 tahun di W1: 1 aset s = 1,0 (0,31), 1,5 (0,38),
2,0 (0,31); 4 aset s = 1,0 (0,43). Pada 4 aset s >= 1,5 efisiensinya 0,74-0,93.

**Penyebab (analisis TAMBAHAN, tidak dipra-registrasi):** gagal per gerbang pada 2.434 hari: **G8** gagal di 55-85 % pasar ber-edge pada s <= 1, K2 (Calmar)
21-76 %, G3 19-69 %. Pada 1 aset dengan s >= 1,5 penyebab terbesar menjadi **K3** (minimal sinyal per tahun; 27-69 %): keunggulan kuat membuat B1 satu aset
hampir terus long, jadi ia jarang berganti posisi - itu syarat PRODUK (Fabius butuh sinyal untuk dijual), bukan uji statistik; itulah sebabnya daya 1 aset
TIDAK naik dari s 1,5 ke 2,0.

## Penyimpangan dari protokol (dipajang)

1. **Sel riwayat 1.095 hari tidak mengukur daya.** Daya 0,0 % di 6.000 dari 6.000 pasar karena **G2 gagal di semuanya**: pasar 1.095 hari menghasilkan kurang
   dari 1.095 hari PnL (hari pertama tanpa return), sedangkan G2 menuntut >= 1.095. Protokol memilih T = 1.095 sebagai "syarat minimum G2" tanpa memeriksa
   ini. Angka 0 % di sel itu BUKAN temuan daya; temuan yang sah: riwayat minimum efektif G2 = 1.096 hari bar.
2. Waktu R2 ±150 menit (perkiraan pilot ±35 menit); tidak mengubah hasil.

## Pembacaan jujur

- **v1 konservatif:** positif-palsu ±1 % dari anggaran 5 %, dan daya pada edge realistis (Sharpe 1, 6,7 tahun) 20-39 % dari plafon 78 %. Ada **ruang anggaran**:
  gerbang bisa dilonggarkan untuk menambah daya sambil tetap <= 5 %. Tuasnya terlihat: G8 (satu-satunya penyaring dan pemakan daya terbesar), lalu K2.
- **Itu BUKAN keputusan.** Melonggarkan = menyetel. Aturan riset #4: set setel != set konfirmasi, protokol baru dipra-registrasi, kunci v2 atas kata
  builder. Gelombang 2 (usulan): setel `placebo_max_p` (dan mungkin `min_calmar`) pada benih setel, konfirmasi pada benih baru, target positif-palsu Wilson
  atas <= 5 % di kelima dunia sambil memaksimalkan daya.
- Batas: dunia sintetik; B1/B6/B2 saja; G10 tidak diuji; keunggulan R2 berbentuk drift bersyarat untuk B1 (bentuk lain belum diuji).

**Terkait:** [[08-Backlog/08 - Riset Optimasi Ambang]] · [[06-Results/31 - Pra-Registrasi P90 R1+R2]] · [[00-Overview/03 - Decisions]] F-D88 / F-D90
