"""P60 (sebagian) - apakah KUTIPAN juga beku, atau hanya TRANSAKSINYA?

E20 (F-D56) mengukur deret klines: dari 41 simbol reachable, hanya 5 yang menitnya benar-benar berisi
transaksi. Tapi klines = hasil dari order yang TERISI. ⑨ (`universe/record_book_depth.py`) merekam hal
yang berbeda: apa yang DITAWARKAN, 20 level, tiap ~200 detik. Kalau kutipan pun diam, venue itu tidak
hanya sepi - ia tidak menghargai informasi. Kalau kutipannya hidup tapi transaksinya nol, yang mati
adalah minat, bukan kuotasi - dan itu beda akibatnya untuk trailing stop (E17) maupun untuk slippage.

Yang diukur per simbol di sini:
  - persen snapshot yang best-bid DAN best-ask-nya SAMA persis dengan snapshot sebelumnya (kutipan beku)
  - run terpanjang kutipan beku, dalam snapshot DAN dalam menit nyata (`detik`)
  - spread bps (median/p90) dan kedalaman dalam ±10 dan ±50 bps dari mid (dalam unit kuotasi)
  - jumlah snapshot (supaya tidak ada yang dibaca sebagai nol padahal cuma sedikit data)

Alat ini HANYA menganalisis berkas yang sudah ada. Daftar pantau ⑨ TIDAK disentuh: F-D53 melarang frame
E16 diubah di tengah jendela, dan aturan itu masih berlaku sampai vonisnya (21:37:45Z).

Pakai:  python -X utf8 tools/book_stale.py                # semua simbol
         python -X utf8 tools/book_stale.py --simbol ASTERUSDT,BOMEUSDT
         python -X utf8 tools/book_stale.py --self-test
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import flow_cluster_test as FC  # noqa: E402

DEPTH = os.path.join(ROOT, "universe", "book-depth.jsonl")
SAMBUNG_MENIT = 12          # jarak antar snapshot di atas ini = bukan run yang sama


def baca(simbol=None):
    per = {}
    for ln in io.open(DEPTH, encoding="utf-8", errors="replace"):
        if not ln.startswith("{"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("k") != "bd":
            continue
        sym = str(d.get("sym") or "").upper()
        if not sym or (simbol and sym not in simbol):
            continue
        per.setdefault(sym, []).append(d)
    for v in per.values():
        v.sort(key=lambda x: int(x.get("detik") or 0))
    return per


def ketebalan(levels, mid, bps, sisi):
    if not levels or not mid:
        return None
    batas_atas = mid * (1.0 + bps / 1e4)
    batas_bawah = mid * (1.0 - bps / 1e4)
    tot = 0.0
    for px, qty in levels:
        try:
            p, q = float(px), float(qty)
        except (TypeError, ValueError):
            continue
        if sisi == "ask" and p <= batas_atas:
            tot += p * q
        elif sisi == "bid" and p >= batas_bawah:
            tot += p * q
    return tot


def ukur(sym, snaps):
    if len(snaps) < 3:
        return {"simbol": sym, "snapshot": len(snaps), "kelas": "TERLALU-SEDIKIT"}
    sama = run = run_menit = 0
    kini = kini_t = 0
    spread = []
    d10, d50 = [], []
    for i, d in enumerate(snaps):
        m = float(d.get("mid") or 0)
        sp = d.get("spread_bps")
        if isinstance(sp, (int, float)):
            spread.append(float(sp))
        d10.append(ketebalan(d.get("bids"), m, 10, "bid"))
        d10.append(ketebalan(d.get("asks"), m, 10, "ask"))
        d50.append(ketebalan(d.get("bids"), m, 50, "bid"))
        d50.append(ketebalan(d.get("asks"), m, 50, "ask"))
        if i == 0:
            prev = d
            kini = kini_t = 0
            continue
        bb = (d["bids"][0][0] if d.get("bids") else None, d["asks"][0][0] if d.get("asks") else None)
        pb = (prev["bids"][0][0] if prev.get("bids") else None,
              prev["asks"][0][0] if prev.get("asks") else None)
        dt = int(d.get("detik") or 0) - int(prev.get("detik") or 0)
        if bb == pb and dt <= SAMBUNG_MENIT * 60:
            sama += 1
            kini += 1
            kini_t += dt
            run = max(run, kini)
            run_menit = max(run_menit, kini_t // 60)
        else:
            kini = 0
            kini_t = 0
        prev = d
    nums = [x for x in d10 if x is not None]
    nums50 = [x for x in d50 if x is not None]
    return {"simbol": sym, "snapshot": len(snaps), "kutipan_beku_persen": round(100.0 * sama / (len(snaps) - 1), 1),
            "run_beku_snapshot_maks": run, "run_beku_menit_maks": run_menit,
            "spread_bps_median": round(FC.med(spread), 2) if spread else None,
            "spread_bps_p90": round(sorted(spread)[int(0.9 * (len(spread) - 1))], 2) if spread else None,
            "kedalaman10bps_median": round(FC.med(nums), 2) if nums else None,
            "kedalaman50bps_median": round(FC.med(nums50), 2) if nums50 else None,
            "tanpa_kedalaman": sum(1 for x in d10 if x is None),
            "rentang_menit": round((int(snaps[-1]["detik"]) - int(snaps[0]["detik"])) / 60.0, 1),
            "kelas": "OK"}


def jalan(simbol):
    if not os.path.exists(DEPTH):
        raise SystemExit("⑨ belum menulis apa pun di mesin ini - jalankan dari clone yang punya "
                         "universe/book-depth.jsonl")
    per = baca(simbol)
    print("P60 | %d simbol dengan snapshot buku order (sumber: universe/book-depth.jsonl)" % len(per))
    rows = []
    for sym in sorted(per, key=lambda s: -len(per[s])):
        u = ukur(sym, per[sym])
        rows.append(u)
        if u["kelas"] != "OK":
            print("   %-14s %3d snapshot - %s (jangan dibaca sebagai nol)"
                  % (sym, u["snapshot"], u["kelas"]))
            continue
        print("   %-14s %3d snapshot | kutipan beku %5.1f%% | run beku maks %3d snapshot / %4d m | "
              "spread %7s bps (p90 %7s) | tebal ±10bps %12s | ±50bps %12s | rentang %6s m"
              % (sym, u["snapshot"], u["kutipan_beku_persen"], u["run_beku_snapshot_maks"],
                 u["run_beku_menit_maks"], u["spread_bps_median"], u["spread_bps_p90"],
                 u["kedalaman10bps_median"], u["kedalaman50bps_median"], u["rentang_menit"]))
    o = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "sumber": "universe/book-depth.jsonl", "ambang_sambung_menit": SAMBUNG_MENIT, "rows": rows,
         "perintah": "python -X utf8 tools/book_stale.py",
         "catatan": "kedalaman dalam UNIT KUOTASI (px*qty), belum dikonversi USD; snapshot ~200 d "
                    "sehingga run beku dalam menit adalah batas bawah dari lama kutipan diam"}
    blob = json.dumps(o, indent=2, ensure_ascii=False, sort_keys=True)
    p = os.path.join(ROOT, "decisions", "p60-book-staleness-%s.json"
                     % o["dibuat_utc"].replace(":", "").replace("-", ""))
    io.open(p, "w", encoding="utf-8", newline="\n").write(blob)
    print("   artefak:", os.path.relpath(p, ROOT))
    return o


def self_test():
    def baris(detik, bid, ask, qb="1.0", qa="1.0"):
        return {"k": "bd", "sym": "UJIUSDT", "detik": detik, "mid": (float(bid) + float(ask)) / 2.0,
                "spread_bps": (float(ask) - float(bid)) / ((float(bid) + float(ask)) / 2.0) * 1e4,
                "bids": [[bid, qb], [str(float(bid) * 0.999), "2.0"]],
                "asks": [[ask, qa], [str(float(ask) * 1.001), "2.0"]]}
    beku = [baris(1000 + i * 200, "100.0", "100.1") for i in range(6)]
    u = ukur("UJIUSDT", beku)
    assert u["kutipan_beku_persen"] > 79.0, u          # 5 dari 6 transisi identik
    assert u["run_beku_snapshot_maks"] == 5 and u["run_beku_menit_maks"] == (6 - 1) * 200 // 60, u
    # (6 snapshot berjarak 200 d = 5 transisi beku = 16 menit, bukan 10 - ekspektasiku
    #  yang salah di pertama kali, alatnya benar)
    hidup = [baris(1000 + i * 200, str(100.0 + i * 0.1), str(100.1 + i * 0.1)) for i in range(6)]
    v = ukur("UJIUSDT", hidup)
    assert v["kutipan_beku_persen"] == 0.0 and v["run_beku_snapshot_maks"] == 0, v
    # celah waktu > SAMBUNG_MENIT tidak boleh dihitung sebagai satu run panjang
    bolong = [baris(1000, "100.0", "100.1"), baris(1000 + 3600, "100.0", "100.1"),
              baris(1000 + 3600 + 200, "100.0", "100.1")]
    w = ukur("UJIUSDT", bolong)
    assert w["run_beku_snapshot_maks"] <= 1, w
    assert ukur("UJIUSDT", beku[:2])["kelas"] == "TERLALU-SEDIKIT"
    assert abs(ketebalan([["100.0", "2.0"], ["99.0", "1.0"]], 100.0, 50, "bid") - 200.0) < 1e-6
    print("self-test P60 OK: kutipan beku vs hidup terpisah | run terputus oleh celah waktu | "
          "<3 snapshot -> TERLALU-SEDIKIT bukan nol | ketebalan dalam unit kuotasi teruji")


def utama():
    ap = argparse.ArgumentParser(description="P60: beku kutipan atau beku transaksi?")
    ap.add_argument("--simbol", default="")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    sim = {x.strip().upper() for x in a.simbol.split(",") if x.strip()} or None
    return jalan(sim)


if __name__ == "__main__":
    utama()
