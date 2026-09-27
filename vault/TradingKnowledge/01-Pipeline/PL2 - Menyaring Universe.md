---
tags: [tk, tk-pipeline, "PL2"]
---

# PL2 - Menyaring Universe

**Keluarga:** [[00 - Hub Pipeline]] · **Tahap:** filtering · sebelumnya [[PL1 - Mengumpulkan Data]] · sesudahnya [[PL3 - Menganalisis]]
**Sumber:** `universe/record_bsc_universe.py`, `tools/screen_universe.py`, `tools/decide.py` · [[Fakta Terukur]] §E

**Ringkas:** Penyaringan bukan mesin pencari peluang, ia mesin **penolakan** — dan produsen resmi
survivorship kita: semua uji di hilir berlangsung di dalam universe yang sudah dipotong, jadi tiap ambang
yang belum diuji terhadap hasil diam-diam menentukan apa yang boleh disebut "edge". Yang paling mahal
secara metodologis bukan daftarnya, melainkan pemisahan tiga keadaan: **lolos**, **ditolak karena risiko
terukur**, dan **tidak bisa dinilai** — yang ketiga bukan penolakan yang benar, ia kegagalan pengukur ([[Concepts/Unmeasured Is Not Clean]]).

## Definisi yang bisa dihitung

```
lolos(x)               : setiap veto TERUKUR dan tidak ada yang tersangkut
ditolak_sebab(x)       : ada veto yang tersangkut, dan alasan yang dicetak == ambang yang kena
tidak_bisa_dinilai(x)  : ada field veto yang null / tidak kembali dari sumber -> BUKAN penolakan
uji_veto(v)            : bandingkan hasil forward(kena v) vs hasil forward(lolos) pada jendela yang sama
                         v yang tidak memprediksi hasil lebih buruk = seremoni -> cabut, catat di 06-Results/02
```

Ambang yang berlaku sekarang — semuanya **diputuskan**, bukan temuan ([[Fakta Terukur]] §E):

| veto | ambang | yang sebenarnya ditolak |
|---|---|---|
| likuiditas pool | `MIN_LIQ_USD` 50.000 USD | tidak ada kapasitas keluar — bukan "token jelek" |
| umur | `MIN_AGE_SEC` 24 jam | tidak ada satu pun bar untuk diuji (aritmetika jendela data) |
| konsentrasi holder | `MAX_TOP10` 45 % supply | satu keputusan pihak lain bisa menghapus pasarmu |
| LP lock | `MIN_LOCK` 20 % | likuiditas bisa ditarik kapan saja |
| bundler | `MAX_BUNDLER` 30 % | "permintaan" itu satu orang berpakaian banyak topeng |
| jumlah holder | `MIN_HOLDER` 60 alamat | "jumlah pemegang" belum berarti apa-apa |
| volum/likuiditas | vol24/liq ≥ 0,10 | trending tanpa permintaan nyata |
| base pasangan | daftar stable/major | ini likuiditas stablecoin, bukan aset yang bisa dipilih |

## Cara pakai yang diklaim

Cara umum di kalangan praktisi (T1): screener dipasang sekali lalu dilupakan, dan hasilnya disebut
"universe bersih". Klaim turunannya — "filter menaikkan win rate" — tidak pernah diberi pembanding oleh
siapa pun yang bisa kami periksa. Yang sahih dari tahap ini jauh lebih sempit: penyaringan menurunkan
ongkos riset (kamu berhenti mengukur yang tidak bisa kamu perdagangkan) dan menentukan **populasi**
tempat semua statistik berikutnya dihitung. Karena itu Fabius memperlakukannya sebagai hipotesis yang
wajib diuji, bukan konfigurasi yang cukup disetel sekali: `tools/screen_universe.py` sengaja mencetak
**corong penolakan** — apa yang terjadi pada yang ditolak dibandingkan dengan yang terjadi pada lolos.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| likuiditas pool + volum 24 j + umur pool | `ADA` | GeckoTerminal per jendela — [[03-Data/01 - Dataset]] |
| field perilaku (holder top-10, lock, bundler, jumlah holder) | `ADA-TAPI` | hanya untuk kandidat yang dikembalikan `market/rank`; server memotong jendela — [[06-Results/02 - Thresholds]] |
| pasangan alamat pool ↔ kandidat perilaku | `ADA-TAPI` | cakupannya kecil dan **sudah diukur habis lewat tiga jalur**; sumber utama keadaan "tidak bisa dinilai" — [[06-Results/03 - Not Yet Proven]] baris 12 |
| keamanan kontrak per kandidat | `ADA-TAPI` | terjangkau pada skala jalur arah (≤5 kandidat), **tidak** pada 40 alamat/snapshot — [[04-Tools/TL3 - security_gate]] |
| hasil forward untuk menguji tiap veto | `ADA-TAPI` | bar cukup dalam hanya untuk aset ber-kontrak perp — [[Fakta Terukur]] §A |
| riwayat ambang yang tidak berubah | `ADA` | ambang tersimpan **di dalam snapshot** dan ikut di-hash — [[03-Data/D5 - Record Schemas]] |

