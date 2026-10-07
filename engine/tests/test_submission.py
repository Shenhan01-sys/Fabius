import copy
import dataclasses
import json
import os
import unittest

from engine import chain, rule as R, submission
from engine.bots import REGISTRY
from engine.replay import replay
from engine.spec import SPECS

from .helpers import BNB, ETH, md_perp, walk

EXAMPLE = os.path.join(os.path.dirname(__file__), "..", "examples", "submission.example.json")
RULE_EXAMPLE = os.path.join(os.path.dirname(__file__), "..", "examples", "submission.rule.example.json")

try:
    from eth_account import Account
    from eth_account.messages import encode_typed_data
except ImportError:                                  # verifikasi tanda tangan opsional di mesin tanpa eth-account
    Account = None


def example():
    with open(EXAMPLE, encoding="utf-8") as f:
        return json.load(f)


def rule_sub():
    with open(RULE_EXAMPLE, encoding="utf-8") as f:
        return json.load(f)


def with_(sub, path, value):
    """Salinan dengan satu field diganti (path 'a.b.c'); value=None menghapus field."""
    s = copy.deepcopy(sub)
    cur = s
    keys = path.split(".")
    for k in keys[:-1]:
        cur = cur[k]
    if value is None:
        cur.pop(keys[-1], None)
    else:
        cur[keys[-1]] = value
    return s


