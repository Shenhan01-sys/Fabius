import dataclasses
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from engine import chain, cli
from engine.data import MarketData, load_csv_dir
from engine.freshness import StaleBars
from engine.replay import replay
from engine.report import summary
from engine.series import DAY_MS
from engine.sinyal import Signal, build_batch, data_fingerprint, diff_signals, ref_prices, signals_at, verify_entry
from engine.spec import SPECS
from engine.target import Target

from .helpers import BNB, BTC, ETH, T0, grow, md_perp, mk_series, walk, write_csvs
from .test_bots import PAXG


class ReplayTests(unittest.TestCase):
    def test_b1_toy_pnl_cost_and_funding(self):
        sp = dataclasses.replace(SPECS["B1-TREND"], param=2, penggaris={"fee_bps_sisi": 10})
        md = md_perp({BTC: grow(10, 0.01)})
        pnl = dict((t, v) for t, v in replay(sp, md))
        day = lambda k: T0 + k * DAY_MS
        self.assertAlmostEqual(pnl[day(2)], 0.0)                 # bobot hari-1 = kosong
        self.assertAlmostEqual(pnl[day(3)], 0.01 - 0.001)        # long dari penutupan hari-2: 1% - 10 bps masuk
        self.assertAlmostEqual(pnl[day(4)], 0.01)                # ditahan: tanpa biaya
        md2 = MarketData(perp=md.perp, funding={BTC: {T0 + k * DAY_MS: 0.0002 for k in range(10)}})
        p2 = dict(replay(sp, md2))
        self.assertAlmostEqual(p2[day(4)], 0.01 - 0.0002)        # sisi long membayar funding positif

    def test_b3_hedged_return_two_legs_and_funding_received(self):
        sp = SPECS["B3-CARRY"]
        n = 12
        perp = {BTC: mk_series(grow(n, 0.01))}
        spot = {BTC: mk_series(grow(n, 0.012))}
        md = MarketData(perp=perp, spot=spot, funding={BTC: {T0 + k * DAY_MS: 0.001 for k in range(n)}})
        pnl = dict(replay(sp, md))
        rs, rp, f = 0.012, 0.01, 0.001
        self.assertAlmostEqual(pnl[T0 + 7 * DAY_MS], 1.0 * (rs - rp + f) - 1.0 * 0.0007 * 2)   # hari pertama berposisi: 2 kaki x 7 bps
        self.assertAlmostEqual(pnl[T0 + 8 * DAY_MS], 1.0 * (rs - rp + f))

    def test_b5_uses_spot_returns_and_weights(self):
        sp = dataclasses.replace(SPECS["B5-CORE-RWA"], param=20)
        md = MarketData(spot={BTC: mk_series(grow(40, 0.01)), PAXG: mk_series(grow(40, 0.0))})
        pnl = dict(replay(sp, md))
        self.assertAlmostEqual(pnl[T0 + DAY_MS], 0.5 * 0.01 + 0.5 * 0.0 - 1.0 * 0.001, places=9)   # hari pertama: turnover masuk 1.0 x 10 bps
        self.assertAlmostEqual(pnl[T0 + 5 * DAY_MS], 0.5 * 0.01, places=9)                          # ditahan 50/50: tanpa biaya

    def test_b4_replay_not_in_m1(self):
        with self.assertRaises(NotImplementedError):
            replay(SPECS["B4-LISTING-FADE"], MarketData())

    def test_summary_known_values(self):
        s = summary([(T0 + i * DAY_MS, 0.001 if i % 2 else 0.0) for i in range(60)])
        self.assertEqual(s["n"], 60)
        self.assertAlmostEqual(s["ann"], 0.0005 * 365)
        self.assertGreater(s["sharpe"], 0)


