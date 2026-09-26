---
tags: [concept, "anchored-before-outcome"]
---

# Anchored Before Outcome — urutannya adalah produknya

**Ringkas.** Nilai satu anchor bukan "kami menyimpan hash", tapi **urutan**: keputusan ditulis →
hash masuk chain → hasilnya baru ada belakangan. Yang dijual adalah ketidakmungkinan menyunting
masa lalu, bukan kecerdasan tebakannya.

**Konsekuensi yang tidak nyaman.** Karena urutannya yang dijunjung, kami **tidak boleh** menarik
anchor yang ternyata salah, dan tidak boleh menghapus penolakan. 14 dari 17 anchor adalah `ABSTAIN`
— justru itu yang membuat 3 sisanya berarti.

**Dua syarat supaya klaim ini tidak melunak jadi slogan:**
1. jejaknya harus bisa dibaca ulang oleh orang lain tanpa memercayai kami
   (`tools/anchor.py --verify`: hitung id dari berkas repo, baca `getAnchor` dari chain, bandingkan
   6 field — nol kunci, nol gas);
2. dan sumber datanya juga harus ber-timestamp pihak ketiga, bukan jam kami
   (`universe/manifest.txt`, `wallet-flow-manifest.txt`; lihat [[Stale Local Copy]]).

**Yang tidak dibuktikannya:** sama sekali tidak ada. Anchor tidak membuat keputusan kami benar.
Itu urusan [[06-Results/00 - Hub Results]].

Lihat: [[02-Contracts/01 - DecisionAnchor]] · [[One-Way Gate]]
