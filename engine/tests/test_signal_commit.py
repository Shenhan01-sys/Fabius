"""Komit sinyal ke SignalAnchor (M3, F-D80): salt, id komit, rekonstruksi tick dari bar, rencana terhadap tiruan chain, calldata vs ABI kontrak, dan
satu jalur penuh di anvil lokal (deploy -> lock -> commit -> reveal) memakai kode yang sama dengan worker Railway.

Uji yang butuh eth-abi/eth-account, artefak `out/` (forge build), atau `anvil` dilewati bila tidak tersedia (engine sendiri tetap stdlib)."""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest

from engine import chain, ledger
from engine.spec import SPECS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import signal_commit as sc                                          # noqa: E402
from paper_tick import Views                                        # noqa: E402

try:
    import eth_abi                                                  # noqa: F401
    import eth_account                                              # noqa: F401
    HAVE_ETH = True
except ImportError:
    HAVE_ETH = False

LEDGER = os.path.join(ROOT, "ledger", "paper")
BARS = os.path.join(ROOT, "ledger", "bars")
OUT = os.path.join(ROOT, "out")
# kunci uji anvil yang diketahui publik (akun #0 dan #1) - bukan rahasia, tidak pernah dipakai di chain 97
DEV_PK0 = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
DEV_PK1 = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
COMMITTER = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"            # alamat DEV_PK1
B3_BAR = 1_790_812_800_000                                          # tick B3 pertama (bar 2026-10-01): 2 sinyal
B3_ASOF_S = (B3_BAR + 86_400_000) // 1000


def tick_of(bot: str, bar: int) -> dict:
    return next(r for r in ledger.load(os.path.join(LEDGER, f"{bot}.jsonl")) if r["type"] == "tick" and r["asof"] == bar)


class FakeChain:
    def __init__(self, max_lag=43_200, window=604_800):
        self.lag, self.window = max_lag, window
        self.locks, self.commits, self.revealed = {}, {}, set()

    def max_lag(self):
        return self.lag

    def reveal_window(self):
        return self.window

    def locked_at(self, committer, bot, spec):
        return self.locks.get((committer.lower(), bot, spec), 0)

    def get_commit(self, cid):
        return self.commits.get(cid, {"committer": sc.ZERO_ADDR, "asof": 0, "committedAt": 0, "n": 0, "revealed": 0, "missed": False,
                                      "botId": sc.ZERO32, "specSha": sc.ZERO32, "root": sc.ZERO32})

    def is_revealed(self, cid, leaf):
        return (cid, leaf) in self.revealed

    def lock(self, bot, at):
        self.locks[(COMMITTER.lower(), bot, SPECS[bot].sha())] = at

    def put_commit(self, bot, asof_s, root, n, revealed=0, committed_at=None):
        cid = sc.commit_id(COMMITTER, bot, SPECS[bot].sha(), asof_s)
        self.commits[cid] = {"committer": COMMITTER, "asof": asof_s, "committedAt": committed_at or asof_s + 3600, "n": n, "revealed": revealed,
                             "missed": False, "botId": chain.ascii32(bot), "specSha": chain.from_hex(SPECS[bot].sha()), "root": root}
        return cid


class PureTests(unittest.TestCase):
    def test_seed_deterministic_and_not_the_key(self):
        s1, s2 = sc.seed_from_key(DEV_PK1), sc.seed_from_key(DEV_PK1)
        self.assertEqual(s1, s2)
        self.assertEqual(len(s1), 32)
        self.assertNotEqual(s1, chain.from_hex(DEV_PK1))
        self.assertNotEqual(s1, sc.seed_from_key(DEV_PK0))

    def test_salts_unique_per_signal_and_deterministic(self):
        views = Views(BARS)
        sigs, probs = sc.rebuild_signals(SPECS["B3-CARRY"], tick_of("B3-CARRY", B3_BAR), views)
        self.assertEqual(probs, [])
        seed = sc.seed_from_key(DEV_PK1)
        salts = [sc.salt_for(seed, s) for s in sigs]
        self.assertEqual(len(set(salts)), len(sigs))
        self.assertEqual(salts, [sc.salt_for(seed, s) for s in sigs])

    @unittest.skipUnless(HAVE_ETH, "eth-abi tidak terpasang")
    def test_commit_id_matches_independent_abi_encoding(self):
        from eth_abi import encode
        from eth_utils import keccak
        spec = SPECS["B3-CARRY"].sha()
        want = keccak(encode(["address", "bytes32", "bytes32", "uint64"], [COMMITTER, chain.ascii32("B3-CARRY"), chain.from_hex(spec), B3_ASOF_S]))
        self.assertEqual(sc.commit_id(COMMITTER, "B3-CARRY", spec, B3_ASOF_S), want)


