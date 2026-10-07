"""P157 (F5, F-D111): akun MCP berbayar meja - deposit FAB lewat x402 -> saldo per dompet, kunci API dari tanda tangan dompet, potong per panggilan.

Modul ini logika + keadaan (tanpa jaringan): settle x402 memakai `Gate.settle` yang sudah ada (Transfer pembeli -> payTo HARUS ada di receipt), data alat
dibaca dari berkas meja gerbang, jadi seluruh jalur diuji tanpa chain. Sumber kebenaran = buku besar append-only `akun.jsonl`:

  deposit  {dompet, atomic, tx, nonce}            kredit; kunci idempoten = (dompet, nonce Permit2): satu otorisasi tidak pernah dikreditkan dua kali
  kunci    {dompet, kunci_id, kunci_sha, pesan_sha} kunci API terbit; hanya sha256-nya yang disimpan (kunci ditampilkan SEKALI)
  cabut    {dompet, kunci_id, oleh}               kunci tidak berlaku lagi
  potong   {dompet, kunci_id, alat, atomic, call_id, respons_sha}   debit; kunci idempoten = (dompet, call_id)

Tiap rekaman membawa `n` (urutan global), `prev` = `h` rekaman sebelumnya DOMPET YANG SAMA, dan `h` = sha256 JSON kanonisnya. Saldo = jumlah deposit -
jumlah potongan, dihitung ulang dari buku saat mulai (tidak ada saldo yang disimpan terpisah). Buku yang rantainya putus / hash-nya tidak cocok = layanan
akun BERHENTI (503), tidak menebak saldo.

Sakelar `FABIUS_F5` (bawaan MATI): hanya "hidup" / "nyala" / "1" yang menyalakan. Mati = semua rute /account menjawab 404 dan tidak ada yang tercatat
(F-D111 #4: sampai dibuka builder, MCP hidup tetap seperti sekarang).

Rute (dipasang gerbang lewat `rute_get` / `rute_post`):
  GET  /account/pricing                harga, cara deposit + kunci, kepala buku (gratis, tanpa kunci)
  GET  /account                        saldo + kunci + riwayat dompet pemilik kunci (Authorization: Bearer fabk_...)
  GET  /account/deposit/<atomik>       402 + PAYMENT-REQUIRED; dengan PAYMENT-SIGNATURE -> settle -> saldo bertambah
  POST /account/key                    {wallet, ts, signature} pesan EIP-191 -> kunci API (sekali tampil)
  POST /account/key/revoke             {wallet, key_id, ts, signature} atau pemegang kunci itu sendiri (Authorization)
  POST /account/call                   {tool, args, call_id} alat yang datanya dari gerbang (fabius_signal / _explain / fabius_data): potong lalu kirim
  POST /account/charge                 {tool, call_id, response_sha, check} alat yang dijalankan server MCP (alat tingkat 0 lama): cek, lalu potong

Pakai:  python -X utf8 tools/akun_mcp.py periksa --folder <dir akun>      # verifikasi rantai buku + saldo per dompet (baca saja)
        python -X utf8 tools/akun_mcp.py uji-kering                       # ujung-ke-ujung lokal: gerbang HTTP lokal + chain palsu, tanpa tx
"""
from __future__ import annotations

