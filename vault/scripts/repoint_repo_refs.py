"""Repoint rujukan ke halaman vault yang pindah, di seluruh repo produk.

Kenapa perlu: migrasi 27 Sep memindahkan 12 halaman vault ke folder bertingkat. Rujukan di dalam
vault sudah ditulis ulang oleh `migrate_vault.py`, tapi rujukan di **README publik** dan di
**komentar kode** tidak - dan rujukan yang busuk di komentar kode lebih berbahaya dari yang di
README: dia berbunyi masuk akal (`lihat vault/02-Ambang.md`), orang membuka foldernya, kosong, dan
akhirnya menebak asal angka. Padahal komentar-komentar itulah tempat ambang berasal.

Bentuk `vault/NN` tanpa nama berkas (mis. `vault/08 §3`) dilaporkan, tidak diganti otomatis:
nomor telat tanpa nama tidak selalu punya satu tujuan.

    python -X utf8 vault/scripts/repoint_repo_refs.py --dry-run
    python -X utf8 vault/scripts/repoint_repo_refs.py
"""
import argparse
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

# Fabius/vault/scripts/ -> naik TIGA tingkat, bukan dua. Kesalahan jumlah tingkat ini sudah pernah
# terjadi dua kali di repo ini (alat menulis di luar repo lalu "verify" melaporkan 4/4 identik
# terhadap keluarannya sendiri), jadi jalurnya di-assert, tidak dipercaya.
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.isfile(os.path.join(REPO, "foundry.toml")):
    sys.exit(f"REPO bukan akar Fabius: {REPO}\n     harus berisi foundry.toml - berhenti, "
             "jangan menulis di luar repo.")

OLD2NEW = {
    "vault/00-Mulai.md": "vault/00-Overview/01 - Briefing.md",
    "vault/01-Klaim-Dan-Batas.md": "vault/06-Results/01 - Claims and Limits.md",
    "vault/02-Ambang.md": "vault/06-Results/02 - Thresholds.md",
    "vault/03-Dataset.md": "vault/03-Data/01 - Dataset.md",
    "vault/04-Kontrak.md": "vault/02-Contracts/01 - DecisionAnchor.md",
    "vault/05-Belum-Terbukti.md": "vault/06-Results/03 - Not Yet Proven.md",
    "vault/06-Keputusan.md": "vault/00-Overview/03 - Decisions.md",
    "vault/07-Deploy-97.md": "vault/02-Contracts/02 - Deployed on 97.md",
    "vault/08-Kelas-Aset-dan-Kursi.md": "vault/01-Agent/01 - Asset Classes and Seats.md",
    "vault/09-Uji-Arah-Tidak-Ada-Edge.md": "vault/06-Results/04 - Negative Results.md",
    "vault/10-Pra-Registrasi-Uji-Aliran.md": "vault/06-Results/05 - Pre-registration Flow.md",
    "vault/11-Pra-Registrasi-Uji-Horison-Whale.md": "vault/06-Results/06 - Pre-registration Horizon.md",
}
# komentar kode menyebut halaman dengan nomor telat: "vault/02-Ambang.md" (sudah di atas) dan
# "vault/08 §3" / "vault/07" - yang terakhir ini dipetakan ke halaman barunya juga
BARE = {
    "vault/02": "vault/06-Results/02 - Thresholds.md",
    "vault/03": "vault/03-Data/01 - Dataset.md",
    "vault/04": "vault/02-Contracts/01 - DecisionAnchor.md",
    "vault/05": "vault/06-Results/03 - Not Yet Proven.md",
    "vault/06": "vault/00-Overview/03 - Decisions.md",
    "vault/07": "vault/02-Contracts/02 - Deployed on 97.md",
    "vault/08": "vault/01-Agent/01 - Asset Classes and Seats.md",
    "vault/09": "vault/06-Results/04 - Negative Results.md",
    "vault/10": "vault/06-Results/05 - Pre-registration Flow.md",
    "vault/11": "vault/06-Results/06 - Pre-registration Horizon.md",
}

ap = argparse.ArgumentParser()
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()

TARGETS = []
for pat in ("*.md", "tools/*.py", "contracts/**/*.sol", "test/*.sol", "universe/*.py",
            "script/*.sol", ".github/workflows/*.yml", "docs/*.json"):
    TARGETS += glob.glob(os.path.join(REPO, pat), recursive=True)
TARGETS = sorted({t for t in TARGETS
                  if "qwen-code-export" not in t and os.sep + "vault" + os.sep not in t})

BARE_RE = re.compile(r"vault/(0[0-9]|1[01])(?![\w.\-])")
changed = 0
bare_left = []
for t in TARGETS:
    text = io.open(t, encoding="utf-8").read()
    orig = text
    for old, new in OLD2NEW.items():
        text = text.replace(old, new)
    # yang masih tinggal: bentuk nomor telat. Ganti HANYA kalau nomornya ada di peta BARE dan
    # tidak diikuti tanda baca yang berarti berkas (`.md` sudah handled di atas).
    for m in BARE_RE.finditer(text):
        bare_left.append((os.path.relpath(t, REPO).replace(os.sep, "/"), m.group(0)))
    text = BARE_RE.sub(lambda m: BARE.get("vault/" + m.group(1), "vault/" + m.group(1)), text)
    if text != orig:
        n = sum(1 for o in OLD2NEW if o in orig) + len(BARE_RE.findall(orig))
        print(f"  {'akan':>5} {os.path.relpath(t, REPO).replace(os.sep, '/')}  ({n} rujukan)")
        if not a.dry_run:
            io.open(t, "w", encoding="utf-8", newline="\n").write(text)
        changed += 1

print(f"\n{changed} berkas diubah." + ("  (dry-run: tidak ada yang ditulis)" if a.dry_run else ""))
print(f"rujukan nomor-telat yang ditemukan: {len(bare_left)}")
for f, s in bare_left[:12]:
    print("   ", f, s)
