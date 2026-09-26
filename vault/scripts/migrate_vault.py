"""Pindahkan vault Fabius ke struktur bertingkat (pola vault Lencana) + tulis halaman yang belum ada.

Kenapa skrip, bukan edit manual satu-satu:
  - pemindahan 12 halaman lama harus UPDATE tautan di dalam berkas yang dipindah JUGA; edit manual
    adalah cara paling pasti untuk meninggalkan tautan rusak di tengah 40 berkas;
  - halaman lama TIDAK ditulis ulang. Konten lama dipindah utuh. Menyalin ringkasan dari memori
    adalah cara klasik menghasilkan vault yang rapi tapi salah - dan vault yang salah lebih buruk
    dari vault yang belum rapi.

Dua hal yang dibedakan secara sadar dari vault Lencana (alasan ditulis di Conventions.md):
  - bahasa catatan: Indonesia (vault ini dibaca builder + agen lanjutan; README publik ikut),
    sementara istilah teknis, ID, dan nama error tetap Inggris;
  - "satu angka hanya boleh masuk kalau ada perintah yang mencetaknya" DIPERTAHANKAN utuh -
    itu aturan yang membuat vault ini berguna, bukan gaya.

Pakai: python scripts/migrate_vault.py --dry-run
       python scripts/migrate_vault.py
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
# Windows: cmd.exe default cp1252 dan glyph yang kami cetak (`①④⑥` di arah, `⚠` di laporan)
# bukan bagian dari yang di-hash - jadi encoding stdout yang disetel, bukan stringnya.
# Tanpa ini, `print` bisa pecah DI TENGAH tabel dan separuh hasilnya terbaca seperti laporan penuh.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # stdout tanpa reconfigure (mis. tertangkap harness) = biarkan apa adanya

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- lama -> baru (dipindah utuh)
MOVES = [
    ("00-Mulai.md",                              "00-Overview/01 - Briefing.md"),
    ("01-Klaim-Dan-Batas.md",                    "06-Results/01 - Claims and Limits.md"),
    ("02-Ambang.md",                             "06-Results/02 - Thresholds.md"),
    ("03-Dataset.md",                            "03-Data/01 - Dataset.md"),
    ("04-Kontrak.md",                             "02-Contracts/01 - DecisionAnchor.md"),
    ("05-Belum-Terbukti.md",                      "06-Results/03 - Not Yet Proven.md"),
    ("06-Keputusan.md",                           "00-Overview/03 - Decisions.md"),
    ("07-Deploy-97.md",                          "02-Contracts/02 - Deployed on 97.md"),
    ("08-Kelas-Aset-dan-Kursi.md",               "01-Agent/01 - Asset Classes and Seats.md"),
    ("09-Uji-Arah-Tidak-Ada-Edge.md",             "06-Results/04 - Negative Results.md"),
    ("10-Pra-Registrasi-Uji-Aliran.md",           "06-Results/05 - Pre-registration Flow.md"),
    ("11-Pra-Registrasi-Uji-Horison-Whale.md",    "06-Results/06 - Pre-registration Horizon.md"),
]

# ---------------------------------------------------------------- halaman baru (ringkas, faktual)
NEW = {}

NEW["START-HERE.md"] = """---
tags: [entry]
---

# START-HERE — vault Fabius

**Baca dulu ini, tiga baris:**

1. Fabius adalah agen riset BNB Chain yang **menerbitkan keputusan yang bisa dibuktikan salah**.
   Dia bukan bot yang menjanjikan untung — tiga jalur sinyal sudah kami uji dan dua kami kubur
   ([[06-Results/04 - Negative Results]], [[06-Results/06 - Pre-registration Horizon]]).
2. Setiap angka di vault ini punya perintah yang mencetaknya. Kalau halaman dan hasil run berbeda,
   **yang menang run-nya** ([[Conventions]] §2).
3. Yang boleh dikutip publik ada di [[10-Submissions/01 - Claims Cheat Sheet]]; yang dilarang
   juga di sana, beserta kalimat penggantinya.

## Siapa membaca apa

| kamu | mulai dari |
|---|---|
| juri / orang baru | [[00-Overview/01 - Briefing]] → [[10-Submissions/02 - Project Detail]] |
| yang mau menjalankan | [[00-Overview/04 - Run It]] (semua perintah, sekali copy) |
| yang mengaudit klaim | [[06-Results/01 - Claims and Limits]] + [[07-Testing/01 - Test Commands]] |
| agen lanjutan (sesi berikutnya) | [[09-Inbox/00 - Hub Inbox]] terakhir + [[08-Backlog/01 - Backlog]] |
| yang cari angka | [[Quick-Reference]] (alamat, hash, gas, tanggal, semua bersumber) |

## Peta lapisan

| # | Modul | Satu baris |
|---|---|---|
| 00 | [[00-Overview/00 - Hub Overview]] | produk, proses bisnis, keputusan, koreksi, cara menjalankan |
| 01 | [[01-Agent/00 - Hub Agent]] | apa yang agen putuskan, gerbang satu-arah, kursi & rotasi |
| 02 | [[02-Contracts/00 - Hub Contracts]] | kontrak di chain 97: anchor, vault eksekusi, venue, vendor x402 |
| 03 | [[03-Data/00 - Hub Data]] | perekam point-in-time, aliran wallet ⑦, kedalaman harga, Dune |
| 04 | [[04-Tools/00 - Hub Tools]] | satu catatan per perkakas, dengan apa yang ia tolak lakukan |
| 05 | [[05-Ecosystem/00 - Hub BNB Ecosystem]] | identitas ERC-8004, pembayaran x402, penemuan antar-agen |
| 06 | [[06-Results/00 - Hub Results]] | angka yang diukur, ambang terkunci, dan apa yang belum terbukti |
| 07 | [[07-Testing/00 - Hub Testing]] | rumah semua angka: perintah + keluaran aslinya |
| 08 | [[08-Backlog/01 - Backlog]] | sisa kerja, risiko, yang kami tunda dan alasannya |
| 09 | [[09-Inbox/00 - Hub Inbox]] | catatan sesi bertanggal (bahan mentah, belum terstruktur) |
| 10 | [[10-Submissions/01 - Claims Cheat Sheet]] | kalimat submission, alamat kontrak, angka publik |