import argparse
import base64
import collections
import hashlib
import json
import os
import re
import secrets
import sys
import threading
import time
from typing import Callable, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (ROOT, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Harga atomik FAB (6 desimal). F-D111 #2 - disetujui builder 5 Okt ("Gasss").
HARGA = {"fabius_signal": 10_000, "fabius_signal_explain": 20_000, "fabius_data": 5_000}
# USULAN (F-D111 #3 memindahkan alat tingkat 0 ke berbayar tanpa menyebut harganya): alat yang dijalankan server MCP lalu dipotong lewat /account/charge.
HARGA_MCP = {nama: 5_000 for nama in ("fabius_analysts", "fabius_desk", "fabius_analyst_join", "fabius_desk_join", "fabius_confidence", "fabius_list_bots",
                                       "fabius_track_record", "fabius_proof_feed", "fabius_locks", "fabius_signals", "fabius_latest_signals",
                                       "fabius_verify", "fabius_status")}
GRATIS = ("fabius_pricing", "fabius_account")
# F-D111 #3: alat data publik P140 dicabut dari MCP. USULAN: `fabius_overview` + `fabius_signal_offer` dilebur ke `fabius_pricing` (gratis hanya penemuan).
DICABUT = ("fabius_dexscreener", "fabius_rugcheck", "fabius_bubblemaps", "fabius_fomo", "fabius_overview", "fabius_signal_offer")
# Batas OPERASIONAL - semuanya USULAN (belum diputuskan builder); dicetak di /account/pricing.
PARAMS_AKUN = {"v": 1, "deposit_min": 50_000, "deposit_maks": 1_000_000, "kunci_maks": 3, "pesan_ttl_s": 600, "call_id_maks": 64, "riwayat_n": 50,
               "cache_respons": 256, "aset_maks": 20}
DESIMAL = 6
NOL = "0x" + "00" * 32
PRE_KUNCI, PRE_CABUT = "Fabius MCP API key v1", "Fabius MCP API key revoke v1"
# Satu sumber bentuk pesan: dipakai fungsi di bawah DAN dicetak di /account/pricing; web/src/lib/akun.ts menyalinnya (tes kontrak lintas bahasa).
FMT_KUNCI = PRE_KUNCI + "\nwallet: {dompet}\nts: {ts}\nchain: 97"
FMT_CABUT = PRE_CABUT + "\nwallet: {dompet}\nkey_id: {kunci_id}\nts: {ts}\nchain: 97"
ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
KUNCI_RE = re.compile(r"^fabk_[A-Za-z0-9_-]{43}$")
KUNCI_ID_RE = re.compile(r"^k_[0-9a-f]{12}$")
CALL_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")
SHA_RE = re.compile(r"^0x[0-9a-f]{64}$")
ASET_RE = re.compile(r"^[A-Z0-9]{2,20}$")
JENIS = ("deposit", "kunci", "cabut", "potong")


class TidakAda(Exception):
    """Data alat belum ada (mis. meja belum punya siklus v2): 404, tidak dipotong."""


class MasukanSalah(Exception):
    """Argumen alat tidak sah: 400, tidak dipotong."""


def sakelar(nilai: Optional[str] = None) -> bool:
    """`FABIUS_F5`: hanya "hidup" / "nyala" / "1" = MCP berbayar terbuka; kosong / "mati" / nilai lain = MATI (bawaan)."""
    v = (os.environ.get("FABIUS_F5", "") if nilai is None else nilai).strip().lower()
    return v in ("hidup", "nyala", "1")


def sha_teks(teks: str) -> str:
    return "0x" + hashlib.sha256(teks.encode("utf-8")).hexdigest()


def kanonis(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha_json(obj) -> str:
    return sha_teks(kanonis(obj))


def hash_rekaman(rec: dict) -> str:
    return sha_json({k: v for k, v in rec.items() if k != "h"})


def fab(atomic: int) -> str:
    return f"{atomic / 10 ** DESIMAL:g}"


def pesan_kunci(dompet: str, ts: int) -> str:
    return FMT_KUNCI.format(dompet=dompet.lower(), ts=int(ts))


def pesan_cabut(dompet: str, kunci_id: str, ts: int) -> str:
    return FMT_CABUT.format(dompet=dompet.lower(), kunci_id=kunci_id, ts=int(ts))


def kunci_dari(headers) -> Optional[str]:
    """Kunci API dari `Authorization: Bearer fabk_...` atau `X-Api-Key`. Token lain (mis. Privy) bukan kunci akun -> None."""
    get = (lambda k: headers.get(k)) if hasattr(headers, "get") else (lambda k: None)
    auth = (get("Authorization") or get("authorization") or "").strip()
    tok = auth[7:].strip() if auth[:7].lower() == "bearer " else (get("X-Api-Key") or get("x-api-key") or "").strip()
    return tok if KUNCI_RE.match(tok or "") else None


def harga_alat(alat: str) -> Optional[int]:
    return HARGA.get(alat, HARGA_MCP.get(alat))


def periksa_rantai(recs: List[dict]) -> Tuple[Dict[str, int], List[str]]:
    """Hitung ulang dari nol: (saldo per dompet, masalah). Dipakai saat mulai DAN oleh CLI `periksa` / pihak luar atas rekamannya sendiri."""
    saldo: Dict[str, int] = {}
    kepala: Dict[str, str] = {}
    masalah: List[str] = []
    for i, r in enumerate(recs):
        d = r.get("dompet")
        if r.get("n") != i:
            masalah.append(f"rekaman {i}: n {r.get('n')} != {i}")
        if r.get("jenis") not in JENIS or not isinstance(d, str):
            masalah.append(f"rekaman {i}: jenis / dompet tidak sah")
            continue
        if r.get("h") != hash_rekaman(r):
            masalah.append(f"rekaman {i}: h tidak cocok dengan isinya")
        if r.get("prev") != kepala.get(d, NOL):
            masalah.append(f"rekaman {i}: prev bukan rekaman terakhir dompet {d}")
        kepala[d] = r.get("h")
        if r["jenis"] == "deposit":
            saldo[d] = saldo.get(d, 0) + int(r["atomic"])
        elif r["jenis"] == "potong":
            saldo[d] = saldo.get(d, 0) - int(r["atomic"])
            if saldo[d] < 0:
                masalah.append(f"rekaman {i}: saldo {d} negatif")
    return saldo, masalah


class Akun:
    """Buku besar akun MCP (tersimpan, append-only) + indeks di memori. `pulihkan(pesan, tanda_tangan) -> alamat` disuntik (bawaan EIP-191 lewat
    eth-account, sama dengan agent luar P166). Semua perubahan lewat `_tulis` di bawah `lock`, jadi cek saldo + potong atomik terhadap utas lain."""

    def __init__(self, folder: str, now: Callable[[], float] = time.time, pulihkan: Optional[Callable[[str, str], str]] = None,
                 params: Optional[dict] = None):
        self.folder, self.now = folder, now
        self.path = os.path.join(folder, "akun.jsonl")
        self.P = {**PARAMS_AKUN, **(params or {})}
        if pulihkan is None:
            import agen_luar as al
            pulihkan = al.pulihkan
        self.pulihkan = pulihkan
        self.lock = threading.Lock()
        self.lock_deposit = threading.Lock()
        self.recs: List[dict] = []
        self.saldo: Dict[str, int] = {}
        self.kepala: Dict[str, str] = {}
        self.kunci: Dict[str, dict] = {}                           # kunci_sha -> {dompet, kunci_id, aktif, t}
        self.deposit_ix: Dict[Tuple[str, str], dict] = {}
        self.potong_ix: Dict[Tuple[str, str], dict] = {}
        self.pesan_ix: set = set()
        self.respons: "collections.OrderedDict[Tuple[str, str], dict]" = collections.OrderedDict()
        self.rusak: List[str] = []
        rows: List[dict] = []
        try:
            with open(self.path, encoding="utf-8") as f:
                for ln in f:
                    if ln.strip():
                        rows.append(json.loads(ln))
        except FileNotFoundError:
            pass
        except (OSError, ValueError) as e:
            self.rusak = [f"buku tak terbaca: {type(e).__name__}"]
            return
        saldo, self.rusak = periksa_rantai(rows)
        if self.rusak:
            return
        for r in rows:
            self._indeks(r)
        self.saldo = saldo

    # ------------------------------------------------------------ buku
    def _indeks(self, r: dict) -> None:
        d = r["dompet"]
        self.recs.append(r)
        self.kepala[d] = r["h"]
        if r["jenis"] == "deposit":
            self.deposit_ix[(d, r["nonce"])] = r
        elif r["jenis"] == "kunci":
            self.kunci[r["kunci_sha"]] = {"dompet": d, "kunci_id": r["kunci_id"], "aktif": True, "t": r["t"]}
            self.pesan_ix.add(r["pesan_sha"])
        elif r["jenis"] == "cabut":
            for v in self.kunci.values():
                if v["kunci_id"] == r["kunci_id"] and v["dompet"] == d:
                    v["aktif"] = False
            if r.get("pesan_sha"):
                self.pesan_ix.add(r["pesan_sha"])
        elif r["jenis"] == "potong":
            self.potong_ix[(d, r["call_id"])] = r

    def _tulis(self, isi: dict) -> dict:
        """Tambah satu rekaman (pemanggil memegang `lock`). Disk dulu, baru indeks: gagal tulis = tidak ada perubahan saldo di memori."""
        d = isi["dompet"]
        r = {"v": 1, "n": len(self.recs), "t": int(self.now()), **isi, "prev": self.kepala.get(d, NOL)}
        r["h"] = hash_rekaman(r)
        os.makedirs(self.folder, exist_ok=True)
        with open(self.path, "a", encoding="utf-8", newline="\n") as f:
            f.write(kanonis(r) + "\n")
        self._indeks(r)
        if r["jenis"] == "deposit":
            self.saldo[d] = self.saldo.get(d, 0) + int(r["atomic"])
        elif r["jenis"] == "potong":
            self.saldo[d] = self.saldo.get(d, 0) - int(r["atomic"])
        return r

    def kepala_buku(self) -> str:
        return self.recs[-1]["h"] if self.recs else NOL

    def pemilik(self, kunci: Optional[str]) -> Optional[dict]:
        if not kunci or not KUNCI_RE.match(kunci):
            return None
        v = self.kunci.get(hashlib.sha256(kunci.encode()).hexdigest())
        return v if v and v["aktif"] else None

    def _gagal_rusak(self) -> Optional[Tuple[int, dict]]:
        if self.rusak:
            return 503, {"error": "account ledger failed its integrity check; paid MCP is stopped until an operator repairs it", "problems": self.rusak[:5]}
        return None

    # ------------------------------------------------------------ kunci API
    def _cek_pesan(self, dompet: object, ts: object, tanda_tangan: object, pesan: str) -> Optional[Tuple[int, dict]]:
        if not isinstance(dompet, str) or not ADDR_RE.match(dompet):
            return 400, {"error": "wallet must be a 0x address"}
        if isinstance(ts, bool) or not isinstance(ts, int):
            return 400, {"error": "ts must be an integer (unix seconds)"}
        if abs(int(self.now()) - ts) > self.P["pesan_ttl_s"]:
            return 401, {"error": f"message expired or from the future (ts must be within {self.P['pesan_ttl_s']} s of now)"}
        if not isinstance(tanda_tangan, str) or not re.match(r"^0x[0-9a-fA-F]{130}$", tanda_tangan):
            return 400, {"error": "signature must be 65 bytes hex (EIP-191 personal_sign)"}
        if sha_teks(pesan) in self.pesan_ix:
            return 409, {"error": "this signed message was already used; sign a new one with a fresh ts"}
        try:
            siapa = self.pulihkan(pesan, tanda_tangan)
        except Exception:  # noqa: BLE001 - tanda tangan rusak = ditolak, tanpa teks galat pustaka
            return 401, {"error": "signature could not be verified"}
        if str(siapa).lower() != dompet.lower():
            return 401, {"error": "signature is not from this wallet"}
        return None

    def buat_kunci(self, body: dict) -> Tuple[int, dict]:
        if (g := self._gagal_rusak()):
            return g
        dompet, ts, sig = body.get("wallet"), body.get("ts"), body.get("signature")
        pesan = pesan_kunci(str(dompet), ts) if isinstance(ts, int) and not isinstance(ts, bool) else ""
        if (g := self._cek_pesan(dompet, ts, sig, pesan)):
            return g
        d = dompet.lower()
        with self.lock:
            if sha_teks(pesan) in self.pesan_ix:
                return 409, {"error": "this signed message was already used; sign a new one with a fresh ts"}
            aktif = [v for v in self.kunci.values() if v["dompet"] == d and v["aktif"]]
            if len(aktif) >= self.P["kunci_maks"]:
                return 409, {"error": f"this wallet already has {len(aktif)} active keys (max {self.P['kunci_maks']}); revoke one first",
                             "keys": [v["kunci_id"] for v in aktif]}
            kunci = "fabk_" + secrets.token_urlsafe(32)
            ks = hashlib.sha256(kunci.encode()).hexdigest()
            rec = self._tulis({"jenis": "kunci", "dompet": d, "kunci_id": "k_" + ks[:12], "kunci_sha": ks, "pesan_sha": sha_teks(pesan)})
        return 201, {"key": kunci, "key_id": rec["kunci_id"], "wallet": d, "record": rec,
                     "note": "Shown ONCE. Fabius stores only its sha256; a lost key cannot be recovered - revoke it and make a new one.",
                     "use": "send it as 'Authorization: Bearer <key>' to the MCP server (/mcp) and to /account"}

    def cabut_kunci(self, body: dict, kunci: Optional[str]) -> Tuple[int, dict]:
        if (g := self._gagal_rusak()):
            return g
        if body.get("signature") is None and kunci:                                        # pemegang kunci mencabut kuncinya sendiri
            info = self.pemilik(kunci)
            if not info:
                return 401, {"error": "invalid or already revoked API key"}
            with self.lock:
                rec = self._tulis({"jenis": "cabut", "dompet": info["dompet"], "kunci_id": info["kunci_id"], "oleh": "kunci"})
            return 200, {"revoked": info["kunci_id"], "record": rec}
        dompet, kid, ts, sig = body.get("wallet"), body.get("key_id"), body.get("ts"), body.get("signature")
        if not isinstance(kid, str) or not KUNCI_ID_RE.match(kid):
            return 400, {"error": "key_id must look like k_<12 hex>"}
        pesan = pesan_cabut(str(dompet), kid, ts) if isinstance(ts, int) and not isinstance(ts, bool) else ""
        if (g := self._cek_pesan(dompet, ts, sig, pesan)):
            return g
        d = dompet.lower()
        with self.lock:
            hit = [v for v in self.kunci.values() if v["dompet"] == d and v["kunci_id"] == kid and v["aktif"]]
            if not hit:
                return 404, {"error": "no active key with this id for this wallet"}
            rec = self._tulis({"jenis": "cabut", "dompet": d, "kunci_id": kid, "oleh": "dompet", "pesan_sha": sha_teks(pesan)})
        return 200, {"revoked": kid, "record": rec}

    # ------------------------------------------------------------ potong
    def _cek_panggilan(self, kunci: Optional[str], alat: object, call_id: object, daftar: Dict[str, int]) -> Tuple[Optional[Tuple[int, dict]], Optional[dict], int, str]:
        if (g := self._gagal_rusak()):
            return g, None, 0, ""
        info = self.pemilik(kunci)
        if not info:                                                                       # SK-M12: tidak ada data, saldo tidak disentuh
            return (401, {"error": "invalid or revoked API key", "how": "sign the key message with your wallet: POST /account/key (see /account/pricing)"}), None, 0, ""
        if not isinstance(alat, str) or alat not in daftar:
            return (400, {"error": f"unknown or free tool {alat!r} for this endpoint", "paid_tools": sorted(daftar)}), None, 0, ""
        cid = call_id if call_id is not None else "c_" + secrets.token_hex(12)
        if not isinstance(cid, str) or not CALL_ID_RE.match(cid) or len(cid) > self.P["call_id_maks"]:
            return (400, {"error": "call_id must be 1-64 chars of [A-Za-z0-9._:-]"}), None, 0, ""
        return None, info, daftar[alat], cid

    def _tolak_saldo(self, dompet: str, harga: int) -> Tuple[int, dict]:
        """SK-M11: saldo kurang -> ditolak + petunjuk deposit; tidak ada data, saldo tidak berubah, tidak ada rekaman."""
        return 402, {"error": "insufficient balance", "price_atomic": harga, "price_fab": fab(harga), "balance_atomic": self.saldo.get(dompet, 0),
                     "balance_fab": fab(self.saldo.get(dompet, 0)), "deposit": "GET /account/deposit/<atomic> with x402 (see /account/pricing); "
                     "free test FAB: POST /faucet {\"address\": \"0x..\"}"}

    def potong(self, kunci: Optional[str], alat: object, call_id: object, respons_sha: object = None, cek: bool = False) -> Tuple[int, dict]:
        """`/account/charge` (alat yang dijalankan server MCP): `cek` = hanya kunci + saldo (tanpa perubahan); tanpa `cek` = potong idempoten per
        (dompet, call_id). Server MCP hanya mengirim hasil alat bila jawaban ini 200."""
        g, info, harga, cid = self._cek_panggilan(kunci, alat, call_id, HARGA_MCP)
        if g:
            return g
        d = info["dompet"]
        if respons_sha is not None and (not isinstance(respons_sha, str) or not SHA_RE.match(respons_sha)):
            return 400, {"error": "response_sha must be 0x + 64 lowercase hex"}
        with self.lock:
            ada = self.potong_ix.get((d, cid))
            if ada:
                return 200, {"charge": ada, "repeat": True, "balance_atomic": self.saldo.get(d, 0), "note": "this call_id was already charged once"}
            if self.saldo.get(d, 0) < harga:
                return self._tolak_saldo(d, harga)
            if cek:
                return 200, {"enough": True, "price_atomic": harga, "balance_atomic": self.saldo.get(d, 0), "call_id": cid}
            rec = self._tulis({"jenis": "potong", "dompet": d, "kunci_id": info["kunci_id"], "alat": alat, "atomic": harga, "call_id": cid,
                               "respons_sha": respons_sha})
        return 200, {"charge": rec, "balance_atomic": self.saldo.get(d, 0), "balance_fab": fab(self.saldo.get(d, 0))}

    def panggil(self, kunci: Optional[str], alat: object, args: object, call_id: object, bangun: Callable[[str, dict], dict]) -> Tuple[int, dict]:
        """`/account/call` (alat yang datanya dari gerbang): kunci sah -> saldo cukup -> data dibangun -> potong (sha respons ikut rekaman) -> data.
        Data gagal dibangun = 503 tanpa potongan. call_id yang sama: jawaban tersimpan dikirim ulang tanpa potongan kedua."""
        g, info, harga, cid = self._cek_panggilan(kunci, alat, call_id, HARGA)
        if g:
            return g
        d = info["dompet"]
        if args is not None and not isinstance(args, dict):
            return 400, {"error": "args must be an object"}
        with self.lock:
            ada = self.potong_ix.get((d, cid))
            if ada:
                simpan = self.respons.get((d, cid))
                if simpan:
                    return 200, {**simpan, "repeat": True}
                return 409, {"error": "this call_id was already charged; the data is not sent again", "charge": ada}
            if self.saldo.get(d, 0) < harga:
                return self._tolak_saldo(d, harga)
        try:
            data = bangun(alat, args or {})
        except (TidakAda, MasukanSalah) as e:
            return 404 if isinstance(e, TidakAda) else 400, {"error": f"{alat}: {e}", "charged": False}
        except Exception as e:  # noqa: BLE001 - data gagal dibaca = tidak dipotong
            return 503, {"error": f"{alat}: data could not be read ({type(e).__name__}); nothing was charged", "charged": False}
        rsha = sha_json(data)
        with self.lock:
            ada = self.potong_ix.get((d, cid))                                                  # utas lain dengan call_id sama menang lebih dulu
            if ada:
                simpan = self.respons.get((d, cid))
                return (200, {**simpan, "repeat": True}) if simpan else (409, {"error": "this call_id was already charged", "charge": ada})
            if self.saldo.get(d, 0) < harga:                                                    # saldo habis oleh panggilan paralel
                return self._tolak_saldo(d, harga)
            rec = self._tulis({"jenis": "potong", "dompet": d, "kunci_id": info["kunci_id"], "alat": alat, "atomic": harga, "call_id": cid,
                               "respons_sha": rsha})
            out = {"tool": alat, "data": data, "response_sha": rsha, "charge": rec, "balance_atomic": self.saldo.get(d, 0),
                   "balance_fab": fab(self.saldo.get(d, 0))}
            self.respons[(d, cid)] = out
            while len(self.respons) > self.P["cache_respons"]:
                self.respons.popitem(last=False)
        return 200, out

    # ------------------------------------------------------------ deposit (x402)
    def kredit(self, dompet: str, atomic: int, nonce: str, settle: Callable[[], dict]) -> Tuple[int, dict]:
        """Satu otorisasi Permit2 (dompet, nonce) dikreditkan paling banyak sekali: sudah ada -> rekaman lama (tanpa settle kedua). `settle()` baru
        dipanggil bila belum ada; kredit hanya sesudah settle sukses (Transfer di receipt, `Gate.settle`)."""
        if (g := self._gagal_rusak()):
            return g
        d = dompet.lower()
        with self.lock_deposit:
            ada = self.deposit_ix.get((d, nonce))
            if ada:
                return 200, {"deposit": ada, "repeat": True, "balance_atomic": self.saldo.get(d, 0), "note": "this authorization was already credited"}
            res = settle()
            if not res.get("ok"):
                return 402, {"error": "settlement failed; nothing was credited", "detail": res}
            if str(res.get("payer", d)).lower() != d:
                return 402, {"error": "settled payer differs from the signed authorization; nothing was credited", "detail": res}
            with self.lock:
                try:
                    rec = self._tulis({"jenis": "deposit", "dompet": d, "atomic": int(atomic), "tx": res["tx"], "nonce": nonce})
                except OSError as e:
                    return 500, {"error": f"PAID BUT NOT CREDITED (ledger write failed: {type(e).__name__}); keep this tx for the operator",
                                 "tx": res["tx"], "payer": d, "atomic": atomic}
        return 200, {"deposit": rec, "balance_atomic": self.saldo.get(d, 0), "balance_fab": fab(self.saldo.get(d, 0))}

    # ------------------------------------------------------------ baca
    def akun(self, kunci: Optional[str]) -> Tuple[int, dict]:
        if (g := self._gagal_rusak()):
            return g
        info = self.pemilik(kunci)
        if not info:
            return 401, {"error": "invalid or revoked API key", "how": "POST /account/key with a wallet-signed message (see /account/pricing)"}
        d = info["dompet"]
        mine = [r for r in self.recs if r["dompet"] == d]
        return 200, {"wallet": d, "balance_atomic": self.saldo.get(d, 0), "balance_fab": fab(self.saldo.get(d, 0)), "key_id": info["kunci_id"],
                     "keys": [{"key_id": v["kunci_id"], "active": v["aktif"], "issued_t": v["t"]} for v in self.kunci.values() if v["dompet"] == d],
                     "deposited_atomic": sum(int(r["atomic"]) for r in mine if r["jenis"] == "deposit"),
                     "spent_atomic": sum(int(r["atomic"]) for r in mine if r["jenis"] == "potong"), "records": mine[-self.P["riwayat_n"]:],
                     "records_total": len(mine), "head": self.kepala.get(d, NOL),
                     "verify": "each record: h = sha256(canonical JSON without h); prev = h of your previous record; deposits carry the BSC testnet tx"}


# ---------------------------------------------------------------- data alat (dibaca dari berkas meja gerbang; tanpa model, tanpa chain)

def _iso(t: Optional[int]) -> Optional[str]:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t)) if t else None


