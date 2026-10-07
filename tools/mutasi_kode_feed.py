"""P167b/P167c: uji MUTASI - tiap cacat yang disuntik ke jalur `code` / `feed` harus membuat tes gagal (tes yang tetap hijau = tes hampa).

Untuk tiap mutasi: baca berkas, pastikan potongan asli ada TEPAT sekali, tulis versi bercacat, jalankan `engine.tests.test_kode` + `engine.tests.test_feed_kind`,
lalu tulis kembali isi asli (sha256 diperiksa sesudahnya). Mencetak TERTANGKAP / LOLOS per mutasi dan ringkasannya. Kode keluar 0 hanya bila semua
tertangkap dan semua berkas kembali utuh. Mutasi bertanda platform ("nt" = Windows / Job Object + DACL, "posix" = Linux / setrlimit) hanya disuntik
di platform itu (jalur platform lain tidak dijalankan tes di sini). Berkas dibaca + ditulis byte-persis: potongan berbaris jamak mengikuti akhir baris
berkas (CRLF di working copy Windows). Jalankan dengan `git status` bersih untuk berkas-berkas ini (alat menulis ke berkas sumber selama berjalan).

Pakai:  python -X utf8 tools/mutasi_kode_feed.py
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MUTASI = [
    ("engine/kode.py", 'elif n.attr.startswith("_") or n.attr not in ATRIBUT:', 'elif n.attr.startswith("_"):', "atribut tanpa daftar-izin"),
    ("engine/kode.py", '    "eval", "exec", "compile", "open",', '    "exec", "compile", "open",', "eval tidak dilarang"),
    ("engine/kode.py", "    ast.If, ast.For, ast.While,", "    ast.Try, ast.ExceptHandler, ast.If, ast.For, ast.While,", "try/except diizinkan"),
    ("engine/kode.py", "        det = json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)", "        det = True", "dua jalan tidak dibandingkan"),
    ("engine/kode.py", "    visit_While = _badan\n", "", "while tanpa anggaran langkah"),
    ("engine/kode.py", "            if gross > 1.0 + 1e-9:\n                out.append(f\"varian {lab}: gross > 1 di bar {t}\")", "            pass", "DATA pelari tanpa cek gross"),
    ("engine/kode.py", "        if sha != self.sha or data_sha(bars) != self.dsha:", "        if sha != self.sha:", "DATA pelari untuk bar lain dilayani"),
    ("engine/kode.py", "    ok = det and n > 0 and not beda", "    ok = det and n > 0", "beda sampel kausal diabaikan"),
    ("engine/kode.py", "        x = int(round(v * f))\n        return max(1, x) if v > 0 else min(-1, x)", "        return float(v) * f", "G5 code: bulat jadi desimal"),
    ("engine/kode_anak.py", "        if gross > 1.0 + TOL_GROSS:", "        if gross > 2.0:", "anak: gross sampai 2 lolos"),
    ("engine/kode_anak.py", "        return MappingProxyType({a: _Aset(kolom[a], n_upto[a][i]) for a in aset if n_upto[a][i] > 0})",
     "        return MappingProxyType({a: _Aset(kolom[a], n_upto[a][i] + 1) for a in aset if n_upto[a][i] > 0})", "anak: satu bar masa depan bocor"),
    ("engine/kode_anak.py", "                i = pos[t]\n                f = namespace()", "                i = pos[t]", "anak: sampel kausal tanpa namespace segar"),
    ("engine/kode_anak.py", "        return _batasi_windows(", "        return None and _batasi_windows(", "anak Windows: tanpa Job Object", "nt"),
    ("engine/kode_anak.py", "(JOB_OBJECT_LIMIT_PROCESS_TIME | ", "(", "anak Windows: tanpa batas CPU", "nt"),
    ("engine/kode_anak.py", "JOB_OBJECT_LIMIT_ACTIVE_PROCESS | JOB_OBJECT_LIMIT_PROCESS_MEMORY", "JOB_OBJECT_LIMIT_ACTIVE_PROCESS", "anak Windows: tanpa batas memori",
     "nt"),
    ("engine/kode_anak.py", "JOB_OBJECT_LIMIT_PROCESS_TIME | JOB_OBJECT_LIMIT_ACTIVE_PROCESS | ", "JOB_OBJECT_LIMIT_PROCESS_TIME | ",
     "anak Windows: boleh membuat proses baru", "nt"),
    ("engine/kode_anak.py", "    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))", "    pass", "anak POSIX: tanpa batas CPU", "posix"),
    ("engine/kode_anak.py", "    resource.setrlimit(resource.RLIMIT_AS, (mem, mem))", "    pass", "anak POSIX: tanpa batas memori", "posix"),
    ("engine/kode.py", 'STATUS_WINDOWS = {0xC0000044: "batas CPU", ', "STATUS_WINDOWS = {", "induk Windows: batas CPU tak terbaca", "nt"),
    ("engine/berkas_privat.py", "    _kunci(path, folder=False)", "    pass", "berkas privat Windows: berkas tanpa DACL terlindung", "nt"),
    ("engine/berkas_privat.py", "    _kunci(os.path.dirname(os.path.abspath(path)), folder=True)", "    pass", "berkas privat Windows: folder tidak dikunci", "nt"),
    ("engine/berkas_privat.py", "os.O_TRUNC, 0o600)", "os.O_TRUNC, 0o644)", "berkas privat POSIX: mode 0644", "posix"),
    ("engine/feed.py", "    if now_s >= bar_close - BATAS_SEBELUM_TUTUP_S:", "    if now_s >= bar_close:", "feed: batas terima = penutupan"),
    ("engine/feed.py", "        if isinstance(v, bool) or not isinstance(v, int):", "        if isinstance(v, bool) or not isinstance(v, (int, float)):", "feed: bobot desimal diterima"),
    ("engine/feed.py", "        if not isinstance(la, int) or not 0 < la < bc:", "        if not isinstance(la, int) or not 0 < la:", "feed: anchor sesudah penutupan diterima"),
    ("engine/feed.py", "        if komits is None:\n            if late:", "        if komits is None and False:\n            if late:", "feed: daftar tak terbaca = tidak ada komit"),
    ("tools/feed_gerbang.py", '            if any(r["bot_id"] == b["bot_id"] and int(r["bar_close"]) == b["bar_close"] for r in ada):',
     "            if False:", "gerbang: komit ganda diterima"),
    ("tools/feed_gerbang.py", '        if who != b["issuer"]:', "        if False:", "gerbang: tanda tangan siapa pun diterima"),
    ("tools/feed_gerbang.py", "            if now >= bc:\n                root, proofs", "            if True:\n                root, proofs", "gerbang: bobot terbuka sebelum bar dibuka"),
    ("tools/feed_gerbang.py", "        if not bc - F.BATAS_SEBELUM_TUTUP_S <= now_s < bc - F.JEDA_ANCHOR_S:", "        if not bc - F.BATAS_SEBELUM_TUTUP_S <= now_s < bc:",
     "gerbang: anchor sampai detik penutupan"),
    ("engine/registri.py", '    diuji = [e for e in mine if e["vonis"] not in TANPA_STATISTIK]', '    diuji = [e for e in mine if e["vonis"] not in TANPA_UJI]',
     "registri: feed memakan alpha + masa tunggu"),
    ("engine/review.py", '    v = "TOLAK_IDENTITAS" if (identity and ident["masalah"]) else feedmod.VONIS', '    v = "TOLAK_IDENTITAS" if (identity and ident["masalah"]) else "LOLOS_SHADOW"',
     "review: feed divonis LOLOS_SHADOW"),
]


def sha(p: str) -> str:
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def tes() -> int:
    env = dict(os.environ)
    return subprocess.run([sys.executable, "-X", "utf8", "-m", "unittest", "engine.tests.test_kode", "engine.tests.test_feed_kind",
                           "engine.tests.test_berkas_privat"], cwd=ROOT,
                          capture_output=True, text=True, timeout=900, env=env).returncode


def main() -> int:
    if tes() != 0:
        print("tes sudah gagal SEBELUM mutasi: hentikan (mutasi tidak bermakna)")
        return 2
    plat = "nt" if os.name == "nt" else "posix"
    berlaku = [m for m in MUTASI if len(m) < 5 or m[4] == plat]
    tangkap, utuh = 0, True
    for rel, lama, baru, nama, *_ in berlaku:
        p = os.path.join(ROOT, rel)
        with open(p, encoding="utf-8", newline="") as f:
            asli = f.read()
        if "\r\n" in asli:
            lama, baru = lama.replace("\n", "\r\n"), baru.replace("\n", "\r\n")
        if asli.count(lama) != 1:
            print(f"  ? {nama}: potongan asli tidak ditemukan tepat sekali di {rel} - mutasi dilewati (alat basi)")
            utuh = False
            continue
        h0 = sha(p)
        try:
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(asli.replace(lama, baru))
            rc = tes()
        finally:
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(asli)
        if sha(p) != h0:
            print(f"  ! {rel} TIDAK kembali utuh")
            utuh = False
        kena = rc != 0
        tangkap += kena
        print(f"  {'TERTANGKAP' if kena else 'LOLOS (tes hampa?)'}: {nama} ({rel})")
    print(f"mutasi ({plat}): {len(berlaku)} disuntik (dari {len(MUTASI)}), {tangkap} tertangkap; berkas utuh {'ya' if utuh else 'TIDAK'}")
    return 0 if tangkap == len(berlaku) and utuh else 1


if __name__ == "__main__":
    raise SystemExit(main())
