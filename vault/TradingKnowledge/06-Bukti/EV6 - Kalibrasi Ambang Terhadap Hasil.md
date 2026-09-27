---
tags: [tk, tk-bukti, "EV6"]
---

# EV6 - Kalibrasi Ambang Terhadap Hasil

**Keluarga:** [[00 - Hub Bukti]] · **Tahap:** filtering ([[PL2 - Menyaring Universe]])
**Sumber:** [[Fakta Terukur]] §E · [[06-Results/02 - Thresholds]] (nilai, asal, dan syarat kalibrasi) · [[06-Results/03 - Not Yet Proven]] baris 9 & 12

**Ringkas:** Semua ambang universe adalah keputusan kita, bukan temuan — [[Fakta Terukur]] §E menulis "diputuskan (belum diuji terhadap hasil)" di hampir tiap barisnya. Catatan ini memisahkan tiga kelas ambang (satu tidak bisa diuji terhadap hasil, satu belum sempat, satu sudah terukur), menetapkan syarat sebelum kalibrasi boleh jalan, dan mengunci keputusan yang sah kalau sebuah veto ternyata tidak memprediksi apa pun: **cabut dan catat**, bukan "pertahankan saja siapa tahu".

## Definisi yang bisa dihitung

| kelas | ambang (nilai saat ini) | status uji | predikat |
|---|---|---|---|
| A — aritmetika data | `MIN_AGE_SEC` 24 jam | TIDAK diuji terhadap hasil — tidak akan pernah | tanpa bar tidak ada yang bisa dinilai; berubah hanya kalau jendela datanya berubah |
| B — risiko diputuskan | `MIN_LIQ_USD` 50.000 · `MAX_TOP10` 45 % · `MIN_LOCK` 20 % · `MAX_BUNDLER` 30 % · `MIN_HOLDER` 60 · `MIN_VOL_OVER_LIQ` 0,10 | WAJIB diuji | "veto memprediksi" := outcome (return forward DAN kemampuan keluar) populasi yang kena veto X lebih buruk daripada yang lolos, pada jendela dan aturan yang sama ([[EV3 - Signifikansi dan Multiple Testing]]) |
| C — ongkos terukur | round-trip 59 bps vs asumsi warisan 20 bps | terukur **dan sudah jadi satu sumber** sejak 28 Sep | P10 ditutup (`tools/costs.py`, §D): default 59, override tercatat `cli-override`; angka mana pun yang masih disebut 20 bps harus dijelaskan sebagai asumsi warisan |

Tiga verdik yang disepakati di muka, bukan tiga sikap: (1) memprediksi → tahan dengan angka + tanggal; (2) tidak memprediksi → **cabut**, tulis alasannya di [[06-Results/02 - Thresholds]]; (3) tidak bisa dinilai → BUKAN keduanya. Kelas B juga membawa tanggal kedaluwarsa moral: ambang yang tetap tak teruji sementara jendela hasil sudah menumpuk bukan lagi konservatisme — itu dekorasi dengan angka di sebelahnya.

## Cara pakai yang diklaim

Cara mesin memakai lapisan ini: [[PL2 - Menyaring Universe]] dan [[PL4 - Memutuskan]] membaca ambang sebagai gerbang yang hanya boleh mengurangi ([[Concepts/One-Way Gate]]) — dan catatan ini satu-satunya tempat yang mendefinisikan jalan kendor yang sah: pencabutan lewat hasil, lewat entri keputusan, setelah itu gerbang tidak lagi dipertahankan "siapa tahu". Ambang yang tidak bisa dibuktikan tetap boleh berdiri — tapi hanya dengan label aslinya: "keputusan, bukan bukti", yang persis fungsi field Asal di halaman ambang.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| snapshot universe per jendela dengan kolom lolos/dinilai | `ADA` | `universe/manifest.txt` (kolom `lolos`, `dinilai_penuh`, `sha256_snapshot`) |
| outcome forward untuk kandidat yang bisa dinilai | `ADA-TAPI` | hanya aset ber-kontrak perp yang bisa dihargai sendiri ([[Fakta Terukur]] §A); token yang benar-benar mati mungkin tidak menghasilkan outcome sama sekali |
| "bisa keluar" — ancaman sesungguhnya di balik ambang likuiditas | `ADA-TAPI` | `seat_eligible`/`sellability` ikut ter-hash, tapi angka ④ milik token spot, bukan kapasitas keluar di venue ([[06-Results/03 - Not Yet Proven]] baris 17) |
| jendela cukup untuk mengkalibrasi | `TIDAK-ADA` | verdik baris 9 di [[06-Results/03 - Not Yet Proven]]: belum ada cukup jendela |

## Uji di Fabius

