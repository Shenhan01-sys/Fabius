"""Penampung daftar tunggu tingkat 1 (P115) lewat bot Telegram Fabius. Stdlib saja; dijalankan rantai GitHub `paper-ledger` tiap putaran (5 menit).

Kenapa perlu penampung: Telegram hanya menyimpan update yang belum diambil selama 24 jam. Tanpa ada yang membaca, orang yang menekan "Masuk daftar
tunggu" di landing hilang besok. Penampungnya adalah CHAT BUILDER (ALERT_TELEGRAM_CHAT): tiap pendaftar dikabarkan ke sana (nama, @username, chat id,
asal tautan). Riwayat chat itu privat dan permanen, dan tidak ada data pribadi yang masuk repo publik.

Perintah untuk pengunjung:  /start [asal]  masuk daftar tunggu  ·  /bukti  vonis terbaru per bot  ·  /stop  keluar  ·  teks lain = bantuan

Aturan (T8 SK-P2..SK-P4):
  - kabar ke builder adalah catatannya. Kalau kabar itu GAGAL, putaran berhenti (TUNDA) dan update itu beserta sesudahnya TIDAK dikonfirmasi ke Telegram,
    jadi diulang 5 menit lagi. Pendaftar tidak boleh hilang diam-diam. Konfirmasi = `getUpdates` dengan offset id terakhir + 1 (disimpan di server Telegram,
    jadi tidak butuh berkas keadaan dan tidak dobel sesudah restart);
  - balasan ke pengunjung yang gagal (mis. ia memblokir bot) tidak menahan antrean;
  - log hanya hitungan. Log Actions repo ini PUBLIK: nama, username, chat id, isi pesan, dan token tidak pernah dicetak;
  - tidak menjanjikan apa pun: tingkat 1 TERKUNCI sampai bot lolos F-D16 + telaah hukum (F-D72); semua masih paper.

    python -X utf8 tools/waitlist.py --poll     # satu putaran: ambil update, proses, konfirmasi. Keluar 0 beres · 2 tanpa kanal · 3 TUNDA
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Dict, List, Optional

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

API = "https://api.telegram.org/bot{token}/{method}"
SITE = "https://fabius-one.vercel.app"
SNAPSHOT_URL = "https://raw.githubusercontent.com/Shenhan01-sys/Fabius/master/web/public/data/snapshot.json"
SNAPSHOT_LOCAL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "public", "data", "snapshot.json")
MAX_PER_POLL = 50

WELCOME = (
    "Fabius: sinyal yang disegel di BNB Chain SEBELUM hasilnya ada.\n\n"
    "Kamu masuk daftar tunggu tingkat 1 (sinyal waktu-nyata). Tingkat 1 masih TERKUNCI: baru dibuka untuk bot yang lolos uji maju (F-D16) dan "
    "sesudah telaah hukum. Kami kabari di chat ini saat dibuka. Semua masih paper; tidak ada janji keuntungan.\n\n"
    f"Gratis sekarang: bukti tiap sinyal {SITE} · untuk agen (MCP): {SITE}/mcp\n"
    "/bukti vonis terbaru · /stop keluar dari daftar tunggu\n\n"
    "EN: you are on the tier-1 waitlist. Tier 1 stays locked until a bot passes the forward test and a legal review. Paper only, no profit claims. "
    f"Free proof feed: {SITE}"
)
BYE = "Kamu sudah keluar dari daftar tunggu Fabius. /start untuk masuk lagi. (EN: you left the waitlist.)"
HELP = f"Fabius: /start masuk daftar tunggu tingkat 1 · /bukti vonis terbaru · /stop keluar. Bukti lengkap: {SITE}"
ADMIN_HELP = "Penampung daftar tunggu aktif (P115). Pendaftar baru dikabarkan di chat ini; riwayat chat ini adalah daftarnya."


class TelegramError(Exception):
    pass


def _call(token: str, method: str, params: dict, timeout: float = 15.0) -> dict:
    req = urllib.request.Request(API.format(token=token, method=method), data=urllib.parse.urlencode(params).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:  # Telegram membalas 4xx dengan JSON {"ok": false, "description": ...}
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            return {"ok": False, "description": f"HTTP {e.code}"}


def latest_proof(snap: Optional[dict]) -> str:
    """Vonis pemeriksa publik terbaru per bot dari snapshot web. Snapshot tak terbaca = katakan begitu, bukan "belum ada sinyal"."""
    if not snap:
        return f"Snapshot bukti tidak terbaca saat ini (bukan berarti kosong). Lihat langsung: {SITE}"
    ch = snap.get("chain")
    if not ch:
        return f"Snapshot terakhir belum memuat bacaan chain. Lihat langsung: {SITE}"
    last: Dict[str, dict] = {}
    for v in ch.get("verdicts", []):
        if v["bot"] not in last or v["bar"] > last[v["bot"]]["bar"]:
            last[v["bot"]] = v
    rows = [f"{b} bar {v['bar']}: {v['verdict']} ({v.get('revealed', 0)}/{v.get('n', 0)} sinyal terungkap)" for b, v in sorted(last.items())]
    return "Vonis terbaru (pemeriksa publik, tanpa kunci):\n" + "\n".join(rows or ["belum ada komit"]) + \
        f"\n\nper snapshot {snap.get('generated_utc', '?')} · cek live: {SITE} · agen: {SITE}/mcp"


def load_snapshot() -> Optional[dict]:
    try:
        with urllib.request.urlopen(SNAPSHOT_URL, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 - jatuh ke salinan lokal
        try:
            with open(SNAPSHOT_LOCAL, encoding="utf-8") as f:
                return json.load(f)
        except Exception:  # noqa: BLE001
            return None


def _who(m: dict) -> str:
    u = m.get("from") or {}
    name = " ".join(x for x in (u.get("first_name"), u.get("last_name")) if x) or "(tanpa nama)"
    return f"{name}{' @' + u['username'] if u.get('username') else ''} · chat {m['chat']['id']}"


class Waitlist:
    def __init__(self, token: str, admin: str, call: Callable[..., dict] = _call, log: Callable[[str], None] = print,
                 proof: Callable[[], str] = lambda: latest_proof(load_snapshot())):
        self.token, self.admin, self.call, self.log, self.proof = token, str(admin), call, log, proof

    def _send(self, chat, text: str) -> bool:
        try:
            r = self.call(self.token, "sendMessage", {"chat_id": chat, "text": text[:3900], "disable_web_page_preview": "true"})
            return bool(r.get("ok"))
        except Exception:  # noqa: BLE001 - jaringan; pemanggil yang memutuskan TUNDA atau lanjut
            return False

    def poll(self) -> Dict[str, int]:
        """Satu putaran. -> hitungan. Melempar TelegramError bila update tidak terbaca (TUNDA: tidak ada yang dikonfirmasi)."""
        try:
            r = self.call(self.token, "getUpdates", {"timeout": 0, "limit": MAX_PER_POLL, "allowed_updates": json.dumps(["message"])})
        except Exception as e:  # noqa: BLE001
            raise TelegramError(f"getUpdates tak terbaca ({type(e).__name__})") from None
        if not r.get("ok"):
            raise TelegramError(f"getUpdates ditolak: {str(r.get('description'))[:80].replace(self.token, '<token>')}")
        st = {"update": 0, "masuk": 0, "keluar": 0, "bukti": 0, "bantuan": 0, "builder": 0, "diabaikan": 0, "balasan_gagal": 0, "tertunda": 0}
        done: Optional[int] = None
        ups: List[dict] = r.get("result") or []
        for i, u in enumerate(ups):
            m = u.get("message") or {}
            chat = m.get("chat") or {}
            text = (m.get("text") or "").strip()
            if chat.get("type") != "private" or not text:
                st["diabaikan"] += 1
            elif str(chat.get("id")) == self.admin:
                st["builder"] += 1
                self._send(chat["id"], ADMIN_HELP)
            else:
                parts = text.split()
                cmd = parts[0].split("@")[0].lower() if text.startswith("/") else ""
                if cmd in ("/start", "/stop"):
                    src = parts[1][:64] if cmd == "/start" and len(parts) > 1 else "langsung"
                    note = f"daftar tunggu +1: {_who(m)} · asal {src}" if cmd == "/start" else f"daftar tunggu -1 (/stop): {_who(m)}"
                    if not self._send(self.admin, note):
                        # TUNDA: kabar ke builder = catatannya. Update ini dan sesudahnya tidak dikonfirmasi -> Telegram mengirimnya lagi putaran berikut.
                        st["tertunda"] = len(ups) - i
                        break
                    st["masuk" if cmd == "/start" else "keluar"] += 1
                    if not self._send(chat["id"], WELCOME if cmd == "/start" else BYE):
                        st["balasan_gagal"] += 1
                elif cmd in ("/bukti", "/proof"):
                    st["bukti"] += 1
                    if not self._send(chat["id"], self.proof()):
                        st["balasan_gagal"] += 1
                else:
                    st["bantuan"] += 1
                    if not self._send(chat["id"], HELP):
                        st["balasan_gagal"] += 1
            done = u["update_id"]
            st["update"] += 1
        if done is not None:
            try:
                ok = self.call(self.token, "getUpdates", {"offset": done + 1, "timeout": 0, "limit": 1}).get("ok")
            except Exception:  # noqa: BLE001
                ok = False
            st["konfirmasi_gagal"] = 0 if ok else 1
        # hanya hitungan: log Actions publik (tidak ada nama, username, chat id, isi pesan, token)
        self.log("daftar tunggu: " + ", ".join(f"{k} {v}" for k, v in st.items() if v))
        return st


def guarded_main(argv: Optional[List[str]] = None, env: Optional[dict] = None, make: Callable[..., Waitlist] = Waitlist) -> int:
    ap = argparse.ArgumentParser(description="Penampung daftar tunggu tingkat 1 lewat bot Telegram (P115).")
    ap.add_argument("--poll", action="store_true", required=True)
    ap.parse_args(argv)
    env = os.environ if env is None else env
    token, admin = (env.get("ALERT_TELEGRAM_TOKEN") or "").strip(), (env.get("ALERT_TELEGRAM_CHAT") or "").strip()
    if not (token and admin):
        print("daftar tunggu: ALERT_TELEGRAM_TOKEN / ALERT_TELEGRAM_CHAT tidak ada di lingkungan ini - tidak ada yang dibaca")
        return 2
    try:
        st = make(token, admin).poll()
    except TelegramError as e:
        print(f"daftar tunggu TUNDA: {e} - tidak ada yang dikonfirmasi, diulang putaran berikut")
        return 3
    except Exception as e:  # noqa: BLE001 - crash sendiri = TUNDA, bukan "tidak ada pendaftar"
        print(f"daftar tunggu TUNDA: crash {type(e).__name__} - diulang putaran berikut")
        return 3
    return 3 if st.get("tertunda") or st.get("konfirmasi_gagal") else 0


if __name__ == "__main__":
    raise SystemExit(guarded_main())
