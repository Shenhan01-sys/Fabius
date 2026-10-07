"""P167b (epik 12 §3.2): jenis `code` - analisis statis daftar-izin, sandbox proses anak berbatas, dua jalan identik, uji kausalitas, G1/G5 atas
parameter bernama, hitungan percobaan, jalur PRIVAT (kode tidak pernah publik; pelari terpisah mengembalikan DATA yang divalidasi lagi).

Tes bermusuhan: tiap upaya kabur (impor, dunder, bingkai generator, format string, builtins berbahaya, try/except, global, kelas, yield, unicode
yang dinormalisasi ke `eval`), bom sumber daya (perulangan tanpa akhir, CPU di builtin, memori, int raksasa, rekursi, keluaran raksasa), dan
nondeterminisme (urutan set lewat PYTHONHASHSEED, keadaan global, argumen bawaan yang bisa diubah)."""
import copy
import json
import os
import shutil
import stat
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "tools"), ROOT]

from engine import gates, kode, review as reviewmod, submission     # noqa: E402
from engine.bots import NULL_KIND, REGISTRY                       # noqa: E402
from engine.series import DAY_MS                                  # noqa: E402
from engine.spec import SPECS, BotSpec                            # noqa: E402
from engine.tests.helpers import T0, md_perp, regime_closes, walk  # noqa: E402

B = {"cpu_s": 3, "waktu_dinding_s": 20, "memori_mb": 256, "langkah_per_panggilan": 20_000}
H = "PARAMS = {'N': 5}\ndef target(bars, params):\n"

TREN = '''"""tren: long bila penutupan > penutupan N bar lalu (bobot sama atas aset yang punya bar hari ini)"""
PARAMS = {"N": 20}
DAY = 86400000


def target(bars, params):
    n = params["N"]
    t = max(bars[a]["t"][-1] for a in bars)
    avail = [a for a in sorted(bars) if bars[a]["t"][-1] == t]
    out = {}
    for a in avail:
        ts = bars[a]["t"]
        c = bars[a]["c"]
        back = t - n * DAY
        j = len(ts) - 1
        while j >= 0 and ts[j] > back:
            j = j - 1
        if j >= 0 and ts[j] == back and c[-1] > c[j]:
            out[a] = 1.0 / len(avail)
    return out
'''


def md_kecil(n=260):
    return md_perp({"BTCUSDT": regime_closes(n, 1), "ETHUSDT": regime_closes(n, 2), "BNBUSDT": walk(n, 3)})


def jalan(src, md=None, varian=None, sampel=True, batas=B):
    md = md or md_kecil(160)
    bars = kode.bars_payload(md, list(md.perp))
    grid = sorted({t for a in bars for t in bars[a]["t"]})
    m, info = kode.periksa(src)
    assert not m, m
    return kode.jalankan(src, bars, varian or {"dasar": info["params"]}, kode.sampel_kausal(grid, 8) if sampel else [], "dasar", batas)