Antrean dan pembaginya ada di satu halaman peta: [[GAP2 - Uji Setiap Veto Terhadap Hasil]]. Bentuknya untuk tiap ambang B: belah populasi per alasan veto — token yang kena VETO-X saja vs yang lolos SEMUA veto, bukan vs "semua yang ditolak" (alasan pencampuran: halaman ambang) — nilai outcome dengan aturan EV3, satu keluarga tes untuk semua ambang × semua horison, verdik masuk [[06-Results/00 - Hub Results]]. Halaman ini tetap tidak boleh memuat angka hasil.

Syarat yang harus ditutup DULU, sudah terukur ([[06-Results/02 - Thresholds]], 23 Sep, satu jendela 03:00Z @ 90 baris): **37 baris tidak punya satu pun field perilaku** (`top10`/`lock`/`bundler`/`holders_unmeasured`), dan **13 di antaranya gugur tanpa satu pun alasan risiko**. Kalibrasi di atas populasi itu mengukur kegagalan penggabungan GeckoTerminal ↔ GMGN, bukan risiko. Rekaman keputusan sudah memisahkan dua daftar (`risk_vetoes` vs `data_gaps`) dan `ENTER` menuntut keduanya kosong — baris 12 di [[06-Results/03 - Not Yet Proven]] adalah prasyarat, bukan catatan kaki.

Perintah yang ada hari ini hanya mengecek keadaan bukti (`tools/winlog.py`, `tools/anchor.py --verify`); perintah veto-vs-hasil adalah PEKERJAAN yang GAP2 nama — catatan ini tidak bisa mengutip hasilnya karena belum ada. *(belum diukur)*.

## Batas dan mode gagal

- **Kalibrasi juga sebuah tes.** Empat ambang pertama × beberapa horison = keluarga yang harus dihitung, atau kita dapat "tervalidasi" lewat selection effect — aturan mainnya di [[EV3 - Signifikansi dan Multiple Testing]].
- **Arah kesalahannya tidak netral, dan tidak tercatat.** Veto yang salah buang token yang akan naik tidak meninggalkan angka rugi di mana pun — dia cuma menghapus sampel. "Tidak ada komplain dari yang ditolak" bukan bukti; yang ditolak tidak bersuara.
- Outcome token berveto likuiditas rendah tidak andal justru karena likuiditas (asumsi fill — [[EV2 - Jebakan Backtest]]); "lolos semua veto tapi tetap −80 %" tidak otomatis berarti `MAX_TOP10` harus 80 %.
- **Mencabut veto melunakkan kalimat yang kita jual** ("agen kami menolak N dari M" — [[10-Submissions/01 - Claims Cheat Sheet]]): karena itu pencabutan harus peristiwa di [[00-Overview/03 - Decisions]], bukan editan senyap di kode filter — supaya yang membaca klaim lama bisa melihat kapan ia berhenti benar.
- Kalibrasi yang jadi setelah tenggat tetap sah sebagai sains dan tidak sah sebagai produk: verdik "belum teruji saat tenggat" jujur; "kami fit ambang di jendela baru" hanya masuk kalau jendela itu tertulis sebelum datanya ada.

## Tingkat bukti

`T3` untuk klaim inti catatan ini — "ambang-ambang itu belum diuji terhadap hasil" — buktinya negatif dan tercetak: field Asal di [[Fakta Terukur]] §E, pemisahan 37/13 yang terukur di [[06-Results/02 - Thresholds]], dan verdik "belum ada cukup jendela" di [[06-Results/03 - Not Yet Proven]]. `T0` untuk pembenaran implisit tiap ambang ("45 % konsentrasi itu berbahaya", "di bawah 20 % lock likuiditas bisa ditarik kapan saja") — klaim yang masuk akal tanpa pemilik yang bisa kami periksa; ia berdiri sebagai keputusan, dan halaman ini menolak memandikannya sampai terlihat seperti temuan.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami menahan empat ambang pertama tanpa bukti bahwa ambang itu memprediksi apa pun — dan prosedur untuk mencabutnya sudah tertulis sebelum hasilnya ada."
- **Dilarang:** "penyaringan universe kami tervalidasi" · "veto = keamanan" · "token yang kami tolak lalu mati berarti veto kami benar" — yang mati tanpa outcome terukur masuk verdik (3), bukan verdik (1).

**Terkait:** [[GAP2 - Uji Setiap Veto Terhadap Hasil]] · [[06-Results/02 - Thresholds]] · [[Fakta Terukur]] · [[EV1 - Tingkat Bukti]] · [[EV3 - Signifikansi dan Multiple Testing]] · [[Concepts/One-Way Gate]] · [[PL2 - Menyaring Universe]]
