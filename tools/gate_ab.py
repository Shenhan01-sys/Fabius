"""E22 - apakah REM bekerja pada data yang belum terjadi, di horison tempat kabar hidup?

Kenapa alat ini ada (29 Sep 2026 ±11:5xZ). Satu-satunya perilaku Fabius yang bertahan setelah
sepekan mencabut klaim sendiri adalah `jual_*` di `tools/flow_gate.py`: F-D31 mengukurnya di horison
30 menit (+82,7 -> +162,3 bps), F-D44 mengukurnya lagi di menit ke-5 (`BOLEH` +285,5 vs `VETO`
-230,3, melewati placebo, dan 16/16 kombinasi ambang lolos di F-D45). Semuanya **di dalam sampel**
yang sama, sampai jam `t_kunci` watch.

Itu posisi yang berbahaya, karena kami sudah tiga kali melihat pola yang sama: angka bagus ->
promosi diam-diam -> mati di hari kedua (F-D30 harga masuk beku, F-D32 control mempromosikan
dirinya, F-D39 satu undian disebut hasil, F-D40 kontrol keluar yang salah, F-D46 satuan dampak).
Satu-satunya obat yang kami punya adalah menulis aturannya SEKARANG, sebelum satu pun pasangan
pasca-kunci dihitung, lalu membiarkan jam bekerja.

Yang diikat (dan ini yang membedakan dari E13):
  populasi   : kejadian beli ⑦ dengan `t > t_kunci` - data yang belum pernah kami lihat
  lengan     : `BOLEH` (gerbang lulus) vs `VETO` (gerbang menolak), dievaluasi pada MENIT KE-5
  outcome    : median ticker `wp` pada t+[2m, 8m], dikurangi harga masuk `wp` terakhir sebelum t,
               dikurangi ongkos round-trip TERUKUR 59,0 bps (`tools/costs.py`)
  kontrolnya : bukan nol. Vonis primer = selisih mean(BOLEH) - mean(VETO), winsor +/-1.500 bps
               (lebih ketat dari E11/E13 karena ekor micro-cap ini bisa 8000x; diganti di spec)
  placebo    : label BOLEH/VETO diacak ulang pada angka yang sama (1.000 undian) - vonis hanya
               kalau selisih sebenarnya melewati CI atas placebo-nya
  wajib      : umur baris harga keluar + `P(ada harga keluar)` per lengan (aturan F-D41),
               karena dua hal itu-lah yang membuat horison jadi ukuran, bukan nama

Vonis LAYAK bila EMPAT-nya serentak: (1) n_BOLEH >= 40 dan n_VETO >= 15; (2) median(BOLEH) > 0
DAN CI bawah bootstrap 4000 dari selisih > 0; (3) satu arah (BOLEH > VETO) p < 0,05 pada
Mann-Whitney DAN placebo; (4) P(ada harga keluar) kedua lengan >= 60 % dan umur barisnya dilaporkan.
Syarat umur kunci **8 jam** (bukan 12 seperti kebiasaan kami) - dan itu kusetujui SEKARANG, sebelum
ada angka: tenggat submission 30 Sep 16:59Z, dan 8 jam siklus ⑦ (~200 d) memberi ratusan kejadian.
Kalau saat matang n kurang, vonisnya tertulis "BELUM BISA DIUJI"; ambang tidak diturunkan.

Alat ini TIDAK mengubah `flow_gate.py` dan TIDAK mengirim order. Kalau hasilnya GAGAL, kalimat
"rem kami memperbaiki hasil" turun jadi klaim in-sample saja - dan itu akan ditulis di halaman 21
bukan dikubur.

Pakai:  python -X utf8 tools/gate_ab.py --lock
       python -X utf8 tools/gate_ab.py --status
       python -X utf8 tools/gate_ab.py            # vonis (menolak sebelum matang)
       python -X utf8 tools/gate_ab.py --self-test
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
import prices as PR  # noqa: E402

MIN = 60
WINS = 1500.0
H = 5
UMUR_JAM_MIN = 8
N_BOLEH_MIN = 40
N_VETO_MIN = 15
PLACEBO_DRAWS = 1000
LOCK = os.path.join(ROOT, "decisions", "prereg-gate-lock.json")

SPESIFIKASI = """E22 - rem diuji prospectif pada horison tempat kabar hidup.

populasi       : kejadian BELI dari ⑦ (k=tx/txc, b=true) dengan t > t_kunci; non-overlap 1 per 30 m
                 per token; harga masuk = `wp` terakhir dengan t_kejadian >= t
