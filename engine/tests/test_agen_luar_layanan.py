"""P151 + P166: layanan Railway agent luar uji - pilihan analis harian (deterministik, sekali per bar, alasan dipakai ulang), alasan disajikan byte
persis sesudah bar tutup dan DITERIMA pemeriksa gerbang sendiri (`analis.alasan_luar`), loop meja PULL menjawab siklus gerbang sungguhan, image minimal."""
import base64
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "tools"), ROOT]

import agen_luar_layanan as lay                                     # noqa: E402
import analis as an                                                 # noqa: E402
import railway_up                                                   # noqa: E402
from .test_deploy_files import tools_imported_by                    # noqa: E402

DAY = 86_400
B = 1_791_417_600                                                   # 2026-10-08T00:00Z
SEL = "0xc0c16337e6c286ec54902d8de7aadf232587f3b1"


def masukan(br60=0.94, r60=0.32, r30=0.06, fund=0.04, bar_terakhir="2026-10-06", bots=lay.BOTS):
    return {"bar_close": B, "selection_anchor": SEL, "commit_before": B,
            "masukan": {"v": 1, "untuk_penutupan_bar": "2026-10-08T00:00:00Z", "bot": {b: {"status": "INTI"} for b in bots},
                        "rezim_pasar": {"bar_terakhir": bar_terakhir, "breadth_di_atas_60h": br60, "btc_ret_60h": r60, "btc_ret_30h": r30,
                                        "funding_rata_7h_tahunan": fund}}}


class Rantai:
    """SelectionAnchor palsu: picks {(agent, close): (bot, keyakinan, reasonHash)}; `gagal` = kiriman berikutnya gagal (revert / RPC)."""

    def __init__(self):
        self.picks, self.kiriman, self.gagal = {}, [], 0

    def sudah(self, sel, aid, close):
        return (aid, close) in self.picks

    def kirim(self, sel, aid, close, bot, k, rh):
        self.kiriman.append((sel, aid, close, bot, k, rh))
        if self.gagal:
            self.gagal -= 1
            return {"ok": False, "tx": "0xgagal"}
        self.picks[(aid, close)] = (bot, k, rh)
        return {"ok": True, "tx": "0x" + "ab" * 32}


class KeputusanTests(unittest.TestCase):
    def test_each_regime_maps_to_its_rule_bot_and_the_reasoning_is_deterministic_and_in_the_external_schema(self):
        kasus = {"B1-TREND": masukan(), "B3-CARRY": masukan(br60=0.3, fund=0.15), "B6-BOUNCE": masukan(br60=0.3, r60=-0.2, r30=-0.15),
                 "B5-CORE-RWA": masukan(br60=0.4, r60=0.05)}
        for bot, inp in kasus.items():
            with self.subTest(bot=bot):
                a = lay.keputusan(inp, 2573)
                self.assertEqual(a["pilihan"]["bot"], bot)
                self.assertTrue(30 <= a["pilihan"]["keyakinan"] <= 70)
                self.assertEqual((a["agent_id"], a["bar_close"]), (2573, B))
                self.assertTrue(set(an.SKEMA_ALASAN) <= set(a) | {"nama", "model"})
                self.assertTrue(set(an.SKEMA_ALASAN["pilihan"]) <= set(a["pilihan"]))
                self.assertEqual(lay.canon(lay.keputusan(json.loads(json.dumps(inp)), 2573)), lay.canon(a))      # deterministik, tanpa jam
                self.assertEqual(lay.sha(a), an.sha(a))                                                        # reasonHash = rumus gerbang
        tanpa_b1 = lay.keputusan(masukan(bots=("B3-CARRY", "B5-CORE-RWA")), 2573)
        self.assertEqual(tanpa_b1["pilihan"]["bot"], "B3-CARRY")                                               # bot aturan tidak ditawarkan

    def test_the_service_refuses_other_secret_like_variables(self):
        self.assertEqual(lay.rahasia_lain({"AGEN_LUAR_UJI_KEY": "0x", "PORT": "1", "RAILWAY_SERVICE_NAME": "x", "PYTHONHASHSEED": "0"}), [])
        self.assertEqual(lay.rahasia_lain({"AGEN_LUAR_UJI_KEY": "0x", "COMMITTER_PRIVATE_KEY": "0x", "GH_TOKEN": "t"}),
                         ["COMMITTER_PRIVATE_KEY", "GH_TOKEN"])


class AnalisTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.arsip, self.rantai = lay.Arsip(self.tmp, 2573), Rantai()

    def test_the_pick_waits_for_fresh_data_then_commits_once_and_never_after_the_close(self):
        basi = masukan(bar_terakhir="2026-10-05")
        self.assertEqual(lay.langkah_analis(basi, 2573, self.arsip, self.rantai, B - 10 * 3600, log=lambda m: None), "tunggu-data")
        self.assertEqual(self.rantai.kiriman, [])
        self.assertEqual(lay.langkah_analis(masukan(), 2573, self.arsip, self.rantai, B - 10 * 3600, log=lambda m: None), "dikomit")
        sel, aid, close, bot, k, rh = self.rantai.kiriman[0]
        with open(os.path.join(self.tmp, f"{B}.json"), "rb") as f:
            self.assertEqual(rh, lay.sha(f.read()))                                                            # hash = byte yang disimpan
        self.assertEqual((sel, aid, close, bot), (SEL, 2573, B, "B1-TREND"))
        self.assertEqual(lay.langkah_analis(masukan(), 2573, self.arsip, self.rantai, B - 9 * 3600, log=lambda m: None), "sudah")
        self.assertEqual(lay.langkah_analis(masukan(), 2573, self.arsip, self.rantai, B, log=lambda m: None), "lewat")
        self.assertEqual(len(self.rantai.kiriman), 1)
        self.assertEqual(lay.langkah_analis(basi, 2573, lay.Arsip(os.path.join(self.tmp, "b"), 2573), Rantai(), B - 3600, log=lambda m: None),
                         "dikomit")                                                                            # cadangan 2 jam: data basi tetap dipakai

    def test_a_failed_send_keeps_the_written_reasoning_so_the_hash_never_changes(self):
        self.rantai.gagal = 1
        self.assertEqual(lay.langkah_analis(masukan(), 2573, self.arsip, self.rantai, B - 5 * 3600, log=lambda m: None), "gagal")
        lain = masukan(br60=0.2, fund=0.2)                                                                     # masukan gerbang berubah sesudahnya
        self.assertEqual(lay.langkah_analis(lain, 2573, self.arsip, self.rantai, B - 4 * 3600, log=lambda m: None), "dikomit")
        self.assertEqual(self.rantai.kiriman[0][5], self.rantai.kiriman[1][5])                                  # alasan pertama dipakai ulang
        self.assertEqual(self.rantai.kiriman[1][3], "B1-TREND")

    def test_sends_that_reached_the_chain_and_failed_stop_after_the_gas_cap_but_estimate_reverts_do_not_count(self):
        class Mahal(Rantai):
            def kirim(self, *a):
                self.kiriman.append(a)
                if len(self.kiriman) == 1:
                    raise RuntimeError("RpcError: execution reverted (estimateGas)")                           # nol gas, tidak dihitung
                return {"ok": False, "tx": "0xrevert"}                                                         # tertambang + revert = gas terbakar
        r = Mahal()
        st = [lay.langkah_analis(masukan(), 2573, self.arsip, r, B - 6 * 3600 + i, log=lambda m: None) for i in range(6)]
        self.assertEqual(st, ["gagal"] * 4 + ["berhenti"] * 2)
        self.assertEqual((len(r.kiriman), self.arsip.catatan(B)["terkirim"]), (4, lay.MAKS_TERKIRIM))


class AlasanHttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.arsip, self.rantai, self.jam = lay.Arsip(self.tmp, 2573), Rantai(), [B - 3600]
        self.srv = lay.buat_server(self.arsip, {"uji": True}, now=lambda: self.jam[0], host="127.0.0.1", port=0)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        self.base = f"http://127.0.0.1:{self.srv.server_address[1]}"

    def ambil(self, path):
        import urllib.error
        import urllib.request
        try:
            with urllib.request.urlopen(self.base + path, timeout=10) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def test_reasons_are_served_only_after_the_close_byte_exact_and_rebuilt_from_the_input_copy(self):
        self.assertEqual(lay.langkah_analis(masukan(), 2573, self.arsip, self.rantai, B - 3600, log=lambda m: None), "dikomit")
        with open(os.path.join(self.tmp, f"{B}.json"), "rb") as f:
            asli = f.read()
        self.assertEqual(self.ambil(f"/reasons/{B}.json")[0], 404)                                            # bar belum tutup: tidak bocor
        self.jam[0] = B + 60
        self.assertEqual(self.ambil(f"/reasons/{B}.json"), (200, asli))
        os.remove(os.path.join(self.tmp, f"{B}.json"))                                                          # berkas alasan hilang
        self.assertEqual(self.ambil(f"/reasons/{B}.json"), (200, asli))                                        # dibangun ulang persis dari salinan masukan
        self.assertEqual(self.ambil(f"/reasons/{B + DAY}.json")[0], 404)
        self.assertEqual(json.loads(self.ambil("/health")[1])["agent_id"], 2573)

    def test_the_gate_own_external_verifier_accepts_the_served_reasoning_and_reads_the_card_template(self):
        self.assertEqual(lay.langkah_analis(masukan(), 2573, self.arsip, self.rantai, B - 3600, log=lambda m: None), "dikomit")
        bot, k, rh = self.rantai.picks[(2573, B)]
        self.jam[0] = B + 120
        import agen_luar_uji as alu
        tpl = alu.reasons_url("agen-luar-uji-production.up.railway.app")
        self.assertEqual(tpl, "https://agen-luar-uji-production.up.railway.app/reasons/{bar_close}.json")
        kartu = {"name": "Fabius external test agent (rule-based)", "fabius": {"reasons": tpl}}

        class Ev:
            def call_decode(self, to, sig, types, values, out):
                assert sig == "tokenURI(uint256)"
                return ("data:application/json;base64," + base64.b64encode(json.dumps(kartu).encode()).decode(),)
        k_luar = an.kartu_luar(Ev(), "0xid", 2573)
        self.assertEqual((k_luar["alasan_url"], k_luar["galat"]), (tpl, None))

        def fetch(url):                                                                                         # https publik -> server lokal
            return self.ambil(re.sub(r"^https://[^/]+", "", url))[1]
        picks = [{"agent": "x2573", "agent_id": 2573, "bar_close": B, "bot": bot, "keyakinan": k, "reasonHash": rh}]
        out_dir, logs = os.path.join(self.tmp, "gerbang"), []
        self.assertEqual(an.alasan_luar(picks, {2573: k_luar}, out_dir, B + 120, fetch=fetch, log=logs.append), 1, logs)
        rec = an.records([out_dir])[0]
        self.assertEqual((rec["luar"], rec["bot"], rec["reasonHash"]), (True, bot, rh))
        salah = [{**picks[0], "reasonHash": "0x" + "cc" * 32}]
        self.assertEqual(an.alasan_luar(salah, {2573: k_luar}, os.path.join(self.tmp, "g2"), B + 120, fetch=fetch, log=logs.append), 0)


try:
    from .test_agen_luar import KEY_A, HAVE_ETH, identitas
    from .test_meja2 import FakePasar, UNI, out
except Exception:  # noqa: BLE001
    HAVE_ETH = False


class LoopMejaTests(unittest.TestCase):
    def test_a_pull_404_after_a_gate_redeploy_rejoins_then_the_cycle_is_answered(self):
        from unittest import mock
        import desk_agent_client as dc
        pulls = iter([(404, {"error": "unknown agent"}), (200, {"siklus": 1_791_200_100, "prompt": ""})])
        join, answer = mock.Mock(return_value=(201, {"registered": True})), mock.Mock(return_value=(200, {"ok": True}))
        status = {}
        with mock.patch.object(dc, "join", join), mock.patch.object(dc, "pull", lambda *a, **k: next(pulls)), mock.patch.object(dc, "answer", answer):
            lay.loop_meja("http://g", 2573, "0xk", status, threading.Event(), log=lambda m: None, sekali=True)
        self.assertEqual(join.call_count, 2)
        self.assertEqual(answer.call_count, 1)
        self.assertEqual(status["siklus_terakhir"]["siklus"], 1_791_200_100)


@unittest.skipUnless(HAVE_ETH, "butuh eth-account")
class MejaTests(unittest.TestCase):
    def setUp(self):
        from http.server import ThreadingHTTPServer
        import x402_sinyal as xs
        self.tmp = tempfile.mkdtemp()
        old, os.environ["ANALIS_DIR"] = os.environ.get("ANALIS_DIR"), os.path.join(self.tmp, "analis")
        self.addCleanup(lambda: os.environ.pop("ANALIS_DIR") if old is None else os.environ.update(ANALIS_DIR=old))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.g = xs.Gate(xs.Data(ROOT), "0xk", "https://g", "https://w", log=lambda m: None)
        self.g.luar.resolve = identitas({2573: (KEY_A, None, "Fabius external test agent")})
        srv = ThreadingHTTPServer(("127.0.0.1", 0), xs.make_handler(self.g))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        self.url = f"http://127.0.0.1:{srv.server_address[1]}"

    def test_the_service_desk_loop_joins_pulls_and_its_rule_answer_is_recorded_ok_in_a_real_gate_cycle(self):
        import meja2
        status, stop = {}, threading.Event()
        th = threading.Thread(target=lay.loop_meja, args=(self.url, 2573, KEY_A, status, stop), kwargs={"log": lambda m: None, "sekali": True},
                              daemon=True)
        th.start()
        for _ in range(200):
            if self.g.luar.terlihat:
                break
            time.sleep(0.05)
        self.assertTrue(self.g.luar.terlihat)
        self.assertEqual(status["join"]["http"], 201)

        def call(ag, system, user):
            if ag.get("luar"):
                return self.g.luar.minta(ag, system, user, ag["siklus"], ag["validasi"], ag.get("tenggat"))
            return out()
        agents = [{"slug": s, "agent_id": i, "model": "m"} for i, s in enumerate(["a", "b", "c"], 1)] + self.g.luar.agents()
        books = {"_v2_kursi": {"kursi": {s: {"status": "aktif", "sejak": 0} for s in ("a", "b", "c")}}}
        get = lambda url: [{"symbol": a, "markPrice": "100", "lastFundingRate": "0"} for a in UNI]       # noqa: E731
        rek, _ = meja2.siklus2(1_791_200_100, agents, books, {}, call, {"sha": "0x1", "fitur_aset": {"SOLUSDT": {"r_1j": 0.01}}, "fitur_bot": {}},
                               FakePasar(), get=get, log=lambda m: None, bukti=self.g.luar.bukti)
        th.join(30)
        stop.set()
        x = next(r for r in rek if r["agent"] == "v2:x2573")
        self.assertEqual((x["status"], x["kursi"]), ("ok", "uji"), x.get("galat"))
        self.assertEqual(status["siklus_terakhir"]["http"], 200)


