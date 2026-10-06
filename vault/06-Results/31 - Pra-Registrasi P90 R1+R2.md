---
tags: [results, pra-registrasi, "P90"]
---

# 31 - Pra-Registrasi P90 R1+R2 (gerbang v1 pada pasar sintetik)

**Bagian dari:** [[06-Results/00 - Hub Results]]
**Sumber:** `tools/riset_p90.py` (konstanta `PROTOKOL`) · rencana riset [[08-Backlog/08 - Riset Optimasi Ambang]] §2 (aturan main) dan §4 (R1, R2)

> **STATUS: PRA-REGISTRASI, BELUM ADA HASIL.** Halaman ini ditulis dan di-push 3 Okt 2026 malam SEBELUM lari R1/R2 sungguhan dan sebelum kalibrasi R2.
> Satu-satunya lari sebelumnya adalah pilot WAKTU (benih 9.000.000+, di luar semua benih protokol; vonisnya tidak dicetak): ±1,3-4,0 detik per pasar.
> Hasil akan ditulis di halaman terpisah, dengan sha protokol yang sama; penyimpangan dipajang di sana.

**sha protokol:** `0xce2f814e334244f8e43c3d9d862b8e654896f3ba1772d20c9e4397e89f2820bd` (`python -X utf8 tools/riset_p90.py protokol`). Cap waktu yang tidak bisa
kami atur = waktu push commit halaman ini ke GitHub.

**Builder:** *"P90 udh mantap ... Gas eksekusi"* (3 Okt malam; nomor keputusan aslinya dicabut 6 Okt, lihat F-D126).

## Apa yang diukur, dengan bahasa biasa

- **R1 - bot jelek lolos?** 5 jenis pasar buatan TANPA keunggulan apa pun (normal, volatilitas berkelompok, ekor tebal, faktor bersama, rezim volatilitas),
  1.100 pasar per jenis, satu bot acak per pasar (B1/B6/B2, universe 1/4/16 aset, parameter acak dari grid) = satu pengajuan jujur. Berapa persen yang lolos
  gerbang v1 yang terkunci? Anggaran A1 (F-D88) = paling banyak 5 %. Juga: gerbang mana yang benar-benar menyaring (buang satu gerbang, lihat naiknya).
- **R2 - bot bagus lolos?** Pasar buatan yang diberi keunggulan B1 (N = 60) dengan Sharpe sebenarnya yang diketahui (0,5 / 0,75 / 1 / 1,5 / 2, sesudah biaya),
  riwayat 3,0 / 3,8 / 6,7 tahun, 1 dan 4 aset, 300 pasar per sel. Berapa peluang lolos, dibanding plafon aritmetika (§1 halaman riset)?

## Aturan keputusan (ditulis sebelum angka)

- **R1 per jenis pasar:** positif-palsu = lolos / 1.100, selang Wilson 95 %. *A1 TERPENUHI* bila batas atas <= 5 %; *A1 DILANGGAR* bila batas bawah > 5 %; selain
  itu *TIDAK TEGAS*. **Global:** v1 memenuhi A1 hanya bila SEMUA jenis pasar *A1 TERPENUHI*.
- **R1 per gerbang (buang satu):** *penyaring* bila positif-palsu naik >= 1 poin persen di setidaknya satu jenis pasar; *tidak menahan beban* bila tidak berubah di
  semua jenis pasar.
- **R2:** daya per sel + Wilson 95 %; efisiensi = daya / plafon. *Gerbang memakan daya* bila efisiensi < 0,5 pada s >= 1 dan riwayat 6,7 tahun di pasar normal.
- **Tidak ada ambang yang berubah otomatis.** Apa pun hasilnya, mengubah ambang = protokol baru (set setel != set konfirmasi) + kunci v2 atas kata builder.
  Hasil negatif dipublikasikan.

## Batas yang diketahui sebelum lari

G10 tidak diuji (tanpa petahana); B3/B4/B5 tidak diuji (butuh funding/spot/event sintetik) - gelombang berikut; R4 (penambang yang mencoba banyak
konfigurasi) tidak di gelombang ini; dunia sintetik = tidak ada klaim tentang pasar nyata.

## Protokol lengkap (keluaran `tools/riset_p90.py protokol`)

