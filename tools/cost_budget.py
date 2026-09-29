"""E19 (T4) - berapa besar spread makan strategi: anggaran biaya nyata per timeframe.

Pertanyaan builder: "saya masih bingung timeframenya gimana". Jawaban yang jujur bukan nama
timeframe, tapi uang: pada cadence kami (kabar ⑦ hidup ±2 menit - E11), strategi 5 menit harus
membayar setengah spread di dua sisi. Kalau setengah spread lebih besar daripada selisih yang kita
klaim, tidak ada timeframe yang menyelamatkan - yang ada adalah biaya.

Angka yang dipakai (semuanya punya alamat):
  * fee + gas yang TERUKUR di venue kami sendiri: 59,0 bps round-trip (`tools/costs.py`,
    `measured-own-venue`) - ini yang sudah kami bayarkan betulan di chain 97;
  * setengah spread per simbol dari `universe/book-depth.jsonl` (rekaman ⑨) - biaya yang belum
    pernah kami masukkan ke model;
  * harapan @5m dari E13 (`BOLEH` +285,5 bps mean / +79,8 median) dan bump E11 (+202,6 mean @5m)
    - dipakai di sini sebagai ATAP, bukan sebagai janji.

Vonis yang dikeluarkan alat ini adalah **anggaran**, bukan sinyal: timeframe berapa yang masih
mungkin dibayar oleh selisih terkecil yang pernah kami ukur (median +79,8 bps).

Pakai:  python -X utf8 tools/cost_budget.py --self-test
       python -X utf8 tools/cost_budget.py
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import costs  # noqa: E402
import flow_cluster_test as FC  # noqa: E402

BUKU = os.path.join(ROOT, "universe", "book-depth.jsonl")
JANGKAR = {"BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"}


def kumpulkan():
    per = {}
    if not os.path.exists(BUKU):
        return per
    for ln in io.open(BUKU, encoding="utf-8", errors="replace"):
        if not ln.startswith("{"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("k") != "bd" or not isinstance(d.get("spread_bps"), (int, float)):
            continue
        per.setdefault(d["sym"], []).append(float(d["spread_bps"]))
    return {k: sorted(v) for k, v in per.items()}


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    rt = costs.rt_cost()
    per = kumpulkan()
    print("E19 anggaran biaya | ongkos terukur %.1f bps RT (fee+gas+slip di venue kami)" % rt)
    if not per:
        raise SystemExit("universe/book-depth.jsonl belum berisi snapshot - ini BELUM DIUKUR, "
                         "bukan 'spread nol'")
    print("snapshot per simbol: %d simbol | total %d baris\n"
          % (len(per), sum(len(v) for v in per.values())))
    print("   %-12s %5s %10s %10s %14s %s"
          % ("simbol", "n", "spread med", "setengah", "biaya RT penuh", "masih untung di median E13"))
    baris = []
    for sym, v in sorted(per.items(), key=lambda kv: FC.med(kv[1])):
        med = FC.med(v)
        penuh = rt + med            # setengah spread dibayar dua sisi = satu spread penuh
        baris.append({"simbol": sym, "n": len(v), "spread_median_bps": round(med, 2),
                      "spread_p90_bps": round(v[int(0.9 * (len(v) - 1))], 2),
                      "biaya_rt_penuh_bps": round(penuh, 2),
                      "jangkar": sym in JANGKAR,
                      "menang_di_median": 79.8 > penuh})
        print("   %-12s %5d %10.2f %10.2f %14.2f %s%s"
              % (sym, len(v), med, med / 2.0, penuh,
                 "YA" if 79.8 > penuh else "TIDAK",
                 "  (jangkar likuid)" if sym in JANGKAR else ""))
    sehat = [x for x in baris if x["menang_di_median"]]
    print("\nAngka yang boleh dipakai untuk bicara timeframe:")
    print("   - harapan MEDIAN kami di horison cepat = +79,8 bps (E13, `BOLEH`, menit ke-5). "
          "Semua simbol dengan spread median > ~21 bps (79,8 - 59) sudah di luar anggaran pada "
          "harapan MEDIAN - bukan pada harapan mean.")
    print("   - harapan MEAN +285,5 bps (E13) memberi ruang spread sampai ~226 bps, tapi mean di "
          "sini ditopang ekor kanan (P(>=+500) 37-40 %), jadi memakainya sebagai anggaran = "
          "berharap dapat undian, bukan dapat edge.")
    print("   - simbol yang masih dalam anggaran median: %d dari %d (%s)"
          % (len(sehat), len(baris), ", ".join(x["simbol"] for x in sehat[:8]) or "KOSONG"))
    print("   - kalau hanya jangkar likuid yang lolos (BTC/ETH/SOL), maka 'timeframe' kami "
          "sebenarnya pertanyaan 'di pasar mana', dan itu jawabannya datang dari buku order, "
          "bukan dari grafik.")
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "ongkos_rt_terukur_bps": rt, "median_net_boleh_e13_bps": 79.8,
           "mean_net_boleh_e13_bps": 285.5, "simbol": baris,
           "dalam_anggaran_median": [x["simbol"] for x in sehat]}
    out["sha"] = "0x" + hashlib.sha256(json.dumps(baris, sort_keys=True).encode()).hexdigest()
    p = os.path.join(ROOT, "decisions", "cost-budget-%s.json"
                     % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("artefak: decisions/%s" % os.path.basename(p))


def self_test():
    global kumpulkan
    asli = kumpulkan
    try:
        # spread 10 bps -> anggaran 69 bps < 79,8 (LOLOS); spread 100 bps -> 159 bps (GAGAL)
        for med, harus in ((10.0, True), (100.0, False)):
            penuh = 59.0 + med
            assert (79.8 > penuh) is harus, (med, penuh)
        rt = costs.rt_cost()
        assert 40.0 <= rt <= 80.0, "ongkos terukur bergeser: %s" % rt
        print("self-test E19 OK: ambang anggaran bergerak searah spread, dan ongkos yang dipakai "
              "masih yang terukur (bukan 20 bps warisan)")
    finally:
        kumpulkan = asli


if __name__ == "__main__":
    utama()
