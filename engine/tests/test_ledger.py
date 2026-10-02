"""Ledger paper maju (M2): rantai hash, tick ex-ante, settle ex-post = replay yang sama, hari bolong, guard 12 jam, deteksi pemalsuan."""
import copy
import dataclasses
import os
import tempfile
import unittest

from engine import ledger
from engine.data import MarketData
from engine.replay import replay
from engine.series import DAY_MS, Series
from engine.spec import SPECS
from engine.freshness import StaleBars

from .helpers import BNB, BTC, ETH, T0, mk_series, regime_closes

LOCK = "0x" + "ab" * 32
N_DAYS = 160


def spec10():
    """B1 pada tiga aset, N = 10: cukup pendek supaya sinyal berganti sering dalam data sintetik."""
    return dataclasses.replace(SPECS["B1-TREND"], bot_id="LEDG-1", template="B1-TREND", param=10, universe=(BTC, ETH, BNB))


def full_md(n=N_DAYS, funding=0.0001, skip=None):
    perp = {BTC: mk_series(regime_closes(n, 1), T0, skip), ETH: mk_series(regime_closes(n, 2), T0), BNB: mk_series(regime_closes(n, 3), T0)}
    md = MarketData(perp=perp)
    if funding is not None:
        md.funding = {a: {T0 + i * DAY_MS: funding for i in range(n)} for a in perp}
    return md


def bar(d):                       # waktu BUKA bar hari ke-d
    return T0 + d * DAY_MS


def now_after(d, hours=1.0):      # `hours` jam sesudah PENUTUPAN bar hari ke-d
    return bar(d) + DAY_MS + int(hours * 3_600_000)


def known(md, d):                 # data yang sudah ada pada penutupan bar d (point-in-time)
    return md.upto(bar(d))


def new_chain(spec, start_day, now_ms=None):
    g = ledger.make_genesis(spec, LOCK, None, bar(start_day), now_ms or now_after(start_day, 0.5), "uji")
    return [ledger.seal(g, ledger.ZERO)]


def run(spec, md, days, start_day=None, records=None, hours=1.0):
    """Putaran harian tiap hari di `days`, hanya dengan data yang sudah ada saat itu. Mengembalikan rantai penuh."""
    start_day = days[0] if start_day is None else start_day
    chain = records if records is not None else new_chain(spec, start_day)
    for d in days:
        new, _ = ledger.step(spec, known(md, d), now_after(d, hours), chain)
        chain.extend(new)
    return chain


class ChainTests(unittest.TestCase):
    def test_forward_run_builds_a_valid_chain_that_recomputes_from_bars(self):
        sp, md = spec10(), full_md()
        chain = run(sp, md, range(100, 140))
        self.assertEqual(ledger.verify_chain(chain), [])
        self.assertEqual(ledger.verify_against_data(sp, chain, md), [])
        st = ledger.stats(chain)
        self.assertEqual((st["n_tick"], st["n_gap"]), (40, 0))
        self.assertEqual(st["n_settle"], 39)                    # bar 101..139: tiap bar ditutup oleh tick sehari sebelumnya
        self.assertEqual(st["n_unsettled"], 1)                  # tick 139 menunggu bar 140

    def test_settle_equals_the_gate_replay_one_code_path(self):
        sp, md = spec10(), full_md()
        chain = run(sp, md, range(100, 140))
        full = dict(replay(sp, md))                              # satu replay penuh (riwayat sebelum 100 ikut menentukan w_prev)
        settles = {r["bar"]: r["net"] for r in chain if r["type"] == "settle"}
        for b, net in settles.items():
            if b >= bar(102):
                # w dan w_prev dari tick yang sama; replay menjumlahkan lewat himpunan Python, jadi sama sampai galat bit terakhir
                self.assertAlmostEqual(net, full[b], places=13, msg=ledger.date_of(b))
        # bar 101 = bar pertama sesudah tick pertama: "flat sebelum tick pertama" (biaya masuk dihitung) - sama dengan replay dari target terpotong
        from engine.bots import REGISTRY
        tg = [t for t in REGISTRY["B1-TREND"](sp, md) if bar(100) <= t.t <= bar(101)]
        self.assertAlmostEqual(settles[bar(101)], replay(sp, md, tg=tg)[-1][1], places=13)

    def test_tick_is_idempotent_and_never_looks_ahead(self):
        sp, md = spec10(), full_md()
        chain = run(sp, md, range(100, 105))
        n = len(chain)
        new, _ = ledger.step(sp, known(md, 104), now_after(104), chain)       # putaran kedua, jam sama
        self.assertEqual(new, [])
        self.assertEqual(len(chain), n)
        # tick hari 110 dari data lengkap (yang mengintip masa depan) == tick dari data terpotong
        self.assertEqual(ledger.compute_tick(sp, md, bar(110)), ledger.compute_tick(sp, known(md, 110), bar(110)))

    def test_settle_waits_for_funding_instead_of_filling_zero(self):
        sp, md = spec10(), full_md(funding=None)                 # tanpa funding sama sekali
        chain = run(sp, md, range(100, 106))
        self.assertEqual(ledger.stats(chain)["n_settle"], 0)     # tertunda, bukan nol
        self.assertIn("funding", ledger.settle_pending_reason(sp, md, [BTC], bar(101)))
        md2 = full_md()                                          # funding datang belakangan -> putaran berikut menutup yang tertunda
        new, _ = ledger.step(sp, known(md2, 105), now_after(105), chain)
        chain.extend(new)
        self.assertGreater(ledger.stats(chain)["n_settle"], 0)
        self.assertEqual(ledger.verify_chain(chain), [])


