"""Laporkan angka di catatan TradingKnowledge yang tidak ada di lembar fakta.

Kenapa ini ada: `tk_check.py` menjaga BENTUK, `check_links.py` menjaga TAUTAN — keduanya buta
terhadap angka. Aturan subtree ini bilang "satu-satunya sumber angka tentang produk adalah
[[Fakta Terukur]]", dan aturan yang tidak diperiksa akan dilanggar tanpa ada yang tahu (sudah
terjadi pada audit pertama: angka yang tidak dicetak perintah apa pun masuk ke tiga catatan).

Ini **bukan** gerbang: ia melapor. Angka konstanta rumus (14, 2,5, 0,618) sah dan tidak bisa
dibedakan secara mekanis dari angka produk yang karangan — jadi yang keluar adalah daftar kandidat
untuk dibaca manusia, plus satu lintasan keras: angka > 100 yang muncul di baris yang menyebut
Fabius/kami/rekaman dan tidak ada di lembar fakta.

    python -X utf8 vault/scripts/tk_facts.py            # kandidat per berkas
    python -X utf8 vault/scripts/tk_facts.py --strict   # exit 1 kalau ada kandidat
"""
import glob
import io
import os
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TK = os.path.join(VAULT, "TradingKnowledge")
SHEET = os.path.join(TK, "Fakta Terukur.md")

# Kata yang membuat sebuah baris "tentang produk": angka di baris seperti ini wajib bersumber.
PRODUK = re.compile(r"(?i)\b(fabius|kami|perekam|rekaman|universe|wallet-flow|dune|gmgn|aster|"
                    r"hyperliquid|geckoterminal|goplus|gdelt|maker|snapshot|tools/|contracts/|"
                    r"decisions/|baris|kolam|kohor|anchor|vault eksekusi|lapangan)\b")
# Angka harus berdiri sendiri: `x402` (nama protokol) dan `EIP-712` bukan klaim jumlah, tapi `\d`
# biasa akan mengambil "402"-nya dan melaporkan hantu.
NUM = re.compile(r"(?<![A-Za-z0-9_])\d[\d.,]*\d|(?<![A-Za-z0-9_])\d(?![A-Za-z0-9_])")
# Konstanta rumus/kecil: tidak pernah kami klaim sebagai hasil ukur produk.
SMALL = set(range(0, 201)) | {618, 705, 786, 1272, 1618, 2360, 3820, 5000, 1000, 2000}
TAHUN = set(range(1900, 2101))
# Kode skema/wire yang bukan jumlah apa pun (0x…, `code -1130`) tidak ikut dilaporkan.
HEX = re.compile(r"0x[0-9a-fA-F]{2,}")


def norm(tok):
    """'51.260' -> 51260 · '0,10' -> '0.10' · '9.599' -> 9599 (pemisah ribu Indonesia)."""
    t = tok.replace(",", ".")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", t):                  # 51.260 / 9.599
        return t.replace(".", "")
    return t


FENCE = re.compile(r"```.*?```", re.S)
INLINE = re.compile(r"`[^`\n]*`")


def allowed_from_sheet():
    """Semua angka yang tercetak di lembar fakta - termasuk yang di dalam `inline code`.

    Versi pertama menghapus inline code dari lembar fakta (warisan aturan "kode = contoh sintaks"
    dari check_links) dan akibatnya 24 dari 44 temuan adalah `NEED_BARS=2400` yang memang ada di
    sana, hanya tertulis dalam backtick. Lembar fakta adalah sumber angka, jadi di sana backtick
    tidak membuang apa pun.
    """
    text = io.open(SHEET, encoding="utf-8").read().replace("`", "")
    out = set()
    for m in NUM.finditer(text):
        out.add(norm(m.group(0)))
    return out


def claim_lines(text):
    """Baris klaim per nomor baris: blok kode dan `inline code` dikosongkan, nomornya dijaga.

    Angka di dalam backtick bukan klaim (konstanta kode, `code -1130`, `429` HTTP, contoh perintah
    `--days 300`) - sama seperti aturan check_links terhadap inline code. Yang tinggal hanya angka
    yang benar-benar ditulis sebagai pernyataan.
    """
    text = FENCE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    text = INLINE.sub(lambda m: " " * len(m.group(0)), text)
    return text.split("\n")


def main():
    if not os.path.isfile(SHEET):
        sys.exit(f"tidak ada {SHEET}")
    ok = allowed_from_sheet()
    strict = "--strict" in sys.argv
    files = sorted(glob.glob(os.path.join(TK, "**", "*.md"), recursive=True))
    total = 0
    for p in files:
        rel = os.path.relpath(p, TK).replace(os.sep, "/")
        if rel == "Fakta Terukur.md" or rel.startswith("Templates/") or "Hub" in os.path.basename(rel):
            continue
        hits = []
        lines = claim_lines(io.open(p, encoding="utf-8").read())
        for i, line in enumerate(lines, 1):
            if not PRODUK.search(line):
                continue
            probe = HEX.sub("", line)
            for m in NUM.finditer(probe):
                v = norm(m.group(0))
                try:
                    f = float(v)
                except ValueError:
                    continue
                if f in SMALL or f in TAHUN or v in ok or m.group(0) in ok:
                    continue
                hits.append((i, m.group(0), line.strip()[:96]))
        if hits:
            total += len(hits)
            print(f"\n{rel}")
            seen = set()
            for i, tok, ln in hits:
                if (i, tok) in seen:
                    continue
                seen.add((i, tok))
                print(f"  :{i}  {tok:>12}  {ln}")
    print(f"\n{len(files)} berkas diperiksa · {total} angka kandidat tanpa sumber di lembar fakta.")
    print("Bukan vonis: konstanta rumus dan batas yang dipilih sengaja juga masuk daftar ini.")
    sys.exit(1 if (strict and total) else 0)


if __name__ == "__main__":
    main()