Lihat juga [[Index]] (semua halaman), [[Conventions]] (aturan menulis), [[Dashboard]].
"""

NEW["Conventions.md"] = """---
tags: [reference]
---

# Conventions

Aturan menulis & merawat vault ini. Strukturasnya meniru vault Lencana (`app/vault/Conventions.md`)
karena pola itu terbukti menahan kami dari klaim yang terlalu besar — **isinya** sama sekali tidak
ditiru.

## Dua aturan yang mengalahkan sisanya

1. **Satu angka hanya boleh masuk kalau ada perintah yang mencetaknya.** Tiap "lulus", jumlah,
   alamat, gas, atau tanggal harus bisa direproduksi dari dalam repo ini (`Fabius/`). Kalau
   halaman dan run terbaru berbeda, **run yang menang**: perbaiki halamannya, jangan kutip
   halamannya. Angka yang cuma bisa dibuktikan dari luar repo (laptop pribadi, folder riset lain)
   bukan klaim produk ini — dia masuk `09-Inbox/` dengan sumbernya, atau tidak masuk sama sekali.
2. **Tidak ada klaim yang boleh melebihi yang diukur.** [[10-Submissions/01 - Claims Cheat Sheet]]
   berisi kalimat yang kami larang untuk diri sendiri beserta pengganti jujurnya. Sebelum
   menulis README, slide, atau caption video, cek ke sheet itu.

## Beda sadar dari vault Lencana (dan alasannya)

| Lencana | Fabius | kenapa |
|---|---|---|
| catatan berbahasa Inggris | **berbahasa Indonesia**, istilah teknis/ID/nama error tetap Inggris | pembaca utama vault ini builder + agen sesi berikutnya, dan repo Fabius sendiri berbahasa Indonesia; memecah bahasa catatan dari bahasa repo membuat keduanya lebih sulit dibaca |
| `scripts/*.ps1` | `scripts/*.py` | PowerShell 5.1 di mesin ini pernah menanam BOM ke berkas Solidity dan solc menolaknya tanpa menyebut "BOM"; Python + `.gitattributes` lebih tahan |
| `D##` (keputusan) | `F-D##` | nomor dipakai bersama antar-proyek di workspace yang sama; tabrakan nomor sudah terjadi |

ID lain: `P#` backlog · `A#` agen · `C#` kontrak · `D#` data · `TL#` perkakas · `E#` ekosistem ·
`R#` hasil · `T#` testing · `OI-#` open item. **ID yang sudah dipakai tidak diganti**; bikin ID baru
tanpa menambah baris ke peta dokumen = cacat.

## Struktur

```
00-Overview/   produk, proses bisnis, keputusan, koreksi, cara menjalankan
01-Agent/      apa yang agen putuskan; gerbang; kelas aset; kursi
02-Contracts/  satu catatan per kontrak yang ter-deploy / akan di-deploy
03-Data/       perekam, kedalaman harga, Dune, integritas dataset
04-Tools/      satu catatan per perkakas + apa yang ia TIDAK boleh lakukan
05-Ecosystem/  identitas 8004, pembayaran x402, penemuan antar-agen
06-Results/    ambang, angka, hasil negatif, pra-registrasi
07-Testing/    rumah semua angka: perintah + keluaran
08-Backlog/    sisa kerja + acceptance criteria per item
09-Inbox/      catatan sesi bertanggal (mentah, belum terstruktur)
10-Submissions/ kalimat klaim, alamat, angka publik
Concepts/      catatan konsep atomik (#concept)
Templates/     kerangka halaman
scripts/       sync_vault.py, check_links.py, new_note.py
```

## Penamaan

- folder modul: `NN-Nama`; hub: `NN - Judul.md`; part note: `<Prefix><k> - Judul.md`
  (nomor urut **per kelompok**, jangan direset per berkas).
- nama berkas tanpa `: \\ / | ? * " < >`, tanpa emoji (tautan & git rusak); emoji di heading boleh.
- **`[[wikilink]]`** untuk antar-halaman; **inline code path** untuk kode/konfig/out-build;
  markdown biasa untuk URL eksternal. Repo-relative, jangan absolut (`C:\\...` hanya bekerja di
  satu mesin di dunia).

## Format part note

Frontmatter `tags` (kategori + identitas, mis. `tags: [kontrak, "C2"]`), lalu
`**Bagian dari:**`, `**Sumber:**`, `**Ringkasan:**`, `**Poin kunci:**`, `**Detail:**`,
`**Terkait:**`. Untuk dokumen per-item wajib ada **baris peta** yang menunjuk saudaranya.

## Perawatan

- Setelah menambah/mengganti nama halaman: `python scripts/sync_vault.py` lalu
  `python scripts/check_links.py` → target **`Broken: 0`**.
- `_Auto-Index.md` jangan disunting manual (dibangkitkan).
- Halaman lama yang digantikan tidak dihapus diam-diam: dipindah + banner
  `⚠️ DIARSIPKAN — lihat <halaman baru>` di kepala, atau isinya dipindah di commit yang sama.
- Koreksi tetap terlihat. Kalau ada klaim sebelumnya yang salah, tulis apa yang salah dan apa yang
  membuktikannya ([[00-Overview/05 - Corrections]]) — jangan sunting sejarah jadi rapi.
- Catatan sementara masuk `09-Inbox/` dengan awalan tanggal
  (`Session-2026-09-27.md`, `Status-2026-09-27.md`).
- Jebakan yang sudah menghantam vault ini (kode yang tertulis sebagai fakta tapi tidak diverifikasi,
  salinan lokal dianggap keadaan sistem) dicatat di [[Concepts/Stale Local Copy]] — baca sebelum
  menyimpulkan "mati" dari satu sumber.

Lihat: [[Index]] · [[Quick-Reference]] · [[Dashboard]] · [[START-HERE]]
"""

NEW["Index.md"] = """---
tags: [hub, index]
---

# 📘 Index — vault Fabius

Masuk struktural: setiap lapisan, satu baris. Untuk orientasi & hitung mundur, baca [[START-HERE]].

## 🚪 Pintu masuk

