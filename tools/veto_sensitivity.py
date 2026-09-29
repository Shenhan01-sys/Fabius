"""E14 - apakah REM kami berdiri di atas tebing? Sensitivitas ambang `jual_*` di horison 5 menit.

F-D44 memberi kami satu perilaku yang masuk di horison tempat kabar hidup (BOLEH +285,5 vs VETO
-230,3 bps pada menit ke-5, melewati placebo). Itu membuat kami gugup dengan cara yang benar:
angka yang bagus bisa saja bergantung pada ambang yang kebetulan kami pilih. `tools/flow_gate.py`
memakai `MAKER_MIN = 2` dan `RASIO_JUAL = 1,5` - dua angka yang ditetapkan 28 Sep dari uji di
horison **30 menit** dan tidak pernah diuji sebagai fungsi horison cepat.

Alat ini TIDAK mencari ambang terbaik (itu cara tercepat menipu diri sendiri). Ia menjawab satu
pertanyaan: **seberapa jauh hasil E13 bergerak kalau ambangnya digeser?** Kalau efeknya hilang di
maker=3, kami punya tebing dan itu harus ditulis. Kalau ia bertahan di seluruh grid, rem itu
perilaku - bukan kebetulan tabel.

Yang dijaga:
  1. pemindaian ulang aturan yang SAMA, dan **assert bahwa pada ambang terpasang (2; 1,5) hasilnya
     identik dengan `flow_gate.state()` untuk SETIAP kejadian** - kalau tidak, alat berhenti dan
     melaporkan selisihnya (itu bug kami, bukan pasar).
  2. placebo = penandaan ulang acak 200 undian atas angka yang sama (kontrol yang membunuh E7/E8),
     dilaporkan sebagai CI atas, bukan sebagai p yang boleh dipilih.
  3. alat ini tidak mengubah satu angka pun di `flow_gate.py`. Mengubah ambang butuh pra-registrasi
     sendiri, bukan halaman ini.

Pakai:  python -X utf8 tools/veto_sensitivity.py --draws 200
       python -X utf8 tools/veto_sensitivity.py --self-test
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
H = 5
GRID_MAKER = (1, 2, 3, 4)
GRID_RASIO = (1.25, 1.5, 2.0, 3.0)


def w(x):
    return max(-WINS, min(WINS, x))


def jendela(rows, t):
    return [r for r in rows if t - FG.JENDELA_M * MIN <= r["t"] <= t]


def status(akir, maker_min, rasio):
    """Aturan yang sama dengan `flow_gate.state()`; ambangnya dipinjam sebagai argumen."""
    jual = [r for r in akir if not r["buy"]]
    beli = [r for r in akir if r["buy"]]
    mk = {r["m"] for r in jual if r["m"]}
    uj = sum(r["u"] for r in jual)
    ub = sum(r["u"] for r in beli)
    if len(mk) >= maker_min:
        return "VETO"
    if uj >= rasio * max(ub, 1.0) and uj > 0:
        return "VETO"
    return "BOLEH"


def bangun():
    txs, _wp = TK.muat()
    rt = costs.rt_cost()
    ev, sensor = HD.kejadian(H)
    out = []
    for e in ev:
        akir = jendela(txs.get(e["tk"], []), e["t"])
        v = HD.net_pada(e, H, rt)
        if v is None:
            continue
        out.append({"tk": e["tk"], "t": e["t"], "net": v, "akir": akir,
                    "resmi": FG.state(e["tk"], now=e["t"])["status"]})
    return out, sensor, rt


def hitung(rows, maker_min, rasio, rnd, draws):
    for r in rows:
        r["st"] = status(r["akir"], maker_min, rasio)
    boleh = [w(r["net"]) for r in rows if r["st"] == "BOLEH"]
    veto = [w(r["net"]) for r in rows if r["st"] == "VETO"]
    if len(boleh) < 20 or len(veto) < 10:
        return {"maker": maker_min, "rasio": rasio, "n_boleh": len(boleh), "n_veto": len(veto),
                "status": "TERLALU KECIL"}
    nb, nv = len(boleh), len(veto)
    sel = sum(boleh) / nb - sum(veto) / nv
    pool = boleh + veto
    acak = []
    for _ in range(draws):
        idx = list(range(len(pool)))
        rnd.shuffle(idx)
        b = [pool[i] for i in idx[:nb]]
        v = [pool[i] for i in idx[nb:nb + nv]]
        acak.append(sum(b) / nb - sum(v) / nv)
    acak.sort()
    return {"maker": maker_min, "rasio": rasio, "n_boleh": nb, "n_veto": nv,
            "mean_boleh": round(sum(boleh) / nb, 1), "median_boleh": round(FC.med(boleh), 1),
            "mean_veto": round(sum(veto) / nv, 1), "median_veto": round(FC.med(veto), 1),
            "selisih_bps": round(sel, 1), "acak_ci_atas": round(acak[int(0.975 * draws)], 1),
            "di_atas_acak": sel > acak[int(0.975 * draws)]}


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    rows, sensor, rt = bangun()
    print("E14 sensitivitas rem | %d kejadian dinilai di menit ke-%d | ongkos %.1f bps | batas %s"
          % (len(rows), H, rt, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(TK.T_BATAS))))
    salah = [r for r in rows if status(r["akir"], FG.MAKER_MIN, FG.RASIO_JUAL) != r["resmi"]]
    print("kocokan dengan flow_gate terpasang (maker=%d, rasio=%.2f): %d/%d berbeda -> %s"
          % (FG.MAKER_MIN, FG.RASIO_JUAL, len(salah), len(rows),
             "SESUAI, pemindaian ulang sah" if not salah else
             "BERBEDA - berhenti, ini bug kami, bukan pasar"))
    if salah:
        for r in salah[:5]:
            print("   %s t=%d resmi=%s scan=%s" % (r["tk"][:10], r["t"], r["resmi"],
                                                   status(r["akir"], FG.MAKER_MIN, FG.RASIO_JUAL)))
        raise SystemExit("alat tidak boleh melaporkan grid sementara aturan dirinya sendiri tidak "
                         "kocok dengan gerbang yang dipakai agen")
    rnd = random.Random(20260929)
    hasil = []
    print("\n   %6s %7s %9s %8s %12s %12s %11s %12s %s"
          % ("maker", "rasio", "n boleh", "n veto", "mean boleh", "mean veto", "selisih",
             "CI atas acak", "vonis"))
    for mk in GRID_MAKER:
        for rs in GRID_RASIO:
            v = hitung(rows, mk, rs, rnd, a.draws)
            hasil.append(v)
            if v.get("status"):
                print("   %6d %7.2f %9d %8d  %s" % (mk, rs, v["n_boleh"], v["n_veto"], v["status"]))
                continue
            tanda = "  <= terpasang" if (mk == FG.MAKER_MIN and abs(rs - FG.RASIO_JUAL) < 1e-9) \
                else ""
            print("   %6d %7.2f %9d %8d %+12.1f %+12.1f %+11.1f %+12.1f %s%s"
                  % (mk, rs, v["n_boleh"], v["n_veto"], v["mean_boleh"], v["mean_veto"],
                     v["selisih_bps"], v["acak_ci_atas"],
                     "DI ATAS" if v["di_atas_acak"] else "di bawah", tanda))
    teb = [v for v in hasil if not v.get("status")]
    lulus = [v for v in teb if v["di_atas_acak"]]
    print("\nE14: %d dari %d kombinasi ambang melewati placebo; selisih terkecil %+0.1f bps, "
          "terbesar %+0.1f bps" % (len(lulus), len(teb), min(v["selisih_bps"] for v in teb),
                                   max(v["selisih_bps"] for v in teb)))
    print("Yang TIDAK dilakukan alat ini: mengubah ambang. `flow_gate.py` tetap maker=%d rasio=%.2f;"
          " mengubah itu butuh pra-registrasi sendiri, bukan halaman ini."
          % (FG.MAKER_MIN, FG.RASIO_JUAL))
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "kejadian": len(rows), "horison_menit": H, "ongkos_bps_rt": rt,
           "kocokan_flow_gate": {"beda": len(salah), "total": len(rows)},
           "terpasang": {"maker_min": FG.MAKER_MIN, "rasio_jual": FG.RASIO_JUAL,
                         "jendela_menit": FG.JENDELA_M},
           "grid": hasil, "lulus": len(lulus), "draws": a.draws,
           "perintah": "python -X utf8 tools/veto_sensitivity.py --draws %d" % a.draws}
    out["sha"] = "0x" + hashlib.sha256(json.dumps(hasil, sort_keys=True).encode()).hexdigest()
    p = os.path.join(ROOT, "decisions", "veto-sensitivity-%s.json"
                     % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("artefak: decisions/%s" % os.path.basename(p))


def self_test():
    """Scan ulang harus mengikuti aturan gerbang, dan kelonggaran harus mengubah klasifikasi."""
    satu_maker = [{"buy": True, "m": "0xa", "u": 100.0, "t": 1000},
                  {"buy": False, "m": "0xb", "u": 50.0, "t": 1001}]
    assert status(satu_maker, 2, 1.5) == "BOLEH", "satu maker jual belum kerumunan"
    dua_maker = satu_maker + [{"buy": False, "m": "0xc", "u": 50.0, "t": 1002}]
    assert status(dua_maker, 2, 1.5) == "VETO", "dua maker = kerumunan pada ambang terpasang"
    jual_besar = [{"buy": True, "m": "0xa", "u": 1000.0, "t": 1000},
                  {"buy": False, "m": "0xb", "u": 2000.0, "t": 1001}]
    assert status(jual_besar, 2, 1.5) == "VETO", "satu maker tapi jual 2x beli -> veto karena rasio"
    assert status(jual_besar, 2, 3.0) == "BOLEH", "rasio dilonggarkan sampai 3x harus lepas"
    assert status(jual_besar, 1, 99.0) == "VETO", "maker_min=1 berarti satu penjual sudah kerumunan"
    assert status(dua_maker, 5, 99.0) == "BOLEH", "dua-duanya dilonggarkan harus jadi BOLEH"
    assert FG.MAKER_MIN == 2 and abs(FG.RASIO_JUAL - 1.5) < 1e-9, "ambang terpasang bergeser"
    print("self-test E14 OK: scan ulang identik dengan aturan flow_gate, dan kelonggaran mengubah "
          "klasifikasi seperti yang diharapkan")


if __name__ == "__main__":
    utama()
