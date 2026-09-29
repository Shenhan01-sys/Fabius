"""E18 (T3) - signed volume imbalance dari TRANSAKSI ⑦: teori buku order, versi yang tidak butuh buku.

Kenapa ini yang pertama dikerjakan dari epik [[08-Backlog/03 - Epik Teori Baru]]: teori builder
butuh histori order book yang baru mulai direkam jam 09:1xZ (E16, vonis 21:37Z). Tapi inti teorinya -
**sisi mana yang lebih agresif menentukan arah** - bisa diukur dari data yang sudah kami punya:
51.669 baris transaksi ⑦ dengan nominal USD, maker, dan sisi beli/jual. Tidak ada histori baru yang
dibutuhkan, jadi tidak ada alasan menunda.

Beda dengan apa yang sudah MATI (wajib disebut, jangan sampai diberi nama baru):
  `usd_ge_1k` / `kluster_beli`  = "ada berapa besar / ada berapa kepala" -> magnitudo mentah
  `svi_*` di alat ini           = "(beli - jual) dibagi (beli + jual)"  -> NORMALISASI berimbang
                                  antara dua sisi. Uji E7 (F-D39) membunuh magnitudo mentah; itu
                                  tidak otomatis membunuh rasio berimbang, dan itu yang diuji di sini.

Empat pembacaan + dua jendela, TIDAK ada yang dipilih setelah lihat hasil:
  svu  = (Σusd_beli - Σusd_jual) / (Σusd_beli + Σusd_jual)        [15 m dan 5 m]
  svn  = (n_beli - n_jual) / (n_beli + n_jual)                    [15 m]
  svm  = (maker_beli - maker_jual) / (maker_beli + maker_jual)     [15 m]
  vpb  = VPIN-style: |Σ tanda·q| / Σ q atas bucket volume sama (K bucket)

Disiplin yang dibayar dari tujuh koreksi alat kami (F-D30/32/37/39/40/43/46):
  * outcome dari ticker `wp` (bukan harga transaksi itu sendiri - F-D30), horizon 2/5/30 m;
  * penjelajahan berhenti di `t_kunci` watch, sama seperti E7/E11/E13 supaya angkanya sebanding;
  * placebo: asal-mula digeser acak 30-90 menit (kalau placebo ikut bergerak, itu bentuk pasar);
  * kontrol: kuantil-atas vs kuantil-bawah pada jendela yang sama; median DAN mean dilaporkan;
  * grid: jendela 15 m dan 5 m, dan kalau salah satu menang sementara yang lain mati, itu tebing
    parameter dan harus ditulis sebagai tebing (aturan E14/F-D45);
  * BH alpha 0,10 atas SEMUA hipotesis di run ini; satu pemenang dari 8 uji = kandidat (F-D39),
    bukan hasil, dan tidak akan dijual sebagai alas masuk di halaman ini.

Pakai:  python -X utf8 tools/flow_variasi.py --self-test
       python -X utf8 tools/flow_variasi.py --draws 200
"""
from __future__ import annotations

import argparse
import bisect
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
import horizon_decay as HD  # noqa: E402
import topk_test as TK  # noqa: E402

MIN = 60
WINS = 2000.0
HOR = (2, 5, 30)
FITUR = ("svu15", "svu5", "svn15", "svm15", "vpb15")


def w(x):
    return max(-WINS, min(WINS, x))


