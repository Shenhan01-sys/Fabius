---
tags: [concept, "pip-vs-retro"]
---

# Point-in-Time vs Retro-updatable

**Ringkas.** Ada dua jenis data yang tampak sama dan tidak boleh dicampur: yang **terkunci pada saat
ia direkam** (commit GitHub, anchor di chain, sha256 di manifest) dan yang **bisa disusulkan/diubah
setelahnya** (baris Dune punya `_updated_at`; API yang paging-nya diabaikan = tidak ada riwayat sama
sekali).

**Aturan yang dipakai di Fabius.** Sumber yang bisa disunting retro **tidak pernah** jadi saksi
waktu; dia boleh jadi bahan statistik. Karena itu: entri ⑦ bisa datang dari Dune, **harga forward**
datang dari kline yang kami tarik sendiri, dan klaim "kami tahu sebelum hasilnya ada" hanya datang
dari commit + anchor.

**Kasus nyata.** `flow_test`/`whale_sweep` memisahkan peran ini dengan sengaja dan menuliskannya di
kepala file. Tanpa pemisahan itu, "+1.717 bps" akan terbaca sebagai penemuan, padahal sumbernya
bisa disusulkan.

Lihat: [[Concepts/Anchored Before Outcome]] · [[03-Data/D4 - Dune]]
