"""Eksekusi satu posisi NYATA di chain 97 lewat ExecutionVault, dengan hash keputusan yang NYATA
sudah ter-anchor — lalu baca kembali hasilnya dari event, bukan dari ingatan proses ini.

Kenapa alat ini ada: `exec_deploy.py` menutup dengan pesan "lanjut: python tools/execute_live.py",
tapi berkas itu tidak pernah ada. Klaim "analisisnya dibuktikan dengan trade" berhenti di kalimat
itu. Ini kaki keduanya.

Tiga aturan yang membuat jalur ini berarti, bukan sekadar swap:
  1. `decisionHash`/`snapshotHash` dibaca dari `decisions/*.jsonl` dan **dibuktikan ada di
     `DecisionAnchor`** sebelum order dikirim. Vault sendiri hanya melarang hash nol
     (`NoAnchorHash`) — pemeriksaan "hash ini sungguh-sungguh ter-anchor" hidup di sini, dan itu
     kami sebut apa adanya: ini pagar proses kami, bukan enforced-by-contract.
  2. Harga masuk/keluar datang dari `swapBuy`/`swapSell` pool, dan yang dilaporkan adalah
     `entryPx18`/`exitPx18` dari **event**, bukan angka yang kami hitung sendiri.
  3. Ukuran diambil dari plafon kontrak (`min(maxPositionQuote, dailyCap - spentToday)`), jadi
     kalau plafonnya bocor, yang terlihat ya plafonnya — bukan tool ini menutupinya.

Pakai:
  python -X utf8 tools/execute_live.py --status
  python -X utf8 tools/execute_live.py --open-long --symbol BREWUSDT
  python -X utf8 tools/execute_live.py --close --symbol BREWUSDT
"""
import argparse
import glob
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anchor as an            # noqa: E402  (agent_creds, load_rows, expected_id, resolve_anchor)
import verify_deploy as vd     # noqa: E402  (rpc/call/send + rotasi RPC + User-Agent)

from eth_abi import decode as aby_decode      # noqa: E402
from eth_utils import to_checksum_address      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY = os.path.join(ROOT, "data", "execution", "deploy.json")
TRAIL = os.path.join(ROOT, "decisions", "execution-trail.jsonl")
Q6 = 10**6

OPENED_TOPIC = None  # dihitung dari signature di bawah, bukan disalin dari log orang lain


def cs(x):
    return to_checksum_address(x)


def topic_of(sig):
    from eth_utils import keccak
    return "0x" + keccak(text=sig).hex()


def load_cfg():
    """Rekaman deploy lokal kalau ada; kalau tidak: manifest ter-track `deployments/<chain>.json`.

    Urutannya penting. `data/` di-gitignore, jadi di clone bersih `deploy.json` TIDAK ada - dan
    tanpa fallback ini `--status` menyuruh orang yang cuma mau MEMERIKSA men-deploy ulang kontraknya
    sendiri. Itu persis cara klaim "periksa tanpa meminta apa pun ke kami" gugur di jalur eksekusi.
    """
    c = {}
    if os.path.isfile(DEPLOY):
        c = json.load(open(DEPLOY, encoding="utf-8"))
    if not all(c.get(k) for k in ("asset", "pair", "vault", "quote")):
        m = vd.deployments().get("contracts", {}) or {}
        got = {"vault": m.get("ExecutionVault"), "pair": m.get("DemoPair"),
               "asset": m.get("DemoAsset"), "quote": m.get("DemoPayToken")}
        if all(got.values()):
            if not c:
                print(f"  (sumber alamat: deployments/{vd.CHAIN}.json, bukan "
                      f"{os.path.relpath(DEPLOY, ROOT)})")
            return {**got, **{k: v for k, v in c.items() if k not in got}}
        raise SystemExit(
            f"tidak ada {os.path.relpath(DEPLOY, ROOT)} DAN manifest "
            f"deployments/{vd.CHAIN}.json tidak lengkap ({got}) -> jalankan "
            "`python -X utf8 tools/write_deployment_manifest.py` dari working copy yang punya "
            "rekamannya. Alamat kontrak tidak pernah ditebak.")
    return c


def read_position(vault, asset):
    """openPositionOf() -> (isShort, assetQty, quoteAtEntry, entryPx18, decisionHash, snapshotHash).
    Posisi tak dikenal TIDAK revert; strukturnya nol — jadi yang dicek adalah `assetQty|entryPx18`."""
    raw = vd.call(cs(vault), "openPositionOf(address)", ("address",), (cs(asset),))
    w = aby_decode(["bool", "uint256", "uint256", "uint256", "bytes32", "bytes32"],
                   bytes.fromhex(raw[2:]))
    return {"short": w[0], "assetQty": w[1], "quoteAtEntry": w[2], "entryPx18": w[3],
            "decisionHash": "0x" + w[4].hex(), "snapshotHash": "0x" + w[5].hex()}


