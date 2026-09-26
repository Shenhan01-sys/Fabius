"""Audit cakupan vault: identifier yang DIPAKAI produk tapi tidak disebut di halaman mana pun.

Kenapa alat ini ada dan bukan daftar yang kutulis dari ingatan: permintaannya persis "audit mana aja
yang belum masuk vault". Daftar yang kutebak hanya mengecek apa yang sudah kupikirkan. Jadi
kandidatnya ditarik otomatis dari kode & README produk, lalu setiap kandidat dicari di seluruh teks
vault (termasuk hub dan `_archive/`).

Dua pagar yang membuat laporannya bisa dibaca:
  1. **Produk menang atas transcript.** Suatu istilah baru dianggap kalau ia muncul di berkas PRODUK
     (`tools/`, `contracts/`, `test/`, `README.md`, `docs/`, workflow, `foundry.toml`). Istilah yang
     cuma ada di ekspor sesi adalah nama parameter alat (`old_string`, `file_path`) - itu bukan fakta
     proyek. Versi pertama tanpa pagar ini menghasilkan 2.248 "temuan" yang 90%-nya sampah.
  2. **Plumbing dibuang.** Nama fungsi bawaan pustaka/kerangka kerja (`assertEq`, `add_argument`,
     `exist_ok`, `internalType`, `SystemExit`) tidak layak punya halaman; yang layak adalah nama
     milik kami sendiri (`seat_eligible`, `HARD_CEILING`, `X402_SKEW`). Karena itu kandidatnya
     disaring ke yang **terpakai >= 2 berkas produk** ATAU yang berhuruf kapital-di-awal pola
     Solidity/ID kami.

Sisa laporan tetap harus dibaca manusia: "tidak disebut di vault" tidak selalu berarti "harus ada
halamannya" - kadang artinya cukup satu baris di Quick-Reference.

    python -X utf8 vault/scripts/fact_coverage.py --top 30
    python -X utf8 vault/scripts/fact_coverage.py --grep HARD_CEILING
"""
import argparse
import collections
import glob
import io
import os
import re
import sys
# Windows: cmd.exe default cp1252 dan glyph yang kami cetak (`①④⑥` di arah, `⚠` di laporan)
# bukan bagian dari yang di-hash - jadi encoding stdout yang disetel, bukan stringnya.
# Tanpa ini, `print` bisa pecah DI TENGAH tabel dan separuh hasilnya terbaca seperti laporan penuh.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # stdout tanpa reconfigure (mis. tertangkap harness) = biarkan apa adanya

FAB = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VAULT = os.path.join(FAB, "vault")
if not os.path.isdir(os.path.join(VAULT, "00-Overview")):
    sys.exit(f"VAULT bukan folder vault: {VAULT}\n     (harus berisi 00-Overview/)")

PRODUCT = sorted(glob.glob(os.path.join(FAB, "tools", "*.py"))
                 + glob.glob(os.path.join(FAB, "contracts", "**", "*.sol"), recursive=True)
                 + glob.glob(os.path.join(FAB, "test", "*.sol"))
                 + glob.glob(os.path.join(FAB, "script", "*.sol"))
                 + glob.glob(os.path.join(FAB, "universe", "*.py"))
                 + glob.glob(os.path.join(FAB, ".github", "workflows", "*.yml"))
                 + glob.glob(os.path.join(FAB, "docs", "*.json"))
                 + [os.path.join(FAB, "README.md"), os.path.join(FAB, "foundry.toml")])
# jalur vault lama yang sudah dipindah: ini temuan kelas "pointer busuk", bukan "belum terdokumentasi"
STALE_PATH = re.compile(r"vault/\d\d-[A-Za-z][\w-]*\.md")

STOP = {
    # python / argparse / foundry / json plumbing
    "add_argument", "ArgumentParser", "parse_args", "store_true", "exist_ok", "ensure_ascii",
    "sort_keys", "SystemExit", "TypeError", "ValueError", "RuntimeError", "KeyError", "Exception",
    "open", "read", "write", "strip", "split", "join", "replace", "format", "print", "return",
    "self", "args", "kwargs", "None", "True", "False", "int", "str", "bool", "list", "dict",
    "import", "from", "with", "lambda", "yield", "def", "class", "range", "len", "sum", "min",
    "max", "abs", "set", "map", "filter", "enumerate", "isinstance", "getattr", "setattr",
    "startswith", "endswith", "append", "extend", "keys", "values", "items", "lower", "upper",
    "assertEq", "assertGt", "assertLt", "expectRevert", "vm", "pragma", "contract", "function",
    "internalType", "inputs", "outputs", "stateMutability", "anonymous", "indexed", "event",
    "require", "mapping", "public", "private", "memory", "calldata", "emit", "constructor",
    "the", "and", "for", "with", "this", "that", "from", "have", "will", "your", "not", "true",
    "false", "name", "data", "path", "file", "line", "key", "value", "item", "text", "type",
    "json", "yaml", "utf", "bytes", "byte", "hex", "addr", "url", "api", "http", "https",
    # lapisan berikut ini hasil run pertama alatnya: kata kunci bahasa & nama pustaka yang lolos
    # karena dipakai di >= 2 berkas. Bukan fakta proyek, jadi dibuang dengan nama.
    "else", "elif", "except", "finally", "while", "lambda", "global", "return", "yield",
    "noqa", "BLE001", "E402", "E501", "F401", "dirname", "abspath", "joinpath", "listdir",
    "makedirs", "setdefault", "strftime", "strptime", "gmtime", "urlopen", "Request", "loads",
    "dumps", "argparse", "annotations", "dataclass", "namedtuple", "datetime", "timezone",
    "timedelta", "OSError", "SystemExit", "KeyboardInterrupt", "Mozilla", "headers",
    "uint8", "uint256", "address", "boolean", "string", "bytes32", "memory", " payable",
    "assertEq", "assertTrue", "deploy", "prank", "warp", "roll", "startPrank", "addr",
    "float", "continue", "sorted", "reversed", "headers", "sleep", "exists", "insert",
    "application", "Content", "Type", "User", "Agent", "latest", "pending", "timeout",
}

