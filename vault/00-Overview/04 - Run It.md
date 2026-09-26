---
tags: [overview, "O4"]
---

# 04 - Run It

**Bagian dari:** [[00-Overview/00 - Hub Overview]]
**Sumber:** semua perintah di halaman ini pernah dijalankan; keluarannya di `07-Testing/`

**Ringkas:** satu halaman untuk menjalankan dan memverifikasi Fabius dari clone. Tidak ada kunci,
tidak ada dana, tidak ada server yang harus nyala untuk membuktikan klaim utamanya.

**Poin kunci:**

```bash
# 0. prasyarat: foundry (forge), python 3.12 + eth_account/eth_abi/eth_utils
git clone https://github.com/Shenhan01-sys/Fabius && cd Fabius
git submodule update --init --recursive          # vendor/: OZ + forge-std

# 1. kontrak & angka uji
forge test                                       # 39 lulus: 21 DecisionAnchor + 18 ExecutionVault
FOUNDRY_PROFILE=fork forge test --fork-url bscTestnet      # 63 lulus, termasuk 9 fork settlement x402
FOUNDRY_PROFILE=fork forge test --match-contract ExecutionVaultTest   # 18 lulus, di kedua profil

# 2. klaim inti, dibaca ulang tanpa kunci dan tanpa gas
python -X utf8 -u tools/anchor.py --verify               # cocok / BEDA / BELUM DI-ANCHOR
python -X utf8 -u tools/verify_vendor.py                 # vendor identik manifest (nol jaringan)

# 3. siklus agen
python -X utf8 -u universe/record_bsc_universe.py        # snapshot universe (satu tarikan)
python -X utf8 -u tools/direction.py --top 5 --emit      # arah + gerbang ①④⑥ + hash
python -X utf8 -u tools/security_gate.py --emit          # ④ dari dua sumber
python -X utf8 -u tools/ledger.py                        # nilai posisi jatuh tempo (atau: belum)

# 4. angka riset
FOUNDRY_PROFILE=fork forge build && python -X utf8 -u tools/backtest.py --mom-only --flip
python -X utf8 -u tools/whale_sweep.py --days 90         # butuh DUNE_API_KEY
```

**Detail:**
- `bscTestnet` = alias di `foundry.toml` → **publicnode**, bukan drpc. Alasan: drpc sehat untuk
  `eth_call` tapi menolak state per-blok yang diminta `--fork-url` (terukur: `Unknown block`).
- Blok 1–2 dan `ledger.py` bisa dijalankan **tanpa kunci apa pun**. Itu bagian dari klaimnya.

## Kunci yang dibaca alat (nama saja — nilainya tidak pernah ada di repo)

| variabel | dibaca oleh | apa yang ia bisa beli | pagar yang menempel |
|---|---|---|---|
| `AGENT_PRIVATE_KEY` / `AGENT_ADDRESS` | `tools/anchor.py:74-100`, `tools/exec_deploy.py`, `tools/verify_deploy.py:203` | tanda tangan anchor + tx eksekusi di **97** | hanya alamat yang ada di `DecisionAnchor` roster; cap kontrak tetap memotong |
| `GMGN_API_KEY` | `universe/record_bsc_universe.py:50`, `universe/record_wallet_flow.py`, workflow `universe-hourly.yml:50` / `wallet-flow.yml:110` | aliran smart money/KOL + `token/security` | route privat butuh `timestamp` + `client_id` (UUID sekali-pakai, `record_bsc_universe.py:86`); demo key ditolak server |
| `JEV_API_KEY` / `TYPESAFE_API_KEY` | `tools/judge.py:69-76`, `tools/probe_bynara.py:25` | panggilan penilai System-One | haknya **mengurangi** saja ([[01-Agent/A3 - One-Way Gates]]); tanpa kunci → `abstain`, bukan gagal |
| `DUNE_API_KEY` | `tools/dune_flow.py` (`dune_key()`), `tools/whale_sweep.py`, `tools/smartmoney_score.py` | kueri agregat historis BSC | kreditnya terbaca di respons (`execution_cost_credits`) — [[03-Data/D4 - Dune]] |
| `X402_SKEW` (opsional, default **15**) | `tools/x402_client.py:145` | koreksi jam laptop vs kepala chain | terlalu kecil → settlement revert **tanpa data** |

Berkas: `.agent.env`, `.jev.env`, `.deployer.env` — ketiganya di-`gitignore`; workflow Actions memakai
**repository secret**, bukan berkas. Yang tidak ada di tabel dan tidak akan pernah ada: seed,
kunci mainnet, dana nyata.

- `exec_deploy.py` dan `x402_*` butuh `.agent.env`. Gateway x402 sementara hidup di mesin kami —
  [[05-Ecosystem/03 - Discovery Gap]].
- **Koreksi 27 Sep:** versi halaman ini menyebut `tools/execute_live.py`; berkas itu tidak ada yang
  menjalankan posisi lewat kontrak (`exec_deploy.py` hanya men-deploy). Jalur buka/tutup posisi nyata
  memang **belum** ada script-nya — itu isi [[08-Backlog/01 - Backlog]] P1, bukan hal yang bisa
  dijalankan hari ini.

## Hygiene kunci (temuan 27 Sep, belum sepenuhnya beres)

Satu ekspor sesi panjang pernah diletakkan **di dalam folder repo Fabius** dan berisi, teks terang:
`AGENT_PRIVATE_KEY`, Dune key, GMGN key, Jev key. Diperiksa dengan `git grep` di `HEAD`: **tidak ada
satu pun yang pernah ter-commit**, dan `.gitignore` kini memblokir pola `qwen-code-export-*.md`
supaya satu `git add -A` yang tidak sengaja tidak bisa mengubahnya jadi commit yang tidak bisa
ditarik kembali. Repo ini publik, jadi celahnya bukan "nanti kalau di-push" — celahnya adalah satu
perintah yang salah ketik.

Yang masih perlu tindakan builder (bukan kami):
- ekspor itu masih ada di disk; paling aman dipindah keluar folder repo
- **rotasi** kunci yang pernah tertulis di dalamnya — private key agen dan tiga API key. Nilai buktinya
  rendah (testnet), tapi kebocoran kebiasaan menaruh kunci di folder repo persis yang membuat
  `scan_tracked_secrets.py` ada di workspace ini.

**Terkait:** [[Quick-Reference]] · [[07-Testing/01 - Test Commands]] ·
[[02-Contracts/C3 - ExecutionVault]] · [[03-Data/D5 - Record Schemas]]
