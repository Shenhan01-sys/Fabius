"""Seberapa "beku" deret harga kami, dan apakah efek K>=2 bertahan kalau kebekuan itu dibuang?

Konteks (terukur 28 Sep 09:19-09:2xZ): baris `px` = harga transaksi TERAKHIR token itu, di-stamp
dengan waktu tarikan. Tidak ada transaksi baru = nilai yang sama diulang dengan stempel baru. Jadi
deret kami bukan ticker - dia tangga yang melangkah hanya saat smart-money bertransaksi.

Tiga pengukuran:
  A. beku-per-baris: % baris px yang nilainya SAMA dengan baris sebelumnya pada token yang sama
  B. robustness: bangun ulang outcome dengan deret yang pengulangan nilainya DIBUANG (satu titik per
     perubahan, stempel = kemunculan pertama). Kalau K>=2 bertahan, efeknya bukan artefak baris dobel
  C. resolusi: berapa kejadian yang gross-nya PERSIS nol, per kelas, pada kedua deret
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import evidence_stack as ES  # noqa: E402
import flow_cluster_test as FC  # noqa: E402
import prices as PR  # noqa: E402

MIN = 60
tx, pxs = ES.load()

beku = total = 0
for tk, s in pxs.items():
    for i in range(1, len(s)):
        total += 1
        if s[i][1] == s[i - 1][1]:
            beku += 1
print("A. baris px yang nilainya sama dengan baris sebelumnya: %d dari %d = %.1f %%"
      % (beku, total, 100.0 * beku / max(total, 1)))

runtun = {}
for tk, s in pxs.items():
    out, last = [], None
    for t, p in s:
        if p != last:
            out.append((t, p))
            last = p
    runtun[tk] = out
n1 = sum(len(v) for v in pxs.values())
n2 = sum(len(v) for v in runtun.values())
print("   baris px: %d -> %d setelah pengulangan nilai dibuang (hilang %.1f %%)"
      % (n1, n2, 100.0 * (n1 - n2) / max(n1, 1)))


def jalankan(sources, label):
    ev, dropped = ES.build_events(tx, sources, 30, 15, (PR.SRC_GMGN,))
    for lab, pool in (("K=1", [e for e in ev if not e["cluster_ge2"]]),
                      ("K>=2", [e for e in ev if e["cluster_ge2"]])):
        xs = [e["net_bps"] for e in pool]
        nol = sum(1 for x in xs if abs(x + 59.0) < 1e-9)
        print("  %-22s %-5s n=%-5d med %+9.1f | gross persis 0: %5d (%.1f %%)"
              % (label, lab, len(xs), FC.med(xs) if xs else 0, nol,
                 100.0 * nol / max(len(xs), 1)))
    r = ES._pair(ev, lambda e: e["cluster_ge2"], "K>=2")
    if r.get("status"):
        print("  %-22s berpasangan: %s" % (label, r["status"]))
    else:
        print("  %-22s berpasangan: token=%d n=%d med %+9.1f CI [%+.0f; %+.0f] p=%.4f"
              % (label, r["token"], r["n"], r["median_selisih_bps"], r["ci_lo"], r["ci_hi"], r["p"]))
    return ev


print("\nB. outcome dengan DERET APA ADANYA (baris berulang ikut jadi titik data)")
ev_a = jalankan({PR.SRC_GMGN: {"rows": pxs}}, "deret mentah")
print("\nC. outcome dengan pengulangan nilai DIBUANG (satu titik per perubahan harga)")
ev_b = jalankan({PR.SRC_GMGN: {"rows": runtun}}, "deret ranah-berubah")

sama = sum(1 for a, b in zip(ev_a, ev_b) if a["tk"] == b["tk"] and a["t"] == b["t"])
print("\nkejadian yang tetap ada di kedua deret: %d (mentah %d | dibuang %d)"
      % (sama, len(ev_a), len(ev_b)))
print("Tafsir: kalau B dan C memberi median yang searah dan sama-sama lolos BH, efek K>=2 bukan")
print("artefak baris berulang. Kalau C runtuh, angka kami sebagian besar adalah counting artifact.")
