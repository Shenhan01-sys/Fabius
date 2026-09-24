"""Uji offline `anchor.decode_anchor()` — tanpa RPC, tanpa kunci, tanpa network.

Kenapa file ini ada: `Anchor` adalah struct yang mengandung `string`, jadi retur
`getAnchor(bytes32)` berupa dinamic struct: head-nya (offset 0x20, agent, offset-string, ...) lalu
tail-nya. Satu word salah geser menghasilkan alamat agen yang terlihat valid tapi salah — persis
kesalahan yang sudah terjadi di `getAgent()` (vault/06 mencatatnya sebagai bug "byte offset vs
word index"). Tipe kesalahan seperti ini tidak kelihatan di layar; yang kelihatan cuma angka yang
tidak masuk akal sesudahnya. Dan memang itu yang terjadi: versi pertama uji ini menangkap offset
string yang dihitung dari awal retur, bukan dari awal struct.

Ini bukan uji kontrak (itu 21 test Foundry di `test/`), ini uji parser kita. Dibuat offline supaya
ia tetap jalan di mesin tanpa RPC, di Actions, dan di laptop yang sedang tidak online.

Pakai:  python tools/test_decode_anchor.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from eth_abi import encode  # noqa: E402

import anchor  # noqa: E402

AGENT = "0x4bb30E3b3bc22082c1935fE3bE7c07448e69c862"
ASSET = "MARSCOINUSDT@perp"
DH = "0x" + "11" * 32
GH = "0x" + "22" * 32
SH = "0x" + "33" * 32
AT = 1790237627


def build(agent=AGENT, asset=ASSET, verdict=0, dh=DH, gh=GH, sh=SH, at=AT):
    """Susun retur persis seperti Solidity menyusun dynamic struct (tuple) satu nilai."""
    body = encode(
        ["(address,string,uint8,bytes32,bytes32,bytes32,uint64)"],
        [(bytes.fromhex(agent[2:]), asset, verdict, bytes.fromhex(dh[2:]),
          bytes.fromhex(gh[2:]), bytes.fromhex(sh[2:]), at)],
    )
    return "0x" + body.hex()


CASES = []


def check(name, got, want):
    ok = got == want
    CASES.append((name, ok, got, want))
    return ok


def main():
    raw = build()
    d = anchor.decode_anchor(raw)
    check("agent dibaca dari word1 (bukan word0 = offset)", d.get("agent").lower(), AGENT.lower())
    check("word0 = offset ke struct (0x20), jadi TIDAK bisa dibaca sebagai alamat",
          "0x" + raw[2:66], "0x" + "0" * 62 + "20")
    check("asset utuh (string di tail)", d.get("asset"), ASSET)
    check("verdict", d.get("verdict"), 0)
    check("decisionHash", d.get("decisionHash"), DH)
    check("gatesHash", d.get("gatesHash"), GH)
    check("snapshotHash", d.get("snapshotHash"), SH)
    check("anchoredAt", d.get("anchoredAt"), AT)

    # asset panjang -> string butuh >1 word; offset harus ikut bergeser, bukan memotong
    long_asset = "1000PEPEUSDT@perp/" + "X" * 70
    dl = anchor.decode_anchor(build(asset=long_asset, verdict=1))
    check("asset 91 byte tidak terpotong", dl.get("asset"), long_asset)
    check("verdict abstain ikut terbaca", dl.get("verdict"), 1)

    # dua anchor berbeda harus menghasilkan decisionHash berbeda (guard anti "selalu word yang sama")
    other = anchor.decode_anchor(build(dh="0x" + "44" * 32))
    check("field bergeser kalau isinya bergeser", other.get("decisionHash"), "0x" + "44" * 32)

    check("retur kosong -> tidak mengarang", anchor.decode_anchor("0x").get("_empty"), True)
    check("retur pendek -> ditandai, bukan dipecah paksa",
          anchor.decode_anchor("0x" + "00" * 96).get("_short"), 3)

    bad = sum(1 for _, ok, _, _ in CASES if not ok)
    for name, ok, got, want in CASES:
        print(f"  {'ok ' if ok else 'GAGAL'} {name}" + ("" if ok else f"  got={str(got)[:60]} want={str(want)[:60]}"))
    print(f"\n{len(CASES) - bad}/{len(CASES)} lolos")
    print("Batas yang harus dibaca bersama hasilnya: yang diuji di sini adalah PARSER kita terhadap"
          " bytes yang kami susun sendiri. Kalau `build()` salah meniru ABI, uji ini tetap hijau"
          " sambil salah - karena itu kecocokan dengan kontrak sungguhan tidak diserahkan ke file"
          " ini, melainkan ke `tools/anchor.py` yang MEMBACA ULANG chain dan mencetak"
          " `chain==lokal: YA/TIDAK` per baris (13 anchor per 25 Sep).")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