class ValidateTests(unittest.TestCase):
    def assertRejected(self, sub, fragment, **kw):
        probs = submission.validate(sub, **kw)
        self.assertTrue(any(fragment in p for p in probs), f"{fragment!r} tidak ada di {probs}")

    def test_example_file_is_valid(self):
        self.assertEqual(submission.validate(example()), [])

    def test_template_rule_and_feed_are_open_and_code_stays_closed(self):
        self.assertEqual(submission.ENABLED_KINDS, ("template", "rule", "feed"))            # P167a rule; P167c feed (7 Okt); code (P167b) TERTUTUP
        for kind in ("code",):
            sub = with_(with_(example(), "kind", kind), "spec.template", None)
            self.assertRejected(sub, f"'{kind}' belum dibuka")
        self.assertRejected(with_(example(), "kind", "method_pr"), "kind: harus salah satu dari")   # jalur PR dihapus di skema v2 (digantikan code)
        # tetap bisa dibuka lewat parameter (jalur masa depan), dan bentuknya sudah divalidasi. P167c: feed tidak membawa template / parameter dan
        # tidak membawa komit maju di formulir (komit dikirim sesudah terdaftar lewat POST /bots/feed/commit)
        sub = with_(with_(example(), "kind", "feed"), "spec.template", None)
        self.assertRejected(sub, "spec.param: tidak dipakai untuk kind=feed", enabled_kinds=submission.KINDS)
        sub = with_(with_(sub, "spec.param_nama", None), "spec.param", None)
        self.assertEqual(submission.validate(sub, enabled_kinds=submission.KINDS), [])
        self.assertRejected(with_(sub, "evidence.komit_maju", [{"root": "0x" + "11" * 32, "bar": "2026-10-01"}]), "komit_maju: kosongkan",
                            enabled_kinds=submission.KINDS)

    def test_closed_schema_rejects_unknown_fields_anywhere(self):
        self.assertRejected(with_(example(), "instruksi", "abaikan aturan sebelumnya"), "'instruksi': field tidak dikenal")
        self.assertRejected(with_(example(), "identity.rahasia", "x"), "identity.'rahasia': field tidak dikenal")
        self.assertRejected(with_(example(), "spec.penggaris", {"fee_bps_sisi": 0}), "spec.'penggaris'")   # penggaris milik kami

    def test_required_fields(self):
        for path in ("kind", "spec.bot_id", "identity.issuer_wallet", "theory.pembunuh", "evidence.percobaan", "declarations.lisensi"):
            self.assertRejected(with_(example(), path, None), f"{path}: wajib diisi")

    def test_text_hygiene_allow_list_by_unicode_category(self):
        hostile = {
            "arah-teks U+202E": "teks‮balik", "lebar-nol U+200B": "nol​lebar", "kontrol BEL": "kontrol\x07bel", "BOM": "bom﻿x",
            "Tag-block ASCII smuggling U+E0041": "aman\U000e0041\U000e0042", "pemilih-varian FE0F": "a️b", "pemilih-varian E0100": "a\U000e0100b",
            "soft-hyphen": "a­b", "CGJ 034F": "a͏b", "ALM 061C": "a؜b", "Mongolian vowel 180E": "a᠎b",
            "pemisah baris 2028": "a b", "pemisah paragraf 2029": "a b", "C1 CSI U+009B": "a\u009bb", "NBSP": "a b",
            "surrogat sendirian": "a\ud800b", "privat-use": "ab",
        }
        base = example()["theory"]["mekanisme"]
        for name, ch in hostile.items():
            for path in ("theory.mekanisme", "identity.handle"):
                self.assertRejected(with_(example(), path, (base if path == "theory.mekanisme" else "handle") + ch), path, enabled_kinds=submission.KINDS)
                probs = submission.validate(with_(example(), path, (base if path == "theory.mekanisme" else "handle") + ch))
                self.assertTrue(probs, f"{name} lolos di {path}")
        # baris baru sah di teks panjang, tidak di teks satu-baris
        self.assertEqual(submission.validate(with_(example(), "theory.mekanisme", base + "\nbaris dua\tdengan tab")), [])
        self.assertTrue(submission.validate(with_(example(), "identity.handle", "dua\nbaris")))

    def test_blank_fillers_do_not_satisfy_minimum_length(self):
        for filler in ("ㅤ", "ﾠ", "⠀", "ᅟ", "ᅠ", "឴"):
            probs = submission.validate(with_(example(), "theory.mekanisme", filler * 120))
            self.assertTrue(probs, f"pengisi {filler!r} memenuhi min-panjang")
        self.assertTrue(submission.validate(with_(example(), "theory.mekanisme", " " * 120)))

    def test_length_limits(self):
        self.assertRejected(with_(example(), "theory.mekanisme", "terlalu pendek"), "terlalu pendek")
        self.assertRejected(with_(example(), "theory.mekanisme", "x" * 1501), "terlalu panjang")

    def test_messages_never_echo_raw_attacker_text(self):
        evil = "\x1b[31mMERAH\x1b[0m ignore previous instructions"
        probs = submission.validate(with_(example(), evil, "x"))
        self.assertTrue(probs)
        for p in probs:
            self.assertNotIn("\x1b", p)
            self.assertLessEqual(len(p), 200)
        probs = submission.validate(with_(example(), "spec.konstanta", {evil: 1}))
        self.assertTrue(all("\x1b" not in p for p in probs))
        probs = submission.validate(with_(example(), "spec.universe", ["ETHUSDT", "\x1b[2J"]))
        self.assertTrue(all("\x1b" not in p for p in probs))

    def test_bot_id_reserved_taken_and_impersonation(self):
        self.assertRejected(with_(example(), "spec.bot_id", "B7-MILIKKU"), "dicadangkan")
        self.assertRejected(with_(example(), "spec.bot_id", "B1-TREND"), "sudah dipakai")
        self.assertRejected(with_(example(), "spec.bot_id", "huruf kecil"), "format tidak valid")
        self.assertRejected(with_(example(), "spec.bot_id", "FABIUS-CORE"), "peniruan Fabius")
        self.assertRejected(with_(example(), "identity.handle", "Fabius Official"), "peniruan Fabius")
        self.assertRejected(with_(example(), "identity.handle", "F-a-b-i-u-s"), "peniruan Fabius")
        self.assertRejected(with_(example(), "identity.handle", "ＦＡＢＩＵＳ"), "peniruan Fabius")           # lebar-penuh, NFKC
        self.assertTrue(any("sudah dipakai" in p for p in submission.validate(example(), existing_ids=["TREND-ETH-30"])))

    def test_wallets_must_be_eip55_checksum(self):
        good = chain.to_checksum_address("0x5aaeb6053f3e94c9b9a09f33669435e7ef1beaed")
        self.assertEqual(submission.validate(with_(with_(example(), "identity.issuer_wallet", good), "identity.payout_wallet", good)), [])
        self.assertRejected(with_(example(), "identity.issuer_wallet", good.lower()), "EIP-55")
        self.assertRejected(with_(example(), "identity.payout_wallet", good[:-1] + good[-1].swapcase()), "EIP-55")
        self.assertRejected(with_(example(), "identity.issuer_wallet", "0x" + "00" * 20), "alamat nol")
        self.assertRejected(with_(example(), "identity.payout_wallet", "0x" + "00" * 20), "alamat nol")

    def test_one_method_one_parameter(self):
        self.assertRejected(with_(example(), "spec.konstanta", {"N": 5}), "konstanta")
        self.assertRejected(with_(example(), "spec.param_nama", "L"), "hanya punya parameter 'N'")

    def test_template_rules(self):
        self.assertRejected(with_(example(), "spec.template", "B9-NGAWUR"), "spec.template")
        self.assertRejected(with_(example(), "spec.template", None), "spec.template")
        self.assertRejected(with_(example(), "spec.konstanta", {"k": 3}), "milik template")
        self.assertRejected(with_(example(), "spec.param", 30.5), "bilangan bulat")
        self.assertRejected(with_(example(), "spec.param", 1), "bilangan bulat >= 2")
        self.assertRejected(with_(example(), "spec.universe", ["ETHUSDT", "NGAWURUSDT"]), "tidak punya data")
        self.assertRejected(with_(example(), "spec.universe", ["ETHUSDT", "ETHUSDT"]), "simbol ganda")

    def test_dates_and_oos_rules(self):
        self.assertRejected(with_(example(), "evidence.insample_akhir", "2019-12-31"), "insample")
        self.assertRejected(with_(example(), "evidence.oos_mulai", "2023-06-01"), "SETELAH in-sample")
        self.assertRejected(with_(example(), "evidence.oos_akhir", None), "mulai DAN akhir")
        self.assertRejected(with_(example(), "evidence.insample_mulai", "2020-13-45"), "tanggal")
        self.assertEqual(submission.validate(with_(with_(example(), "evidence.oos_mulai", None), "evidence.oos_akhir", None)), [])

    def test_unicode_digits_in_dates_are_rejected(self):
        for d in ("２０２０-０１-０１", "٢٠٢٠-٠١-٠١"):
            self.assertTrue(any("tanggal" in p for p in submission.validate(with_(example(), "evidence.insample_mulai", d))))

    def test_declarations_are_mandatory_true(self):
        for k in ("tanpa_lookahead", "tanpa_info_orang_dalam", "tanpa_wash_trading", "menerima_protokol", "izin_publikasi"):
            self.assertRejected(with_(example(), f"declarations.{k}", False), "pernyataan wajib")
            self.assertRejected(with_(example(), f"declarations.{k}", "true"), "true/false")

    def test_killer_must_be_structured_and_non_vacuous(self):
        self.assertRejected(with_(example(), "theory.pembunuh.metric", "perasaan"), "harus salah satu")
        self.assertRejected(with_(example(), "theory.pembunuh.window_sinyal", 3), "minimal 10")
        self.assertRejected(with_(example(), "theory.pembunuh", "kalau rugi banyak"), "harus objek")
        for metric, bad in (("net_pnl_bps", 1e15), ("net_pnl_bps", -1e15), ("net_pnl_bps", -6000), ("sharpe", 50), ("sharpe", -50),
                            ("mdd_pct", 5), ("mdd_pct", -100), ("mdd_pct", -95), ("rata_net_per_sinyal_bps", 1e6)):
            sub = with_(with_(example(), "theory.pembunuh.metric", metric), "theory.pembunuh.threshold", bad)
            self.assertRejected(sub, "theory.pembunuh.threshold")                    # hampa (tak pernah terpicu) atau langsung terpicu
        ok = with_(with_(example(), "theory.pembunuh.metric", "mdd_pct"), "theory.pembunuh.threshold", -30)
        self.assertEqual(submission.validate(ok), [])

    def test_references_need_public_https_urls_and_unique(self):
        self.assertRejected(with_(example(), "theory.referensi", []), "minimal 1")
        r = example()["theory"]["referensi"][0]
        bad_urls = ["javascript:alert(1)", "http://x.example/a", "https://localhost/a", "https://127.0.0.1/a", "https://169.254.169.254/latest/meta-data",
                    "https://[::1]/a", "https://user@evil.example/a", "https://good.example@evil.example/a", "https://server.internal/a",
                    "https://x.example:8443/a", "https://nodot/a", "https://xn--e1afmkfd.example/‮a", "https://10.0.0.5/a", "https://2130706433/a"]
        for u in bad_urls:
            self.assertTrue(submission.validate(with_(example(), "theory.referensi", [dict(r, url=u)])), u)
        self.assertEqual(submission.validate(with_(example(), "theory.referensi", [dict(r, url="https://doi.org/10.1000/xyz123")])), [])
        self.assertRejected(with_(example(), "theory.referensi", [r, dict(r)]), "URL ganda")

    def test_numbers_reject_nan_inf_bool_and_huge(self):
        for v in (float("nan"), float("inf"), True, 10 ** 400):
            self.assertTrue(submission.validate(with_(example(), "evidence.klaim.sharpe_net", v)), repr(v))
        self.assertRejected(with_(example(), "evidence.percobaan", 0), "minimal 1")

    def test_huge_numbers_never_raise_out_of_validate(self):
        big = 10 ** 400                                          # float(big) -> OverflowError; json.dumps -> batas 4300 digit
        for path in ("spec.param", "evidence.percobaan", "evidence.klaim.sharpe_net", "evidence.klaim.n_sinyal",
                     "identity.erc8004_agent_id", "theory.kapasitas_usd", "theory.pembunuh.threshold"):
            for val in (big, -big, float("inf"), float("-inf"), float("nan"), 1e300):
                probs = submission.validate(with_(example(), path, val))
                self.assertTrue(probs, f"{path}={val!r} lolos")
        self.assertTrue(submission.validate(with_(example(), "spec.konstanta", {"x": big})))
        self.assertTrue(submission.validate(with_(example(), "spec.konstanta", {"x": float("inf")})))

    def test_too_many_fields_and_problem_flood_are_bounded(self):
        flood = dict(example(), **{f"x{i}": 1 for i in range(5000)})
        probs = submission.validate(flood)
        self.assertTrue(probs and len(probs) <= 50)
        sub = with_(example(), "identity", dict(example()["identity"], **{f"y{i}": 1 for i in range(100)}))
        self.assertTrue(any("terlalu banyak field" in p for p in submission.validate(sub)))

    def test_fuzz_every_leaf_with_hostile_values_never_raises(self):
        hostile = [None, True, False, 0, -1, 10 ** 400, float("inf"), float("nan"), "", " ", "x" * 5000, [], {}, [1], {"a": 1},
                   "0x" + "zz" * 20, "‮", "​", "２０２０-０１-０１", "٢٠٢٠-٠١-٠١", "\x00", "<script>", "a\ud800b", "\U000e0041"]

        def paths(node, prefix=""):
            for k, v in node.items():
                p = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    yield p
                    yield from paths(v, p)
                else:
                    yield p
                    if isinstance(v, list) and v and isinstance(v[0], dict):
                        yield from ((f"{p}.0.{kk}") for kk in v[0])
        base = example()
        n = 0
        for p in paths(base):
            for h in hostile:
                sub = copy.deepcopy(base)
                cur = sub
                keys = p.split(".")
                try:
                    for k in keys[:-1]:
                        cur = cur[int(k)] if isinstance(cur, list) else cur[k]
                    if isinstance(cur, list):
                        cur[int(keys[-1])] = h
                    else:
                        cur[keys[-1]] = h
                except (KeyError, IndexError, TypeError, ValueError):
                    continue
                n += 1
                probs = submission.validate(sub)                  # sifat yang diuji: TIDAK melempar apa pun (teks bebas memang menerima string biasa)
                self.assertIsInstance(probs, list, f"{p}={h!r}")
        self.assertGreater(n, 500)

    def test_non_dict_and_wrong_types_do_not_raise(self):
        self.assertEqual(submission.validate("bukan objek"), ["pengajuan harus objek"])
        self.assertTrue(submission.validate({}))
        self.assertTrue(submission.validate(with_(example(), "spec", "teks")))
        self.assertTrue(submission.validate(with_(example(), "spec.universe", "ETHUSDT")))


