"""Catat bukti P1 (posisi nyata pertama) dan P8 (jalur pemeriksaan hidup dari clone) ke halaman
pemiliknya. Sekali-jalan; setiap pasangan wajib ketemu tepat satu kali, yang tidak ketemu
dilaporkan supaya bisa dibaca, bukan dilewati diam-diam.

Kenapa lewat skrip dan bukan edit manual: tiga edit tanganku hari ini salah arah dan meninggalkan
berkas yang *compile* tapi rusak strukturnya (lihat komentar di `_research/patch_agent_sources.py`).
Untuk perubahan teks massal, cara mengamannya adalah assert jumlah + laporan, bukan keyakinan.
"""
import io
import os
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isdir(os.path.join(VAULT, "00-Overview")):
    sys.exit(f"VAULT bukan folder vault: {VAULT}")

E = []   # (berkas, lama, baru)

# ---------------------------------------------------------------- Quick-Reference: alamat + angka
E.append(("Quick-Reference.md",
 "| ExecutionVault (chain 97) | `0x2743cD33C8790437594E119289838F35c0d1d290` | belum ter-deploy — lihat [[08-Backlog/01 - Backlog]] P1 |",
 "| ExecutionVault (97) | `0x2743cD33C8790437594E119289838F35c0d1d290` | ter-deploy 27 Sep, cap $5/hari + $1/posisi (owner = agen, tidak ada jalan pintas) |\n| DemoPair (97) | `0x6f93d787bBE99A6842CCa511ccB3b8D6d976696E` | venue x·y=k, fee 30 bps, spot 2,0000 |\n| DemoAsset (97) | `0x4180A42A119F0B5480637900679C0AaFB1F2a8d7` | ERC20 demo 6 desimal (bukan OZ — lihat [[02-Contracts/C4 - DemoPair and DemoAsset]]) |\n| manifest alamat ter-track | `deployments/97.json` | 8 alamat + hasil cek bytecode dari chain; inilah yang membuat `--verify` jalan di clone |"))

E.append(("Quick-Reference.md",
 "| agen (roster `DecisionAnchor`) | `0x4bb30E3b3bc22082c1935fE3bE7c07448e69c862` | `countByAgent` = ? |",
 "| agen (roster `DecisionAnchor`) | `0x4bb30E3b3bc22082c1935fE3bE7c07448e69c862` | `getAgent()` aktif=True, `countByAgent()` = **17** (= `anchorCount()`) |"))

E.append(("Quick-Reference.md",
 "| posisi nyata di 97 lewat vault | 0 | belum ada — [[08-Backlog/01 - Backlog]] P1 |",
 "| posisi nyata di 97 lewat vault | 2 round-trip, masing-masing **−59 bps** | `decisions/execution-trail.jsonl`; harga dari pool, angka dari event `Closed` |"))

# ---------------------------------------------------------------- Backlog: P1 & P8 selesai
E.append(("08-Backlog/01 - Backlog.md",
 "| P1 | **Eksekusi nyata pertama di 97** (deploy `DemoAsset`+`DemoPair`+`ExecutionVault`, buka & tutup 1 posisi) | 🟡 alatnya ada; blocker-nya **taksiran guard**, bukan dana |",
 "| P1 | **Eksekusi nyata pertama di 97** (deploy `DemoAsset`+`DemoPair`+`ExecutionVault`, buka & tutup 1 posisi) | ✅ **selesai 27 Sep** — 2 round-trip nyata, realized −59 bps per putaran |"))

E.append(("08-Backlog/01 - Backlog.md",
 "| P8 | **Bukti clone bersih** — `git clone` ke direktori kosong, lalu jalankan baris 1–6 registry [[07-Testing/01 - Test Commands]] | ⬜ | tangkapan keluarannya ditempel di halaman itu. Ini yang membuat \"verifiable tanpa kami\" berdiri: sampai sekarang belum pernah kujalankan dari clone, hanya dari working copy ini |",
 "| P8 | **Bukti clone bersih** — `git clone` ke direktori kosong, lalu jalankan baris 1–6 registry [[07-Testing/01 - Test Commands]] | ✅ **selesai 27 Sep: 4/4**, dan tesnya menemukan dua klaim yang tadinya palsu | lihat [[07-Testing/T6 - Clean Clone Evidence]] — `--verify` gagal di clone karena alamat agen cuma ada di `.agent.env` (di-gitignore); diperbaiki lewat `deployments/97.json` + cek roster ke kontrak |"))

