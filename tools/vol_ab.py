"""E9 - A/B TERKUNCI dari kandidat masuk pertama Fabius: volatilitas rendah vs tinggi.

Kenapa halaman ini ada (29 Sep 2026, ±05:2xZ): sampai detik ini tidak ada satu pun fitur yang
melewati kontrolnya sendiri. `tools/topk_test.py` (E7, 10 fitur, harga ticker `wp`, kontrol = acak
SESAMA KANDIDAT dalam siklus 30 menit) menghasilkan SATU kandidat:

    vol_rendah   n=95  mean winso +132,9  (acak -134,3; CI atas acak +116,1)  -> DI ATAS ACAK
    sembilan fitur lain       -425,7 .. +107,1                              -> di bawah acak

Angka itu TIDAK boleh dijual, dan alasannya aritmatika, bukan selera: sepuluh fitur diuji
sekaligus, jadi peluang satu "menang" tanpa efek apa pun ≈ 10 x 0,025 = 0,25. Ini kandidat,
bukan hasil. Satu-satunya yang mengubah kandidat jadi hasil adalah data yang belum terjadi -
kunci ini dipasang sebelum data itu ada.

Yang diuji di sini BUKAN backtest-nya diulang, tapi aturannya dijalankan hidup: `tools/paper_book.py`
sekarang membuka DUA lengan pada jam yang sama dari feed yang sama dengan gerbang yang sama, dan
yang berbeda hanya peringkat volatilitas ticker `wp`-nya:

    lengan A `vol-rendah`  - separuh volatilitas TERENDAH dari kandidat yang layak hari itu
    lengan B `vol-tinggi`  - separuh VOLATILITAS TERTINGGI (inilah kontrolnya, bukan angka nol)

Aturan yang dikunci (lihat [[06-Results/18 - Kandidat Pertama, Diuji Hidup]]):
  vonis LAYAK hanya bila tiga-tiganya serentak:
    (1) n lengan A >= 20 posisi yang sudah dinilai (gerbang F-D16), DAN
    (2) median net_bps lengan A > 0 DAN batas bawah CI bootstrap 4000 (seed 20260928) > 0, DAN
    (3) Mann-Whitney satu arah A > B dengan p < 0,05.
  Kalau n < 20 pada saat matang: tulis "BELUM BISA DIUJI", jangan "TIDAK ADA EFEK", dan jangan
  turunkan ambangnya.
  Data yang dihitung: HANYA slot dengan open_utc > t_kunci. Slot sebelum kunci = prefill, dia
  tidak ikut vonis (kalau ikut, kita menguji aturan pada data yang sudah kita lihat).

Yang TIDAK diubah alat ini: tidak mengirim order, tidak menyentuh rantai, tidak menaikkan
`promote-after`. Dia hanya punya hak bicara atas pertanyaan "lengan mana yang layak jadi posisi
asli" - dan itu pun hanya setelah umurnya cukup.

Pakai:  python -X utf8 tools/vol_ab.py --lock            # pasang kunci (sekali, menolak dobel)
       python -X utf8 tools/vol_ab.py --status           # umur + berapa slot yang sudah ada
       python -X utf8 tools/vol_ab.py                    # jalankan vonis (menolak sebelum matang)
       python -X utf8 tools/vol_ab.py --self-test        # aturan diuji pada slot sintetis
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import io
import json
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import flow_cluster_test as FC  # noqa: E402

SLOT = os.path.join(ROOT, "decisions", "paper-book-positions.jsonl")
LOCK = os.path.join(ROOT, "decisions", "prereg-vol-lock.json")
UMUR_JAM_MIN = 12
N_MIN = 20
WINS = 2000.0
ARML = "vol-rendah"
ARMH = "vol-tinggi"

SPESIFIKASI = """E9 - A/B terkunci: lengan `vol-rendah` vs lengan `vol-tinggi` pada buku paper.

sumber_aturan : tools/topk_test.py E7 (10 fitur; hanya vol_rendah melewati acak-siklus)
lengan_A      : kebijakan == "vol-rendah" (separuh volatilitas wp terendah kandidat layak harian)
lengan_B      : kebijakan == "vol-tinggi" (kontrolnya, bukan nol)
harga_masuk   : seperti yang dicatat paper_book (tx.peristiwa + haircut dampak s/L)
hasil         : net_bps yang sudah dinilai paper_book (ongkos 59 bps RT sudah dipotong)
perhitungan   : HANYA slot dengan open_utc > t_kunci; slot sebelum kunci = prefill
vonis_layak   : (1) n_A >= 20 DAN (2) median_A > 0 DAN CI bawah bootstrap 4000 (seed 20260928) > 0
                DAN (3) Mann-Whitney satu arah A > B p < 0,05
