"""Gerbang bentuk untuk lapisan TradingKnowledge: bentuk catatan, bukan isinya.

Kenapa perlu alat sendiri: `hub_shape.py` hanya memeriksa hub (`00 - Hub*`), `check_links.py` hanya
memeriksa tautan. Catatan metode yang kehilangan bagian `## Butuh data` atau `## Tingkat bukti`
tetap hijau di keduanya — padahal bagian itulah yang menahan catatan trading dari berubah menjadi
prosa motivasi. Bentuk yang seragam juga yang membuat angka Fabius bisa diaudit: tanpa tabel status
data, "metode ini bisa dipakai" selalu terbaca seperti sudah terbukti.

Dipakai sebagai gerbang: `python -X utf8 vault/scripts/tk_check.py` -> exit non-zero kalau ada
catatan yang bentuknya tidak lengkap. Periksa juga: `check_links.py`, `hub_shape.py`.
"""
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
if not os.path.isdir(TK):
    sys.exit(f"tidak ada {TK}")

METODE = ("## Definisi", "## Cara pakai", "## Butuh data", "## Uji di Fabius",
          "## Batas", "## Tingkat bukti", "## Boleh")
SETUP = ("## Resep", "## Butuh data", "## Uji di Fabius", "## Konfluensi",
         "## Batas", "## Tingkat bukti", "## Boleh")
PENANDA = ("**Ringkas:**", "**Terkait:**", "**Sumber:**")
STATUS = ("ADA-TAPI", "TIDAK-ADA", "MATI-DARI-MESIN-INI", "ADA")
LEVEL = ("T0", "T1", "T2", "T3")
ID_OK = ("PL", "FD", "S", "I", "V", "U", "O", "M", "ST", "QT", "EV", "GAP")
ROOT_OK = {"Aturan Subtree", "Fakta Terukur", "Glossary-TK"}
WIKI_CODE = re.compile(r"\[\[[^\]|#]*\.(?:txt|py|sol|json|md|yml|toml|env)\b")
# Aksara CJK/Hiragana/Katakana/Hangul: vault ini berbahasa Indonesia. Kejadian 27-28 Sep: beberapa
# kalimat menyisipkan aksara Tiongkok di tengah bahasa Indonesia dan tidak ada satu pun pemeriksaan
# yang menegurnya - jadi ini ditegakkan alat, bukan oleh pembacaan ulang yang letih.
CJK = re.compile(r"[぀-ヿ㐀-䶿一-鿿가-힯豈-﫿]")
SPAN = re.compile(r"`[^`]*`")


def role(rel):
    """Bagian mana dari lapisan ini - menentukan bentuk yang dituntut."""
    parts = rel.split("/")
    if len(parts) == 1:
        return "root"
    if parts[0] == "Templates":
        return "template"
    if os.path.basename(rel).startswith("00 - Hub"):
        return "hub"
    return "setup" if parts[0] == "04-Setup" else "metode"


def section(text, head):
    """Isi satu bagian, berhenti di heading `## ` berikutnya.

    `[^\\n]*` dipakai di baris heading, BUKAN `.*`: dengan `re.S` (dibutuhkan badan bagian bisa
    multiline), `.*` melahap seluruh berkas lalu berhenti di `\\n` TERAKHIR - akibatnya "isi"
    bagian nyaris selalu kosong dan setiap catatan dilaporkan tanpa status data. Bug ini keluar
    pada run pertama, bukan pada dokumen.
    """
    m = re.search(r"^" + re.escape(head) + r"[^\n]*\n(.*?)(?=^##\s|\Z)", text, flags=re.M | re.S)
    return m.group(1) if m else None