def caps(vault):
    return {k: int(vd.call(cs(vault), f"{k}()"), 16)
            for k in ("dailyCap", "maxPositionQuote", "spentToday", "closedCount")}


def pick_decision(symbol):
    """Baris keputusan TERAKHIR untuk simbol itu yang verdict=ENTER, dari berkas direction mana pun."""
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, "decisions", "direction-*.jsonl"))):
        for r in an.load_rows(f):
            d = an.as_anchor_row(r)
            if d["asset"].split("@")[0] == symbol and d["verdict"] == 0:
                d["file"] = os.path.basename(f)
                rows.append(d)
    if not rows:
        raise SystemExit(f"tidak ada keputusan ENTER untuk {symbol} di decisions/ -> "
                         "jalankan `python -X utf8 tools/direction.py --top 5 --emit` dulu")
    return rows[-1]


def require_anchored(dec, agent_addr):
    """Buktikan hash-nya ADA di DecisionAnchor sebelum kita pakai sebagai alas posisi."""
    contract = vd.resolve_anchor()
    aid = an.expected_id(agent_addr, dec["decisionHash"], dec["snapshotHash"])
    raw = vd.call(cs(contract), "getAnchor(bytes32)", ("bytes32",), (bytes.fromhex(aid[2:]),))
    body = raw[2:]
    if len(body) < 192 or set(body[:192]) == {"0"}:
        raise SystemExit(
            f"decisionHash {dec['decisionHash'][:14]}… BEDA/NON-JADI di chain: getAnchor(id={aid[:14]}…) "
            "mengembalikan struct nol.-anchor dulu: `python -X utf8 tools/anchor.py "
            f"--file decisions/{dec['file']} --only {dec['asset']}`\n"
            "     Catatan posisi ini sengaja keras: `ExecutionVault` hanya melarang hash NOL, jadi "
            "kalau kami tidak memeriksanya sendiri, 'dibuktikan dengan trade' bisa dibohongi dengan "
            "hash karangan.")
    return aid


def find_entry(vault, asset):
    """Cari tx `Opened` terakhir untuk (vault, asset) dari trail kami sendiri."""
    if not os.path.isfile(TRAIL):
        return None
    last = None
    for line in open(TRAIL, encoding="utf-8"):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("asset") == asset and r.get("action") == "open":
            last = r
    return last