lengan         : BOLEH (flow_gate.state lulus) vs VETO (ditolak) - aturan ambang TIDAK diubah
outcome        : median `wp` pada t+[2m, 8m] minus harga masuk, minus ongkos round-trip terukur
winsor         : +/-1.500 bps pada mean (bukan 2.000 seperti E11 - dipilih sebelum lihat hasil);
                 median dilaporkan tanpa winsor
vonis_primer   : selisih = mean_winso(BOLEH) - mean_winso(VETO)
syarat_layak   : (1) n_boleh >= 40 DAN n_veto >= 15
                 (2) median(BOLEH) > 0 DAN CI bawah bootstrap 4000 (seed 20260929) dari selisih > 0
                 (3) Mann-Whitney satu arah BOLEH > VETO p < 0,05 DAN selisih > CI atas placebo
                     (penandaan ulang label, 1000 undian)
                 (4) P(ada harga keluar) >= 60 % pada KEDUA lengan DAN umur baris harga keluar
                     dilaporkan dalam menit, per lengan
umur_kunci     : 8 jam (disetujui sebelum ada angka; tenggat 30 Sep 16:59Z)
kalau_kecil    : 'BELUM BISA DIUJI' - ambang, winsor, dan umur tidak diubah setelah hasil dilihat
kalau_gagal    : klaim 'rem memperbaiki hasil' tetap in-sample; TIDAK dibalik menjadi
                 'VETO justru untung' tanpa kunci baru
jangan         : tidak mengubah flow_gate.py; tidak mengirim order; tidak mengutip OFI/buku order
                 (halaman itu punya kuncinya sendiri, E16)
