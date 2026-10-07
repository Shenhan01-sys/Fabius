"""P167c: penyimpanan komit `feed` di gerbang `fabius-x402` (volume) + anchor akar per bar ke `LockRegistry` (kontrak yang sudah ada).

Rute (dipasang `tools/x402_sinyal.py`):
  POST /bots/feed/typed-data  {bot_id, bar_close, bobot}              -> pesan EIP-712 `FeedCommit` yang harus ditandatangani dompet penerbit
  POST /bots/feed/commit      {bot_id, bar_close, bobot, signature}   -> 201 diterima | 400 bentuk/bobot | 401 tanda tangan | 404 bot bukan feed
                                                                           terdaftar | 409 sudah ada komit untuk bar ini | 422 waktu (terlambat / terlalu jauh)
  GET  /bots/feed[/<bot_id>]                                          -> aturan + komit publik. Bobot + tanda tangan + bukti baru terbuka SESUDAH bar dibuka
                                                                           (sebelumnya hanya daun + weights_sha: tidak membocorkan sinyal penerbit)

Penyimpanan (volume gerbang; berantai hash seperti ledger, LF murni):
  komit.jsonl  satu catatan per komit yang diterima (semua bot)
  akar.jsonl   satu catatan per percobaan anchor (bar_close, akar, n, tx, lockedAt, status)
Anchor: sesudah batas terima (`feed.BATAS_SEBELUM_TUTUP_S` sebelum penutupan) dan sebelum `JEDA_ANCHOR_S` terakhir, gerbang mengunci akar semua komit
bar itu di LockRegistry (`lock(bytes32("FABIUS-FEED"), akar, "fabius-feed:<barClose>:<n>")`) dengan kuncinya sendiri; status dibaca ULANG dari chain
(`lockedAt`), bukan dari kwitansi saja. Gagal = dicoba lagi selama masih sebelum penutupan; sesudahnya bar itu tidak ter-anchor (komitnya tidak dinilai).
"""
from __future__ import annotations

import os
import sys
import threading
import time
from typing import Callable, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from engine import chain, feed as F, ledger, submission                 # noqa: E402

CHAIN_ID = 97
MAX_BODY = 8 * 1024


