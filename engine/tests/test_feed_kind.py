"""P167c (epik 12 §3.3): jenis `feed` - komit bobot bertanda tangan EIP-712 SEBELUM penutupan bar, satu per bar per bot, akar Merkle di-anchor ke
LockRegistry (kontrak yang sudah ada) sebelum penutupan, dinilai MAJU di ledger paper yang sama; gerbang replay N/A (bukan LOLOS); 120 hari bayangan,
tanpa slot. Tes: komit terlambat / ganda / tanda tangan salah / bobot tak sah ditolak; anchor; tick / gap / settle; verifikasi ulang; tinjauan."""
import copy
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "tools"), ROOT]

from engine import chain, feed as F, gates, ledger, registri, replay as replaymod, review as reviewmod, submission, terdaftar   # noqa: E402
from engine.data import MarketData                                  # noqa: E402
from engine.series import DAY_MS                                    # noqa: E402
from engine.tests.helpers import T0, mk_series, regime_closes, walk  # noqa: E402

try:
    from eth_account import Account
    from eth_account.messages import encode_typed_data
except ImportError:                                                     # pragma: no cover
    Account = None

DAY = 86_400
T0S = T0 // 1000
UNI = ("BTCUSDT", "ETHUSDT")
SPEC_SHA = "0x" + "ab" * 32


def md_uji(n=120) -> MarketData:
    perp = {"BTCUSDT": mk_series(regime_closes(n, 1)), "ETHUSDT": mk_series(walk(n, 2))}
    fund = {a: {T0 + i * DAY_MS: 0.0001 for i in range(n)} for a in perp}
    return MarketData(perp=perp, funding=fund)


def feed_sub(issuer: str, bot_id="FEED-ML-1"):
    with open(os.path.join(ROOT, "engine", "examples", "submission.example.json"), encoding="utf-8") as f:
        sub = json.load(f)
    sub["kind"] = "feed"
    for k in ("template", "param_nama", "param"):
        sub["spec"].pop(k, None)
    sub["spec"].update(bot_id=bot_id, universe=list(UNI))
    sub["identity"]["issuer_wallet"] = sub["identity"]["payout_wallet"] = issuer
    return sub


@unittest.skipIf(Account is None, "eth-account tidak terpasang")
class _Basis(unittest.TestCase):
    def setUp(self):
        import feed_gerbang as fg
        self.fg = fg
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.acct = Account.create()
        sub = feed_sub(self.acct.address)
        self.spec = submission.to_botspec(sub)
        self.reg = {"FEED-ML-1": {"spec": self.spec, "issuer": self.acct.address, "spec_sha": SPEC_SHA, "t_lolos": T0S + 50 * DAY}}
        self.now = [T0S + 60 * DAY]
        self.st = fg.KomitFeed(os.path.join(self.tmp, "feed"), now=lambda: self.now[0])

    def sign(self, bar_close, bobot, acct=None, bot="FEED-ML-1"):
        td = F.typed_data(bot, SPEC_SHA, self.acct.address, bar_close, bobot, 97)
        sig = (acct or self.acct).sign_message(encode_typed_data(full_message=td)).signature.hex()
        return {"bot_id": bot, "bar_close": bar_close, "bobot": bobot, "signature": "0x" + sig.removeprefix("0x")}

    def komit(self, bar_close, bobot, **kw):
        return self.st.terima(self.sign(bar_close, bobot, **kw), self.reg)


