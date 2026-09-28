"""Percobaan pertama untuk "KAPAN BOLEH MASUK": menyortir dalam budget 5 posisi/hari.

Agen kami punya `dailyCap` 5 (ExecutionVault), jadi pertanyaan yang benar bukan "masuk/tidak", tapi
"dari kandidat yang boleh, 5 yang mana?". Kalau tidak ada fitur yang mengalahkan acak, maka
kepunyaan kami memang cuma rem - dan itu harus diukur, bukan diasumsikan.

Yang dipakai untuk menyortir: kolom dari snapshot universe KITA SENDIRI (`universe/bsc-universe.jsonl`
- volume 24 jam, likuiditas, umur pool, perubahan harga 24 jam, smart_degen, sniper, top10, lock),
dengan aturan point-in-time: snapshot yang boleh dipakai hanyalah yang `epoch <= t` kejadian.
Fitur maker (kerumunan) sudah dikuras di `tools/tail_test.py` dan tidak ada yang menaikkan ekor.

Kebijakan yang dibandingkan pada hari yang sama:
  first-5   : kandidat pertama yang lolos gerbang (tanpa penyortiran)
  random-5  : 5 acak dari kandidat (4.000 undian -> CI)
  top-<fit> : 5 teratas menurut satu fitur, arah tetap (desc) - dieveri satu per satu, bukan digabung
Semua net sudah dipotong ongkos 59 bps dan di-winsor +-2.000 bps.
"""
from __future__ import annotations

import io
import json
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import costs  # noqa: E402
import flow_cluster_test as FC  # noqa: E402
import mirror_test as MT  # noqa: E402

WINS, CAP = 2000.0, 5
FITUR = ["volume_24h", "liquidity", "age_sec", "price_change_24h", "smart_degen_count",
         "sniper_count", "holder_count", "top_10_holder_rate", "lock_percent", "bundler_rate"]
HARI = 86400


def w(x):
    return min(max(x, -WINS), WINS)


def snapshots():
    out = []
    for ln in io.open(os.path.join(ROOT, "universe", "bsc-universe.jsonl"), encoding="utf-8",
                      errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        d = json.loads(ln)
        ep = int(d.get("epoch") or 0)
        if not ep:
            continue
        m = {}
        for r in d.get("rows") or []:
            tk = str(r.get("base_token") or "").lower()
            if tk:
                m[tk] = {k: r.get(k) for k in FITUR}
        out.append((ep, m))
    out.sort()
    return out


def ambil(snap, tk, t):
    """Snapshot terakhir yang STEMPELNYA <= t (point-in-time; bukan yang 'paling baru di disk')."""
    pilih = None
    for ep, m in snap:
        if ep > t:
            break
        if tk in m:
            pilih = m[tk]
    return pilih


def main():
    rt = costs.rt_cost()
    ev = MT.bangun(30, 15)
    boleh = [e for e in ev if not (e["jual_2"] or e["jual_bersih"])]
    snap = snapshots()
    berfitur = []
    for e in boleh:
        f = ambil(snap, e["tk"], e["t"])
        if f and any(isinstance(f.get(k), (int, float)) for k in FITUR):
            e["f"] = f
            berfitur.append(e)
    print("harga peristiwa | ongkos %.1f bps | %d kejadian | lolos gerbang %d | yang punya fitur "
          "point-in-time %d (%.1f %% dari yang lolos)"
          % (rt, len(ev), len(boleh), len(berfitur), 100.0 * len(berfitur) / max(len(boleh), 1)))
    hari = sorted({e["t"] // HARI for e in berfitur})
    per_hari = {d: [e for e in berfitur if e["t"] // HARI == d] for d in hari}
    cukup = [d for d in hari if len(per_hari[d]) >= 2 * CAP]
    print("hari teramati %d | hari dengan kandidat >= %d: %d" % (len(hari), 2 * CAP, len(cukup)))
    if len(cukup) < 2:
        print("SAMPEL TIDAK CUKIL untuk menyortir per hari - tidak ada vonis. (bukan 'tidak ada "
              "efek', cuma belum bisa diuji)")
        return

    def nilai(pilihan):
        return [w(e["net"]) for e in pilihan]

    def policy_first():
        xs = []
        for d in cukup:
            xs += nilai(sorted(per_hari[d], key=lambda e: e["t"])[:CAP])
        return xs

    def policy_top(feat):
        xs = []
        for d in cukup:
            kandidat = [e for e in per_hari[d] if isinstance(e["f"].get(feat), (int, float))]
            if len(kandidat) < CAP:
                continue
            xs += nilai(sorted(kandidat, key=lambda e: -e["f"][feat])[:CAP])
        return xs

    rnd = random.Random(20260928)
    draws = []
    for _ in range(2000):
        xs = []
        for d in cukup:
            k = per_hari[d][:]
            rnd.shuffle(k)
            xs += nilai(k[:CAP])
        draws.append(sum(xs) / len(xs))
    draws.sort()
    acak_lo, acak_hi = draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws))]
    acak_mean = sum(draws) / len(draws)
    f = policy_first()
    print("\n%-24s %6s %11s %-21s %9s" % ("kebijakan", "n", "mean winso", "CI 95 %", "median"))
    print("%-24s %6d %+11.1f [%+9.1f; %+9.1f] %+9.1f"
          % ("first-5 (tanpa sortir)", len(f), sum(f) / len(f), acak_lo, acak_hi, FC.med(f)))
    print("%-24s %6d %+11.1f [%+9.1f; %+9.1f] %9s"
          % ("random-5 (4.000 undian)", len(f), acak_mean, acak_lo, acak_hi, "-"))
    hasil = []
    for feat in FITUR:
        xs = policy_top(feat)
        if len(xs) < 8:
            continue
        m = sum(xs) / len(xs)
        hasil.append((feat, m, len(xs)))
        tanda = "di atas acak" if m > acak_hi else ("di BAWAH acak" if m < acak_lo else "seri")
        print("%-24s %6d %+11.1f %-21s %+9.1f  %s"
              % ("top-5 " + feat, len(xs), m, "", FC.med(xs), tanda))
    print("\nacakan 95 %% CI = [%+.1f; %+.1f] bps/posisi. Tidak ada fitur di atas batas atas CI "
          "acak = TIDAK ADA yang bisa kami pakai untuk memilih." % (acak_lo, acak_hi))
    menang = [h for h in hasil if h[1] > acak_hi]
    print("fitur yang mengalahkan acak: %s" % (", ".join("%s (%+.1f)" % t for t in menang) or "TIDAK ADA"))
    n_no = sum(1 for h in hasil if h[1] < acak_lo)
    print("fitur yang justru di bawah acak: %d dari %d - kalau semua 'seri', tidak ada penyortiran "
          "yang kami klaim" % (n_no, len(hasil)))


if __name__ == "__main__":
    main()