class StatikTests(unittest.TestCase):
    """Lapis 1: daftar-izin AST. Semua yang tidak diizinkan ditolak SEBELUM ada proses yang dijalankan; `periksa` tidak pernah melempar."""

    def test_the_contract_example_passes_and_reports_sha_size_and_named_params(self):
        m, info = kode.periksa(TREN)
        self.assertEqual(m, [])
        self.assertEqual((info["params"], info["ukuran"], info["sha"]), ({"N": 20}, len(TREN.encode()), kode.sha_kode(TREN)))
        import pengajuan as pj
        self.assertEqual(kode.periksa(pj.KODE_CONTOH)[0], [])                                  # contoh di editor web juga sah

    def test_every_escape_attempt_is_rejected_statically(self):
        hostile = {
            "import os": "import os\n" + H + "    return {}\n",
            "import sys": "import sys\n" + H + "    return {}\n",
            "import socket": "import socket\n" + H + "    return {}\n",
            "from os import path": "from os import path\n" + H + "    return {}\n",
            "from math import *": "from math import *\n" + H + "    return {}\n",
            "alias underscore": "import math as _m\n" + H + "    return {}\n",
            "dunder class": H + "    return {}.__class__\n",
            "subclasses": H + "    return ().__class__.__bases__[0].__subclasses__()\n",
            "func globals": H + "    return target.__globals__\n",
            "__builtins__": H + "    return __builtins__\n",
            "__import__": H + "    return __import__('os')\n",
            "gen frame": H + "    g = (x for x in [1])\n    return g.gi_frame.f_globals\n",
            "statistics.sys": "import statistics\n" + H + "    return statistics.sys\n",
            "statistics.random": "import statistics\n" + H + "    return statistics.random\n",
            "str.format": H + "    return '{0.__class__}'.format(1)\n",
            "open": H + "    return open('/etc/passwd')\n",
            "eval": H + "    return eval('1')\n",
            "exec": H + "    exec('x=1')\n    return {}\n",
            "compile": H + "    return compile('1', 'x', 'eval')\n",
            "getattr": H + "    return getattr(1, 'real')\n",
            "vars": H + "    return vars()\n",
            "globals": H + "    return globals()\n",
            "type": H + "    return type(1)\n",
            "print": H + "    print(1)\n    return {}\n",
            "id": H + "    return {'BTCUSDT': id(bars) % 2}\n",
            "hash": H + "    return {'BTCUSDT': hash('x') % 2}\n",
            "try": H + "    try:\n        return {}\n    except BaseException:\n        return {}\n",
            "with": H + "    with x:\n        pass\n    return {}\n",
            "class": "class A:\n    pass\n" + H + "    return {}\n",
            "global": H + "    global Y\n    return {}\n",
            "nonlocal": "PARAMS = {'N': 5}\ndef f():\n    x = 1\n    def g():\n        nonlocal x\n    return g\ndef target(bars, params):\n    return {}\n",
            "yield": "PARAMS = {'N': 5}\ndef f():\n    yield 1\ndef target(bars, params):\n    return {}\n",
            "async": "PARAMS = {'N': 5}\nasync def f():\n    return 1\ndef target(bars, params):\n    return {}\n",
            "del": H + "    x = 1\n    del x\n    return {}\n",
            "raise": H + "    raise ValueError()\n",
            "assert": H + "    assert True\n    return {}\n",
            "f-string": H + "    return {f'{bars}': 0}\n",
            "walrus": H + "    if (x := 1):\n        pass\n    return {}\n",
            "decorator": "PARAMS = {'N': 5}\n@staticmethod\ndef target(bars, params):\n    return {}\n",
            "annotation": "PARAMS = {'N': 5}\ndef target(bars: dict, params):\n    return {}\n",
            "starred": H + "    return max(*[1, 2])\n",
            "attribute store": H + "    target.cache = 1\n    return {}\n",
            "kwargs splat": H + "    return dict(**params)\n",
            "unicode eval": H + "    return \uff45\uff56\uff41\uff4c('1')\n",
            "unicode dunder": H + "    return {}.\uff3f\uff3fclass\uff3f\uff3f\n",
            "bidi char": H + "    return {} # \u202e\n",
            "bytes literal": H + "    return {b'x': 1}\n",
            "long string": H + "    return {'" + "x" * 100 + "': 0}\n",
            "module computation": "PARAMS = {'N': 5}\nX = len([1, 2])\ndef target(bars, params):\n    return {}\n",
            "module loop": "PARAMS = {'N': 5}\nfor i in range(3):\n    pass\ndef target(bars, params):\n    return {}\n",
            "no target": "PARAMS = {'N': 5}\ndef f(bars, params):\n    return {}\n",
            "two targets": H + "    return {}\ndef target(bars, params):\n    return {}\n",
            "target arity": "PARAMS = {'N': 5}\ndef target(bars):\n    return {}\n",
            "target default state": "PARAMS = {'N': 5}\ndef target(bars, params, memo=[]):\n    return {}\n",
            "no PARAMS": "def target(bars, params):\n    return {}\n",
            "PARAMS zero": "PARAMS = {'N': 0}\ndef target(bars, params):\n    return {}\n",
            "PARAMS bool": "PARAMS = {'N': True}\ndef target(bars, params):\n    return {}\n",
            "PARAMS nan": "PARAMS = {'N': float('nan')}\ndef target(bars, params):\n    return {}\n",
            "PARAMS too many": "PARAMS = {" + ", ".join(f"'P{i}': 1" for i in range(7)) + "}\ndef target(bars, params):\n    return {}\n",
            "PARAMS bad name": "PARAMS = {'_x': 1}\ndef target(bars, params):\n    return {}\n",
            "PARAMS twice": "PARAMS = {'N': 1}\nPARAMS = {'N': 2}\ndef target(bars, params):\n    return {}\n",
            "syntax": H + "    return {\n",
            "too big": H + "    return {}\n" + "#" * (16 * 1024),
            "deep nesting": H + "    return " + "(" * 400 + "1" + ")" * 400 + "\n",
            "many nodes": H + "    x = [" + ", ".join(["1"] * 5000) + "]\n    return {}\n",
        }
        for name, src in hostile.items():
            with self.subTest(name=name):
                m, info = kode.periksa(src)
                self.assertTrue(m, f"{name} lolos analisis statis")
                self.assertEqual(info, {})
        for junk in (None, b"PARAMS={}", {"x": 1}, 12, "", "   "):
            self.assertTrue(kode.periksa(junk)[0])                                                  # tidak pernah melempar

    def test_problems_never_echo_the_submitted_code_text(self):
        m, _ = kode.periksa(H + "    return {}.rahasia_penerbit_xyz\n")
        self.assertTrue(m)
        self.assertFalse(any("rahasia_penerbit_xyz" in x and len(x) > 200 for x in m))
        self.assertTrue(all(len(x) < 200 for x in m))

    def test_meta_in_the_public_form_must_match_the_private_text(self):
        m, info = kode.periksa(TREN)
        meta = {"sha": info["sha"], "ukuran": info["ukuran"], "params": {"N": 20}}
        self.assertEqual(kode.validate_meta(meta), [])
        self.assertEqual(kode.cocok_meta(TREN, meta), [])
        self.assertTrue(kode.cocok_meta(TREN.replace("20", "21"), meta))                           # teks lain = sha lain
        self.assertTrue(kode.cocok_meta(TREN, dict(meta, params={"N": 21})))                     # PARAMS yang ditandatangani harus sama
        self.assertTrue(kode.validate_meta(dict(meta, kode=TREN)))                               # teks kode tidak boleh ikut formulir publik
        self.assertTrue(kode.validate_meta(dict(meta, sha="0x" + "AB" * 32)))