- [[START-HERE]] — posisi proyek, siapa membaca apa
- [[Conventions]] — aturan yang membuat folder ini bisa dipercaya
- [[00-Overview/01 - Briefing]] — produknya dalam bahasa orang awam
- [[00-Overview/02 - Business Process]] — siapa membayar, untuk apa, uangnya lewat mana
- [[06-Results/01 - Claims and Limits]] — yang terbukti vs yang tidak
- [[10-Submissions/01 - Claims Cheat Sheet]] — kalimat yang kami larang untuk diri sendiri
- [[08-Backlog/01 - Backlog]] — sisa kerja
- [[Quick-Reference]] — alamat, perintah, angka

## 🗂️ Lapisan

| # | Modul | Satu baris |
|---|---|---|
| 00 | [[00-Overview/00 - Hub Overview]] | produk, proses bisnis, keputusan `F-D##`, koreksi, cara menjalankan |
| 01 | [[01-Agent/00 - Hub Agent]] | alur keputusan, gerbang satu-arah, kelas aset, kursi & rotasi |
| 02 | [[02-Contracts/00 - Hub Contracts]] | DecisionAnchor · ExecutionVault · DemoPair/DemoAsset · vendor x402 |
| 03 | [[03-Data/00 - Hub Data]] | universe, wallet-flow ⑦, kedalaman harga, Dune, integritas sha256 |
| 04 | [[04-Tools/00 - Hub Tools]] | judge · direction · security_gate · anchor · ledger · backtest · x402 |
| 05 | [[05-Ecosystem/00 - Hub BNB Ecosystem]] | identitas 8004 (tokenId 2494), pembayaran x402, penemuan |
| 06 | [[06-Results/00 - Hub Results]] | ambang, hasil negatif, hasil jatuh tempo, pra-registrasi |
| 07 | [[07-Testing/00 - Hub Testing]] | rumah setiap angka, dengan keluaran aslinya |
| 08 | [[08-Backlog/01 - Backlog]] | yang tersisa + risiko + yang ditunda dan alasannya |
| 09 | [[09-Inbox/00 - Hub Inbox]] | catatan sesi bertanggal |
| 10 | [[10-Submissions/01 - Claims Cheat Sheet]] | kalimat publik, alamat kontrak untuk form |

## ⚡ Referensi

[[Quick-Reference]] · [[Dashboard]] · [[_Auto-Index]] · [[Conventions]]

## 🗺️ Semua halaman (otomatis)

```dataview
LIST FROM "" WHERE file.name != "Index" AND file.name != "_Auto-Index" SORT file.folder ASC, file.name ASC
```
"""

NEW["Quick-Reference.md"] = """---
tags: [reference]
---

# Quick-Reference

Semua yang biasa dicari, satu baris per fakta, **dengan sumber angkanya**. Angka tanpa sumber
dihapus saat audit, bukan disimpan sopan-sopanan.

## Alamat & kontrak

| apa | nilai | dari mana |
|---|---|---|
| DecisionAnchor (chain 97) | `0xdd162afb5f5f92d5092f845a93660e3b38259330` | [[02-Contracts/02 - Deployed on 97]] |
| agen (penanda-tangan anchor) | `0x4bb30E3b3bc22082c1935fE3bE7c07448e69c862` | `Fabius/.agent.env` (tidak di-commit) |
| x402 `IdentityRegistry` 97 | `0x8004A818BFB912233c491871b3d84c89A494BD9e` | [[05-Ecosystem/01 - ERC-8004 Identity]] |
| tokenId agen | **2494** | `python tools/x8004_register.py --verify` |
| x402 proxy kanonis | `0x402085c248EeA27D92E8b30b2C58ed07f9E20001` (ada kode di 56 & 97) | [[05-Ecosystem/02 - x402 Payment]] |
| Permit2 | `0x000000000022D473030F116dDEE9F6B43aC78BA3` | sama |
| X402DemoToken (koin demo kami) | `0xB11D90214089684081F57A03d3300E20725297f8` | `python tools/x402_deploy.py` |

## Perintah yang paling sering dipakai

```bash
forge test                                                     # 21 anchor (profil default)
FOUNDRY_PROFILE=fork forge test --fork-url bscTestnet          # 44 test, termasuk settlement x402
FOUNDRY_PROFILE=fork forge test --match-contract ExecutionVaultTest   # 18 test jalur eksekusi
python -u tools/anchor.py --verify                             # baca ulang trail chain: tanpa kunci/gas
python -u tools/ledger.py                                      # nilai posisi jatuh tempo (atau: belum)
python -u tools/direction.py --top 5 --emit                    # siklus keputusan
python -u universe/write_universe_manifest.py                  # integritas dataset (sha256 per baris)
python -u _research/panel_stats.py                             # ukuran panel ⑦
```

## Angka yang sedang berlaku (per 27 Sep, semua terukur)

| fakta | angka | sumber |
|---|---|---|
| anchor di chain | **17** (Enter 3 / Abstain 14) | `anchorCount()` / `countByVerdict` |
| verifikasi ulang trail | 11/11 cocok 6 field, 0 BEDA | `anchor.py --verify` |
| posisi jatuh tempo | 2: **+1,5** dan **−146,3 bps** net | `ledger.py`, [[06-Results/07 - Matured Outcomes]] |
| biaya round-trip venue demo | **59 bps** | `forge test --match-test test_round_trip_...` |
| hasil uji aturan arah | rugi setelah ongkos **12/12**; dibalik tetap kalah | [[06-Results/04 - Negative Results]] |
| hasil uji smart money 4 j | **−10,4 bps** vs kerumunan, p=0,568 | [[06-Results/06 - Pre-registration Horizon]] |
| aliran wallet terekam | 7.137 transaksi / 322 maker / 10,14 jam | `_research/panel_stats.py` |
| integritas dataset | **60 dari 62** snapshot lolos verifikasi sha256 | `write_universe_manifest.py` |
| kredit Dune terpakai hari ini | 1,259 (agregat 90 hari, ±11 s) | `execution_cost_credits` di API |

## Batas yang harus ikut disebut kapan pun angka di atas dikutip

