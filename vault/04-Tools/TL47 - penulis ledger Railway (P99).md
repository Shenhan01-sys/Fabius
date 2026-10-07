---
tags: [perkakas, "TL47", ledger, railway, penulis, rest]
---

# TL47 - penulis ledger Railway: pengganti rantai `paper-ledger` GitHub (P99 tahap 2 + P100 tahap 3)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/penulis_ledger.py` (`Penulis.putaran`, `blok_tick`, `blok_jaga`, `blok_eksekusi`, `dorong`, `komit`, `syarat`, `isi_rest`, `cek_vision`,
`bandingkan`; `Kunci.ambil` / `lepas`; `syarat_rantai_github`; `git_env` / `saring`; `bandingkan_ledger` / `bandingkan_bars` / `bandingkan_ref`; CLI `siapa` /
`syarat` / `bandingkan` / `jalan`) · sakelar `config/penulis-ledger.json` · penjaga di `.github/workflows/paper-ledger.yml` + `paper-ledger-watchdog.yml`
· `FABIUS_FUNDING_REST` di `tools/feed_bars.py::update_funding` · `tools/shadow_tick.py::append_rows` / `needs_rest` (P100) · tes
`engine/tests/test_penulis_ledger.py` (23) · T8 SK-R3 + SK-RW1..SK-RW10 (**USULAN** nomor) · keputusan [[00-Overview/03 - Decisions]] F-D78 / F-D83 / F-D86 ·
backlog P99, P100 · bukti angka sebelumnya: [[04-Tools/TL17 - shadow_tick]] (5/5 hari IDENTIK)

## Apa

Satu job Railway yang menjalankan **isi loop rantai GitHub `paper-ledger` apa adanya**, urutan dan gerbangnya sama, lalu commit + push ke GitHub dengan token
dari variabel Railway. Tahap 2 (P99): sumber bar tetap zip Vision, jadi isi ledger sama persis dengan rantai GitHub; yang pindah hanya PENULIS-nya
(cron GitHub yang bolong + runner yang diblokir Binance, F-D78 / F-D94). Tahap 3 (P100): `PENULIS_SUMBER=rest` menambahkan baris bar hari itu dari REST
mulai +2 menit sesudah penutupan, sehingga tick keluar ±5 menit sesudah 00:00Z alih-alih ±9-10 jam.

Alat rantai dijalankan dari **klon repo** (sparse: `engine tools ledger config deployments`), bukan dari image: versi kodenya = HEAD cabang, sama dengan
rantai GitHub yang men-checkout repo. Image hanya membawa `penulis_ledger.py` + modul yang ia impor (`shadow_tick`, `feed_bars`, `alert`, `rest_vs_vision`).

## Satu putaran (tiap 5 menit) = satu iterasi loop rantai

1. fetch + rebase klon ke ujung cabang (gagal = BERHENTI); periksa syarat penulis (di bawah); tidak terpenuhi = **tidak ada alat yang dijalankan**.
2. di jendela tick (vision 08:40-11:58Z, rest 00:02-11:58Z) sampai tick hari itu beres: [rest: baris REST] -> `paper_tick.py --feed` (rc 0 beres / 4 coba
   lagi / lain = BERHENTI) -> `engine.cli ledger verify` (gagal = BERHENTI, tidak commit) -> `feed_tick.py` (peringatan saja) -> commit
   `ledger/paper ledger/bars [ledger/feed]` "ledger paper <UTC> [skip ci]" -> dorong. Sesudah rc 0: `book epoch --write` + `book verify` -> commit
   `ledger/book`; `kertas_eksekusi.py run` -> commit `ledger/kertas` (gagal = peringatan, dibuang, dicoba besok).
3. sesudah tick beres: `worker_watch.py --alert --ringkasan` sampai menilai (rc 0/1), lalu picu `web-snapshot.yml`, `validasi.yml`, `bot-review.yml` lewat API.
4. tiap putaran: `eksekusi_ledger.py run --alert --state` -> `verify` -> commit `ledger/eksekusi`; `periksa --alert`; `waitlist.py --poll`.

**Dorong** = perpanjang sewa kunci -> fetch + rebase -> `ledger verify` LAGI bila hulu bergerak -> push; ditolak = jeda 12 s, 5 kali (sama dengan rantai).
**BERHENTI** = di rantai GitHub `exit 1` lalu watchdog menyalakan mata rantai baru <= 20 menit kemudian; di sini: klon direset ke ujung cabang, Telegram,
jeda 20 menit, lalu jalan lagi. Semua alat mendapat `FABIUS_FUNDING_REST=0` (SK-R2: di Railway REST funding terbuka, di runner GitHub 451).

## Mode (`PENULIS_MODE`)

