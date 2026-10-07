"""deckgen: bangun deck PPTX dari satu berkas md = satu slide (vault/13-SubmmisionsDocs).

Alur: `mdparse` membaca berkas slide + berkas Design Style -> `facts` mengisi angka dari snapshot yang dicetak mesin
-> `layouts` menggambar tiap slide dengan bentuk asli PowerPoint (bukan gambar) -> `build` menyimpan .pptx.
"""

__all__ = ["theme", "xmlfx", "draw", "iso", "measure", "markup", "facts", "mdparse", "layouts", "build"]