class RepoLedgerTests(unittest.TestCase):
    """Setiap tick di ledger repo harus bisa direproduksi PERSIS dari bar repo - itulah syarat worker mau mengomit."""

    def test_every_repo_tick_rebuilds_exactly(self):
        views = Views(BARS)
        n = 0
        for bot in sc.BOTS_DEFAULT:
            for r in ledger.load(os.path.join(LEDGER, f"{bot}.jsonl")):
                if r["type"] != "tick":
                    continue
                sigs, probs = sc.rebuild_signals(SPECS[bot], r, views)
                self.assertEqual(probs, [], (bot, r["asof_date"]))
                self.assertEqual([s.id() for s in sigs], r["signal_ids"])
                n += 1
        self.assertGreaterEqual(n, 2)


class PlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.views = Views(BARS)
        cls.seed = sc.seed_from_key(DEV_PK1)
        cls.now = B3_ASOF_S + 10 * 3600                              # 10 jam sesudah penutupan, seperti runner sungguhan

    def plan(self, fc, now=None, seed="default", ledger_dir=LEDGER, bots=("B3-CARRY",)):
        return sc.plan(list(bots), ledger_dir, self.views, fc, COMMITTER, self.seed if seed == "default" else seed, now or self.now)

    def only(self, acts, date="2026-10-01"):
        got = [a for a in acts if a.asof_date == date]
        self.assertEqual(len(got), 1, [a.line() for a in acts])
        return got[0]

    def test_not_locked_is_skipped(self):
        a = self.only(self.plan(FakeChain()))
        self.assertEqual(a.kind, "skip")
        self.assertIn("belum dikunci", a.detail)

    def test_lock_after_bar_is_skipped(self):
        fc = FakeChain()
        fc.lock("B3-CARRY", B3_ASOF_S + 1)
        a = self.only(self.plan(fc))
        self.assertEqual(a.kind, "skip")
        self.assertIn("lebih tua dari kunci", a.detail)

    def test_locked_in_time_commits_two_signals_with_matching_root(self):
        fc = FakeChain()
        fc.lock("B3-CARRY", B3_ASOF_S - 3600)
        a = self.only(self.plan(fc))
        self.assertEqual(a.kind, "commit")
        self.assertEqual(len(a.batch.entries), 2)
        tick = tick_of("B3-CARRY", B3_BAR)
        self.assertEqual(sorted(e.signal.id() for e in a.batch.entries), sorted(tick["signal_ids"]))
        self.assertEqual(a.batch.root, chain.merkle_root([e.leaf for e in a.batch.entries]))
        for e in a.batch.entries:
            self.assertTrue(chain.merkle_verify(list(e.proof), a.batch.root, e.leaf))
        self.assertEqual(a.cid, sc.commit_id(COMMITTER, "B3-CARRY", SPECS["B3-CARRY"].sha(), B3_ASOF_S))

    def test_too_late_is_never_forced(self):
        fc = FakeChain()
        fc.lock("B3-CARRY", B3_ASOF_S - 3600)
        a = self.only(self.plan(fc, now=B3_ASOF_S + 43_200 - 200))
        self.assertEqual(a.kind, "skip")
        self.assertIn("TERLEWAT", a.detail)

    def test_committed_unrevealed_then_partly_then_fully(self):
        fc = FakeChain()
        fc.lock("B3-CARRY", B3_ASOF_S - 3600)
        b = self.only(self.plan(fc)).batch
        cid = fc.put_commit("B3-CARRY", B3_ASOF_S, b.root, 2)
        a = self.only(self.plan(fc))
        self.assertEqual((a.kind, len(a.entries)), ("reveal", 2))
        fc.revealed.add((cid, b.entries[0].leaf))
        fc.commits[cid]["revealed"] = 1
        a = self.only(self.plan(fc))
        self.assertEqual((a.kind, [e.leaf for e in a.entries]), ("reveal", [b.entries[1].leaf]))
        fc.commits[cid]["revealed"] = 2
        self.assertEqual(self.only(self.plan(fc)).kind, "ok")

    def test_onchain_root_different_from_ledger_is_an_alarm(self):
        fc = FakeChain()
        fc.lock("B3-CARRY", B3_ASOF_S - 3600)
        fc.put_commit("B3-CARRY", B3_ASOF_S, b"\x11" * 32, 2)
        a = self.only(self.plan(fc))
        self.assertEqual(a.kind, "alarm")
        self.assertIn("BEDA", a.detail)

    def test_silent_bot_commits_zero_root(self):
        fc = FakeChain()
        fc.lock("B1-TREND", B3_ASOF_S - 3600)
        a = self.only(self.plan(fc, bots=("B1-TREND",)))
        self.assertEqual(a.kind, "commit")
        self.assertEqual((len(a.batch.entries), a.batch.root), (0, sc.ZERO32))

    def test_without_key_reports_need_but_builds_nothing(self):
        fc = FakeChain()
        fc.lock("B3-CARRY", B3_ASOF_S - 3600)
        a = self.only(self.plan(fc, seed=None))
        self.assertEqual(a.kind, "commit")
        self.assertIsNone(a.batch)

    def test_old_ticks_outside_lookback_are_ignored(self):
        acts = self.plan(FakeChain(), now=B3_ASOF_S + 30 * 86400)
        self.assertEqual([a.line() for a in acts if a.asof_date == "2026-10-01"], [])

    def test_resealed_but_altered_tick_is_refused(self):
        """Ledger yang disunting lalu di-seal ulang (rantai hash sah) tetap ketahuan: isi tick tidak bisa direproduksi dari bar -> tidak dikomit."""
        tmp = tempfile.mkdtemp()
        try:
            recs = ledger.load(os.path.join(LEDGER, "B3-CARRY.jsonl"))
            out, prev = [], ledger.ZERO
            for r in recs:
                body = {k: v for k, v in r.items() if k not in ("h", "prev", "v")}
                if body["type"] == "tick" and body["asof"] == B3_BAR:
                    body["targets"] = {"DOTUSDT": 0.125}
                sealed = ledger.seal(body, prev)
                out.append(sealed)
                prev = sealed["h"]
            p = os.path.join(tmp, "B3-CARRY.jsonl")
            for i, r in enumerate(out):
                ledger.append(p, r, out[:i])
            fc = FakeChain()
            fc.lock("B3-CARRY", B3_ASOF_S - 3600)
            a = self.only(self.plan(fc, ledger_dir=tmp))
            self.assertEqual(a.kind, "alarm")
            self.assertIn("targets", a.detail)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


