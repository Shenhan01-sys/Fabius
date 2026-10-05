"""P152 (F-D109): meja AI 5 menit (tools/meja.py) - format keputusan baku, rumus konsensus terkunci, buku paper dengan fee, siklus yang menghasilkan
rekaman ber-hash + Merkle root. Binance dan model dipalsukan; tidak ada jaringan."""
import json
import os
import sys
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, ROOT)

import meja                                                         # noqa: E402
from engine import chain                                            # noqa: E402

T0 = 1_791_200_100                                                  # kelipatan 300


def jawab(target: dict, ring: str = "trend up, small risk") -> str:
    return "ok:\n" + json.dumps({"ringkasan": ring, "target": target})


class FormatTests(unittest.TestCase):
    def test_a_decision_is_a_full_target_vector_where_omitted_assets_keep_the_previous_target(self):
        prev = {"ETHUSDT": {"w": -0.1, "k": 0.6, "alasan": "x"}}
        d = meja.parse(jawab({"BTCUSDT": {"arah": "long", "ukuran": 0.2, "keyakinan": 70, "alasan": "breakout"},
                              "SOLUSDT": {"arah": "flat", "keyakinan": 50}, "FOOUSDT": {"arah": "long", "ukuran": 0.1, "keyakinan": 50},
                              "XRPUSDT": {"arah": "long", "ukuran": 0.9, "keyakinan": 50}}), prev)
        self.assertEqual(d["target"]["BTCUSDT"], {"w": 0.2, "k": 0.7, "alasan": "breakout"})
        self.assertEqual(d["target"]["SOLUSDT"]["w"], 0.0)
        self.assertEqual(d["target"]["ETHUSDT"]["w"], -0.1)                               # tidak disebut = tahan
        self.assertEqual(sorted(x["aset"] for x in d["ditolak"]), ["FOOUSDT", "XRPUSDT"])  # aset asing, ukuran > 0,25
        self.assertEqual(d["diubah"], ["BTCUSDT", "SOLUSDT"])
        with self.assertRaises(ValueError):
            meja.parse(jawab({}, ring=""), {})                                           # wajib menjelaskan, termasuk saat menahan

    def test_gross_exposure_above_one_is_scaled_down(self):
        t = {a: {"arah": "long", "ukuran": 0.25, "keyakinan": 80} for a in meja.PARAMS["aset"][:8]}
        d = meja.parse(jawab(t), {})
        self.assertAlmostEqual(sum(abs(v["w"]) for v in d["target"].values()), 1.0, places=5)
        self.assertEqual(d["diskala"], 0.5)


class ConsensusTests(unittest.TestCase):
    def test_consensus_is_the_confidence_weighted_average_with_a_quorum_of_two(self):
        a = {"target": {"BTCUSDT": {"w": 0.2, "k": 0.8}, "ETHUSDT": {"w": -0.1, "k": 0.5}}}
        b = {"target": {"BTCUSDT": {"w": 0.1, "k": 0.6}}}
        t, why = meja.konsensus({"a": a, "b": b}, {})
        self.assertAlmostEqual(t["BTCUSDT"]["w"], (0.8 * 0.2 + 0.6 * 0.1) / 2)
        self.assertAlmostEqual(t["ETHUSDT"]["w"], (0.5 * -0.1) / 2)
        self.assertIn("2 agent", why)
        held, why = meja.konsensus({"a": a}, {"SOLUSDT": {"w": 0.05, "k": 1.0}})
        self.assertEqual(held, {"SOLUSDT": {"w": 0.05, "k": 1.0}})                        # 1 < kuorum: tahan
        self.assertIn("kuorum", why)


