---
tags: [tk, tk-fondasi, "FD8"]
---

# FD8 - Volatilitas

**Keluarga:** [[00 - Hub Fondasi]] · **Tahap:** analisis ([[PL3 - Menganalisis]]), mengikat ukuran ([[FD6 - Ukuran Posisi]])
**Sumber:** [[Fakta Terukur]] §A/§C/§E · `tools/direction.py` (ATR, `vol_annual`) · sisanya pengetahuan standar pasar — tidak ada rujukannya di repo ini

**Ringkas:** Volatilitas adalah besaran tanpa tanda: ia mengukur seberapa jauh harga bisa bergerak,
bukan ke mana. Hampir semua hal yang bisa membunuh sebuah posisi (jarak stop, ukuran, ongkos keluar,
peluang kena likuidasi) adalah fungsi vol — sementara hampir semua sinyal berbicara arah. Karena itu
vol jarang salah dan sering dipakai untuk hal yang salah.

## Definisi yang bisa dihitung

```
realized vol   : std(log return) pada jendela n bar            -> ada di repo (lihat batasnya di bawah)
ATR            : rata-rata true range; true range = max(h-l, |h-prevC|, |l-prevC|)
                 `tools/direction.py`: mean TR 24 bar terakhir (bukan smoothing Wilder)
estimator range: Parkinson / Garman-Klass dari OHLC -> memakai high-low, lebih efisien dari close-to-close
implikasi vol  : butuh harga opsi (IV)                          -> TIDAK-ADA di repo ini, jadi tidak tersedia
GARCH(1,1)     : sigma_t^2 = omega + alpha*eps_{t-1}^2 + beta*sigma_{t-1}^2 -> tidak ada implementasinya
ATR ratio      : ATR_pendek / ATR_panjang                       -> penanda vol sedang naik/mengempis
```

Satu temuan kode yang wajib ikut disebut: `tools/direction.py` menghitung `vol_annual` sebagai
`std(log return) * sqrt(6)` dengan komentar `4 jam -> hari -> tahun`, padahal bar yang dipakai
berinterval **1 jam**; annualisasi bar 1 jam memakai `sqrt(24 * 365)`. Selain satuan yang salah
label itu, angkanya **tidak dirujuk di tempat lain** — ia masuk `feats()` lalu berhenti. Ini pola
yang sama dengan konstanta mati yang kami temukan di korpus rujukan (`VOL_HI`, lihat
[[06-Results/02 - Thresholds]]): fitur yang ada bukan fitur yang dipakai.

## Cara pakai yang diklaim

Klaim praktisi: vol tinggi = "saatnya masuk", vol rendah = "konsolidasi sebelum meledak"; dan
sebagai filter: jangan trading kalau ATR terlalu besar. Yang benar secara mekanis: vol menentukan
**ukuran dan jarak**, bukan arah. Yang tidak pernah ikut diklaim siapa pun dengan bukti: bahwa
ledakan vol datang **setelah** konsolidasi, bukan sering kali sesudahnya dan di arah yang tidak
ditentukan oleh konsolidasi itu.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| OHLC 1 jam ≥ 2.400 bar untuk vol terealisasi | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari, hanya aset ber-kontrak perp — [[Fakta Terukur]] §A |
| harga opsi / implied volatility | `TIDAK-ADA` | tidak ada sumber opsi di repo ini — §C; jadi "realized vs implikasi" **tidak bisa** ditutup |
| funding rate sebagai proksi posisi/carry | `ADA-TAPI` | hanya pembacaan saat ini, histori per aset tidak bisa ditarik mundur — §C/§A |
| volum 24 j vs likuiditas (sering disalahsebut "vol") | `ADA` | `MIN_VOL_OVER_LIQ >= 0,10` — §E; itu **putaran uang**, bukan volatilitas harga |
| estimator range (Parkinson dkk.) | `ADA-TAPI` | bahannya (OHLC) ada, tidak ada satu pun alat yang menghitungnya |
| vol lintas aset untuk risiko keranjang | `ADA-TAPI` | deretnya ada untuk 608 kontrak, tidak ada kode korelasi — [[FD10 - Korelasi dan Risiko Keranjang]] |