def _siklus_terakhir(gate) -> Tuple[dict, List[dict], Optional[dict]]:
    """(rekaman buku Fabius "v2" terakhir, rekaman agent v2 siklus yang sama, baris siklus itu)."""
    rek = gate._meja_baca("rekaman", 2)
    fab_ = [r for r in rek if r.get("agent") == "v2"]
    if not fab_:
        raise TidakAda("the desk has no v2 cycle yet")
    akhir = fab_[-1]
    agen = [r for r in rek if str(r.get("agent", "")).startswith("v2:") and r.get("siklus") == akhir["siklus"]]
    sik = next((x for x in reversed(gate._meja_baca("siklus", 2)) if x.get("siklus") == akhir["siklus"]), None)
    return akhir, agen, sik


def _bukti(gate, sik: Optional[dict]) -> dict:
    return {"root": (sik or {}).get("root"), "tx": (sik or {}).get("tx"), "status": (sik or {}).get("status"), "leaves": (sik or {}).get("n"),
            "anchor": gate.data.cfg_raw().get("contracts", {}).get("DeskAnchor"), "chain_id": 97,
            "check": "every record hash is a leaf of this cycle's Merkle root, committed to DeskAnchor before the cycle ended; GET /desk/proof/<hash>"}


def kontribusi(agen: List[dict], bot: Optional[str]) -> List[dict]:
    """Kontribusi tiap agent kursi AKTIF dengan jawaban sah ke nilai bot `bot`, rumus konsensus r4 (`meja2.konsensus2`): nilai_b = sum(k_i x s_i,b) / n.
    poin_i = k_i x s_i,b / n; bagian_i = poin_i / nilai_b (None bila nilai_b = 0)."""
    sah = [r for r in agen if r.get("kursi") == "aktif" and r.get("status", "ok") == "ok" and isinstance(r.get("keputusan"), dict)]
    if not bot or not sah:
        return []
    baris = []
    for r in sah:
        kep = r["keputusan"]
        k, s = float(kep.get("k") or 0.0), float((kep.get("skor_bot") or {}).get(bot) or 0)
        baris.append({"agent": r["agent"].split(":", 1)[-1], "confidence": k, "score_for_bot": s, "points": k * s / len(sah), "picked_bot": kep.get("bot")})
    total = sum(b["points"] for b in baris)
    for b in baris:
        b["share"] = round(b["points"] / total, 4) if total else None
        b["points"] = round(b["points"], 4)
    return sorted(baris, key=lambda b: (-b["points"], b["agent"]))


