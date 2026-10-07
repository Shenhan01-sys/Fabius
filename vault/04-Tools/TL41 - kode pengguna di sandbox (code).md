---
title: TL41 - kode pengguna di sandbox (code)
tags: [tools, P167, code, sandbox, pengajuan]
---

# TL41 - kode pengguna di sandbox `kind=code` (P167b, epik 12)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]

**Status (7 Okt 2026):** DIBANGUN di lokal, BELUM di-push / deploy, dan **TERTUTUP untuk pengguna luar** (`submission.ENABLED_KINDS` tidak memuat `code`) sampai builder menyetujui jalur privat di bawah (penyimpanan privat gerbang + pelari terpisah) atau repo menjadi privat. Keputusan: [[08-Backlog/12 - Epik Pengajuan Terbuka dan Peninjau LLM]] §3.2 (F-D125: kode PRIVAT). Bukti: epik 12 §11. Semantik kegagalan: [[07-Testing/T8 - Semantik Kegagalan Operator]] SK-J14..SK-J22. Label kepercayaan di laporan + web: **"kode privat, tidak bisa diulang publik"**.

## Kontrak penerbit

```python
PARAMS = {"N": 60}                 # angka BERNAMA yang digeser G5 (<= 6, bukan nol; bulat tetap bulat)

def target(bars, params):          # dipanggil SEKALI per bar harian i
    c = bars["BTCUSDT"]["c"]       # bars = {simbol: {"t","o","h","l","c","v": tuple sampai bar i}} - tidak pernah memuat bar sesudah i
    n = params["N"]
    return {"BTCUSDT": 1.0} if len(c) > n and c[-1] > c[-1 - n] else {}   # {simbol: bobot}, gross <= 1
```

Bobot berlaku untuk return bar i+1 (konvensi mesin, sama dengan `rule`); biaya + funding = penggaris standar milik kami (`kode.PENGGARIS`, sama dengan rule / B1 / B2). Formulir publik hanya memuat `spec.kode` = `{sha, ukuran, params}`; teks kode dikirim terpisah (`body.code`).

## Lapis pagar

| Lapis | Di mana | Apa |
|---|---|---|
| 1 statis | `engine/kode.py::periksa` | AST DAFTAR-IZIN: def, aritmetika, perbandingan, if / for / while, comprehension, lambda; impor hanya `math` + `statistics` (anggota terdaftar, tanpa `statistics.sys` / `NormalDist`); nama berawalan `_` ditolak (dunder); atribut hanya dari daftar-izin (tanpa `format`, `gi_frame`, `f_globals`); tanpa try / with / class / global / nonlocal / yield / f-string / walrus / dekorator / anotasi; tanpa `eval open exec compile getattr vars type print id hash`; tingkat modul hanya docstring, impor, konstanta literal, def; teks <= 64 karakter (docstring <= 2000); <= 4000 simpul; <= 16 KB. Tidak pernah melempar; pesan tanpa teks kode |
| 2 anggaran langkah | `engine/kode.py::instrumentasi` | `_l()` disisipkan di tiap badan fungsi, perulangan, comprehension, lambda: 200 000 langkah per panggilan `target` (nama `_l` tidak bisa dibayangi: awalan `_` ditolak) |
| 3 proses anak | `engine/kode_anak.py` | `python -s -S -P`, lingkungan kosong kecuali `PYTHONHASHSEED`, cwd folder sementara kosong, tanpa jalur repo; memasang batas PADA DIRINYA sebelum membaca kode - Linux / Railway: RLIMIT_CPU 120 s, RLIMIT_AS 768 MB, RLIMIT_FSIZE 0, RLIMIT_NOFILE 16, RLIMIT_CORE 0; Windows (mesin builder, F-D127): Job Object tanpa nama - waktu CPU per proses 120 s, memori ter-commit 768 MB, maksimal 1 proses, mati tanpa dialog, UI terkunci, pegangan ditutup sesudah memasang; gagal memasang = gagal tertutup; induk membaca sebab berhenti per platform (`kode.sebab_keluar`: sinyal POSIX / NTSTATUS Windows); builtins daftar-izin; impor lewat proksi berisi anggota yang diizinkan; rekursi <= 200; induk menegakkan waktu dinding 180 s; keluaran <= 48 MB |
| 4 dua jalan | `engine/kode.py::jalankan` | dua proses dengan PYTHONHASHSEED 1 dan 2; keluaran harus identik (`deterministik`); tiap keluaran diperiksa: dict, kunci = aset yang punya bar sampai hari itu, bobot terhingga, gross <= 1 |
| 5 kausalitas | `kode_anak.py` + `engine/kode.py::uji_kausal` | kausal oleh konstruksi (data dipotong <= i, pemetaan + tuple tak bisa diubah); sampel bar (seperti G1: seed, dari hari ke-60, + hari terakhir) dihitung ulang di namespace SEGAR - menangkap keadaan global / argumen bawaan yang bisa diubah |
| 6 privat | `tools/pengajuan.py`, `tools/pelari_kode.py`, `railway/pelari/Dockerfile`, `engine/kode.py::PelariData` | lihat di bawah |

## Jalur privat (rancangan dibangun; MENUNGGU persetujuan builder + deploy)