class SandboxTests(unittest.TestCase):
    """Lapis 2-5: proses anak berbatas, keluaran diperiksa, dua jalan identik, uji kausalitas namespace segar."""

    def test_a_clean_program_runs_twice_identically_and_passes_the_causality_samples(self):
        r = jalan(TREN)
        self.assertTrue(r["ok"], r["galat"])
        self.assertIs(r["deterministik"], True)
        self.assertGreater(r["kausal"]["n"], 0)
        self.assertEqual(r["kausal"]["beda"], [])

    def test_the_program_never_sees_a_bar_after_the_one_it_is_called_for(self):
        src = H + "    t = bars['BTCUSDT']['t'][-1]\n    return {'BTCUSDT': (t - %d) / 1e12}\n" % T0
        r = jalan(src, sampel=False)
        self.assertTrue(r["ok"], r["galat"])
        for t, w in r["varian"]["dasar"]:
            self.assertEqual(w, {"BTCUSDT": (t - T0) / 1e12} if t != T0 else {})                    # bar terakhir yang terlihat = bar panggilan itu
        r = jalan(H + "    c = bars['BTCUSDT']['c']\n    return {'BTCUSDT': 0.1 if c[len(c)] > 0 else 0.0}\n", sampel=False)
        self.assertEqual((r["ok"], r["galat"]), (False, "galat IndexError"))                         # mengintip satu bar ke depan = galat, bukan nilai

    def test_resource_bombs_are_stopped_by_the_right_layer(self):
        cases = {
            "infinite loop": (H + "    while True:\n        pass\n", "anggaran langkah habis"),
            "loop inside a builtin": (H + "    return {'BTCUSDT': sum(range(10 ** 12)) * 0}\n", "batas CPU"),
            "memory bomb": (H + "    x = [0] * (10 ** 9)\n    return {}\n", "batas memori"),
            "huge string": (H + "    s = 'x' * (10 ** 9)\n    return {}\n", "batas memori"),
            "giant integer": (H + "    x = 10 ** (10 ** 8)\n    return {}\n", "batas CPU"),
            "recursion": ("PARAMS = {'N': 5}\ndef f(n):\n    return f(n + 1)\ndef target(bars, params):\n    return f(0)\n", "rekursi terlalu dalam"),
            "huge output": (H + "    return {str(i): 0.0 for i in range(10 ** 6)}\n", "anggaran langkah habis"),
        }
        for name, (src, want) in cases.items():
            with self.subTest(name=name):
                r = jalan(src, sampel=False)
                self.assertFalse(r["ok"])
                self.assertIn(want, r["galat"])
                self.assertEqual(r["varian"], {})                                                  # gagal = tidak ada bobot sama sekali

    def test_bad_outputs_and_mutation_attempts_fail_closed(self):
        cases = {
            "gross above one": ("return {'BTCUSDT': 0.8, 'ETHUSDT': -0.5}", "gross > 1"),
            "nan": ("return {'BTCUSDT': float('nan')}", "tidak terhingga"),
            "inf": ("return {'BTCUSDT': float('inf')}", "tidak terhingga"),
            "asset outside the data": ("return {'XRPUSDT': 0.1}", "aset di luar data"),
            "not a dict": ("return [1]", "bukan dict"),
            "text weight": ("return {'BTCUSDT': '0.5'}", "bobot bukan angka"),
            "bool weight": ("return {'BTCUSDT': True}", "bobot bukan angka"),
            "mutate bars": ("bars['BTCUSDT'] = 1\n    return {}", "galat TypeError"),
            "mutate tuple": ("c = bars['BTCUSDT']['c']\n    c[0] = 1\n    return {}", "galat TypeError"),
            "import at runtime of a disallowed member": ("import math\n    return {'BTCUSDT': math.sqrt(-1)}", "galat ValueError"),
        }
        for name, (body, want) in cases.items():
            with self.subTest(name=name):
                r = jalan(H + "    " + body + "\n", sampel=False)
                self.assertFalse(r["ok"])
                self.assertIn(want, r["galat"])

    def test_nondeterminism_through_hash_randomisation_is_caught_by_the_second_process(self):
        src = H + "    order = list({'a' + str(i) for i in range(64)})\n    return {'BTCUSDT': order.index('a0') / 100}\n"
        r = jalan(src, sampel=False)
        self.assertTrue(r["ok"])
        self.assertIs(r["deterministik"], False)
        self.assertIn("tidak deterministik", r["galat"])

    def test_state_leaking_through_globals_or_mutable_defaults_is_caught_by_fresh_namespace_samples(self):
        glob = "PARAMS = {'N': 5}\nSEEN = []\ndef target(bars, params):\n    SEEN.append(1)\n    return {'BTCUSDT': 0.5} if len(SEEN) % 2 == 0 else {}\n"
        dflt = ("PARAMS = {'N': 5}\ndef helper(x, memo=[]):\n    memo.append(x)\n    return len(memo)\n"
                "def target(bars, params):\n    return {'BTCUSDT': 0.5} if helper(1) > 3 else {}\n")
        for src in (glob, dflt):
            r = jalan(src)
            self.assertTrue(r["ok"])
            self.assertIs(r["deterministik"], True)                                                  # berulang identik, tetapi bergantung riwayat
            self.assertTrue(r["kausal"]["beda"], "kebocoran keadaan tidak tertangkap")

    def test_the_child_has_no_environment_and_no_repo_on_its_path(self):
        with open(kode.__file__, encoding="utf-8") as f:
            self.assertIn('"-s", "-S", "-P"', f.read())                                               # tanpa direktori skrip / site di sys.path
        with open(kode.ANAK, encoding="utf-8") as f:
            src = f.read()
        self.assertNotIn("from engine", src)
        self.assertNotIn("import engine", src)
        for lim in ("RLIMIT_CPU", "RLIMIT_AS", "RLIMIT_FSIZE", "RLIMIT_NOFILE", "RLIMIT_CORE"):
            self.assertIn(lim, src)


