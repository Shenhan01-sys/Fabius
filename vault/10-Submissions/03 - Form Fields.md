---
tags: [submission, "P-FORM"]
---

# Form Fields — nilai yang diisi ke portal

**Bagian dari:** [[10-Submissions/00 - Hub Submissions]]
**Sumber:** `02-Contracts/02 - Deployed on 97.md`, `05-Ecosystem/01 - ERC-8004 Identity.md`

Dibaca ulang dari repo pada 27 Sep. **Jangan menyalin dari chat** — satu karakter salah di kolom
kontrak artinya alamat milik orang lain.

| field | isi | verifikasi |
|---|---|---|
| GitHub repo | `https://github.com/Shenhan01-sys/Fabius` (publik) | `gh repo view` |
| Smart contract (1 kolom) | `0xdd162afb5f5f92d5092f845a93660e3b38259330` — `DecisionAnchor` | `python -X utf8 -u tools/anchor.py --verify` |
| Network | **BSC Testnet (97)** | `eth_chainId` = 97 |
| Demo | folder `00-Overview/04 - Run It.md` = skrip video 5 menit | — |

Kontrak lain yang **tidak muat** di form dan harus disebut di README/deskripsi:
`ExecutionVault` & `DemoPair` (setelah P1 selesai), `X402DemoToken` `0xB11D9021…`, identitas
ERC-8004 tokenId `2494` di `0x8004A818BFB912233c491871b3d84c89A494BD9e` (registry pihak ketiga —
sebut sebagai milik mereka, bukan milik kami).

Syarat yang harus dicek ulang sebelum submit: tim terdaftar di Luma; kontrak resolve di BscScan;
repo publik; riwayat commit berada dalam periode hackathon.
