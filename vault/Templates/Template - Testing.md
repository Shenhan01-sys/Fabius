---
tags: [template]
---

# Template - Testing

> Satu halaman per perintah uji. Ini rumah resmi angka: halaman lain mengutip ke sini.

```markdown
---
tags: [testing, "T<n>"]
---

# T<n> - <nama perintah>

**Bagian dari:** [[07-Testing/00 - Hub Testing]]
**Perintah:** `perintah persis, bisa di-copy`
**Dijalankan:** <tanggal> oleh <siapa/mesin>
**Prasyarat:** <profil foundry / env var / kunci yang TIDAK disimpan di repo>

## Keluaran

```text
<tempel output asli, dipotong seperlunya tapi jangan dirapikan>
```

## Yang dibuktikannya — dan yang tidak

- ✅ <klaim spesifik yang angka ini dukung>
- ❌ <klaim yang tampak didukung tapi tidak — biasanya cakupan, sampel, atau survivorship>

## Kalau gagal

<apa yang dicek duluan, dan jebakan yang sudah pernah memakan waktu di perintah ini>
```

Aturan:
- Output mentah, bukan ringkasan. Kalau tidak bisa menempel output, jangan buat halamannya.
- Satu halaman = satu perintah. Nomor `T<k>` tidak diulang.
- Kolom "yang tidak dibuktikan" wajib ada; tanpanya halaman uji jadi brosur.
