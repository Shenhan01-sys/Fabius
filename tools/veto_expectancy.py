"""E13 - apakah REM (`jual_*`) yang mengubah harapan, atau cuma mengubah daftar?

Sampai 29 Sep, satu-satunya perilaku Fabius yang bertahan setelah empat koreksi alat (F-D30 harga
masuk beku, F-D32 control mempromosikan dirinya, F-D37 MW salah urut, F-D39 satu undian disebut
hasil, F-D40 kontrol keluar yang salah) adalah **menolak**: kerumunan jual dalam jendela ⑦
mematikan posisi. Angka yang membuatnya terpasang (F-D31, `tools/policy_test.py`) membandingkan
harapan **di horison 30 menit** - horison yang sejak E11/F-D41 kami tahu sedang bocor.

Pertanyaan yang belum dijawab karena itu: **rem yang sama bekerja di horison tempat kabar itu hidup
tidak?** Kalau iya, kombinasi "gerbang + keluar cepat" adalah satu kalimat yang bisa kami pertanggung
jawabkan; kalau tidak, gerbang itu hanya berlaku untuk gaya trading yang sudah kami tinggalkan.

Yang dilakukan: tiap kejadian beli diukur tiga kali (2, 5, 30 menit) dan ditandai dengan status
gerbang ⑦ pada jam kejadian itu - `BOLEH` / `VETO` / `TAK ADA DATA` - pakai kode yang sama dengan
agen (`tools/flow_gate.py`, bukan reimplementasi). Lalu:

  bandingkan  = harapan(BOLEH) - harapan(VETO) pada horison yang sama, posisi berbeda, jendela sama
  sensor      = n tiap kelompok, P(ada harga keluar) tiap kelompok, umur baris harga keluar
  placebo     = kelompok "BOLEH palsu" yang diacak dari daftar yang sama (F-D40): kalau acak
                menghasilkan selisih sebesar ini, tidak ada yang perlu dilaporkan

Sama seperti E11: mean dilaporkan MEDIAN dari banyak pengulangan (F-D39), dan vonis tidak boleh
dibalik arah. EKSPLORASI pada data sampai `t_kunci` watch - uji terkunci yang berdiri di depan adalah
E12 (`tools/hold_ab.py`), bukan halaman ini.

Pakai:  python -X utf8 tools/veto_expectancy.py
       python -X utf8 tools/veto_expectancy.py --draws 200
       python -X utf8 tools/veto_expectancy.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import costs  # noqa: E402
import flow_cluster_test as FC  # noqa: E402
import flow_gate as FG  # noqa: E402
import horizon_decay as HD  # noqa: E402
import topk_test as TK  # noqa: E402

MIN = 60
WINS = 2000.0
HORISON = (2, 5, 30)


def w(x):
    return max(-WINS, min(WINS, x))


def kelompok(ev, rt):
    """Tiap kejadian: status gerbang ⑦ saat itu + net pada tiap horison."""
    out = []
    for e in ev:
        g = FG.state(e["tk"], now=e["t"])
        baris = {"tk": e["tk"], "t": e["t"], "gerbang": g["status"],
                 "alasan": (g.get("alasan") or "")[:80]}
        for h in HORISON:
            v = HD.net_pada(e, h, rt)
            u = HD.umur_keluar(e, h)
            baris["h%d" % h] = v
            baris["umur%d" % h] = None if u is None else round(u / 60.0, 2)
        out.append(baris)
    return out


def hitung(rows, rnd, draws):
    res = {}
    for h in HORISON:
        boleh = [w(r["h%d" % h]) for r in rows if r["gerbang"] == "BOLEH"
                 and isinstance(r["h%d" % h], (int, float))]
        veto = [w(r["h%d" % h]) for r in rows if r["gerbang"] == "VETO"
                and isinstance(r["h%d" % h], (int, float))]
        ttd = [r for r in rows if r["gerbang"] == "TAK ADA DATA"]
        if len(boleh) < 10 or len(veto) < 10:
            res[str(h)] = {"n_boleh": len(boleh), "n_veto": len(veto),
                           "status": "BELUM BISA DIUJI (kelompok kecil)"}
            continue
        sel = sum(boleh) / len(boleh) - sum(veto) / len(veto)
        pool = boleh + veto
        nb, nv = len(boleh), len(veto)
        acak = []
        for _ in range(draws):
            idx = list(range(len(pool)))
            rnd.shuffle(idx)
            b = [pool[i] for i in idx[:nb]]
            v = [pool[i] for i in idx[nb:nb + nv]]
            acak.append(sum(b) / nb - sum(v) / nv)
        acak.sort()
        res[str(h)] = {"n_boleh": nb, "n_veto": nv, "n_tanpa_data": len(ttd),
                      "mean_boleh": round(sum(boleh) / nb, 1),
                      "median_boleh": round(FC.med(boleh), 1),
                      "mean_veto": round(sum(veto) / nv, 1),
                      "median_veto": round(FC.med(veto), 1),
                      "selisih_bps": round(sel, 1),
                      "acak_mean": round(sum(acak) / len(acak), 1),
                      "acak_ci_atas": round(acak[int(0.975 * len(acak))], 1),
                      "di_atas_acak": sel > acak[int(0.975 * len(acak))],
                      "P_ada_harga_keluar_boleh": round(
                          100.0 * nb / max(1, sum(1 for r in rows if r["gerbang"] == "BOLEH")), 1),
                      "umur_keluar_menit": FC.med([r["umur%d" % h] for r in rows
                                                   if isinstance(r["umur%d" % h], float)])}
    return res


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    rt = costs.rt_cost()
    ev, sensor = HD.kejadian(max(HORISON))
    print("E13 gerbang x horison | %d kejadian | horison %s m | ongkos %.1f bps RT | batas %s"
          % (len(ev), HORISON, rt, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(TK.T_BATAS))))
    rows = kelompok(ev, rt)
    hit = {}
    for g in ("BOLEH", "VETO", "TAK ADA DATA"):
        hit[g] = sum(1 for r in rows if r["gerbang"] == g)
    print("status gerbang saat kejadian: %s" % json.dumps(hit, sort_keys=True))
    if min(hit.get("BOLEH", 0), hit.get("VETO", 0)) < 10:
        print("\nCATATAN: salah satu kelompok keputusan (BOLEH/VETO) berisi < 10 kejadian. "
              "TAK ADA DATA = 0 di sini berarti gerbang tidak pernah buta pada jendela ini - itu "
              "BUKAN kegagalan, dan tetap bukan alasan untuk mengecilkan yang lain.")
    rnd = random.Random(20260929)
    res = hitung(rows, rnd, a.draws)
    print("\n   %7s %9s %9s %12s %12s %11s %11s %12s %12s %s"
          % ("horison", "n boleh", "n veto", "mean boleh", "mean veto", "med boleh", "med veto",
             "selisih", "CI atas acak", "vonis"))
    for h, v in sorted(res.items(), key=lambda kv: int(kv[0])):
        if v.get("status"):
            print("   %7s %9d %9d  %s" % (h, v["n_boleh"], v["n_veto"], v["status"]))
            continue
        print("   %7s %9d %9d %+12.1f %+12.1f %+11.1f %+11.1f %+12.1f %+12.1f %s"
              % (h, v["n_boleh"], v["n_veto"], v["mean_boleh"], v["mean_veto"], v["median_boleh"],
                 v["median_veto"], v["selisih_bps"],
                 v["acak_ci_atas"], "DI ATAS ACAK" if v["di_atas_acak"] else "di bawah acak"))
    lulus = [h for h, v in res.items() if v.get("di_atas_acak")]
    print("\nE13: horison tempat rem mengubah harapan melewati placebo: %s" % (lulus or "TIDAK ADA"))
    if lulus:
        print("   itu tetap EKSPLORASI pada data sampai t_kunci. Yang berdiri di depan adalah E12 "
              "(`tools/hold_ab.py`, vonis 20:04:56Z), dan E12 tidak mengubah aturannya karena "
              "halaman ini.")
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "kejadian": len(ev),
           "sensor": sensor, "status_gerbang": hit, "horison_menit": list(HORISON),
           "hasil": res, "lulus": lulus, "draws": a.draws}
    out["sha"] = "0x" + hashlib.sha256(json.dumps(res, sort_keys=True).encode()).hexdigest()
    p = os.path.join(ROOT, "decisions", "veto-expectancy-%s.json"
                     % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("artefak: decisions/%s" % os.path.basename(p))


def self_test():
    """Rem harus TERLIHAT berpengaruh saat memang ada bedanya, dan tidak saat tidak ada."""
    rows = []
    for i in range(60):
        rows.append({"tk": "0x%d" % i, "t": 1_000_000 + i, "gerbang": "BOLEH" if i % 2 == 0 else
                     "TAK ADA DATA" if i % 3 == 0 else "VETO",
                     "h2": (120.0 if i % 2 == 0 else -120.0), "h5": (200.0 if i % 2 == 0 else -200.0),
                     "h30": (60.0 if i % 2 == 0 else -60.0), "umur2": 0.1, "umur5": 0.1,
                     "umur30": 0.1})
    rnd = random.Random(1)
    res = hitung(rows, rnd, 120)
    assert res["5"]["n_boleh"] == 30 and res["5"]["n_veto"] == 20, res
    assert res["5"]["selisih_bps"] > 300, res["5"]
    for h in ("2", "5", "30"):
        assert isinstance(res[h]["P_ada_harga_keluar_boleh"], float), res[h]
        assert isinstance(res[h]["umur_keluar_menit"], float), res[h]
    # keadaan tanpa efek: semua angka sama -> tidak boleh ada yang 'DI ATAS ACAK'
    datar = [dict(r, h2=50.0, h5=50.0, h30=50.0) for r in rows]
    res2 = hitung(datar, rnd, 120)
    assert not any(v.get("di_atas_acak") for v in res2.values()), res2
    print("self-test E13 OK: selisih terdeteksi saat ada, tidak terdeteksi saat nol, sensor ikut "
          "dilaporkan")


if __name__ == "__main__":
    utama()
