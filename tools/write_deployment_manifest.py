"""Tulis `deployments/<chainId>.json` — daftar alamat yang dibutuhkan orang yang MEMERIKSA kami.

Kenapa: `resolve_anchor()` hanya tahu alamat dari env atau `data/broadcast/*.json`, dan `data/`
di-gitignore. Artinya kloning bersih tidak bisa menjalankan `tools/anchor.py --verify` - padahal
kalimat itulah klaim utama vault ini ("siapa pun bisa memeriksa tanpa meminta apa pun ke kami").
Alamat kontrak itu PUBUK (ada di explorer), jadi menyimpannya di repo tidak membocorkan apa pun;
yang tidak disimpan di repo justru kemampuan orang lain untuk memulainya.

Isi manifesto dibangun dari berkas rekaman yang ada di disk + dibaca ulang dari chain - bukan
ditulis tangan, karena alamat yang diketik ulang adalah kelas bug yang sudah pernah kami bayar
(`from_hex('0x…')` tidak error, hanya tidak pernah cocok).

    python -X utf8 tools/write_deployment_manifest.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import verify_deploy as vd  # noqa: E402

from eth_utils import to_checksum_address  # noqa: E402

OUT_DIR = os.path.join(ROOT, "deployments")
X402_PROXY = "0x402085c248EeA27D92E8b30b2C58ed07f9E20001"      # kanonis, dari docs/upstream-x402
PERMIT2 = "0x000000000022D473030F116dDEE9F6B43aC78BA3"          # kanonis
IDENTITY_REGISTRY = "0x8004A818BFB912233c491871b3d84c89A494BD9e"  # ERC-8004 di 97


def read_json(path):
    if not os.path.isfile(path):
        return None
    try:
        return json.load(open(path, encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def has_code(addr):
    """Beda 'alamat salah' dengan 'kontrak memang belum ada': baca bytecodenya."""
    try:
        c = vd.rpc("eth_getCode", [to_checksum_address(addr), "latest"])
    except Exception:  # noqa: BLE001
        return None
    return (len(c) - 2) // 2


def main():
    if vd.CHAIN != 97:
        raise SystemExit(f"CHAIN={vd.CHAIN}; manifest ini untuk jalur testnet 97 dulu")
    cid = vd.num(vd.rpc("eth_chainId", []))
    if cid != vd.CHAIN:
        raise SystemExit(f"RPC membalas chainId={cid}, config {vd.CHAIN} -> berhenti")

    anchor = x402 = ex = None
    try:
        anchor = vd.resolve_anchor()
    except SystemExit:
        pass
    x402 = read_json(os.path.join(ROOT, "data", "x402", "deploy.json"))
    ex = read_json(os.path.join(ROOT, "data", "execution", "deploy.json"))
    if not (anchor and ex):
        raise SystemExit("butuh anchor + data/execution/deploy.json. Yang tidak ada TIDAK ditulis "
                         "sebagai 'nanti diisi manual' - manifest yang sebagian lebih berbahaya dari kosong.")

    m = {
        "chainId": vd.CHAIN,
        "written_utc": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()),
        "why": "dibutuhkan agar `tools/anchor.py --verify` dan `tools/execute_live.py --status` "
               "bisa dijalankan dari clone bersih; alamat ini juga terbaca publik di explorer",
        "contracts": {},
        "verification": {},
    }
    for label, addr in [("DecisionAnchor", anchor),
                        ("ExecutionVault", ex["vault"]), ("DemoPair", ex["pair"]),
                        ("DemoAsset", ex["asset"]), ("DemoPayToken", (x402 or {}).get("token")),
                        ("x402ExactPermit2Proxy", X402_PROXY), ("Permit2", PERMIT2),
                        ("ERC8004IdentityRegistry", IDENTITY_REGISTRY)]:
        if not addr:
            print(f"  ! {label}: tidak ada rekamannya -> dilewati dari manifest")
            continue
        size = has_code(addr)
        m["contracts"][label] = to_checksum_address(addr)
        m["verification"][label] = ("bytecode %d B" % size) if size else ("KOSONG" if size == 0 else "GAGAL BACA")
        print(f"  {label:24} {m['contracts'][label]}  {m['verification'][label]}")
    m["agent"] = to_checksum_address(__import__("anchor").agent_address())
    m["execution_state"] = {"daily_cap_quote_atomic": ex.get("daily_cap_quote_atomic"),
                            "max_position_quote_atomic": ex.get("max_position_quote_atomic")}

    os.makedirs(OUT_DIR, exist_ok=True)
    p = os.path.join(OUT_DIR, f"{vd.CHAIN}.json")
    json.dump(m, open(p, "w", encoding="utf-8"), indent=1, sort_keys=True)
    print(f"\ntertulis: deployments/{vd.CHAIN}.json  ({len(m['contracts'])} kontrak, "
          "bytecode-nya sudah dicek dari chain)")


if __name__ == "__main__":
    main()
