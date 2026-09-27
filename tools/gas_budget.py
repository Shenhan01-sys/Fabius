"""Berapa harga satu siklus agen dalam gas, dan berapa yang tersisa di dompetnya.

Dipakai untuk menjawab "top-up tBNB itu buat apa": yang dibayar tBNB bukan posisi, tapi GAS dari
transaksi yang membuat analisis bisa diperiksa orang. Angka di bawah dibaca live dari chain 97,
bukan dari perkiraan di komentar. Kunci privat tidak pernah dicetak - hanya alamat dan saldo.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import verify_deploy as vd  # noqa: E402

ENV = os.path.join(vd.ROOT if hasattr(vd, "ROOT") else ".", ".agent.env")


def load_env():
    a = os.environ.get("AGENT_ADDRESS")
    if a:
        return a
    for p in (".agent.env", os.path.join("data", "agent.env")):
        if os.path.isfile(p):
            for line in open(p, encoding="utf-8"):
                if line.strip().startswith("AGENT_ADDRESS="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


addr = load_env()
if not addr:
    sys.exit("AGENT_ADDRESS tidak ketemu (env atau .agent.env) - berhenti, jangan menebak alamatnya")

bal = vd.num(vd.rpc("eth_getBalance", [addr, "latest"]))
gas = vd.num(vd.rpc("eth_gasPrice", []))
head = vd.num(vd.rpc("eth_blockNumber", []))
print(f"agen    : {addr}")
print(f"saldo   : {bal/1e18:.6f} tBNB   (blok {head:,} @ {gas/1e9:.1f} gwei)")
print()
print("satu transaksi, biaya gas kalau plafon penuh terpakai:")
for name, cap, why in [
    ("anchor keputusan", vd.AGENT_GAS, "menulis decisionHash+gatesHash+snapshotHash ke DecisionAnchor"),
    ("openLong / close", 400_000, "eksekusi posisi demo lewat vault (plafon kirim verifikasinya)"),
    ("deploy 1 kontrak", 6_000_000, "DemoAsset / DemoPair / ExecutionVault, masing-masing sekali"),
    ("register 8004", 900_000, "IDENTITAS AGEN - terukur 200.844 gas nyata untuk register(string)"),
]:
    c = cap * gas / 1e18
    print(f"  {name:18} cap {cap:>9,}  ~{c:.6f} tBNB   <- {why}")
print()
need_anchor, need_exec = 20 * vd.AGENT_GAS * gas, 4 * 400_000 * gas
deploy = 3 * 6_000_000 * gas
for label, x in [("1 siklus eksekusi (deploy 3 kontrak)", deploy),
                 ("4 panggilan vault (buka+tutup 2 posisi)", need_exec),
                 ("20 anchor berikutnya", need_anchor),
                 ("TOTAL jalur P1 + trail 20 keputusan", deploy + need_exec + need_anchor)]:
    bar = "cukup" if bal >= x else "KURANG"
    print(f"  {label:42} {x/1e18:.6f} tBNB  -> {bar}")
