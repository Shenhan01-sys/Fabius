---
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