PAT = re.compile(r"\b([A-Za-z][A-Za-z0-9_]{3,34})\b")
OUR_STYLE = re.compile(r"^(?:[A-Z][a-z0-9]+){2,}$|^[a-z][a-z0-9]*_[a-z0-9_]+$|^[A-Z][A-Z0-9_]{3,}$")
# angka yang menempel satuannya adalah klaim, bukan plumbing: "20 bps", "5.000 bar", "1.259 kredit".
# Bentuk ini yang boleh lolos walau cuma muncul di satu berkas - dialah yang harus punya halaman.
NUM_UNIT = re.compile(r"^\d[\d.,]*\s?(?:bps|atomic|kredit|credits|bar|tx|maker|jam|hari|menit|detik|"
                      r"KB|MB|tBNB|USDT|B)$", re.I)


def vault_blob():
    return "\n".join(io.open(f, encoding="utf-8", errors="replace").read()
                     for f in glob.glob(os.path.join(VAULT, "**", "*.md"), recursive=True)).lower()


ap = argparse.ArgumentParser()
ap.add_argument("--top", type=int, default=30)
ap.add_argument("--grep", help="cek satu istilah di vault (case-insensitive)")
a = ap.parse_args()

vb = vault_blob()
if a.grep:
    print(f"{a.grep!r} di vault: {'ADA' if a.grep.lower() in vb else 'TIDAK ADA'}")
    sys.exit(0)

files_scanned = 0
stale = collections.Counter()
where = collections.defaultdict(set)
freq = collections.Counter()
for p in PRODUCT:
    if not os.path.isfile(p):
        continue
    files_scanned += 1
    rel = os.path.relpath(p, FAB).replace(os.sep, "/")
    t = io.open(p, encoding="utf-8", errors="replace").read()
    for m in STALE_PATH.finditer(t):
        stale[m.group(0)] += 1
    for m in PAT.finditer(t):
        tok = m.group(1)
        if tok in STOP or tok.lower() in STOP:
            continue
        freq[tok] += 1
        where[tok].add(rel)

cands = []
for tok, nfiles in ((t, len(s)) for t, s in where.items()):
    # Gerbangnya dua, dan keduanya perlu. Versi pertama hanya menyaring yang < 2 berkas sehingga
    # kata kunci bahasa (`else`, `noqa`, `dirname`, `uint8`) lolos beratus-ratus dan laporan tidak
    # bisa dibaca. Sekarang: bentuknya harus mirip ID kami (camelCase kami, snake_case, atau
    # konstanta KAPITAL) ATAU angka-bersatuan; DAN harus dipakai di >= 2 berkas produk >= 8 kali.
    if not OUR_STYLE.match(tok) and not NUM_UNIT.match(tok):
        continue
    if nfiles < 2 and freq[tok] < 8:
        continue
    if tok.lower() in vb:
        continue
    cands.append((tok, freq[tok], nfiles, sorted(where[tok])))
cands.sort(key=lambda x: (-x[2], -x[1]))

print(f"{files_scanned} berkas produk dipindai · {len(where)} identifier · "
      f"{len(cands)} tidak disebut vault mana pun\n")
for tok, f, nf, srcs in cands[:a.top]:
    print(f"  {nf:2} berkas  {freq[tok]:5}x  {tok:26} <- {', '.join(os.path.basename(s) for s in srcs[:3])}")

print(f"\nJALUR VAULT BUSUK di produk ({sum(stale.values())} kemunculan, {len(stale)} tujuan):")
for p, c in stale.most_common():
    print(f"  {c:3}x  {p}")
if not stale:
    print("  (tidak ada - README & komentar sudah menunjuk halaman yang benar)")
print("\nBaca catatannya: tidak disebut vault TIDAK sama dengan wajib dapat halaman. Sebagian cuma")
print("butuh satu baris di Quick-Reference; sebagian lagi memang internals yang tidak didokumentasi.")
