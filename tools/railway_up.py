"""Deploy worker Railway (F-D80) dari commit HEAD, bukan dari folder kerja: `git archive HEAD <jalur worker>` -> folder sementara -> `railway up --path-as-root`.
Berkas yang tidak di-commit (`.env`, `.committer.env`, ekspor sesi) tidak mungkin ikut terunggah.

Konfigurasi service (sekali, sudah dipasang 2 Okt; railway.json DIABAIKAN Railway untuk proyek baru dan config-as-code deprecated):
  railway variable set RAILWAY_DOCKERFILE_PATH=railway/Dockerfile --service fabius-engine --skip-deploys
  railway service scale --service fabius-engine southeast-asia=1 sfo=0          # SATU replika: dua replika = dua penanda tangan

Pakai:  python -X utf8 tools/railway_up.py [--service fabius-engine] [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PATHS = ["railway", "engine", "tools/evm.py", "tools/signal_commit.py", "tools/operator_loop.py", "tools/paper_tick.py", "tools/rest_vs_vision.py", "tools/rest_latency.py",
         "tools/shadow_tick.py", "tools/feed_bars.py", "tools/pin_book.py"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Deploy worker Railway dari HEAD (git archive).")
    ap.add_argument("--service", default="fabius-engine")
    ap.add_argument("--dry-run", action="store_true", help="siapkan arsip dan tampilkan isinya, tanpa railway up")
    a = ap.parse_args()
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", *PATHS], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    if dirty:
        print(f"PERINGATAN: ada perubahan belum di-commit di jalur worker - yang dideploy adalah HEAD {head}, bukan folder kerja:\n{dirty}")
    tmp = tempfile.mkdtemp(prefix="fabius-railway-")
    try:
        tar = os.path.join(tmp, "src.tar")
        subprocess.run(["git", "archive", "--format=tar", "-o", tar, "HEAD", *PATHS], cwd=ROOT, check=True)
        out = os.path.join(tmp, "src")
        os.makedirs(out)
        with tarfile.open(tar) as t:
            t.extractall(out, filter="data")
        n = sum(len(fs) for _, _, fs in os.walk(out))
        print(f"arsip HEAD {head}: {n} berkas dari {', '.join(PATHS)}")
        if a.dry_run:
            return 0
        exe = shutil.which("railway")          # di Windows CLI npm = railway.cmd; CreateProcess tidak menemukan "railway" polos
        if not exe:
            print("CLI railway tidak ditemukan di PATH")
            return 2
        r = subprocess.run([exe, "up", out, "--path-as-root", "--service", a.service, "--detach", "-m", f"worker {head}"], cwd=ROOT)
        print("\nCek: railway deployment list --service", a.service, "--json   lalu   railway logs --service", a.service, "--lines 40")
        return r.returncode
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