def check(path):
    rel = os.path.relpath(path, TK).replace(os.sep, "/")
    text = io.open(path, encoding="utf-8").read()
    kind = role(rel)
    bad, warn = [], []
    for i, line in enumerate(text.splitlines(), 1):
        hit = CJK.search(line)
        if hit:
            bad.append(f"aksara di luar Indonesia/Inggris di baris {i}: '{hit.group(0)}' - {line.strip()[:60]}")
        # `|acf|` dan `|net|` adalah nama field yang kami pakai di mana-mana. Di paragraf tidak
        # masalah; di baris tabel setiap pipa memecah sel, dan tidak ada gerbang lain yang melihat
        # itu karena teksnya tetap terbaca sah (perbaikan: scripts/fix_tk_table_pipes.py).
        if line.lstrip().startswith("|"):
            for m in SPAN.finditer(line):
                if re.search(r"(?<!\\)\|", m.group(0)):
                    bad.append(f"baris tabel {i} punya pipa di dalam code span ({m.group(0)[:24]}) - "
                               "tulis `\\|acf\\|`")
    if kind in ("root", "template", "hub"):
        return kind, bad, warn, len(text.splitlines())

    base = os.path.splitext(os.path.basename(rel))[0]
    m = re.match(r"^([A-Z]{1,3})(\d+)\s+-\s+(.+)$", base)
    if not m:
        bad.append(f"nama berkas bukan '<ID><n> - <Judul>.md': {base}")
    else:
        pre, num = m.group(1), m.group(2)
        if pre not in ID_OK:
            bad.append(f"prefix ID {pre} tidak ada di peta ID [[Aturan Subtree]]")
        if f'"{pre}{num}"' not in text.split("\n---\n")[0]:
            bad.append(f"frontmatter tidak membawa identitas \"{pre}{num}\"")

    heads = [h.rstrip() for h in re.findall(r"^## .*", text, flags=re.M)]
    perlu = SETUP if kind == "setup" else METODE
    for want in perlu:
        if not any(h.startswith(want) for h in heads):
            bad.append(f"bagian `{want}` HILANG")

    for pen in PENANDA:
        if pen not in text:
            bad.append(f"penanda `{pen}` HILANG")
    if "**Keluarga:**" not in text and "**Bagian dari:**" not in text:
        bad.append("tidak ada `**Keluarga:**` / `**Bagian dari:**` (catatan yatim di graf)")

    isi = section(text, "## Butuh data")
    if isi is not None and not any(s in isi for s in STATUS):
        bad.append("`## Butuh data` tanpa status enum (ADA / ADA-TAPI / TIDAK-ADA / MATI-DARI-MESIN-INI)")
    isi = section(text, "## Tingkat bukti")
    if isi is not None and not any(re.search(r"\b" + lv + r"\b", isi) for lv in LEVEL):
        bad.append("`## Tingkat bukti` tanpa T0..T3")

    n = len(text.splitlines())
    if n < 40:
        warn.append(f"terlalu pendek untuk disebut metode ({n} baris)")
    if n > 200:
        warn.append(f"terlalu panjang untuk satu catatan ({n} baris) - pecah dua")
    if re.search(r"[A-Za-z]:\\\\", text) or "C:\\" in text:
        bad.append("memuat path absolut Windows (vault harus terbaca di mesin mana pun)")
    for mm in WIKI_CODE.finditer(text):
        bad.append(f"wikilink ke berkas non-md: {mm.group(0)[:40]}…")
    return kind, bad, warn, n


def nearest_hub(path):
    """Hub yang memetakan sebuah catatan: `00 - Hub*` terdekat ke atas (folder keluarga ikut induknya)."""
    d = os.path.dirname(path)
    while os.path.abspath(d) != os.path.abspath(TK) and os.path.abspath(d).startswith(os.path.abspath(TK)):
        for f in sorted(os.listdir(d)):
            if f.startswith("00 - Hub") and f.endswith(".md"):
                return os.path.join(d, f)
        d = os.path.dirname(d)
    for f in sorted(os.listdir(TK)):
        if f.startswith("00 - Hub") and f.endswith(".md"):
            return os.path.join(TK, f)
    return None


def main():
    files, rusak, peringatan = [], 0, 0
    for cur, dirs, names in os.walk(TK):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        files += [os.path.join(cur, f) for f in names if f.endswith(".md")]
    hub_cache = {}
    for p in sorted(files):
        kind, bad, warn, n = check(p)
        rel = os.path.relpath(p, TK).replace(os.sep, "/")
        if kind == "metode" or kind == "setup":
            h = nearest_hub(p)
            if h is None:
                bad.append("tidak ada hub induk untuk folder ini (peta tidak akan menyebutnya)")
            else:
                if h not in hub_cache:
                    hub_cache[h] = io.open(h, encoding="utf-8").read()
                base = os.path.splitext(os.path.basename(p))[0]
                if base not in hub_cache[h]:
                    bad.append(f"tidak disebut di `## Bagian` {os.path.relpath(h, TK).replace(os.sep, '/')} "
                               "— berkas yang tidak ada di peta tidak akan pernah dibaca orang")
        peringatan += len(warn)
        if bad:
            rusak += 1
        if kind in ("root", "template", "hub") and not bad and not warn:
            continue
        print(f"{'ok  ' if not bad else 'RUSAK'} [{kind:6}] {rel}")
        for b in bad:
            print(f"      - {b}")
        for w in warn:
            print(f"      ~ {w}")
    print(f"\n{len(files)} catatan diperiksa · {rusak} rusak bentuk · {peringatan} peringatan.")
    sys.exit(1 if rusak else 0)


if __name__ == "__main__":
    main()
