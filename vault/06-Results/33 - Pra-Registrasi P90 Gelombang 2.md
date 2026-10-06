---
tags: [results, pra-registrasi, "P90"]
---

# 33 - Pra-Registrasi P90 Gelombang 2 (setel G8 + K2 pada set setel, konfirmasi pada set baru)

**Bagian dari:** [[06-Results/00 - Hub Results]]
**Sumber:** `tools/riset_p90_g2.py` (konstanta `PROTOKOL2`) · tes `engine/tests/test_riset_p90_g2.py` · rencana riset [[08-Backlog/08 - Riset Optimasi Ambang]] §2 (aturan main) · keputusan builder [[00-Overview/03 - Decisions]] F-D126

> **STATUS: PRA-REGISTRASI, BELUM ADA HASIL.** Halaman ini ditulis dan di-push SEBELUM satu pun pasar gelombang 2 dijalankan. Satu-satunya lari sebelumnya adalah pilot WAKTU (benih 9.500.000+, di luar semua
> benih protokol; vonisnya tidak dicetak): 1,1-2,5 detik per pasar pada 6 pasar contoh. Hasil akan ditulis di halaman terpisah dengan sha protokol yang sama; penyimpangan dipajang di sana.

**sha protokol:** `0x4587f1efc4c418ed0b3d6873ed86e3cc922278e5c1250e1d777d206e8b7e2140` (`python -X utf8 tools/riset_p90_g2.py protokol`; dikunci tes `test_protocol_is_the_registered_one`). Cap waktu yang tidak bisa kami atur = waktu push commit halaman ini ke GitHub.

**Builder:** *"P90 gas"* (6 Okt malam, F-D126). Gelombang 1 ([[06-Results/31 - Pra-Registrasi P90 R1+R2]], [[06-Results/32 - Hasil P90 R1+R2]]) mengukur gerbang apa adanya dan TIDAK menyetel; halaman ini adalah protokol baru yang ia syaratkan.

## Apa yang diukur, dengan bahasa biasa

Gelombang 1 menemukan gerbang kita **konservatif**: bot tanpa keunggulan lolos hanya ±1 % (anggaran A1 = 5 %), tetapi bot yang SUNGGUH bagus hanya lolos 20-39 % dari yang secara aritmetika mungkin (Sharpe 1, riwayat 6,7 tahun).
Dua gerbang paling banyak memakan daya: **G8** (placebo: bot harus mengalahkan versi dirinya yang diacak waktunya, dengan batas atas 95 % yang sengaja konservatif) dan **K2** (Calmar >= 0,5). Pertanyaan gelombang 2:
*bisakah dua ambang itu dilonggarkan sedikit tanpa melanggar anggaran positif-palsu 5 %, dan apakah hasilnya bertahan di pasar yang BELUM dipakai untuk memilihnya?* Ini bukan menyetel sampai bot kita lolos: tidak ada bot Fabius atau
penerbit di dalam riset, hanya pasar sintetik.

**Cara:** tiap pasar dijalankan SEKALI dengan ambang terkunci; yang direkam bukan hanya lolos/gagal tetapi dua angka mentah (batas atas placebo G8, Calmar K2). Dari angka itu 15 kombinasi ambang (5 untuk G8 x 3 untuk K2) dinilai
OFFLINE. Urutannya satu arah:

1. **Set SETEL** (benih baru; 3.000 pasar tanpa keunggulan + 3.200 pasar dengan keunggulan): aturan pilihan di bawah memilih SATU kandidat (atau menyatakan "tetap terkunci").
2. Pilihan dicetak ke `riset/p90/g2-pilihan.json` SEBELUM set konfirmasi dijalankan (konfirmasi menolak jalan tanpa berkas itu; tidak ada putaran setel kedua).
3. **Set KONFIRMASI** (benih baru lagi + satu keluarga dunia baru, "lompatan": 6.600 pasar tanpa keunggulan + 4.800 pasar dengan keunggulan): hanya kandidat terpilih diuji; hasil negatif dipublikasikan.

## Aturan keputusan (ditulis sebelum angka)