def _fitur_siklus(gate, data_sha: Optional[str]) -> Tuple[Optional[dict], bool]:
    rows = gate._meja_baca("fitur", 2)
    hit = next((r for r in reversed(rows) if data_sha and r.get("sha") == data_sha), None)
    return (hit, True) if hit else ((rows[-1] if rows else None), False)


def bangun_data(gate, alat: str, args: dict) -> dict:
    """Isi alat berbayar dari gerbang. Hanya data yang SUDAH dikomit siklus meja (rekaman ber-hash + root) atau snapshot F1 yang tercatat."""
    if alat == "fabius_signal":
        akhir, agen, sik = _siklus_terakhir(gate)
        import meja2
        return {"cycle": akhir["siklus"], "cycle_utc": _iso(akhir["siklus"]), "formula": f"r{meja2.PARAMS2['v']}", "dominant_bot": akhir.get("bot"),
                "bot_values": akhir.get("nilai_bot"), "basis": akhir.get("dasar"), "instruments": akhir.get("instrumen") or [],
                "instrument_scores": akhir.get("skor_instrumen"), "exposure": akhir.get("eksposur"), "veto": akhir.get("veto") or [],
                "rule_target": akhir.get("target") or {}, "open_slots": akhir.get("slot"), "fills_this_cycle": akhir.get("isi") or [],
                "equity": akhir.get("ekuitas"), "seats": {r["agent"].split(":", 1)[-1]: {"seat": r.get("kursi"), "status": r.get("status", "ok")} for r in agen},
                "record_hash": akhir.get("hash"), "proof": _bukti(gate, sik),
                "honesty": "PAPER desk on Binance USDT-M futures prices with real fees; no real money; a new strategy, not the bots' forward record"}
    if alat == "fabius_signal_explain":
        akhir, agen, sik = _siklus_terakhir(gate)
        data_sha = next((r.get("data_sha") for r in agen if r.get("data_sha")), akhir.get("data_sha"))
        snap, cocok = _fitur_siklus(gate, data_sha)
        ins = list(akhir.get("instrumen") or [])
        fa = (snap or {}).get("fitur_aset") or {}
        return {"cycle": akhir["siklus"], "cycle_utc": _iso(akhir["siklus"]), "dominant_bot": akhir.get("bot"), "bot_values": akhir.get("nilai_bot"),
                "basis": akhir.get("dasar"), "contribution": kontribusi(agen, akhir.get("bot")),
                "agents": [{"agent": r["agent"].split(":", 1)[-1], "agent_id": r.get("agent_id"), "model": r.get("model"), "seat": r.get("kursi"),
                            "status": r.get("status", "ok"), "error": r.get("galat"),
                            "answer": {k: (r.get("keputusan") or {}).get(k) for k in ("bot", "skor_bot", "k", "eksposur", "instrumen", "veto", "faktor", "ringkasan")}
                            if r.get("status", "ok") == "ok" else None, "record_hash": r.get("hash"), "prompt_sha": r.get("prompt_sha")}
                           for r in sorted(agen, key=lambda r: r["agent"])],
                "features": {"snapshot_sha": (snap or {}).get("sha"), "snapshot_matches_cycle": cocok, "snapshot_t": (snap or {}).get("t"),
                             "instruments": {a: fa.get(a) for a in ins}},
                "counted": "only ACTIVE seats with a valid answer count (trial seats are recorded, not counted); bot value = sum(confidence x score) / n",
                "proof": _bukti(gate, sik)}
    if alat == "fabius_data":
        v = gate.data_view()
        snap = v.get("terakhir")
        if not snap:
            raise TidakAda("no F1 data snapshot yet")
        aset = args.get("assets")
        if aset is not None:
            if not isinstance(aset, list) or len(aset) > PARAMS_AKUN["aset_maks"] or not all(isinstance(a, str) and ASET_RE.match(a) for a in aset):
                raise MasukanSalah(f"assets must be a list of up to {PARAMS_AKUN['aset_maks']} symbols like BTCUSDT")
        fa = snap.get("fitur_aset") or {}
        return {"snapshot_t": snap.get("t"), "snapshot_utc": _iso(snap.get("t")), "snapshot_sha": snap.get("sha"), "registry_sha": snap.get("registry_sha"),
                "health": snap.get("kesehatan"), "sources": snap.get("sumber"),
                "asset_features": {a: fa[a] for a in (aset if aset is not None else sorted(fa)) if a in fa},
                "bot_features": snap.get("fitur_bot"), "health_24h": v.get("sumber"),
                "note": "snapshot_sha covers the FULL snapshot; a filtered answer is a subset of it"}
    raise TidakAda(f"unknown tool {alat}")


