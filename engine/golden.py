"""Pemeriksaan emas mesin pada data nyata: mencetak ulang SEMUA angka yang dikutip, tidak menyimpan angka bawaan.

    python -X utf8 -m engine.golden --data <dir> [--since 2020-12-01]

Isi: (1) bolong data, (2) ringkasan lima bot yang punya replay (B4 menunggu M2), (3) sensitivitas fase - B2 per hari-minggu
dan B5 per tanggal pembaruan, (4) invarian point-in-time: memotong data di hari D tidak boleh mengubah target di hari D
(deteksi look-ahead). Kode keluar 1 bila invarian gagal.

Konteks 2 Okt 2026: layar pandas melaporkan B2 Sharpe 1.27-1.29 padahal itu Rabu (1 Jan 2020 = Rabu, `i % 7`); hari lain jauh
berbeda. Tabel (3) mencetak ketujuhnya supaya klaim tidak bersandar pada satu undian fase.
"""
from __future__ import annotations

import argparse
import dataclasses
import sys

from .bots import REGISTRY
from .data import load_csv_dir
from .quality import gap_report, missing_days
from .replay import replay
from .report import date_ms, fmt, summary
from .spec import PERP_UNIVERSE, SPECS

SYMS = list(PERP_UNIVERSE) + ["PAXGUSDT", "XAUUSDT"]
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


def _iso(t):
    import datetime as dt
    return dt.datetime.fromtimestamp(t / 1000, dt.timezone.utc).strftime("%Y-%m-%d")


def _with(spec, **konst):
    return dataclasses.replace(spec, konstanta={**spec.konstanta, **konst})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--since", default="2020-12-01")
    a = ap.parse_args(argv)
    md = load_csv_dir(a.data, SYMS)
    since = date_ms(a.since)
    print(f"DATA {a.data}: perp {len(md.perp)} spot {len(md.spot)} funding {len(md.funding)} aset")
    for kind, bag in (("perp", md.perp), ("spot", md.spot)):
        lasts = sorted({_iso(s.t[-1]) for s in bag.values() if len(s)})
        print(f"  {kind}: bar terakhir {lasts}")
    gaps = gap_report(md)
    print(f"  bolong bar harian: {sum(len(v) for v in gaps.values())} di {len(gaps)} seri")
    for k, gs in gaps.items():
        print("   ", k, "; ".join(f"{missing_days(g)} hari ({_iso(g[0])}->{_iso(g[1])})" for g in gs))

    print("\n== RINGKASAN (dalam-sampel, biaya = penggaris spec; B4 menunggu M2) ==")
    pnls = {}
    for b in ("B1-TREND", "B2-RS", "B3-CARRY", "B5-CORE-RWA", "B6-BOUNCE"):
        pnls[b] = replay(SPECS[b], md)
        print(f"{b:12} penuh        {fmt(summary(pnls[b]))}")
        print(f"{'':12} sejak {a.since} {fmt(summary(pnls[b], since))}")

    days = sorted({t for p in pnls.values() for t, _ in p if t >= since})
    maps = {b: dict(p) for b, p in pnls.items()}
    ew = [(t, sum(m.get(t, 0.0) for m in maps.values()) / len(maps)) for t in days]
    print(f"{'EW lima bot':12} sejak {a.since} {fmt(summary(ew))}")
    print(f"{'':12} sejak 2025-01-01 {fmt(summary(ew, date_ms('2025-01-01')))}")
    names = list(maps)
    cors = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            x = [maps[names[i]].get(t, 0.0) for t in days]
            y = [maps[names[j]].get(t, 0.0) for t in days]
            mx, my = sum(x) / len(x), sum(y) / len(y)
            sxy = sum((p - mx) * (q - my) for p, q in zip(x, y))
            sxx = sum((p - mx) ** 2 for p in x)
            syy = sum((q - my) ** 2 for q in y)
            cors.append(sxy / (sxx * syy) ** 0.5 if sxx > 0 and syy > 0 else float("nan"))
    print(f"  korelasi antar-bot (10 pasang): maks {max(cors):+.2f}, rerata {sum(cors) / len(cors):+.2f}")

    print(f"\n== B2-RS sensitivitas hari-rebalance (tranche=1), sejak {a.since} ==")
    sh = []
    for wd in range(7):
        s = summary(replay(_with(SPECS["B2-RS"], tranche=1, rebalance_hari_utc=wd), md), since)
        sh.append(s["sharpe"])
        print(f"  {HARI[wd]:7} Sharpe {s['sharpe']:+.3f}  ann {s['ann'] * 100:+7.1f}%  MDD {s['mdd'] * 100:6.1f}%")
    t7 = summary(replay(SPECS["B2-RS"], md), since)
    print(f"  rentang tujuh hari: {min(sh):+.3f} .. {max(sh):+.3f}, rerata {sum(sh) / 7:+.3f}")
    print(f"  tranche=7 (bawaan mesin, tanpa pilihan hari): Sharpe {t7['sharpe']:+.3f}  ann {t7['ann'] * 100:+7.1f}%  MDD {t7['mdd'] * 100:6.1f}%")
    print(f"\n== B2-RS pindai L tanpa undian fase (tranche=7), sejak {a.since} ==")
    print("  " + "  ".join(
        f"L={L}:{summary(replay(dataclasses.replace(SPECS['B2-RS'], param=L), md), since)['sharpe']:+.2f}"
        for L in (7, 10, 14, 21, 28, 42, 56)))

    print(f"\n== B5-CORE-RWA sensitivitas tanggal pembaruan bulanan, sejak {a.since} ==")
    for d in (1, 5, 10, 15, 20, 25, 28):
        s = summary(replay(_with(SPECS["B5-CORE-RWA"], hari_pembaruan=d), md), since)
        print(f"  tanggal {d:>2}  Sharpe {s['sharpe']:+.3f}  ann {s['ann'] * 100:+6.1f}%  MDD {s['mdd'] * 100:6.1f}%")

    print("\n== INVARIAN POINT-IN-TIME (potong data di D -> target hari D harus sama) ==")
    bad = 0
    for b in ("B1-TREND", "B2-RS", "B3-CARRY", "B5-CORE-RWA", "B6-BOUNCE"):
        sp = SPECS[b]
        full = {t.t: t for t in REGISTRY[b](sp, md)}
        days = sorted(full)
        picks = [days[int(len(days) * q)] for q in (0.3, 0.5, 0.7, 0.9)] + [days[-1]]
        ok = 0
        for t in picks:
            cut = REGISTRY[b](sp, md.upto(t))
            same = bool(cut) and cut[-1].t == t and set(cut[-1].weights) == set(full[t].weights) and all(
                abs(cut[-1].weights[x] - full[t].weights[x]) < 1e-12 for x in full[t].weights)
            ok += same
            if not same:
                bad += 1
                print(f"  GAGAL {b} pada {_iso(t)}")
        print(f"  {b:12} {ok}/{len(picks)} hari identik")
    print("\nSTATUS: USULAN 2 Okt 2026 - tidak ada bot terkunci, tidak ada hasil maju. Angka di atas = dalam-sampel.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
