---
tags: [tk, tk-bukti, "EV2"]
---

# EV2 - Jebakan Backtest

**Keluarga:** [[00 - Hub Bukti]] · **Tahap:** penilaian ([[PL6 - Menilai Hasil]])
**Sumber:** tiap jebakan di bawah punya kasus nyata — [[Fakta Terukur]] §F/§H atau dua halaman pra-registrasi (`06-Results/05`, `06-Results/06`); ditulis dari yang menggigit, bukan dari manual

**Ringkas:** Backtest tidak gagal dengan suara keras. Dia gagal dengan menghasilkan tabel yang terlihat benar, lengkap dengan n dan p. Catatan ini menahan sembilan jebakan yang sudah pernah terjadi di repo ini, sudah dirancang-lawan, atau dibuat mustahil oleh data kami sendiri — dan untuk tiap jebakan satu kolom yang biasanya hilang: **cara mendeteksinya sebelum hasil**, karena sesudah hasil semua jebakan terlihat seperti penemuan.

## Definisi yang bisa dihitung

| jebakan | definisi | deteksi SEBELUM hasil |
|---|---|---|
| lookahead | keputusan memakai informasi bertimestamp setelah waktunya | entri di open bar **setelah** bar sinyal ([[06-Results/06 - Pre-registration Horizon]]); keanggotaan panel wajib lebih tua dari tx yang dinilai |
| survivorship universe | hanya aset yang selamat dapat harga | tulis apa yang hilang di definisi universe: bisa dihargai = punya kontrak perp di Aster; yang mati di tengah jalan tidak akan pernah tercetak di kline mana pun ([[Fakta Terukur]] §A) |
| survivorship panel | dompet dilabeli "pintar" justru karena sejarah yang diuji | tanggal pertama label terlihat ada di data? terukur: 0 dari 607 transaksi pertama tanpa tag ([[Fakta Terukur]] §B) → tanpa koreksi: flag `TERCEMAR` |
| data direvisi | baris bisa berubah setelah dibaca | pisahkan peran: sumber retro (`_updated_at` di Dune) boleh jadi statistik, dilarang jadi saksi waktu ([[Concepts/Point-in-Time vs Retro-updatable]]) |
| asumsi fill | fill di harga ideal bar terakhir | fill ≤ ongkos terukur menyebut venue-nya: round-trip kami **59 bps**, 3× asumsi warisan 20 bps ([[Fakta Terukur]] §D) |
| overfit parameter | ambang fungsi hasil | header run menulis "ambang diimpor, tidak di-fit"; tiap setelan pasca-hasil = run baru, run lama tidak digeser |
| non-overlap dilanggar | satu peristiwa dihitung berkali | sampel = satu per (token, jam) / (wallet, token, hari); `MIN_SAMPLES=20` hanya menghitung observasi yang tidak tumpang tindih horison |
| ongkos yang menghapus | edge tipis dimakan biaya nyata | ongkos tercetak **sebelum** tabel; artefak tanpa ongkos itu gross — `decisions/whale-sweep-90d.json` membawa `cost_bps_applied = 0.0` ([[Fakta Terukur]] §H) |
| null yang salah | dibandingkan dengan nol, atau tanpa pembanding | pembanding disebut dan sepadan: bukan "hold 0 %" tapi "arah acak pada token & jam yang sama" ([[Fakta Terukur]] §B) |

Sembilan baris ini bukan larangan moral, mereka predikat: tiap kolom deteksi harus bisa dijawab Ya/Tidak sebelum satu angka hasil pun dilihat. Kalau sebuah pertanyaan baru terjawab sesudah tabelnya ada, ia pindah ke bagian penyimpangan, bukan ke desain.

## Cara pakai yang diklaim