# ---------------------------------------------------------------- Corrections: tiga baris baru
E.append(("00-Overview/05 - Corrections.md",
 "| 27 Sep | `git add -A` di repo induk (2×) | ikut menelan berkas sesi lain ke commit-ku | `git show --stat`; dipecah ulang, tidak ada yang hilang |",
 "| 27 Sep | `git add -A` di repo induk (2×) | ikut menelan berkas sesi lain ke commit-ku | `git show --stat`; dipecah ulang, tidak ada yang hilang |\n| 27 Sep | \"`anchor.py --verify` nol kunci, siapa pun bisa periksa\" | **gugur di clone bersih**: `AGENT_ADDRESS` hanya hidup di `.agent.env` yang di-gitignore, jadi perintahnya mati dengan \"AGENT_ADDRESS tidak diketahui\". Yang kami maksud sebenarnya \"terbuka kalau punya salinan kerja kami\" | `python -X utf8 _research/probe_clone_paths.py` -> rc=1; sekarang alamat jatuh ke `deployments/97.json` **dan** dicek ke kontrak (`getAgent`/`countByAgent`) |\n| 27 Sep | \"P1 terhenti karena kekurangan gas\" | guard memang menolak, tapi pakai **plafon 1 gwei** sementara testnet live 0,10 gwei: jalur penuh 0,0018 tBNB vs saldo 0,0079 -> dananya cukup. Yang menahan adalah taksiran konservatif, dan itu harus dipilih sadar (top-up atau turunkan plafon), bukan diwarisi | `python -X utf8 _research/read_balances.py`; lalu P1 jalan dan selesai |\n| 27 Sep | hipotesis \"selisih 17 vs 11 itu karena `--verify` cuma baca `direction-*`\" | **dibantah oleh pengukuran**: perluasan cakupan malah menyeret 301 baris kandidat `screen` (termasuk nama token non-ASCII) jadi keluarannya \"11/312 cocok\". Cakupan dikembalikan; P6b tetap terbuka, sekarang dengan peringatan di keluaran `--verify` | `decisions-20260923.jsonl` isinya kandidat, bukan keputusan |"))

# ---------------------------------------------------------------- C3 / C4: status eksekusi
E.append(("02-Contracts/C3 - ExecutionVault.md",
 "**Detail:** bug yang sudah dikoreksi dicatat di komentar kontrak (bukan dihapus) supaya pembaca\nmengerti kenapa urutannya penting. Deploy & posisi nyata: [[08-Backlog/01 - Backlog]] P1.",
 "**Detail:** bug yang sudah dikoreksi dicatat di komentar kontrak (bukan dihapus) supaya pembaca\nmengerti kenapa urutannya penting.\n\n**Status 27 Sep: ter-deploy dan pernah dipakai.** `ExecutionVault`\n`0x2743cD33C8790437594E119289838F35c0d1d290` di 97, cap harian 5 unit / per posisi 1 unit\n(`setCaps` tx nyata), dan **dua round-trip nyata** sudah melewatinya: `openLong` gas 258.008/295.443,\n`close` 123.216/150.576, realized **−59 bps** keduanya — dibaca dari event `Closed`, bukan\nhitungan kami (`decisions/execution-trail.jsonl`). Yang tetap belum: venue pasar sungguhan dan\nkeputusan yang dihasilkan siklus otomatis (dua posisi ini memakai hash keputusan 24 Sep)."))

