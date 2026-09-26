---
tags: [template]
---

# Template - Part Note

> Satu bagian = satu topik = satu titik di graf. Kedalaman tinggal di sini; hub hanya merutekan.

```markdown
---
tags: [<area>, "<Identity>"]
---

# <Identity> - <Title>

**Bagian dari:** [[<hub>]]
**Sumber:** `path/from/fabius/root.ext:line`  (atau perintah yang mencetak angkanya)

**Ringkas:** 3-6 kalimat. Apa yang ia lakukan, dan apa yang sengaja **tidak** ia lakukan.

**Poin kunci:**
- 4-8 poin konkret. Nama, bukan vibes: signature fungsi, field, guard, nama error, angka.
- Setiap angka: sebut perintah yang mencetaknya. Tidak bisa? Tandai *(belum diukur)*.

**Detail:**
- Yang dibutuhkan pembaca untuk mengubahnya dengan aman: invarian, urutan, batas.
- Jebakan yang sudah pernah memakan waktu, kalau ada — jangan dihapus demi kerapian.

**Terkait:** [[<saudara>]] · [[<concept>]]
```

Aturan:
- `<Identity>` sama dengan prefiks nama berkas (`A2`, `C3`, `D4`, `TL5`, `E1`, `R7`, `T3`, `P1`).
- Sumber non-`.md` = inline code, **jangan** wikilink.
- "Ia tidak menangani X" bernilai lebih dari satu paragraf yang menyinggung ulang kode.
- Bahasa: Indonesia; istilah teknis, ID, dan nama error tetap Inggris.
