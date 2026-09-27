---
tags: [tk, tk-pipeline, "PL7"]
---

# PL7 - Kontrak Antar-Tahap

**Keluarga:** [[00 - Hub Pipeline]] · **Tahap:** lintas-tahap (PL1–PL6) · urutan ringkas: [[01-Agent/A2 - Decision Spine]]
**Sumber:** `tools/anchor.py`, `tools/decide.py`, `tools/direction.py` · [[03-Data/D5 - Record Schemas]] · [[Fakta Terukur]] §G

**Ringkas:** Yang membuat sebuah pipeline trading bisa diperiksa orang lain bukan kecerdasannya,
melainkan **kontrak di antara tahapnya**: bentuk record, hash, dan aturan apa yang dilarang berubah setelah
ditulis. Fabius memakai tiga hash — `decisionHash`, `gatesHash`, `snapshotHash` — dan ketiganya dikirim ke
chain **sebelum** hasilnya ada. Umur snapshot ikut ter-hash, sehingga keputusan di atas data basi tetap
terbaca basi sampai ke buktinya. Urutan inilah produknya, bukan tebakan kami ([[Concepts/Anchored Before Outcome]]).

## Definisi yang bisa dihitung

```
kanonis(obj)   = json.dumps(sort_keys=True, separators=(",",":"))     # dua orang, satu hasil
snapshotHash   = sha256(kanonis(snapshot aslian))         # termasuk UMUR snapshot (universe_age_h)
gatesHash      = sha256(kanonis(daftar gerbang yang menggugurkan))
decisionHash   = sha256(kanonis(rec))                     # rec memuat seat_blockers + alasan ①④⑥
id_chain       = keccak(agen, decisionHash, snapshotHash, chainid)   # dibaca ulang tanpa kunci/gas
```

Aturan kontrak, ditulis sebagai larangan supaya bisa diuji dengan melanggarnya:

```
setelah_tertulis(x): x tidak disunting, tidak ditarik, tidak di-reset
hasil_datang(x)    : boleh menutup x (jadi MENANG/RUGI), tidak boleh mengubah x
tanpa_hash(x)      : kontrak menolak (hash nol ditolak) -> tidak ada posisi tanpa jejak
```

Artefak minimum tiap tahap ada di berkas yang bisa dibaca pihak lain, bukan di log proses: snapshot
per jendela + `manifest.txt` ber-sha256, `decisions/*.jsonl`, `ledger-*.jsonl`, `execution-trail.jsonl`
([[03-Data/01 - Dataset]], [[03-Data/D5 - Record Schemas]]).

## Cara pakai yang diklaim

Praktik umum (T1): "simpan catatan eksperimen" (MLflow, spreadsheet hasil, notebook). Untuk trading
retail itu biasanya berarti "ada file CSV di suatu tempat". Yang kami pakai sebagai gantinya adalah
versi yang bisa diadu: **skema tertulis, field yang ikut di-hash disebutkan, dan verifikasinya
menolak asumsi**. `tools/decide.py` tidak membaca field kesimpulan yang tersimpan di snapshot,
melainkan menghitung ulang gerbangnya dari angka mentah memakai ambang yang tersimpan di snapshot itu
sendiri — kalau kita memercayai hasil simpanan, snapshot turun derajat jadi memorandum.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| skema record yang terdaftar field per field | `ADA` | [[03-Data/D5 - Record Schemas]] (dibuat oleh `vault/scripts/dump_schemas.py`) |
| hash snapshot pada saat pengambilan, di commit | `ADA` | `universe/manifest.txt` — riwayat git tidak bisa disisipi diam-diam — [[03-Data/01 - Dataset]] |
| penulisan anchor + pembacaan ulang oleh pihak lain | `ADA` | `tools/anchor.py --verify`, nol kunci nol gas — §G |
| verifikasi historis 100 % bersih | `ADA-TAPI` | ada baris snapshot yang tidak bisa diverifikasi ulang dan alarmnya **dibiarkan berbunyi** — [[06-Results/03 - Not Yet Proven]] baris 21 |
| riwayat yang bisa disusulkan di jalur bukti | `TIDAK-ADA` | sumber ber-`_updated_at` tidak boleh jadi saksi waktu — [[Concepts/Point-in-Time vs Retro-updatable]] |
| kontrak dengan dua verdict saja | `ADA` | `Enter`/`Abstain`; "flat" masuk `Abstain` — [[02-Contracts/01 - DecisionAnchor]] |

