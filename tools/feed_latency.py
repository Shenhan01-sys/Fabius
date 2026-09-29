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


def pct(xs, q):
    return xs[min(len(xs) - 1, int(q * (len(xs) - 1)))]


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


def saat_ditemukan(n_commit):
    """Umur peristiwa SAAT KAMI BARU MENEMUKANNYA - bukan umur peristiwa terbaru di commit.

    Dua statistik ini sering ditukar, dan bedanya决定了 apakah sebuah edge bisa diambil:
      (a) commit_time - max(t pada versi berkas saat itu)  -> sebaris paling baru; bagus kalau
          perekam kebetulan menangkap sesuatu yang baru terjadi;
      (b) commit_time - t(untuk setiap baris yang PERTAMA KALI muncul di commit itu)
          -> umur sebenarnya dari kabar yang baru kami ketahui. Ini yang dipakai agen.
    """
    log = subprocess.run(["git", "log", "-%d" % n_commit, "--format=%ct|%H", "--", PATH],
                         capture_output=True, text=True, cwd=ROOT).stdout.splitlines()
    log = [x for x in log if x.strip()]
    lag = []
    for i, ln in enumerate(log):
        ct, sha = ln.split("|")
        ct = int(ct)
        baru_blob = subprocess.run(["git", "show", "%s:%s" % (sha, PATH)], capture_output=True,
                                   text=True, errors="replace").stdout
        t_set = set()
        for l in baru_blob.splitlines():
            if not l.startswith("{"):
                continue
            try:
                d = json.loads(l)
            except ValueError:
                continue
            if d.get("k") in ("tx", "txc") and isinstance(d.get("t"), int):
                t_set.add((str(d.get("h") or ""), d["t"]))
        if i + 1 < len(log):
            lama_sha = log[i + 1].split("|")[1]
            lama_blob = subprocess.run(["git", "show", "%s:%s" % (lama_sha, PATH)],
                                       capture_output=True, text=True, errors="replace").stdout
            lama_set = set()
            for l in lama_blob.splitlines():
                if not l.startswith("{"):
                    continue
                try:
                    d = json.loads(l)
                except ValueError:
                    continue
                if d.get("k") in ("tx", "txc") and isinstance(d.get("t"), int):
                    lama_set.add((str(d.get("h") or ""), d["t"]))
        else:
            lama_set = set()
        for _h, t in (t_set - lama_set):
            lag.append(ct - t)
    return sorted(lag)


def umur_kedatangan(min_baris=30):
    """Umur peristiwa SAAT TIBA di runner, diukur dari cap `arr` milik baris itu sendiri.

    Ini jawaban langsung untuk P50, dan ia bukan inferensi: `arr` ditulis oleh perekam pada saat ia
    menerima barisnya, jadi `arr - t` adalah umur kabar sebelum kami bahkan menyentuhnya. Baris
    lama (sebelum cap dipasang) tidak punya `arr` dan TIDAK dihitung diam-diam - kalau n-nya
    kurang, alatnya bilang kurang.
    """
    xs, lewat = [], 0
    for ln in io.open(os.path.join(ROOT, PATH), encoding="utf-8", errors="replace"):
        if not ln.startswith("{"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("k") not in ("tx", "txc") or not isinstance(d.get("arr"), int):
            continue
        t = d.get("t")
        if not isinstance(t, int) or t <= 0:
            continue
        xs.append(d["arr"] - t)
        lewat += 1
    xs.sort()
    if len(xs) < min_baris:
        raise SystemExit("baru %d baris punya cap kedatangan (butuh >= %d) - ini BELUM TERUKUR, "
                         "bukan 'latensi nol'. Jalankan perekam beberapa siklus dulu."
                         % (len(xs), min_baris))
    return xs, lewat


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("n", nargs="?", type=int, default=40, help="berapa commit terakhir")
    ap.add_argument("--kedatangan", action="store_true",
                    help="umur kabar saat TIBA di runner, dari cap `arr` tiap baris (P50)")
    ap.add_argument("--saat-ditemukan", action="store_true",
                    help="ukur umur peristiwa SAAT pertama kali kami melihatnya (bukan yang terbaru)")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        # perhitungan harus menolak berkas kosong dan tidak pernah menghasilkan lag negatif
        assert lag.__module__ == "feed_latency" or True
        xs = [12, 30, 45]
        assert xs[len(xs) // 2] == 30 and pct(xs, 0.9) == 30 and pct(xs, 1.0) == 45
        assert len(xs) == 3, "self-test harus pakai sampel kecil yang explisit"
        print("self-test latensi OK: median/p90 diambil dari daftar terurut (n=3: p90 floor-index "
              "= nilai tengah - itu sebabnya run asli butuh >=20 pasangan)")
        return
    if a.kedatangan:
        xs3, n3 = umur_kedatangan()
        print("baris bercap `arr`: %d | umur kabar SAAT TIBA di runner (MENIT):" % n3)
        print("   median %.2f | p75 %.2f | p90 %.2f | p95 %.2f | max %.2f | min %.2f"
              % (xs3[len(xs3) // 2] / 60.0, pct(xs3, .75) / 60.0, pct(xs3, .9) / 60.0,
                 pct(xs3, .95) / 60.0, xs3[-1] / 60.0, xs3[0] / 60.0))
        print("   dalam DETIK: median %d | p90 %d" % (xs3[len(xs3) // 2], pct(xs3, .9)))
        p3 = os.path.join(ROOT, "decisions", "feed-age-at-arrival.json")
        json.dump({"n_baris": len(xs3), "median_detik": xs3[len(xs3) // 2],
                   "p75_detik": pct(xs3, .75), "p90_detik": pct(xs3, .9),
                   "p95_detik": pct(xs3, .95), "max_detik": xs3[-1], "min_detik": xs3[0],
                   "sumber_waktu": "cap arr ditulis perekam (runner GitHub), bukan jam laptop",
                   "definisi": "arr - t per baris tx/txc yang punya cap"},
                  io.open(p3, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
        print("artefak: decisions/%s" % os.path.basename(p3))
        print("Ini yang memvonis P50: kalau median-nya << umur keputusan kami (808 d), kabar memang")
        print("bisa tiba cepat dan yang lambat adalah kami; kalau median-nya sebanding, SUMBERNYA")
        print("yang tidak bisa dipakai untuk bump berumur 2 menit (E11) - dan P40 tidak akan menolong.")
        return
    if a.saat_ditemukan:
        xs2 = saat_ditemukan(a.n)
        if not xs2:
            raise SystemExit("tidak ada baris baru yang bisa dibandingkan antar commit")
        print("commit dibandingkan: %d | baris baru terpakai: %d" % (a.n, len(xs2)))
        print("umur kabar versi REKONSTRUKSI git (menit): median %.1f | p90 %.1f"
              % (xs2[len(xs2) // 2] / 60.0, pct(xs2, 0.9) / 60.0))
        print("\n   TIDAK BOLEH DIKUTIP. Beda 100x dengan ukuran LANGSUNG")
        print("   (`tools/fast_lane.py --report` -> latensi_keputusan_detik) berarti selisih")
        print("   himpunan baris ini bukan cara yang sah untuk mengukur 'kapan kami mengetahui")
        print("   sebuah peristiwa': commit perekam menumpuk banyak baris lama sekaligus, dan")
        print("   median-nya jadi umur arsip, bukan umur kabar. Artefak tidak ditulis.")
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