@unittest.skipUnless(HAVE_ETH, "eth-abi tidak terpasang")
class CalldataTests(unittest.TestCase):
    def test_selectors_match_compiled_abi(self):
        paths = {"SignalAnchor": os.path.join(OUT, "SignalAnchor.sol", "SignalAnchor.json"), "LockRegistry": os.path.join(OUT, "LockRegistry.sol", "LockRegistry.json")}
        if not all(os.path.isfile(p) for p in paths.values()):
            self.skipTest("artefak out/ belum ada (forge build)")
        from evm import selector
        ids = {}
        for p in paths.values():
            with open(p, encoding="utf-8") as f:
                ids.update(json.load(f)["methodIdentifiers"])
        for sig in (sc.SIG_COMMIT, sc.SIG_REVEAL, sc.SIG_GET_COMMIT, sc.SIG_IS_REVEALED, sc.SIG_LOCKED_AT, sc.SIG_LOCK, "maxLag()", "revealWindow()"):
            self.assertIn(sig, ids, sig)
            self.assertEqual(selector(sig).hex(), ids[sig], sig)

    def test_reveal_calldata_roundtrip(self):
        from eth_abi import decode
        fc = FakeChain()
        fc.lock("B3-CARRY", B3_ASOF_S - 3600)
        a = sc.plan(["B3-CARRY"], LEDGER, Views(BARS), fc, COMMITTER, sc.seed_from_key(DEV_PK1), B3_ASOF_S + 36_000)[0]
        e = a.batch.entries[0]
        cd = sc.reveal_calldata(a.cid, e)
        cid, tup, salt, proof = decode(["bytes32", sc.SIGNAL_TUPLE, "bytes32", "bytes32[]"], cd[4:])
        self.assertEqual((cid, list(tup), salt, list(proof)), (a.cid, e.signal.abi_fields(), e.salt, list(e.proof)))


