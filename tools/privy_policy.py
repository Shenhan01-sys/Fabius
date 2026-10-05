"""Policy Privy untuk session signer fabius-bot1 (P148, F-D103 #3): kunci bot HANYA boleh menandatangani pembayaran FAB lewat Permit2 ke gerbang
x402 di chain 97, paling banyak 1 FAB (= harga puncak tabel terkunci `engine/harga.py`). Ditegakkan di enclave Privy, bukan hanya oleh kode gerbang:
kalau kunci bot bocor, yang bisa ditandatangani tetap hanya pembayaran FAB ke payTo gerbang.

Dua aturan ALLOW untuk `eth_signTypedData_v4` (apa pun yang tidak cocok = ditolak Privy):
  1. Permit2 witness: domain verifyingContract = Permit2, chainId 97; message spender = proxy x402, witness.to = payTo gerbang,
     permitted.token = FAB, permitted.amount <= 1 FAB.
  2. EIP-2612 FAB: domain verifyingContract = FAB, chainId 97; message spender = Permit2, value <= 1 FAB.

    railway run --service fabius-x402 python -X utf8 tools/privy_policy.py buat              # buat policy, cetak id (tanpa rahasia)
    railway run --service fabius-x402 python -X utf8 tools/privy_policy.py uji <policy_id>   # dompet server uji + 6 kasus tanda tangan
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import privy_server as pv                                           # noqa: E402

PERMIT2 = "0x000000000022D473030F116dDEE9F6B43aC78BA3"
PROXY = "0x402085c248EeA27D92E8b30b2C58ed07f9E20001"
BATAS = 1_000_000                                                   # 1 FAB (6 desimal) = HargaParams.puncak


def _varian(a: str) -> list:
    """Alamat dalam semua bentuk yang mungkin dikirim (huruf kecil + checksum) - perbandingan Privy tidak dijamin tak peka huruf."""
    try:
        from eth_utils import to_checksum_address
        cs = to_checksum_address(a)
    except ImportError:
        cs = a
    return sorted({a, a.lower(), cs})


def policy_body(token: str, pay_to: str, chain_id: int = 97, batas: int = BATAS) -> dict:
    """Peta `types` disalin PERSIS dari `x402_sinyal.typed_pair` (yang dikirim gerbang ke Privy): syarat `ethereum_typed_data_message` hanya dinilai
    bila `types` policy = `types` permintaan, termasuk EIP712Domain dan urutan field (dok Privy; tidak cocok = syarat false = ditolak)."""
    import x402_sinyal as xs
    p2, e2612, _ = xs.typed_pair(token, 1, pay_to, "0x" + "00" * 20, 0, 0, 0, chain_id)
    dom = lambda f, op, v: {"field_source": "ethereum_typed_data_domain", "field": f, "operator": op, "value": v}     # noqa: E731

    def msg(td: dict, f: str, op: str, v):
        return {"field_source": "ethereum_typed_data_message", "typed_data": {"types": td["types"], "primary_type": td["primaryType"]},
                "field": f, "operator": op, "value": v}
    return {"version": "1.0", "name": "fabius-bot1: FAB x402 only", "chain_type": "ethereum", "rules": [
        {"name": "Permit2 witness FAB to gate", "method": "eth_signTypedData_v4", "action": "ALLOW", "conditions": [
            dom("verifyingContract", "in", _varian(PERMIT2)), dom("chainId", "eq", str(chain_id)),
            msg(p2, "spender", "in", _varian(PROXY)), msg(p2, "witness.to", "in", _varian(pay_to)),
            msg(p2, "permitted.token", "in", _varian(token)), msg(p2, "permitted.amount", "lte", str(batas))]},
        {"name": "EIP-2612 FAB to Permit2", "method": "eth_signTypedData_v4", "action": "ALLOW", "conditions": [
            dom("verifyingContract", "in", _varian(token)), dom("chainId", "eq", str(chain_id)),
            msg(e2612, "spender", "in", _varian(PERMIT2)), msg(e2612, "value", "lte", str(batas))]},
    ]}


def _cfg() -> dict:
    with open(os.path.join(os.path.dirname(HERE), "deployments", "97.json"), encoding="utf-8") as f:
        d = json.load(f)["x402_sinyal"]
    return {"token": d["token"], "pay_to": d["facilitator"]}


def _privy() -> pv.Privy:
    return pv.Privy(os.environ["PRIVY_APP_ID"], os.environ["PRIVY_APP_SECRET"], os.environ.get("PRIVY_AUTH_PRIVATE_KEY"))


def cmd_buat(a) -> int:
    c = _cfg()
    p = _privy().create_policy(policy_body(c["token"], c["pay_to"]))
    print(f"policy {p['id']} | aturan {[r.get('name') for r in p.get('rules', [])]}")
    return 0


def cmd_uji(a) -> int:
    import secrets
    import x402_sinyal as xs
    c, pr = _cfg(), _privy()
    w = pr.create_wallet([a.policy_id], os.environ["PRIVY_KEY_QUORUM_ID"])
    print(f"dompet uji {w['id']} {w['address']} (kosong, testnet; pemilik = key quorum bot)")
    now = int(time.time())
    p2, e2612, _ = xs.typed_pair(c["token"], 10_000, c["pay_to"], w["address"], 0, now, int.from_bytes(secrets.token_bytes(16), "big"))
    cur = lambda o: json.loads(json.dumps(o))                                                                # noqa: E731
    kasus = [("Permit2 sah 0,01 FAB ke gerbang", p2, True), ("EIP-2612 sah", e2612, True)]
    x = cur(p2); x["message"]["witness"]["to"] = "0x" + "66" * 20; kasus.append(("Permit2 ke alamat lain", x, False))
    x = cur(p2); x["message"]["permitted"]["amount"] = str(BATAS + 1); kasus.append(("Permit2 di atas 1 FAB", x, False))
    x = cur(e2612); x["message"]["spender"] = "0x" + "66" * 20; kasus.append(("EIP-2612 spender lain", x, False))
    x = cur(e2612); x["domain"]["chainId"] = 56; kasus.append(("EIP-2612 chain 56", x, False))
    gagal = 0
    for nama, td, harap in kasus:
        try:
            pr.sign_typed_data(w["id"], td)
            hasil = True
        except pv.PrivyError as e:
            hasil = False
            why = str(e)[:120]
        cocok = hasil == harap
        gagal += not cocok
        print(f"  {'OK ' if cocok else 'SALAH'} {nama}: {'ditandatangani' if hasil else 'DITOLAK (' + why + ')'}")
    print(f"RINGKAS uji policy: {len(kasus) - gagal}/{len(kasus)} sesuai harapan")
    return 1 if gagal else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Policy Privy kunci bot fabius-bot1 (P148).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("buat")
    u = sub.add_parser("uji")
    u.add_argument("policy_id")
    a = ap.parse_args()
    return {"buat": cmd_buat, "uji": cmd_uji}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