# ---------------------------------------------------------------- rute HTTP (dipanggil handler gerbang; mengembalikan (kode, isi, header) atau None)

def info_harga(gate, akun: Akun) -> dict:
    cfg = gate.data.cfg()
    return {"open": True, "token": {"symbol": "FAB", "address": cfg.get("token"), "decimals": DESIMAL, "network": "eip155:97", "name": "Fabius Credit"},
            "payTo": cfg.get("facilitator"),
            "tools": {"free": list(GRATIS), "paid": {a: {"atomic": h, "fab": fab(h), "status": "approved F-D111"} for a, h in HARGA.items()},
                      "paid_run_by_mcp": {a: {"atomic": h, "fab": fab(h), "status": "USULAN"} for a, h in sorted(HARGA_MCP.items())},
                      "removed": list(DICABUT)},
            "deposit": {"how": f"GET {gate.public_url}/account/deposit/<atomic> -> 402 PAYMENT-REQUIRED (x402 v2 exact, Permit2 + EIP-2612, payer pays "
                               "no gas) -> sign -> repeat with PAYMENT-SIGNATURE -> balance credited after the on-chain Transfer is proven",
                        "min_atomic": akun.P["deposit_min"], "max_atomic": akun.P["deposit_maks"], "limits_status": "USULAN",
                        "test_tokens": f"POST {gate.public_url}/faucet {{\"address\": \"0x..\"}}"},
            "key": {"how": f"POST {gate.public_url}/account/key {{wallet, ts, signature}} with an EIP-191 personal_sign of the message below",
                    "message": FMT_KUNCI, "revoke_message": FMT_CABUT, "ttl_s": akun.P["pesan_ttl_s"], "max_active_per_wallet": akun.P["kunci_maks"],
                    "use": "Authorization: Bearer <key> on /mcp and /account"},
            "ledger": {"head": akun.kepala_buku(), "records": len(akun.recs), "integrity": "ok" if not akun.rusak else "BROKEN"},
            "signal_packages": f"{gate.public_url}/ (per-bot x402 signal packages, unchanged)",
            "honesty": ["PAPER ONLY: no real money is traded; FAB is a testnet credit with no value.",
                        "The desk is a new strategy (AI picks bot + instruments, locked rules compute direction), not the six bots' forward record.",
                        "The public proof pages (/verify) stay free."],
            "params": akun.P}