- semua settlement & deploy di **BNB Chain testnet (97)**; tidak ada dana nyata
- token pembayaran adalah **koin demo milik kami sendiri**
- gateway x402 berjalan **di mesin kami** (belum di-host) — lihat [[05-Ecosystem/03 - Discovery Gap]]
- jalur eksekusi **sudah ada dan teruji, belum dipakai trading nyata di 97** (lihat [[08-Backlog/01 - Backlog]] P1)

Lihat juga: [[START-HERE]] · [[06-Results/01 - Claims and Limits]]
"""

NEW["Dashboard.md"] = """---
tags: [dashboard]
---

# Dashboard

Pertanyaan proyek dalam bentuk tabel. Semua barisnya diambil dari perintah yang ada di repo;
kolom "diperbarui" adalah tanggal run, bukan tanggal edit halaman.

| pertanyaan | jawaban sekarang | dibuktikan oleh | diperbarui |
|---|---|---|---|
| Produknya apa? | agen yang menerbitkan keputusan yang bisa dibuktikan salah | [[00-Overview/01 - Briefing]] | 2026-09-27 |
| Kenapa tidak "bot trading"? | tiga jalur sinyal diuji; dua mati, satu ditahan karena lookahead | [[06-Results/04 - Negative Results]] | 2026-09-27 |
| BNB-nya di mana? | kontrak 97 · identitas ERC-8004 · pembayaran x402 · venue & vault eksekusi | [[05-Ecosystem/00 - Hub BNB Ecosystem]] | 2026-09-27 |
| Bisa dijalankan orang lain? | ya: `forge test`, `anchor.py --verify` (tanpa kunci), `ledger.py` | [[07-Testing/01 - Test Commands]] | 2026-09-27 |
| Angka paling jujur yang kami punya | −72,4 bps rata-rata dari 2 posisi jatuh tempo (n=2) | [[06-Results/07 - Matured Outcomes]] | 2026-09-27 |
| Yang paling lemah sekarang | eksekusi nyata belum terjadi di 97; gateway belum di-host | [[08-Backlog/01 - Backlog]] | 2026-09-27 |
| Berapa sisa waktu | tenggat 30 Sep 23:59 **WIB** | [[00-Overview/06 - Roadmap]] | 2026-09-27 |

```dataview
TABLE WITHOUT ID file.folder AS folder, file.name AS halaman
FROM "09-Inbox" SORT file.name DESC
```
"""

for f in ["00-Overview/00 - Hub Overview.md", "01-Agent/00 - Hub Agent.md",
          "02-Contracts/00 - Hub Contracts.md", "03-Data/00 - Hub Data.md",
          "04-Tools/00 - Hub Tools.md", "05-Ecosystem/00 - Hub BNB Ecosystem.md",
          "06-Results/00 - Hub Results.md", "07-Testing/00 - Hub Testing.md",
          "09-Inbox/00 - Hub Inbox.md"]:
    NEW[f] = None  # diisi oleh HUBS di bawah

HUBS = {
    "00-Overview/00 - Hub Overview.md": ("overview", "Overview", """
Ini lapisan "apa dan kenapa": produk, proses bisnis, keputusan (`F-D##`), koreksi kami sendiri,
dan cara menjalankan. **Bukan** tempat angka hasil pengukuran — itu di `06-Results/` dan
`07-Testing/`. Yang tidak ada di sini: detail kontrak (02) dan perilaku perkakas (04).""",
        ["[[01 - Briefing]] — produk dalam bahasa orang awam",
         "[[02 - Business Process]] — siapa membayar, untuk apa, uangnya lewat mana",
         "[[03 - Decisions]] — keputusan F-D## beserta alasannya",
         "[[04 - Run It]] — semua perintah, sekali copy",
         "[[05 - Corrections]] — klaim kami yang salah dan apa yang membuktikannya",
         "[[06 - Roadmap]] — hitung mundur ke tenggat 30 Sep WIB"]),
    "01-Agent/00 - Hub Agent.md": ("agen", "Agent", """
Alur keputusan agen: rekam → saring → putuskan → anchor → nilai. Prinsip yang menahan semuanya:
**gerbang hanya boleh mengurangi** — tidak ada komponen (model, ④, kursi) yang bisa membuka posisi
yang ditolak gerbang lain. Yang TIDAK dilakukan agen: menyimpan dana siapa pun, menandatangani
order nyata ke venue utama, menjanjikan return.""",
        ["[[01 - Asset Classes and Seats]] — 7 bidang data, 8 kelas aset, 5 kursi + rotasi",
         "[[A2 - Decision Spine]] — rekam → gerbang → hash → anchor → ledger",
         "[[A3 - One-Way Gates]] — doktrin satu-arah dan di mana saja ia ditegakkan"]),
    "02-Contracts/00 - Hub Contracts.md": ("kontrak", "Contracts", """
Kontrak yang benar-benar ada (atau akan di-deploy) di BNB Chain testnet 97. Satu catatan per
kontrak: apa yang ia tegakkan di byte-code, apa yang ia **tolak** lakukan, dan perintah untuk
membacanya sendiri. Angka gas di sini berasal dari receipt, bukan dari perkiraan.""",
        ["[[01 - DecisionAnchor]] — roster agen, verdict, hash; 21 test",
         "[[02 - Deployed on 97]] — alamat, biaya nyata, verifikasi chain, trail 17 anchor",
         "[[C3 - ExecutionVault]] — posisi nyata: plafon $5/hari, hash wajib, realized PnL",
         "[[C4 - DemoPair and DemoAsset]] — venue x·y=k dan kenapa kami bikin sendiri",
         "[[C5 - Vendored x402 Sources]] — verbatim + sha256, dan kenapa tidak dikompilasi"]),
    "03-Data/00 - Hub Data.md": ("data", "Data", """
