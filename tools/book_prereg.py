"""⑩ BUKU ORDER sebagai prediktor - terkunci SEBELUM historinya ada (E16).

Konteks (29 Sep 2026 ±09:2xZ): builder membawa teori dari seorang trader yang dia hormati -
"jumlahkan total variasi harga sisi beli, kurangi sisi jual; positif = pantul naik, negatif = turun".
Teori itu masuk akal, dan kami punya endpoint buku order (Aster `/fapi/v1/depth`, diverifikasi
hidup). Yang tidak kami punya: **riwayatnya**. Perekam `universe/record_book_depth.py` baru dipasang
29 Sep 09:1xZ, jadi satu-satunya yang boleh dikerjakan sekarang adalah menulis aturannya dengan
tegas lalu menjalankan jamnya - bukan menyesuaikan aturan nanti saat angkanya sudah kelihatan.

Yang bikin teori ini belum bisa dinyatakan sebagai satu hipotesis - dan itu ditemukan di snapshot
PERTAMA, sebelum ada satu pun uji prediktif:

    ETHUSDT  bi1 -0,651   bi20 +0,525      <- imbalance BERBALIK tanda tergantung kedalaman
    BTCUSDT  bi20 -0,010  util20 -0,707    <- dan tergantung pembobotan (kuantitas vs jarak)

Empat pembacaan dibarik di perekam (`bi1/bi5/bi20/mi20/util20`) karena "variasi harga" ambigu di
dalam teori aslinya. Kunci ini TIDAK memilih satu: ia mengikat (a) definisi yang diuji = `bi5`
sebagai hipotesis PRIMER (paling dekat dengan teks builder dan tidak menghukum likuiditas jauh),
(b) sisanya dilaporkan sebagai hipotesis SEKUNDER dengan koreksi multiple-testing Benjamini-Hochberg
alpha 0,10, dan (c) kalau pun `bi5` gagal sementara `util20` lolos, `util20` TIDAK boleh dijual
sebagai penemuan - dia jadi hipotesis baru yang butuh kunci berikutnya.

Horison dan timeframe - pertanyaan yang builder sendiri bilang bingung:
  * cadence kami = per siklus ⑦ (~200 detik), bukan streaming; jadi horizon prediksi terpendek yang
    JUJUR adalah 5 menit (3 snapshot), dan 15 menit (450 baris kline 15m) tidak bisa dibedakan dari
    noise pada cadence ini;
  * E11 mengukur kabar di ⑦ hidup ±2 menit - buku order di cadence 200 detik TIDAK akan pernah
    menangkap yang selama itu. Jadi yang diuji di sini adalah versi lambat dari teori itu, dan
    kalau versi lambungnya tidak predictive, kami belum membalikkan teorinya, cuma
    membalikkan pengukuran kami.

Vonis LAYAK (primer) hanya bila empat hal serentak:
  (1) n >= 40 pasangan (simbol, waktu) pasca-kunci,
  (2) median return-ahead > 0 DAN batas bawah CI bootstrap 4000 (seed 20260929) > 0,
  (3) Mann-Whitney satu arah kelompok-atas-vs-bawah `bi5` p < 0,05,
  (4) **ongkos nyata**: return dikurangi spread satu arah (dari `bookTicker`/bid-ask snapshot yang
      sama) masih > 0 - kalau edge-nya lebih kecil dari setengah spread, itu bukan edge, itu biaya.
Kalau n < 40 saat matang: "BELUM BISA DIUJI", ambang tidak diturunkan.

Pakai:  python -X utf8 tools/book_prereg.py --lock
       python -X utf8 tools/book_prereg.py --status
       python -X utf8 tools/book_prereg.py            # vonis (menolak sebelum matang)
       python -X utf8 tools/book_prereg.py --self-test
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
import flow_cluster_test as FC  # noqa: E402

BUKU = os.path.join(ROOT, "universe", "book-depth.jsonl")
LOCK = os.path.join(ROOT, "decisions", "prereg-book-lock.json")
UMUR_JAM_MIN = 12
N_MIN = 40
HORIZON_DTK = 300          # 5 menit = 3 snapshot pada cadence ⑦ (~200 s)
WINS = 1500.0
PRIMER = "bi5"
SEKUNDER = ["bi1", "bi20", "mi20", "util20"]

SPESIFIKASI = """E16 - buku order sebagai prediktor, terkunci sebelum historinya ada.

sumber_teori  : builder (29 Sep), dari trader yang dia hormati: 'total variasi harga beli - jual'
hipotesis_primer : kuantil-atas `bi5` (imbalance kuantitas 5 level) menghasilkan return-ahead
                   5 menit lebih tinggi dari kuantil-bawah, pada simbol yang sama
