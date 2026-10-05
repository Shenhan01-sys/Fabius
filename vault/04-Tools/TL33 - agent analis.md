---
tags: [perkakas, "TL33", erc-8004, analis, llm]
---

# TL33 - agent analis (ERC-8004) dan SelectionAnchor

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** kontrak `contracts/SelectionAnchor.sol` (+ `test/SelectionAnchor.t.sol`, 6 tes) · deploy `tools/deploy_selection_anchor.py` · agent
`tools/analis.py` (`masukan`, `prompt`, `parse`, `call_model`, `run_round`, `records`) · thread + endpoint `/analis` + Telegram `/analysts` di
`tools/x402_sinyal.py` · kartu `docs/analis/<slug>.json` · arsip alasan `ledger/analis/<bar_close>.jsonl` + volume Railway `/data/analis` · tes
`engine/tests/test_analis.py` (6) · T8 SK-A1..SK-A3 · keputusan [[00-Overview/03 - Decisions]] F-D102 · backlog P141, P142

**SelectionAnchor** `0xc0c16337e6c286ec54902d8de7aadf232587f3b1` (chain 97, deploy 5 Okt tx `0x338bd913…` blok 134.940.475, deployer = committer):
`pick(agentId, barClose, botId, confidence, reasonHash)` - pengirim = dompet agen (`getAgentWallet`) atau pemilik identitas ERC-8004; SEBELUM
`barClose` (penutupan bar harian 00:00Z, maks 2 hari ke depan); satu per (agent, bar); bot + hash alasan bukan nol; keyakinan 0..100.

**Arti waktu:** pilihan untuk `barClose` = bot yang posisinya diikuti dari penutupan bar itu sampai penutupan berikutnya (tick bar itu). Pilihan
dikomit sebelum posisi itu terbentuk dan sebelum jendela hasilnya dimulai.

**Agent rumah (pendaftar pertama, 5 Okt):** GLM 5.3 (qwencloud, `reasoning_effort` low - "medium" ditolak HTTP 400 untuk GLM) = **agent 2558**
dompet `0x8e0E…a8A8` (tx daftar `0x559a39ff…`); Qwen 3.8 Flash (xhigh) = **agent 2559** dompet `0x8B16…9FA2` (tx `0x213b02d1…`); masing-masing diisi
0,01 tBNB dari committer. Claude Sonnet 5.5 disiapkan tetapi nonaktif (tanpa dana kredit API; jalur Anthropic belum pernah diuji).

**Masukan (deterministik, di-hash):** rezim pasar dari bar publik (BTC return 30/60 h, volatilitas 30 h, breadth di atas level 20/60 h, funding rata 7 h)
+ per bot: aturan, status, vonis gerbang v1, confidence maju, eksposur tick terakhir, perubahan. Alasan = JSON (model, effort, hash masukan/prompt/
jawaban mentah, pilihan); `reasonHash` on-chain = sha256 kanonisnya.

**Bukti 5 Okt:** pilihan on-chain pertama untuk penutupan 2026-10-06 00:00Z - GLM -> B1-TREND (62, tx `0xb118a186…`), Qwen -> B1-TREND (42, tx
`0x85adc927…`); dibaca ulang dari kontrak; sha256 alasan = `reasonHash` untuk keduanya. Otomasi: thread gerbang tiap 10 menit, 09-22 UTC.

**P143 (5 Okt):** aturan bot aktif TERKUNCI `engine/pemilih.py` (sha `0x48b4fa8b…`, dikunci sebelum satu pun pilihan terskor): tanpa pilihan ->
identitas; ada agent dengan >= 20 pilihan terskor -> pemimpin (jumlah selisih vs identitas atas 30 terakhir); selain itu suara terbanyak, seri ->
identitas. Skor = net paper bot pilihan pada bar yang dibuka di `bar_close` (settle FINAL ledger, atau PROVISIONAL: fungsi settle sama + funding
estimasi) dikurangi net identitas. Reputasi ERC-8004 dari gerbang (fasilitator `0x10c4…f1b1`; self-feedback ditolak kontrak, dicek eth_call):
value = selisih bps x100 (2 desimal), tag1 `fabius-pick-v1`, tag2 `provisional`/`final`. Arsip alasan ke repo hanya bila sha256 = reasonHash.

**Web (P145, F-D104):** `/analis` - slip pilihan bersegel + papan peringkat untuk semua; alasan lengkap untuk akun yang login + membeli sinyal dalam 7 hari (`GET /analis/lengkap`, token akses Privy); alasan bar terbuka disegel di `/analis` publik dan di `/analysts`.
**Yang belum:** pendaftaran agent LUAR lewat MCP/HTTP
(kontraknya sudah terbuka: agent ERC-8004 mana pun bisa memanggil `pick`, tetapi belum dinilai otomatis); alat data (P140).

**Terkait:** [[TL30 - validasi ERC-8004]] · [[TL32 - gerbang x402 per sinyal]] · [[05-Ecosystem/01 - ERC-8004 Identity]]
