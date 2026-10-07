"""P99/P100: penulis ledger Railway (tools/penulis_ledger.py). Tanpa jaringan, tanpa GitHub: "GitHub" = repo git bare LOKAL.

Ujung-ke-ujung (git sungguhan, proses alat sungguhan):
  * alat tiruan di repo uji (paper_tick / engine.cli / feed_tick / ... palsu yang dikendalikan berkas JSON) -> alur rantai: penulis tunggal (config +
    workflow + kunci sewa), verify gagal = tidak commit, balapan push = rebase + verify ulang, cabang uji tidak pernah menyentuh master;
  * engine ASLI + ledger repo ASLI: catatan terakhir B1-TREND dicabut dari repo uji, `paper_tick` tiruan mengembalikannya, `engine.cli ledger verify`
    sungguhan menjadi gerbang -> blob ledger yang di-push IDENTIK dengan blob yang ditulis rantai GitHub; satu angka diubah = verify gagal, tidak di-push.
"""
import contextlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

from engine import ledger
from engine.series import DAY_MS
from engine.spec import PERP_UNIVERSE

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import feed_bars as fb                                              # noqa: E402
import penulis_ledger as pl                                         # noqa: E402
from engine.tests import test_shadow_tick as tst                   # noqa: E402

NOW = ledger.iso_ms("2026-10-08T09:00:00Z")                         # di jendela vision (08:40-11:58Z)
MENIT = 60_000
ID = ("-c", "user.name=uji", "-c", "user.email=uji@uji.invalid")

UJI_PY = '''import json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def kendali():
    p = os.environ.get("UJI_PENULIS_KENDALI")
    return json.load(open(p, encoding="utf-8")) if p and os.path.exists(p) else {}


def catat(nama):
    k = kendali()
    if k.get("jejak"):
        with open(k["jejak"], "a", encoding="utf-8") as f:
            f.write(json.dumps({"alat": nama, "argv": sys.argv[1:], "alert": "ALERT_TELEGRAM_TOKEN" in os.environ, "gh": "GH_TOKEN" in os.environ,
                                "funding_rest": os.environ.get("FABIUS_FUNDING_REST"), "rahasia": "PENULIS_GITHUB_TOKEN" in os.environ}) + "\\n")
    return k


def tambah(rel, line):
    p = os.path.join(ROOT, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8", newline="") as f:
        f.write(line.rstrip("\\n") + "\\n")


def git(cwd, *a):
    subprocess.run(["git", "-c", "user.name=luar", "-c", "user.email=luar@uji.invalid", *a], cwd=cwd, check=True, capture_output=True)
'''

PAPER_TICK = '''import os, subprocess, sys
import _uji
k = _uji.catat("paper_tick")
for rel, line in k.get("tambah", []):
    _uji.tambah(rel, line)
if k.get("balapan"):                                   # penulis lain mendorong commit ke cabang yang sama di tengah putaran
    luar = k["balapan"]
    with open(os.path.join(luar, "catatan-balapan.md"), "a", encoding="utf-8") as f:
        f.write("x\\n")
    _uji.git(luar, "add", "-A")
    _uji.git(luar, "commit", "-q", "-m", "commit balapan")
    _uji.git(luar, "push", "-q", "origin", "HEAD:refs/heads/master")
if k.get("curi_kunci"):                                 # proses lain merebut sewa kunci di tengah putaran
    luar, ref, isi = k["curi_kunci"]
    run = lambda a, i: subprocess.run(["git", *a], cwd=luar, input=i.encode(), capture_output=True, check=True).stdout.decode().strip()
    blob = run(["hash-object", "-w", "--stdin"], isi)
    tree = run(["mktree"], "100644 blob " + blob + "\\tkunci.json\\n")
    c = subprocess.run(["git", "-c", "user.name=p", "-c", "user.email=p@p", "commit-tree", tree, "-m", "curi"], cwd=luar, capture_output=True, text=True,
                       check=True).stdout.strip()
    _uji.git(luar, "push", "-q", "--force", "origin", c + ":" + ref)
sys.exit(int(k.get("rc", 0)))
'''

ENGINE_CLI = '''import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import _uji
k = _uji.catat("engine.cli")
a = sys.argv[1:]
if a[:2] == ["ledger", "verify"]:
    d = os.path.join(_uji.ROOT, "ledger", "paper")
    bad = any("RUSAK" in open(os.path.join(d, f), encoding="utf-8").read() for f in os.listdir(d))
    print("ledger verify:", "GAGAL" if bad else "SAH")
    sys.exit(1 if bad else 0)
if a[:2] == ["book", "epoch"] and k.get("buku"):
    _uji.tambah("ledger/book/buku.jsonl", k["buku"])
sys.exit(0)
'''

EKSEKUSI = '''import sys
import _uji
k = _uji.catat("eksekusi_ledger")
if sys.argv[1] == "run" and k.get("eksekusi"):
    _uji.tambah("ledger/eksekusi/B1.jsonl", k["eksekusi"])
sys.exit(0)
'''

