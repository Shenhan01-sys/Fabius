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
forge test                                       # 39 lulus: 21 DecisionAnchor + 18 ExecutionVault  (2 Okt: 63 = + 24 SignalAnchor/LockRegistry)
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

**Operator (sejak 2 Okt 2026; paper penuh):**

```bash
# ledger paper maju - tanpa kunci; jaringan hanya untuk --feed
python -X utf8 -m engine.cli ledger verify          # hitung ulang tiap tick/settle dari ledger/bars
python -X utf8 -m engine.cli ledger report
python -X utf8 -m engine.cli ledger fd16            # F-D16 pada data maju (P88): LOLOS / BELUM CUKUP DATA / TIDAK LOLOS
python -X utf8 -m engine.cli ledger pembunuh        # pembunuh terstruktur B1/B3 (P107): USULAN sampai dikunci; YA / BELUM / TIDAK
python -X utf8 -m engine.cli ledger skor            # skor maju + berpasangan (P85) - bahan keputusan slot
python -X utf8 -m engine.cli book verify            # buku slot hidup: rantai + keputusan dihitung ulang (P87); `book epoch --write` = penulis
python -X utf8 tools/pin_book.py --verify           # book_sha epoch terakhir di LockRegistry
python -X utf8 tools/lock_spec.py --file engine/locks/fd16.lock.json --name FABIUS-FD16-MAJU-v1 --verify   # kunci F-D16 maju di chain (F-D84)
python -X utf8 tools/paper_tick.py --dry-run         # rencana tick tanpa menulis
python -X utf8 tools/test_census.py                  # suite Python + sensus: lulus / DILEWATI / GAGAL (P110); CI: gh run list --workflow tests.yml
gh run list --workflow paper-ledger.yml --limit 5    # rantai GitHub = penulis TUNGGAL ledger (F-D78)

# M3 di chain 97 - baca tanpa kunci
cast call 0x9B78200beFbbBe836585d31bd5b6dB32587064f3 "commitCount()(uint256)" --rpc-url https://bsc-testnet.publicnode.com
python -X utf8 tools/signal_commit.py --committer 0xCA9c7322210E9a7F7d0953c862d4Ef60cC0D64A4    # rencana komit/ungkap
python -X utf8 tools/verify_signals.py                  # pemeriksa PUBLIK: komit + ungkap vs ledger + bar; vonis per bot per bar (P106)
python -X utf8 tools/worker_watch.py                   # penjaga LUAR worker (P111): tick terakhir sudah dikomit + diungkap? (stdlib, tanpa kunci)

# web: landing tingkat 0 + server MCP untuk agen (P113/P114) - butuh node 20+; tanpa kunci, tanpa env var
python -X utf8 tools/web_snapshot.py                    # data landing -> web/public/data/snapshot.json
cd web && npm ci && npm run build && npx next start -p 3006                               # landing di :3006, MCP di :3006/mcp
npx @modelcontextprotocol/inspector --cli http://localhost:3006/mcp --transport http --method tools/list   # klien MCP resmi: 8 alat
python -X utf8 tools/web_snapshot.py --if-changed       # tulis hanya bila isi berubah; keluar 3 = chain tak terbaca, snapshot lama dipertahankan
gh workflow run web-snapshot.yml                         # snapshot landing dari GitHub (biasanya dipicu rantai paper-ledger sesudah tick); push -> Vercel
python -X utf8 tools/waitlist.py --poll                 # daftar tunggu P115 (butuh ALERT_TELEGRAM_*; rantai paper-ledger menjalankannya tiap 5 menit)

# eksekusi venue (epik 10): kertas-venue dulu, uang nyata hanya canary pipa <= 10 USDT atas kata builder (F-D92)
python -X utf8 tools/kertas_eksekusi.py filters        # snapshot lot/min notional venue -> ledger/kertas/filter/
python -X utf8 tools/kertas_eksekusi.py run            # eksekusi B1 di atas kertas (rantai GitHub menjalankannya tiap hari)
python -X utf8 tools/kertas_eksekusi.py ringkas        # tracking error vs paper, bobot terpenuhi, vs ambang PRD §6

# peninjau pengajuan penerbit (P83): k keluarga dari registri ledger/pengajuan/registri.jsonl; pratinjau tidak mengikat
python -X utf8 -m engine.cli review --file engine/examples/submission.example.json --data ledger/bars            # pratinjau (alpha A1/k)
python -X utf8 -m engine.cli review --file <sub.json> --data <dir> --signature 0x.. --nonce N --deadline D --catat  # resmi: dicatat, memakan anggaran

# Railway (butuh login CLI builder; JANGAN `railway environment config --json` / `railway variable list --json|--kv`: mencetak kunci)
railway logs --service fabius-engine --lines 40
railway logs --service fabius-probe --lines 80                                       # mode bayangan tahap 2+3 (F-D86): VONIS bayangan
# alert (P101): pasang ALERT_TELEGRAM_TOKEN + ALERT_TELEGRAM_CHAT di Railway (dashboard, JANGAN lewat chat); start ulang -> pesan "worker mulai"
python -X utf8 tools/railway_up.py [--service fabius-probe]                                      # deploy dari HEAD
```

Perekam wallet-flow (`wallet-flow.yml`) **dihentikan 2 Okt** (F-D81); blok 3-4 di atas tetap benar sebagai riwayat riset agen BSC.

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
| `BINANCE_API_KEY` / `BINANCE_SECRET_KEY` / `BINANCE_API_ENV` (`testnet` bawaan, `prod`) | `tools/venue_binance.py` (`BinanceFutures`), kelak eksekutor Railway `fabius-exec` (P118) | order futures USDⓈ-M di testnet (tanpa dana nyata) atau prod (sub-akun Agentic) | prod hanya bila kunci TANPA izin tarik (`check_no_withdraw`, start ditolak bila tidak) + kata builder per venue (F-D91/F-D92); kunci testnet dibuat di https://testnet.binancefuture.com (tab API Key); dipasang builder lewat dashboard Railway, JANGAN lewat chat |

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