class KomitTests(_Basis):
    def test_a_signed_commit_before_the_cutoff_is_stored_and_sealed_until_the_bar_opens(self):
        bc = T0S + 61 * DAY
        code, out = self.komit(bc, {"BTCUSDT": 250_000, "ETHUSDT": -100_000})
        self.assertEqual(code, 201, out)
        self.assertEqual(out["weights_sha"], F.weights_sha({"BTCUSDT": 250_000, "ETHUSDT": -100_000}))
        self.assertEqual(F.bobot_kanonik({"ETHUSDT": -100_000, "BTCUSDT": 250_000, "XRPUSDT": 0}), "BTCUSDT:250000,ETHUSDT:-100000")
        row = self.st.publik("FEED-ML-1")[0]
        self.assertNotIn("bobot", row)                                                            # bar belum dibuka: sinyal penerbit tidak bocor
        self.assertEqual(row["sealed_until"], bc)
        self.now[0] = bc
        row = self.st.publik("FEED-ML-1")[0]
        self.assertEqual(row["bobot"], {"BTCUSDT": 250_000, "ETHUSDT": -100_000})
        self.assertTrue(chain.merkle_verify([chain.from_hex(p) for p in row["proof"]], chain.from_hex(row["root"]), chain.from_hex(row["leaf"])))
        recs, prev = self.st.semua(), ledger.ZERO
        for r in recs:                                                                            # berkas komit berantai hash (append-only)
            self.assertEqual((r["prev"], r["h"]), (prev, ledger.record_hash(r)))
            prev = r["h"]

    def test_late_early_misaligned_and_pre_registration_commits_are_rejected(self):
        bc = T0S + 61 * DAY
        self.now[0] = bc - F.BATAS_SEBELUM_TUTUP_S
        code, out = self.komit(bc, {"BTCUSDT": 1})
        self.assertEqual(code, 422)
        self.assertIn("terlambat", out["problems"][0])
        self.now[0] = bc + 5
        self.assertEqual(self.komit(bc, {"BTCUSDT": 1})[0], 422)                                   # sesudah penutupan
        self.now[0] = bc - F.BATAS_SEBELUM_TUTUP_S - 1
        self.assertEqual(self.komit(bc, {"BTCUSDT": 1})[0], 201)                                   # satu detik sebelum batas: sah
        self.now[0] = T0S + 60 * DAY
        self.assertEqual(self.komit(T0S + 63 * DAY, {"BTCUSDT": 1})[0], 422)                        # > 2 hari ke depan
        self.assertEqual(self.komit(T0S + 61 * DAY + 3600, {"BTCUSDT": 1})[0], 422)                 # bukan 00:00 UTC
        self.now[0] = T0S + 40 * DAY
        self.assertEqual(self.komit(T0S + 41 * DAY, {"BTCUSDT": 1})[0], 422)                        # sebelum bot terdaftar

    def test_one_commit_per_bar_per_bot_and_it_is_never_replaced(self):
        bc = T0S + 61 * DAY
        self.assertEqual(self.komit(bc, {"BTCUSDT": 500_000})[0], 201)
        self.assertEqual(self.komit(bc, {"BTCUSDT": 500_000})[0], 409)                             # kiriman ulang yang sama
        self.assertEqual(self.komit(bc, {"ETHUSDT": 500_000})[0], 409)                             # bobot lain untuk bar yang sama
        self.assertEqual(len(self.st.semua()), 1)
        self.assertEqual(self.komit(bc + DAY, {"ETHUSDT": 500_000})[0], 201)                        # bar berikutnya boleh

    def test_bad_signatures_are_rejected(self):
        bc = T0S + 61 * DAY
        self.assertEqual(self.komit(bc, {"BTCUSDT": 1}, acct=Account.create())[0], 401)             # bukan dompet penerbit
        body = self.sign(bc, {"BTCUSDT": 1})
        body["bobot"] = {"BTCUSDT": 2}                                                              # tanda tangan atas bobot lain
        self.assertEqual(self.st.terima(body, self.reg)[0], 401)
        self.assertEqual(self.st.terima(dict(body, signature="0x" + "00" * 65), self.reg)[0], 401)
        self.assertEqual(self.st.terima(dict(body, signature="0xzz"), self.reg)[0], 401)
        self.assertEqual(self.st.terima({k: v for k, v in body.items() if k != "signature"}, self.reg)[0], 400)
        self.assertEqual(self.st.semua(), [])

    def test_weights_must_be_finite_integer_ppm_inside_the_universe_with_gross_at_most_one(self):
        bc = T0S + 61 * DAY
        for bobot in ({"BTCUSDT": 0.5}, {"BTCUSDT": float("nan")}, {"BTCUSDT": float("inf")}, {"BTCUSDT": True}, {"BTCUSDT": "1"},
                      {"BTCUSDT": 600_000, "ETHUSDT": -400_001}, {"BTCUSDT": 1_000_001}, {"XRPUSDT": 1}, [1], "x"):
            with self.subTest(bobot=bobot):
                body = {"bot_id": "FEED-ML-1", "bar_close": bc, "bobot": bobot, "signature": "0x" + "00" * 65}
                self.assertEqual(self.st.terima(body, self.reg)[0], 400)
        self.assertEqual(self.komit(bc, {"BTCUSDT": 600_000, "ETHUSDT": -400_000})[0], 201)        # gross tepat 1
        self.assertEqual(self.komit(bc + DAY, {})[0], 201)                                         # flat = komit sah
        self.assertEqual(self.st.terima(self.sign(bc, {}, bot="FEED-LAIN"), self.reg)[0], 404)      # bukan bot feed terdaftar

    def test_the_message_to_sign_comes_from_the_gate_and_matches_the_engine(self):
        bc = T0S + 61 * DAY
        code, td = self.st.typed({"bot_id": "FEED-ML-1", "bar_close": bc, "bobot": {"BTCUSDT": 7}}, self.reg)
        self.assertEqual(code, 200)
        self.assertEqual(td, F.typed_data("FEED-ML-1", SPEC_SHA, self.acct.address, bc, {"BTCUSDT": 7}, 97))
        self.assertEqual((td["domain"]["name"], td["domain"]["version"]), (submission.EIP712_NAME, str(submission.SCHEMA_V)))


