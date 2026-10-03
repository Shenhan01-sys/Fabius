---
tags: [reference]
---

# Quick-Reference

Semua yang biasa dicari, satu baris per fakta, **dengan sumber angkanya**. Angka tanpa sumber
dihapus saat audit, bukan disimpan sopan-sopanan.

## Alamat & kontrak

| apa | nilai | dari mana |
|---|---|---|
| DecisionAnchor (chain 97) | `0xdd162afb5f5f92d5092f845a93660e3b38259330` | [[02-Contracts/02 - Deployed on 97]] |
| ExecutionVault (chain 97) | `0x2743cD33C8790437594E119289838F35c0d1d290` | ter-deploy 27 Sep; cap 5 unit/hari, 1 unit/posisi |
| DemoPair (97) | `0x6f93d787bBE99A6842CCa511ccB3b8D6d976696E` | x·y=k, fee 30 bps, spot 2,0000 |
| DemoAsset (97) | `0x4180A42A119F0B5480637900679C0AaFB1F2a8d7` | ERC20 demo 6 desimal |
| **manifest alamat** | `deployments/97.json` (ter-track) | 8 alamat (10 sejak 2 Okt: + LockRegistry, SignalAnchor) + cek bytecode dari chain — inilah yang membuat `--verify` jalan di clone |
| agen (penanda-tangan anchor) | `0x4bb30E3b3bc22082c1935fE3bE7c07448e69c862` | env → `deployments/97.json` → derivasi kunci; **dibantah ke kontrak** lewat `getAgent()`/`countByAgent()` = 17, aktif=True |
| ERC-8004 `IdentityRegistry` (chain 97) | `0x8004A818BFB912233c491871b3d84c89A494BD9e` | [[05-Ecosystem/01 - ERC-8004 Identity]] |
| tokenId agen | **2494** | `python -X utf8 -u tools/x8004_register.py --verify` |
| x402 proxy kanonis | `0x402085c248EeA27D92E8b30b2C58ed07f9E20001` (ada kode di 56 & 97) | [[05-Ecosystem/02 - x402 Payment]] |
| Permit2 | `0x000000000022D473030F116dDEE9F6B43aC78BA3` | sama |
| X402DemoToken (koin demo kami) | `0xB11D90214089684081F57A03d3300E20725297f8` | `python -X utf8 -u tools/x402_deploy.py` |
| LockRegistry (chain 97, M3) | `0xcF6fBF95fc04DEd8d670512CEc0723a2246Fbb0C` | [[02-Contracts/C6 - LockRegistry]] · ter-deploy 2 Okt 13:04Z |
| SignalAnchor (chain 97, M3) | `0x9B78200beFbbBe836585d31bd5b6dB32587064f3` | [[02-Contracts/C7 - SignalAnchor]] · maxLag 43200 s, revealWindow 604800 s |
| committer SignalAnchor (aktif) | `0xCA9c7322210E9a7F7d0953c862d4Ef60cC0D64A4` | `deployments/97.json` `m3.committer`; `0xE12e…812a` pensiun (F-D82) |
| kunci ambang peninjau v1 | sha `0xf145b70abd251b9fcf421bfb811bcf3788dade347c37b3bea331a09fedfe5f32`, anchoredAt 2026-10-02T08:17:48Z | `python -X utf8 tools/anchor_lock.py --verify` · F-D74 |
| kunci parameter F-D16 maju | sha `0x5a47cc4b87758730b0a1898f5a626029806b287abbb730292422fe5136797a45`, di-pin LockRegistry `lockedAt` 2026-10-02T17:10:57Z (tx `0x6bf7d51201b9…`) | `python -X utf8 tools/lock_spec.py --file engine/locks/fd16.lock.json --name FABIUS-FD16-MAJU-v1 --verify` · F-D84 |
| buku slot hidup epoch 690 | `book_sha 0xfe37d7595644fd7e23fc5cd2c9aa659db1b66e316069c7414dd478e231f6e05c`, di-pin `FABIUS-BUKU-E690` `lockedAt` 2026-10-02T17:26:09Z | `python -X utf8 tools/pin_book.py --verify` · F-D85 |
| anggaran gerbang A1/A2 (F-D88) | `engine/locks/anggaran.lock.json` sha `0x833f25987bae2dbddf7f2aaa94477744e1b8bb55284271e0815e75293cd5a94d`, di-pin `FABIUS-ANGGARAN-v1` `lockedAt` 2026-10-03T07:55:41Z | `python -X utf8 tools/lock_spec.py --file engine/locks/anggaran.lock.json --name FABIUS-ANGGARAN-v1 --verify` |
| pembunuh terstruktur B1/B3 (F-D87) | `engine/locks/pembunuh.lock.json` sha `0xa55b4782a6d5ec97a90df00634798a3887dc3300921a6ca3f21fb1e95a8607d4`, di-pin `FABIUS-PEMBUNUH-v1` `lockedAt` 2026-10-03T06:26:28Z | `python -X utf8 tools/lock_spec.py --file engine/locks/pembunuh.lock.json --name FABIUS-PEMBUNUH-v1 --verify` · `python -X utf8 -m engine.cli ledger pembunuh` |

## Perintah yang paling sering dipakai