| mode | menulis ke | syarat | yang tidak dilakukan |
|---|---|---|---|
| `mati` (bawaan) | - | - | apa pun (klon pun tidak) |
| `bayangan-tulis` | cabang `PENULIS_CABANG_UJI` (bawaan `penulis-uji`), **tidak pernah** master (konstruktor menolak) | sewa `refs/penulis/kunci-penulis-uji` | Telegram dari alat, daftar tunggu (`getUpdates` akan mencuri update rantai resmi), penjaga worker, pemicu workflow |
| `master` | `master` | (1) `config/penulis-ledger.json` di ujung master: `"penulis": "railway"`; (2) workflow `paper-ledger.yml` berstatus `disabled_*` DAN tidak ada run-nya yang `in_progress/queued/waiting/pending/requested` (API GitHub; tak terbaca = tidak menulis); (3) sewa `refs/penulis/kunci-master` dipegang proses ini | - |

**Bayangan-tulis** tiap putaran membandingkan catatan yang DITULIS cabang uji (hash tidak ada di master; warisan bersama bukan bukti) dengan catatan
resmi asof yang sama: tick -> `IDENTIK` / `BEDA (<kolom>)` (kolom `targets, data_hash, signal_ids, n_aset`, sama dengan [[04-Tools/TL17 - shadow_tick]]) /
`MENUNGGU` / `RESMI GAP` / `RESMI ADA, UJI BELUM MENULIS`; baris bar sesudah titik cabang -> `N sama persis, M beda`. Vonis tick dan ALARM bar dikirim
Telegram sekali. Perintah lokal yang sama, dihitung ulang dari git (bukan dari log):
`git fetch origin penulis-uji && python -X utf8 tools/penulis_ledger.py bandingkan` (keluar 1 bila ada BEDA).

## Penulis tunggal (SK-R3) + kunci

- **Sakelar publik** `config/penulis-ledger.json`: `github` (yang dikomit; berkas hilang / rusak juga dibaca `github` oleh workflow) atau `railway`.
  Workflow membacanya di awal job dan di awal **setiap putaran dari ujung cabang** (`git fetch` + `penulis_ledger.py siapa --ref FETCH_HEAD`);
  `railway` = mata rantai keluar tanpa menulis dan tanpa "Sambung rantai"; watchdog tidak men-dispatch. Railway justru gagal-tertutup: config tak
  terbaca = tidak menulis. Riwayat berkas = riwayat publik kapan penulis pindah.
- **Kunci sewa** = ref `refs/penulis/kunci-<cabang>` berisi satu commit yatim `kunci.json` (pemegang, mode, sampai). Diambil / diperpanjang dengan
  `git push --force-with-lease=<ref>:<sha yang dibaca>` - bandingkan-dan-tukar di server git, jadi dua proses (deploy tumpang-tindih, replika kedua,
  jalan lokal) tidak bisa sama-sama memegangnya. Sewa 20 menit, diperpanjang tiap putaran DAN sebelum tiap push (direbut di tengah putaran = push
  dibatalkan), dilepas saat SIGTERM. Pemegang = `<service>:<deployment>:<replika>` Railway. Ref di luar `refs/heads`: bukan cabang, jadi tidak
  memicu workflow `push` atau pratinjau Vercel. Awalan bisa diganti `PENULIS_KUNCI_PREFIX`.
- **Token** `PENULIS_GITHUB_TOKEN`: git menerimanya hanya sebagai `http.https://github.com/.extraheader` lewat `GIT_CONFIG_COUNT/KEY_0/VALUE_0`
  (cara `actions/checkout`), tidak pernah di argumen (terlihat di `ps`), URL remote, atau log (keluaran git + alat disaring: token dan bentuk base64-nya
  -> `<rahasia>`). Alat anak tidak mewarisinya (`eksekusi_ledger` membaca Gist lewat URL raw publik tanpa token).

## P100: tick dari REST (`PENULIS_SUMBER=rest`)

Di awal putaran (paling cepat +2 menit sesudah penutupan) bila bar resmi belum sampai hari itu (`shadow_tick.needs_rest`, tanpa jaringan): bacaan REST
sampai dua bacaan berurutan berjarak >= 60 s IDENTIK (SK-R1, `read_final`), baris dibangun dengan aturan `feed_bars` (`build_rows`: kline perp/spot
16 aset universe + estimasi funding dari menit indeks premium), ditambahkan DI TEMPAT ke `ledger/bars` klon (`append_rows`; funding aktual tidak pernah,
SK-R2), lalu rantai biasa (`paper_tick --feed` tidak menemukan apa pun lagi untuk deret itu). Baris yang hilang / tidak sah di jam pertama = TUNDA, sesudahnya
diteruskan dan `make_tick` yang memutuskan. REST gagal dibaca = peringatan, rantai jalan dengan Vision.
**Pemeriksa Vision** (setara SK-R4): baris REST yang ditulis disimpan di `/tmp/fabius-penulis/rest-baris/<tgl>.json`; >= 8 jam sesudah penutupan (tiap
30 menit) salinan bar dengan baris itu dicabut diisi ulang dari zip Vision oleh `feed_bars` dan dibandingkan (`compare_rows`) -> `VONIS baris REST vs
Vision <tgl>: N sama persis ...` atau `ALARM` + Telegram. Tidak ada yang ditimpa (append-only; manusia memutuskan). Vision tak terbit 2 hari = TIDAK TERUJI.