1. Penerbit: `POST /bots/typed-data` lalu `POST /bots/submit` {submission (`spec.kode` = sha + ukuran + PARAMS, ditandatangani EIP-712), signature, nonce, deadline, `code`}. Gerbang: validasi formulir + `kode.cocok_meta` (sha, ukuran, PARAMS, analisis statis) + identitas; teks disimpan PRIVAT `pengajuan/kode/<sha>.py` lewat `engine/berkas_privat.py` (Linux 0600; Windows DACL terlindung satu ACE akun gerbang, folder ikut dikunci; volume gerbang); antrean publik dan repo hanya memuat formulir (sha + ukuran + PARAMS).
2. Pelari (`tools/pelari_kode.py`, layanan Railway SENDIRI, image minimal stdlib + 4 berkas, pengguna non-root, tanpa domain publik, MENOLAK mulai bila lingkungannya memuat nama seperti rahasia): `POST /run` {kode, bar publik, varian (`kode.varian_semua`), sampel} -> DATA berbatas (bobot per bar per varian + hasil uji kausalitas + determinisme). Tidak menyimpan kode, tidak menulis berkas.
3. Pihak tepercaya: `kode.PelariData` memvalidasi DATA lagi (sha data, grid, aset, gross, varian lengkap, uji ada) lalu `review()` menjalankan G1-G11 + KPI pada DATA itu tanpa pernah memegang teks kode. Data terpotong / varian lain = galat (gagal tertutup).

## Integrasi gerbang

- `REGISTRY["CODE"] = kode.targets` (pelari aktif: `PelariLokal` di pemegang kode / tes, `PelariData` di pihak tepercaya).
- G1 = `kode.uji_kausal` (sampel identik + deterministik); G5 = `gates._g5_kode` atas PARAMS bernama (SATU per SATU + semua bersama; parameter dekoratif atau tanpa PARAMS = GAGAL); G8 = placebo waktu bawaan (tidak ada `NULL_KIND` untuk CODE); `n_trials` += varian G5 (`varian_g5` di laporan, seperti rule).
- Laporan: `label_kepercayaan`, `kode` = {sha, ukuran} (tanpa teks); `render` mencetak `(code)` + label.
- Web `/submit`: ubin Code tampil "segera" (nonaktif) dari `kinds_open`; editor (`web/src/components/submit/KindPanels.tsx::CodeEditor`, `web/src/lib/kode.ts`) dibangkitkan dari `GET /bots/schema` -> `code` (kontrak, batas, contoh, label, catatan "kode dikirim ke penyedia model peninjau"), menghitung sha + ukuran + PARAMS yang SAMA dengan gerbang (tes kontrak Node).

## Yang BELUM / tidak dibuktikan

- Jenis tertutup; layanan Railway pelari belum ada; volume privat + panggilan gerbang -> pelari belum hidup (deploy dan persetujuan = langkah builder).
- Orkestrasi tinjauan harian `code` (gerbang memanggil pelari, menyimpan DATA, tinjauan tepercaya memakai `PelariData`) BELUM disambung ke rantai harian; `review` atas `PelariData` hanya terbukti di tes.
- Jam maju harian bot code (tick tiap hari lewat pelari) BELUM dibangun.
- "Tanpa jaringan" = di tingkat bahasa (tanpa impor / builtins jaringan, proksi modul) + pelari tanpa rahasia; namespace jaringan OS (`unshare`) TIDAK dipakai (butuh hak istimewa). RLIMIT_NPROC tidak dipasang di Linux (fork tidak terjangkau dari bahasa yang diizinkan); di Windows Job Object membatasi 1 proses. Windows tidak punya padanan RLIMIT_FSIZE / NOFILE di Job Object: tertutup di tingkat bahasa (tanpa `open`, analisis statis menolaknya).
- Peninjau LLM (P168) belum disambung untuk `code`; laporan publiknya tidak boleh mengutip kode (epik 12 §3.2 (d)).
- Bukan klaim bahwa kode penerbit menghasilkan untung: B1 sebagai kode di `ledger/bars` divonis TOLAK (G8, G10) - itu yang diharapkan dari duplikat petahana.

## Cara memakai

- Tes: `python -X utf8 -m unittest engine.tests.test_kode engine.tests.test_berkas_privat` (kontrak web butuh Node >= 22.6) - jalan penuh di Windows (Job Object) dan Linux (setrlimit; di mesin builder lewat WSL Ubuntu).
- Bukti di data nyata: `python -X utf8 tools/kode_ekuivalensi.py [--gerbang]`.
- Mutasi (cacat disuntik ke jalur code + feed, tes harus gagal): `python -X utf8 tools/mutasi_kode_feed.py` (menulis berkas sumber sementara; jalankan dengan pohon kerja bersih; mutasi bertanda `nt` / `posix` hanya disuntik di platformnya).
- Pelari lokal: `python -X utf8 tools/pelari_kode.py --host 127.0.0.1 --port 8090` (menolak mulai bila ada variabel bernama seperti rahasia).

**Terkait:** [[00-Overview/03 - Decisions]] F-D122 · F-D125 · F-D127 · [[04-Tools/TL37 - jalur pengajuan bot]] · [[04-Tools/TL39 - aturan deklaratif (rule)]] · [[04-Tools/TL42 - komit maju penerbit (feed)]]
