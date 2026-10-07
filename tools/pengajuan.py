"""P161 B1a: antrean pengajuan bot di gerbang (`POST /bots/submit`, `GET /bots/submissions`). Gerbang hanya MENERIMA: skema tertutup + identitas
EIP-712 diperiksa saat kiriman masuk (tanda tangan berlaku <= 1 jam), lalu kiriman masuk antrean publik. Peninjauan (gerbang G1-G11 + KPI + registri
P83) dijalankan rantai GitHub harian di repo publik dengan `--now = t_terima`, jadi siapa pun bisa mengulang verifikasi tanda tangan dan vonisnya.

Penyimpanan (volume gerbang):
  masuk.jsonl   antrean publik: formulir TANPA `identity.contact` (kontak tidak ikut hash, jadi sha tetap bisa dicek) + tanda tangan + nonce + deadline
  kontak.jsonl  kontak penerbit (privat; tidak pernah dikirim lewat API)
Batas: <= 2 kiriman belum ditinjau per penerbit, <= 50 kiriman per hari UTC (semua penerbit); nonce per penerbit tidak boleh dipakai ulang.

P167b (`kind=code`, TERTUTUP sampai builder menyetujui jalur privat): teks kode dikirim di `body.code` (DI LUAR formulir yang di-hash); harus cocok
dengan `spec.kode` {sha, ukuran, params} yang ditandatangani dan lolos analisis statis. Disimpan PRIVAT di `kode/<sha>.py` (volume gerbang), tidak
pernah lewat API publik / repo; antrean publik hanya memuat sha + ukuran + params.
"""
from __future__ import annotations

import copy
import json
import os
import threading
import time
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from engine import kode as kodemod, rule as rulemod, submission
from engine.spec import SPECS

import feed_gerbang                                                    # noqa: E402  P167c

CHAIN_ID = 97
MAX_BODY = 64 * 1024
MAKS_TERTUNDA_PER_PENERBIT = 2
MAKS_PER_HARI = 50