class RuleKindTests(unittest.TestCase):
    """P167a: kind=rule - metode sepenuhnya dari penerbit (aturan JSON), bidang template tidak dipakai, aturan diperiksa dengan jalurnya."""

    def assertRejected(self, sub, fragment, **kw):
        probs = submission.validate(sub, **kw)
        self.assertTrue(any(fragment in p for p in probs), f"{fragment!r} tidak ada di {probs}")

    def test_the_rule_example_is_valid_and_rule_is_open_while_code_is_not(self):
        self.assertEqual(submission.validate(rule_sub()), [])
        self.assertIn("rule", submission.ENABLED_KINDS)
        self.assertEqual(submission.SCHEMA_V, 2)
        self.assertRejected(with_(rule_sub(), "kind", "code"), "'code' belum dibuka")                # P167b tertutup sampai jalur privat disetujui
        self.assertRejected(with_(rule_sub(), "kind", "feed"), "spec.rule: tidak dipakai untuk kind=feed")   # P167c terbuka, tanpa aturan

    def test_a_rule_form_has_no_template_parameter_or_constants(self):
        self.assertRejected(with_(rule_sub(), "spec.rule", None), "spec.rule: wajib untuk kind=rule")
        for f, v in (("template", "B1-TREND"), ("param_nama", "N"), ("param", 30)):
            self.assertRejected(with_(rule_sub(), f"spec.{f}", v), f"spec.{f}: tidak dipakai untuk kind=rule")
        self.assertRejected(with_(rule_sub(), "spec.konstanta", {"k": 3}), "kosongkan")
        self.assertRejected(with_(example(), "spec.rule", rule_sub()["spec"]["rule"]), "spec.rule: hanya untuk kind=rule")      # kind=template membawa aturan
        for f in ("param_nama", "param"):
            self.assertRejected(with_(example(), f"spec.{f}", None), f"spec.{f}: wajib untuk kind=template")             # template tetap wajib punya parameter

    def test_rule_problems_are_reported_with_their_path_and_the_universe_is_checked(self):
        self.assertRejected(with_(rule_sub(), "spec.rule.params.R", 1), "spec.rule.masuk_long.and[0].a.n: parameter 'R' dipakai sebagai jendela")
        self.assertRejected(with_(rule_sub(), "spec.rule.mode", "acak"), "spec.rule.mode")
        bad = rule_sub()
        bad["spec"]["rule"]["masuk_long"]["and"][0]["a"]["n"] = {"p": "ZZ"}
        self.assertRejected(bad, "spec.rule.masuk_long.and[0].a.n: parameter 'ZZ' tidak dideklarasikan")
        self.assertRejected(with_(rule_sub(), "spec.universe", ["ETHUSDT", "NGAWURUSDT"]), "tidak punya data")
        rank = {"mode": "peringkat", "params": {}, "skor": {"f": "ret", "n": 20}, "long_teratas": 1, "short_terbawah": 1, "min_aset": 5, "rotasi": "harian",
                "bobot": {"skema": "sama", "gross_maks": 2.0}}
        sub = with_(with_(rule_sub(), "spec.rule", rank), "spec.universe", ["ETHUSDT", "BNBUSDT"])
        self.assertRejected(sub, "lebih besar dari jumlah aset universe")
        self.assertEqual(submission.validate(with_(with_(rule_sub(), "spec.rule", rank), "spec.universe", ["ETHUSDT", "BNBUSDT", "BTCUSDT", "SOLUSDT", "XRPUSDT"])), [])

    def test_reserved_ids_and_the_theory_block_apply_to_rules_too(self):
        self.assertRejected(with_(rule_sub(), "spec.bot_id", "B9-RULE"), "dicadangkan")
        self.assertRejected(with_(rule_sub(), "theory.pembunuh.threshold", 99999), "theory.pembunuh.threshold")
        self.assertRejected(with_(rule_sub(), "evidence.percobaan", 0), "minimal 1")

    def test_to_botspec_builds_a_canonical_rule_spec_with_our_ruler(self):
        sub = rule_sub()
        sp = submission.to_botspec(sub)
        self.assertEqual((sp.bot_id, sp.template, sp.method, sp.param_nama), ("PULLBACK-TREND-1", "RULE", "RULE", "aturan"))
        self.assertEqual(sp.penggaris, {"fee_bps_sisi": 7, "funding": "nyata dua sisi"})        # penerbit tidak menentukan biaya
        self.assertEqual(sp.konstanta, {"rule": R.canonical(sub["spec"]["rule"])})
        self.assertEqual(sp.param, submission.sha0x(sp.konstanta["rule"]))                       # param = sha aturan kanonik
        self.assertIn("net_pnl_bps", sp.pembunuh)
        self.assertEqual(sp.universe, tuple(sub["spec"]["universe"]))
        self.assertIn("RULE", REGISTRY)
        # 2 vs 2.0 dan kunci yang sama: bot yang sama; aturan beda: bot beda
        fl = with_(with_(sub, "spec.rule.params.R", 14.0), "spec.rule.bobot.gross_maks", 1)
        self.assertEqual(submission.validate(fl), [])
        self.assertEqual(submission.to_botspec(fl).fingerprint(), sp.fingerprint())
        self.assertNotEqual(submission.to_botspec(with_(sub, "spec.rule.params.T", 120)).fingerprint(), sp.fingerprint())
        self.assertNotEqual(submission.submission_sha(fl), submission.submission_sha(sub))        # sha pengajuan memakai teks apa adanya (tanda tangan)
        self.assertEqual(submission.to_botspec(with_(with_(sub, "kind", "feed"), "spec.rule", None)).method, "FEED")   # P167c: feed = komit maju
        with self.assertRaises(ValueError):
            submission.to_botspec(with_(sub, "kind", "method_pr"))

    def test_a_rule_form_runs_in_the_engine_and_replays(self):
        sp = submission.to_botspec(rule_sub())
        md = md_perp({ETH: walk(400, 1, drift=0.002), BNB: walk(400, 2, drift=0.002)})
        tg = REGISTRY[sp.method](sp, md)
        self.assertTrue(all(t.bot_id == "PULLBACK-TREND-1" for t in tg))
        self.assertGreater(len(replay(sp, md)), 0)

    def test_the_signed_message_binds_the_rule_and_the_domain_is_schema_v2(self):
        sub = rule_sub()
        td = submission.typed_data(sub, 97, 1, 2)
        self.assertEqual(td["domain"]["version"], "2")
        self.assertEqual(td["message"]["specSha"], submission.spec_sha_of(sub))
        other = copy.deepcopy(sub)
        other["spec"]["rule"]["masuk_long"]["and"][0]["b"]["c"] = 25
        self.assertNotEqual(submission.typed_data(other, 97, 1, 2)["message"]["specSha"], td["message"]["specSha"])        # aturan lain = tanda tangan lain

    def test_the_schema_exposes_the_rule_field_for_the_web_builder(self):
        sch = submission.schema_json()["spec"]
        self.assertEqual(sch["rule"]["t"], "rule")
        self.assertTrue(sch["rule"]["optional"])
        for f in ("template", "param_nama", "param", "konstanta"):
            self.assertTrue(sch[f]["optional"], f)
        self.assertEqual(submission.schema_json()["kind"]["values"], ("template", "rule", "code", "feed"))


