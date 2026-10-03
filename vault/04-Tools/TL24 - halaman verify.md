---
tags: [perkakas, "TL24", fe]
---

# TL24 - halaman /verify (pemeriksaan publik di peramban)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** brief `docs/design/verify.md` · halaman `web/src/app/verify/page.tsx` + `web/src/components/verify/VerifyView.tsx` · API
`web/src/app/api/verify/route.ts` · logika bersama `web/src/lib/verify.ts` (dipakai juga alat MCP `fabius_verify` / `fabius_signals`, [[TL20 - server MCP]])

**Ringkas:** versi manusia dari `fabius_verify`. Pilih bot (bot berjam maju) + hari bar; halaman memanggil `/api/verify`, yang membaca ledger publik
(GitHub raw) + SignalAnchor chain 97 SAAT ITU, menyusun ulang leaf + id tiap sinyal dari isinya di chain, dan mencocokkannya dengan tick ledger. Tanpa
kunci, tanpa gas. URL bisa dibagikan: `/verify?bot=B3-CARRY&bar=2026-10-02`; sel kalender landing yang sudah dikomit (tersegel/SAH) menaut ke sini.

**Bentuk (FE Doctrine, sistem [[TL23 - Sistem Visual FE]]):** empat stasiun pada satu rel (01 tick ledger -> 02 dikomit di chain -> 03 dibuka -> 04 dihitung
ulang), tiap stasiun menyala berurutan saat hasilnya ada; tiap sinyal = satu blok; vonis = kubus besar (putih bercahaya SAH, indigo tersegel, merah
ALARM/tidak dikomit, lavender bergembok sebelum kunci, violet bernapas menunggu komit). Saat membaca chain: satu blok tersegel berjalan di rel.

**Vonis yang mungkin:** SAH · SEALED_NOT_YET_REVEALED · ALARM (masalah ditulis apa adanya) · NO_TICK · BEFORE_LOCK · BAR_NOT_CLOSED · AWAITING_COMMIT ·
NOT_COMMITTED. Gagal baca chain/GitHub = HTTP 503 + pesan "bukan vonis" (T8); input salah = 400.

**Yang ia TOLAK lakukan:** menampilkan angka untung; memberi vonis saat sumber tak terbaca; memegang kunci apa pun (Vercel tidak punya rahasia).

**Bukti 4 Okt (lokal, `next start` + chain 97 live):** `/api/verify?bot=B3-CARRY&bar=2026-10-02` -> SAH (DOTUSDT EXIT, leaf ✓, id ✓); B1-TREND 2026-10-02 ->
SAH (akar nol, 0/0); B1-TREND 2026-10-01 -> BEFORE_LOCK; tanpa `bar` -> bar terakhir (SAH); bot asing / `2026-02-30` -> 400. Tangkapan layar desktop +
lebar ponsel di peramban waktu-nyata: empat stasiun menyala, tabel sinyal, vonis "Verified"; satu bug tata letak (panel `pre` melebar di ponsel)
diperbaiki dengan `min-w-0`.

**Terkait:** [[TL19 - web landing]] · [[TL20 - server MCP]] · [[TL14 - verify_signals]] · [[TL23 - Sistem Visual FE]]