```json
{
 "v": 1,
 "nama": "P90 gelombang 1: R1 positif-palsu + R2 daya, gerbang v1 TERKUNCI, pasar sintetik",
 "mengukur": "GateParams/KpiParams bawaan = kunci v1 (engine.cli lock: TERKUNCI); n_trials = 2 (formulir minimum percobaan 1 + 1, seperti review pada k = 1 keluarga)",
 "tidak_menyetel": "gelombang ini tidak mengubah satu ambang pun; perubahan = protokol baru dengan set setel != set konfirmasi + kunci v2 atas kata builder",
 "harga": {
  "return": "aritmetik harian, rerata 0 di bawah nol, dipotong >= -0.95",
  "vol_harian": 0.03,
  "T0": "2020-01-01T00:00Z",
  "biaya": "penggaris spesifikasi templat (7 bps per sisi)",
  "funding": 0,
  "simbol": "PERP_UNIVERSE urutan engine, k pertama"
 },
 "dunia": {
  "W1-iid": "r = 0.03 z, z ~ N(0,1) iid per aset",
  "W2-garch": "GARCH(1,1) per aset: h = w + 0.08 r^2 + 0.90 h, w = 0.03^2 x 0.02; z normal",
  "W3-ekor-t": "r = 0.03 t3 / sqrt(3) (t berderajat bebas 3, varians satu)",
  "W4-faktor": "faktor bersama rho 0.5; varians GARCH(0.08, 0.90) bersama dari return faktor; z t4 varians satu (faktor dan idiosinkratik)",
  "W5-rezim": "rezim volatilitas Markov bersama {0.015, 0.05}, peluang pindah 0.02 per hari; z normal"
 },
 "r1": {
  "dunia": [
   "W1-iid",
   "W2-garch",
   "W3-ekor-t",
   "W4-faktor",
   "W5-rezim"
  ],
  "pasar_per_dunia": 1100,
  "hari": 1400,
  "seed": "31000000 + 100000 x indeks_dunia + i",
  "konfigurasi": "satu per pasar (pengajuan jujur satu kali), diundi dari rng pasar itu: templat seragam {B1-TREND, B6-BOUNCE, B2-RS}; universe seragam {1, 4, 16} (B2-RS: 16, min_aset 8); parameter seragam dari grid",
  "grid": {
   "B1-TREND": [
    5,
    7,
    10,
    14,
    20,
    30,
    45,
    60,
    90,
    120
   ],
   "B6-BOUNCE": [
    5,
    7,
    10,
    14,
    20,
    30,
    45,
    60
   ],
   "B2-RS": [
    7,
    14,
    21,
    28,
    42,
    56,
    90
   ]
  },
  "keluaran": "per pasar: status tiap gerbang G1-G11 + K1-K5, Sharpe, persentil bootstrap, vonis gates.verdict",
  "aturan_keputusan": {
   "per_dunia": "FP = lolos/1100, Wilson 95%: 'A1 TERPENUHI' bila batas atas <= 0.05; 'A1 DILANGGAR' bila batas bawah > 0.05; selain itu 'TIDAK TEGAS'",
   "global": "v1 memenuhi A1 bila semua dunia 'A1 TERPENUHI'",
   "leave_one_gate_out": "FP tanpa gerbang g (gerbang wajib lain tetap): 'penyaring' bila naik >= 0.01 absolut di >= 1 dunia; 'tidak menahan beban' bila sama di semua dunia"
  }
 },
 "r2": {
  "dunia": [
   "W1-iid",
   "W4-faktor"
  ],
  "templat": "B1-TREND N = 60",
  "s": [
   0.5,
   0.75,
   1.0,
   1.5,
   2.0
  ],
  "hari": [
   1095,
   1400,
   2434
  ],
  "universe": [
   1,
   4
  ],
  "pasar_per_sel": 300,
  "seed": "41000000 + 10000 x indeks_sel + i (urutan sel: dunia, universe, s, hari)",
  "injeksi": "r_t aset a += mu bila c(t-1) > c(t-61) aset itu (keunggulan yang dieksploitasi B1 N = 60)",
  "kalibrasi": "mu per (dunia, universe, s): grid mu 0..0.012 langkah 0.0005, benih sama (CRN) 20 pasar x 36500 hari, Sharpe NET B1 rata-rata, interpolasi linear; s tercapai diverifikasi pada 20 pasar x 36500 hari benih segar (seed 52000000+), dilaporkan",
  "kalibrasi_seed": 51000000,
  "plafon": "run14: daya = 1 - Phi((1.645 - s sqrt(T)) / sqrt(1 + s^2/2))",
  "aturan_keputusan": "daya per sel + Wilson 95%; efisiensi = daya / plafon; 'gerbang memakan daya' bila efisiensi < 0.5 pada s >= 1.0 dan T = 2434 di W1-iid. Tidak ada ambang yang berubah otomatis (A3 belum ditetapkan)."
 },
 "aturan": [
  "pilot hanya mencetak waktu",
  "hasil negatif dipublikasikan",
  "penyimpangan dari protokol dipajang di halaman hasil",
  "tidak ada kandidat luar yang antre (aturan #9)"
 ],
 "batas": [
  "G10 tidak diuji (tanpa petahana)",
  "B3/B4/B5 tidak diuji (butuh funding/spot/event sintetik) - gelombang berikut",
  "dunia sintetik; tidak ada klaim tentang pasar nyata",
  "R4 (penambang/oracle) tidak di gelombang ini"
 ]
}
```

**Terkait:** [[08-Backlog/08 - Riset Optimasi Ambang]] · [[00-Overview/03 - Decisions]] F-D88 / F-D126 · [[04-Tools/TL8 - engine]]
