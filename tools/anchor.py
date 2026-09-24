"""Kirim keputusan YANG SUNGGUHAN dihasilkan (dari decisions/*.jsonl) ke chain 97, lalu baca kembali.

Kenapa file ini ada: `verify_deploy.py` meng-anchor hash ACAR. Itu pengujian kontrak yang sah -
yang diuji adalah "kontrak menerima/menolak sesuai guard". Tapi hash acak tidak bisa ditunjukkan
kepada juri sebagai "prediksi kami sebelum hasilnya ada". Yang di sini melakukan itu: membaca
rekaman `direction`/`enter` dari siklus keputusan, mengirim tiga hash-nya persis seperti adanya,
lalu MEMBACA ULANG dari chain dan membandingkan word per word.

Tiga hal yang sengaja dibuat menyusahkan (karena itu gunanya):
  1. Tidak ada `--yes`. Yang menghentikanmu hanya `--dry-run`. Jadi tidak ada cara diam-diam
     mengirim 30 tx; tiap siklus menulis apa yang dikirim.
  2. Urutan baca-tulis: `anchorCount()` sebelum dan sesudah, dan `getAnchor(id)` sesudah kirim.
     "sukses" tidak hanya dari status tx - status=1 tanpa word yang cocok adalah kegagalan.
  3. Revert dianggap hasil, bukan bencana: `DuplicateDecision` berarti keputusan ini sudah pernah
     masuk chain. Itu dicetak, bukan dilempar, supaya pipeline ulang tidak terlihat merusak jejak.

`side` dipetakan ke enum kontrak: punya arah -> Enter(0); flat/unassessable -> Abstain(1).
Bukan supaya "flat" terlihat seperti kalah, tapi karena kontrak memang hanya punya dua verdict,
dan yang membedakan kualitas keputusan adalah `decisionHash` + isi file aslinya.

Pakai:  python tools/anchor.py --dry-run                  # lihat apa yang AKAN dikirim
         python tools/anchor.py                            # kirim semua baris file terbaru
         python tools/anchor.py --file decisions/direction-20260925.jsonl --only MARSCOINUSDT
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import verify_deploy as vd  # noqa: E402  (rpc/cd/call/send/resolve_anchor/AGENT_GAS sudah di sini)

ANCHOR = "anchor(string,uint8,bytes32,bytes32,bytes32)"
GET_ANCHOR = "getAnchor(bytes32)"
# Word0 retur = offset string (struct mengandung dynamic type), JADI indeks field = word+1.
# Salah geser satu word = membaca offset sebagai `agent` (kesalahan yang sudah terjadi di
# `getAgent` - lihat vault/06).
FIELD_WORDS = ["agent", "verdict", "decisionHash", "gatesHash", "snapshotHash", "anchoredAt"]


def chain_check():
    """Baca chainId dari RPC yang dipakai dan pastikan 97 SEBELUM ada transaksi dikirim.

    Ini bukan seremonial: `send()` menandatangani dengan `chainId` dari config. Kalau config
    salah dan kita tidak memeriksa, tx yang ditandatangani di sini sah di chain LAIN - dan
    anchor "bukti prediksi" kita hilang ke tempat yang tidak kita baca.
    """
    try:
        cid = vd.num(vd.rpc("eth_chainId", []))
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"tidak ada RPC 97 yang membalas ({str(e)[:120]}) - keputusan tetap di "
                         "file lokal, aman: tidak ada yang salah kirim.")
    if cid != vd.CHAIN:
        raise SystemExit(f"RPC {vd.RPC} menjawab chainId={cid}, config bilang {vd.CHAIN} -> "
                         "BERHENTI. Jangan tandatangani tx untuk chain yang tidak dibaca.")
    return vd.RPC


def agent_creds():
    """Kunci agen dari .agent.env (bukan .env). Kalau tidak ada, berhenti dengan alasan."""
    k = {}
    for path in (os.path.join(ROOT, ".agent.env"), os.path.expanduser("~/.config/fabius/agent.env")):
        try:
            for ln in open(path, encoding="utf-8"):
                ln = ln.strip()
                if ln and not ln.startswith("#") and "=" in ln:
                    a, b = ln.split("=", 1)
                    k.setdefault(a.strip(), b.strip())
            if k.get("AGENT_PRIVATE_KEY"):
                return k["AGENT_PRIVATE_KEY"], k.get("AGENT_ADDRESS", "?"), path
        except OSError:
            continue
    raise SystemExit("tidak ada AGENT_PRIVATE_KEY di .agent.env - anchor tidak bisa ditandatangani. "
                     "Kontrak tetap sah, tapi jejak keputusannya berhenti di file lokal.")


def load_rows(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln:
                out.append(json.loads(ln))
    return out


def pick_rows(rows, only=None):
    """Baris terbaru per simbol menang: kalau satu simbol ditulis dua kali dalam sehari, yang
    dikirim yang terakhir - yang pertama sudah dibantah oleh data berikutnya."""
    if only:
        rows = [r for r in rows if r.get("symbol") == only or r.get("asset") == only]
    latest = {}
    for i, r in enumerate(rows):
        key = r.get("symbol") or r.get("asset") or f"row{i}"
        latest[key] = r
    return list(latest.values())


def as_anchor_row(r):
    """Normalkan dua bentuk rekaman (`direction` & `enter`) ke satu bentuk anchor()."""
    if r.get("kind") == "direction":
        d = r.get("decision") or {}
        side = d.get("side") or "flat"
        return {"asset": f"{r['symbol']}@perp",
                "verdict": 0 if side in ("long", "short") else 1,
                "side": side, "regime": d.get("regime"),
                "decisionHash": r["decisionHash"], "gatesHash": r["gatesHash"],
                "snapshotHash": r["snapshotHash"]}
    d = r.get("gates") or r.get("decision") or {}
    return {"asset": r.get("asset") or r.get("symbol") or "?",
            "verdict": 0 if str(r.get("verdict", "")).upper() == "ENTER" else 1,
            "side": r.get("verdict"), "regime": d.get("regime"),
            "decisionHash": r["decisionHash"],
            "gatesHash": r.get("gatesHash") or "0x" + "00" * 32,
            "snapshotHash": r["snapshotHash"]}


def decode_anchor(ret):
    """Retur getAnchor(bytes32) -> dict, dengan geseran offset string ditangani di sini."""
    if not ret or ret == "0x":
        return {"_empty": True}
    b = bytes.fromhex(ret[2:] if ret.startswith("0x") else ret)
    w = [b[i:i + 32] for i in range(0, len(b) // 32 * 32, 32)]
    if len(w) < 8:
        return {"_short": len(w)}
    # w[0]=offset head (0x20), w[1]=agent, w[2]=offset string asset, w[3]=verdict,
    # w[4]=decisionHash, w[5]=gatesHash, w[6]=snapshotHash, w[7]=anchoredAt
    off = int.from_bytes(w[2], "big")
    asset_len = int.from_bytes(b[off:off + 32], "big") if off + 32 <= len(b) else 0
    asset = b[off + 32:off + 32 + asset_len].decode("utf-8", "replace") if asset_len else ""
    return {"agent": "0x" + w[1].hex()[-40:], "verdict": int.from_bytes(w[3], "big"),
            "decisionHash": "0x" + w[4].hex(), "gatesHash": "0x" + w[5].hex(),
            "snapshotHash": "0x" + w[6].hex(), "anchoredAt": int.from_bytes(w[7], "big"),
            "asset": asset, "_words": len(w)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=None, help="rekaman keputusan (default: terbaru di decisions/)")
    ap.add_argument("--only", default=None, help="satu simbol saja")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    cands = ([a.file] if a.file else
             sorted(glob.glob(os.path.join(ROOT, "decisions", "*.jsonl")), key=os.path.getmtime))
    cands = [c for c in cands if c and os.path.exists(c)]
    if not cands:
        raise SystemExit("decisions/ kosong - jalankan tools/direction.py --emit atau tools/decide.py --emit dulu")
    path = cands[-1]
    rows = pick_rows(load_rows(path), a.only)
    if not rows:
        raise SystemExit(f"tidak ada baris yang cocok di {os.path.relpath(path, ROOT)}")
    print(f"sumber : {os.path.relpath(path, ROOT)}  ({len(rows)} baris)")

    pk, agent_addr, src = agent_creds()
    addr = vd.resolve_anchor()
    rpc = chain_check()
    print(f"agen   : {agent_addr}  (kunci dari {os.path.relpath(src, ROOT)})")
    print(f"kontrak: {addr}  chainId={vd.CHAIN}")
    print(f"rpc    : {rpc}\n")
    head0 = vd.num(vd.call(addr, "anchorCount()"))
    print(f"anchorCount() sebelum: {head0}")

    # Gas per anchor terukur 250.639-302.011 (vault/07); plafon per tx = AGENT_GAS. Yang dicek
    # di sini adalah BIAYA TERBURUK, bukan rata-rata: kalau saldo cukup untuk plafon semua baris,
    # tidak ada satupun baris yang mati di tengah siklus meninggalkan jejak setengah.
    if not a.dry_run:
        gp = max(vd.num(vd.rpc("eth_gasPrice", [])), 10**9)
        bal = vd.num(vd.rpc("eth_getBalance", [agent_addr, "latest"]))
        need = len(rows) * vd.AGENT_GAS * gp
        print(f"gas    : {gp/10**9:.2f} gwei | saldo agen {bal/10**18:.6f} tBNB | "
              f"butuh (terburuk) {need/10**18:.6f} tBNB")
        if bal < need:
            raise SystemExit(f"saldo agen tidak cukup untuk {len(rows)} anchor sekaligus "
                             f"(kurang {(need - bal)/10**18:.6f} tBNB). Pakai --only utk satu simbol, "
                             "atau danai ulang lewat _research/make_fabius_burner.py. Tidak ada tx terkirim.")
        print()
    else:
        print()

    print(f"{'asset':22}{'verdict':>9}{'side':>7}{'hasil':>11}{'gas':>9}  id / catatan")
    print("-" * 120)
    ok = 0
    for r in rows:
        q = as_anchor_row(r)
        data = vd.cd(ANCHOR, ("string", "uint8", "bytes32", "bytes32", "bytes32"),
                     (q["asset"], q["verdict"], bytes.fromhex(q["decisionHash"][2:]),
                      bytes.fromhex(q["gatesHash"][2:]), bytes.fromhex(q["snapshotHash"][2:])))
        if a.dry_run:
            print(f"{q['asset']:22}{'ENTER' if q['verdict'] == 0 else 'ABSTAIN':>9}{str(q['side']):>7}"
                  f"{'dry-run':>11}{'-':>9}  dh={q['decisionHash'][:18]}… "
                  f"{len(bytes.fromhex(data[2:]))} byte calldata")
            continue
        try:
            h, st, blk, gu, rec = vd.send(pk, addr, data, gas=vd.AGENT_GAS)
        except Exception as e:  # noqa: BLE001
            print(f"{q['asset']:22}{'-':>9}{str(q['side']):>7}{'KIRIM GAGAL':>11}{'-':>9}  {str(e)[:72]}")
            continue
        if st == 0:
            why = ("out-of-gas (naikkan plafon, ini BUKAN penolakan logika)"
                   if gu >= vd.AGENT_GAS else "revert guard (kemungkinan DuplicateDecision: sudah masuk)")
            print(f"{q['asset']:22}{'-':>9}{str(q['side']):>7}{'DITOLAK':>11}{gu:>9}  {why} tx={h[:16]}…")
            continue
        logs = [l for l in (rec or {}).get("logs", []) if l["address"].lower() == addr.lower()]
        ida = logs[0]["topics"][1] if logs and len(logs[0]["topics"]) > 1 else None
        got = vd.call(addr, GET_ANCHOR, ("bytes32",), (bytes.fromhex(ida[2:]),)) if ida else "0x"
        d = decode_anchor(got)
        match = all(d.get(k) == q[k] for k in ("decisionHash", "gatesHash", "snapshotHash", "verdict"))
        ok += 1 if match else 0
        print(f"{q['asset']:22}{'ENTER' if q['verdict'] == 0 else 'ABSTAIN':>9}{str(q['side']):>7}"
              f"{'TERANCHOR':>11}{gu:>9}  blok={blk} id={ida[:16] if ida else '-'}…  "
              f"chain==lokal: {'YA' if match else 'TIDAK -> ' + json.dumps({k: str(d.get(k))[:20] for k in FIELD_WORDS})[:130]}")

    if a.dry_run:
        print("\ndry-run: tidak ada transaksi yang dikirim.")
        return
    head1 = vd.num(vd.call(addr, "anchorCount()"))
    en = vd.num(vd.call(addr, "countByVerdict(uint8)", ("uint8",), (0,)))
    ab = vd.num(vd.call(addr, "countByVerdict(uint8)", ("uint8",), (1,)))
    print(f"\nanchorCount() {head0} -> {head1} (dikirim {len(rows)}, cocok semua {ok})  |  Enter={en} Abstain={ab}")
    print("Batas: yang terbukti di chain adalah KETERIKATAN dan WAKTU (hash & blok), bukan kebenaran "
          "arahnya. Apakah short 4 jam itu jadi untung baru bisa dibaca setelah horizons lewat - "
          "dan itu tugas ledger.py, bukan tugas file ini.")


if __name__ == "__main__":
    main()
