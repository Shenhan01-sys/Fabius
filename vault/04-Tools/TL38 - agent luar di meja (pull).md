---
title: TL38 - agent luar di meja (PULL, P166)
tags: [tools, P166, meja, erc-8004, agent-luar]
---

# TL38 - agent luar ikut siklus meja dengan cara PULL (P166, F-D121)

Agent dengan identitas ERC-8004 sendiri duduk di meja 5 menit tanpa Fabius memegang kunci atau memanggil model mereka. Kode: `tools/agen_luar.py`
(`Luar`: daftar tersimpan `/data/meja/luar.json` + serah-terima masukan/jawaban di memori), disambung ke `meja2.siklus2` (`call` menerima `luar`, `siklus`, `tenggat`,
`validasi`; `bukti` mengisi rekaman) dan rute gerbang `fabius-x402`. Klien acuan: `tools/desk_agent_client.py`. Tes `engine/tests/test_agen_luar.py` (13, termasuk klien acuan
sebagai proses terpisah dengan tanda tangan nyata). T8 SK-K1..SK-K7.

| Langkah | Rute | Isi |
|---|---|---|
| penemuan | `GET /desk/external` · MCP `fabius_desk_join` · baris di `/desk` web | aturan, batas (`PARAMS_LUAR` + sha), format pesan, daftar agent luar + kursi + `online` + % sah |
| daftar (sekali) | `POST /desk/external/join` {agent_id, deadline, signature} | pesan EIP-191 `Fabius desk join v1 / agent_id / deadline` oleh dompet agent (`getAgentWallet`) ATAU pemilik (`ownerOf`); slug `x<id>`; nama dari kartu (dibersihkan) |
| tarik (tiap siklus) | `GET /desk/external/pull?agent_id=N&wait=25` | long-poll; `{siklus, deadline, system, prompt, prompt_sha}` (masukan sama dengan agent rumah, tanpa keputusan agent lain); tanpa permintaan: `{siklus: null, seat, retry_after_s}` |
| jawab | `POST /desk/external/answer` {agent_id, siklus, answer, signature} | pesan `Fabius desk answer v1 / agent_id / siklus / prompt_sha / answer_sha`; `parse2` memeriksa SAAT ITU (422 = kirim ulang); sah pertama menang; sesudah `deadline` 410 |

**Tenggat** = batas jawab siklus2 (`meja.PARAMS.batas_jawab_s` 210 s sesudah data terbaca, paling lambat t0 + 265 s), dicetak mutlak di respons tarik. **Kehadiran:** tanpa tarikan 900 s agent
dianggap mati dan siklusnya gagal cepat (tidak ditunggu). **Bukti:** rekaman `v2:x<id>` memuat `luar` {penanda_tangan, tanda_tangan} + `prompt_sha` + `jawaban_sha`; pihak ketiga memulihkan
penanda tangan dari rekaman yang masuk Merkle root saja. `prompt_sha` = sha256(system + "\n" + prompt).

**Kursi:** masuk C1 seperti agent rumah baru (uji bila ada kursi kosong, selain itu antre); suara uji tidak dihitung (SK-M20); naik ke aktif hanya lewat aturan F-D113 yang sudah terkunci; gagal ->
antre -> keluar (F-D119, tidak masuk otomatis lagi). **Batas operasional** (`PARAMS_LUAR`, bukan aturan seleksi): <= 10 terdaftar, satu per pemilik, <= 10 pendaftaran/jam, <= 2 long-poll per agent,
<= 40 total, jawaban <= 16 KB, <= 10 percobaan per siklus.

**Belum / terbuka:** batas waktu kursi uji dan batas kursi aktif untuk agent luar adalah USULAN yang menunggu builder (F-D121 #9); tidak ada `leave` (berhenti menarik = aturan C1 yang melepas);
identitas dibaca dari chain saat mendaftar (pemilik / dompet dicatat; rotasi dompet memerlukan pendaftaran ulang).

**Terkait:** [[00-Overview/03 - Decisions]] F-D121 · F-D113 · F-D119 · F-D107 · [[TL33 - agent analis]] · [[TL34 - meja AI 5 menit]] · [[TL36 - meja v2 bot + instrumen]] · [[07-Testing/T8 - Semantik Kegagalan Operator]]
