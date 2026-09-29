---
tags: [overview, "O6"]
---

# 06 - Roadmap to the Deadline

**Bagian dari:** [[00-Overview/00 - Hub Overview]]
**Sumber:** [[08-Backlog/01 - Backlog]] · tenggat resmi 30 Sep **23:59 WIB**

**Ringkas:** sisa waktu dipakai untuk membuat klaim bisa diperiksa orang lain, bukan untuk menambah
fitur yang tidak bisa diverifikasi.

**Poin kunci (urutan, dengan apa yang didapat per langkah):**

| hari | kerja | selesai terlihat sebagai |
|---|---|---|
| 27 | P1 eksekusi nyata di 97 (deploy → 1 posisi buka&tutup) | tx `status=1`, `openPositionOf` terbaca, realized PnL dari event |
| 27–28 | P4 `seats.py` (5 kursi + rotasi di atas `seat_eligible`) | satu siklus draft kursi ter-anchor, alasan rotasi tercatat |
| 28 | P2 host gateway + P3 FE (builder pakai Vercel) | URL kartu agen bukan localhost; orang awam bisa lihat satu keputusan |
| 28–29 | P5 Uji A horison pendek (prospektif) | angka whale **tanpa** lookahead, walau n kecil |
| 29 | video 5 menit + README + form (`03 - Form Fields`) | naskah per scene, alamat ditempel dari repo |
| 30 | submit | repo publik, contract resolve di BscScan, tim terdaftar di Luma |

**Detail / risiko yang sudah kelihatan:**
- P1 bisa gagal bukan karena kode tapi karena gas testnet — guard `exec_deploy.py` sengaja menolak
  sebelum mengirim; top-up tower adalah jalurnya.
- Kalau Uji A tidak sempat terkumpul: jangan tulis apa pun yang menyiratkan "whale diuji bersih".
**29-30 Sep - yang tersisa, dengan jamnya (bukan urutan keinginan):**

| jam (UTC) | kerja | selesai terlihat sebagai |
|---|---|---|
| jam ini | **⑨ buku order** menyala penuh: daftar valid + `merge=union` + cakupan simbol kabar | `universe/record_book_depth.py --report` dengan rasio `bd:bdx` membaik dan >12 simbol punya >5 snapshot |
| **14:59Z 29 Sep** | vonis halaman 17 (watch, kerumunan maker di `wp`) | `python -X utf8 tools/day2_replicate.py --halaman 17` + hasil ditulis di halaman 17 |
| **17:13:25Z** | **vonis E9** - `vol-rendah` vs `vol-tinggi` | `tools/vol_ab.py` dengan tiga syarat + komposisi 25/25 slot |
| **20:04:56Z** | **vonis E12** - keluar 5 m vs tahan 30 m, posisi yang sama | `tools/hold_ab.py` empat syarat (termasuk umur baris harga keluar) |
| **21:37:45Z** | **vonis E16** - state imbalance buku order | `tools/book_prereg.py` + WAJIB komposisi simbol (jangkar vs simbol kabar) |
| setelah vonis | **P42** satuan dampak ke `tools/costs.py` + `skema_dampak` per slot | tiga varian `tools/impact_audit.py` jadi satu angka yang punya varian jelas |
| sebelum submit | **P2-P6b** jalur submission (host, kartu agen, form satu kontrak) | URL publik + form terisi dengan angka yang baris perintahnya ada di registry |
| kalau ada ruang | **P49/E17** trailing sebagai uji bentuk-distribusi (random-barrier placebo) | tabel `P(net <= -X)` + median vs placebo, bukan "untung/tidak" |

Yang **tidak** dikejar: mengubah ambang karena grid menunjukkan angka lebih bagus (P45/F-D45 memilih
maker=4 = mengulang F-D32), membalik arah E18/F-D44 yang gugur jadi "fade" (halaman 12 dan 22
menutup dua arah), dan menambah uji terkunci baru yang matang **setelah** tenggat - itu cuma
membeli hak untuk bilang "belum bisa diuji" dengan gaya yang lebih buruk.

- Yang **tidak** masuk roadmap: Greenfield (bukan bagian cerita agen resmi, dan decision-log
  per-keputusan pola terburuk untuk objek storage), mainnet (testnet sah + dana asli bukan harga
  yang boleh diasumsikan), dan mengejar "edge" baru tanpa jendela validasi.

**Terkait:** [[08-Backlog/01 - Backlog]] · [[START-HERE]]
