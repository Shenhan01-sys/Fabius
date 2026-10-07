"""P161: jalur kandidat ujung-ke-ujung dengan KODE SUNGGUHAN (uji kering `tools/uji_jalur_kandidat.py` pada bar repo, jam simulasi) + pemeriksa jejak
`engine/seleksi.py`: tiap tahap tercatat dan diperiksa; rekaman yang diubah merusak jejak tepat di tahapnya; pemeriksaan yang tidak bisa dijalankan
tidak pernah dilaporkan OK; epoch mencatat kandidat yang dilewati; petahana G10 = buku hidup termasuk penghuni penerbit; worker mengomit bot penerbit
hanya bila sakelar menyala."""
import copy
import dataclasses
import json
import os
import shutil
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from engine import book_live, cli, ledger, registri, seleksi, slots, submission, terdaftar
from engine.gates import GateParams

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "tools")]

try:
    import eth_account  # noqa: F401
    HAVE_ETH = True
except ImportError:                                                   # pragma: no cover
    HAVE_ETH = False

BOT = "UJI-TREND-ETH-30"
DAY_S = 86_400
_CACHE = {}


def _jalan(kind, hari):
    """Satu uji kering sungguhan per (kind, hari) untuk seluruh modul; tiap tes menyalin rekamannya sebelum mengubah apa pun."""
    if (kind, hari) not in _CACHE:
        import uji_jalur_kandidat as u
        root = tempfile.mkdtemp(prefix=f"jalur-{kind}-")
        _CACHE[(kind, hari)] = (root, u.jalankan("2026-05-01", hari, kind, True, root, log=None))
    return _CACHE[(kind, hari)]


def tearDownModule():
    for root, _ in _CACHE.values():
        shutil.rmtree(root, True)


def _salin(src):
    dst = tempfile.mkdtemp(prefix="jejak-")
    shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return dst


def _status(j):
    return {t["nama"]: t["status"] for t in j["tahap"]}


def _tulis_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)


def _ubah_jsonl(path, i, fn):
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(x) for x in f if x.strip()]
    fn(rows[i])
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")


