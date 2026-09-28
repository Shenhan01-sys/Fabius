"""Sumber harga ketiga: harga PERISTIWA transaksi (`tx.t`,`tx.p`) - umur = 0, dan satu ukuran di kedua ujung.

Kenapa ini perlu (terukur 28 Sep): `px` = harga transaksi terakhir yang di-stamp waktu tarikan, jadi
"harga <= 10 menit" yang kita jamin sebenarnya "kita lihat <= 10 menit" - umur aslinya median 8,7
menit, p90 42 menit, dan 71,7 % barisnya hanya pengulangan nilai. Baris `tx` sudah membawa
(t, price) untuk SETIAP transaksi, jadi deret yang dibangun darinya punya harga pada saat ia terjadi.

Aturan yang berlaku tetap sama persis: harga masuk = nilai terakhir dengan stempel <= t (boleh
transaksi itu sendiri - itulah harga yang bisa kita dapat), harga keluar = median nilai pada
[t+H-15m, t+H+15m], kedua ujung WAJIB dari sumber yang sama.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import flow_cluster_test as FC  # noqa: E402

FLOW = os.path.join(ROOT, "universe", "wallet-flow.jsonl")
SRC_TX = "txevent"


def load_tx_series(path=FLOW):
    """[(t, p)] per token dari baris transaksi (sisi apa pun), dilebur per stempel."""
    raw = {}
    n = 0
    for ln in io.open(path, encoding="utf-8", errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("k") not in ("tx", "txc"):
            continue
        tk = str(d.get("tk") or "").lower()
        t = int(d.get("t") or 0)
        p = float(d.get("p") or 0.0)
        if tk and t and p > 0:
            raw.setdefault(tk, []).append((t, p))
            n += 1
    out, merged = {}, 0
    for tk, s in raw.items():
        s.sort(key=lambda r: r[0])
        ded = FC.dedupe_px(s)
        merged += len(s) - len(ded)
        out[tk] = ded
    return {"rows": out, "n_row": n, "merged": merged}


def self_test():
    now = 1000
    s = FC.dedupe_px([(0, 2.0), (0, 4.0), (60, 3.0)])
    assert s == [(0, 3.0), (60, 3.0)], s
    tmp = os.path.join(ROOT, ".qwen", "tmp_tx_probe.jsonl")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"k": "tx", "tk": "0xA", "t": 10, "p": 1.5, "b": 1}) + "\n")
        f.write(json.dumps({"k": "tx", "tk": "0xa", "t": 20, "p": 1.7, "b": 0}) + "\n")
        f.write(json.dumps({"k": "px", "tk": "0xa", "t": 30, "p": 9.9}) + "\n")
        f.write(json.dumps({"k": "tx", "tk": "0xb", "t": 40, "p": 0}) + "\n")
    got = load_tx_series(tmp)
    os.remove(tmp)
    assert list(got["rows"]) == ["0xa"], got["rows"]
    assert got["rows"]["0xa"] == [(10, 1.5), (20, 1.7)], got["rows"]["0xa"]
    assert got["n_row"] == 2, got
    print("self-test txevent OK: 2 titik, baris px diabaikan, harga 0 ditolak")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        d = load_tx_series()
        ts = [t for s in d["rows"].values() for t, _ in s]
        print("txevent: baris=%d token=%d dilebur=%d titik=%d rentang=%.2f jam"
              % (d["n_row"], len(d["rows"]), d["merged"], len(ts),
                 (max(ts) - min(ts)) / 3600.0))