Cara mesin memakai lapisan ini: `## Uji di Fabius` di catatan mana pun wajib mengisi baris pembanding dan ongkos sebelum dijalankan — uji tanpa pembanding bernama bukan uji, itu deskripsi angka. Tiap baris tabel di atas adalah predikat yang bisa dijawab mekanis oleh halaman pra-registrasi, bukan checklist yang dibaca setelah hasilnya ada.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| deret harga forward unduhan sendiri | `ADA` | Aster 9.599 bar ≈ 400 hari; Hyperliquid 5.001 bar kontrol silang — [[Fakta Terukur]] §A |
| koreksi survivorship yang sejati | `TIDAK-ADA` | catatan token yang mati di tengah jalan tidak ada dan tidak bisa dibeli ([[06-Results/06 - Pre-registration Horizon]]) |
| riwayat panel sebelum berlabel | `ADA-TAPI` | rekaman ⑦ dipasang 26 Sep 08:01Z (aritmetika §B) — Uji A baru bisa berverdik setelah **30 hari data prospektif** terkumpul; tanggalnya konsekuensi, bukan angka produk |
| funding historis / L2 / tick | `TIDAK-ADA` | daftar tertutup di [[Fakta Terukur]] §C — metode yang bergantung padanya tidak bisa diuji surut sama sekali |

## Uji di Fabius

`tools/backtest.py` pola yang sah: ambang diimpor dari kode hidup, lima segmen waktu, fold terbaik dibuang, tiga varian dicetak berdampingan (asli, gerbang dicabut, arah dibalik) — bagian terakhir yang membuat bukti jebakan terbaca: ketika yang dibalik pun kalah (−39,2…−12,1 bps), yang salah bukan tanda kita, melainkan aturan yang tidak memuat informasi arah. `tools/whale_sweep.py` kasus di mana catatan ini gagal pada dirinya sendiri: artefaknya lahir dengan ongkos nol, sehingga semua horison di dalamnya GROSS dan tidak bisa dikutip sebagai bukti ([[Fakta Terukur]] §H). Jebakannya bukan di desain, tapi di alat — dan di sini ia tercatat apa adanya.

## Batas dan mode gagal

- Daftar ini tidak tertutup: pergeseran rezim dan dependensi jalur eksekusi belum pernah menggigit uji kami karena kami tidak pernah sampai ke tahap itu — "belum kena" bukan "aman".
- Deteksi sebelum hasil memakan waktu; gerbang sesungguhnya bukan catatan ini, tapi halaman pra-registrasi yang memaksa pembanding ditulis sebelum angka ([[EV5 - Reproduksibilitas dan Pra-Registrasi]]).
- Jebakan yang ketahuan **setelah** hasil tidak dihapus — dicetak sebagai penyimpangan. [[06-Results/05 - Pre-registration Flow]] membuat bagiannya sendiri setara hasil; bagian itulah yang membuat bagian hasil bisa dipercaya.
- Hasil negatif di bawah bias tetap kredibel; hasil positif di bawah bias tidak ([[Concepts/Lookahead Bound]]) — asimetri ini alasan `TERCEMAR` boleh membawa angka, tapi hanya satu arah yang boleh dipercaya.

## Tingkat bukti

`T3` untuk klaim "tiap jebakan di tabel punya kasus nyata di repo ini" — semua menunjuk artefak di [[Fakta Terukur]] §F/§H atau dua halaman pra-registrasi. `T1` untuk kelengkapan daftar: kelas standar praktik kuantitatif, tidak ada yang menguji "daftar ini tidak kekurangan nomor".

## Boleh dibaca, dilarang dibaca

- **Boleh:** "uji di repo ini dirancang terhadap daftar jebakan spesifik; sebagian besar pernah mengenainya di sini, dan setiap yang kena meninggalkan jejak tercetak."
- **Dilarang:** "backtest kami bebas bias" — survivorship tidak dibuang dengan data yang ada, cuma bisa ditunjuk; "hasil negatif tidak butuh kontrol" — butuh, hanya saja kontrolnya tidak akan pernah mengubah verdik negatif menjadi klaim.

**Terkait:** [[EV1 - Tingkat Bukti]] · [[EV3 - Signifikansi dan Multiple Testing]] · [[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]] · [[QT2 - Backtesting yang Jujur]] · [[QT4 - Overfitting dan Validasi]] · [[Concepts/Lookahead Bound]] · [[Fakta Terukur]]