class ImageTests(unittest.TestCase):
    def test_the_service_image_copies_exactly_its_archive_and_every_module_it_imports(self):
        with open(os.path.join(ROOT, "railway", "agen-luar-uji", "Dockerfile"), encoding="utf-8") as f:
            dock = f.read()
        copied = {x for ln in dock.splitlines() if ln.startswith("COPY ") for x in re.findall(r"(tools/[A-Za-z0-9_]+\.py)", ln)}
        paths = railway_up.PATHS_LAYANAN["agen-luar-uji"]
        self.assertEqual(copied, {p for p in paths if p.endswith(".py")})
        need = set()
        for f in copied:
            need |= tools_imported_by(os.path.join(ROOT, f))
        self.assertEqual(sorted(need - copied), [])                                                            # tanpa engine / alat worker
        self.assertIn("USER agen", dock)
        self.assertNotIn("COPY engine", dock)

    def _image(self):
        """Folder kosong berisi HANYA berkas yang di-COPY image (tanpa engine/) -> python -E (abaikan PYTHONPATH) dengan cwd di sana."""
        import subprocess
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "tools"))
        for p in railway_up.PATHS_LAYANAN["agen-luar-uji"]:
            if p.endswith(".py"):
                shutil.copy(os.path.join(ROOT, p), os.path.join(tmp, p))
        env = {k: v for k, v in os.environ.items() if not lay.RAHASIA.search(k)}
        return tmp, env, lambda args, **kw: subprocess.run([sys.executable, "-E", "-X", "utf8", *args], cwd=tmp, capture_output=True, text=True,
                                                           timeout=60, **kw)

    @unittest.skipUnless(HAVE_ETH, "butuh eth-abi")
    def test_without_the_engine_package_the_image_builds_the_same_pick_and_getpick_calldata(self):
        import evm
        _, env, run = self._image()
        kode = ("import sys; sys.path.insert(0, 'tools'); import agen_luar_layanan as lay, evm\n"
                f"print(evm.calldata(lay.SIG_PICK, ('uint256','uint64','bytes32','uint8','bytes32'), (2573, {B}, lay.ascii32('B1-TREND'), 55,"
                " bytes(range(32)))).hex())\n"
                f"print(evm.calldata('getPick(uint256,uint64)', ('uint256','uint64'), (2573, {B})).hex())\n"
                "print('engine' in sys.modules)")
        r = run(["-c", kode], env=env)
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        want = [evm.calldata(lay.SIG_PICK, ("uint256", "uint64", "bytes32", "uint8", "bytes32"), (2573, B, lay.ascii32("B1-TREND"), 55,
                                                                                                   bytes(range(32)))).hex(),
                evm.calldata("getPick(uint256,uint64)", ("uint256", "uint64"), (2573, B)).hex(), "False"]
        self.assertEqual(r.stdout.split(), want)                                                               # Keccak eth_utils == engine.chain

    def test_the_image_entrypoint_refuses_to_start_with_another_secret_and_without_the_key(self):
        _, env, run = self._image()
        r = run(["tools/agen_luar_layanan.py"], env={**env, lay.VAR_KUNCI: "0x" + "11" * 32, "GH_TOKEN": "x"})
        self.assertEqual(r.returncode, 3)
        self.assertIn("MENOLAK MULAI", r.stdout)
        self.assertIn("GH_TOKEN", r.stdout)
        self.assertNotIn("11" * 32, r.stdout + r.stderr)
        self.assertEqual(run(["tools/agen_luar_layanan.py"], env=env).returncode, 2)


if __name__ == "__main__":
    unittest.main()
