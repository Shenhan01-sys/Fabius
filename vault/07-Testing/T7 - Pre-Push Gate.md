---
tags: [testing, "T7"]
---

# T7 - Pre-Push Gate

**Bagian dari:** [[07-Testing/00 - Hub Testing]]
**Perintah:** `python -X utf8 vault/scripts/prepush_check.py` (dan `--self-test`, `--all`, `--range A..B`)
**Dijalankan:** 27 Sep 2026 ±14:30 WIB (= 27 Sep 07:30Z) — self-test 6/6; `origin/master..HEAD` = 0
commit (lolos); `--all` = 1 pelanggaran dari 393 commit
**Aturan yang dijaganya:** F-D22 di [[00-Overview/03 - Decisions]] — tidak ada trailer atribusi AI di
pesan commit, dan **setiap push didahului kabar ke builder**.

**Ringkas:** aturan atribusi kami pernah dilanggar bukan karena tidak ada yang tahu, tapi karena
tidak ada yang *enegakkan*. Ini gerbangnya: baca pesan commit pada rentang yang akan dikirim, cari
polanya (`co-authored-by` / `signed-off-by` / `generated-with` + nama model, atau alamat
`noreply@…anthropic/openai`), keluar **non-zero** kalau kena.

## Keluaran

```text
$ python -X utf8 vault/scripts/prepush_check.py --self-test
  ok    bersih: terdeteksi=0 harus=tidak
  ok    trailer claude: terdeteksi=2 harus=ya
  ok    signed-off AI: terdeteksi=1 harus=ya
  ok    generated-with: terdeteksi=1 harus=ya
  ok    nama model di badan pesan: terdeteksi=0 harus=tidak
  ok    pembahasan aturan: terdeteksi=0 harus=tidak
6 kasus, 0 salah.

$ python -X utf8 vault/scripts/prepush_check.py
0 commit pada origin/master..HEAD (--range) -> tidak ada yang perlu diperiksa; lolos.

$ python -X utf8 vault/scripts/prepush_check.py --all
  PELANGGARAN 08cb04  vault disusun ulang: pola Lencana (hub + part note), isi sesi 26
      -> 'Co-Authored-By: Claude <noreply@anthropic'
      -> 'noreply@anthropic.com'
393 commit diperiksa pada HEAD (--all (seluruh riwayat)); 1 commit membawa atribusi AI -> JANGAN push.
```

## Yang dibuktikannya — dan yang tidak

- ✅ Detektornya menangkap **kasus nyata** (`08cb049`), bukan cuma contoh sintetis — dan hanya itu
  satu dari 393 commit, yang memang keputusan builder (lihat F-D22).
- ✅ Ia **tidak** menyalakan alarm untuk prose yang membahas aturannya sendiri ("jangan menulis
  `Co-A…By: …` di commit") dan tidak untuk `nama model di badan pesan`. Guard yang berisik dibypass
  lalu dimatikan; ini sudah kami alami hari yang sama di lapis lain.
- ✅ Jalan di server: `.github/workflows/attribution-guard.yml` memanggil `--self-test` lalu
  `--range <sebelum>..<sesudah>` tiap push/PR, `permissions: {}`, read-only. Jadi penegakannya tidak
  bergantung pada siapa yang sedang menyetir agent.
- ❌ **Bukan** pengganti kabar ke builder. Perintah ini jalan *setelah* commit ada; ia tidak bisa
  memutuskan apakah sebuah commit layak dikirim. Kabar sebelum push tetap wajib (F-D22).
- ❌ Tidak memeriksa isi diff, tidak menilai klaim, dan tidak menutup celah "pesan commit ditulis
  lewat editor interaktif tanpa melewati alat ini" — itu urusan Actions, yang justru karena itu ada.

## Kalau gagal

- Exit 2 (bukan 1) = **tidak bisa menyimpulkan** (branch tanpa upstream / `git log` gagal). Jangan
  artikan itu sebagai lolos; pakai `--range origin/master..HEAD` eksplisit.
- Menemukan pelanggaran di commit yang **belum ter-push**: `git commit --amend -F <pesan>` untuk yang
  di ujung, `git rebase -i` untuk yang di tengah.
- Pelanggaran yang **sudah ter-push**: jangan force-push sendiri. Ukur dulu
  `git rev-list --count <base>..HEAD` — satu commit lama bisa menyeret ratusan hash — laporkan
  angkanya, dan minta keputusan builder. Itu persis urutan yang dipakai untuk `5e4468f`.

**Terkait:** [[00-Overview/03 - Decisions]] F-D22 · [[Conventions]] §Turunan ·
[[07-Testing/T5 - Integrity Harness]] · [[07-Testing/01 - Test Commands]] baris 9–10
