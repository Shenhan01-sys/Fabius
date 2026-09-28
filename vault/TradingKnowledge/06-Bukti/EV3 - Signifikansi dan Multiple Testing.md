---
tags: [tk, tk-bukti, "EV3"]
---

# EV3 - Signifikansi dan Multiple Testing

**Keluarga:** [[00 - Hub Bukti]] · **Tahap:** penilaian ([[PL6 - Menilai Hasil]])
**Sumber:** nilai & asal di [[06-Results/02 - Thresholds]] · keadaan hidup di [[Fakta Terukur]] §E/§G/§H · dua halaman pra-registrasi

**Ringkas:** Tiga hipotesis × empat horison × dua panel = dua puluh empat tes — tapi hanya kalau kamu menghitungnya. Catatan ini mengunci cara menghitung tes dan apa yang dilakukan saat satu artefak statistik tidak bisa dijelaskan: dilapor, bukan diperbaiki diam-diam lalu dijalankan ulang. Satu kelemahan yang kami warisi tetap tertulis di sini, tidak dipoles: p-value kami pada n=20–40 **sistematis terlalu kecil**.

## Definisi yang bisa dihitung

```
keluarga tes = hipotesis × horison × panel/aset
      (horison ganda = tes ganda — dikunci di halaman pra-registrasi horison)
satu tes     = satu token; BH berlaku LINTAS token, bukan lintas fitur satu token
"lolos"      := n >= 20 non-overlap  AND  BH q <= alpha 0,10
                 AND net > 0 setelah fold terbaik dibuang  AND gross > ongkos terukur
```

- **BH-FDR α 0,10** — diwarisi dari kode rujukan, bukan dibela sebagai optimal. Keluarga koreksi di proyek rujukan hanya **per-aset**; bentuk lintas-aset tidak punya padanan kode di sana, jadi kewajiban kami justru mulai di tempat rujukan berhenti ([[06-Results/02 - Thresholds]]).
- **p satu arah, aproksimasi normal.** Pada `n = 20–40` p ini sistematis **terlalu kecil** ([[Fakta Terukur]] §E). Kami mewarisi bentuknya supaya angkanya sebanding dengan proyek rujukan, dan menulis kelemahannya — bukan memolesnya diam-diam. Konsekuensi yang wajib ikut tiap hasil: "lolos BH pada n kecil" lebih lemah dari yang terbaca; itu salah satu alasan drop-best-fold bukan pelengkap.
- **bootstrap/permutasi** saat distribusi hasil tidak diketahui: seed dan jumlah shuffle tercetak bersama p ([[06-Results/04 - Negative Results]] §4c melakukan itu). Bootstrap yang tidak bisa dijelaskan bukan pengukuran.

**Kasus yang harus tetap terbuka.** `decisions/whale-sweep-90d.json` (artefak `tools/whale_sweep.py`) mencetak `p_boot` **identik** di empat horison: `0,00024993751562109475`. Horison dengan n dan rata-rata berbeda tidak punya alasan berbagi satu p. **Belum ada di sini yang tahu kenapa**, dan justru karena itu semua angka di berkas itu tidak bisa dikutip ([[Fakta Terukur]] §H). Aturan yang lahir dari kasus ini: dua hasil yang seharusnya berbeda mencetak angka sama → investigasi alat mendahului interpretasi hasil; pelajaran sekerabatnya sudah tertulis: *tampilkan berdampingan hasil yang seharusnya berbeda* ([[06-Results/05 - Pre-registration Flow]]).

## Cara pakai yang diklaim