class EngineTests(unittest.TestCase):
    """Integrasi: REGISTRY["CODE"] -> gerbang G1-G11 yang sama; G1 = uji kausalitas + determinisme; G5 atas PARAMS bernama; G8 bawaan waktu."""

    def setUp(self):
        self.lama = kode.pasang_pelari(kode.PelariLokal(batas=B))
        self.addCleanup(kode.pasang_pelari, self.lama)

    def spec(self, src, params=None, uni=("BTCUSDT", "ETHUSDT", "BNBUSDT")):
        sha = kode.pelari().daftarkan(src)
        m, info = kode.periksa(src)
        self.assertEqual(m, [])
        return BotSpec(bot_id="KODE-X", metode="uji", param_nama=kode.PARAM_NAMA, param=sha,
                       konstanta={"kode": {"sha": sha, "ukuran": info["ukuran"], "params": params or info["params"]}}, universe=tuple(uni),
                       penggaris=dict(kode.PENGGARIS), template=kode.KODE_METHOD)

    def test_a_code_version_of_b1_gives_the_same_weights_as_the_template_on_the_same_bars(self):
        md = md_kecil(300)
        sp = self.spec(TREN, {"N": 20})
        got = REGISTRY["CODE"](sp, md)
        b1 = REGISTRY["B1-TREND"](BotSpec(**{**SPECS["B1-TREND"].__dict__, "param": 20, "universe": ("BTCUSDT", "ETHUSDT", "BNBUSDT")}), md)
        self.assertEqual([(t.t, t.weights) for t in got], [(t.t, t.weights) for t in b1])
        self.assertGreater(sum(1 for t in got if t.weights), 50)

    def test_g1_passes_a_clean_program_and_fails_a_history_dependent_one(self):
        md = md_kecil(160)
        c = gates._Ctx(self.spec(TREN), md, gates.GateParams.fast(), None)
        self.assertEqual(gates.g1_pit(c).status, gates.PASS)
        leak = "PARAMS = {'N': 5}\nSEEN = []\ndef target(bars, params):\n    SEEN.append(1)\n    return {'BTCUSDT': 0.5} if len(SEEN) % 3 == 0 else {}\n"
        r = gates.g1_pit(gates._Ctx(self.spec(leak), md, gates.GateParams.fast(), None))
        self.assertEqual(r.status, gates.FAIL)
        self.assertIn("sampel identik", r.value)

    def test_g5_shifts_named_params_and_fails_decorative_or_missing_ones(self):
        md = md_kecil(400)
        c = gates._Ctx(self.spec(TREN), md, gates.GateParams.fast(), None)
        r = gates.g5_plateau(c)
        self.assertIn("N:", r.value)                                                                  # varian N dievaluasi
        deko = TREN.replace('n = params["N"]', 'n = PARAMS["N"]')                                   # baca global, abaikan argumen
        r = gates.g5_plateau(gates._Ctx(self.spec(deko), md, gates.GateParams.fast(), None))
        self.assertEqual(r.status, gates.FAIL)
        self.assertIn("dekoratif", r.value)
        kosong = TREN.replace('PARAMS = {"N": 20}', "PARAMS = {}").replace('n = params["N"]', "n = 20")
        r = gates.g5_plateau(gates._Ctx(self.spec(kosong), md, gates.GateParams.fast(), None))
        self.assertEqual(r.status, gates.FAIL)
        self.assertIn("tanpa parameter bernama", r.value)
        self.assertEqual(kode.kelompok_plateau({"N": 20, "k": 0.5}, (0.5, 1.5))[0][1], [("10", {"N": 10, "k": 0.5}), ("30", {"N": 30, "k": 0.5})])
        self.assertEqual(kode.geser(-3, 0.25), -1)                                                    # bulat tetap bulat, tanda dipertahankan

    def test_g8_uses_the_default_time_placebo_for_code(self):
        self.assertNotIn(kode.KODE_METHOD, NULL_KIND)
        md = md_kecil(400)
        r = gates.g8_null(gates._Ctx(self.spec(TREN), md, gates.GateParams.fast(), None))
        self.assertIn("pergeseran waktu", r.rule)

    def test_a_failing_program_fails_every_gate_closed(self):
        res = gates.run_gates(self.spec(H + "    return {'BTCUSDT': 2.0}\n"), md_kecil(160), None, gates.GateParams.fast())
        self.assertEqual((res[0].gate, res[0].status), ("G*", gates.FAIL))
        self.assertEqual(gates.verdict(res)[0], "TOLAK")

    def test_a_code_form_counts_its_g5_variants_and_never_publishes_the_code(self):
        sub = code_sub(TREN)
        self.assertIn("belum dibuka", " ".join(submission.validate(sub)))                           # TERTUTUP untuk pengguna luar
        kode.pelari().daftarkan(TREN)
        rep = reviewmod.review(sub, md_kecil(260), None, gate_params=gates.GateParams.fast(), enabled_kinds=submission.KINDS)
        self.assertEqual(rep["varian_g5"], 4)                                                         # 1 parameter x 4 faktor
        self.assertEqual(rep["n_trials"], 1 + 0 + 1 + 4)
        self.assertEqual(rep["label_kepercayaan"], kode.LABEL_KEPERCAYAAN)
        self.assertEqual(rep["template"], "CODE")
        self.assertNotIn("def target", json.dumps(rep))
        self.assertIn("(code)", reviewmod.render(rep))
        self.assertIn("LABEL KEPERCAYAAN: kode privat", reviewmod.render(rep))


