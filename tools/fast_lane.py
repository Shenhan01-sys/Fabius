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
import calendar
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

# `beli_baru()` berhenti memilih kandidat dari URUTAN BERKAS pada commit b990ab5
# (2026-09-29T18:22:56+07 = 11:22:56Z). Sebelum itu "12 teratas" = yang paling TUA di
# jendela, jadi `latensi_keputusan_detik` yang tercatat sebelum jam itu mengukur alat yang
# BERBEDA. Dua rejim tidak boleh digabung dalam satu median (F-D50/P50).
BATAS_REJIM = "2026-09-29T11:22:56Z"
REJIM_BARI = "terbaru-dulu"


def rejim(r):
    """Klasifikasi baris keputusan: mana yang dihasilkan pemilih terbaru-dulu, mana yang tidak."""
    if r.get("pemilih"):
        return str(r["pemilih"])
    return "urutan-berkas" if str(r.get("dibuat_utc") or "") < BATAS_REJIM else REJIM_BARI


def sah_arm(x, h):
    """Apakah arm pada horison `h` menit menilai SESUDAH kami memutuskan - bukan sebelumnya.

    Jendelanya `[t + h*60 - 180, t + h*60 + 180]` dengan `t` = waktu kejadian, sedangkan harga masuk
    kami adalah harga pada saat keputusan. Jadi arm hanya berarti sebagai "hasil dari masuk kami"
    kalau umur keputusan <= h*60 - 180. Baris lama (sebelum cap `sah` ada) dihitung dari
    `latensi_keputusan_detik` yang tercatat di barisnya sendiri - tidak ditebak.
    """
    a = x.get("keluar_%dm" % h) or {}
    if "sah" in a:
        return bool(a["sah"])
    lat = x.get("latensi_keputusan_detik")
    return True if lat is None else lat <= h * MIN - JENDELAPAS


def w(x):
    return max(-WINS, min(WINS, x))


def iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def epoch(s):
    """`2026-09-29T12:15:00Z` -> detik unix. Untuk baris lama yang belum punya cap `t_putus`."""
    try:
        return int(calendar.timegm(time.strptime(str(s), "%Y-%m-%dT%H:%M:%SZ")))
    except (TypeError, ValueError):
        return None


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
    """Baris beli ⑦ yang belum pernah disentuh, **diurut dari yang paling segar**.

    Versi pertama mengembalikan urutan berkas, dan karena satu muatan bisa berisi baris yang
    rentang umurnya lebar, "12 teratas dari urutan berkas" = systematically yang paling TUA di
    jendela. Itu yang membuat `latensi_keputusan_detik` terlihat 534-899 detik: sebagian bukan
    umur kabar saat tiba, tapi urutan pilihanku. Perbaikan ini juga membuat angka latensi yang
    tercatat selanjutnya berarti apa-apa (F-D50/P50).
    """
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


