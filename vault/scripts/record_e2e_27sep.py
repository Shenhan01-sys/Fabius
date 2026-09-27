"""Catat hasil jalannya Fabius end-to-end 27 Sep: bug yang ketahuan, pointer yang basi, dan Laya.

Sekali-jalan; pola wajib ketemu tepat satu kali.
"""
import io
import os
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isdir(os.path.join(VAULT, "00-Overview")):
    sys.exit(f"VAULT bukan folder vault: {VAULT}")

E = []

# 1. Corrections: dua temuan dari run end-to-end
E.append(("00-Overview/05 - Corrections.md",
 "| 27 Sep | \"P1 terhenti karena kekurangan gas\"",
 "| 27 Sep | \"pipeline kami sudah pernah dijalankan utuh\" | sudah, tapi TIDAK sekali pun lewat "
 "`judge.py` dengan kunci dari berkas: `ROOT` dirujuk `_key()` tanpa pernah didefinisikan di "
 "`tools/judge.py` (bug asli sejak `d79a499`). Tidak pernah kena selama kuncinya ada di "
 "environment pemanggil - persis tipe cacat yang hanya keluar di jalur fallback. Ketahuan 27 Sep "
 "saat run end-to-end tanpa env | `python -X utf8 -c \"import sys;sys.path.insert(0,'tools');"
 "import judge\"` -> `NameError: ROOT`; sesudah perbaikan: `ROOT = <akar Fabius>` |\n"
 "| 27 Sep | \"kartu agen menunjuk keputusan terbaru\" | tunjukannya benar, isinya basi: "
 "`docs/decisions/direction-latest.json` hanya ditulis ulang saat `x8004_register.py --card` "
 "dijalankan, jadi setelah siklus keputusan baru ia masih berisi FLNCUSDT dari 25 Sep. Pointer "
 "yang busuk secara senyap lebih buruk dari pointer yang mati | `direction.py --emit` tidak "
 "menyentuhnya; kini disegarkan (TACUSDT flat) dan sisanya dibuat item terbuka P9 |\n"
 "| 27 Sep | \"P1 terhenti karena kekurangan gas\""))

# 2. TL1 judge: Laya sebagai kandidat, dengan syarat kontrol negatif
E.append(("04-Tools/TL1 - judge.md",
 "**Terkait:** [[04-Tools/TL2 - direction]] · [[Concepts/One-Way Gate]]",
 "## Kandidat pengganti / pendamping: Laya (System-One open-source)\n\n"
 "Builder menaruh catatan di `vault/11-Notes/Laya-LLM.txt` (27 Sep): **Laya** (Convai Innovations, "
 "Apache-2.0) adalah tandingan open-source Jev dengan kontrak yang sama - `choice` / `score` / "
 "`noul` + probabilitas, encoder (bukan decoder), klaim ~33 ms per pertanyaan di T4 dan akurasi "
 "typed-decision 76,6 % vs Jev 72,7 %.\n\n"
 "Yang membuat ini relevan untuk Fabius: `judge.py` sudah berbentuk adapter dengan **satu** "
 "kontrak internal (`ask_jev(state, questions)` -> jawaban bertipe). Menukar Jev ke Laya berarti "
 "menukar URL + payload, bukan mengubah gerbang - dan gerbang tetap satu arah "
 "([[01-Agent/A3 - One-Way Gates]]), jadi kalau modelnya berganti, klaim kami tidak ikut bergeser.\n\n"
 "Yang masih harus dibuktikan sebelum nama apa pun masuk kalimat publik:\n"
 "- **Kontrol negatif wajib.** Kami sudah punya presedennya di proyek ini dan di Lencana: penilai "
 "yang tidak bisa menjatuhkan tidak sedang menilai. Ukur Laya dan Jev dengan fixture yang sama "
 "(state nyata vs state kosong/berisi sampah) dan cetak dua-duanya. Klaim akurasi di atas datang "
 "dari checkpoint yang di-fine-tune; nol-shot jauh lebih rendah (catatan builder sendiri bilang "
 "demikian) - dan kami tidak punya fine-tune untuk bahasa kami.\n"
 "- **Jalur host mana.** `laya-mlx` (repo yang dikirimi builder) = runtime MLX native, **Apple "
 "saja** - tidak berjalan di mesin Windows ini; `pip install laya` resmi butuh `transformers` + "
 "bobot ~0,7 GB dari Hugging Face (torch sudah ada di mesin ini). Menjalankan paket pihak ketiga "
 "dari PyPI/GitHub bukan keputusan teknis sepele: itu kode yang jalan dengan akses ke `.agent.env` "
 "dan `.jev.env` kita. Putuskan sadar, atau pakai endpoint pihak ketiga tanpa memasang kodenya.\n"
 "- Belum ada satu pun angka Laya yang kuukur di proyek ini. *(belum diukur)*\n\n"
 "**Terkait:** [[04-Tools/TL2 - direction]] · [[Concepts/One-Way Gate]] · [[11-Notes/Laya-LLM]]"))

