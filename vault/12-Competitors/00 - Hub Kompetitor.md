---
tags: [kompetitor, hub]
---

# 12 - Competitors

**Sumber:** *(workspace)* `../Competitors/` (scrape halaman submission, repo, deck, video delapan proyek, 21–26 Okt 2026) · situs hackathon `indonesiaweb3hack.xyz` (26 Okt)

SWOT Fabius terhadap delapan kompetitor Indonesia Web3 Hackathon 2026, **satu kompetitor = satu catatan `KP#`**, ditulis berurutan dengan penggaris yang sama: lima kriteria juri panitia tanpa bobot (bobot tidak dipublikasikan) dan baseline Fabius di [[12-Competitors/KP0 - Baseline Fabius dan Konteks Penjurian]]. Ini **bukan** klaim produk: angka kompetitor bersumber dari luar repo (*workspace*) dan "unggul/kalah" adalah penilaian analis. Satu hal yang tidak boleh dilewatkan: per 26 Okt `/status` Fabius menyala `alarm` dan gate x402 HTTP 500, sementara tujuh dari delapan kompetitor hidup — setiap SWOT di sini memperhitungkan keadaan itu menjelang Demo Day 31 Okt.

## Bagian

- [[12-Competitors/KP0 - Baseline Fabius dan Konteks Penjurian]] — yang dilihat juri dari Fabius, kriteria/hadiah/timeline panitia, keadaan hidup 26 Okt, penggaris SWOT
- [[12-Competitors/KP1 - Matura]] — best-execution liquidity untuk pendapatan yang belum cair; rekayasa paling rapi; tidak di AI Agents
- [[12-Competitors/KP2 - Perago]] — mandat sekali pakai untuk agen yang memegang dompet; pesaing tesis paling langsung di AI Agents
- [[12-Competitors/KP3 - AgentEco]] — marketplace + escrow antar agen dengan SDK npm dan fee 2,5 % di kontrak; tumpang tindih tiga track
- [[12-Competitors/KP4 - BagiPanen]] — pembiayaan petani anti-ijon dengan dua kunci AI ERC-8004 + koperasi; terkuat di dampak
- [[12-Competitors/KP5 - SAMA]] — pencocokan rebalancing bStocks dompet-ke-dompet di mainnet; satu-satunya yang memindahkan aset bernilai
- [[12-Competitors/KP6 - Tagei]] — game trading 30 detik dengan settlement dari checkpoint oracle; app mati (402)
- [[12-Competitors/KP7 - Kawal]] — marketplace agen yang memprobe endpoint sebelum listing, mandat session key mainnet; kembaran filosofis Fabius
- [[12-Competitors/KP8 - Kulaya]] — kredit mikro warung, "AI proposes, contract decides" dengan red-team publik; kandidat kuat semua track
- [[12-Competitors/KP9 - Ranking dan Skenario Finalis]] — lima terkuat, posisi Fabius per skenario, kecocokan per track, distribusi 10 finalis (termasuk Lencana)
- [[12-Competitors/KP10 - Celah Analisis dan Solusi]] — tinjauan diri: 16 celah persiapan + solusi optimal, pemilik, prioritas; info bocoran top-15 (Fabius AI Agents, Lencana Consumer)

<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->
## Ringkasan posisi (penilaian, lihat tiap KP untuk alasannya)

| KP | Kompetitor | Irisan track dengan Fabius | Fabius unggul di | Kompetitor unggul di |
|---|---|---|---|---|
| KP1 | Matura | Consumer, Finance, Grand | inovasi, relevansi AI | eksekusi hari ini, bisnis, UX |
| KP2 | Perago | AI Agents, Consumer, Grand | platform terbuka, x402 hidup, multi-agen | eksekusi on-chain nyata, UX, demo |
| KP3 | AgentEco | semua | standar ekosistem (8004/x402/MCP), presentasi | transaksi antar agen hidup, fee di kontrak |
| KP4 | BagiPanen | semua | primitif bukti waktu, platform | dampak, UX, presentasi, pemakaian 8004 |
| KP5 | SAMA | semua | kedalaman AI, keterbukaan kode | mainnet, UX, nilai uang |
| KP6 | Tagei | Consumer, Finance, Grand | presentasi, demo bisa dibuka, AI | UX (di atas kertas), branding |
| KP7 | Kawal | AI Agents, Finance, Grand | AI dalam keputusan, x402, pitch | 8004 mainnet, mandat dieksekusi |
| KP8 | Kulaya | semua | bukti terhadap operator, disiplin n, platform | dampak, UX, presentasi, demo keamanan AI |

Pola lintas delapan catatan: Fabius konsisten unggul di **kedalaman primitif bukti dan keterbukaan platform**, dan konsisten kalah di **persona/dampak, keandalan hari ini, dan demo yang bisa dicoba juri**. Langkah yang muncul di hampir semua KP: pulihkan rantai (`/status` hijau), tabel "verify it yourself" tiga tx, konsol "coba patahkan" untuk revert kontrak, satu persona + satu angka, satu kalimat pembeda "bukti waktu keputusan".

```dataview
LIST FROM #kompetitor SORT file.name ASC
```

## Terkait

- [[Index]] · [[10-Submissions/00 - Hub Submissions]] · [[06-Results/03 - Not Yet Proven]] · [[08-Backlog/13 - Langkah Builder Tertunda]] · [[Conventions]]