def rute_get(gate, akun: Akun, parts: List[str], headers, hdr_bayar: Optional[str], xs=None) -> Optional[Tuple[int, dict, dict]]:
    """`xs` = modul gerbang yang sedang berjalan (`x402_sinyal`, di produksi `__main__`) untuk pemeriksa pembayaran yang SAMA dengan /signal."""
    if not parts or parts[0] != "account":
        return None
    if not sakelar():
        return 404, {"error": "paid MCP is not open (FABIUS_F5 off)"}, {}
    if parts == ["account", "pricing"]:
        return 200, info_harga(gate, akun), {}
    if parts == ["account"]:
        return (*akun.akun(kunci_dari(headers)), {})
    if len(parts) == 3 and parts[1] == "deposit":
        return deposit(gate, akun, parts[2], hdr_bayar, xs)
    return 404, {"error": "unknown account route"}, {}


def rute_post(gate, akun: Akun, path: str, headers, body: dict) -> Optional[Tuple[int, dict]]:
    if not path.startswith("/account"):
        return None
    if not sakelar():
        return 404, {"error": "paid MCP is not open (FABIUS_F5 off)"}
    if not isinstance(body, dict):
        return 400, {"error": "body must be a JSON object"}
    kunci = kunci_dari(headers)
    if path == "/account/key":
        return akun.buat_kunci(body)
    if path == "/account/key/revoke":
        return akun.cabut_kunci(body, kunci)
    if path == "/account/call":
        return akun.panggil(kunci, body.get("tool"), body.get("args"), body.get("call_id"), lambda a, x: bangun_data(gate, a, x))
    if path == "/account/charge":
        return akun.potong(kunci, body.get("tool"), body.get("call_id"), body.get("response_sha"), bool(body.get("check")))
    return 404, {"error": "unknown account route"}