class SpecAndHashTests(unittest.TestCase):
    def test_to_botspec_uses_template_constants_and_our_ruler(self):
        sp = submission.to_botspec(example())
        base = SPECS["B1-TREND"]
        self.assertEqual((sp.bot_id, sp.template, sp.method, sp.param, sp.universe), ("TREND-ETH-30", "B1-TREND", "B1-TREND", 30, ("ETHUSDT", "BNBUSDT")))
        self.assertIsInstance(sp.param, int)
        self.assertEqual(sp.konstanta, base.konstanta)
        self.assertEqual(sp.penggaris, base.penggaris)             # penerbit tidak menentukan penggaris biaya
        self.assertIn("net_pnl_bps", sp.pembunuh)
        self.assertNotEqual(sp.sha(), base.sha())
        self.assertEqual(SPECS["B1-TREND"].sha(), base.sha())

    def test_to_botspec_coerces_param_to_the_template_type(self):
        sub = with_(with_(with_(example(), "spec.template", "B3-CARRY"), "spec.param_nama", "theta"), "spec.param", 1)       # JSON `1` untuk template float
        self.assertEqual(submission.validate(sub), [])
        sp = submission.to_botspec(sub)
        self.assertIsInstance(sp.param, float)
        self.assertEqual(sp.param, 1.0)

    def test_botspec_runs_in_engine_and_signals_carry_issuer_bot_id(self):
        sp = dataclasses.replace(submission.to_botspec(example()), param=5)
        md = md_perp({ETH: walk(60, 1, drift=0.01), BNB: walk(60, 2, drift=0.01)})
        tg = REGISTRY[sp.method](sp, md)
        self.assertTrue(all(t.bot_id == "TREND-ETH-30" for t in tg))
        self.assertGreater(len(replay(sp, md)), 0)

    def test_fingerprint_ignores_names_text_order_and_number_literal(self):
        a = submission.to_botspec(example())
        b = dataclasses.replace(a, bot_id="NAMA-LAIN", metode="kalimat lain yang sama sekali berbeda dari aslinya", pembunuh="x",
                                universe=tuple(reversed(a.universe)))
        c = dataclasses.replace(a, param=30.0)
        self.assertEqual(a.fingerprint(), b.fingerprint())
        self.assertEqual(a.fingerprint(), c.fingerprint())
        self.assertNotEqual(a.sha(), b.sha())                                  # sha penuh tetap membedakan (itu kuncinya)
        self.assertNotEqual(a.fingerprint(), dataclasses.replace(a, param=31).fingerprint())
        self.assertNotEqual(a.fingerprint(), dataclasses.replace(a, universe=("ETHUSDT",)).fingerprint())
        self.assertNotEqual(a.fingerprint(), SPECS["B1-TREND"].fingerprint())

    def test_hashes_are_stable_and_sensitive(self):
        a, b = example(), example()
        self.assertEqual(submission.submission_sha(a), submission.submission_sha(b))
        self.assertNotEqual(submission.submission_sha(a), submission.submission_sha(with_(a, "identity.handle", "lain")))
        self.assertEqual(submission.spec_sha_of(a), submission.spec_sha_of(with_(a, "identity.handle", "lain")))   # spec tak ikut identitas
        self.assertNotEqual(submission.spec_sha_of(a), submission.spec_sha_of(with_(a, "spec.param", 31)))

    def test_contact_is_not_part_of_the_public_hash(self):
        a = example()
        self.assertEqual(submission.submission_sha(a), submission.submission_sha(with_(a, "identity.contact", "nomor-lain@example.invalid")))
        self.assertNotIn("contact", json.dumps(submission._hashable(a)))
        td = submission.typed_data(a, 97, 1, 2)
        self.assertNotIn("contoh@example.invalid", json.dumps(td))

    def test_schema_json_is_a_copy(self):
        s = submission.schema_json()
        s["kind"]["values"] = ()
        self.assertEqual(submission.SCHEMA["kind"]["values"], submission.KINDS)
        self.assertEqual(s["spec"]["bot_id"]["t"], "str")


