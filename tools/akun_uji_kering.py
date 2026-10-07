"""P157 (F5): uji kering ujung-ke-ujung akun MCP berbayar - gerbang HTTP LOKAL (handler gerbang yang sama), chain PALSU, tanpa transaksi.

Yang sungguhan: handler `x402_sinyal.make_handler`, `Gate.settle` + `paid_in_receipt` (receipt palsu dibangun dari calldata settle yang SUNGGUHAN
didekode), pemeriksa otorisasi `check_payment`, tanda tangan EIP-712 (Permit2 witness + EIP-2612) dan EIP-191 dari dompet BUANGAN (kunci acak, tanpa
dana, tidak pernah disimpan), buku besar akun, dan data meja keluaran `meja2.siklus2` ASLI dengan pasar + agent sintetis (`meja_eval.contoh_arsip`).
Yang palsu: chain (tidak ada tx), harga pasar, agent. Angka sintetis TIDAK berarti apa pun tentang meja hidup.

Dipakai `python -X utf8 tools/akun_mcp.py uji-kering` dan tes `engine/tests/test_akun_mcp.py`."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from typing import Callable, Dict, List, Optional, Tuple
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (ROOT, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

TOKEN = "0x" + "fa" * 20                        # FAB palsu (tidak ada di chain mana pun)
PAYTO = "0x" + "fc" * 20                        # payTo gerbang palsu
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def isi_meja_contoh(meja_dir: str, siklus: int = 3, t_awal: int = 1_791_540_000) -> int:
    """Tulis keluaran `meja2.siklus2` ASLI (pasar + tiga agent sintetis) ke berkas meja gerbang: rekaman, siklus, fitur. -> siklus terakhir."""
    import meja_eval as me
    hari = me.contoh_arsip(hari=1, siklus=siklus, t_awal=t_awal)
    akhir = 0
    for d in hari:
        rek = sorted(d["records"] + d["agent_records"], key=lambda r: (r["siklus"], r["agent"] != "v2", r["agent"]))
        tgl = time.strftime("%Y-%m-%d", time.gmtime(rek[0]["siklus"]))
        for kind in ("rekaman", "siklus", "fitur"):
            os.makedirs(os.path.join(meja_dir, kind), exist_ok=True)
        with open(os.path.join(meja_dir, "rekaman", tgl + ".jsonl"), "w", encoding="utf-8", newline="\n") as f:
            for r in rek:
                f.write(json.dumps(r, sort_keys=True) + "\n")
        with open(os.path.join(meja_dir, "siklus", tgl + ".jsonl"), "w", encoding="utf-8", newline="\n") as f:
            for c in d["cycles"]:
                f.write(json.dumps({"siklus": c["cycle"], "root": c["root"], "tx": "0x" + hashlib.sha256(c["root"].encode()).hexdigest(),
                                    "status": "dikomit", "n": c["leaves"], "harga": c["prices"], "harga_v2": c["prices"]}, sort_keys=True) + "\n")
        with open(os.path.join(meja_dir, "fitur", tgl + ".jsonl"), "w", encoding="utf-8", newline="\n") as f:
            for c in d["cycles"]:
                t0 = c["cycle"]
                f.write(json.dumps({"v": 1, "t": t0, "sha": f"0x{t0:064x}", "registry_sha": "0x" + "ab" * 32,
                                    "kesehatan": {"binance": {"cakupan": 1.0, "status": "ok"}},
                                    "sumber": {"binance": {}}, "fitur_aset": {a: {"r_1j": 0.0, "harga": p} for a, p in c["prices"].items()},
                                    "fitur_bot": {"B1-TREND": {"pnl_1j": 0.0}}, "durasi_s": 3.0}, sort_keys=True) + "\n")
            akhir = max(akhir, max(c["cycle"] for c in d["cycles"]))
    return akhir


class RantaiPalsu:
    """Chain palsu untuk `Gate.settle`: `eth_call` lolos, `send` MENDEKODE calldata settle sungguhan (eth_abi) lalu membalas receipt sukses berisi
    Transfer(pemilik -> witness.to, jumlah) - persis yang diperiksa `paid_in_receipt`. Tidak ada tx; tidak ada jaringan."""

    def __init__(self, token: str = TOKEN):
        self.token, self.sent = token, []

    def rpc(self, method, params):
        return "0x"

    def send(self, pk, to, data, gas=None):
        import x402_sinyal as xs
        from eth_abi import decode
        vals = decode(xs.SETTLE_PARAMS, bytes(data)[4:])
        pemilik, jumlah, ke = vals[2], int(vals[1][0][1]), vals[3][0]
        pad = lambda a: "0x" + "0" * 24 + a.lower()[2:]                                     # noqa: E731
        tx = "0x" + hashlib.sha256(bytes(data)).hexdigest()
        self.sent.append(tx)
        return {"status": "0x1", "transactionHash": tx,
                "logs": [{"address": self.token, "topics": [TRANSFER_TOPIC, pad(pemilik), pad(ke)], "data": hex(jumlah)}]}

    def call_decode(self, to, sig, types, values, out):
        return (0,)


def tanda_x402(akun, accepts: dict, now_s: int, tok_nonce: int = 0, nonce: Optional[int] = None) -> str:
    """Header PAYMENT-SIGNATURE berbentuk SAMA dengan `web/src/lib/x402-buy.ts::buy`: Permit2 witness + EIP-2612, ditandatangani `akun` (eth-account)."""
    from eth_account import Account
    import x402_sinyal as xs
    owner, amount, pay_to = akun.address, accepts["amount"], accepts["payTo"]
    va, dl = str(now_s - 15), str(now_s + 110)
    n = str(nonce if nonce is not None else int.from_bytes(os.urandom(16), "big"))
    p2 = {"domain": {"name": "Permit2", "chainId": 97, "verifyingContract": xs.PERMIT2},
          "types": {"EIP712Domain": [{"name": "name", "type": "string"}, {"name": "chainId", "type": "uint256"}, {"name": "verifyingContract", "type": "address"}],
                    "PermitWitnessTransferFrom": [{"name": "permitted", "type": "TokenPermissions"}, {"name": "spender", "type": "address"},
                                                  {"name": "nonce", "type": "uint256"}, {"name": "deadline", "type": "uint256"}, {"name": "witness", "type": "Witness"}],
                    "TokenPermissions": [{"name": "token", "type": "address"}, {"name": "amount", "type": "uint256"}],
                    "Witness": [{"name": "to", "type": "address"}, {"name": "validAfter", "type": "uint256"}]},
          "primaryType": "PermitWitnessTransferFrom",
          "message": {"permitted": {"token": accepts["asset"], "amount": int(amount)}, "spender": xs.PROXY, "nonce": int(n), "deadline": int(dl),
                      "witness": {"to": pay_to, "validAfter": int(va)}}}
    t2612 = {"domain": {"name": "Fabius Credit", "version": "1", "chainId": 97, "verifyingContract": accepts["asset"]},
             "types": {"EIP712Domain": [{"name": "name", "type": "string"}, {"name": "version", "type": "string"}, {"name": "chainId", "type": "uint256"},
                                        {"name": "verifyingContract", "type": "address"}],
                       "Permit": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}, {"name": "value", "type": "uint256"},
                                  {"name": "nonce", "type": "uint256"}, {"name": "deadline", "type": "uint256"}]},
             "primaryType": "Permit", "message": {"owner": owner, "spender": xs.PERMIT2, "value": int(amount), "nonce": tok_nonce, "deadline": int(dl)}}
    from eth_account.messages import encode_typed_data
    s1 = Account.sign_typed_data(akun.key, full_message=p2)
    s2 = Account.sign_typed_data(akun.key, full_message=t2612)
    for td, sg in ((p2, s1), (t2612, s2)):                                                  # tanda tangan memang dari dompet itu
        if Account.recover_message(encode_typed_data(full_message=td), signature=sg.signature) != owner:
            raise AssertionError("tanda tangan EIP-712 tidak pulih ke dompet penanda tangan")
    pay = {"x402Version": 2, "accepted": {"scheme": "exact", "network": "eip155:97", "amount": amount, "asset": accepts["asset"], "payTo": pay_to},
           "payload": {"signature": "0x" + s1.signature.hex().removeprefix("0x"),
                       "permit2Authorization": {"permitted": {"token": accepts["asset"], "amount": amount}, "from": owner, "spender": xs.PROXY, "nonce": n,
                                                "deadline": dl, "witness": {"to": pay_to, "validAfter": va}}},
           "extensions": {"eip2612GasSponsoring": {"info": {"from": owner, "asset": accepts["asset"], "spender": xs.PERMIT2, "amount": amount,
                                                            "nonce": str(tok_nonce), "deadline": dl, "signature": "0x" + s2.signature.hex().removeprefix("0x"),
                                                            "version": "1"}}}}
    return base64.b64encode(json.dumps(pay).encode()).decode()


def tanda_pesan(akun, pesan: str) -> str:
    from eth_account import Account
    from eth_account.messages import encode_defunct
    return "0x" + Account.sign_message(encode_defunct(text=pesan), private_key=akun.key).signature.hex().removeprefix("0x")


def gerbang_lokal(repo: str, now_s: int):
    """Gerbang `x402_sinyal.Gate` atas repo sementara (deployments/97.json palsu, tanpa ledger) + chain palsu. -> (gate, rantai)."""
    import x402_sinyal as xs
    os.makedirs(os.path.join(repo, "deployments"), exist_ok=True)
    os.makedirs(os.path.join(repo, "ledger", "paper"), exist_ok=True)
    with open(os.path.join(repo, "deployments", "97.json"), "w", encoding="utf-8") as f:
        json.dump({"x402_sinyal": {"token": TOKEN, "facilitator": PAYTO}, "m3": {"committer": "0x" + "11" * 20},
                   "contracts": {"SignalAnchor": "0x" + "a1" * 20, "LockRegistry": "0x" + "a2" * 20, "DeskAnchor": "0x" + "a3" * 20}}, f)
    g = xs.Gate(xs.Data(repo), "0x" + "77" * 32, "http://127.0.0.1", "https://web.example", ev=None, log=lambda m: None, now=lambda: now_s)
    rantai = RantaiPalsu()
    g.ev = rantai
    g.views = lambda cfg: (None, None)
    return g, rantai


def http(base: str, metode: str, path: str, body: Optional[dict] = None, headers: Optional[dict] = None) -> Tuple[int, dict, dict]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=metode, headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode()), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}"), dict(e.headers)


def jalankan(cetak: Callable[[object], None] = print, simpan: Optional[str] = None) -> int:
    """Seluruh alur lewat HTTP ke gerbang lokal. -> 0 bila semua langkah sesuai harapan, 1 bila ada yang menyimpang."""
    from eth_account import Account
    import akun_mcp as am
    import x402_sinyal as xs
    from http.server import ThreadingHTTPServer
    tmp = tempfile.mkdtemp(prefix="akun-uji-")
    langkah: List[dict] = []
    ok = True

    def catat(nama: str, kode: int, harap: int, info: dict) -> None:
        nonlocal ok
        ok = ok and kode == harap
        langkah.append({"langkah": nama, "http": kode, "harap": harap, **info})

    try:
        with mock.patch.dict(os.environ, {"FABIUS_F5": "hidup"}):
            t_akhir = 0
            g, rantai = gerbang_lokal(os.path.join(tmp, "repo"), 0)
            t_akhir = isi_meja_contoh(g.meja_dir)
            now = t_akhir + 60
            g.now = lambda: now
            g.akun = am.Akun(os.path.join(tmp, "akun"), now=g.now)
            srv = ThreadingHTTPServer(("127.0.0.1", 0), xs.make_handler(g))
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            base = f"http://127.0.0.1:{srv.server_address[1]}"
            g.public_url = base
            dompet = Account.create()                                                       # dompet BUANGAN: tanpa dana, tidak disimpan
            k, b, _ = http(base, "GET", "/account/pricing")
            catat("harga (gratis)", k, 200, {"signal_atomic": b["tools"]["paid"]["fabius_signal"]["atomic"], "kepala": b["ledger"]["head"][:18]})
            k, b, h = http(base, "GET", "/account/deposit/100000")
            req = json.loads(base64.b64decode(h.get("PAYMENT-REQUIRED") or h.get("Payment-Required")).decode())
            catat("deposit tanpa bayar -> 402", k, 402, {"amount": req["accepts"][0]["amount"], "payTo": req["accepts"][0]["payTo"]})
            hdr = tanda_x402(dompet, req["accepts"][0], now)
            k, b, _ = http(base, "GET", "/account/deposit/100000", headers={"PAYMENT-SIGNATURE": hdr})
            catat("deposit 0,1 FAB (x402, tanda tangan EIP-712 sungguhan)", k, 200, {"saldo": b.get("balance_atomic"), "tx_palsu": len(rantai.sent)})
            k, b, _ = http(base, "GET", "/account/deposit/100000", headers={"PAYMENT-SIGNATURE": hdr})
            catat("otorisasi sama dikirim ulang -> tidak dikreditkan lagi", k, 200, {"repeat": b.get("repeat"), "saldo": b.get("balance_atomic"),
                                                                                  "tx_palsu": len(rantai.sent)})
            ts = int(now)
            pesan = am.pesan_kunci(dompet.address, ts)
            k, b, _ = http(base, "POST", "/account/key", {"wallet": dompet.address, "ts": ts, "signature": tanda_pesan(dompet, pesan)})
            kunci = b.get("key")
            catat("kunci API dari tanda tangan EIP-191", k, 201, {"key_id": b.get("key_id"), "kunci_di_buku": kunci is not None and kunci in open(g.akun.path, encoding="utf-8").read()})
            auth = {"Authorization": f"Bearer {kunci}"}
            k, b, _ = http(base, "POST", "/account/key", {"wallet": dompet.address, "ts": ts, "signature": tanda_pesan(dompet, pesan)})
            catat("pesan kunci yang sama dipakai ulang -> ditolak", k, 409, {})
            k, b, _ = http(base, "POST", "/account/call", {"tool": "fabius_signal", "call_id": "uji-1"}, headers={"Authorization": "Bearer fabk_" + "x" * 43})
            catat("kunci palsu -> 401 tanpa data (SK-M12)", k, 401, {"ada_data": "data" in b})
            k, b, _ = http(base, "POST", "/account/call", {"tool": "fabius_signal", "call_id": "uji-1"}, headers=auth)
            catat("fabius_signal 0,01 FAB", k, 200, {"bot": (b.get("data") or {}).get("dominant_bot"), "saldo": b.get("balance_atomic"),
                                                    "root": ((b.get("data") or {}).get("proof") or {}).get("root", "")[:18]})
            k, b2, _ = http(base, "POST", "/account/call", {"tool": "fabius_signal", "call_id": "uji-1"}, headers=auth)
            catat("call_id sama -> jawaban sama, tanpa potongan kedua", k, 200, {"repeat": b2.get("repeat"), "saldo": b2.get("balance_atomic"),
                                                                              "sha_sama": b2.get("response_sha") == b.get("response_sha")})
            k, b, _ = http(base, "POST", "/account/call", {"tool": "fabius_signal_explain", "call_id": "uji-2"}, headers=auth)
            kon = (b.get("data") or {}).get("contribution") or []
            catat("fabius_signal_explain 0,02 FAB", k, 200, {"agent": len((b.get("data") or {}).get("agents") or []), "kontribusi": len(kon),
                                                            "jumlah_bagian": round(sum(x["share"] or 0 for x in kon), 6), "saldo": b.get("balance_atomic")})
            k, b, _ = http(base, "POST", "/account/call", {"tool": "fabius_data", "call_id": "uji-3", "args": {"assets": ["BTCUSDT", "PAXGUSDT"]}}, headers=auth)
            catat("fabius_data 0,005 FAB (disaring 2 aset)", k, 200, {"aset": sorted(((b.get("data") or {}).get("asset_features") or {})), "saldo": b.get("balance_atomic")})
            k, b, _ = http(base, "POST", "/account/charge", {"tool": "fabius_verify", "call_id": "uji-4", "check": True}, headers=auth)
            catat("alat tingkat 0 lama: cek saldo (tanpa potongan)", k, 200, {"cukup": b.get("enough"), "saldo": b.get("balance_atomic")})
            k, b, _ = http(base, "POST", "/account/charge", {"tool": "fabius_verify", "call_id": "uji-4", "response_sha": "0x" + "ab" * 32}, headers=auth)
            catat("alat tingkat 0 lama: potong 0,005 FAB (USULAN)", k, 200, {"saldo": b.get("balance_atomic")})
            for i in range(10):
                k, b, _ = http(base, "POST", "/account/call", {"tool": "fabius_signal_explain", "call_id": f"habis-{i}"}, headers=auth)
                if k != 200:
                    break
            catat("panggil sampai saldo kurang -> 402 + petunjuk deposit (SK-M11)", k, 402, {"panggilan_sukses_sebelumnya": i, "saldo": b.get("balance_atomic"),
                                                                                           "petunjuk": "deposit" in b, "ada_data": "data" in b})
            k, b, _ = http(base, "GET", "/account", headers=auth)
            catat("akun (gratis): saldo + riwayat", k, 200, {"saldo": b.get("balance_atomic"), "deposit": b.get("deposited_atomic"), "terpakai": b.get("spent_atomic"),
                                                            "rekaman": b.get("records_total")})
            k, b, _ = http(base, "POST", "/account/key/revoke", {}, headers=auth)
            catat("pemegang kunci mencabut kuncinya", k, 200, {"dicabut": b.get("revoked")})
            k, b, _ = http(base, "GET", "/account", headers=auth)
            catat("kunci yang dicabut -> 401", k, 401, {})
            srv.shutdown()
            srv.server_close()
            with open(g.akun.path, encoding="utf-8") as f:
                rows = [json.loads(x) for x in f if x.strip()]
            saldo, masalah = am.periksa_rantai(rows)
        cetak({"uji_kering": "akun MCP berbayar (P157) - gerbang lokal, chain palsu, tanpa tx", "langkah": langkah,
               "buku": {"rekaman": len(rows), "masalah": masalah, "saldo_hitung_ulang": saldo, "kepala": rows[-1]["h"] if rows else None},
               "semua_sesuai": ok and not masalah})
        if simpan:
            shutil.copytree(tmp, simpan, dirs_exist_ok=True)
        return 0 if ok and not masalah else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