class Antrean:
    def __init__(self, folder: str, now: Callable[[], float] = time.time, kinds: Iterable[str] = submission.ENABLED_KINDS):
        self.folder, self.now, self.kinds = folder, now, tuple(kinds)
        self.lock = threading.Lock()
        self.masuk = os.path.join(folder, "masuk.jsonl")
        self.kontak = os.path.join(folder, "kontak.jsonl")
        self.kode_dir = os.path.join(folder, "kode")                     # P167b: kode PRIVAT (tidak pernah dilayani API publik)

    def semua(self) -> List[dict]:
        if not os.path.exists(self.masuk):
            return []
        with open(self.masuk, encoding="utf-8") as f:
            return [json.loads(ln) for ln in f if ln.strip()]

    def terima(self, body: dict, registri: Iterable[dict] = ()) -> Tuple[int, dict]:
        """-> (kode HTTP, isi). 201 = masuk antrean; 400 formulir/permintaan salah; 401 identitas; 409 ganda / nonce bekas; 429 batas."""
        if not isinstance(body, dict) or not isinstance(body.get("submission"), dict):
            return 400, {"error": "body must be {submission, signature, nonce, deadline[, payout_signature]}"}
        sub, sig = body["submission"], body.get("signature")
        try:
            nonce, deadline = int(body.get("nonce")), int(body.get("deadline"))
        except (TypeError, ValueError):
            return 400, {"error": "nonce and deadline must be integers"}
        if not isinstance(sig, str) or not sig.startswith("0x"):
            return 400, {"error": "signature (0x...) required: the issuer wallet signs the EIP-712 Submission message"}
        reg = list(registri)
        now = int(self.now())
        with self.lock:
            ada = self.semua()
            try:
                sha = submission.submission_sha(sub)
            except Exception:  # noqa: BLE001 - formulir rusak: biar validate yang menjelaskan
                sha = None
            if sha and any(r["submission_sha"] == sha for r in ada):
                return 409, {"error": "this submission was already received", "id": sha}
            ids = {r["bot_id"] for r in ada} | {r.get("bot_id") for r in reg} | set(SPECS)
            masalah = submission.validate(sub, existing_ids=ids, enabled_kinds=self.kinds)
            if not masalah and sub["kind"] == "code":
                masalah = kodemod.cocok_meta(body.get("code"), sub["spec"]["kode"]) if isinstance(body.get("code"), str) else [
                    "code: teks kode wajib dikirim di body.code (privat; tidak ikut formulir publik)"]
            if masalah:
                return 400, {"error": "form rejected", "problems": masalah}
            issuer = sub["identity"]["issuer_wallet"]
            dipakai = [r["nonce"] for r in ada if r["issuer"] == issuer]
            ident = submission.verify_identity(sub, sig, CHAIN_ID, nonce, deadline, now, used_nonces=dipakai,
                                               payout_signature_hex=body.get("payout_signature"))
            if ident:
                return (409 if any("nonce" in m for m in ident) else 401), {"error": "identity rejected", "problems": ident}
            ditinjau = {r.get("submission_sha") for r in reg}
            if sum(1 for r in ada if r["issuer"] == issuer and r["submission_sha"] not in ditinjau) >= MAKS_TERTUNDA_PER_PENERBIT:
                return 429, {"error": f"at most {MAKS_TERTUNDA_PER_PENERBIT} submissions per issuer waiting for review"}
            hari = now // 86_400
            if sum(1 for r in ada if r["t"] // 86_400 == hari) >= MAKS_PER_HARI:
                return 429, {"error": f"daily intake limit ({MAKS_PER_HARI}) reached, try again after 00:00 UTC"}
            publik = copy.deepcopy(sub)
            kontak = publik["identity"].pop("contact", None)
            rec = {"t": now, "submission_sha": sha, "spec_sha": submission.spec_sha_of(sub), "bot_id": sub["spec"]["bot_id"], "issuer": issuer,
                   "payout": sub["identity"]["payout_wallet"], "chain_id": CHAIN_ID, "nonce": nonce, "deadline": deadline, "signature": sig,
                   "payout_signature": body.get("payout_signature"), "submission": publik}
            os.makedirs(self.folder, exist_ok=True)
            with open(self.masuk, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
            if kontak:
                with open(self.kontak, "a", encoding="utf-8", newline="\n") as f:
                    f.write(json.dumps({"submission_sha": sha, "contact": kontak}, ensure_ascii=False) + "\n")
            if sub["kind"] == "code":                                          # privat: hanya pemegang volume + pelari terpisah yang membacanya
                os.makedirs(self.kode_dir, exist_ok=True)
                kp = os.path.join(self.kode_dir, sub["spec"]["kode"]["sha"][2:] + ".py")
                with open(os.open(kp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w", encoding="utf-8", newline="\n") as f:
                    f.write(body["code"])
        return 201, {"id": sha, "status": "received", "received_t": now, "bot_id": rec["bot_id"], "spec_sha": rec["spec_sha"],
                     "next": "reviewed by the daily public review run (gates G1-G11 + KPI on the repo's daily bars); status at /bots/submissions/" + sha}

    def daftar(self, registri: Iterable[dict] = (), sha: Optional[str] = None, status: Optional[Dict[str, dict]] = None,
               bayangan: Optional[Dict[str, dict]] = None) -> List[dict]:
        """Antrean publik + status dari repo: registri (vonis, laporan) atau `status.json` peninjau (tertahan masa tunggu / ditolak sebelum
        gerbang). Tanpa kontak."""
        by, st = {r.get("submission_sha"): r for r in registri}, status or {}
        out = []
        for r in self.semua():
            if sha and r["submission_sha"] != sha:
                continue
            g, x = by.get(r["submission_sha"]), st.get(r["submission_sha"])
            label = "reviewed" if g else ("rejected" if x and x.get("final") else "queued" if x else "waiting for review")
            sh = (bayangan or {}).get(r["bot_id"]) if g and g.get("vonis") in ("LOLOS_SHADOW", "MAJU_FEED") else None
            if sh:
                label = "in slot" if sh.get("slot") else "shadow"
            out.append({**r, "status": label, "review": {k: g.get(k) for k in ("vonis", "report_sha", "k", "alpha", "t_utc")} if g else None,
                        "note": (x or {}).get("alasan") if not g else None, "shadow": sh})
        return out


def baca_status(path: str) -> Dict[str, dict]:
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def baca_registri(path: str) -> List[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(ln) for ln in f if ln.strip()]


def info_tanda_tangan() -> Dict[str, object]:
    """Untuk formulir web: cara membangun pesan EIP-712 (sama dengan `submission.typed_data`)."""
    return {"eip712_name": submission.EIP712_NAME, "version": str(submission.SCHEMA_V), "chain_id": CHAIN_ID, "primary_type": "Submission",
            "max_ttl_s": 3600, "templates": {k: {"param_nama": v.param_nama, "param": v.param, "metode": v.metode} for k, v in sorted(SPECS.items())
                                              if k in submission.REGISTRY},
            "symbols": sorted(submission.KNOWN_SYMBOLS), "kill_bounds": submission.KILL_BOUNDS, "shadow_days": 60,
            "kinds_open": list(submission.ENABLED_KINDS), "rule": rulemod.vocabulary(), "schema": submission.schema_json(),
            "code": info_kode(), "feed": feed_gerbang.info()}


KODE_CONTOH = '''PARAMS = {"N": 60}


def target(bars, params):
    """Called once per daily bar with bars up to that bar only. Return {symbol: weight}; gross <= 1."""
    n = params["N"]
    out = {}
    for sym in sorted(bars):
        c = bars[sym]["c"]
        if len(c) > n and c[-1] > c[-1 - n]:
            out[sym] = 1.0 / len(bars)
    return out
'''


def info_kode() -> Dict[str, object]:
    """Kontrak `kind=code` untuk editor web (P167b). Kode PRIVAT dan jenis ini TERTUTUP sampai builder menyetujui jalur privat."""
    return {"open": "code" in submission.ENABLED_KINDS, "label": kodemod.LABEL_KEPERCAYAAN, "reviewer_note": kodemod.CATATAN_PENINJAU,
            "max_bytes": kodemod.LIMITS["ukuran_maks"], "max_params": kodemod.LIMITS["max_parameter"], "imports": list(kodemod.MODUL),
            "builtins": list(kodemod.BUILTINS), "template": KODE_CONTOH,
            "limits": {k: kodemod.LIMITS[k] for k in ("langkah_per_panggilan", "cpu_s", "memori_mb", "waktu_dinding_s")},
            "public_copy": "sha + size + PARAMS only; the code text never enters the public repo"}


def bayangan_dari(workdir: str, now_s: int) -> Dict[str, dict]:
    """Progres bot penerbit sesudah lolos: hari bayangan sejak genesis ledger maju + apakah sudah di slot buku hidup (B1e). P167c: bot feed = bayangan
    120 hari dari `ledger/feed/<bot>.jsonl`, tanpa slot, berlabel "tidak bisa diverifikasi ulang"."""
    from engine import book_live, feed as feedmod, ledger, terdaftar
    out: Dict[str, dict] = {}
    try:
        for b in terdaftar.feed_rincian(workdir)[0]:
            p = os.path.join(workdir, "ledger", "feed", f"{b}.jsonl")
            g = ledger.load(p)[0] if os.path.exists(p) else None
            hari = max(0, (now_s * 1000 - int(g["first_asof"])) // 86_400_000) if g and g.get("first_asof") is not None else 0
            out[b] = {"days": int(hari), "of": feedmod.BAYANGAN_HARI, "slot": False, "started": bool(g), "label": feedmod.LABEL_KEPERCAYAAN}
    except Exception:  # noqa: BLE001 - status tampilan saja
        pass
    try:
        luar = terdaftar.penerbit(workdir)[0]
        buku_path = os.path.join(workdir, "ledger", "book", "buku.jsonl")
        di_buku = {e.bot_id for e in book_live.current_book(ledger.load(buku_path))} if os.path.exists(buku_path) else set()
    except Exception:  # noqa: BLE001 - status tampilan saja; jalur resminya di repo
        return out
    for b in luar:
        p = os.path.join(workdir, "ledger", "paper", f"{b}.jsonl")
        try:
            g = ledger.load(p)[0] if os.path.exists(p) else None
        except Exception:  # noqa: BLE001
            g = None
        hari = max(0, (now_s * 1000 - int(g["first_asof"])) // 86_400_000) if g and g.get("first_asof") is not None else 0
        out[b] = {"days": int(hari), "of": 60, "slot": b in di_buku, "started": bool(g)}
    return out
