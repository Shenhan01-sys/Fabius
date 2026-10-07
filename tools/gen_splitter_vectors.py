"""Vektor uji lintas bahasa untuk `RevenueSplitter` + `BotRegistry` (P81): `engine/economics.py` + `engine/splitter.py` -> `test/fixtures/splitter_vectors.json`.

Bagian yang dihasilkan PYTHON (diperiksa oleh uji Foundry `test/RevenueSplitter.t.sol` dan `test/BotRegistry.t.sol`):
  split     - `economics.split(amount, issuer_bps)` untuk jumlah 0 .. 2^256-1 dan bps 0 .. 10000 (kontrak harus membayar PERSIS sama)
  share     - `economics.share_change_allowed(old, new)`: kontrak harus menerima / menolak penurunan bagian Fabius persis sama
  skenario  - urutan setor / release / turunkan bagian Fabius; harapan per langkah dihitung model segmen di bawah, yang setiap segmennya dibagi
              `economics.split` (tidak ada aritmetika bagi hasil lain di berkas ini)
  create2   - `splitter.splitter_salt` + `splitter.predict_splitter` untuk masukan tetap (kontrak harus menghitung salt dan alamat yang sama)
Bagian yang dihasilkan FORGE (diperiksa oleh uji Python `engine/tests/test_splitter.py`):
  evm       - alamat klon yang BENAR-BENAR di-deploy `BotRegistry.register` di EVM uji Foundry, dicetak `test_vektor_evm_dicetak` dan dibaca dari
              `forge test --json` (fixture hanya-baca bagi Foundry, jadi Foundry tidak bisa menulisnya sendiri)

Tanpa jaringan, tanpa kunci, tanpa acak. Dua kali jalan = byte sama.

    python -X utf8 tools/gen_splitter_vectors.py            # tulis ulang bagian Python (bagian evm yang ada dipertahankan)
    python -X utf8 tools/gen_splitter_vectors.py --evm      # juga jalankan forge (butuh `forge` di PATH, --offline) dan tulis ulang bagian evm
    python -X utf8 tools/gen_splitter_vectors.py --check    # kode 1 bila bagian Python di repo beda dari engine sekarang atau evm tidak cocok
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from engine import chain, economics, splitter              # noqa: E402

OUT = os.path.join(ROOT, "test", "fixtures", "splitter_vectors.json")
BPS = economics.BPS
EVM_TEST = "test_vektor_evm_dicetak"
EVM_MARK = "VEKTOR_EVM "

# Kode operasi skenario (sama dengan `RevenueSplitterTest._langkah`).
SETOR, RELEASE, RELEASE_ISSUER, RELEASE_FABIUS, TURUN, TURUN_CHECKPOINT = range(6)

AMOUNTS = [0, 1, 2, 3, 7, 9_999, 10_000, 10_001, 12_345, 10**6, 10**18 + 1, 2**128 - 1, (2**256 - 1) // BPS, 2**256 - 1]
ISSUER_BPS = [0, 1, 3_333, 5_000, economics.ISSUER_SHARE_BPS, 9_999, BPS]
SHARE_OLD = [0, 1, 2_500, 3_999, economics.FABIUS_SHARE_BPS, 6_000, BPS]
SHARE_NEW = [0, 1, 2_499, 2_500, 2_501, 3_999, 4_000, 4_001, BPS, BPS + 1]


class SegmentModel:
    """Model rujukan pembukuan satu token di `RevenueSplitter`. Setiap segmen tarif dibagi `economics.split` atas TOTAL segmen itu (kumulatif,
    jadi banyaknya release tidak mengubah hasil). Tarif berubah -> segmen lama ditutup pada checkpoint terakhir (release, atau token yang
    di-checkpoint saat bagian Fabius diturunkan); saldo yang belum di-checkpoint ikut tarif baru."""

    def __init__(self, fabius_bps: int):
        self.fabius_bps = fabius_bps
        self.received = 0
        self.last = 0
        self.seg_start = 0
        self.seg_issuer = 0
        self.seg_bps = None
        self.paid_issuer = 0
        self.paid_fabius = 0

    def checkpoint(self) -> int:
        cur = BPS - self.fabius_bps
        if self.seg_bps is None:
            self.seg_bps = cur
        elif self.seg_bps != cur:
            self.seg_issuer += economics.split(self.last - self.seg_start, self.seg_bps)[0]
            self.seg_start, self.seg_bps = self.last, cur
        self.last = self.received
        issuer_credit = self.seg_issuer + economics.split(self.received - self.seg_start, self.seg_bps)[0]
        assert issuer_credit + (self.received - issuer_credit) == self.received
        return issuer_credit

    def step(self, op: int, value: int) -> None:
        if op == SETOR:
            self.received += value
        elif op in (RELEASE, RELEASE_ISSUER, RELEASE_FABIUS):
            credit = self.checkpoint()
            if op != RELEASE_FABIUS:
                self.paid_issuer = credit
            if op != RELEASE_ISSUER:
                self.paid_fabius = self.received - credit
        elif op in (TURUN, TURUN_CHECKPOINT):
            if not economics.share_change_allowed(self.fabius_bps, value):
                raise ValueError(f"skenario tidak sah: bagian Fabius {self.fabius_bps} -> {value}")
            if op == TURUN_CHECKPOINT:
                self.checkpoint()
            self.fabius_bps = value
        else:
            raise ValueError(f"op tak dikenal {op}")


SCENARIOS = [
    ("rilis_bertahap_sama_dengan_satu_split", economics.FABIUS_SHARE_BPS,
     [(SETOR, 3), (RELEASE, 0), (SETOR, 7), (RELEASE, 0), (SETOR, 1), (SETOR, 2), (RELEASE, 0), (RELEASE, 0), (SETOR, 10**18 + 1), (RELEASE, 0)]),
    ("satu_pihak_dulu", economics.FABIUS_SHARE_BPS,
     [(SETOR, 1_001), (RELEASE_ISSUER, 0), (SETOR, 999), (RELEASE_FABIUS, 0), (SETOR, 5), (RELEASE_ISSUER, 0), (RELEASE, 0)]),
    ("turun_dengan_checkpoint", economics.FABIUS_SHARE_BPS,
     [(SETOR, 1_001), (RELEASE, 0), (SETOR, 333), (TURUN_CHECKPOINT, 2_500), (SETOR, 999), (RELEASE, 0)]),
    ("turun_tanpa_checkpoint", economics.FABIUS_SHARE_BPS,
     [(SETOR, 1_001), (RELEASE, 0), (SETOR, 333), (TURUN, 2_500), (SETOR, 999), (RELEASE, 0)]),
    ("turun_berkali_kali", economics.FABIUS_SHARE_BPS,
     [(SETOR, 10_007), (TURUN_CHECKPOINT, 3_000), (SETOR, 10_007), (TURUN_CHECKPOINT, 0), (SETOR, 10_007), (RELEASE, 0)]),
    ("turun_sebelum_ada_setoran", economics.FABIUS_SHARE_BPS,
     [(TURUN_CHECKPOINT, 1_000), (SETOR, 12_345), (RELEASE, 0)]),
    ("turun_sama_tanpa_perubahan", economics.FABIUS_SHARE_BPS,
     [(SETOR, 9_999), (TURUN, economics.FABIUS_SHARE_BPS), (SETOR, 1), (RELEASE, 0)]),
    ("bot_fabius_sendiri_seratus_persen", BPS,
     [(SETOR, 77_777), (RELEASE, 0)]),
]


def label_addr(label: str) -> str:
    """Alamat tetap untuk vektor: 20 byte terakhir keccak256(label) (seperti `makeAddr` tanpa kunci)."""
    return chain.to_checksum_address(chain.hex0x(chain.keccak256(label.encode())[12:]))


CREATE2_INPUTS = [
    ("registry-a", "implementation-a", "B1-TREND", "penerbit-1", "payout-1", "spec-1"),
    ("registry-a", "implementation-a", "B1-TREND", "penerbit-1", "payout-2", "spec-1"),     # payout lain = alamat lain
    ("registry-a", "implementation-a", "B1-TREND", "penerbit-1", "payout-1", "spec-2"),     # spesifikasi lain = alamat lain
    ("registry-b", "implementation-b", "X7-PENERBIT-LUAR-DUA-PULUH-DUA", "penerbit-2", "penerbit-2", "spec-3"),
]


def build_split() -> dict:
    out = {"amount": [], "issuerBps": [], "issuer": [], "fabius": []}
    for amount in AMOUNTS:
        for bps in ISSUER_BPS:
            issuer, fabius = economics.split(amount, bps)
            assert issuer + fabius == amount
            out["amount"].append(str(amount))
            out["issuerBps"].append(bps)
            out["issuer"].append(str(issuer))
            out["fabius"].append(str(fabius))
    return out


def build_share() -> dict:
    out = {"old": [], "new": [], "allowed": []}
    for old in SHARE_OLD:
        for new in SHARE_NEW:
            out["old"].append(old)
            out["new"].append(new)
            out["allowed"].append(economics.share_change_allowed(old, new))
    return out


def build_scenarios() -> list:
    out = []
    for name, fabius_bps, steps in SCENARIOS:
        m = SegmentModel(fabius_bps)
        sc = {"nama": name, "fabiusBpsAwal": fabius_bps, "op": [], "nilai": [], "issuerTotal": [], "fabiusTotal": []}
        for op, value in steps:
            m.step(op, value)
            sc["op"].append(op)
            sc["nilai"].append(str(value))
            sc["issuerTotal"].append(str(m.paid_issuer))
            sc["fabiusTotal"].append(str(m.paid_fabius))
        out.append(sc)
    return out


def build_create2() -> dict:
    out = {k: [] for k in ("deployer", "implementation", "botIdText", "botId", "issuer", "issuerPayee", "specSha", "salt", "predicted")}
    for reg, impl, bot, iss, pay, spec in CREATE2_INPUTS:
        r, i, s, p = label_addr(reg), label_addr(impl), label_addr(iss), label_addr(pay)
        spec_sha = chain.hex0x(chain.keccak256(spec.encode()))
        out["deployer"].append(r)
        out["implementation"].append(i)
        out["botIdText"].append(bot)
        out["botId"].append(chain.hex0x(splitter.bot_id_bytes(bot)))
        out["issuer"].append(s)
        out["issuerPayee"].append(p)
        out["specSha"].append(spec_sha)
        out["salt"].append(chain.hex0x(splitter.splitter_salt(bot, s, p, spec_sha)))
        out["predicted"].append(splitter.predict_splitter(r, i, bot, s, p, spec_sha))
    return out


def build() -> dict:
    return {"_catatan": "dihasilkan tools/gen_splitter_vectors.py dari engine/economics.py + engine/splitter.py (bagian evm: dari forge); "
                        "jangan disunting tangan",
            "split": build_split(), "share": build_share(), "skenario": build_scenarios(), "create2": build_create2()}


def evm_from_forge() -> dict:
    """Jalankan uji Foundry yang memasang BotRegistry + klon sungguhan dan mencetak vektornya; ambil dari keluaran JSON `forge test`."""
    cmd = ["forge", "test", "--offline", "--json", "--match-contract", "BotRegistryTest", "--match-test", EVM_TEST]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        raise SystemExit(f"forge gagal (kode {p.returncode}): {p.stderr[-2000:] or p.stdout[-2000:]}")
    start = p.stdout.find("{")
    if start < 0:
        raise SystemExit("keluaran forge tidak memuat JSON")
    data = json.loads(p.stdout[start:])
    lines = [ln for suite in data.values() for name, res in suite.get("test_results", {}).items() if name.startswith(EVM_TEST)
             for ln in res.get("decoded_logs", []) if ln.startswith(EVM_MARK)]
    if len(lines) != 1:
        raise SystemExit(f"butuh tepat satu baris '{EVM_MARK.strip()}' dari {EVM_TEST}, dapat {len(lines)}")
    evm = json.loads(lines[0][len(EVM_MARK):])
    evm["_sumber"] = f"forge test --match-test {EVM_TEST} (klon di-deploy BotRegistry.register di EVM uji Foundry)"
    return evm


def evm_problems(evm: dict) -> list:
    """Bandingkan vektor forge dengan prediksi Python (dipakai --check dan tes)."""
    probs = []
    if chain.hex0x(splitter.bot_id_bytes(evm["botIdText"])) != evm["botId"].lower():
        probs.append("botIdText -> bytes32 beda dari botId forge")
    salt = chain.hex0x(splitter.splitter_salt(evm["botIdText"], evm["issuer"], evm["issuerPayee"], evm["specSha"]))
    if salt != evm["salt"].lower():
        probs.append(f"salt Python {salt} != forge {evm['salt']}")
    pred = splitter.predict_splitter(evm["registry"], evm["implementation"], evm["botIdText"], evm["issuer"], evm["issuerPayee"], evm["specSha"])
    if pred.lower() != evm["deployed"].lower():
        probs.append(f"alamat Python {pred} != klon forge {evm['deployed']}")
    return probs


def render(d: dict) -> str:
    return json.dumps(d, indent=2, sort_keys=True) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--evm", action="store_true")
    a = ap.parse_args()
    old = None
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            old = json.load(f)
    data = build()
    if a.check:
        if old is None:
            print("fixture tidak ada - jalankan tanpa --check")
            return 1
        same = {k: v for k, v in old.items() if k != "evm"} == data
        probs = evm_problems(old["evm"]) if "evm" in old else ["bagian evm tidak ada (jalankan dengan --evm)"]
        print("bagian Python COCOK dengan engine" if same else "bagian Python BEDA dari engine - jalankan tanpa --check lalu ulangi forge test")
        print("vektor evm COCOK dengan prediksi Python" if not probs else "vektor evm: " + "; ".join(probs))
        return 0 if same and not probs else 1
    if old and "evm" in old:
        data["evm"] = old["evm"]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:          # bagian Python dulu: uji forge pembuat evm tidak membacanya
        f.write(render(data))
    if a.evm:
        data["evm"] = evm_from_forge()
        probs = evm_problems(data["evm"])
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write(render(data))
        print("vektor evm dari forge: " + ("COCOK dengan prediksi Python" if not probs else "; ".join(probs)))
        if probs:
            return 1
    print(f"ditulis {os.path.relpath(OUT, ROOT)}" + ("" if "evm" in data else " (TANPA bagian evm: jalankan dengan --evm)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
