"""P107: terjemahan terstruktur pembunuh B1/B3 (engine/pembunuh.py) - dinilai pada ledger sintetis yang hasilnya diketahui, plus kunci dan kaitan ke buku."""
import os
import random
import tempfile
import unittest

from engine import pembunuh as pb
from engine.data import MarketData
from engine.series import DAY_MS, Series

D0 = 1_767_225_600_000                      # 2026-01-01T00:00Z
ASSETS = ("BTCUSDT", "ETHUSDT")


def md_with(returns_by_day):
    """Deret perp dua aset dengan return harian yang ditentukan (sama untuk keduanya)."""
    rows, c = [], 100.0
    for k, r in enumerate(returns_by_day):
        c *= 1.0 + r
        rows.append([D0 + k * DAY_MS, c, c, c, c, 1.0])
    s = Series.from_rows(rows)
    return MarketData(perp={a: s for a in ASSETS})


def settles(nets, start=1, n_held=1):
    return [{"type": "settle", "bar": D0 + (start + k) * DAY_MS, "net": v, "n_held": n_held} for k, v in enumerate(nets)]


K1 = {"id": "B1-K1", "jenis": "patokan_bh", "jendela_hari": 40, "cakupan_min": 0.9, "patokan": "bh_sama_rata_universe", "aturan": "-"}
K2 = {"id": "B1-K2", "jenis": "placebo_geser", "jendela_hari": 60, "cakupan_min": 0.9, "n": 200, "geser_min": 10, "aturan": "-"}
K3 = {"id": "B3-K1", "jenis": "bulan_aktif_negatif_beruntun", "bulan": 3, "hari_aktif_min": 10, "aturan": "-"}
K4 = {"id": "B3-K2", "jenis": "kejadian_eksekusi", "kejadian": "ADL pada kaki perp", "batas": 1, "aturan": "-"}


class PatokanTests(unittest.TestCase):
    def setUp(self):
        rng = random.Random(3)
        self.bh = [rng.gauss(0.001, 0.03) for _ in range(60)]
        self.md = md_with(self.bh)
        self.end = D0 + 45 * DAY_MS

    def test_bot_that_beats_buy_and_hold_on_both_is_not_killed(self):
        nets = [0.5 * r + 0.002 for r in self.bh[1:46]]                 # setengah risiko, lebih banyak hasil
        st, det = pb.eval_patokan_bh(pb.SPECS["B1-TREND"], settles(nets), self.md, K1, self.end)
        self.assertEqual(st, pb.TIDAK, det)

    def test_bot_that_loses_on_sharpe_or_mdd_is_killed(self):
        nets = [1.5 * r - 0.002 for r in self.bh[1:46]]
        st, det = pb.eval_patokan_bh(pb.SPECS["B1-TREND"], settles(nets), self.md, K1, self.end)
        self.assertEqual(st, pb.TERPICU, det)

    def test_better_sharpe_but_deeper_drawdown_is_still_killed(self):
        """Tafsir ketat "mengalahkan buy&hold pada MDD DAN Sharpe": menang satu saja tidak cukup."""
        nets = [2.0 * r + 0.004 for r in self.bh[1:46]]
        bot = pb.eval_patokan_bh(pb.SPECS["B1-TREND"], settles(nets), self.md, K1, self.end)
        self.assertEqual(bot[0], pb.TERPICU, bot[1])
        sb, sk = (float(x) for x in bot[1].split(";")[0].replace("Sharpe", "").split("vs"))
        self.assertGreater(sb, sk)                                      # Sharpe memang menang - yang kalah MDD

    def test_short_window_is_not_enough_data_to_kill_or_to_save(self):
        st, det = pb.eval_patokan_bh(pb.SPECS["B1-TREND"], settles([0.01] * 20, start=26), self.md, K1, self.end)
        self.assertEqual(st, pb.BELUM, det)


class PlaceboTests(unittest.TestCase):
    """Placebo geser-melingkar pada tick maju: bot yang tahu hari naik mengalahkan placebo; bot yang memegang tepat sebelum hari turun kalah."""

    def setUp(self):
        rng = random.Random(5)
        self.r = [rng.choice((0.02, -0.02)) for _ in range(80)]
        self.md = md_with(self.r)
        self.end = D0 + 70 * DAY_MS

    def ledger(self, good: bool):
        recs = []
        for k in range(8, 70):
            nxt = self.r[k + 1]                                         # return bar berikutnya = yang dipegang tick ini
            hold = (nxt > 0) if good else (nxt < 0)
            recs.append({"type": "tick", "asof": D0 + k * DAY_MS, "targets": {a: (0.5 if hold else 0.0) for a in ASSETS}})
        recs += settles([0.0] * 62, start=9)
        recs.append({"type": "settle", "bar": self.end, "net": 0.0, "n_held": 1, "h": "0x" + "12" * 32})
        return recs

    def test_perfect_timing_beats_the_placebo(self):
        st, det = pb.eval_placebo_geser(pb.SPECS["B1-TREND"], self.ledger(True), self.md, K2, self.end)
        self.assertEqual(st, pb.TIDAK, det)

    def test_holding_into_down_days_loses_to_the_placebo(self):
        st, det = pb.eval_placebo_geser(pb.SPECS["B1-TREND"], self.ledger(False), self.md, K2, self.end)
        self.assertEqual(st, pb.TERPICU, det)


