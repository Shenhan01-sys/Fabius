"""P85: skor maju + statistik berpasangan dari ledger paper (engine/forward.py) dan sambungannya ke `slots.decide`. Ledger sintetis (tick + settle)."""
import datetime as dt
import unittest

from engine import forward, slots
from engine.book import genesis_book
from engine.spec import SPECS

D = 86_400_000
T0 = int(dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)


def ledger(bot, nets, first=T0):
    """nets[i] = net settle bar ke-(i+1) sesudah `first`; None = hari itu tidak ditutup (tak terukur)."""
    recs = [{"type": "genesis", "bot_id": bot, "first_asof": first}]
    for i, net in enumerate(nets):
        bar = first + (i + 1) * D
        recs.append({"type": "tick", "asof": bar - D, "signal_ids": [f"0x{i:04x}"]})
        if net is not None:
            recs.append({"type": "settle", "bar": bar, "net": net})
    return recs


def wob(n, mean, amp):
    pat = (amp, -amp, 0.5 * amp, -0.5 * amp)
    return [mean + pat[i % 4] for i in range(n)]


class ForwardTests(unittest.TestCase):
    def test_no_settles_is_unmeasured_not_zero(self):
        st = forward.stats_for("B1", ledger("B1", []), T0 + 10 * D)
        self.assertEqual((st.score_bps, st.shadow_score_bps, st.n_settle, st.shadow_days), (None, None, 0, 10))

    def test_full_window_score_is_sum_in_bps(self):
        recs = ledger("B1", [0.001] * 90)
        end = forward.common_end({"B1": recs}, 0)
        st = forward.stats_for("B1", recs, end)
        self.assertEqual(st.covered_days, 90)
        self.assertAlmostEqual(st.score_bps, 900.0, places=6)
        self.assertAlmostEqual(st.shadow_score_bps, 900.0, places=6)

    def test_low_coverage_gives_no_score(self):
        nets = [0.001 if i % 3 else None for i in range(90)]               # 60 dari 90 hari ditutup < 80 %
        st = forward.stats_for("B1", ledger("B1", nets), T0 + 90 * D)
        self.assertEqual(st.covered_days, 60)
        self.assertIsNone(st.score_bps)

    def test_paired_same_days_gap_and_sign(self):
        led = {"A": ledger("A", wob(90, 0.0010, 0.002)), "B": ledger("B", wob(90, 0.0005, 0.002))}
        pt = forward.paired_table(led, forward.common_end(led, 0))
        gap, t = pt[("A", "B")]
        self.assertAlmostEqual(gap, 450.0, places=4)
        self.assertGreater(t, 2.0)
        self.assertAlmostEqual(pt[("B", "A")][0], -450.0, places=4)

    def test_common_end_is_latest_settle_or_fallback(self):
        led = {"A": ledger("A", [0.0] * 5), "B": ledger("B", [0.0] * 9)}
        self.assertEqual(forward.common_end(led, 123), T0 + 9 * D)
        self.assertEqual(forward.common_end({"A": ledger("A", [])}, 123), 123)

    def test_fields_feed_slots_decide(self):
        """Penantang Fabius (B3) dengan shadow 70 hari positif masuk slot kosong; dengan shadow 30 hari ditolak - keputusan tetap milik `slots`."""
        b3 = SPECS["B3-CARRY"]
        now_s = (T0 + 70 * D) // 1000
        book = genesis_book(now_s - 100 * 86_400)

        def challenger(n_days):
            led = {"B1-TREND": ledger("B1-TREND", [0.0005] * n_days), "B3-CARRY": ledger("B3-CARRY", [0.001] * n_days)}
            f = forward.challenger_fields("B3-CARRY", led, ["B1-TREND"], forward.common_end(led, 0))
            return slots.Challenger(bot_id="B3-CARRY", issuer=slots.FABIUS, spec_sha=b3.sha(), fingerprint=b3.fingerprint(), gate_verdict="LOLOS_SHADOW",
                                    report_sha="0x" + "ab" * 32, book_sha=slots.book_sha(book), payout="", **f)

        self.assertEqual(slots.decide(book, challenger(70), now_s).action, slots.ADMIT)
        d = slots.decide(book, challenger(30), now_s)
        self.assertEqual(d.action, slots.REJECT)
        self.assertIn("shadow maju baru 30 hari", d.reason)


if __name__ == "__main__":
    unittest.main()
