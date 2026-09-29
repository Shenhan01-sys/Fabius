"""E7/E8 - dua uji yang bentuknya mirip keputusan agen, bukan mirip statistik.

Kenapa keduanya beda dari semua uji sebelumnya:

  E7 top-k DALAM SATU SIKLUS. Agen ini punya `dailyCap` 5 kursi. Yang ia hadapi bukan "apakah
     kerumunan lebih baik dari rata-rata sepanjang masa", tapi "dari kandidat yang ADA detik ini,
     lima yang mana". Control yang jujur karena itu adalah sesama kandidat di siklus yang sama -
     kalau acaknya disebar ke seluruh jendela waktu, yang diukur adalah rezim jam, bukan kemampuan
     memilih.
  E8 aturan KELUAR. Sudah terukur kerumunan beli diikuti hasil yang lebihburuk. Kalau itu nyata,
     menjual SAAT kerumunan datang harus memperbaiki hasil dari POSISI YANG SAMA - bukan dari
     populasi lain. Ini satu-satunya klaim "pandai trading" yang berdiri di angka kami sekarang.

Yang dijaga: outcome diambil dari ticker `wp` (berdetak sendiri, tidak menunggu transaksi), dan
penjelajahan berhenti di `t_kunci` spesifikasi watch (29 Sep 02:59:06Z). Data setelah jam itu
adalah milik uji terkunci [[06-Results/17 - Pra-Registrasi Watch]] dan tidak boleh kukecap di sini.

Pakai:  python -X utf8 tools/topk_test.py
       python -X utf8 tools/topk_test.py --k 5 --horizon 30
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import io
import json
import os
import random
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import costs  # noqa: E402
import flow_cluster_test as FC  # noqa: E402
import prices as PR  # noqa: E402

MIN = 60
WINS = 2000.0
KUNCI_WATCH = os.path.join(ROOT, "decisions", "prereg-watch-lock.json")


def batas_jelajah():
    """Batas penjelajahan DIBACA dari berkas kunci, bukan ditulis sebagai angka.

    Versi pertama hardcode epoch dan saya meleset SATU TAHUN (1,759e9 vs 1,790e9) - akibatnya
    semua kejadian dianggap 'setelah batas', alatnya melaporkan `kejadian 0`, lalu crash di
    pembagian nol. Angka yang menyalin keadaan mesin lain bukan batas; ini yang membuatnya tetap
    benar ketika kunci dipasang ulang.
    """
    if not os.path.exists(KUNCI_WATCH):
        raise SystemExit("tidak ada %s - kunci watch harus dipasang sebelum penjelajahan"
                         % os.path.relpath(KUNCI_WATCH, ROOT))
    lock = json.load(io.open(KUNCI_WATCH, encoding="utf-8"))
    t = int(lock.get("t_kunci") or 0)
    assert 1_700_000_000 < t < 2_000_000_000, "t_kunci bukan detik Unix: %d" % t
    return t


T_BATAS = batas_jelajah()
# satu siklus = sepanjang horison keputusan. Versi pertama memakai 5 menit dan tiap "siklus" hanya
# berisi 1-2 kandidat, jadi top-5 tidak pernah terdefinisi dan uji E7 lolos tanpa pernah diuji.
# Situasinya nyata: `dailyCap` 5 kursi di isi dari kandidat yang datang dalam satu jam kerja agen.
SIKLUS_DTK = 30 * 60          # satu siklus = 30 menit kandidat
FITUR = ["kluster_beli", "maker_ge3", "spread_ok", "usd_ge_1k", "vol_tinggi", "vol_rendah",
         "di_atas_puncak60", "di_bawah_puncak60", "sepi_total", "banyak_jual"]


def w(x):
    return max(-WINS, min(WINS, x))


def muat():
    txs = {}
    for ln in io.open(os.path.join(ROOT, "universe", "wallet-flow.jsonl"), encoding="utf-8",
                      errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("k") not in ("tx", "txc"):
            continue
        tk = str(d.get("tk") or "").lower()
        t, p = int(d.get("t") or 0), float(d.get("p") or 0)
        if tk and t and p > 0:
            txs.setdefault(tk, []).append({"t": t, "p": p, "u": float(d.get("u") or 0),
                                           "buy": bool(d.get("b")),
                                           "m": str(d.get("m") or "").lower()})
    for tk in txs:
        txs[tk].sort(key=lambda r: r["t"])
    wp = PR.load(os.path.join(ROOT, "universe", "watch-prices.jsonl"), "wp")
    return txs, wp["rows"]


def build(hor):
    txs, wp = muat()
    ev, sensor = [], {"tanpa_wp_masuk": 0, "tanpa_wp_keluar": 0, "n_oleh_batas": 0,
                      "token_tanpa_wp": 0}
    rt = costs.rt_cost()
    for tk, rows in txs.items():
        s = wp.get(tk)
        if not s:
            sensor["token_tanpa_wp"] += len([r for r in rows if r["buy"]])
            continue
        st = [x[0] for x in s]
        taken = -10 ** 15
        for r in [x for x in rows if x["buy"]]:
            t = r["t"]
            if t - taken < hor * MIN:
                continue
            if t > T_BATAS:
                sensor["n_oleh_batas"] += 1
                continue
            i = bisect.bisect_right(st, t) - 1
            if i < 0:
                sensor["tanpa_wp_masuk"] += 1
                continue
            p0 = s[i][1]
            t_masuk = s[i][0]
            a = bisect.bisect_left(st, t + (hor - 15) * MIN)
            b = bisect.bisect_right(st, t + (hor + 15) * MIN)
            if a >= b:
                sensor["tanpa_wp_keluar"] += 1
                continue
            p1 = FC.med([s[j][1] for j in range(a, b)])
            if p0 <= 0:
                continue
            taken = t
            w15 = [q for q in rows if t - 15 * MIN <= q["t"] <= t]
            wb = [q for q in w15 if q["buy"]]
            wsell = [q for q in w15 if not q["buy"]]
            mk_b = {q["m"] for q in wb if q["m"]}
            mk_s = {q["m"] for q in wsell if q["m"]}
            usd_b = sum(q["u"] for q in wb)
            usd_s = sum(q["u"] for q in wsell)
            top = max((q["u"] for q in wb), default=0.0)
            lalu = [p for tt, p in s[max(0, i - 200):i] if tt >= t - 60 * MIN]
            puncak = max(lalu) if len(lalu) >= 5 else None
            vol = None
            ekor = [p for tt, p in s[max(0, i - 40):i + 1]]
            if len(ekor) >= 12:
                dr = [statistics.pstdev([0.0])]
                dr = [j / k - 1.0 for j, k in zip(ekor[1:], ekor[:-1]) if k > 0]
                vol = statistics.pstdev(dr) if len(dr) >= 8 else None
            # E8 di dalam E7: kalau kerumunan beli datang sebelum horison, kebijakan kita keluar di
            # sana. `net_exit` = hasil POSISI YANG SAMA kalau aturan keluar dipakai; tc=None berarti
            # tidak ada kerumunan -> tetap hold.
            tcx = waktu_kluster(rows, t, hor)
            p_exit = None
            if tcx:
                j = bisect.bisect_right(st, tcx + 3 * MIN) - 1
                if j > i:
                    p_exit = s[j][1]
            net_exit = round(10000.0 * ((p_exit if p_exit else p1) - p0) / p0 - rt, 1)
            ev.append({"tk": tk, "t": t, "siklus": t // SIKLUS_DTK, "exit_awal": bool(p_exit),
                       "net_exit": net_exit, "net": round(10000.0 *
                                                                                 (p1 - p0) / p0
                                                                                 - rt, 1),
                       "usia_harga_s": t - t_masuk, "vol": vol, "usd_b": usd_b,
                       "kluster_beli": len(mk_b) >= 2, "maker_ge3": len(mk_b) >= 3,
                       "spread_ok": usd_b > 0 and top <= 0.6 * usd_b,
                       "usd_ge_1k": usd_b >= 1000.0,
                       "sepi_total": len(mk_b) == 0 and usd_b < 100.0,
                       "banyak_jual": len(mk_s) >= 2 or usd_s >= 1.5 * max(usd_b, 1.0),
                       "di_atas_puncak60": bool(puncak) and p0 >= puncak,
                       "di_bawah_puncak60": bool(puncak) and p0 < 0.9 * puncak})
    vs = sorted([e["vol"] for e in ev if e["vol"] is not None])
    med = vs[len(vs) // 2] if vs else None
    for e in ev:
        if med is not None and e["vol"] is not None:
            e["vol_tinggi"] = e["vol"] >= med
            e["vol_rendah"] = e["vol"] < med
    return ev, sensor


def ringkas_topk(ev, fitur, k, rnd, draws, seeds=40):
    """E7 - top-k per siklus menurut `fitur`, lawan acak-siklus, DAN lawan undiannya sendiri.

    Dua koreksi atas versi pertama (29 Sep, ditemukan `uji_kombinasi`/E10):

    1. Versi pertama membandingkan SATA mean pilihan terhadap CI atas distribusi acak. Tapi
       pemilihannya sendiri memakai pengacak sebagai tie-break, jadi mean itu juga variabel acak -
       membandingkan satu undian terhadap persentil distribusi lawan adalah perbandingan yang
       tidak seimbang. Sekarang: `seeds` pengulangan pemilihan, lalu vonis memakai MEDIAN seed dan
       `frac_seed_di_atas` (berapa sering pemilihan itu benar-benar melewati kontrolnya).
    2. Yang diuji bukan "berapa mean-nya" tapi "apakah bedanya lebih besar dari bunyi acak alat
       pemilihnya sendiri".
    """
    per = _siklus(ev, k)
    if len(per) < 8:
        return {"h": fitur, "siklus": len(per), "status": "SIKLUS TIDAK CUKUP"}
    xs_pilih = pilih_topk(per, fitur, k, rnd)
    nilai = [w(e["net"]) for e in xs_pilih]
    acak_mean = sorted(kebijakan_mean(per, None, k, rnd, "net") for _ in range(draws))
    ci_atas = acak_mean[int(0.975 * draws)]
    ms = sorted(kebijakan_mean(per, fitur, k, rnd, "net") for _ in range(seeds))
    med_seed = ms[len(ms) // 2]
    return {"h": fitur, "siklus": len(per), "n": len(nilai),
            "mean": round(med_seed, 1), "median": round(FC.med(nilai), 1),
            "p_ge_500": round(100.0 * sum(1 for x in nilai if x >= 500) / len(nilai), 1),
            "acak_mean": round(sum(acak_mean) / len(acak_mean), 1),
            "acak_ci_atas": round(ci_atas, 1),
            "sebar_seed": [round(ms[0], 1), round(ms[-1], 1)],
            "frac_seed_di_atas": round(sum(1 for x in ms if x > ci_atas) / float(len(ms)), 2),
            "di_atas": med_seed > ci_atas}


def waktu_kluster(rows, t0, hor):
    """Waktu pertama SETELAH t0 ketika >=2 maker berbeda beli dalam satu jendela 15 menit.

    Ini momen yang kami klaim sebagai 'kerumunan datang' - dihitung hanya dari transaksi yang sudah
    terjadi, jadi tidak ada intip-masa-depan: kita memang baru tahu setelah yang kedua muncul.
    """
    jendela = []
    for q in [x for x in rows if x["buy"] and x["t"] > t0 and x["t"] <= t0 + hor * MIN]:
        jendela.append((q["t"], q["m"]))
        jendela = [(tt, mm) for tt, mm in jendela if tt > q["t"] - 15 * MIN]
        if len({mm for _, mm in jendela if mm}) >= 2:
            return q["t"]
    return None


def uji_keluar(hor):
    """E8: POSISI YANG SAMA - keluar saat kerumunan beli datang vs menahan sampai horison.

    Yang dibandingkan bukan dua populasi, jadi tidak ada ruang 'mungkin kohornya beda':
    delta = (harga keluar dini - harga hold) / harga masuk. Positif = keluar dini menolong.
    """
    txs, wp = muat()
    delta, lebih, buruk, dipantau = [], 0, 0, 0
    for tk, rows in txs.items():
        rows.sort(key=lambda r: r["t"])
        s = wp.get(tk)
        if not s:
            continue
        st = [x[0] for x in s]
        taken = -10 ** 15
        for r in [x for x in rows if x["buy"] and x["t"] <= T_BATAS]:
            t = r["t"]
            if t - taken < hor * MIN:
                continue
            i = bisect.bisect_right(st, t) - 1
            a = bisect.bisect_left(st, t + (hor - 15) * MIN)
            b = bisect.bisect_right(st, t + (hor + 15) * MIN)
            if i < 0 or a >= b:
                continue
            taken = t
            p0, p_hold = s[i][1], FC.med([s[j][1] for j in range(a, b)])
            if p0 <= 0:
                continue
            tc = waktu_kluster(rows, t, hor)
            if not tc:
                continue
            dipantau += 1
            j = bisect.bisect_right(st, tc + 3 * MIN) - 1
            if j <= i:
                continue
            p_exit = s[j][1]
            d = (p_exit - p_hold) / p0 * 10000.0
            delta.append(w(d))
            if d > 1:
                lebih += 1
            elif d < -1:
                buruk += 1
    if not delta:
        return {"status": "tidak ada posisi yang memuat kerumunan keluar"}
    lo, hi = (lambda v: (v[int(0.025 * len(v))], v[int(0.975 * len(v))]))(
        sorted(delta))
    return {"posisi_dipantau": len(delta), "keluar_dini_menang": lebih,
            "keluar_dini_kalah": buruk, "median_delta_bps": round(FC.med(delta), 1),
            "mean_winso_delta": round(sum(delta) / len(delta), 1),
            "delta_persentil_5_95": [round(lo, 1), round(hi, 1)]}


def waktu_kluster(rows, t0, hor):
    """Waktu pertama SETELAH t0 ketika >=2 maker berbeda beli dalam satu jendela 15 menit.

    Ini momen yang kami klaim sebagai 'kerumunan datang' - dihitung hanya dari transaksi yang sudah
    terjadi, jadi tidak ada intip-masa-depan: kita memang baru tahu setelah yang kedua muncul.
    """
    jendela = []
    for q in [x for x in rows if x["buy"] and x["t"] > t0 and x["t"] <= t0 + hor * MIN]:
        jendela.append((q["t"], q["m"]))
        jendela = [(tt, mm) for tt, mm in jendela if tt > q["t"] - 15 * MIN]
        if len({mm for _, mm in jendela if mm}) >= 2:
            return q["t"]
    return None


def uji_keluar(hor):
    """E8: POSISI YANG SAMA - keluar saat kerumunan beli datang vs menahan sampai horison.

    Yang dibandingkan bukan dua populasi, jadi tidak ada ruang 'mungkin kohornya beda':
    delta = (harga keluar dini - harga hold) / harga masuk. Positif = keluar dini menolong.
    """
    txs, wp = muat()
    delta, lebih, buruk, dipantau = [], 0, 0, 0
    for tk, rows in txs.items():
        rows.sort(key=lambda r: r["t"])
        s = wp.get(tk)
        if not s:
            continue
        st = [x[0] for x in s]
        taken = -10 ** 15
        for r in [x for x in rows if x["buy"] and x["t"] <= T_BATAS]:
            t = r["t"]
            if t - taken < hor * MIN:
                continue
            i = bisect.bisect_right(st, t) - 1
            a = bisect.bisect_left(st, t + (hor - 15) * MIN)
            b = bisect.bisect_right(st, t + (hor + 15) * MIN)
            if i < 0 or a >= b:
                continue
            taken = t
            p0, p_hold = s[i][1], FC.med([s[j][1] for j in range(a, b)])
            if p0 <= 0:
                continue
            tc = waktu_kluster(rows, t, hor)
            if not tc:
                continue
            dipantau += 1
            j = bisect.bisect_right(st, tc + 3 * MIN) - 1
            if j <= i:
                continue
            p_exit = s[j][1]
            d = (p_exit - p_hold) / p0 * 10000.0
            delta.append(w(d))
            if d > 1:
                lebih += 1
            elif d < -1:
                buruk += 1
    if not delta:
        return {"status": "tidak ada posisi yang memuat kerumunan keluar"}
    lo, hi = (lambda v: (v[int(0.025 * len(v))], v[int(0.975 * len(v))]))(
        sorted(delta))
    return {"posisi_dipantau": len(delta), "keluar_dini_menang": lebih,
            "keluar_dini_kalah": buruk, "median_delta_bps": round(FC.med(delta), 1),
            "mean_winso_delta": round(sum(delta) / len(delta), 1),
            "delta_persentil_5_95": [round(lo, 1), round(hi, 1)]}


def _siklus(ev, k):
    per = {}
    for e in ev:
        per.setdefault(e["siklus"], []).append(e)
    return {c: xs for c, xs in per.items() if len(xs) >= 2 * k}


def pilih_topk(per, fitur, k, rnd):
    xs_all = []
    for c in sorted(per):
        xs = per[c][:]
        rnd.shuffle(xs)
        if fitur is not None:
            xs.sort(key=lambda e: (0 if bool(e.get(fitur)) else 1,))
        xs_all += xs[:k]
    return xs_all


def kebijakan_mean(per, fitur, k, rnd, kunci):
    xs = pilih_topk(per, fitur, k, rnd)
    return sum(w(e[kunci]) for e in xs) / len(xs)


def uji_kombinasi(ev, k, rnd, draws, seeds=40):
    """E10 - kebijakan UTUH (pemilihan x aturan keluar) + berapa besar hasilnya bergantung SEED.

    Kenapa seed ikut dilaporkan: pemilihan top-k dipecah dengan pengacakan saat seri. Kalau
    "mean kandidat" berubah puluhan bps hanya karena urutan seri ditukar, maka satu angka dari satu
    undian bukan efek - itu hasil sampingan pemilihannya. Kontrol acak dibangun sebagai DISTRIBUSI
    mean per undian (bukan persentil nilai individual), supaya bandingkan vs bandingkan.
    """
    per = _siklus(ev, k)
    out = []
    for kunci in ("net", "net_exit"):
        acak = sorted(kebijakan_mean(per, None, k, rnd, kunci) for _ in range(draws))
        ci_atas = acak[int(0.975 * len(acak))]
        out.append({"outcome": kunci, "fitur": "ACAK (kontrol)", "n": k * len(per),
                    "mean": round(sum(acak) / len(acak), 1), "median": round(FC.med(acak), 1),
                    "acak_ci_atas": round(ci_atas, 1), "di_atas_acak": False,
                    "sebar_seed": None})
        for f in ("vol_rendah", "kluster_beli", "usd_ge_1k", "di_bawah_puncak60"):
            ms = sorted(kebijakan_mean(per, f, k, rnd, kunci) for _ in range(seeds))
            m = ms[len(ms) // 2]
            out.append({"outcome": kunci, "fitur": f, "n": k * len(per),
                        "mean": round(m, 1), "median": round(FC.med(ms), 1),
                        "acak_ci_atas": round(ci_atas, 1),
                        "di_atas_acak": m > ci_atas,
                        "sebar_seed": [round(ms[0], 1), round(ms[-1], 1)],
                        "frac_seed_di_atas_acak": round(
                            sum(1 for x in ms if x > ci_atas) / float(len(ms)), 2)})
    return out


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--horizon", type=int, default=30)
    ap.add_argument("--draws", type=int, default=600)
    a = ap.parse_args()
    ev, sensor = build(a.horizon)
    rt = costs.rt_cost()
    print("E7 top-%d per siklus | horison %d m | outcome dari ticker `wp` | ongkos %.1f bps | "
          "batas jelajah %s" % (a.k, a.horizon, rt,
                                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(T_BATAS))))
    print("kejadian %d | sensor %s" % (len(ev), sensor))
    if not ev:
        raise SystemExit("tidak ada kejadian yang bisa dinilai - ini BUKAN 'tidak ada efek', ini "
                         "alat yang tidak dapat bahan. Periksa umur/cakupan `wp`.")
    pool = [w(e["net"]) for e in ev]
    print("pool: mean winso %+0.1f | median %+0.1f | P>=500 %.1f %% | %d siklus"
          % (sum(pool) / len(pool), FC.med(pool), 100.0 * sum(1 for x in pool if x >= 500) / len(pool),
             len({e['siklus'] for e in ev})))
    rnd = random.Random(20260929)
    print("\n   %-18s %7s %6s %10s %9s %11s %-12s %-26s"
          % ("fitur", "siklus", "n", "mean*", "median", "acak (CI atas)", "vonis",
             "sebar seed (frac di atas)"))
    print("   * mean = MEDIAN dari 40 pengulangan pemilihan (tie-break diacak); satu undian "
          "bukan hasil")
    hasil = []
    for f in FITUR:
        r = ringkas_topk(ev, f, a.k, rnd, a.draws)
        if r.get("status"):
            print("   %-18s %7s  %s" % (f, r["siklus"], r["status"]))
            continue
        hasil.append(r)
        print("   %-18s %7d %6d %+10.1f %+9.1f %10.1f%% %+11.1f (%+8.1f) %-12s %+.1f..%+.1f (%2.0f%%)"
              % (f, r["siklus"], r["n"], r["mean"], r["median"], r["p_ge_500"], r["acak_mean"],
                 r["acak_ci_atas"], "DI ATAS ACAR" if r["di_atas"] else "di bawah acak",
                 r["sebar_seed"][0], r["sebar_seed"][1], 100.0 * r["frac_seed_di_atas"]))
    lulus = [r["h"] for r in hasil if r["di_atas"]]
    print("\nE7: fitur yang mengalahkan acak-siklus: %s" % (lulus or "TIDAK ADA"))

    print("\nE10 kebijakan utuh (pemilihan x aturan keluar) pada posisi yang sama:")
    print("   %-10s %-18s %6s %10s %10s %11s %-14s %s"
          % ("outcome", "fitur", "n", "mean", "median", "CI atas acak", "vonis", "ketergantungan seed"))
    kk = uji_kombinasi(ev, a.k, rnd, a.draws)
    for r in kk:
        ss = ("seed %0.1f..%0.1f | %s%% seed di atas acak"
              % (r["sebar_seed"][0], r["sebar_seed"][1],
                 int(100 * r["frac_seed_di_atas_acak"]))) if r.get("sebar_seed") else ""
        print("   %-10s %-18s %6d %+10.1f %+10.1f %+11.1f %-14s %s"
              % (r["outcome"], r["fitur"], r["n"], r["mean"], r["median"], r["acak_ci_atas"],
                 "DI ATAS ACAK" if r["di_atas_acak"] else
                 ("(kontrol)" if "ACAK" in r["fitur"] else "di bawah acak"), ss))
    print("   catatan: `net` = tahan sampai horison; `net_exit` = keluar saat kerumunan beli datang "
          "(E8). Kedua lengan memakai aturan yang sama, jadi selisihnya murni pemilihan.")

    print("\nE8 keluar saat kerumunan beli (posisi yang sama, bukan populasi lain):")
    ek = uji_keluar(a.horizon)
    print("   %s" % json.dumps(ek, sort_keys=True))
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "k": a.k, "horizon_menit": a.horizon, "batas_jelajah_utc":
           time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(T_BATAS)),
           "kejadian": len(ev), "sensor": sensor, "pool_mean_winso": round(sum(pool) / len(pool), 1),
           "e7": hasil, "e8": ek, "e10": kk, "ongkos_bps_rt": rt}
    out["sha"] = "0x" + hashlib.sha256(json.dumps([hasil, ek, kk], sort_keys=True).encode()).hexdigest()
    p = os.path.join(ROOT, "decisions", "topk-test-%s.json"
                     % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("artefak: decisions/%s" % os.path.basename(p))


if __name__ == "__main__":
    utama()