def deposit(gate, akun: Akun, jumlah: str, hdr: Optional[str], xs=None) -> Tuple[int, dict, dict]:
    if xs is None:
        import x402_sinyal as xs
    cfg = gate.data.cfg()
    if not (cfg.get("token") and cfg.get("facilitator")):
        return 503, {"error": "gate is not configured (deployments/97.json x402_sinyal)"}, {}
    if not jumlah.isdigit() or not (akun.P["deposit_min"] <= int(jumlah) <= akun.P["deposit_maks"]):
        return 400, {"error": f"deposit must be an integer number of atomic FAB between {akun.P['deposit_min']} and {akun.P['deposit_maks']}"}, {}
    atomic = int(jumlah)
    resource = f"{gate.public_url}/account/deposit/{atomic}"
    desc = f"Fabius MCP deposit {fab(atomic)} FAB -> balance for paid MCP calls (testnet 97, no value)"
    if not hdr:
        req = {"x402Version": 2, "error": "PAYMENT-SIGNATURE header is required", "resource": {"url": resource, "description": desc, "mimeType": "application/json"},
               "accepts": xs.accepts_for(resource, cfg["token"], cfg["facilitator"], atomic, desc)}
        b64 = base64.b64encode(json.dumps(req, sort_keys=True).encode()).decode()
        return 402, {"deposit_atomic": atomic, "deposit_fab": fab(atomic), "pay": "x402 v2 exact, permit2 + eip2612GasSponsoring (payer pays no gas)"}, \
            {"PAYMENT-REQUIRED": b64, "X-PAYMENT-REQUIRED": b64}
    pay = xs.decode_payment(hdr)
    if not pay:
        return 400, {"error": "PAYMENT-SIGNATURE could not be decoded"}, {}
    why = xs.check_payment(pay, cfg["token"], cfg["facilitator"], atomic, int(gate.now()))
    if why:
        return 402, {"error": f"payment rejected: {why}", "expected": {"amount": str(atomic), "asset": cfg["token"], "payTo": cfg["facilitator"]}}, {}
    a = pay["payload"]["permit2Authorization"]
    code, body = akun.kredit(a["from"], atomic, str(a["nonce"]), lambda: gate.settle(pay, cfg, atomic))
    if code == 200 and not body.get("repeat"):
        gate.log(f"DEPOSIT MCP {fab(atomic)} FAB dompet {body['deposit']['dompet']} tx {body['deposit']['tx']}")
    extra = {}
    if code == 200:
        resp = {"success": True, "transaction": body["deposit"]["tx"], "network": xs.NETWORK, "payer": body["deposit"]["dompet"]}
        b64 = base64.b64encode(json.dumps(resp, sort_keys=True).encode()).decode()
        extra = {"PAYMENT-RESPONSE": b64, "X-PAYMENT-RESPONSE": b64}
    return code, body, extra


# ---------------------------------------------------------------- CLI

def _cetak(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True))


def cmd_periksa(folder: str) -> int:
    path = os.path.join(folder, "akun.jsonl")
    rows = []
    with open(path, encoding="utf-8") as f:
        for ln in f:
            if ln.strip():
                rows.append(json.loads(ln))
    saldo, masalah = periksa_rantai(rows)
    print(f"buku {path}: {len(rows)} rekaman | kepala {rows[-1]['h'] if rows else NOL} | masalah {len(masalah)}")
    for m in masalah[:20]:
        print("  !", m)
    for d, s in sorted(saldo.items()):
        print(f"  {d}: saldo {s} atomik ({fab(s)} FAB)")
    return 1 if masalah else 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("periksa", help="verifikasi rantai buku akun + saldo per dompet (baca saja)")
    p.add_argument("--folder", required=True)
    sub.add_parser("uji-kering", help="ujung-ke-ujung lokal: gerbang HTTP lokal, chain palsu, tanda tangan sungguhan dompet buangan; tanpa tx")
    a = ap.parse_args(argv)
    if a.cmd == "periksa":
        return cmd_periksa(a.folder)
    import akun_uji_kering
    return akun_uji_kering.jalankan(_cetak)


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
    raise SystemExit(main())
