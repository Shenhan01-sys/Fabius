---
tags: [overview, "O7"]
---

# 07 - Ecosystem Positioning

> **BN-PIVOT - 2 Okt 2026.** Arah proyek bergeser: Fabius menjadi **operator pemilih bot** yang kelak menjual **sinyal
> berbukti** dan membuka slot bot untuk penerbit luar ([[00-Overview/03 - Decisions]] F-D70 dan F-D71). Halaman ini
> menggambarkan keadaan **sebelum** pivot dan tetap benar untuk apa yang **sudah dibangun**; arah baru masih **usulan dan kode
> awal** ([[08-Backlog/05 - Epik Enam Bot]], [[08-Backlog/06 - Epik Gerbang Sinyal]], [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]]).
> Jangan memakai halaman ini untuk menyangkal arah baru, dan jangan menyebut arah baru sebagai fitur yang sudah ada.

**Bagian dari:** [[00-Overview/00 - Hub Overview]]
**Sumber:** audit 26 Sep atas pertanyaan builder: *"apa jangan-jangan ini malah hanya project
trading doang dan gaada essential kesana?"* — dijalankan read-only, tanpa mengubah apa pun,
sebelum repo dibuka ke publik.

**Ringkas:** pertanyaan itu benar, dan jawabannya tidak sepenuhnya nyaman. Fabius **bukan** cuma
project trading, tapi sebagian dari klaim "BNB ecosystem agentic AI" waktu itu masih berupa
**niat**, bukan artefak. Yang diubah setelah audit inilah yang membuatnya bisa ditunjuk jari.

## Yang sudah BNB-native dan bisa diperiksa orang lain (terukur)

| lapisan | artefak nyata | cara memeriksa tanpa kami |
|---|---|---|
| identitas agen | `IdentityRegistry` chain 97 `0x8004A818…`, agen = **tokenId 2494**, `getAgentWallet(2494)` menunjuk alamat agen kami | baca registry di explorer/BscScan, atau `python -X utf8 tools/x8004_register.py --verify` |
| kartu agen | `docs/agent-card.json` di raw.githubusercontent repo publik; endpoint, harga, network, dan berkas keputusan yang ia tunjuk **benar-benar ditulis alatnya** | `curl` kartu itu, lalu cocokkan field-nya dengan repo |
| pembayaran antar-agen | proxy kanonis x402 `0x402085c2…` + Permit2; satu settlement nyata di 97 (tx `0xb6093e59…`, token bergerak 1.000 atomic = tagihan) | `eth_getTransactionReceipt` + `balanceOf`, atau `forge test` profil fork (9 test) |
| jejak keputusan | `DecisionAnchor` di 97: `anchorCount()` = 17 (3 Enter / 14 Abstain); `id = keccak(agent, decisionHash, snapshotHash, chainid)` | `python -X utf8 tools/anchor.py --verify` — nol kunci, nol gas |
| data BSC-native | aliran smart money **BSC** dari GMGN; deret harga **perp BNB-native** (Aster) 9.599 bar ≈ 400 hari; `dex.trades` Dune `blockchain='bnb'` 5,27 juta swap/jam | [[03-Data/D2 - Wallet Flow]], [[03-Data/D3 - Price Depth]], [[03-Data/D4 - Dune]] |
| gerbang keamanan token | honeypot/`can_not_sell` diukur dari GMGN **dan** GoPlus untuk kontrak BSC | [[04-Tools/TL3 - security_gate]] |

## Kelemahan yang ketahuan oleh audit itu, dan apa yang kami lakukan

1. **"Agentic" waktu itu berarti "script yang jalan sendiri".** Tidak ada identitas di registry,
   tidak ada cara bagi agen lain memanggil kami, repo privat. Tiga-tiganya sekarang ada
   (baris 1–3 tabel di atas) — dan urutan kerjanya memang dimulai dari sini, bukan dari fitur.
2. **Aturan keputusannya tidak BNB-spesifik.** Ini yang jujur: SMA24/ret24/acf yang dipakai
   `direction.py` akan bekerja sama di chain mana pun. Yang membuat jalur ini milik BNB adalah
   **datanya** (universe BSC, aliran GMGN, perp Aster, keamanan kontrak BSC) dan **cara bukti
   dibuang** (anchor + x402 + registry di 97), bukan alphanya — dan alphanya, sejauh yang kami
   ukur, **negatif setelah ongkos** ([[06-Results/04 - Negative Results]]).
3. **Maka jualannya bukan "trading yang menang".** Jualannya: keputusan yang tercatat sebelum
   hasilnya ada dan tidak bisa disunting sesudahnya, dijual ke agen lain lewat relasi pembayaran
   resmi chain, dengan angka yang bisa dihitung ulang dari clone. Itu kalimat yang tidak bisa
   diklaim peserta lain tanpa membangun mekanisme yang sama.
4. **Yang masih setengah:** penemuan oleh agen **asing** belum terbukti — pembelinya sampai sekarang
   program kami sendiri, dan endpoint-nya masih `127.0.0.1`. Dinyatakan apa adanya di
   [[05-Ecosystem/03 - Discovery Gap]], tidak dibungkus.

## Yang dilarang untuk diri sendiri waktu framing

- Menulis "first BNB-native agentic vault" atau klaim urutan apa pun — kita tidak mengukur peserta lain.
- Meminjam konteks: jalur kredensial/1EdTech adalah **proyek lain kami** (Lencana) dan tidak
  dipakai untuk membuat Fabius tampak ekosistemik.
- Menyebut "AI trading bot yang profitable". Angka kami bilang sebaliknya.
- Menjual "terhubung ke ekosistem BNB" sebagai fitur kalau yang terhubung cuma README-nya.

**Detail:** audit ini dijalankan sebelum repo dijadikan publik; builder kemudian mengubah
visibilitas repo ke publik (26 Sep) — itu yang membuat "verifiable tanpa kami" berubah dari niat
menjadi property yang bisa diperiksa juri. Lihat F-D19/F-D20 di [[00-Overview/03 - Decisions]].

**Terkait:** [[00-Overview/01 - Briefing]] · [[00-Overview/02 - Business Process]] ·
[[05-Ecosystem/00 - Hub BNB Ecosystem]] · [[10-Submissions/01 - Claims Cheat Sheet]]
