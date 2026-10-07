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

## Hasil

(diisi sesudah lari pertama; angka dicetak perintah di atas)

**Terkait:** [[08-Backlog/05 - Epik Enam Bot]] §5 · [[04-Tools/TL33 - agent analis]] · [[04-Tools/TL9 - ledger paper maju]] · [[04-Tools/TL43 - evaluasi meja F4]] ·
[[00-Overview/03 - Decisions]] F-D16 · F-D102
