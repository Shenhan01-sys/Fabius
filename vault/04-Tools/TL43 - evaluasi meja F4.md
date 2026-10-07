---
tags: [perkakas, "TL43", meja, llm, desk, evaluasi]
---

# TL43 - evaluasi meja F4: nilai agent, bobot bayangan, buku ablasi, usulan evaluator (P156)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/meja_eval.py` (`siklus_bayangan`, `nilai_entri`, `spearman`, `ringkas`, `hitung_bobot`, `berbobot`, `tanpa_sumber`, `langkah_dunia`,
`rapor_teks`, `efek_rapor`, `validasi_usulan`, `ubah_status`, `evaluator_aturan`, `parse_usulan_llm`, `laporan`, `contoh_arsip`, CLI `rapor` / `usulan` /
`contoh` / `kunci`) · gerbang `tools/x402_sinyal.py` (`f4_siapkan`, `f4_gabung`, `v2_siklus`, `meja_loop`, `Gate.eval_simpan`, `Gate.meja_archive`) ·
rumus dipra-registrasi `engine/locks/meja_f4.usulan.json` · tes `engine/tests/test_meja_eval.py` (24) · T8 SK-M13, SK-M36..SK-M42 · epik
[[08-Backlog/11 - Epik Meja AI v2]] §6 + §13 · keputusan [[00-Overview/03 - Decisions]] F-D110 #4 · backlog P156 · meja hidup [[04-Tools/TL36 - meja v2 bot + instrumen]]

## Apa

Loop evaluasi + perbaikan diri meja v2 (epik §6), dibangun dan dijalankan sebagai **BAYANGAN**: tiap siklus 5 menit, SESUDAH siklus hidup selesai,
F4 menilai tiap agent, menghitung bobot agent usulan, menjalankan buku bayangan (ablasi), menulis rapor, dan (harian) menulis usulan. Tidak ada yang
menyentuh keputusan, buku Fabius, prompt agent, Merkle root, atau konfigurasi hidup. Mesin hidup tetap rumus r4 (F-D116): bot dominan = argmax
rata-rata (keyakinan x skor_bot) kursi aktif dengan bobot agent **sama**.

**Teks epik §5-§6 vs mesin hari ini:** V_b = sum W_i k_i s_i,b / sum W_i + lambda x Q_b ditulis sebelum r4. Prior Q_b tidak pernah dirumuskan atau dikunci,
dan mesin hidup tidak memakainya, jadi F4 memakai lambda = 0 (sama dengan mesin hidup); bobot W_i hanya ada di dunia bayangan `bobot`.

## Rumus (dipra-registrasi: `PARAMS_F4`, sha `0x41a1001dfbbfad72710f35bc682c4e129af33b3605285faee9177305f74113ff`, status USULAN)

- **Portofolio bot:** aturan terkunci bot itu (`meja2.arah`) pada SEMUA aset berharga isi siklus itu (universe v2 + aset dipegang), bobot / max(1, gross)
  = `meja2.posisi` pada eksposur 1 tanpa veto. Satu definisi untuk semua agent; tidak bergantung instrumen pilihan agent.
- **Return bot** 5 menit (h = 1) dan 1 jam (h = 12): sum w x (P(t+h) / P(t) - 1) pada harga isi tercatat siklus t dan t+h TEPAT (bukan siklus terdekat).
- **IC** per agent per siklus = Spearman skor_bot (6 bot) vs return 6 bot, peringkat rata-rata untuk seri (B3 di meja perp-only selalu datar = 0).
  **Hit** = bot pilihan termasuk return tertinggi (seri = kena); **acak** = jumlah bot seri tertinggi / 6 (pembanding jujur). **Kalibrasi** = ember
  keyakinan 0-49 / 50-64 / 65-79 / 80-100 -> hit + IC per ember. Agent uji ikut dinilai (bahan kursi), konsensus tetap hanya kursi aktif.
