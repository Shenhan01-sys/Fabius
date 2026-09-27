---
tags: [testing, "T5"]
---

# T5 - Integrity Harness

**Bagian dari:** [[07-Testing/00 - Hub Testing]]
**Perintah (enam baris; lima pertama jalan dari clone tanpa kunci):**

```bash
python -X utf8 vault/scripts/check_links.py
python -X utf8 tools/verify_vendor.py
python -X utf8 universe/record_wallet_flow.py --report
python -X utf8 vault/scripts/hub_shape.py
python -X utf8 vault/scripts/prepush_check.py --self-test
python -X utf8 _research/check_garbled.py
```

**Dijalankan:** 27 Sep 2026 ±03:35 WIB (= 26 Sep 20:35Z) — empat baris `sama`, exit 0

## Keluaran

```text
berkas .md: 79 · target unik: 79
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

```text
total halaman: 92 · tanpa YAML: 0 · YAML tanpa `tags:`: 0
```

Dua angka berkas yang berbeda itu **bukan pertentangan**: `check_links` menghitung 79 (isi `_archive/`,
`Templates/`, `Sessions/` memang dikecualikan dari graf), `structure_report` menghitung 92 karena ia
melihat semua berkas `.md` di disk. Yang boleh dikutip sebagai "vault terhubung" hanya yang pertama.
Menyebut salah satu tanpa menyebut definisinya adalah cara tercepat membuat dua halaman tidak pernah
lagi cocok.

`record_wallet_flow.py --report` + `_research/panel_stats.py` *(workspace)* → angka panel hari ini di
[[03-Data/D2 - Wallet Flow]] — **8.053 tx / 348 maker / 643 token / 11,82 jam**, dan itu dibaca dari
`origin/main`, bukan dari salinan lokal.

## Yang dibuktikannya — dan yang tidak

- ✅ `Broken: 0` = setiap rujukan di vault menunjuk halaman yang benar-benar ada. Aturan yang
  dipakai: **berkas yang tidak ditunjuk siapa-siapa adalah berkas yang tidak akan dibaca orang.**
- ✅ Vendor tidak disunat: salinan yang dipakai untuk menurunkan selector sama byte-nya dengan
  upstream pada commit yang di-pin (bukan `main`, yang bisa bergerak).
- ✅ Manifest dataset: sha256 per berkas + ukuran + ekor; kalau barisnya tidak bertambah, alatnya
  **exit non-zero** — pertumbuhan direkam, bukan diasumsikan.
- ✅ `prepush_check.py` = gerbang **pra-push** aturan atribusi (F-D22): baca pesan commit pada
  `origin/master..HEAD`, non-zero kalau ada trailer AI. Terukur 27 Sep: self-test 6/6; `--all` =
  1 pelanggaran / 393 commit (`08cb049`, ditinggalkan sadar). Ia juga jalan di server lewat
  `.github/workflows/attribution-guard.yml` — jadi tidak bergantung pada siapa yang menyetir.
  Rinci di [[07-Testing/T7 - Pre-Push Gate]].
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
