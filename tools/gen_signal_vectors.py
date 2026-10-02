"""Vektor uji lintas bahasa untuk SignalAnchor (M3): sinyal deterministik dibuat oleh `engine/sinyal.py` -> daun, akar, bukti -> `test/fixtures/signal_vectors.json`.

Tanpa jaringan, tanpa kunci, tanpa acak (salt diturunkan dari benih tetap). Uji Foundry `test/SignalAnchor.t.sol` membaca berkas ini dan memeriksa bahwa kontrak
menghitung daun dan memverifikasi bukti PERSIS sama dengan engine - kalau salah satu sisi berubah, uji di sisi lain gagal.

    python -X utf8 tools/gen_signal_vectors.py            # tulis ulang fixture (deterministik: dua kali jalan = byte sama)
    python -X utf8 tools/gen_signal_vectors.py --check    # gagal (kode 1) bila fixture di repo berbeda dari yang dihasilkan engine sekarang
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from engine import chain                                   # noqa: E402
from engine.series import DAY_MS                           # noqa: E402
from engine.sinyal import SIGNAL_V, Signal, build_batch, iso_close     # noqa: E402
from engine.spec import SPECS, sha0x                       # noqa: E402

OUT = os.path.join(ROOT, "test", "fixtures", "signal_vectors.json")
T_OPEN = 1_790_812_800_000                                  # bar 2026-10-01 (waktu buka, ms UTC)


def salt(i: int) -> bytes:
    return chain.keccak256(b"fabius-signal-vector-salt-" + str(i).encode())


def batch_json(bot_id: str, spec_sha: str, sigs, salts) -> dict:
    b = build_batch(bot_id, spec_sha, T_OPEN, sigs, salts)
    out = []
    for e in b.entries:
        f = e.signal.abi_fields()
        out.append({"v": f[0], "asset": chain.hex0x(f[4]), "aksi": f[5], "bobotLama": f[6], "bobotBaru": f[7], "hargaRef": f[8],
                    "dataHash": chain.hex0x(f[9]), "salt": chain.hex0x(e.salt), "leaf": chain.hex0x(e.leaf),
                    "proof": [chain.hex0x(p) for p in e.proof], "id": e.signal.id()})
    return {"botId": chain.hex0x(chain.ascii32(bot_id)), "specSha": spec_sha, "asof": (T_OPEN + DAY_MS) // 1000,
            "root": chain.hex0x(b.root), "n": len(sigs), "signals": out}


def build() -> dict:
    bot = "B3-CARRY"
    spec_sha = SPECS[bot].sha()
    data_hash = sha0x({"vektor": "signal-anchor-m3", "bar": T_OPEN})
    mk = lambda asset, aksi, a0, a1, px: Signal(SIGNAL_V, bot, spec_sha, T_OPEN, iso_close(T_OPEN), asset, aksi, a0, a1, px, data_hash, {})
    three = [mk("DOTUSDT", "MASUK_LONG", 0.0, 0.0625, 4.1234), mk("ETCUSDT", "MASUK_LONG", 0.0, 0.0625, 17.85),
             mk("BTCUSDT", "MASUK_SHORT", 0.0, -0.125, 84829.6)]
    one = [mk("ETHUSDT", "KELUAR", 0.0625, 0.0, None)]
    return {"_catatan": "dihasilkan tools/gen_signal_vectors.py dari engine/sinyal.py; jangan disunting tangan",
            "tiga": batch_json(bot, spec_sha, three, [salt(i) for i in range(3)]),
            "satu": batch_json(bot, spec_sha, one, [salt(100)])}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = json.dumps(build(), indent=2, sort_keys=True) + "\n"
    if a.check:
        with open(OUT, encoding="utf-8") as f:
            same = f.read().replace("\r\n", "\n") == text
        print("fixture COCOK dengan engine" if same else "fixture BEDA dari engine - jalankan tanpa --check lalu ulangi forge test")
        return 0 if same else 1
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"ditulis {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
