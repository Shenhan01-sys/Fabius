---
tags: [perkakas, "TL8"]
---

# TL8 - engine

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `engine/` (paket stdlib), `python -X utf8 -m engine.cli specs|replay|emit|verify|gate|schema|intake|review|lock|book|gaps|ledger`; tes `engine/tests/`

**Ringkas:** mesin bot operator (M1): enam bot = satu metode + satu parameter, spesifikasi ber-sha, sinyal = niat posisi (`engine/sinyal.py`), keccak256 + Merkle murni Python (`engine/chain.py`), gerbang G1-G11 + KPI K1-K5, peninjau-bot deterministik, kunci ambang, ledger paper maju.

**Poin kunci:**
- Hanya stdlib; tidak menyentuh jaringan, kunci, atau chain - semua bagian jaringan ada di `tools/`.
- `hashlib.sha3_256` BUKAN keccak; `engine/chain.py` mengimplementasikan keccak256 sendiri dan diuji terhadap kontrak lewat vektor lintas bahasa.
- Guard umur bar (`engine/freshness.py`): data basi = `StaleBars`, bukan sinyal.
- `python -X utf8 -m unittest discover -s engine/tests -t .` = 272 lulus (2 Okt malam) → 292 sesudah P88.
- `engine/fd16.py` (P88): F-D16 pada data MAJU - `python -X utf8 -m engine.cli ledger fd16` menilai hanya ledger yang SAH (rantai + hitung ulang dari bar); parameter DIKUNCI (F-D84, `engine/locks/fd16.lock.json`; kode yang bergeser dicetak MENYIMPANG) - rincian di [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] §11.
- `engine/forward.py` (P85): skor maju 90 hari kalender + statistik berpasangan (hari yang sama) dari settle final - bahan `slots.decide`; `python -X utf8 -m engine.cli ledger skor` (hanya ledger SAH; hari tanpa settle = tak terukur, bukan nol).
- `engine/book_live.py` (P87, F-D85): buku slot hidup - `python -X utf8 -m engine.cli book epoch [--write]` (gerbang penantang terhadap buku sekarang, keputusan `slots.decide_epoch`) dan `book verify` (keputusan dihitung ulang dari masukan yang tercatat).

**Yang ia TOLAK lakukan:** mengintip bar besok (ada tes yang menangkapnya); mengubah `data_hash` tick lama ketika data jenis lain datang belakangan (`ledger.target_view`).

**Detail:** keputusan dan koreksinya: F-D70..F-D77 dan koreksi K1-K3 di [[08-Backlog/05 - Epik Enam Bot]].

**Terkait:** [[08-Backlog/05 - Epik Enam Bot]] §14 · [[TL9 - ledger paper maju]] · [[TL10 - kunci dan anchor kunci]]