def rows_tx():
    per = {}
    for ln in io.open(os.path.join(ROOT, "universe", "wallet-flow.jsonl"), encoding="utf-8",
                      errors="replace"):
        if not ln.startswith("{"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("k") not in ("tx", "txc"):
            continue
        tk, t, p = str(d.get("tk") or "").lower(), int(d.get("t") or 0), float(d.get("p") or 0)
        if not tk or not t or p <= 0:
            continue
        per.setdefault(tk, []).append({"t": t, "p": p, "u": float(d.get("u") or 0),
                                       "buy": bool(d.get("b")), "m": str(d.get("m") or "").lower()})
    for tk in per:
        per[tk].sort(key=lambda r: r["t"])
    return per


def imbalance(rrows, t, menit, mode):
    """(beli - jual) / (beli + jual) pada jendela [t-menit, t]; mode: usd | n | maker | bucket."""
    akir = [r for r in rrows if t - menit * MIN <= r["t"] <= t]
    if not akir:
        return None
    b = [r for r in akir if r["buy"]]
    s = [r for r in akir if not r["buy"]]
    if mode == "usd":
        x, y = sum(r["u"] for r in b), sum(r["u"] for r in s)
    elif mode == "n":
        x, y = float(len(b)), float(len(s))
    elif mode == "maker":
        x, y = float(len({r["m"] for r in b if r["m"]})), float(len({r["m"] for r in s if r["m"]}))
    else:  # bucket / VPIN-style pada bucket volume sama
        tot = sum(r["u"] for r in akir)
        if tot <= 0:
            return None
        target = tot / max(1.0, min(10.0, len(akir) / 2.0))
        acc, signs, cur = 0.0, [], 0.0
        for r in sorted(akir, key=lambda q: q["t"]):
            cur += r["u"]
            acc += r["u"] * (1 if r["buy"] else -1)
            if cur >= target:
                signs.append(acc)
                cur, acc = 0.0, 0.0
        if not signs:
            return None
        tot_abs = sum(abs(x) for x in signs)
        return round(abs(sum(signs)) / tot_abs, 5) if tot_abs > 0 else None
    if (x + y) <= 0:
        return None
    return round((x - y) / (x + y), 5)


def bangun():
    """Kejadian + outcome diambil dari `tools/horizon_decay.py` - bukan salinan yang 'mirip'.

    Ini pelajaran F-D41/E10: begitu definisi hasil ditulis ulang di alat baru, angka dua alat tidak
    lagi bisa dibandingkan, dan perbedaannya akan dibacakan sebagai efek. `kejadian()` sudah memakai
    ticker `wp` sebagai harga masuk/keluar, non-overlap per horison, dan berhenti di `t_kunci` watch;
    `net_pada()` juga melaporkan umur baris yang dipakai, jadi label "2 menit" adalah ukuran.
    """
    ev_base, sensor = HD.kejadian(max(HOR))
    txs = rows_tx()
    rt = costs.rt_cost()
    ev = []
    for e in ev_base:
        net = {h: HD.net_pada(e, h, rt) for h in HOR}
        umur = {h: HD.umur_keluar(e, h) for h in HOR}
        if net[5] is None or net[max(HOR)] is None:
            sensor["tanpa_keluar"] = sensor.get("tanpa_keluar", 0) + 1
            continue
        rrows = txs.get(e["tk"], [])
        ev.append({"tk": e["tk"], "t": e["t"], "net": net,
                   "umur_keluar": {str(h): umur[h] for h in HOR},
                   "svu15": imbalance(rrows, e["t"], 15, "usd"),
                   "svu5": imbalance(rrows, e["t"], 5, "usd"),
                   "svn15": imbalance(rrows, e["t"], 15, "n"),
                   "svm15": imbalance(rrows, e["t"], 15, "maker"),
                   "vpb15": imbalance(rrows, e["t"], 15, "bucket")})
    return ev, sensor, rt


def uji(ev, f, rnd, draws, seeds=40):
    xs = [e for e in ev if isinstance(e.get(f), (int, float))]
    if len(xs) < 60:
        return {"fitur": f, "n": len(xs), "status": "TERLALU KECIL"}

    def bagi():
        urutan = xs[:]
        rnd.shuffle(urutan)                  # tie-break acak: fitur biner punya banyak ties
        return ([w(e["net"][5]) for e in urutan[len(urutan) // 2:]],
                [w(e["net"][5]) for e in urutan[:len(urutan) // 2]])

    atas, bawah = bagi()
    # SATU pembagian bukan hasil: run sebelumnya memberi tanda selisih yang BERBEDA untuk
    # svm15/svu5 antara dua eksekusi, murni karena shuffle. Jadi selisih dilaporkan sebagai
    # distribusi dari `seeds` pembagian - sama seperti perlakuan E7 setelah F-D39.
    ss = []
    for _ in range(seeds):
        a, b = bagi()
        ss.append(sum(a) / len(a) - sum(b) / len(b))
    ss.sort()
    selisih = ss[len(ss) // 2]
    p_mw = FC.mann_whitney_p(atas, bawah)
    lo, hi = boot(atas)
    # placebo: fitur digeser asal-mulanya (kejadian lain pada token lain), hubungan diputus
    pool = atas + bawah
    pl = []
    for _ in range(draws):
        idx = list(range(len(pool)))
        rnd.shuffle(idx)
        a = [pool[i] for i in idx[:len(atas)]]
        bb = [pool[i] for i in idx[len(atas):len(atas) + len(bawah)]]
        pl.append(sum(a) / len(a) - sum(bb) / len(bb))
    pl.sort()
    # Placebo diukur pada DUA ekor. Versi pertama hanya menjaga ekor atas, jadi selisih NEGATIF
    # (arah terbalik terhadap teori) tidak bisa dinyatakan apa-apa: angka -157,6 vs "CI atas +284,6"
    # terlihat aman padahal yang perlu ditanya adalah seberapa sering placebo menghasilkan selisih
    # se-ekstrem itu di sisi bawah.
    lo_ci = pl[int(0.025 * draws)]
    p_bawah = sum(1 for x in pl if x <= selisih) / float(draws)
    p_dua_ekor = min(1.0, 2.0 * min((sum(1 for x in pl if x >= selisih) + 1) / (draws + 1.0),
                                    (sum(1 for x in pl if x <= selisih) + 1) / (draws + 1.0)))
    return {"fitur": f, "n": len(xs), "n_atas": len(atas), "n_bawah": len(bawah),
            "median_net_atas": round(FC.med(atas), 1), "median_net_bawah": round(FC.med(bawah), 1),
            "mean_net_atas": round(sum(atas) / len(atas), 1),
            "mean_net_bawah": round(sum(bawah) / len(bawah), 1),
            "selisih": round(selisih, 1), "sebar_selisih": [round(ss[0], 1),
                                                            round(ss[-1], 1)],
            "frac_selisih_positif": round(sum(1 for x in ss if x > 0) / float(len(ss)), 2),
            "ci_bawah_atas": round(lo, 1),
            "p_mw": None if p_mw is None else round(p_mw, 5),
            "placebo_ci": [round(lo_ci, 1), round(pl[int(0.975 * draws)], 1)],
            "p_placebo_dua_ekor": round(p_dua_ekor, 4),
            "ekstrem_di_bawah_placebo": selisih < lo_ci,
            "di_atas_placebo": selisih > pl[int(0.975 * draws)],
            "di_atas_nol": selisih > 0 and lo > 0}


def boot(xs, draws=2000, seed=20260929):
    rnd = random.Random(seed)
    n = len(xs)
    m = sorted(sum([xs[rnd.randrange(n)] for _ in range(n)]) / n for _ in range(draws))
    return m[int(0.025 * draws)], m[int(0.975 * draws)]


def bh(res):
    ps = [(r["fitur"], r["p_mw"]) for r in res if r.get("p_mw") is not None]
    if not ps:
        return []
    ps.sort(key=lambda x: x[1])
    k = 0
    for i, (_f, p) in enumerate(ps, 1):
        if p <= i / len(ps) * 0.10:
            k = i
    return [f for f, _p in ps[:k]]


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    ev, sensor, rt = bangun()
    print("E18 signed-volume imbalance | %d kejadian | outcome `wp` @%s m | ongkos %.1f bps | "
          "batas jelajah %s" % (len(ev), list(HOR), rt,
                                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(TK.T_BATAS))))
    print("sensor %s" % json.dumps(sensor, sort_keys=True))
    if len(ev) < 60:
        raise SystemExit("kejadian terlalu sedikit - ini BUKAN 'tidak ada efek'")
    rnd = random.Random(20260929)
    res = [uji(ev, f, rnd, a.draws) for f in FITUR]
    print("   (pembagian = kuantil posisional dengan tie-break acak, bukan \x22di atas median\x22 - "
          "dengan fitur biner median_low membuat satu kelompok kosong)")
    print("\n   %-8s %6s %8s %12s %12s %11s %12s %11s %s"
          % ("fitur", "n", "n a/b", "median a|b", "mean a|b", "selisih", "p95 placebo", "p MW",
             "vonis"))
    for r in res:
        if r.get("status"):
            print("   %-8s %6d  %s" % (r["fitur"], r["n"], r["status"]))
            continue
        print("   %-8s %6d %4d/%-4d %+6.1f|%+7.1f %+6.1f|%+7.1f %+11.1f %+12.1f %-11s %-38s %-9s %s%s"
              % (r["fitur"], r["n"], r["n_atas"], r["n_bawah"], r["median_net_atas"],
                 r["median_net_bawah"], r["mean_net_atas"], r["mean_net_bawah"], r["selisih"],
                 r["placebo_ci"][1], "%s" % ("%.4f" % r["p_mw"] if r["p_mw"] else "-"),
                 ("DI ATAS PLACEBO" if r["di_atas_placebo"] else
                  ("DI BAWAH PLACEBO (arah TERBALIK dari teori)" if r["ekstrem_di_bawah_placebo"]
                   else "dalam placebo")),
                 "p2=%s" % r["p_placebo_dua_ekor"],
                 "sebar %+.0f..%+.0f | %2.0f%% pembagiaan positif"
                 % (r["sebar_selisih"][0], r["sebar_selisih"][-1],
                    100.0 * r["frac_selisih_positif"]),
                 " +di atas nol" if r["di_atas_nol"] else ""))
    um = [e["umur_keluar"]["5"] for e in ev
              if isinstance(e["umur_keluar"].get("5"), (int, float))]
    if um:
        tersusun = sorted(um)
        print("   umur baris harga keluar @5m (detik): median %+0.0f | p90 %+0.0f | "
              "persen lebih tua dari horison %0.1f"
              % (FC.med(um), tersusun[int(0.9 * (len(tersusun) - 1))],
                 100.0 * sum(1 for x in um if abs(x) > 5 * MIN) / len(um)))
    lulus_bh = bh(res)
    print("\nBH alpha 0,10 atas %d hipotesis: %s" % (len(res), lulus_bh or "KOSONG"))
    print("di atas placebo: %s | DI BAWAH placebo (arah terbalik): %s"
          % ([r["fitur"] for r in res if r.get("di_atas_placebo")] or "TIDAK ADA",
             [r["fitur"] for r in res if r.get("ekstrem_di_bawah_placebo")] or "TIDAK ADA"))
    print("\nCatatan yang tidak boleh hilang: satu pemenang dari %d uji = KANDIDAT (F-D39), dan"
          % len(res))
    print("yang diuji di sini adalah rasio berimbang dari transaksi, bukan buku order (T1 ada di")
    print("halaman 22, terkunci, vonis 21:37:45Z).")
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "kejadian": len(ev),
           "sensor": sensor, "horison_menit": list(HOR), "ongkos_bps_rt": rt, "hasil": res,
           "bh_lulus": lulus_bh, "draws": a.draws}
    out["sha"] = "0x" + hashlib.sha256(json.dumps(res, sort_keys=True).encode()).hexdigest()
    p = os.path.join(ROOT, "decisions", "flow-variasi-%s.json"
                     % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("artefak: decisions/%s" % os.path.basename(p))


def self_test():
    """Alatnya harus bisa bilang 'tidak ada efek' pada data yang hubungannya diputus."""
    def baris(t, u, buy, m):
        return {"t": t, "p": 1.0, "u": u, "buy": buy, "m": m}
    rrows = [baris(1000 - i * 10, 100.0, i % 2 == 0, "0x%d" % (i % 4)) for i in range(10)]
    x = imbalance(rrows, 1000, 15, "usd")
    assert isinstance(x, float) and -1 <= x <= 1, x
    assert imbalance([], 1000, 15, "usd") is None
    sepi = [{"t": 900, "p": 1.0, "u": 0.0, "buy": True, "m": "a"}]
    assert imbalance(sepi, 1000, 15, "usd") is None, "nol-total harus None, bukan 0"
    beli_only = [baris(990, 500.0, True, "a"), baris(991, 500.0, True, "b")]
    assert abs(imbalance(beli_only, 1000, 15, "usd") - 1.0) < 1e-9
    assert abs(imbalance(beli_only, 1000, 15, "maker") - 1.0) < 1e-9
    assert imbalance(beli_only, 1000, 15, "bucket") is not None
    # dan yang penting: placebo TIDAK boleh bisa 'menang' saat hubungan diputus total
    rnd = random.Random(3)
    ev = []
    for i in range(400):
        ev.append({"tk": "0xt", "t": 1000 + i, "net": {5: (50.0 if i % 2 else -50.0)},
                   "svu15": (0.5 if i % 2 else -0.5), "svu5": 0.0, "svn15": 0.0, "svm15": 0.0,
                   "vpb15": 0.0})
    acak = [dict(e, svu15=rnd.choice([0.5, -0.5])) for e in ev]
    acak = [dict(e, svu15=rnd.choice([0.5, -0.5])) for e in ev]
    u = uji(acak, "svu15", rnd, 60)
    assert not u.get("status"), u
    assert abs(u["selisih"]) < 400, "hubungan yang diputus tidak boleh dibaca jadi efek: %s" % u
    # dan yang lama: dua nilai biner saja tidak boleh membuat satu kelompok kosong (membagi nol)
    biner = [dict(e, svn15=(0.5 if i % 2 else -0.5)) for i, e in enumerate(ev)]
    assert not uji(biner, "svn15", rnd, 60).get("status"), uji(biner, "svn15", rnd, 60)["status"]
    print("self-test E18 OK: imbalance terarah, nol-total -> None, dan hubungan acak tidak "
          "dibaca jadi efek")


if __name__ == "__main__":
    utama()