E.append(("02-Contracts/C4 - DemoPair and DemoAsset.md",
 "- Yang **tidak** diklaim: kurva ini mewakili pasar meme sungguhan. Yang dibuktikan: proses eksekusi\n  (harga dari kontrak, bukan dari kami) dan **besarnya ongkos**.",
 "- Yang **tidak** diklaim: kurva ini mewakili pasar meme sungguhan. Yang dibuktikan: proses eksekusi\n  (harga dari kontrak, bukan dari kami) dan **besarnya ongkos** — dan sejak 27 Sep yang kedua punya\n  dua angka yang saling mengunci: test suite memprediksi **59 bps**, eksekusi nyata di 97 menghasilkan\n  **−59 bps** realized per round-trip. Prediksi dan kenyataan bertemu di angka yang sama; itu property\n  yang tidak bisa direkayasa dengan mengedit salah satunya."))

# ---------------------------------------------------------------- A4: komponen yang jadi
E.append(("01-Agent/A4 - Trust Gating and Real-Money Rules.md",
 "| `execution.py` — buka/tutup posisi nyata | **belum ada**; yang ada `tools/exec_deploy.py` = men-deploy saja (dan berhenti sendiri karena guard saldo) |",
 "| `execution.py` — buka/tutup posisi nyata | **ada: `tools/execute_live.py`** (27 Sep). Menolak membuka posisi kalau `decisionHash`-nya tidak ada di `DecisionAnchor`, dan menolak `ABSTAIN`. Dua round-trip nyata: −59 bps per putaran |"))

E.append(("01-Agent/A4 - Trust Gating and Real-Money Rules.md",
 "| `trust.py` — kelayakan real-trade (n≥20, net>0, drop-best-fold, BH) dan menampilkan **berapa lagi yang kurang** | **belum ada** — dan memang tidak ada gunanya sebelum P1 menghasilkan posisi nyata |",
 "| `trust.py` — kelayakan real-trade (n≥20, net>0, drop-best-fold, BH) dan menampilkan **berapa lagi yang kurang** | **belum ada.** P1 sudah jalan, jadi alasan \"nunggu posisi nyata\" sudah tidak berlaku: yang tersisa cuma keputusan apakah gerbangnya dipasang sebelum demo atau sesudahnya |"))

# ---------------------------------------------------------------- Claims cheat sheet: baris eksekusi
E.append(("10-Submissions/01 - Claims Cheat Sheet.md",
 "| \"sistem kami sudah diperdagangkan\" | \"jalur eksekusi ada, 18 test lulus, dan belum ada posisi nyata di 97 (butuh 1 top-up gas)\" | lihat [[08-Backlog/01 - Backlog]] P1 |",
 "| \"sistem kami sudah diperdagangkan\" | \"dua round-trip nyata dieksekusi on-chain di 97 lewat vault ber-cap, masing-masing −59 bps — di venue demo kami sendiri, bukan di pasar\" | `decisions/execution-trail.jsonl`, [[02-Contracts/C3 - ExecutionVault]] |\n| \"agent kami untung dari trading\" | \"yang untung di jalur ini baru biaya pool; posisi pertama kami rugi 59 bps dan itu angka yang diprediksi test suite\" | sama |"))

# ---------------------------------------------------------------- Cost Is Fixed: angka nyata
E.append(("Concepts/Cost Is Fixed.md",
 "| gas nyata `openLong`/`close` di 97 | *(belum diukur — P1 belum jalan)* | — |",
 "| gas nyata `openLong` di 97 | **258.008 / 295.443 gas** (±0,00003 tBNB @ 0,1 gwei) | `execute_live.py --open-long` |\n| gas nyata `close` di 97 | **123.216 / 150.576**; kontrak membukukan `gasUnitsPaid` 127.213 / 161.413 di event | `execute_live.py --close` |\n| realized round-trip nyata | **−59 bps** per putaran, pada posisi 1 unit | event `Closed` (bukan hitungan kami) |"))

NEW = []