class SignalTests(unittest.TestCase):
    sp = SPECS["B1-TREND"]

    H0 = "0x" + "00" * 32

    def sig(self, **kw):
        d = dict(v=1, bot_id="B1-TREND", spec_sha=self.sp.sha(), t=T0, asof_utc="2020-01-02T00:00:00Z", asset=BTC,
                 aksi="MASUK_LONG", bobot_lama=0.0, bobot_baru=0.5, harga_ref=100.0, data_hash=self.H0, meta={})
        d.update(kw)
        return Signal(**d)

    def test_id_stable_leaf_binds_salt_and_matches_manual_keccak(self):
        a, b = self.sig(), self.sig()
        self.assertEqual(a.id(), b.id())
        self.assertNotEqual(a.id(), self.sig(asset=ETH).id())
        s1, s2 = b"\x01" * 32, b"\x02" * 32
        self.assertNotEqual(a.leaf(s1), a.leaf(s2))
        self.assertEqual(a.leaf(s1), a.leaf(s1))
        self.assertEqual(a.leaf(s1), chain.keccak256(a.abi() + s1))
        self.assertEqual(a.id(), chain.hex0x(chain.keccak256(a.abi())))
        self.assertNotEqual(chain.hex0x(a.leaf(s1)), a.id())
        with self.assertRaises(ValueError):
            a.leaf(b"\x01" * 31)

    def test_meta_is_informational_not_hashed(self):
        self.assertEqual(self.sig(meta={"N": 60}).id(), self.sig(meta={"N": 5, "x": 1}).id())

    def test_abi_struct_fields_and_scaling(self):
        s = self.sig(bobot_lama=-0.333333333, bobot_baru=0.5, harga_ref=77634.6, aksi="KELUAR", asset="NEARUSDT")
        f = s.abi_fields()
        self.assertEqual(f[0], 1)
        self.assertEqual(f[3], (T0 + DAY_MS) // 1000)
        self.assertEqual(f[4], chain.ascii32("NEARUSDT"))
        self.assertEqual(f[5], 3)
        self.assertEqual((f[6], f[7], f[8]), (-333333333, 500000000, 7763460000000))
        self.assertEqual(self.sig(harga_ref=None).abi_fields()[8], 0)
        self.assertEqual(len(s.abi()), 320)

    def test_quantize_once_and_json_roundtrip_is_exact(self):
        mk = lambda w: Target("B2-RS", T0 + DAY_MS, w, {})
        out = diff_signals(SPECS["B2-RS"], None, mk({"A": 1 / 3, "B": -2 / 3}), self.H0, {"A": 0.1 + 0.2})
        a = [s for s in out if s.asset == "A"][0]
        self.assertEqual((a.bobot_baru, a.harga_ref), (0.333333333, 0.3))
        for s in out:
            back = Signal.from_dict(json.loads(json.dumps(s.as_dict())))
            self.assertEqual(back, s)
            self.assertEqual(back.id(), s.id())
            self.assertEqual(back.leaf(b"\x07" * 32), s.leaf(b"\x07" * 32))

    def test_batch_commit_reveal_verify_and_tamper(self):
        sigs = [self.sig(asset=a) for a in (BTC, ETH, BNB)]
        salts = [bytes([i + 1]) * 32 for i in range(3)]
        b = build_batch("B1-TREND", self.sp.sha(), T0, sigs, salts)
        self.assertEqual(len(b.entries), 3)
        self.assertEqual(b.asof(), (T0 + DAY_MS) // 1000)
        for e in b.entries:
            ok, why = verify_entry(e.signal.as_dict(), chain.hex0x(e.salt), [chain.hex0x(p) for p in e.proof], chain.hex0x(b.root))
            self.assertTrue(ok, why)
            bad = dict(e.signal.as_dict(), bobot_baru=0.9)                     # muatan diubah penerbit/perantara
            self.assertFalse(verify_entry(bad, chain.hex0x(e.salt), [chain.hex0x(p) for p in e.proof], chain.hex0x(b.root))[0])
            self.assertFalse(verify_entry(e.signal.as_dict(), "0x" + "99" * 32, [chain.hex0x(p) for p in e.proof], chain.hex0x(b.root))[0])
            self.assertFalse(verify_entry(e.signal.as_dict(), chain.hex0x(e.salt), [chain.hex0x(p) for p in e.proof], "0x" + "11" * 32)[0])
        self.assertFalse(verify_entry({"v": 1}, "0x00", [], "0x00")[0])         # muatan rusak ditolak, tidak melempar
        e0 = b.entries[0]
        args = (chain.hex0x(e0.salt), [chain.hex0x(p) for p in e0.proof], chain.hex0x(b.root))
        for hostile in (float("inf"), float("-inf"), float("nan"), 10 ** 400, 1e300, "abc", None, [1], {"a": 1}):
            ok, why = verify_entry(dict(e0.signal.as_dict(), bobot_baru=hostile), *args)       # inf/nan/raksasa dari penjual: BEDA, bukan traceback
            self.assertFalse(ok, repr(hostile))
        self.assertFalse(verify_entry(dict(e0.signal.as_dict(), harga_ref=float("inf")), *args)[0])
        self.assertFalse(verify_entry(e0.signal.as_dict(), "0x" + "ab" * 31 + "  ", args[1], args[2])[0])       # salt berspasi

    def test_empty_batch_commits_zero_root_and_bad_batches_rejected(self):
        self.assertEqual(build_batch("B1-TREND", self.sp.sha(), T0, [], []).root, b"\x00" * 32)
        s = self.sig()
        with self.assertRaises(ValueError):
            build_batch("B1-TREND", self.sp.sha(), T0, [s, self.sig(asset=ETH)], [b"\x01" * 32, b"\x01" * 32])   # salt kembar
        with self.assertRaises(ValueError):
            build_batch("B2-RS", self.sp.sha(), T0, [s], [b"\x01" * 32])                                          # bot berbeda
        with self.assertRaises(ValueError):
            build_batch("B1-TREND", self.sp.sha(), T0, [s], [])

    def test_diff_enter_exit_flip_reweight(self):
        mk = lambda w, **m: Target("B2-RS", T0 + DAY_MS, w, m)
        prev = Target("B2-RS", T0, {"A": 0.5, "B": -0.5, "C": 0.5, "D": 0.4}, {})
        cur = mk({"A": -0.5, "C": 0.5, "D": 0.45, "E": 0.3, "F": -0.2})
        got = {(s.asset, s.aksi) for s in diff_signals(SPECS["B2-RS"], prev, cur, "0x00", {"E": 7.0})}
        self.assertEqual(got, {("A", "KELUAR"), ("A", "MASUK_SHORT"), ("B", "KELUAR"), ("E", "MASUK_LONG"), ("F", "MASUK_SHORT")})
        e = [s for s in diff_signals(SPECS["B2-RS"], prev, cur, "0x00", {"E": 7.0}) if s.asset == "E"][0]
        self.assertEqual(e.harga_ref, 7.0)
        # perubahan bobot kecil diabaikan kecuali bot menandai rebalance
        self.assertEqual([s.asset for s in diff_signals(SPECS["B2-RS"], prev, cur, "0x00", {}) if s.aksi == "UBAH_BOBOT"], [])
        reb = diff_signals(SPECS["B2-RS"], prev, mk({"A": 0.5, "B": -0.5, "C": 0.5, "D": 0.45}, rebalanced=True), "0x00", {})
        self.assertEqual([(s.asset, s.aksi) for s in reb], [("D", "UBAH_BOBOT")])
        self.assertEqual(diff_signals(SPECS["B2-RS"], prev, prev, "0x00", {}), [])

    def test_first_target_has_no_previous(self):
        out = diff_signals(self.sp, None, Target("B1-TREND", T0, {BTC: 0.5}, {}), "0x00", {BTC: 1.0})
        self.assertEqual([(s.asset, s.aksi) for s in out], [(BTC, "MASUK_LONG")])

    def test_signals_at_point_in_time_and_stale_guard(self):
        sp = dataclasses.replace(self.sp, param=5)
        md = md_perp({BTC: grow(40, 0.01), ETH: grow(40, 0.01)})
        # ETH berbalik turun pada hari ke-30 -> KELUAR; data setelah asof tidak boleh berpengaruh
        eth = grow(40, 0.01)
        for i in range(30, 40):
            eth[i] = eth[29] * (0.97 ** (i - 29))
        md = md_perp({BTC: grow(40, 0.01), ETH: eth})
        t = T0 + 33 * DAY_MS
        a = signals_at(sp, md, t)
        cut = MarketData(perp={k: v.upto(t) for k, v in md.perp.items()})
        b = signals_at(sp, cut, t)
        self.assertEqual([s.id() for s in a], [s.id() for s in b])
        self.assertTrue(all(s.t == t for s in a))
        with self.assertRaises(StaleBars):
            signals_at(sp, cut, T0 + 60 * DAY_MS)                 # data berhenti jauh sebelum asof -> tolak, jangan pakai bar basi

    def test_signals_at_b4_flat_outside_events(self):
        self.assertEqual(signals_at(SPECS["B4-LISTING-FADE"], MarketData(), T0), [])

    def test_fingerprint_ignores_irrelevant_assets_but_tracks_data(self):
        sp = self.sp
        base = md_perp({BTC: walk(30, 1)})
        h0 = data_fingerprint(sp, base)
        extra = md_perp({BTC: walk(30, 1)})
        extra.perp["NOTINUNIVERSEUSDT"] = mk_series(walk(30, 2))
        self.assertEqual(h0, data_fingerprint(sp, extra))
        self.assertNotEqual(h0, data_fingerprint(sp, md_perp({BTC: walk(31, 1)})))
        self.assertNotEqual(h0, data_fingerprint(sp, md_perp({BTC: walk(30, 3)})))

    def test_ref_prices_spot_for_b5(self):
        md = MarketData(spot={BTC: mk_series([10.0, 11.0])}, perp={BTC: mk_series([20.0, 22.0])})
        self.assertEqual(ref_prices(SPECS["B5-CORE-RWA"], md, T0 + DAY_MS), {BTC: 11.0})
        self.assertEqual(ref_prices(SPECS["B1-TREND"], md, T0 + DAY_MS), {BTC: 22.0})
        self.assertEqual(ref_prices(SPECS["B1-TREND"], md, T0 + 5 * DAY_MS), {})


class CliTests(unittest.TestCase):
    def run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = cli.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def test_specs_lists_all_six(self):
        rc, out, _ = self.run_cli(["specs"])
        self.assertEqual(rc, 0)
        for b in SPECS:
            self.assertIn(b, out)

    def test_loader_replay_emit_and_stale_guard(self):
        with tempfile.TemporaryDirectory() as d:
            n = 70
            perp = {BTC: grow(n, 0.01), ETH: grow(n, 0.005)}
            write_csvs(d, perp=perp, spot={BTC: grow(n, 0.01), ETH: grow(n, 0.005)}, fund_per_day={BTC: 0.0, ETH: 0.0})
            md = load_csv_dir(d, [BTC, ETH])
            self.assertEqual(len(md.perp[BTC]), n)
            self.assertAlmostEqual(md.funding[BTC][T0], 0.0)
            rc, out, _ = self.run_cli(["replay", "--data", d, "--bot", "B1-TREND"])
            self.assertEqual(rc, 0)
            self.assertIn("B1-TREND", out)
            asof = "2020-03-01"                                   # indeks 60: N=60 terpenuhi, BTC dan ETH sama-sama MASUK_LONG
            seed = "ab" * 32
            rc, out, err = self.run_cli(["emit", "--data", d, "--bot", "B1-TREND", "--asof", asof, "--seed", seed])
            self.assertEqual(rc, 0, err)
            rows = [json.loads(x) for x in out.splitlines() if x.strip()]
            self.assertEqual(len(rows), 3)                        # satu baris batch + dua sinyal
            batch, entries = rows[0]["batch"], rows[1:]
            self.assertEqual((batch["bot_id"], batch["n"]), ("B1-TREND", 2))
            salts = set()
            for r in entries:
                s = Signal.from_dict(r["sinyal"])
                self.assertEqual(r["id"], s.id())
                self.assertEqual(r["leaf"], chain.hex0x(s.leaf(chain.from_hex(r["salt"]))))
                self.assertEqual(r["abi"], chain.hex0x(s.abi()))
                self.assertTrue(verify_entry(r["sinyal"], r["salt"], r["proof"], batch["root"])[0])
                salts.add(r["salt"])
            self.assertEqual(len(salts), 2)                       # salt unik per sinyal meski dari satu benih
            # sisi pembeli lewat CLI: berkas hasil emit diperiksa terhadap akar; muatan diubah -> GAGAL
            path = os.path.join(d, "batch.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                f.write(out)
            rc, vout, _ = self.run_cli(["verify", "--file", path])
            self.assertEqual(rc, 0, vout)
            self.assertIn("2/2 cocok", vout)
            tampered = out.replace('"bobot_baru": 0.5', '"bobot_baru": 0.9')
            self.assertNotEqual(tampered, out)
            with open(path, "w", encoding="utf-8") as f:
                f.write(tampered)
            rc, vout, _ = self.run_cli(["verify", "--file", path])
            self.assertEqual(rc, 1)
            self.assertIn("GAGAL", vout)
            rc, vout, _ = self.run_cli(["verify", "--file", path, "--root", "0x" + "00" * 32])
            self.assertEqual(rc, 1)                               # akar dari chain menimpa baris batch
            with open(path, "w", encoding="utf-8") as f:           # baris sampah dan muatan inf: GAGAL, tanpa traceback
                f.write(out.replace('"bobot_baru": 0.5', '"bobot_baru": Infinity') + "bukan json\n" + '{"sinyal": 5}\n')
            rc, vout, _ = self.run_cli(["verify", "--file", path])
            self.assertEqual(rc, 1)
            self.assertIn("GAGAL", vout)
            self.assertNotIn("Traceback", vout)
            # jam sekarang jauh setelah bar terakhir -> DITOLAK dengan kode 2 dan TANPA sinyal
            rc, out, err = self.run_cli(["emit", "--data", d, "--bot", "B1-TREND", "--now", "2020-06-01T00:00:00Z"])
            self.assertEqual(rc, 2)
            self.assertEqual(out.strip(), "")
            self.assertIn("DITOLAK", err)
            # bar yang masih berjalan tidak dipakai: 'sekarang' = 2 jam setelah bar terakhir DIBUKA -> asof = bar sebelumnya
            last_open = T0 + (n - 1) * DAY_MS
            iso = __import__("datetime").datetime.fromtimestamp((last_open + 2 * 3_600_000) / 1000, __import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            rc, out, err = self.run_cli(["emit", "--data", d, "--bot", "B1-TREND", "--now", iso])
            self.assertEqual(rc, 0, err)
            self.assertIn("sah pada penutupan bar", err)
            for x in out.splitlines():
                if x.strip():
                    row = json.loads(x)
                    t_open = row["sinyal"]["t"] if "sinyal" in row else row["batch"]["asof"] * 1000 - DAY_MS
                    self.assertLess(t_open, last_open)


if __name__ == "__main__":
    unittest.main()
