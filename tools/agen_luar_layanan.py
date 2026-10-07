"""P151 + P166 di Railway: LAYANAN agent luar uji 2573 (milik builder) yang bisa ditinggal - satu proses, tiga tugas:

  (a) meja 5 menit: join bertanda tangan lalu loop PULL (`tools/desk_agent_client.py`), jawaban dari penjawab aturan
      `tools/agen_luar_uji_jawab.py` (tanpa model bahasa). Pull 404 = join ulang.
  (b) analis harian: sekali per penutupan bar harian, SEBELUM 00:00 UTC, pilihan berbasis aturan dari GET /analysts/input
      (`keputusan`, deterministik: tanpa jam di dalam alasan) -> JSON alasan per skema luar -> `SelectionAnchor.pick` dari dompet agent dengan
      reasonHash = sha256 JSON kanonis. Idempoten: pilihan yang sudah ada di chain tidak dikirim lagi; alasan yang sudah ditulis dipakai ulang
      (hash tidak berubah walau masukan gerbang berubah).
  (c) HTTP: GET /reasons/<bar_close>.json = byte persis JSON alasan, HANYA sesudah bar tutup (template `fabius.reasons` di kartu); GET /health.
      Berkas di `ALASAN_DIR` (volume Railway). Bila berkas alasan hilang tetapi salinan masukan ada, alasan dibangun ulang PERSIS dari salinan itu.

Satu-satunya rahasia = kunci dompet agent (`AGEN_LUAR_UJI_KEY`). Layanan MENOLAK MULAI bila lingkungannya memuat variabel lain yang bernamakan
rahasia (pola `tools/pelari_kode.py`). Agent ini berlabel jujur "builder-operated test agent" di kartunya - bukan adopsi pihak ketiga.

Lingkungan: AGEN_LUAR_UJI_KEY (wajib), AGEN_LUAR_ID (2573), FABIUS_GATE, ALASAN_DIR (/data/alasan), PORT (8080), RPC_URL (opsional), ANALIS_TIAP_S (300).
Pakai:  python -X utf8 tools/agen_luar_layanan.py
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import agen_luar_uji_jawab as jw                                            # noqa: E402  (stdlib saja)

GATE = "https://fabius-x402-production.up.railway.app"
VAR_KUNCI = "AGEN_LUAR_UJI_KEY"
RAHASIA = re.compile(r"(KEY|SECRET|TOKEN|PASSW|MNEMONIC|PRIVATE_K)", re.I)
DAY_S = 86_400
CHAIN_ID = 97
BOTS = ("B1-TREND", "B2-RS", "B3-CARRY", "B4-LISTING-FADE", "B5-CORE-RWA", "B6-BOUNCE")
SIG_PICK = "pick(uint256,uint64,bytes32,uint8,bytes32)"
NAMA = "Fabius external test agent (rule-based)"
# USULAN (belum diputus builder): aturan pilihan harian + cadangan waktu. Sengaja sederhana: agent ini membuktikan JALUR, bukan keunggulan.
ATURAN = ("B1-TREND bila breadth_di_atas_60h >= 0,6 dan btc_ret_60h > 0; selain itu B3-CARRY bila funding_rata_7h_tahunan >= 0,10; selain itu "
          "B6-BOUNCE bila btc_ret_30h <= -0,10; selain itu B5-CORE-RWA. Keyakinan 30-70 dari kekuatan kondisinya.")
CADANGAN_S = 2 * 3600          # data gerbang belum segar sampai 2 jam sebelum penutupan -> tetap memilih dengan data yang ada
MAKS_TERKIRIM = 3              # tx yang SUDAH masuk mempool tetapi gagal (revert tertambang / receipt tidak datang) per bar -> berhenti (batas gas)


def rahasia_lain(env: Optional[Dict[str, str]] = None) -> List[str]:
    """Nama variabel bernamakan rahasia SELAIN kunci agent (layanan ini hanya boleh memegang kunci dompetnya sendiri)."""
    env = os.environ if env is None else env
    return sorted(k for k in env if RAHASIA.search(k) and k != VAR_KUNCI and not k.startswith("PYTHON"))


def canon(o) -> bytes:
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(o) -> str:
    """= `tools/analis.py::sha` (sha256 JSON kanonis: kunci terurut, tanpa spasi, UTF-8) - reasonHash yang diperiksa gerbang."""
    return "0x" + hashlib.sha256(o if isinstance(o, bytes) else canon(o)).hexdigest()


def ascii32(s: str) -> bytes:
    b = s.encode("ascii")
    if not 0 < len(b) <= 32:
        raise ValueError("bot id 1..32 byte")
    return b + b"\x00" * (32 - len(b))


def _f(d: dict, k: str) -> float:
    try:
        return float(d.get(k) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def keputusan(inp: dict, agent_id: int) -> dict:
    """JSON alasan (skema luar `analis.SKEMA_ALASAN`) dari masukan publik gerbang - DETERMINISTIK (masukan sama = byte sama)."""
    m = inp.get("masukan") or {}
    rp, ada = m.get("rezim_pasar") or {}, [b for b in BOTS if b in (m.get("bot") or {})] or list(BOTS)
    br60, r60, r30, fund = _f(rp, "breadth_di_atas_60h"), _f(rp, "btc_ret_60h"), _f(rp, "btc_ret_30h"), _f(rp, "funding_rata_7h_tahunan")
    if br60 >= 0.6 and r60 > 0:
        bot, kuat = "B1-TREND", br60
        alasan = f"Trend regime: {br60:.0%} of the universe is above its 60-day level and BTC is {r60:+.1%} over 60 days."
    elif fund >= 0.10:
        bot, kuat = "B3-CARRY", min(1.0, fund / 0.3)
        alasan = f"Funding is rich: the 7-day average annualises to {fund:.1%}, which is the carry the B3 rule collects."
    elif r30 <= -0.10:
        bot, kuat = "B6-BOUNCE", min(1.0, -r30 / 0.3)
        alasan = f"BTC is {r30:+.1%} over 30 days; a stretched drop is the B6 setup."
    else:
        bot, kuat = "B5-CORE-RWA", 0.2
        alasan = (f"No clear regime: breadth above 60 days {br60:.0%}, BTC 60 days {r60:+.1%}, funding {fund:.1%} a year; "
                  "a small core allocation is the cautious default.")
    if bot not in ada:
        bot, alasan = ada[0], alasan + f" The rule's bot is not offered today, so {ada[0]} is used."
    return {"v": 1, "agent_id": int(agent_id), "bar_close": int(inp["bar_close"]), "nama": NAMA,
            "model": "rules (tools/agen_luar_layanan.py), no language model", "aturan": ATURAN, "masukan_sha256": sha(m),
            "pilihan": {"bot": bot, "keyakinan": int(round(min(70.0, max(30.0, 30.0 + 40.0 * kuat)))), "alasan": alasan,
                        "risiko": "Rule-based test agent operated by the Fabius builder; it proves the external path, it claims no edge."}}


def segar(inp: dict) -> bool:
    """Masukan sudah memuat tick bar harian terakhir sebelum penutupan yang dipilih (bar_terakhir = tanggal bar_close - 2 hari)."""
    try:
        want = dt.datetime.fromtimestamp(int(inp["bar_close"]) - 2 * DAY_S, dt.timezone.utc).strftime("%Y-%m-%d")
        return ((inp.get("masukan") or {}).get("rezim_pasar") or {}).get("bar_terakhir") == want
    except (KeyError, TypeError, ValueError):
        return False


class Arsip:
    """Berkas per bar di `folder`: <close>.json (byte JSON alasan kanonis), <close>.masukan.json (salinan masukan), <close>.pick.json (hasil kirim)."""

    def __init__(self, folder: str, agent_id: int):
        self.folder, self.agent_id = folder, int(agent_id)
        os.makedirs(folder, exist_ok=True)

    def _p(self, close: int, akhir: str) -> str:
        return os.path.join(self.folder, f"{int(close)}{akhir}")

    def _tulis(self, path: str, data: bytes) -> None:
        tmp = path + ".tmp"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, path)

    def simpan(self, close: int, alasan: dict, masukan: dict) -> bytes:
        self._tulis(self._p(close, ".masukan.json"), canon({"bar_close": int(close), "masukan": masukan}))
        b = canon(alasan)
        self._tulis(self._p(close, ".json"), b)
        return b

    def alasan(self, close: int) -> Optional[bytes]:
        """Byte alasan; bila berkasnya hilang tetapi salinan masukan ada, dibangun ulang PERSIS (keputusan deterministik)."""
        p = self._p(close, ".json")
        if os.path.exists(p):
            with open(p, "rb") as f:
                return f.read()
        q = self._p(close, ".masukan.json")
        if os.path.exists(q):
            with open(q, "rb") as f:
                b = canon(keputusan(json.loads(f.read()), self.agent_id))
            self._tulis(p, b)
            return b
        return None

    def catat(self, close: int, rec: dict) -> None:
        self._tulis(self._p(close, ".pick.json"), canon(rec))

    def catatan(self, close: int) -> dict:
        try:
            with open(self._p(close, ".pick.json"), "rb") as f:
                return json.loads(f.read())
        except (OSError, ValueError):
            return {}


class Rantai:
    """SelectionAnchor sungguhan lewat `tools/evm.py` (estimateGas dulu: revert ketahuan SEBELUM gas terbakar)."""

    def __init__(self, key: str, rpc_urls: Optional[List[str]] = None):
        import evm
        first = (os.environ.get("RPC_URL") or "").strip()
        urls = rpc_urls or (([first] if first else []) + [u for u in evm.DEFAULT_RPCS if u != first])
        self.ev, self.key, self.evm = evm.Evm(urls, CHAIN_ID), key, evm

    def sudah(self, sel: str, agent_id: int, close: int) -> bool:
        p = self.ev.call_decode(sel, "getPick(uint256,uint64)", ("uint256", "uint64"), (int(agent_id), int(close)), ("(bytes32,uint8,bytes32,uint64)",))[0]
        return int(p[3]) != 0

    def kirim(self, sel: str, agent_id: int, close: int, bot: str, keyakinan: int, rh: str) -> dict:
        data = self.evm.calldata(SIG_PICK, ("uint256", "uint64", "bytes32", "uint8", "bytes32"),
                                 (int(agent_id), int(close), ascii32(bot), int(keyakinan), bytes.fromhex(rh[2:])))
        r = self.ev.send(self.key, sel, data)
        return {"ok": self.evm.receipt_ok(r), "tx": r.get("transactionHash")}


def langkah_analis(inp: dict, agent_id: int, arsip: Arsip, rantai, now_s: int, log: Callable[[str], None] = print) -> str:
    """Satu putaran analis harian. -> status: lewat | sudah | tunggu-data | dikomit | gagal | berhenti. Tidak pernah melempar."""
    try:
        close, sel = int(inp["bar_close"]), str(inp["selection_anchor"])
    except (KeyError, TypeError, ValueError):
        return "masukan-rusak"
    if now_s >= close or close % DAY_S:
        return "lewat"
    try:
        if rantai.sudah(sel, agent_id, close):
            if arsip.alasan(close) is None:
                log(f"PERINGATAN pilihan bar {close} sudah di chain tetapi alasannya tidak ada di {arsip.folder} (volume hilang?)")
            return "sudah"
    except Exception as e:  # noqa: BLE001 - RPC: coba lagi putaran berikutnya
        log(f"analis: baca getPick gagal {type(e).__name__}: {str(e)[:120]}")
        return "gagal"
    ada = arsip.alasan(close)
    if ada is None:
        if not segar(inp) and now_s < close - CADANGAN_S:
            return "tunggu-data"
        ada = arsip.simpan(close, keputusan(inp, agent_id), inp.get("masukan") or {})
    a = json.loads(ada)
    rh = sha(ada)
    terkirim = int(arsip.catatan(close).get("terkirim", 0))
    if terkirim >= MAKS_TERKIRIM:
        log(f"analis bar {close}: BERHENTI - {terkirim} tx terkirim gagal untuk bar ini (batas gas {MAKS_TERKIRIM}); periksa log / saldo")
        return "berhenti"
    try:
        hasil = rantai.kirim(sel, agent_id, close, a["pilihan"]["bot"], a["pilihan"]["keyakinan"], rh)
    except Exception as e:  # noqa: BLE001 - estimateGas revert = nol gas; "tx 0x.. belum masuk blok" = sudah di mempool
        hasil = {"ok": False, "galat": f"{type(e).__name__}: {str(e)[:160]}"}
    if not hasil.get("ok") and (hasil.get("tx") or "belum masuk blok" in str(hasil.get("galat"))):
        terkirim += 1
    arsip.catat(close, {"bar_close": close, "bot": a["pilihan"]["bot"], "keyakinan": a["pilihan"]["keyakinan"], "reasonHash": rh, "t": int(now_s),
                        "terkirim": terkirim, **hasil})
    log(f"analis bar {close}: {a['pilihan']['bot']} ({a['pilihan']['keyakinan']}) reasonHash {rh[:18]}... {'DIKOMIT ' + str(hasil.get('tx')) if hasil.get('ok') else 'GAGAL ' + str(hasil.get('galat') or hasil.get('tx'))}")
    return "dikomit" if hasil.get("ok") else "gagal"


def loop_meja(gate: str, agent_id: int, key: str, status: dict, stop: threading.Event, log: Callable[[str], None] = print,
              sekali: bool = False) -> None:
    """Join lalu PULL tiap siklus; jawaban dari penjawab aturan. `sekali` = berhenti sesudah satu siklus terjawab (tes)."""
    import desk_agent_client as dc
    terdaftar = False
    while not stop.is_set():
        try:
            if not terdaftar:
                code, out = dc.join(gate, agent_id, key)
                terdaftar = code in (200, 201)
                status["join"] = {"http": code, "t": int(time.time())}
                log(f"meja: join HTTP {code} {str(out)[:160]}")
                if not terdaftar:
                    stop.wait(30)
                    continue
            code, req = dc.pull(gate, agent_id, key)
            if code == 404:
                terdaftar = False
                continue
            if code != 200:
                log(f"meja: pull HTTP {code} {str(req)[:160]}")
                stop.wait(5)
                continue
            if not req.get("siklus"):
                stop.wait(min(int(req.get("retry_after_s", 5)), 10))
                continue
            aset, nama = jw.urai(req.get("prompt") or "")
            code, out = dc.answer(gate, agent_id, key, req, json.dumps(jw.putuskan(aset, nama)))
            status["siklus_terakhir"] = {"siklus": req["siklus"], "http": code, "t": int(time.time())}
            log(f"meja: siklus {req['siklus']} HTTP {code}")
            if sekali:
                return
        except Exception as e:  # noqa: BLE001 - jaringan / gerbang deploy ulang: tunggu lalu lanjut
            log(f"meja: {type(e).__name__}: {str(e)[:160]}")
            stop.wait(10)


def buat_server(arsip: Arsip, status: dict, now: Callable[[], float] = time.time, host: str = "0.0.0.0", port: int = 8080) -> ThreadingHTTPServer:
    class H(BaseHTTPRequestHandler):
        def log_message(self, fmt, *a):
            return

        def _kirim(self, code: int, body: bytes, ctype: str = "application/json") -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = self.path.split("?")[0].rstrip("/")
            m = re.fullmatch(r"/reasons/(\d{9,11})\.json", path)
            if m:
                close = int(m.group(1))
                if now() < close:
                    return self._kirim(404, canon({"error": "served after the bar closes"}))
                b = arsip.alasan(close)
                return self._kirim(200, b) if b is not None else self._kirim(404, canon({"error": "no pick for this bar"}))
            if path in ("", "/health"):
                return self._kirim(200, canon({"ok": True, "agent_id": arsip.agent_id, "operator": "Fabius builder (test agent)", **status}))
            return self._kirim(404, canon({"error": "unknown route"}))
    return ThreadingHTTPServer((host, port), H)


def main() -> int:
    bad = rahasia_lain()
    if bad:
        print(f"MENOLAK MULAI: layanan agent luar hanya boleh memegang {VAR_KUNCI}; lingkungan memuat {bad}")
        return 3
    key = os.environ.get(VAR_KUNCI)
    if not key:
        print(f"{VAR_KUNCI} tidak ada")
        return 2
    gate = os.environ.get("FABIUS_GATE", GATE).rstrip("/")
    aid = int(os.environ.get("AGEN_LUAR_ID", "2573"))
    folder = os.environ.get("ALASAN_DIR", "/data/alasan")
    try:
        arsip = Arsip(folder, aid)
        arsip._tulis(os.path.join(folder, ".uji-tulis"), b"ok")
    except OSError as e:
        print(f"{folder} tidak bisa ditulis ({type(e).__name__}): volume Railway dipasang milik root - lihat TL48 (RAILWAY_RUN_UID=0)")
        return 4
    status, stop = {}, threading.Event()
    srv = buat_server(arsip, status, port=int(os.environ.get("PORT", "8080")))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    threading.Thread(target=loop_meja, args=(gate, aid, key, status, stop), daemon=True).start()
    print(f"agent luar uji {aid} mulai | gerbang {gate} | alasan {folder} | port {srv.server_address[1]}", flush=True)
    import desk_agent_client as dc
    rantai, tiap = Rantai(key), int(os.environ.get("ANALIS_TIAP_S", "300"))
    while True:
        try:
            code, inp = dc.http(f"{gate}/analysts/input")
            st = langkah_analis(inp, aid, arsip, rantai, int(time.time())) if code == 200 else f"input HTTP {code}"
        except Exception as e:  # noqa: BLE001
            st = f"{type(e).__name__}: {str(e)[:120]}"
        status["analis"] = {"status": st, "t": int(time.time())}
        time.sleep(tiap)


if __name__ == "__main__":
    raise SystemExit(main())
