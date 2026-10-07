---
title: TL48 - agent luar uji di Railway (P151 P166)
tags: [tools, "TL48", P151, P166, agent-luar, analis, meja, railway]
---

# TL48 - agent luar uji 2573 di Railway: meja PULL 24/7 + pilihan analis harian + alasan publik (P151 + P166)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/agen_luar_layanan.py` (`keputusan`, `segar`, `Arsip`, `Rantai`, `langkah_analis`, `loop_meja`, `buat_server`, `rahasia_lain`, `main`) ·
kartu `tools/agen_luar_uji.py kartu --domain` (`reasons_url`) · image `railway/agen-luar-uji/Dockerfile` · arsip deploy `tools/railway_up.py::PATHS_LAYANAN` ·
`tools/evm.py::keccak` (cadangan Keccak tanpa `engine/`) · tes `engine/tests/test_agen_luar_layanan.py` (12) · T8 SK-AL1..SK-AL9 · jalur gerbang yang
dipakai apa adanya: `tools/analis.py` (`temukan_agent`, `kartu_luar`, `alasan_luar`, F-D107) + meja PULL `tools/x402_sinyal.py` (F-D121) · agent luar
uji P166: `tools/agen_luar_uji.py`, `tools/agen_luar_uji_jawab.py` · rencana [[09-Inbox/Session-2026-10-02]] §159 butir 3

**Status (7 Okt 2026):** DIBANGUN + diuji lokal di cabang `kerja-p151`; BELUM di-push, layanan Railway BELUM ada, kartu BELUM memuat
`fabius.reasons`, belum ada satu pun pick dari layanan ini. Semua langkah yang mengubah sesuatu di luar repo = langkah builder (di bawah).

## Apa

