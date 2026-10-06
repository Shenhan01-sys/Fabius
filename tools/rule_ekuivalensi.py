"""P167a (epik 12 §3.1): bukti ekuivalensi. B1-TREND, B6-BOUNCE, B2-RS dinyatakan ulang sebagai aturan JSON (`kind=rule`) harus menghasilkan bobot
dan PnL IDENTIK dengan bot template pada SELURUH `ledger/bars` (data nyata, termasuk bolong data). Mencetak per konfigurasi: hari, hari berposisi,
bobot identik, PnL identik; kode keluar 0 hanya bila SEMUANYA identik. Aturan yang diuji = fungsi bantu tes (`engine/tests/test_rule.py`).

Pakai:  python -X utf8 tools/rule_ekuivalensi.py [--bars ledger/bars]
"""
from __future__ import annotations

import argparse
import dataclasses
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine import cli, rule as R                                           # noqa: E402
from engine.bots import REGISTRY                                            # noqa: E402
from engine.data import load_csv_dir                                        # noqa: E402
from engine.replay import replay                                            # noqa: E402
from engine.spec import SPECS                                              # noqa: E402
from engine.tests.test_rule import rule_b1, rule_b2, rule_b6, spec_of       # noqa: E402

KASUS = (("B1-TREND", rule_b1, (60, 30, 90)), ("B6-BOUNCE", rule_b6, (10, 20)), ("B2-RS", rule_b2, (28, 14)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bars", default=os.path.join(ROOT, "ledger", "bars"))
    a = ap.parse_args()
    md = load_csv_dir(a.bars, cli.DATA_SYMBOLS)
    print(f"data: {len(md.perp)} aset perp, {len(md.perp['BTCUSDT'])} bar BTC")
    ok = True
    for bid, mk, params in KASUS:
        for p in params:
            base = dataclasses.replace(SPECS[bid], param=p)
            sp = spec_of(mk(p), universe=base.universe)
            ta, tb = REGISTRY[base.method](base, md), REGISTRY[R.RULE_METHOD](sp, md)
            same_t = [t.t for t in ta] == [t.t for t in tb]
            beda = sum(1 for x, y in zip(ta, tb) if x.weights != y.weights)
            posisi = sum(1 for t in ta if t.weights)
            pnl = replay(base, md, ta) == replay(sp, md, tb)
            good = same_t and beda == 0 and pnl and posisi > 0
            ok = ok and good
            print(f"{bid:10} param {p:3} | {len(ta)} hari | berposisi {posisi} | hari beda bobot {beda} | PnL identik {'ya' if pnl else 'TIDAK'} | {'IDENTIK' if good else 'BEDA'}")
    print("VONIS:", "IDENTIK pada semua konfigurasi" if ok else "ADA YANG BEDA")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