@unittest.skipUnless(HAVE_ETH, "eth-account tidak terpasang (uji kering menandatangani kiriman dengan kunci sekali-pakai)")
class JalurTests(unittest.TestCase):
    """Satu uji kering sungguhan (template, 8 hari maju, gerbang cepat) + satu kiriman rule yang ditolak gerbang; rekaman disalin per tes."""

    @classmethod
    def setUpClass(cls):
        import uji_jalur_kandidat as u
        cls.u = u
        cls.root, cls.out = _jalan("template", 8)
        cls.tolak_root, cls.tolak = _jalan("rule", 1)
        cls.sim = u.ChainSimulasi()
        e = registri.load(os.path.join(cls.root, "ledger", "pengajuan", "registri.jsonl"))[-1]
        cls.sim.pin(e["bot_id"], e["spec_sha"], int(e["t_s"]) + DAY_S)
        cls.sha, cls.e = cls.out["submission_sha"], e

    def jejak(self, root=None, **kw):
        kw.setdefault("chain", self.sim)
        kw.setdefault("now_s", self.out_now())
        return seleksi.jejak(root or self.root, kw.pop("kunci", self.sha), **kw)

    def out_now(self):
        return int(ledger.iso_ms("2026-05-11T09:00:00Z") // 1000)

    def test_a_passing_candidate_is_recorded_at_every_stage_it_reached_by_the_production_code(self):
        self.assertEqual((self.out["gerbang_http"], self.out["vonis"], self.out["k"]), (201, registri.LOLOS, 1))
        self.assertEqual(self.out["petahana_tinjauan"], ["B1-TREND"])                         # G10 tinjauan = buku hidup (genesis: bot identitas)
        j = self.jejak(hitung_ulang=True, bars_dir=os.path.join(ROOT, "ledger", "bars"))
        self.assertIsNone(j["rusak_di"])
        self.assertEqual(_status(j), {"diterima": "OK", "gerbang": "OK", "registri": "OK", "dipin": "OK", "bayangan": "BELUM", "penantang": "OK",
                                      "slot": "BELUM", "pembunuh": "BELUM", "sinyal_chain": "BELUM"})
        cat = {t["nama"]: t["catatan"] for t in j["tahap"]}
        self.assertIn("data_hash = bar repo s/d 2026-05-01", cat["gerbang"])                 # vonis bisa diulang dari potongan bar yang sama
        self.assertIn("/60 hari", cat["bayangan"])
        self.assertIn("dihitung ulang dari bar", cat["bayangan"])
        self.assertIn("epoch 685", cat["penantang"])
        self.assertIn("laporan ber-sha cocok", cat["penantang"])
        self.assertEqual(seleksi.jejak(self.root, BOT, chain=self.sim, now_s=self.out_now())["submission_sha"], self.sha)   # bot_id = sha yang sama
        st = _status(self.jejak(hitung_ulang=True, bars_dir=os.path.join(self.root, "tidak-ada")))
        self.assertEqual((st["gerbang"], st["bayangan"]), ("TAK_TERPERIKSA", "TAK_TERPERIKSA"))   # bar tidak ada di mesin ini != ledger palsu
        self.assertEqual([x["submission_sha"] for x in seleksi.semua(self.root, chain=self.sim)], [self.sha])

    def test_a_rejected_candidate_is_recorded_and_stops_at_the_gate(self):
        self.assertEqual(self.tolak["vonis"], "TOLAK")
        j = seleksi.jejak(self.tolak_root, self.tolak["submission_sha"], chain=self.sim)
        st = _status(j)
        self.assertEqual((st["diterima"], st["gerbang"], st["registri"]), ("OK", "OK", "OK"))   # TOLAK tetap tercatat (memakan alpha keluarga)
        self.assertEqual({st[k] for k in ("dipin", "bayangan", "penantang", "slot", "pembunuh", "sinyal_chain")}, {"TIDAK_BERLAKU"})
        self.assertFalse(os.path.exists(os.path.join(self.tolak_root, "ledger", "pengajuan", "spec")))

    def test_each_tampered_record_breaks_the_trail_at_its_own_stage(self):
        d = os.path.join("ledger", "pengajuan")
        kasus = {
            "diterima": lambda r: _ubah_json(os.path.join(r, d, "masuk", f"{self.sha}.json"), lambda m: m["submission"]["spec"].update(param=31)),
            "gerbang": lambda r: _ubah_json(os.path.join(r, d, "laporan", f"{self.sha}.json"), lambda m: m.update(vonis="TOLAK")),
            "registri": lambda r: _ubah_jsonl(os.path.join(r, d, "registri.jsonl"), 0, lambda e: e.update(k=2)),
            "dipin": lambda r: _ubah_json(os.path.join(r, d, "spec", f"{BOT}.json"), lambda s: s["botspec"].update(param=31)),
            "bayangan": lambda r: _ubah_jsonl(os.path.join(r, "ledger", "paper", f"{BOT}.jsonl"), 2, lambda x: x.update(net=0.5)),
            "penantang": lambda r: _ubah_jsonl(os.path.join(r, "ledger", "book", "buku.jsonl"), 1, lambda x: x["keputusan"][0].__setitem__(3, "x")),
        }
        for tahap, ubah in kasus.items():
            with self.subTest(tahap=tahap):
                r = _salin(self.root)
                self.addCleanup(shutil.rmtree, r, True)
                ubah(r)
                j = self.jejak(r)
                self.assertEqual(j["rusak_di"], tahap, j["ringkas"])
                st = _status(j)
                urut = [n for n, _ in seleksi.TAHAP]
                for n in urut[urut.index(tahap) + 1:]:
                    self.assertEqual(st[n], "TIDAK_BERLAKU")                              # sesudah rusak: tidak dinilai, tidak OK
        r = _salin(self.root)                                                             # laporan gerbang EPOCH yang diubah
        self.addCleanup(shutil.rmtree, r, True)
        lap = os.path.join(r, "ledger", "book", "laporan")
        f = sorted(os.listdir(lap))[0]
        _ubah_json(os.path.join(lap, f), lambda m: m.update(vonis="TOLAK" if m["vonis"] != "TOLAK" else "LOLOS_SHADOW"))
        self.assertEqual(self.jejak(r)["rusak_di"], "penantang")

    def test_checks_that_cannot_run_here_are_never_reported_ok(self):
        j = self.jejak(chain=None)
        self.assertEqual(_status(j)["dipin"], "TAK_TERPERIKSA")                             # tanpa --chain: tidak dibaca, bukan OK
        with mock.patch.object(submission, "recover_signer", side_effect=RuntimeError("tanpa eth-account")):
            j = self.jejak()
        self.assertEqual(_status(j)["diterima"], "TAK_TERPERIKSA")
        self.assertIsNone(j["rusak_di"])
        r = _salin(self.root)                                                             # bar diganti sesudah tinjauan: vonis tak bisa diulang
        self.addCleanup(shutil.rmtree, r, True)
        _ubah_json(os.path.join(r, "ledger", "pengajuan", "laporan", f"{self.sha}.json"), lambda m: m.update(data_hash="0x" + "11" * 32), sha=True)
        j = self.jejak(r, hitung_ulang=True, bars_dir=os.path.join(ROOT, "ledger", "bars"))
        self.assertEqual(_status(j)["gerbang"], "TAK_TERPERIKSA")

    def test_a_reused_nonce_or_a_missing_public_copy_breaks_acceptance(self):
        r = _salin(self.root)
        self.addCleanup(shutil.rmtree, r, True)
        src = os.path.join(r, "ledger", "pengajuan", "masuk", f"{self.sha}.json")
        m = json.load(open(src, encoding="utf-8"))
        m2 = copy.deepcopy(m)
        m2["submission"]["spec"]["bot_id"] = "UJI-LAIN-1"
        m2["submission_sha"] = submission.submission_sha(seleksi._form(m2))
        _tulis_json(os.path.join(r, "ledger", "pengajuan", "masuk", f"{m2['submission_sha']}.json"), m2)
        self.assertEqual(self.jejak(r)["rusak_di"], "diterima")                            # nonce penerbit yang sama dipakai dua kali
        r2 = _salin(self.root)
        self.addCleanup(shutil.rmtree, r2, True)
        os.remove(os.path.join(r2, "ledger", "pengajuan", "masuk", f"{self.sha}.json"))
        self.assertEqual(self.jejak(r2)["rusak_di"], "diterima")                           # catatan registri tanpa salinan formulir publik


def _ubah_json(path, fn, sha=False):
    with open(path, encoding="utf-8") as f:
        obj = json.load(f)
    fn(obj)
    if sha:                                                                               # isi diubah DENGAN sha yang ikut dihitung ulang
        from engine.spec import sha0x
        obj["report_sha"] = sha0x({k: v for k, v in obj.items() if k != "report_sha"})
    _tulis_json(path, obj)


@unittest.skipUnless(HAVE_ETH, "eth-account tidak terpasang")
class BukuTests(unittest.TestCase):
    """Epoch mencatat yang dilewati; G10 = buku hidup + penghuni penerbit; ekor jalur (slot, pembunuh, sinyal) + sakelar komit worker."""

    @classmethod
    def setUpClass(cls):
        import uji_jalur_kandidat as u
        cls.u = u
        cls.root, cls.out = _jalan("template", 8)
        cls.luar = terdaftar.rincian(cls.root)[0]
        cls.md = u.BarDipotong({}, ledger.iso_ms("2026-05-06T00:00:00Z")).get("actual")

    def epoch(self, r, iso, **kw):
        a = SimpleNamespace(file=os.path.join(r, "ledger", "book", "buku.jsonl"), ledger=os.path.join(r, "ledger", "paper"),
                            bars=os.path.join(ROOT, "ledger", "bars"), now=iso, write=True, no_gates=False, root=r, gate_params=GateParams.fast(),
                            potong_ms=ledger.last_closed_bar(ledger.iso_ms(iso)))
        with mock.patch("builtins.print"):
            self.assertEqual(cli._book_epoch(a), 0)
        recs = ledger.load(a.file)
        self.assertEqual(book_live.verify_book(recs), [])                                  # medan baru tidak mengubah hitung ulang keputusan
        return recs[-1]

    def masuk_slot(self, r):
        """Epoch berikut dengan penantang yang memenuhi semua syarat (dibangun lewat `build_epoch`, jadi verify_book menghitung ulang yang sama)."""
        p = os.path.join(r, "ledger", "book", "buku.jsonl")
        recs = ledger.load(p)
        book = book_live.current_book(recs)
        sp, x = self.luar[BOT]["spec"], self.luar[BOT]
        now_s = (recs[-1]["epoch"] + 1) * 30 * DAY_S + 3600
        ch = slots.Challenger(bot_id=BOT, issuer=x["issuer"], spec_sha=sp.sha(), fingerprint=sp.fingerprint(), gate_verdict="LOLOS_SHADOW",
                              report_sha="0x" + "ab" * 32, book_sha=slots.book_sha(book), shadow_days=64, shadow_score_bps=120.0, paired={},
                              payout=x["payout"])
        rec = book_live.build_epoch(book, now_s, ledger.last_closed_bar(now_s * 1000), {e.bot_id: None for e in book}, [ch], {"B1-TREND": "TEKS"})
        self.assertEqual(rec["keputusan"][0][1], slots.ADMIT)
        recs.append(book_live.append(p, rec, recs))
        nxt = book_live.build_epoch(book_live.current_book(recs), now_s + 30 * DAY_S, ledger.last_closed_bar((now_s + 30 * DAY_S) * 1000),
                                    {}, [], {"B1-TREND": "TEKS", BOT: "BELUM"})
        book_live.append(p, nxt, recs)
        return now_s

    def test_the_epoch_records_the_bots_it_skipped_and_still_verifies(self):
        r = _salin(self.root)
        self.addCleanup(shutil.rmtree, r, True)
        os.remove(os.path.join(r, "ledger", "paper", f"{BOT}.jsonl"))
        rec = self.epoch(r, "2026-06-06T08:44:00Z")
        self.assertIn({"bot": BOT, "alasan": "ledger maju belum dimulai"}, rec["dilewati"])
        self.assertNotIn(BOT, [c["bot_id"] for c in rec["penantang"]])
        r2 = _salin(self.root)
        self.addCleanup(shutil.rmtree, r2, True)
        with mock.patch("engine.peninjau.tahan_bot", return_value="TAHAN: uji"):
            rec = self.epoch(r2, "2026-06-06T08:44:00Z")
        self.assertIn({"bot": BOT, "alasan": "ditahan peninjau LLM: TAHAN: uji"}, rec["dilewati"])
        j = seleksi.jejak(r2, BOT, chain=None)
        self.assertIn("dilewati - ditahan peninjau LLM", next(t["catatan"] for t in j["tahap"] if t["nama"] == "penantang"))

    def test_g10_incumbents_are_the_live_book_including_issuer_occupants(self):
        r = _salin(self.root)
        self.addCleanup(shutil.rmtree, r, True)
        self.assertEqual(sorted(cli._book_pnls(self.md, r)), ["B1-TREND"])
        self.masuk_slot(r)
        inc = cli._book_pnls(self.md, r)
        self.assertEqual(sorted(inc), ["B1-TREND", BOT])                                   # penerbit di slot direplay dari BotSpec registri
        book = book_live.current_book(ledger.load(os.path.join(r, "ledger", "book", "buku.jsonl")))
        palsu = [dataclasses.replace(e, spec_sha="0x" + "cd" * 32) if e.bot_id == BOT else e for e in book]
        pnl, tak = seleksi.petahana_buku(palsu, self.md, r)
        self.assertEqual((sorted(pnl), list(tak)), (["B1-TREND"], [BOT]))                  # sha buku != registri: tidak ditebak
        with open(os.path.join(r, "ledger", "book", "buku.jsonl"), "a", encoding="utf-8") as f:
            f.write('{"type": "epoch", "h": "0xpalsu"}\n')
        with self.assertRaises(ValueError):
            cli._book_pnls(self.md, r)                                                    # buku tidak sah: berhenti, bukan genesis diam-diam

    def test_an_admitted_candidate_shows_its_slot_and_killer_and_the_signal_stage_needs_the_chain(self):
        r = _salin(self.root)
        self.addCleanup(shutil.rmtree, r, True)
        self.masuk_slot(r)
        st = _status(seleksi.jejak(r, BOT, chain=None))
        self.assertEqual((st["penantang"], st["slot"], st["pembunuh"]), ("OK", "OK", "OK"))
        e = {"vonis": registri.LOLOS, "bot_id": BOT, "spec_sha": "0xs"}
        ticks = [{"type": "tick", "asof": (20_000 + i) * 86_400_000} for i in range(3)]
        c = {"e": e, "slot_s": 20_000 * DAY_S, "ledger": ticks, "chain": None}
        self.assertEqual(seleksi._t_sinyal(c).status, "TAK_TERPERIKSA")
        c["chain"] = self.u.ChainSimulasi()
        self.assertEqual(seleksi._t_sinyal(c).status, "BELUM")                              # belum dikomit (sakelar mati)
        c["chain"] = SimpleNamespace(committer="0xc", komit=lambda b, s, t: {"n": 1})
        self.assertEqual(seleksi._t_sinyal(c).status, "OK")

    def test_the_worker_commits_issuer_occupants_only_when_switched_on(self):
        import operator_loop as ol
        import signal_commit as sc
        r = _salin(self.root)
        self.addCleanup(shutil.rmtree, r, True)
        bots, specs, cat = ol.bot_komit(r, "0", bots=["B1-TREND"])
        self.assertEqual((bots, cat), (["B1-TREND"], []))                                  # bawaan: perilaku lama
        self.assertEqual(ol.bot_komit(r, "slot", bots=[])[0], [])                           # belum di slot
        self.assertEqual(ol.bot_komit(r, "semua", bots=[])[0], [BOT])
        self.assertIn("tidak dikenal", ol.bot_komit(r, "ya", bots=[])[2][0])
        self.masuk_slot(r)
        bots, specs, cat = ol.bot_komit(r, "slot", bots=["B1-TREND"])
        self.assertEqual(bots, ["B1-TREND", BOT])
        self.assertEqual(specs[BOT], self.luar[BOT]["spec"])                                # BotSpec dari formulir yang cocok registri
        paper = os.path.join(r, "ledger", "paper")
        last = ledger.load(os.path.join(paper, f"{BOT}.jsonl"))
        tk = [x for x in last if x["type"] == "tick"][-1]
        now = sc.asof_s_of(tk) + 3600
        ch = self.u.ChainSimulasi()
        ch.pin(BOT, specs[BOT].sha(), sc.asof_s_of(tk) - 10 * DAY_S)
        views = self.u.BarDipotong({}, ledger.last_closed_bar(now * 1000))
        acts = sc.plan([BOT], paper, views, self.u.AnchorSimulasi(ch), ch.committer, None, now, specs=specs)
        self.assertIn("commit", {a.kind for a in acts})                                    # worker akan mengomit tick terakhir penghuni
        acts = sc.plan([BOT], paper, views, self.u.AnchorSimulasi(ch), ch.committer, None, now)
        self.assertEqual([a.kind for a in acts], ["alarm"])                                # tanpa spesifikasi registri: tidak dikenal, tidak dikomit
        with open(os.path.join(r, "ledger", "pengajuan", "registri.jsonl"), "a", encoding="utf-8") as f:
            f.write('{"type": "pengajuan", "h": "0xpalsu"}\n')
        bots, _, cat = ol.bot_komit(r, "semua", bots=[])
        self.assertEqual(bots, [])                                                         # registri rusak = tidak ada bot penerbit
        self.assertIn("tidak dikomit", cat[0])


if __name__ == "__main__":
    unittest.main()