@unittest.skipUnless(HAVE_ETH, "eth-account tidak terpasang")
class OperatorLoopTests(unittest.TestCase):
    def test_waiting_state_logged_once_although_repo_head_moves(self):
        """Commit bot ke master tiap ±4 menit tidak boleh membuat log Railway mengulang baris 'menunggu deploy' tiap putaran."""
        import operator_loop as ol
        heads = iter(["a" * 40, "b" * 40, "c" * 40])
        got = []
        orig = (ol.sync, ol.sc.load_addresses, ol.log)
        ol.sync = lambda workdir=None: next(heads)
        ol.sc.load_addresses = lambda path=None: {"anchor": None, "registry": None, "committer": None}
        ol.log = got.append
        try:
            w = ol.Worker(workdir=tempfile.gettempdir())
            for _ in range(3):
                w.once()
        finally:
            ol.sync, ol.sc.load_addresses, ol.log = orig
        self.assertEqual(sum(1 for m in got if m.startswith("menunggu deploy")), 1, got)
        self.assertEqual(sum(1 for m in got if m.startswith("detak:")), 1, got)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@unittest.skipUnless(HAVE_ETH and shutil.which("anvil") and os.path.isfile(os.path.join(OUT, "SignalAnchor.sol", "SignalAnchor.json")),
                     "butuh eth-account + anvil + out/ (forge build)")