- **Bobot W:** W_i = clamp(1 + 5 x rata-rata IC 1 jam, 0,5, 2) atas siklus yang hasil 1 jamnya sudah ada dalam 288 siklus terakhir; W = 1 bila nilai IC
  kumulatif agent < 288 (pemanasan), IC dalam jendela < 144, atau ada nilai tidak hingga (SK-M37). Dihitung di siklus PERTAMA tiap jam UTC baru (tahan
  siklus bolong), di antaranya tetap.
- **Konsensus berbobot (bayangan):** `meja2.konsensus2` yang sama, dengan keyakinan agent, keyakinan instrumen, dan eksposur dikali
  f_i = W_i x n / sum W -> nilai bot = sum W k s / sum W, eksposur = sum W e / sum W; W = 1 -> f = 1,0 persis (diuji bit demi bit, 300 kasus acak).

## Dunia bayangan (buku slot r4 masing-masing, state hysteresis sendiri)

Langkah tiap dunia = ekor `meja2.siklus2` (konsensus2 -> posisi -> rem rugi harian -> kandidat slot -> migrasi + langkah), pola replay P163:

| dunia | isi |
|---|---|
| `penuh` | W = 1, tidak ada yang dibuang -> **WAJIB SETIA** ke rekaman Fabius tiap siklus (bot, instrumen, target, slot, isi; ekuitas <= 0,01 USDT). Tidak SETIA / siklus bolong -> dicatat + hanya dunia ini disinkron ulang (SK-M40) |
| `bobot` | konsensus dengan W bayangan |
| `tanpa:<agent>` | per kursi aktif: keputusan agent itu dibuang, ambang dari n aktif - 1 |
| `tanpa_sumber:<Y>` | per sumber (binance, binance_ekstra, dexscreener, rugcheck, fomo, berita, candle_harian, ledger_bot): instrumen yang SEMUA faktornya dari Y dibuang, keputusan yang SEMUA faktor utamanya dari Y dibuang, veto agent berfaktor Y dibuang, fitur Y di snapshot dikosongkan (veto keras RugCheck / likuiditas DEX hilang) |

Dunia baru dimulai dari salinan buku + state Fabius pada siklus itu, jadi "kontribusi" = selisih sejak dunia itu mulai.

## Rapor, usulan, sakelar

- **Rapor** per agent tiap jam (bahasa Inggris = bahasa prompt meja, <= 600 karakter): IC, hit vs acak, kalibrasi, kesalahan terbesar; teks + sha DIREKAM,
  TIDAK masuk prompt hidup. `efek_rapor` mengukur sebelum/sesudah (288 vs 288 siklus) bila kelak dinyalakan.
- **Usulan evaluator** (siklus pertama tiap hari UTC; aturan kode, LLM opsional lewat CLI): E1 agent IC 1 jam <= 0 atas >= 144 siklus -> usulan prompt
  "lampirkan rapor"; E2 dunia `tanpa_sumber:Y` unggul >= 0,5 pp atas buku Fabius dalam 24 jam dengan `penuh` SETIA -> usulan fitur "buang Y". Status
  hanya `usulan -> bayangan -> lulus/gagal -> siap_kunci`; kriteria lulus wajib ditulis saat dibuat (sha atas usulan + kriteria), bayangan >= 288 siklus,
  usulan prompt butuh izin biaya builder (panggilan model kedua), `siap_kunci` butuh kata builder + sha kunci versi baru. Tidak ada status hidup (SK-M13);
  jenis / isi lain = ditolak (SK-M38).
- **Sakelar:** `FABIUS_F4=bayangan` di service `fabius-x402` (bawaan MATI; nilai lain termasuk `hidup` = MATI, SK-M41). Gerbang menyalin state + buku
  Fabius SEBELUM siklus (`f4_siapkan`), memulai utas F4 SESUDAH hasil hidup siap (komit tidak menunggu, SK-M39), menggabung hasilnya di awal siklus
  berikutnya hanya bila v2 siklus itu masuk buku hidup (`f4_gabung`, SK-M42), dan merekam `/data/meja/evaluasi/<tgl>.jsonl` (tidak masuk Merkle root:
  semuanya dihitung ulang dari rekaman yang dikomit + harga isi). `GET /desk/archive/<tgl>` kini juga membawa `agent_records` (rekaman agent apa adanya,
  ber-hash), `evaluation`, dan `data_health` (kesehatan sumber F1 per snapshot); tanpa akses anggota dipotong 24 jam seperti rekaman lain (P165).
  `tools/meja_eval.py` ikut arsip `tools/railway_up.py` + `COPY` di `railway/Dockerfile`: tanpa itu gerbang produksi hanya akan mencatat
  `f4 bayangan tidak disiapkan: ModuleNotFoundError` (ditangkap `engine/tests/test_deploy_files.py` lewat gerbang T8 `--run` sebelum commit).

