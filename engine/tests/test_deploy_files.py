"""Image worker Railway memuat setiap modul tools/ yang dipakai worker (5 Okt 2026: `erc8004_validasi` ada di arsip `railway_up.py` tetapi tidak
di-COPY oleh `railway/Dockerfile` -> `ModuleNotFoundError` di worker yang sudah ter-deploy; langkahnya dibungkus sendiri, jadi komit tidak terganggu,
tetapi fiturnya mati diam-diam sampai log dibaca)."""
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import railway_up                                                   # noqa: E402


def copied_tools() -> set:
    with open(os.path.join(ROOT, "railway", "Dockerfile"), encoding="utf-8") as f:
        lines = [ln for ln in f if ln.startswith("COPY ")]
    out = set()
    for ln in lines:
        out |= set(re.findall(r"(tools/[A-Za-z0-9_]+\.py)", ln))
    return out


def tools_imported_by(path: str) -> set:
    """Nama modul tools/ yang di-import (juga di dalam fungsi) oleh berkas itu."""
    with open(path, encoding="utf-8") as f:
        src = f.read()
    names = set(re.findall(r"^\s*import ([A-Za-z0-9_]+)", src, re.M)) | set(re.findall(r"^\s*from ([A-Za-z0-9_]+) import", src, re.M))
    return {f"tools/{n}.py" for n in names if os.path.isfile(os.path.join(ROOT, "tools", f"{n}.py"))}


class DeployFilesTests(unittest.TestCase):
    def test_every_tools_file_in_the_archive_is_copied_into_the_image(self):
        archived = {p for p in railway_up.PATHS if p.startswith("tools/") and p.endswith(".py")}
        self.assertEqual(sorted(archived - copied_tools()), [])

    def test_every_tools_module_the_worker_imports_is_in_the_archive_and_the_image(self):
        need = set()
        for f in ("operator_loop.py", "canary.py", "eksekutor.py", "erc8004_validasi.py", "x402_sinyal.py", "analis.py", "privy_server.py", "kabar.py", "meja.py", "meja_data.py", "meja2.py", "meja_slot.py", "pengajuan.py", "pin_spec.py", "agen_luar.py"):
            need |= tools_imported_by(os.path.join(ROOT, "tools", f))
        need -= {"tools/x8004_register.py", "tools/verify_signals.py"}           # hanya perintah lokal / validasi.yml, bukan jalur worker
        self.assertEqual(sorted(need - copied_tools()), [])
        self.assertEqual(sorted(need - set(railway_up.PATHS)), [])

    def test_the_agent_registry_ships_with_the_gate_image(self):
        # P159: analis.py membaca config/agents.json saat diimpor; tanpa berkas itu gerbang gagal mulai
        self.assertIn("config/agents.json", railway_up.PATHS)
        with open(os.path.join(ROOT, "railway", "Dockerfile"), encoding="utf-8") as f:
            self.assertIn("COPY config/agents.json config/agents.json", f.read())


if __name__ == "__main__":
    unittest.main()
