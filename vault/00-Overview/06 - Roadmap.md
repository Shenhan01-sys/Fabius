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
- Yang **tidak** masuk roadmap: Greenfield (bukan bagian cerita agen resmi, dan decision-log
  per-keputusan pola terburuk untuk objek storage), mainnet (testnet sah + dana asli bukan harga
  yang boleh diasumsikan), dan mengejar "edge" baru tanpa jendela validasi.

**Terkait:** [[08-Backlog/01 - Backlog]] · [[START-HERE]]