## Uji di Fabius

Uji yang bisa dijalankan dari data yang sudah ada (belum ada perintahnya; `tools/vol_study.py` —
**belum ditulis**):

1. **Daya ramal ATR:** label `ATR(t)` dari bar ≤ t, bandingkan dengan range terealisasi pada horizon
   tetap (4 j / 24 j). Kontrol: estimasi naif "range besok = range kemarin". Klaim vol clustering baru
   sah kalau ATR mengalahkan naif itu — *(belum diukur)*.
2. **Clustering diukur pada `|return|`, bukan pada return.** Proxy arah kami
   (`|acf|` return log lag 1/6/24, §E/§F) sengaja mengukur persistensi **arah**; ia buta terhadap
   penggerombolan vol. Dua pertanyaan berbeda, satu perkakas tidak menjawab keduanya.
3. **Vol ≠ arah, dan ini sudah terukur di sisi lain:** deret paling dalam yang kami punya jatuh ke
   rezim `efficient` (`|acf|` kecil) sementara yang lolos ke keputusan justru bersejarah pendek
   ([[01-Agent/01 - Asset Classes and Seats]] §5). Kedalaman dan struktur bukan hal yang sama, dan
   keduanya bukan arah.
4. Semua hasil harus dinyatakan pada `n >= 20` non-overlap dan dibandingkan ongkos **59 bps**
   terukur (§D), karena vol juga mengubah ongkos.

## Batas dan mode gagal

- **Vol melebar bersamaan dengan melebarnya spread dan mengecilnya kedalaman.** Pakai ATR untuk
  jarak, lalu berasumsi fill ada di jarak itu = dua asumsi yang sama-sama gagal di saat yang sama
  ([[FD3 - Likuiditas dan Dampak Harga]], [[FD7 - Invalidation Stop dan Time-Stop]]).
- **Vol itu autokorelatif, arahnya tidak.** Model vol (GARCH, ATR ratio) mewarisi manfaat itu;
  model arah tidak boleh mengaku memakai "filter vol" kalau yang diuji cuma rata-rata return.
- **Regim vol bukan regim arah.** Sebuah aset bisa berayun besar tanpa persistensi (jalan acak yang
  mahal) — persis bentuk yang menghasilkan sinyal banyak dan expectancy negatif.
- **Tanpa opsi, "implikasi" tidak boleh disebut.** Kalimat seperti "pasar mengharapkan gerakan
  besar" tidak punya sumber di repo ini; kalau ditulis, itu opini, bukan bacaan data
  ([[U2 - Funding Rate dan Basis]] adalah satu-satunya proksi posisi yang kami punya, dan itu
  proksi).
- **Satu-satunya "vol" yang ditegakkan kode kami bukan volatilitas.** `MIN_VOL_OVER_LIQ` (§E)
  memfilter putaran volume terhadap likuiditas; menyebutnya filter vol adalah salah nama.

## Tingkat bukti

`T1` untuk ATR/realized vol sebagai pengukuran (kerangka standar, dipakai di repo) · `T2` untuk
clustering dan GARCH sebagai fakta stylized literatur (tidak kami reproduksi) · untuk Fabius:
**belum diuji** — tidak ada satu pun run yang membandingkan ramalan vol dengan kontrol naif; dan
`vol_annual` yang ada tidak layak dikutip sebelum satuannya dibetulkan.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "vol menentukan jarak stop, ukuran, dan ongkos keluar; ia tidak menentukan arah, dan di
  repo ini volatilitas implikasi tidak tersedia sama sekali."
- **Dilarang:** "vol tinggi berarti akan naik" · "fabius menargetkan volatilitas" · "implied vol
  kami baca dari pasar" · memakai `vol_annual` sebagai angka tahunan.

**Terkait:** [[FD1 - Struktur Pasar dan Rezim]] · [[FD6 - Ukuran Posisi]] · [[FD7 - Invalidation Stop dan Time-Stop]] ·
[[I6 - ATR dan Jarak Ternormalisasi]] · [[U2 - Funding Rate dan Basis]] · [[O4 - Active Addresses dan Pemakaian Gas]] ·
[[PL3 - Menganalisis]]