NEW.append(("07-Testing/T6 - Clean Clone Evidence.md", """---
tags: [testing, "T6"]
---

# T6 - Clean Clone Evidence

**Bagian dari:** [[07-Testing/00 - Hub Testing]]
**Perintah:** `python -X utf8 _research/probe_clone_paths.py` *(workspace — dia yang meng-clone,
bukan bagian clone)*
**Dijalankan:** 27 Sep 2026 ±12:25 WIB terhadap HEAD `304fe4f` (clone lokal ke direktori kosong,
`PYTHONIOENCODING=utf-8`, env `ANCHOR_ADDRESS`/`AGENT_ADDRESS`/`AGENT_PRIVATE_KEY`/`RPC_URL` dibuang)

## Keluaran

```text
HEAD ter-track : 304fe4f
  ada di clone? deployments/97.json                        YA
  ada di clone? tools/execute_live.py                      YA
  ada di clone? decisions/execution-trail.jsonl            YA
### anchor --verify (0 kunci, 0 gas)  -> rc=0
### execute_live --status             -> rc=0
### verdict_counts (split dari chain) -> rc=0
### verify_vendor (manifest == disk)  -> rc=0

4/4 jalur pemeriksaan hidup dari clone bersih HEAD 304fe4f.
```

Sebelum perbaikannya, baris pertama berbunyi `rc=1` dengan
`AGENT_ADDRESS tidak diketahui -> tidak bisa menghitung ulang id anchor` — dan itu **membantah
kalimat yang kami jual sendiri**. Lihat [[00-Overview/05 - Corrections]].

## Yang dibuktikannya — dan yang tidak

- ✅ Empat jalur pemeriksaan (baca trail dari chain, status vault, split verdict, integritas vendor)
  hidup tanpa `.env`, tanpa `data/`, tanpa cache — jadi "verifiable tanpa kami" sekarang berlaku di
  jalur ini, bukan cuma di niat.
- ✅ Alamat agen tidak dipercaya begitu saja dari repo: `--verify` mencetak
  `roster : getAgent() -> handler 0x4bb3…69c862 aktif=True | countByAgent = 17`, dan angka itu
  dijawab **kontrak**. Berkas repo yang boleh dipakai harus bisa dibantah.
- ❌ **Bukan** `forge test` dari clone: itu butuh `git submodule update --init --recursive`
  (langkah 0 di [[00-Overview/04 - Run It]]) dan belum pernah diuji dalam bentuk clone.
- ❌ Bukan jalur yang menulis: mengirim anchor/posisi tetap butuh kunci agen, dan itu memang tidak
  seharusnya bisa dilakukan orang lain.
- ⚠️ Yang masih terbuka: P6b (`anchorCount()` 17 vs 11 baris terpelacak) dan P2 (endpoint publik).

## Kalau gagal

- `AGENT_ADDRESS tidak diketahui` lagi → `deployments/<chain>.json` hilang atau field `agent`-nya
  kosong; bangkitkan dengan `python -X utf8 tools/write_deployment_manifest.py` (ia mengecek
  bytecode tiap alamat ke chain, jadi tidak bisa salah ketik diam-diam).
- `roster : ... getAgent()` menampilkan handler yang bukan alamat agen → manifest ditukar/salah;
  berhenti, jangan lanjut membandingkan hash.
- `execute_live.py --status` minta `deploy.json` → fallback manifesto tidak ketemu; cek
  `contracts.ExecutionVault/DemoPair/DemoAsset/DemoPayToken` di `deployments/97.json`.

**Terkait:** [[07-Testing/01 - Test Commands]] · [[07-Testing/T2 - Anchor Verify]] ·
[[00-Overview/04 - Run It]] · [[08-Backlog/01 - Backlog]] P8
"""))