Sumber data dan batas masing-masing. Yang membedakan vault ini: setiap halaman data menyebut
**kedalaman** (bisa ditarik mundur berapa lama?) dan **siapa yang bisa membantahnya**. Data yang
hanya maju (aliran wallet) diperlakukan sebagai aset yang bisa hilang — karena memang bisa.""",
        ["[[01 - Dataset]] — universe point-in-time, sha256 per baris, manifest & gap",
         "[[D2 - Wallet Flow]] — ⑦: jendela 8–13 menit, tanpa paging, rantai dispatch-diri",
         "[[D3 - Price Depth]] — Aster 9.599 bar vs GMGN 41,6 hari vs GeckoTerminal",
         "[[D4 - Dune]] — dialek Trino, kredit terukur, lag BSC ±1 jam"]),
    "04-Tools/00 - Hub Tools.md": ("perkakas", "Tools", """
Satu catatan per perkakas: apa yang ia cetak, apa yang ia **tolak** lakukan, dan bug yang sudah
pernah ia hasilkan. Kaidah yang diulang di semua halaman sini: alat yang gagal diam-diam lebih
berbahaya dari alat yang gagal keras.""",
        ["[[TL1 - judge]] — penilai LLM, veto satu-arah, `ask_jev`",
         "[[TL2 - direction]] — side/entry/stop/ukuran/horizon; dua rezim keluar",
         "[[TL3 - security_gate]] — 4 status; `UNMEASURED` bukan `bersih`",
         "[[TL4 - anchor and verify]] — trail on-chain; `getAnchor` kembalikan struct nol",
         "[[TL5 - ledger]] — event-level dedupe, `AMBIGU`, belum jatuh tempo ≠ hasil",
         "[[TL6 - x402 gate and client]] — bentuk wire dari specs, status lokal",
         "[[TL7 - measurement harness]] — backtest · whale_sweep · flow_test, dan pager statistik"]),
    "05-Ecosystem/00 - Hub BNB Ecosystem.md": ("ekosistem", "BNB Ecosystem", """
Jawaban atas pertanyaan "di mana BNB-nya?" — bukan "kita pakai data BSC", tapi partisipasi di rel
agen BNB Chain: identitas (ERC-8004), pembayaran (x402), dan eksekusi (kontrak kami di 97).
Setiap halaman di sini menyebut apa yang **belum**: hosting endpoint, penemuan oleh agen asing.""",
        ["[[01 - ERC-8004 Identity]] — tokenId 2494, diverifikasi dengan membaca registry",
         "[[02 - x402 Payment]] — transaksi nyata, klien nol gas, saldo dibaca dari chain",
         "[[03 - Discovery Gap]] — bagaimana agen lain menemukan kami (dan apa yang belum bisa)"]),
    "06-Results/00 - Hub Results.md": ("hasil", "Results", """
Tempat angka tinggal. Dua jenis halaman di sini: **ambang** (apa yang harus dilewati, ditulis
sebelum hasil) dan **vonis** (apa yang terjadi). Halaman pra-registrasi tidak boleh diedit setelah
hasil keluar — koreksi lewat halaman baru, supaya urutannya bisa dipertanggungjawabkan.""",
        ["[[01 - Claims and Limits]] — yang terbukti vs yang tidak",
         "[[02 - Thresholds]] — MIN_TRADES, BH α, ongkos 20 bps, asal tiap angka",
         "[[03 - Not Yet Proven]] — daftar hidup yang belum kami buktikan",
         "[[04 - Negative Results]] — aturan arah mati; smart money vs kerumunan",
         "[[05 - Pre-registration Flow]] — uji aliran kerumunan, terkunci sebelum hasil",
         "[[06 - Pre-registration Horizon]] — uji horison whale + vonisnya",
         "[[07 - Matured Outcomes]] — hasil pertama prediksi yang di-anchor"]),
    "07-Testing/00 - Hub Testing.md": ("testing", "Testing", """
Rumah resmi setiap angka. Aturan: sebuah angka masuk dokumen lain **hanya** kalau halaman di sini
punya perintah yang mencetaknya plus keluarannya. Kalau run hari ini berbeda dari halaman kemarin,
yang benar adalah run hari ini.""",
        ["[[01 - Test Commands]] — semua perintah, dalam satu tempat untuk di-copy",
         "[[T2 - Anchor Verify]] — trail dibaca ulang tanpa kunci",
         "[[T3 - forge execution suite]] — 18 test jalur eksekusi + biaya 59 bps",
         "[[T4 - x402 Fork Suite]] — 9 fork test lewat alias `bscTestnet`",
         "[[T5 - hygiene scanners]] — karakter asing, BOM, print non-cp1252, tautan vault"]),
    "09-Inbox/00 - Hub Inbox.md": ("inbox", "Inbox", """
Catatan sesi bertanggal, sebelum sempat distrukturkan. Isinya sah dikutip **kalau** menyebut
perintah/sumbernya; kalau sebuah fakta di sini sudah punya halaman permanen, rujuk halaman itu,
jangan gandakan kalimatnya.""",
        ["[[Session-2026-09-26-27]] — eksekusi, Dune, whale horison, dua koreksi diri"]),
}

for k, (tag, title, intro, parts) in HUBS.items():
    NEW[k] = f"""---
tags: [{tag}, hub]
---

# {title}

{intro.strip()}

## Bagian

- """ + "\n- ".join(parts) + """

## Terkait

- [[Index]] · [[Conventions]] · [[Quick-Reference]]

```dataview
LIST FROM #{tag} SORT file.name ASC
```
"""

NEW["10-Submissions/01 - Claims Cheat Sheet.md"] = """---
tags: [klaim, "OI-CS"]
---

# Claims Cheat Sheet — kalimat yang kami larang untuk diri sendiri

**Bagian dari:** [[10-Submissions/00 - Hub Submissions]]
**Sumber:** `README.md`, `06-Results/`, `07-Testing/`

Aturannya sederhana: kalau kalimatnya tidak bisa ditunjukkan ke satu baris keluaran perintah, dia
tidak masuk materi. Yang di bawah ini bukan saran gaya — ini penahan agar submission kami tidak
runtuh saat ada juri yang tahu x402.

