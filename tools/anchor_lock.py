"""Anchor kunci ambang peninjau-bot (`engine/locks/review.lock.json`) ke DecisionAnchor di chain 97, lalu baca kembali.

Kenapa file ini ada: `python -X utf8 -m engine.cli lock` mencetak sidik jari kunci, tetapi sidik jari yang hanya hidup di laptop adalah
pengakuan, bukan bukti pra-registrasi (anchor-before-outcome). `tools/anchor.py` hanya mengirim keputusan dari decisions/*.jsonl; kunci
bukan keputusan perdagangan, jadi alat ini mengirim SATU baris `anchor()` untuk kunci, dengan pemetaan yang dikatakan terang-terangan:

  asset         "FABIUS-LOCK/review-v<N>"   label saja (kontrak hanya menolak string kosong)
  verdict       Abstain (1)                 kontrak cuma punya Enter/Abstain; kunci BUKAN keputusan masuk, dan Enter akan menggelembungkan
                                            hitungan "Enter". Abstain mewajibkan gatesHash; kita punya satu (di bawah)
  decisionHash  lock["sha"]                 sha256 JSON kanonik atas SEMUA angka lolos/gagal; sama dengan yang dicetak `engine.cli lock`
  gatesHash     sha256 JSON kanonik atas params.gerbang (bagian gerbang saja)
  snapshotHash  sha256 JSON kanonik atas SELURUH berkas kunci, termasuk `dikunci` dan `catatan` (mengikat isi berkas, bukan hanya angkanya)

Ketiganya bisa dihitung ulang siapa pun dari berkas yang di-commit; `--verify` melakukannya (nol kunci, nol transaksi). Jam yang berlaku
untuk sebuah kunci = `anchoredAt` (waktu blok) dari baris ini, BUKAN `dikunci` di berkas (itu jam laptop).

Yang TIDAK dibuktikan: bahwa angka-angkanya benar atau teroptimasi. Ia membuktikan angka-angka ini ada, utuh, dan sudah ada sebelum
kandidat luar pertama (urutan waktu), oleh agen yang terdaftar di kontrak.

Keselamatan: DEFAULT = rencana (dry-run, tidak mengirim apa pun). `--send` mengirim satu transaksi dan butuh AGENT_PRIVATE_KEY di
`.agent.env` (alat ini tidak pernah mencetaknya). Idempoten: bila id sudah ada di chain, tidak mengirim lagi. `--verify` tanpa kunci.

Pakai:  python -X utf8 tools/anchor_lock.py            # rencana: hash, id, keadaan chain (tidak mengirim)
        python -X utf8 tools/anchor_lock.py --send     # kirim SATU tx anchor() dari agen, baca ulang, tulis catatan
        python -X utf8 tools/anchor_lock.py --verify   # baca ulang dari chain, bandingkan word per word
        python -X utf8 tools/anchor_lock.py --file engine/locks/history/<berkas>.json --verify    # kunci lama
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # stdout tanpa reconfigure = biarkan apa adanya

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

from engine import locks                       # noqa: E402  (murni: tidak menyentuh jaringan, kunci, atau chain)
from engine.spec import sha0x                  # noqa: E402

VERDICT_ABSTAIN = 1
ANCHORS_DIR = os.path.join(locks.LOCK_DIR, "anchors")
SIG = "anchor(string,uint8,bytes32,bytes32,bytes32)"
TYPES = ("string", "uint8", "bytes32", "bytes32", "bytes32")
FIELDS = ("agent", "asset", "verdict", "decisionHash", "gatesHash", "snapshotHash")


def load_lock(path: str = locks.LOCK_FILE) -> dict:
    """Baca berkas kunci dan tolak yang rusak (sha != sha(params)). Tidak ada tebakan."""
    try:
        with open(path, encoding="utf-8") as f:
            lock = json.load(f)
    except (OSError, ValueError) as e:
        raise SystemExit(f"berkas kunci tidak terbaca: {path} ({e})")
    try:
        ok = sha0x(lock["params"]) == lock["sha"]
    except (KeyError, TypeError):
        ok = False
    if not ok:
        raise SystemExit("berkas kunci RUSAK: sha tidak sama dengan sha(params). Tidak ada yang dikirim.")
    return lock


def plan(lock: dict) -> dict:
    """Pemetaan kunci -> argumen anchor(). Murni dan deterministik; dua orang dari berkas yang sama mendapat tiga hash yang sama."""
    return {"asset": f"FABIUS-LOCK/review-v{lock['params']['v']}", "verdict": VERDICT_ABSTAIN,
            "decisionHash": lock["sha"], "gatesHash": sha0x(lock["params"]["gerbang"]), "snapshotHash": sha0x(lock)}


def record_path(lock: dict) -> str:
    return os.path.join(ANCHORS_DIR, f"{lock['sha'][2:14]}.json")


def _hex32(h: str) -> bytes:
    return bytes.fromhex(h[2:])


def _iso(ts: int) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_chain(an, vd, addr: str, agent: str, p: dict):
    """-> (id, keadaan): 'BELUM' | 'ADA' dengan hasil dekode. Struct nol = belum ada (kontrak tidak menjaga id tak dikenal)."""
    iid = an.expected_id(agent, p["decisionHash"], p["snapshotHash"])
    got = vd.call(addr, an.GET_ANCHOR, ("bytes32",), (_hex32(iid),))
    d = an.decode_anchor(got)
    zeroish = (str(d.get("agent", "")).lower().endswith("0" * 40) and not d.get("asset")
               and int(str(d.get("decisionHash", "0x00")), 16) == 0 and int(str(d.get("snapshotHash", "0x00")), 16) == 0)
    return iid, ("BELUM" if zeroish or d.get("_empty") else "ADA"), d


def _compare(d: dict, p: dict, agent: str) -> list:
    want = dict(p)
    want["agent"] = agent.lower()
    return [f for f in FIELDS if d.get(f) != want[f]]


def main() -> int:
    ap = argparse.ArgumentParser(description="Anchor kunci ambang ke DecisionAnchor (default = rencana, tidak mengirim).")
    ap.add_argument("--file", default=locks.LOCK_FILE, help="berkas kunci (default: engine/locks/review.lock.json)")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--send", action="store_true", help="kirim SATU transaksi anchor() (butuh kunci agen)")
    mode.add_argument("--verify", action="store_true", help="baca ulang dari chain dan bandingkan; nol kunci, nol transaksi")
    a = ap.parse_args()

    lock = load_lock(a.file)
    p = plan(lock)
    st = locks.status() if os.path.abspath(a.file) == os.path.abspath(locks.LOCK_FILE) else {"state": "BERKAS-LAMA"}
    print(f"kunci  : {os.path.relpath(a.file, ROOT)}  dikunci(jam laptop) {lock.get('dikunci')}  status kode {st['state']}")
    print(f"asset  : {p['asset']}   verdict ABSTAIN (pemetaan, bukan abstain dagang)")
    print(f"decisionHash {p['decisionHash']}   (= sha kunci)")
    print(f"gatesHash    {p['gatesHash']}   (params.gerbang)")
    print(f"snapshotHash {p['snapshotHash']}   (seluruh berkas)")

    import anchor as an                        # noqa: E402  tools/anchor.py (impor malas: tes tidak membaca .env)
    vd = an.vd
    addr = vd.resolve_anchor()
    agent = an.agent_address()
    rpc_url = an.chain_check()
    n0 = vd.num(vd.call(addr, "anchorCount()"))
    print(f"kontrak: {addr}  chainId={vd.CHAIN}  rpc {rpc_url}\nagen   : {agent}  anchorCount() = {n0}")
    handler, active, n_agent = an.agent_roster(agent)
    print(f"roster : getAgent() -> handler {handler or '?'} aktif={active} countByAgent={n_agent}  (dijawab kontrak)")
    iid, where, d = _read_chain(an, vd, addr, agent, p)
    print(f"id     : {iid}  -> {'SUDAH di chain' if where == 'ADA' else 'belum di chain'}")

    if a.verify:
        if where == "BELUM":
            print("\nBELUM DI-ANCHOR: tidak ada baris di chain untuk berkas kunci ini. Nol transaksi dikirim.")
            return 1
        diffs = _compare(d, p, agent)
        if diffs:
            print(f"\nBEDA di {diffs}: chain={json.dumps({f: str(d.get(f))[:30] for f in diffs})[:200]}")
            return 1
        print(f"\ncocok word-per-word (agen, asset, verdict, 3 hash) | anchoredAt {d['anchoredAt']} = {_iso(d['anchoredAt'])} (jam yang berlaku)")
        print("Nol transaksi dikirim, nol kunci dipakai.")
        return 0

    if where == "ADA":
        diffs = _compare(d, p, agent)
        print("\nSudah ter-anchor" + (" dan cocok" if not diffs else f" tetapi BEDA di {diffs}") +
              f" | anchoredAt {d.get('anchoredAt')} = {_iso(d['anchoredAt']) if d.get('anchoredAt') else '?'}. Tidak mengirim lagi.")
        return 0 if not diffs else 1
    if not (active and handler and handler.lower() == agent.lower()):
        print("\nBERHENTI: agen tidak terdaftar/aktif di kontrak; anchor() akan revert. Tidak ada tx terkirim.")
        return 2
    if st["state"] != "TERKUNCI":
        print(f"\nBERHENTI: status kunci {st['state']} (parameter kode tidak sama dengan berkas kunci, atau bukan kunci berjalan). Tidak ada tx terkirim.")
        return 2

    data = vd.cd(SIG, TYPES, (p["asset"], p["verdict"], _hex32(p["decisionHash"]), _hex32(p["gatesHash"]), _hex32(p["snapshotHash"])))
    print(f"calldata {len(bytes.fromhex(data[2:]))} byte; plafon gas {vd.AGENT_GAS}")
    if not a.send:
        print("\nDRY-RUN (default): tidak ada yang dikirim. Tambahkan --send untuk mengirim SATU transaksi dari agen di atas.")
        return 0

    pk, _cfg_addr, _src = an.agent_creds()
    from eth_account import Account            # noqa: E402
    if Account.from_key(pk).address.lower() != agent.lower():          # alamat penanda tangan = msg.sender; jangan kirim dari alamat lain
        print("\nBERHENTI: alamat dari kunci di .agent.env tidak sama dengan alamat agen yang terdaftar. Tidak ada tx terkirim.")
        return 2
    gp = max(vd.num(vd.rpc("eth_gasPrice", [])), 10**9)
    bal = vd.num(vd.rpc("eth_getBalance", [agent, "latest"]))
    need = vd.AGENT_GAS * gp
    print(f"gas    : {gp / 10**9:.2f} gwei | saldo agen {bal / 10**18:.6f} tBNB | butuh (terburuk) {need / 10**18:.6f} tBNB")
    if bal < need:
        print("\nBERHENTI: saldo agen tidak cukup untuk plafon gas. Tidak ada tx terkirim.")
        return 2
    try:
        h, status, blk, gu, rec = vd.send(pk, addr, data, gas=vd.AGENT_GAS)
    except Exception as e:  # noqa: BLE001
        print(f"\nKIRIM GAGAL: {str(e)[:160]}")
        return 1
    if status == 0:
        why = "out-of-gas (naikkan plafon; ini BUKAN penolakan logika)" if gu >= vd.AGENT_GAS else "revert guard"
        print(f"\nDITOLAK status=0 gasUsed={gu} {why} tx={h}")
        return 1
    logs = [l for l in (rec or {}).get("logs", []) if l["address"].lower() == addr.lower()]
    ida = logs[0]["topics"][1] if logs and len(logs[0]["topics"]) > 1 else None
    iid2, where2, d2 = _read_chain(an, vd, addr, agent, p)
    diffs = _compare(d2, p, agent) if where2 == "ADA" else ["(tidak terbaca)"]
    match = where2 == "ADA" and not diffs and (ida is None or ida.lower() == iid2.lower())
    n1 = vd.num(vd.call(addr, "anchorCount()"))
    print(f"\ntx {h}\nblok {blk} gasUsed {gu} | anchorCount() {n0} -> {n1} | id event {ida} | readback cocok: {'YA' if match else 'TIDAK ' + str(diffs)}")
    if not match:
        print("PERINGATAN: transaksi masuk tetapi readback tidak cocok word-per-word; catatan TIDAK ditulis. Periksa manual.")
        return 1
    os.makedirs(ANCHORS_DIR, exist_ok=True)
    out = {"v": 1, "lock_sha": lock["sha"], "asset": p["asset"], "verdict": "ABSTAIN", "decisionHash": p["decisionHash"],
           "gatesHash": p["gatesHash"], "snapshotHash": p["snapshotHash"], "id": iid2, "tx": h, "block": blk,
           "anchoredAt": d2["anchoredAt"], "anchoredAt_utc": _iso(d2["anchoredAt"]), "contract": addr, "agent": agent,
           "chainId": vd.CHAIN, "lock_file": os.path.relpath(a.file, ROOT).replace("\\", "/"),
           "catatan": "jam yang berlaku = anchoredAt (waktu blok), bukan `dikunci` di berkas kunci (jam laptop)"}
    path = record_path(lock)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    print(f"catatan: {os.path.relpath(path, ROOT)}  | anchoredAt {d2['anchoredAt']} = {_iso(d2['anchoredAt'])} (jam yang berlaku)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
