"""P166 (F-D121): agent LUAR ikut siklus meja 5 menit dengan cara PULL.

Agent dengan identitas ERC-8004 sendiri (1) mendaftar sekali dengan pesan EIP-191 yang ditandatangani dompet agent atau pemilik identitas,
(2) tiap siklus MENGAMBIL masukan lewat long-poll, (3) MENGIRIM jawaban v2 bertanda tangan sebelum batas. Fabius tidak punya kunci mereka dan tidak
memanggil model mereka. Modul ini murni logika + keadaan (tanpa jaringan; identitas ERC-8004 disuntik lewat `resolve`), jadi seluruh jalur diuji tanpa chain.

Gerbang memasang: `Luar.minta` di dalam `meja2.siklus2` (thread siklus menunggu jawaban), rute HTTP `/desk/external[/join|/pull|/answer]`.
Aturan seleksi kursi tidak di sini: agent luar masuk C1 seperti agent rumah baru (kursi uji tidak dihitung konsensus)."""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from typing import Callable, Dict, List, Optional, Tuple

# Batas OPERASIONAL (bukan aturan seleksi): mencegah banjir pendaftaran dan menjaga komit siklus tetap sempat. Dicetak di /desk/external.
PARAMS_LUAR = {"v": 1, "maks_terdaftar": 10, "satu_per_pemilik": True, "join_ttl_s": 3600, "join_per_jam": 10,
               "batas_jawab_s": 210,        # cadangan bila siklus2 tidak memberi `tenggat`; siklus2 menutup jawab pada tenggat mutlak (maks t0 + 265)
               "hadir_s": 900,              # tanpa tarikan selama ini = agent dianggap mati, siklusnya gagal cepat (tidak ditunggu)
               "wait_maks_s": 30, "tarik_ttl_s": 120, "pengintai_maks": 40, "pengintai_per_agen": 2, "jawaban_maks_byte": 16_384, "percobaan_per_siklus": 10, "nama_maks": 24}
NAMA_OK = re.compile(r"[^A-Za-z0-9 ._-]")
PRE_JOIN, PRE_JAWAB, PRE_TARIK = "Fabius desk join v1", "Fabius desk answer v1", "Fabius desk pull v1"


def sha_bytes(b: bytes) -> str:
    return "0x" + hashlib.sha256(b).hexdigest()


def sha_masukan(system: str, user: str) -> str:
    """Sama dengan `prompt_sha` di rekaman meja2: sha256(system + "\\n" + prompt)."""
    return sha_bytes(system.encode() + b"\n" + user.encode())


def pesan_join(agent_id: int, deadline: int) -> str:
    return f"{PRE_JOIN}\nagent_id: {int(agent_id)}\ndeadline: {int(deadline)}"


def pesan_tarik(agent_id: int, ts: int) -> str:
    return f"{PRE_TARIK}\nagent_id: {int(agent_id)}\nts: {int(ts)}"


def pesan_jawab(agent_id: int, siklus: int, prompt_sha: str, answer_sha: str) -> str:
    return f"{PRE_JAWAB}\nagent_id: {int(agent_id)}\nsiklus: {int(siklus)}\nprompt_sha: {prompt_sha}\nanswer_sha: {answer_sha}"


def pulihkan(pesan: str, tanda_tangan: str) -> str:
    """Alamat (EIP-55) penanda tangan pesan teks EIP-191. Butuh `eth-account`; tanpa itu gagal TERTUTUP (RuntimeError)."""
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct
    except ImportError as e:                       # pragma: no cover
        raise RuntimeError("verifikasi tanda tangan butuh eth-account") from e
    return Account.recover_message(encode_defunct(text=pesan), signature=tanda_tangan)


def bersih_nama(nama: object, agent_id: int) -> str:
    n = NAMA_OK.sub("", str(nama or "")).strip()[:PARAMS_LUAR["nama_maks"]].strip()
    return n or f"agent {agent_id}"


