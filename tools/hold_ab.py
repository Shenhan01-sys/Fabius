"""E12 - uji TERKUNCI bahwa "keluar cepat" adalah kebijakan, bukan kebetulan sampel.

Kenapa halaman ini ada (29 Sep 2026 ±08:10Z, setelah F-D41). E11 (`tools/horizon_decay.py`)
menemukan hal pertama yang positif dan lolos placebo di proyek ini: harapan +192,7 bps di menit ke-2
dan +202,6 di menit ke-5 setelah buy kerumunan pintar, lalu meluruh jadi **-182,5 di menit ke-30** -
dengan placebo asal-mula (jam digeser acak 30-90 menit) yang **datar di -180**. Itu temuan di data
SAMPAI `t_kunci` watch, dan temuan di dalam sampel bukan hasil. Kami sudah dibakar empat kali oleh
pola itu (F-D30 harga masuk beku, F-D32 control mempromosikan dirinya, F-D37 MW salah urut, F-D39
satu undian disebut hasil, F-D40 kontrol keluar yang salah), jadi yang dipasang sekarang adalah
kunci, bukan headline.

Yang diuji, dalam bentuk yang bisa dimenangkan atau dikalahkan:

    ARM KEBIJAKAN : keluar pada horison 5 menit
    ARM KONTROL   : horison 30 menit - pada POSISI YANG SAMA (bukan nol, bukan rata-rata sepanjang
                    masa: F-D16 melarang membandingkan dengan angka nol)
    delta         = net(5 m) - net(30 m), winsor +/-2.000 bps, ongkos 59 bps RT di kedua sisi

Vonis LAYAK hanya bila empat hal serentak (dan ini yang dikunci, bukan yang dinegosiasi nanti):
  (1) n >= 20 pasangan,
  (2) median delta > 0 DAN batas bawah CI bootstrap 4000 (seed 20260928) > 0,
  (3) tanda-uji eksak satu arah p < 0,05,
  (4) syarat baru F-D41: `P(ada harga keluar)` dan **umur baris harga keluar** dilaporkan untuk
      KEDUA horison - kalau kami tidak bisa menunjukkan bahwa "5 menit" benar-benar 5 menit,
      angkanya tidak masuk vault.

Data yang dihitung: HANYA kejadian dengan `t > t_kunci`. Kejadian sebelum kunci adalah bahan E11
dan tidak boleh dipakai ulang - itu persis cara pra-registrasi dibatalkan diam-diam.

Yang TIDAK dilakukan alat ini: tidak mengirim order; tidak mengklaim kami bisa menangkap bump itu.
E11 mengukur **informasi**; kemampuan mengeksekusi dalam jendela dua menit adalah P40, dan kalau
P40 gagal, vonis E12 tetap harus dibaca sebagai "kabar ada, kami tidak bisa datang tepat waktu".

Pakai:  python -X utf8 tools/hold_ab.py --lock      # pasang kunci (sekali, menolak dobel)
       python -X utf8 tools/hold_ab.py --status      # umur kunci + berapa pasangan yang sudah ada
       python -X utf8 tools/hold_ab.py              # vonis (menolak sebelum matang)
       python -X utf8 tools/hold_ab.py --self-test
"""
from __future__ import annotations

import argparse
import bisect
import calendar
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
import prices as PR  # noqa: E402

MIN = 60
WINS = 2000.0
FLOW = os.path.join(ROOT, "universe", "wallet-flow.jsonl")
WP = os.path.join(ROOT, "universe", "watch-prices.jsonl")
LOCK = os.path.join(ROOT, "decisions", "prereg-hold-lock.json")
UMUR_JAM_MIN = 12
N_MIN = 20
ARM_CEPAT = 5
ARM_LAMBAT = 30
JENDELAPAS = 3 * MIN

