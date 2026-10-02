"""P98 (tools/rest_latency.py): pencatat jeda + perubahan dan pemilihan tengah malam diuji tanpa jaringan."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import rest_latency as rl                                           # noqa: E402

D = 86_400_000
CLOSE = 1_790_985_600_000                                            # 2026-10-03T00:00:00Z


class TrackerTests(unittest.TestCase):
    def test_first_seen_latency_and_no_change(self):
        tr = rl.Tracker(CLOSE)
        tr.see("perp", "BTCUSDT", None, CLOSE - 5_000)               # belum tertutup: tidak dicatat
        tr.see("perp", "BTCUSDT", (1.0, 2.0, 0.5, 1.5, 9.0), CLOSE + 2_500)
        tr.see("perp", "BTCUSDT", (1.0, 2.0, 0.5, 1.5, 9.0), CLOSE + 17_500)
        self.assertEqual(tr.latency_s("perp"), [2.5])
        self.assertEqual(tr.changes, [])
        self.assertEqual(tr.missing("perp", ["BTCUSDT", "ETHUSDT"]), ["ETHUSDT"])

    def test_change_after_first_seen_is_recorded(self):
        tr = rl.Tracker(CLOSE)
        tr.see("spot", "ETHUSDT", (1.0, 2.0, 0.5, 1.5, 9.0), CLOSE + 1_000)
        tr.see("spot", "ETHUSDT", (1.0, 2.0, 0.5, 1.5, 9.5), CLOSE + 16_000)
        self.assertEqual(len(tr.changes), 1)
        self.assertEqual(tr.changes[0][:3], ("spot", "ETHUSDT", CLOSE + 16_000))
        self.assertTrue(any("perubahan nilai sesudah pertama terlihat: 1" in s for s in tr.summary(["ETHUSDT"])))

    def test_digest_depends_on_final_values_only(self):
        a, b = rl.Tracker(CLOSE), rl.Tracker(CLOSE)
        a.see("funding", "BTCUSDT", (CLOSE, 1e-4), CLOSE + 1_000)
        b.see("funding", "BTCUSDT", (CLOSE, 1e-4), CLOSE + 9_000)
        self.assertEqual(a.digest("funding"), b.digest("funding"))


class ScheduleTests(unittest.TestCase):
    def test_inside_window_measures_today_otherwise_next_midnight(self):
        self.assertEqual(rl.next_close(CLOSE + 5 * 60_000, 10), CLOSE)
        self.assertEqual(rl.next_close(CLOSE + 11 * 60_000, 10), CLOSE + D)
        self.assertEqual(rl.next_close(CLOSE - 7 * 3_600_000, 10), CLOSE)


class PollTests(unittest.TestCase):
    def test_poll_stops_asking_funding_once_seen(self):
        calls = []

        def fake_get(url):
            calls.append(url)
            if "fundingRate" in url:
                return [{"fundingTime": CLOSE + 3, "fundingRate": "0.0001"}]
            return [[CLOSE - D, "1", "2", "0.5", "1.5", "9", CLOSE - 1]]

        rest = rl.Rest(fake_get)
        tr = rl.Tracker(CLOSE)
        rl.poll_once(rest, tr, ["BTCUSDT"], CLOSE - D, lambda: CLOSE + 2_000)
        rl.poll_once(rest, tr, ["BTCUSDT"], CLOSE - D, lambda: CLOSE + 17_000)
        self.assertEqual(sum("fundingRate" in u for u in calls), 1)
        self.assertEqual(tr.first[("funding", "BTCUSDT")][1], (CLOSE + 3, 0.0001))
        self.assertEqual(tr.latency_s("perp"), [2.0])


if __name__ == "__main__":
    unittest.main()
