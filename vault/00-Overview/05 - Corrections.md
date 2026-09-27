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
| 27 Sep | "`anchor.py --verify` nol kunci, siapa pun bisa periksa" | **gugur di clone bersih**: `AGENT_ADDRESS` hanya hidup di `.agent.env` yang di-gitignore, jadi perintahnya mati dengan "AGENT_ADDRESS tidak diketahui". Yang kami maksud sebenarnya "terbuka kalau punya salinan kerja kami" | `python -X utf8 _research/probe_clone_paths.py` -> rc=1; sekarang alamat jatuh ke `deployments/97.json` **dan** dicek ke kontrak (`getAgent`/`countByAgent`) |
| 27 Sep | "pipeline kami sudah pernah dijalankan utuh" | sudah, tapi TIDAK sekali pun lewat `judge.py` dengan kunci dari berkas: `ROOT` dirujuk `_key()` tanpa pernah didefinisikan di `tools/judge.py` (bug asli sejak `d79a499`). Tidak pernah kena selama kuncinya ada di environment pemanggil - persis tipe cacat yang hanya keluar di jalur fallback. Ketahuan 27 Sep saat run end-to-end tanpa env | `python -X utf8 -c "import sys;sys.path.insert(0,'tools');import judge"` -> `NameError: ROOT`; sesudah perbaikan: `ROOT = <akar Fabius>` |
| 27 Sep | "kartu agen menunjuk keputusan terbaru" | tunjukannya benar, isinya basi: `docs/decisions/direction-latest.json` hanya ditulis ulang saat `x8004_register.py --card` dijalankan, jadi setelah siklus keputusan baru ia masih berisi FLNCUSDT dari 25 Sep. Pointer yang busuk secara senyap lebih buruk dari pointer yang mati | `direction.py --emit` tidak menyentuhnya; kini disegarkan (TACUSDT flat) dan sisanya dibuat item terbuka P9 |
| 27 Sep | "P1 terhenti karena kekurangan gas" | guard memang menolak, tapi pakai **plafon 1 gwei** sementara testnet live 0,10 gwei: jalur penuh 0,0018 tBNB vs saldo 0,0079 -> dananya cukup. Yang menahan adalah taksiran konservatif, dan itu harus dipilih sadar (top-up atau turunkan plafon), bukan diwarisi | `python -X utf8 _research/read_balances.py`; lalu P1 jalan dan selesai |
| 27 Sep | "perkakas perawatan vault sudah hijau, jadi aman" | dua alatku sendiri merusak dokumen setelah gerbangnya hijau: `sync_vault.py` menelan heading `## Terkait` + `**Sumber:**` di **11 hub** (regex-nya menulis ulang sampai blok dataview), lalu `repair_hub_sections.py` mengangkat 2 gloss sah keluar dari daftar Bagian (aturannya mencari karakter pemisah di mana saja, dan `x·y=k` kebagian). `check_links.py` tetap melaporkan `Broken: 0` sepanjang itu: tautannya valid, **tempatnya** yang pindah | `scripts/hub_shape.py` (baru; 11 hub, 0 masalah) + `scripts/restore_lifted_glosses.py`. Catatan yang tidak enak: commit `08cb049` sendiri sudah cacat, jadi `git checkout` tidak memulihkannya — bentuk harus digate, bukan diasumsikan
| 27 Sep | hipotesis "selisih 17 vs 11 itu karena `--verify` cuma baca `direction-*`" | **dibantah oleh pengukuran**: perluasan cakupan malah menyeret 301 baris kandidat `screen` (termasuk nama token non-ASCII) jadi keluarannya "11/312 cocok". Cakupan dikembalikan; P6b tetap terbuka, sekarang dengan peringatan di keluaran `--verify` | `decisions-20260923.jsonl` isinya kandidat, bukan keputusan |
| 28 Sep | "jalur uji menutup dengan ongkos 20 bps" — dipakai diam-diam oleh `backtest.py`, `ledger.py`, `screen_universe.py`, `smartmoney_score.py`, `flow_test.py` | venue kami sendiri menghasilkan **59 bps**, dan tidak ada artefak yang bilang penggaris mana yang dipakai. `tools/costs.py` jadi satu sumber (default terukur; override tercatat `cli-override`). Deret dihitung ulang: aturan arah tetap **12/12 rugi** (kini **−39,8…−66,9 bps**/trade, gross tidak berubah), ambang gross **118 bps**, dan **satu-satunya "MENANG +1,5 bps" di seri paper menjadi −37,5 bps** → PAPER n=3, WR 0 % | `python -X utf8 tools/costs.py --self-test` · `tools/backtest.py --mom-only` · `tools/ledger.py` · `tools/winlog.py` mencetak `2 decisionHash dengan net berbeda` → [[06-Results/04 - Negative Results]] §5b · [[06-Results/07 - Matured Outcomes]] |

**Detail:** klaim yang ditarik juga meninggalkan jejak di halaman aslinya (banner koreksi), bukan
dihapus senyap — itu bedanya vault dengan brosur.

**Terkait:** [[Conventions]] · [[Concepts/Stale Local Copy]] · [[06-Results/03 - Not Yet Proven]]
