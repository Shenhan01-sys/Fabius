"""Baca split verdict langsung dari DecisionAnchor di 97 (read-only, nol gas, nol kunci).

Alasannya ada di vault: angka 14/17 pernah kutulis dari ingatan sesi, dan vault ini melarang itu.
Yang dihitung: anchorCount(), countByVerdict(Enter), countByVerdict(Abstain), plus total dari event.
"""
import json
import urllib.request

RPC = "https://bsc-testnet.publicnode.com"
CONTRACT = "0xdd162afb5f5f92d5092f845a93660e3b38259330"
# enum Verdict { Enter, Abstain } -> di ABI jadi uint8
SELS = {
    "anchorCount": "0x0aa80ff9",   # dihitung di bawah, ini fallback kalau salah
    "countByVerdict(uint8)": None,
}


def sel(sig):
    from eth_utils import keccak
    return "0x" + keccak(text=sig)[:4].hex()


def call(data):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                       "params": [{"to": CONTRACT, "data": data}, "latest"]}).encode()
    req = urllib.request.Request(RPC, data=body, headers={
        "Content-Type": "application/json", "User-Agent": "fabius-vault/1.0"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())["result"]


print("selector anchorCount()      =", sel("anchorCount()"))
print("selector countByVerdict(u8) =", sel("countByVerdict(uint8)"))
n = int(call(sel("anchorCount()")), 16)
enter = int(call(sel("countByVerdict(uint8)") + "0" * 63 + "0"), 16)
abst = int(call(sel("countByVerdict(uint8)") + "0" * 63 + "1"), 16)
print(f"anchorCount()        = {n}")
print(f"countByVerdict(0=Enter)   = {enter}")
print(f"countByVerdict(1=Abstain) = {abst}")
print(f"enter + abstain = {enter + abst}  (harus == anchorCount kalau tidak ada verdict lain)")