class LateDataTests(unittest.TestCase):
    def test_funding_that_arrives_late_does_not_break_recomputation_of_old_ticks(self):
        """Funding hari lalu datang belakangan (zip bulanan): `data_hash` tick lama tidak boleh berubah, sebab target B1 tidak memakai funding."""
        sp = spec10()
        md_full, md_nofund = full_md(), full_md(funding=None)
        chain = run(sp, md_nofund, range(100, 106))                       # tick dibuat saat funding belum ada
        self.assertEqual(ledger.stats(chain)["n_settle"], 0)
        new, _ = ledger.step(sp, known(md_full, 105), now_after(105), chain)   # funding tiba; settle menutup bar yang tertunda
        chain.extend(new)
        self.assertGreater(ledger.stats(chain)["n_settle"], 0)
        self.assertEqual(ledger.verify_against_data(sp, chain, md_full), [])
        probs = ledger.verify_against_data(sp, chain, md_nofund)           # tanpa funding: tick tetap cocok; hanya settle yang butuh funding
        self.assertTrue(probs and all("settle" in p for p in probs), probs)


class GapAndGuardTests(unittest.TestCase):
    def test_missed_day_becomes_a_gap_and_is_never_backfilled(self):
        sp, md = spec10(), full_md()
        chain = run(sp, md, [100, 101, 102])
        chain = run(sp, md, [104, 105, 106, 107], start_day=100, records=chain)      # hari 103 tidak dijalankan
        types = {(r["asof_date"], r["type"]) for r in chain if r["type"] in ("tick", "gap")}
        self.assertIn((ledger.date_of(bar(103)), "gap"), types)
        self.assertNotIn((ledger.date_of(bar(103)), "tick"), types)
        self.assertEqual(ledger.verify_chain(chain), [])
        settled = {r["bar"] for r in chain if r["type"] == "settle"}
        for d in (101, 102, 103):                 # posisi yang dipegang selama bar 103 = tick 102 (ada), turnover dari tick 101 (ada)
            self.assertIn(bar(d), settled, d)
        self.assertNotIn(bar(104), settled)       # posisi bar 104 = tick 103 yang tidak ada
        self.assertNotIn(bar(105), settled)       # tick 104 ada, tetapi tick 103 (turnover) tidak ada dan 104 bukan tick pertama: tak terukur
        for d in (106, 107):                      # tick 105/104 dan 106/105 ada: kontigu lagi
            self.assertIn(bar(d), settled, d)

    def test_late_tick_is_refused_and_recorded_as_gap(self):
        sp, md = spec10(), full_md()
        chain = run(sp, md, [100, 101])
        new, notes = ledger.step(sp, known(md, 102), now_after(102, hours=13), chain)    # 13 jam > batas 12 jam
        self.assertEqual([r["type"] for r in new if r["type"] != "settle"], ["gap"])      # settle bar 102 (tick 101) tetap sah dan ikut
        self.assertEqual(new[0]["asof"], bar(102))
        chain.extend(new)
        self.assertEqual(ledger.verify_chain(chain), [])

    def test_stale_bars_within_deadline_leave_no_record_and_retry_later(self):
        sp, md = spec10(), full_md()
        chain = run(sp, md, [100, 101])
        stale = known(md, 101)                                   # data berhenti di bar 101 padahal bar 102 sudah tertutup
        new, notes = ledger.step(sp, stale, now_after(102, hours=2), chain)
        self.assertEqual(new, [])
        self.assertTrue(any("DITOLAK" in n for n in notes))
        new, _ = ledger.step(sp, known(md, 102), now_after(102, hours=5), chain)         # data tiba, masih < 12 jam
        self.assertEqual([r["type"] for r in new][:1], ["tick"])

    def test_asset_dropping_out_of_the_feed_is_refused(self):
        sp, md = spec10(), full_md()
        chain = run(sp, md, [100, 101])
        pit = known(md, 102)
        pit.perp[ETH] = pit.perp[ETH].upto(bar(101))             # ETH berhenti di bar 101 sementara BTC/BNB sampai 102
        new, notes = ledger.step(sp, pit, now_after(102), chain)
        self.assertEqual([r for r in new if r["type"] in ("tick", "gap")], [])        # tidak ada tick/gap: coba lagi nanti
        self.assertTrue(any("aset hilang" in n for n in notes))

    def test_bars_before_the_genesis_start_are_not_ticked(self):
        sp, md = spec10(), full_md()
        chain = new_chain(sp, 120)
        new, notes = ledger.step(sp, known(md, 110), now_after(110), chain)
        self.assertEqual(new, [])                                # bar 110 < first_asof 120: bukan gap, bukan tick

    def test_spec_change_after_genesis_is_refused(self):
        sp, md = spec10(), full_md()
        chain = run(sp, md, [100, 101])
        other = dataclasses.replace(sp, param=11)
        with self.assertRaises(ledger.LedgerError):
            ledger.make_tick(other, known(md, 102), now_after(102), chain[0])


