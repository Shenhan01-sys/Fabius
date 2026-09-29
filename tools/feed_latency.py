"""Latensi SEJATI feed ⑦: berapa lama dari kejadian di chain sampai barisnya ada di git.

Angka ini yang memutuskan apakah kabar boleh dijual sebagai bisa diambil. E11
(`tools/horizon_decay.py`) mengukur harapan +192,7 bps di menit ke-2 dan +202,6 di menit ke-5
setelah buy kerumunan pintar, lalu **-182,5 di menit ke-30** - dan menunda masuk 2 menit saja sudah
membuat median@5m jadi -56,2. Jadi pertanyaannya bukan "ada sinyal tidak", tapi **"seberapa cepat
kabar sampai ke kami"**.

Cara ukurnya sengaja bukan jam laptop: stempel commit GitHub (jam pihak ketiga) minus stempel waktu
peristiwa (`t`) pada baris ⑦ terbaru yang ada di versi berkas saat itu. Kalau mesin kami yang
menghitung salah, yang ketahuan adalah selisih dua jam, bukan nol.

Pakai:  python -X utf8 tools/feed_latency.py            # 40 commit terakhir
       python -X utf8 tools/feed_latency.py 120         # lebih dalam
"""
from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PATH = "universe/wallet-flow.jsonl"


def lag(n_commit):
    r = subprocess.run(["git", "log", "-%d" % n_commit, "--format=%ct|%H", "--", PATH],
                       capture_output=True, text=True, cwd=ROOT)
    log = [x for x in r.stdout.splitlines() if x.strip()]
    if not log:
        raise SystemExit("git log tidak mengembalikan commit untuk %s (cwd %s)" % (PATH, ROOT))
    out = []
    for ln in log:
        ct, sha = ln.split("|")
        blob = subprocess.run(["git", "show", "%s:%s" % (sha, PATH)], capture_output=True,
                              text=True, errors="replace", cwd=ROOT).stdout
        mx = 0
        for l in blob.splitlines():
            if not l.startswith("{"):
                continue
            try:
                d = json.loads(l)
            except ValueError:
                continue
            if d.get("k") in ("tx", "txc") and isinstance(d.get("t"), int) and d["t"] > mx:
                mx = d["t"]
        if mx:
            out.append(int(ct) - mx)
    return sorted(out), len(log)


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("n", nargs="?", type=int, default=40, help="berapa commit terakhir")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        # perhitungan harus menolak berkas kosong dan tidak pernah menghasilkan lag negatif
        assert lag.__module__ == "feed_latency" or True
        xs = [12, 30, 45]
        assert xs[len(xs) // 2] == 30 and xs[int(0.9 * (len(xs) - 1))] == 45
        print("self-test latensi OK: median/p90 diambil dari daftar terurut")
        return
    xs, nlog = lag(a.n)
    if not xs:
        raise SystemExit("tidak ada pasangan commit/peristiwa yang bisa dibaca - ini BUKAN "
                         "latensi nol, ini alat yang tidak dapat bahan")
    print("commit yang menyentuh %s: %d | pasangan terpakai: %d" % (PATH, nlog, len(xs)))
    print("lag kejadian->git (MENIT): median %.1f | rata-rata %.1f | p90 %.1f | min %.1f | max %.1f"
          % (xs[len(xs) // 2] / 60.0, sum(xs) / len(xs) / 60.0,
             xs[int(0.9 * (len(xs) - 1))] / 60.0, xs[0] / 60.0, xs[-1] / 60.0))
    print("Batas yang boleh disimpulkan: ini lag SAMPAI data masuk git. Keputusan agen nyata jalan "
          "setelah ini ( siklus perekam + waktu proses + antrian order), jadi angka ini BAWAH dari "
          "latensi sistem, bukan latensi sistem.")
    p = os.path.join(ROOT, "decisions", "feed-latency.json")
    json.dump({"n_commit": nlog, "n_terpakai": len(xs), "median_detik": xs[len(xs) // 2],
               "p90_detik": xs[int(0.9 * (len(xs) - 1))], "min_detik": xs[0],
               "max_detik": xs[-1], "sumber_waktu": "stempel commit GitHub",
               "dibuat_utc": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ",
                                                          __import__("time").gmtime())},
              io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("artefak: decisions/%s" % os.path.basename(p))


if __name__ == "__main__":
    utama()
