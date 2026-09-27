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
  ! anchorCount() = 17 tapi hanya 11 baris yang terpelacak di ['direction-20260924Z.jsonl', 'direction-20260925.jsonl']
     -> yang diperiksa di bawah adalah baris yang TERPELACAK, bukan seluruh isi kontrak. Sisanya
        keputusan siklus awal, sebelum format rekaman ini ada; belum diurutkan (P6b).
verify : 11 keputusan dari 2 berkas | agen 0x4bb30E3b3bc22082c1935fE3bE7c07448e69c862
kontrak: 0xDD162AFB5F5f92d5092f845A93660e3B38259330 | anchorCount() di chain = 17 | rpc https://bsc-testnet.drpc.org

roster : getAgent() -> handler 0x4bb30e3b3bc22082c1935fe3be7c07448e69c862 aktif=True | countByAgent = 17  (dijawab kontrak, bukan oleh kami)

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

### Run ulang 28 Sep 2026 — keadaan hidup (blok di atas tetap sejarah, tidak disunat)

```text
  ! anchorCount() = 19 tapi hanya 13 baris yang terpelacak di ['direction-20260924Z.jsonl', 'direction-20260925.jsonl', 'direction-20260927Z.jsonl']
verify : 13 keputusan dari 3 berkas | agen 0x4bb30E3b3bc22082c1935fE3bE7c07448e69c862
kontrak: 0xDD162AFB5F5f92d5092f845A93660e3B38259330 | anchorCount() di chain = 19 | rpc https://bsc-testnet.drpc.org
roster : getAgent() -> handler ... aktif=True | countByAgent = 19  (dijawab kontrak, bukan oleh kami)
13/13 yang ADA di chain cocok word-per-word (agen, asset, verdict, 3 hash) | 0 tidak cocok | 0 belum di-anchor
```

`python -X utf8 tools/verdict_counts.py` pada hari yang sama: `anchorCount()` = **19**,
`countByVerdict` = **4 Enter / 15 Abstain** (4 + 15 = 19, tidak ada verdict ketiga). Berkas
`direction-20260927Z.jsonl` ikut terbaca sekarang — itu hasil dari run end-to-end 27 Sep
(commit `d00863e`), bukan dari perubahan verifier.

## Yang dibuktikannya — dan yang tidak

- ✅ Yang dihitung repo (`keccak(agent, decisionHash, snapshotHash, chainId)`) **ada di chain dengan
  isi yang sama**, termasuk tiga hash dan field `asset`.
- ✅ Split yang terbaca: `verdict=0` = **Enter**, `verdict=1` = **Abstain** (urutan enum di
  `contracts/DecisionAnchor.sol`). Dari 11 yang terpelacak: **2 Enter** (dua-duanya MARSCOIN short —
  persis dua peristiwa yang dinilai [[04-Tools/TL5 - ledger]]) dan **9 Abstain**.
- ✅ Baris `roster :` dijawab **kontrak**, bukan oleh kami: `getAgent()` menunjuk handler = alamat
  agen, `aktif=True`, `countByAgent()` = 17 = `anchorCount()`. Ini yang membuat alamat boleh datang
  dari `deployments/97.json` tanpa mengubah verifier jadi kepercayaan buta pada repo — berkas repo
  harus bisa dibantah, dan inilah bantahannya.
- ✅ Perintah ini jalan **dari clone bersih** (0 kunci, 0 gas, tanpa `data/`): 4/4 di
  [[07-Testing/T6 - Clean Clone Evidence]]. Sebelumnya ia **gagal** di clone karena `AGENT_ADDRESS`
  cuma ada di `.agent.env` — lihat [[00-Overview/05 - Corrections]].
- ⚠️ Chain vs repo **tidak sama banyak**, dan ini lubang yang kuukur, bukan kusimpulkan:
  `anchorCount()` = **17** (3 Enter + 14 Abstain, dari `countByVerdict`) sedangkan verifier membaca
  **11** keputusan (2 Enter + 9 Abstain) dari 2 berkas. 6 entri — termasuk 1 Enter — ada di chain tanpa
  baris sumber yang bisa dibaca repo. Perintah pembanding: `python -X utf8 tools/verdict_counts.py`.
  Dijadikan item terbuka ([[08-Backlog/01 - Backlog]] P6b). Sampai itu terurut, angka yang boleh dikutip
  adalah **11** (yang terbuktikan dari berkas), **bukan 17**.
  **28 Sep:** keduanya bertambah — **19** di chain vs **13** terpelacak — tapi selisihnya **tetap
  6 entri**, jadi P6b tidak tertutup oleh pertambahan angka; yang boleh dikutip sekarang **13**.
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