def nilai_arm(seri, t, p0, h, rt, t_putus=None):
    """Satu lengan pada horison `h` menit, diukur dari HARGA KEJADIAN `t`.

    _GUARD yang tidak boleh dihapus:_ jendela penilaian ada di `t + h m ± 3 m`. Kalau kami baru
    memutuskan SETELAH tepi awal jendela itu, angka yang keluar mengukur masa lalu - bukan hasil
    dari keputusan kami. Versi pertama alat ini tidak memeriksa itu, dan karena kandidatnya dipilih
    dari urutan berkas (umur kabar median 812 d), SEMUA lengan 5 m-nya (58 dari 58) ternyata
    mengukur sebelum kami masuk. Angka itu sudah telanjur dikutip; lihat F-D54.
    """
    if not seri or not p0:
        return None
    awal = t + (h * MIN - JENDELAPAS)
    js = [p for tt, p in seri if awal <= tt <= t + (h * MIN + JENDELAPAS)]
    ts = [tt for tt, p in seri if awal <= tt <= t + (h * MIN + JENDELAPAS)]
    if not js:
        return None
    sah = True if t_putus is None else (t_putus <= awal)
    return {"net_bps": round(10000.0 * (FC.med(js) - p0) / p0 - rt, 1),
            "umur_baris_detik": FC.med(ts) - (t + h * MIN),
            "sah": sah, "tepi_jendela_d": awal - t,
            "umur_keputusan_d": None if t_putus is None else t_putus - t}


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
        cepat = nilai_arm(seri, t, p0, ARM_CEPAT, rt,
                          t_putus=r.get("t_putus") or epoch(r.get("dibuat_utc")) or now)
        lambat = nilai_arm(seri, t, p0, ARM_LAMBAT, rt,
                           t_putus=r.get("t_putus") or epoch(r.get("dibuat_utc")) or now) \
            if now - t >= ARM_LAMBAT * MIN else None
        if cepat is None:
            baru = dict(r, status="TAK ADA DATA", dinilai_utc=iso(now), alasan="tidak ada baris "
                        "wp pada jendela %d m - ini BUKAN nol bps" % ARM_CEPAT)
        elif not cepat.get("sah"):
            baru = dict(r, status="DI LUAR JENDEL", dinilai_utc=iso(now),
                        alasan="kami memutuskan %d d sesudah kejadian, tapi jendela %d m mulai di "
                               "kejadian+%d d - arm ini mengukur MASA LALU, tidak dinilai (F-D54)"
                               % (cepat["umur_keputusan_d"], ARM_CEPAT, cepat["tepi_jendela_d"]))
        else:
            baru = dict(r, status="dinilai", dinilai_utc=iso(now), keluar_5m=cepat,
                        keluar_30m=lambat,
                        delta_cepat_kurang_lambat=(round(cepat["net_bps"] - lambat["net_bps"], 1)
                                                   if lambat else None))
        dinilai += 1
        rows.append(baru)

    # 2) buka baru
    tk_siklus = set()
    kandidat = beli_baru(now, cari_menit, sudah)
    for c in sorted(kandidat, key=lambda x: -x["t"])[:max(per_run * 4, 12)]:
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
                         "pemilih": REJIM_BARI,
                         "mode": "PAPER", "gerbang": "flow_gate ⑦ (satu arah)"})
            continue
        ent = wp_terakhir(wp.get(c["tk"]), now)
        if not ent or ent["px"] <= 0:
            tolak += 1
            rows.append({"slot_id": "N" + hashlib.sha256(c["kunci"].encode()).hexdigest()[:16],
                         "status": "TAK ADA DATA", "tk": c["tk"], "t_kejadian": c["t"],
                         "kunci": c["kunci"], "dibuat_utc": iso(now), "pemilih": REJIM_BARI,
                         "alasan": "ticker `wp` tidak punya baris <= sekarang untuk token ini",
                         "mode": "PAPER"})
            continue
        sid = hashlib.sha256(c["kunci"].encode()).hexdigest()[:16]
        dibuka += 1
        tk_siklus.add(c["tk"])
        rows.append({"slot_id": sid, "status": "terbuka", "mode": "PAPER", "label": "FAST-5m",
                     "tk": c["tk"], "simbol": c["simbol"], "t_kejadian": c["t"],
                     "kunci": c["kunci"], "dibuat_utc": iso(now), "t_putus": now,
                     "pemilih": REJIM_BARI,
                     "latensi_keputusan_detik": now - c["t"], "entry_px": ent["px"],
                     "umur_baris_entry_detik": ent["umur_detik"], "tx_p": c["tx_p"],
                     "usd": c["usd"], "gerbang": fg["status"],
                     "sha": "0x" + hashlib.sha256(json.dumps(
                         {"k": c["kunci"], "now": now}, sort_keys=True).encode()).hexdigest()[:16]})
    return rows, dibuka, dinilai, tolak


