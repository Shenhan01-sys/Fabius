#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Alat ini dulunya tinggal di folder kerja (`_research/`) dan dikutip dari berkas hasil
# yang sudah terbit. Dipromosikan 29 Sep supaya perintah di vault bisa dijalankan dari
# clone: angka yang tidak bisa dijalankan orang bukan bukti, itu ingatan.
# (dipindah oleh _research/promosi2.py; path di dalamnya kini diturunkan dari __file__)
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import evidence_stack as ES  # noqa: E402
import flow_cluster_test as FC  # noqa: E402
import prices as PR  # noqa: E402

# signature `build_events` berubah (satu tempat untuk deret harga + aturan satu-sumber); alat lama
# yang dipromosikan ikut disesuaikan, bukan dibiarkan memanggil API usang
tx, pxs = ES.load()
ev, _ = ES.build_events(tx, {PR.SRC_GMGN: {"rows": pxs}}, 30, 15, (PR.SRC_GMGN,))
LULUS = ["cluster_ge2", "cluster_ge3", "repeat_maker", "money_spread", "buy_usd_ge_1k"]


def show(r):
    if r.get("status"):
        print("%-34s %s" % (r["fitur"], r["status"]))
        return
    print("%-34s token=%-4d n=%-4d med %+9.1f CI [%+8.1f; %+9.1f] positif %5.1f%% p=%.4f"
          % (r["fitur"], r["token"], r["n"], r["median_selisih_bps"], r["ci_lo"], r["ci_hi"],
             r["proporsi_positif"], r["p"]))


CASES = [
    ("stack lulus termasuk fresh", lambda e: sum(1 for f in LULUS + ["fresh_token"] if e.get(f)) >= 2),
    ("stack lulus TANPA fresh", lambda e: sum(1 for f in LULUS if e.get(f)) >= 2),
    ("aliran saja (ge2+repeat+spread)", lambda e: sum(1 for f in ["cluster_ge2", "repeat_maker",
                                                                  "money_spread"] if e.get(f)) >= 2),
    ("ge2 DAN money_spread", lambda e: e.get("cluster_ge2") and e.get("money_spread")),
    ("ge2 DAN money_spread DAN repeat", lambda e: e.get("cluster_ge2") and e.get("money_spread")
                                                  and e.get("repeat_maker")),
    ("ge2 DAN usd1k", lambda e: e.get("cluster_ge2") and e.get("buy_usd_ge_1k")),
    ("money_spread saja", lambda e: e.get("money_spread")),
    ("ge3 TANPA fresh", lambda e: e.get("cluster_ge3") and not e.get("fresh_token")),
    ("fresh DAN ge2", lambda e: e.get("fresh_token") and e.get("cluster_ge2")),
    ("ge2 ATAU money_spread", lambda e: e.get("cluster_ge2") or e.get("money_spread")),
]
for name, pred in CASES:
    show(ES._pair(ev, pred, name))

print()
print("jumlah aspek lulus (tanpa fresh) yang menyala -> median selisih:")
for nfa in range(0, 6):
    show(ES._pair(ev, (lambda k: (lambda e: sum(1 for f in LULUS if e.get(f)) == k))(nfa),
                  "tepat %d aspek" % nfa))

print()
print("absolut (bukan selisih) per kondisi:")
for lab, pred in [("K=1", lambda e: not e.get("cluster_ge2")),
                  ("K>=2", lambda e: e.get("cluster_ge2")),
                  ("K>=2 + spread", lambda e: e.get("cluster_ge2") and e.get("money_spread")),
                  ("fresh", lambda e: e.get("fresh_token"))]:
    xs = [e["net_bps"] for e in ev if pred(e)]
    ys = [e["net_bps"] for e in ev if not pred(e)]
    print("  %-16s n=%-5d med %+9.1f  %% positif %5.1f%% | median lainnya %+9.1f (n=%d)"
          % (lab, len(xs), FC.med(xs), 100.0 * sum(1 for v in xs if v > 0) / max(len(xs), 1),
             FC.med(ys), len(ys)))
print("  cuaca n=%d" % 0)