class AnchorTests(_Basis):
    def test_the_root_is_locked_on_the_existing_lockregistry_between_the_cutoff_and_the_close(self):
        bc = T0S + 61 * DAY
        self.komit(bc, {"BTCUSDT": 300_000})
        acct2 = Account.create()
        self.reg["FEED-ML-2"] = dict(self.reg["FEED-ML-1"], issuer=acct2.address)
        td = F.typed_data("FEED-ML-2", SPEC_SHA, acct2.address, bc, {"ETHUSDT": -1}, 97)
        self.st.terima({"bot_id": "FEED-ML-2", "bar_close": bc, "bobot": {"ETHUSDT": -1},
                        "signature": "0x" + acct2.sign_message(encode_typed_data(full_message=td)).signature.hex().removeprefix("0x")}, self.reg)
        self.assertIsNone(self.st.rencana(bc - F.BATAS_SEBELUM_TUTUP_S - 1))                          # masih menerima komit
        self.assertIsNone(self.st.rencana(bc - F.JEDA_ANCHOR_S))                                      # terlalu dekat penutupan
        plan = self.st.rencana(bc - F.BATAS_SEBELUM_TUTUP_S)
        self.assertEqual((plan["bar_close"], plan["n"]), (bc, 2))
        try:
            from evm import calldata
            import signal_commit as sc
            want = calldata(sc.SIG_LOCK, ("bytes32", "bytes32", "string"), (chain.ascii32(F.LABEL_ANCHOR), chain.from_hex(plan["root"]),
                                                                             F.uri_anchor(bc, 2)))
            self.assertEqual(plan["calldata"], want)                                                  # ABI sama dengan pin_spec / lock_spec
        except ImportError:
            pass
        terkunci, kiriman = {}, []

        def kirim(data):
            kiriman.append(data)
            terkunci[plan["root"]] = bc - 300
            return {"transactionHash": "0xtx", "status": "0x1"}
        rec = self.st.putaran_anchor(bc - 590, kirim, lambda who, root: terkunci.get(root, 0), "0xGerbang", "0xLockRegistry")
        self.assertEqual((rec["status"], rec["locked_at"], len(kiriman)), ("ter-anchor", bc - 300, 1))
        self.assertIsNone(self.st.putaran_anchor(bc - 500, kirim, lambda who, root: terkunci.get(root, 0), "0xGerbang", "0xL"))   # sekali saja
        self.now[0] = bc
        for row in self.st.publik():
            self.assertEqual((row["root"], row["anchor"]["status"], row["anchor"]["locked_at"]), (plan["root"], "ter-anchor", bc - 300))

    def test_a_failed_or_late_anchor_is_recorded_and_retried_only_before_the_close(self):
        bc = T0S + 61 * DAY
        self.komit(bc, {"BTCUSDT": 300_000})

        def rusak(data):
            raise OSError("rpc mati")
        rec = self.st.putaran_anchor(bc - 590, rusak, lambda who, root: 0, "0xG", "0xL")
        self.assertTrue(rec["status"].startswith("gagal"))
        rec = self.st.putaran_anchor(bc - 580, lambda d: {"transactionHash": "0x2"}, lambda who, root: bc + 1, "0xG", "0xL")
        self.assertEqual(rec["status"], "terlambat")                                                    # lockedAt >= penutupan = bukan bukti
        self.assertIsNone(self.st.putaran_anchor(bc + 10, rusak, lambda who, root: 0, "0xG", "0xL"))   # sesudah penutupan: tidak dicoba lagi


