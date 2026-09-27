---
tags: [tk, tk-bukti, "EV5"]
---

# EV5 - Reproduksibilitas dan Pra-Registrasi

**Keluarga:** [[00 - Hub Bukti]] · **Tahap:** keputusan ([[PL4 - Memutuskan]]) — melintang semua tahap
**Sumber:** `vault/Conventions.md` §1–2 · [[06-Results/05 - Pre-registration Flow]] · [[06-Results/06 - Pre-registration Horizon]] · [[Fakta Terukur]] §B/§G

**Ringkas:** Reproduksibilitas dan pra-registrasi adalah satu hal dari dua arah: mengunci informasi melawan kepentingan kita sendiri. Yang pertama membuat pihak ketiga sampai ke angka yang sama tanpa memercayai kami; yang kedua membuat kami tidak boleh mengubah aturan setelah tahu di pihak mana aturan itu menang. Tidak satu pun membuktikan tebakan kami benar — dan justru itu gunanya.

## Definisi yang bisa dihitung

| properti | predikat operasional | keadaan di repo (28 Sep 2026) |
|---|---|---|
| angka reproduksibel | orang lain, dari clone bersih, menjalankan SATU perintah → angka sama | `python -X utf8 tools/anchor.py --verify` → `anchorCount() = 19 · 13 baris terpelacak · 13/13 COCOK`; **19 vs 13 itu lubang tercatat (P6b), bukan keberhasilan** ([[Fakta Terukur]] §G) |
| rantai artefak | baris bertimestamp + sha256; mengubah masa lalu = mengubah hash, tidak = menghapus jejak | `rows_sha256` di artefak `tools/ledger.py` dan `tools/maker_ledger.py`; manifest ⑦ menyimpan sha256 berkas + hash ekor + umur |
| aturan sebelum hasil | halaman pra-registrasi dengan `ditulis:` lebih awal dari angka pertama; amend HANYA lewat entri baru di [[00-Overview/03 - Decisions]], tidak lewat menyunting halaman | pola terkunci `06-Results/05` dan `06-Results/06`; keduanya mencetak penyimpangan run-nya sendiri |
| waktu dari pihak ketiga | timestamp diterbitkan pihak yang tidak berkepentingan: server GitHub (`.github/workflows/`), blok chain — bukan jam laptop | ekor ⑦ `2026-09-27T18:21:16Z` dari commit server, bukan dari kita |
| preseden | **run mengalahkan halaman**: kalau keluaran fresh berbeda dari yang tertulis, halaman diperbaiki; run tidak dirunding | [[Aturan Subtree]] §satu angka satu perintah |

Empat properti pertama saling mengunci: tanpa timestamp pihak ketiga, sha256 cuma aritmetika; tanpa pra-registrasi, hash bisa dipilih-pilih setelah hasilnya diketahui.

## Cara pakai yang diklaim

Cara mesin memakai lapisan ini — mengevaluasi catatan trading tanpa memberi catatan itu peluang mengubah aturan setelah fakta: (1) `## Uji di Fabius` menyebut perintah yang ADA atau menulis "belum ditulis" — tidak ada keadaan ketiga; (2) tangga di `## Tingkat bukti` hanya boleh menunjuk artefak run, tidak pernah ke prosa, termasuk prosa catatan ini; (3) verdik yang lewat ledger dibaca dari **rekaman** (`entry_ref` ikut ter-hash) oleh `tools/ledger.py`, bukan dari ingatan siapa; (4) deviasi yang ketahuan saat menjalankan dicetak sebagai deviasi — halaman pra-registrasi kami punya bagiannya sendiri, setara hasil.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| anchor chain + verifikasinya | `ADA` | `tools/anchor.py --verify` tanpa kunci, tanpa gas — [[Fakta Terukur]] §G |
| ledger kertas vs chain yang bisa dicetak ulang | `ADA` | `tools/winlog.py`: PAPER n=2 WR 50 % net rata2 −72,4 bps · CHAIN n=3 WR 0 % −59,0 bps · F-D16 `n>=20` BELUM — §G |
| commit ber-timestamp pihak ketiga untuk rekaman | `ADA` | `.github/workflows/` (rantai ⑦ + universe per-jam) — [[03-Data/D2 - Wallet Flow]] |
| kunci pra-registrasi yang ditegakkan alat | `TIDAK-ADA` | "terkunci" konvensi teks + visibilitas git; menyunting halaman akan TERLIHAT, tapi tidak TERBLOKIR — jujur soal itu |
| artefak yang dihitung ulang dari clone | `ADA-TAPI` | ada snapshot yang hash-nya tidak bisa dihitung ulang dan pemicunya belum diketahui — yang dijaga adalah angka jujurnya, bukan yang dibulatkan ([[10-Submissions/01 - Claims Cheat Sheet]]; [[07-Testing/T6 - Clean Clone Evidence]]) |

