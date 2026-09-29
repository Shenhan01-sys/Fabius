---
tags: [hasil, "pra-registrasi", "E22", veto]
---

# 25 - Rem, Terkunci Prospectif

**Bagian dari:** [[06-Results/00 - Hub Results]] · [[08-Backlog/02 - Epik Alasan Masuk]] §3f ·
[[06-Results/21 - Rem di Horison Cepat]]
**Alat:** `tools/gate_ab.py` · **Kunci:** `decisions/prereg-gate-lock.json`

## 1. Kenapa halaman ini ada

Satu-satunya perilaku Fabius yang bertahan setelah sepekan mencabut klaim sendiri adalah rem
`jual_*`. Tapi semua angkanya (**+82,7 → +162,3 bps** di 30 menit, **BOLEH +285,5 vs VETO −230,3**
di menit ke-5, **16/16 grid ambang**) berasal dari **satu jendela yang sama**, sampai jam
`t_kunci` watch. Itu posisi yang sudah tiga kali kami huni dan selalu berakhir di halaman koreksi
(F-D30, F-D32, F-D39, F-D40, F-D46). Obatnya bukan menganalisis lebih dalam - obatnya menulis
aturannya sekarang, lalu menunggu data yang belum pernah kami lihat.

## 2. Spesifikasi yang dikunci

```text
E22 - rem diuji prospectif pada horison tempat kabar hidup.

populasi       : kejadian BELI dari ⑦ (k=tx/txc, b=true) dengan t > t_kunci; non-overlap 1 per 30 m
                 per token; harga masuk = `wp` terakhir dengan t_kejadian >= t
lengan         : BOLEH (flow_gate.state lulus) vs VETO (ditolak) - aturan ambang TIDAK diubah
outcome        : median `wp` pada t+[2m, 8m] minus harga masuk, minus ongkos round-trip terukur
winsor         : +/-1.500 bps pada mean (bukan 2.000 seperti E11 - dipilih sebelum lihat hasil);
                 median dilaporkan tanpa winsor
vonis_primer   : selisih = mean_winso(BOLEH) - mean_winso(VETO)
syarat_layak   : (1) n_boleh >= 40 DAN n_veto >= 15
                 (2) median(BOLEH) > 0 DAN CI bawah bootstrap 4000 (seed 20260929) dari selisih > 0
                 (3) Mann-Whitney satu arah BOLEH > VETO p < 0,05 DAN selisih > CI atas placebo
                     (penandaan ulang label, 1000 undian)
                 (4) P(ada harga keluar) >= 60 % pada KEDUA lengan DAN umur baris harga keluar
                     dilaporkan dalam menit, per lengan
umur_kunci     : 8 jam (disetujui sebelum ada angka; tenggat 30 Sep 16:59Z)
kalau_kecil    : 'BELUM BISA DIUJI' - ambang, winsor, dan umur tidak diubah setelah hasil dilihat
kalau_gagal    : klaim 'rem memperbaiki hasil' tetap in-sample; TIDAK dibalik menjadi
                 'VETO justru untung' tanpa kunci baru
jangan         : tidak mengubah flow_gate.py; tidak mengirim order; tidak mengutip OFI/buku order
                 (halaman itu punya kuncinya sendiri, E16)
```

## 3. Empat syarat, dan apa yang menggagalkannya

| syarat | maksudnya | siapa yang sudah membunuh klaim kami lewat pintu ini |
|---|---|---|
| **1** n≥40 `BOLEH`, n≥15 `VETO` | angka kecil tidak boleh punya opini | F-D16; `lock_percent` mati di hari kedua (P27) |
| **2** median(BOLEH)>0 **dan** CI bawah selisih >0 | mean ber-ekor tebal bisa berbohung; kami laporkan keduanya | F-D39 (mean = satu undian), FD5 (expectancy ≠ win rate) |
| **3** satu arah: Mann-Whitney **dan** placebo label | satu kontrol pernah mempromosikan dirinya sendiri (F-D32); placebolabel itu kontrolnya E13 | F-D32, F-D40 |
| **4** `P(ada harga keluar)` ≥60 % kedua lengan **dan** umur barisnya dilaporkan | supaya "5 menit" adalah ukuran, bukan nama | F-D41, F-D30 |

**Syarat umur 8 jam, bukan 12** seperti tiga kunci sebelumnya - dan itu kusetujui di sini, **sebelum**
satu pun pasangan pasca-kunci dihitung, karena tenggat 30 Sep 16:59Z dan siklus ⑦ (~200 detik)
memberi ratusan kejadian per 8 jam. Bukan kompromi yang discovered nanti: kalau saat matang n masih
kurang, vonisnya tertulis "BELUM BISA DIUJI" dan ambang tetap di tempatnya.

Kalau hasilnya **GAGAL**, yang berubah adalah kalimat kami: "rem memperbaiki hasil" tetap
kebenaran **di dalam sampel**, dan klaim prospectifnya dicabut - bukan dibalik jadi "VETO justru
untung". Kalau **LAYAK**, ini pertama kalinya sebuah perilaku Fabius lolos uji pada data yang
belum ada saat rule-nya ditulis - dan itu tetap tidak berarti "profit": tiga tembok (venue
3,1 %, umur kabar ±13 menit, `i` +245 bps) tidak bergerak oleh halaman ini.

## 4. Cara menjalankan

```bash
python -X utf8 tools/gate_ab.py --self-test
python -X utf8 tools/gate_ab.py --lock      # sekali; menolak dobel
python -X utf8 tools/gate_ab.py --status    # umur kunci + jumlah kejadian pasca-kunci
python -X utf8 tools/gate_ab.py             # vonis (menolak cetak angka sebelum matang)
```

## 5. Hasil

_kosong sampai umur kunci cukup - kekosongan ini bagian dari spesifikasinya._

**Terkait:** [[06-Results/21 - Rem di Horison Cepat]] · [[06-Results/18 - Kandidat Pertama, Diuji Hidup]] · [[06-Results/20 - Keluar Cepat, Terkunci]] · [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] · [[00-Overview/03 - Decisions]] F-D31/F-D44/F-D45/F-D52
