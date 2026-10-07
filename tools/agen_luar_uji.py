"""P151 / P166: AGENT LUAR UJI milik builder - identitas ERC-8004 SENDIRI (dompet terpisah, bukan agent rumah) yang memakai jalur agent luar
publik persis seperti pihak ketiga: daftar identitas -> join meja (tanda tangan EIP-191) -> jawab tiap siklus lewat PULL (`tools/desk_agent_client.py`)
dengan penjawab berbasis aturan (`tools/agen_luar_uji_jawab.py`, tanpa LLM). Tujuannya MEMBUKTIKAN jalur agent luar hidup; ia diberi label jujur
"test agent operated by the Fabius builder" di kartunya - bukan adopsi pihak ketiga.

Kunci dompet di `.agen_luar_uji.env` (gitignored, tidak pernah dicetak). Transaksi hanya dengan `--send`.

  python -X utf8 tools/agen_luar_uji.py kunci            # buat dompet (sekali)
  python -X utf8 tools/agen_luar_uji.py kartu            # tulis docs/agen-luar-uji.json (kartu ERC-8004 publik; commit + push sebelum daftar)
  python -X utf8 tools/agen_luar_uji.py daftar [--send]  # rencana / kirim: isi 0,01 tBNB dari committer + register(kartu) dari dompet ini
  python -X utf8 tools/agen_luar_uji.py join             # join meja sebagai agent luar (tanpa tx)
  python -X utf8 tools/agen_luar_uji.py jalan [--sekali] # jawab siklus meja (PULL) dengan penjawab aturan
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, ROOT]

import signal_commit as sc                                                                  # noqa: E402

ENV = os.path.join(ROOT, ".agen_luar_uji.env")
VAR = "AGEN_LUAR_UJI_KEY"
KARTU = os.path.join(ROOT, "docs", "agen-luar-uji.json")
KARTU_URL = "https://raw.githubusercontent.com/Shenhan01-sys/Fabius/master/docs/agen-luar-uji.json"
FUND_WEI = 10 ** 16
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def kunci() -> str:
    k = os.environ.get(VAR) or sc.read_env_file(ENV, VAR)
    if not k:
        raise SystemExit("kunci belum ada: jalankan `kunci`")
    return k


def deploy() -> dict:
    with open(sc.DEPLOYMENTS, encoding="utf-8") as f:
        return json.load(f)


def cmd_kunci(a) -> int:
    from eth_account import Account
    k = os.environ.get(VAR) or sc.read_env_file(ENV, VAR)
    if k:
        print(f"dompet agent luar uji: {Account.from_key(k).address} (sudah ada, tidak ditimpa)")
        return 0
    acct = Account.create()
    hx = acct.key.hex()
    with open(ENV, "a", encoding="utf-8") as f:
        f.write("# kunci dompet AGENT LUAR UJI (P151/P166). JANGAN di-commit / ditempel.\n" f"{VAR}={hx if hx.startswith('0x') else '0x' + hx}\n")
    print(f"dompet agent luar uji: {acct.address} (BARU; kunci di .agen_luar_uji.env, tidak dicetak)")
    return 0


def cmd_kartu(a) -> int:
    from eth_account import Account
    d = deploy()
    card = {"protocol": "erc-8004/1", "name": "Fabius external test agent (rule-based)", "type": "analyst",
            "description": ("TEST agent operated by the Fabius builder to prove the PUBLIC external-agent path end to end (separate wallet and "
                            "ERC-8004 identity, not a house agent). It joins the 5-minute desk by signature and answers every cycle by PULL with a "
                            "small rule set (B6 when z_10h < -2, B1 when >= 3 instruments trend up, else a small B5 core); no language model. "
                            "It is not third-party adoption."),
            "model": {"provider": "none", "id": "rules (tools/agen_luar_uji_jawab.py)", "effort": "n/a"},
            "wallet": Account.from_key(kunci()).address,
            "evidence": {"desk": "https://fabius-x402-production.up.railway.app/desk/external", "chain_id": 97,
                         "selection_anchor": d.get("contracts", {}).get("SelectionAnchor"), "code": "tools/agen_luar_uji.py, tools/agen_luar_uji_jawab.py"},
            "limits_stated_honestly": ["paper only, BNB testnet", "builder-operated test agent", "rule-based, no edge claimed"]}
    os.makedirs(os.path.dirname(KARTU), exist_ok=True)
    with open(KARTU, "w", encoding="utf-8", newline="\n") as f:
        json.dump(card, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"kartu ditulis: {os.path.relpath(KARTU, ROOT)} (wallet {card['wallet']}); commit + push sebelum `daftar --send` supaya URI-nya hidup")
    return 0


def cmd_daftar(a) -> int:
    import evm as evmmod
    from evm import address_of, calldata, receipt_ok
    d = deploy()
    reg = d.get("agen_luar_uji") or {}
    pk = kunci()
    w = address_of(pk)
    if reg.get("agent_id"):
        print(f"sudah terdaftar: agent {reg['agent_id']} (dompet {reg['wallet']})")
        return 0
    ev = evmmod.Evm(sc.rpc_urls(), sc.CHAIN_ID)
    ev.chain_check()
    bal = ev.balance(w)
    identity = d["erc8004"]["identity"]
    print(f"dompet {w} saldo {bal / 1e18:.6f} tBNB | IdentityRegistry {identity} | URI {KARTU_URL}")
    if not a.send:
        print("RENCANA: isi 0,01 tBNB dari committer (bila saldo < 0,005) + register(string URI) dari dompet ini - tanpa --send tidak ada yang dikirim")
        return 0
    if bal < FUND_WEI // 2:
        r = ev.send(sc.committer_key(), w, b"", value=FUND_WEI, gas=21_000)
        print(f"isi 0,01 tBNB tx {r['transactionHash']} {'OK' if receipt_ok(r) else 'GAGAL'}")
    r = ev.send(pk, identity, calldata("register(string)", ("string",), (KARTU_URL,)))
    if not receipt_ok(r):
        print(f"register GAGAL tx {r.get('transactionHash')}")
        return 1
    pad = "0x" + "0" * 24 + w.lower()[2:]
    tid = next(int(lg["topics"][3], 16) for lg in r["logs"] if lg["topics"][0].lower() == TRANSFER and lg["topics"][1] == "0x" + "0" * 64
               and lg["topics"][2].lower() == pad)
    owner = ev.call_decode(identity, "ownerOf(uint256)", ("uint256",), (tid,), ("address",))[0]
    if owner.lower() != w.lower():
        print(f"BERHENTI: ownerOf({tid}) = {owner} bukan {w}")
        return 1
    d["agen_luar_uji"] = {"agent_id": tid, "wallet": w, "tx": r["transactionHash"], "uri": KARTU_URL, "jenis": "uji milik builder, berbasis aturan"}
    with open(sc.DEPLOYMENTS, "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False))
    print(f"TERDAFTAR agent {tid} tx {r['transactionHash']} (ownerOf dibaca ulang = dompet)")
    return 0


def _klien(*args: str) -> int:
    reg = deploy().get("agen_luar_uji") or {}
    if not reg.get("agent_id"):
        raise SystemExit("belum terdaftar: jalankan `daftar --send`")
    env = {**os.environ, VAR: kunci()}
    return subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "desk_agent_client.py"), "--agent-id", str(reg["agent_id"]), "--key-env", VAR,
                           *args], env=env).returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("kunci")
    sub.add_parser("kartu")
    d = sub.add_parser("daftar")
    d.add_argument("--send", action="store_true")
    sub.add_parser("join")
    j = sub.add_parser("jalan")
    j.add_argument("--sekali", action="store_true")
    a = ap.parse_args()
    if a.cmd == "join":
        return _klien("join")
    if a.cmd == "jalan":
        jawab = f'"{sys.executable}" -X utf8 "{os.path.join(HERE, "agen_luar_uji_jawab.py")}"'
        return _klien("run", "--answer-cmd", jawab, *(["--once"] if a.sekali else []))
    return {"kunci": cmd_kunci, "kartu": cmd_kartu, "daftar": cmd_daftar}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
