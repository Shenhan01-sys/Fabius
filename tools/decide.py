"""Envolve snapshot yang sudah direkam menjadi KEPUTUSAN yang siap di-anchor.

Ini sambungan yang membuat `DecisionAnchor` masuk akal. Kontrak itu mewajibkan dua hal:
  - `snapshotHash` bukan nol  -> diambil dari sha256 snapshot aslinya, dihitung ulang di sini
  - `ABSTAIN` membawa `gatesHash` bukan nol -> dihitung dari daftar gerbang yang menggugurkan

Semua di sini deterministik dan bisa dijalankan ulang oleh orang lain: kami TIDAK membaca
field `vetoes` yang tersimpan di snapshot, melainkan MENGHITUNG ULANG-nya dari angka mentah
(umur, likuiditas, top-10, lock, bundler, holder, vol/liq) memakai ambang yang tersimpan di
dalam snapshot itu sendiri. Bedanya penting: kalau kita memercayai hasil simpanan, snapshot
bukan lagi bukti — cuma memorandum. Kalau dihitung ulang, siapa pun bisa memeriksa bahwa
keputusan ini memang keluar dari data itu, pada ambang itu.

Yang TIDAK dilakukan file ini, dan jangan ditulis seolah-olah dilakukan:
  - tidak ada model bahasa, tidak ada probabilitas, tidak ada klaim "agen memprediksi";
  - tidak ada order, tidak ada dana, tidak ada transaksi — hanya calldata yang dicetak;
  - keputusan ENTER di sini berarti "lolos gerbang deterministik", bukan "bakar duit".

Pakai:
  python tools/decide.py                     satu jendela terbaru, laporan ke layar
  python tools/decide.py --emit              + tulis keputusan ke decisions/decisions-<UTC>.jsonl
  python tools/decide.py --emit --calldata   + cetak calldata anchor() siap tempel
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "universe", "bsc-universe.jsonl")
OUT_DIR = os.path.join(ROOT, "decisions")


def sha256_canon(obj) -> bytes:
    """Sama seperti `record_hash()` HeliQuant & sha256 snapshot: sorted keys, compact."""
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).digest()


def recompute(row, th):
    """Kembalikan (vetoes_risiko, celah_data) - DUA hal berbeda, dan mencampurnya merusak proyek.

    'top10 tidak diukur' bukan penolakan karena token-nya berbahaya; itu tanda bahwa GT dan GMGN
    tidak ketemu untuk baris ini (terukur: 5 dari 40 baris pool punya field perilaku). Kalau
    digabung ke dalam satu daftar 'alasan', maka nanti kita 'mengkalibrasi ambang' di atas angka
    yang sebenarnya mengukur kegagalan penggabungan sumber - persis kelas kesalahan yang kami
    tuduhkan ke catatan proyek lama.
    """
    v, gap = [], []
    base = str(row.get("symbol") or (row.get("name") or "").split("/")[0] or "").strip().upper()
    if base in th["STABLE_BASES"]:
        v.append("not_a_choosable_asset")
    if row.get("is_honeypot") in (1, True, "1", "true"):
        v.append("honeypot")
    if row.get("can_not_sell") in (1, True, "1", "true"):
        v.append("cannot_sell")
    liq, age, vol = row.get("liquidity"), row.get("age_sec"), row.get("volume_24h")
    if liq is None:
        gap.append("liquidity_unmeasured")
    elif liq < th["MIN_LIQ_USD"]:
        v.append("liquidity_below_floor")
    if age is None:
        gap.append("age_unmeasured")
    elif age < th["MIN_AGE_SEC"]:
        v.append("younger_than_validation_window")
    t10 = row.get("top_10_holder_rate")
    if t10 is None:
        gap.append("top10_unmeasured")
    elif t10 > th["MAX_TOP10"]:
        v.append("concentrated_ownership")
    lk = row.get("lock_percent")
    if lk is None:
        gap.append("lock_unmeasured")
    elif lk < th["MIN_LOCK"]:
        v.append("lp_unlockable")
    bd = row.get("bundler_rate")
    if bd is None:
        gap.append("bundler_unmeasured")
    elif bd > th["MAX_BUNDLER"]:
        v.append("bundled_volume")
    hc = row.get("holder_count")
    if hc is None:
        gap.append("holders_unmeasured")
    elif hc < th["MIN_HOLDER"]:
        v.append("too_few_holders")
    if liq and vol is None:
        gap.append("volume_unmeasured")
    elif liq and vol is not None and vol / max(liq, 1.0) < th["MIN_VOL_OVER_LIQ"]:
        v.append("trending_without_demand")
    assert not (set(v) & set(gap)), "satu alasan tidak boleh jadi risiko DAN celah data"
    return v, gap


def latest_window():
    """Ambil SATU baris per jendela jam (yang pertama). Aturan baca dataset, lihat universe/README.md."""
    seen, out = {}, []
    for line in open(DATA, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        if not d.get("schema"):
            continue                     # semantik lama: veto volume tidak jalan -> jangan dipakai
        w = d["epoch"] // 3600
        if w in seen:
            continue
        seen[w] = True
        out.append(d)
    return out[-1] if out else None


def calldata_for(rec) -> str:
    """ABI-encode anchor(string,uint8,bytes32,bytes32,bytes32).

    `eth_abi.encode` sudah menyusun head + offset string secara lengkap, jadi tidak ada
    perhitungan offset manual di sini - kalau manual, itu sumber bug sunyi nomor satu.
    """
    try:
        from eth_abi import encode
        from eth_utils import keccak
    except Exception as e:  # noqa: BLE001
        return f"(eth_abi/eth_utils tidak tersedia: {type(e).__name__} - keputusan tetap sah, calldata dilewati)"
    selector = keccak(b"anchor(string,uint8,bytes32,bytes32,bytes32)")[:4]
    verdict = 0 if rec["verdict"] == "ENTER" else 1
    gates = bytes.fromhex(rec["gatesHash"][2:]) if rec["gatesHash"] else b"\x00" * 32
    body = encode(["string", "uint8", "bytes32", "bytes32", "bytes32"],
                  [rec["asset"], verdict, bytes.fromhex(rec["decisionHash"][2:]),
                   gates, bytes.fromhex(rec["snapshotHash"][2:])])
    return "0x" + selector.hex() + body.hex()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--calldata", action="store_true")
    args = ap.parse_args()

    snap = latest_window()
    if not snap:
        raise SystemExit("belum ada snapshot berskema di universe/ — jalankan universe/record_bsc_universe.py")

    th = dict(snap["thresholds"])
    # daftar terurut, BUKAN set: th ikut di-hash ke dalam gatesHash, dan set tidak bisa diserialisasi
    # ke JSON ( TypeError: Object of type set is not JSON serializable ).
    th["STABLE_BASES"] = ["USDT", "USDC", "BUSD", "FDUSD", "DAI", "TUSD", "USD1", "USDD",
                          "USDE", "BTCB", "WBNB", "BNB", "ETH"]
    snap_hash = snap["sha256"]
    if len(snap_hash) != 66 or not snap_hash.startswith("0x"):
        raise SystemExit("snapshot tidak punya sha256 kanonik — jangan lanjut")

    decisions, enters, unassessed = [], 0, 0
    for row in snap["rows"]:
        asset = str(row.get("symbol") or row.get("name") or "")[:48]
        addr = (row.get("address") or row.get("base_token") or "")
        vetoes, gaps = recompute(row, th)
        # ENTER butuh keduanya kosong: tanpa risiko TERUKUR dan tanpa CELAH DATA.
        assessable = not gaps
        if not assessable:
            unassessed += 1
        verdict = "ENTER" if (assessable and not vetoes) else "ABSTAIN"
        if verdict == "ENTER":
            enters += 1
        reasons = vetoes + [f"gap:{g}" for g in gaps]
        gates_hash = "0x" + sha256_canon({"risk": vetoes, "gaps": gaps, "thresholds": th}).hex()
        record = {
            "asset": asset, "addr": addr, "verdict": verdict, "assessable": assessable,
            "risk_vetoes": vetoes, "data_gaps": gaps,
            "snapshot_utc": snap["snapshot_utc"],
            "engine": "deterministic-veto-v2", "model": None,
        }
        decisions.append({**record, "reasons": reasons,
                          "decisionHash": "0x" + sha256_canon(record).hex(),
                          "gatesHash": gates_hash, "snapshotHash": snap_hash})

    print(f"snapshot  : {snap['snapshot_utc']}  schema={snap['schema']}  universe={snap['universe_size']}")
    print(f"hash      : {snap_hash[:22]}…")
    print(f"keputusan : {len(decisions)}   ENTER={enters}   ABSTAIN={len(decisions) - enters}"
          f"   (dari yang ABSTAIN: {unassessed} sebenarnya TIDAK DINILAI - datanya tidak ada)")

    risk, gap = {}, {}
    for d in decisions:
        for g in d["risk_vetoes"]:
            risk[g] = risk.get(g, 0) + 1
        for g in d["data_gaps"]:
            gap[g] = gap.get(g, 0) + 1
    print("\nA. ditolak karena RISIKO TERUKUR:")
    for k, n in sorted(risk.items(), key=lambda kv: -kv[1]):
        print(f"  {k:32} {n:>3}")
    print("\nB. TIDAK DINILAI karena CELOH DATA (bukan vonis; ini kegagalan penggabungan sumber):")
    for k, n in sorted(gap.items(), key=lambda kv: -kv[1]):
        print(f"  {k:32} {n:>3}")
    hanya_gap = sum(1 for d in decisions if not d["assessable"] and not d["risk_vetoes"])
    print(f"\n  yang gugur HANYA karena data tidak ada (tanpa satu pun alasan risiko): {hanya_gap}")
    if hanya_gap:
        print("  -> kelompok ini TIDAK BOLEH dihitung sebagai 'penolakan yang benar' saat ambang dikalibrasi.")

    siap = [d for d in decisions if d["verdict"] == "ENTER"]
    if siap:
        print("\nkandidat ENTER (lolos gerbang deterministik; BELUM ada model, BELUM ada biaya exit):")
        for d in siap[:8]:
            print(f"  {d['asset'][:26]:26} {d['decisionHash'][:22]}…")
    else:
        print("\nENTER = 0. Hasil yang sah, bukan kegagalan: tidak ada yang lolos semua gerbang TERUKUR.")

    if args.emit:
        os.makedirs(OUT_DIR, exist_ok=True)
        path = os.path.join(OUT_DIR, f"decisions-{snap['snapshot_utc'][:10].replace('-', '')}.jsonl")
        with open(path, "a", encoding="utf-8") as fh:
            for d in decisions:
                fh.write(json.dumps(d, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"\ntertulis: {path}")
        if args.calldata:
            print("\ncalldata anchor() untuk kandidat ENTER:")
            for d in siap[:5]:
                print(f"  {d['asset'][:20]:20} {calldata_for(d)[:150]}")
        else:
            print("(tambahkan --calldata untuk mencetak payload anchor())")

    print(
        "\nBatas: ini lapisan gerbang deterministik. Tidak ada model, tidak ada probabilitas, "
        "tidak ada transaksi yang dikirim. Sebelum anchor nyata, keputusan ini hidup di mesin kita "
        "sendiri — dan itulah bedanya antara jejak audit dan klaim."
    )


if __name__ == "__main__":
    main()