SPESIFIKASI = """E12 - uji terkunci 'keluar cepat' sebagai kebijakan.

arm_kebijakan : keluar pada horison 5 menit setelah kejadian beli kerumunan pintar
arm_kontrol   : horison 30 menit pada POSISI yang sama (bukan nol)
delta         : net(5m) - net(30m), winsor +/-2.000 bps, ongkos 59 bps RT di kedua sisi
harga_masuk   : `wp` terakhir dengan t <= t_kejadian (kanonis E7/E11); varian `tx.p` dilaporkan
                sebagai pemeriksaan, BUKAN sebagai lengan yang boleh dipilih setelah lihat hasil
harga_keluar  : median `wp` pada t+[H-3m, H+3m]; umur median itu dilaporkan apa adanya
perhitungan   : HANYA kejadian dengan t > t_kunci; non-overlap 1 per 30 m per token
vonis_layak   : (1) n >= 20 DAN (2) median > 0 DAN CI bawah bootstrap 4000 (seed 20260928) > 0
                DAN (3) tanda-uji eksak satu arah p < 0,05
                DAN (4) P(ada harga keluar) + umur baris harga keluar dilaporkan untuk dua arm
kalau_kecil   : tulis 'BELUM BISA DIUJI', jangan 'TIDAK ADA EFEK'; ambang tidak diturunkan
kalau_gagal   : horison pendek ditutup sebagai kebijakan; TIDAK dibalik jadi 'tahan lebih lama'
lapor_wajib   : n pasangan, token unik, median & mean winso delta, CI, p, umur harga tiap arm,
                P(ada harga keluar) tiap arm, selisih `wp` vs `tx.p`
eksekusi      : alat ini tidak mengirim order; klaim 'bisa diambil' butuh P40 (jalur < 2 menit)
"""


def w(x):
    return max(-WINS, min(WINS, x))


def iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def epoch(utc):
    # `calendar.timegm`, BUKAN `time.mktime` (jam lokal menggeser +7 jam - kelas kesalahan tercatat).
    return calendar.timegm(time.strptime(utc, "%Y-%m-%dT%H:%M:%SZ"))


