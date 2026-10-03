"""Mode bayangan tahap 2+3 (tools/shadow_tick.py): tick dari REST dibandingkan dengan tick resmi. Tanpa jaringan.

Skenario utama memakai data repo sungguhan: bar 2026-10-01 dicabut dari salinan `ledger/bars` (seolah zip Vision belum terbit) lalu disajikan oleh
REST tiruan. Bila REST = Vision, tick bayangan harus IDENTIK dengan tick resmi di `ledger/paper`; satu harga beda = BEDA + ALARM baris."""
import csv
import os
import shutil
import sys
import tempfile
import unittest

from engine import funding_est as fest, ledger
from engine.series import DAY_MS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import shadow_tick as st                                            # noqa: E402

BARS = os.path.join(ROOT, "ledger", "bars")
LEDGER = os.path.join(ROOT, "ledger", "paper")
BAR = 1_790_812_800_000                                             # 2026-10-01
CLOSE = BAR + DAY_MS


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def write_rows(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f, lineterminator="\n").writerows(rows)


def official_without_last_day(dst):
    """Salinan ledger/bars tanpa bar 2026-10-01 (kline) dan tanpa estimasi funding hari itu. -> baris yang dicabut, per deret."""
    shutil.copytree(BARS, dst)
    removed = {}
    for name in sorted(os.listdir(dst)):
        p = os.path.join(dst, name)
        rows = read_rows(p)
        if name.startswith(("fut_", "spot_")):
            kind, sym = name.split("_")[0], name.split("_")[1]
            # SEMUA bar sejak BAR dicabut, bukan hanya BAR: ledger/bars repo terus bertambah (rantai GitHub), dan mencabut satu hari di tengah
            # membuat lubang buatan (patah 3 Okt 08:40Z saat bar 2026-10-02 masuk). REST tiruan hanya menyajikan BAR.
            keep = [r for r in rows if not (r and r[0].isdigit() and int(r[0]) >= BAR)]
            removed[f"{kind}:{sym}"] = [(int(r[0]), *map(float, r[1:6])) for r in rows if r and r[0].isdigit() and int(r[0]) == BAR]
        elif name.startswith("fund_est_"):
            sym = name[len("fund_est_"):-4]
            keep = [r for r in rows if not (r and r[0].isdigit() and int(r[0]) >= BAR)]
            removed[f"fest:{sym}"] = [(int(r[0]), float(r[1])) for r in rows if r and r[0].isdigit() and BAR <= int(r[0]) < CLOSE]
        else:
            continue
        write_rows(p, keep)
    return removed


class FakeRest:
    """REST tiruan: menyajikan baris yang dicabut, opsional diubah; `flips` = jumlah bacaan pertama yang memberi close BTC berbeda (bacaan belum final)."""

    def __init__(self, removed, tweak=None, drop=(), flips=0):
        self.removed, self.tweak, self.drop, self.flips = removed, tweak or {}, set(drop), flips
        self.reads = 0

    def klines(self, kind, sym, t_from, now_ms):
        if kind == "fut" and sym == "BTCUSDT":
            self.reads += 1
        key = f"{kind}:{sym}"
        if key in self.drop:
            return []
        out = []
        for r in self.removed.get(key, []):
            if r[0] >= t_from:
                r = list(r)
                if key in self.tweak:
                    r[4] += self.tweak[key]
                if key == "fut:BTCUSDT" and self.reads <= self.flips:
                    r[4] += 0.1 * self.reads
                out.append(tuple(r))
        return out

    def premium(self, sym, t_from, t_to, now_ms):
        return {t: 0.0003 for t in range(t_from, t_to, 60_000)}


class Env:
    def __init__(self, src_kw=None, now=CLOSE + 5 * 60_000):
        self.tmp = tempfile.mkdtemp()
        self.work = os.path.join(self.tmp, "work")
        self.removed = official_without_last_day(os.path.join(self.work, "ledger", "bars"))
        shutil.copytree(LEDGER, os.path.join(self.work, "ledger", "paper"))
        self.src = FakeRest(self.removed, **(src_kw or {}))
        self.logs, self.now = [], now
        est = {k.split(":")[1]: v for k, v in self.removed.items() if k.startswith("fest:")}
        self.sh = st.Shadow(workdir=self.work, state_dir=os.path.join(self.tmp, "state"), src=self.src, log=self.logs.append,
                            sleep=lambda s: None, now_fn=lambda: self.now,
                            est_fn=lambda sym, minutes, d: [r for r in est[sym] if d <= r[0] < d + DAY_MS] or None)

    def vision_publishes(self):
        b = os.path.join(self.work, "ledger", "bars")
        shutil.rmtree(b)
        shutil.copytree(BARS, b)

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class FinalityTests(unittest.TestCase):
    def test_first_reads_that_change_are_not_accepted(self):
        e = Env({"flips": 2})
        try:
            got = st.read_final(e.src, os.path.join(e.work, "ledger", "bars"), BAR, lambda: e.now, lambda s: None, e.logs.append)
            self.assertIsNotNone(got)
            snap, n = got
            self.assertEqual(n, 4)                                  # bacaan 1 dan 2 berubah, 3 = 4 identik
            self.assertEqual(snap["fut:BTCUSDT"][0][4], e.removed["fut:BTCUSDT"][0][4])
            self.assertEqual(sum("beda dari bacaan" in m for m in e.logs), 2)
        finally:
            e.close()

    def test_source_that_never_settles_is_tunda_not_accepted(self):
        e = Env({"flips": 99})
        try:
            self.assertIsNone(st.read_final(e.src, os.path.join(e.work, "ledger", "bars"), BAR, lambda: e.now, lambda s: None, e.logs.append))
            self.assertIn("TUNDA", e.logs[-1])
            self.assertFalse(e.sh.run_day(BAR))
            self.assertEqual(e.sh.state["hari"], {})
        finally:
            e.close()

    def test_due_waits_two_minutes_and_stops_at_the_deadline(self):
        e = Env()
        try:
            self.assertIsNone(e.sh.due(CLOSE + 60_000))
            self.assertEqual(e.sh.due(CLOSE + 121_000), BAR)
            self.assertIsNone(e.sh.due(CLOSE + ledger.MAX_LAG_S * 1000 + 1))
        finally:
            e.close()