class AnvilEndToEndTests(unittest.TestCase):
    """Jalur penuh di chain lokal: deploy -> lock (sebelum bar) -> lompat ke 10 jam sesudah penutupan -> plan + execute (kode worker) -> baca ulang."""

    @classmethod
    def setUpClass(cls):
        import evm
        from eth_abi import encode
        cls.port = _free_port()
        cls.proc = subprocess.Popen(["anvil", "--port", str(cls.port), "--timestamp", str(B3_ASOF_S - 7200), "--silent"],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cls.ev = evm.Evm([f"http://127.0.0.1:{cls.port}"], 31337, receipt_wait_s=20, poll_s=0.2)
        for _ in range(100):
            try:
                cls.ev.chain_check()
                break
            except Exception:
                time.sleep(0.1)
        art = {}
        for name in ("LockRegistry", "SignalAnchor"):
            with open(os.path.join(OUT, f"{name}.sol", f"{name}.json"), encoding="utf-8") as f:
                art[name] = bytes.fromhex(json.load(f)["bytecode"]["object"][2:])
        r1 = cls.ev.send(DEV_PK0, None, art["LockRegistry"])
        cls.registry = r1["contractAddress"]
        r2 = cls.ev.send(DEV_PK0, None, art["SignalAnchor"] + encode(["address", "uint64", "uint64"], [cls.registry, 43_200, 604_800]))
        cls.anchor = r2["contractAddress"]
        for bot in ("B3-CARRY", "B1-TREND"):
            cls.ev.send(DEV_PK1, cls.registry, evm.calldata(sc.SIG_LOCK, ("bytes32", "bytes32", "string"),
                                                             (chain.ascii32(bot), chain.from_hex(SPECS[bot].sha()), f"uji://{bot}")))
        cls.ev.rpc("evm_setNextBlockTimestamp", [B3_ASOF_S + 36_000])
        cls.ev.rpc("evm_mine", [])

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        try:
            cls.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            cls.proc.kill()

    def test_commit_and_reveal_through_worker_code(self):
        cv = sc.AnchorView(self.ev, self.anchor, self.registry)
        self.assertEqual((cv.max_lag(), cv.reveal_window()), (43_200, 604_800))
        self.assertGreater(cv.locked_at(COMMITTER, "B3-CARRY", SPECS["B3-CARRY"].sha()), 0)
        now = self.ev.block_timestamp()
        acts = sc.plan(["B3-CARRY", "B1-TREND"], LEDGER, Views(BARS), cv, COMMITTER, sc.seed_from_key(DEV_PK1), now)
        todo = {(a.bot, a.asof_date): a for a in acts if a.asof_date == "2026-10-01"}
        self.assertEqual(todo[("B3-CARRY", "2026-10-01")].kind, "commit")
        self.assertEqual(todo[("B1-TREND", "2026-10-01")].kind, "commit")
        logs = []
        st = sc.execute(acts, self.ev, self.anchor, DEV_PK1, log=logs.append, settle_s=0)
        self.assertEqual((st["commit"], st["reveal"], st["gagal"]), (2, 2, 0), logs)
        b3 = todo[("B3-CARRY", "2026-10-01")]
        c = cv.get_commit(b3.cid)
        self.assertEqual((c["n"], c["revealed"], bytes(c["root"]), c["asof"]), (2, 2, b3.batch.root, B3_ASOF_S))
        for e in b3.batch.entries:
            self.assertTrue(cv.is_revealed(b3.cid, e.leaf))
        c1 = cv.get_commit(todo[("B1-TREND", "2026-10-01")].cid)
        self.assertEqual((c1["n"], bytes(c1["root"])), (0, sc.ZERO32))
        again = sc.plan(["B3-CARRY", "B1-TREND"], LEDGER, Views(BARS), cv, COMMITTER, sc.seed_from_key(DEV_PK1), self.ev.block_timestamp())
        self.assertEqual({a.kind for a in again if a.asof_date == "2026-10-01"}, {"ok"})          # idempoten: putaran kedua tidak mengirim apa pun

    def test_public_verifier_reads_back_sah(self):
        """P106: pemeriksa publik (tanpa kunci) membaca komit + event Revealed dari chain dan memvonis SAH terhadap ledger + bar repo."""
        import verify_signals as vs
        cv = sc.AnchorView(self.ev, self.anchor, self.registry)
        acts = sc.plan(["B3-CARRY", "B1-TREND"], LEDGER, Views(BARS), cv, COMMITTER, sc.seed_from_key(DEV_PK1), self.ev.block_timestamp())
        sc.execute(acts, self.ev, self.anchor, DEV_PK1, log=lambda m: None, settle_s=0)       # idempoten bila uji komit sudah jalan lebih dulu
        commits = vs.all_commits(cv)
        events = vs.revealed_events(self.ev, self.anchor, 0, int(self.ev.rpc("eth_blockNumber", []), 16))
        rows, st = vs.verify(["B3-CARRY", "B1-TREND"], LEDGER, Views(BARS), cv, commits, events, COMMITTER, self.ev.block_timestamp())
        got = {(r.bot, r.bar): r.vonis for r in rows}
        self.assertEqual((got[("B3-CARRY", "2026-10-01")], got[("B1-TREND", "2026-10-01")]), ("SAH", "SAH"), [(r.bot, r.bar, r.vonis, r.detail) for r in rows])
        self.assertEqual(st["ALARM"], 0)

    def test_contract_reverts_are_named_before_any_gas_is_spent(self):
        import evm
        bogus = sc.commit_id(COMMITTER, "B3-CARRY", SPECS["B3-CARRY"].sha(), 1)
        e = sc.Entry(sc.Signal.from_dict({"v": 1, "bot_id": "B3-CARRY", "spec_sha": SPECS["B3-CARRY"].sha(), "t": B3_BAR, "asof_utc": "x",
                                           "asset": "BTCUSDT", "aksi": "KELUAR", "bobot_lama": 0.1, "bobot_baru": 0.0, "harga_ref": None,
                                           "data_hash": "0x" + "00" * 32}), b"\x01" * 32, b"\x02" * 32, ())
        with self.assertRaises(evm.RpcError) as cm:
            self.ev.send(DEV_PK1, self.anchor, sc.reveal_calldata(bogus, e))
        self.assertEqual(evm.error_name(cm.exception.data, sc.ERRORS), "UnknownCommit(bytes32)")


if __name__ == "__main__":
    unittest.main()