@unittest.skipIf(Account is None, "eth-account tidak terpasang")
class SignatureTests(unittest.TestCase):
    CHAIN, NONCE, NOW = 97, 7, 1_900_000_000
    DEADLINE = NOW + 600

    def signed(self, separate_payout=False):
        acct = Account.create()                                  # kunci sekali-pakai untuk tes; bukan rahasia siapa pun
        payout = Account.create() if separate_payout else acct
        sub = with_(with_(example(), "identity.issuer_wallet", acct.address), "identity.payout_wallet", payout.address)
        self.assertEqual(submission.validate(sub), [])
        msg = encode_typed_data(full_message=submission.typed_data(sub, self.CHAIN, self.NONCE, self.DEADLINE))
        sig = "0x" + acct.sign_message(msg).signature.hex().removeprefix("0x")
        psig = "0x" + payout.sign_message(msg).signature.hex().removeprefix("0x")
        return acct, payout, sub, sig, psig

    def verify(self, sub, sig, **kw):
        return submission.verify_identity(sub, sig, kw.pop("chain", self.CHAIN), kw.pop("nonce", self.NONCE), kw.pop("deadline", self.DEADLINE),
                                          kw.pop("now", self.NOW), **kw)

    def test_valid_signature_binds_identity(self):
        acct, _, sub, sig, _ = self.signed()
        self.assertEqual(submission.recover_signer(sub, sig, self.CHAIN, self.NONCE, self.DEADLINE), acct.address)
        self.assertEqual(self.verify(sub, sig), [])

    def test_tampered_submission_other_chain_nonce_or_deadline_are_rejected(self):
        _, _, sub, sig, _ = self.signed()
        for kw in ({"chain": 56}, {"nonce": self.NONCE + 1}, {"deadline": self.DEADLINE + 1}):
            probs = self.verify(sub, sig, **kw)
            self.assertTrue(probs and "bukan issuer_wallet" in probs[0], (kw, probs))
        probs = self.verify(with_(sub, "spec.param", 31), sig)
        self.assertTrue(probs and "bukan issuer_wallet" in probs[0], probs)

    def test_signature_by_other_wallet_expired_ttl_nonce_and_garbage(self):
        acct, _, sub, sig, _ = self.signed()
        other = Account.create()
        sub2 = with_(with_(sub, "identity.issuer_wallet", other.address), "identity.payout_wallet", other.address)
        self.assertTrue(self.verify(sub2, sig))
        self.assertEqual(self.verify(sub, sig, now=self.DEADLINE + 1), ["tanda tangan kedaluwarsa"])
        self.assertTrue(any("TTL" in p for p in self.verify(sub, sig, now=self.NOW - 100_000)))                 # deadline terlalu jauh
        self.assertTrue(any("nonce sudah dipakai" in p for p in self.verify(sub, sig, used_nonces={self.NONCE})))
        self.assertEqual(self.verify(sub, sig, used_nonces={1, 2, 3}), [])
        probs = self.verify(sub, "0x1234")
        self.assertTrue(probs and "tidak terbaca" in probs[0])

    def test_payout_wallet_must_cosign_when_different(self):
        acct, payout, sub, sig, psig = self.signed(separate_payout=True)
        self.assertTrue(any("belum menandatangani" in p for p in self.verify(sub, sig)))                       # tanpa persetujuan: tolak
        self.assertEqual(self.verify(sub, sig, payout_signature_hex=psig), [])
        stranger = Account.create()
        msg = encode_typed_data(full_message=submission.typed_data(sub, self.CHAIN, self.NONCE, self.DEADLINE))
        bad = "0x" + stranger.sign_message(msg).signature.hex().removeprefix("0x")
        self.assertTrue(any("bukan payout_wallet" in p for p in self.verify(sub, sig, payout_signature_hex=bad)))
        self.assertTrue(any("tidak terbaca" in p for p in self.verify(sub, sig, payout_signature_hex="0xzz")))


if __name__ == "__main__":
    unittest.main()
