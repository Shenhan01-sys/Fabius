"""Deploy jalur eksekusi ke chain 97: DemoAsset -> DemoPair -> ExecutionVault, lalu isi likuiditas.

Kenapa Python, bukan `forge script --broadcast`: yang kita butuhkan bukan kemudahan DeployScript,
tapi bisa MEMBACA saldo dan menaksir gas SEBELUM mengirim apa pun. Tiga deploy + seeding itu
ratusan ribu gas; mengirim tanpa tahu saldo berarti rantai transaksi mati di tengah - dan
kontrak yang setengah jadi di chain publik lebih buruk daripada belum deploy sama sekali.

Yang dilakukan, berurutan:
  1. estimasi gas tiap create + total biaya vs saldo agen -> kalau kurang, BERHENTI dan suruh
     top-up (tidak ada tx yang dikirim);
  2. deploy, tunggu receipt, dan verifikasi `eth_getCode` benar-benar berisi (status=1 saja
     tidak membuktikan kontraknya ada di alamat yang kita kira);
  3. seeding: pair dapat asset+quote lalu `bootstrap()`; vault dapat inventaris untuk long & short;
  4. `setVenue` + `setCaps` (plafon $5/hari, $1/posisi);
  5. `eth_call` openLong sebagai dry-run: jalur terpanggil tanpa menghabiskan gas.

Rekaman alamat ditulis ke `data/execution/deploy.json` (di-gitignore) dan dibaca
`tools/execute_live.py`. Alamat juga dicetak supaya bisa ditempel ke dokumen.

Pakai:  python tools/exec_deploy.py
         python tools/exec_deploy.py --existing 0x.. 0x.. 0x..   # pakai kontrak yang sudah ada
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
from eth_abi import encode as enc  # noqa: E402
from eth_account import Account  # noqa: E402
from eth_utils import keccak, to_checksum_address as cs  # noqa: E402

ART = lambda n: os.path.join(ROOT, "out", f"{n}.sol", f"{n}.json")     # noqa: E731
QUOTE = "0xB11D90214089684081F57A03d3300E20725297f8"   # X402DemoToken (deploy 26 Sep, di chain 97)
OUT = os.path.join(ROOT, "data", "execution", "deploy.json")
Q6 = 10**6


def creds():
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
    return k["AGENT_PRIVATE_KEY"], cs(k["AGENT_ADDRESS"])


def bytecode(name):
    p = ART(name)
    if not os.path.exists(p):
        raise SystemExit(f"artifact {p} tidak ada - build dulu: forge build")
    obj = json.load(open(p, encoding="utf-8"))
    return obj["bytecode"]["object"]


def wait_receipt(h, tries=40):
    for _ in range(tries):
        r = vd.rpc("eth_getTransactionReceipt", [h])
        if r:
            return r
        time.sleep(2)
    raise SystemExit(f"receipt {h} tidak muncul dalam {tries * 2}s - JANGAN kirim ulang, "
                     "nonce sudah terpakai; cek explorer dulu")


def deploy(pk, addr, name, args=(), gas=6_000_000):
    data = bytecode(name)
    if args:
        types = ["address"] * len(args)
        data = data + enc(types, list(args)).hex()
    gp = max(vd.num(vd.rpc("eth_gasPrice", [])), 10**9)
    tx = {"chainId": vd.CHAIN, "from": addr, "to": None, "value": 0, "gas": gas, "gasPrice": gp,
          "data": data, "nonce": vd.num(vd.rpc("eth_getTransactionCount", [addr, "latest"]))}
    try:
        est = vd.num(vd.rpc("eth_estimateGas", [{"from": addr, "data": data}]))
        tx["gas"] = int(est * 1.3)
    except Exception as e:  # noqa: BLE001
        print(f"  (estimateGas gagal untuk {name}: {str(e)[:90]} - pakai plafon penuh)")
    s = Account.sign_transaction(tx, pk)
    raw = s.raw_transaction if hasattr(s, "raw_transaction") else s.rawTransaction
    h = vd.rpc("eth_sendRawTransaction", ["0x" + bytes(raw).hex()])
    r = wait_receipt(h)
    if vd.num(r["status"]) != 1:
        raise SystemExit(f"deploy {name} GAGAL (gas terpakai {vd.num(r['gasUsed'])}) - berhenti, "
                         "jangan lanjut ke kontrak berikutnya")
    ca = r["contractAddress"]
    code = vd.rpc("eth_getCode", [ca, "latest"])
    if code in ("0x", "", None):
        raise SystemExit(f"{name}: receipt sukses tapi TIDAK ada kode di {ca} - berhenti")
    print(f"  {name:16} {ca}  kode {(len(code)-2)//2:>6} B  gas {vd.num(r['gasUsed']):>9,}")
    return ca, h


def send(pk, addr, to, sig, types, vals, gas=400_000, label=""):
    data = "0x" + keccak(text=sig)[:4].hex() + enc(list(types), list(vals)).hex()
    h, st, blk, gu, _ = vd.send(pk, cs(to), data, gas=gas)
    ok = "OK " if st == 1 else "GAGAL"
    print(f"  {ok} {label:26} gas {gu:>8,}  https://testnet.bscscan.com/tx/{h}")
    if st != 1:
        raise SystemExit(f"{label} gagal - berhenti sebelum menuliskan keadaan setengah jadi")
    return h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--existing", nargs=3, default=None, metavar=("ASSET", "PAIR", "VAULT"))
    a = ap.parse_args()
    pk, addr = creds()
    cid = vd.num(vd.rpc("eth_chainId", []))
    if cid != vd.CHAIN:
        raise SystemExit(f"RPC membalas chainId={cid}, config {vd.CHAIN} -> berhenti")

    bal = vd.num(vd.rpc("eth_getBalance", [addr, "latest"]))
    gp = max(vd.num(vd.rpc("eth_gasPrice", [])), 10**9)
    print(f"chain={cid} agen={addr}\nsaldo {bal/1e18:.6f} tBNB @ {gp/1e9:.1f} gwei")
    need = 18_000_000 * gp                      # taksiran kasar 3 create + 4 panggilan
    if not a.existing and bal < need:
        raise SystemExit(f"perlu ~{need/1e18:.6f} tBNB, saldo {bal/1e18:.6f} -> top-up dulu "
                         "(python ../_research/topup_agent.py 0.03). TIDAK ada tx yang dikirim.")

    if a.existing:
        asset, pair, vault = [cs(x) for x in a.existing]
        print(f"memakai kontrak yang sudah ada: asset={asset} pair={pair} vault={vault}")
        txs = {}
    else:
        print("deploy:")
        asset, t1 = deploy(pk, addr, "DemoAsset")
        pair, t2 = deploy(pk, addr, "DemoPair", (asset, QUOTE, addr))
        vault, t3 = deploy(pk, addr, "ExecutionVault", (QUOTE, addr, addr))
        txs = {"asset_tx": t1, "pair_tx": t2, "vault_tx": t3}

    # likuiditas: pair perlu KEDUA sisi. quote adalah X402DemoToken yang supply-nya kita pegang.
    print("seeding:")
    send(pk, addr, asset, "give(address,uint256)", ("address", "uint256"),
         [pair, 100_000 * Q6], label="mint asset -> pair")
    send(pk, addr, QUOTE, "transfer(address,uint256)", ("address", "uint256"),
         [pair, 200_000 * Q6], label="quote -> pair")
    send(pk, addr, pair, "bootstrap()", (), (), label="pair.bootstrap()")
    send(pk, addr, asset, "give(address,uint256)", ("address", "uint256"),
         [vault, 500 * Q6], label="mint asset -> vault (inventaris short)")
    send(pk, addr, QUOTE, "transfer(address,uint256)", ("address", "uint256"),
         [vault, 50 * Q6], label="quote -> vault (amunisi long)")
    send(pk, addr, vault, "setVenue(address,address)", ("address", "address"),
         [asset, pair], label="vault.setVenue")
    send(pk, addr, vault, "setCaps(uint256,uint256)", ("uint256", "uint256"),
         [5 * Q6, 1 * Q6], label="vault.setCaps($5/hari,$1/posisi)")

    # dry-run: jalur benar-benar terpanggil, tanpa gas dan tanpa mengubah chain.
    data = "0x" + keccak(text="openLong(address,uint256,bytes32,bytes32)")[:4].hex() + \
        enc(["address", "uint256", "bytes32", "bytes32"],
            [asset, Q6, b"\x11" * 32, b"\x22" * 32]).hex()
    try:
        vd.rpc("eth_call", [{"from": addr, "to": vault, "data": data}, "latest"])
        print("  dry-run openLong: DITERIMA (view/simulasi lolos)")
    except Exception as e:  # noqa: BLE001
        print(f"  dry-run openLong REVERT: {str(e)[:160]}")

    spot = int(vd.call(cs(pair), "spotPrice()"), 16) / 1e18
    print(f"\nspot pair = {spot:.4f} quote per asset")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"chainId": vd.CHAIN, "asset": asset, "pair": pair, "vault": vault,
               "quote": QUOTE, "owner_agent": addr,
               "daily_cap_quote_atomic": 5 * Q6, "max_position_quote_atomic": 1 * Q6,
               "deployed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **txs},
              open(OUT, "w", encoding="utf-8"), indent=1, sort_keys=True)
    print(f"tertulis: {os.path.relpath(OUT, ROOT)}")
    print("lanjut: python tools/execute_live.py --open-long   atau   --open-short")


if __name__ == "__main__":
    main()