kalau_kecil   : tulis "BELUM BISA DIUJI", jangan "TIDAK ADA EFEK"; ambang tidak diturunkan
lapor_wajib   : n tiap lengan, P(ada harga keluar), median, mean winso + CI, p MW, token unik
winso         : +/-2.000 bps pada mean (ekornya tebal di dua arah; median dilaporkan terpisah)
jangan        : tidak ada order, tidak ada rantai, tidak ada perubahan promote-after
"""


def w(x):
    return max(-WINS, min(WINS, x))


def iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def epoch(utc):
    # `calendar.timegm`, BUKAN `time.mktime`: mem-parse stempel UTC sebagai waktu lokal meleset
    # +7 jam di mesin ini (kelas kesalahan yang sudah tercatat di vault).
    return calendar.timegm(time.strptime(utc, "%Y-%m-%dT%H:%M:%SZ"))


def pasang_kunci():
    if os.path.exists(LOCK):
        d = json.load(io.open(LOCK, encoding="utf-8"))
        raise SystemExit("kunci sudah dipasang %s (spec %s) - dipasang ulang = spesifikasi baru = "
                         "hipotesis baru, dan itu halaman baru, bukan menimpa yang ini"
                         % (d.get("dibuat_utc"), d.get("spec_sha256")))
    t = int(time.time())
    out = {"dibuat_utc": iso(t), "t_kunci": t, "t_kunci_iso": iso(t),
           "umur_jam_min": UMUR_JAM_MIN, "n_min": N_MIN,
           "parameter_terkunci": {"vonis": "tiga syarat serentak (lihat spesifikasi)",
                                  "data": "HANYA open_utc > t_kunci",
                                  "kontrol": "lengan vol-tinggi pada jam/feed/gerbang yang sama"},
           "spesifikasi": "vault/06-Results/18 - Kandidat Pertama, Diuji Hidup.md",
           "spek_teks": SPESIFIKASI,
           "spec_sha256": "0x" + hashlib.sha256(SPESIFIKASI.encode()).hexdigest()}
    json.dump(out, io.open(LOCK, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("kunci E9 dipasang %s | spec %s | vonis boleh dibaca mulai %s"
          % (out["dibuat_utc"], out["spec_sha256"][:18], iso(t + UMUR_JAM_MIN * 3600)))


def baca_slot(lock=None):
    """Slot yang sudah DINILAI per lengan. `lock` diberikan -> hanya yang lahir sesudah kunci."""
    out = {ARML: [], ARMH: []}
    if not os.path.exists(SLOT):
        return out
    tk_kunci = lock["t_kunci"] if lock else None
    for ln in io.open(SLOT, encoding="utf-8", errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        kb = d.get("kebijakan")
        if kb not in out or d.get("status") != "dinilai":
            continue
        if isinstance(d.get("net_bps"), (int, float)) is False:
            continue
        if tk_kunci is not None:
            try:
                if epoch(d["open_utc"]) <= tk_kunci:
                    continue
            except (KeyError, ValueError):
                continue
        out[kb].append(d)
    return out


def arm_stats(slots):
    if not slots:
        return {"n": 0}
    xs = [s["net_bps"] for s in slots]
    ws = [w(x) for x in xs]
    lo, hi = boot_mean(ws)
    return {"n": len(xs), "token_unik": len({s.get("tk") for s in slots}),
            "median_bps": round(FC.med(xs), 1),
            "mean_winso_bps": round(sum(ws) / len(ws), 1),
            "ci_bootstrap": [round(lo, 1), round(hi, 1)],
            "p_ge_500": round(100.0 * sum(1 for x in xs if x >= 500) / len(xs), 1),
            "p_positif": round(100.0 * sum(1 for x in xs if x > 0) / len(xs), 1)}


def boot_mean(xs, draws=4000, seed=20260928):
    import random as _r
    rnd = _r.Random(seed)
    n = len(xs)
    means = sorted(sum([xs[rnd.randrange(n)] for _ in range(n)]) / n for _ in range(draws))
    return means[int(0.025 * draws)], means[int(0.975 * draws)]


def vonis(a, b):
    """Tiga syarat serentak. Kurang satu = BELUM LAYAK, dan alatnya mencetak syarat mana."""
    xsa = [s["net_bps"] for s in a]
    xsb = [s["net_bps"] for s in b]
    c1 = len(xsa) >= N_MIN
    lo, _ = boot_mean([w(x) for x in xsa]) if xsa else (0.0, 0.0)
    c2 = bool(xsa) and FC.med(xsa) > 0 and lo > 0
    # `mann_whitney_p` SATU ARAH dari pabriknya: a bergeser naik terhadap b; None kalau n < 5.
    p = FC.mann_whitney_p(xsa, xsb) if len(xsa) >= 5 and len(xsb) >= 5 else None
    c3 = (p is not None) and p < 0.05
    return {"syarat_1_n_cukup": c1, "syarat_2_median_di_atas_nol": c2,
            "syarat_3_melampaui_kontrol": c3,
            "p_mann_whitney_a_lewat_b": None if p is None else round(p, 4),
            "layak": c1 and c2 and c3,
            "fehlbar": ("BELUM BISA DIUJI - n lengan A %d < %d" % (len(xsa), N_MIN)
                        if not c1 else ("GAGAL" if not (c2 and c3) else "LAYAK"))}


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lock", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--tanpa-umur", action="store_true",
                    help="cetak angka sebelum matang dengan LABEL PERINGATAN (bukan vonis)")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.lock:
        return pasang_kunci()
    if not os.path.exists(LOCK):
        raise SystemExit("tidak ada %s - aturan tanpa kunci adalah opini" % os.path.basename(LOCK))
    lock = json.load(io.open(LOCK, encoding="utf-8"))
    assert "0x" + hashlib.sha256(lock["spek_teks"].encode()).hexdigest() == lock["spec_sha256"], \
        "SPESIFIKASI DIUBAH SETELAH DIKUNCI"
    # Kunci yang tidak dibaca orang lain cuma setengah gerbang: halaman spesifikasinya ikut
    # dicocokkan, supaya "menyunting halaman setelah hasil dilihat" tertolak oleh alat yang punya
    # hak vonis.
    halaman = os.path.join(ROOT, *(lock["spesifikasi"].strip().lstrip("/")).split("/"))
    if os.path.exists(halaman):
        teks = io.open(halaman, encoding="utf-8", errors="replace").read()
        assert lock["spek_teks"].rstrip() in teks, \
            "HALAMAN %s TIDAK LAGI memuat spec yang di-sha %s - jangan sunting setelah dilihat" % (
                os.path.basename(halaman), lock["spec_sha256"][:18])
    else:
        raise SystemExit("halaman spesifikasi %s TIDAK ADA - vonis tanpa dokumen yang bisa dibaca "
                         "orang lain bukan pra-registrasi, itu catatan pribadi"
                         % lock["spesifikasi"])
    semua = baca_slot(None)
    pasca = baca_slot(lock)
    jam = (time.time() - lock["t_kunci"]) / 3600.0
    print("kunci %s | spec %s | umur %.2f jam dari kebutuhan %d"
          % (lock["dibuat_utc"], lock["spec_sha256"][:18], jam, lock["umur_jam_min"]))
    print("slot: prefill A/B = %d/%d | PASCA-KUNCI A/B = %d/%d (hanya yang kanan ikut vonis)"
          % (len(semua[ARML]), len(semua[ARMH]), len(pasca[ARML]), len(pasca[ARMH])))
    if a.status:
        return
    if jam < lock["umur_jam_min"] and not a.tanpa_umur:
        print("\nBELUM SAH - kurang %.1f jam lagi. Ketiadaan hasil BUKAN hasil: tidak ada angka "
              "yang dicetak sebagai vonis, tidak ada klaim yang bergerak."
              % (lock["umur_jam_min"] - jam))
        return
    A, B = pasca_kunci(pasca, a)
    sa, sb = arm_stats(A), arm_stats(B)
    print("\n   %-12s %4s %-11s %11s %22s %9s %9s" % ("lengan", "n", "median", "mean winso",
                                                      "CI bootstrap", "P>=500", "positif"))
    for nm, s in ((ARML, sa), (ARMH, sb)):
        print("   %-12s %4d %+11s %+11s %-22s %8s%% %8s%%"
              % (nm, s.get("n", 0), "%0.1f" % s.get("median_bps", 0),
                 "%0.1f" % s.get("mean_winso_bps", 0),
                 "[%0.1f; %0.1f]" % (s["ci_bootstrap"][0], s["ci_bootstrap"][1]) if s.get("n") else
                 "-", s.get("p_ge_500", 0), s.get("p_positif", 0)))
    v = vonis(A, B)
    print("\nvonis E9: %s   (%s)" % (v["fehlbar"], json.dumps(
        {k: (round(x, 4) if isinstance(x, float) else x) for k, x in v.items() if
         k != "fehlbar"}, sort_keys=True)))
    if jam < lock["umur_jam_min"]:
        print("   ^^^ SEMUA ANGKA DI ATAS DICETAK SEBELUM MATANG (%.2f/%d jam) - bacaan sementara, "
              "BUKAN vonis." % (jam, lock["umur_jam_min"]))
    out = {"dibuat_utc": iso(int(time.time())), "t_kunci_iso": lock["t_kunci_iso"],
           "umur_jam": round(jam, 2), "spec_sha256": lock["spec_sha256"],
           "prefill": {"A": len(semua[ARML]) - len(pasca[ARML]),
                       "B": len(semua[ARMH]) - len(pasca[ARMH])},
           "lengan_A": sa, "lengan_B": sb, "vonis": v}
    p = os.path.join(ROOT, "decisions", "vol-ab-%s.json" % time.strftime("%Y%m%dT%H%M%SZ",
                                                                         time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("artefak: decisions/%s" % os.path.basename(p))


def pasca_kunci(pasca, a):
    return pasca[ARML], pasca[ARMH]


def self_test():
    """Yang diuji: vonis hanya bisa LAYAK kalau tiga-tiganya lulus, dan prefill tidak ikut."""
    tmp = os.path.join(ROOT, "decisions", "vol-ab-selftest.jsonl")
    global SLOT
    asli = SLOT
    now = int(time.time())
    kunci_t = now - 13 * 3600

    def slot(i, kb, net, t):
        return json.dumps({"slot_id": "st%02d" % i, "kebijakan": kb, "tk": "0xtok%d" % (i % 7),
                           "status": "dinilai", "net_bps": net,
                           "open_utc": iso(t)}, sort_keys=True)

    rows = []
    for i in range(25):
        rows.append(slot(i, ARML, 120.0 + i, kunci_t + 600 + i * 60))       # A pasca-kunci, positif
    for i in range(25):
        rows.append(slot(100 + i, ARMH, -300.0 - i, kunci_t + 600 + i * 60))  # B pasca, negatif
    for i in range(9):
        rows.append(slot(200 + i, ARML, 9000.0, kunci_t - 3600))            # PREFILL: harus dibuang
    io.open(tmp, "w", encoding="utf-8", newline="\n").write("\n".join(rows) + "\n")
    SLOT = tmp
    try:
        lk = {"t_kunci": kunci_t}
        got = baca_slot(lk)
        assert len(got[ARML]) == 25, "prefill ikut terhitung: %d" % len(got[ARML])
        assert len(got[ARMH]) == 25, got
        v = vonis(got[ARML], got[ARMH])
        assert v["layak"] and v["syarat_1_n_cukup"] and v["syarat_2_median_di_atas_nol"], v
        # A semua NEGATIF -> syarat 2 harus jatuh, dan vonis tidak boleh LAYAK
        got[ARML] = [dict(x, net_bps=-50.0) for x in got[ARML]]
        v2 = vonis(got[ARML], got[ARMH])
        assert not v2["syarat_2_median_di_atas_nol"] and not v2["layak"], v2
        # n kecil -> harus "BELUM BISA DIUJI", bukan "GAGAL"
        v3 = vonis(got[ARML][:3], got[ARMH][:3])
        assert v3["fehlbar"].startswith("BELUM BISA DIUJI"), v3
        # A == B -> MW tidak boleh menolong
        same = [dict(x, net_bps=10.0) for x in got[ARML]]
        v4 = vonis(same + [dict(x, net_bps=10.0) for x in same] * 2,
                   [dict(x, net_bps=10.0) for x in same] * 9)
        assert not v4["syarat_3_melampaui_kontrol"] and not v4["layak"], v4
        st = arm_stats(got[ARML])
        assert st["n"] == 25 and "ci_bootstrap" in st, st
    finally:
        SLOT = asli
        os.remove(tmp)
    print("self-test E9 OK: prefill dibuang | 3 syarat serentak | n kecil != gagal | A==B tidak "
          "pernah LAYAK")


if __name__ == "__main__":
    utama()
