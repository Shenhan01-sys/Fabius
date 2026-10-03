"""Alert operator (P101): pesan Telegram saat sesuatu butuh mata manusia. Worker Railway dan mode bayangan memanggil `Alerter.send`; tanpa kanal, ia diam.

Kanal = variabel Railway yang DIPASANG BUILDER sendiri (token bot adalah rahasia: tidak lewat chat, tidak di repo, tidak pernah dicetak):
  ALERT_TELEGRAM_TOKEN    token dari @BotFather
  ALERT_TELEGRAM_CHAT     chat id tujuan (angka; kirim satu pesan ke bot dulu supaya bot boleh membalas)
Tanpa keduanya: alert hanya dicatat di log sekali per kunci ("alert TANPA KANAL: ..."), tidak ada yang dikirim.

Aturan (SK-W18..W20 di vault/07-Testing/T8):
  - satu kunci (mis. "alarm:B1-TREND:2026-10-02") dikirim paling banyak sekali per COOLDOWN_S (6 jam); `sekali=True` = sekali per proses (kondisi
    permanen seperti TERLEWAT bar X tidak perlu diulang tiap 6 jam). Keadaan di memori, jadi restart worker bisa mengulang satu kali - lebih baik dua kali
    daripada nol;
  - gagal mengirim TIDAK pernah menghentikan putaran worker: dicatat (token disamarkan) dan dicoba lagi saat kunci yang sama muncul lagi;
  - isi pesan hanya keadaan publik (bot, bar, tx, saldo); tidak pernah kunci, token, atau isi berkas rahasia.

Uji kanal dari mesin yang punya variabelnya:  python -X utf8 tools/alert.py --test "halo dari Fabius"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from typing import Callable, Dict, Optional

COOLDOWN_S = 6 * 3600
API = "https://api.telegram.org/bot{token}/sendMessage"


def _post(url: str, data: dict, timeout: float = 10.0) -> dict:
    body = urllib.parse.urlencode(data).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data=body, method="POST"), timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


class Alerter:
    def __init__(self, token: Optional[str] = None, chat: Optional[str] = None, log: Callable[[str], None] = print,
                 post: Callable[[str, dict], dict] = _post, now: Callable[[], float] = time.time, prefix: str = "Fabius"):
        self.token = token if token is not None else (os.environ.get("ALERT_TELEGRAM_TOKEN") or "").strip()
        self.chat = chat if chat is not None else (os.environ.get("ALERT_TELEGRAM_CHAT") or "").strip()
        self.log, self.post, self.now, self.prefix = log, post, now, prefix
        self.sent: Dict[str, float] = {}

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.chat)

    def _clean(self, s: str) -> str:
        return s.replace(self.token, "<token>") if self.token else s

    def send(self, key: str, text: str, sekali: bool = False) -> str:
        """-> 'terkirim' | 'diredam' (kunci sama dalam cooldown, atau sudah pernah bila `sekali`) | 'tanpa-kanal' | 'gagal'. Tidak pernah melempar galat."""
        t = self.now()
        last = self.sent.get(key)
        if last is not None and (sekali or t - last < COOLDOWN_S):
            return "diredam"
        msg = f"[{self.prefix}] {text}"[:3900]
        if not self.enabled:
            self.sent[key] = t
            self.log(f"alert TANPA KANAL ({key}): {text[:200]}")
            return "tanpa-kanal"
        try:
            r = self.post(API.format(token=self.token), {"chat_id": self.chat, "text": msg, "disable_web_page_preview": "true"})
            if not r.get("ok"):
                raise RuntimeError(f"Telegram menolak: {str(r.get('description'))[:120]}")
        except Exception as e:  # noqa: BLE001 - alert gagal tidak boleh mematikan worker
            self.log(f"alert GAGAL dikirim ({key}): {self._clean(type(e).__name__ + ': ' + str(e))[:200]}")
            return "gagal"
        self.sent[key] = t
        self.log(f"alert terkirim ({key})")
        return "terkirim"


def main() -> int:
    ap = argparse.ArgumentParser(description="Uji kanal alert Telegram (P101).")
    ap.add_argument("--test", required=True, help="teks pesan uji")
    a = ap.parse_args()
    al = Alerter()
    if not al.enabled:
        print("ALERT_TELEGRAM_TOKEN / ALERT_TELEGRAM_CHAT belum dipasang di lingkungan ini: tidak ada yang dikirim")
        return 2
    st = al.send("uji", a.test)
    print(f"hasil: {st}")
    return 0 if st == "terkirim" else 1


if __name__ == "__main__":
    raise SystemExit(main())
