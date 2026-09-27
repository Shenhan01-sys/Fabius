---
tags: [perkakas, "TL1"]
---

# TL1 - judge.py

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/judge.py`, `06-Results/03 - Not Yet Proven.md` #13

**Ringkas:** penilai LLM yang **boleh dicabut**. Defaultnya `none` (gerbang deterministik); kalau
dinyalakan, ia hanya boleh mengurangi ([[01-Agent/A3 - One-Way Gates]]).

**Poin kunci:**
- Rantai provider: Jev/Typesafe System-One → cadangan OpenAI-compatible → `abstain`.
- `ask_jev(state, questions)` menerima pertanyaan **dari pemanggil**. Tanpa ini, `direction.py`
  menyiapkan `side_<SYM>` tapi `judge()` mengirim pertanyaan bakunya sendiri → kolom `model` kosong
  **sambil mencetak `ok=True`** (bug nyata 25 Sep: klaim terlihat seperti sudah memanggil model).
- Pertanyaan bertipe `noul` (bahaya) dipakai **satu arah**: veto boleh membatalkan, tidak pernah
  membuka. Output mentah disimpan biar keputusan bisa direproduksi tanpa model.
- Biaya: router promo terukur $0; jalur resmi $0,042/MTok masuk, keluar gratis — angka pihak
  ketiga, bukan harga yang kami janjikan.
- Belum terbukti: kalibrasi penilai (apakah vetonya memprediksi hasil). Diukur sebagai
  `06-Results/03` #13, statusnya masih terbuka.

## Kandidat pengganti / pendamping: Laya (System-One open-source)

Builder menaruh catatan di `vault/11-Notes/Laya-LLM.txt` (27 Sep): **Laya** (Convai Innovations, Apache-2.0) adalah tandingan open-source Jev dengan kontrak yang sama - `choice` / `score` / `noul` + probabilitas, encoder (bukan decoder), klaim ~33 ms per pertanyaan di T4 dan akurasi typed-decision 76,6 % vs Jev 72,7 %.

Yang membuat ini relevan untuk Fabius: `judge.py` sudah berbentuk adapter dengan **satu** kontrak internal (`ask_jev(state, questions)` -> jawaban bertipe). Menukar Jev ke Laya berarti menukar URL + payload, bukan mengubah gerbang - dan gerbang tetap satu arah ([[01-Agent/A3 - One-Way Gates]]), jadi kalau modelnya berganti, klaim kami tidak ikut bergeser.

Yang masih harus dibuktikan sebelum nama apa pun masuk kalimat publik:
- **Kontrol negatif wajib.** Kami sudah punya presedennya di proyek ini dan di Lencana: penilai yang tidak bisa menjatuhkan tidak sedang menilai. Ukur Laya dan Jev dengan fixture yang sama (state nyata vs state kosong/berisi sampah) dan cetak dua-duanya. Klaim akurasi di atas datang dari checkpoint yang di-fine-tune; nol-shot jauh lebih rendah (catatan builder sendiri bilang demikian) - dan kami tidak punya fine-tune untuk bahasa kami.
- **Jalur host mana.** `laya-mlx` (repo yang dikirimi builder) = runtime MLX native, **Apple saja** - tidak berjalan di mesin Windows ini; `pip install laya` resmi butuh `transformers` + bobot ~0,7 GB dari Hugging Face (torch sudah ada di mesin ini). Menjalankan paket pihak ketiga dari PyPI/GitHub bukan keputusan teknis sepele: itu kode yang jalan dengan akses ke `.agent.env` dan `.jev.env` kita. Putuskan sadar, atau pakai endpoint pihak ketiga tanpa memasang kodenya.
- Belum ada satu pun angka Laya yang kuukur di proyek ini. *(belum diukur)*

**Terkait:** [[04-Tools/TL2 - direction]] · [[Concepts/One-Way Gate]] · [[11-Notes/Laya-LLM]]