## Cara memakai

```
# Railway (service SENDIRI, satu replika, southeast-asia):
FABIUS_JOB=penulis_ledger  PENULIS_MODE=bayangan-tulis|master  PENULIS_SUMBER=vision|rest  PENULIS_GITHUB_TOKEN=<rahasia>
[ALERT_TELEGRAM_TOKEN / ALERT_TELEGRAM_CHAT]  [PENULIS_CABANG_UJI=penulis-uji]  [PENULIS_WORKDIR=/tmp/fabius-penulis]
# lokal, hanya baca:
python -X utf8 tools/penulis_ledger.py siapa [--ref FETCH_HEAD]        # github | railway (yang dipakai workflow)
python -X utf8 tools/penulis_ledger.py syarat                          # 1. config 2. rantai GitHub 3. kunci (API tanpa token bisa 403 = TIDAK)
python -X utf8 tools/penulis_ledger.py bandingkan [--resmi origin/master] [--uji origin/penulis-uji]
```
Log yang dicari: `boleh menulis: kunci refs/penulis/kunci-master diambil`, `=== putaran`, `paper_tick rc=`, `push OK (percobaan 1)`, `VONIS penulis-uji`,
`VONIS baris REST vs Vision`, `TIDAK MENULIS:`, `GALAT:`.

## Runbook alih (urutan WAJIB, SK-R3) - langkah builder

**0. Siapkan (penulis belum pindah; tidak mengubah apa pun yang hidup):**
1. kata builder -> sesi utama menggabung `kerja-p99` ke master + gerbang prepush + push. Config berkata `github`, jadi rantai GitHub tidak berubah. Bukti:
   log run `paper-ledger` berikutnya mencetak `penulis ledger menurut config/penulis-ledger.json: [github]`.
2. buat **fine-grained PAT** (Settings -> Developer settings -> Fine-grained tokens): pemilik `Shenhan01-sys`, hanya repo `Fabius`, izin **Contents:
   Read and write** + **Actions: Read and write** (Metadata read otomatis), kedaluwarsa **USULAN** 90 hari. Periksa master tidak punya aturan cabang yang
   hanya mengizinkan GitHub Actions mendorong.
3. Railway, service baru **`fabius-penulis` (USULAN nama)** di proyek yang sama: variabel `RAILWAY_DOCKERFILE_PATH=railway/Dockerfile`,
   `FABIUS_JOB=penulis_ledger`, `PENULIS_MODE=bayangan-tulis`, `PENULIS_SUMBER=vision`, `PENULIS_GITHUB_TOKEN` (**ketik di dashboard**, jangan lewat sesi),
   opsional `ALERT_TELEGRAM_TOKEN/CHAT` (sama dengan `fabius-engine`); `railway service scale --service fabius-penulis southeast-asia=1 sfo=0`; deploy
   `python -X utf8 tools/railway_up.py --service fabius-penulis`.
4. **uji paralel >= 1 hari penuh (USULAN 2 hari)**: `railway logs --service fabius-penulis --lines 200` -> `VONIS penulis-uji <bot> <tgl>: IDENTIK` untuk
   semua bot + `VONIS baris bar penulis-uji: N sama persis, 0 beda`; lokal `git fetch origin penulis-uji && python -X utf8 tools/penulis_ledger.py
   bandingkan` keluar 0. Opsional hari berikutnya `PENULIS_SUMBER=rest` di uji (tick uji ±00:05Z vs resmi ±09:40Z).

**1. Alih** (sesudah tick hari itu beres, **USULAN** 12:30-23:30Z):
1. sesi utama mengomit `config/penulis-ledger.json` -> `"penulis": "railway"` + push (kata builder). Mata rantai GitHub yang hidup berhenti di awal
   putaran berikutnya (<= 5 menit) tanpa menulis dan tanpa menyambung; watchdog tidak men-dispatch.