hipotesis_sekunder : bi1, bi20, mi20, util20 - masing-masing diuji, Benjamini-Hochberg alpha 0,10
return_ahead  : 10000 * (mid(t+300s) - mid(t)) / mid(t), mid dari snapshot berikutnya yang
                |t' - t - 300s| <= 150s; kalau tidak ada -> TIDAK DIHITUNG, bukan nol
biaya         : dikurangi setengah spread (bps) pada snapshot t - syarat (4) vonis adalah
                net-of-cost, bukan gross
perhitungan   : HANYA snapshot dengan detik > t_kunci; jangkar likuid (BTC/ETH/SOL) dilaporkan
                TERPISAH dari simbol kabar - menggabungkannya akan menyembunyikan bentuknya
vonis_layak   : (1) n >= 40 DAN (2) median > 0 DAN CI bawah bootstrap 4000 (seed 20260929) > 0
                DAN (3) Mann-Whitney satu arah atas-vs-bawah p < 0,05 DAN (4) mean net-of-cost > 0
kalau_kecil   : 'BELUM BISA DIUJI' - ambang tidak diturunkan, horison tidak diperpanjang diam-diam
kalau_gagal   : buku order ditutup sebagai jalur prediksi pada cadence kami; TIDAK dibalik
                jadi 'contra-imbalance' tanpa kunci baru
cadence_batas : ~200 s/simbol dari loop ⑦; E11 mengukur kabar hidup ±2 menit, jadi uji ini tidak
                bisa memalsukan versi CEPAT dari teori - hanya versi lambatnya
