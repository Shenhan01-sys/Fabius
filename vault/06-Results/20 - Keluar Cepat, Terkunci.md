---
tags: [hasil, "pra-registrasi", "E12", "umur-posisi"]
---

# 20 - Keluar Cepat, Terkunci

**Alat:** `tools/hold_ab.py` · **Kunci:** `decisions/prereg-hold-lock.json` · **Job:** rantai ⑦
(menulis `tx` + `wp` terus) · **Bagian dari:** [[06-Results/00 - Hub Results]] ·
[[08-Backlog/02 - Epik Alasan Masuk]] §3e

## 1. Yang sedang di bayar di halaman ini

[[06-Results/19 - Umur Posisi]] (E11) adalah angka positif pertama proyek ini yang lolos placebo.
Ia juga adalah godaan pertama yang sungguh-sungguh: kurva yang naik lalu meluruh itu mudah sekali
dibaca sebagai "Fabius tahu kapan masuk dan kapan keluar", padahal yang diukur adalah data **sampai**
`t_kunci` watch — sampel yang sama yang sudah empat kali mempromosikan dirinya sendiri (F-D30 harga
masuk beku, F-D32 control yang menang karena bentuknya, F-D37 Mann-Whitney salah urut, F-D39 satu
undian disebut hasil, F-D40 kontrol keluar yang salah).

Satu-satunya obat yang kami punya untuk pola itu adalah menulis aturannya sebelum datanya ada.
Kunci ini dipasang **setelah** E11 dilihat dan **sebelum** satu pun pasangan E12 dihitung — itu
artinya dia boleh berbeda dari E11, tapi tidak boleh lagi diubah oleh hasilnya.

## 2. Spesifikasi yang dikunci

```text
E12 - uji terkunci 'keluar cepat' sebagai kebijakan.

arm_kebijakan : keluar pada horison 5 menit setelah kejadian beli kerumunan pintar
arm_kontrol   : horison 30 menit pada POSISI yang sama (bukan nol)
delta         : net(5m) - net(30m), winsor +/-2.000 bps, ongkos 59 bps RT di kedua sisi
harga_masuk   : `wp` terakhir dengan t <= t_kejadian (kanonis E7/E11); varian `tx.p` dilaporkan
                sebagai pemeriksaan, BUKAN sebagai lengan yang boleh dipilih setelah lihat hasil
harga_keluar  : median `wp` pada t+[H-3m, H+3m]; umur median itu dilaporkan apa adanya
perhitungan   : HANYA kejadian dengan t > t_kunci; non-overlap 1 per 30 m per token
vonis_layak   : (1) n >= 20 DAN (2) median > 0 DAN CI bawah bootstrap 4000 (seed 20260928) > 0
                DAN (3) tanda-uji eksak satu arah p < 0,05
                DAN (4) P(ada harga keluar) + umur baris harga keluar dilaporkan untuk dua arm
kalau_kecil   : tulis 'BELUM BISA DIUJI', jangan 'TIDAK ADA EFEK'; ambang tidak diturunkan
kalau_gagal   : horison pendek ditutup sebagai kebijakan; TIDAK dibalik jadi 'tahan lebih lama'
lapor_wajib   : n pasangan, token unik, median & mean winso delta, CI, p, umur harga tiap arm,
                P(ada harga keluar) tiap arm, selisih `wp` vs `tx.p`
eksekusi      : alat ini tidak mengirim order; klaim 'bisa diambil' butuh P40 (jalur < 2 menit)
```

## 3. Kenapa kontrolnya horison 30 menit, bukan nol

Di pool yang mean-nya **−183,7 bps** (E7), apa pun yang "melawan nol" akan terlihat hebat. F-D16
sudah pernah menangkap kami karena itu, jadi arm pembandingnya adalah **kebiasaan lama kami sendiri
pada posisi yang sama**: tahan sampai 30 menit. Kalau keluar 5 menit tidak mengalahkan itu, tidak ada
yang berubah dan tidak ada yang boleh ditulis.

Dan kalau menang: yang menang adalah **kebijakan umur**, bukan kemampuan membaca arah. E11 sudah
menunjukkan bahwa menunda masuk **2 menit** saja membuat median@5m jadi **−56,2** — jadi klaim
"bisa diambil" tetap butuh P40 (jalur sinyal→order di bawah dua menit), dan itu pekerjaan
infrastruktur, bukan pekerjaan halaman ini.

## 4. Cara menjalankan

```bash
python -X utf8 tools/hold_ab.py --self-test   # 4 kasus: prefill dibuang, datar != layak,
                                              # arah buruk = GAGAL, syarat lapor umur dinilai
python -X utf8 tools/hold_ab.py --lock        # pasang kunci SEKALI (menolak dobel)
python -X utf8 tools/hold_ab.py --status      # umur kunci + berapa pasangan pasca-kunci
python -X utf8 tools/hold_ab.py               # vonis (menolak cetak angka sebelum matang)
python -X utf8 tools/hold_ab.py --tanpa-umur  # bacaan sementara, dicetak dengan LABEL PERINGATAN
```

Syarat umur **12 jam** dari pemasangan kunci. Kalau saat matang `n < 20`: vonisnya tertulis
**"BELUM BISA DIUJI"** — ambang tidak boleh diturunkan, dan itu bukan "tidak ada efek"
([[Concepts/Unmeasured Is Not Clean]]).

## 5. Hasil

_kosong sampai umur kunci cukup — dan kekosongan ini bagian dari spesifikasinya._

**Terkait:** [[06-Results/19 - Umur Posisi]] · [[06-Results/18 - Kandidat Pertama, Diuji Hidup]] ·
[[06-Results/13 - Apakah Tidak Trading Itu Gratis]] · [[00-Overview/03 - Decisions]] F-D41 ·
[[Concepts/One-Way Gate]] · [[TradingKnowledge/FD5 - Expectancy Bukan Win Rate]]