Cara mesin memakai lapisan ini: tiap verdik yang dikirim [[PL6 - Menilai Hasil]] ke ledger membawa n, ukuran keluarga, p, q BH, dan ongkos terukur; "signifikan" tanpa keluarga bernama bukan verdik, itu awal selection effect. Lapisan ini memakai catatan ini ke dirinya sendiri juga: tujuh ambang universe × horison yang akan dipilih = keluarga tes yang harus dihitung saat [[EV6 - Kalibrasi Ambang Terhadap Hasil]] berjalan.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| deret 1 jam untuk sampel non-overlap | `ADA-TAPI` | 9.599 bar ([[Fakta Terukur]] §A) — tetapi `NEED_BARS=2400` mengeksklusi token kecil dari uji |
| n ≥ 20 OOS tertutup untuk ⑦ | `TIDAK-ADA` | gerbang F-D16: `n>=20` → BELUM, kurang 17 penutupan ([[Fakta Terukur]] §G, `tools/winlog.py`) |
| independensi antar-token untuk BH | `TIDAK-ADA` | token bergerak dalam satu pasar; "0 dari 12" bukan 12 trial bebas ([[06-Results/04 - Negative Results]] §6) |
| koreksi distribusi-t untuk n kecil | `TIDAK-ADA` | pilihan sadar: kelemahan diwarisi demi comparability; menggantinya keputusan yang harus dicatat, bukan bugfix sunyi |

## Uji di Fabius

Run yang bentuknya sudah benar: `tools/backtest.py` — ambang diimpor, 12 aset, BH α 0,10 lintas simbol, drop-best-fold; hasilnya net rugi **12/12** ([[Fakta Terukur]] §F). `tools/whale_sweep.py` — BH lintas wallet **dan** lintas horison; berkasnya sendiri menggantung pada `p_boot` yang belum terjelaskan (§H), jadi ia contoh kegagalan yang dilaporkan, bukan hasil. Yang dilarang catatan ini: memilih horison setelah melihat tabel. Urutan sah: pra-registrasi → jalankan → hitung semua tes → cetak semua baris, bukan hanya yang lolos.

## Batas dan mode gagal

- **Signifikansi ≠ materialitas.** Net 5 bps dengan p 1e-9 tetap mati oleh ongkos nyata 59 bps ([[Fakta Terukur]] §D).
- α 0,10 mengendalikan harapan penemuan palsu di antara yang dinyatakan lolos, bukan kebenaran per klaim — "lolos BH" bukan "token ini pengecualian".
- Jumlah tes tidak bisa diverifikasi pihak luar: artefak tidak merekam berapa varian yang sudah dicoba penulisnya sebelum yang dilaporkan — itu yang dikunci pra-registrasi ([[EV5 - Reproduksibilitas dan Pra-Registrasi]]), bukan catatan ini.
- Mean bisa digendong beberapa peristiwa; itu sebabnya trim teratas dan split-sample ada di halaman horison. Mean lolos yang medianya berlawanan arah = kesalahan laporan, bukan edge.
- Ini catatan epistemik, bukan metode: ia tidak punya tingkat terhadap pasar — yang di bawah adalah tingkat klaim-klaimnya.

## Tingkat bukti

`T3` untuk semua mode gagal di catatan ini (masing-masing punya artefak: anomali `p_boot`, "12/12", F-D16 yang belum tercapai); `T2` untuk pilihan statistik itu sendiri - koreksi selection-bias atas jumlah tes ada literatur terkenalnya (Bailey & López de Prado, *Deflated Sharpe Ratio*, SSRN `10.2139/ssrn.2460551`, [[Sumber dan Jangkauan]] #3) dan tidak kami reproduksi — BH, α 0,10, `MIN_SAMPLES=20` tidak kami uji lawan alternatif, hanya diwarisi dan dicatat asalnya.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami melaporkan semua horison dan semua tes yang dijalankan, termasuk satu p yang belum bisa kami jelaskan — karena itu aritmetika kami tidak perlu dipercaya bulat-bulat."
- **Dilarang:** "0 dari 12 lolos BH membuktikan tidak ada edge" (yang diuji sempit — [[10-Submissions/01 - Claims Cheat Sheet]]); "p < 0,05 = penemuan"; "whale sweep lolos p_boot 0,00025 di 30 hari" — angka itu tercemar dua kali: ongkos nol dan anomali yang belum terjelaskan.

**Terkait:** [[EV1 - Tingkat Bukti]] · [[EV2 - Jebakan Backtest]] · [[EV6 - Kalibrasi Ambang Terhadap Hasil]] · [[QT4 - Overfitting dan Validasi]] · [[06-Results/02 - Thresholds]] · [[Concepts/Lookahead Bound]] · [[Fakta Terukur]]
