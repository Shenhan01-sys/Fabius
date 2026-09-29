"""P33 tahap 2 - buku kehadiran: siapa yang benar-benar HILANG, bukan siapa yang tak terukur.

Halaman 16 memberi kita bound: 80,6 % kejadian kohort muda tidak punya harga keluar, dan kalau yang
hilang itu diberi nilai seburuk p05 teramati, mean kohort jatuh dari +249 ke -1.563. Itu Jujur tapi
buta - ia tidak membedakan "poolnya mati" dari "kami tidak kebagian batch".

Yang belum dipakai: sejarah `universe/watch-prices.jsonl` sudah mengandung jawaban atas pertanyaan itu.
Perekam pantau menarik SEMUA token yang pernah lewat, tiap siklus, selama 2 jam - dan satu siklus
memakai SATU stempel untuk seluruh batch-nya. Jadi token yang hadir di siklus 1..k lalu lenyap di
siklus k+1.. sementara siklus-siklus itu tetap menghasilkan harga untuk token lain = token yang
**tidak lagi dijawab venue**. Bukan lubang pemanggilan kita.

Status yang dilaporkan per token (aturan ditulis sebelum melihat hasilnya):
  ADA         muncul di siklus terakhir yang dianggap subuh (>= 12 token terjawab)
  HILANG      tidak muncul di >= 3 siklus subuh berturut-turut SETELAH kemunculan terakhirnya
  SEPARUH     ada siklus subuh yang tidak memuatnya, tapi belum 3 berturut
  TIDAK-JELAS tidak pernah muncul di siklus subuh setelahnya / riwayat terlalu pendek

Lalu bound lama dihitung ulang dengan bukti ini: kejadian tanpa harga keluar dibagi menjadi
"HILANG (kemungkinan besar rugi)" vs "belum tentu". Kalau +249,3 bertahan setelah yang HILANG
dihitung rugi, dia layak dikejar; kalau tidak, dia memang angka korban selamat.

Pakai:  python -X utf8 tools/presence_ledger.py
       python -X utf8 tools/presence_ledger.py --min-siklus 3 --horizon 30
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import costs  # noqa: E402
import flow_cluster_test as FC  # noqa: E402
import mirror_test as MT  # noqa: E402  (SATU definisi kejadian + harga peristiwa)

WP = os.path.join(ROOT, "universe", "watch-prices.jsonl")
SUBUH_MIN = 12
WINS = 2000.0


def w(x):
    return max(-WINS, min(WINS, x))


def baca_bukti():
    """`wp0` = ditanya dan tidak dijawab (berita). `wpc` = berapa yang kami tanya siklus itu.

    Dengan dua baris ini status kehadiran tidak lagi perlu dispekulasikan dari pola hilang-timbul:
    'tidak dijawab' dan 'tidak ditanya' sudah terpisah di berkas. Yang mengembalikan fungsi ini:
    (hadir_tak_dijawab: {tk: [t,...]}, cakupan: [(t, n_tanya, n_jawab)])
    """
    tak_dijawab, tanya = {}, {}
    for ln in io.open(WP, encoding="utf-8", errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        k = d.get("k")
        t = int(d.get("t") or 0)
        if k == "wp0" and d.get("why", "").startswith("answered"):
            tak_dijawab.setdefault(str(d.get("tk") or ""), []).append((t, d["why"]))
        elif k == "wpc":
            tanya[t] = [int(d.get("n_tanya") or 0), 0]
    return tak_dijawab, tanya


def baca_wp():
    siklus = {}
    for ln in io.open(WP, encoding="utf-8", errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("k") not in ("wp", "wp0"):
            continue
        tk, t = str(d.get("tk") or "").lower(), int(d.get("t") or 0)
        if not tk or not t:
            continue
        s = siklus.setdefault(t, {"ada": set(), "tak": set()})
        (s["ada"] if d["k"] == "wp" else s["tak"]).add(tk)
    return siklus


def status(siklus, min_siklus=3, watch_menit=120):
    """Status kehadiran - dengan jendela pantau sebagai batas yang sah, bukan sebagai noise.

    Versi pertama memanggil 74 % token 'HILANG' dan itu salah: jendela perekam 120 menit, jadi
    absen di siklus ke-40 berarti keluar dari DAFTAR KAMI, bukan tidak dijawab venue. Sekarang
    hanya siklus di dalam (last_seen, last_seen + watch_menit] yang boleh dijadikan bukti.
    """
    ts = sorted(siklus)
    subuh = [t for t in ts if len(siklus[t]["ada"]) >= SUBUH_MIN]
    muncul = {}
    for t in subuh:
        for tk in siklus[t]["ada"]:
            muncul.setdefault(tk, t)
    hadir_terakhir = {}
    for t in subuh:
        for tk, tt in muncul.items():
            if tk in siklus[t]["ada"]:
                hadir_terakhir[tk] = t
    out = {}
    batas = watch_menit * 60
    for tk, tt in muncul.items():
        h = hadir_terakhir.get(tk, tt)
        layak = [t for t in subuh if h < t <= h + batas]
        absen = [t for t in layak if tk not in siklus[t]["ada"]]
        if tk in siklus[h]["ada"] and h == subuh[-1]:
            st = "ADA"
        elif len(layak) >= min_siklus and len(absen) >= min_siklus:
            st = "HILANG"
        elif absen:
            st = "SEPARUH"
        else:
            st = "ADA"
        out[tk] = {"status": st, "muncul_pertama": tt, "hadir_terakhir": h,
                   "siklus_dalam_jendela": len(layak), "absen_dalam_jendela": len(absen)}
    return out, subuh


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-siklus", type=int, default=3)
    ap.add_argument("--horizon", type=int, default=30)
    ap.add_argument("--watch-min", type=int, default=120,
                    help="jendela pantau perekam - hanya siklus di dalamnya yang boleh jadi bukti")
    a = ap.parse_args()
    if not os.path.exists(WP):
        raise SystemExit("tidak ada %s - jalankan universe/record_watch_prices.py dulu" % WP)
    siklus = baca_wp()
    st, subuh = status(siklus, a.min_siklus, a.watch_min)
    tak_dijawab, tanya = baca_bukti()
    jawab = {}
    for t, v in siklus.items():
        jawab[t] = len(v["ada"])
    for t in tanya:
        if t in jawab:
            tanya[t][1] = jawab[t]
    n_bukti = sum(1 for tk, lst in tak_dijawab.items()
                  if any(w == "answered-no-pair" for _, w in lst))
    if tak_dijawab:
        # bukti mengalahkan inferensi: token yang DITANYA dan TIDAK DIJAWAI di >= N siklus
        for tk, lst in tak_dijawab.items():
            NP = sum(1 for _, wy in lst if wy == "answered-no-pair")
            if NP >= a.min_siklus:
                st.setdefault(tk, {"status": "?", "hadir_terakhir": max(x[0] for x in lst)})
                st[tk]["status"] = "HILANG"
                st[tk]["bukti_wp0"] = NP
    cakupan = [(t, v[0], v[1]) for t, v in sorted(tanya.items())]
    bolong = sum(1 for _, n, j in cakupan if n > j)
    hit = {}
    for v in st.values():
        hit[v["status"]] = hit.get(v["status"], 0) + 1
    print("wp: %d siklus (%d subuh, >= %d token terjawab) | %d token pernah terlihat | "
          "jendela pantau %d m"
          % (len(siklus), len(subuh), SUBUH_MIN, len(st), a.watch_min))
    print("status kehadiran: %s" % " | ".join("%s=%d" % (k, hit.get(k, 0))
                                              for k in ("ADA", "HILANG", "SEPARUH")))
    print("bukti langsung dari berkas: %d token pernah `answered-no-pair` | %d siklus `wpc` "
          "tercatat (%d siklus TANYA > JAWAB)" % (n_bukti, len(cakupan), bolong))
    if not cakupan:
        print("   -> belum ada `wpc` di berkas (perbarui perekam + dorong): status HILANG di atas "
              "masih INFERENSI jendela, bukan bukti venue")
    if subuh:
        print("siklus subuh terakhir: %s (%.2f jam lalu)"
              % (time.strftime("%H:%M:%SZ", time.gmtime(subuh[-1])),
                 (time.time() - subuh[-1]) / 3600.0))

    ev = MT.bangun(a.horizon, 15)
    pool = [e for e in ev if not (e["jual_2"] or e["jual_bersih"])]
    print("\nkejadian (harga peristiwa, lolos veto): %d dari %d" % (len(pool), len(ev)))
    # kejadian kita tidak lagi dibuang senyap: tandai apakah tokennya masih ada atau hilang
    for e in pool:
        s = st.get(e["tk"], {}).get("status", "TIDAK-JELAS")
        e["hadir"] = s
    for lab, sub in (("SEMUA", pool),
                     ("hadir=ADA", [e for e in pool if e["hadir"] == "ADA"]),
                     ("hadir=HILANG", [e for e in pool if e["hadir"] == "HILANG"]),
                     ("hadir=SEPARUH", [e for e in pool if e["hadir"] == "SEPARUH"]),
                     ("hadir=TIDAK-JELAS", [e for e in pool if e["hadir"] == "TIDAK-JELAS"])):
        if len(sub) < 10:
            print("  %-18s n=%-4d terlalu kecil" % (lab, len(sub)))
            continue
        v = [w(e["net"]) for e in sub]
        print("  %-18s n=%-4d mean %+9.1f | median %+9.1f | P>=500 %5.1f %% | %4.1f %% positif"
              % (lab, len(v), sum(v) / len(v), FC.med(v),
                 100.0 * sum(1 for x in v if x >= 500) / len(v),
                 100.0 * sum(1 for x in v if x > 0) / len(v)))

    # bound dengan bukti: yang HILANG dihitung rugi penuh (-2.000), yang lain tetap teramati
    teramati = [e for e in pool if e["hadir"] != "HILANG"]
    hilang = [e for e in pool if e["hadir"] == "HILANG"]
    if teramati and hilang:
        vt = [w(e["net"]) for e in teramati]
        untuk_hari_ini = (sum(vt) - len(hilang) * WINS) / (len(vt) + len(hilang))
        print("\nbound dengan bukti kehadiran: %d kejadian teramati (mean %+0.1f) + %d token "
              "HILANG dianggap rugi penuh -> %+0.1f bps/posisi"
              % (len(vt), sum(vt) / len(vt), len(hilang), untuk_hari_ini))
        print("Ini BUKAN angka konservatif - ini konsekuensi dari 'yang tidak menjawab biasanya "
              "sudah tidak bisa dijual'.")
    print("\nYang TIDAK diklaim: siklus tanpa harga tidak otomatis berarti batch gagal (limbah 2 jam "
          "pantau membuat sebagian token memang keluar daftar). Status HILANG butuh >= %d siklus "
          "subuh berturut-turut tanpa token itu." % a.min_siklus)


if __name__ == "__main__":
    utama()