Builder (7 Okt): *"P151 dijalanin di railway aja kah biar bisa ditinggal?"*. Agent luar uji 2573 (milik builder, label jujur "builder-operated test
agent" di kartu) sampai hari ini menjawab meja dari laptop builder (`tools/agen_luar_uji.py jalan`) dan belum pernah memilih di jalur analis luar. Layanan
Railway SENDIRI `agen-luar-uji` menjalankan satu proses dengan tiga tugas:

1. **Meja (P166):** join bertanda tangan EIP-191 lalu loop PULL `tools/desk_agent_client.py`; jawaban dari penjawab aturan
   `tools/agen_luar_uji_jawab.py` (tanpa model bahasa, sama dengan versi laptop). Pull 404 (gerbang deploy ulang) = join ulang. Tanpa tx.
2. **Analis harian (P151):** tiap `ANALIS_TIAP_S` (300 s) baca `GET /analysts/input`; sekali per penutupan bar harian, SEBELUM 00:00 UTC, buat JSON alasan
   per skema luar (`analis.SKEMA_ALASAN`) dengan aturan di bawah, simpan, lalu `SelectionAnchor.pick(2573, bar_close, bot, keyakinan, reasonHash)` dari
   dompet agent; reasonHash = sha256 JSON kanonis (rumus `analis.sha`: `sort_keys`, pemisah `,` `:`, `ensure_ascii=False`).
3. **Alasan publik:** `GET /reasons/<bar_close>.json` = byte PERSIS yang di-hash, HANYA sesudah bar tutup (sebelumnya 404, pilihan tidak bocor);
   `GET /health` = status meja + analis. Template ini yang ditulis ke kartu sebagai `fabius.reasons`.

Gerbang tidak berubah: ia menemukan agent dari event `Picked`, membaca kartu lewat `tokenURI` (cache 6 jam), dan sesudah bar tutup mengambil alasan dari
template kartu, mencocokkan hash + `agent_id` + `bar_close` + `pilihan.bot`, mencoba lagi tiap jam bila gagal (tanpa batas menyerah). Kartu yang
terlambat diperbarui tetap terverifikasi paling lambat ±6 jam sesudah push kartu.

## Aturan pilihan harian (USULAN - belum diputus builder)

Agent ini membuktikan JALUR, tidak mengklaim keunggulan. Masukan = `masukan.rezim_pasar` dari `/analysts/input`:

| urutan | syarat | bot | kekuatan (0-1) |
|---|---|---|---|
| 1 | `breadth_di_atas_60h >= 0,6` dan `btc_ret_60h > 0` | B1-TREND | breadth 60 hari |
| 2 | `funding_rata_7h_tahunan >= 0,10` | B3-CARRY | min(1, funding / 0,3) |
| 3 | `btc_ret_30h <= -0,10` | B6-BOUNCE | min(1, -ret 30 hari / 0,3) |
| 4 | selain itu | B5-CORE-RWA | 0,2 |

Keyakinan = bulat(30 + 40 x kekuatan), dijepit 30-70. Bot aturan yang tidak ditawarkan di `masukan.bot` -> bot pertama yang ditawarkan (dicatat di alasan).
Alasan memuat `aturan`, `masukan_sha256`, `nama`, `model` ("rules ..., no language model"), `pilihan.risiko` (label uji) - TANPA jam, jadi deterministik.

**Waktu (USULAN):** data dianggap segar bila `rezim_pasar.bar_terakhir` = tanggal (bar_close - 2 hari), yaitu tick ledger bar harian terakhir sudah masuk;
belum segar -> tunggu (SK-AL1); mulai 2 jam sebelum penutupan (22:00Z) memilih dengan data yang ada (`CADANGAN_S`). Gerbang membaca rezim dari
`ledger/bars` (`analis.regime`), yang ikut rantai ledger harian; commit `ledger paper` 5-7 Okt masuk 11:05Z, 08:42Z, 10:02Z
(`git log -- ledger/paper/B3-CARRY.jsonl`), jadi pick normal diharapkan siang UTC, jauh sebelum 00:00 UTC (belum teramati di produksi).

**Sekali per bar:** `getPick` dibaca dulu (sudah ada = tidak dikirim, SK-AL2); alasan yang sudah ditulis dipakai ulang walau masukan berubah (hash tetap,
SK-AL3); tx yang SUDAH masuk mempool lalu gagal (revert tertambang / receipt tidak datang) dihitung, berhenti di 3 per bar (`MAKS_TERKIRIM`, USULAN,
SK-AL4); revert saat `estimateGas` = nol gas, tidak dihitung.

## Penyimpanan

`ALASAN_DIR` (bawaan `/data/alasan`, volume Railway di `/data` - USULAN): per bar `<close>.json` (byte alasan), `<close>.masukan.json` (salinan masukan),
`<close>.pick.json` (hasil kirim + hitungan `terkirim`). Tulis = berkas sementara lalu `os.replace`. Berkas alasan hilang tetapi salinan masukan ada ->
dibangun ulang PERSIS (SK-AL6). Volume hilang seluruhnya -> alasan bar yang sudah dikomit tidak bisa disajikan lagi; gerbang yang sudah memverifikasinya
tetap menyimpan salinannya sendiri, yang belum = tidak akan pernah terverifikasi (dicetak PERINGATAN di log).

## Rahasia dan image

- Satu-satunya rahasia = `AGEN_LUAR_UJI_KEY` (kunci dompet agent 2573, isinya dari `.agen_luar_uji.env` di laptop builder). Variabel lain yang namanya
  mengandung KEY / SECRET / TOKEN / PASSW / MNEMONIC / PRIVATE_K -> **MENOLAK MULAI** (exit 3, nama dicetak, nilai tidak; SK-AL7). Tanpa kunci = exit 2.
  `ALASAN_DIR` tidak bisa ditulis = exit 4 dengan petunjuk.
- Meja hanya tanda tangan pesan (tanpa tx), jadi tidak ada tabrakan nonce dengan pick harian dari dompet yang sama.
- Image `python:3.12-slim` + `eth-account==0.13.7` + `eth-abi==5.2.0` (pin sama dengan `railway/requirements.txt`), user non-root `agen` (uid 10001),
  HANYA empat berkas: `agen_luar_layanan.py`, `desk_agent_client.py`, `agen_luar_uji_jawab.py`, `evm.py` - tanpa `engine/`, tanpa alat worker / gerbang.
  `tools/railway_up.py --service agen-luar-uji` mengarsip hanya `PATHS_LAYANAN` (bukan arsip worker).
- `tools/evm.py::keccak` dulu SELALU mengimpor `engine.chain`: di image ini pick pertama akan mati `ModuleNotFoundError`. Kini jatuh ke Keccak-256
  eth-account (`eth_utils.keccak`) bila `engine` tidak ada; tes menjalankan berkas image di folder kosong tanpa `engine/` dan membandingkan calldata
  `pick` / `getPick` byte demi byte (SK-AL9). Pemanggil lain (worker, gerbang) tetap memakai `engine.chain` seperti sebelumnya.

## Biaya gas (dibaca 7 Okt 2026 14:07Z, baca-saja, tanpa tx)

`estimateGas` `pick(2573, 1791417600, B1-TREND, 60, ...)` DARI dompet `0xcFbB50cA211d70A7F7Ac036B80f408832caF5BB0` = **172 548** (lolos: dompet ini
memang `getAgentWallet` / pemilik 2573 dan bar sah; `getPick` bar itu 0). Gas terkirim = x1,25 + 10 000 = 225 685; harga gas = lantai
`evm.MIN_GAS_PRICE` 1,0 gwei -> **maks 0,000226 tBNB per pick**, ±0,0068 tBNB per 30 hari. Saldo dompet saat itu **0,00979912 tBNB** = ±43 pick.
Usulan isi: **0,05 tBNB** (±220 hari pada biaya maks; USULAN). Batas terburuk per bar = 1 pick sukses + 3 tx gagal.

## Yang BELUM / tidak dibuktikan

- Layanan belum pernah berjalan di Railway; image belum pernah dibangun (tes bentuk-image memakai Python lokal di folder berisi empat berkas yang sama,
  bukan `python:3.12-slim`). Izin tulis volume Railway (dipasang milik root) untuk user uid 10001 belum dicoba - lihat runbook.
- `Rantai.kirim` belum pernah mengirim tx sungguhan; yang terbukti di chain hanya `estimateGas` + `getPick` (baca-saja, di atas). Tx sungguhan pertama =
  pick pertama layanan.
- Uji ujung-ke-ujung memakai gerbang LOKAL: `x402_sinyal.Gate` sungguhan di server HTTP lokal + `meja2.siklus2` (rekaman `v2:x2573` status ok, kursi uji)
  dan pemeriksa alasan gerbang sungguhan `analis.alasan_luar` + `analis.kartu_luar` (alasan diambil dari server layanan lokal; URL https kartu ditulis
  ulang ke http lokal). TLS / tepi Railway / raw GitHub tidak diuji. Rantai di tes = SelectionAnchor palsu (`getPick` / `pick`), bukan anvil.
- Aturan pilihan tidak dievaluasi dan tidak mengklaim edge; ia hanya membuat jalur analis luar punya pengguna nyata.
- Dua penjawab meja untuk agent yang sama (laptop + Railway) tidak diuji: matikan `jalan` di laptop sebelum layanan dinyalakan.
- Jam = jam container. Hanya satu replika yang benar (dua replika = dua pick bersaing; yang kedua revert saat estimasi, nol gas, tetapi meja dijawab dua kali).

## Cara memakai (langkah builder, berurutan)

Variabel di bawah = NAMA saja; nilai kunci tidak pernah diketik di chat / argumen perintah.

```
# 0. kode masuk master (cabang kerja-p151) + push atas kata builder
# 1. hentikan penjawab laptop (tools/agen_luar_uji.py jalan) bila masih jalan
# 2. buat service KOSONG "agen-luar-uji" di project Railway Fabius (dasbor: New -> Empty Service; atau `railway add --service agen-luar-uji`, belum dicoba)
railway variable set RAILWAY_DOCKERFILE_PATH=railway/agen-luar-uji/Dockerfile --service agen-luar-uji --skip-deploys
#    AGEN_LUAR_UJI_KEY = isi dari .agen_luar_uji.env -> lewat DASBOR (Variables), bukan baris perintah
#    opsional: AGEN_LUAR_ID (2573), FABIUS_GATE, ALASAN_DIR (/data/alasan), RPC_URL, ANALIS_TIAP_S (300) - bawaan sudah benar
#    JANGAN tambah variabel lain bernama *KEY* / *TOKEN* / *SECRET* (layanan menolak mulai)
# 3. volume: dasbor service -> Volumes -> mount path /data (USULAN)
# 4. domain publik: dasbor -> Settings -> Networking -> Generate Domain (port 8080), atau `railway domain --service agen-luar-uji`
# 5. kartu (di repo utama, butuh .agen_luar_uji.env untuk alamat dompet; tanpa tx: tokenURI = raw GitHub, URI tidak berubah)
python -X utf8 tools/agen_luar_uji.py kartu --domain <domain dari langkah 4>
#    -> docs/agen-luar-uji.json memuat "fabius": {"reasons": "https://<domain>/reasons/{bar_close}.json"}; commit + push
# 6. isi dompet agent 0xcFbB50cA211d70A7F7Ac036B80f408832caF5BB0 dengan 0,05 tBNB (USULAN; saldo 7 Okt 0,0098 = ±43 hari)
# 7. deploy (arsip HEAD hanya PATHS_LAYANAN)
python -X utf8 tools/railway_up.py --service agen-luar-uji
```

## Runbook

- **Mulai sehat** (`railway logs --service agen-luar-uji --lines 40`): `agent luar uji 2573 mulai | gerbang ... | alasan /data/alasan | port 8080`,
  lalu `meja: join HTTP 201` dan `meja: siklus <n> HTTP 200` tiap 5 menit. `curl https://<domain>/health` -> `join`, `siklus_terakhir`, `analis.status`.
- **Status analis** (`/health` -> `analis.status`): `tunggu-data` (tick ledger belum masuk) -> `dikomit` (log `analis bar <close>: <bot> (<k>) reasonHash
  0x... DIKOMIT <tx>`) -> `sudah` sampai penutupan -> `lewat`. `gagal` = dicoba lagi 5 menit kemudian; `berhenti` = 3 tx terkirim gagal untuk bar itu
  -> baca log, cek saldo, perbaiki, bar berikutnya jalan sendiri.
- **Sesudah 00:00 UTC:** `curl https://<domain>/reasons/<bar_close>.json` = 200; dalam ±1 jam (kartu baru: ±6 jam) `/analysts/registry` memuat 2573
  sebagai agent LUAR dengan alasan terverifikasi hash.
- **exit 4 "tidak bisa ditulis"** = volume milik root: set variabel `RAILWAY_RUN_UID=0` (container jalan sebagai root; USULAN, tukar-guling: image
  tidak lagi non-root) lalu redeploy.
- **exit 3 "MENOLAK MULAI"** = hapus variabel rahasia lain yang dicetak namanya.
- **Berhenti / balik:** hapus deployment / service di dasbor; pick yang sudah dikomit tetap di chain, alasan yang belum diambil gerbang hilang bersama
  volume. Penjawab laptop bisa dinyalakan lagi (`tools/agen_luar_uji.py jalan`).

## USULAN (belum diputus builder)

Aturan pilihan harian + keyakinan 30-70 · cadangan 2 jam sebelum penutupan · `MAKS_TERKIRIM` = 3 tx gagal per bar · volume di `/data`, `ALASAN_DIR` =
`/data/alasan` · port 8080 · interval analis 300 s · isi dompet 0,05 tBNB · `RAILWAY_RUN_UID=0` bila volume tidak bisa ditulis.

## Bukti (7 Okt 2026, worktree `kerja-p151`)

`python -X utf8 -m pytest -q engine/tests/test_agen_luar_layanan.py` -> 12 lulus (+4 subtes): aturan 4 rezim + determinisme + rumus hash = gerbang ·
penolakan rahasia · tunggu-data / komit sekali / lewat penutupan · alasan dipakai ulang sesudah kirim gagal · batas tx gagal · alasan 404 sebelum tutup,
byte persis sesudahnya, dibangun ulang dari salinan masukan · `analis.kartu_luar` membaca template kartu + `analis.alasan_luar` MENERIMA alasan yang
disajikan (hash salah = 0) · pull 404 -> join ulang · meja e2e gerbang lokal sungguhan `v2:x2573` ok · image tanpa `engine/` = calldata sama ·
entrypoint menolak rahasia lain / tanpa kunci. Sensus + T8: [[07-Testing/01 - Test Commands]].

**Terkait:** [[04-Tools/TL33 - agent analis]] · [[04-Tools/TL38 - agent luar di meja (pull)]] · [[07-Testing/T8 - Semantik Kegagalan Operator]] SK-AL1..SK-AL9 · [[08-Backlog/01 - Backlog]] P151, P166 ·
[[00-Overview/03 - Decisions]] F-D107, F-D121