# 3. Backlog: P9 penyegar pointer publik
E.append(("08-Backlog/01 - Backlog.md",
 "| P8 | **Bukti clone bersih**",
 "| P9 | Segarkan `docs/decisions/direction-latest.json` **otomatis** setiap siklus (bukan hanya "
 "saat `x8004_register.py --card`), plus pemeriksaan di CI bahwa tanggal isi <= umur siklus | ⬜ "
 "ketahuan 27 Sep: kartu menunjuk keputusan terbaru, isinya masih 25 Sep | selesai = ada baris di "
 "`01 - Test Commands` yang membuktikannya dari run, bukan dari klaim |\n"
 "| P8 | **Bukti clone bersih**"))

NEW = [("11-Notes/Laya-LLM.md", """---
tags: [inbox, "S-27-laya"]
---

# Laya-LLM — catatan builder

**Bagian dari:** [[11-Notes/00 - Hub Notes]]
**Sumber:** `vault/11-Notes/Laya-LLM.txt` (ditaruh builder 27 Sep 2026; berkas aslinya dibiarkan
apa adanya, halaman ini cuma peta-nya)

**Ringkas:** ekspor percakapan riset tentang **Laya** — model keputusan "System One" open-source
(Convai Innovations, Apache-2.0) yang diajukan builder sebagai saingan Jev: sama-sama menjawab
bertipe (`choice` / `score` / `noul` + probabilitas), encoder ringan (~322–421 M), klaim ~33 ms di
T4 dan 76,6 % pada benchmark typed-decision vs Jev 72,7 %, bisa self-host (`pip install laya`) atau
lewat hosted (Laya Studio, 5 run gratis), dan ada jalur fine-tune di Kaggle T4×2.

**Poin kunci:**
- Yang relevan buat kami: `judge.py` sudah adapter dengan satu kontrak internal, jadi menukar
  penilai tidak menyentuh gerbang satu-arah.
- Yang belum terbukti: apa pun tentang Laya **di proyek ini**. Belum diukur. Kontrol negatif wajib
  sebelum nama itu muncul di satu kalimat publik (aturan yang sama dipakai saat memilih penilai
  di Lencana: penilai yang tidak bisa menjatuhkan tidak sedang menilai).
- `github.com/mizorewww/laya-mlx` = runtime **MLX native (Apple)**: bukan fork resmi Laya dan tidak
  bisa dijalankan di mesin Windows ini. Yang resmi: `github.com/NandhaKishorM/laya`, bobot
  `huggingface.co/convaiinnovations/laya`, PyPI `laya`.
- Memasang paket pihak ketiga = menjalankan kode dengan akses ke `.agent.env`/`.jev.env`. Itu
  keputusan sadar, bukan langkah instalasi.

**Detail rumah tindak lanjutnya:** [[04-Tools/TL1 - judge]] §Kandidat.

**Terkait:** [[04-Tools/TL1 - judge]] · [[01-Agent/A3 - One-Way Gates]]
"""),
 ("11-Notes/00 - Hub Notes.md", """---
tags: [inbox, hub]
---

# 11 - Notes

**Sumber:** `vault/11-Notes/`

Tempat catatan mentah dari builder tinggal — ekspor percakapan, tautan, tangkisan ide. Bedanya
dengan [[09-Inbox/00 - Hub Inbox]]: inbox adalah **jurnal kerja aku**, notes ini adalah **bahan
baku dari kamu**. Isinya tidak kuubah; yang kubuat adalah halaman peta supaya bahan itu ketemu
halaman yang memilikinya, dan supaya tidak ada berkas yang masuk vault tanpa tempat di peta.

## Bagian

- [[Laya-LLM]] — catatan builder tentang Laya (System-One open-source); pemetaannya di
  [[04-Tools/TL1 - judge]]

```dataview
LIST FROM #inbox SORT file.name ASC
```

## Terkait

- [[Index]] · [[09-Inbox/00 - Hub Inbox]] · [[Conventions]]
""")]

bad = []
for rel, old, new in E:
    p = os.path.join(VAULT, rel.replace("/", os.sep))
    t = io.open(p, encoding="utf-8").read()
    if t.count(old) != 1:
        bad.append(f"{rel}: {t.count(old)}x -> {old[:50]!r}")
        continue
    io.open(p, "w", encoding="utf-8", newline="\n").write(t.replace(old, new, 1))
    print("ok  ", rel)

for rel, text in NEW:
    p = os.path.join(VAULT, rel.replace("/", os.sep))
    if os.path.exists(p):
        print("lewat", rel)
        continue
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8", newline="\n").write(text)
    print("tulis", rel)

if bad:
    print("\n".join("!! " + b for b in bad))
    sys.exit(f"{len(bad)} suntingan tidak diterapkan.")
print("\nselesai.")
