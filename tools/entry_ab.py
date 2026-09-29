"""E24 - apakah masuk yang kami pilih mengalahkan masuk ACAK pada siklus yang sama?

F-D54 memberi angka pertama yang sah untuk titik masuk kami: 25 lengan 5m, mean winso
**-519,4 bps**, umur keputusan median 58 d. Angka itu jujur, tapi ia belum menjawab pertanyaan
yang sebenarnya, karena tidak ada pembanding. Di repo ini pembandingnya bukan nol (F-D8): yang
harus dikalahkan adalah **kontrol acak dari kolam yang sama pada siklus yang sama** - kalau
kontrol acak juga memberi -520, maka "kami kalah" bukan tentang seleksi, itu tentangsubstratnya.

`tools/fast_lane.py` mulai mencatat lengan kontrol itu (label `ACAK-5m`, dipilih seragam dengan
benih = waktu siklus, gerbang TIDAK dilihat). Halaman ini menguncinya SEBELUM ada satu pun
pasangan kontrol dinilai, dan menolak memvonis sebelum jamnya.

Pakai:  python -X utf8 tools/entry_ab.py --lock       # pasang kunci (sekali, spec di-sha)
         python -X utf8 tools/entry_ab.py --status     # apa yang terlihat sekarang (bukan vonis)
         python -X utf8 tools/entry_ab.py             # vonis - menolak sebelum matang
         python -X utf8 tools/entry_ab.py --self-test

Yang TIDAK dilakukan alat ini: mengirim order, mengubah ambang gerbang, atau menulis apa pun ke
buku paper. Dia hanya membaca `decisions/fast-lane.jsonl`.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import flow_cluster_test as FC  # noqa: E402
import fast_lane as FL  # noqa: E402

LOG = os.path.join(ROOT, "decisions", "fast-lane.jsonl")
# BUKAN `prereg-entry-lock.json` - itu kunci E1/E2/E3 (`tools/entry_lab.py`, dipasang 28 Sep
# 11:32:07Z), dan menimpanya berarti menghapus ujian yang sudah berjalan. E24 punya kunci
# sendiri: satu ujian = satu berkas = satu sha.
LOCK = os.path.join(ROOT, "decisions", "prereg-fastlane-lock.json")
H = 5                      # horison lengan yang dinilai (menit)
WINS = 1500.0              # dipilih SEBELUM hasil; lebih ketat dari E11 (2.000) dan sama dengan E22
UMUR_JAM_MIN = 8           # syarat maturitas kunci
SEED = 20260929
N_MIN = 40                 # per lengan - bukan 20: di sini dua lengan, dan kami tidak mau undian

SPEC = """E24 - masuk terpilih vs masuk acak pada horison tempat kabar masih hidup.

populasi       : baris keputusan tools/fast_lane.py dengan dibuat_utc > t_kunci; lengan yang
                 dinilai hanya yang SAH (umur keputusan <= %d d; jendela %dm mulai di
                 kejadian+%d d - F-D54), status dinilai, dan punya keluar_%dm
lengan T       : yang dibuka setelah gerbang ⑦ BOLEH (label FAST-5m, kontrol != True)
lengan K       :kontrol acak siklus yang sama (label ACAK-5m, kontrol == True) - gerbang tidak
                 dilihat; satu kontrol per siklus; benih pengambilannya waktu siklus
outcome        : net_bps dari harga ticker `wp` saat keputusan ke median `wp` pada
                 kejadian+%dm +-3 m, dikurangi ongkos round-trip terukur 59 bps
winsor         : +/-%.0f bps pada mean; median dilaporkan tanpa winsor
vonis_primer   : selisih = mean_winso(T) - mean_winso(K)
syarat_layak   : (1) n_T >= %d DAN n_K >= %d
                 (2) median(T) > 0 DAN CI bawah bootstrap %d (seed %d) dari selisih > 0
                 (3) Mann-Whitney satu arah T > K dengan p < 0,05
                 (4) komposisi kedua lengan dicetak: token berbeda, median umur keputusan,
                     median umur baris harga masuk - kalau T dan K tidak sebanding pada
                     ketiganya, vonisnya BELUM BISA DIUJI
kalau_gagal    : T tidak lebih baik dari K berarti seleksi kami tidak menambah apa pun di atas
                 "masuk acak pada menit pertama setelah whale beli"; angka T yang NEGATIF dan
                 K yang NEGATIF berarti substratnya yang buruk, bukan penilaiannya - dan itu
                 TIDAK boleh dibaca sebagai "fade saja", arah dibalik butuh kunci baru
