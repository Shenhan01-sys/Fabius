---
tags: [testing, "T5"]
---

# T5 - Integrity Harness

**Bagian dari:** [[07-Testing/00 - Hub Testing]]
**Perintah (empat baris, jalan dari clone, tanpa kunci):**

```bash
python -X utf8 vault/scripts/check_links.py
python -X utf8 tools/verify_vendor.py
python -X utf8 universe/record_wallet_flow.py --report
python -X utf8 _research/check_garbled.py
```

**Dijalankan:** 27 Sep 2026 ±03:35 WIB (= 26 Sep 20:35Z) — empat baris `sama`, exit 0

## Keluaran

```text
berkas .md: 74 · target unik: 74
Broken: 0
Tanpa penunjuk (orphan): 0
Folder tanpa hub: 0
```

```text
  sama   docs/upstream-x402/x402BasePermit2Proxy.sol          0x276f1d092f740ede… 7411 B
  sama   docs/upstream-x402/x402ExactPermit2Proxy.sol         0x6af38108c14d82dc… 4055 B
  sama   contracts/vendor/x402/interfaces/ISignatureTransfer.sol 0x9ba755409cba5cad… 3755 B
  sama   docs/upstream-x402/LICENSE.txt                       0x50e6751797c50ded… 11324 B

upstream github.com/coinbase/x402 @ dd927a26cfefc98c24b3ec38b3a8f204dad0c60d
4/4 identik dengan yang dicatat manifest
```

Angka 74 itu **setelah** 12 penunjuk lama digulung ke `_archive/` (tidak dihitung, tidak ditaut).
Sebelumnya 86 — dan kalau kamu melihat halaman lain menulis jumlah berkas, yang berlaku adalah
keluaran run terakhir, bukan angka yang pernah dikatakanku.

`record_wallet_flow.py --report` → jumlah baris unik, rentang jam, maker & token (angka hari ini di
[[03-Data/D2 - Wallet Flow]] — **7.137 tx / 322 maker / 604 token / 10,14 jam**, dan itu dari
`origin/main`, bukan dari salinan lokal).

## Yang dibuktikannya — dan yang tidak

- ✅ `Broken: 0` = setiap rujukan di vault menunjuk halaman yang benar-benar ada. Aturan yang
  dipakai: **berkas yang tidak ditunjuk siapa-siapa adalah berkas yang tidak akan dibaca orang.**
- ✅ Vendor tidak disunat: salinan yang dipakai untuk menurunkan selector sama byte-nya dengan
  upstream pada commit yang di-pin (bukan `main`, yang bisa bergerak).
- ✅ Manifest dataset: sha256 per berkas + ukuran + ekor; kalau barisnya tidak bertambah, alatnya
  **exit non-zero** — pertumbuhan direkam, bukan diasumsikan.
- ❌ Keempatnya alat **kesehatan dokumen/kode**, bukan alat pembuktian pasar. Tidak satu pun
  menghasilkan klaim tentang win-rate.
- ⚠️ Yang masih terbuka di sini: 2 dari 62 sha256 snapshot universe **tidak bisa dihitung ulang**
  dari isi berkasnya; penyebabnya belum diketahui (dua hipotesis sudah dibantah dengan pengukuran).
  Lihat [[06-Results/03 - Not Yet Proven]] #21 dan [[08-Backlog/01 - Backlog]] P6.

## Kalau gagal

- `check_links` melaporkan `Broken` → jalankan `python -X utf8 vault/scripts/sync_vault.py` dulu,
  baru cari nama halaman yang berubah (sering penyebabnya rujukan bentuk pendek `[[TL7]]`).
- `check_garbled.py` menandakan CJK di komentar Indonesia → itu pernah terjadi 4×; perbaiki glyph,
  jangan perluas daftarnya.
- `verify` vendor gagal di mesin lain → `.gitattributes` (`-text` di jalur vendor) belum terpakai;
  tanpa itu git menormalisasi CRLF→LF dan hash-nya beda.

**Terkait:** [[Conventions]] · [[04-Tools/TL7 - measurement harness]]
