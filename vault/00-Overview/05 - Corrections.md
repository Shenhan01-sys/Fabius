---
tags: [overview, "O5"]
---

# 05 - Corrections

**Bagian dari:** [[00-Overview/00 - Hub Overview]]
**Sumber:** keluaran perintah, bukan perasaan. Kolom terakhir = cara mereproduksinya.

**Ringkas:** apa yang kami nyatakan, yang ternyata salah, dan apa yang membuktikannya. Dikumpulkan
di satu tempat supaya "sudah clear?" tidak pernah lagi dijawab dari ingatan.

| tanggal | yang kami tulis | yang sebenarnya | bagaimana ketahuan |
|---|---|---|---|
| 25 Sep | "cron GitHub tidak dipersenjatai" (berdasarkan `GET /schedule` 404) | cron **hidup**, cuma tidak disiplin: `state=active` dan Actions mengirim snapshot sendiri beberapa menit setelah kalimat itu ditulis | riwayat jalanan (`gh run list`), bukan satu respons |
| 25 Sep | "settlement x402 terbukti di fork 97/56, tinggal pakai" | perintah fork-nya menunjuk RPC yang **sudah pensiun**; tidak seorang pun (termasuk kami) bisa menjalankan buktinya | aku menjalankan ulang perintah yang tertulis di README sendiri |
| 26 Sep | "16 test lulus di fork" untuk klaim di README | angka itu benar, tapi **dokumen tidak menyebut** bahwa endpoint dokumentasinya mati | sama |
| 27 Sep | "perekam ⑦ mati 24 jam" | lubang nyata ±6 menit. Yang basi adalah **salinan lokalku** (78 commit tertinggal) | `git fetch` + `git log origin` — lihat [[Concepts/Stale Local Copy]] |
| 27 Sep | "calldata kitalah yang salah (nested tuple)" | verdiknya kubangun di atas alat yang menghitung keccak dari string berisi kata `tuple` — bukan bentuk kanonis. Selector kami **benar** | alatnya kuperbaiki (rekursi komponen) lalu dibandingkan ulang |
| 27 Sep | "smart money menang di 30 hari" (sempat terbaca sebagai temuan) | tetap **belum** apa-apa: panel dipilih oleh label yang diberikan setelah sejarahnya terjadi | aturan yang kami tulis sendiri di `06-Results/06` §2 |
| 27 Sep | assertion "biaya round-trip > 400 bps" | salah hitung skala kami (0,6 % = 60 bps); terukur **59 bps** | test gagal → yang dikoreksi tesnya, bukan angkanya |
| 27 Sep | `git add -A` di repo induk (2×) | ikut menelan berkas sesi lain ke commit-ku | `git show --stat`; dipecah ulang, tidak ada yang hilang |

**Detail:** klaim yang ditarik juga meninggalkan jejak di halaman aslinya (banner koreksi), bukan
dihapus senyap — itu bedanya vault dengan brosur.

**Terkait:** [[Conventions]] · [[Concepts/Stale Local Copy]] · [[06-Results/03 - Not Yet Proven]]