class Luar:
    """Daftar agent luar (tersimpan) + serah-terima masukan/jawaban per siklus (di memori).

    `resolve(agent_id) -> {"wallet": str|None, "owner": str, "nama": str}`; KeyError bila identitas tidak ada, galat lain = RPC bermasalah.
    `status(slug) -> {"kursi": str|None, "gagal": bool, "n": int, "sah_pct": float|None}` dari state meja (bisa kosong).
    `rumah() -> set[int]` id agent rumah (tidak boleh didaftarkan sebagai agent luar)."""

    def __init__(self, path: str, now: Callable[[], float] = time.time, resolve: Optional[Callable[[int], dict]] = None,
                 status: Optional[Callable[[str], dict]] = None, rumah: Optional[Callable[[], set]] = None, params: Optional[dict] = None):
        self.path, self.now, self.resolve = path, now, resolve
        self.status = status or (lambda slug: {})
        self.rumah = rumah or (lambda: set())
        self.P = {**PARAMS_LUAR, **(params or {})}
        self.cv = threading.Condition()
        self.pending: Dict[int, dict] = {}         # agent_id -> permintaan siklus yang sedang terbuka
        self.terlihat: Dict[int, float] = {}       # agent_id -> waktu tarikan terakhir
        self.pengintai: Dict[int, int] = {}
        self.bukti_siklus: Dict[str, dict] = {}    # slug -> {siklus, penanda_tangan, tanda_tangan} (jawaban sah terakhir)
        self.join_waktu: List[float] = []
        self.agen: Dict[str, dict] = {}
        try:
            with open(path, encoding="utf-8") as f:
                self.agen = (json.load(f) or {}).get("agen", {})
        except (OSError, ValueError):
            pass

    # ------------------------------------------------------------ pendaftaran
    def _simpan(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"agen": self.agen}, f, sort_keys=True, ensure_ascii=False)
        os.replace(tmp, self.path)

    def agent(self, agent_id: int) -> Optional[dict]:
        return next((a for a in self.agen.values() if a["agent_id"] == agent_id), None)

    def agents(self) -> List[dict]:
        """Daftar untuk `meja2.siklus2` (urut id): bentuk sama dengan agent rumah + `luar: True`."""
        return [{"slug": a["slug"], "name": a["nama"], "agent_id": a["agent_id"], "model": f"external ERC-8004 #{a['agent_id']}", "provider": "external",
                 "luar": True} for a in sorted(self.agen.values(), key=lambda a: a["agent_id"])]

    def nama(self, slug: str) -> Optional[str]:
        return (self.agen.get(slug) or {}).get("nama")

    def join(self, body: dict) -> Tuple[int, dict]:
        try:
            aid, dl, sig = int(body["agent_id"]), int(body["deadline"]), str(body["signature"])
        except (KeyError, TypeError, ValueError):
            return 400, {"error": "body needs agent_id (int), deadline (unix s), signature (0x hex)"}
        if aid <= 0 or aid >= 10 ** 14:
            return 400, {"error": "agent_id out of range"}
        now = self.now()
        if dl < now:
            return 401, {"error": "signature expired"}
        if dl - now > self.P["join_ttl_s"]:
            return 400, {"error": f"deadline too far (max {self.P['join_ttl_s']} s)"}
        try:
            who = pulihkan(pesan_join(aid, dl), sig)
        except RuntimeError:
            raise
        except Exception as e:  # noqa: BLE001 - tanda tangan rusak: tolak, jangan lempar
            return 400, {"error": f"signature unreadable: {type(e).__name__}"}
        try:
            ident = self.resolve(aid)
        except KeyError:
            return 404, {"error": f"no ERC-8004 identity with agent_id {aid}"}
        except Exception as e:  # noqa: BLE001
            return 502, {"error": f"identity lookup failed: {type(e).__name__}"}
        pemilik, dompet = str(ident["owner"]).lower(), (str(ident["wallet"]).lower() if ident.get("wallet") else None)
        if who.lower() not in (pemilik, dompet):
            return 403, {"error": f"signer {who} is neither the agent wallet nor the identity owner"}
        sudah = self.agent(aid)
        if sudah and (self.status(sudah["slug"]) or {}).get("gagal"):
            return 403, {"error": "removed after repeated trial failures (F-D119); only a builder decision seats this agent again"}
        if sudah:
            return 200, {"registered": True, "already": True, "slug": sudah["slug"], "agent_id": aid, **self._info(sudah)}
        if aid in self.rumah():
            return 409, {"error": "this agent is one of Fabius' own desk agents"}
        if len(self.agen) >= self.P["maks_terdaftar"]:
            return 409, {"error": f"desk full: {self.P['maks_terdaftar']} external agents registered"}
        if self.P["satu_per_pemilik"] and any(a["pemilik"] == pemilik for a in self.agen.values()):
            return 409, {"error": "this identity owner already has an external agent registered (one per owner)"}
        self.join_waktu = [t for t in self.join_waktu if now - t < 3600]
        if len(self.join_waktu) >= self.P["join_per_jam"]:
            return 429, {"error": "too many registrations this hour"}
        self.join_waktu.append(now)
        a = {"slug": f"x{aid}", "agent_id": aid, "nama": bersih_nama(ident.get("nama"), aid), "pemilik": pemilik, "dompet": dompet, "sejak": int(now)}
        self.agen[a["slug"]] = a
        self._simpan()
        return 201, {"registered": True, "already": False, "slug": a["slug"], "agent_id": aid, **self._info(a),
                     "next": "poll GET /desk/external/pull?agent_id=%d&wait=25 every cycle; the desk seats you in a trial seat or the queue" % aid}

    def _info(self, a: dict) -> dict:
        st = self.status(a["slug"]) or {}
        return {"name": a["nama"], "seat": st.get("kursi"), "removed_for_failures": bool(st.get("gagal"))}

    def roster(self) -> List[dict]:
        now, out = self.now(), []
        for a in sorted(self.agen.values(), key=lambda a: a["agent_id"]):
            st = self.status(a["slug"]) or {}
            out.append({"slug": a["slug"], "agent_id": a["agent_id"], "name": a["nama"], "since": a["sejak"], "seat": st.get("kursi"),
                        "removed_for_failures": bool(st.get("gagal")), "answers_observed": st.get("n"), "valid_pct": st.get("sah_pct"),
                        "online": now - self.terlihat.get(a["agent_id"], -1e12) <= self.P["hadir_s"]})
        return out

    def info(self) -> dict:
        return {"what": "External agents join Fabius' 5-minute desk by PULL: register once, then each cycle fetch the input and post a signed v2 answer. "
                        "Fabius never holds your key and never calls your model. You need your own ERC-8004 identity (chain 97).",
                "params": self.P, "params_sha": sha_bytes(json.dumps(self.P, sort_keys=True, separators=(",", ":")).encode()),
                "endpoints": {"join": "POST /desk/external/join {agent_id, deadline, signature}",
                              "pull": "GET /desk/external/pull?agent_id=N&wait=25&ts=<unix s>&signature=<0x hex>",
                              "answer": "POST /desk/external/answer {agent_id, siklus, answer, signature}"},
                "sign": {"scheme": "EIP-191 personal_sign (text)", "signer": "the agent wallet (getAgentWallet) or the identity owner (ownerOf)",
                         "join_message": pesan_join(0, 0).replace("agent_id: 0", "agent_id: <id>").replace("deadline: 0", "deadline: <unix s, <= now + 3600>"),
                         "answer_message": pesan_jawab(0, 0, "<prompt_sha>", "<answer_sha>").replace("agent_id: 0", "agent_id: <id>").replace("siklus: 0", "siklus: <t0>"),
                         "pull_message": pesan_tarik(0, 0).replace("agent_id: 0", "agent_id: <id>").replace("ts: 0", "ts: <unix s, within +-%d s of the gate clock>" % self.P["tarik_ttl_s"]),
                         "answer_sha": "0x + sha256 of the answer string exactly as sent (utf-8)",
                         "prompt_sha": "0x + sha256 of system + '\\n' + prompt, as returned by pull"},
                "seats": "A new agent takes a trial seat (or waits in the queue). Trial answers are recorded and anchored but NOT counted in the consensus; "
                         "promotion to an active seat follows the locked F-D113 rules (>= 288 cycles, >= 95 % valid, result >= active median or +0.5 pp over the weakest). "
                         "Fewer than 80 % valid answers over >= 144 observed cycles sends you to the back of the queue, twice = removed (F-D119).",
                "deadline": "each pull response carries the absolute deadline (unix s, about 3.5 minutes after the cycle's data is read); late or invalid answers count as failures",
                "agents": self.roster()}

    # ------------------------------------------------------------ tarik (agent) dan minta (siklus)
    def tarik(self, agent_id: int, wait_s: float, ts: object, tanda_tangan: object) -> Tuple[int, dict]:
        """Long-poll BERTANDA TANGAN (pesan `Fabius desk pull v1 / agent_id / ts`, ts dalam +-`tarik_ttl_s`): tanpa tanda tangan siapa pun bisa memalsukan
        kehadiran sebuah agent (siklusnya lalu ditunggu penuh dan dicatat gagal) atau menghabiskan slot long-poll-nya."""
        a = self.agent(agent_id)
        if not a:
            return 404, {"error": "agent not registered; POST /desk/external/join first"}
        try:
            ts = int(ts)
            who = pulihkan(pesan_tarik(agent_id, ts), str(tanda_tangan))
        except RuntimeError:
            raise
        except Exception:  # noqa: BLE001 - ts / tanda tangan hilang atau rusak
            return 400, {"error": "pull needs ts (unix s) and signature (0x hex) over: " + pesan_tarik(agent_id, 0).replace("ts: 0", "ts: <ts>")}
        if not self.now() - self.P["tarik_ttl_s"] <= ts <= self.now() + 30:
            return 401, {"error": f"ts outside the allowed window (+-{self.P['tarik_ttl_s']} s of the gate clock)"}
        if who.lower() not in (a["pemilik"], a["dompet"]):
            return 403, {"error": f"signer {who} is neither the agent wallet nor the identity owner recorded at registration"}
        return self._tarik(a, agent_id, wait_s)

    def _tarik(self, a: dict, agent_id: int, wait_s: float) -> Tuple[int, dict]:
        wait_s = max(0.0, min(float(wait_s), self.P["wait_maks_s"]))
        with self.cv:
            if sum(self.pengintai.values()) >= self.P["pengintai_maks"] or self.pengintai.get(agent_id, 0) >= self.P["pengintai_per_agen"]:
                return 429, {"error": "too many open polls"}
            self.pengintai[agent_id] = self.pengintai.get(agent_id, 0) + 1
            try:
                self.terlihat[agent_id] = self.now()
                tutup = time.monotonic() + wait_s
                while True:
                    req = self.pending.get(agent_id)
                    if req and req["jawaban"] is None and self.now() < req["deadline"]:
                        return 200, {"siklus": req["siklus"], "deadline": req["deadline"], "system": req["system"], "prompt": req["prompt"],
                                     "prompt_sha": req["prompt_sha"], "answer_message": pesan_jawab(agent_id, req["siklus"], req["prompt_sha"], "<answer_sha>")}
                    sisa = tutup - time.monotonic()
                    if sisa <= 0:
                        break
                    self.cv.wait(timeout=min(sisa, 1.0))
                    self.terlihat[agent_id] = self.now()
            finally:
                self.pengintai[agent_id] -= 1
        st = self.status(a["slug"]) or {}
        nxt = int(self.now() // 300 * 300) + 300
        return 200, {"siklus": None, "next_siklus": nxt, "seat": st.get("kursi"), "retry_after_s": max(1, int(nxt + 8 - self.now())),
                     "note": (("removed after repeated trial failures (F-D119)" if st.get("gagal") else
                               "no input for you this cycle: your seat is '%s' (only trial and active seats are asked)" % st.get("kursi"))
                              if st.get("kursi") not in (None, "aktif", "uji") else "no open request; the next cycle starts at next_siklus (+8 s)")}

    def minta(self, ag: dict, system: str, user: str, siklus: int, validasi: Callable[[str], object], tenggat: Optional[float] = None) -> str:
        """Dipanggil thread siklus (`meja2.siklus2`): menaruh masukan agent ini lalu MENUNGGU jawaban bertanda tangan sampai batas. Agent yang tidak menarik
        dalam `hadir_s` gagal cepat (komit siklus tidak mundur). Galat = RuntimeError / TimeoutError -> rekaman `gagal`."""
        aid = int(ag["agent_id"])
        now = self.now()
        if now - self.terlihat.get(aid, -1e12) > self.P["hadir_s"]:
            raise RuntimeError(f"external agent not polling (no pull in the last {self.P['hadir_s']} s)")
        req = {"siklus": int(siklus), "deadline": int(tenggat if tenggat else int(siklus) + self.P["batas_jawab_s"]), "system": system, "prompt": user, "prompt_sha": sha_masukan(system, user),
               "validasi": validasi, "jawaban": None, "tanda_tangan": None, "penanda_tangan": None, "percobaan": 0, "slug": ag["slug"]}
        with self.cv:
            self.pending[aid] = req
            self.cv.notify_all()
            tutup = time.monotonic() + max(0.0, req["deadline"] - self.now())
            while req["jawaban"] is None:
                sisa = tutup - time.monotonic()
                if sisa <= 0:
                    break
                self.cv.wait(timeout=min(sisa, 1.0))
            if self.pending.get(aid) is req:
                del self.pending[aid]
            jawaban = req["jawaban"]
            if jawaban is not None:
                self.bukti_siklus[ag["slug"]] = {"siklus": req["siklus"], "penanda_tangan": req["penanda_tangan"], "tanda_tangan": req["tanda_tangan"]}
        if jawaban is None:
            raise TimeoutError("no valid signed answer before the deadline")
        return jawaban

    def bukti(self, slug: str, siklus: int) -> Optional[dict]:
        b = self.bukti_siklus.get(slug)
        return dict(b) if b and b["siklus"] == siklus else None

    # ------------------------------------------------------------ jawab (agent)
    def jawab(self, body: dict) -> Tuple[int, dict]:
        try:
            aid, siklus, ans, sig = int(body["agent_id"]), int(body["siklus"]), body["answer"], str(body["signature"])
        except (KeyError, TypeError, ValueError):
            return 400, {"error": "body needs agent_id (int), siklus (int), answer (string), signature (0x hex)"}
        if not isinstance(ans, str):
            return 400, {"error": "answer must be a string (the JSON text exactly as you hashed it)"}
        a = self.agent(aid)
        if not a:
            return 403, {"error": "agent not registered"}
        if len(ans.encode("utf-8")) > self.P["jawaban_maks_byte"]:
            return 413, {"error": f"answer larger than {self.P['jawaban_maks_byte']} bytes"}
        with self.cv:
            req = self.pending.get(aid)
            if not req or req["siklus"] != siklus or self.now() >= req["deadline"]:
                return 410, {"error": "no open request for this agent and cycle (closed, late, or not yet started)"}
            if req["jawaban"] is not None:
                return 409, {"error": "this cycle already has a valid answer from you"}
            if req["percobaan"] >= self.P["percobaan_per_siklus"]:
                return 429, {"error": "too many attempts this cycle"}
            req["percobaan"] += 1
            psha = req["prompt_sha"]
        try:
            who = pulihkan(pesan_jawab(aid, siklus, psha, sha_bytes(ans.encode("utf-8"))), sig)
        except RuntimeError:
            raise
        except Exception as e:  # noqa: BLE001
            return 400, {"error": f"signature unreadable: {type(e).__name__}"}
        if who.lower() not in (a["pemilik"], a["dompet"]):
            return 403, {"error": f"signer {who} is neither the agent wallet nor the identity owner recorded at registration"}
        try:
            req["validasi"](ans)
        except Exception as e:  # noqa: BLE001 - jawaban salah format: boleh kirim ulang sebelum batas
            return 422, {"error": "answer rejected", "problems": [f"{type(e).__name__}: {str(e)[:200]}"], "retry": "fix and resend before the deadline"}
        with self.cv:
            if req["jawaban"] is not None:
                return 409, {"error": "this cycle already has a valid answer from you"}
            if self.now() >= req["deadline"] or self.pending.get(aid) is not req:
                return 410, {"error": "the cycle closed while your answer was being checked"}
            req["jawaban"], req["tanda_tangan"], req["penanda_tangan"] = ans, sig, who
            self.cv.notify_all()
        return 200, {"accepted": True, "siklus": siklus, "answer_sha": sha_bytes(ans.encode("utf-8")), "prompt_sha": psha}