"""


def w(x):
    return max(-WINS, min(WINS, x))


def iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def pasang_kunci():
    if os.path.exists(LOCK):
        d = json.load(io.open(LOCK, encoding="utf-8"))
        raise SystemExit("kunci sudah dipasang %s (%s) - dipasang ulang = hipotesis baru, itu "
                         "halaman baru" % (d.get("dibuat_utc"), d.get("spec_sha256")))
    if not os.path.exists(BUKU):
        raise SystemExit("perekam ⑨ belum pernah jalan (%s belum ada) - pasang perekam dulu, "
                         "kunci tidak perlu data, tapi alatnya perlu tahu bedanya"
                         % os.path.basename(BUKU))
    t = int(time.time())
    out = {"dibuat_utc": iso(t), "t_kunci": t, "t_kunci_iso": iso(t), "umur_jam_min": UMUR_JAM_MIN,
           "n_min": N_MIN, "horizon_detik": HORIZON_DTK, "primer": PRIMER,
           "sekunder": SEKUNDER,
           "spesifikasi": "vault/06-Results/22 - Buku Order, Terkunci Lebih Dulu.md",
           "spek_teks": SPESIFIKASI,
           "spec_sha256": "0x" + hashlib.sha256(SPESIFIKASI.encode()).hexdigest()}
    json.dump(out, io.open(LOCK, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("kunci E16 dipasang %s | spec %s | vonis boleh dibaca mulai %s"
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


def muat(t_kunci=None):
    per = {}
    tolak = {"bdx": 0, "pra_kunci": 0, "tanpa_mid": 0}
    for ln in io.open(BUKU, encoding="utf-8", errors="replace"):
        if not ln.startswith("{"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("k") != "bd":
            tolak["bdx"] += 1
            continue
        if t_kunci is not None and int(d.get("detik") or 0) <= t_kunci:
            tolak["pra_kunci"] += 1
            continue
        if not isinstance(d.get("mid"), (int, float)) or d["mid"] <= 0:
            tolak["tanpa_mid"] += 1
            continue
        per.setdefault(d["sym"], []).append(d)
    for s in per:
        per[s].sort(key=lambda x: x["detik"])
    return per, tolak


def pasangan(per, horizon=HORIZON_DTK, tolerance=150):
    out = []
    for sym, rows in per.items():
        for i, r in enumerate(rows):
            tgt = r["detik"] + horizon
            j = min(range(len(rows)), key=lambda k: abs(rows[k]["detik"] - tgt))
            if abs(rows[j]["detik"] - tgt) > tolerance or j <= i:
                continue
            sp = r.get("spread_bps")
            out.append({"sym": sym, "detik": r["detik"],
                        "ret_bps": round(10000.0 * (rows[j]["mid"] - r["mid"]) / r["mid"], 2),
                        "ret_net": round(10000.0 * (rows[j]["mid"] - r["mid"]) / r["mid"]
                                         - (sp if isinstance(sp, (int, float)) else 0.0) / 2.0, 2),
                        "spread_bps": sp,
                        **{k: r.get(k) for k in (PRIMER,) + tuple(SEKUNDER)}})
    return out


def uji(ps, kunci):
    xs = [p for p in ps if isinstance(p.get(kunci), (int, float))]
    if len(xs) < N_MIN:
        return {"hipotesis": kunci, "n": len(xs), "status": "BELUM BISA DIUJI (n < %d)" % N_MIN}
    med = FC.med([p[kunci] for p in xs])
    atas = [p for p in xs if p[kunci] >= med]
    bawah = [p for p in xs if p[kunci] < med]
    if len(atas) < 10 or len(bawah) < 10:
        return {"hipotesis": kunci, "n": len(xs), "status": "PECAHAN KECIL"}
    ra = [w(p["ret_bps"]) for p in atas]
    rb = [w(p["ret_bps"]) for p in bawah]
    net = [w(p["ret_net"]) for p in atas]
    lo, hi = boot([w(p["ret_bps"]) for p in atas])
    p_mw = FC.mann_whitney_p(ra, rb)
    syarat = {"1_n": len(xs) >= N_MIN, "2_median_ci": FC.med(ra) > 0 and lo > 0,
              "3_mw": p_mw is not None and p_mw < 0.05,
              "4_net_of_cost": sum(net) / len(net) > 0}
    # TIDAK ada "median_selisih": kelompok atas/bawah tidak punya pasangan satu-satu, dan
    # memzip-nya secara posisional (yang saya lakukan di versi pertama) akan menghasilkan
    # "selisih" yang kelihatan rapi padahal isinya urutan array - persis kesalahan yang mencabut
    # E8 (F-D40). Yang dilaporkan: dua median, dua mean, dan Mann-Whitney atas distribusinya.
    return {"hipotesis": kunci, "n": len(xs), "n_atas": len(ra), "n_bawah": len(rb),
            "median_ret_atas": round(FC.med(ra), 2), "median_ret_bawah": round(FC.med(rb), 2),
            "mean_ret_atas": round(sum(ra) / len(ra), 2),
            "mean_net_atas": round(sum(net) / len(net), 2),
            "ci_atas": [round(lo, 2), round(hi, 2)],
            "p_mw": None if p_mw is None else round(p_mw, 5),
            "selisih_mean": round(sum(ra) / len(ra) - sum(rb) / len(rb), 2),
            "syarat": syarat, "layak": all(syarat.values())}


def boot(xs, draws=4000, seed=20260929):
    rnd = random.Random(seed)
    n = len(xs)
    m = sorted(sum([xs[rnd.randrange(n)] for _ in range(n)]) / n for _ in range(draws))
    return m[int(0.025 * draws)], m[int(0.975 * draws)]


def bh(res):
    ps = [r["p_mw"] for r in res if r.get("p_mw") is not None]
    if not ps:
        return "tidak ada p"
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    lulus, k = [], 0
    for rank, i in enumerate(order, 1):
        if ps[i] <= rank / len(ps) * 0.10:
            lulus.append(i)
            k = rank
    return {"alpha": 0.10, "lulus_rank": k, "yang_lulus": [res[i]["hipotesis"] for i in lulus]}


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
    semua, t1 = muat(None)
    pasca, t2 = muat(lk["t_kunci"])
    nsm = sum(len(v) for v in pasca.values())
    print("kunci %s | spec %s | umur %.2f/%d jam | horizon %d s"
          % (lk["dibuat_utc"], lk["spec_sha256"][:18], jam, lk["umur_jam_min"], lk["horizon_detik"]))
    print("snapshot: semua=%d di %d simbol | PASCA-KUNCI=%d di %d simbol | sensor %s"
          % (sum(len(v) for v in semua.values()), len(semua), nsm, len(pasca), t2))
    if a.status:
        return
    if jam < lk["umur_jam_min"] and not a.tanpa_umur:
        print("\nBELUM SAH - kurang %.1f jam. Tidak ada angka yang dicetak sebagai vonis."
              % (lk["umur_jam_min"] - jam))
        return
    ps = pasangan(pasca)
    # Komposisi dicetak SELALU, termasuk sebelum matang: jendela E16 tidak homogen karena daftar
    # pantau baru dibetulkan 09:5xZ (F-D47) - jadi "siapa yang diukur" bukan catatan kaki.
    dari = {}
    for p in ps:
        dari[p["sym"]] = dari.get(p["sym"], 0) + 1
    if dari:
        top = sorted(dari.items(), key=lambda kv: -kv[1])
        jangkar = sum(v for k, v in dari.items() if k in ("BTCUSDT", "ETHUSDT", "SOLUSDT",
                                                          "BNBUSDT"))
        print("   komposisi pasangan: %d simbol | teratas %s | share 4 jangkar likuid %0.0f %%"
              % (len(dari), ", ".join("%s=%d" % kv for kv in top[:5]),
                 100.0 * jangkar / len(ps)))
    res = [uji(ps, k) for k in (PRIMER,) + tuple(SEKUNDER)]
    for r in res:
        if r.get("status"):
            print("   %-8s %-12s %s" % (r["hipotesis"], "n=%d" % r["n"], r["status"]))
            continue
        print("   %-8s n=%4d | ret atas %+8.2f (net %+8.2f) | bawah %+8.2f | selisih %+8.2f "
              "| p=%-8s | layak %s %s" % (r["hipotesis"], r["n"], r["mean_ret_atas"],
                                          r["mean_net_atas"], r["median_ret_bawah"],
                                          r["selisih_mean"], r["p_mw"], r["layak"],
                                          json.dumps(r["syarat"], sort_keys=True)))
    print("\nBH sekunder: %s" % json.dumps(bh([r for r in res if r["hipotesis"] != PRIMER]),
                                          default=str, sort_keys=True))
    print("VONIS PRIMER (%s): %s" % (PRIMER, next((("LAYAK" if r["layak"] else "GAGAL")
                                                   for r in res if r["hipotesis"] == PRIMER
                                                   and not r.get("status")),
                                                   "BELUM BISA DIUJI")))
    out = {"dibuat_utc": iso(int(time.time())), "umur_jam": round(jam, 2), "spec_sha256":
           lk["spec_sha256"], "pasangan": len(ps), "hasil": res}
    p = os.path.join(ROOT, "decisions", "book-prereg-%s.json"
                     % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("artefak: decisions/%s" % os.path.basename(p))


def self_test():
    """Alatnya harus bisa bilang 'tidak tahu', dan harus menangkap edge yang memang ada."""
    global BUKU
    asli = BUKU
    import tempfile
    tmp_dir = tempfile.mkdtemp(prefix="e16-uji-")
    assert not os.path.abspath(tmp_dir).startswith(os.path.abspath(ROOT)), tmp_dir
    tmp = os.path.join(tmp_dir, "book.jsonl")
    BUKU = tmp
    assert BUKU != asli

    def baris(sym, d, mid, bi5, sp=4.0):
        return json.dumps({"k": "bd", "sym": sym, "detik": d, "mid": mid, "spread_bps": sp,
                           "bi1": bi5, "bi5": bi5, "bi20": bi5, "mi20": bi5, "util20": bi5},
                          sort_keys=True)
    rows = []
    mid = 100.0
    for i in range(120):
        # SATU deret per simbol, satu snapshot tiap 300 detik, dan mid berikutnya bergerak
        # searah imbalance snapshot ini. Percobaan pertama saya menulis baris "berpasangan"
        # (t dan t+300 untuk tiap i) sehingga baris t+300 ikut jadi prediktor dengan hasil
        # dari baris berikutnya - setengah pasangan jadi cross-baris dan edge-nya hilang.
        sign = 1.0 if i % 2 == 0 else -1.0
        rows.append(baris("S1", 1_000_000 + i * 300, mid, sign * 0.3))
        mid = mid * (1 + sign * 0.0005)
    rows.append('{"k":"bdx","sym":"S2","kode_http":429}')
    io.open(tmp, "w", encoding="utf-8", newline="\n").write("\n".join(rows) + "\n")
    try:
        per, sens = muat(None)
        assert sens["bdx"] == 1 and len(per["S1"]) == 120, (sens, len(per.get("S1", [])))
        ps = pasangan(per)
        assert len(ps) >= 55, len(ps)
        r = uji(ps, "bi5")
        assert r["layak"] and r["mean_ret_atas"] > 0 and r["median_ret_bawah"] < 0, r
        assert r["syarat"]["4_net_of_cost"], r
        # ambang umur: kunci di masa depan harus membuat status bilang belum sah, bukan nol angka
        assert UMUR_JAM_MIN == 12 and N_MIN == 40
        # hipotesis sekunder yang sama arahnya tidak boleh otomatis LAYAK tanpa n cukup
        kecil = uji(ps[:5], "bi5")
        assert kecil.get("status", "").startswith("BELUM BISA DIUJI"), kecil
    finally:
        BUKU = asli
        os.remove(tmp)
        os.rmdir(tmp_dir)
        assert os.path.exists(os.path.join(ROOT, "universe", "book-depth.jsonl")), \
            "berkas buku order yang ASLI hilang - ini yang terjadi di fast_lane (F-D42)"
    print("self-test E16 OK: edge buatan terdeteksi, baris gagal (bdx) tidak menyamar jadi nol, "
          "n kecil = BELUM BISA DIUJI")


if __name__ == "__main__":
    utama()
