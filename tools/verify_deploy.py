"""Buktikan DecisionAnchor bekerja di chain 97 - dibaca dari KEADAAN CHAIN, bukan dari log forge.

`forge script` menutup dengan "ONCHAIN EXECUTION COMPLETE & SUCCESSFUL". Itu membuktikan forge
selesai, bukan bahwa produk kita bekerja. Yang boleh masuk README/vault hanya apa yang dibaca
kembali dari chain: kontrak ada, agen mendaftarkan diri, satu keputusan ter-anchor dengan event
ter-indeks, dan REM on-chain benar-benar membuat panggilan agen revert.

Alur, tiap langkah diverifikasi setelah ditulis:
  1. eth_getCode + owner() + anchorCount()
  2. agen = kunci TERSENDIRI (bukan owner), dibiayai 0.002 tBNB dari burner deployer
  3. registerAgent(owner) -> baca AgentRegistered
  4. anchor(ABSTAIN) dari AGEN, dengan snapshotHash = sha256 snapshot NYATA dari bsc-universe.jsonl
     -> baca Anchored (topic1=id, topic2=agen), anchorCount, countByVerdict, getAnchor
  5. setAgentActive(false) -> anchor() agen berikutnya harus REVERT
  6. setAgentActive(true)  -> agen boleh mencatat lagi (remnya bisa dilepas-pasang, bukan mati permanen)

Mengirim TRANSAKSI NYATA ke BSC testnet. Tidak ada mainnet, tidak ada dana sungguhan, tidak ada
order. Kunci dibaca dari .env / .agent.env dan tidak pernah dicetak.

Pakai:  python tools/verify_deploy.py
        ANCHOR_ADDRESS=0x... python tools/verify_deploy.py     # kalau tidak mau baca broadcast/
"""
import glob
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ENV, AGENT_ENV = os.path.join(ROOT, ".env"), os.path.join(ROOT, ".agent.env")
DATA = os.path.join(ROOT, "universe", "bsc-universe.jsonl")

env = {}
for _p in (ENV,):
    try:
        for ln in open(_p, encoding="utf-8", errors="ignore"):
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                env[k.strip()] = v.strip()
    except OSError:
        pass

RPC = env.get("RPC_URL") or "https://data-seed-prebsc-1-s2.binance.org:8545/"
CHAIN = int(env.get("CHAIN_ID") or 97)
AGENT_GAS = 1_000_000   # catatan: 300000 HABIS TERPAKAI persis (out-of-gas), bukan revert logika.
                        # anchor() menulis string + push array + event 2 topic pada storage dingin.
                        # Plafon 1 juta @1 gwei = 0,001 tBNB; agen dibiayai 0,006 -> aman.

from eth_abi import encode                       # noqa: E402
from eth_account import Account                    # noqa: E402
from eth_utils import keccak                       # noqa: E402


def rpc(method, params):
    req = urllib.request.Request(RPC, data=json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
        headers={"Content-Type": "application/json"})
    last = None
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                d = json.loads(r.read().decode())
            if "error" in d:
                raise RuntimeError(str(d["error"])[:220])
            return d["result"]
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3)
    raise RuntimeError(f"RPC {method} gagal 3x: {last}")


def sel(sig):
    return "0x" + keccak(text=sig)[:4].hex()


def cd(sig, types=(), values=()):
    return sel(sig) + (encode(list(types), list(values)).hex() if types else "")


def call(to, sig, types=(), values=()):
    return rpc("eth_call", [{"to": to, "data": cd(sig, types, values)}, "latest"])


def num(hexstr):
    return int(hexstr, 16) if hexstr and hexstr != "0x" else 0


def addr_of(hexstr):
    return "0x" + hexstr[-40:]


