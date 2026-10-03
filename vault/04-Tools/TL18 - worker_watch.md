---
tags: [perkakas, "TL18"]
---

# TL18 - worker_watch (penjaga luar worker)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/worker_watch.py` · uji `engine/tests/test_worker_watch.py` + `test_signal_commit.AnvilEndToEndTests.test_external_watch_reads_the_same_chain_state`

**Ringkas:** worker Railway yang MATI tidak bisa mengirim alert tentang dirinya sendiri. Alat ini adalah pemeriksa dari luar. Rantai GitHub `paper-ledger.yml`
menjalankannya tiap putaran sesudah tick hari itu beres. Ia membaca chain 97 tanpa kunci: tick resmi terakhir tiap bot sudah dikomit ke SignalAnchor dan isinya
sudah diungkap?

**Poin kunci:**
- Status: OK · SEBELUM KUNCI · MENUNGGU (tick < 30 menit) · ALARM ("WORKER DIAM" = tick >= 30 menit tanpa komit; "UNGKAP TERTAHAN" = komit >= 30 menit
  tetapi ungkap belum lengkap). Kode keluar 0 / 1 (ALARM) / 2 (MENUNGGU) / 3 (TAK TERBACA).
- Hanya stdlib (rantai GitHub tidak memasang pip): JSON-RPC lewat urllib, ABI lewat `engine/chain.py`. Uji anvil membuktikan hasil bacanya SAMA dengan pembaca
  worker (eth-abi) pada komit sungguhan.
- ALARM = `::error::` di run + Telegram bila secrets `ALERT_TELEGRAM_TOKEN` / `ALERT_TELEGRAM_CHAT` dipasang di GitHub; rantai ledger tetap jalan.

**Ringkasan harian (P112, 3 Okt):** `--ringkasan` mengirim satu pesan "SEMUA BERES" per bar bila semua bot OK. Tidak datangnya pesan itu sendiri adalah tanda untuk diperiksa (detak untuk manusia).

**Yang ia TOLAK lakukan:** menuduh worker mati karena chain tak terbaca atau karena dirinya sendiri crash (keluar 3, bukan 1); menghentikan rantai ledger; memakai kunci.

**Terkait:** [[TL11 - komit sinyal M3]] · [[TL9 - ledger paper maju]] · [[07-Testing/T8 - Semantik Kegagalan Operator]] SK-R5/SK-W24/SK-W25
