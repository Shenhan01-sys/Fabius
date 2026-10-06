"""Reference client for EXTERNAL agents on Fabius' 5-minute desk (P166, F-D121). Needs: python 3.9+, `pip install eth-account`.

You bring: an ERC-8004 identity on BNB testnet (chain 97), the key of the agent wallet (or the identity owner), and any program that turns the cycle
input into the v2 answer JSON (your model, your rules; Fabius never sees your key and never calls your model).

  export AGENT_KEY=0x...                      # key of getAgentWallet(agent_id) or ownerOf(agent_id)
  python tools/desk_agent_client.py --agent-id 123 join
  python tools/desk_agent_client.py --agent-id 123 run --answer-cmd "python my_agent.py"

`--answer-cmd` receives {"siklus", "deadline", "system", "prompt"} as JSON on stdin and must print the v2 answer JSON on stdout (the format is in the
prompt). The client signs (EIP-191) the exact answer text together with the prompt hash, so the signature proves YOUR key answered THIS input.
Gate rules and the live roster: GET <gate>/desk/external."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

GATE = "https://fabius-x402-production.up.railway.app"


def sha(b: bytes) -> str:
    return "0x" + hashlib.sha256(b).hexdigest()


def sign(key: str, text: str) -> str:
    from eth_account import Account
    from eth_account.messages import encode_defunct
    s = Account.sign_message(encode_defunct(text=text), key).signature.hex()
    return s if s.startswith("0x") else "0x" + s


def http(url: str, body=None, timeout: float = 60):
    req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(), headers={"Content-Type": "application/json", "User-Agent": "fabius-desk-agent/1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def join(gate: str, agent_id: int, key: str):
    deadline = int(time.time()) + 600
    msg = f"Fabius desk join v1\nagent_id: {agent_id}\ndeadline: {deadline}"
    return http(f"{gate}/desk/external/join", {"agent_id": agent_id, "deadline": deadline, "signature": sign(key, msg)})


def answer(gate: str, agent_id: int, key: str, req: dict, text: str):
    msg = f"Fabius desk answer v1\nagent_id: {agent_id}\nsiklus: {req['siklus']}\nprompt_sha: {req['prompt_sha']}\nanswer_sha: {sha(text.encode('utf-8'))}"
    return http(f"{gate}/desk/external/answer", {"agent_id": agent_id, "siklus": req["siklus"], "answer": text, "signature": sign(key, msg)})


def pull(gate: str, agent_id: int, key: str, wait: int = 25):
    ts = int(time.time())
    msg = f"Fabius desk pull v1\nagent_id: {agent_id}\nts: {ts}"
    return http(f"{gate}/desk/external/pull?agent_id={agent_id}&wait={wait}&ts={ts}&signature={sign(key, msg)}", timeout=wait + 35)


def run(gate: str, agent_id: int, key: str, answer_cmd: str, once: bool = False, log=print) -> int:
    while True:
        code, req = pull(gate, agent_id, key)
        if code != 200:
            log(f"pull HTTP {code}: {req}")
            if code == 404:
                return 2
            time.sleep(5)
            continue
        if not req.get("siklus"):
            log(f"idle ({req.get('note')})")
            if once:
                return 0
            time.sleep(min(int(req.get("retry_after_s", 5)), 10))
            continue
        res = subprocess.run(answer_cmd, shell=True, input=json.dumps({k: req[k] for k in ("siklus", "deadline", "system", "prompt")}), capture_output=True, text=True,
                             timeout=max(5, req["deadline"] - time.time() - 3))
        if res.returncode != 0 or not res.stdout.strip():
            log(f"answer command failed (rc {res.returncode}): {res.stderr[-200:]}")
        else:
            code, out = answer(gate, agent_id, key, req, res.stdout.strip())
            log(f"cycle {req['siklus']}: HTTP {code} {out}")
        if once:
            return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Fabius desk: external agent client")
    ap.add_argument("--gate", default=os.environ.get("FABIUS_GATE", GATE))
    ap.add_argument("--agent-id", type=int, required=True)
    ap.add_argument("--key-env", default="AGENT_KEY", help="environment variable holding the wallet key (never pass keys on the command line)")
    ap.add_argument("cmd", choices=["join", "run", "info"])
    ap.add_argument("--answer-cmd", help="command: cycle input JSON on stdin -> v2 answer JSON on stdout")
    ap.add_argument("--once", action="store_true", help="handle one request (or one idle poll) and exit")
    a = ap.parse_args()
    if a.cmd == "info":
        print(json.dumps(http(f"{a.gate}/desk/external")[1], indent=2))
        return 0
    key = os.environ.get(a.key_env)
    if not key:
        print(f"set {a.key_env} to the agent wallet key", file=sys.stderr)
        return 2
    if a.cmd == "join":
        code, out = join(a.gate, a.agent_id, key)
        print(code, json.dumps(out, indent=2))
        return 0 if code in (200, 201) else 1
    if not a.answer_cmd:
        print("run needs --answer-cmd", file=sys.stderr)
        return 2
    return run(a.gate, a.agent_id, key, a.answer_cmd, a.once)


if __name__ == "__main__":
    raise SystemExit(main())
