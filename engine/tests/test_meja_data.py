"""P153 (F1, F-D110): data luas meja v2 (tools/meja_data.py) - registry alamat terkunci (bukan simbol), fitur murni, cache + anggaran per sumber,
sumber gagal / tanpa kunci ditandai (tidak dikarang), snapshot ber-hash. Jaringan dipalsukan."""
import json
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, ROOT)

import meja                                                         # noqa: E402
import meja_data as md                                              # noqa: E402

T0 = 1_791_200_100
WIF = md.REGISTRY["WIFUSDT"]["alamat"]


class RegistryTests(unittest.TestCase):
    def test_every_entry_has_a_valid_address_for_its_chain_and_a_contract_multiplier(self):
        for perp, r in md.REGISTRY.items():
            self.assertIn(r["chain"], ("solana", "ethereum", "base"), perp)
            ok = re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", r["alamat"]) if r["chain"] == "solana" else re.fullmatch(r"0x[0-9a-f]{40}", r["alamat"])
            self.assertTrue(ok, perp)
            self.assertEqual(r["kali"], 1000 if perp.startswith("1000") else 1, perp)
        self.assertEqual(md.registry_sha(), md.registry_sha())


class FeatureTests(unittest.TestCase):
    def test_dex_uses_the_registry_address_not_the_symbol_and_scales_price_by_the_contract_multiplier(self):
        tiruan = {"baseToken": {"address": "0xdeadbeef", "symbol": "WIF"}, "liquidity": {"usd": 9e9}, "priceUsd": "9"}
        asli = {"baseToken": {"address": WIF.lower(), "symbol": "$WIF"}, "liquidity": {"usd": 2e5}, "priceUsd": "0.5",
                "volume": {"h1": 100, "h24": 1200}, "txns": {"h1": {"buys": 30, "sells": 10}}}
        p = md.pasangan_terbaik([tiruan, asli], WIF)
        self.assertIs(p, asli)                                                            # likuiditas tiruan lebih besar, tetap ditolak
        f = md.f_dex(p, 501.0, 1000)
        self.assertEqual((f["dex_vol_1j_rel"], f["dex_beli_porsi_1j"]), (2.0, 0.75))
        self.assertAlmostEqual(f["dex_basis"], 500 / 501 - 1, places=6)
        self.assertEqual(md.f_dex(None, 1.0, 1)["dex_basis"], None)

    def test_rugcheck_danger_fomo_mentions_and_news_windows(self):
        self.assertTrue(md.f_rug({"risks": [{"level": "danger"}], "score_normalised": 9})["rug_bahaya"])
        self.assertEqual(md.f_rug(None)["rug_bahaya"], None)                              # tidak terbaca != aman
        lb = {"traders": [{"topTokens": [{"symbol": "WIF"}]}, {"topTokens": [{"symbol": "WIFE"}]}, {"topTokens": [{"address": WIF}]}]}
        th = {"theses": [{"token": {"symbol": "wif"}, "text": "x"}, {"token": {}, "text": "buying $WIF here"}, {"token": {}, "text": "no"}]}
        self.assertEqual(md.f_fomo(lb, th, "WIF", WIF), {"fomo_trader_top": 2, "fomo_thesis": 2})
        self.assertEqual(md.f_fomo(None, None, "WIF", WIF), {"fomo_trader_top": None, "fomo_thesis": None})
        jd = [{"sumber": "cointelegraph", "judul": "Bitcoin ETF inflows", "waktu": T0 - 3600},
              {"sumber": "decrypt", "judul": "BTC old story", "waktu": T0 - 8 * 3600},
              {"sumber": "binance-delisting", "judul": "Binance Will Delist BTCDOM", "waktu": T0 - 60}]
        f = md.f_berita(jd, ["BTC", "Bitcoin"], T0)
        self.assertEqual((f["berita_sebut_6j"], f["binance_delisting"]), (1, False))       # BTCDOM bukan BTC; > 6 jam tidak dihitung
        self.assertEqual(md.f_berita(None, ["BTC"], T0)["berita_sebut_6j"], None)

    def test_bot_fit_features(self):
        fa = {a: {"r_1j": 0.01 if i % 2 else -0.01, "r_4j": -0.05, "vol_1j": 0.005, "funding": 0.0001} for i, a in enumerate(meja.PARAMS["aset"])}
        fa["PAXGUSDT"] = {"vol_1j": 0.001, "r_1j": 0.0}
        self.assertEqual(md.f_bot("B1-TREND", {"BTCUSDT": 0.5}, fa, [])["breadth_naik_1j"], 0.5)
        b3 = md.f_bot("B3-CARRY", {}, fa, [])
        self.assertAlmostEqual(b3["funding_tahunan"], 0.0001 * 3 * 365)
        self.assertEqual(md.f_bot("B6-BOUNCE", {}, fa, [])["porsi_oversold"], 1.0)        # -5 % / (0,5 % x 2) = -5 < -2
        self.assertEqual(md.f_bot("B5-CORE-RWA", {}, fa, [])["vol_btc_per_emas"], 5.0)
        self.assertEqual(md.zskor(1.0, [0.0] * 10), None)                                  # < 30 titik: belum ada z


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.t = float(T0)
        self.calls = []

    def get(self, url, headers=None):
        self.calls.append(url)
        if "premiumIndex" in url:
            return [{"symbol": a, "markPrice": "100", "lastFundingRate": "0.0001"} for a in meja.PARAMS["aset"] + list(md.REGISTRY) + ["PAXGUSDT"]]
        if "klines" in url:
            return [[0, "0", "0", "0", str(100 + i * 0.1), "0", (T0 - 300 * (50 - i)) * 1000 + 299_999, "1000"] for i in range(50)]
        if "openInterestHist" in url:
            return [{"sumOpenInterest": str(100 + i)} for i in range(13)]
        if "takerlongshortRatio" in url:
            return [{"buySellRatio": "1.5"}]
        if "dexscreener" in url:
            return [{"baseToken": {"address": a}, "liquidity": {"usd": 1e6}, "priceUsd": "0.1", "volume": {"h1": 1, "h24": 24},
                     "txns": {"h1": {"buys": 1, "sells": 1}}} for a in url.rsplit("/", 1)[1].split(",")]
        if "rugcheck" in url:
            raise OSError("HTTP 429")
        raise AssertionError(url)

    def test_sources_are_cached_inside_their_budget_and_failures_or_missing_keys_are_reported(self):
        p = md.Pengumpul(get=self.get, fomo_key=None, kabar_fn=lambda now: {"judul": []}, now=lambda: self.t)
        ps = meja.pasar(T0, self.get)
        s1 = p.kumpul(T0, ps, {"B1-TREND": {"BTCUSDT": 0.0625}})
        k = s1["kesehatan"]
        self.assertIn("429", k["rugcheck"]["status"])
        self.assertEqual(k["rugcheck"]["cakupan"], 0.0)
        self.assertIn("tanpa kunci", k["fomo"]["status"])
        self.assertEqual((k["dexscreener"]["cakupan"], k["binance_ekstra"]["cakupan"]), (1.0, 1.0))
        self.assertIsNone(s1["fitur_aset"]["WIFUSDT"]["rug_bahaya"])                       # gagal baca = None, bukan "aman"
        self.assertAlmostEqual(s1["fitur_aset"]["BTCUSDT"]["oi_ubah_1j"], 112 / 100 - 1)
        self.assertEqual(s1["sha"], meja.sha({k: v for k, v in s1.items() if k != "sha"}))
        n_dex = sum("dexscreener" in u for u in self.calls)
        self.t += 60                                                                        # < 290 s: DexScreener dari cache
        p.kumpul(T0 + 300, ps, {"B1-TREND": {"BTCUSDT": 0.0625}})
        self.assertEqual(sum("dexscreener" in u for u in self.calls), n_dex)
        self.t += 300
        p.kumpul(T0 + 600, ps, {"B1-TREND": {"BTCUSDT": 0.0625}})
        self.assertGreater(sum("dexscreener" in u for u in self.calls), n_dex)


if __name__ == "__main__":
    unittest.main()
