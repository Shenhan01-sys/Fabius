"""P167b (epik 12 §3.2): bukti jalur sandbox `kind=code` pada data NYATA. B1-TREND ditulis ulang sebagai KODE penerbit (`engine/tests/test_kode.py::TREN`)
dan dijalankan lewat pelari lokal (proses anak berbatas, dua proses PYTHONHASHSEED berbeda, sampel kausalitas namespace segar) pada SELURUH
`ledger/bars` (universe B1). Mencetak per N: hari, hari berposisi, hari beda bobot vs template B1 (bit-ke-bit), beda PnL harian maksimum
(toleransi 1e-12 = `ledger.SETTLE_TOL`: urutan kunci dict kode berbeda dari template, jadi urutan penjumlahan float `replay` berbeda), deterministik,
sampel kausalitas, dan waktu dinding dua jalan sandbox. Kode keluar 0 hanya bila bobot identik, PnL dalam toleransi, dan semua uji sandbox lolos.

Pakai:  python -X utf8 tools/kode_ekuivalensi.py [--bars ledger/bars] [--gerbang]
        --gerbang: juga G1-G11 + KPI penuh (GateParams bawaan, petahana = buku slot sekarang) atas bot code N=60 lewat sandbox; mencetak status
                   tiap gerbang, vonis, dan waktu dinding (tanpa klaim: B1 sebagai kode menilai jalur, bukan strategi baru)
"""
from __future__ import annotations

import argparse
import dataclasses
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine import cli, kode                                               # noqa: E402
from engine.bots import REGISTRY                                           # noqa: E402
from engine.data import load_csv_dir                                       # noqa: E402
from engine.replay import replay                                           # noqa: E402
from engine.spec import SPECS, BotSpec                                     # noqa: E402
from engine.tests.test_kode import TREN                                    # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bars", default=os.path.join(ROOT, "ledger", "bars"))
    ap.add_argument("--gerbang", action="store_true")
    a = ap.parse_args()
    md = load_csv_dir(a.bars, cli.DATA_SYMBOLS)
    uni = SPECS["B1-TREND"].universe
    print(f"data: {len(md.perp)} aset perp, {len(md.perp['BTCUSDT'])} bar BTC; universe B1 {len(uni)} aset")
    pel = kode.PelariLokal()
    kode.pasang_pelari(pel)
    sha = pel.daftarkan(TREN)
    m, info = kode.periksa(TREN)
    bars = kode.bars_payload(md, uni)
    grid = sorted({t for x in bars for t in bars[x]["t"]})
    ok = not m
    for n in (60, 30, 90):
        base = dataclasses.replace(SPECS["B1-TREND"], param=n)
        sp = BotSpec(bot_id="KODE-B1", metode="B1 sebagai kode", param_nama=kode.PARAM_NAMA, param=sha,
                     konstanta={"kode": {"sha": sha, "ukuran": info["ukuran"], "params": {"N": n}}}, universe=uni, penggaris=dict(base.penggaris),
                     template=kode.KODE_METHOD)
        t0 = time.time()
        r = kode.jalankan(TREN, bars, {"dasar": {"N": n}}, kode.sampel_kausal(grid, 12), "dasar")
        dt = time.time() - t0
        ta, tb = REGISTRY["B1-TREND"](base, md), REGISTRY[kode.KODE_METHOD](sp, md)
        same_t = [t.t for t in ta] == [t.t for t in tb]
        beda = sum(1 for x, y in zip(ta, tb) if x.weights != y.weights)
        pa, pb = replay(base, md, ta), replay(base, md, tb)
        dmax = max((abs(x[1] - y[1]) for x, y in zip(pa, pb)), default=0.0)
        pnl_same = [x[0] for x in pa] == [y[0] for y in pb] and dmax <= 1e-12             # urutan dict beda -> urutan penjumlahan float beda (toleransi ledger)
        k = r.get("kausal") or {}
        lolos = same_t and beda == 0 and pnl_same and r.get("ok") and r.get("deterministik") is True and not k.get("beda") and k.get("n", 0) > 0
        ok = ok and bool(lolos)
        print(f"B1 N={n}: {len(tb)} hari, berposisi {sum(1 for t in tb if t.weights)}, hari beda bobot {beda}, PnL sama (maks |beda| {dmax:.1e} <= 1e-12) "
              f"{'ya' if pnl_same else 'TIDAK'}, "
              f"deterministik {r.get('deterministik')}, sampel kausal {k.get('n', 0) - len(k.get('beda') or [])}/{k.get('n', 0)}, "
              f"dua jalan sandbox {dt:.1f} s -> {'SAMA' if lolos else 'BEDA'}")
    print("SEMUA SAMA (bobot bit-ke-bit; PnL harian <= 1e-12)" if ok else "ADA YANG BEDA")
    if a.gerbang:
        from engine.gates import GateParams, run_gates, verdict
        sp60 = BotSpec(bot_id="KODE-B1", metode="B1 sebagai kode", param_nama=kode.PARAM_NAMA, param=sha,
                       konstanta={"kode": {"sha": sha, "ukuran": info["ukuran"], "params": {"N": 60}}}, universe=uni,
                       penggaris=dict(SPECS["B1-TREND"].penggaris), template=kode.KODE_METHOD)
        t0 = time.time()
        res = run_gates(sp60, md, cli._incumbents(md, "book"), GateParams())
        print("gerbang (kode N=60, sandbox): " + " ".join(f"{r.gate}:{r.status}" for r in res))
        for r in res:
            if r.gate in ("G1", "G5", "G8", "G10"):
                print(f"  {r.gate} {r.status} {r.value}")
        print(f"vonis {verdict(res)[0]} dalam {time.time() - t0:.0f} s")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