class TamperTests(unittest.TestCase):
    def setUp(self):
        self.sp, self.md = spec10(), full_md()
        self.chain = run(self.sp, self.md, range(100, 112))

    def test_editing_a_record_breaks_its_hash(self):
        c = copy.deepcopy(self.chain)
        tick = next(r for r in c if r["type"] == "tick")
        tick["targets"] = {BTC: 1.0}
        self.assertTrue(any("hash tidak cocok" in p for p in ledger.verify_chain(c)))

    def test_removing_or_reordering_records_breaks_the_link(self):
        c = copy.deepcopy(self.chain)
        del c[3]
        self.assertTrue(any("prev tidak menyambung" in p for p in ledger.verify_chain(c)))
        c2 = copy.deepcopy(self.chain)
        c2[3], c2[4] = c2[4], c2[3]
        self.assertTrue(ledger.verify_chain(c2))

    def test_resealing_an_edited_record_still_fails_the_link_of_the_next(self):
        c = copy.deepcopy(self.chain)
        i = 4
        c[i]["lag_s"] = 5
        c[i]["h"] = ledger.record_hash(c[i])                     # penyerang menghitung ulang hash catatan yang diubah
        probs = ledger.verify_chain(c)
        self.assertTrue(any("prev tidak menyambung" in p for p in probs))        # catatan berikutnya menunjuk hash lama

    def test_late_tick_cannot_be_smuggled_in_with_a_valid_hash(self):
        c = copy.deepcopy(self.chain)
        t = next(r for r in c if r["type"] == "tick")
        t["lag_s"] = ledger.MAX_LAG_S + 1
        probs = ledger.verify_chain(c)
        self.assertTrue(any("lag_s" in p for p in probs))

    def test_altering_a_historical_bar_is_caught_by_recompute(self):
        md2 = copy.deepcopy(self.md)
        s = md2.perp[BTC]
        rows = [[s.t[i], s.o[i] if hasattr(s, "o") else s.c[i], s.c[i], s.c[i], s.c[i] * (1.5 if i == 105 else 1.0), 1.0] for i in range(len(s))]
        md2.perp[BTC] = Series.from_rows(rows)
        probs = ledger.verify_against_data(self.sp, self.chain, md2)
        self.assertTrue(any("data_hash BEDA" in p for p in probs), probs[:3])


class FileTests(unittest.TestCase):
    def test_append_and_load_roundtrip_lf_only(self):
        sp = spec10()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "x", "LEDG-1.jsonl")
            g = ledger.seal(ledger.make_genesis(sp, LOCK, None, bar(100), now_after(100)), ledger.ZERO)
            ledger.append(path, g, [])
            recs = ledger.load(path)
            self.assertEqual(recs, [g])
            with open(path, "rb") as f:
                raw = f.read()
            self.assertNotIn(b"\r", raw)
            self.assertTrue(raw.endswith(b"\n"))

    def test_append_refuses_a_record_that_does_not_extend_the_head(self):
        sp = spec10()
        g = ledger.seal(ledger.make_genesis(sp, LOCK, None, bar(100), now_after(100)), ledger.ZERO)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "a.jsonl")
            ledger.append(path, g, [])
            bad = ledger.seal({"type": "gap", "bot_id": sp.bot_id, "asof": bar(100), "asof_date": "x", "reason": "r", "noted_utc": "t"}, ledger.ZERO)
            with self.assertRaises(ledger.LedgerError):
                ledger.append(path, bad, [g])                     # prev nol, bukan ujung rantai
            forged = dict(ledger.seal({"type": "gap", "bot_id": sp.bot_id, "asof": bar(100), "asof_date": "x", "reason": "r", "noted_utc": "t"}, g["h"]))
            forged["reason"] = "diubah"
            with self.assertRaises(ledger.LedgerError):
                ledger.append(path, forged, [g])                  # hash tidak cocok isi

    def test_load_refuses_a_garbage_line(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "a.jsonl")
            with open(path, "wb") as f:
                f.write(b'{"type":"genesis"}\nINI BUKAN JSON\n')
            with self.assertRaises(ledger.LedgerError):
                ledger.load(path)

    def test_genesis_needs_a_day_aligned_first_bar(self):
        with self.assertRaises(ValueError):
            ledger.make_genesis(spec10(), LOCK, None, bar(100) + 1, now_after(100))


if __name__ == "__main__":
    unittest.main()