KERTAS = '''import sys
import _uji
k = _uji.catat("kertas_eksekusi")
if k.get("kertas"):
    _uji.tambah("ledger/kertas/B1.jsonl", k["kertas"])
sys.exit(0)
'''


def simple(nama, rc_key=None):
    return f"import sys\nimport _uji\nk = _uji.catat({nama!r})\nsys.exit(int(k.get({rc_key!r}, 0)) if {rc_key!r} else 0)\n"


FAKE_TOOLS = {
    "tools/_uji.py": UJI_PY,
    "tools/paper_tick.py": PAPER_TICK,
    "tools/feed_tick.py": simple("feed_tick", "feed_rc"),
    "tools/kertas_eksekusi.py": KERTAS,
    "tools/eksekusi_ledger.py": EKSEKUSI,
    "tools/worker_watch.py": simple("worker_watch", "watch_rc"),
    "tools/waitlist.py": simple("waitlist"),
    "tools/feed_bars.py": "# tiruan: sakelar FABIUS_FUNDING_REST dikenal (SK-R2)\n",
}
FAKE_ENGINE = {"engine/__init__.py": "", "engine/cli.py": ENGINE_CLI}


def tick(asof, h, targets=None, lag=300, data_hash="0xd1"):
    return {"type": "tick", "asof": asof, "targets": targets or {"BTCUSDT": 0.5}, "data_hash": data_hash, "signal_ids": ["s1"], "n_aset": 1,
            "lag_s": lag, "h": h}


def _rm(path):
    for d, _, files in os.walk(path):
        for f in files:
            try:
                os.chmod(os.path.join(d, f), stat.S_IWRITE)
            except OSError:
                pass
    shutil.rmtree(path, ignore_errors=True)


def g(cwd, *args, inp=None):
    r = subprocess.run(["git", *ID, *args], cwd=cwd, capture_output=True, text=True, input=inp, encoding="utf-8")
    if r.returncode != 0:
        raise AssertionError(f"git {args}: {r.stderr}")
    return r.stdout.strip()


class FakeApi:
    slug, token = "uji/fabius", ""

    def __init__(self, state="disabled_manually", runs=(), fail=False, wd="disabled_manually"):
        self.state, self.runs, self.fail, self.wd = state, list(runs), fail, wd
        self.dispatched = []

    def get(self, path):
        if self.fail:
            raise RuntimeError("GET -> HTTP 502")
        if "/runs?" in path:
            return {"workflow_runs": list(self.runs)}
        return {"state": self.wd if pl.WATCHDOG in path else self.state}

    def dispatch(self, wf, ref):
        self.dispatched.append((wf, ref))
        return True


class FakeAlert:
    def __init__(self):
        self.sent = []

    def send(self, key, text, sekali=False):
        self.sent.append(text)
        return "terkirim"


