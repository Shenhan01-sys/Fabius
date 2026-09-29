"""E27 - bump pada venue yang bukunya HIDUP: apakah kabar ⑦ punya efek di luar venue kami?

Rangkaian malam ini: E11 menemukan bump pada deret **spot BSC** (+192,7 → +202,6 bps, placebo datar).
E26 mengujinya pada harga perp **venue kami** dan tidak menemukan apa pun (F-D58). Lalu P61
(`tools/gate_liveness.py`) membalik arah curiga kami: pada 35 kontrak yang sama, venue pembanding punya
**14 simbol HIDUP dan nol simbol MATI**, sementara venue kami 5 HIDUP dan 14 MATI (F-D59). Jadi "tidak
ada bump di perp" bisa berarti dua hal yang sangat berbeda: (a) bumpnya memang tidak ada, atau (b)
bumpnya ada tapi venue kami terlalu beku untuk menunjukkannya.

Alat ini memisahkan dua kemungkinan itu. Deretnya dari venue pembanding; **seluruh matematikanya
diimpor dari `tools/perp_bump.py`** - tidak ada salinan rumus, karena begitu ada dua salinan, yang
terbakar adalah angka yang tidak sebanding.

Pakai:  python -X utf8 tools/gate_bump.py                 # semua simbol kelas HIDUP di Gate
         python -X utf8 tools/gate_bump.py --kelas TIPIS   # sensitivitas
         python -X utf8 tools/gate_bump.py --self-test

Yang tetap tidak boleh disimpulkan: ini **bukan** jalur eksekusi kami - ExecutionVault kami bicara ke
venue lain. Jawaban "ada bump di sana" berarti ada alasan untuk mengintegrasikan, bukan alasan untuk
mengklaim uang hari ini.
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import perp_bump as PB  # noqa: E402  - nilai(), harga_pada(), jendela_median(), w(), H, MIN
import perp_liveness as PL  # noqa: E402
import gate_liveness as GL  # noqa: E402
import flow_cluster_test as FC  # noqa: E402

GATE = "gate"
BUTUH_HARI = 1


def artefak_p61():
    fs = sorted(glob.glob(os.path.join(ROOT, "decisions", "e20b-gate-liveness-*.json")))
    if not fs:
        raise SystemExit("belum ada artefak P61 - jalankan `python -X utf8 tools/gate_liveness.py` dulu; "
                         "tanpa itu tidak ada daftar simbol yang bisa diuji (ini urutan kerja, bukan "
                         "kegagalan pengukuran)")
    return json.load(io.open(fs[-1], encoding="utf-8")), os.path.basename(fs[-1])


def kejadian_gate(per_kelas, kelas_ok):
    """Buy ⑦ 24 jam pada simbol yang kelasnya `kelas_ok` di venue pembanding, dedupe 30 m/simbol."""
    batas = int(time.time()) - 86400
    rows = []
    for ln in io.open(PL.VB.FLOW, encoding="utf-8", errors="replace"):
        if not ln.startswith("{"):
            continue
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if r.get("k") not in ("tx", "txc") or not r.get("b"):
            continue
        y = str(r.get("y") or "").strip().upper()
        t = int(r.get("t") or 0)
        if t < batas or y not in per_kelas or per_kelas[y] not in kelas_ok:
            continue
        rows.append({"y": y, "t": t, "usd": float(r.get("u") or 0)})
    rows.sort(key=lambda x: (x["y"], x["t"]))
    out, last = [], {}
    for r in rows:
        if r["y"] in last and r["t"] - last[r["y"]] < PB.DEDUPE_MENIT * PB.MIN:
            continue
        last[r["y"]] = r["t"]
        out.append(r)
    return out


def jalan(kelas_ok, draws):
    d, nama = artefak_p61()
    per_kelas = {r["basis"]: r["kelas_gate"] for r in d["rows"]}
    gm = GL.daftar_kontrak()
    ev = kejadian_gate(per_kelas, kelas_ok)
    print("E27 | venue pembanding (%s), kelas %s: %d kejadian (dedupe %d m/simbol)"
          % (nama, "/".join(sorted(kelas_ok)), len(ev), PB.DEDUPE_MENIT))
    if len(ev) < 5:
        print("   n terlalu kecil - BELUM BISA DIUJI, bukan nol")
        return {"vonis": "BELUM BISA DIUJI", "n": len(ev)}
    seri, gagal = {}, []
    for y in sorted({e["y"] for e in ev}):
        if y not in gm:
            gagal.append((y, "tidak ada kontrak"))
            continue
        der, err = GL.klines_1m(gm[y], butuh=BUTUH_HARI * 1440)
        if der:
            seri[y] = der
        else:
            gagal.append((y, json.dumps(err)[:60]))
    pakai = [e for e in ev if e["y"] in seri]
    print("   kejadian dengan deret: %d dari %d (simbol %d); gagal: %s"
          % (len(pakai), len(ev), len({e["y"] for e in pakai}),
             ", ".join("%s(%s)" % g for g in gagal) or "tidak ada"))
    if len(pakai) < 5:
        print("   setelah kegagalan tidak ada yang tersisa untuk diuji - ini BUKAN hasil nol")
        return {"vonis": "BELUM BISA DIUJI", "n": len(pakai)}
    hasil = {}
    for h in PB.H:
        a = [x for x in (PB.nilai(seri[e["y"]], e, h) for e in pakai) if x is not None]
        b = [x for x in (PB.nilai(seri[e["y"]], e, h, 1) for e in pakai) if x is not None]
        if not a:
            print("      @%d m: 0 dari %d - tidak ada yang bisa dirata-ratakan" % (h, len(pakai)))
            continue
        rng = random.Random(20260929)
        pla = []
        for e in pakai:
            x = PB.nilai(seri[e["y"]], dict(e, t=e["t"] + rng.randrange(30, 91) * PB.MIN), h)
            if x is not None:
                pla.append(x)
        hasil[str(h)] = {"n": len(a), "hilang": len(pakai) - len(a), "menit": h,
                    "mean_winso": round(sum(PB.w(x) for x in a) / len(a), 1),
                    "median": round(FC.med(a), 1),
                    "telat1m_mean": round(sum(PB.w(x) for x in b) / len(b), 1) if b else None,
                    "placebo_mean": round(sum(PB.w(x) for x in pla) / len(pla), 1) if pla else None}
        print("      @%2d m | n=%-3d (%d hilang) | asli mean %+7.1f median %+7.1f | masuk +1 m %+7.1f | "
              "placebo %+7.1f" % (h, hasil[str(h)]["n"], hasil[str(h)]["hilang"],
                                  hasil[str(h)]["mean_winso"], hasil[str(h)]["median"],
                                  -999 if hasil[str(h)]["telat1m_mean"] is None
                                  else hasil[str(h)]["telat1m_mean"],
                                  -999 if hasil[str(h)]["placebo_mean"] is None
                                  else hasil[str(h)]["placebo_mean"]))
    if "5" in hasil and "30" in hasil:
        pair = [(PB.nilai(seri[e["y"]], e, 5), PB.nilai(seri[e["y"]], e, 30)) for e in pakai]
        pair = [(x, y) for x, y in pair if x is not None and y is not None]
        men = sum(1 for x, y in pair if x > y)
        ka = sum(1 for x, y in pair if x < y)
        p = FC.sign_p(men, men + ka) if men + ka >= 5 else None
        hasil["berpasangan"] = {"n": len(pair), "median_delta": round(FC.med([x - y for x, y in pair]), 1),
                                "menang_5m": men, "kalah_5m": ka, "p_tanda": p}
        print("      berpasangan 5m vs 30m (posisi sama): median %+0.1f bps | menang %d kalah %d | p=%s"
              % (hasil["berpasangan"]["median_delta"], men, ka, "-" if p is None else "%.5f" % p))
    print("\n   pembanding yang harus dibaca berdampingan: E26 di venue kami memberi @5 m +15,2 vs "
          "placebo +10,7 (p=0,50). Kalau di sini aslinya JAUH di atas placebo, berarti yang membunuh "
          "klaim kami selama ini adalah buku beku venue - bukan sinyalnya.")
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "venue": GATE,
           "kelas": sorted(kelas_ok), "artefak_p61": nama, "n_kejadian": len(pakai),
           "gagal_ambil": [list(g) for g in gagal], "horison": hasil,
           "perintah": "python -X utf8 tools/gate_bump.py",
           "batas": "bukan jalur eksekusi kami (ExecutionVault bicara ke venue lain); n=%d satu hari; "
                    "klines != kedalaman; TIDAK dikunci - ini eksplorasi pemisah hipotesis" % len(pakai)}
    p = os.path.join(ROOT, "decisions", "e27-gate-bump-%s.json"
                     % out["dibuat_utc"].replace(":", "").replace("-", ""))
    blob = json.dumps(out, indent=2, ensure_ascii=False, sort_keys=True)
    io.open(p, "w", encoding="utf-8", newline="\n").write(blob)
    print("   artefak:", os.path.relpath(p, ROOT))
    return out


def self_test():
    b = lambda t, c, v: {"t": t, "c": c, "v": v, "o": c, "h": c, "l": c}
    t0 = 1_800_000_000
    naik = [b((t0 + i * PB.MIN) * 1000, 1.0 * (1.0 + 0.003 * min(i, 3)), 4000.0) for i in range(400)]
    assert PB.nilai(naik, {"t": t0}, 2) > 20, PB.nilai(naik, {"t": t0}, 2)
    assert PB.nilai(naik, {"t": t0}, 2, 1) < PB.nilai(naik, {"t": t0}, 2)   # masuk telat = lebih kecil
    datar = [b((t0 + i * PB.MIN) * 1000, 1.0, 0.0) for i in range(400)]
    assert abs(PB.nilai(datar, {"t": t0}, 5)) < 1e-9
    # kejadian_gate() pada data nyata: dedupe harus menjauhkan dua kejadian simbol sama >= 30 m
    ev = kejadian_gate({"DOGE": "HIDUP", "LINK": "HIDUP", "ZEC": "HIDUP"}, {"HIDUP"})
    dari = {}
    for x in ev:
        assert x["t"] - dari.get(x["y"], -10 ** 9) >= PB.DEDUPE_MENIT * PB.MIN, (x, dari)
        dari[x["y"]] = x["t"]
    assert all(x["t"] > int(time.time()) - 86400 for x in ev), "jendela 24 jam tidak dijaga"
    print("self-test E27 OK: matematika diimpor dari E26 (tidak ada salinan rumus) | bump terukur | "
          "masuk +1 m lebih kecil dari masuk di harga kejadian | deret beku = 0")


def utama():
    ap = argparse.ArgumentParser(description="E27 bump pada venue pembanding")
    ap.add_argument("--kelas", default="HIDUP")
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    return jalan({x.strip().upper() for x in a.kelas.split(",")}, a.draws)


if __name__ == "__main__":
    utama()