| ❌ jangan | ✅ ganti dengan | kenapa |
|---|---|---|
| "agen trading yang menguntungkan" | "agen yang menerbitkan keputusan yang bisa dibuktikan salah" | 3 jalur sinyal diuji; rugi setelah ongkos (`06-Results/04`) |
| "edge tervalidasi di 30 hari" | "satu horison tempat whale > baseline acak — dan kami tidak mengklaimnya, karena panelnya dipilih oleh label pasca-sejarah" | batas atas lookahead (`06-Results/06` §2) |
| "verifiable / tamper-proof / siapa pun bisa memverifikasi" sebagai pembeda | "keputusannya ter-anchor **sebelum** hasilnya ada, dan `anchor.py --verify` membacanya tanpa kunci" | "verifiable" itu table stakes; yang langka urutannya |
| "terhubung ke ekosistem agen BNB" (tanpa lanjutannya) | "identitas ERC-8004 tokenId 2494 di `0x8004A818…` + pembayaran x402 lewat proxy kanonis di 97" | harus ada alamat & tx, bukan kategori |
| "endpoint publik kami" | "endpoint di mesin kami (belum di-host); URL berubah tiap run" | `agent-card.json` menuliskan itu; jangan menghapus katanya |
| "62 snapshot tervalidasi sha256" | "60 dari 62; 2 tidak bisa dihitung ulang dan pemicunya belum diketahui" | `write_universe_manifest.py` |
| "sistem kami sudah diperdagangkan" | "jalur eksekusi ada, 18 test lulus, dan belum ada posisi nyata di 97 (butuh 1 top-up gas)" | lihat [[08-Backlog/01 - Backlog]] P1 |
| "data real-time" | "aliran live GMGN (jendela 8–13 menit) untuk keputusan; Dune punya lag ±1 jam dan dipakai untuk sejarah" | `03-Data/D4` |
| angka win-rate apa pun dengan n < 20 | "n=2, satu menang +1,5 bps / satu rugi −146,3 bps; belum membuktikan apa pun" | `MIN_TRADES=20` (`06-Results/02`) |

Lihat juga: [[06-Results/01 - Claims and Limits]] · [[00-Overview/02 - Business Process]]
"""

NEW["10-Submissions/00 - Hub Submissions.md"] = """---
tags: [submission, hub]
---

# Submissions

Isi yang disiapkan untuk form & video. Bedanya dengan `06-Results/`: di sini kalimat sudah
dikalibrasi untuk pembaca luar; di sana angkanya hidup.

## Bagian

- [[01 - Claims Cheat Sheet]] — yang boleh dan tidak boleh dikatakan
- [[02 - Project Detail]] — ringkas (kotak deskripsi) dan panjang (dokumen)
- [[03 - Form Fields]] — alamat kontrak, network, dan apa yang tidak muat di form

## Terkait

- [[START-HERE]] · [[Conventions]]
"""

NEW["10-Submissions/02 - Project Detail.md"] = """---
tags: [submission, "P-DETAIL"]
---

# Project Detail — Fabius

**Bagian dari:** [[10-Submissions/00 - Hub Submissions]]
**Sumber:** `00-Overview/01 - Briefing.md`, `06-Results/`, `05-Ecosystem/`

## Kotak deskripsi (±2 kalimat, untuk form)

> Fabius adalah agen riset di BNB Chain yang menerbitkan **keputusan** atas aset meme — arah, masuk,
> stop, ukuran, horizon — dan menyimpan hash-nya ke chain **sebelum** hasilnya ada. Tiga jalur
> sinyal sudah kami uji sendiri; dua kami temukan mati setelah ongkos, danagenya sebagian besar
> **menolak** — penolakan itulah yang ikut ter-anchor (14 dari 17 keputusan), sehingga klaim
> "disiplin" kami bisa diperiksa, bukan didengar.

## Versi panjang

**Masalahnya bukan "tidak ada bot", tapi "tidak ada yang bisa membuktikan bot-nya jujur".**
Sebagian besar submission agen trading berakhir sebagai klaim: angkanya ada, tapi tidak ada satu pun
kalimat yang bisa diperiksa orang luar tanpa memercayai timnya. Kami membalik bobotnya.

**Yang kami buat.** Sebuah agen yang tiap siklus: merekam keadaan pasar (universe BSC + narasi +
aliran wallet, dengan sha256 dan timestamp milik mesin pihak ketiga) → menyaring lewat gerbang
keras (riwayat harga cukup? keamanan kontrak **terukur**? likuiditas cukup untuk keluar?) →
mengambil keputusan arah lengkap (long/short, masuk, stop, target, ukuran, horizon) → mengirim
hash keputusan + hash gerbang + hash snapshot ke kontrak di chain 97 → dan, setelah horizon lewat,
menilai dirinya sendiri dari harga yang ia ambil sendiri.

**Yang membuatnya bukan klaim kosong.** `anchor.py --verify` menghitung ulang id setiap anchor
dari berkas di repo, lalu membaca `getAnchor(id)` ke chain dan membandingkan enam field — termasuk
nama aset — **tanpa kunci dan tanpa gas**. 11/11 cocok. Dan yang paling penting: yang ter-anchor
bukan hanya keputusan berani, tapi juga **penolakan**, dengan alasannya ikut ter-hash.

**Bagian BNB-nya.** Agen ini punya identitas di `IdentityRegistry` ERC-8004 resmi chain 97
(tokenId 2494; diverifikasi dengan membaca registry, `ownerOf`/`getAgentWallet` = alamat agen),
menerbitkan kartu agen yang menyebut endpoint-nya, dan **menjual keluarannya lewat x402** ke proxy
kanonis `0x402085c2…` — ada transaksi nyata yang membuktikan pembayarannya (klien nol gas, uang
berpindah, kami baca saldo dari chain, bukan dari log server kami). Jalur eksekusi posisi
(`ExecutionVault` + `DemoPair`) sudah ada dengan pagar di kontrak: plafon harian, ukuran maksimum,
dan larangan membuka posisi tanpa hash keputusan yang ter-anchor.

**Yang tidak kami klaim.** Kami tidak menjual sinyal. Setelah ongkos nyata, momentum harga rugi di
12/12 aset; menyalin smart money di 24 jam justru **kalah** dari kerumunan; satu-satunya horison
yang menguntungkan kerumunan whale (30 hari) tidak bisa kami bersihkan dari bias seleksi sebelum
tenggat — jadi kami tinggal menunggu, bukan menjualnya. Semua testnet, token demo milik sendiri,
tanpa custody, tanpa dana pengguna.
"""

NEW["10-Submissions/03 - Form Fields.md"] = """---
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
| Smart contract (1 kolom) | `0xdd162afb5f5f92d5092f845a93660e3b38259330` — `DecisionAnchor` | `python tools/anchor.py --verify` |
| Network | **BSC Testnet (97)** | `eth_chainId` = 97 |
| Demo | folder `00-Overview/04 - Run It.md` = skrip video 5 menit | — |