- **Layak (set setel):** positif-palsu per dunia (Wilson 95 %) batas atas <= 4 % (= anggaran 5 % dikurangi margin pengaman 1 poin terhadap optimisme pemenang) di SEMUA 5 dunia.
- **Skor:** rerata daya atas 16 sel (W1-iid / W4-faktor x universe 1 / 4 x Sharpe sebenarnya 1,0 / 1,5 x riwayat 1.400 / 2.434 hari).
- **Pilih:** layak dengan skor tertinggi; selisih <= 0,005 = seri -> yang lebih ketat. Bila kenaikan skor di atas ambang terkunci < 0,05 (mutlak): **tetap terkunci**, konfirmasi tidak dijalankan.
- **Konfirmasi:** positif-palsu batas atas <= 5 % di SEMUA 6 dunia (termasuk dunia baru) DAN kenaikan rerata daya >= 0,05 (mutlak, pasar yang sama). Keduanya terpenuhi -> **USULAN** kunci baru; selain itu **tetap terkunci**.
- **Tidak ada ambang yang berubah otomatis.** Apa pun hasilnya, perubahan = kunci baru atas kata builder (`engine.cli lock --write --supersede`, aturan riset #8). Hasil negatif dipublikasikan. Tidak ada "sekali lagi".

**Catatan penerapan:** di produksi G8 memakai alpha A1/k per pengajuan ke-k (`engine/anggaran.py::gate_params_for`); bila ada usulan terkonfirmasi, pengali c berlaku pada alpha itu dan skala per keluarga tetap. K2 tidak diskalakan per keluarga.

## Batas yang diketahui sebelum lari

G10 tidak diuji (tanpa petahana); B3/B4/B5 tidak diuji; dunia sintetik, tidak ada klaim tentang pasar nyata; K2 adalah KPI ekonomi, jadi mengendurkannya hanya dibenarkan oleh daya di dunia sintetik, bukan oleh toleransi risiko pelanggan
(R3 menjawab itu, belum jalan); aturan #9 (tidak menyetel dengan melihat kandidat luar yang antre): saat halaman ini ditulis tidak ada kandidat luar.

## Waktu dan perintah

Pilot 6 Okt: 1,1-2,5 detik per pasar contoh (universe kecil); gelombang 1 rata-rata ±4,9 detik per pasar positif-palsu. Perkiraan (BELUM diukur untuk gelombang ini): 17.600 pasar, ±1-1,5 jam pada 14 pekerja.

```
python -X utf8 tools/riset_p90_g2.py setel-fp ; python -X utf8 tools/riset_p90_g2.py setel-daya     # bisa dilanjutkan bila terputus
python -X utf8 tools/riset_p90_g2.py pilih                                                          # aturan pilihan -> riset/p90/g2-pilihan.json
python -X utf8 tools/riset_p90_g2.py konfirmasi-fp ; python -X utf8 tools/riset_p90_g2.py konfirmasi-daya
python -X utf8 tools/riset_p90_g2.py ringkas                                                        # -> riset/p90/g2-ringkasan.json
```

## Protokol lengkap (keluaran `tools/riset_p90_g2.py protokol`)

```json
{
 "nama": "P90 gelombang 2: setel G8 (placebo_max_p) dan K2 (min_calmar) pada set setel, konfirmasi pada set baru; pasar sintetik",
 "mengukur": "gerbang TERKUNCI (GateParams/KpiParams bawaan, n_trials = 2) dijalankan APA ADANYA, satu kali per pasar; direkam status tiap gerbang + G8 batas atas 95% p placebo + K2 Calmar; ambang kandidat dievaluasi offline: G8 lolos bila batas_atas <= c x A1, K2 lolos bila Calmar >= min_calmar, gerbang lain tetap seperti terukur",
 "tidak_menyetel": "tidak ada ambang yang berubah oleh gelombang ini; hasil terkonfirmasi hanya menjadi USULAN kunci baru atas kata builder (F-D126)",
 "ambang_terkunci": {
  "placebo_max_p": 0.05,
  "min_calmar": 0.5,
  "A1": 0.05
 },
 "kandidat": {
  "placebo_max_p_kali_A1": [
   1.0,
   1.25,
   1.5,
   1.75,
   2.0
  ],
  "min_calmar": [
   0.5,
   0.4,
   0.3
  ],
  "catatan": "15 kombinasi termasuk yang terkunci (c = 1, min_calmar 0,5); c > 1 ~ G8 mendekati uji nominal (batas atas 95% p placebo memang konservatif)"
 },
 "dunia": {
  "W1-iid": "r = 0.03 z, z ~ N(0,1) iid per aset",
  "W2-garch": "GARCH(1,1) per aset: h = w + 0.08 r^2 + 0.90 h, w = 0.03^2 x 0.02; z normal",
  "W3-ekor-t": "r = 0.03 t3 / sqrt(3) (t berderajat bebas 3, varians satu)",
  "W4-faktor": "faktor bersama rho 0.5; varians GARCH(0.08, 0.90) bersama dari return faktor; z t4 varians satu (faktor dan idiosinkratik)",
  "W5-rezim": "rezim volatilitas Markov bersama {0.015, 0.05}, peluang pindah 0.02 per hari; z normal",
  "W6-lompatan": "lompatan: r = sqrt(0.03^2 - 0.01 x 0.12^2) z + J, J = 0.12 z' dengan peluang 0.01 per hari (varians total 0.03^2; tanpa keunggulan); HANYA di set konfirmasi (keluarga generatif baru)"
 },
 "konfigurasi_fp": "sama dengan R1 gelombang 1: templat seragam {B1-TREND, B6-BOUNCE, B2-RS}; universe seragam {1, 4, 16} (B2-RS: 16); parameter seragam dari grid gelombang 1; satu bot per pasar",
 "setel": {
  "fp": {
   "dunia": [
    "W1-iid",
    "W2-garch",
    "W3-ekor-t",
    "W4-faktor",
    "W5-rezim"
   ],
   "pasar_per_dunia": 600,
   "hari": 1400,
   "seed": "61000000 + 100000 x indeks_dunia + i"
  },
  "daya": {
   "templat": "B1-TREND N = 60",
   "dunia": [
    "W1-iid",
    "W4-faktor"
   ],
   "universe": [
    1,
    4
   ],
   "s": [
    1.0,
    1.5
   ],
   "hari": [
    1400,
    2434
   ],
   "pasar_per_sel": 200,
   "seed": "81000000 + 10000 x indeks_sel + i (urutan sel: dunia, universe, s, hari)",
   "mu": {
    "W1-iid|1|1.0": 0.0021500099446232534,
    "W1-iid|1|1.5": 0.0030219690381890585,
    "W1-iid|4|1.0": 0.0011642581590203774,
    "W1-iid|4|1.5": 0.001657936698305621,
    "W4-faktor|1|1.0": 0.0018802597065242645,
    "W4-faktor|1|1.5": 0.0026673508675394736,
    "W4-faktor|4|1.0": 0.0014455601088131866,
    "W4-faktor|4|1.5": 0.002064785547955466
   },
   "injeksi": "sama dengan R2 gelombang 1: r_t aset a += mu bila c(t-1) > c(t-61)"
  }
 },
 "konfirmasi": {
  "fp": {
   "dunia": [
    "W1-iid",
    "W2-garch",
    "W3-ekor-t",
    "W4-faktor",
    "W5-rezim",
    "W6-lompatan"
   ],
   "pasar_per_dunia": 1100,
   "hari": 1400,
   "seed": "71000000 + 100000 x indeks_dunia + i"
  },
  "daya": {
   "sel": "sama dengan set setel",
   "pasar_per_sel": 300,
   "seed": "91000000 + 10000 x indeks_sel + i"
  }
 },
 "aturan_pilihan": {
  "layak": "kandidat layak bila di SET SETEL positif-palsu (lolos/600 per dunia, Wilson 95 %) batas atas <= A1 - 0.01 = 0.04 di SEMUA 5 dunia",
  "skor": "rerata daya atas 16 sel daya (bobot sama): W1-iid/W4-faktor x universe 1/4 x s 1,0/1,5 x hari 1400/2434",
  "pilih": "kandidat layak dengan skor tertinggi; selisih skor <= 0.005 = seri -> ambil yang lebih ketat (c lebih kecil, lalu min_calmar lebih besar)",
  "materialitas": "bila skor terpilih - skor terkunci < 0.05 (mutlak): TETAP ambang terkunci; konfirmasi tidak dijalankan",
  "satu_kali": "pilihan dicetak ke riset/p90/g2-pilihan.json SEBELUM set konfirmasi dijalankan; konfirmasi menolak jalan tanpa berkas itu; tidak ada putaran setel kedua"
 },
 "aturan_konfirmasi": {
  "fp": "kandidat terpilih: Wilson 95 % batas atas <= A1 = 0.05 di SEMUA 6 dunia (set konfirmasi, 1100 pasar per dunia, termasuk W6-lompatan)",
  "daya": "kenaikan rerata daya terpilih - terkunci >= 0.05 (mutlak, pasar yang sama) di 16 sel set konfirmasi",
  "vonis": "TERKONFIRMASI bila keduanya terpenuhi -> USULAN kunci baru atas kata builder; selain itu TETAP ambang terkunci (hasil negatif dipublikasikan)"
 },
 "aturan": [
  "pilot hanya mencetak waktu",
  "hasil negatif dipublikasikan",
  "penyimpangan dari protokol dipajang di halaman hasil",
  "tidak ada kandidat luar yang antre (aturan #9 riset P90)",
  "tidak ada 'sekali lagi'"
 ],
 "batas": [
  "G10 tidak diuji (tanpa petahana)",
  "B3/B4/B5 tidak diuji",
  "dunia sintetik; tidak ada klaim tentang pasar nyata",
  "K2 adalah KPI ekonomi: usulan mengendurkannya hanya dibenarkan oleh daya pada dunia sintetik, bukan oleh toleransi risiko pelanggan (R3)",
  "pada penerapan, G8 memakai alpha A1/k per pengajuan ke-k (`anggaran.gate_params_for`): c berlaku sebagai pengali alpha, skala per keluarga tetap"
 ]
}
```

**Terkait:** [[08-Backlog/08 - Riset Optimasi Ambang]] · [[06-Results/31 - Pra-Registrasi P90 R1+R2]] · [[06-Results/32 - Hasil P90 R1+R2]] · [[00-Overview/03 - Decisions]] F-D88 / F-D126 · [[04-Tools/TL8 - engine]]