class Lab:
    """repo sumber -> bare ("GitHub") + klon luar (penulis lain / builder) + berkas kendali alat tiruan."""

    def __init__(self, penulis="github", files=None, extra=None, defaults=True):
        self.tmp = tempfile.mkdtemp(prefix="uji-penulis-")
        src = os.path.join(self.tmp, "src")
        os.makedirs(src)
        tree = dict(FAKE_TOOLS)
        tree.update(FAKE_ENGINE if files is None else {})
        tree.update(files or {})
        tree[pl.CONFIG_REL] = json.dumps({"penulis": penulis}) + "\n"
        if defaults:
            tree.setdefault("ledger/paper/B1.jsonl", json.dumps({"type": "genesis", "h": "0xg"}) + "\n")
            tree.setdefault("ledger/bars/x.csv", "t,o,h,l,c,v\n")
        tree["deployments/97.json"] = "{}\n"
        tree["docs/README.md"] = "di luar sparse\n"
        for rel, body in tree.items():
            p = os.path.join(src, *rel.split("/"))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(body)
        if extra:
            extra(src)
        g(src, "init", "-q", "-b", "master")
        g(src, "config", "core.autocrlf", "false")
        g(src, "add", "-A")
        g(src, "commit", "-q", "-m", "awal")
        self.bare = os.path.join(self.tmp, "bare.git")
        g(self.tmp, "clone", "-q", "--bare", src, self.bare)
        self.luar = os.path.join(self.tmp, "luar")
        g(self.tmp, "clone", "-q", self.bare, self.luar)
        self.kendali = os.path.join(self.tmp, "kendali.json")
        self.jejak = os.path.join(self.tmp, "jejak.jsonl")
        self.now = NOW
        self.set()
        self.logs = []
        self.env = mock.patch.dict(os.environ, {"UJI_PENULIS_KENDALI": self.kendali, "ALERT_TELEGRAM_TOKEN": "tg-uji", "ALERT_TELEGRAM_CHAT": "1",
                                                "PENULIS_GITHUB_TOKEN": "rahasia-yang-tidak-boleh-bocor",
                                                "GH_TOKEN": "gh-yang-tidak-boleh-bocor"})
        self.env.start()

    def set(self, **k):
        k["jejak"] = self.jejak
        with open(self.kendali, "w", encoding="utf-8") as f:
            json.dump(k, f)

    def penulis(self, mode="master", nama="w1", api=None, **kw):
        return pl.Penulis(mode, kw.pop("sumber", "vision"), self.bare, os.path.join(self.tmp, nama), api=api or FakeApi(), alerter=FakeAlert(),
                          log=self.logs.append, sleep=lambda s: None, now_fn=lambda: self.now, pemegang=nama, **kw)

    def luar_tulis(self, rel, body, msg, branch="master"):
        g(self.luar, "fetch", "-q", "origin")
        g(self.luar, "checkout", "-q", "-B", branch, f"origin/{branch}")
        p = os.path.join(self.luar, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
        g(self.luar, "add", "-A")
        g(self.luar, "commit", "-q", "-m", msg)
        g(self.luar, "push", "-q", "origin", f"HEAD:refs/heads/{branch}")

    def subjects(self, ref="master"):
        return g(self.bare, "log", "--format=%s", ref).splitlines()

    def show(self, ref, rel):
        return g(self.bare, "show", f"{ref}:{rel}")

    def refs(self):
        return g(self.bare, "for-each-ref", "--format=%(refname)").splitlines()

    def trace(self):
        if not os.path.exists(self.jejak):
            return []
        with open(self.jejak, encoding="utf-8") as f:
            return [json.loads(ln) for ln in f if ln.strip()]

    def close(self):
        self.env.stop()
        _rm(self.tmp)


# ======================================================================== ujung-ke-ujung: penulis tunggal
class SingleWriterTests(unittest.TestCase):
    def test_master_writes_only_when_config_workflow_and_lease_all_agree_then_runs_the_whole_chain_in_order(self):
        lab = Lab()
        try:
            t = json.dumps(tick(1000, "0xt1"))
            lab.set(tambah=[["ledger/paper/B1.jsonl", t], ["ledger/bars/x.csv", "1000,1,2,0.5,1.5,10"]], buku='{"epoch": 1}', kertas='{"k": 1}',
                    eksekusi='{"x": 1}')
            api = FakeApi(state="active")
            pn = lab.penulis(api=api)
            # 1) config masih github: tidak ada alat yang jalan, tidak ada kunci, master tidak berubah
            self.assertEqual(pn.putaran(), "tolak")
            self.assertIn("masih rantai GitHub", lab.logs[-1])
            self.assertEqual(lab.trace(), [])
            self.assertEqual(lab.subjects(), ["awal"])
            self.assertFalse(any("penulis" in r for r in lab.refs()))
            # 2) builder membalik config, tetapi workflow masih aktif -> SK-R3 menolak
            lab.luar_tulis(pl.CONFIG_REL, '{"penulis": "railway"}\n', "alih penulis ke railway")
            self.assertEqual(pn.putaran(), "tolak")
            self.assertIn("SK-R3", lab.logs[-1])
            # 3) workflow dimatikan tetapi satu mata rantai masih jalan -> tunggu
            api.state, api.runs = "disabled_manually", [{"id": 7, "status": "in_progress"}]
            self.assertEqual(pn.putaran(), "tolak")
            self.assertIn("masih hidup", lab.logs[-1])
            self.assertEqual(lab.trace(), [])
            # 4) semua syarat terpenuhi -> isi rantai berjalan, urut, dan sampai di "GitHub"
            api.runs = []
            self.assertEqual(pn.putaran(), "ok")
            subj = lab.subjects()
            self.assertEqual([s.split(" 20")[0] for s in subj[:4]], ["ledger eksekusi", "kertas eksekusi", "buku slot epoch", "ledger paper"], subj)
            self.assertTrue(all(s.endswith("[skip ci]") for s in subj[:4]))
            self.assertIn(t, lab.show("master", "ledger/paper/B1.jsonl"))
            self.assertIn("1000,1,2,0.5,1.5,10", lab.show("master", "ledger/bars/x.csv"))
            self.assertIn("refs/penulis/kunci-master", lab.refs())
            self.assertEqual(json.loads(lab.show("refs/penulis/kunci-master", "kunci.json"))["pemegang"], "w1")
            order = [(x["alat"], x["argv"][:2]) for x in lab.trace()]
            self.assertEqual(order[:8], [("paper_tick", ["--feed"]), ("engine.cli", ["ledger", "verify"]), ("feed_tick", []),
                                         ("engine.cli", ["book", "epoch"]), ("engine.cli", ["book", "verify"]), ("kertas_eksekusi", ["run"]),
                                         ("worker_watch", ["--alert", "--ringkasan"]), ("eksekusi_ledger", ["run", "--alert"])])
            self.assertEqual(order[-1], ("waitlist", ["--poll"]))
            self.assertEqual(api.dispatched, [(wf, "master") for wf in pl.DISPATCH])
            for x in lab.trace():
                self.assertEqual(x["funding_rest"], "0", x)                  # SK-R2 untuk setiap alat
                self.assertFalse(x["rahasia"] or x["gh"], x)                 # token push tidak pernah sampai ke alat
                self.assertTrue(x["alert"], x)                               # penulis resmi: alat boleh mengirim Telegram
            self.assertNotIn("docs", os.listdir(pn.klon))                    # klon sparse
            # 5) putaran berikut di hari yang sama: tick sudah beres, tidak ada tick/commit ledger paper baru
            n_tick = sum(x["alat"] == "paper_tick" for x in lab.trace())
            lab.set()
            self.assertEqual(pn.putaran(), "ok")
            self.assertEqual(sum(x["alat"] == "paper_tick" for x in lab.trace()), n_tick)
            self.assertEqual(sum(s.startswith("ledger paper") for s in lab.subjects()), 1)
        finally:
            lab.close()

    def test_unreadable_github_api_means_no_write(self):
        lab = Lab(penulis="railway")
        try:
            pn = lab.penulis(api=FakeApi(fail=True))
            self.assertEqual(pn.putaran(), "tolak")
            self.assertIn("tak terbaca", lab.logs[-1])
            self.assertEqual((lab.subjects(), lab.trace()), (["awal"], []))
            self.assertTrue(any("TIDAK menulis" in s for s in pn.alert.sent))
        finally:
            lab.close()

    def test_a_second_writer_is_refused_while_the_first_holds_the_lease_and_takes_over_only_after_it_expires(self):
        lab = Lab(penulis="railway")
        try:
            lab.set(tambah=[["ledger/paper/B1.jsonl", json.dumps(tick(1000, "0xt1"))]], rc=4)
            w1 = lab.penulis(nama="w1")
            self.assertEqual(w1.putaran(), "ok")
            before = lab.subjects()
            self.assertTrue(before[0].startswith("ledger paper"))
            lab.set(tambah=[["ledger/paper/B1.jsonl", json.dumps(tick(2000, "0xw2"))]], rc=4)
            w2 = lab.penulis(nama="w2")
            self.assertEqual(w2.putaran(), "tolak")
            self.assertIn("dipegang w1", lab.logs[-1])
            self.assertEqual(lab.subjects(), before)
            self.assertNotIn("0xw2", lab.show("master", "ledger/paper/B1.jsonl"))
            lab.now += (pl.KUNCI_TTL_S + 60) * 1000                         # w1 mati tanpa melepas kunci: sewa habis
            self.assertEqual(w2.putaran(), "ok")
            self.assertEqual(json.loads(lab.show("refs/penulis/kunci-master", "kunci.json"))["pemegang"], "w2")
            self.assertIn("0xw2", lab.show("master", "ledger/paper/B1.jsonl"))
            self.assertEqual(w1.putaran(), "tolak")
            self.assertIn("dipegang w2", lab.logs[-1])
            self.assertTrue(w2.kunci.lepas())                                 # SIGTERM: kunci dilepas -> ref hilang
            self.assertNotIn("refs/penulis/kunci-master", lab.refs())
        finally:
            lab.close()

    def test_lease_taken_by_someone_else_mid_round_means_nothing_is_pushed(self):
        lab = Lab(penulis="railway")
        try:
            isi = json.dumps({"pemegang": "pencuri", "sampai_ms": NOW + 3600_000, "sampai_utc": "nanti"})
            lab.set(tambah=[["ledger/paper/B1.jsonl", json.dumps(tick(1000, "0xt1"))]], curi_kunci=[lab.luar, "refs/penulis/kunci-master", isi])
            pn = lab.penulis()
            self.assertEqual(pn.putaran(), "berhenti")
            self.assertTrue(any("DIBATALKAN" in m and "pencuri" in m for m in lab.logs), lab.logs[-6:])
            self.assertEqual(lab.subjects(), ["awal"])
        finally:
            lab.close()

    def test_failed_verify_is_never_committed_and_stops_like_exit_1_then_retries_after_the_pause(self):
        lab = Lab(penulis="railway")
        try:
            lab.set(tambah=[["ledger/paper/B1.jsonl", json.dumps(tick(1000, "0xRUSAK"))]])
            pn = lab.penulis()
            self.assertEqual(pn.putaran(), "berhenti")
            self.assertIn("ledger verify GAGAL", pn.alert.sent[-1])
            self.assertEqual(lab.subjects(), ["awal"])
            with open(os.path.join(pn.klon, "ledger", "paper", "B1.jsonl"), encoding="utf-8") as f:
                self.assertNotIn("RUSAK", f.read())                              # klon direset, bukan dibiarkan kotor
            lab.set(tambah=[["ledger/paper/B1.jsonl", json.dumps(tick(1000, "0xt1"))]])
            n = len(lab.trace())
            lab.now += 10 * MENIT
            self.assertEqual(pn.putaran(), "berhenti")                          # jeda 20 menit (setara watchdog GitHub)
            self.assertEqual(len(lab.trace()), n)
            lab.now += 15 * MENIT
            self.assertEqual(pn.putaran(), "ok")
            self.assertIn("0xt1", lab.show("master", "ledger/paper/B1.jsonl"))
        finally:
            lab.close()

    def test_paper_tick_error_stops_and_rc4_commits_progress_and_retries(self):
        lab = Lab(penulis="railway")
        try:
            lab.set(rc=3)
            pn = lab.penulis()
            self.assertEqual(pn.putaran(), "berhenti")
            self.assertIn("paper_tick rc=3", pn.alert.sent[-1])
            lab.now += 25 * MENIT
            lab.set(tambah=[["ledger/paper/B1.jsonl", json.dumps(tick(1000, "0xt1"))]], rc=4)
            self.assertEqual(pn.putaran(), "ok")
            self.assertTrue(lab.subjects()[0].startswith("ledger paper"), lab.subjects())
            self.assertIsNone(pn.selesai)                                       # rc 4: belum beres, putaran berikut mencoba lagi
            self.assertFalse(any(x["alat"] == "kertas_eksekusi" for x in lab.trace()))
        finally:
            lab.close()

    def test_push_race_rebases_and_verifies_the_rebased_ledger_again_before_pushing(self):
        lab = Lab(penulis="railway")
        try:
            lab.set(tambah=[["ledger/paper/B1.jsonl", json.dumps(tick(1000, "0xt1"))]], balapan=lab.luar, rc=4)
            pn = lab.penulis()
            self.assertEqual(pn.putaran(), "ok")
            self.assertEqual(lab.subjects()[:2][1], "commit balapan")
            self.assertTrue(lab.subjects()[0].startswith("ledger paper"))
            verifies = [x for x in lab.trace() if x["argv"][:2] == ["ledger", "verify"]]
            self.assertEqual(len(verifies), 2)                                  # sebelum commit + sesudah menarik hulu yang bergerak
        finally:
            lab.close()

    def test_a_branch_whose_feed_bars_lacks_the_funding_switch_is_never_written(self):
        lab = Lab(penulis="railway", files=dict(FAKE_ENGINE, **{"tools/feed_bars.py": "# versi lama\n"}))
        try:
            pn = lab.penulis()
            self.assertEqual(pn.putaran(), "tolak")
            self.assertIn("SK-R2", lab.logs[-1])
            self.assertEqual((lab.subjects(), lab.trace()), (["awal"], []))
        finally:
            lab.close()


# ======================================================================== ujung-ke-ujung: bayangan-tulis
class TrialBranchTests(unittest.TestCase):
    def test_bayangan_tulis_writes_only_to_the_trial_branch_and_compares_with_the_official_ticks(self):
        lab = Lab(penulis="github")                                          # rantai GitHub masih penulis resmi; uji berjalan paralel
        try:
            api = FakeApi(state="active")
            lab.set(tambah=[["ledger/paper/B1.jsonl", json.dumps(tick(1000, "0xu1"))], ["ledger/bars/x.csv", "1000,1,2,0.5,1.5,10"]],
                    eksekusi='{"x": 1}')
            pn = lab.penulis("bayangan-tulis", api=api)
            self.assertEqual(pn.putaran(), "ok")
            self.assertEqual(lab.subjects("master"), ["awal"])                  # master tidak pernah disentuh
            self.assertTrue(lab.subjects("penulis-uji")[0].startswith("ledger eksekusi"))
            self.assertIn("refs/penulis/kunci-penulis-uji", lab.refs())
            self.assertNotIn("refs/penulis/kunci-master", lab.refs())
            self.assertEqual(api.dispatched, [])
            names = {x["alat"] for x in lab.trace()}
            self.assertFalse(names & {"waitlist", "worker_watch"})              # daftar tunggu + penjaga worker milik rantai resmi
            self.assertFalse(any(x["alert"] for x in lab.trace()))              # tanpa Telegram dari alat
            self.assertFalse(any("--alert" in x["argv"] for x in lab.trace()))
            self.assertTrue(any("MENUNGGU" in m for m in lab.logs))
            # rantai resmi menulis tick hari yang sama (jam berbeda, hash berbeda, isi sama) + baris bar yang sama
            off = pl.baca(os.path.join(lab.luar, "ledger", "paper", "B1.jsonl")) + json.dumps(tick(1000, "0xr1", lag=33000)) + "\n"
            lab.luar_tulis("ledger/paper/B1.jsonl", off, "paper-ledger ledger paper [skip ci]")
            bars = pl.baca(os.path.join(lab.luar, "ledger", "bars", "x.csv")) + "1000,1.0,2.0,0.5,1.5,10.0\n"
            lab.luar_tulis("ledger/bars/x.csv", bars, "paper-ledger bar [skip ci]")
            lab.set()
            lab.now += 5 * MENIT
            self.assertEqual(pn.putaran(), "ok")
            v = [m for m in lab.logs if m.startswith("VONIS")]
            self.assertTrue(any("B1 1970-01-01: IDENTIK" in m and "uji 5.0 menit vs resmi 9.2 jam" in m for m in v), v)
            self.assertTrue(any("VONIS baris bar penulis-uji: 1 sama persis, 0 beda" in m for m in v), v)
            self.assertTrue(any("IDENTIK" in s for s in pn.alert.sent))
            # hari berikutnya: target beda = BEDA
            lab.set(tambah=[["ledger/paper/B1.jsonl", json.dumps(tick(2000, "0xu2", targets={"BTCUSDT": 0.4}))]])
            lab.now += DAY_MS
            self.assertEqual(pn.putaran(), "ok")
            off += json.dumps(tick(2000, "0xr2")) + "\n"
            lab.luar_tulis("ledger/paper/B1.jsonl", off, "paper-ledger ledger paper 2 [skip ci]")
            lab.set()
            lab.now += 5 * MENIT
            pn.putaran()
            self.assertTrue(any("1970-01-01: BEDA (targets)" in m for m in lab.logs), [m for m in lab.logs if "VONIS" in m])
            self.assertEqual(lab.subjects("master")[0], "paper-ledger ledger paper 2 [skip ci]")
        finally:
            lab.close()

    def test_trial_mode_can_never_point_at_the_official_branch(self):
        with self.assertRaises(ValueError):
            pl.Penulis("bayangan-tulis", "vision", "x", "y", cabang_uji="master")
        with self.assertRaises(ValueError):
            pl.Penulis("tulis-semua", "vision", "x", "y")


# ======================================================================== ujung-ke-ujung: engine + ledger ASLI
class RealEngineTests(unittest.TestCase):
    def test_real_verify_gate_pushes_a_byte_identical_ledger_and_rejects_a_changed_number(self):
        bot = "ledger/paper/B1-TREND.jsonl"
        blob = subprocess.run(["git", "archive", "HEAD", "engine", "ledger", "deployments"], cwd=ROOT, capture_output=True, check=True).stdout
        resmi = subprocess.run(["git", "rev-parse", f"HEAD:{bot}"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        lines = {}

        def extra(src):
            with tarfile.open(fileobj=io.BytesIO(blob)) as tf:
                tf.extractall(src, filter="data") if sys.version_info >= (3, 12) else tf.extractall(src)
            p = os.path.join(src, *bot.split("/"))
            with open(p, encoding="utf-8", newline="") as f:
                rows = f.read().splitlines(keepends=True)
            lines["akhir"] = rows[-1]
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.writelines(rows[:-1])                                       # repo uji = ledger SEBELUM catatan terakhir rantai GitHub

        lab = Lab(penulis="railway", files={}, extra=extra, defaults=False)
        try:
            last = lines["akhir"].rstrip("\r\n")
            rec = json.loads(last)
            self.assertIn("h", rec)
            changed = json.loads(last)
            key = next(k for k in ("targets", "data_hash", "n_aset", "lag_s", "asof") if k in changed)
            changed[key] = {"BTCUSDT": 0.123} if key == "targets" else ("0x" + "0" * 64 if key == "data_hash" else int(changed[key]) + 1)
            lab.set(tambah=[[bot, json.dumps(changed, separators=(",", ":"))]], rc=4)
            pn = lab.penulis()
            self.assertEqual(pn.putaran(), "berhenti")                         # engine.cli ledger verify ASLI menolak satu angka yang diubah
            self.assertEqual(lab.subjects(), ["awal"])
            lab.set(tambah=[[bot, last]], rc=4)
            lab.now += 25 * MENIT
            self.assertEqual(pn.putaran(), "ok")
            self.assertTrue(lab.subjects()[0].startswith("ledger paper"))
            self.assertEqual(g(lab.bare, "rev-parse", f"master:{bot}"), resmi)  # blob identik dengan yang dikomit rantai GitHub
        finally:
            lab.close()


# ======================================================================== P100: baris REST + pemeriksa Vision
class RestModeTests(unittest.TestCase):
    def _env(self, src_kw=None, now=tst.CLOSE + 5 * MENIT):
        tmp = tempfile.mkdtemp(prefix="uji-penulis-rest-")
        bars = os.path.join(tmp, "repo", "ledger", "bars")
        removed = tst.official_without_last_day(bars)
        est = {k.split(":")[1]: v for k, v in removed.items() if k.startswith("fest:")}
        clock = {"now": now}
        pn = pl.Penulis("bayangan-tulis", "rest", "unused", tmp, rest_src=tst.FakeRest(removed, **(src_kw or {})), alerter=FakeAlert(),
                        log=[].append, sleep=lambda s: None, now_fn=lambda: clock["now"],
                        est_fn=lambda sym, minutes, d: [r for r in est[sym] if d <= r[0] < d + DAY_MS] or None)
        return tmp, bars, removed, pn, clock

    def test_rows_from_two_identical_rest_reads_are_appended_in_place_and_actual_funding_is_untouched(self):
        tmp, bars, removed, pn, clock = self._env()
        try:
            fund_before = {n: pl.baca(os.path.join(bars, n)) for n in os.listdir(bars) if n.startswith("fund_") and not n.startswith("fund_est_")}
            self.assertEqual(pn.isi_rest(), "diisi")
            for key, rows in removed.items():
                kind, sym = key.split(":")
                path = os.path.join(bars, f"fund_est_{sym}.csv" if kind == "fest" else f"{kind}_{sym}_1d.csv")
                got = tst.read_rows(path)
                if sym not in PERP_UNIVERSE:                                    # deret di luar universe (koin listing B4, emas B5): menunggu Vision
                    self.assertFalse([r for r in got if r and r[0].isdigit() and int(r[0]) >= tst.BAR], key)
                elif kind == "fest":
                    self.assertEqual([(int(r[0]), float(r[1])) for r in got[-len(rows):]], rows, key)
                else:
                    self.assertEqual((int(got[-1][0]), *map(float, got[-1][1:6])), rows[0], key)
            self.assertEqual({n: pl.baca(os.path.join(bars, n)) for n in fund_before}, fund_before)        # SK-R2
            reads = pn.rest_src.reads
            self.assertEqual(pn.isi_rest(), "lengkap")                          # bar sudah lengkap: REST tidak dibaca lagi
            self.assertEqual(pn.rest_src.reads, reads)
        finally:
            _rm(tmp)

    def test_unsettled_or_missing_rest_rows_wait_and_write_nothing(self):
        for kw in ({"flips": 99}, {"drop": ["fut:ETHUSDT"]}):
            tmp, bars, removed, pn, clock = self._env(kw)
            try:
                before = {n: os.path.getsize(os.path.join(bars, n)) for n in os.listdir(bars)}
                self.assertEqual(pn.isi_rest(), "tunda", kw)
                self.assertEqual({n: os.path.getsize(os.path.join(bars, n)) for n in os.listdir(bars)}, before, kw)
            finally:
                _rm(tmp)

    def test_too_early_after_close_reads_nothing(self):
        tmp, bars, removed, pn, clock = self._env(now=tst.CLOSE + 60_000)
        try:
            self.assertEqual(pn.isi_rest(), "terlalu-dini")
            self.assertEqual(pn.rest_src.reads, 0)
        finally:
            _rm(tmp)

    def test_committed_rest_rows_are_checked_against_vision_once_it_is_published(self):
        for tweak, want in ((None, "sama persis, beda harga 0, beda estimasi funding 0"), ({"fut:BTCUSDT": 0.1}, "2026-10-01: ALARM - ")):
            tmp, bars, removed, pn, clock = self._env({"tweak": tweak} if tweak else None)
            try:
                pn.vision_fn = lambda b, rows, d, out: tst.BARS                 # zip Vision sudah terbit = bar resmi repo
                self.assertEqual(pn.isi_rest(), "diisi")
                self.assertEqual(pn.cek_vision(), [])                           # baru 5 menit sesudah penutupan: Vision belum mungkin ada
                clock["now"] = tst.CLOSE + 9 * 3600_000
                out = pn.cek_vision()
                self.assertEqual(len(out), 1, out)
                self.assertIn(want, out[0])
                self.assertIn(want, pn.alert.sent[-1])
                self.assertEqual(os.listdir(pn.rest_dir), [])                   # sekali per hari
            finally:
                _rm(tmp)


# ======================================================================== satuan
class UnitTests(unittest.TestCase):
    def test_token_travels_only_as_a_git_config_header_and_is_masked_everywhere(self):
        tok = "github_pat_UJI_1234567890"
        env = pl.git_env(tok, base={"PENULIS_GITHUB_TOKEN": tok, "GH_TOKEN": tok, "PATH": "x"})
        self.assertNotIn("PENULIS_GITHUB_TOKEN", env)
        self.assertNotIn("GH_TOKEN", env)
        self.assertEqual(env["GIT_CONFIG_KEY_0"], "http.https://github.com/.extraheader")
        self.assertNotIn(tok, json.dumps(env))                                  # hanya bentuk base64 di header
        hdr = env["GIT_CONFIG_VALUE_0"].split()[-1]
        self.assertEqual(pl.saring(f"a {tok} b {hdr}", tok), "a <rahasia> b <rahasia>")
        seen = []

        def fake_run(cmd, **kw):
            seen.append((cmd, kw["env"]))
            return subprocess.CompletedProcess(cmd, 128, "", f"fatal: auth gagal untuk {tok}")

        with mock.patch.object(pl.subprocess, "run", fake_run):
            with self.assertRaises(pl.GitError) as cm:
                pl.Git(".", tok).run("push", "origin", "HEAD")
        self.assertNotIn(tok, str(cm.exception))
        self.assertTrue(all(tok not in " ".join(c) for c, _ in seen))

    def test_tools_never_inherit_the_push_token_and_trial_tools_get_no_telegram(self):
        with mock.patch.dict(os.environ, {"PENULIS_GITHUB_TOKEN": "t", "GH_TOKEN": "t", "ALERT_TELEGRAM_TOKEN": "a", "ALERT_TELEGRAM_CHAT": "c"}):
            m = pl.Penulis("master", "vision", "x", tempfile.gettempdir(), token="t")
            u = pl.Penulis("bayangan-tulis", "vision", "x", tempfile.gettempdir(), token="t")
            e = m.env_alat()
            self.assertNotIn("PENULIS_GITHUB_TOKEN", e)
            self.assertNotIn("GH_TOKEN", e)
            self.assertEqual(e["FABIUS_FUNDING_REST"], "0")
            self.assertEqual(e["ALERT_TELEGRAM_TOKEN"], "a")
            self.assertNotIn("ALERT_TELEGRAM_TOKEN", u.env_alat())

    def test_config_switch_reads_github_on_anything_but_a_clean_railway(self):
        for teks in (None, "", "{", '{"penulis": "RAILWAY"}', '["railway"]', '{"penulis": "github"}'):
            self.assertEqual(pl.siapa(teks), "github", teks)
        self.assertEqual(pl.siapa('{"penulis": "railway", "catatan": "x"}'), "railway")
        self.assertIsNone(pl.penulis_dari("{"))
        self.assertEqual(pl.penulis_dari(pl.baca(os.path.join(ROOT, pl.CONFIG_REL))), "github")    # yang dikomit: perilaku lama
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(pl.main(["siapa", "--ref", "ref-yang-tidak-ada"]), 0)
        self.assertEqual(out.getvalue().strip(), "github")

    def test_workflow_guards_are_wired_and_inert_until_the_switch_says_railway(self):
        wf = pl.baca(os.path.join(ROOT, ".github", "workflows", "paper-ledger.yml"))
        self.assertIn("tools/penulis_ledger.py siapa 2>/dev/null || echo github", wf)
        self.assertIn("tools/penulis_ledger.py siapa --ref FETCH_HEAD 2>/dev/null || echo github", wf)
        self.assertEqual(wf.count("if: env.RANTAI_ADA == '0' && env.PENULIS_LAIN != '1'"), 2)       # loop + sambung rantai
        wd = pl.baca(os.path.join(ROOT, ".github", "workflows", "paper-ledger-watchdog.yml"))
        self.assertIn("contents/config/penulis-ledger.json", wd)
        self.assertIn("|| echo github", wd)

    def test_tick_windows(self):
        at = lambda hm: ledger.iso_ms(f"2026-10-08T{hm}:00Z")                 # noqa: E731
        self.assertEqual([pl.di_jendela(at(h), "vision") for h in ("08:39", "08:40", "11:58", "11:59")], [False, True, True, False])
        self.assertEqual([pl.di_jendela(at(h), "rest") for h in ("00:01", "00:02", "11:58", "12:00")], [False, True, True, False])

    def test_github_chain_must_be_off_and_idle_and_readable(self):
        ok = lambda **k: pl.syarat_rantai_github(FakeApi(**k))                # noqa: E731
        self.assertFalse(ok(state="active")[0])
        self.assertIn("SK-R3", ok(state="active")[1])
        self.assertFalse(ok(runs=[{"id": 1, "status": "queued"}])[0])
        self.assertFalse(ok(fail=True)[0])
        self.assertEqual(ok(), (True, "workflow paper-ledger disabled_manually, tidak ada run hidup"))
        self.assertIn("watchdog masih AKTIF", ok(wd="active")[1])
        self.assertTrue(ok(runs=[{"id": 2, "status": "completed"}])[0])

    def test_compare_counts_only_records_the_trial_branch_wrote_itself(self):
        shared = [{"type": "genesis", "h": "0xg"}, tick(500, "0xs")]
        resmi = shared + [tick(1000, "0xr1", lag=33000), {"type": "gap", "asof": 2000, "h": "0xr2"}, tick(3000, "0xr3")]
        uji = shared + [tick(1000, "0xu1"), tick(2000, "0xu2"), tick(4000, "0xu4", data_hash="0xd9")]
        got = [(a, v, d) for a, v, d, _, _ in pl.bandingkan_ledger(uji, resmi)]
        self.assertEqual(got, [(1000, "IDENTIK", []), (2000, "RESMI GAP", []), (3000, "RESMI ADA, UJI BELUM MENULIS", []), (4000, "MENUNGGU", [])])
        self.assertEqual(pl.bandingkan_ledger(uji[:2], resmi[:2]), [])         # warisan bersama bukan bukti
        diff = pl.bandingkan_ledger(shared + [tick(1000, "0xu1", targets={"BTCUSDT": 0.4})], resmi)
        self.assertEqual(diff[0][1:3], ("BEDA", ["targets"]))

    def test_funding_switch_never_calls_rest_and_falls_back_to_the_monthly_zip(self):
        tmp = tempfile.mkdtemp(prefix="uji-fund-")
        try:
            with open(os.path.join(tmp, "fund_BTCUSDT.csv"), "w", encoding="utf-8") as f:
                f.write("t,rate\n1788192000000,0.0001\n")                        # 2026-08-31 16:00Z
            for val, first in (("0", "/futures/um/monthly/fundingRate/"), ("1", "/fapi/v1/fundingRate")):
                urls = []
                with mock.patch.dict(os.environ, {"FABIUS_FUNDING_REST": val}):
                    rep = fb.update_funding(tmp, "BTCUSDT", ledger.iso_ms("2026-10-08T00:00:00Z"), fetch=lambda u: urls.append(u) or None, dry_run=True)
                self.assertIn(first, urls[0], val)
                if val == "0":
                    self.assertFalse(any("fapi" in u for u in urls))
                    self.assertIn("REST dimatikan", rep["note"])
        finally:
            _rm(tmp)


if __name__ == "__main__":
    unittest.main()