def write_trail(rec):
    os.makedirs(os.path.dirname(TRAIL), exist_ok=True)
    rec["at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(TRAIL, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def show_status(cfg):
    vault, pair, asset = cfg["vault"], cfg["pair"], cfg["asset"]
    c = caps(vault)
    pos = read_position(vault, asset)
    spot = int(vd.call(cs(pair), "spotPrice()"), 16)
    print(f"vault {vault}\npair  {pair}\nasset {asset}")
    print(f"cap harian {c['dailyCap']/Q6:.2f} | per posisi {c['maxPositionQuote']/Q6:.2f} | "
          f"terpakai hari ini {c['spentToday']/Q6:.2f} | tertutup {c['closedCount']}")
    print(f"spot pool {spot/1e18:.6f} quote/asset")
    if pos["entryPx18"]:
        side = "SHORT" if pos["short"] else "LONG"
        print(f"posisi terbuka: {side} qty {pos['assetQty']/Q6:.4f} masuk "
              f"{pos['quoteAtEntry']/Q6:.4f} @ {pos['entryPx18']/1e18:.6f}")
        print(f"  decisionHash {pos['decisionHash']}\n  snapshotHash {pos['snapshotHash']}")
    else:
        print("posisi terbuka: -")


def main():
    global OPENED_TOPIC
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--open-long", metavar="SYMBOL", default=None)
    ap.add_argument("--open-short", metavar="SYMBOL", default=None)
    ap.add_argument("--close", metavar="SYMBOL", default=None)
    ap.add_argument("--asset-address", default=None,
                    help="adres token yang diperdagangkan (default: dari deploy.json)")
    a = ap.parse_args()
    cfg = load_cfg()
    vault, pair = cfg["vault"], cfg["pair"]
    asset = a.asset_address or cfg["asset"]
    OPENED_TOPIC = topic_of("Opened(address,bool,uint256,uint256,uint256,bytes32,bytes32)")
    closed_topic = topic_of("Closed(address,bool,uint256,uint256,int256,int256,uint256)")

    if a.status or not (a.open_long or a.open_short or a.close):
        show_status(cfg)
        return

    pk, agent_addr, _path = an.agent_creds()
    if agent_addr == "?":
        agent_addr = an.agent_address()   # boleh DIDERIVASI dari kunci, bukan ditebak
    bal = vd.num(vd.rpc("eth_getBalance", [agent_addr, "latest"]))
    gp = max(vd.num(vd.rpc("eth_gasPrice", [])), 10**9)
    need = 2 * vd.AGENT_GAS * gp
    print(f"agen {agent_addr} | saldo {bal/1e18:.6f} tBNB @ {gp/1e9:.1f} gwei")
    if bal < need:
        raise SystemExit(f"  perlu ~{need/1e18:.6f} tBNB untuk 1 tx dengan aman -> top-up dulu. "
                         "TIDAK ada tx yang dikirim.")

    if a.close:
        dec = find_entry(vault, asset) or {}
        symbol = a.close
        pos = read_position(vault, asset)
        if not pos["entryPx18"]:
            raise SystemExit("tidak ada posisi terbuka untuk aset ini -> tidak ada yang ditutup")
        h, st, blk, gu, rec = vd.send(pk, cs(vault),
                                      vd.cd("close(address)", ("address",), (cs(asset),)),
                                      gas=vd.AGENT_GAS)
        print(f"{'OK ' if st == 1 else 'GAGAL'} close  gas {gu:,} blok {blk}\n"
              f"   https://testnet.bscscan.com/tx/{h}")
        for lg in rec["logs"]:
            if lg["topics"][0].lower() == closed_topic.lower():
                v = aby_decode(["bool", "uint256", "uint256", "int256", "int256", "uint256"],
                               bytes.fromhex(lg["data"][2:]))
                side = "short" if v[0] else "long"
                print(f"   Closed: {side} keluar {v[1]/Q6:.4f} @ {v[2]/1e18:.6f} "
                      f"| realized {v[3]/Q6:+.4f} quote = {v[4]:+.1f} bps | gas terpakai {v[5]:,}")
                write_trail({"action": "close", "asset": asset, "symbol": symbol, "tx": h,
                             "status": st, "realized_quote": v[3], "realized_bps": v[4],
                             "gas_units_paid": v[5], "decisionHash": dec.get("decisionHash")})
                return
        print("   (event Closed tidak ditemukan di receipt -> tidak ada angka yang kami karang)")
        write_trail({"action": "close", "asset": asset, "symbol": symbol, "tx": h, "status": st})
        return

    symbol = a.open_long or a.open_short
    short = bool(a.open_short)
    dec = pick_decision(symbol)
    aid = require_anchored(dec, agent_addr)
    c = caps(vault)
    room = max(c["dailyCap"] - c["spentToday"], 0)
    size = min(c["maxPositionQuote"], room)
    if size <= 0:
        raise SystemExit("plafon harian sudah habis -> tidak ada yang boleh dibuka (itu pagar, bukan bug)")
    spot = int(vd.call(cs(pair), "spotPrice()"), 16)
    if short:
        qty = (size * 10**18) // spot
        sig, types, vals = ("openShort(address,uint256,bytes32,bytes32)", ("address", "uint256", "bytes32", "bytes32"),
                            (cs(asset), qty, bytes.fromhex(dec["decisionHash"][2:]),
                             bytes.fromhex(dec["snapshotHash"][2:])))
        print(f"buka SHORT {symbol}: qty {qty/Q6:.4f} (~{size/Q6:.2f} quote) atas anchor {aid[:16]}…")
    else:
        sig, types, vals = ("openLong(address,uint256,bytes32,bytes32)", ("address", "uint256", "bytes32", "bytes32"),
                            (cs(asset), size, bytes.fromhex(dec["decisionHash"][2:]),
                             bytes.fromhex(dec["snapshotHash"][2:])))
        print(f"buka LONG {symbol}: {size/Q6:.2f} quote atas anchor {aid[:16]}…")

    h, st, blk, gu, rec = vd.send(pk, cs(vault), vd.cd(sig, types, vals), gas=vd.AGENT_GAS)
    print(f"{'OK ' if st == 1 else 'GAGAL'}  gas {gu:,} blok {blk}\n   https://testnet.bscscan.com/tx/{h}")
    for lg in rec["logs"]:
        if lg["topics"][0].lower() == OPENED_TOPIC.lower():
            v = aby_decode(["bool", "uint256", "uint256", "uint256", "bytes32", "bytes32"],
                           bytes.fromhex(lg["data"][2:]))
            impact = (v[3] - spot) / spot * 10_000 if spot else 0.0
            print(f"   Opened: {'short' if v[0] else 'long'} qty {v[1]/Q6:.4f} "
                  f"quote {v[2]/Q6:.4f} @ {v[3]/1e18:.6f} | dampak vs spot {impact:+.1f} bps "
                  f"(harga dari pool, bukan dari kami)")
            write_trail({"action": "open", "asset": asset, "symbol": symbol, "tx": h, "status": st,
                         "shortSide": v[0], "assetQty": v[1], "quote": v[2], "entryPx18": v[3],
                         "decisionHash": dec["decisionHash"], "snapshotHash": dec["snapshotHash"],
                         "anchorId": aid, "gas_used": gu})
            return
    print("   (event Opened tidak ditemukan -> posisi tidak kami catat sebagai terbuka)")


if __name__ == "__main__":
    main()