def send(pk, to, data, gas=AGENT_GAS, value=0):
    """Kirim + tunggu receipt. Mengembalikan (hash, status, blok, gasUsed, receipt)."""
    from eth_utils import to_checksum_address
    a = Account.from_key(pk)
    # eth-account MENOLAK `to` berupa hex huruf-kecil semua ("Transaction had invalid fields").
    # Alamat kontrak dari broadcast/ datang lowercase, jadi dinormalkan di sini - bukan di tiap
    # pemanggil, supaya tidak ada satu jalur yang lupa dan gagal dengan pesan yang membingungkan.
    tx = {"chainId": CHAIN, "from": a.address, "to": to_checksum_address(to), "value": value,
          "nonce": num(rpc("eth_getTransactionCount", [a.address, "latest"])),
          "gas": gas, "gasPrice": max(num(rpc("eth_gasPrice", [])), 10**9)}
    if data:
        tx["data"] = bytes.fromhex(data[2:])
    s = Account.sign_transaction(tx, pk)
    raw = s.raw_transaction if hasattr(s, "raw_transaction") else s.rawTransaction
    raw = raw if isinstance(raw, str) else "0x" + raw.hex()
    h = rpc("eth_sendRawTransaction", [raw])
    for _ in range(50):
        r = rpc("eth_getTransactionReceipt", [h])
        if r:
            return h, num(r["status"]), num(r["blockNumber"]), num(r["gasUsed"]), r
        time.sleep(2)
    raise RuntimeError(f"tx {h} tidak masuk dalam 100 detik (RPC/mempool?)")


def resolve_anchor():
    a = (os.environ.get("ANCHOR_ADDRESS") or env.get("ANCHOR_ADDRESS") or "").strip()
    if a:
        return a
    files = sorted(glob.glob(os.path.join(ROOT, "broadcast", "**", "run-latest.json"), recursive=True))
    for f in reversed(files):
        br = json.load(open(f, encoding="utf-8"))
        for t in br.get("transactions", []):
            if t.get("contractName") == "DecisionAnchor" and t.get("contractAddress"):
                return t["contractAddress"]
    raise SystemExit("alamat kontrak tidak diketahui: set ANCHOR_ADDRESS atau jalankan deploy dulu")


def latest_snapshot():
    last = None
    for line in open(DATA, encoding="utf-8"):
        line = line.strip()
        if line:
            d = json.loads(line)
            if d.get("schema") and d.get("sha256"):
                last = d
    if not last:
        raise SystemExit("tidak ada snapshot berskema di universe/ - jalankan perekam dulu")
    return last


def ensure_agent(owner_pk):
    ag = {}
    try:
        for ln in open(AGENT_ENV, encoding="utf-8"):
            if "=" in ln:
                k, v = ln.strip().split("=", 1)
                ag[k] = v
    except OSError:
        pass
    if not ag.get("AGENT_PRIVATE_KEY"):
        a = Account.create()
        with open(AGENT_ENV, "w", encoding="utf-8") as fh:
            fh.write("# kunci agen testnet Fabius. jangan commit; jangan cetak.\n")
            fh.write(f"AGENT_ADDRESS={a.address}\nAGENT_PRIVATE_KEY="
                     + (a.key.hex() if isinstance(a.key, str) else "0x" + a.key.hex()) + "\n")
        try:
            os.chmod(AGENT_ENV, 0o600)
        except OSError:
            pass
        ag = {"AGENT_ADDRESS": a.address,
              "AGENT_PRIVATE_KEY": a.key.hex() if isinstance(a.key, str) else "0x" + a.key.hex()}
    pk, addr = ag["AGENT_PRIVATE_KEY"], ag["AGENT_ADDRESS"]
    # hanya top-up kalau saldo benar-benar tidak cukup untuk SATU anchor (~0,0003) - jangan
    # memindahkan seluruh saldo burner tiap kali skrip dijalankan.
    if num(rpc("eth_getBalance", [addr, "latest"])) < 10**15:
        h, st, blk, gu, _ = send(owner_pk, addr, None, gas=21000, value=2 * 10**15)
        print(f"  dana agen     : {h[:16]}… status={st} blok={blk}")
        assert st == 1, "pendanaan agen gagal"
    return pk, addr, num(rpc("eth_getBalance", [addr, "latest"])) / 10**18


