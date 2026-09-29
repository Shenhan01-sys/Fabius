"""E11 - berapa lama menahan posisi? Kurva harapan sebagai fungsi UMUR posisi.

Kenapa alat ini ada (29 Sep 2026, setelah F-D40). E8 (keluar saat kerumunan) gugur lawan kontrol
"keluar di waktu acak", dan itu meninggalkan satu penjelasan yang belum diukur sendiri: kalau
harapan memburuk seiring umur posisi, maka "keluar lebih awal" bukan strategi - itu **menghentikan
pendarahan**, dan agen yang menahan 30 menit sedang membayar untuk sesuatu yang ia kira analisis.

Pertanyaan yang dijawab: bukan "kapan masuk", tapi **berapa lama boleh memegang** - satu-satunya
knob yang tersisa setelah masuk dan keluar sama-sama tidak punya sinyal.

Yang dijaga (semuanya pelajaran dari koreksi F-D30/F-D39/F-D40):
  harga masuk  = ticker `wp` terakhir sebelum `t` (kanonis, sama dengan E7)
  harga keluar = median `wp` pada jendela [t+h-3m, t+h+3m] - BUKAN baris tunggal, supaya satu
                 ticks berisik tidak berubah jadi kesimpulan
  penjelajahan berhenti di `t_kunci` watch (sama dengan E7/E8/E9 - angka lintas uji harus sebanding)
  sensor       = `P(ada harga keluar)` per horison dilaporkan, karena horison panjang punya lebih
                 banyak korban penyensoran; kalau cakupan jatuh, itu BUKAN "tidak ada efek"
  paired       = tiap horison dibandingkan dengan horison yang sama pada POSISI yang sama, lalu
                 tanda-uji eksak atas menang/kalah - bukan dua populasi berbeda
  median seed  = tidak ada satu undian pun yang dipakai sebagai vonis (F-D39)

Ini TIDAK membuktikan ada sinyal masuk. Kalau kemiringannya negatif dan nyata, yang boleh ditulis
adalah: "di substrate kami, menahan posisi memakan harapan - dan itu alasan struktural, bukan
kebetulan pasar". Kalau datanya tidak cukup, alatnya bilang begitu.

Pakai:  python -X utf8 tools/horizon_decay.py
       python -X utf8 tools/horizon_decay.py --horisons 2,5,10,15,20,30
       python -X utf8 tools/horizon_decay.py --self-test
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
import topk_test as TK  # noqa: E402

MIN = 60
WINS = 2000.0
JENDELAPAS = 3 * MIN


def w(x):
    return max(-WINS, min(WINS, x))


def kejadian(horison_luar):
    """Satu kejadian per token per `horison_luar` menit (non-overlap, sama seperti E7/E8)."""
    txs, wp = TK.muat()
    ev, sensor = [], {"token_tanpa_wp": 0, "tanpa_wp_masuk": 0, "n_oleh_batas": 0}
    for tk, rows in txs.items():
        s = wp.get(tk)
        if not s:
            sensor["token_tanpa_wp"] += 1
            continue
        st = [x[0] for x in s]
        taken = -10 ** 15
        for r in [x for x in rows if x["buy"]]:
            t = r["t"]
            if t - taken < horison_luar * MIN or t > TK.T_BATAS:
                if t > TK.T_BATAS:
                    sensor["n_oleh_batas"] += 1
                continue
            i = TK.bisect.bisect_right(st, t) - 1
            if i < 0:
                sensor["tanpa_wp_masuk"] += 1
                continue
            p0 = s[i][1]
            if p0 <= 0:
                continue
            taken = t
            ev.append({"tk": tk, "t": t, "p0": p0, "tx_p": r["p"], "seri": s, "st": st})
    return ev, sensor


def umur_keluar(e, h):
    """Umur SEJATI harga keluar (detik) - supaya "horison 5 menit" bukan cuma nama.

    Ticker `wp` ditulis per siklus rekaman, dan untuk token yang tidak selalu terjawab satu
    baris bisa berumur puluhan menit. Kalau umur median itu lebih besar dari horisonnya sendiri,
    angka "2 menit" tidak mengukur 2 menit - itu kelas kesalahan F-D30 (harga masuk beku) di sisi
    keluar.
    """
    a = TK.bisect.bisect_left(e["st"], e["t"] + (h * MIN - JENDELAPAS))
    b = TK.bisect.bisect_right(e["st"], e["t"] + (h * MIN + JENDELAPAS))
    if a >= b:
        return None
    ts = [e["seri"][j][0] for j in range(a, b)]
    return FC.med(ts) - (e["t"] + h * MIN)


def net_pada(e, h, rt):
    a = TK.bisect.bisect_left(e["st"], e["t"] + (h * MIN - JENDELAPAS))
    b = TK.bisect.bisect_right(e["st"], e["t"] + (h * MIN + JENDELAPAS))
    if a >= b:
        return None
    p1 = FC.med([e["seri"][j][1] for j in range(a, b)])
    return round(10000.0 * (p1 - e["p0"]) / e["p0"] - rt, 1)


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("--horisons", default="2,5,10,15,20,30,45,60")
    ap.add_argument("--dasar", type=int, default=30, help="horison pembanding untuk uji berpasangan")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    hs = [int(x) for x in a.horisons.split(",") if x.strip()]
    rt = costs.rt_cost()
    ev, sensor = kejadian(max(hs))
    print("E11 kurva umur posisi | %d kejadian | horison %s m | harga `wp` | ongkos %.1f bps RT | "
          "batas jelajah %s" % (len(ev), hs, rt,
                                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(TK.T_BATAS))))
    print("sensor %s" % sensor)
    if len(ev) < 40:
        raise SystemExit("kejadian cuma %d - tidak cukup untuk memutus apa pun (ini BUKAN 'tidak "
                         "ada kemiringan')" % len(ev))
    nilai = {}
    for h in hs:
        nilai[h] = [net_pada(e, h, rt) for e in ev]
    print("\n   %7s %8s %11s %10s %9s %9s %9s %10s %7s"
          % ("umur(m)", "n_ada", "mean winso", "median", "P>=500", "positif", "P(ada hrg)",
             "umur harga", "basi"))
    print("   'basi' = % baris keluar yang umurnya melebihi horisonnya sendiri - kalau tinggi, "
          "label horisonnya kosmetik, bukan ukuran")
    for h in hs:
        xs = [x for x in nilai[h] if x is not None]
        if not xs:
            print("   %7d %8s -" % (h, "0"))
            continue
        um = [umur_keluar(e, h) for e in ev]
        um = [x for x in um if x is not None]
        umur_med = FC.med(um) if um else float("nan")
        bocor = sum(1 for x in um if x > h * MIN) / float(len(um or [1]))
        print("   %7d %8d %+11.1f %+10.1f %8.1f%% %8.1f%% %8.1f%% %10.0f %6.1f%%"
              % (h, len(xs), sum(w(x) for x in xs) / len(xs), FC.med(xs),
                 100.0 * sum(1 for x in xs if x >= 500) / len(xs),
                 100.0 * sum(1 for x in xs if x > 0) / len(xs),
                 100.0 * len(xs) / len(ev), umur_med, 100.0 * bocor))
    # uji berpasangan: tiap horison vs horison dasar, pada POSISI yang sama
    print("\n   berpasangan vs umur %d m (posisi yang sama; vonis = tanda-uji eksak satu arah):"
          % a.dasar)
    baris = []
    for h in hs:
        if h == a.dasar:
            continue
        d = [nilai[h][i] - nilai[a.dasar][i] for i in range(len(ev))
             if nilai[h][i] is not None and nilai[a.dasar][i] is not None]
        if len(d) < 20:
            print("   %7d %8d  (sepasang tidak cukup - tidak divonis)" % (h, len(d)))
            continue
        lebih = sum(1 for x in d if x > 1)
        kalah = sum(1 for x in d if x < -1)
        p = FC.sign_p(lebih, lebih + kalah)
        row = {"umur_m": h, "n_sepasang": len(d), "median_delta_bps": round(FC.med(d), 1),
               "mean_winso_delta": round(sum(w(x) for x in d) / len(d), 1),
               "menang": lebih, "kalah": kalah, "p_tanda": round(p, 5),
               "lebih_pendek_lebih_baik": (FC.med(d) > 0 and p < 0.05)}
        baris.append(row)
        print("   %7d %8d %+16.1f %+18.1f %6d/%-6d p=%-9.5f %s"
              % (h, len(d), row["median_delta_bps"], row["mean_winso_delta"], lebih, kalah, p,
                 "PENDEK = BAIK" if row["lebih_pendek_lebih_baik"] else
                 ("pendek = buruk" if (FC.med(d) < 0 and p < 0.05) else "tidak jelas")))
    kemudi = [b for b in baris if b["umur_m"] < a.dasar and b["lebih_pendek_lebih_baik"]]
    print("\nVONIS E11: %s" % ("menahan lebih lama dari %d m memakan harapan secara terukur (%d dari "
                               "%d horison pendek menang berpasangan)"
                               % (a.dasar, len(kemudi), sum(1 for b in baris if b["umur_m"] < a.dasar))
                               if kemudi else
                               "tidak ada kemiringan umur yang terbukti - jangan ubah kebijakan "
                               "hanya karena kurva rata-rata terlihat turun"))
    print("\nPLACEBO - kurva yang sama dengan ASAL-MULA digeser acak 30-90 m (memutus hubungan "
          "dengan peristiwa):")
    rnd = random.Random(20260929)
    geser = placebo(ev, hs, rt, rnd, shifts=25)
    print("   %7s %12s %12s %12s" % ("umur(m)", "mean asli", "mean placebo", "median placebo"))
    for h in hs:
        a_ = [x for x in nilai[h] if x is not None]
        print("   %7d %+12.1f %+12.1f %+12.1f"
              % (h, sum(w(x) for x in a_) / max(1, len(a_)), geser["mean"][h], geser["median"][h]))
    print("   kalau placebo TIDAK turun seiring umur, kemiringan di atas milik peristiwa kami; "
          "kalau placebo ikut turun, yang kami ukur adalah bentuk pasar BSC pada jam itu, bukan "
          "kerumunan pintar.")

    print("\nSCALAR EKSEKUSI - masuk tertunda `d` menit SETELAH peristiwa (sejauh mana kabar kami "
          "tiba tepat waktu):")
    lat = scan_delay(ev, hs, rt, rnd)
    print("   %7s %12s %12s %12s %12s" % ("delay(m)", "mean@5m", "median@5m", "mean@30m",
                                          "median@30m"))
    for d, v in sorted(lat.items(), key=lambda kv: int(kv[0])):
        print("   %7s %+12.1f %+12.1f %+12.1f %+12.1f"
              % (d, v["5"]["mean"], v["5"]["median"], v["30"]["mean"], v["30"]["median"]))
    mati = None
    for d in sorted(lat, key=lambda x: int(x)):
        if lat[d]["5"]["mean"] < 0:
            mati = d
            break
    print("   %s" % ("edge di horison 5 m sudah NEGATIF pada delay %s m: kabar kami tiba setelah "
                     "acaranya selesai - jangan dijual sebagai bisa ditradingkan"
                     % mati if mati else
                     "edge horison 5 m masih positif sampai delay terbesar yang diuji - perlu uji "
                     "khusus sebelum dianggap bisa dieksekusi"))

    print("\nKONTROL SUMBER HARGA MASUK - kalau `wp` terakhir kami lebih rendah dari harga "
          "transaksi di jam yang sama, bump horison pendek adalah SELISIH PENGUKURAN, bukan peluang:")
    amb = [10000.0 * (e["tx_p"] - e["p0"]) / e["p0"] for e in ev if e["p0"] > 0]
    amb.sort()
    print("   selisih tx.p - wp.p0 (bps): median %+0.1f | mean %+0.1f | p90 %+0.1f | %0.1f%% positif"
          % (FC.med(amb), sum(amb) / len(amb), amb[int(0.9 * (len(amb) - 1))],
             100.0 * sum(1 for x in amb if x > 0) / len(amb)))
    dua = {}
    for sumber in ("wp", "tx"):
        for h in (2, 5, 10, 30):
            xs = []
            for e in ev:
                e2 = dict(e, p0=e["tx_p"] if sumber == "tx" else e["p0"])
                v = net_pada(e2, h, rt)
                if v is not None:
                    xs.append(v)
            if xs:
                dua["%s@%d" % (sumber, h)] = {"n": len(xs),
                                              "mean": round(sum(w(x) for x in xs) / len(xs), 1),
                                              "median": round(FC.med(xs), 1)}
    print("   %-10s %10s %10s | %-10s %10s %10s" % ("wp mean", "wp median", "n", "tx mean",
                                                    "tx median", "n"))
    for h in (2, 5, 10, 30):
        a1, a2 = dua.get("wp@%d" % h, {}), dua.get("tx@%d" % h, {})
        print("   %2d m      %+10.1f %+10.1f %10d | %+11.1f %+10.1f %10d"
              % (h, a1.get("mean", 0), a1.get("median", 0), a1.get("n", 0),
                 a2.get("mean", 0), a2.get("median", 0), a2.get("n", 0)))
    susut = [dua.get("tx@%d" % h, {}).get("mean", 0) - dua.get("wp@%d" % h, {}).get("mean", 0)
             for h in (2, 5)]
    print("   %s" % ("bump horison pendek MENYUSUT %+0.1f..%+0.1f bps begitu harga masuk diganti "
                     "sumber - sebagian edge itu adalah celah pengukuran kami sendiri"
                     % (susut[0], susut[1]) if min(susut) < -20 else
                     "bump horison pendek bertahan saat harga masuk diambil dari transaksi - "
                     "bukan artefak sumber harga"))

    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "kejadian": len(ev),
           "sensor": sensor, "horison_menit": hs, "dasar_menit": a.dasar, "ongkos_bps_rt": rt,
           "kurva": {str(h): {"n_ada": sum(1 for x in nilai[h] if x is not None),
                              "mean_winso": round(sum(w(x) for x in nilai[h] if x is not None) /
                                                  max(1, sum(1 for x in nilai[h] if x is not None)), 1),
                              "median": round(FC.med([x for x in nilai[h] if x is not None]), 1)}
                     for h in hs},
           "berpasangan": baris, "kemudi": bool(kemudi), "placebo": geser,
           "scan_delay": lat,
           "selisih_harga_masuk_bps": {"median": round(FC.med(amb), 1),
                                       "mean": round(sum(amb) / len(amb), 1),
                                       "persen_positif": round(100.0 * sum(1 for x in amb if x > 0)
                                                               / len(amb), 1)},
           "dua_sumber": dua}
    out["sha"] = "0x" + hashlib.sha256(json.dumps([out["kurva"], baris], sort_keys=True)
                                      .encode()).hexdigest()
    p = os.path.join(ROOT, "decisions", "horizon-decay-%s.json"
                     % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("artefak: decisions/%s" % os.path.basename(p))


def placebo(ev, hs, rt, rnd, shifts=25):
    """Kurva umur dengan asal-mula digeser acak - kontrol bentuk, bukan kontrol sinyal.

    Tiap pergeseran memakai HARI yang sama, token yang sama, dan horison yang sama; hanya jam
    keluarnya dilepas dari peristiwa. Kalau kurva placebo ikut melorot bersama umur, kemiringan
    yang kita lihat di E11 adalah properti substrate (berdetak lalu mati), bukan informasi.
    """
    out = {h: [] for h in hs}
    for _ in range(shifts):
        for e in ev:
            e2 = dict(e)
            e2["t"] = e["t"] + rnd.randint(30, 90) * MIN
            for h in hs:
                v = net_pada(e2, h, rt)
                if v is not None:
                    out[h].append(v)
    return {"mean": {h: round(sum(w(x) for x in out[h]) / max(1, len(out[h])), 1) for h in hs},
            "median": {h: round(FC.med(out[h]), 1) if out[h] else 0.0 for h in hs},
            "n": {h: len(out[h]) for h in hs}, "shifts": shifts}


def scan_delay(ev, hs, rt, rnd, delays=(0, 2, 5, 10, 20)):
    """Kurva umur diukur dari `t + d`, bukan dari `t`.

    Ini pertanyaan yang membedakan "ada efek" dari "bisa diambil": feed kami datang dengan
    latensi (rekaman per siklus, antrian, jam pihak ketiga), dan harga bergerak di dalam
    delay itu. Kalau expectancy sudah melorot pada d = 5 menit, maka yang kami punya adalah
    laporan arkeologi, bukan sinyal masuk.
    """
    out = {}
    for d in delays:
        geser = []
        for e in ev:
            e2 = dict(e)
            i = TK.bisect.bisect_right(e2["st"], e2["t"] + d * MIN) - 1
            if i < 0:
                continue
            e2["t"] = e2["t"] + d * MIN
            e2["p0"] = e2["seri"][i][1]
            if e2["p0"] > 0:
                geser.append(e2)
        out[str(d)] = {}
        for h in (5, 30):
            xs = []
            for e in geser:
                v = net_pada(e, h, rt)
                if v is not None:
                    xs.append(v)
            out[str(d)][str(h)] = {"n": len(xs), "mean": round(sum(w(x) for x in xs) /
                                                               max(1, len(xs)), 1),
                                   "median": round(FC.med(xs), 1) if xs else 0.0}
    return out


def self_test():
    """Deret buatan dengan kemiringan yang diketahui - kurva harus menemukan arahnya."""
    def buat(drift, n=40, jitter=0.0):
        rnd = random.Random(5)
        ev = []
        for i in range(n):
            t0 = 1_000_000
            ser = [(t0 + k * MIN, 1.0 * (1 + drift * k) * (1 + (jitter * rnd.uniform(-1, 1))))
                   for k in range(0, 70)]
            ev.append({"tk": "0x%d" % i, "t": t0, "p0": 1.0, "seri": ser, "st": [s[0] for s in ser]})
        return ev
    rt = 0.0
    turun = buat(-0.004)
    na = net_pada(turun[0], 2, rt)
    nb = net_pada(turun[0], 30, rt)
    assert na is not None and nb is not None and na > nb, (na, nb)
    d = [net_pada(e, 2, rt) - net_pada(e, 30, rt) for e in turun]
    assert FC.med(d) > 0 and FC.sign_p(sum(1 for x in d if x > 1), len(d)) < 0.05
    datar = buat(0.0)
    d2 = [net_pada(e, 2, rt) - net_pada(e, 30, rt) for e in datar]
    assert abs(FC.med(d2)) < 50, FC.med(d2)
    naik = buat(0.004)
    d3 = [net_pada(e, 2, rt) - net_pada(e, 30, rt) for e in naik]
    assert FC.med(d3) < 0, FC.med(d3)
    # horison tanpa baris -> None, BUKAN 0 (nol akan menyamar jadi "hasil nol bps")
    e = dict(turun[0], t=1_000_000 + 69 * MIN)
    assert net_pada(e, 60, rt) is None
    print("self-test E11 OK: drift turun/naik/datar dikenali arahnya, horison bolong -> None")


if __name__ == "__main__":
    utama()
