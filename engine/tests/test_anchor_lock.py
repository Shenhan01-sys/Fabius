"""`tools/anchor_lock.py`: bagian murni (pemetaan kunci -> argumen anchor(), tiga hash, catatan anchor di repo). Tidak menyentuh jaringan atau kunci."""
import copy
import json
import os
import sys
import tempfile
import unittest

from engine import locks
from engine.spec import sha0x

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import anchor_lock as al                                      # noqa: E402  (impor ringan: engine + stdlib; `anchor`/.env diimpor malas di main)


def make_lock(note="uji", params=None):
    params = params if params is not None else locks.current_params()
    return {"v": 1, "sha": sha0x(params), "params": params, "dikunci": "2026-01-01T00:00:00Z", "catatan": note}


class PlanTests(unittest.TestCase):
    def test_three_hashes_are_nonzero_32_byte_and_distinct(self):
        p = al.plan(make_lock())
        hs = [p["decisionHash"], p["gatesHash"], p["snapshotHash"]]
        for h in hs:
            self.assertRegex(h, r"^0x[0-9a-f]{64}$")
            self.assertNotEqual(int(h, 16), 0)
        self.assertEqual(len(set(hs)), 3)

    def test_plan_is_deterministic_and_decision_hash_is_the_lock_sha(self):
        lock = make_lock()
        self.assertEqual(al.plan(lock), al.plan(copy.deepcopy(lock)))
        self.assertEqual(al.plan(lock)["decisionHash"], lock["sha"])

    def test_abstain_mapping_and_asset_label(self):
        p = al.plan(make_lock())
        self.assertEqual(p["verdict"], 1)                     # kontrak: Enter=0, Abstain=1; kunci bukan keputusan masuk
        self.assertEqual(p["asset"], "FABIUS-LOCK/review-v1")

    def test_note_changes_the_snapshot_but_not_the_decision_or_gates_hash(self):
        a, b = al.plan(make_lock("satu")), al.plan(make_lock("dua"))
        self.assertEqual((a["decisionHash"], a["gatesHash"]), (b["decisionHash"], b["gatesHash"]))
        self.assertNotEqual(a["snapshotHash"], b["snapshotHash"])      # snapshot mengikat isi berkas, bukan hanya angkanya

    def test_changing_a_gate_number_changes_all_three_hashes(self):
        params = locks.current_params()
        params2 = copy.deepcopy(params)
        params2["gerbang"]["min_net_sharpe"] = 0.6
        a, b = al.plan(make_lock(params=params)), al.plan(make_lock(params=params2))
        for k in ("decisionHash", "gatesHash", "snapshotHash"):
            self.assertNotEqual(a[k], b[k], k)

    def test_changing_a_non_gate_number_keeps_the_gates_hash(self):
        params = locks.current_params()
        params2 = copy.deepcopy(params)
        params2["kpi"]["min_calmar"] = 0.4
        a, b = al.plan(make_lock(params=params)), al.plan(make_lock(params=params2))
        self.assertEqual(a["gatesHash"], b["gatesHash"])
        self.assertNotEqual(a["decisionHash"], b["decisionHash"])

    def test_calldata_layout_matches_the_contract_signature(self):
        try:
            from eth_abi import encode
            from eth_utils import keccak
        except ImportError:
            self.skipTest("eth-abi / eth-utils tidak terpasang")
        p = al.plan(make_lock())
        args = (p["asset"], p["verdict"], bytes.fromhex(p["decisionHash"][2:]), bytes.fromhex(p["gatesHash"][2:]), bytes.fromhex(p["snapshotHash"][2:]))
        data = keccak(text=al.SIG)[:4] + encode(list(al.TYPES), list(args))
        self.assertEqual(al.SIG, "anchor(string,uint8,bytes32,bytes32,bytes32)")
        self.assertEqual(len(data), 228)                      # 4 + 5 kata kepala + (panjang + isi) string 21 byte = 4 + 160 + 64


class LoadLockTests(unittest.TestCase):
    def test_tampered_params_are_refused(self):
        lock = make_lock()
        lock["params"]["gerbang"]["min_net_sharpe"] = 0.1       # sha tidak lagi cocok dengan params
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "x.lock.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(lock, f)
            with self.assertRaises(SystemExit):
                al.load_lock(path)

    def test_missing_file_is_refused(self):
        with self.assertRaises(SystemExit):
            al.load_lock(os.path.join(tempfile.gettempdir(), "tidak-ada-kunci-ini.json"))

    def test_repo_lock_loads_and_the_record_if_present_matches_it(self):
        lock = al.load_lock()                                   # kunci berjalan di repo
        p = al.plan(lock)
        rec = al.record_path(lock)
        if not os.path.exists(rec):
            self.skipTest("kunci ini belum ter-anchor (belum ada catatan)")
        with open(rec, encoding="utf-8") as f:
            r = json.load(f)
        for k in ("decisionHash", "gatesHash", "snapshotHash", "asset"):
            self.assertEqual(r[k], p[k], k)                     # catatan anchor tidak boleh menyimpang dari berkas kunci yang di-commit
        self.assertEqual(r["lock_sha"], lock["sha"])
        self.assertEqual(r["verdict"], "ABSTAIN")
        self.assertRegex(r["tx"], r"^0x[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