def parse_agent(hexstr):
    """Decode retur `getAgent(address) -> Agent` yang BENAR.

    Struct-nya mengandung `string`, jadi returannya ABI dinamis: word0 = OFFSET ke struct (0x20),
    BUKAN handler. Membaca word0 sebagai alamat adalah bug yang membuat "apakah agen sudah
    terdaftar?" selalu menjawab YA (0x20 != 0) - persis yang terjadi pada percobaan pertama,
    yang berakhir dengan anchor() revert karena NotAnAgent.

    Layout struct di memori: [0] handler, [1] offset label, [2] active, [3] registeredAt,
    lalu data label (length + kata-kata).
    """
    h = hexstr[2:] if hexstr.startswith("0x") else hexstr
    w = [h[i:i + 64] for i in range(0, len(h), 64)]
    if len(w) < 2:
        return None
    off = int(w[0], 16) // 32                    # offset BYTE -> indeks word (pernah //2: selalu salah)
    if off + 3 >= len(w):
        return None
    handler = "0x" + w[off][24:]
    lab_off = int(w[off + 1], 16)                # byte offset, relatif ke awal struct
    active = bool(int(w[off + 2], 16))
    reg_at = int(w[off + 3], 16)
    label = ""
    li = off + lab_off // 32                    # byte offset -> indeks word (sama seperti di atas)
    if 0 < li < len(w):
        ln = int(w[li], 16)
        chars = "".join(w[li + 1 + k] for k in range((ln + 31) // 32))
        label = bytes.fromhex(chars[:ln * 2]).decode("utf-8", "replace")
    return {"handler": handler, "active": active, "registeredAt": reg_at, "label": label,
            "retur_words": len(w)}


def main():
    dep_pk = env.get("DEPLOYER_PRIVATE_KEY")
    if not dep_pk:
        raise SystemExit(".env tanpa DEPLOYER_PRIVATE_KEY")
    owner = Account.from_key(dep_pk).address
    addr = resolve_anchor()

    print(f"RPC        : {RPC}  chainId={num(rpc('eth_chainId', []))}")
    print(f"kontrak    : {addr}")
    code = rpc("eth_getCode", [addr, "latest"])
    size = max(0, len(code) // 2 - 1)
    print(f"  bytecode : {size} byte -> {'ADA' if size > 100 else 'KOSONG: tidak ter-deploy'}")
    assert size > 100
    assert addr_of(call(addr, "owner()")).lower() == owner.lower(), "owner bukan deployer"
    print(f"  owner()  : {owner}  (cocok dengan deployer)")
    n0 = num(call(addr, "anchorCount()"))
    print(f"  anchorCount sebelum: {n0}")

    apk, agent, abal = ensure_agent(dep_pk)
    print(f"  agen     : {agent}  {abal:.4f} tBNB  terpisah dari owner: {agent.lower() != owner.lower()}")

    g = parse_agent(call(addr, "getAgent(address)", ("address",), (agent,))) or {}
    print(f"  getAgent() : retur={g.get('retur_words', 0)} word  handler={g.get('handler', '?')} "
          f"aktif={g.get('active')} label={g.get('label')!r}")
    zero = "0x0000000000000000000000000000000000000000"
    if (g.get("handler") or zero).lower() == zero.lower():
        h, st, blk, gu, rec = send(dep_pk, addr,
                                   cd("registerAgent(address,string)", ("address", "string"), (agent, "desk-likuiditas-v1")),
                                   gas=400000)
        print(f"  registerAgent: {h[:16]}… status={st} gas={gu} blok={blk}")
        assert st == 1
    else:
        print("  registerAgent: sudah terdaftar (idempoten)")

    snap = latest_snapshot()
    sh = bytes.fromhex(snap["sha256"][2:])
    dec = bytes.fromhex(("0x" + os.urandom(32).hex())[2:])
    gates = bytes.fromhex(("0x" + os.urandom(32).hex())[2:])
    ANCHOR = "anchor(string,uint8,bytes32,bytes32,bytes32)"
    h, st, blk, gu, rec = send(apk, addr, cd(ANCHOR, ("string", "uint8", "bytes32", "bytes32", "bytes32"),
                                             ("TEST/USDT", 1, dec, gates, sh)), gas=AGENT_GAS)
    print(f"  anchor() dari AGEN: {h[:16]}… status={st} gas={gu} blok={blk}")
    assert st == 1, "anchor dari agen harus sukses saat aktif"
    n1 = num(call(addr, "anchorCount()"))
    ae = num(call(addr, "countByVerdict(uint8)", ("uint8",), (0,)))
    ab = num(call(addr, "countByVerdict(uint8)", ("uint8",), (1,)))
    print(f"  anchorCount: {n0} -> {n1} | Enter={ae} Abstain={ab}")
    logs = [l for l in rec["logs"] if l["address"].lower() == addr.lower()]
    assert logs, "tidak ada event -> indexer tidak akan melihat apa pun"
    t = logs[0]["topics"]
    print(f"  event Anchored: topics={len(t)} topic1(id)={t[1][:14]}… topic2(agen)={'0x' + t[2][-40:]}")
    print(f"    topic2 == agen yang mengirim? {'YA' if addr_of(t[2]).lower() == agent.lower() else 'TIDAK'}")
    got = call(addr, "getAnchor(bytes32)", ("bytes32",), (bytes.fromhex(t[1][2:]),))
    print(f"    getAnchor(id): retur {max(0, len(got)//2 - 1)} byte, "
          f"snapshotHash asli ikut tersimpan: {'YA' if snap['sha256'][2:] in got else 'TIDAK'}")

    h, st, blk, gu, _ = send(dep_pk, addr, cd("setAgentActive(address,bool)", ("address", "bool"), (agent, False)),
                             gas=200000)
    print(f"  REM (revoke): status={st} blok={blk}")
    try:
        h2, st2, _, gu2, _ = send(apk, addr, cd(ANCHOR, ("string", "uint8", "bytes32", "bytes32", "bytes32"),
                                                ("X/Y", 1, dec, gates, sh)), gas=AGENT_GAS)
        print(f"    anchor setelah revoke: status={st2} -> {'REVERT, rem bekerja' if st2 == 0 else 'LOLOS: REM TIDAK BEKERJA'}")
        assert st2 == 0, "setelah dicabut, panggilan agen harus gagal"
    except Exception as e:  # noqa: BLE001
        print(f"    anchor setelah revoke: ditolak -> {str(e)[:110]}")

    h, st, blk, gu, _ = send(dep_pk, addr, cd("setAgentActive(address,bool)", ("address", "bool"), (agent, True)),
                             gas=200000)
    print(f"  relist: status={st}")
    h, st, _, gu, _ = send(apk, addr, cd(ANCHOR, ("string", "uint8", "bytes32", "bytes32", "bytes32"),
                                         ("X/Y", 1, bytes.fromhex(("0x" + os.urandom(32).hex())[2:]),
                                          gates, sh)), gas=AGENT_GAS)
    print(f"  anchor setelah relist: status={st} gas={gu}  -> {'pulih' if st == 1 else 'MASIH MATI'}")
    print(f"\nexplorer : https://testnet.bscscan.com/address/{addr}")
    print(f"tx anchor: https://testnet.bscscan.com/tx/{h}")
    print(f"ANCHOR_ADDRESS={addr}  (salin ke vault/04-Kontrak.md & README)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