class BookTests(unittest.TestCase):
    def test_fills_pay_fees_mark_profit_and_skip_changes_below_two_percent(self):
        b = meja.buku_baru()
        f = meja.isi(b, {"BTCUSDT": {"w": 0.2, "k": 1}}, {"BTCUSDT": 100.0})
        self.assertEqual(len(f), 1)
        self.assertAlmostEqual(b["biaya"], 0.0005 * 2000)                                 # 20 % x 10.000 x fee
        self.assertAlmostEqual(meja.ekuitas(b, {"BTCUSDT": 110.0}), 10_000 - 1 + 200)     # +10 % pada 2.000 notional
        self.assertEqual(meja.isi(b, {"BTCUSDT": {"w": 0.21, "k": 1}}, {"BTCUSDT": 100.0}), [])   # 1 % < ambang 2 %
        meja.isi(b, {}, {"BTCUSDT": 110.0})                                               # tutup: untung direalisasi
        self.assertEqual(b["posisi"], {})
        self.assertAlmostEqual(b["saldo"], 10_000 - 1 + 200 - 0.0005 * 2200, places=6)


class CycleTests(unittest.TestCase):
    def get(self, url):
        if "premiumIndex" in url:
            return [{"symbol": a, "markPrice": "100", "lastFundingRate": "0.0001"} for a in meja.PARAMS["aset"]]
        k = [[0, "0", "0", "0", str(100 + i * 0.1), "0", (T0 - 300 * (50 - i)) * 1000 + 299_999, "1000"] for i in range(50)]
        return k + [[0, "0", "0", "0", "999", "0", T0 * 1000 + 299_999, "1"]]                # candle berjalan: tidak boleh dipakai

    def test_every_agent_record_is_hashed_into_one_root_and_failures_are_recorded_not_skipped(self):
        agents = [{"slug": "a", "agent_id": 1, "model": "m1"}, {"slug": "b", "agent_id": 2, "model": "m2"}, {"slug": "c", "agent_id": 3, "model": "m3"}]

        def call(ag, system, user):
            self.assertIn("price 104.9", user)                                            # candle tutup terakhir, bukan 999
            if ag["slug"] == "c":
                raise RuntimeError("HTTP 429")
            return jawab({"BTCUSDT": {"arah": "long", "ukuran": 0.2 if ag["slug"] == "a" else 0.1, "keyakinan": 80}})
        books, ring = {}, {}
        rek, sik = meja.siklus(T0, agents, books, ring, call, get=self.get, log=lambda m: None)
        by = {r["agent"]: r for r in rek}
        self.assertEqual((by["a"]["status"], by["b"]["status"], by["c"]["status"]), ("ok", "ok", "gagal"))
        self.assertIn("429", by["c"]["galat"])
        self.assertEqual(by[meja.KONSENSUS]["masuk"], ["a", "b"])
        self.assertAlmostEqual(by[meja.KONSENSUS]["target"]["BTCUSDT"]["w"], (0.8 * 0.2 + 0.8 * 0.1) / 2)
        for r in rek:
            self.assertEqual(r["hash"], meja.sha({k: v for k, v in r.items() if k != "hash"}))
        root = bytes.fromhex(meja.root_of(sik["daun"])[2:])
        for h in sik["daun"]:
            self.assertTrue(chain.merkle_verify([bytes.fromhex(p[2:]) for p in meja.proof_of(sik["daun"], h)], root, bytes.fromhex(h[2:])))
        self.assertEqual(ring["a"], "trend up, small risk")

    def test_an_agent_that_answers_too_late_is_recorded_as_late(self):
        import time as _t

        def call(ag, system, user):
            if ag["slug"] == "b":
                _t.sleep(1.5)
            return jawab({})
        agents = [{"slug": "a", "agent_id": 1, "model": "m"}, {"slug": "b", "agent_id": 2, "model": "m"}]
        mulai = _t.time()
        with mock.patch.dict(meja.PARAMS, {"batas_jawab_s": 0.5}):
            rek, _ = meja.siklus(T0, agents, {}, {}, call, get=self.get, log=lambda m: None)
        self.assertLess(_t.time() - mulai, 1.2)                                           # siklus TIDAK menunggu agent yang terlambat
        self.assertEqual({r["agent"]: r.get("status") for r in rek if r["agent"] != meja.KONSENSUS}, {"a": "ok", "b": "terlambat"})


if __name__ == "__main__":
    unittest.main()
