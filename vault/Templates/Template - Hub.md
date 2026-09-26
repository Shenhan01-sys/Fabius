---
tags: [template]
---

# Template - Hub

> Satu hub per folder modul. Dia **peta**, bukan esai: beberapa kalimat tentang isi folder, lalu
> daftar setiap bagian dengan satu baris penjelasan.

````markdown
---
tags: [<area>, hub]
---

# <NN> - <Title>

<2-5 kalimat padat: lapisan ini apa, apa yang BUKAN dia, dan satu hal yang tidak boleh dilewatkan
pembaca baru.>

## Bagian

- [[<Prefix>1 - <Judul>]] — <isinya apa>
- [[<Prefix>2 - <Judul>]] — <isinya apa>

## Terkait

- [[<hub lain>]] · [[Quick-Reference]]
````

```dataview
LIST FROM #<area> SORT file.name ASC
```

Aturan:
- `## Bagian` wajib menyebut **setiap** berkas di folder — berkas yang tidak ada di peta adalah
  berkas yang tidak akan pernah dibaca orang.
- Tiap baris dapat penjelasan, bukan cuma tautan.
- `**Sumber:**` sebuah hub = direktori yang ia dokumentasi, mis. ``tools/``.
- Blok `dataview` di akhir adalah yang menjaga peta tetap jujur saat ada berkas ditambahkan manual.
