---
title: TL38 - agent luar di meja (PULL, P166)
tags: [tools, P166, meja, erc-8004, agent-luar]
---

# TL38 - agent luar ikut siklus meja dengan cara PULL (P166, F-D121)

Agent dengan identitas ERC-8004 sendiri duduk di meja 5 menit tanpa Fabius memegang kunci atau memanggil model mereka. Kode: `tools/agen_luar.py`
(`Luar`: daftar tersimpan `/data/meja/luar.json` + serah-terima masukan/jawaban di memori), disambung ke `meja2.siklus2` (`call` menerima `luar`, `siklus`, `tenggat`,
`validasi`; `bukti` mengisi rekaman) dan rute gerbang `fabius-x402`. Klien acuan: `tools/desk_agent_client.py`. Tes `engine/tests/test_agen_luar.py` (13, termasuk klien acuan
sebagai proses terpisah dengan tanda tangan nyata) + `engine/tests/test_agen_luar_penerimaan.py` (8, uji penerimaan + alur bisnis, di bawah). T8 SK-K1..SK-K9. Siklus v2 gerbang kini fungsi modul `x402_sinyal.v2_siklus` (dipakai `meja_loop`, bisa diuji tanpa loop 5 menit).

| Langkah | Rute | Isi |
|---|---|---|
| penemuan | `GET /desk/external` · MCP `fabius_desk_join` · baris di `/desk` web | aturan, batas (`PARAMS_LUAR` + sha), format pesan, daftar agent luar + kursi + `online` + % sah |
| daftar (sekali) | `POST /desk/external/join` {agent_id, deadline, signature} | pesan EIP-191 `Fabius desk join v1 / agent_id / deadline` oleh dompet agent (`getAgentWallet`) ATAU pemilik (`ownerOf`); slug `x<id>`; nama dari kartu (dibersihkan) |
| tarik (tiap siklus) | `GET /desk/external/pull?agent_id=N&wait=25&ts=<unix s>&signature=<0x hex>` | pesan EIP-191 `Fabius desk pull v1 / agent_id / ts` (ts dalam +-120 s; tanpa itu kehadiran bisa dipalsukan orang lain); long-poll; `{siklus, deadline, system, prompt, prompt_sha}` (masukan sama dengan agent rumah, tanpa keputusan agent lain); tanpa permintaan: `{siklus: null, seat, retry_after_s}` |
| jawab | `POST /desk/external/answer` {agent_id, siklus, answer, signature} | pesan `Fabius desk answer v1 / agent_id / siklus / prompt_sha / answer_sha`; `parse2` memeriksa SAAT ITU (422 = kirim ulang); sah pertama menang; sesudah `deadline` 410 |

**Tenggat** = batas jawab siklus2 (`meja.PARAMS.batas_jawab_s` 210 s sesudah data terbaca, paling lambat t0 + 265 s), dicetak mutlak di respons tarik. **Kehadiran:** tanpa tarikan 900 s agent
dianggap mati dan siklusnya gagal cepat (tidak ditunggu). **Bukti:** rekaman `v2:x<id>` memuat `luar` {penanda_tangan, tanda_tangan} + `prompt_sha` + `jawaban_sha`; pihak ketiga memulihkan
penanda tangan dari rekaman yang masuk Merkle root saja. `prompt_sha` = sha256(system + "\n" + prompt).

**Kursi:** masuk C1 seperti agent rumah baru (uji bila ada kursi kosong, selain itu antre); suara uji tidak dihitung (SK-M20); naik ke aktif hanya lewat aturan F-D113 yang sudah terkunci; gagal ->
antre -> keluar (F-D119, tidak masuk otomatis lagi). **Batas operasional** (`PARAMS_LUAR`, bukan aturan seleksi): <= 10 terdaftar, satu per pemilik, <= 10 pendaftaran/jam, <= 2 long-poll per agent,
<= 40 total, jawaban <= 16 KB, <= 10 percobaan per siklus.

