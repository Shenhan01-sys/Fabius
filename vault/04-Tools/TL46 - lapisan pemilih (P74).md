---
tags: [perkakas, "TL46", pemilih, evaluasi, brier]
---

# TL46 - lapisan pemilih + evaluasi: pembanding EW / acak / trailing, ongkos ganti, BH, Brier (P74)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `engine/pemilih_eval.py` (aturan + angka `PARAMS_P74`, kebijakan pembanding, `jalankan`, uji, Brier, `evaluasi`, `teks`, kunci) · CLI
`tools/pemilih_eval.py` (`status` / `usulan` / `kunci` / `mundur` / `maju`) · pra-registrasi `engine/locks/pemilih_eval.usulan.json` (status USULAN) ·
tes `engine/tests/test_pemilih_eval.py` · aturan pemilih hidup yang DINILAI [[04-Tools/TL33 - agent analis]] (`engine/pemilih.py`, P143, terkunci) ·
spesifikasi [[08-Backlog/05 - Epik Enam Bot]] §5 "Evaluasi pemilih" + §12 P74 · backlog P74

## Apa

Epik 05 §5 menulis aturan evaluasi pemilih bot sebelum pemilihnya ada: *"kontrol = EW enam bot + pilihan acak + 'bot terbaik 60 hari'; skor Brier
prediksi rezim sebelum PnL; BH lintas enam bot; jeda minimum antar-pergantian (pergantian = ongkos)"*. Pemilihnya sekarang ada (`engine/pemilih.py`:
bot AKTIF per bar dari pilihan agent analis, P143). Halaman ini adalah lapisan yang MENGUKURNYA. Ia **hanya mengukur**: tidak mengubah bot aktif, buku
slot, aturan pemilih, atau apa pun yang hidup.

## Aturan (dipra-registrasi SEBELUM hasil apa pun dilihat; status USULAN sampai kata builder)

Semua angka hidup di `PARAMS_P74` (sha di berkas usulan); mengubah satu angka sesudah hasil terlihat = keputusan baru + usulan baru yang tercatat di
`engine/locks/history/`, bukan penyetelan diam-diam (`status()` mencetak MENYIMPANG bila kode bergeser dari berkas).