## Uji di Fabius

Dari clone, berurutan: `python -X utf8 tools/anchor.py --verify` (bukti urutan keputusan→chain→hasil), `python -X utf8 tools/winlog.py` (progres terhadap gerbang F-D16), `python -X utf8 tools/ledger.py` (penilaian dari rekaman). Gerbang bentuk subtree — perintah di bagian Perawatan [[Aturan Subtree]] — memeriksa catatan ini sendiri: heading utuh, tangga terisi, tanpa path absolut. Yang gerbang itu TIDAK periksa, dan tidak boleh pura-pura: apakah tangga yang tertulis benar — yang memverifikasi itu tetap run yang ditunjuk, dan pointer yang mati lebih baik daripada angka yang hidup di halaman yang salah.

Yang tidak otomatis di semua ini: membandingkan ulang keluaran run baru dengan teks halaman lama tetap kerja manusia — konvensi yang menjaganya, bukan alat; dan konvensi hanya berharga selama ia dibayar dengan entri keputusan setiap kali dilanggar.

## Batas dan mode gagal

- **Reproduksibel ≠ benar.** `tools/maker_ledger.py` menghasilkan angka yang bisa dihitung ulang DAN salah mekanikanya (median `|net|` 4.558,3 bps, maks 1.222.045,4 bps) — keadaan H di [[Fakta Terukur]]: alat hijau yang mencetak omong kosong tetap omong kosong.
- Pra-registrasi tidak mencegah hipotesis buruk: halaman aliran mencatat sendiri bahwa "tiga hipotesis sebenarnya dua" (fitur sama, tanda dibalik) — itu cacat cara menghitung tes ([[EV3 - Signifikansi dan Multiple Testing]]), bukan cacat kejujuran; bedanya hanya kelihatan karena keduanya ditulis.
- Anchor tidak membuat keputusan benar; ia membuat keputusan tidak bisa disunting ([[Concepts/Anchored Before Outcome]]).
- Semua keadaan di tabel pertama basi dalam hitungan jam — angka blok G harus dijalankan ulang, bukan dikutip ([[Fakta Terukur]] §G); `git fetch` sebelum menyimpulkan apa pun tentang rantai rekaman ([[Concepts/Stale Local Copy]]).
- Reproduksibilitas punya biaya yang tidak kelihatan di mana pun: tiap perintah yang harus tetap jalan dari clone adalah kode yang tidak boleh kita romantiskan — ia dirawat atau klaimnya ikut mati bersamanya.

## Tingkat bukti

`T3` untuk setiap mekanisme di tabel definisi — masing-masing punya perintah dan keadaan hidup yang dicetaknya hari ini ([[Fakta Terukur]] §G). `T1` untuk pra-registrasi sebagai disiplin: praktik standar yang kami adopsi, tidak kami uji sebagai perlakuan terhadap data kami.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "verdik kami bisa dihitung ulang dari clone; kalau hitungan ulang berbeda, halaman kami yang salah — dan perbaikannya lewat entri keputusan baru, bukan lewat sunting."
- **Dilarang:** "semuanya verifiable jadi kami layak dipercaya" — verifiability itu lantai, bukan produk; kalimat itu ada di daftar larangan [[10-Submissions/01 - Claims Cheat Sheet]]; "ter-anchor, jadi pasti benar" — anchor mengunci urutan, bukan kebenaran.

**Terkait:** [[Concepts/Anchored Before Outcome]] · [[Concepts/Stale Local Copy]] · [[04-Tools/TL4 - anchor and verify]] · [[04-Tools/TL5 - ledger]] · [[EV1 - Tingkat Bukti]] · [[EV3 - Signifikansi dan Multiple Testing]] · [[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]] · [[07-Testing/T6 - Clean Clone Evidence]]
