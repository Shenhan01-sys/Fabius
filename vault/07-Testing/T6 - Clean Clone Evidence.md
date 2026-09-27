---
tags: [testing, "T6"]
---

# T6 - Clean Clone Evidence

**Bagian dari:** [[07-Testing/00 - Hub Testing]]
**Perintah:** `python -X utf8 _research/probe_clone_paths.py` *(workspace — dia yang meng-clone,
bukan bagian clone)*
**Dijalankan:** 27 Sep 2026 ±13:45 WIB terhadap HEAD `f12b781` (clone lokal ke direktori kosong,
`PYTHONIOENCODING=utf-8`, env `ANCHOR_ADDRESS`/`AGENT_ADDRESS`/`AGENT_PRIVATE_KEY`/`RPC_URL`
dibuang). Commit itu hasil **penulisan ulang berkah**: `5e4468f` → `1f0faec` karena pesan aslinya
membawa trailer atribusi AI yang dicabut hari yang sama, dan dua turunannya ikut berganti hash —
lihat F-D22 di [[00-Overview/03 - Decisions]] dan gerbangnya di [[07-Testing/T7 - Pre-Push Gate]].

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
