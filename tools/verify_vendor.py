"""Verifikasi manifest vendor x402 dari DALAM clone Fabius — nol jaringan, nol kunci.

Kenapa berkas ini ada: `_research/vendored_x402.py` (yang mengunduh) hidup di workspace, jadi
kalau vault menyuruh orang "periksa bahwa vendor kami identik upstream" lewat path di luar repo
produk, klaim "bisa diverifikasi dari clone" putus untuk jalur itu. Yang dibutuhkan pembaca clone
cuma: baca manifest, hash berkasnya, bandingkan. Itu di sini.

Kolom `repo_path` di manifest memang ditambahkan untuk ini — ia jalur relatif ke clone, sementara
`path` masih jalur relatif ke workspace (dipakai alat unduh).

Pakai:  python tools/verify_vendor.py            # semua berkas vendor di manifest
"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "contracts", "vendor", "x402", "VENDORED.json")
if not os.path.isdir(os.path.join(ROOT, "contracts")) or not os.path.isfile(MANIFEST):
    sys.exit(f"ROOT salah: {ROOT}\n     harus berisi contracts/ + contracts/vendor/x402/VENDORED.json")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 16), b""):
            h.update(blk)
    return "0x" + h.hexdigest()


def main():
    man = json.load(open(MANIFEST, encoding="utf-8"))
    bad = []
    for e in man["files"]:
        rel = e.get("repo_path") or e["path"]
        rel = rel[len("Fabius/"):] if rel.startswith("Fabius/") else rel
        p = os.path.join(ROOT, *rel.split("/"))
        if not os.path.exists(p):
            print(f"  HILANG  {rel}")
            bad.append(rel)
            continue
        got = sha256(p)
        ok = got == e["sha256"]
        size_ok = os.path.getsize(p) == e.get("bytes")
        print(f"  {'sama  ' if ok and size_ok else 'BEDA  '} {rel:52} {got[:18]}… "
              f"{os.path.getsize(p)} B" + ("" if size_ok else f" (manifest {e.get('bytes')} B)"))
        if not (ok and size_ok):
            bad.append(rel)
    n = len(man["files"])
    print(f"\nupstream {man['upstream']} @ {man['commit']}")
    print(f"{n - len(bad)}/{n} identik dengan yang dicatat manifest")
    if bad:
        print("Jangan tulis 'vendor verbatim' selama baris di atas bukan n/n. Yang BEDA bisa jadi")
        print("EOL yang dinormalisasi git (cek .gitattributes `-text` di jalur vendor), bukan")
        print("sumber yang disunat — tapi itu tetap berarti klaimnya belum terbuktikan di mesinmu.")
        return 1
    print("Verbatim itu property yang bisa diperiksa, bukan yang bisa dinyatakan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