class LedgerTests(_Basis):
    """Tick feed = komit sah + ter-anchor; tanpa komit / tak ter-anchor = gap; gerbang mati = TUNDA; settle lewat replay yang sama."""

    def jalankan_hari(self, bars, bobot_per_hari, anchored=True, skip=(), late_anchor=()):
        terkunci = {}
        for k, bc in enumerate(bars):
            if k in skip:
                continue
            self.now[0] = bc - 3600 - F.BATAS_SEBELUM_TUTUP_S
            self.assertEqual(self.komit(bc, bobot_per_hari[k])[0], 201)
            if anchored:
                plan = self.st.rencana(bc - F.BATAS_SEBELUM_TUTUP_S)
                la = bc + 10 if k in late_anchor else bc - 200
                self.st.putaran_anchor(bc - F.BATAS_SEBELUM_TUTUP_S, lambda d, r=plan["root"], la=la: terkunci.__setitem__(r, la) or {"transactionHash": "0x1"},
                                       lambda who, root: terkunci.get(root, 0), "0xGerbang", "0xL")
        return terkunci

    def test_ticks_gaps_and_settles_follow_the_commitments_and_verify_from_scratch(self):
        md = md_uji(120)
        first = T0 + 60 * DAY_MS
        g = ledger.seal(ledger.make_genesis(self.spec, "0x" + "00" * 32, None, first, first + DAY_MS), ledger.ZERO)
        bars = [first // 1000 + DAY * (k + 1) for k in range(6)]
        bobot = [{"BTCUSDT": 500_000}, {"BTCUSDT": 500_000, "ETHUSDT": -250_000}, {}, {"ETHUSDT": 400_000}, {"BTCUSDT": 1_000_000}, {"BTCUSDT": 1}]
        terkunci = self.jalankan_hari(bars, bobot, skip=(3,), late_anchor=(4,))
        self.now[0] = bars[-1] + DAY
        komits = [r for r in self.st.publik("FEED-ML-1")]
        recs = [g]
        reader = lambda who, root: terkunci.get(root, 0)                                                  # noqa: E731
        for k in range(len(bars) + 1):
            now_ms = (first + (k + 1) * DAY_MS) + 3_600_000
            new, notes = F.step(self.spec, md, now_ms, recs, komits, self.acct.address, SPEC_SHA, 97, reader, "0xGerbang")
            recs += new
        kinds = [(r["type"], ledger.date_of(r.get("asof", r.get("bar", 0)))) for r in recs[1:] if r["type"] in ("tick", "gap")]
        self.assertEqual([x[0] for x in kinds], ["tick", "tick", "tick", "gap", "gap", "tick", "gap"])
        gaps = [r["reason"] for r in recs if r["type"] == "gap"]
        self.assertIn("tidak ada komit untuk bar ini", gaps[0])                                        # hari tanpa komit
        self.assertIn("tidak ter-anchor sebelum penutupan", gaps[1])                                   # anchor terlambat = tak terukur
        ticks = [r for r in recs if r["type"] == "tick"]
        self.assertEqual(ticks[1]["targets"], {"BTCUSDT": 0.5, "ETHUSDT": -0.25})
        self.assertEqual(ticks[1]["asof"], bars[1] * 1000 - DAY_MS)                                    # dipegang selama bar yang dibuka di barClose
        settles = [r for r in recs if r["type"] == "settle"]
        self.assertGreaterEqual(len(settles), 2)
        s = next(r for r in settles if r["bar"] == bars[1] * 1000)
        tg = [replaymod.Target("FEED-ML-1", t["asof"], dict(t["targets"])) for t in ticks[:2]] + [replaymod.Target("FEED-ML-1", bars[1] * 1000, {})]
        self.assertAlmostEqual(s["net"], replaymod.replay(self.spec, md, tg)[-1][1], places=15)        # replay yang sama dengan bot lain
        self.assertEqual(F.verify(self.spec, recs, md, komits, self.acct.address, SPEC_SHA, 97, reader, "0xGerbang"), [])
        palsu = copy.deepcopy(recs)
        i = next(j for j, r in enumerate(palsu) if r["type"] == "tick" and r["targets"])
        palsu[i]["targets"] = {"BTCUSDT": 1.0}
        for j in range(i, len(palsu)):                                                                 # disegel ulang: rantai sah, isi palsu
            palsu[j] = ledger.seal({k: v for k, v in palsu[j].items() if k not in ("h", "prev", "v")}, palsu[j - 1]["h"])
        self.assertTrue(any("targets BEDA" in p for p in F.verify(self.spec, palsu, md, komits, self.acct.address, SPEC_SHA, 97, reader, "0xGerbang")))
        self.assertTrue(F.verify(self.spec, recs, md, komits, self.acct.address, SPEC_SHA, 97, lambda w, r: 1, "0xGerbang"))   # chain berkata lain
        self.assertTrue(F.verify(self.spec, recs, md, komits, self.acct.address, SPEC_SHA, 97, reader, "0xOrangLain"))          # dikunci alamat lain

    def test_an_unreadable_commit_list_is_deferred_not_read_as_no_commit(self):
        md = md_uji(120)
        first = T0 + 60 * DAY_MS
        g = ledger.seal(ledger.make_genesis(self.spec, "0x" + "00" * 32, None, first, first + DAY_MS), ledger.ZERO)
        new, notes = F.step(self.spec, md, first + DAY_MS + 3_600_000, [g], None, self.acct.address, SPEC_SHA)
        self.assertEqual(new, [])
        self.assertIn("TUNDA", notes[0])
        new, _ = F.step(self.spec, md, first + DAY_MS + 13 * 3_600_000, [g], None, self.acct.address, SPEC_SHA)
        self.assertEqual([r["type"] for r in new], ["gap"])                                             # lewat 12 jam: gap, tidak diisi belakangan

        def rpc_mati(who, root):
            raise OSError("rpc")
        self.jalankan_hari([first // 1000 + DAY], [{"BTCUSDT": 1}])
        self.now[0] = first // 1000 + 2 * DAY
        with self.assertRaises(OSError):                                                               # RPC mati = TUNDA (pemanggil), bukan gap
            F.step(self.spec, md, first + DAY_MS + 3_600_000, [g], self.st.publik(), self.acct.address, SPEC_SHA, 97, rpc_mati, "0xGerbang")

    def test_the_daily_feed_tick_tool_writes_genesis_ticks_and_the_public_commit_copy(self):
        import feed_tick
        md = md_uji(120)
        first = T0 + 60 * DAY_MS
        bars = [first // 1000 + DAY * (k + 1) for k in range(2)]
        terkunci = self.jalankan_hari(bars, [{"BTCUSDT": 500_000}, {"ETHUSDT": -500_000}])
        self.now[0] = bars[-1] + DAY
        led = os.path.join(self.tmp, "led")
        bots = {"FEED-ML-1": dict(self.reg["FEED-ML-1"])}
        out = []
        for k in range(len(bars)):
            rc = feed_tick.tick(bots, led, md, first + (k + 1) * DAY_MS + 3_600_000, lambda b: self.st.publik(b), lambda w, r: terkunci.get(r, 0),
                                "0xGerbang", False, out.append)
            self.assertEqual(rc, 0)
        recs = ledger.load(os.path.join(led, "FEED-ML-1.jsonl"))
        self.assertEqual([r["type"] for r in recs], ["genesis", "tick", "settle", "tick", "settle"])   # bar sintetis sudah ada: settle langsung
        with open(os.path.join(led, "komit", "FEED-ML-1.json"), encoding="utf-8") as f:
            self.assertEqual(len(json.load(f)), 2)
        self.assertEqual(feed_tick.verifikasi(bots, led, md, lambda w, r: terkunci.get(r, 0), "0xGerbang", out.append), 0)
        rc = feed_tick.tick(bots, led, md, first + 3 * DAY_MS + 3_600_000, lambda b: (_ for _ in ()).throw(OSError("gerbang mati")),
                            lambda w, r: terkunci.get(r, 0), "0xGerbang", False, out.append)
        self.assertEqual(rc, 4)                                                                          # TUNDA, bukan gap
        self.assertTrue(any("LABEL: tidak bisa diverifikasi ulang" in x for x in out))


class TinjauanTests(_Basis):
    """Gerbang replay N/A (bukan LOLOS) + vonis MAJU_FEED; tidak memakan alpha keluarga; tidak pernah menjadi penantang slot."""

    def test_the_review_writes_every_replay_gate_as_na_with_a_reason_and_a_forward_only_verdict(self):
        sub = feed_sub(self.acct.address)
        self.assertIn("belum dibuka", " ".join(submission.validate(sub, enabled_kinds=("template", "rule"))))
        self.assertEqual(submission.validate(sub, enabled_kinds=submission.KINDS), [])
        rep = reviewmod.review(sub, md_uji(120), None, enabled_kinds=submission.KINDS)
        self.assertEqual(rep["vonis"], "MAJU_FEED")
        self.assertNotEqual(rep["vonis"], "LOLOS_SHADOW")
        ids = [g["gate"] for g in rep["gerbang"]]
        self.assertEqual(ids, ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "G11", "K1", "K2", "K3", "K4", "K5"])
        self.assertTrue(all(g["status"] == gates.TB and g["value"].startswith("N/A") for g in rep["gerbang"]))
        self.assertEqual((rep["label_kepercayaan"], rep["bayangan_hari"]), ("tidak bisa diverifikasi ulang", 120))
        text = reviewmod.render(rep)
        self.assertIn("VONIS: MAJU_FEED", text)
        self.assertNotIn("LOLOS", text)
        self.assertIn("N/A", text)

    def test_replay_gates_on_a_feed_spec_are_unmeasured_never_passed(self):
        res = gates.run_gates(self.spec, md_uji(120), None, gates.GateParams.fast())
        self.assertEqual((res[0].gate, res[0].status), ("G*", gates.NA))
        self.assertEqual(gates.verdict(res)[0], "TIDAK_TERUKUR")

    def test_a_recorded_feed_uses_no_family_alpha_triggers_no_cooldown_and_never_enters_the_book(self):
        root = os.path.join(self.tmp, "repo")
        d = os.path.join(root, "ledger", "pengajuan")
        os.makedirs(os.path.join(d, "masuk"))
        sub = feed_sub(self.acct.address)
        td = submission.typed_data(sub, 97, 1, 1_900_000_600)
        sig = "0x" + self.acct.sign_message(encode_typed_data(full_message=td)).signature.hex().removeprefix("0x")
        ident = {"signature": sig, "chain_id": 97, "nonce": 1, "deadline": 1_900_000_600, "now_s": 1_900_000_000}
        rc, rep, msgs = reviewmod.tinjau_tercatat(sub, md_uji(120), None, path=os.path.join(d, "registri.jsonl"), now_s=1_900_000_000, catat=True,
                                                  identity=ident, enabled_kinds=submission.KINDS)
        self.assertEqual((rep["vonis"], rep["mengikat"]), ("MAJU_FEED", True))
        pub = copy.deepcopy(sub)
        pub["identity"].pop("contact")
        with open(os.path.join(d, "masuk", rep["submission_sha"] + ".json"), "w", encoding="utf-8") as f:
            json.dump({"submission": pub}, f)
        entries = registri.load(os.path.join(d, "registri.jsonl"))
        self.assertEqual(registri.verify(entries), [])
        st = registri.status_keluarga(entries, self.acct.address, self.acct.address, 1_900_000_100)
        self.assertEqual((st["k"], st["boleh_ajukan"]), (1, True))                                    # tidak memakan alpha, tidak memicu masa tunggu
        rinci, masalah = terdaftar.feed_rincian(root)
        self.assertIn("FEED-ML-1", rinci, masalah)
        self.assertEqual(terdaftar.rincian(root)[0], {})                                               # bukan penantang slot (tanpa slot sampai terbukti)
        self.assertNotIn("FEED-ML-1", terdaftar.semua(root))                                           # bukan ledger paper biasa


def _anvil_siap() -> bool:
    import shutil as sh
    return bool(Account is not None and sh.which("anvil") and os.path.isfile(os.path.join(ROOT, "out", "LockRegistry.sol", "LockRegistry.json")))


@unittest.skipUnless(_anvil_siap(), "butuh eth-account + anvil + out/ (forge build)")
class AnvilAnchorTests(_Basis):
    """Akar komit dikunci di bytecode LockRegistry ASLI (anvil lokal) lewat putaran anchor gerbang yang sama; `lockedAt` dibaca ulang dari chain
    dan komit lolos pemeriksaan ulang publik hanya bila lockedAt < penutupan bar."""

    def test_the_gate_locks_the_root_on_lockregistry_before_the_close_and_anyone_can_recheck_it(self):
        import subprocess
        import time
        import evm
        import signal_commit as sc
        from engine.tests.test_signal_commit import DEV_PK1, _free_port
        bc = T0S + 61 * DAY
        port = _free_port()
        proc = subprocess.Popen(["anvil", "--port", str(port), "--timestamp", str(bc - 900), "--silent"], stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        self.addCleanup(proc.wait, 10)
        self.addCleanup(proc.terminate)
        ev = evm.Evm([f"http://127.0.0.1:{port}"], 31337, receipt_wait_s=20, poll_s=0.2)
        for _ in range(100):
            try:
                ev.chain_check()
                break
            except Exception:                                                                       # noqa: BLE001
                time.sleep(0.1)
        with open(os.path.join(ROOT, "out", "LockRegistry.sol", "LockRegistry.json"), encoding="utf-8") as f:
            reg = ev.send(DEV_PK1, None, bytes.fromhex(json.load(f)["bytecode"]["object"][2:]))["contractAddress"]
        locker = evm.address_of(DEV_PK1)
        self.now[0] = bc - 3600
        self.assertEqual(self.komit(bc, {"BTCUSDT": 400_000, "ETHUSDT": -200_000})[0], 201)

        def baca(who, root):
            return int(ev.call_decode(reg, sc.SIG_LOCKED_AT, ("address", "bytes32", "bytes32"),
                                      (who, chain.ascii32(F.LABEL_ANCHOR), chain.from_hex(root)), ("uint64",))[0])
        ev.rpc("evm_setNextBlockTimestamp", [bc - 400])
        rec = self.st.putaran_anchor(bc - 590, lambda data: ev.send(DEV_PK1, reg, data, gas=150_000), baca, locker, reg)
        self.assertEqual((rec["status"], rec["locked_at"]), ("ter-anchor", bc - 400))
        self.now[0] = bc
        row = self.st.publik("FEED-ML-1")[0]
        self.assertEqual(row["anchor"]["locked_at"], bc - 400)
        self.assertEqual(F.periksa_komit(row, self.acct.address, SPEC_SHA, UNI, 97, baca, locker), [])     # bukti publik lewat chain
        self.assertTrue(F.periksa_komit(row, self.acct.address, SPEC_SHA, UNI, 97, baca, "0x" + "11" * 20))   # dikunci alamat lain = bukan anchor kami


@unittest.skipIf(Account is None, "eth-account tidak terpasang")
class HttpTests(unittest.TestCase):
    def setUp(self):
        import x402_sinyal as xs
        self.tmp = tempfile.mkdtemp()
        old, os.environ["ANALIS_DIR"] = os.environ.get("ANALIS_DIR"), os.path.join(self.tmp, "analis")
        self.addCleanup(lambda: os.environ.pop("ANALIS_DIR") if old is None else os.environ.update(ANALIS_DIR=old))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.acct = Account.create()
        self.now = T0S + 60 * DAY
        self.g = xs.Gate(xs.Data(ROOT), "0xk", "https://g", "https://w", log=lambda m: None, now=lambda: self.now)
        spec = submission.to_botspec(feed_sub(self.acct.address))
        self.g.feed_terdaftar = lambda: {"FEED-ML-1": {"spec": spec, "issuer": self.acct.address, "spec_sha": SPEC_SHA, "t_lolos": T0S}}
        srv = ThreadingHTTPServer(("127.0.0.1", 0), xs.make_handler(self.g))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        self.url = f"http://127.0.0.1:{srv.server_address[1]}"

    def call(self, path, body=None):
        req = urllib.request.Request(self.url + path, data=None if body is None else json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"}, method="GET" if body is None else "POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def test_an_issuer_program_gets_the_message_signs_commits_and_the_public_sees_it_after_the_bar_opens(self):
        code, info = self.call("/bots/feed")
        self.assertEqual((code, info["shadow_days"], info["label"], info["bots"]), (200, 120, "tidak bisa diverifikasi ulang", ["FEED-ML-1"]))
        code, schema = self.call("/bots/schema")
        self.assertEqual((schema["feed"]["commit_cutoff_s"], schema["code"]["open"]), (F.BATAS_SEBELUM_TUTUP_S, False))
        bc = T0S + 61 * DAY
        body = {"bot_id": "FEED-ML-1", "bar_close": bc, "bobot": {"BTCUSDT": 400_000}}
        code, td = self.call("/bots/feed/typed-data", body)
        self.assertEqual(code, 200)
        sig = "0x" + self.acct.sign_message(encode_typed_data(full_message=td)).signature.hex().removeprefix("0x")
        code, out = self.call("/bots/feed/commit", dict(body, signature=sig))
        self.assertEqual(code, 201, out)
        self.assertEqual(self.call("/bots/feed/commit", dict(body, signature=sig))[0], 409)
        self.assertNotIn("bobot", self.call("/bots/feed/FEED-ML-1")[1]["komit"][0])
        self.now = bc
        self.assertEqual(self.call("/bots/feed/FEED-ML-1")[1]["komit"][0]["bobot"], {"BTCUSDT": 400_000})
        self.assertEqual(self.call("/bots/feed/commit", dict(body, bar_close=bc + DAY, signature=sig))[0], 401)
        self.assertEqual(self.call("/bots/feed/commit", {"bot_id": "FEED-ML-1"})[0], 400)


@unittest.skipUnless(__import__("shutil").which("node"), "Node tidak ada")
class WebContractTests(unittest.TestCase):
    """Teks kanonik + sha bobot ppm di web (`web/src/lib/feed.ts`) = gerbang (`engine/feed.py`): pesan yang ditandatangani program penerbit /
    web punya weightsSha yang sama dengan yang dihitung ulang gerbang."""

    def test_canonical_weights_text_and_sha_match_between_web_and_gate(self):
        from engine.tests.test_kode import _ada_node, node_web
        if not _ada_node():
            self.skipTest("Node >= 22.6 tidak ada")
        cases = [{}, {"BTCUSDT": 250_000, "ETHUSDT": -100_000}, {"ETHUSDT": -100_000, "BTCUSDT": 250_000, "XRPUSDT": 0}, {"BTCUSDT": 1_000_000},
                 {"SOLUSDT": -1, "ADAUSDT": 1, "BNBUSDT": 333_333}]
        out = node_web({"weights": cases})
        for w, web in zip(cases, out["weights"]):
            self.assertEqual(web, {"text": F.bobot_kanonik(w), "sha": F.weights_sha(w)})
        self.assertEqual(out["ppm"], [250_000, -100_000, 333_333])


if __name__ == "__main__":
    unittest.main()
