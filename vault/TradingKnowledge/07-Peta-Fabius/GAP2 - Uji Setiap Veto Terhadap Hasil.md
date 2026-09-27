---
tags: [tk, tk-peta, "GAP2"]
---

# GAP2 - Uji Setiap Veto Terhadap Hasil

**Keluarga:** [[00 - Hub Peta Fabius]] · **Tahap:** penilaian ([[PL6 - Menilai Hasil]])
**Sumber:** [[06-Results/02 - Thresholds]] (daftar ambang + status "diputuskan, bukan diukur"),
[[Fakta Terukur]] §E (ambang) + §F (corong outcome yang **sudah** dihitung)

**Ringkas:** tujuh ambang penyaring universe Fabius **diputuskan**, bukan **diuji** — dan angka
pembandingnya ternyata **sudah pernah dihitung**: `tools/screen_universe.py` mencetak kohort lolos
vs ditolak. Hasilnya tidak mendukung kita: kohort **ditolak** justru mean-nya lebih tinggi
(**+353,7 bps**, n=713) daripada kohort **lolos** (**+148,0 bps**, n=52); medians berlawanan arah
(−44,4 vs +35,9), dan mean itu digerakkan ekor (`best` **+213.686,5 bps**). Jadi halaman ini bukan
lagi "rancangkan uji yang belum ada" — ini **"apa yang harus dilakukan dengan angka yang sudah ada
dan arah yang salah"**: mean jangan dipakai sebagai putusan, medians jangan dibaca tanpa bootstrap,
dan uji yang sah harus memakai ongkos terukur kita, bukan 20 bps warisan yang dipakai report itu.

## Definisi yang bisa dihitung

Untuk satu veto `v` dan satu jendela snapshot `w`:

```
Ditolak(v,w) = token yang gugur HANYA karena v (atau kelompok yang v-nya satu-satunya beda)
Lolos(v,w)   = token yang lolos semua veto di jendela yang sama
outcome(tok) = return bersih 24 jam pada harga YANG KAMI CATAT SENDIRI, minus ongkos
hipotesis    = median outcome(Ditolak) < median outcome(Lolos)   (satu arah)
```

Yang dilarang: membandingkan `Ditolak` dengan "semua yang lain" termasuk token yang gugur karena
sebab lain — itu mengukur campuran, bukan veto. Dan yang paling dilarang: menghitung `outcome`
dengan asumsi token yang hilang harganya nol **dan** sekaligus memasukkannya ke `Lolos`.

## Cara pakai yang diklaim

"Pakai veto yang sudah terbukti memprediksi rugi; cabut yang tidak." Bentuk klaimnya benar secara
bentuk tapi menuntut dua hal yang belum kita punya: hasil jatuh tempo dalam jumlah cukup, dan
harga forward untuk token yang **ditolak** (persis kelompok yang paling sulit dihargai — lihat
`## Batas`).

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| snapshot universe per jam + field perilaku per token | `ADA` | `universe/bsc-universe.jsonl`, skema 4, ambang **ikut dinormalkan di baris** supaya bisa dihitung ulang ([[03-Data/D5 - Record Schemas]]) |
| tally alasan penolakan | `ADA` | `top_reasons`, `survivable_count`, `fully_evaluated_count` per snapshot |
| harga forward untuk aset **ber-kontrak perp** | `ADA` | Aster 9.599 bar 1 j ≈ 400 hari ([[Fakta Terukur]] §A) |
| harga forward untuk token yang **tidak** punya perp | `ADA-TAPI` | baris `px` dari perekam ⑦ — **27.886 baris / 1.607 token** pada ekor `origin/master` ([[Fakta Terukur]] §B); jangkauannya seumur perekam, bukan 400 hari |
| hasil "rug / tidak bisa dijual" | `ADA-TAPI` | `security-*.jsonl` (`is_honeypot`, `can_not_sell`) dibaca live; tidak ada histori keadaan itu |
| pemisah "ditolak" vs "tidak bisa dinilai" | `ADA` | `tools/decide.py` memulangkan `risk_vetoes` vs `data_gaps` setelah terukur **37 baris tanpa field perilaku, 13 gugur tanpa satu pun alasan risiko** — angkanya ada di [[Fakta Terukur]] §A.3 |
| **kohort lolos vs ditolak yang sudah dihitung** | `ADA-TAPI` | `tools/screen_universe.py` → `tools/out/screen_report.json`: §F memuat mean/median per kelompok **dan per alasan**; batasnya tercetak di report itu sendiri: "bukan trade yang bisa dieksekusi · tanpa slippage nyata · tanpa ukuran posisi · **bukan prediksi return**". `out/` **di-gitignore** → artefaknya tidak ikut clone, perintahnya ada |

## Uji di Fabius

Urutan yang sah, semuanya tanpa biaya data:

1. Bangun pasangan `(token, jendela)` hanya dari skema **≥ 3** (veto `not_a_choosable_asset` lahir
   di skema 3; baris skema 2 tidak sebanding — aturan di [[03-Data/D5 - Record Schemas]]).
2. Pisahkan tiga kelompok: `Lolos`, `Ditolak-karena-v-saja`, `Tidak-bisa-dinilai`. Kelompok ketiga
   **tidak masuk** perbandingan apa pun.
3. `outcome` dari baris `px` kami sendiri (dan `Aster` untuk yang punya perp), horizon 24 j,
   ongkos **59 bps** ([[Fakta Terukur]] §D) — jangan pakai 20 bps warisan sambil menyebut hasil
   "bersih".
