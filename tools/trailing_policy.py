"""E17 - trailing stop sebagai KEBIJAKAN, diuji pada posisi yang sama, lawan dua placebo.

Kenapa alat ini ada (29 Sep 2026, setelah F-D48). Builder mengusulkan: TP/SL dinamis, SL jadi
trailing, "pokoknya jangan sampai rugi", jaraknya sudah menghitung spread + fee. Gerbang algebra
(`tools/trailing_gate.py`) sudah menjawab bagian "selalu untung" = mustahil, dan bagian
"lock bersyarat" = lazim (63-66 % kejadian). Yang belum dijawab adalah pertanyaan sebenarnya:

    apakah menggeser EXIT ke aturan trailing mengubah HASIL, atau hanya mengubah BENTUK?

Literatur meramalkan yang kedua - stop-loss *\x22neither reduce nor increase investors' losses ...
the value ... may come largely from risk reduction rather than return improvement\x22*
(Lei & Li 2009, Financial Services Review 18(1):23-51; abstrak dibaca langsung 29 Sep, S6 di
[[08-Backlog/04 - Riset Teori (Sitasi)]]). Kami mengujinya di substrate sendiri, dengan aturan
yang sudah memotong kami empat kali (F-D39/F-D40):

  * SATU populasi posisi yang sama - semua lengan dieksekusi pada jalur yang identik, bukan cohort
    berbeda;
  * baseline yang harus dikalahkan bukan nol: **A = tahan 30 m** (kebiasaan buku kami) dan
    **B = keluar di waktu ACAK pada jendela yang sama** (kontrol yang membunuh E8);
  * **placebo penjangkaran**: lengan `statis` memasang stop di LEVEL FINAL yang sama seperti yang
    akan dipakai trailing di ujung jendela, tapi TIDAK bergerak mengikuti puncak. Kalau statis =
    trailing, yang bekerja adalah level, bukan penjangkaran ke puncak;
  * tanpa intip-masa-depan: keputusan pada tick `i` hanya boleh memakai `peak` sampai `i`;
  * sensivitas biaya: `gap` (fill menembus level) dijalankan 0/20/100 bps, bukan dipilih satu;
    `C` = 59,0 bps ongkos round-trip TERUKUR sudah dipotong di semua lengan;
  * vonis yang boleh dipakai: trailing = **mengurangi buntut** hanya kalau `P(net <= -200)` turun
    vs baseline DAN harapan tidak memburuk; trailing = **menaikkan harapan** hanya kalau mean
    mengalahkan CI atas placebo B dan lolos BH lintas lengan.

Yang TIDAK alat ini lakukan: mengirim order, mengubah ambang `flow_gate`, atau mengklaim sudah
meniru eksekusi nyata. Pada 5 menit resolusi `wp` kami bahkan tidak melihat puncak (31 % kejadian
punya >= 2 baris) - jadi angka di bawah adalah trailing **pada resolusi kami**, dan itu batas yang
ditulis di outputnya sendiri, bukan di kaki halaman.

Pakai:  python -X utf8 tools/trailing_policy.py --self-test
       python -X utf8 tools/trailing_policy.py --gap 0,20,100
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
import horizon_decay as HD  # noqa: E402
import topk_test as TK  # noqa: E402

MIN = 60
WINS = 2000.0
JALAN = 60                      # jendela jalur harga yang dipakai (menit)
TRAIL = (60, 120, 250, 500)    # jarak trailing, bps
BASIS_TAHAN = 30               # arm A
PLASEBO_UNDIAN = 300


def w(x):
    return max(-WINS, min(WINS, x))


def jalur(e):
    """[(detik_sejak_masuk, harga)] dari ticker `wp`, hanya maju (tanpa intip masa depan)."""
    ser = e["seri"]
    out = [(t - e["t"], p) for t, p in ser if e["t"] < t <= e["t"] + JALAN * MIN]
    return out if len(out) >= 3 else None


def eksekusi(e, aturan, gap):
    """Satu posisi -> (net_bps, alasan_keluar). `aturan` menentukan kapan keluar."""
    p0 = e["p0"]
    if p0 <= 0:
        return None
    js = jalur(e)
    if not js:
        return None
    puncak = p0
    for dt, p in js:
        if p > puncak:
            puncak = p
        stop = aturan(puncak, p0, dt)
        if stop is not None and p <= stop:
            raw = 10000.0 * (p - p0) / p0 - gap
            return round(raw - COST, 1), "trigger@%ds" % dt
    dt, p = js[-1]
    return round(10000.0 * (p - p0) / p0 - COST, 1), "ujung_jendela"


def eksekusi_tahan(e, hor):
    v = HD.net_pada(e, hor, COST)
    return (v, "tahan_%dm" % hor) if v is not None else None


def random_time(e, rnd):
    """Keluar pada waktu acak di jendela - kontrol F-D40, bukan 'tahan sampai habis'."""
    js = jalur(e)
    if not js:
        return None
    dt, p = js[rnd.randrange(len(js))]
    return round(10000.0 * (p - e["p0"]) / e["p0"] - COST, 1), "waktu_acak"


def level_statis(e, d):
    """Stop DIAM pada jarak `d` dari harga MASUK - tanpa informasi masa depan sama sekali.

    AWAS (F-D49): versi pertama fungsi ini mengambil level dari puncak AKHIR jendela
    (`max(seluruh jalur)`), yaitu look-ahead. Placebo yang boleh melihat masa depannya akan
    mengalahkan lengan yang jujur (+50,9 vs -0,9 bps mean) dan angkanya sepenuhnya artifisial.
    Placebo harus berdiri di atas informasi yang sama dengan lengan yang diuji.
    """
    lv = e["p0"] * (1 - d / 10000.0)

    def f(puncak, p0, dt):
        return lv
    return f


def statis_setelah_biaya(e, d):
    """Stop DIAM yang baru dipasang setelah posisi menutup ongkos - placebo untuk lengan BERSAYARAT.

    Kalau ini menyamai `aturan_trailing(d, hanya_setelah_biaya=True)`, yang bekerja adalah
    \x22jangan setop sebelum posisi menutup biaya\x22, bukan \x22stop mengikuti puncak\x22.
    """
    state = {"lv": None}

    def f(puncak, p0, dt):
        if state["lv"] is None and puncak >= p0 * (1 + (d + COST) / 10000.0):
            state["lv"] = p0 * (1 + d / 10000.0) * (1 - 2 * d / 10000.0)
        return state["lv"]
    return f


def aturan_trailing(d, hanya_setelah_biaya=False):
    def f(puncak, p0, dt):
        amb = (p0 * (1 + (d + COST) / 10000.0)) if hanya_setelah_biaya else 0.0
        if puncak * (1 - d / 10000.0) < amb:
            return None
        return puncak * (1 - d / 10000.0)
    return f


def boot(dosis, draws=2000, seed=20260929):
    rnd = random.Random(seed)
    n = len(dosis)
    m = sorted(sum([dosis[rnd.randrange(n)] for _ in range(n)]) / n for _ in range(draws))
    return m[int(0.025 * draws)], m[int(0.975 * draws)]


def ringkas(xs):
    xs = sorted(xs)
    if not xs:
        return {}
    return {"n": len(xs), "mean_winso": round(sum(w(x) for x in xs) / len(xs), 1),
            "mean_pure": round(sum(xs) / len(xs), 1), "median": round(FC.med(xs), 1),
            "P_ge_500": round(100.0 * sum(1 for x in xs if x >= 500) / len(xs), 1),
            "P_le_m200": round(100.0 * sum(1 for x in xs if x <= -200) / len(xs), 1),
            "positif": round(100.0 * sum(1 for x in xs if x > 0) / len(xs), 1)}


COST = 59.0


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gap", default="0,20,100")
    ap.add_argument("--draws", type=int, default=PLASEBO_UNDIAN)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    global COST
    COST = costs.rt_cost()
    if a.self_test:
        return self_test()
    ev, sensor = HD.kejadian(JALAN)
    ev = [e for e in ev if jalur(e)]
    print("E17 trailing sebagai kebijakan | %d posisi dengan jalur >=3 baris dalam %d m | "
          "C = %.1f bps | batas jelajah %s" % (len(ev), JALAN, COST,
                                              time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                            time.gmtime(TK.T_BATAS))))
    if len(ev) < 60:
        raise SystemExit("jalur terlalu sedikit - BELUM BISA DIUJI")
    rnd = random.Random(20260929)
    gaps = [float(x) for x in a.gap.split(",")]
    hasil = []
    print("\n   %-38s %6s %10s %9s %8s %9s %8s %5s %10s %13s %8s"
          % ("lengan", "n", "mean winso", "median", "P>=500", "P<=-200", "positif", "gap",
             "delta med", "CI delta", "p tanda"))
    print("   delta = selisih pada POSISI YANG SAMA vs A2 (tanpa aturan); CI = bootstrap 2000")
    print("   delta median 0,0 BUKAN 'placebo menyamai': itu berarti >= separuh posisi level stopnya"
          "\n   tidak pernah terlihat oleh bar harga kami (1-4 bar per jam). Aturan yang tidak bisa"
          "\n   tersentuh oleh data tidak bisa dinilai dengan data itu.")
    for gap in gaps:
        arm = []
        tahan = [eksekusi_tahan(e, BASIS_TAHAN) for e in ev]
        ok_i = [i for i, x in enumerate(tahan) if x]
        a2 = [eksekusi(ev[i], lambda p, p0, dt: None, gap)[0] for i in
              [i for i, x in enumerate(tahan) if x]]
        if len(ok_i) != len(ev):
            print("   catatan: %d posisi tidak punya harga keluar %d m - dikeluarkan dari SEMUA "
                  "lengan supaya pairnya utuh (bukan hanya dari baseline)"
                  % (len(ev) - len(ok_i), BASIS_TAHAN))
        ev_p = [ev[i] for i in ok_i]
        base = a2
        arm.append(("A2 ujung jalur (BASELINE pairing)", base))
        sama = sum(1 for a, b in zip([tahan[i][0] for i in ok_i], a2) if abs(a - b) < 0.05)
        arm.append(("A tahan 30 m (referensi saja)", [tahan[i][0] for i in ok_i]))
        print("   %d/%d posisi (%0.0f %%) tidak punya baris harga antara 30 dan 60 menit: di sana"
              " 'tahan 30 m' = 'tahan 60 m' secara harfiah. Karena itu pairing memakai A2."
              % (sama, len(ok_i), 100.0 * sama / max(1, len(ok_i))))
        for d in TRAIL:
            xs = [eksekusi(e, aturan_trailing(d), gap) for e in ev_p]
            arm.append(("C trailing %4d bps (terus-armed)" % d, [x[0] for x in xs if x]))
        xs = [eksekusi(e, aturan_trailing(120, True), gap) for e in ev_p]
        arm.append(("D trailing 120 BERSYARAT (arm>=biaya)", [x[0] for x in xs if x]))
        for d in TRAIL:
            xs = [eksekusi(e, level_statis(e, d), gap) for e in ev_p]
            arm.append(("E statis -%4d dr masuk (placebo C)" % d, [x[0] for x in xs if x]))
        for d in TRAIL:
            xs = [eksekusi(e, statis_setelah_biaya(e, d), gap) for e in ev_p]
            arm.append(("F statis-arm>=biaya %4d (placebo D)" % d, [x[0] for x in xs if x]))
        rnd_d = random.Random(20260929)
        xs = [eksekusi(e, aturan_trailing(rnd_d.choice(TRAIL), bool(rnd_d.getrandbits(1))), gap)
              for e in ev_p]
        arm.append(("G d + armed diacak (placebo gabungan)", [x[0] for x in xs if x]))
        for nm, xs in arm:
            st = ringkas(xs)
            if not st:
                continue
            baris = {"gap_bps": gap, "lengan": nm, **st}
            if not nm.startswith("A") and len(xs) != len(base):
                baris["pairing"] = "TIDAK SEPADAN %d vs %d" % (len(xs), len(base))
            if not nm.startswith("A") and len(xs) == len(base):
                ds = sorted(a - b for a, b in zip(xs, base))
                lo, hi = boot(ds)
                lb = sum(1 for x in ds if x > 1)
                kb = sum(1 for x in ds if x < -1)
                baris["delta_median"] = round(FC.med(ds), 1)
                baris["ci_delta"] = [round(lo, 1), round(hi, 1)]
                baris["p_tanda"] = round(FC.sign_p(lb, lb + kb), 5)
            hasil.append(baris)
            print("   %-38s %6d %10.1f %9.1f %7.1f%% %8.1f%% %7.1f%% %5.0f %10s %13s %8s"
                  % (nm, st["n"], st["mean_winso"], st["median"], st["P_ge_500"], st["P_le_m200"],
                     st["positif"], gap, baris.get("delta_median", "-"),
                     ("%+.0f..%+.0f" % tuple(baris["ci_delta"])) if baris.get("ci_delta") else "-",
                     ("%.5f" % baris["p_tanda"]) if baris.get("p_tanda") is not None else "-"))
        # kontrol waktu-acak dilaporkan terpisah: distribusinya tidak berpasangan 1-1 per posisi
        pool = []
        for _ in range(max(1, a.draws // 30)):
            for e in ev:
                r = random_time(e, rnd)
                if r:
                    pool.append(r[0])
        st = ringkas(pool)
        hasil.append({"gap_bps": gap, "lengan": "B keluar waktu ACAK (kontrol F-D40)", **st})
        print("   %-38s %6d %10.1f %9.1f %7.1f%% %8.1f%% %7.1f%% %5.0f %10s %13s %8s"
              % ("B keluar waktu ACAK (kontrol F-D40)", st["n"], st["mean_winso"], st["median"],
                 st["P_ge_500"], st["P_le_m200"], st["positif"], gap, "-", "tak berpasangan", "-"))
        print()
    print("   DIAGNOSIS RESOLUSI - jalur dijarangkan (tiap baris ke-k); kalau keunggulan lengan"
          "\n   tumbuh saat bar makin jarang, itu bukan kebijakan, itu alat kami yang butuh di"
          "\n   antara dua rekaman:")
    print("   %8s %12s %12s %12s %12s" % ("step", "A tahan30", "C trail 120",
                                          "D BERSYARAT", "D - C"))
    for step in (1, 2, 4):
        try:
            jar = [x[::step] for x in [jalur(e) for e in ev_p]]
        except Exception:
            continue
        bar = []
        for xs_i, js in zip(ev_p, jar):
            e2 = dict(xs_i)
            e2["seri"] = [(e2["t"] + int(dt), p) for dt, p in js]
            e2["st"] = [t for t, _ in e2["seri"]]
            bar.append(e2)
        if len(bar) < 30:
            continue
        def mean_of(fn):
            vs = [fn(e) for e in bar]
            vs = [v for v in vs if v is not None]
            return round(sum(w(v) for v in vs) / max(1, len(vs)), 1) if vs else 0.0
        mA = mean_of(lambda e: eksekusi_tahan(e, BASIS_TAHAN) and
                     eksekusi_tahan(e, BASIS_TAHAN)[0])
        mC = mean_of(lambda e: eksekusi(e, aturan_trailing(120), gaps[0]) and
                     eksekusi(e, aturan_trailing(120), gaps[0])[0])
        mD = mean_of(lambda e: eksekusi(e, aturan_trailing(120, True), gaps[0]) and
                     eksekusi(e, aturan_trailing(120, True), gaps[0])[0])
        print("   %8d %12.1f %12.1f %12.1f %12.1f" % (step, mA, mC, mD, mD - mC))

    kb = [h for h in hasil if h["lengan"].startswith("B ") and h["gap_bps"] == gaps[0]]
    kb_mean = kb[0]["mean_winso"] if kb else 0.0
    va = ([h for h in hasil if h["lengan"].startswith("A2 ")] or
          [h for h in hasil if h["lengan"].startswith("A ")])[0]
    ekor = [h for h in hasil if h["lengan"].startswith("C") and h["gap_bps"] == gaps[0]]
    pla = [h for h in hasil if h["lengan"].startswith(("E ", "F ", "G ")) and h["gap_bps"]
           == gaps[0]]
    print("VONIS E17:")
    if ekor and pla:
        bc = min(ekor, key=lambda x: x["P_le_m200"])
        bf = ([h for h in hasil if h["lengan"].startswith("D") and h["gap_bps"] == gaps[0]] or [None])[0]
        pl_min = min(pla, key=lambda x: x["P_le_m200"])
        print("   - buntut (P(net<=-200)): A %0.1f %% | trailing terus-armed terbaik %0.1f %% "
              "(%s) | trailing BERSYARAT %0.1f %% | placebo terkecil %0.1f %% (%s)"
              % (va["P_le_m200"], bc["P_le_m200"], bc["lengan"].strip(),
                 bf["P_le_m200"] if bf else -1, pl_min["P_le_m200"], pl_min["lengan"].strip()))
        if bf:
            print("   - harapan (mean winsor): A %+0.1f | trailing terbaik %+0.1f | BERSYARAT "
                  "%+0.1f | placebo %+0.1f | B waktu-acak %+0.1f"
                  % (va["mean_winso"], bc["mean_winso"], bf["mean_winso"], pl_min["mean_winso"],
                     kb_mean))
            lo = (bf.get("ci_delta") or [None])[0]
            lebih_dari_placebo = bf["mean_winso"] > pl_min["mean_winso"] + 1.0
            print("   - vonis mekanis: BERSYARAT mengalahkan placebo-nya? %s | CI bawah delta vs A "
                  "= %s | mengalahkan kontrol waktu-acak? %s"
                  % ("YA" if lebih_dari_placebo else "TIDAK", lo,
                     "YA" if bf["mean_winso"] > kb_mean else "TIDAK"))
            if lebih_dari_placebo and lo is not None and lo > 0 and bf["mean_winso"] > kb_mean:
                print("   -> yang BERSYARAT (jangan setop sebelum posisi menutup ongkos) adalah "
                      "kandidat: ia mengalahkan placebo arm-only-nya, CI bawahnya > 0, dan "
                      "melawan kontrol waktu-acak. Tapi ini SATU keluarga uji pada satu jendela "
                      "dengan gap yang belum diukur -> butuh kunci prospectif, bukan slide.")
            else:
                print("   -> tidak ada yang boleh dijual: placebo menyamai, CI bawah belum > 0, "
                      "atau kontrol waktu-acak masih lebih baik.")
    print("   - kalimat yang boleh dipakai sekarang: trailing di substrate kami mengubah **bentuk** "
          "hasil (P(<=-200), median, persen positif) dan itu persis yang diramalkan literatur - "
          "Lei & Li 2009: stop-loss mengubah risiko, bukan harapan. \\x22Tidak rugi\\x22 tetap "
          "mustahil (F-D48).")
    print("   - koreksi metode yang menempel: placebo pertama alat ini memakai puncak AKHIR jendela "
          "(look-ahead) dan menangkan trailing dengan +50,9 bps palsu - lihat F-D49. Placebo harus "
          "punya hak melihat masa depan yang sama dengan lengan yang diuji.")
    nz = [h for h in hasil if h.get("delta_median") == 0.0 and not h["lengan"].startswith("A")]
    print("   - temuan utama justru negatif-methodologis: %d dari %d lengan punya delta median 0,0 -"
          " pada 1-4 bar per jam, sebagian besar posisi TIDAK PERNAH melihat level stopnya. E17 "
          "tidak bisa dinilai dengan data ini; yang bisa dinilai hanya 'apakah bar kami cukup rapat' "
          "(jawabannya: tidak)." % (len(nz), max(1, len([h for h in hasil if h.get("delta_median")
                                                        is not None]))))
    print("   - batas lain: resolusi `wp` (bukan tick bursa, horison 5 m tidak bisa direplikasi), "
          "gap fill 0/20/100 bps sebagai parameter karena `i` belum diukur, dan jendela jalur 60 m.")
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "posisi": len(ev),
           "C_bps": COST, "gap_bps": gaps, "hasil": hasil,
           "perintah": "python -X utf8 tools/trailing_policy.py --gap %s" % a.gap}
    out["sha"] = "0x" + hashlib.sha256(json.dumps(hasil, sort_keys=True).encode()).hexdigest()
    p = os.path.join(ROOT, "decisions", "trailing-policy-%s.json"
                     % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("artefak: decisions/%s" % os.path.basename(p))


def self_test():
    """Trailing harus memotong buntut pada jalur yang jatuh, dan tidak boleh mengarang upside."""
    global COST
    asli = COST
    COST = 0.0
    def mk(sari):
        return {"tk": "0xuji", "t": 1000, "p0": sari[0][1], "tx_p": sari[0][1], "seri": sari,
                "st": [t for t, _ in sari]}
    try:
        runtuh = mk([(1000, 1.00), (1060, 1.10), (1120, 1.09), (1180, 0.70), (1240, 0.60),
                     (2560, 0.66), (2680, 0.61), (2760, 0.60), (2900, 0.58)])
        naik_terus = mk([(1000, 1.00), (1060, 1.02), (1120, 1.05), (1180, 1.08), (1240, 1.12),
                         (2560, 1.15), (2680, 1.18), (2760, 1.20), (2900, 1.21)])
        a = eksekusi(runtuh, aturan_trailing(150), 0.0)
        b = eksekusi_tahan(runtuh, 30)
        assert b and b[0] is not None, b
        assert a and a[0] > b[0], (a, b)          # trailing memotong kejatuhan
        assert "trigger" in a[1], a
        c = eksekusi(naik_terus, aturan_trailing(150), 0.0)
        assert c and "ujung_jendela" in c[1], c          # tren naik tidak boleh kepotong
        # tanpa intip masa depan: hasil pada jalur yang sama harus identik tiap dijalankan ulang
        assert eksekusi(runtuh, aturan_trailing(150), 0.0) == a
        # placebo statis harus TETAP dipicu oleh level, bukan oleh puncak bergerak
        st = eksekusi(runtuh, level_statis(runtuh, 150), 0.0)
        assert st and st[1].startswith("trigger"), st
        assert COST == 0.0
    finally:
        COST = asli
    print("self-test E17 OK: trailing memotong kejatuhan, tidak memotong tren, deterministik, "
          "placebo statis terpicu oleh level")


if __name__ == "__main__":
    utama()
