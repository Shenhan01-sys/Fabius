"""tools/paper_tick.py (genesis, kelayakan bot) dan `engine.cli ledger verify|report` (hitung-ulang dari CSV bar)."""
import contextlib
import io
import os
import sys
import tempfile
import unittest

from engine import book, cli, ledger
from engine.data import load_csv_dir
from engine.spec import SPECS

from .helpers import BNB, BTC, ETH, regime_closes, write_csvs
from .test_ledger import LOCK, bar, now_after

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import paper_tick as pt                                          # noqa: E402


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*a, **k)
    return rc, buf.getvalue()


def rd(path, mode="rb"):
    with open(path, mode) as f:
        return f.read()


class EligibilityTests(unittest.TestCase):
    def test_only_the_identity_bot_and_the_gate_passer_may_have_a_forward_clock(self):
        self.assertIn(book.IDENTITY_BOT_ID, book.SHADOW_ELIGIBLE)
        self.assertIn("B3-CARRY", book.SHADOW_ELIGIBLE)
        for b in ("B2-RS", "B4-LISTING-FADE", "B5-CORE-RWA", "B6-BOUNCE"):
            self.assertNotIn(b, book.SHADOW_ELIGIBLE)
        self.assertTrue(set(book.SHADOW_ELIGIBLE) <= set(SPECS))

    def test_all_fabius_bots_may_run_forward_labelled_core_or_provisional_but_the_book_challengers_are_unchanged(self):
        self.assertEqual(set(book.FORWARD_BOTS), set(SPECS))                                   # F-D95
        self.assertEqual(book.STATUS["B1-TREND"], "INTI")
        self.assertTrue(all(book.STATUS[b] == "SEMENTARA" for b in SPECS if b != book.IDENTITY_BOT_ID))
        self.assertEqual(book.GATE_V1["B1-TREND"], "TOLAK")                                    # INTI = pilihan builder, bukan lolos gerbang
        self.assertEqual([b for b, v in book.GATE_V1.items() if v == "LOLOS_SHADOW"], ["B3-CARRY"])

    def test_init_refuses_unknown_bots_and_never_overwrites_an_existing_ledger(self):
        now = now_after(100, 5.0)
        with tempfile.TemporaryDirectory() as d:
            rc, out = quiet(pt.init_bot, "B9-UNKNOWN", d, now, False)
            self.assertEqual(rc, 3)
            self.assertFalse(os.path.exists(os.path.join(d, "B9-UNKNOWN.jsonl")))
            rc, _ = quiet(pt.init_bot, "B2-RS", d, now, False)                                 # F-D95: B2 kini boleh punya jam maju
            self.assertEqual(rc, 0)
            self.assertEqual(ledger.load(os.path.join(d, "B2-RS.jsonl"))[0]["spec_sha"], SPECS["B2-RS"].sha())
            rc, _ = quiet(pt.init_bot, "B1-TREND", d, now, False)
            self.assertEqual(rc, 0)
            recs = ledger.load(os.path.join(d, "B1-TREND.jsonl"))
            self.assertEqual(ledger.verify_chain(recs), [])
            g = recs[0]
            self.assertEqual(g["spec_sha"], SPECS["B1-TREND"].sha())
            self.assertEqual(g["first_asof"], ledger.last_closed_bar(now))             # 5 jam sesudah penutupan: masih dalam batas 12 jam
            before = rd(os.path.join(d, "B1-TREND.jsonl"))
            rc, out = quiet(pt.init_bot, "B1-TREND", d, now, False)
            self.assertEqual(rc, 3)
            self.assertEqual(rd(os.path.join(d, "B1-TREND.jsonl")), before)

    def test_genesis_after_the_deadline_starts_at_the_next_bar(self):
        now = now_after(100, 13.0)                                                       # 13 jam sesudah penutupan bar 100: bar itu sudah terlambat
        with tempfile.TemporaryDirectory() as d:
            rc, _ = quiet(pt.init_bot, "B1-TREND", d, now, False)
            self.assertEqual(rc, 0)
            self.assertEqual(ledger.load(os.path.join(d, "B1-TREND.jsonl"))[0]["first_asof"], bar(101))

    def test_dry_run_init_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            rc, _ = quiet(pt.init_bot, "B1-TREND", d, now_after(100), True)
            self.assertEqual(rc, 0)
            self.assertEqual(os.listdir(d), [])


class CliLedgerTests(unittest.TestCase):
    def build(self, d):
        bars, led = os.path.join(d, "bars"), os.path.join(d, "paper")
        os.makedirs(bars)
        os.makedirs(led)
        perp = {BTC: regime_closes(160, 1), ETH: regime_closes(160, 2), BNB: regime_closes(160, 3)}
        write_csvs(bars, perp, fund_per_day={a: 0.0001 for a in perp})
        md = load_csv_dir(bars, cli.DATA_SYMBOLS)
        sp = SPECS["B1-TREND"]
        chain = [ledger.seal(ledger.make_genesis(sp, LOCK, None, bar(100), now_after(100, 0.5)), ledger.ZERO)]
        for k in range(100, 130):
            new, _ = ledger.step(sp, md.upto(bar(k)), now_after(k), chain)
            chain.extend(new)
        path, so_far = os.path.join(led, "B1-TREND.jsonl"), []
        for r in chain:
            ledger.append(path, r, so_far)
            so_far.append(r)
        return bars, led, path

    def test_verify_passes_then_catches_an_altered_bar_and_an_altered_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            bars, led, path = self.build(d)
            rc, out = quiet(cli.main, ["ledger", "verify", "--ledger", led, "--bars", bars])
            self.assertEqual(rc, 0, out)
            self.assertIn("SAH", out)
            rc, out = quiet(cli.main, ["ledger", "report", "--ledger", led])
            self.assertEqual(rc, 0)
            self.assertIn("LEDGER B1-TREND", out)
            self.assertIn("PERINGATAN", out)                                           # 30 hari: jendela pendek harus diberi peringatan
            # 1) bar diubah sesudah kejadian -> data_hash berbeda
            p = os.path.join(bars, "fut_BTCUSDT_1d.csv")
            lines = rd(p, "r").split("\n")
            cols = lines[110].split(",")
            cols[4] = str(float(cols[4]) * 1.3)
            lines[110] = ",".join(cols)
            with open(p, "w", newline="") as f:
                f.write("\n".join(lines))
            rc, out = quiet(cli.main, ["ledger", "verify", "--ledger", led, "--bars", bars])
            self.assertEqual(rc, 1)
            self.assertIn("BEDA", out)
            # 2) ledger diubah (satu karakter) -> rantai/baca gagal
            os.makedirs(os.path.join(d, "second"))
            bars2, led2, path2 = self.build(os.path.join(d, "second"))
            raw = rd(path2)
            i = raw.index(b'"targets"') + 20
            with open(path2, "wb") as f:
                f.write(raw[:i] + (b"9" if raw[i:i + 1] != b"9" else b"8") + raw[i + 1:])
            rc, out = quiet(cli.main, ["ledger", "verify", "--ledger", led2, "--bars", bars2])
            self.assertEqual(rc, 1)

    def test_verify_without_any_ledger_is_not_ok(self):
        with tempfile.TemporaryDirectory() as d:
            rc, out = quiet(cli.main, ["ledger", "verify", "--ledger", d, "--bars", d])
            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