4. Uji: selisih median + bootstrap, `n ≥ 20` **per kelompok**, koreksi BH α 0,10 **lintas ketujuh
   veto** (ini tujuh tes, bukan satu — lihat [[EV3 - Signifikansi dan Multiple Testing]]).
5. Output mendarat di `decisions/veto-calibration-<UTC>.json` + satu baris per veto di
   [[06-Results/02 - Thresholds]]: **dipertahankan dengan bukti**, **dicabut dengan bukti**, atau
   **tetap diputuskan** (jujur: belum teruji).

**Sudah ada** (jangan dihitung ulang dengan nama lain): funnel outcome per alasan + tally BH
(`tools/screen_universe.py` → `tools/out/screen_report.json`; 5 dari 105 tes keluarga lolos pada
α 0,10 — dan itu keluarga tes alat itu, bukan tujuh veto kita).

**Belum ada** (`tools/veto_study.py` = belum ditulis): langkah 1–5 di atas dengan ongkos **59 bps**,
median sebagai statistik utama + bootstrap, dan **satu keputusan tercatat per veto**. Report yang
ada memakai `RT_COST_BPS = 20` (P10 ditutup 28 Sep; sebelum itu `RT_COST_BPS = 20` - lihat [[Fakta Terukur]] §D) — jadi ia tidak bisa ditutup
dengan menekan tombol yang sama; itu alasan langkah 5 harus alat baru, bukan hasil lama.

## Batas dan mode gagal

- **Yang dibuang justru yang paling ingin kita nilai.** `MIN_AGE_SEC` (24 jam) membuang token yang
  paling sering mati sebelum 24 jam — kelompok yang hasilnya paling ingin kita tahu. Untuk veto
  ini, "tidak bisa diuji" adalah jawaban yang sah, bukan pekerjaan yang tertunda.
- **Token yang hilang dari feed ≠ token yang rugi.** Bisa mati, bisa keluar jendela ⑦, bisa
  kebanjiran symbol lain. Mengasumsikan salah satu arah = memilih kesimpulan sebelum mengukur
  ([[Concepts/Unmeasured Is Not Clean]]).
- **Kelompok kecil.** Untuk `MAX_BUNDLER` dan `MIN_LOCK` kita mungkin tidak pernah punya `n ≥ 20`
  per kelompok pada jendela yang sama — laporkan itu, jangan turunkan ambangnya diam-diam.
- **Mean di sini bukan putusan.** Ekor kohort ditolak menarik rata-ratanya ke atas
  (`best_bps` **+213.686,5** untuk satu token): mean **+353,7** bukan berarti "yang kita tolak
  biasanya untung", melainkan "beberapa ledakan menutupi yang lain". Median dua kelompok justru
  berlawanan arah (**−44,4** vs **+35,9**) — dan tidak satu pun dari itu boleh dikutip tanpa
  interval. Yang sah: bootstrap atas median, bukan perbandingan mean.
- **Alat ukurnya sendiri bilang bukan prediksi.** Empat batas tercetak di report: bukan trade yang
  bisa dieksekusi, tanpa slippage nyata, tanpa ukuran posisi, bukan prediksi return. Memakainya
  sebagai vonis veto = meminjam angka alat untuk kalimat yang alat itu tolak.
- **Veto boleh jadi benar tapi tidak berguna.** Kalau semua yang ditolak `MIN_VOL_OVER_LIQ` ternyata
  rugi tapi tidak ada satu pun kandidat kita yang kena, veto itu tidak mengubah keputusan apa pun
  dan cuma menambah rasa aman.

## Tingkat bukti

`T1` untuk ketujuh ambang (diputuskan, dipakai, **belum diuji dengan uji yang sah**) ·
`T3` **hanya** untuk fakta bahwa perbandingan kohortnya sudah pernah dijalankan dan bisa dicetak
ulang (`tools/screen_universe.py`) — **bukan** `T3` untuk klaim apa pun tentang nilai veto; report
itu sendiri membatasi dirinya "bukan prediksi return" dan memakai ongkos 20 bps. Status "belum
diuji" itu resmi tertulis di [[06-Results/02 - Thresholds]]: "Empat angka pertama masih perlu diuji
terhadap hasil, bukan dipertahankan karena sudah ditulis."

## Boleh dibaca, dilarang dibaca

- **Boleh:** "tujuh ambang penolakan kita; satu (umur 24 jam) punya alasan aritmetika; outcome
  kohort lolos vs ditolak sudah pernah dihitung dan **arahnya tidak mendukung klaim bahwa veto kita
  menambah nilai** — mean +353,7 (ditolak) vs +148,0 (lolos), median −44,4 vs +35,9. Yang belum ada
  adalah verdik dengan ongkos terukur dan selang kepercayaan, bukan angkanya."
- **Dilarang:** "filter keamanan kami terbukti menolak token buruk" · "kohort yang kita tolak
  ternyata lebih untung, jadi filternya salah" (mean yang sama bisa dibalik oleh satu token dan
  medians-nya bergerak arah berlawanan — itu sebabnya verdik butuh bootstrap) · "semua kandidat yang
  lolos filter kami aman" (filter mengukur risiko struktural, bukan peluang untung).

**Terkait:** [[GAP3 - Yang Punya Data Tapi Belum Diuji]] · [[GAP5 - Urutan Kerja dan Bayarnya]] ·
[[O6 - Konsentrasi Holder Bundler dan LP Lock]] · [[EV6 - Kalibrasi Ambang Terhadap Hasil]] ·
[[PL2 - Menyaring Universe]]
