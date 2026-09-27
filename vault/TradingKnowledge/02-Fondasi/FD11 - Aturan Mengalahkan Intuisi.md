---
tags: [tk, tk-fondasi, "FD11"]
---

# FD11 - Aturan Mengalahkan Intuisi

**Keluarga:** [[00 - Hub Fondasi]] · **Tahap:** keputusan ([[PL4 - Memutuskan]]), mengikat semua tahap
**Sumber:** [[Fakta Terukur]] §E/§F · `tools/judge.py` §1 · [[01-Agent/A3 - One-Way Gates]] · [[06-Results/05 - Pre-registration Flow]] · [[00-Overview/03 - Decisions]] F-D16

**Ringkas:** "Psikologi trading" bukan cerita tentang rasa takut — itu cerita tentang seseorang yang
mengubah aturan setelah melihat hasil. Agen tidak punya rasa takut, tapi punya versi mesin dari
penyakit yang sama: ia bisa mencoba 400 varian dan melaporkan dua yang lolos. Obatnya bukan
kecerdasan, melainkan gerbang yang hanya boleh mengurangi dan aturan yang ditulis sebelum hasilnya ada.

## Definisi yang bisa dihitung

```
gerbang satu-arah : keluaran komponen penilaian hanya boleh mengurangi
                    (veto / kecilkan / tandai belum-terukur), tidak pernah membuka
pra-registrasi    : definisi + ambang + aturan keputusan tercatat SEBELUM satu angka hasil dilihat
amend             : perubahan aturan = entri keputusan baru, BUKAN menyunting halaman lama
data snooping     : jumlah aturan yang dicoba sebelum yang dipakai dilaporkan; tanpa angka ini,
                    p-value tidak punya arti (lihat [[EV3 - Signifikansi dan Multiple Testing]])
keberatan yang sah: hasil yang memaksa aturan berubah harus lewat uji baru pada DATA BARU, bukan
                    lewat menala aturan di data yang sama
```

Terjemahan "psikologi trading" menjadi kode, satu per satu:

| penyakit manusia | padanan agen | rem yang ada di repo |
|---|---|---|
| FOMO / mengejar | model/LLM usul arah di luar gerbang | `tools/judge.py`: penilai hanya boleh menambah penolakan; ABSTAIN tidak pernah naik jadi ENTER |
| denial / menahan rugi | status "belum tahu" dianggap bersih | `tools/direction.py::apply_gates`: `UNMEASURED` **mencabut** hak kursi, tidak memberi ([[Concepts/Unmeasured Is Not Clean]]) |
| revenge trading | menambah ukuran setelah rugi | tidak ada jalur penambah ukuran; `AlreadyOpen` menolak posisi kedua per aset |
| hindsight bias | menarik kembali prediksi yang salah | anchor dibiarkan jatuh tempo; menariknya = menghancurkan buktinya ([[06-Results/04 - Negative Results]] §5) |
| motivated reasoning | memilih keluar yang paling enak | `tools/ledger.py`: stop+target di bar yang sama ditulis `AMBIGU`; `BELUM JATUH TEMPO` tidak ikut agregat |
| overconfidence | keyakinan menaikkan ukuran | `conf` hanya memotong (`conf = min(conf, 0,5)`) dan memilih rezim; plafon datang dari kontrak |
| narasi "tapi pasarnya beda" | menala aturan di data yang sama | pra-registrasi terkunci + uji arah balik (`--flip`) dijalankan, bukan dinarasikan |

## Cara pakai yang diklaim

Klaim biasa: "disiplin menaikkan return". Yang bisa kami dukung lebih sempit dan lebih keras: aturan
satu-arah menaikkan **nilai bukti** dari apa yang kami laporkan, dan sering **menurunkan** jumlah
trade yang boleh dilakukan. Ia tidak menciptakan edge; ia mencegah edge imajiner dibuat oleh
penulisan ulang sejarah. Ini produknya, bukan caranya menjual.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| rekaman aturan yang dipakai saat memutuskan | `ADA` | `why`/`regime`/`sellability`/`seat_eligible` ikut `gatesHash`; `seat_blockers` dan `entry_ref` ikut `decisionHash` — `tools/direction.py` |
| jejak yang tidak bisa disunting setelah hasil tiba | `ADA` | anchor di chain + `tools/anchor.py --verify` ([[Concepts/Anchored Before Outcome]]) |
| halaman pra-registrasi yang terkunci | `ADA` | [[06-Results/05 - Pre-registration Flow]] dan [[06-Results/06 - Pre-registration Horizon]] ditulis sebelum angka; amend hanya lewat entri keputusan |
| hitungan berapa varian yang dicoba | `TIDAK-ADA` | tidak ada register hipotesis; kami jujur menyebutnya di batas halaman ini |
| aturan yang berubah tanpa jejak | `ADA-TAPI` | `killSwitch` bisa dimatikan kembali oleh owner (`setKillSwitch(bool)`), jadi "satu-arah" hidup di lapisan keputusan + rekaman, bukan di bytecode |

