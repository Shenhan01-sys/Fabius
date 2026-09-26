---
tags: [perkakas, "TL4"]
---

# TL4 - anchor.py dan --verify

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/anchor.py`, `02-Contracts/02 - Deployed on 97.md`

**Ringkas:** dua pekerjaan yang berbeda: **mengirim** keputusan nyata ke chain, dan **membaca ulang**
trail itu tanpa memercayai kami. Yang kedua yang membuat vault ini berguna.

**Poin kunci:**
- `--dry-run` mencetak apa yang AKAN dikirim; tanpa flag itu ia kirim. Tidak ada mode "kirim semua
  tanpa laporan".
- Guard saldo dihitung pada **plafon gas × jumlah baris** (terburuk, bukan rata-rata) → siklus yang
  kurang dana berhenti dengan **nol transaksi terkirim**, jadi tidak pernah ada jejak setengah.
- `chainId` dibaca & dibandingkan **sebelum** menandatangani: kegagalan yang dicegah adalah
  menandatangani tx untuk chain yang tidak kita baca.
- `--verify`: `id = keccak(agen, decisionHash, snapshotHash, chainid)` dihitung ulang dari berkas
  repo → `getAnchor(id)` dibaca → **6 field** dibandingkan (termasuk `asset` dan `agent`).
  Nol kunci, nol gas → auditor bisa menjalankannya.
- Temuan kontrak yang mengubah alat kami: `getAnchor` untuk id tak dikenal **tidak revert** — ia
  mengembalikan struct nol. Klasifikasi "belum di-anchor" yang mencari kata `reverted` jadi cabang
  mati, dan 4 keputusan terbaru tercetak "BEDA" seolah buktinya rusak. Sekarang tiga keadaan:
  `cocok` / `BEDA` / `BELUM DI-ANCHOR`.
- Bug yang ditemukan tes parser: offset string pada retur dinamis dihitung **relatif ke awal
  struct**, bukan ke awal retur. Tiga hash tetap cocok, jadi `chain==lokal: YA` tercetak **sambil**
  `asset` terbaca sampah — yang salah adalah field yang tidak dibandingkan.

**Terkait:** [[Concepts/Anchored Before Outcome]] · [[07-Testing/T2 - Anchor Verify]]
