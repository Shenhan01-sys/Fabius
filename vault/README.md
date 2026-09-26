---
tags: [reference]
---

# README — vault Fabius

Dua kebiasaan yang membuat folder ini masih layak dipercaya:

1. **Angka dari perintah, bukan dari ingatan.** Setiap jumlah, alamat, gas, atau tanggal di sini
   harus bisa direproduksi dari dalam repo. Kalau halaman dan run berbeda, **run menang** —
   perbaiki halamannya. Lihat [[Conventions]] §2 dan [[07-Testing/01 - Test Commands]].
2. **Koreksi tidak dihapus, dipajang.** Kami salah beberapa kali di proyek ini (menyimpulkan
   "perekam mati 24 jam" dari salinan lokal yang tertinggal 78 commit; menyimpulkan "calldata
   salah" dari alat perbandingan yang itself rusak). Semuanya ada di
   [[00-Overview/05 - Corrections]], lengkap dengan apa yang membuktikannya. Vault yang tidak
   punya halaman koreksi biasanya bukan vault yang benar — cuma vault yang malu.

Mulai dari [[START-HERE]]. Perawatan: `python -X utf8 -u scripts/sync_vault.py` lalu
`python -X utf8 -u scripts/check_links.py` (target `Broken: 0`).