| bagian | aturan | angka |
|---|---|---|
| konvensi waktu | `net[bot][T]` = net paper bot pada bar T (waktu BUKA) dari target penutupan bar sebelumnya (sama dengan `replay()` + `settle`). Kebijakan memutuskan bot untuk bar T HANYA dari net bar < T | - |
| kandidat + kalender | bot yang punya net; kalender = bar tempat SEMUA kandidat punya net (irisan) | - |
| IDENTITAS | selalu bot identitas (penghuni buku slot) | `B1-TREND` |
| EW | rata-rata net harian semua kandidat (satu sub-akun per bot, tanpa ongkos ganti) | - |
| TRAILING ("bot terbaik 60 hari") | pada penutupan bar sebelum T: bot dengan jumlah net 60 bar kalender terakhir tertinggi; seri -> identitas bila ikut seri, selain itu abjad; < 60 bar riwayat -> identitas; ganti hanya bila sudah >= jeda bar sejak ganti terakhir | jendela 60 · jeda 5 **USULAN** |
| ACAK | tiap 5 bar pilih seragam di antara kandidat; DISTRIBUSI 1.000 tarikan (benih = sha masukan + nomor tarikan), bukan satu tarikan | n 1.000 · jeda 5 **USULAN** |
| NONE | datar, net 0 - selalu sah dan gratis | - |
| ongkos ganti | bar pertama sesudah ganti A -> B: `gross_A x biaya_A + gross_B x biaya_B` (keluar penuh + masuk penuh, tanpa netting aset yang sama = batas atas). `biaya` = penggaris spesifikasi per sisi (B3: per kaki x 2); `gross` = jumlah abs bobot target yang dipegang; tanpa data bobot = 1,0 | **USULAN** |
| pemilih tanpa pilihan di satu bar | bot identitas (aturan 1 `engine/pemilih.py`) | - |
| uji | statistik = rerata selisih net harian (pemilih - pembanding); p satu sisi dari bootstrap blok melingkar terpusat (pola `engine/fd16.py`); vs ACAK: p = (1 + jumlah tarikan dengan jumlah net >= pemilih) / (n + 1) | blok 5 hari · 10.000 tarikan · benih = sha masukan |
| keluarga BH | SEMUA hipotesis (pemilih x pembanding) dalam satu laporan, Benjamini-Hochberg | alpha 0,10 **USULAN** (sama dengan S5 F-D16) |
| Brier (dicetak SEBELUM PnL) | biner: p = keyakinan / 100 untuk kejadian "bot pilihan net > bot identitas net" (pilihan = identitas atau net sama dikecualikan); acuan 0,5 -> Brier 0,25; skill = 1 - Brier / 0,25. Multi-kelas: p per bot, kelas = bot terbaik bar itu (seri dibagi rata), acuan seragam 1/N. Kalibrasi: 5 ember | min 30 prakiraan **USULAN** |
| vonis MAJU | BELUM CUKUP DATA bila hari < 60; UNGGUL bila SEMUA hipotesis pemilih itu lolos BH DAN (bila ada prakiraan dengan n >= 30) skill Brier > 0; selain itu TIDAK UNGGUL | hari min 60 **USULAN** |
| mode MUNDUR | replay historis dari `ledger/bars`: parameter bot dipilih pada periode yang sama -> DALAM-SAMPEL; tidak pernah memberi vonis, hanya `EKSPLORATIF` | - |
| data MAJU | settle FINAL `ledger/paper` + pilihan dikomit `ledger/analis` (satu per agent per bar, yang dikomit menang); settle PROVISIONAL dicetak terpisah tanpa vonis | - |

**Butir USULAN yang menunggu builder:** jeda 5 bar (TRAILING + ACAK), model ongkos ganti (keluar + masuk penuh), alpha BH 0,10 lintas semua hipotesis,
hari minimum 60, Brier min 30 + makna `keyakinan` (peluang bot pilihan mengalahkan bot identitas pada bar itu), dan pemilih tanpa pilihan = identitas.

## Yang BELUM / tidak dibuktikan

- Tidak ada vonis maju sekarang: settle FINAL butuh funding aktual bulanan (B1, B2, B6 baru final sesudah zip Oktober terbit awal November), dan pilihan
  agent baru ada sejak penutupan 2026-10-06. Laporan maju akan BELUM CUKUP DATA sampai >= 60 hari kalender bersama.
- Rekonstruksi pemilih hidup memakai skor pilihan yang tersedia SAAT DIHITUNG (final), bukan provisional saat gerbang memutuskan dulu; perbedaannya
  hanya mungkin di bar yang pemimpinnya berganti karena skor provisional berubah menjadi final.
- B4 tidak bisa direplay (`replay()` menolak; butuh deret per event), jadi mode mundur memakai lima bot harian (B1, B2, B3, B5, B6).
- Ongkos ganti adalah batas atas penggaris spesifikasi (fee per sisi); spread dan dampak belum dimodelkan (P69).
- "Prediksi rezim" dalam arti probabilitas per bot belum dihasilkan pemilih mana pun; antarmuka multi-kelas siap dan diuji, yang terpakai hari ini
  hanya keyakinan agent analis (biner).

## Cara memakai

```
python -X utf8 tools/pemilih_eval.py status                         # USULAN / TERKUNCI / MENYIMPANG + sha
python -X utf8 tools/pemilih_eval.py mundur [--json out.json]        # EKSPLORATIF, replay ledger/bars, tanpa vonis
python -X utf8 tools/pemilih_eval.py maju   [--json out.json]        # MENGIKAT: settle final + pilihan dikomit; provisional terpisah
python -X utf8 tools/pemilih_eval.py kunci --catatan "disetujui Hans <tanggal>"   # hanya atas kata builder, sha = berkas usulan
```

