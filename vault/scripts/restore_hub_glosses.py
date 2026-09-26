"""Satu kali: kembalikan baris penjelasan (gloss) di tiap hub yang sempat kuhapus `sync_vault.py`.

Urutan yang terjadi, dan yang bikin ini perlu ada:
  1. `migrate_vault.py` menulis hub dengan `- [[A2 - Decision Spine]] — alur lima tahap...`
  2. `sync_vault.py` (versi pertama) menulis ulang daftar dari nol -> glossnya hilang diam-diam
  3. `sync_vault.py` sekarang append-only, tapi yang hilang tidak kembali sendiri

Jadi gloss diambil dari sumber yang sudah ada di repo (`HUBS` di `migrate_vault.py`), bukan kutik
ulang dari ingatan — kalau teksnya berubah, berubahnya di satu tempat itu.

    python scripts/restore_hub_glosses.py
"""
import ast
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

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(HERE)
SRC = os.path.join(HERE, "migrate_vault.py")

tree = ast.parse(io.open(SRC, encoding="utf-8").read())
hubs = None
for node in tree.body:
    if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "HUBS":
        hubs = ast.literal_eval(node.value)
if not hubs:
    sys.exit("HUBS tidak ketemu di migrate_vault.py — jangan menebak isinya.")

repl = 0
for rel, val in hubs.items():
    # HUBS[rel] = (tag, judul, pembuka, [gloss...]) — yang dibutuhkan hanya daftar gloss
    gloss_src = val[3] if isinstance(val, tuple) and len(val) > 3 else val
    text = "\n".join("- " + g for g in gloss_src)
    p = os.path.join(VAULT, rel.replace("/", os.sep))
    if not os.path.isfile(p):
        print(f"  skip  {rel} (tidak ada)")
        continue
    cur = io.open(p, encoding="utf-8").read()
    have = re.search(r"## Bagian\n(.*?)(?=\n```dataview|\n<!--|\Z)", cur, flags=re.S)
    if not have:
        print(f"  skip  {rel} (struktur tidak dikenali — periksa manual, jangan dipaksa)")
        continue
    gloss = [l for l in text.splitlines() if l.strip().startswith("- [[")]
    bare = [l for l in have.group(1).splitlines() if l.strip().startswith("- [[")]
    if any("—" in l for l in gloss) and not any("—" in l for l in bare):
        names = {re.match(r"- \[\[([^\]|]+)", l).group(1).strip().split("/")[-1]: l for l in gloss}
        new_lines = []
        for l in bare:
            n = re.match(r"- \[\[([^\]|]+)", l).group(1).strip().split("/")[-1]
            new_lines.append(names.get(n, l))
        fixed = cur.replace(have.group(0), "## Bagian\n\n" + "\n".join(new_lines) + "\n")
        io.open(p, "w", encoding="utf-8", newline="\n").write(fixed)
        print(f"  ok    {rel} ({len(new_lines)} baris dapat penjelasan lagi)")
        repl += 1
    elif any("—" in l for l in bare):
        print(f"  ok    {rel} (gloss masih utuh)")
    else:
        print(f"  ?     {rel} — tidak ada gloss di sumber MAUPUN di hub: tulis manual")
print(f"\n{repl} hub dipulihkan. Lanjutkan: python scripts/sync_vault.py && python scripts/check_links.py")