""" % (H * 60 - FL.JENDELAPAS, H, H * 60 - FL.JENDELAPAS, H, H, WINS, N_MIN, N_MIN, 4000, SEED)


def w(x):
    return max(-WINS, min(WINS, x))


def iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def sha_spec():
    return "0x" + hashlib.sha256(SPEC.encode("utf-8")).hexdigest()


def pasang_kunci(now):
    if os.path.exists(LOCK):
        lama = json.load(io.open(LOCK, encoding="utf-8"))
        if lama.get("spec_sha256") != sha_spec():
            raise SystemExit("KUNCI SUDAH ADA dengan spec BERBEDA di %s (sha %s) - tidak ditimpa, "
                             "tidak dibaca sebagai E24. Buka nama kunci baru untuk ujian baru."
                             % (os.path.relpath(LOCK, ROOT), str(lama.get("spec_sha256"))[:18]))
        print("kunci sudah ada:", lama.get("t_kunci"), "| sha", lama["spec_sha256"][:18],
              "- tidak ditimpa (satu kunci = satu ujian)")
        return lama
    d = {"kunci": "E24", "t_kunci": iso(now), "t_kunci_epoch": now,
         "spec": SPEC, "spec_sha256": sha_spec(), "umur_jam_min": UMUR_JAM_MIN,
         "menit_kunci": now + UMUR_JAM_MIN * 3600,
         "perintah_vonis": "python -X utf8 tools/entry_ab.py"}
    io.open(LOCK, "w", encoding="utf-8", newline="\n").write(json.dumps(d, indent=2, sort_keys=True))
    print("KUNCI E24 DIPASANG %s | sha %s | vonis %s"
          % (d["t_kunci"], d["spec_sha256"][:18], iso(d["menit_kunci"])))
    print("kejadian pasca-kunci yang sudah tercatat sekarang:", jumlah(now))
    return d


def jumlah(now):
    n = 0
    if os.path.exists(LOG):
        for ln in io.open(LOG, encoding="utf-8", errors="replace"):
            if ln.startswith("{"):
                try:
                    d = json.loads(ln)
                except ValueError:
                    continue
                if str(d.get("dibuat_utc") or "") > iso(now):
                    n += 1
    return n


def ambil(t_kunci):
    """Baris terakhir per slot, lalu dipecah jadi T / K - hanya yang SAH dan pasca-kunci."""
    latest, urutan = FL.muat_log()
    T, K, kosedang = [], [], 0
    for sid in urutan:
        r = latest[sid]
        if str(r.get("dibuat_utc") or "") <= t_kunci:
            continue
        if r.get("status") != "dinilai" or not isinstance(r.get("keluar_%dm" % H), dict):
            if r.get("kontrol") and r.get("status") == "KONTROL-KOSONG":
                kosedang += 1
            continue
        if not FL.sah_arm(r, H):
            continue
        (K if r.get("kontrol") else T).append(r)
    return T, K, kosedang


def komposisi(xs):
    if not xs:
        return {}
    lat = sorted(x.get("latensi_keputusan_detik") or 0 for x in xs)
    um = sorted(x.get("umur_baris_entry_detik") or 0 for x in xs)
    return {"n": len(xs), "token_berbeda": len({x.get("tk") for x in xs}),
            "umur_keputusan_median_d": int(FC.med(lat)), "umur_baris_median_d": int(FC.med(um)),
            "latensi_max_d": int(lat[-1])}


def boot_diff(a, b, n=4000, seed=SEED):
    """CI 5 % satu arah dari selisih dua mean (winsorised)."""
    import random
    rng = random.Random(seed)
    wa, wb = [w(x) for x in a], [w(x) for x in b]
    if not wa or not wb:
        return None, None
    ds = []
    for _ in range(n):
        sa = [wa[rng.randrange(len(wa))] for _ in wa]
        sb = [wb[rng.randrange(len(wb))] for _ in wb]
        ds.append(sum(sa) / len(sa) - sum(sb) / len(sb))
    ds.sort()
    return ds[int(0.05 * n)], ds[int(0.95 * n)]


def vonis(now, kunci, simpan=True):
    t_kunci = kunci["t_kunci"]
    if now < kunci["menit_kunci"]:
        print("MENOLAK MEMVONIS - kunci dipasang %s, syarat umur %d jam baru jatuh %s (sekarang %s)."
              % (t_kunci, UMUR_JAM_MIN, iso(kunci["menit_kunci"]), iso(now)))
        print("Yang boleh dilaporkan tanpa melanggar kunci: status, bukan vonis (--status).")
        return {"vonis": "BELUM MATANG"}
    T, K, kosedang = ambil(t_kunci)
    vt = [x["keluar_%dm" % H]["net_bps"] for x in T]
    vk = [x["keluar_%dm" % H]["net_bps"] for x in K]
    kt, kk = komposisi(T), komposisi(K)
    print("E24 | populasi pasca-kunci %s: T=%s K=%s (kontrol tanpa kandidat: %d)"
          % (t_kunci, json.dumps(kt, ensure_ascii=False), json.dumps(kk, ensure_ascii=False),
             kosedang))
    if not vt or not vk:
        print("VONIS: BELUM BISA DIUJI - %s" % ("lengan kontrol belum ada yang dinilai" if not vk
                                                else "lengan perlakuan belum ada yang dinilai"))
        return {"vonis": "BELUM BISA DIUJI", "n_T": len(vt), "n_K": len(vk)}
    lo_d, hi_d = boot_diff(vt, vk)
    selisih = sum(w(x) for x in vt) / len(vt) - sum(w(x) for x in vk) / len(vk)
    p_mw = FC.mann_whitney_p(vt, vk)
    c1 = len(vt) >= N_MIN and len(vk) >= N_MIN
    c2 = FC.med(vt) > 0 and (lo_d or -1) > 0
    c3 = p_mw < 0.05
    c4 = bool(kt) and bool(kk) and abs(kt["umur_keputusan_median_d"] - kk["umur_keputusan_median_d"]) <= 60
    print("   T (terpilih) : mean winso %+0.1f | median %+0.1f | n=%d"
          % (sum(w(x) for x in vt) / len(vt), FC.med(vt), len(vt)))
    print("   K (acak)     : mean winso %+0.1f | median %+0.1f | n=%d"
          % (sum(w(x) for x in vk) / len(vk), FC.med(vk), len(vk)))
    print("   selisih mean %+0.1f bps | CI bawah 5%% %+0.1f | Mann-Whitney satu arah p=%.4f"
          % (selisih, lo_d, p_mw))
    print("   syarat: (1) n>=40 per lengan %s | (2) median(T)>0 & CI bawah>0 %s | (3) p<0,05 %s | "
          "(4) umur keputusan sebanding %s"
          % ("LOLOS" if c1 else "GAGAL", "LOLOS" if c2 else "GAGAL", "LOLOS" if c3 else "GAGAL",
             "LOLOS" if c4 else "GAGAL"))
    vonis = "LAYAK" if (c1 and c2 and c3 and c4) else "BELUM BISA DIUJI" if not c1 else "GAGAL"
    print("VONIS E24: %s" % vonis)
    if vonis == "GAGAL":
        print("   baca yang benar: seleksi kami TIDAK mengalahkan masuk acak pada horison ini. Ini "
              "bukan 'VETO justru untung' - arah dibalik butuh kunci baru, bukan reinterpretasi.")
    d = {"kunci": "E24", "t_kunci": t_kunci, "vonis_utc": iso(now), "spec_sha256": sha_spec(),
         "n_T": len(vt), "n_K": len(vk), "komposisi_T": kt, "komposisi_K": kk,
         "mean_winso_T": round(sum(w(x) for x in vt) / len(vt), 1),
         "mean_winso_K": round(sum(w(x) for x in vk) / len(vk), 1),
         "median_T": round(FC.med(vt), 1), "median_K": round(FC.med(vk), 1),
         "selisih_mean": round(selisih, 1), "ci_bawah_selisih": None if lo_d is None else round(lo_d, 1),
         "p_mann_whitney": round(p_mw, 5), "kontrol_kosong": kosedang,
         "syarat": {"n_cukup": c1, "median_ci": c2, "mw": c3, "sebanding": c4}, "vonis": vonis,
         "winsor_bps": WINS, "boot_n": 4000, "seed": SEED,
         "perintah": "python -X utf8 tools/entry_ab.py"}
    if simpan:
        io.open(os.path.join(ROOT, "decisions",
                             "entry-ab-vonis-%s.json" % iso(now).replace(":", "").replace("-", "")),
                "w", encoding="utf-8", newline="\n").write(json.dumps(d, indent=2, sort_keys=True,
                                                                      ensure_ascii=False))
    return d


def status(now, kunci):
    T, K, kosedang = ambil(kunci["t_kunci"])
    print("STATUS E24 (bukan vonis) | kunci %s | matang %s | sekarang %s"
          % (kunci["t_kunci"], iso(kunci["menit_kunci"]), iso(now)))
    print("   T terpasang %d | K terpasang %d | siklus tanpa kandidat kontrol %d"
          % (len(T), len(K), kosedang))
    print("   komposisi T:", json.dumps(komposisi(T), ensure_ascii=False))
    print("   komposisi K:", json.dumps(komposisi(K), ensure_ascii=False))
    print("   perlu %d lagi di tiap lengan sebelum vonis boleh dijatuhkan (n_min %d, tidak "
          "diturunkan)" % (max(0, N_MIN - len(T)), N_MIN))
    return {"n_T": len(T), "n_K": len(K)}


def self_test():
    global LOG
    asli, fl = LOG, FL.LOG
    tmp = os.path.join(ROOT, "decisions", "_entry_ab_uji.jsonl")
    assert "_uji" in tmp
    LOG = tmp
    FL.LOG = tmp
    io.open(tmp, "w", encoding="utf-8").write("")
    now = 1_800_000_000
    tk = iso(now)
    baris = []
    for i in range(50):
        for ctl in (False, True):
            baris.append({"slot_id": ("R" if ctl else "S") + "%03d" % i, "status": "dinilai",
                          "kontrol": ctl, "dibuat_utc": iso(now + 10), "pemilih": FL.REJIM_BARI,
                          "latensi_keputusan_detik": 60 if ctl else (58 + i % 4),
                          "keluar_%dm" % H: {"net_bps": (120.0 if ctl else 700.0) - i,
                                             "sah": True, "umur_baris_detik": 0},
                          "tk": "0xt%02d" % (i % 12), "umur_baris_entry_detik": 38})
    io.open(tmp, "w", encoding="utf-8", newline="\n").write(
        "\n".join(json.dumps(b) for b in baris) + "\n")
    T, K, kosong = ambil(tk)
    assert len(T) == 50 and len(K) == 50, (len(T), len(K))
    assert komposisi(T)["token_berbeda"] == 12, komposisi(T)
    assert FL.sah_arm({"keluar_%dm" % H: {"net_bps": 1.0}, "latensi_keputusan_detik": 121}, H) is False
    lo, hi = boot_diff([x["keluar_%dm" % H]["net_bps"] for x in T],
                       [x["keluar_%dm" % H]["net_bps"] for x in K])
    assert lo > 0, (lo, hi)
    d = vonis(now + UMUR_JAM_MIN * 3600 + 60, {"t_kunci": tk, "menit_kunci": now + 60},
             simpan=False)
    assert d["vonis"] == "LAYAK", d
    # KONTROL NEGATIF: kalau T dan K diambil dari distribusi yang SAMA, vonis tidak boleh LAYAK.
    # Tanpa baris ini, harness apa pun bisa lulus dengan sekadar selalu menjawab "ya".
    sama = []
    for i, b in enumerate(baris):
        nb = dict(b)
        nb["keluar_%dm" % H] = {"net_bps": 300.0 - (i % 25) * 12.0, "sah": True,
                                "umur_baris_detik": 0}
        sama.append(nb)
    io.open(tmp, "w", encoding="utf-8", newline="\n").write(
        "\n".join(json.dumps(x) for x in sama) + "\n")
    dn = vonis(now + UMUR_JAM_MIN * 3600 + 60, {"t_kunci": tk, "menit_kunci": now + 60},
              simpan=False)
    assert dn["vonis"] == "GAGAL", dn
    # sebelum matang: tidak boleh ada vonis sama sekali
    assert vonis(now, {"t_kunci": tk, "menit_kunci": now + 3600}, simpan=False)["vonis"] == "BELUM MATANG"
    os.remove(tmp)
    LOG, FL.LOG = asli, fl
    print("self-test E24 OK: dua lengan terpisah | LAYAK pada selisih nyata | GAGAL pada "
          "distribusi IDENTIK (kontrol negatif) | `sah` menolak keputusan telat | "
          "menolak vonis sebelum matang | tidak ada artefak uji yang ditulis")


def utama():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--lock", action="store_true")
    p.add_argument("--status", action="store_true")
    p.add_argument("--self-test", dest="self_test", action="store_true")
    a = p.parse_args()
    now = int(time.time())
    if a.self_test:
        return self_test()
    if a.lock:
        return pasang_kunci(now)
    if not os.path.exists(LOCK):
        raise SystemExit("belum ada kunci E24 - jalankan --lock (dan hanya sebelum ada pasangan "
                         "kontrol dinilai)")
    kunci = json.load(io.open(LOCK, encoding="utf-8"))
    assert kunci["spec_sha256"] == sha_spec(), "spec kunci tidak cocok dengan spec alat - JANGAN " \
                                               "mengubah ujian setelah di-sha"
    if a.status:
        return status(now, kunci)
    return vonis(now, kunci)


if __name__ == "__main__":
    utama()