## Uji di Fabius

```
python -X utf8 tools/screen_universe.py            # corong penolakan: hasil vs alasan
python -X utf8 tools/decide.py                     # veto DIHITUNG ULANG dari angka mentah
```

`tools/decide.py` tidak memercayai field hasil yang tersimpan di snapshot: ia menghitung ulang
penolakan memakai ambang yang tercatat di snapshot itu sendiri, supaya orang lain bisa memeriksa bahwa
keputusan memang keluar dari data itu. Gerbang sebuah veto naik tingkat bukti: `n >= 20` hasil
non-overlap per alasan, arah konsisten, pembandingnya **kohort lolos pada jendela yang sama** (bukan
nol), lolos BH α 0,10, tetap benar setelah fold terbaik dibuang ([[Fakta Terukur]] §E); rancangannya di
[[GAP2 - Uji Setiap Veto Terhadap Hasil]]. Status hari ini: empat ambang universe pertama **masih belum
diuji terhadap hasil**.

## Batas dan mode gagal

- **Survivorship ganda:** kita memotong kandidat, lalu menilai strategi di populasi sisa — dan yang punya
  riwayat panjang hanyalah yang selamat ([[03-Data/D3 - Price Depth]]).
- **"Ditolak" ≠ "tidak bisa dinilai".** Mencampur keduanya membuat kalibrasi ambang berjalan di atas
  angka yang sebenarnya mengukur kegagalan penggabungan sumber; karena itu `ENTER` mensyaratkan **kedua**
  daftar kosong ([[06-Results/02 - Thresholds]]).
- **Satu jendela = satu sampel.** Bucket per jam, ambil baris pertama; baris tambahan dari jalankan-sekali
  manual bukan sampel ([[03-Data/01 - Dataset]]).
- **Angka lintas skema tidak sebanding:** `survivable_count` berganti definisi antar versi skema, jadi
  menyatukannya = membandingkan dua arti "lolos" ([[03-Data/D5 - Record Schemas]]).
- **Umur dan likuiditas adalah penolakan struktural**, bukan kegagalan agen — jangan ikut dihitung
  sebagai "penolakan yang benar".
- **Veto yang terlalu tajam membunuh uji atas veto itu sendiri:** setiap ambang juga mengurangi `n` yang
  dibutuhkan untuk membuktikan ambang tersebut ([[PL6 - Menilai Hasil]]).
- **Definisi kelompok = klaim pihak ketiga.** Panel berlabel ("smart money") dipilih vendor, dan label
  yang diberikan setelah sejarahnya terjadi menaikkan angka kelompok itu ([[Concepts/Lookahead Bound]]).

## Tingkat bukti

`T1` untuk bentuk funnel dan isi daftar veto (praktik umum; kami memakainya karena masuk akal, bukan karena
teruji). Untuk kekuatan prediktif tiap ambang: **belum diuji** — `T0` sampai `GAP2` dijalankan, dan itu
tertulis apa adanya di [[Fakta Terukur]] §E. `NEGATIF` untuk klaim tetangga yang sering dipakai membenarkan
penyaringan — "kelompok berlabel pintar menghasilkan hasil lebih baik": pada data kami panel justru kalah
dari baseline acak di horizon yang kami perdagangkan ([[06-Results/04 - Negative Results]]).

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami menolak jauh lebih banyak kandidat daripada yang kami ambil, tiap penolakan punya
  alasan yang bisa dihitung ulang dari berkas, dan kami belum membuktikan alasan itu memprediksi hasil."
- **Dilarang:** "universe kami sudah bersih dari rug" · "filter kami menaikkan win rate" ·
  "kandidat yang tidak lolos itu buruk" (sering: tidak dinilai) · "ambang kami terkalibrasi".

**Terkait:** [[PL1 - Mengumpulkan Data]] · [[PL3 - Menganalisis]] · [[PL4 - Memutuskan]] · [[EV6 - Kalibrasi Ambang Terhadap Hasil]] ·
[[O6 - Konsentrasi Holder Bundler dan LP Lock]] · [[FD3 - Likuiditas dan Dampak Harga]] · [[Concepts/Unmeasured Is Not Clean]]