## Uji di Fabius

Yang sudah terukur dan menunjukkan gerbang bekerja **melawan** usulan penilai: pada run 25 Sep Jev
menjawab `short` untuk kandidat yang `bar < 720`; keputusannya tetap `flat`, dan itu tercetak.
Catatan jujur: kode sekarang membuang kandidat itu **sebelum** model ditanya
(`tools/direction.py:205`, `:372`), jadi batasnya tetap benar tapi contohnya tidak bisa
direproduksi dari clone hari ini
([[01-Agent/A3 - One-Way Gates]]; [[01-Agent/01 - Asset Classes and Seats]] §5). Contoh kedua:
`security_gate` 5/5 kandidat membalas,
4 `OK` + 1 `UNMEASURED`, dan yang `UNMEASURED` **tidak** dihitung bersih (§F).

Yang diuji dan justru menjadi alasan halaman ini ada: aturan arah diuji apa adanya, lalu diuji lagi
dengan gerbang dicabut, lalu diuji dengan **arah dibalik** — tiga pertanyaan yang satu manusia
kemungkinan besar tidak akan diajukan sendiri karena semuanya merusak cerita. Hasilnya: net rugi
**12/12**, dan dibalik tetap kalah (−39,2 … −12,1 bps) (§F). Halaman hasilnya menulis eksplisit:
"jangan panggil ini walk-forward fitted" — tidak ada parameter yang dipilih dengan melihat hasil
([[06-Results/04 - Negative Results]] §5).

## Batas dan mode gagal

- **Yang menulis aturan boleh jadi sumber kebocoran.** Gerbang satu-arah menahan siapa yang
  **membuka** posisi, bukan siapa yang **menetapkan ambang**. Empat ambang universe kami masih
  "diputuskan, bukan diukur" (§E) dan wajib diuji terhadap hasil ([[GAP2 - Uji Setiap Veto Terhadap Hasil]]).
- **Disiplin bukan bukti.** Registry kosong karena aturan, dan itu bisa dibaca juri sebagai produk
  yang belum jadi — padahal kalimat yang benar adalah "kami menolak 100 % sinyal arah pada aset
  dalam" (§F). Jangan menjual penolakan sebagai kecerdasan.
- **Aturan yang terlalu ketat juga membunuh sinyal sungguhan.** Kalau semua gerbang menolak, `E`
  tidak akan pernah terukur; karena itu jalur penguji ambang harus dijalankan, bukan cuma jalur veto.
- **Rekor yang benar tidak membuat prediksi benar.** Anchor membuktikan urutan, bukan akurasi
  ([[Concepts/Anchored Before Outcome]]).
- **Godaan pivot paling besar tepat sesudah hasil buruk.** Itu saat aturan diuji, dan satu-satunya
  jawaban yang sah adalah data baru, bukan kata sifat baru ([[EV5 - Reproduksibilitas dan Pra-Registrasi]]).

## Tingkat bukti

`T3` untuk perilaku gerbang (teruji: keputusan model dibatalkan aturan, `UNMEASURED` tidak dianggap
bersih, ambiguitas tidak dipilih yang enak) · `T1` untuk klaim umum "aturan mengalahkan intuisi"
(praktik, tidak kami ukur sebagai penyumbang return) · untuk klaim "gerbang kami meningkatkan
hasil": **tidak diuji dan mungkin tidak bisa diuji** dengan `n = 2`; yang diuji adalah bahwa gerbang
menolak, dan penolakan itu tercatat.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "agen tidak boleh menaikkan keputusan yang ditolak gerbang; aturan ditulis sebelum
  hasil; dan contoh terukur kami: model bilang short, sistem bilang flat, dan itu masih bisa dibaca
  orang sampai sekarang."
- **Dilarang:** "fabius punya disiplin yang menguntungkan" · "AI tidak emosional jadi lebih baik" ·
  "karena killSwitch, risiko kami nol".

**Terkait:** [[Concepts/One-Way Gate]] · [[01-Agent/A3 - One-Way Gates]] · [[Concepts/Anchored Before Outcome]] ·
[[FD5 - Expectancy Bukan Win Rate]] · [[EV5 - Reproduksibilitas dan Pra-Registrasi]] ·
[[10-Submissions/01 - Claims Cheat Sheet]] · [[PL4 - Memutuskan]]
