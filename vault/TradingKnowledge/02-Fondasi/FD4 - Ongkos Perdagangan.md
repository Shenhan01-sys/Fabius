---
tags: [tk, tk-fondasi, "FD4"]
---

# FD4 - Ongkos Perdagangan

**Keluarga:** [[00 - Hub Fondasi]] · **Tahap:** keputusan ([[PL4 - Memutuskan]]), penilaian ([[PL6 - Menilai Hasil]])
**Sumber:** [[Fakta Terukur]] §D (59 bps, 20 bps, $0,05, gas 97) · §E (ambang efektif) · §F (gross vs ongkos) · §H (`cost_bps_applied = 0.0`) · `tools/direction.py` (gerbang funding)

**Ringkas:** Ongkos adalah sisi negatif dari setiap trade yang tidak hilang ketika sinyalnya bagus.
Ia terdiri dari komponen proporsional (fee, spread, dampak) dan komponen **tetap** (gas, minimum
order) yang porsinya membesar saat posisi dikecilkan. Di Fabius, ongkos bukan hiasan laporan: ia
satu-satunya alasan aturan yang gross-nya positif bisa tetap rugi di 12 dari 12 aset.

## Definisi yang bisa dihitung

```
ongkos_rt(notional) = 2*fee_taker + spread_effectif + dampak(notional)      # proporsional
                    + 2*biaya_per_transaksi                                 # TETAP (gas, minimum)
ambang efektif      = gross > 2 * ongkos_rt   -> net > 0
carry               = funding per interval * jumlah interval posisi hidup
```

Komponen dan keadaan angkanya di repo ini:

| komponen | angka | sifat |
|---|---|---|
| round-trip venue demo, posisi 1 unit | **59 bps** | **terukur** (`x·y=k` + fee 30 bps; bukan gas mainnet) — §D |
| realized nyata di chain 97 | **−59 bps** per putaran | terukur, dibaca dari event `Closed` — §D |
| model biaya warisan (`edge_lab`) | 5,5 + 4,5 bps per sisi = **20 bps** RT | **asumsi**, bukan hasil ukur kami — §D |
| ambang efektif warisan | gross > **40 bps** | konsekuensi 2× dari baris di atas — §D/§E |
| ongkos tetap ±$0,05 bolak-balik pada posisi $1 | butuh **+5 %** untuk balik modal | estimasi mainnet — **belum diukur di repo ini** — §D |
| gas testnet 97 | live **0,10 gwei**; guard lama memakai floor **1 gwei** | terukur; guard menolak karena plafon sendiri — §D |
| funding/carry | gerbang: `> 0,05 %/4 j` menolak posisi | wired di `tools/direction.py` — §A |

## Cara pakai yang diklaim

Cara pakai yang benar: ongkos menentukan **di ukuran berapa** sebuah edge masih hidup, jadi ia
dipakai sebelum membicarakan sinyal — sebagai filter, bukan sebagai catatan kaki. Cara pakai yang
umum di komunitas (dan yang kami tolak): melaporkan gross, menyebutnya "return", lalu mengoreksi
dengan fee tunggal yang tidak pernah diukur di venue tempat mereka berdagang.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| ongkos round-trip terukur di venue sendiri | `ADA` | 59 bps — [[Fakta Terukur]] §D |
| ongkos terukur di venue produksi (meme spot BSC) | `TIDAK-ADA` | tidak ada venue produksi; angka 20 bps adalah warisan asumsi — §D |
| gas per panggilan yang dibukukan | `ADA` | `gasUnitsPaid` di event `Closed` (`contracts/ExecutionVault.sol`); angkanya dibaca dari run, bukan dari halaman ini |
| funding historis per aset | `TIDAK-ADA` | hanya pembacaan saat ini — §C, sehingga carry tidak ikut diuji di backtest |
| spread & dampak pada ukuran nyata | `TIDAK-ADA` | hanya 1 unit yang pernah dijalankan — lihat [[FD3 - Likuiditas dan Dampak Harga]] |

## Uji di Fabius

