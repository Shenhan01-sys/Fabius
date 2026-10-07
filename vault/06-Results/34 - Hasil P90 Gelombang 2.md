---
tags: [results, "P90"]
---

# 34 - Hasil P90 Gelombang 2 (setel G8 + K2, konfirmasi di set baru)

**Bagian dari:** [[06-Results/00 - Hub Results]]
**Pra-registrasi:** [[06-Results/33 - Pra-Registrasi P90 Gelombang 2]] · sha protokol `0x4587f1efc4c418ed0b3d6873ed86e3cc922278e5c1250e1d777d206e8b7e2140` (dicek ulang sebelum lari; dikunci tes)
**Perintah:** `python -X utf8 tools/riset_p90_g2.py setel-fp | setel-daya | pilih | konfirmasi-fp | konfirmasi-daya | ringkas` (4 pekerja) · data mentah `riset/p90/g2-setel-fp.jsonl` (3.000), `g2-setel-daya.jsonl` (3.200), `g2-pilihan.json`, `g2-konfirmasi-fp.jsonl` (6.600), `g2-konfirmasi-daya.jsonl` (4.800), `g2-ringkasan.json` · lari 7 Okt 01:19Z - 03:03Z

> Dunia sintetik. Ini mengukur PERILAKU GERBANG, bukan pasar nyata dan bukan bot Fabius. **Tidak ada ambang yang berubah karena halaman ini**: hasilnya USULAN kunci baru atas kata builder (F-D126).

## Urutan satu arah (dipajang dengan cap waktu GitHub)

1. Set SETEL lengkap -> `pilih` -> `g2-pilihan.json` di-commit + di-push (`659d998`, 7 Okt 01:53Z) SEBELUM satu pun pasar konfirmasi dijalankan.
2. Set KONFIRMASI (benih baru + dunia baru W6-lompatan) -> `ringkas`. Pemeriksa konsistensi (vonis ambang terkunci dari statistik mentah = vonis resmi gerbang): **0 beda** di kedua set.

## Set setel: pilihan

Semua 15 kandidat LAYAK (Wilson atas <= 4 % di 5 dunia; tertinggi 3,5 %). Skor daya naik monoton dengan c (pengali placebo): terkunci 0,3138 -> c 2,0 / K2 0,4 **0,4128**; c 2,0 / K2 0,3 = 0,4150 seri (selisih <= 0,005) -> aturan memilih yang lebih ketat. **Terpilih: `placebo_max_p` 0,10 (c = 2,0 x A1), `min_calmar` 0,40**, kenaikan +0,0991 (>= 0,05 = material) -> konfirmasi dijalankan.

## Set konfirmasi: vonis

| dunia | positif-palsu terpilih | Wilson 95 % atas | terkunci |
|---|---|---|---|
| W1 iid | 1,36 % | 2,24 % | 0,91 % |
| W2 GARCH | 1,45 % | 2,35 % | 1,00 % |
| W3 ekor t3 | 1,45 % | 2,35 % | 1,09 % |
| W4 faktor | 0,82 % | 1,55 % | 0,55 % |
| W5 rezim | 1,45 % | 2,35 % | 0,82 % |
| W6 lompatan (BARU) | 1,36 % | 2,24 % | 1,36 % |

Daya rerata 16 sel: **terpilih 0,4096 vs terkunci 0,3096 (+0,1000; syarat >= 0,05)**; positif-palsu semua 6 dunia <= 5 %: ya.
**VONIS (aturan pra-registrasi): TERKONFIRMASI -> USULAN kunci baru `placebo_max_p` = 0,10, `min_calmar` = 0,40.**

Daya per sel (lolos / 300), terpilih vs terkunci:

| sel (dunia, aset, Sharpe, hari) | terpilih | terkunci |
|---|---|---|
| W1, 1, 1,0, 1400 / 2434 | 15,7 % / 37,0 % | 8,7 % / 26,7 % |
| W1, 1, 1,5, 1400 / 2434 | 21,0 % / 40,7 % | 13,3 % / 30,3 % |
| W1, 4, 1,0, 1400 / 2434 | 29,0 % / 48,3 % | 19,7 % / 36,0 % |
| W1, 4, 1,5, 1400 / 2434 | 59,7 % / 80,3 % | 46,7 % / 69,0 % |
| W4, 1, 1,0, 1400 / 2434 | 12,7 % / 29,0 % | 5,7 % / 18,7 % |
| W4, 1, 1,5, 1400 / 2434 | 18,0 % / 35,0 % | 10,7 % / 28,3 % |
| W4, 4, 1,0, 1400 / 2434 | 33,7 % / 51,0 % | 24,0 % / 37,3 % |
| W4, 4, 1,5, 1400 / 2434 | 62,7 % / 81,7 % | 49,3 % / 71,0 % |

## Pembacaan jujur (TIDAK dipra-registrasi, untuk keputusan builder)

- **Hampir seluruh kenaikan datang dari G8.** Di konfirmasi, K2 0,5 -> 0,4 pada c 2,0 hanya +0,005 (0,4042 -> 0,4096); K2 0,3 +0,001 lagi. Melonggarkan K2 = ekonomi (KPI), bukan statistik; builder boleh mengambil G8 saja.
- **Pilihan jatuh di TEPI grid** (c = 2,0 terbesar yang diuji); skor masih naik di tepi. Itu bukan izin mencoba c lebih besar: gelombang ini tidak boleh diputar ulang (aturan "tidak ada sekali lagi"); c > 2 butuh protokol baru.
- **Harga yang dibayar:** positif-palsu naik ±0,3-0,6 poin per dunia (tertinggi 1,45 %, Wilson atas 2,35 %), masih jauh di bawah anggaran A1 5 %.
- **c 2,0 berarti G8 mendekati uji nominal**: batas atas 95 % p placebo <= 0,10 kira-kira setara p titik <= 0,05; yang dilonggarkan adalah sabuk pengaman batas atas, bukan alpha.
- Batas yang tetap: dunia sintetik; hanya B1 / B6 / B2; G10 tidak diuji; keunggulan berbentuk drift bersyarat B1; di produksi G8 memakai alpha A1/k per pengajuan ke-k, jadi c berlaku pada alpha itu.

## Penyimpangan dari protokol (dipajang)

1. 4 pekerja, bukan 14 (lingkungan sesi); hanya waktu (1 jam 44 menit dinding), tidak mengubah hasil.
2. Set setel positif-palsu dihentikan dan dilanjutkan sekali (insiden `git stash`, [[Conventions]]): data diselamatkan dari handle proses, berkas di disk terbukti awalan data itu, 924 pasar sisanya dijalankan dengan benih yang sama (lari bisa dilanjutkan oleh rancangan); 3.000 baris unik, konsistensi 0 beda.

**Langkah berikut = kata builder:** kunci baru lewat `engine.cli lock --write --supersede` (aturan riset #8) atau tetap terkunci ([[08-Backlog/13 - Langkah Builder Tertunda]] LB14).

**Terkait:** [[06-Results/33 - Pra-Registrasi P90 Gelombang 2]] · [[06-Results/32 - Hasil P90 R1+R2]] · [[08-Backlog/08 - Riset Optimasi Ambang]] · [[00-Overview/03 - Decisions]] F-D88 / F-D126