class ShadowVsOfficialTests(unittest.TestCase):
    def test_rest_equal_to_vision_gives_a_tick_identical_to_the_official_one_minutes_after_close(self):
        e = Env()
        try:
            self.assertTrue(e.sh.run_day(BAR))
            day = e.sh.state["hari"]["2026-10-01"]
            self.assertTrue(day["uji_rest"])
            self.assertEqual(day["n_baca"], 2)
            for bot in ("B1-TREND", "B3-CARRY"):
                self.assertEqual(day["bot"][bot]["lag_s"], 300)
            out = e.sh.compare_pending()
            self.assertEqual(sorted(x.split(":")[1].strip().split(" ")[0] for x in out if x.startswith("VONIS bayangan")), ["IDENTIK", "IDENTIK"], out)
            self.assertIsNone(day.get("baris_vonis"))                # Vision belum terbit di salinan: baris menunggu
            e.vision_publishes()
            out = e.sh.compare_pending()
            self.assertEqual(day["baris_vonis"], "SAMA", out)
            self.assertIsNone(e.sh.state["hari"]["2026-10-01"]["bot"]["B1-TREND"].get("beda") or None)
            self.assertEqual(e.sh.state["hari"]["2026-10-01"]["bot"]["B1-TREND"]["lag_resmi_s"], 33201)
        finally:
            e.close()

    def test_one_close_different_from_vision_is_beda_and_a_row_alarm(self):
        e = Env({"tweak": {"fut:BTCUSDT": 0.1}})
        try:
            self.assertTrue(e.sh.run_day(BAR))
            e.sh.compare_pending()
            b1 = e.sh.state["hari"]["2026-10-01"]["bot"]["B1-TREND"]
            self.assertEqual(b1["vonis"], "BEDA")
            self.assertIn("data_hash", b1["beda"])
            e.vision_publishes()
            e.sh.compare_pending()
            self.assertEqual(e.sh.state["hari"]["2026-10-01"]["baris_vonis"], "ALARM")
            self.assertTrue(any("! fut BTCUSDT 2026-10-01 c:" in m for m in e.logs), e.logs[-5:])
        finally:
            e.close()

    def test_missing_rest_bar_waits_in_the_first_hour_then_the_tick_decides(self):
        e = Env({"drop": ["fut:ETHUSDT"]})
        try:
            self.assertFalse(e.sh.run_day(BAR))
            self.assertIn("TUNDA", e.logs[-1])
            e.now = CLOSE + 2 * 3600_000
            self.assertTrue(e.sh.run_day(BAR))
            b1 = e.sh.state["hari"]["2026-10-01"]["bot"]["B1-TREND"]
            self.assertIn("aset hilang", b1["tolak"])
            e.sh.compare_pending()
            self.assertEqual(b1["vonis"], "RESMI ADA, BAYANGAN DITOLAK")
        finally:
            e.close()


    def test_when_vision_is_already_in_the_official_bars_the_shadow_says_it_tested_nothing(self):
        e = Env()
        try:
            e.vision_publishes()
            self.assertTrue(e.sh.run_day(BAR))
            self.assertFalse(e.sh.state["hari"]["2026-10-01"]["uji_rest"])
            self.assertTrue(any("TIDAK menguji REST" in m for m in e.logs), e.logs)
            self.assertEqual(e.sh.compare_pending(), [])                     # tidak ada vonis yang bisa dikira bukti (dan tidak ada alert)
        finally:
            e.close()


class FundingRuleTests(unittest.TestCase):
    def test_actual_funding_is_never_written_and_estimates_come_from_rest_minutes(self):
        """SK-R2: hanya estimasi yang ditambahkan (dari menit indeks premium REST, rumus engine); berkas funding AKTUAL tetap byte-per-byte resmi."""
        e = Env()
        try:
            bars = os.path.join(e.work, "ledger", "bars")
            snap = st.read_snapshot(e.src, bars, BAR, e.now)
            rows, probs = st.build_rows(snap, bars, BAR)                # est_fn bawaan = engine.funding_est.estimate_day
            self.assertEqual(probs, [])
            self.assertEqual([t for t, _ in rows["fest:BTCUSDT"]], fest.day_events(BAR))
            self.assertTrue(all(abs(r - 0.0001) < 1e-12 for _, r in rows["fest:BTCUSDT"]))
            self.assertEqual([abs(r) < 1e-12 for _, r in rows["fest:BNBUSDT"]], [True] * 3)
            out = st.make_shadow_bars(bars, rows, os.path.join(e.tmp, "sb"))
            for name in os.listdir(bars):
                if name.startswith("fund_") and not name.startswith("fund_est_"):
                    with open(os.path.join(bars, name), "rb") as a, open(os.path.join(out, name), "rb") as b:
                        self.assertEqual(a.read(), b.read(), name)
            self.assertEqual(len(read_rows(os.path.join(out, "fund_est_BTCUSDT.csv"))), len(read_rows(os.path.join(bars, "fund_est_BTCUSDT.csv"))) + 3)
        finally:
            e.close()


if __name__ == "__main__":
    unittest.main()