## Hasil (7 Okt 2026, lari pertama SESUDAH pra-registrasi `0x4003c4befa0e609ecbc5ceeed3b7101387777dfbeeedd8d655645e5aa711045c`)

Urutan bukti: berkas usulan ditulis 06:37:05Z dan di-commit (`a54825d1` di cabang kerja) SEBELUM `mundur` / `maju` pertama dijalankan.

**Mundur - EKSPLORATIF, dalam-sampel** (`python -X utf8 tools/pemilih_eval.py mundur`, 7,8 s): kalender 1.373 bar 2023-01-02 .. 2026-10-05
(irisan lima bot harian; B5 mulai 2023 karena deret PAXG), jumlah + MDD = penjumlahan net harian (bukan majemuk).

| kebijakan | rata bps / hari | jumlah % | Sharpe | MDD % | ganti | ongkos ganti % |
|---|---|---|---|---|---|---|
| IDENTITAS (B1-TREND) | +8,68 | +119,15 | 0,80 | 41,88 | 0 | 0,00 |
| EW lima bot | +4,70 | +64,49 | 1,03 | 18,66 | 0 | 0,00 |
| TRAILING 60 (jeda 5) | +2,30 | +31,52 | 0,19 | 100,28 | 84 | 12,14 |
| NONE | 0,00 | 0,00 | - | 0,00 | 0 | 0,00 |
| ACAK (1.000 tarikan, jeda 5) | jumlah % p05 -46,32 · p50 +34,05 · p95 +120,02 | | | | | |

Per bot (konteks, bukan hipotesis): B1 +8,68 bps (Sharpe 0,80) · B2 +2,89 (0,20; MDD 96,10) · B3 +0,72 (4,77; MDD 0,74) · B5 +8,90 (1,47) · B6 +2,29 (0,35).
Uji eksploratif TRAILING: vs ACAK p 0,5225 · vs EW p 0,6773 · vs IDENTITAS p 0,8736 - tidak ada yang lolos BH. Bacaan (bukan klaim, dalam-sampel):
"bot terbaik 60 hari" adalah lantai yang rendah - 84 kali ganti memakan 12,14 poin persen - sedangkan EW (Sharpe 1,03, MDD 18,66) adalah pembanding
yang sulit dikalahkan. Pemilih yang ingin UNGGUL harus mengalahkan keduanya SESUDAH ongkos ganti.

**Maju - MENGIKAT** (`python -X utf8 tools/pemilih_eval.py maju`): FINAL - kandidat B3-CARRY, B5-CORE-RWA, B6-BOUNCE (yang punya settle final);
bot identitas B1-TREND belum punya settle final (funding aktual Oktober belum terbit) -> PEMILIH, agent:berita, agent:glm, agent:qwen = **BELUM CUKUP
DATA**. PROVISIONAL - lima bot, kalender 1 bar (2026-10-05); pilihan agent pertama (3 catatan, penutupan 2026-10-06) belum ber-settle -> bar terukur
1 < 2, label PROVISIONAL (bukan vonis). Vonis maju pertama paling cepat sesudah >= 60 bar settle final bersama.

**Tes:** `engine/tests/test_pemilih_eval.py` 27 lulus; lima mutasi (trailing membaca bar T, ongkos ganti dihapus, hari minimum diabaikan, BH
diabaikan, pilihan di luar kandidat ditebak) semuanya membuat tes gagal (satu tes hampa ditemukan + diperbaiki: gangguan masa depan yang sama untuk
semua bot tidak mengubah peringkat).

**Terkait:** [[08-Backlog/05 - Epik Enam Bot]] §5 · [[04-Tools/TL33 - agent analis]] · [[04-Tools/TL9 - ledger paper maju]] · [[04-Tools/TL43 - evaluasi meja F4]] ·
[[00-Overview/03 - Decisions]] F-D16 · F-D102
