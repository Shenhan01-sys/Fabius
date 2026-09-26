---
tags: [kontrak, "C5"]
---

# C5 - Vendored x402 Sources

**Bagian dari:** [[02-Contracts/00 - Hub Contracts]]
**Sumber:** `contracts/vendor/x402/VENDORED.json`, `docs/upstream-x402/`,
`_research/vendored_x402.py`

**Ringkas:** sumber x402 upstream ada di repo ini sebagai **bacaan**, dengan sha256 tercatat. Yang
kami panggil adalah kontrak kanonis yang sudah ter-deploy, bukan hasil kompilasi vendor ini.

**Poin kunci:**
- Upstream: `github.com/coinbase/x402` @ commit `dd927a26cfefc98c24b3ec38b3a8f204dad0c60d`
  (bukan `main` — vendor yang bergerak bukan vendor, itu dependensi hantu).
- `interfaces/ISignatureTransfer.sol` ikut dikompilasi (interface-only, aman untuk shanghai);
  dua proxy implentasinya ditaruh di `docs/upstream-x402/` dan **tidak** dikompilasi: mereka memakai
  `mcopy`, dan memaksanya masuk akan merusak profil default (terjadi nyata: 4 error kompilasi di
  `vendor/openzeppelin/.../Bytes.sol`).
- Panggilan nyata memakai interface kami sendiri: `contracts/vendor/x402/IX402ExactPermit2Proxy.sol`.
  Selector **diturunkan dari tipe parameternya**, tidak ditulis tangan.
- Audit integritas **dari dalam clone**: `python -X utf8 -u tools/verify_vendor.py` (hash + ukuran disk vs
  manifest; terukur 27 Sep: 4/4 identik). Mode `compare` di `_research/vendored_x402.py` membanding-
  kan salinan POC dengan upstream — itu alat workspace, jalurnya di luar repo produk, jadi jangan
  dipakai sebagai bukti yang bisa dijalankan orang lain.
- `.gitattributes` memberi `-text` ke jalur vendor & dataset. Tanpa itu git menormalisasi LF→CRLF
  di Windows dan membuat klaim "verbatim"/hash gagal di mesin orang lain.

**Terkait:** [[05-Ecosystem/02 - x402 Payment]] · [[07-Testing/T4 - x402 Fork Suite]]