def laporan_terpasang(latest, urutan, rt):
    """Angka yang paling jujur dari jalur cepat: apa hasil masuk dengan umur kabar yang kami dapat.

    Dua saringan, keduanya dicetak sebagai hitungan (bukan dibuang diam-diam):
      (a) `sah` - jendela arm 5 m dimulai di kejadian+120 d; keputusan yang tiba sesudah itu
          mengukur MASA LALU, bukan hasil masuk kami. Ini yang membongkar F-D54: 58 dari 58
          lengan 5 m rejim lama tertolak oleh saringan ini.
      (b) rejim - sebelum b990ab5 kandidatnya diambil dari urutan berkas (yang tertua di jendela).
    Tanda-uji dan winsor seperti semua uji lain di repo ini.
    """
    semua = [latest[sid] for sid in urutan
             if latest[sid].get("status") == "dinilai"
             and isinstance(latest[sid].get("keluar_5m"), dict)
             and isinstance(latest[sid].get("keluar_30m"), dict)]

    tak_sah = [x for x in semua if not (sah_arm(x, ARM_CEPAT) and sah_arm(x, ARM_LAMBAT))]
    if tak_sah:
        print("   pairing: %d slot DIBUANG karena salah satu armnya menilai SEBELUM kami memutuskan "
              "(F-D54); %d tersisa" % (len(tak_sah), len(semua) - len(tak_sah)))
    ps = [x for x in semua if x not in tak_sah]
    seg = [x for x in ps if rejim(x) == REJIM_BARI]
    if not seg:
        print("   pairing REJIM SEGAR: 0 slot - belum ada posisi yang dibuka sesudah perbaikan "
              "urutan DAN berumur 30 m. Yang di bawah ini rejim LAMA (kandidat tertua di jendela), "
              "mengukur alat yang sudah tidak berjalan - BUKAN vonis alat sekarang.")
    else:
        dibuang = len(ps) - len(seg)
        if dibuang:
            print("   pairing: %d slot pasangan DIBUANG karena rejim lama (urutan berkas = kandidat "
                  "paling tua di jendela) - tidak sejawat dengan alat yang berjalan sekarang" % dibuang)
        ps = seg
    if not ps:
        print("   pairing: belum ada slot dengan DUA arm dinilai - ini BELUM BISA DIUJI")
        return None
    d = [x["keluar_5m"]["net_bps"] - x["keluar_30m"]["net_bps"] for x in ps]
    usia = sorted(x.get("latensi_keputusan_detik") or 0 for x in ps)
    lb = sum(1 for x in d if x > 1)
    kb = sum(1 for x in d if x < -1)
    p = FC.sign_p(lb, lb + kb) if lb + kb >= 5 else None
    r = {"n_terpasang": len(ps),
         "usia_kabar_median_d": int(FC.med(usia)),
         "usia_kabar_min_d": int(min(usia)), "usia_kabar_maks_d": int(max(usia)),
         "mean_5m": round(sum(w(x["keluar_5m"]["net_bps"]) for x in ps) / len(ps), 1),
         "mean_30m": round(sum(w(x["keluar_30m"]["net_bps"]) for x in ps) / len(ps), 1),
         "median_5m": round(FC.med([x["keluar_5m"]["net_bps"] for x in ps]), 1),
         "median_30m": round(FC.med([x["keluar_30m"]["net_bps"] for x in ps]), 1),
         "median_delta_5m_kurang_30m": round(FC.med(d), 1),
         "menang_5m": lb, "kalah_5m": kb, "p_tanda": None if p is None else round(p, 4),
         "P_ge_500_5m": round(100.0 * sum(1 for x in ps if x["keluar_5m"]["net_bps"] >= 500)
                              / len(ps), 1),
         "P_ge_500_30m": round(100.0 * sum(1 for x in ps if x["keluar_30m"]["net_bps"] >= 500)
                               / len(ps), 1)}
    print("   PAIRING pada posisi yang sama (n=%d, umur kabar median %d d):"
          % (r["n_terpasang"], r["usia_kabar_median_d"]))
    print("      5m : mean winso %+0.1f | median %+0.1f | P(>=+500) %0.1f %%"
          % (r["mean_5m"], r["median_5m"], r["P_ge_500_5m"]))
    print("      30m: mean winso %+0.1f | median %+0.1f | P(>=+500) %0.1f %%"
          % (r["mean_30m"], r["median_30m"], r["P_ge_500_30m"]))
    print("      delta 5m-30m median %+0.1f bps | menang %d / kalah %d | tanda-uji p=%s"
          % (r["median_delta_5m_kurang_30m"], r["menang_5m"], r["kalah_5m"],
             "-" if r["p_tanda"] is None else "%.4f" % r["p_tanda"]))
    if r["usia_kabar_median_d"] >= 3 * MIN:
        print("      baca: ini bukan 'strategi 5 menit kalah', ini apa yang tersisa dari bump E11")
        print("      SETELAH kabarnya menua %d menit (min %d, maks %d) - dan E11 sudah memprediksi"
              % (r["usia_kabar_median_d"] // 60, r["usia_kabar_min_d"] // 60,
                 r["usia_kabar_maks_d"] // 60))
        print("      `delay 5 m` -> mean@5m -166,4 bps; di sini kita masuk pada delay yang lebih besar.")
    else:
        print("      baca: kami masuk pada umur kabar median %d d - di DALAM jendela bump E11 "
              "(±2 m), jadi delta ini bukan lagi 'apa yang tersisa setelah kabarnya menua'."
              % r["usia_kabar_median_d"])
        print("      n=%d masih kecil, dan E11 sendiri tidak pernah lolos tanda-uji pada n=24."
              % r["n_terpasang"])
    return r


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
    # DUA REJIM dipisah, tidak digabung: sebelum b990ab5 kandidatnya dipilih dari urutan berkas
    # (= yang paling tua di jendela), sesudahnya dari yang paling segar. Satu median bersama akan
    # berbohong tentang alat yang berjalan SEKARANG (F-D50/P50).
    per = {}
    for r in buka + nilai + tolak + hili:
        x = r.get("latensi_keputusan_detik")
        if isinstance(x, int):
            per.setdefault(rejim(r), []).append(x)
    for nama in sorted(per):
        v = sorted(per[nama])
        keterangan = {"urutan-berkas": "TUA - alat lama; jangan dikutip sebagai keadaan sekarang",
                      REJIM_BARI: "SEGAR - alat yang berjalan sekarang"}.get(nama, "?")
        print("   umur kabar saat memutuskan [%s]: median %d d | p90 %d | max %d | n=%d | <180 d %d%%"
              % (nama, v[len(v) // 2], v[int(0.9 * (len(v) - 1))], v[-1], len(v),
                 100 * sum(1 for x in v if x < 180) // len(v)))
        print("      %s" % keterangan)
    tua, baru = sorted(per.get("urutan-berkas", [])), sorted(per.get(REJIM_BARI, []))
    if tua and baru:
        print("   PERBAIKAN TERUKUR: %d d -> %d d (%.0f%% lebih muda) pada alat yang sama, hanya "
              "karena urutan pilihannya dibetulkan - BUKAN karena sumbernya berubah"
              % (tua[len(tua) // 2], baru[len(baru) // 2],
                 100.0 * (1 - baru[len(baru) // 2] / float(tua[len(tua) // 2]))))
    # validitas lengan: jendela 5m mulai di kejadian+120 d, jadi ini bukan formalitas
    for h in (ARM_CEPAT, ARM_LAMBAT):
        key = "keluar_%dm" % h
        rek = [r for r in nilai if isinstance(r.get(key), dict)]
        byr = {}
        for r in rek:
            byr.setdefault(rejim(r), [0, 0])
            byr[rejim(r)][0 if sah_arm(r, h) else 1] += 1
        if rek:
            ringkas = " | ".join("%s: %d sah, %d mengukur MASA LALU" % (k, v[0], v[1])
                                 for k, v in sorted(byr.items()))
            print("   arm %2dm: %d tercatat -> %s" % (h, len(rek), ringkas))
    if nilai:
        print("      ambang sah: memutuskan <= %d d sesudah kejadian untuk 5m, <= %d d untuk 30m "
              "(jendela +-3 m di sekitar horison)" % (ARM_CEPAT * MIN - JENDELAPAS,
                                                      ARM_LAMBAT * MIN - JENDELAPAS))
    if lat:
        print("   latensi keputusan GABUNGAN DUA REJIM: median %d | p90 %d | max %d | n=%d "
              "- TIDAK BOLEH DIKUTIP; pakai angka per-rejim di atas"
              % (lat[len(lat) // 2], lat[int(0.9 * (len(lat) - 1))], lat[-1], len(lat)))
    if dl:
        c = [r["keluar_5m"]["net_bps"] for r in nilai if r.get("keluar_5m")]
        l = [r["keluar_30m"]["net_bps"] for r in nilai if r.get("keluar_30m")]
        cSah = [r["keluar_5m"]["net_bps"] for r in nilai if isinstance(r.get("keluar_5m"), dict)
                and sah_arm(r, ARM_CEPAT)]
        print("   PROSPEKTIF pada posisi yang sama: 5m mean winso %+0.1f (n=%d) | 30m mean winso "
              "%+0.1f (n=%d) | delta median %+0.1f"
              % (sum(w(x) for x in c) / max(1, len(c)), len(c), sum(w(x) for x in l) / max(1, len(l)),
                 len(l), FC.med(dl)))
        if cSah:
            print("      5m HANYA yang sah (memutuskan <= %d d): mean winso %+0.1f | median %+0.1f "
                  "| n=%d dari %d - sisanya mengukur masa lalu dan tidak boleh ikut rata-rata"
                  % (ARM_CEPAT * MIN - JENDELAPAS, sum(w(x) for x in cSah) / len(cSah),
                     FC.med(cSah), len(cSah), len(c)))
    if hili:
        print("   tanpa data: %d - ini KEHILANGAN, bukan hasil nol" % len(hili))
    rtp = laporan_terpasang(latest, urutan, rt)
    if tolak:
        alasan = {}
        for r in tolak:
            alasan[r.get("aksi_keputusan", "?")] = alasan.get(r.get("aksi_keputusan", "?"), 0) + 1
        print("   penolakan gerbang per status: %s" % json.dumps(alasan, sort_keys=True))
    return {"dinilai": len(nilai), "terbuka": len(buka), "ditolak": len(tolak),
            "tanpa_data": len(hili), "latensi_median_detik": lat[len(lat) // 2] if lat else None,
            "delta_median_bps": round(FC.med(dl), 1) if dl else None, "pairing_ci": rtp}


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
        # dua rejim harus terpisah: baris baru terbaca SEGAR, baris tanpa cap sebelum jam
        # perbaikan terbaca TUA, dan sesudahnya SEGAR (median gabungan = alat yang berbohong)
        assert rows[0]["pemilih"] == REJIM_BARI and rejim(rows[0]) == REJIM_BARI, rows[0]
        assert rejim({"dibuat_utc": "2026-09-29T08:11:42Z"}) == "urutan-berkas"
        assert rejim({"dibuat_utc": "2026-09-29T12:15:00Z"}) == REJIM_BARI
        # guard F-D54: arm yang jendelanya sudah lewat saat kami memutuskan TIDAK dianggap sah
        a = nilai_arm(seri["0xtok"], now - 60, 1.0, 5, 59.0, t_putus=now - 60 + 60)
        assert a["sah"] is True, a
        b = nilai_arm(seri["0xtok"], now - 60, 1.0, 5, 59.0, t_putus=now - 60 + 600)
        assert b["sah"] is False and b["umur_keputusan_d"] == 600, b
        assert sah_arm({"keluar_5m": b, "latensi_keputusan_detik": 600}, 5) is False
        assert sah_arm({"keluar_5m": {"net_bps": 1.0}, "latensi_keputusan_detik": 100}, 5) is True
        assert sah_arm({"keluar_5m": {"net_bps": 1.0}, "latensi_keputusan_detik": 534}, 5) is False
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