```bash
forge test                                                     # 39 lulus (21 anchor + 18 eksekusi)
FOUNDRY_PROFILE=fork forge test --fork-url bscTestnet          # 63 lulus, termasuk 9 fork x402 (27 Sep)
FOUNDRY_PROFILE=fork forge test --match-contract ExecutionVaultTest   # 18 test jalur eksekusi
python -X utf8 tools/anchor.py --verify                        # baca ulang trail chain: tanpa kunci/gas
python -X utf8 tools/ledger.py                                 # nilai posisi jatuh tempo (atau: belum)
python -X utf8 tools/verify_vendor.py                          # vendor == manifest (nol jaringan)
python -X utf8 tools/direction.py --top 5 --emit               # siklus keputusan
python -X utf8 universe/write_universe_manifest.py             # integritas dataset (sha256 per baris)
python -X utf8 vault/scripts/prepush_check.py                  # WAJIB sebelum push: cek atribusi
python -X utf8 -m engine.cli ledger verify                     # ledger paper maju: hitung ulang dari ledger/bars (2 Okt)
python -X utf8 tools/verify_signals.py                          # komit sinyal di chain 97 vs ledger + bar, tanpa kunci (P106)
python -X utf8 -m engine.cli ledger fd16                         # gerbang F-D16 pada ledger maju (P88)
python -X utf8 -m engine.cli ledger skor                         # skor maju 90 hari + berpasangan (P85)
python -X utf8 -m engine.cli book verify                         # buku slot hidup (P87)
python -X utf8 tools/web_snapshot.py                             # data landing web (P113) -> web/public/data/snapshot.json
cd web && npm run build && npx next start -p 3006                # landing + server MCP /mcp (P114, 8 alat hanya baca)
python -X utf8 -m unittest discover -s engine/tests -t .        # 272 lulus (2 Okt malam)
```

Yang **tidak** masuk blok itu dengan sengaja: `panel_stats.py`, `check_garbled.py` — apa pun
di `_research/` root workspace. Itu alat di luar clone, jadi ia ditandai *(workspace)* di tiap
halaman yang mengutip angkanya dan tidak pernah dipakai sebagai bukti produk. `tools/verdict_counts.py` pindah ke dalam repo 27 Sep justru karena namanya sebelumnya
`_research/vault_verdict_counts.py`, dan `_research` punya dua arti di workspace ini.
dipakai untuk menghasilkan angka di bawah, dan ditandai begitu di tiap halaman yang mengutipnya
([[Conventions]] §Turunan). Angka yang hanya bisa dibangkitkan alat workspace tidak dipajang
sebagai klaim produk.

## Angka yang sedang berlaku (per 28 Sep 2026, semua terukur)

| fakta | angka | sumber |
|---|---|---|
| anchor di chain | **19** (Enter 4 / Abstain 15) | `anchorCount()` / `countByVerdict` via `python -X utf8 tools/verdict_counts.py` |
| verifikasi ulang trail | 13/13 cocok word-per-word, 0 BEDA | `anchor.py --verify` (28 Sep) |
| keputusan jatuh tempo (PAPER) | n=2: **+1,5** dan **−146,3 bps** net (rata-rata −72,4) | `ledger.py` + `python -X utf8 tools/winlog.py`, [[06-Results/07 - Matured Outcomes]] |
| biaya round-trip venue demo | **59 bps** — default SEMUA jalur uji sejak **P10 28 Sep** (`tools/costs.py`) | `forge test --match-test test_round_trip_...` |
| hasil uji aturan arah | rugi setelah ongkos **12/12**; dibalik tetap kalah. Hitung ulang 28 Sep (P10, 59 bps): tetap 12/12, kini −39,8…−66,9 bps | [[06-Results/04 - Negative Results]] §1/§5b |
| hasil uji smart money 4 j | **−10,4 bps** vs kerumunan, p=0,568 | [[06-Results/06 - Pre-registration Horizon]] |
| **posisi nyata dieksekusi di 97** | 3 round-trip, realized **−59 bps** per putaran (WR 0 %) | `decisions/execution-trail.jsonl` (angka dari event `Closed`) + `tools/winlog.py` |
| gas nyata eksekusi | open 258.008/295.443 · close 123.216/150.576 | `tools/execute_live.py` |
| jalur pemeriksaan hidup dari clone bersih | **4/4** pada HEAD `304fe4f` | [[07-Testing/T6 - Clean Clone Evidence]] |
| aliran wallet terekam | **21.907 transaksi / 452 maker / 1.590 token / rentang 34,33 jam** pada ekor `origin/master` (`94aead6`, 27 Sep 18:21Z) | `universe/wallet-flow-manifest.txt` — baca ulang: `git fetch` + `python -X utf8 tools/whale_report.py` |
| integritas dataset | **60 dari 62** snapshot lolos verifikasi sha256 | `write_universe_manifest.py` |
| kredit Dune terpakai hari ini | 1,259 (agregat 90 hari, ±11 s) | `execution_cost_credits` di API |

## Batas yang harus ikut disebut kapan pun angka di atas dikutip

- semua settlement & deploy di **BNB Chain testnet (97)**; tidak ada dana nyata
- token pembayaran adalah **koin demo milik kami sendiri**
- gateway x402 berjalan **di mesin kami** (belum di-host) — lihat [[05-Ecosystem/03 - Discovery Gap]]
- jalur eksekusi **sudah dipakai**: tiga round-trip nyata di 97, masing-masing rugi 59 bps —
  di **venue demo milik kami sendiri**, jadi angkanya adalah biaya, bukan hasil pasar
- `anchorCount()` di chain (**19**) lebih besar dari baris keputusan yang terpelacak di repo (**13**);
  `--verify` memperingatkan ini di keluarannya. Jangan kutip 19 sebagai jumlah keputusan kami
  (lihat [[08-Backlog/01 - Backlog]] P6b)
- lapisan pengetahuan trading tidak menghitung apa pun: angkanya lewat satu pintu,
  [[TradingKnowledge/Fakta Terukur]] — dan halaman itu sendiri cuma mencatat ulang apa yang tercetak di sini

Lihat juga: [[START-HERE]] · [[06-Results/01 - Claims and Limits]]