def code_sub(src, bot_id="KODE-TREN-1"):
    with open(os.path.join(ROOT, "engine", "examples", "submission.example.json"), encoding="utf-8") as f:
        sub = json.load(f)
    m, info = kode.periksa(src)
    sub["kind"] = "code"
    sp = sub["spec"]
    for k in ("template", "param_nama", "param"):
        sp.pop(k, None)
    sp.update(bot_id=bot_id, kode={"sha": info["sha"], "ukuran": info["ukuran"], "params": info["params"]},
              universe=["BTCUSDT", "ETHUSDT", "BNBUSDT"])
    sub["evidence"]["percobaan"] = 1
    return sub


try:
    from eth_account import Account
    from eth_account.messages import encode_typed_data
except ImportError:                                                     # pragma: no cover
    Account = None


@unittest.skipIf(Account is None, "eth-account tidak terpasang")
class PrivatTests(unittest.TestCase):
    """Lapis 6: kode PRIVAT. Gerbang menyimpan teks di volume (0600), antrean publik hanya sha + ukuran + params; pelari terpisah TANPA rahasia
    mengembalikan DATA; pihak tepercaya memvalidasi DATA itu lagi dan menjalankan G1-G11 tanpa pernah memegang teks kode."""

    def setUp(self):
        import pengajuan as pj
        self.pj = pj
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.acct = Account.create()

    def tanda(self, sub, nonce=1):
        now = 1_900_000_000
        td = submission.typed_data(sub, 97, nonce, now + 600)
        return {"submission": sub, "signature": "0x" + self.acct.sign_message(encode_typed_data(full_message=td)).signature.hex().removeprefix("0x"),
                "nonce": nonce, "deadline": now + 600}, now

    def test_the_gate_keeps_code_private_and_closed_by_default(self):
        sub = code_sub(TREN)
        sub["identity"]["issuer_wallet"] = sub["identity"]["payout_wallet"] = self.acct.address
        body, now = self.tanda(sub)
        tutup = self.pj.Antrean(os.path.join(self.tmp, "a"), now=lambda: now)
        code, out = tutup.terima(dict(body, code=TREN))
        self.assertEqual(code, 400)
        self.assertIn("belum dibuka", " ".join(out["problems"]))                                    # jenis code TERTUTUP (menunggu builder)
        buka = self.pj.Antrean(os.path.join(self.tmp, "b"), now=lambda: now, kinds=submission.KINDS)
        self.assertEqual(buka.terima(body)[0], 400)                                                   # tanpa teks kode
        self.assertEqual(buka.terima(dict(body, code=TREN.replace("20", "21")))[0], 400)             # teks tidak cocok dengan sha bertanda tangan
        code, out = buka.terima(dict(body, code=TREN))
        self.assertEqual(code, 201, out)
        kp = os.path.join(buka.kode_dir, sub["spec"]["kode"]["sha"][2:] + ".py")
        with open(kp, encoding="utf-8") as f:
            self.assertEqual(f.read(), TREN)
        self.assertEqual(stat.S_IMODE(os.stat(kp).st_mode), 0o600)
        publik = json.dumps(buka.daftar())
        self.assertNotIn("def target", publik)
        self.assertIn(sub["spec"]["kode"]["sha"], publik)                                              # salinan publik = sha + ukuran + params
        info = self.pj.info_tanda_tangan()
        self.assertEqual((info["code"]["open"], info["code"]["label"]), (False, kode.LABEL_KEPERCAYAAN))
        self.assertIn("penyedia model peninjau", info["code"]["reviewer_note"])
        self.assertNotIn("code", info["kinds_open"])

    def test_the_separate_runner_returns_bounded_data_that_the_trusted_side_validates_and_gates(self):
        import pelari_kode as pk
        from http.server import ThreadingHTTPServer
        srv = ThreadingHTTPServer(("127.0.0.1", 0), pk.make_handler(threading.Lock()))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        url = f"http://127.0.0.1:{srv.server_address[1]}"
        md = md_kecil(260)
        uni = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        bars = kode.bars_payload(md, uni)
        grid = sorted({t for a in bars for t in bars[a]["t"]})
        gp = gates.GateParams.fast()
        varian = kode.varian_semua({"N": 20}, gp.plateau_factors)
        req = {"kode": TREN, "bars": bars, "varian": varian, "sampel": kode.sampel_kausal(grid, gp.pit_days, gp.seed), "dasar": "dasar"}
        r = urllib.request.urlopen(urllib.request.Request(url + "/run", data=json.dumps(req).encode(), headers={"Content-Type": "application/json"}),
                                   timeout=120)
        data = json.loads(r.read().decode())
        self.assertTrue(data["ok"] and data["deterministik"], data.get("galat"))
        self.assertNotIn("def target", json.dumps(data))                                              # DATA saja
        sha = kode.sha_kode(TREN)
        pd = kode.PelariData(sha, bars, data, varian, uni)
        lama = kode.pasang_pelari(pd)                                                                 # pihak tepercaya: TANPA teks kode
        self.addCleanup(kode.pasang_pelari, lama)
        rep = reviewmod.review(code_sub(TREN), md, None, gate_params=gp, enabled_kinds=submission.KINDS)
        g = {x["gate"]: x for x in rep["gerbang"]}
        self.assertEqual(g["G1"]["status"], gates.PASS)
        self.assertIn("N:", g["G5"]["value"])
        with self.assertRaises(kode.KodeError):                                                       # data terpotong / lain = gagal tertutup
            pd.hasil(sha, kode.bars_payload(md.upto(grid[-10]), uni), {"dasar": {"N": 20}})
        bad = copy.deepcopy(data)
        bad["varian"]["dasar"][100][1] = {"BTCUSDT": 0.9, "ETHUSDT": 0.9}
        for rusak in (bad, dict(data, data_sha="0x" + "00" * 32), dict(data, varian={"dasar": data["varian"]["dasar"]}),
                      dict(data, deterministik=None), dict(data, kode_sha="0x" + "11" * 32)):
            with self.assertRaises(kode.KodeError):
                kode.PelariData(sha, bars, rusak, varian, uni)
        code, out = pk.kerjakan({"kode": TREN, "bars": {"BTCUSDT": {"t": [1]}}, "varian": {}})
        self.assertEqual(code, 400)
        h = json.loads(urllib.request.urlopen(url + "/health", timeout=10).read().decode())
        self.assertTrue(h["ok"])

    def test_the_runner_refuses_to_start_with_secrets_in_its_environment(self):
        import pelari_kode as pk
        self.assertEqual(pk.rahasia_di_env({"PORT": "1", "PYTHONHASHSEED": "1", "RAILWAY_PRIVATE_DOMAIN": "x", "HOME": "/h"}), [])
        self.assertEqual(pk.rahasia_di_env({"X402_FACILITATOR_PRIVATE_KEY": "0x", "XKIRO_API_KEY": "k", "GH_TOKEN": "t", "PORT": "1"}),
                         ["GH_TOKEN", "X402_FACILITATOR_PRIVATE_KEY", "XKIRO_API_KEY"])
        with open(os.path.join(ROOT, "railway", "pelari", "Dockerfile"), encoding="utf-8") as f:
            dock = f.read()
        self.assertIn("USER pelari", dock)
        self.assertNotIn("requirements", dock)                                                         # tanpa pustaka tanda tangan / kunci
        self.assertNotIn("COPY engine engine", dock)                                                   # image minimal

    def test_the_runner_works_with_only_the_files_its_image_copies(self):
        import re
        import subprocess
        with open(os.path.join(ROOT, "railway", "pelari", "Dockerfile"), encoding="utf-8") as f:
            files = [x for ln in f if ln.startswith("COPY ") for x in ln.split()[1:-1]]
        self.assertEqual(sorted(files), ["engine/__init__.py", "engine/kode.py", "engine/kode_anak.py", "tools/pelari_kode.py"])
        img = os.path.join(self.tmp, "img")
        for rel in files:
            os.makedirs(os.path.join(img, os.path.dirname(rel)), exist_ok=True)
            shutil.copy(os.path.join(ROOT, rel), os.path.join(img, rel))
        md = md_kecil(90)
        bars = kode.bars_payload(md, ["BTCUSDT", "ETHUSDT"])
        req = {"kode": TREN, "bars": bars, "varian": {"dasar": {"N": 20}}, "sampel": [sorted(bars["BTCUSDT"]["t"])[-1]], "dasar": "dasar"}
        prog = ("import sys, json; sys.path.insert(0, sys.argv[1] + '/tools'); import pelari_kode as pk; "
                "print(json.dumps(pk.kerjakan(json.loads(sys.stdin.read()))[1]))")
        r = subprocess.run([sys.executable, "-I", "-c", prog, img], input=json.dumps(req), capture_output=True, text=True, timeout=120, cwd=img)
        self.assertEqual(r.returncode, 0, r.stderr[-300:])
        out = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual((out["ok"], out["deterministik"], out["kausal"]["beda"]), (True, True, []))   # tanpa repo, tanpa pustaka luar
        self.assertFalse(re.search(r"\.git|ledger|deployments", " ".join(os.listdir(img))))


