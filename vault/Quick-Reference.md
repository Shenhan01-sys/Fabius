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
| **manifest alamat** | `deployments/97.json` (ter-track) | 8 alamat + cek bytecode dari chain — inilah yang membuat `--verify` jalan di clone |
| agen (penanda-tangan anchor) | `0x4bb30E3b3bc22082c1935fE3bE7c07448e69c862` | env → `deployments/97.json` → derivasi kunci; **dibantah ke kontrak** lewat `getAgent()`/`countByAgent()` = 17, aktif=True |
| ERC-8004 `IdentityRegistry` (chain 97) | `0x8004A818BFB912233c491871b3d84c89A494BD9e` | [[05-Ecosystem/01 - ERC-8004 Identity]] |
| tokenId agen | **2494** | `python -X utf8 -u tools/x8004_register.py --verify` |
| x402 proxy kanonis | `0x402085c248EeA27D92E8b30b2C58ed07f9E20001` (ada kode di 56 & 97) | [[05-Ecosystem/02 - x402 Payment]] |
| Permit2 | `0x000000000022D473030F116dDEE9F6B43aC78BA3` | sama |
| X402DemoToken (koin demo kami) | `0xB11D90214089684081F57A03d3300E20725297f8` | `python -X utf8 -u tools/x402_deploy.py` |

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
```

Yang **tidak** masuk blok itu dengan sengaja: `panel_stats.py`, `check_garbled.py` — apa pun
di `_research/` root workspace. Itu alat di luar clone, jadi ia ditandai *(workspace)* di tiap
halaman yang mengutip angkanya dan tidak pernah dipakai sebagai bukti produk. `tools/verdict_counts.py` pindah ke dalam repo 27 Sep justru karena namanya sebelumnya
`_research/vault_verdict_counts.py`, dan `_research` punya dua arti di workspace ini.
dipakai untuk menghasilkan angka di bawah, dan ditandai begitu di tiap halaman yang mengutipnya
([[Conventions]] §Turunan). Angka yang hanya bisa dibangkitkan alat workspace tidak dipajang
sebagai klaim produk.

## Angka yang sedang berlaku (per 27 Sep, semua terukur)

| fakta | angka | sumber |
|---|---|---|
| anchor di chain | **17** (Enter 3 / Abstain 14) | `anchorCount()` / `countByVerdict` |
| verifikasi ulang trail | 11/11 cocok 6 field, 0 BEDA | `anchor.py --verify` |
| posisi jatuh tempo | 2: **+1,5** dan **−146,3 bps** net | `ledger.py`, [[06-Results/07 - Matured Outcomes]] |
| biaya round-trip venue demo | **59 bps** | `forge test --match-test test_round_trip_...` |
| hasil uji aturan arah | rugi setelah ongkos **12/12**; dibalik tetap kalah | [[06-Results/04 - Negative Results]] |
| hasil uji smart money 4 j | **−10,4 bps** vs kerumunan, p=0,568 | [[06-Results/06 - Pre-registration Horizon]] |
| **posisi nyata dieksekusi di 97** | 2 round-trip, realized **−59 bps** per putaran | `decisions/execution-trail.jsonl` (angka dari event `Closed`) |
| gas nyata eksekusi | open 258.008/295.443 · close 123.216/150.576 | `tools/execute_live.py` |
| jalur pemeriksaan hidup dari clone bersih | **4/4** pada HEAD `304fe4f` | [[07-Testing/T6 - Clean Clone Evidence]] |
| aliran wallet terekam | 8.053 transaksi / 348 maker / 643 token / 11,82 jam | `_research/panel_stats.py` *(workspace)* |
| integritas dataset | **60 dari 62** snapshot lolos verifikasi sha256 | `write_universe_manifest.py` |
| kredit Dune terpakai hari ini | 1,259 (agregat 90 hari, ±11 s) | `execution_cost_credits` di API |

## Batas yang harus ikut disebut kapan pun angka di atas dikutip

- semua settlement & deploy di **BNB Chain testnet (97)**; tidak ada dana nyata
- token pembayaran adalah **koin demo milik kami sendiri**
- gateway x402 berjalan **di mesin kami** (belum di-host) — lihat [[05-Ecosystem/03 - Discovery Gap]]
- jalur eksekusi **sudah dipakai**: dua round-trip nyata di 97, masing-masing rugi 59 bps —
  di **venue demo milik kami sendiri**, jadi angkanya adalah biaya, bukan hasil pasar
- `anchorCount()` di chain (17) lebih besar dari baris keputusan yang terpelacak di repo (11);
  `--verify` memperingatkan ini di keluarannya. Jangan kutip 17 sebagai jumlah keputusan kami
  (lihat [[08-Backlog/01 - Backlog]] P6b)

Lihat juga: [[START-HERE]] · [[06-Results/01 - Claims and Limits]]