## Uji di Fabius

```
python -X utf8 tools/anchor.py --dry-run      # apa yang AKAN dikirim (tanpa flag ini ia kirim)
python -X utf8 tools/anchor.py                # kirim, lalu baca ulang dan bandingkan word per word
python -X utf8 tools/anchor.py --verify       # auditor: hitung id dari berkas repo, baca chain
python -X utf8 vault/scripts/dump_schemas.py  # exit non-zero kalau field baris pertama != terakhir
```

Kelulusan yang berlaku: `--verify` mencetak **semua** field yang dibandingkan cocok (§G: 13 baris
terpelacak, 13/13 COCOK). Angka yang tidak boleh dilunakkan: `anchorCount()` = 19 sementara hanya 13
yang terpelacak — **lubang yang tercatat**, bukan keberhasilan (§G, P6b di
[[08-Backlog/01 - Backlog]]). Urutan tidak boleh diputar: tidak ada jalur di mana hasil tahap 6
mengubah tahap 4, karena anchor tidak pernah ditarik.

## Batas dan mode gagal

- **Hash dihitung di atas struktur, jadi bentuk adalah bagian dari bukti.** String `①④⑥` di
  `seat_blockers` ikut masuk `decisionHash`; menggantinya ke ASCII mengubah hash keputusan berikutnya
  — dan glyph itu tidak ada di cp1252. Karena itu semua perintah vault ditulis `python -X utf8`:
  `print` yang pecah **di tengah** laporan lebih buruk daripada gagal di awal
  ([[Conventions]], [[04-Tools/TL2 - direction]]).
- **Baris yang salah label dibiarkan.** Menyunting berkas append-only untuk kerapian mengubah bukti
  menjadi sesuatu yang tidak bisa dipercaya siapa pun; koreksinya adalah catatan, bukan suntingan
  ([[00-Overview/05 - Corrections]]).
- **Kegagalan senyap di sisi pembaca:** `getAnchor(id)` untuk id tak dikenal **tidak revert** — ia
  mengembalikan struct nol, dan klasifikasi "belum di-anchor" sempat jadi cabang mati
  ([[04-Tools/TL4 - anchor and verify]]).
- **Sebuah klaim hanya boleh menyebut field yang benar-benar dibandingkan.** Pernah `chain==lokal: YA`
  tercetak sambil satu field lain terbaca sampah: hash cocok, pemeriksaannya lebih sempit dari kalimatnya.
- **Dua penulis = satu berkas rusak secara metodologis** (konflik union), dan **nomor skema yang
  naik di tengah proses hidup** menghasilkan baris salah label ([[03-Data/D2 - Wallet Flow]]).
- **Artefak lama tidak dipindah demi kerapian:** jalur yang sudah berubah pun dibiarkan seperti pada
  saat run, dengan peta jalur lama→baru ([[03-Data/D5 - Record Schemas]]).

## Tingkat bukti

`T3` untuk kontrak dan verifikasinya: perintahnya ada, bisa dijalankan dari clone tanpa kunci, dan
keluarannya menjadi tempat angka §G dicetak. Untuk isi keputusan yang di-anchor, tingkat buktinya
tetap apa yang ada di [[PL6 - Menilai Hasil]] — **anchor tidak membuat tebakan benar**, ia hanya
membuat tebakan tidak bisa disunting setelah kenyataan datang.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "keputusan kami ditulis, di-hash, dan masuk chain sebelum hasilnya ada; orang lain bisa
  membacanya ulang tanpa memercayai kami; dan umur data yang dipakai ikut ter-hash."
- **Dilarang:** "semua rekaman kami lolos verifikasi" (ada yang tidak, dan alarmnya sengaja tetap
  berbunyi) · "anchor membuktikan keputusan kami benar" · "verifiable" tanpa menyebut field yang dibandingkan.

**Terkait:** [[PL1 - Mengumpulkan Data]] · [[PL4 - Memutuskan]] · [[PL6 - Menilai Hasil]] ·
[[Concepts/Anchored Before Outcome]] · [[Concepts/Point-in-Time vs Retro-updatable]] ·
[[EV5 - Reproduksibilitas dan Pra-Registrasi]] · [[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]