NEW.append(("09-Inbox/Session-2026-09-27-siang.md", """---
tags: [inbox, "S-27-b"]
---

# Session 27 Sep (siang) — P1 jalan, dan tes clone membantah satu klaim kami

**Bagian dari:** [[09-Inbox/00 - Hub Inbox]]
**Sumber:** keluaran perintah di bawah; yang bukan hasil run ditandai *(belum diukur)*.

## Yang terjadi, berurutan

1. Pertanyaan builder: *"top-up tBNB untuk agen untuk apa? di trade kah?"*. Jawabannya berubah jadi
   temuan: **tBNB cuma untuk gas** (posisi memakai token demo), dan guard `exec_deploy.py` menolak
   kemarin karena memakai **plafon 1 gwei** sementara testnet live **0,10 gwei**. Jalur penuh
   = 0,0018 tBNB vs saldo 0,007884 -> **dananya cukup**; yang menahan adalah taksiran konservatif.
2. Builder memilih sumber dana: pakai tBNB deployer di `app/.env`. Tower
   `0xAEc63F6c…c8361` (0,214667 tBNB) mengirim 0,03 -> agen **0,037884**
   (tx `0x37489064…`, `status=1`, blok 133.419.795, receipt dibaca ulang).
3. **P1 selesai.** Deploy `DemoAsset`/`DemoPair`/`ExecutionVault` + 7 tx seeding/config, lalu
   `tools/execute_live.py` (berkas yang sebelumnya *disuruh* dijalankan oleh `exec_deploy.py`
   padahal tidak pernah ada): dua round-trip nyata di bawah anchor `0x0f5ff29e327902eb…` —
   realized **−59 bps** per putaran, sama dengan prediksi test suite. Guard-nya terbukti sendiri:
   `--open-long BREWUSDT` **ditolak** karena keputusan itu `ABSTAIN`.
4. Probe clone (`_research/probe_clone_paths.py`) memulainya 3/4: `anchor.py --verify` **gagal**
   karena `AGENT_ADDRESS` cuma ada di `.agent.env` yang di-gitignore. Jadi kalimat "nol kunci,
   siapa pun bisa periksa" selama ini sebenarnya berarti "punya salinan kerja kami".
   Perbaikan: `deployments/97.json` (ter-track, 8 alamat, bytecode dicek ke chain) + roster
   dicetak dari `getAgent()`/`countByAgent()`. Hasil: **4/4**.
5. Satu hipotesis kuukur dan gugur sendiri: mengira selisih 17 vs 11 itu karena cakupan verifier
   sempit. Perluasan malah menyeret 301 baris kandidat `screen` -> "11/312 cocok". Cakupan
   dikembalikan, dan `--verify` sekarang **mencetak peringatan** kalau `anchorCount()` != jumlah
   baris terpelacak. P6b tetap terbuka.

## Angka baru yang resmi tinggal di halaman ini

| hal | nilai | halaman pemilik |
|---|---|---|
| agen 0x4bb3…69c862 | 0,034220 tBNB setelah 4 tx eksekusi | [[Quick-Reference]] |
| posisi nyata | 2 round-trip, −59 bps tiap putaran | [[02-Contracts/C3 - ExecutionVault]] |
| gas nyata | open 258.008/295.443 · close 123.216/150.576 | [[Concepts/Cost Is Fixed]] |
| jalur pemeriksaan dari clone | 4/4 hidup pada HEAD `304fe4f` | [[07-Testing/T6 - Clean Clone Evidence]] |

## Yang belum diukur *(jangan dikutip sebagai angka)*

- slippage pasar sungguhan — venue kita tetap pool x·y=k milik sendiri
- apakah agen **asing** mau membayar — endpoint masih lokal (P2)
- win-rate dengan `n ≥ 20` — yang dinilai masih 2 posisi

**Terkait:** [[09-Inbox/Session-2026-09-26-27]] · [[08-Backlog/01 - Backlog]] · [[START-HERE]]
"""))

bad = []
for rel, old, new in E:
    p = os.path.join(VAULT, rel.replace("/", os.sep))
    if not os.path.isfile(p):
        bad.append(f"TIDAK ADA {rel}")
        continue
    t = io.open(p, encoding="utf-8").read()
    c = t.count(old)
    if c != 1:
        bad.append(f"{rel}: {c}x untuk {old[:56]!r}")
        continue
    io.open(p, "w", encoding="utf-8", newline="\n").write(t.replace(old, new, 1))
    print("ok  ", rel)

for rel, text in NEW:
    p = os.path.join(VAULT, rel.replace("/", os.sep))
    if os.path.exists(p):
        print("lewat", rel, "(sudah ada)")
        continue
    io.open(p, "w", encoding="utf-8", newline="\n").write(text)
    print("tulis", rel)

if bad:
    print("\n".join("!! " + b for b in bad))
    sys.exit(f"\n{len(bad)} dari {len(E)} perbaikan TIDAK diterapkan.")
print(f"\n{len(E)} suntingan + {len(NEW)} halaman baru.")