def pasang_kunci():
    if os.path.exists(LOCK):
        d = json.load(io.open(LOCK, encoding="utf-8"))
        raise SystemExit("kunci sudah dipasang %s (spec %s) - dipasang ulang = spesifikasi baru, "
                         "dan itu halaman baru, bukan menimpa yang ini"
                         % (d.get("dibuat_utc"), d.get("spec_sha256")))
    t = int(time.time())
    out = {"dibuat_utc": iso(t), "t_kunci": t, "t_kunci_iso": iso(t),
           "umur_jam_min": UMUR_JAM_MIN, "n_min": N_MIN,
           "arm_kebijakan_menit": ARM_CEPAT, "arm_kontrol_menit": ARM_LAMBAT,
           "spesifikasi": "vault/06-Results/20 - Keluar Cepat, Terkunci.md",
           "spek_teks": SPESIFIKASI,
           "spec_sha256": "0x" + hashlib.sha256(SPESIFIKASI.encode()).hexdigest()}
    json.dump(out, io.open(LOCK, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("kunci E12 dipasang %s | spec %s | vonis boleh dibaca mulai %s"
          % (out["dibuat_utc"], out["spec_sha256"][:18], iso(t + UMUR_JAM_MIN * 3600)))


def baca_kunci():
    if not os.path.exists(LOCK):
        raise SystemExit("tidak ada %s - aturan tanpa kunci adalah opini" % os.path.basename(LOCK))
    lk = json.load(io.open(LOCK, encoding="utf-8"))
    assert "0x" + hashlib.sha256(lk["spek_teks"].encode()).hexdigest() == lk["spec_sha256"], \
        "SPESIFIKASI DIUBAH SETELAH DIKUNCI"
    halaman = os.path.join(ROOT, *(lk["spesifikasi"].strip().lstrip("/")).split("/"))
    if not os.path.exists(halaman):
        raise SystemExit("halaman spesifikasi %s TIDAK ADA - vonis tanpa dokumen yang bisa dibaca "
                         "orang lain bukan pra-registrasi" % lk["spesifikasi"])
    assert lk["spek_teks"].rstrip() in io.open(halaman, encoding="utf-8",
                                               errors="replace").read(), \
        "HALAMAN spesifikasinya tidak lagi memuat teks yang di-sha"
    return lk


def pasangan(t_kunci=None, flow=None, wp=None):
    """Satu baris per posisi: net cepat, net lambat, umur harga, sumber harga alternatif."""
    txs = {}
    for ln in io.open(flow or FLOW, encoding="utf-8", errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("k") not in ("tx", "txc") or not d.get("b"):
            continue
        tk, t, p = str(d.get("tk") or "").lower(), int(d.get("t") or 0), float(d.get("p") or 0)
        if tk and t and p > 0:
            txs.setdefault(tk, []).append((t, p))
    seri = wp if wp is not None else PR.load(WP, "wp")["rows"]
    rt = costs.rt_cost()
    out = {"n_kunci": 0, "tanpa_wp": 0, "keluar_bolong": 0, "n_usah": 0}
    ev = []
    for tk, rows in txs.items():
        s = seri.get(tk)
        if not s:
            out["tanpa_wp"] += len(rows)
            continue
        st = [x[0] for x in s]
        taken = -10 ** 15
        for t, txp in sorted(rows):
            if t - taken < ARM_LAMBAT * MIN:
                continue
            if t_kunci is not None and t <= t_kunci:
                out["n_kunci"] += 1
                continue
            i = bisect.bisect_right(st, t) - 1
            if i < 0:
                continue
            p0 = s[i][1]
            if p0 <= 0:
                continue
            taken = t
            out["n_usah"] += 1
            v = {}
            for h in (ARM_CEPAT, ARM_LAMBAT):
                a = bisect.bisect_left(st, t + (h * MIN - JENDELAPAS))
                b = bisect.bisect_right(st, t + (h * MIN + JENDELAPAS))
                if a >= b:
                    v[h] = None
                    continue
                px = FC.med([s[j][1] for j in range(a, b)])
                ts = [s[j][0] for j in range(a, b)]
                v[h] = {"net": round(10000.0 * (px - p0) / p0 - rt, 1),
                        "net_tx": round(10000.0 * (px - txp) / txp - rt, 1),
                        "umur_s": FC.med(ts) - (t + h * MIN)}
            if v[ARM_CEPAT] is None or v[ARM_LAMBAT] is None:
                out["keluar_bolong"] += 1
                continue
            ev.append({"tk": tk, "t": t, "cepat": v[ARM_CEPAT], "lambat": v[ARM_LAMBAT]})
    return ev, out


def vonis(ev, sens=None):
    dl = [w(p["cepat"]["net"] - p["lambat"]["net"]) for p in ev]
    if not dl:
        return {"n": 0, "layak": False, "vonis": "BELUM BISA DIUJI - tidak ada pasangan"}
    lebih = sum(1 for x in dl if x > 1)
    kalah = sum(1 for x in dl if x < -1)
    p = FC.sign_p(lebih, lebih + kalah)
    lo, hi = boot_ci(dl)
    med = FC.med(dl)
    c1 = len(dl) >= N_MIN
    c2 = med > 0 and lo > 0
    c3 = lebih + kalah >= 5 and p < 0.05
    c4 = (all(isinstance(x["umur_s"], (int, float)) for x in
              ([e["cepat"] for e in ev] + [e["lambat"] for e in ev]))
          and bool(sens) and "n_usah" in sens)
    return {"n": len(dl), "token_unik": len({e["tk"] for e in ev}),
            "median_delta_bps": round(med, 1),
            "mean_winso_delta": round(sum(dl) / len(dl), 1),
            "ci_bootstrap": [round(lo, 1), round(hi, 1)], "menang": lebih, "kalah": kalah,
            "p_tanda": round(p, 5),
            "umur_keluar_menit": {str(h): round(FC.med([e[k]["umur_s"] for e in ev]) / 60.0, 2)
                                  for h, k in ((ARM_CEPAT, "cepat"), (ARM_LAMBAT, "lambat"))},
            "P_ada_harga_keluar": (round(100.0 * len(ev) / (sens or {}).get("n_usah", len(ev)), 1)
                                   if sens else None),
            "net_cepat_mean": round(sum(w(e["cepat"]["net"]) for e in ev) / len(ev), 1),
            "net_lambat_mean": round(sum(w(e["lambat"]["net"]) for e in ev) / len(ev), 1),
            "net_cepat_dari_tx_mean": round(sum(w(e["cepat"]["net_tx"]) for e in ev) / len(ev), 1),
            "syarat": {"1_n": c1, "2_mediator_ci": c2, "3_tanda_uji": c3, "4_lapor_umur": c4},
            "layak": c1 and c2 and c3 and c4,
            "vonis": ("BELUM BISA DIUJI - n %d < %d" % (len(dl), N_MIN) if not c1
                      else ("LAYAK - keluar 5 m mengalahkan tahan 30 m pada posisi yang sama"
                            if (c1 and c2 and c3 and c4) else "GAGAL"))}


def boot_ci(xs, draws=4000, seed=20260928):
    rnd = random.Random(seed)
    n = len(xs)
    means = sorted(sum([xs[rnd.randrange(n)] for _ in range(n)]) / n for _ in range(draws))
    return means[int(0.025 * draws)], means[int(0.975 * draws)]


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
    semua, sens = pasangan(None)
    pasca, sens_p = pasangan(lk["t_kunci"])
    print("kunci %s | spec %s | umur %.2f jam dari kebutuhan %d | arm %d m vs %d m"
          % (lk["dibuat_utc"], lk["spec_sha256"][:18], jam, lk["umur_jam_min"],
             lk["arm_kebijakan_menit"], lk["arm_kontrol_menit"]))
    print("pasangan: semua=%d | PASCA-KUNCI=%d (hanya yang kanan ikut vonis) | sensor %s"
          % (len(semua), len(pasca), sens_p))
    if a.status:
        return
    if jam < lk["umur_jam_min"] and not a.tanpa_umur:
        print("\nBELUM SAH - kurang %.1f jam. Ketiadaan hasil bukan hasil: tidak ada angka yang "
              "dicetak sebagai vonis." % (lk["umur_jam_min"] - jam))
        return
    v = vonis(pasca, sens_p)
    print("\n%s" % json.dumps(v, indent=1, sort_keys=True))
    if jam < lk["umur_jam_min"]:
        print("   ^^^ semua angka dicetak SEBELUM MATANG (%.2f/%d jam) - bacaan sementara, BUKAN "
              "vonis." % (jam, lk["umur_jam_min"]))
    out = {"dibuat_utc": iso(int(time.time())), "t_kunci_iso": lk["t_kunci_iso"],
           "umur_jam": round(jam, 2), "spec_sha256": lk["spec_sha256"],
           "prefill_dibuang": len(semua) - len(pasca), "sensor": sens_p, "vonis": v}
    p = os.path.join(ROOT, "decisions", "hold-ab-%s.json"
                     % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("artefak: decisions/%s" % os.path.basename(p))


def self_test():
    """Vonis harus bisa kalah, dan kejadian sebelum kunci harus benar-benar dibuang."""
    now = 1_800_000_000
    seri = {"0xa": [(now - 5 * MIN, 1.0), (now + 2 * MIN, 1.02), (now + 6 * MIN, 1.02),
                    (now + 28 * MIN, 0.98), (now + 32 * MIN, 0.98)]}
    flow = "0xa\t%d\t1.0" % now
    import tempfile
    fd, fp = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    io.open(fp, "w", encoding="utf-8").write(
        json.dumps({"k": "tx", "b": True, "tk": "0xa", "t": now, "p": 1.0}) + "\n")
    try:
        ev, sens = pasangan(None, flow=fp, wp=seri)
        assert len(ev) == 1 and ev[0]["cepat"]["net"] > ev[0]["lambat"]["net"], ev
        # kejadian SEBELUM kunci -> dibuang, dan hitungannya harus bilang begitu
        ev2, sens2 = pasangan(now + 10, flow=fp, wp=seri)
        assert ev2 == [] and sens2["n_kunci"] == 1, (ev2, sens2)
        # kejadian SESUDAH kunci ikut dihitung
        ev3, _ = pasangan(now - 10, flow=fp, wp=seri)
        assert len(ev3) == 1, ev3
        v = vonis(ev3 * 25, {"n_usah": 25})
        assert v["layak"] and v["syarat"]["1_n"], v
        # posisi datar -> median nol, tidak boleh LAYAK
        datar = {"0xa": [(now - 5 * MIN, 1.0), (now + 2 * MIN, 1.0), (now + 6 * MIN, 1.0),
                         (now + 28 * MIN, 1.0), (now + 32 * MIN, 1.0)]}
        evd, sd = pasangan(None, flow=fp, wp=datar)
        vd = vonis(evd * 25, sd)
        assert not vd["layak"] and vd["median_delta_bps"] == 0.0, vd
        # horison pendek JELEK (turun cepat) -> GAGAL, dan tidak boleh dibaca terbalik
        buruk = {"0xa": [(now - 5 * MIN, 1.0), (now + 2 * MIN, 0.97), (now + 6 * MIN, 0.97),
                         (now + 28 * MIN, 0.99), (now + 32 * MIN, 0.99)]}
        evb, sb = pasangan(None, flow=fp, wp=buruk)
        vb = vonis(evb * 25, sb)
        assert not vb["layak"] and vb["vonis"] == "GAGAL" and vb["median_delta_bps"] < 0, vb
        assert "umur_keluar_menit" in vb and "P_ada_harga_keluar" in vb, vb
    finally:
        os.remove(fp)
    print("self-test E12 OK: prefill dibuang | posisi datar tidak LAYAK | arah buruk = GAGAL | "
          "syarat lapor umur ikut dinilai")


if __name__ == "__main__":
    utama()
