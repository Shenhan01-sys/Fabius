"""Deploy X402DemoToken ke chain 97 dan danai dompet klien - sekali jalan, rekornya di data/.

Kenapa bukan `forge create`: bisa, dan memang itu yang dipakai untuk BUILD-nya (profil `fork`,
karena token ini butuh Cancun). Yang kubawa ke Python adalah langkah LANJUTANNYA - transfer ke
payer + menulis `data/x402/deploy.json` - supaya alamat yang dipakai gerbang dan klien berasal dari
SATU catatan, bukan dari copy-paste terminal (alamat yang salah ketik di form submission adalah
cara paling sunyi untuk membayar kontrak orang lain).

Pakai:  set FOUNDRY_PROFILE=fork&& forge build
         python tools/x402_deploy.py                # deploy + fund
         python tools/x402_deploy.py --existing 0x.. # pakai alamat yang sudah ada
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import verify_deploy as vd  # noqa: E402

ART = os.path.join(ROOT, "out", "X402DemoToken.sol", "X402DemoToken.json")
OUT = os.path.join(ROOT, "data", "x402", "deploy.json")
# Alamat pembeli TIDAK dikarang di sini: diturunkan dari alat yang sama yang akan memakainya.
# Versi earlier punya konstanta sendiri + komentar "derive: keccak(...)" yang tidak benar, dan
# dananya pun masuk ke dompet yang bukan klien.
import x402_client as cli  # noqa: E402
PAYER = cli.payer_address()


def load_agent():
    k = {}
    for path in (os.path.join(ROOT, ".agent.env"), os.path.expanduser("~/.config/fabius/agent.env")):
        try:
            for ln in open(path, encoding="utf-8"):
                ln = ln.strip()
                if ln and not ln.startswith("#") and "=" in ln:
                    a, b = ln.split("=", 1)
                    k.setdefault(a.strip(), b.strip())
        except OSError:
            continue
    if not k.get("AGENT_PRIVATE_KEY"):
        raise SystemExit(".agent.env tidak berisi AGENT_PRIVATE_KEY")
    return k["AGENT_PRIVATE_KEY"], k["AGENT_ADDRESS"]


def deploy(pk, addr):
    from eth_account import Account
    from eth_utils import to_checksum_address as cs
    if not os.path.exists(ART):
        raise SystemExit(f"artifact tidak ada: {ART}\n  build dulu: set FOUNDRY_PROFILE=fork&& forge build")
    data = json.load(open(ART, encoding="utf-8"))["bytecode"]["object"]
    if not data.startswith("0x") or len(data) < 20:
        raise SystemExit("bytecode kosong di artifact - build-nya belum benar")
    bal = vd.num(vd.rpc("eth_getBalance", [addr, "latest"]))
    print(f"  gas    : {vd.num(vd.rpc('eth_gasPrice', [])) / 10**9:.2f} gwei | "
          f"saldo deployer {bal / 10**18:.6f} tBNB")
    if bal < 3_000_000_000_000_000:      # 0,003 tBNB cukup untuk satu create + satu transfer
        raise SystemExit("saldo deployer terlalu kecil untuk create + transfer - top-up dulu "
                         "(_research/topup_agent.py). Tidak ada tx yang dikirim.")
    nonce = vd.num(vd.rpc("eth_getTransactionCount", [addr, "latest"]))
    gp = max(vd.num(vd.rpc("eth_gasPrice", [])), 10**9)
    tx = {"chainId": vd.CHAIN, "from": cs(addr), "to": None, "value": 0, "nonce": nonce,
          "gas": 3_000_000, "gasPrice": gp, "data": data}
    signed = Account.sign_transaction(tx, pk)
    raw = signed.raw_transaction if hasattr(signed, "raw_transaction") else signed.rawTransaction
    h = vd.rpc("eth_sendRawTransaction", ["0x" + raw.hex()])
    print(f"  create : https://testnet.bscscan.com/tx/{h}")
    for _ in range(40):
        r = vd.rpc("eth_getTransactionReceipt", [h])
        if r:
            if vd.num(r["status"]) != 1:
                raise SystemExit(f"create GAGAL (gas terpakai {vd.num(r['gasUsed'])}) - "
                                 "cek apakah 97 menerima opcode Cancun sebelum menyalahkan kodenya")
            return vd.rpc("eth_getCode", [r["contractAddress"], "latest"]), r
        time.sleep(2)
    raise SystemExit("receipt tidak muncul dalam 80 detik - jangan kirim ulang, nonce sudah terpakai")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--existing", default=None)
    ap.add_argument("--fund", type=int, default=5_000_000, help="atomic (6 desimal) utk payer")
    a = ap.parse_args()
    pk, addr = load_agent()
    token = a.existing
    if not token:
        print(f"chain={vd.CHAIN} deployer={addr}")
        _, rec = deploy(pk, addr)
        token = rec["contractAddress"]
    from eth_utils import to_checksum_address as cs
    code = vd.rpc("eth_getCode", [cs(token), "latest"])
    print(f"token  : {token}  (code {max(0, (len(code) - 2) // 2)} byte)")
    if code in ("0x", "", None):
        raise SystemExit("alamat token tidak berisi kontrak - berhenti")

    # danai payer dengan SUPPLY YANG SUDAH ADA (constructor memberi deployer 1.000.000 token);
    # sengaja bukan `faucet()`: faucet perlu gas dari sisi klien, dan salah satu poin uji kita
    # justru bahwa klien TIDAK pernah mengirim transaksi.
    from eth_abi import encode as enc
    from eth_utils import keccak
    calldata = "0x" + keccak(text="transfer(address,uint256)")[:4].hex() + \
        enc(["address", "uint256"], [cs(PAYER), a.fund]).hex()
    h, st, blk, gas, _ = vd.send(pk, cs(token), calldata, gas=200_000)
    print(f"fund   : {a.fund} atomic -> {PAYER}  status={st} gas={gas}")
    print(f"         https://testnet.bscscan.com/tx/{h}")
    if st != 1:
        raise SystemExit("transfer gagal - gerbang tidak akan punya pembeli")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"token": cs(token), "network": f"eip155:{vd.CHAIN}", "payer": PAYER,
               "proxy": "0x402085c248EeA27D92E8b30b2C58ed07f9E20001",
               "deployed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "deploy_tx": h, "funded_atomic": a.fund},
              open(OUT, "w", encoding="utf-8"), indent=1, sort_keys=True)
    print(f"\ntertulis: {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