def node_web(masukan: dict) -> dict:
    """Jalankan `tools/web_kode_feed.mjs` (web/src/lib/kode.ts + feed.ts) dengan Node >= 22.6; masukan JSON lewat stdin."""
    import subprocess
    from engine.tests.test_rule import node_ts
    r = subprocess.run([node_ts(), "--experimental-strip-types", "--no-warnings", os.path.join(ROOT, "tools", "web_kode_feed.mjs")],
                       input=json.dumps(masukan), capture_output=True, text=True, timeout=120, cwd=ROOT)
    assert r.returncode == 0, r.stderr[-400:]
    return json.loads(r.stdout)


def _ada_node() -> bool:
    from engine.tests.test_rule import node_ts
    return bool(node_ts())


@unittest.skipUnless(_ada_node(), "Node >= 22.6 tidak ada: kontrak web tidak bisa dijalankan di mesin ini")
class WebContractTests(unittest.TestCase):
    """Editor kode di web (`web/src/lib/kode.ts`) menghitung `spec.kode` {sha, ukuran, PARAMS} yang SAMA dengan gerbang (`kode.periksa`):
    formulir yang ditandatangani di web cocok dengan teks yang diperiksa gerbang."""

    def test_the_web_editor_computes_the_same_sha_size_and_params_as_the_gate(self):
        import pengajuan as pj
        codes = [TREN, pj.KODE_CONTOH, TREN.replace('"N": 20', '"N": 20, "k": 0.5'), "PARAMS = {}\ndef target(bars, params):\n    return {}\n",
                 "# é unicode \u00e9\n" + TREN]
        out = node_web({"codes": codes})["codes"]
        for src, web in zip(codes, out):
            m, info = kode.periksa(src)
            self.assertEqual(m, [], src[:40])
            self.assertEqual(web, {"sha": info["sha"], "ukuran": info["ukuran"], "params": info["params"]})
            self.assertEqual(kode.validate_meta(web), [])


if __name__ == "__main__":
    unittest.main()