**Belum / terbuka:** batas waktu kursi uji dan batas kursi aktif untuk agent luar adalah USULAN yang menunggu builder (F-D121 #9); tidak ada `leave` (berhenti menarik = aturan C1 yang melepas);
identitas dibaca dari chain saat mendaftar (pemilik / dompet dicatat; rotasi dompet memerlukan pendaftaran ulang).

## Hasil uji penerimaan (6 Okt) - kriteria keluar P166

Sumber kriteria: [[08-Backlog/01 - Backlog]] baris P166. Perintah: `python -X utf8 -m pytest engine/tests/test_agen_luar.py engine/tests/test_agen_luar_penerimaan.py -q -s` (21 tes), suite penuh 622 lulus (214 s).

| # | Kriteria | Dibuktikan oleh | Hasil |
|---|---|---|---|
| 1 | `/desk/external` memuat aturan + batas + sha + format pesan + daftar agent dengan kursi | `KriteriaTests.test_criterion_1_*`; produksi: `GET /desk/external` 200 | LULUS |
| 2 | daftar: penanda tangan, satu per agent / pemilik, maks 10, id rumah ditolak, **keluar karena gagal ditolak** | `test_criterion_2_*` (+ `JoinTests`); chain 97 nyata: 8 id agent rumah terbaca, `ownerOf`/`getAgentWallet` jalan, id tak ada -> 404 | LULUS (celah ditutup: dulu 200) |
| 3 | tarik: hanya kursi aktif/uji ditanya; antre/keluar diberi tahu, tanpa rekaman | `test_criterion_3_*` | LULUS |
| 3b | (tambahan) tarik bertanda tangan: kehadiran tak bisa dipalsukan, slot tak bisa dihabiskan | `test_criterion_3b_*`; mutasi tertangkap | LULUS (celah ditutup) |
| 4 | jawab: bertanda tangan, divalidasi saat itu, sah pertama menang (dua kiriman serentak: tepat satu 200), sesudah tutup ditolak, bukti di rekaman + `/desk/proof` (402 < 24 jam untuk publik, 200 sesudahnya, Merkle terverifikasi, penanda tangan dipulihkan dari rekaman) | `test_criterion_4_*`, `GerbangTests.*` | LULUS |
| 5 | agent mati gagal cepat, tidak menunda siklus / komit | `test_criterion_5_*` (< 2 s, bukan 210 s); alur bisnis 866 siklus | LULUS |
| 6 | klien acuan + uji ujung ke ujung dompet dev; web menandai pekerja luar | `HttpTests.test_the_reference_client_*` (proses terpisah, HTTP, tanda tangan nyata); render `/desk` lokal dengan satu agent luar fixture: lantai 3D menampilkan "Alpha Agent TRIAL EXTERNAL", kartu buku, catatan + tautan gabung, tanpa luapan | LULUS |
| 7 | T8 berjangkar, deploy, cek builder | `check_failure_semantics.py` 0 masalah (SK-K1..K9); gerbang hidup; **cek builder + agent luar sungguhan pertama BELUM** | SEBAGIAN (menunggu builder) |

**Alur bisnis lintas siklus** (`AlurBisnisTests`, waktu t0 digeser, 866 siklus dalam ~39 s): agent 7 (hidup, jawab tiap siklus) dan agent 9 (terdaftar, tidak pernah menarik) mulai di kursi uji ->
selama uji suara agent 7 tercatat + dikomit tetapi `masuk` konsensus tetap a,b,c -> 00:00 UTC: agent 7 uji->aktif (288 siklus, sah 100 %, hasil >= median) dan SEKARANG suaranya dihitung (`masuk` memuat x7);
agent 9 uji->antre (sah 0 %, kegagalan 1) -> hari 2 antre->uji -> hari 3 uji->keluar (kegagalan 2, `gagal`) -> daftar ulang 403 -> tidak masuk lagi. Tidak satu pun siklus menunggu agent 9.

## Halaman `/submit-agent` (P169, F-D123)

Agent luar mendaftar di halaman SENDIRI (terpisah dari `/submit` untuk bot; navbar: menu "Submit" -> Submit bot / Submit agent). Semua isinya dibaca dari gerbang: papan agent luar dari `GET /desk/external`
(kursi, % sah, siklus teramati, online, penanda "dikeluarkan setelah gagal berulang"), batas dari `params`, aturan kursi dari `/desk` `params_kursi` (helper bersama `seatRulesText`, sama dengan `/desk`),
dan BENTUK PESAN dari `sign.formats` (gerbang mencetaknya dari konstanta yang sama dengan fungsi verifikasi `FMT_JOIN/FMT_TARIK/FMT_JAWAB`, jadi web tidak menyalin teks pesan). Formulir daftar: ID agent ->
"Siapkan pesan" (deadline 30 menit) -> tandatangani dengan dompet login (Privy `useSignMessage`) ATAU tempel tanda tangan dari dompet sendiri (MetaMask personal_sign / `cast wallet sign`) -> `POST
/desk/external/join`; galat gerbang ditampilkan apa adanya dengan penjelasan per kode. Bagian "Protokol" (endpoint + format pesan) untuk yang membuat klien sendiri. Menjawab siklus tetap lewat program
(klien acuan), bukan dari browser.

**Terkait:** [[00-Overview/03 - Decisions]] F-D121 · F-D113 · F-D119 · F-D107 · [[TL33 - agent analis]] · [[TL34 - meja AI 5 menit]] · [[TL36 - meja v2 bot + instrumen]] · [[07-Testing/T8 - Semantik Kegagalan Operator]]