Kontrak lain yang **tidak muat** di form dan harus disebut di README/deskripsi:
`ExecutionVault` & `DemoPair` (setelah P1 selesai), `X402DemoToken` `0xB11D9021…`, identitas
ERC-8004 tokenId `2494` di `0x8004A818BFB912233c491871b3d84c89A494BD9e` (registry pihak ketiga —
sebut sebagai milik mereka, bukan milik kami).

Syarat yang harus dicek ulang sebelum submit: tim terdaftar di Luma; kontrak resolve di BscScan;
repo publik; riwayat commit berada dalam periode hackathon.
"""

NEW["08-Backlog/01 - Backlog.md"] = """---
tags: [backlog, hub]
---

# Backlog

**Sumber:** keluaran perintah di `07-Testing/`, bukan perasaan. Tenggat: **30 Sep 23:59 WIB**.

| # | pekerjaan | status | yang menahan / bukti selesai |
|---|---|---|---|
| P1 | **Eksekusi nyata pertama di 97** (deploy `DemoAsset`+`DemoPair`+`ExecutionVault`, buka & tutup 1 posisi) | 🟡 alatnya ada, **terhenti oleh guard sendiri** | saldo agen 0,0079 tBNB < taksiran 0,018 → `python ../_research/topup_agent.py 0.03` lalu `python tools/exec_deploy.py`. Selesai = ada tx `status=1` + `openPositionOf` terbaca |
| P2 | **Host gateway x402** supaya URL kartu agen bukan `127.0.0.1` | ⬜ | `agent-card.json` menunjuk URL tetap; kartu tidak lagi ditulis "LOCAL ONLY" |
| P3 | **FE dua pintu** (Vercel, oleh builder) — orang awam lihat rekaman; agen baca kartu + bayar | ⬜ | halaman + data dari chain; `verify` dijalankan orang lain dari browser |
| P4 | `seats.py` — 5 kursi + rotasi memakai `seat_eligible` | ⬜ | `vault/08` §3 sudah jadi aturan, belum jadi kode |
| P5 | Uji A (prospektif, tanpa lookahead) pada horison 24/48 jam | ⏳ butuh waktu, bukan kerja | entri setelah 26 Sep 08:01Z dinilai 27–28 Sep |
| P6 | Investigasi 2 snapshot universe yang sha-nya tidak bisa dihitung ulang | ⬜ 2 hipotesis sudah digugurkan | `06-Results/03` #21 |
| P7 | Putuskan: 30 hari jadi fitur (butuh dana & waktu) atau tetap hipotesis terbuka | ⬜ keputusan builder | kalimat publik sudah dikunci di `10-Submissions/01` |

## Terkait

- [[00-Overview/06 - Roadmap]] · [[Index]]
"""

NEW["Concepts/One-Way Gate.md"] = """---
tags: [concept, "one-way-gate"]
---

# One-Way Gate — gerbang yang hanya boleh mengurangi

**Ringkas.** Di seluruh Fabius, komponen apa pun yang menilai suatu kandidat (model LLM, keamanan
kontrak ④, kapasitas keluar ⑥, plafon eksekusi) boleh **membatalkan** atau **mengecilkan**, tidak
pernah membuka posisi yang sudah ditolak gerbang lain.

**Kenapa ini bukan gaya bahasa.** Kalau satu komponen boleh membuka, maka setiap angka negatif dari
komponen lain jadi bisa ditawar, dan "disiplin" berubah jadi kosmetik. Doktrin ini yang membuat
kalimat "agen kami menolak 14 dari 17 keputusan" bisa dipercaya: penolakan tidak bisa dibalik oleh
siapa pun di hilir, termasuk kami.

**Di mana ditegakkan.** `tools/judge.py` (veto satu-arah, keputusan §1), `tools/direction.py::apply_gates`
(④ `BLOCKED` → `flat`; `UNMEASURED` mencabut hak kursi, bukan memberi),
`contracts/ExecutionVault.sol` (posisi ditolak tanpa `decisionHash`/`snapshotHash`, plafon di
byte-code, `HARD_CEILING` memotong perintah pemilik).

**Kebalikannya yang harus diwaspadai:** kegagalan pengukur **tidak** boleh diperlakukan seperti hasil
bersih — lihat [[Unmeasured Is Not Clean]].

Lihat: [[01-Agent/A3 - One-Way Gates]] · [[04-Tools/00 - Hub Tools]]
"""

NEW["Concepts/Unmeasured Is Not Clean.md"] = """---
tags: [concept, "unmeasured-not-clean"]
---

# Unmeasured Is Not Clean

**Ringkas.** "Tidak ada angka" bukan angka nol. Setiap kali Fabius butuh status keamanan kontrak,
ia memakai empat keadaan: `OK` / `BLOCKED` / `DISAGREE` / `UNMEASURED` — dan yang terakhir
**tidak** diperlakukan seperti bersih.

**Kenapa keras.** Kalau `UNMEASURED` disamakan dengan bersih, gerbang bisa di-bypass cukup dengan
membuat panggilannya gagal, dan kegagalan itu tidak meninggalkan bekas di data. Ini pola kegagalan
yang sama persis dengan yang kami temukan di tempat lain: `getAnchor(id)` tidak revert tapi
mengembalikan struct nol; hasil Dune yang berhenti di halaman pertama; salinan lokal dianggap
keadaan sistem.

**Terapan.** `tools/security_gate.py` (4 status; terpicu nyata saat GMGN membalas
`is_honeypot=null`), `03-Data/01 - Dataset.md` (baris tanpa alasan risiko dipisah dari baris
"bersih"), `06-Results/03 - Not Yet Proven.md`.

Lihat: [[One-Way Gate]] · [[Stale Local Copy]]
"""

NEW["Concepts/Stale Local Copy.md"] = """---
tags: [concept, "stale-local-copy"]
---