2. `gh workflow disable paper-ledger.yml` lalu `gh workflow disable paper-ledger-watchdog.yml`.
3. `gh run list --workflow paper-ledger.yml --limit 3` -> tidak ada yang `in_progress` / `queued`.
4. `railway variable set PENULIS_MODE=master --service fabius-penulis` (redeploy; `PENULIS_SUMBER=vision` = tahap 2).
5. bukti: log `boleh menulis: kunci refs/penulis/kunci-master diambil`; di jendela berikutnya commit `ledger paper ... [skip ci]` oleh
   `paper-ledger-railway` di master; lokal `git pull` + `python -X utf8 -m engine.cli ledger verify` = SAH; `worker_watch` / web-snapshot / validasi /
   bot-review terpicu seperti biasa.
6. tahap 3 (P100) = `PENULIS_SUMBER=rest` sesudah tahap 2 bersih **USULAN** >= 3 hari.

**2. Balik** (kapan pun):
1. `railway variable set PENULIS_MODE=mati --service fabius-penulis` (proses melepas kunci saat SIGTERM).
2. sesi utama mengomit config -> `"penulis": "github"` + push.
3. `gh workflow enable paper-ledger.yml` + `gh workflow enable paper-ledger-watchdog.yml`, lalu `gh workflow run paper-ledger.yml` (atau tunggu
   watchdog <= 20 menit). Bukti: log run `[github]` dan loop berjalan.
Urutan terbalik pun tidak menghasilkan dua penulis: begitu workflow aktif lagi Railway menolak (syarat 2) dan selama config berkata `railway` rantai GitHub
keluar - paling buruk TIDAK ADA penulis beberapa menit (lewat 12 jam = gap, SK-L5).

## Yang BELUM / tidak dibuktikan

- **Belum pernah jalan di Railway dan belum pernah mendorong ke GitHub**: semua bukti dari repo git bare LOKAL. Belum terbukti: push dengan PAT lewat
  `http.extraheader`, push ref di luar `refs/heads` (`refs/penulis/*`) diterima GitHub (bila ditolak: `PENULIS_KUNCI_PREFIX=refs/heads/penulis-kunci-`,
  ref jadi cabang -> bisa memicu pratinjau Vercel), dan bentuk jawaban API status workflow/run (diuji dengan API tiruan; `syarat` dari laptop builder tanpa
  token mendapat HTTP 403 -> tercetak "tidak menulis (gagal = tertutup)").
- Uji ujung-ke-ujung memakai `paper_tick` TIRUAN (tanpa jaringan); gerbang `engine.cli ledger verify` ASLI dijalankan pada ledger repo ASLI: blob
  `B1-TREND.jsonl` yang di-push = blob yang dikomit rantai GitHub, satu angka diubah = ditolak. Kesamaan tick REST vs Vision dibuktikan TL17 (5/5 hari),
  bukan oleh alat ini.
- Penjaga workflow diuji sebagai teks + perintah `siapa`; belum dieksekusi di runner. Bukti pertama = log run sesudah push (`[github]`).
- REST hanya untuk 16 aset universe (sama dengan bayangan); deret lain (koin listing B4, emas B5) tetap menunggu Vision, jadi `paper_tick` rc 4 sampai
  ±09:40Z dan `kertas_eksekusi` (sesudah rc 0) tetap di jam Vision.
- Keadaan pemeriksa Vision ada di `/tmp`: hilang saat redeploy (hari yang tertunda tidak diperiksa) - **USULAN**: volume Railway atau commit ke `ledger/`.
- Cap waktu commit berasal dari jam Railway, bukan jam runner GitHub; bukti "sinyal ada sebelum hasil" tetap komit SignalAnchor (jam chain).
- Cabang uji adalah cabang sungguhan: Vercel mungkin membangun pratinjau tiap push (commit `[skip ci]` melewati workflow push GitHub).
- Durasi file tes ±80 s di Windows (git + proses alat sungguhan per putaran).

## USULAN (belum disetujui builder)

nama service `fabius-penulis`; cabang uji `penulis-uji`; ref kunci `refs/penulis/kunci-<cabang>`, sewa 20 menit; jeda BERHENTI 20 menit; identitas commit
`paper-ledger-railway <paper-ledger-railway@users.noreply.github.com>` (bisa diganti `PENULIS_GIT_NAME/EMAIL`); berkas sakelar `config/penulis-ledger.json`;
uji paralel >= 1 hari (saran 2); tahap 3 sesudah >= 3 hari tahap 2 bersih; izin + kedaluwarsa PAT; jam alih 12:30-23:30Z; nomor T8 SK-RW1..SK-RW10.

**Terkait:** [[04-Tools/TL17 - shadow_tick]] · [[04-Tools/TL13 - rest_vs_vision]] · [[04-Tools/TL9 - ledger paper maju]] ·
[[07-Testing/T8 - Semantik Kegagalan Operator]] · [[00-Overview/03 - Decisions]] F-D78 / F-D86 · [[08-Backlog/13 - Langkah Builder Tertunda]]
