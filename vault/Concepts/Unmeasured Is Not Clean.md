---
tags: [concept, "unmeasured-not-clean"]
---

# Unmeasured Is Not Clean

**Ringkas.** "Tidak ada angka" bukan angka nol. Setiap kali Fabius butuh status keamanan kontrak,
ia memakai empat keadaan: `OK` / `BLOCKED` / `DISAGREE` / `UNMEASURED` — dan yang terakhir
**tidak** diperlakukan seperti bersih.

**Kenapa keras.** Kalau `UNMEASURED` disamakan dengan bersih, gerbang bisa di-bypass cukup dengan
membuat panggilannya gagal, dan kegagalan itu tidak meninggalkan bekas di data. Ini pola kegagalan
yang sama persis dengan yang kami temukan di tempat lain: `getAnchor(id)` tidak revert tapi
mengembalikan struct nol; hasil Dune yang berhenti di halaman pertama; salinan lokal dianggap
keadaan sistem.

**Terapan.** `tools/security_gate.py` (4 status; terpicu nyata saat GMGN membalas
`is_honeypot=null`), `03-Data/01 - Dataset.md` (baris tanpa alasan risiko dipisah dari baris
"bersih"), `06-Results/03 - Not Yet Proven.md`.

Lihat: [[One-Way Gate]] · [[Stale Local Copy]]