"""


def w(x):
    return max(-WINS, min(WINS, x))


def iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def pasang_kunci():
    if os.path.exists(LOCK):
        d = json.load(io.open(LOCK, encoding="utf-8"))
        raise SystemExit("kunci sudah dipasang %s (%s) - dipasang ulang = hipotesis baru"
                         % (d.get("dibuat_utc"), d.get("spec_sha256")))
    t = int(time.time())
    out = {"dibuat_utc": iso(t), "t_kunci": t, "t_kunci_iso": iso(t),
           "umur_jam_min": UMUR_JAM_MIN, "horison_menit": H, "winsor_bps": WINS,
           "n_boleh_min": N_BOLEH_MIN, "n_veto_min": N_VETO_MIN,
           "spesifikasi": "vault/06-Results/25 - Rem, Terkunci Prospectif.md",
           "spek_teks": SPESIFIKASI,
           "spec_sha256": "0x" + hashlib.sha256(SPESIFIKASI.encode()).hexdigest()}
    json.dump(out, io.open(LOCK, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("kunci E22 dipasang %s | spec %s | vonis boleh dibaca mulai %s"
          % (out["dibuat_utc"], out["spec_sha256"][:18], iso(t + UMUR_JAM_MIN * 3600)))


def baca_kunci():
    if not os.path.exists(LOCK):
        raise SystemExit("tidak ada %s - aturan tanpa kunci adalah opini" % os.path.basename(LOCK))
    lk = json.load(io.open(LOCK, encoding="utf-8"))
    assert "0x" + hashlib.sha256(lk["spek_teks"].encode()).hexdigest() == lk["spec_sha256"], \
        "SPESIFIKASI DIUBAH SETELAH DIKUNCI"
    halaman = os.path.join(ROOT, *(lk["spesifikasi"].strip().lstrip("/")).split("/"))
    assert os.path.exists(halaman), "halaman spesifikasi hilang: %s" % lk["spesifikasi"]
    assert lk["spek_teks"].rstrip() in io.open(halaman, encoding="utf-8",
                                               errors="replace").read(), \
        "halaman spesifikasi tidak lagi memuat teks yang di-sha"
    return lk


def kejadian(t_kunci):
    """Kejadian BELI pasca-kunci + status gerbang + net@5m (semua aturan sama dengan E11/E13)."""
    txs = {}
    for ln in io.open(os.path.join(ROOT, "universe", "wallet-flow.jsonl"), encoding="utf-8",
                      errors="replace"):
        if not ln.startswith("{"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("k") not in ("tx", "txc") or not d.get("b"):
            continue
        tk, t, p = str(d.get("tk") or "").lower(), int(d.get("t") or 0), float(d.get("p") or 0)
        if tk and t and p > 0 and t > t_kunci:
            txs.setdefault(tk, []).append({"t": t, "p": p})
    seri = PR.load(os.path.join(ROOT, "universe", "watch-prices.jsonl"), "wp")["rows"]
    rt = costs.rt_cost()
    out, sensor = [], {"tanpa_wp": 0, "tanpa_keluar": 0, "tak_ada_data": 0, "pra_kunci": 0}
    for tk, rows in txs.items():
        s = seri.get(tk)
        if not s:
            sensor["tanpa_wp"] += len(rows)
            continue
        st = [x[0] for x in s]
        taken = -10 ** 15
        for r in sorted(rows, key=lambda x: x["t"]):
            t = r["t"]
            if t - taken < 30 * MIN:
                continue
            i = _bisect(st, t) - 1
            if i < 0 or s[i][1] <= 0:
                continue
            e = {"tk": tk, "t": t, "p0": s[i][1], "seri": s, "st": st}
            v = HD.net_pada(e, H, rt)
            if v is None:
                sensor["tanpa_keluar"] += 1
                continue
            umur = HD.umur_keluar(e, H)
            g = FG.state(tk, now=t)
            taken = t
            if g["status"] == "TAK ADA DATA":
                sensor["tak_ada_data"] += 1
                continue
            out.append({"tk": tk, "t": t, "status": g["status"], "net": v,
                        "umur_s": None if umur is None else umur,
                        "alasan": (g.get("alasan") or "")[:60]})
    return out, sensor, rt


def _bisect(st, t):
    lo, hi = 0, len(st)
    while lo < hi:
        mid = (lo + hi) // 2
        if st[mid] <= t:
            lo = mid + 1
        else:
            hi = mid
    return lo


def boot(xs, draws=4000, seed=20260929):
    rnd = random.Random(seed)
    n = len(xs)
    m = sorted(sum([xs[rnd.randrange(n)] for _ in range(n)]) / n for _ in range(draws))
    return m[int(0.025 * draws)], m[int(0.975 * draws)]


def boot_diff(a, b, draws=4000, seed=20260929):
    rnd = random.Random(seed)
    na, nb = len(a), len(b)
    m = sorted(sum([a[rnd.randrange(na)] for _ in range(na)]) / na -
               sum([b[rnd.randrange(nb)] for _ in range(nb)]) / nb for _ in range(draws))
    return m[int(0.025 * draws)], m[int(0.975 * draws)]


def vonis(rows, rnd):
    boleh = [w(r["net"]) for r in rows if r["status"] == "BOLEH"]
    veto = [w(r["net"]) for r in rows if r["status"] == "VETO"]
    if len(boleh) < N_BOLEH_MIN or len(veto) < N_VETO_MIN:
        return {"n_boleh": len(boleh), "n_veto": len(veto),
                "vonis": "BELUM BISA DIUJI", "layak": False,
                "sebab": "n lengan kurang (butuh BOLEH>=%d, VETO>=%d)" % (N_BOLEH_MIN,
                                                                          N_VETO_MIN)}
    selisih = sum(boleh) / len(boleh) - sum(veto) / len(veto)
    pool = boleh + veto
    nb = len(boleh)
    pl = []
    for _ in range(PLACEBO_DRAWS):
        idx = list(range(len(pool)))
        rnd.shuffle(idx)
        a = [pool[i] for i in idx[:nb]]
        b = [pool[i] for i in idx[nb:]]
        pl.append(sum(a) / len(a) - sum(b) / len(b))
    pl.sort()
    p_mw = FC.mann_whitney_p(boleh, veto)
    # CI-nya untuk SELISIH dua mean, dibootstrap terpisah per lengan - bukan boot dari satu lengan
    # lalu dikurangi sepihak, dan bukan zip posisional (dua lengan tidak punya pasangan satu-satu).
    lo_d, hi_d = boot_diff(boleh, veto)
    def cakupan(st):
        xs = [r for r in rows if r["status"] == st]
        ada = [r for r in xs if r["net"] is not None]
        um = [r["umur_s"] for r in ada if isinstance(r["umur_s"], (int, float))]
        return {"n": len(xs), "P_ada_harga_keluar": round(100.0 * len(ada) / max(1, len(xs)), 1),
                "umur_keluar_menit_median": (round(FC.med(um) / 60.0, 2) if um else None)}
    c_b, c_v = cakupan("BOLEH"), cakupan("VETO")
    syarat = {"1_n": True,
              "2_median_dan_ci": FC.med(boleh) > 0 and lo_d > 0,
              "3_arah_dua_kontrol": (p_mw is not None and p_mw < 0.05
                                    and selisih > pl[int(0.975 * PLACEBO_DRAWS)]),
              "4_cakupan_dan_umur": (c_b["P_ada_harga_keluar"] >= 60.0
                                    and c_v["P_ada_harga_keluar"] >= 60.0
                                    and c_b["umur_keluar_menit_median"] is not None
                                    and c_v["umur_keluar_menit_median"] is not None)}
    return {"n_boleh": len(boleh), "n_veto": len(veto),
            "mean_winso_boleh": round(sum(boleh) / len(boleh), 1),
            "mean_winso_veto": round(sum(veto) / len(veto), 1),
            "median_boleh": round(FC.med(boleh), 1), "median_veto": round(FC.med(veto), 1),
            "selisih_bps": round(selisih, 1), "ci_bawah_selisih_bps": round(lo_d, 1),
            "ci_atas_selisih_bps": round(hi_d, 1),
            "p_mw": None if p_mw is None else round(p_mw, 5),
            "placebo_ci_atas": round(pl[int(0.975 * PLACEBO_DRAWS)], 1),
            "lengkap_boleh": c_b, "lengkap_veto": c_v, "winsor_bps": WINS,
            "horison_menit": H, "syarat": syarat, "layak": all(syarat.values()),
            "vonis": ("LAYAK - rem memperbaiki hasil pada data yang belum terlihat"
                      if all(syarat.values()) else "GAGAL")}


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lock", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--tanpa-umur", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.lock:
        return pasang_kunci()
    lk = baca_kunci()
    jam = (time.time() - lk["t_kunci"]) / 3600.0
    rows, sensor, rt = kejadian(lk["t_kunci"])
    semua = len(rows)
    print("kunci %s | spec %s | umur %.2f/%d jam | arm BOLEH vs VETO di menit ke-%d | "
          "winsor %d bps" % (lk["dibuat_utc"], lk["spec_sha256"][:18], jam,
                             lk["umur_jam_min"], lk["horison_menit"], int(lk["winsor_bps"])))
    print("kejadian pasca-kunci: %d | sensor %s" % (semua, json.dumps(sensor, sort_keys=True)))
    if a.status:
        return
    if jam < lk["umur_jam_min"] and not a.tanpa_umur:
        print("\nBELUM SAH - kurang %.1f jam. Tidak ada angka yang dicetak sebagai vonis."
              % (lk["umur_jam_min"] - jam))
        return
    v = vonis(rows, random.Random(20260929))
    print("\n%s" % json.dumps(v, indent=1, sort_keys=True))
    if jam < lk["umur_jam_min"]:
        print("   ^^^ dicetak SEBELUM MATANG (%.2f/%d jam) - bacaan sementara, BUKAN vonis."
              % (jam, lk["umur_jam_min"]))
    out = {"dibuat_utc": iso(int(time.time())), "t_kunci_iso": lk["t_kunci_iso"],
           "umur_jam": round(jam, 2), "spec_sha256": lk["spec_sha256"], "kejadian": semua,
           "sensor": sensor, "ongkos_bps_rt": rt, "hasil": v}
    p = os.path.join(ROOT, "decisions", "gate-ab-%s.json"
                     % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("artefak: decisions/%s" % os.path.basename(p))
    print("VONIS: %s" % v["vonis"])


def self_test():
    """Vonis harus bisa GAGAL, dan placebo tidak boleh bisa menang saat label diacak."""
    rnd = random.Random(1)
    rows = [{"tk": "0xt", "t": 1000 + i * 60, "status": "BOLEH" if i % 2 == 0 else "VETO",
             "net": (120.0 if i % 2 == 0 else -120.0), "umur_s": 30} for i in range(80)]
    v = vonis(rows, rnd)
    assert v["layak"] and v["syarat"]["3_arah_dua_kontrol"], v
    assert v["n_boleh"] == 40 and v["n_veto"] == 40, v
    # n kurang -> BELUM BISA DIUJI, bukan GAGAL
    v2 = vonis(rows[:20], rnd)
    assert v2["vonis"] == "BELUM BISA DIUJI" and not v2["layak"], v2
    # label diacak total (semua net sama) -> syarat 2/3 harus jatuh
    datar = [dict(r, net=0.0) for r in rows]
    v3 = vonis(datar, rnd)
    assert not v3["layak"] and not v3["syarat"]["2_median_dan_ci"], v3
    # cakupan buruk (umur baris None) -> syarat 4 jatuh walau lainnya lolos
    tua = [dict(r, umur_s=None) for r in rows]
    v4 = vonis(tua, rnd)
    assert not v4["syarat"]["4_cakupan_dan_umur"], v4
    assert WINS == 1500.0 and UMUR_JAM_MIN == 8
    print("self-test E22 OK: LAYAK butuh 4 syarat; n kecil != gagal; data datar tidak LAYAK; "
          "umur baris hilang membatalkan syarat cakupan")


if __name__ == "__main__":
    utama()