class KomitFeed:
    def __init__(self, folder: str, now: Callable[[], float] = time.time):
        self.folder, self.now = folder, now
        self.lock = threading.Lock()
        self.path_komit = os.path.join(folder, "komit.jsonl")
        self.path_akar = os.path.join(folder, "akar.jsonl")

    # ------------------------------------------------------------ baca
    def semua(self) -> List[dict]:
        return ledger.load(self.path_komit)

    def akar_tercatat(self) -> Dict[int, dict]:
        """bar_close -> catatan anchor TERAKHIR (yang ter-anchor menang atas percobaan gagal)."""
        out: Dict[int, dict] = {}
        for r in ledger.load(self.path_akar):
            bc = int(r["bar_close"])
            if out.get(bc, {}).get("status") != "ter-anchor":
                out[bc] = r
        return out

    # ------------------------------------------------------------ terima
    @staticmethod
    def _bentuk(body: object) -> Tuple[Optional[str], Optional[dict]]:
        if not isinstance(body, dict):
            return "body must be {bot_id, bar_close, bobot[, signature]}", None
        bot, bc, bobot = body.get("bot_id"), body.get("bar_close"), body.get("bobot")
        if not isinstance(bot, str) or not 3 <= len(bot) <= 31 or isinstance(bc, bool) or not isinstance(bc, int) or not isinstance(bobot, dict):
            return "bot_id (text), bar_close (integer seconds) and bobot ({symbol: integer ppm}) are required", None
        return None, {"bot_id": bot, "bar_close": bc, "bobot": bobot}

    def _cek(self, body: object, terdaftar: Dict[str, dict]) -> Tuple[int, dict, Optional[dict]]:
        err, b = self._bentuk(body)
        if err:
            return 400, {"error": err}, None
        reg = terdaftar.get(b["bot_id"])
        if reg is None:
            return 404, {"error": "bot_id is not a registered feed bot (submit kind=feed first; it must be recorded by the daily review)"}, None
        now = int(self.now())
        why = F.periksa_waktu(b["bar_close"], now)
        if why:
            return 422, {"error": "commit time rejected", "problems": [why], "now": now}, None
        if b["bar_close"] <= int(reg["t_lolos"]):
            return 422, {"error": "commit time rejected", "problems": ["bar_close sebelum bot terdaftar"], "now": now}, None
        masalah = F.validate_bobot(b["bobot"], reg["spec"].universe)
        if masalah:
            return 400, {"error": "weights rejected", "problems": masalah}, None
        td = F.typed_data(b["bot_id"], reg["spec_sha"], reg["issuer"], b["bar_close"], b["bobot"], CHAIN_ID,
                          submission.EIP712_NAME, str(submission.SCHEMA_V))
        return 200, td, dict(b, issuer=reg["issuer"], spec_sha=reg["spec_sha"], now=now)

    def typed(self, body: object, terdaftar: Dict[str, dict]) -> Tuple[int, dict]:
        code, out, _ = self._cek(body, terdaftar)
        return code, out

    def terima(self, body: object, terdaftar: Dict[str, dict]) -> Tuple[int, dict]:
        code, td, b = self._cek(body, terdaftar)
        if b is None:
            return code, td
        sig = body.get("signature") if isinstance(body, dict) else None
        if not isinstance(sig, str) or not sig.startswith("0x"):
            return 400, {"error": "signature (0x...) required: the issuer wallet signs the EIP-712 FeedCommit message"}
        try:
            who = F.recover(td, sig)
        except RuntimeError:
            raise
        except Exception as e:                                                  # noqa: BLE001 - tanda tangan rusak = tolak, bukan 500
            return 401, {"error": "signature rejected", "problems": [f"tanda tangan tidak terbaca: {type(e).__name__}"]}
        if who != b["issuer"]:
            return 401, {"error": "signature rejected", "problems": [f"penanda tangan {who} bukan dompet penerbit terdaftar"]}
        with self.lock:
            why = F.periksa_waktu(b["bar_close"], int(self.now()))                # diulang DI DALAM kunci: rencana anchor membaca berkas di kunci yang sama,
            if why:                                                               # jadi komit tidak pernah masuk sesudah akar bar itu dihitung
                return 422, {"error": "commit time rejected", "problems": [why]}
            ada = self.semua()
            if any(r["bot_id"] == b["bot_id"] and int(r["bar_close"]) == b["bar_close"] for r in ada):
                return 409, {"error": "a commit for this bot and bar already exists (one per bar, never replaced)"}
            rec = {"type": "komit", "t_terima": b["now"], "t_utc": ledger.utc_iso(b["now"] * 1000), "bot_id": b["bot_id"], "issuer": b["issuer"],
                   "spec_sha": b["spec_sha"], "bar_close": b["bar_close"], "bobot": {k: int(v) for k, v in sorted(b["bobot"].items())},
                   "weights_sha": td["message"]["weightsSha"], "signature": sig}
            rec["leaf"] = chain.hex0x(F.daun(rec))
            ledger.append(self.path_komit, ledger.seal(rec, ledger.head(ada)), ada)
        return 201, {"status": "committed", "bot_id": b["bot_id"], "bar_close": b["bar_close"], "leaf": rec["leaf"], "weights_sha": rec["weights_sha"],
                     "anchor": f"root locked on LockRegistry before {ledger.utc_iso(b['bar_close'] * 1000)} (label {F.LABEL_ANCHOR})",
                     "label": F.LABEL_KEPERCAYAAN}

    # ------------------------------------------------------------ publik
    def publik(self, bot_id: Optional[str] = None) -> List[dict]:
        """Komit publik. Sebelum bar dibuka: daun + weights_sha + waktu terima saja; sesudahnya: bobot, tanda tangan, akar, bukti, anchor."""
        now = int(self.now())
        recs = self.semua()
        anc = self.akar_tercatat()
        per_bar: Dict[int, List[dict]] = {}
        for r in recs:
            per_bar.setdefault(int(r["bar_close"]), []).append(r)
        out = []
        for r in recs:
            if bot_id and r["bot_id"] != bot_id:
                continue
            bc = int(r["bar_close"])
            row = {k: r[k] for k in ("bot_id", "bar_close", "t_terima", "t_utc", "issuer", "spec_sha", "weights_sha", "leaf")}
            if now >= bc:
                root, proofs = F.akar(per_bar[bc])
                a = anc.get(bc) or {}
                cocok = a.get("root") == chain.hex0x(root)
                row.update(bobot=r["bobot"], signature=r["signature"], root=chain.hex0x(root), proof=proofs[r["leaf"]],
                           anchor={"status": a.get("status", "tidak ada") if cocok or not a else "akar beda dari yang di-anchor",
                                   "tx": a.get("tx"), "locked_at": a.get("locked_at") if cocok else None, "locker": a.get("locker"),
                                   "contract": a.get("contract")})
            else:
                row["sealed_until"] = bc
            out.append(row)
        return out

    # ------------------------------------------------------------ anchor
    def rencana(self, now_s: int) -> Optional[dict]:
        """Anchor yang harus dikirim SEKARANG (bar berikutnya, batas terima lewat, belum ter-anchor, ada komit), atau None."""
        bc = (now_s // F.DAY_S + 1) * F.DAY_S
        if not bc - F.BATAS_SEBELUM_TUTUP_S <= now_s < bc - F.JEDA_ANCHOR_S:
            return None
        if self.akar_tercatat().get(bc, {}).get("status") == "ter-anchor":
            return None
        with self.lock:                                                           # lihat `terima`: batas waktu + baca berkas di kunci yang sama
            recs = [r for r in self.semua() if int(r["bar_close"]) == bc]
        if not recs:
            return None
        root, _ = F.akar(recs)
        return {"bar_close": bc, "root": chain.hex0x(root), "n": len(recs), "calldata": F.lock_calldata(root, bc, len(recs))}

    def putaran_anchor(self, now_s: int, kirim: Callable[[bytes], dict], baca_locked_at: Callable[[str, str], int], locker: str,
                       contract: str) -> Optional[dict]:
        """Satu putaran anchor. Status dari `lockedAt` on-chain (dibaca ulang): ter-anchor hanya bila 0 < lockedAt < bar_close."""
        plan = self.rencana(now_s)
        if plan is None:
            return None
        tx, why = None, None
        try:
            la = int(baca_locked_at(locker, plan["root"]))
            if la == 0:
                r = kirim(plan["calldata"])
                tx = r.get("transactionHash")
                la = int(baca_locked_at(locker, plan["root"]))
        except Exception as e:                                                  # noqa: BLE001 - RPC/tx gagal: dicatat, dicoba lagi putaran berikut
            la, why = 0, f"gagal: {type(e).__name__}"
        status = "ter-anchor" if 0 < la < plan["bar_close"] else ("terlambat" if la else (why or "gagal: lockedAt masih 0"))
        rec = {"type": "anchor", "bar_close": plan["bar_close"], "root": plan["root"], "n": plan["n"], "tx": tx, "locked_at": la or None,
               "locker": locker, "contract": contract, "status": status, "t_utc": ledger.utc_iso(int(now_s) * 1000)}
        with self.lock:
            ada = ledger.load(self.path_akar)
            ledger.append(self.path_akar, ledger.seal(rec, ledger.head(ada)), ada)
        return rec


def info() -> dict:
    """Aturan feed untuk web + penerbit (dibagikan `GET /bots/schema` dan `GET /bots/feed`)."""
    return {"label": F.LABEL_KEPERCAYAAN, "shadow_days": F.BAYANGAN_HARI, "slot": "none until proven (builder decides what proven means)",
            "commit_cutoff_s": F.BATAS_SEBELUM_TUTUP_S, "max_ahead_s": F.MAKS_KE_DEPAN_S, "ppm": F.PPM, "anchor_label": F.LABEL_ANCHOR,
            "eip712": {"name": submission.EIP712_NAME, "version": str(submission.SCHEMA_V), "chain_id": CHAIN_ID, "primary_type": "FeedCommit",
                       "types": F.FEED_TYPES},
            "weights_text": "sorted 'SYMBOL:ppm' joined by ',' (zero weights dropped; empty = flat); weightsSha = sha256 of that ASCII text",
            "replay_gates": "N/A (not PASS): a feed cannot be replayed; only forward evidence counts",
            "routes": ["POST /bots/feed/typed-data", "POST /bots/feed/commit", "GET /bots/feed/<bot_id>"]}
