"""P161 B1a: antrean pengajuan bot di gerbang (`POST /bots/submit`, `GET /bots/submissions`). Gerbang hanya MENERIMA: skema tertutup + identitas
EIP-712 diperiksa saat kiriman masuk (tanda tangan berlaku <= 1 jam), lalu kiriman masuk antrean publik. Peninjauan (gerbang G1-G11 + KPI + registri
P83) dijalankan rantai GitHub harian di repo publik dengan `--now = t_terima`, jadi siapa pun bisa mengulang verifikasi tanda tangan dan vonisnya.

Penyimpanan (volume gerbang):
  masuk.jsonl   antrean publik: formulir TANPA `identity.contact` (kontak tidak ikut hash, jadi sha tetap bisa dicek) + tanda tangan + nonce + deadline
  kontak.jsonl  kontak penerbit (privat; tidak pernah dikirim lewat API)
Batas: <= 2 kiriman belum ditinjau per penerbit, <= 50 kiriman per hari UTC (semua penerbit); nonce per penerbit tidak boleh dipakai ulang.
"""
from __future__ import annotations

import copy
import json
import os
import threading
import time
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from engine import submission
from engine.spec import SPECS

CHAIN_ID = 97
MAX_BODY = 64 * 1024
MAKS_TERTUNDA_PER_PENERBIT = 2
MAKS_PER_HARI = 50


class Antrean:
    def __init__(self, folder: str, now: Callable[[], float] = time.time):
        self.folder, self.now = folder, now
        self.lock = threading.Lock()
        self.masuk = os.path.join(folder, "masuk.jsonl")
        self.kontak = os.path.join(folder, "kontak.jsonl")

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
            masalah = submission.validate(sub, existing_ids=ids)
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
        return 201, {"id": sha, "status": "received", "received_t": now, "bot_id": rec["bot_id"], "spec_sha": rec["spec_sha"],
                     "next": "reviewed by the daily public review run (gates G1-G11 + KPI on the repo's daily bars); status at /bots/submissions/" + sha}

    def daftar(self, registri: Iterable[dict] = (), sha: Optional[str] = None, status: Optional[Dict[str, dict]] = None) -> List[dict]:
        """Antrean publik + status dari repo: registri (vonis, laporan) atau `status.json` peninjau (tertahan masa tunggu / ditolak sebelum
        gerbang). Tanpa kontak."""
        by, st = {r.get("submission_sha"): r for r in registri}, status or {}
        out = []
        for r in self.semua():
            if sha and r["submission_sha"] != sha:
                continue
            g, x = by.get(r["submission_sha"]), st.get(r["submission_sha"])
            label = "reviewed" if g else ("rejected" if x and x.get("final") else "queued" if x else "waiting for review")
            out.append({**r, "status": label, "review": {k: g.get(k) for k in ("vonis", "report_sha", "k", "alpha", "t_utc")} if g else None,
                        "note": (x or {}).get("alasan") if not g else None})
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
            "max_ttl_s": 3600, "templates": sorted(k for k in SPECS), "schema": submission.schema_json()}
