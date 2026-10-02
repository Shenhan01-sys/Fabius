"""P88: F-D16 pada data maju (engine/fd16.py) - diuji dengan ledger sintetis (hanya tick + settle; validasi rantai dikerjakan pemanggil CLI)."""
import datetime as dt
import unittest

from engine import fd16

D = 86_400_000
T0 = int(dt.datetime(2026, 10, 2, tzinfo=dt.timezone.utc).timestamp() * 1000)


def ledger(nets, n_signals=30, head="0xabcdef0123456789"):
    recs = [{"type": "genesis", "bot_id": "X"}]
    per = max(1, n_signals // max(1, len(nets))) if nets else 0
    left = n_signals
    for i, net in enumerate(nets):
        k = min(per, left) if i < len(nets) - 1 else left
        left -= k
        recs.append({"type": "tick", "asof": T0 + i * D, "signal_ids": [f"0x{i:02x}{j:02x}" for j in range(k)]})
        recs.append({"type": "settle", "bar": T0 + (i + 1) * D, "net": net})
    if not nets and n_signals:
        recs.append({"type": "tick", "asof": T0, "signal_ids": [f"0x{j:04x}" for j in range(n_signals)]})
    recs[-1]["h"] = head
    return recs


def wobble(n, mean, amp):
    """Deret deterministik dengan rerata tepat `mean` (pola ±amp berulang, jumlah nol tiap 4 hari)."""
    pat = (amp, -amp, 0.5 * amp, -0.5 * amp)
    return [mean + pat[i % 4] for i in range(n)]


class Fd16Tests(unittest.TestCase):
    def test_empty_forward_ledger_is_not_enough_data(self):
        r = fd16.check({"B1": ledger([], n_signals=0)})[0]
        self.assertEqual(r.vonis, "BELUM CUKUP DATA")
        self.assertIsNone(r.p)

    def test_steady_positive_three_months_passes(self):
        r = fd16.check({"B1": ledger(wobble(90, 0.0005, 0.001))})[0]
        self.assertEqual(r.vonis, "LOLOS", r.alasan)
        self.assertGreater(r.ci_lo_bps, 0)
        self.assertGreater(r.tanpa_bulan_terbaik_bps, 0)
        self.assertTrue(r.bh_lolos)

    def test_positive_only_because_of_best_month_fails_fold(self):
        nets = wobble(30, 0.004, 0.001) + wobble(60, -0.0005, 0.001)      # Okt-awal Nov sangat positif, sisanya negatif
        r = fd16.check({"B1": ledger(nets)})[0]
        self.assertGreater(r.mean_bps, 0)
        self.assertEqual(r.vonis, "TIDAK LOLOS")
        self.assertTrue(any(a.startswith("S4") for a in r.alasan), r.alasan)

    def test_too_few_signals_is_not_enough_data_even_if_profitable(self):
        r = fd16.check({"B1": ledger(wobble(90, 0.0005, 0.001), n_signals=12)})[0]
        self.assertEqual(r.vonis, "BELUM CUKUP DATA")
        self.assertTrue(any(a.startswith("S1") for a in r.alasan))

    def test_bh_across_bots_keeps_strong_and_rejects_null(self):
        res = {r.bot: r for r in fd16.check({"KUAT": ledger(wobble(90, 0.0008, 0.001), head="0x1111111111111111"),
                                              "NOL": ledger(wobble(90, 0.0, 0.001), head="0x2222222222222222")})}
        self.assertEqual(res["KUAT"].vonis, "LOLOS", res["KUAT"].alasan)
        self.assertNotEqual(res["NOL"].vonis, "LOLOS")
        self.assertFalse(res["NOL"].bh_lolos)

    def test_deterministic_for_same_ledger(self):
        a = fd16.check({"B1": ledger(wobble(60, 0.0003, 0.002))})[0]
        b = fd16.check({"B1": ledger(wobble(60, 0.0003, 0.002))})[0]
        self.assertEqual((a.ci_lo_bps, a.ci_hi_bps, a.p), (b.ci_lo_bps, b.ci_hi_bps, b.p))

    def test_bh_step_up(self):
        self.assertEqual(fd16.bh_reject({"a": 0.01, "b": 0.04, "c": 0.5}, 0.10), {"a": True, "b": True, "c": False})
        self.assertEqual(fd16.bh_reject({"a": 0.2, "b": 0.3}, 0.10), {"a": False, "b": False})


class LockTests(unittest.TestCase):
    def test_repo_lock_matches_code(self):
        """Kunci F-D84 di repo = parameter kode sekarang; mengubah satu angka di kode tanpa kunci v2 = MENYIMPANG (tes ini merah)."""
        self.assertEqual(fd16.status()["state"], "TERKUNCI")

    def test_drift_detected_and_overwrite_refused(self):
        import os
        import tempfile
        p = os.path.join(tempfile.mkdtemp(), "fd16.lock.json")
        self.assertEqual(fd16.status(path=p)["state"], "BELUM_DIKUNCI")
        fd16.write_lock("uji", now_iso="2026-01-01T00:00:00Z", path=p)
        self.assertEqual(fd16.status(path=p)["state"], "TERKUNCI")
        self.assertEqual(fd16.status(fd16.Fd16Params(n_sinyal_min=19), path=p)["state"], "MENYIMPANG")
        with self.assertRaises(FileExistsError):
            fd16.write_lock("lagi", path=p)


if __name__ == "__main__":
    unittest.main()
