# /verify: design brief (4 Okt 2026)

Kontrak untuk `web/src/app/verify/`. Sistem visual sama dengan landing (`docs/design/landing.md`, vault TL23 - Sistem Visual FE).

## Proses yang diwakili

Pemeriksaan publik satu (bot, bar), tanpa kunci, dibaca live: ledger publik (GitHub raw) + SignalAnchor (chain 97). Satu kode dengan alat MCP
`fabius_verify` (`web/src/lib/verify.ts`).

```
tick ledger (id sinyal yang diputuskan) -> komit di SignalAnchor (akar Merkle, jam blok) -> isi dibuka (event Revealed: aset, aksi, bobot, harga, salt)
-> dihitung ulang (leaf = keccak(abi.encode(Signal, salt)); id = keccak(abi.encode(Signal)) ada di tick) -> vonis
```

## Objek fisik + gerak

- **Empat stasiun** pada satu rel (sama dengan section 01 landing), kiri ke kanan: TICK -> KOMIT -> DIBUKA -> DIHITUNG ULANG. Tiap stasiun = panel kaca
  yang menyala ketika pemeriksaannya selesai (berurutan, pegas). Stasiun yang gagal = retak merah.
- **Tiap sinyal = satu blok** (`IsoCube`): tersegel (indigo) di stasiun KOMIT, terbuka (putih) di DIBUKA, bercahaya + centang di DIHITUNG ULANG bila leaf
  dan id cocok. Bot diam (akar nol) = satu blok kaca bening "tidak ada sinyal hari ini, tetap dikomit".
- **Vonis** = kubus besar di ujung rel: putih bercahaya (SAH), indigo (tersegel, belum dibuka), merah retak (ALARM), lavender bergembok (sebelum kunci),
  violet bernapas (menunggu komit).

## Data dalam geometri

Jumlah blok = jumlah sinyal di tick; blok yang tidak cocok tampil merah di stasiun tempat ia gagal. Angka (lag jam, blok, tx) mono di bawah tiap stasiun,
dengan tautan BscScan.

## Interaksi

Pilih bot (bot berjam maju) + tanggal bar (bawaan: bar terakhir yang di-tick), tombol Periksa. URL bisa dibagikan: `/verify?bot=B3-CARRY&bar=2026-10-02`.
Sel kalender di landing yang sudah dikomit menaut ke sini.

## Batas kejujuran

Vonis ini memeriksa BUKTI (sinyal ada sebelum hasilnya dan tidak diubah), bukan kinerja. Tidak ada angka untung. Gagal baca chain/GitHub = pesan galat
yang terlihat, bukan vonis. "Periksa sendiri" menampilkan perintah Python + alamat MCP.