# Stale Local Copy — salinanmu bukan keadaan sistem

**Ringkas.** Untuk sistem yang penulisnya mesin lain (GitHub Actions, API pihak ketiga), jumlah
baris di diskamu bukan ukuran. Ukurannya: commit di `origin`.

**Kejadian nyata 27 Sep.** Aku melaporkan "perekam ⑦ mati 24 jam" setelah membaca
`universe/wallet-flow.jsonl` di laptop — padahal working copy-ku **78 commit tertinggal**. Di
origin perekam mengirim commit tiap ±3,5 menit tanpa henti; lubang nyatanya ±6 menit. Klaim
salah itu sempat masuk pesan ke builder dan commit message, lalu dicabut.

**Aturan turunannya.**
- `git fetch` dulu, baru simpulkan apa pun tentang "hidup/mati".
- Untuk hal ber-waktu: sumber waktu = timestamp pihak ketiga (commit Actions, epoch respons API),
  bukan jam laptop — ia pernah melompat setelah tidur.
- Untuk hal ber-status: kalau alat hanya bisa membaca satu berkas, ia tidak boleh mengklaim melihat
  sistem.

Ini pasangan dari [[Unmeasured Is Not Clean]]: keduanya tentang kesimpulan yang tampak berbukti
tapi sumbernya salah pilih.

Lihat: [[03-Data/D2 - Wallet Flow]] · [[00-Overview/05 - Corrections]]
"""

NEW["Concepts/Anchored Before Outcome.md"] = """---
tags: [concept, "anchored-before-outcome"]
---

# Anchored Before Outcome — urutannya adalah produknya

**Ringkas.** Nilai satu anchor bukan "kami menyimpan hash", tapi **urutan**: keputusan ditulis →
hash masuk chain → hasilnya baru ada belakangan. Yang dijual adalah ketidakmungkinan menyunting
masa lalu, bukan kecerdasan tebakannya.

**Konsekuensi yang tidak nyaman.** Karena urutannya yang dijunjung, kami **tidak boleh** menarik
anchor yang ternyata salah, dan tidak boleh menghapus penolakan. 14 dari 17 anchor adalah `ABSTAIN`
— justru itu yang membuat 3 sisanya berarti.

**Dua syarat supaya klaim ini tidak melunak jadi slogan:**
1. jejaknya harus bisa dibaca ulang oleh orang lain tanpa memercayai kami
   (`tools/anchor.py --verify`: hitung id dari berkas repo, baca `getAnchor` dari chain, bandingkan
   6 field — nol kunci, nol gas);
2. dan sumber datanya juga harus ber-timestamp pihak ketiga, bukan jam kami
   (`universe/manifest.txt`, `wallet-flow-manifest.txt`; lihat [[Stale Local Copy]]).

**Yang tidak dibuktikannya:** sama sekali tidak ada. Anchor tidak membuat keputusan kami benar.
Itu urusan [[06-Results/00 - Hub Results]].

Lihat: [[02-Contracts/01 - DecisionAnchor]] · [[One-Way Gate]]
"""

NEW["Notes/README.md"] = """---
tags: [inbox, hub]
---

# Notes / Inbox

Catatan sesi bertanggal. Nama: `Session-YYYY-MM-DD[-topik].md`, `Status-YYYY-MM-DD.md`.

- Satu sesi = satu berkas; jangan menambal berkas sesi lama dengan temuan baru.
- Angka di sini wajib menyebut perintahnya, atau ditandai "belum diukur".
- Begitu sebuah fakta punya halaman permanen di `00`–`10`, rujuk halaman itu dari sini.

Isi sekarang: [[Session-2026-09-26-27]]
"""

# ------------------------------------------------------------------- isi ditulis di langkah kedua
SESSION_NOTE = None  # ditulis oleh script berikutnya (butuh angka dari run)


def write(rel, text):
    p = os.path.join(VAULT, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    moves = []
    for old, new in MOVES:
        src = os.path.join(VAULT, old.replace("/", os.sep))
        dst = os.path.join(VAULT, new.replace("/", os.sep))
        if not os.path.exists(src):
            print(f"  LEWATI   {old} (tidak ada)")
            continue
        if os.path.exists(dst):
            print(f"  LEWATI   {new} (sudah ada - jangan timpa)")
            continue
        moves.append((src, dst, old, new))
        print(f"  pindah   {old}  ->  {new}")

    for rel, text in NEW.items():
        if text is None:
            continue
        if a.dry_run:
            print(f"  tulis    {rel}")
            continue
        write(rel, text)
        print(f"  tulis    {rel}")

    if a.dry_run:
        print("\nDRY-RUN: tidak ada yang ditulis/dipindah.")
        return

    # pindah + sisakan penunjuk, supaya tautan lama dari README/catatan lain tidak jadi lubang
    for src, dst, old, new in moves:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        with open(src, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("---\ntags: [arsip]\n---\n\n"
                     f"# ⚠️ DIARSIPKAN — pindah ke `{new}`\n\n"
                     "Halaman ini tidak lagi dipelihara di sini; isinya dipindah **utuh** (bukan "
                     "disalin dari ingatan) ke lokasi di atas. Jangan menulis temuan baru di file "
                     "arsip — itu cara vault berdivergensi jadi dua kebenaran.\n")
    print("\npencaharian tautan lama -> baru di seluruh vault ...")
    pat = {re.escape(old): new for old, new in MOVES}
    n = 0
    for dirpath, _dirs, files in os.walk(VAULT):
        if any(x in dirpath for x in (os.sep + ".git", "scripts")):
            continue
        for fn in files:
            if not fn.endswith(".md"):
                continue
            p = os.path.join(dirpath, fn)
            try:
                txt = open(p, encoding="utf-8").read()
            except (OSError, UnicodeDecodeError):
                continue
            out = txt
            for rx, new in pat.items():
                out = re.sub(rx, new, out)
            if out != txt:
                with open(p, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(out)
                n += 1
    print(f"  {n} berkas diperbarui tautannya")
    print("selesai. lanjutkan: python scripts/sync_vault.py && python scripts/check_links.py")


if __name__ == "__main__":
    main()
