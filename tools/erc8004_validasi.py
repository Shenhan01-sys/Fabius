"""Validasi ERC-8004 untuk komit sinyal Fabius (P136, F-D98): agen 2494 di `IdentityRegistry` chain 97, `ValidationRegistry` v2.0.0 resmi.

Peran (satu berkas, empat pemanggil):
  minta    committer (worker Railway, `Worker.validation_step`): untuk tiap komit Fabius yang ADA di SignalAnchor ->
           `validationRequest(validator, 2494, uri, requestHash = commitId)`. Idempoten: `getValidationStatus(commitId)` sudah ada = dilewati.
  jawab    validator (workflow `validasi.yml`, dipicu rantai paper-ledger): pemeriksa publik P106 (`tools/verify_signals.py`) menghitung ulang
           kunci -> komit -> ungkap -> daun -> isi ledger; vonis SAH -> 100, ALARM / TIDAK DIUNGKAP -> 0, selain itu (jendela masih terbuka) -> tunggu.
           `responseHash` = sha256 laporan JSON yang dicetak di log run; `responseURI` = URL run Actions itu.
  setuju   agen pemilik 2494 (sekali, lokal, kata builder): `approve(committer, 2494)` - committer boleh meminta validasi untuk 2494 saja.
  kunci-validator  (sekali, lokal): kunci baru ke `.validator.env` (di-gitignore); yang dicetak dan ditulis ke deployments/97.json hanya ALAMAT.

Klaim yang jujur: validator = kunci KAMI SENDIRI di infrastruktur lain (GitHub Actions publik, bukan Railway yang memegang kunci committer). Ini
"dihitung ulang oleh CI publik dan siapa pun bisa menjalankan pemeriksa yang sama", BUKAN validasi tanpa kepercayaan (vault 06-Results).

    python -X utf8 tools/erc8004_validasi.py ringkas                 # tanpa kunci, tanpa gas
    python -X utf8 tools/erc8004_validasi.py setuju [--send]         # rencana dulu; --send hanya atas kata builder
    python -X utf8 tools/erc8004_validasi.py minta  [--send]         # yang dilakukan worker tiap putaran
    python -X utf8 tools/erc8004_validasi.py jawab  [--send]         # yang dilakukan validasi.yml
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from typing import Callable, Dict, List, Optional, Sequence, Tuple

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from engine import chain, ledger                                              # noqa: E402
from engine.spec import SPECS                                                 # noqa: E402
import signal_commit as sc                                                    # noqa: E402

VALIDATOR_ENV = os.path.join(ROOT, ".validator.env")
VALIDATOR_VAR = "VALIDATOR_PRIVATE_KEY"
TAG = "fabius-komit-ungkap-v1"
URI = "https://fabius-one.vercel.app/bot/{bot}?bar={bar}"
SCORE = {"SAH": 100, "ALARM": 0, "TIDAK DIUNGKAP": 0}       # vonis lain = belum final (jendela ungkap / maxLag masih terbuka): tunggu
LIMIT = 6                                                    # tx per putaran per peran: membatasi gas bila ada tumpukan

SIG_REQUEST = "validationRequest(address,uint256,string,bytes32)"
SIG_RESPONSE = "validationResponse(bytes32,uint8,string,bytes32,string)"
SIG_STATUS = "getValidationStatus(bytes32)"
STATUS_OUT = ("address", "uint256", "uint8", "bytes32", "string", "uint256")


def load_cfg(path: str = sc.DEPLOYMENTS) -> Optional[dict]:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("erc8004")
    except (OSError, ValueError):
        return None


def validator_key() -> Optional[str]:
    return os.environ.get(VALIDATOR_VAR) or sc.read_env_file(VALIDATOR_ENV, VALIDATOR_VAR)


class RegistryView:
    """Pembaca IdentityRegistry + ValidationRegistry lewat `evm.Evm`. Uji memakai tiruan dengan metode yang sama."""

    def __init__(self, evm, cfg: dict):
        self.evm, self.cfg = evm, cfg

    def authorized(self, agent_id: int, who: str) -> bool:
        ident, w = self.cfg["identity"], who.lower()
        owner = self.evm.call_decode(ident, "ownerOf(uint256)", ("uint256",), (agent_id,), ("address",))[0]
        if owner.lower() == w:
            return True
        if self.evm.call_decode(ident, "getApproved(uint256)", ("uint256",), (agent_id,), ("address",))[0].lower() == w:
            return True
        return bool(self.evm.call_decode(ident, "isApprovedForAll(address,address)", ("address", "address"), (owner, who), ("bool",))[0])

    def status(self, request_hash: bytes) -> Optional[dict]:
        """None = belum pernah diminta (kontrak revert "unknown")."""
        from evm import RpcError
        try:
            v = self.evm.call_decode(self.cfg["validation"], SIG_STATUS, ("bytes32",), (request_hash,), STATUS_OUT)
        except RpcError as e:
            if "unknown" in str(e):
                return None
            raise
        return dict(zip(("validator", "agentId", "response", "responseHash", "tag", "lastUpdate"), v))

    def validator_requests(self, validator: str) -> List[bytes]:
        return list(self.evm.call_decode(self.cfg["validation"], "getValidatorRequests(address)", ("address",), (validator,), ("bytes32[]",))[0])

    def summary(self, agent_id: int, validators: Sequence[str], tag: str) -> Tuple[int, int]:
        c, avg = self.evm.call_decode(self.cfg["validation"], "getSummary(uint256,address[],string)", ("uint256", "address[]", "string"),
                                      (agent_id, list(validators), tag), ("uint64", "uint8"))
        return int(c), int(avg)


# ---------------------------------------------------------------- minta (committer)

def candidates(bots: Sequence[str], ledger_dir: str, cv, committer: str) -> List[Tuple[str, str, bytes]]:
    """(bot, bar, commitId) untuk tiap tick ledger yang komitnya ADA di SignalAnchor dari committer kita; urut bar naik."""
    out = []
    for bot in bots:
        if bot not in SPECS:
            continue
        sha = SPECS[bot].sha()
        for tk in ledger.load(os.path.join(ledger_dir, f"{bot}.jsonl")):
            if tk.get("type") != "tick":
                continue
            cid = sc.commit_id(committer, bot, sha, sc.asof_s_of(tk))
            if int(str(cv.get_commit(cid)["committer"]), 16):
                out.append((bot, tk["asof_date"], cid))
    return sorted(out, key=lambda t: (t[1], t[0]))


def request_round(reg, send: Callable[[str, bytes], dict], committer: str, cfg: dict, cands: Sequence[Tuple[str, str, bytes]],
                  log: Callable[[str], None] = print, limit: int = LIMIT) -> Dict[str, int]:
    """Minta validasi untuk komit yang belum punya permintaan. Belum disetujui pemilik 2494 = tidak mengirim apa pun (bukan galat)."""
    from evm import calldata, receipt_ok
    st = {"diminta": 0, "sudah": 0, "gagal": 0, "belum_setuju": 0}
    agent, validator = int(cfg["agent_id"]), cfg["validator"]
    if not reg.authorized(agent, committer):
        st["belum_setuju"] = 1
        return st
    for bot, bar, cid in cands:
        if reg.status(cid) is not None:
            st["sudah"] += 1
            continue
        if st["diminta"] + st["gagal"] >= limit:
            break
        data = calldata(SIG_REQUEST, ("address", "uint256", "string", "bytes32"), (validator, agent, URI.format(bot=bot, bar=bar), cid))
        try:
            r = send(cfg["validation"], data)
            ok = receipt_ok(r)
        except Exception as e:  # noqa: BLE001 - satu permintaan gagal tidak menghentikan yang lain; diulang putaran berikut
            ok, r = False, {"transactionHash": f"{type(e).__name__}: {str(e)[:120]}"}
        st["diminta" if ok else "gagal"] += 1
        log(f"validasi ERC-8004 {'DIMINTA' if ok else 'GAGAL diminta'}: {bot} {bar} commitId {chain.hex0x(cid)[:18]}… tx {r.get('transactionHash')}")
    return st


# ---------------------------------------------------------------- jawab (validator)

def report_of(row, run_url: str, repo_sha: str) -> dict:
    return {"v": 1, "tag": TAG, "pemeriksa": "tools/verify_signals.py (P106)", "bot": row.bot, "bar": row.bar, "commitId": row.commit_id,
            "vonis": row.vonis, "detail": row.detail, "masalah": list(row.problems), "n": row.n, "terungkap": row.revealed, "lag_s": row.lag_s,
            "skor": SCORE[row.vonis], "repo_sha": repo_sha, "run": run_url}


def report_hash(rep: dict) -> bytes:
    return hashlib.sha256(json.dumps(rep, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).digest()


def answer_round(reg, send: Callable[[str, bytes], dict], validator: str, rows, run_url: str, repo_sha: str,
                 log: Callable[[str], None] = print, limit: int = LIMIT) -> Dict[str, int]:
    """Jawab permintaan yang ditujukan ke `validator` dan belum dijawab, memakai vonis pemeriksa P106. Vonis belum final = tunggu."""
    from evm import calldata, receipt_ok
    by_cid = {str(r.commit_id).lower(): r for r in rows if r.commit_id}
    st = {"dijawab": 0, "sudah": 0, "tunggu": 0, "asing": 0, "gagal": 0}
    for rh in reg.validator_requests(validator):
        s = reg.status(rh)
        if s is None or str(s["validator"]).lower() != validator.lower():
            st["asing"] += 1
            continue
        if int.from_bytes(bytes(s["responseHash"]), "big"):
            st["sudah"] += 1
            continue
        row = by_cid.get(chain.hex0x(rh).lower())
        if row is None:
            st["asing"] += 1                       # permintaan untuk komit yang tidak ada di ledger yang diperiksa: tidak dijawab, tidak dikarang
            log(f"  permintaan {chain.hex0x(rh)[:18]}… bukan komit Fabius yang diperiksa - tidak dijawab")
            continue
        if row.vonis not in SCORE:
            st["tunggu"] += 1
            continue
        if st["dijawab"] + st["gagal"] >= limit:
            break
        rep = report_of(row, run_url, repo_sha)
        h = report_hash(rep)
        log("LAPORAN " + json.dumps(rep, sort_keys=True, ensure_ascii=False) + f" sha256 {chain.hex0x(h)}")
        data = calldata(SIG_RESPONSE, ("bytes32", "uint8", "string", "bytes32", "string"), (rh, rep["skor"], run_url, h, TAG))
        try:
            r = send(reg.cfg["validation"], data)
            ok = receipt_ok(r)
        except Exception as e:  # noqa: BLE001
            ok, r = False, {"transactionHash": f"{type(e).__name__}: {str(e)[:120]}"}
        st["dijawab" if ok else "gagal"] += 1
        log(f"validasi ERC-8004 {'DIJAWAB' if ok else 'GAGAL dijawab'} {rep['skor']}: {row.bot} {row.bar} ({row.vonis}) tx {r.get('transactionHash')}")
    return st


# ---------------------------------------------------------------- CLI

def _evm():
    import evm as evmmod
    ev = evmmod.Evm(sc.rpc_urls(), sc.CHAIN_ID)
    ev.chain_check()
    return ev


def _sender(ev, pk: str, dry: bool, log=print):
    def send(to: str, data: bytes) -> dict:
        if dry:
            from evm import address_of
            gas = ev.estimate(address_of(pk), to, data)
            log(f"  RENCANA (tanpa --send): ke {to}, estimasi gas {gas}")
            return {"status": "0x1", "transactionHash": "(rencana)"}
        return ev.send(pk, to, data)
    return send


def cmd_kunci_validator(args) -> int:
    from eth_account import Account
    if os.path.exists(VALIDATOR_ENV):
        print(f"{VALIDATOR_ENV} sudah ada - tidak ditimpa. Alamat: {Account.from_key(validator_key()).address}")
        return 0
    acct = Account.create()
    with open(VALIDATOR_ENV, "w", encoding="utf-8") as f:
        f.write(f"# kunci validator ERC-8004 Fabius (P136). JANGAN di-commit, JANGAN ditempel ke chat. GitHub secret: VALIDATOR_PK\n"
                f"{VALIDATOR_VAR}={acct.key.hex() if acct.key.hex().startswith('0x') else '0x' + acct.key.hex()}\n"
                f"VALIDATOR_ADDRESS={acct.address}\n")
    with open(sc.DEPLOYMENTS, encoding="utf-8") as f:
        d = json.load(f)
    d.setdefault("erc8004", {})["validator"] = acct.address
    with open(sc.DEPLOYMENTS, "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps(d, indent=1, ensure_ascii=False, sort_keys=True))      # format berkas yang ada: indent 1, kunci urut, tanpa baris akhir
    print(f"kunci validator dibuat di .validator.env (tidak dicetak). Alamat: {acct.address} -> deployments/97.json erc8004.validator")
    return 0


def cmd_setuju(args) -> int:
    from evm import address_of, calldata, receipt_ok
    from x8004_register import agent_creds
    cfg, ev = load_cfg(), _evm()
    pk, _ = agent_creds()
    committer = (json.load(open(sc.DEPLOYMENTS, encoding="utf-8")).get("m3") or {}).get("committer")
    reg = RegistryView(ev, cfg)
    if reg.authorized(int(cfg["agent_id"]), committer):
        print(f"committer {committer} SUDAH boleh meminta validasi untuk agen {cfg['agent_id']} - tidak ada yang dikirim")
        return 0
    if not pk:
        print("kunci agen (pemilik 2494) tidak ditemukan - tidak bisa menyetujui")
        return 2
    owner = ev.call_decode(cfg["identity"], "ownerOf(uint256)", ("uint256",), (int(cfg["agent_id"]),), ("address",))[0]
    if owner.lower() != address_of(pk).lower():
        print(f"kunci agen {address_of(pk)} bukan pemilik 2494 ({owner}) - berhenti")
        return 2
    data = calldata("approve(address,uint256)", ("address", "uint256"), (committer, int(cfg["agent_id"])))
    r = _sender(ev, pk, not args.send)(cfg["identity"], data)
    if args.send:
        print(f"approve(committer, {cfg['agent_id']}) tx {r.get('transactionHash')} status {'OK' if receipt_ok(r) else 'GAGAL'}")
        print(f"baca ulang: committer boleh meminta = {reg.authorized(int(cfg['agent_id']), committer)}")
    return 0


def cmd_minta(args) -> int:
    cfg, ev = load_cfg(), _evm()
    if not (cfg and cfg.get("validator")):
        print("deployments/97.json erc8004.validator belum ada (jalankan kunci-validator dulu)")
        return 2
    pk = sc.committer_key()
    if not pk:
        print("kunci committer tidak ada")
        return 2
    from evm import address_of
    committer = address_of(pk)
    addrs = sc.load_addresses()
    cv = sc.AnchorView(ev, addrs["anchor"], addrs["registry"])
    st = request_round(RegistryView(ev, cfg), _sender(ev, pk, not args.send), committer, cfg,
                       candidates(sc.BOTS_DEFAULT, os.path.join(ROOT, "ledger", "paper"), cv, committer))
    print(f"RINGKAS minta: {st}")
    return 0


def cmd_jawab(args) -> int:
    import verify_signals as vs
    cfg = load_cfg()
    if not (cfg and cfg.get("validator")):
        print("deployments/97.json erc8004.validator belum ada")
        return 2
    vpk = validator_key()
    if args.send and not vpk:
        print(f"{VALIDATOR_VAR} tidak ada - tidak bisa menjawab")
        return 2
    rows, st, info = vs.run(sc.BOTS_DEFAULT, os.path.join(ROOT, "ledger", "paper"), os.path.join(ROOT, "ledger", "bars"))
    print(f"pemeriksa P106: {st}")
    if vpk:
        from evm import address_of
        if address_of(vpk).lower() != cfg["validator"].lower():
            print(f"kunci validator {address_of(vpk)} != erc8004.validator {cfg['validator']} - berhenti")
            return 2
    run_url = (f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
               if os.environ.get("GITHUB_RUN_ID") else "lokal (bukan run Actions)")
    repo_sha = os.environ.get("GITHUB_SHA", "")
    ev = info["ev"]
    send = _sender(ev, vpk, not args.send) if vpk else (lambda to, data: {"status": "0x1", "transactionHash": "(rencana, tanpa kunci)"})
    res = answer_round(RegistryView(ev, cfg), send, cfg["validator"], rows, run_url, repo_sha)
    print(f"RINGKAS jawab: {res}")
    return 1 if st.get("ALARM") else 0


def cmd_ringkas(args) -> int:
    cfg, ev = load_cfg(), _evm()
    reg = RegistryView(ev, cfg)
    agent = int(cfg["agent_id"])
    committer = (json.load(open(sc.DEPLOYMENTS, encoding="utf-8")).get("m3") or {}).get("committer")
    print(f"agen {agent} | ValidationRegistry {cfg['validation']} | validator {cfg.get('validator')} | committer boleh meminta: "
          f"{reg.authorized(agent, committer)}")
    if cfg.get("validator"):
        n, avg = reg.summary(agent, [cfg["validator"]], TAG)
        print(f"getSummary(tag {TAG}): {n} jawaban, rata-rata {avg}")
        for rh in reg.validator_requests(cfg["validator"]):
            s = reg.status(rh)
            done = int.from_bytes(bytes(s["responseHash"]), "big") != 0
            print(f"  {chain.hex0x(rh)[:18]}… {'skor ' + str(s['response']) if done else 'BELUM DIJAWAB'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Validasi ERC-8004 komit sinyal Fabius (P136).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("setuju", "minta", "jawab"):
        p = sub.add_parser(name)
        p.add_argument("--send", action="store_true", help="kirim tx sungguhan (tanpa ini: rencana + estimasi gas)")
    sub.add_parser("kunci-validator")
    sub.add_parser("ringkas")
    a = ap.parse_args()
    return {"kunci-validator": cmd_kunci_validator, "setuju": cmd_setuju, "minta": cmd_minta, "jawab": cmd_jawab, "ringkas": cmd_ringkas}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