## Perintah (builder)

```
# 1. sesudah push + deploy gerbang (python -X utf8 tools/railway_up.py): nyalakan bayangan (redeploy)
railway variable set FABIUS_F4=bayangan --service fabius-x402
#    log mulai harus mencetak: "evaluasi meja F4 (P156): BAYANGAN (FABIUS_F4=bayangan) | params 0x41a1001dfbbfad72 | kunci USULAN"
# 2. rapor harian per agent + per sumber + ablasi (3 hari berturut = kriteria F4)
python -X utf8 tools/meja_eval.py rapor --dari 2026-10-08 --sampai 2026-10-10 [--token <token Privy anggota>]
#    hari sebelum F4 menyala: nilai per agent dihitung ulang dari candle harian Binance Vision (ablasi hanya dari bayangan hidup);
#    butuh gerbang versi P156 (arsip membawa agent_records dari berkas rekaman lama); jalur ini diuji dengan pasar palsu, BELUM dengan Vision sungguhan
python -X utf8 tools/meja_eval.py rapor --dari 2026-10-05 --sampai 2026-10-07 --vision
# 3. usulan evaluator dari arsip (opsional model sungguhan: --model <slug>); tidak menulis apa pun yang hidup
python -X utf8 tools/meja_eval.py usulan --dari 2026-10-10 --sampai 2026-10-10
# 4. kunci rumus (KATA BUILDER; sha harus sama dengan berkas usulan)
python -X utf8 tools/meja_eval.py kunci --tulis --catatan "builder: <kata> <tanggal>"
# luring / demo: arsip SINTETIS dari meja hidup asli + pasar dan model palsu
python -X utf8 tools/meja_eval.py contoh --keluar f4-contoh.json && python -X utf8 tools/meja_eval.py rapor --berkas f4-contoh.json
```

## Batas yang dicatat jujur

- **Ablasi sumber = atribusi sitasi**, bukan kontrafaktual "agent tidak pernah melihat Y" (itu butuh panggilan model kedua per agent per sumber per
  siklus). Keputusan yang menyitasi Y bersama sumber lain tetap dipakai.
- IC atas 6 bot per siklus berderau; horizon 1 jam saling tumpang 12 siklus, jadi n efektif lebih kecil dari jumlah siklus. Bobot W hanya bayangan.
- Portofolio bot = aturan pada seluruh universe meja, bukan pada instrumen pilihan agent (definisi tunggal yang bisa dibandingkan antar agent).
- Kalibrasi diukur sebagai hit per ember keyakinan; pembanding hit bukan 50 % melainkan `acak`.
- SETIA bergantung pada urutan penjumlahan float yang sama dengan mesin hidup (rekaman tidak menyimpan urutan jawaban); selisih apa pun tertangkap
  `setia: false` dan dicatat, tidak disembunyikan. Batas cache candle harian (1 jam) di sekitar 00:00 UTC bisa memberi satu siklus tidak SETIA.
- Bayangan rapor-di-prompt dan usulan prompt butuh panggilan model tambahan: belum dijalankan (izin biaya builder).
- Durasi satu siklus F4 terukur hanya pada pasar SINTETIS 62 aset / 5 agent / 15 dunia di container sesi (median 63 ms, maks 117 ms); angka gerbang
  produksi belum ada.

**Terkait:** [[08-Backlog/11 - Epik Meja AI v2]] · [[04-Tools/TL36 - meja v2 bot + instrumen]] · [[04-Tools/TL35 - data meja v2]] ·
[[04-Tools/TL34 - meja AI 5 menit]] · [[07-Testing/T8 - Semantik Kegagalan Operator]]
