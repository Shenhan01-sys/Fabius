"""JALUR CEPAT Fabius - membuka dan menilai posisi paper dalam hitungan menit, bukan jam.

Kenapa alat ini ada (29 Sep 2026, setelah F-D41). E11 (`tools/horizon_decay.py`) mengukur bahwa
harapan pasca-buy kerumunan pintar **hidup sekitar dua menit**: mean winso +192,7 bps di menit ke-2,
+202,6 di menit ke-5, lalu -182,5 di menit ke-30, dengan placebo asal-mula yang datar di -180.
E11 juga mengukur latensi DATA kami: median 0,2 menit dari kejadian ke baris yang sudah masuk git
(`_research/ukur_latensi_feed.py`, stempel commit GitHub). Jadi yang menahan agen bukan kabar -
yang menahan adalah **belum ada jalur dari kabar ke keputusan pada kecepatan kabar itu hidup**.

Alat ini memasang jalur itu dan sekaligus jadi alat ukurnya. Dia dijalankan DI dalam siklus rantai ⑦
(setelah perekam menulis, pada runner yang sama, atas berkas yang baru saja ditulis) sehingga
"berapa lama dari kejadian sampai kami memutuskan" terukur, bukan diklaim.

Yang dilakukan tiap siklus:
  1. kandidat = baris BELI ⑦ yang tiba dalam `--cari` menit terakhir, tanpa penyortiran by-fitur -
     urutan berkas, bukan urutan "fitur terbaik", karena tidak ada satu pun fitur yang lolos
     kontrolnya sendiri (E7/F-D39). Ini alat ukur, bukan strategi.
  2. gerbang ⑦ (`tools/flow_gate.py`, satu arah: hanya boleh menolak) menyaring - dan **penolakan
     ikut ditulis**, karena "kami menolak karena X pada jam Y" adalah bukti perilaku, bukan narasi.
  3. slot dibuka dengan harga masuk `wp` terakhir + **umur barisnya** (aturan F-D41: angka horison
     tanpa umur baris tidak boleh masuk vault).
  4. pada usia 5 dan 30 menit, kedua arm dinilai dari ticker yang sama, pada posisi yang sama,
     dan delta-nya dilaporkan - persis pasangan yang E12 kunci, tapi sekarang dengan
     `latensi_keputusan_detik` yang nyata.

Yang TIDAK dilakukannya: tidak mengirim order, tidak menyentuh kunci penandatangan, tidak menaikkan
`promote-after`. Semuanya PAPER dan berlabel - menutup posisi asli tetap lewat
`tools/execute_live.py --close --symbol`.

Pakai:  python -X utf8 tools/fast_lane.py --run             # satu siklus (dipakai workflow)
       python -X utf8 tools/fast_lane.py --report           # ringkasan seluruh riwayat
       python -X utf8 tools/fast_lane.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import costs  # noqa: E402
import flow_cluster_test as FC  # noqa: E402
import flow_gate as FG  # noqa: E402
import prices as PR  # noqa: E402

MIN = 60
WINS = 2000.0
FLOW = os.path.join(ROOT, "universe", "wallet-flow.jsonl")
LOG = os.path.join(ROOT, "decisions", "fast-lane.jsonl")
ARM_CEPAT = 5
ARM_LAMBAT = 30
JENDELAPAS = 3 * MIN


def w(x):
    return max(-WINS, min(WINS, x))


def iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def muat_log():
    """Baris TERAKHIR per slot_id (log append-only; penilaian menambah versi baru)."""
    latest, urutan = {}, []
    if os.path.exists(LOG):
        for ln in io.open(LOG, encoding="utf-8", errors="replace"):
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            try:
                d = json.loads(ln)
            except ValueError:
                continue
            sid = d.get("slot_id")
            if not sid:
                continue
            if sid not in latest:
                urutan.append(sid)
            latest[sid] = d
    return latest, urutan


def tulis(rows):
    with io.open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")


def beli_baru(now, cari_menit, sudah):
    """Baris beli ⑦ yang tiba dalam jendela cari, urut berkas, belum pernah disentuh."""
    out = []
    for ln in io.open(FLOW, encoding="utf-8", errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("k") not in ("tx", "txc") or not d.get("b"):
            continue
        t = int(d.get("t") or 0)
        tk = str(d.get("tk") or "").lower()
        if not tk or t < now - cari_menit * MIN or t > now:
            continue
        key = "%s|%s|%s" % (tk, t, str(d.get("h") or d.get("m") or ""))
        if key in sudah:
            continue
        out.append({"tk": tk, "t": t, "tx_p": float(d.get("p") or 0), "usd": float(d.get("u") or 0),
                    "maker": str(d.get("m") or "").lower(), "simbol": d.get("y"), "kunci": key})
    return out


def wp_terakhir(seri, t):
    """Harga + umur baris pada waktu `t` - umur dilaporkan, tidak disenyapkan (F-D41)."""
    if not seri:
        return None
    idx = [i for i, (tt, _) in enumerate(seri) if tt <= t]
    if not idx:
        return None
    i = idx[-1]
    return {"px": seri[i][1], "umur_detik": t - seri[i][0]}


def nilai_arm(seri, t, p0, h, rt):
    if not seri or not p0:
        return None
    js = [p for tt, p in seri if t + (h * MIN - JENDELAPAS) <= tt <= t + (h * MIN + JENDELAPAS)]
    ts = [tt for tt, p in seri if t + (h * MIN - JENDELAPAS) <= tt <= t + (h * MIN + JENDELAPAS)]
    if not js:
        return None
    return {"net_bps": round(10000.0 * (FC.med(js) - p0) / p0 - rt, 1),
            "umur_baris_detik": FC.med(ts) - (t + h * MIN)}


def jalankan(now, per_run, cari_menit, rt):
    latest, _ = muat_log()
    sudah = {r.get("kunci") for r in latest.values() if r.get("kunci")}
    wp = PR.load(os.path.join(ROOT, "universe", "watch-prices.jsonl"), "wp")["rows"]
    rows, dinilai, dibuka, tolak = [], 0, 0, 0

    # 1) penilaian dulu (slot yang umurnya sudah lewat) supaya delta tak tertunda satu siklus
    for sid, r in latest.items():
        if r.get("status") != "terbuka":
            continue
        t, p0 = int(r["t_kejadian"]), r.get("entry_px")
        seri = wp.get(r["tk"])
        if now - t < ARM_CEPAT * MIN:
            continue
        cepat = nilai_arm(seri, t, p0, ARM_CEPAT, rt)
        lambat = nilai_arm(seri, t, p0, ARM_LAMBAT, rt) if now - t >= ARM_LAMBAT * MIN else None
        if cepat is None:
            baru = dict(r, status="TAK ADA DATA", dinilai_utc=iso(now), alasan="tidak ada baris "
                        "wp pada jendela %d m - ini BUKAN nol bps" % ARM_CEPAT)
        else:
            baru = dict(r, status="dinilai", dinilai_utc=iso(now), keluar_5m=cepat,
                        keluar_30m=lambat,
                        delta_cepat_kurang_lambat=(round(cepat["net_bps"] - lambat["net_bps"], 1)
                                                   if lambat else None))
        dinilai += 1
        rows.append(baru)

    # 2) buka baru
    tk_siklus = set()
    for c in beli_baru(now, cari_menit, sudah)[:max(per_run * 4, 12)]:
        if dibuka >= per_run:
            break
        if c["tk"] in tk_siklus or now - c["t"] < 5:
            continue
        fg = FG.state(c["tk"], now=now)
        if fg["status"] != "BOLEH":
            tolak += 1
            rows.append({"slot_id": "T" + hashlib.sha256(c["kunci"].encode()).hexdigest()[:16],
                         "status": "DITOLAK", "aksi_keputusan": fg["status"],
                         "alasan": fg.get("alasan") or json.dumps(
                             {k: fg.get(k) for k in ("maker_jual", "jual_ada", "usd_jual")}),
                         "tk": c["tk"], "t_kejadian": c["t"], "kunci": c["kunci"],
                         "dibuat_utc": iso(now), "latensi_keputusan_detik": now - c["t"],
                         "mode": "PAPER", "gerbang": "flow_gate ⑦ (satu arah)"})
            continue
        ent = wp_terakhir(wp.get(c["tk"]), now)
        if not ent or ent["px"] <= 0:
            tolak += 1
            rows.append({"slot_id": "N" + hashlib.sha256(c["kunci"].encode()).hexdigest()[:16],
                         "status": "TAK ADA DATA", "tk": c["tk"], "t_kejadian": c["t"],
                         "kunci": c["kunci"], "dibuat_utc": iso(now),
                         "alasan": "ticker `wp` tidak punya baris <= sekarang untuk token ini",
                         "mode": "PAPER"})
            continue
        sid = hashlib.sha256(c["kunci"].encode()).hexdigest()[:16]
        dibuka += 1
        tk_siklus.add(c["tk"])
        rows.append({"slot_id": sid, "status": "terbuka", "mode": "PAPER", "label": "FAST-5m",
                     "tk": c["tk"], "simbol": c["simbol"], "t_kejadian": c["t"],
                     "kunci": c["kunci"], "dibuat_utc": iso(now),
                     "latensi_keputusan_detik": now - c["t"], "entry_px": ent["px"],
                     "umur_baris_entry_detik": ent["umur_detik"], "tx_p": c["tx_p"],
                     "usd": c["usd"], "gerbang": fg["status"],
                     "sha": "0x" + hashlib.sha256(json.dumps(
                         {"k": c["kunci"], "now": now}, sort_keys=True).encode()).hexdigest()[:16]})
    return rows, dibuka, dinilai, tolak


def report(rt):
    latest, urutan = muat_log()
    buka = [latest[s] for s in urutan if latest[s].get("status") == "terbuka"]
    nilai = [latest[s] for s in urutan if latest[s].get("status") == "dinilai"]
    tolak = [latest[s] for s in urutan if latest[s].get("status") == "DITOLAK"]
    hili = [latest[s] for s in urutan if latest[s].get("status") == "TAK ADA DATA"]
    lat = sorted(r["latensi_keputusan_detik"] for r in buka + nilai + tolak
                 if isinstance(r.get("latensi_keputusan_detik"), int))
    dl = [r["delta_cepat_kurang_lambat"] for r in nilai
          if isinstance(r.get("delta_cepat_kurang_lambat"), (int, float))]
    print("FAST-LANE | slot: %d dinilai, %d terbuka, %d ditolak gerbang, %d tanpa data"
          % (len(nilai), len(buka), len(tolak), len(hili)))
    if lat:
        print("   latensi keputusan (detik dari kejadian -> kami memutuskan): median %d | p90 %d | "
              "max %d | n=%d" % (lat[len(lat) // 2], lat[int(0.9 * (len(lat) - 1))], lat[-1],
                                 len(lat)))
    if dl:
        c = [r["keluar_5m"]["net_bps"] for r in nilai if r.get("keluar_5m")]
        l = [r["keluar_30m"]["net_bps"] for r in nilai if r.get("keluar_30m")]
        print("   PROSPEKTIF pada posisi yang sama: 5m mean winso %+0.1f (n=%d) | 30m mean winso "
              "%+0.1f (n=%d) | delta median %+0.1f"
              % (sum(w(x) for x in c) / max(1, len(c)), len(c), sum(w(x) for x in l) / max(1, len(l)),
                 len(l), FC.med(dl)))
    if hili:
        print("   tanpa data: %d - ini KEHILANGAN, bukan hasil nol" % len(hili))
    if tolak:
        alasan = {}
        for r in tolak:
            alasan[r.get("aksi_keputusan", "?")] = alasan.get(r.get("aksi_keputusan", "?"), 0) + 1
        print("   penolakan gerbang per status: %s" % json.dumps(alasan, sort_keys=True))
    return {"dinilai": len(nilai), "terbuka": len(buka), "ditolak": len(tolak),
            "tanpa_data": len(hili), "latensi_median_detik": lat[len(lat) // 2] if lat else None,
            "delta_median_bps": round(FC.med(dl), 1) if dl else None}


def self_test():
    """Yang diuji: latensi tercatat, penolakan tercatat, dua arm dinilai berpasangan.

   _GUARD yang tidak boleh dihapus:_ berkas uji harus berada DI LUAR `ROOT` dan path-nya harus
    benar-benar beda dari berkas nyata. Versi pertama test ini memakai `tempfile.mkstemp()` tanpa
    guard dan memulihkan global SEBELUM `os.remove` - akibatnya `os.remove(FLOW)` menunjuk
    `universe/wallet-flow.jsonl` dan **menghapus berkas data riwayat** (29 Sep 08:2xZ; selamat hanya
    karena git menyimpannya: `git checkout -- universe/wallet-flow.jsonl`, 115.487 baris). Alat yang
    menguji dirinya sendiri tidak boleh punya jalan untuk menyentuh keadaan asli.
    """
    global FLOW, LOG
    fflow, flog = FLOW, LOG
    tmp = tempfile.mkdtemp(prefix="fastlane-uji-")
    assert not os.path.abspath(tmp).startswith(os.path.abspath(ROOT)), tmp
    FLOW = os.path.join(tmp, "flow.jsonl")
    LOG = os.path.join(tmp, "log.jsonl")
    assert FLOW != fflow and LOG != flog
    now = 1_800_000_000
    io.open(FLOW, "w", encoding="utf-8").write(
        json.dumps({"k": "tx", "b": True, "tk": "0xtok", "t": now - 60, "p": 1.0, "u": 500.0,
                    "m": "0xm", "y": "TOK", "h": "0xh1"}) + "\n")
    seri = {"0xtok": [(now - 5 * MIN, 1.0), (now + 4 * MIN, 1.05), (now + 6 * MIN, 1.05),
                      (now + 29 * MIN, 0.97), (now + 31 * MIN, 0.97)]}
    old_state, old_load = FG.state, PR.load
    FG.state = lambda a, now=None, **k: {"status": "BOLEH", "alasan": None}
    PR.load = lambda *a, **k: {"rows": seri}
    try:
        rows, dib, nil, tol = jalankan(now, 3, 15, 59.0)
        assert dib == 1 and rows[0]["status"] == "terbuka", rows
        assert rows[0]["latensi_keputusan_detik"] == 60, rows[0]
        assert rows[0]["umur_baris_entry_detik"] == 5 * MIN, rows[0]
        tulis(rows)
        # siklus berikutnya: slot dinilai (5m lewat, 30m belum) -> delta masih None
        rows2, _, nil2, _ = jalankan(now + 6 * MIN, 3, 15, 59.0)
        assert nil2 == 1 and rows2[0]["status"] == "dinilai", rows2
        assert rows2[0]["keluar_30m"] is None and rows2[0]["delta_cepat_kurang_lambat"] is None
        # setelah 30 m: dua arm terisi dan delta berpasangan ada
        rows3, _, nil3, _ = jalankan(now + 31 * MIN, 3, 15, 59.0)
        assert nil3 == 1 and rows3[0]["delta_cepat_kurang_lambat"] is not None, rows3
        assert rows3[0]["keluar_5m"]["net_bps"] > 0 > rows3[0]["keluar_30m"]["net_bps"], rows3
        assert isinstance(rows3[0]["keluar_5m"]["umur_baris_detik"], (int, float))
        # gerbang menolak -> tertulis sebagai DITOLAK, bukan hilang diam-diam
        FG.state = lambda a, now=None, **k: {"status": "VETO", "alasan": "kerumunan jual"}
        io.open(FLOW, "w", encoding="utf-8").write(
            json.dumps({"k": "tx", "b": True, "tk": "0xtok2", "t": now - 30, "p": 1.0, "u": 500.0,
                        "m": "0xm", "y": "T2", "h": "0xh2"}) + "\n")
        rows4, dib4, _, tol4 = jalankan(now, 3, 15, 59.0)
        assert dib4 == 0 and tol4 == 1 and rows4[0]["status"] == "DITOLAK", rows4
        assert rows4[0]["alasan"] == "kerumunan jual"
        # tidak ada baris wp -> TAK ADA DATA, BUKAN 0 bps
        FG.state = lambda a, now=None, **k: {"status": "BOLEH", "alasan": None}
        PR.load = lambda *a, **k: {"rows": {}}
        io.open(FLOW, "w", encoding="utf-8").write(
            json.dumps({"k": "tx", "b": True, "tk": "0xtok3", "t": now - 30, "p": 1.0, "u": 9.0,
                        "m": "0xm", "y": "T3", "h": "0xh3"}) + "\n")
        rows5, dib5, _, tol5 = jalankan(now, 3, 15, 59.0)
        assert dib5 == 0 and tol5 == 1 and rows5[0]["status"] == "TAK ADA DATA", rows5
        rep = report(59.0)
        assert set(("dinilai", "ditolak", "tanpa_data")) <= set(rep), rep
    finally:
        FLOW_, LOG_ = FLOW, LOG
        FG.state, PR.load = old_state, old_load
        FLOW, LOG = fflow, flog
        for p in (FLOW_, LOG_):
            if os.path.exists(p):
                os.remove(p)
        if os.path.isdir(tmp):
            os.rmdir(tmp)
        assert FLOW == fflow and LOG == flog, "global tidak kembali - berkas nyata dalam bahaya"
        assert os.path.exists(fflow), "berkas aliran asli HILANG saat self-test: %s" % fflow
    print("self-test jalur cepat OK: latensi tercatat | dua arm berpasangan | VETO tertulis | "
          "tanpa data != nol")



def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--per-run", type=int, default=3)
    ap.add_argument("--cari", type=int, default=15)
    ap.add_argument("--now", type=int, default=None)
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    rt = costs.rt_cost()
    now = a.now or int(time.time())
    if a.report:
        report(rt)
        return
    if not a.run:
        raise SystemExit("pilih --run, --report, atau --self-test")
    rows, dibuka, dinilai, tolak = jalankan(now, a.per_run, a.cari, rt)
    tulis(rows)
    print("FAST-LANE %s | dibuka %d | dinilai %d | ditolak/tanpa-data %d | ongkos %.1f bps RT"
          % (iso(now), dibuka, dinilai, tolak, rt))
    for r in rows:
        print("   %-8s %-10s %s" % (r["slot_id"][:8], r["tk"][:10],
                                    "%s lat=%ss %s" % (r["status"],
                                                       r.get("latensi_keputusan_detik"),
                                                       json.dumps({k: r[k] for k in
                                                                   ("keluar_5m", "delta_cepat_kurang_lambat",
                                                                    "alasan") if k in r},
                                                                  ensure_ascii=False)[:110])))
    print("riwayat append-only: decisions/%s (slot yang sama bertambah versinya saat dinilai)"
          % os.path.basename(LOG))


if __name__ == "__main__":
    utama()
