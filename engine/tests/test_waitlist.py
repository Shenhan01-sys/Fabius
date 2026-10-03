"""P115: penampung daftar tunggu lewat bot Telegram (tools/waitlist.py). Telegram dipalsukan; tidak ada jaringan."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import waitlist as wl                                               # noqa: E402

TOKEN = "123456:SECRET-token-ABC"
ADMIN = "5000"


def msg(uid, chat, text, typ="private", first="Budi", username="budi_rahasia"):
    return {"update_id": uid, "message": {"chat": {"id": chat, "type": typ}, "from": {"first_name": first, "username": username}, "text": text}}


class FakeTelegram:
    """getUpdates mengembalikan antrean yang belum dikonfirmasi; sendMessage ke chat di `fail_to` gagal."""

    def __init__(self, updates, fail_to=(), get_fails=False):
        self.queue, self.fail_to, self.get_fails = list(updates), {str(c) for c in fail_to}, get_fails
        self.sent, self.confirmed = [], None

    def __call__(self, token, method, params):
        assert token == TOKEN
        if method == "getUpdates":
            if self.get_fails:
                raise OSError("jaringan mati")
            if "offset" in params:
                self.confirmed = params["offset"]
                self.queue = [u for u in self.queue if u["update_id"] >= params["offset"]]
                return {"ok": True, "result": self.queue[:1]}
            return {"ok": True, "result": list(self.queue)}
        if method == "sendMessage":
            if str(params["chat_id"]) in self.fail_to:
                return {"ok": False, "description": "Forbidden: bot was blocked by the user"}
            self.sent.append((str(params["chat_id"]), params["text"]))
            return {"ok": True}
        raise AssertionError(method)


def run(tg, proof=lambda: "vonis"):
    logs = []
    st = wl.Waitlist(TOKEN, ADMIN, call=tg, log=logs.append, proof=proof).poll()
    return st, logs


class PollTests(unittest.TestCase):
    def test_start_tells_the_builder_first_then_welcomes_and_confirms(self):
        tg = FakeTelegram([msg(10, 777, "/start tingkat1")])
        st, _ = run(tg)
        self.assertEqual(st["masuk"], 1)
        self.assertEqual(tg.sent[0][0], ADMIN)
        self.assertIn("daftar tunggu +1", tg.sent[0][1])
        self.assertIn("@budi_rahasia", tg.sent[0][1])
        self.assertIn("chat 777", tg.sent[0][1])
        self.assertIn("asal tingkat1", tg.sent[0][1])
        self.assertEqual(tg.sent[1], ("777", wl.WELCOME))
        self.assertIn("TERKUNCI", wl.WELCOME)
        self.assertEqual(tg.confirmed, 11)

    def test_builder_message_failing_holds_that_update_and_everything_after(self):
        # TUNDA (SK-P2): kabar ke builder = catatannya; gagal = update 21 dan 22 tidak dikonfirmasi, Telegram mengirimnya lagi putaran berikut
        tg = FakeTelegram([msg(20, 777, "/start"), msg(21, 888, "/start"), msg(22, 999, "/bukti")])
        calls = {"n": 0}
        real = tg.__call__

        def flaky(token, method, params):
            if method == "sendMessage" and str(params["chat_id"]) == ADMIN:
                calls["n"] += 1
                if calls["n"] == 2:
                    return {"ok": False, "description": "Too Many Requests"}
            return real(token, method, params)

        st, _ = run(flaky)
        self.assertEqual(st["masuk"], 1)
        self.assertEqual(st["tertunda"], 2)
        self.assertEqual(tg.confirmed, 21)
        self.assertNotIn("999", [c for c, _ in tg.sent])
        self.assertEqual(wl.guarded_main(["--poll"], env={"ALERT_TELEGRAM_TOKEN": TOKEN, "ALERT_TELEGRAM_CHAT": ADMIN},
                                         make=lambda t, a: wl.Waitlist(t, a, call=FakeTelegram([msg(1, 5, "/start")], fail_to=[ADMIN]), log=lambda s: None)), 3)

    def test_visitor_who_blocked_the_bot_does_not_hold_the_queue(self):
        tg = FakeTelegram([msg(30, 777, "/start"), msg(31, 888, "/start")], fail_to=[777])
        st, _ = run(tg)
        self.assertEqual(st["masuk"], 2)
        self.assertEqual(st["balasan_gagal"], 1)
        self.assertEqual(tg.confirmed, 32)

    def test_groups_and_non_text_are_confirmed_without_a_reply(self):
        tg = FakeTelegram([msg(40, -100, "/start", typ="group"), {"update_id": 41, "message": {"chat": {"id": 5, "type": "private"}, "photo": []}}])
        st, _ = run(tg)
        self.assertEqual(st["diabaikan"], 2)
        self.assertEqual(tg.sent, [])
        self.assertEqual(tg.confirmed, 42)

    def test_public_log_has_counts_only(self):
        # SK-P4: log Actions repo ini publik
        tg = FakeTelegram([msg(50, 777, "/start"), msg(51, 778, "halo"), msg(52, 779, "/stop")])
        _, logs = run(tg)
        joined = "\n".join(logs)
        for secret in ("budi", "Budi", "777", "778", "779", TOKEN, "halo"):
            self.assertNotIn(secret, joined)
        self.assertIn("masuk 1", joined)
        self.assertIn("keluar 1", joined)

    def test_unreadable_updates_are_tunda_not_empty(self):
        # SK-P3: getUpdates gagal = keluar 3, bukan "tidak ada pendaftar"
        tg = FakeTelegram([msg(60, 777, "/start")], get_fails=True)
        with self.assertRaises(wl.TelegramError):
            run(tg)
        rc = wl.guarded_main(["--poll"], env={"ALERT_TELEGRAM_TOKEN": TOKEN, "ALERT_TELEGRAM_CHAT": ADMIN},
                             make=lambda t, a: wl.Waitlist(t, a, call=tg, log=lambda s: None))
        self.assertEqual(rc, 3)
        self.assertEqual(wl.guarded_main(["--poll"], env={}), 2)

    def test_builder_chat_gets_status_not_a_waitlist_entry(self):
        tg = FakeTelegram([msg(70, int(ADMIN), "/start")])
        st, _ = run(tg)
        self.assertEqual((st["builder"], st["masuk"]), (1, 0))
        self.assertEqual(tg.sent, [(ADMIN, wl.ADMIN_HELP)])

    def test_bukti_reports_the_latest_verdict_per_bot(self):
        snap = {"generated_utc": "2026-10-03T09:00:00Z", "chain": {"verdicts": [
            {"bot": "B3-CARRY", "bar": "2026-10-01", "verdict": "SEBELUM KUNCI", "n": 0, "revealed": 0},
            {"bot": "B3-CARRY", "bar": "2026-10-02", "verdict": "SAH", "n": 1, "revealed": 1},
            {"bot": "B1-TREND", "bar": "2026-10-02", "verdict": "SAH", "n": 0, "revealed": 0}]}}
        text = wl.latest_proof(snap)
        self.assertIn("B3-CARRY bar 2026-10-02: SAH (1/1", text)
        self.assertNotIn("SEBELUM KUNCI", text)
        self.assertIn("tidak terbaca", wl.latest_proof(None))
        tg = FakeTelegram([msg(80, 777, "/bukti")])
        run(tg, proof=lambda: text)
        self.assertEqual(tg.sent, [("777", text)])


if __name__ == "__main__":
    unittest.main()