Yang sudah diuji dengan ongkos di dalam angka: `tools/backtest.py` (400 hari × 12 aset, ambang
diimpor, tidak di-fit) memberi gross **+1,5 … +4,0 bps** per trade melawan ongkos **20 bps** —
hasilnya net **−27,9 … −0,8 bps** dan rugi di **12/12**; arah dibalik tetap kalah
(−39,2 … −12,1) ([[Fakta Terukur]] §F). Ini contoh terukur dari "filter ongkos membunuh edge tipis",
bukan sekadar rumus.

Keadaan yang harus ikut disebut di setiap angka: **P10 masih terbuka** — 59 bps terukur belum
disatukan dengan 20 bps asumsi di seluruh jalur uji ([[Fakta Terukur]] §D). Praktisnya hari ini ada
tiga bahasa ongkos sekaligus: jalur uji memakai 20 bps, venue kami menghasilkan 59 bps, dan artefak
`decisions/whale-sweep-90d.json` memakai `cost_bps_applied = 0.0` sehingga **semua** horison di
berkas itu GROSS (§H). Angka mana pun yang digabungkan dengan 20 bps wajib menyebut bahwa ongkos
terukur kami 3× lipat. Kalau ambang efektif warisan (2×) dipakai apa adanya pada ongkos terukur,
garisnya berubah dari gross > 40 bps menjadi gross > ±118 bps — aritmetika, dan sampai P10 ditutup
**belum ada satu pun jalur yang menegakkannya**.

## Batas dan mode gagal

- **Komponen tetap tidak ikut mengecil.** Menambah posisi jadi lebih kecil menaikkan ongkos per
  dolar; "$1 per posisi" bisa menuntut **+5 %** hanya untuk kembali ke nol (§D) — inilah yang membuat
  ukuran kecil terlihat rendah risiko padahal hanya rendah *harapan*.
- **Ongkos membuat horizon pendek lebih sulit, bukan lebih netral.** Semakin pendek hold, semakin
  besar bagian ongkos yang dipaksa tertutup oleh pergerakan kecil.
- **Funding bukan bonus, dia harga tiket.** Carry dibayar per interval selama posisi hidup, dan
  gerbang kami memveto di `0,05 %/4 j` — tapi historinya tidak ada (§C), jadi uji kami hari ini
  **tidak pernah** membayar carry.
- **Ongkos berkorelasi dengan rezim.** Spread melebar dan dampak membesar justru saat sinyal
  paling menarik ([[FD8 - Volatilitas]], [[FD3 - Likuiditas dan Dampak Harga]]). Memakai satu angka
  ongkos untuk semua keadaan adalah optimisme yang rapi.
- **Duplikasi dengan gerbang lain:** `MIN_VOL_OVER_LIQ` 0,10 (§E) menyaring hal yang sebagian
  tumpang tindih dengan kapasitas keluar — jangan dihitung sebagai dua bukti.

## Tingkat bukti

`T3` untuk 59 bps dan −59 bps (kami yang mengukur, dua jalur berbeda setuju) · `T1` untuk bentuk
"ongkos tetap + proporsional" (kerangka standar, tidak kami validasi sendiri) · `T0` untuk angka
$0,05 dan segala turunan "+5 %"-nya (estimasi mainnet, belum diukur di repo) · untuk klaim
"ongkos sudah disatukan di jalur uji": **belum**, dan itu P10, bukan teori.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "aturan arah kami gross +1,5…+4,0 bps melawan ongkos 20 bps dan rugi di 12/12; di venue
  kami sendiri ongkos terukurnya 59 bps — dan keduanya belum disatukan (P10)."
- **Dilarang:** "biaya kami sekitar 20 bps" (itu warisan, terukur 59) · "strategi ini net profit"
  tanpa menyebut pada ukuran berapa · menampilkan angka horison `whale-sweep-90d.json` sebagai net.

**Terkait:** [[Concepts/Cost Is Fixed]] · [[01-Agent/A4 - Trust Gating and Real-Money Rules]] ·
[[FD5 - Expectancy Bukan Win Rate]] · [[FD6 - Ukuran Posisi]] · [[FD3 - Likuiditas dan Dampak Harga]] ·
[[U2 - Funding Rate dan Basis]] · [[EV6 - Kalibrasi Ambang Terhadap Hasil]]
