---
tags: [testing, "T2"]
---

# T2 - Anchor Verify

**Bagian dari:** [[07-Testing/00 - Hub Testing]]
**Perintah:** `python -X utf8 tools/anchor.py --verify`
**Dijalankan:** 27 Sep 2026 ±03:30 WIB (= 26 Sep 20:29Z) di mesin ini
**Prasyarat:** tidak ada. Tidak kunci, tidak gas, tidak `.agent.env`. Ini penting: halaman ini harus
bisa dijalankan orang yang sama sekali tidak percaya kami.

## Keluaran

```text
verify : 11 keputusan dari 2 berkas | agen 0x4bb30E3b3bc22082c1935fE3bE7c07448e69c862
kontrak: 0xdd162afb5f5f92d5092f845a93660e3b38259330 | anchorCount() di chain = 17 | rpc https://bsc-testnet.drpc.org

  MARSCOINUSDT@perp      cocok  blok_waktu=1790280380 verdict=0 id=0x1826f4dcb0c21645…
  GENIUSUSDT@perp        cocok  blok_waktu=1790280383 verdict=1 id=0x7defe9e31f66aa3b…
  TACUSDT@perp           cocok  blok_waktu=1790280390 verdict=1 id=0x50439c6f28b29ed8…
  ASTEROIDUSDT@perp      cocok  blok_waktu=1790280392 verdict=1 id=0x7367b19274f262da…
  BREWUSDT@perp          cocok  blok_waktu=1790276681 verdict=1 id=0xadcc70474123ed13…
  GSTOCKUSDT@perp        cocok  blok_waktu=1790276684 verdict=1 id=0x7de9f26af4d65739…
  STONKSUSDT@perp        cocok  blok_waktu=1790276688 verdict=1 id=0xdbc1795c645f8e75…
  MARSCOINUSDT@perp      cocok  blok_waktu=1790276692 verdict=0 id=0x0f5ff29e327902eb…
  FLORKUSDT@perp         cocok  blok_waktu=1790276696 verdict=1 id=0x4ae5647313082fff…
  TACUSDT@perp           cocok  blok_waktu=1790276699 verdict=1 id=0x6f58d55bf9e27a54…
  FLNCUSDT@perp          cocok  blok_waktu=1790276704 verdict=1 id=0x3becd919eb3fdced…

11/11 yang ADA di chain cocok word-per-word (agen, asset, verdict, 3 hash) | 0 tidak cocok | 0 belum di-anchor
```

## Yang dibuktikannya — dan yang tidak

- ✅ Yang dihitung repo (`keccak(agent, decisionHash, snapshotHash, chainId)`) **ada di chain dengan
  isi yang sama**, termasuk tiga hash dan field `asset`.
- ✅ Split yang terbaca: `verdict=0` = **Enter**, `verdict=1` = **Abstain** (urutan enum di
  `contracts/DecisionAnchor.sol`). Dari 11 yang terpelacak: **2 Enter** (dua-duanya MARSCOIN short —
  persis dua peristiwa yang dinilai [[04-Tools/TL5 - ledger]]) dan **9 Abstain**.
- ⚠️ Chain vs repo **tidak sama banyak**, dan ini lubang yang kuukur, bukan kusimpulkan:
  `anchorCount()` = **17** (3 Enter + 14 Abstain, dari `countByVerdict`) sedangkan verifier membaca
  **11** keputusan (2 Enter + 9 Abstain) dari 2 berkas. 6 entri — termasuk 1 Enter — ada di chain tanpa
  baris sumber yang bisa dibaca repo. Perintah pembanding: `python -X utf8 tools/verdict_counts.py`.
  Dijadikan item terbuka ([[08-Backlog/01 - Backlog]] P6b). Sampai itu terurut, angka yang boleh dikutip
  adalah **11** (yang terbuktikan dari berkas), **bukan 17**.
- ❌ Tidak membuktikan keputusannya **benar**. Nilainya dinilai terpisah di
  [[04-Tools/TL5 - ledger]].
- ❌ Tidak membuktikan saya tidak bisa menulis jejak baru — hanya yang **lama** tidak bisa diubah.
  Anchor tidak pernah di-update; tidak ada fungsi untuk itu ([[Concepts/Anchored Before Outcome]]).

## Kalau gagal

- Semua `BEDA` → cek chainId dulu (`chain_check`), lalu fork/`rpc` yang dipakai; `asset` ikut
  dibandingkan sejak 25 Sep, jadi offset string yang salah kini bunyi, bukan diam.
- `TypeError ... int too large` saat decode → ingat offset string retur **relatif ke awal struct**
  (sudah diperbaiki; tes: `test_decode_anchor.py`).
- 0 keputusan ditemukan → `decisions/` kosong di clone-mu; tarik branch `main` (folder ini ikut
  di-commit, dataset besar di-`gitignore` dan sha256-nya lewat manifest).

**Terkait:** [[04-Tools/TL4 - anchor and verify]] · [[02-Contracts/02 - Deployed on 97]]
