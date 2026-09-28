"""Alat yang MENOLAK membocorkan hasilnya sendiri (P20).

Alur kerjanya adalah bagiannya yang penting:

  1. spesifikasi dibaca dari `vault/06-Results/11 - Pra-Registrasi Hari Kedua.md` (blok ```text)
  2. run pertama mengunci: sha256(blok) + `t_kunci` = stempel aliran terakhir SAAT ITU, lalu
     BERHENTI - tidak ada satu pun angka yang dicetak
  3. run berikutnya membandingkan sha: kalau blok spesifikasi diedit setelah dikunci, alat mati
  4. alat hanya mau menilai kalau rekaman baru >= syarat_umur_jam sejak `t_kunci`
  5. yang dinilai HANYA kejadian setelah `t_kunci` (out-of-sample murni), dengan aturan yang terkunci

Ini bukan seremoni: halaman 09 dan 10 berisi angka yang lahir dari satu jendela yang sama, dan satu
jendela tidak bisa membuktikan dua kali. Kalau halaman 11 mati sebelum angka keluar, dialah yang
punya hak bicara soal gerbang ⑧ - bukan aku.

Pakai:  python -X utf8 tools/day2_replicate.py
       python -X utf8 tools/day2_replicate.py --status
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import evidence_stack as ES  # noqa: E402  (build_events + _pair: SATU implementasi uji)
import flow_cluster_test as FC  # noqa: E402
import prices as PR  # noqa: E402
import tx_prices as TP  # noqa: E402  (deret harga peristiwa)

SPEC = os.path.join(ROOT, "vault", "06-Results", "11 - Pra-Registrasi Hari Kedua.md")
LOCK = os.path.join(ROOT, "decisions", "prereg-day2-lock.json")
OUT_DIR = os.path.join(ROOT, "decisions")
FLOW = os.path.join(ROOT, "universe", "wallet-flow.jsonl")
ASPEK_LULUS = ["cluster_ge2", "cluster_ge3", "repeat_maker", "money_spread", "buy_usd_ge_1k"]

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def read_spec(spec_path=SPEC):
    if not os.path.exists(spec_path):
        raise SystemExit("tidak ada %s - spesifikasi harus ada sebelum alat ini boleh jalan"
                         % spec_path)
    s = io.open(spec_path, encoding="utf-8", errors="replace").read()
    m = re.search(r"```text\n(.*?)\n```", s, re.S)
    if not m:
        raise SystemExit("blok ```text spesifikasi tidak ditemukan di halaman 11")
    blok = m.group(1)
    kv = {}
    for ln in blok.splitlines():
        ln = re.sub(r"\s+#.*$", "", ln).strip()
        if ":" in ln:
            k, v = ln.split(":", 1)
            kv[k.strip()] = v.strip()
    need = ["horison_menit", "jendela_menit", "ongkos_bps_roundtrip", "koreksi", "syarat_umur_jam",
            "uji_primer", "uji_kedua", "uji_ketiga", "sumber_harga"]
    hilang = [k for k in need if k not in kv]
    if hilang:
        raise SystemExit("spesifikasi tidak lengkap, kunci hilang: %s" % ", ".join(hilang))
    sha = "0x" + hashlib.sha256(blok.encode("utf-8")).hexdigest()
    return kv, sha


def last_flow_stamp():
    """Stempel terakhir di SALINAN LOKAL - dan itu persis yang menipu kami dua kali (27 & 28 Sep).

    Umur aliran menentukan kapan alat ini boleh bicara. Salinan yang basi membuat jam replikasi
    terbaca salah arah, jadi penjaga ini membandingkan dengan commit data terbaru di `origin/*` dan
    BERTERIA kalau bedanya > 10 menit. Vonis tetap dihitung dari berkas lokal - itu satu-satunya
    berkas yang bisa dibaca utuh - tapi pembacanya tahu kalau tanahnya gompal.
    """
    t = 0
    for ln in io.open(FLOW, encoding="utf-8", errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        x = int(d.get("t") or 0)
        if x > t:
            t = x
    try:
        import subprocess
        for ref in ("origin/master", "origin/HEAD"):
            r = subprocess.run(["git", "log", "-1", "--format=%ct", ref, "--",
                                "universe/wallet-flow.jsonl"], cwd=ROOT, capture_output=True,
                               text=True)
            tok = int((r.stdout or "0").strip() or 0) if r.returncode == 0 else 0
            if not tok:
                continue
            if tok > t + 600:
                print("PERINGATAN: salinan lokal BASI - %s punya commit data %.0f MENIT lebih baru "
                      "dari stempel terakhir %s. Jam dan vonis di bawah dihitung dari berkas yang "
                      "basi itu: jalankan `git pull` sebelum mempercayainya."
                      % (ref, (tok - t) / 60.0, os.path.basename(FLOW)))
            break
    except Exception as e:
        print("(penjaga salinan basi tidak bisa jalan: %r - keadaan lokal TIDAK terverifikasi)" % e)
    return t


def verdict(r):
    if r.get("status"):
        return "TIDAK DIUJI (%s)" % r["status"]
    ok = (r["median_selisih_bps"] > 0 and (r["ci_lo"] or 0) > 0 and r["p"] < 0.05)
    return "REPLIKASI" if ok else "GAGAL"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true", help="hanya: terkunci kapan, berapa jam lagi")
    ap.add_argument("--halaman", default="11", choices=("11", "12"),
                    help="11 = spesifikasi lama (harga px, sudah DIKUNCI 28 Sep 08:30Z); "
                         "12 = spesifikasi jujur (harga peristiwa). Masing-masing punya berkas "
                         "kunci sendiri - mengedit yang satu tidak mengubah yang lain.")
    a = ap.parse_args()
    if a.halaman == "12":
        spec = os.path.join(ROOT, "vault", "06-Results", "12 - Harga Masuk yang Benar.md")
        lock_p = os.path.join(OUT_DIR, "prereg-honest-lock.json")
        prefix = "day2h"
    else:
        spec, lock_p, prefix = SPEC, LOCK, "day2"
    kv, sha = read_spec(spec)
    umur_butuh = int(kv["syarat_umur_jam"])
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if not os.path.exists(lock_p):
        if a.status:
            print("BELUM DIKUNCI - jalankan tanpa --status untuk mengunci sekarang.")
            return
        t_kunci = last_flow_stamp()
        if not t_kunci:
            raise SystemExit("aliran kosong - tidak ada yang bisa dikunci")
        assert 1_700_000_000 < t_kunci < 2_000_000_000, "t_kunci bukan detik Unix: %d" % t_kunci
        lock = {"dibuat_utc": now, "spec_sha256": sha, "t_kunci": t_kunci,
                "t_kunci_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t_kunci)),
                "spesifikasi": os.path.relpath(spec, ROOT).replace("\\", "/"),
                "parameter_terkunci": kv, "aspek_lulus_28Sep": ASPEK_LULUS}
        os.makedirs(OUT_DIR, exist_ok=True)
        json.dump(lock, io.open(lock_p, "w", encoding="utf-8", newline="\n"), indent=1,
                  sort_keys=True, ensure_ascii=False)
        print("TERKUNCI %s" % sha)
        print("t_kunci = %s (stempel aliran terakhir saat mengunci)" % lock["t_kunci_iso"])
        print("syarat replikasi: rekaman baru >= %d jam SETELAH t_kunci, lalu jalankan ulang."
              % umur_butuh)
        print("Tidak ada satu pun angka hasil yang dicetak - itu memang bagian dari alat ini.")
        print("kunci: decisions/%s" % os.path.basename(lock_p))
        return

    lock = json.load(io.open(lock_p, encoding="utf-8"))
    if lock.get("spec_sha256") != sha:
        raise SystemExit("SPESIFIKASI DIUBAH SETELAH DIKUNCI (%s != %s). Tidak ada hasil: "
                         "yang berubah bukan datanya, aturan mainnya."
                         % (str(lock.get("spec_sha256"))[:18], sha[:18]))
    t_kunci = int(lock["t_kunci"])
    t_now = last_flow_stamp()
    baru_jam = (t_now - t_kunci) / 3600.0
    print("terkunci %s | spec %s | rekaman baru %.2f jam dari kebutuhan %d jam"
          % (lock["dibuat_utc"], sha[:18], max(baru_jam, 0.0), umur_butuh))
    if a.status:
        print("sisa: %s" % ("SIAP JALAN" if baru_jam >= umur_butuh else
                            "%.1f jam lagi" % (umur_butuh - baru_jam)))
        return
    if baru_jam < umur_butuh:
        print("BELUM SAH - kurang %.1f jam lagi. Ketiadaan hasil BUKAN hasil: tidak ada angka "
              "yang dicetak, tidak ada klaim yang bergerak." % (umur_butuh - baru_jam))
        return

    H, W = int(kv["horison_menit"]), int(kv["jendela_menit"])
    order = {"watch": (PR.SRC_WATCH,), "gmgn": (PR.SRC_GMGN,), "txevent": (TP.SRC_TX,)}[
        kv["sumber_harga"]]
    tx, _ = ES.load()
    sources = PR.load_all()
    if TP.SRC_TX in order:
        sources[TP.SRC_TX] = TP.load_tx_series()
    ev, dropped = ES.build_events(tx, sources, H, W, order)
    ev = [e for e in ev if e["t"] > t_kunci]
    ntok = len({e["tk"] for e in ev})
    print("bahan replikasi: %d kejadian pada %d token (semuanya SETELAH t_kunci) | sensor %s"
          % (len(ev), ntok, dropped))
    if len(ev) < 40:
        print("SAMPEL TERLALU KECIL untuk replikasi apa pun (%d) - tidak ada vonis." % len(ev))
        return
    rows = []
    for key in ("uji_primer", "uji_kedua", "uji_ketiga"):
        fitur = kv[key]
        if fitur.startswith("stack"):
            pred = lambda e, f=ASPEK_LULUS: sum(1 for x in f if e.get(x)) >= 2  # noqa: E731
        else:
            pred = lambda e, f=fitur: bool(e.get(f))  # noqa: E731
        r = ES._pair(ev, pred, fitur)
        r["kunci"] = key
        r["vonis"] = verdict(r)
        rows.append(r)
        if r.get("status"):
            print("  %-14s %-14s %s" % (key, fitur, r["status"]))
        else:
            print("  %-14s %-14s token=%-4d n=%-4d med %+9.1f CI [%+.0f; %+.0f] p=%.4f -> %s"
                  % (key, fitur, r["token"], r["n"], r["median_selisih_bps"], r["ci_lo"], r["ci_hi"],
                     r["p"], r["vonis"]))
    ps = FC.bh([(r["fitur"], r["p"]) for r in rows if r.get("p") is not None])
    lulus = sum(1 for r in rows if r["vonis"] == "REPLIKASI")
    if lulus == 0:
        vonis = ("TIDAK ADA REPLIKASI - klaim pada halaman yang diuji DICABUT (aturan halaman "
                 "%s baris terakhir)" % a.halaman)
    elif rows[0]["vonis"] == "REPLIKASI":
        vonis = "uji_primer replikasi - kandidat gerbang ⑧ boleh diusulkan ke P15 (turun saja)"
    else:
        vonis = ("uji_primer gagal tapi uji kedua/ketiga replikasi - yang hidup STRUKTUR DANA, "
                 "halaman 09 diturunkan statusnya")
    out = {"dibuat_utc": now, "halaman_spesifikasi": a.halaman, "spec_sha256": sha,
           "t_kunci": t_kunci, "rekaman_baru_jam": round(baru_jam, 2),
           "horizon_menit": H, "window_menit": W, "kejadian": len(ev), "token": ntok,
           "rows": rows, "lolos_bh_dalam_run": sorted(ps), "vonis": vonis,
           "batas": ["satu jendela rezim mungkin masih sama dengan jendela saat spesifikasi ditulis",
                     "belum ada fill nyata; outcome = probabilitas 30 menit, bukan PnL",
                     "maker = yang ditampilkan feed vendor: kerumunan = batas bawah"]}
    os.makedirs(OUT_DIR, exist_ok=True)
    p = os.path.join(OUT_DIR, "%s-%s.json" % (prefix, time.strftime("%Y%m%dT%H%M%SZ",
                                               time.gmtime())))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True,
              ensure_ascii=False)
    print("\nVONIS: %s" % vonis)
    print("artefak: decisions/%s" % os.path.basename(p))


if __name__ == "__main__":
    main()
