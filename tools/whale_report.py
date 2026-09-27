"""Readout status smart-money/whale hari ini — dari artefak + rekaman, bukan dari ingatan.

Kenapa alat ini ada: pertanyaan "gimana soal whale-nya?" sudah tiga kali dijawab dari ingatan sesi,
dan setiap kali angka yang keluar perlu diperiksa ulang. Jadi jawaban atas pertanyaan itu harus bisa
dicetak: artefak `decisions/whale-sweep-90d.json` (uji horison panel via Dune) + kesehatan perekam
⑦ (breadth maker, umur aliran, jangkauan ke kandidat kita).

Yang membuat bacaan ini jujur, dan itu bagian utamanya:
  - `cost_bps_applied` dicetak PALING AWAL. Kalau nol, semua angka horison di bawah adalah GROSS.
  - `note_ongkos` dari artefak ikut dicetak, bukan diringkas.
  - umur aliran ⑦ dan jendela yang baru terisi dilaporkan: uji prospektif belum bisa disimpulkan.

Pakai:  python -X utf8 tools/whale_report.py [--json]
"""
import collections
import glob
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if not os.path.isfile(os.path.join(ROOT, "foundry.toml")):
    sys.exit(f"ROOT bukan akar Fabius: {ROOT}")

ART = os.path.join(ROOT, "decisions", "whale-sweep-90d.json")
FLOW = os.path.join(ROOT, "universe", "wallet-flow.jsonl")
UNIV = os.path.join(ROOT, "universe", "bsc-universe.jsonl")


def last_snapshot_utc():
    last = None
    if os.path.isfile(UNIV):
        for line in io.open(UNIV, encoding="utf-8", errors="replace"):
            if line.strip():
                last = line.strip()
    try:
        return json.loads(last or "{}").get("snapshot_utc"), json.loads(last or "{}").get("rows") or []
    except json.JSONDecodeError:
        return None, []


def main():
    as_json = "--json" in sys.argv
    out = {}

    if os.path.isfile(ART):
        d = json.load(io.open(ART, encoding="utf-8"))
        out["sweep"] = {k: d.get(k) for k in ("wallets_n", "cost_bps_applied", "note_ongkos",
                                             "horizons", "generated_utc", "prereg")}
        out["sweep_rows"] = d.get("rows") or []
    else:
        out["sweep"] = None

    makers = collections.Counter()
    tags = collections.Counter()
    tmin = tmax = None
    if os.path.isfile(FLOW):
        for line in io.open(FLOW, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("k") != "tx":
                continue
            makers[r.get("m")] += 1
            for g in (r.get("g") or [])[:1]:
                tags[g] += 1
            t = r.get("t")
            if isinstance(t, (int, float)):
                tmin = t if tmin is None else min(tmin, t)
                tmax = t if tmax is None else max(tmax, t)
    n = sorted(makers.values(), reverse=True)
    snap_utc, rows = last_snapshot_utc()
    snap_epoch = time.mktime(time.strptime(snap_utc, "%Y-%m-%dT%H:%M:%SZ")) - time.timezone if snap_utc else None
    win = 24 * 3600
    recent = collections.Counter()
    if snap_epoch and os.path.isfile(FLOW):
        for line in io.open(FLOW, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("k") == "tx" and snap_epoch - win <= (r.get("t") or 0) <= snap_epoch:
                recent[r.get("m")] += 1
    out["recorder"] = {
        "tx_total": sum(n), "maker_unik": len(makers),
        "maker_ge20": sum(1 for v in n if v >= 20), "maker_ge40": sum(1 for v in n if v >= 40),
        "maker_ge100": sum(1 for v in n if v >= 100),
        "rentang_jam": round((tmax - tmin) / 3600, 2) if (tmin and tmax) else None,
        "umur_aliran_jam": round((snap_epoch - tmax) / 3600, 2) if (snap_epoch and tmax) else None,
        "maker_24j_terakhir": len(recent), "tx_24j_terakhir": sum(recent.values()),
        "top_tag": dict(tags.most_common(4)),
    }
    out["universe"] = {"snapshot_utc": snap_utc, "simbol": [str(r.get("symbol")) for r in rows]}

    if as_json:
        print(json.dumps(out, indent=1, sort_keys=True, ensure_ascii=False))
        return

    s = out["sweep"] or {}
    print(f"### artefak uji horison panel (Dune) — dibuat {s.get('generated_utc')}")
    print(f"  ongkos yang dipakai: {s.get('cost_bps_applied')} bps   <-- kalau 0, SEMUA angka di bawah GROSS")
    print(f"  catatan artefak: {s.get('note_ongkos')}")
    print(f"  panel: {s.get('wallets_n')} dompet | praregistrasi: {s.get('prereg')}")
    print(f"  {'horizon':9} {'n':>7} {'panel':>9} {'base':>9} {'selisih':>10} {'p_boot':>8} "
          f"{'median':>9} {'buang1%':>9} {'top1%':>9}")
    for r in out.get("sweep_rows") or []:
        def f(k):
            v = r.get(k)
            return v if isinstance(v, (int, float)) else 0.0
        print(f"  {str(r.get('horizon')):9} {f('n_panel'):7.0f} {f('panel_bps'):+9.1f} "
              f"{f('base_bps'):+9.1f} {f('diff_bps'):+10.1f} {str(r.get('p_boot')):>8} "
              f"{f('panel_median_bps'):+9.1f} {f('tanpa_top1pct_bps'):+9.1f} {f('top1pct_bps'):+9.1f}")

    rc = out["recorder"]
    print(f"\n### perekam ⑦ (jalur kami sendiri, point-in-time)")
    print(f"  tx {rc['tx_total']:,} | maker unik {rc['maker_unik']} | >=20 tx {rc['maker_ge20']} | "
          f">=40 tx {rc['maker_ge40']} | >=100 tx {rc['maker_ge100']}")
    print(f"  rentang aliran {rc['rentang_jam']} jam | umur tail terakhir {rc['umur_aliran_jam']} jam | "
          f"jendela 24j: {rc['tx_24j_terakhir']:,} tx dari {rc['maker_24j_terakhir']} maker")
    print(f"  tag dominan: {rc['top_tag']}")
    print(f"  universe {out['universe']['snapshot_utc']}: {len(out['universe']['simbol'])} simbol")
    print("\n  Bacaan yang sah: uji horison di atas GROSS dan panelnya dipilih GMGN setelah sejarahnya")
    print("  ada (batas lookahead), jadi ia belum bisa dipakai menjual 'whale pintar'. Jendela 24 jam")
    print("  dari perekam kami baru terisi ~1 hari - Uji A prospektif belum punya bahan untuk disimpulkan.")


if __name__ == "__main__":
    main()
