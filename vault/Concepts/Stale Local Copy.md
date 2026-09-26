---
tags: [concept, "stale-local-copy"]
---

# Stale Local Copy — salinanmu bukan keadaan sistem

**Ringkas.** Untuk sistem yang penulisnya mesin lain (GitHub Actions, API pihak ketiga), jumlah
baris di diskamu bukan ukuran. Ukurannya: commit di `origin`.

**Kejadian nyata 27 Sep.** Aku melaporkan "perekam ⑦ mati 24 jam" setelah membaca
`universe/wallet-flow.jsonl` di laptop — padahal working copy-ku **78 commit tertinggal**. Di
origin perekam mengirim commit tiap ±3,5 menit tanpa henti; lubang nyatanya ±6 menit. Klaim
salah itu sempat masuk pesan ke builder dan commit message, lalu dicabut.

**Aturan turunannya.**
- `git fetch` dulu, baru simpulkan apa pun tentang "hidup/mati".
- Untuk hal ber-waktu: sumber waktu = timestamp pihak ketiga (commit Actions, epoch respons API),
  bukan jam laptop — ia pernah melompat setelah tidur.
- Untuk hal ber-status: kalau alat hanya bisa membaca satu berkas, ia tidak boleh mengklaim melihat
  sistem.

Ini pasangan dari [[Unmeasured Is Not Clean]]: keduanya tentang kesimpulan yang tampak berbukti
tapi sumbernya salah pilih.

Lihat: [[03-Data/D2 - Wallet Flow]] · [[00-Overview/05 - Corrections]]
