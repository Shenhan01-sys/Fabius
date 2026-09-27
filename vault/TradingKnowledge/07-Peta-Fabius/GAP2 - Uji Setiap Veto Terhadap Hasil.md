---
tags: [tk, tk-peta, "GAP2"]
---

# GAP2 - Uji Setiap Veto Terhadap Hasil

**Keluarga:** [[00 - Hub Peta Fabius]] · **Tahap:** penilaian ([[PL6 - Menilai Hasil]])
**Sumber:** [[06-Results/02 - Thresholds]] (daftar ambang + status "diputuskan, bukan diukur"),
[[Fakta Terukur]] §E

**Ringkas:** tujuh ambang penyaring universe Fabius **diputuskan**, bukan **diuji**. Mereka
menolak kandidat setiap jam, dan tidak satu pun punya bukti bahwa penolakannya memprediksi hasil
yang lebih buruk. Ini lubang paling murah untuk ditutup dan paling mahal kalau dibiarkan: setiap
angka `survivable_count` yang kami kutip berdiri di atas ketujuhnya.

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
| pemisah "ditolak" vs "tidak bisa dinilai" | `ADA` | sudah diperbaiki di `tools/decide.py` (`risk_vetoes` vs `data_gaps`) setelah terukur **37 baris tanpa field perilaku, 13 di antaranya gugur tanpa satu pun alasan risiko** ([[06-Results/02 - Thresholds]]) |

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

Perintahnya belum ada (`tools/veto_study.py` = belum ditulis). Jangan mengutip halaman ini sebagai
hasil.

## Batas dan mode gagal

- **Yang dibuang justru yang paling ingin kita nilai.** `MIN_AGE_SEC` (24 jam) membuang token yang
  paling sering mati sebelum 24 jam — kelompok yang hasilnya paling ingin kita tahu. Untuk veto
  ini, "tidak bisa diuji" adalah jawaban yang sah, bukan pekerjaan yang tertunda.
- **Token yang hilang dari feed ≠ token yang rugi.** Bisa mati, bisa keluar jendela ⑦, bisa
  kebanjiran symbol lain. Mengasumsikan salah satu arah = memilih kesimpulan sebelum mengukur
  ([[Concepts/Unmeasured Is Not Clean]]).
- **Kelompok kecil.** Untuk `MAX_BUNDLER` dan `MIN_LOCK` kita mungkin tidak pernah punya `n ≥ 20`
  per kelompok pada jendela yang sama — laporkan itu, jangan turunkan ambangnya diam-diam.
- **Veto boleh jadi benar tapi tidak berguna.** Kalau semua yang ditolak `MIN_VOL_OVER_LIQ` ternyata
  rugi tapi tidak ada satu pun kandidat kita yang kena, veto itu tidak mengubah keputusan apa pun
  dan cuma menambah rasa aman.

## Tingkat bukti

`T1` untuk ketujuh ambang (diputuskan, dipakai, belum diuji terhadap hasil) · flag `BELUM DIUJI`
resmi tercatat di [[06-Results/02 - Thresholds]] sendiri: "Empat angka pertama masih perlu diuji
terhadap hasil, bukan dipertahankan karena sudah ditulis."

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami punya tujuh ambang penolakan; satu (umur 24 jam) punya alasan aritmetika, enam
  sisanya adalah keputusan yang belum diuji terhadap hasil — dan jalurnya sudah dirancang."
- **Dilarang:** "filter keamanan kami terbukti menolak token buruk" (belum ada satu pun angka yang
  membandingkan hasil dua kelompok) · "semua kandidat yang lolos filter kami aman" (filter
  mengukur risiko struktural, bukan peluang untung).

**Terkait:** [[GAP3 - Yang Punya Data Tapi Belum Diuji]] · [[GAP5 - Urutan Kerja dan Bayarnya]] ·
[[O6 - Konsentrasi Holder Bundler dan LP Lock]] · [[EV6 - Kalibrasi Ambang Terhadap Hasil]] ·
[[PL2 - Menyaring Universe]]
