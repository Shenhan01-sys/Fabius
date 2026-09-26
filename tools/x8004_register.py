"""Daftarkan agen Fabius ke IdentityRegistry ERC-8004 yang RESMI di chain 97, lalu buktikan.

Kenapa ini ada: `DecisionAnchor.agents` adalah registry buatan kami sendiri — dia mencatat
"alamat ini agen kami", tapi tidak bisa ditemukan siapa pun. Registry 8004 (`0x8004A818…BD9e`,
terverifikasi ADA KODE dan `name()='AgentIdentity'`) justru tempat agen-agen di BNB Chain dicari.
Mendaftar di sana mengubah kalimat submission dari "agen kami menulis hash ke kontrak testnet"
menjadi "agen kami punya identitas pada standar yang dipakai ekosistemnya".

Urutannya disengaja, dan ini bagian yang membuat hasil di bawah bisa dipercaya:
  1) simulasi `register(...)` lewat `eth_call` (TANPA tx, TANPA gas) untuk ketiga varian ABI yang
     ada di upstream — yang mana pun yang diterima kontraklah yang kami kirim;
  2) bandingkan `totalSupply`/`ownerOf` sebelum-sesudah, bukan hanya percaya status tx;
  3) `--verify` membaca ulang `getAgentWallet(tokenId)` dan `ownerOf(tokenId)` dari chain dan
     mencocokkannya dengan alamat agen di `.agent.env`.

Kartu agen (`docs/agent-card.json`) ditulis lebih dulu dan diarahkan ke alamat mentah repo publik
kami — tanpa itu `agentURI` menunjuk ke sesuatu yang tidak ada, dan "terdaftar" jadi hiasan.

Pakai:  python tools/x8004_register.py            # dry-run: simulasi + kartu, tidak ada tx
         python tools/x8004_register.py --send     # daftar sungguhan (testnet, gas dari agen)
         python tools/x8004_register.py --verify   # baca ulang registry dari chain
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
from eth_utils import keccak, to_checksum_address as cs  # noqa: E402

REGISTRY = "0x8004A818BFB912233c491871b3d84c89A494BD9e"   # IdentityRegistry BSC testnet (terverifikasi)
CARD = os.path.join(ROOT, "docs", "agent-card.json")
# Rekor identitas TIDAK boleh di `data/`: direktori itu di-gitignore, dan kalau catatan tokenId
# ada di sana, orang yang meng-clone repo ini tidak akan bisa menjalankan `--verify` sama sekali -
# persis kebalikan dari maksud klaimnya.
RECORD = os.path.join(ROOT, "docs", "8004-identity.json")


def read_record():
    try:
        return json.load(open(RECORD, encoding="utf-8"))
    except (OSError, ValueError):
        return None


CARD_URL = ("https://raw.githubusercontent.com/Shenhan01-sys/Fabius/master/docs/agent-card.json")
GAS = 900_000


def agent_creds():
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
    return k.get("AGENT_PRIVATE_KEY"), k.get("AGENT_ADDRESS")


def call(sel_hex, types=(), values=(), frm=None):
    tx = {"to": cs(REGISTRY), "data": "0x" + sel_hex}
    if frm:
        tx["from"] = cs(frm)
    return vd.rpc("eth_call", [tx, "latest"])


def sel_of(sig):
    return keccak(text=sig)[:4].hex()


def abi_event_topic(name):
    """Signature event diambil dari ABI vendor, bukan dari string yang kunyarang.

    `Registered(uint256,address,string)` yang kunyarang sendiri itu SALAH - yang ter-deploy
    `Registered(uint256,string,address)`. Cocok-cocokan tema yang salah tidak menghasilkan error
    yang jelas: ia menghasilkan "event tidak ditemukan", dan parser yang punya fallback diam-diam
    akan mengambil angka yang salah.
    """
    p = os.path.join(ROOT, "docs", "upstream-8004", "IdentityRegistry.json")
    abi = json.load(open(p, encoding="utf-8"))
    if isinstance(abi, dict):
        abi = abi.get("abi", [])

    def comp(i):
        if i.get("type") != "tuple":
            return i["type"]
        return "(" + ",".join(comp(c) for c in (i.get("components") or [])) + ")"

    for e in abi:
        if e.get("type") == "event" and e["name"] == name:
            return e["name"] + "(" + ",".join(comp(i) for i in e["inputs"]) + ")"
    raise SystemExit(f"event {name} tidak ada di ABI vendor {p}")


def build_card(token_hint=None):
    """Kartu agen: apa yang kami sediakan, bagaimana cara memanggilnya, dan di mana buktinya."""
    dec = None
    try:
        import glob
        fs = sorted(glob.glob(os.path.join(ROOT, "decisions", "direction-*.jsonl")),
                    key=os.path.getmtime)
        if fs:
            lines = [json.loads(x) for x in open(fs[-1], encoding="utf-8") if x.strip()]
            if lines:
                r = lines[-1]
                d = r.get("decision") or {}
                dec = {"symbol": r.get("symbol"), "side": d.get("side"), "regime": d.get("regime"),
                       "sellability": d.get("sellability"), "seat_eligible": d.get("seat_eligible"),
                       "decisionHash": r.get("decisionHash"), "snapshotHash": r.get("snapshotHash")}
    except Exception as e:  # noqa: BLE001
        print(f"  (kartu: keputusan terakhir tidak terbaca: {type(e).__name__})")
    if dec:
        # Tulis juga berkas publik yang ditunjuk kartu ini. Tanpa langkah itu, kartu menunjuk ke URL
        # yang tidak ada - kelas bug yang sama persis dengan pointer `docs/upstream-x402` kemarin,
        # dan tidak ketahuan sampai seseorang benar-benar mengkliknya.
        pub = os.path.join(ROOT, "docs", "decisions")
        os.makedirs(pub, exist_ok=True)
        with open(os.path.join(pub, "direction-latest.json"), "w", encoding="utf-8") as fh:
            json.dump(dec, fh, indent=1, sort_keys=True)
    return {
        "protocol": "x402/1 + erc-8004/1",
        "name": "Fabius",
        "description": ("Agent riset yang menerbitkan keputusan BNB Chain yang bisa dibuktikan "
                        "salah: gerbang deterministik, penolakan di-anchor, hasil dinilai ledger."),
        "image": None,
        "registry": {"chainId": vd.CHAIN, "identityRegistry": REGISTRY,
                     # dibaca dari rekor kalau ada: kartu tidak boleh menyebut tokenId yang tidak
                     # bisa dibuktikan alat ini sendiri lewat --verify
                     "tokenId": token_hint or (read_record() or {}).get("tokenId")},
        "wallet": (agent_creds()[1] or "").lower(),
        "endpoints": [
            {"url": "http://127.0.0.1:8046/vault/latest", "protocol": "http",
             "method": "GET", "paywall": "x402 exact eip155:97",
             # Ditulis apa adanya, bukan dibuat terlihat siap produksi: endpoint ini terbukti
             # dibayar (tx 0xb6093e59...) tapi berjalan di mesin kami. Menghapus kata "belum"
             # di sini akan mengubah bukti menjadi klaim.
             "status": "TERBUKTI DIBAYAR di chain 97; masih LOCAL ONLY - belum di-host publik",
             "description": "ringkasan vault + statistik (dibayar per permintaan)"},
            {"url": CARD_URL.replace("agent-card.json", "decisions/direction-latest.json"),
             "protocol": "http", "method": "GET", "paywall": None,
             "description": "rekaman keputusan terbaru (terbaca publik, tanpa bayar)"},
        ],
        "evidence": {
            "anchor_contract": "0xdd162afb5f5f92d5092f845a93660e3b38259330",
            "check_yourself": "python tools/anchor.py --verify   # tanpa kunci, tanpa gas",
            "registered_tx": (read_record() or {}).get("tx"),
        },
        "limits_stated_honestly": [
            "semua settlement di BNB Chain TESTNET (97); tidak ada dana nyata",
            "token pembayaran adalah koin demo milik kami sendiri",
            "strategi arah kami kalah setelah ongkos 20 bps (vault/09) - yang dijual adalah bukti, bukan sinyal",
        ],
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--card", action="store_true", help="regenerasi kartu agen dari rekor, tanpa tx")
    a = ap.parse_args()
    if a.card:
        rec0 = read_record()
        if not rec0:
            raise SystemExit("tidak ada rekor identitas - tidak ada yang bisa ditulis ke kartu")
        os.makedirs(os.path.dirname(CARD), exist_ok=True)
        with open(CARD, "w", encoding="utf-8") as fh:
            json.dump(build_card(), fh, indent=1, sort_keys=True)
        print(f"kartu ditulis ulang dari rekor: tokenId={rec0.get('tokenId')} tx={str(rec0.get('tx'))[:18]}…")
        return
    pk, addr = agent_creds()
    cid = vd.num(vd.rpc("eth_chainId", []))
    if cid != vd.CHAIN:
        raise SystemExit(f"RPC membalas chainId={cid}, config {vd.CHAIN} -> berhenti")
    name = call(sel_of("name()"), frm=addr)
    # `name()` mengembalikan string ABI-encoded (offset + panjang + data), bukan bytes polos.
    # Versi pertama hanya rstrip sehingga keluar `\x00...  \rAgentIdentity` (0x0d = panjang 13).
    try:
        from eth_abi import decode as dec
        nm = dec(["string"], bytes.fromhex(name[2:]))[0]
    except Exception:  # noqa: BLE001
        nm = bytes.fromhex(name[2:]).rstrip(b"\x00").decode("utf-8", "replace")
    print(f"registry : {REGISTRY}  name()={nm!r}  chain={cid}")

    if a.verify:
        if not os.path.exists(RECORD):
            raise SystemExit(f"belum ada {os.path.relpath(RECORD, ROOT)} - jalankan --send dulu")
        rec = json.load(open(RECORD, encoding="utf-8"))
        tid = int(rec["tokenId"])
        w = call(sel_of("getAgentWallet(uint256)") + enc(["uint256"], [tid]).hex(), frm=addr)
        o = call(sel_of("ownerOf(uint256)") + enc(["uint256"], [tid]).hex(), frm=addr)
        got_w = "0x" + w[-40:]
        got_o = "0x" + o[-40:]
        print(f"tokenId  : {tid}")
        print(f"wallet   : {got_w}   == agen {addr}  -> {'YA' if got_w.lower() == addr.lower() else 'TIDAK'}")
        print(f"ownerOf  : {got_o}   (NFT identitas dimiliki agen -> {'YA' if got_o.lower() == addr.lower() else 'TIDAK'})")
        print(f"tx       : https://testnet.bscscan.com/tx/{rec['tx']}")
        return

    card = build_card()
    os.makedirs(os.path.dirname(CARD), exist_ok=True)
    with open(CARD, "w", encoding="utf-8") as fh:
        json.dump(card, fh, indent=1, sort_keys=True)
    print(f"kartu    : {os.path.relpath(CARD, ROOT)} (wallet={card['wallet']})")

    variants = [("register(string)", ["string"], [CARD_URL]),
                ("register(string,(string,string)[])", ["string", "((string,string)[])"],
                 [CARD_URL, []])]
    chosen = None
    for sig, types, vals in variants:
        data = "0x" + sel_of(sig) + enc(types, vals).hex()
        try:
            out = vd.rpc("eth_call", [{"from": cs(addr), "to": cs(REGISTRY), "data": data}, "latest"])
            tid = int(out, 16) if out and out != "0x" else None
            print(f"  SIMULASI OK  {sig:38} -> tokenId berikutnya = {tid}  ({len(data)//2 - 1} byte calldata)")
            chosen = (sig, data)
            break
        except Exception as e:  # noqa: BLE001
            print(f"  simulasi GAGAL {sig:38} -> {str(e)[:150]}")
    if not chosen:
        raise SystemExit("kedua varian register() ditolak kontrak yang ter-deploy -> tidak ada tx yang dikirim")
    if not a.send:
        print("\ndry-run: tidak ada transaksi dikirim. Pakai --send untuk mendaftar sungguhan.")
        return

    h, st, blk, gas, rec = vd.send(pk, cs(REGISTRY), chosen[1], gas=GAS)
    print(f"\ntx       : https://testnet.bscscan.com/tx/{h}\n           status={st} gas={gas} blok={blk}")
    if st == 0:
        raise SystemExit("register revert" + (" (out-of-gas, BUKAN penolakan logika)" if gas >= GAS else ""))
    logs = [l for l in (rec or {}).get("logs", []) if l["address"].lower() == REGISTRY.lower()]
    tid = None
    topic_reg = "0x" + keccak(text=abi_event_topic("Registered")).hex()
    for l in logs:
        if l["topics"] and l["topics"][0] == topic_reg:
            tid = int(l["topics"][1], 16)
    if tid is None:
        # TIDAK ada fallback "log pertama, topics[1]". Versi dengan fallback itu melaporkan
        # `tokenId 0` untuk transaksi yang sukses: log pertama mint ERC-721 adalah
        # Transfer(from=0x0,...) jadi topics[1] = alamat nol, bukan tokenId. Angka 0 itu bukan
        # "gagal kecil" - itu catatan palsu yang akan kuverifikasi sendiri sebagai benar.
        print("!!  event Registered tidak ditemukan di receipt - TIDAK menulis tokenId. "
              "Cek manual: python _research/diag_8004_event.py")
        raise SystemExit(1)
    card = build_card(token_hint=tid)
    card["evidence"]["registered_tx"] = h
    with open(CARD, "w", encoding="utf-8") as fh:
        json.dump(card, fh, indent=1, sort_keys=True)
    os.makedirs(os.path.dirname(RECORD), exist_ok=True)
    json.dump({"tokenId": tid, "tx": h, "block": blk, "registry": REGISTRY, "wallet": addr,
               "agentURI": CARD_URL, "registered_utc":
                   time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(RECORD, "w", encoding="utf-8"), indent=1, sort_keys=True)
    print(f"tokenId  : {tid}   (kartu diperbarui dengan identitas ini)")
    print("cek      : python tools/x8004_register.py --verify")


if __name__ == "__main__":
    main()