class BulanAktifTests(unittest.TestCase):
    def month_settles(self, month_index, nets, n_held=1):
        start = [0, 31, 59, 90, 120][month_index]                       # Jan..Mei 2026
        return settles(nets, start=start, n_held=n_held)

    def test_three_negative_active_months_kill_and_dormant_months_are_skipped(self):
        recs = (self.month_settles(0, [-0.001] * 12) + self.month_settles(1, [0.0] * 20, n_held=0)        # Feb dorman: dilewati
                + self.month_settles(2, [-0.001] * 12) + self.month_settles(3, [-0.002] * 15))
        end = D0 + 125 * DAY_MS                                                                              # Mei berjalan: tidak dihitung
        st, det = pb.eval_bulan_aktif(recs, K3, end)
        self.assertEqual(st, pb.TERPICU, det)
        self.assertNotIn("2026-02", det)

    def test_one_positive_month_among_the_last_three_saves_the_bot(self):
        recs = self.month_settles(0, [-0.001] * 12) + self.month_settles(2, [0.002] * 12) + self.month_settles(3, [-0.002] * 15)
        self.assertEqual(pb.eval_bulan_aktif(recs, K3, D0 + 125 * DAY_MS)[0], pb.TIDAK)

    def test_running_month_and_thin_months_do_not_count(self):
        recs = self.month_settles(0, [-0.001] * 12) + self.month_settles(2, [-0.001] * 5) + self.month_settles(3, [-0.002] * 15)
        self.assertEqual(pb.eval_bulan_aktif(recs, K3, D0 + 100 * DAY_MS)[0], pb.BELUM)


class VerdictAndLockTests(unittest.TestCase):
    def test_adl_is_not_applicable_on_paper_and_counts_once_executions_exist(self):
        self.assertEqual(pb.eval_kejadian(K4, None)[0], pb.TAK_BERLAKU)
        self.assertEqual(pb.eval_kejadian(K4, [{"kejadian": "ADL pada kaki perp"}])[0], pb.TERPICU)
        res = pb.evaluate("B3-CARRY", [], None, D0, [K3, K4])
        self.assertEqual(res["vonis"], "BELUM")                       # tidak berlaku tidak menyelamatkan dan tidak membunuh

    def test_lock_binds_spec_sha_and_text_and_refuses_overwrite(self):
        d = tempfile.mkdtemp()
        path = os.path.join(d, "pembunuh.lock.json")
        self.assertEqual(pb.status(path)["state"], "BELUM_DIKUNCI")
        with self.assertRaises(ValueError):
            pb.write_lock("  ", path=path)
        lock = pb.write_lock("uji", now_iso="2026-10-03T00:00:00Z", path=path)
        self.assertEqual(lock["params"]["bot"]["B1-TREND"]["spec_sha"], pb.SPECS["B1-TREND"].sha())
        self.assertEqual(lock["params"]["bot"]["B3-CARRY"]["teks"], pb.SPECS["B3-CARRY"].pembunuh)
        self.assertEqual(pb.status(path)["state"], "TERKUNCI")
        with self.assertRaises(FileExistsError):
            pb.write_lock("lagi", path=path)
        orig = pb.USULAN["B3-CARRY"][0]["hari_aktif_min"]
        pb.USULAN["B3-CARRY"][0]["hari_aktif_min"] = 5                 # terjemahan digeser sesudah kunci
        try:
            self.assertEqual(pb.status(path)["state"], "MENYIMPANG")
        finally:
            pb.USULAN["B3-CARRY"][0]["hari_aktif_min"] = orig

    def test_repo_lock_matches_the_code(self):
        """Kunci 3 Okt (P107, kata builder): terjemahan atau spesifikasi yang digeser sesudahnya membuat tes ini gagal - geser = keputusan baru + kunci v2."""
        self.assertEqual(pb.status()["state"], "TERKUNCI", pb.status())

    def test_book_keeps_text_killers_until_the_translation_is_locked(self):
        from engine import cli
        from engine.book import genesis_book
        book = genesis_book(0)
        orig = pb.LOCK_FILE
        pb.LOCK_FILE = os.path.join(tempfile.mkdtemp(), "tidak-ada.json")
        try:
            got = cli._book_killers(book, {}, lambda v: None, D0)
        finally:
            pb.LOCK_FILE = orig
        self.assertEqual(set(got.values()), {"TEKS"})


if __name__ == "__main__":
    unittest.main()
