"""Deploy worker Railway (F-D80) dari commit HEAD, bukan dari folder kerja: `git archive HEAD <jalur worker>` -> folder sementara -> `railway up --path-as-root`.
Berkas yang tidak di-commit (`.env`, `.committer.env`, ekspor sesi) tidak mungkin ikut terunggah.

Konfigurasi service (sekali, sudah dipasang 2 Okt; railway.json DIABAIKAN Railway untuk proyek baru dan config-as-code deprecated):
  railway variable set RAILWAY_DOCKERFILE_PATH=railway/Dockerfile --service fabius-engine --skip-deploys
  railway service scale --service fabius-engine southeast-asia=1 sfo=0          # SATU replika: dua replika = dua penanda tangan

Layanan agent luar uji (P151 + P166) memakai arsip SENDIRI yang minimal (`PATHS_LAYANAN`), bukan arsip worker:
  railway variable set RAILWAY_DOCKERFILE_PATH=railway/agen-luar-uji/Dockerfile --service agen-luar-uji --skip-deploys

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
         "tools/shadow_tick.py", "tools/feed_bars.py", "tools/pin_book.py", "tools/alert.py",
         "tools/eksekutor.py", "tools/venue_binance.py", "tools/exec_feed.py", "tools/canary.py",
         "tools/erc8004_validasi.py", "tools/x402_sinyal.py", "tools/sinyal_gambar.py", "tools/analis.py", "tools/privy_server.py", "tools/kabar.py", "tools/meja.py", "tools/meja_data.py", "tools/meja2.py", "tools/meja_slot.py", "tools/meja_eval.py", "tools/pengajuan.py", "tools/feed_gerbang.py", "tools/pin_spec.py", "tools/agen_luar.py", "tools/peninjau_llm.py", "tools/akun_mcp.py", "config/agents.json"]  # P118 eksekutor (F-D93) + P119 umpan Gist (F-D94) + P133 canary (F-D96) + P136 validasi ERC-8004 (F-D98)


# P151 + P166: service `agen-luar-uji` - hanya berkas yang di-COPY `railway/agen-luar-uji/Dockerfile` (tanpa engine, tanpa alat worker).
PATHS_LAYANAN = {"agen-luar-uji": ["railway/agen-luar-uji", "tools/agen_luar_layanan.py", "tools/desk_agent_client.py", "tools/agen_luar_uji_jawab.py",
                                   "tools/evm.py"]}


def main() -> int:
    ap = argparse.ArgumentParser(description="Deploy worker Railway dari HEAD (git archive).")
    ap.add_argument("--service", default="fabius-engine")
    ap.add_argument("--dry-run", action="store_true", help="siapkan arsip dan tampilkan isinya, tanpa railway up")
    a = ap.parse_args()
    paths = PATHS_LAYANAN.get(a.service, PATHS)
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", *paths], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    if dirty:
        print(f"PERINGATAN: ada perubahan belum di-commit di jalur worker - yang dideploy adalah HEAD {head}, bukan folder kerja:\n{dirty}")
    tmp = tempfile.mkdtemp(prefix="fabius-railway-")
    try:
        tar = os.path.join(tmp, "src.tar")
        subprocess.run(["git", "archive", "--format=tar", "-o", tar, "HEAD", *paths], cwd=ROOT, check=True)
        out = os.path.join(tmp, "src")
        os.makedirs(out)
        with tarfile.open(tar) as t:
            t.extractall(out, filter="data")
        n = sum(len(fs) for _, _, fs in os.walk(out))
        print(f"arsip HEAD {head}: {n} berkas dari {', '.join(paths)}")
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
