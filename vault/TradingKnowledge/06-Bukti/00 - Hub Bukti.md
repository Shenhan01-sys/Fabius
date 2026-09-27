---
tags: [tk-bukti, hub]
---

# 00 - Hub Bukti

**Sumber:** `vault/TradingKnowledge/06-Bukti/`

Aturan yang membuat folder `03-Sinyal/` bukan kumpulan mitos trading yang dirapikan. Satu
pertanyaan mengikat semuanya: **siapa yang menguji, pada data apa, dan bolehkah kamu mengubah
aturannya setelah melihat hasilnya?** Halaman di folder ini tidak menambah pengetahuan trading
baru — ia memasang rem pada pengetahuan yang sudah ada.

Konsep lintas-lapis yang dipakai di sini sudah ada di `Concepts/` dan **tidak diduplikasi**:
[[Concepts/One-Way Gate]], [[Concepts/Unmeasured Is Not Clean]], [[Concepts/Lookahead Bound]],
[[Concepts/Point-in-Time vs Retro-updatable]], [[Concepts/Anchored Before Outcome]].

## Bagian

- [[EV1 - Tingkat Bukti]] — skala `T0`–`T3` + flag `NEGATIF`/`TERCEMAR`; dan aturan bahwa tidak ada
  catatan di subtree ini yang bisa menaikkan bukti produk — hanya run
- [[EV2 - Jebakan Backtest]] — lookahead, survivorship, revisi data, asumsi fill, null yang salah;
  tiap jebakan dengan cara mendeteksinya **sebelum** hasil
- [[EV3 - Signifikansi dan Multiple Testing]] — satu tes per token, BH α 0,10, `n ≥ 20` non-overlap,
  dan kelemahan p-value yang kami warisi lalu kami tulis, bukan kami poles
- [[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]] — dua kelas data, dan konsekuensi
  bahwa beberapa metode tidak akan pernah bisa diuji surut di repo ini
- [[EV5 - Reproduksibilitas dan Pra-Registrasi]] — sha256, timestamp pihak ketiga, hipotesis sebelum
  hasil; "kalau halaman dan run berbeda, run yang menang"
- [[EV6 - Kalibrasi Ambang Terhadap Hasil]] — cara menguji ambang yang lahir sebagai keputusan, dan
  kapan mencabutnya

## Terkait

- [[00 - Hub Trading Knowledge]] · [[Fakta Terukur]] §E/§F/§H · [[Aturan Subtree]]
- [[06-Results/00 - Hub Results]] — rumah angka yang sebenarnya ·
  [[06-Results/05 - Pre-registration Flow]] · [[06-Results/06 - Pre-registration Horizon]]
- [[10-Submissions/01 - Claims Cheat Sheet]] — kalimat yang dilarang, beserta penggantinya

```dataview
LIST FROM #tk-bukti SORT file.name ASC
```
