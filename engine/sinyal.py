"""Sinyal = NIAT (intent), bukan order: apa yang berubah pada target sebuah bot setelah satu bar tertutup.

Cakupan sinyal (keputusan builder 2 Okt 2026: "yang penting open posisi"): niat posisi saja - masuk long/short, keluar, atau
menyesuaikan ukuran posisi yang ada. Bukan jenis order, bukan saran leverage, bukan perintah eksekusi.

Skema komit (keputusan 2 Okt 2026, diterapkan di sini): satu sinyal = struct statis ABI
    (uint8 v, bytes32 botId, bytes32 specSha, uint64 asof, bytes32 asset, uint8 aksi,
     int256 bobotLama, int256 bobotBaru, uint256 hargaRef, bytes32 dataHash)
  - `id()`    = keccak256(abi.encode(struct))            - sidik jari sinyal, tanpa salt;
  - `leaf()`  = keccak256(abi.encode(struct, salt))      - daun komit-ungkap; tanpa salt isi sinyal tak bisa ditebak;
  - `Batch`   = akar Merkle (cocok dengan OpenZeppelin `MerkleProof`) atas semua daun satu bot pada satu bar; HANYA akar yang
                masuk chain. Pembeli menerima muatan + salt + bukti dan memeriksanya sendiri terhadap akar itu.
  Akar nol = "bot diam pada bar ini" yang dikomit (bukan bot yang melewatkan hari).
  Bobot disimpan x1e-9, harga referensi x1e-8 (0 = tak ada); keduanya dikuantisasi SEKALI saat sinyal dibuat supaya JSON dan
  struct selalu menghasilkan bilangan bulat yang sama. `meta` hanya informasi (tidak ikut hash).
  `spec_sha` dan `data_hash` tetap sha256 JSON kanonik (paritas dengan `tools/direction.py`); di dalam struct keduanya cuma bytes32.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional, Sequence, Tuple

from . import chain
from .bots import REGISTRY
from .data import MarketData
from .freshness import StaleBars
from .series import DAY_MS
from .spec import BotSpec, sha0x
from .target import Target

SIGNAL_V = 1
EPS = 1e-9
ACTION_CODE = {"MASUK_LONG": 1, "MASUK_SHORT": 2, "KELUAR": 3, "UBAH_BOBOT": 4}
WEIGHT_DP = 9
PRICE_DP = 8
STRUCT_TYPES = ("uint8", "bytes32", "bytes32", "uint64", "bytes32", "uint8", "int256", "int256", "uint256", "bytes32")


def quantize(x: Optional[float], dp: int) -> Optional[float]:
    """Pembulatan desimal tepat (HALF_EVEN pada repr terpendek) - tanpa galat perkalian float."""
    return None if x is None else float(round(Decimal(repr(float(x))), dp))


def _scaled_int(x: Optional[float], dp: int) -> int:
    return 0 if x is None else int(Decimal(repr(float(x))).scaleb(dp).to_integral_value())


@dataclass(frozen=True)
class Signal:
    v: int
    bot_id: str
    spec_sha: str
    t: int                       # waktu buka bar terakhir yang tertutup (ms UTC)
    asof_utc: str                # saat bar itu tertutup (ISO UTC) = saat sinyal sah
    asset: str
    aksi: str                    # MASUK_LONG | MASUK_SHORT | KELUAR | UBAH_BOBOT
    bobot_lama: float
    bobot_baru: float
    harga_ref: Optional[float]   # penutupan bar itu (referensi, BUKAN harga isi)
    data_hash: str
    meta: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"v": self.v, "bot_id": self.bot_id, "spec_sha": self.spec_sha, "t": self.t, "asof_utc": self.asof_utc,
                "asset": self.asset, "aksi": self.aksi, "bobot_lama": self.bobot_lama, "bobot_baru": self.bobot_baru,
                "harga_ref": self.harga_ref, "data_hash": self.data_hash, "meta": self.meta}

    @classmethod
    def from_dict(cls, d: dict) -> "Signal":
        return cls(int(d["v"]), d["bot_id"], d["spec_sha"], int(d["t"]), d["asof_utc"], d["asset"], d["aksi"],
                   float(d["bobot_lama"]), float(d["bobot_baru"]), None if d.get("harga_ref") is None else float(d["harga_ref"]),
                   d["data_hash"], dict(d.get("meta") or {}))

    def asof(self) -> int:
        """Detik Unix penutupan bar (uint64 di struct)."""
        return (self.t + DAY_MS) // 1000

    def abi_fields(self) -> list:
        return [self.v, chain.ascii32(self.bot_id), chain.from_hex(self.spec_sha), self.asof(), chain.ascii32(self.asset),
                ACTION_CODE[self.aksi], _scaled_int(self.bobot_lama, WEIGHT_DP), _scaled_int(self.bobot_baru, WEIGHT_DP),
                _scaled_int(self.harga_ref, PRICE_DP), chain.from_hex(self.data_hash)]

    def abi(self) -> bytes:
        return chain.abi_encode(STRUCT_TYPES, self.abi_fields())

    def id(self) -> str:
        return chain.hex0x(chain.keccak256(self.abi()))

    def leaf(self, salt: bytes) -> bytes:
        """Daun komit-ungkap. `salt` = tepat 32 byte acak PER SINYAL (satu salt dipakai ulang = sinyal lain bisa ditebak)."""
        return chain.keccak256(self.abi() + chain.abi_encode(["bytes32"], [salt]))


def iso_close(t_open_ms: int) -> str:
    return dt.datetime.fromtimestamp((t_open_ms + DAY_MS) / 1000, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def relevant_assets(spec: BotSpec) -> List[str]:
    """Aset yang boleh memengaruhi bot ini (universe + kandidat emas), supaya data lain tidak mengubah `data_hash`."""
    return sorted(set(spec.universe) | set(spec.konstanta.get("emas_kandidat", [])))


def data_fingerprint(spec: BotSpec, data: MarketData) -> str:
    """sha256 atas SELURUH riwayat (waktu, penutupan) per aset relevan - perp dan spot - plus funding harian dan event.
    Seluruh riwayat, bukan jendela: B6 menghitung keadaannya dari awal. Data sudah dipotong point-in-time oleh pemanggil."""
    body: Dict[str, object] = {}
    for a in relevant_assets(spec):
        for kind, bag in (("perp", data.perp), ("spot", data.spot)):
            s = bag.get(a)
            if s is not None and len(s):
                body[f"{kind}:{a}"] = [[s.t[i], s.c[i]] for i in range(len(s))]
        f = data.funding.get(a)
        if f:
            body[f"funding:{a}"] = [[d, round(f[d], 12)] for d in sorted(f)]
    if data.events:
        body["events"] = [[e.asset, e.day1_open_t, e.day1_close, e.day1_quote_volume_usd] for e in data.events]
    return sha0x(body)


def ref_prices(spec: BotSpec, data: MarketData, t: int) -> Dict[str, float]:
    """Penutupan bar `t` per aset (spot untuk B5, perp untuk lainnya). Hanya referensi, bukan harga isi."""
    bag = data.spot if spec.method == "B5-CORE-RWA" else data.perp
    out: Dict[str, float] = {}
    for a, s in bag.items():
        i = s.index_at_or_before(t)
        if i >= 0 and s.t[i] == t:
            out[a] = s.c[i]
    return out


def diff_signals(spec: BotSpec, prev: Optional[Target], cur: Target, data_hash: str,
                 prices: Dict[str, float], min_reweight: float = 0.25) -> List[Signal]:
    """Apa yang berubah dari `prev` ke `cur`. Pembalikan arah = KELUAR lalu MASUK; perubahan bobot kecil diabaikan
    kecuali bot menandai `rebalanced` (B2/B5) dan bobotnya memang berubah. Bobot dan harga dikuantisasi di sini."""
    w0 = prev.weights if prev else {}
    w1 = cur.weights
    out: List[Signal] = []
    asof = iso_close(cur.t)

    def mk(asset, aksi, a0, a1):
        out.append(Signal(SIGNAL_V, cur.bot_id, spec.sha(), cur.t, asof, asset, aksi, quantize(a0, WEIGHT_DP),
                          quantize(a1, WEIGHT_DP), quantize(prices.get(asset), PRICE_DP), data_hash, dict(cur.meta)))

    for asset in sorted(set(w0) | set(w1)):
        a0, a1 = w0.get(asset, 0.0), w1.get(asset, 0.0)
        if abs(a0) < EPS and abs(a1) < EPS:
            continue
        if abs(a0) < EPS:
            mk(asset, "MASUK_LONG" if a1 > 0 else "MASUK_SHORT", a0, a1)
        elif abs(a1) < EPS:
            mk(asset, "KELUAR", a0, a1)
        elif (a0 > 0) != (a1 > 0):
            mk(asset, "KELUAR", a0, 0.0)
            mk(asset, "MASUK_LONG" if a1 > 0 else "MASUK_SHORT", 0.0, a1)
        else:
            rel = abs(a1 - a0) / abs(a0)
            if rel >= min_reweight or (cur.meta.get("rebalanced") and abs(a1 - a0) > 1e-6):
                mk(asset, "UBAH_BOBOT", a0, a1)
    return out


def signals_at(spec: BotSpec, data: MarketData, t_asof: int, min_reweight: float = 0.25) -> List[Signal]:
    """Sinyal yang sah pada penutupan bar `t_asof` (waktu buka bar, ms UTC), dari data sampai bar itu SAJA (point-in-time).

    Menolak (StaleBars) bila tidak ada target tepat pada `t_asof` - artinya data berhenti sebelum bar itu (cache basi atau
    bolong). Itulah guard yang tidak dimiliki `tools/direction.py` pada cacat 2 Okt 2026."""
    md = data.upto(t_asof)
    tg = REGISTRY[spec.method](spec, md)
    by_t = {x.t: x for x in tg}
    cur = by_t.get(t_asof)
    if cur is None:
        if spec.method == "B4-LISTING-FADE":        # bot event: tak ada target = tak ada posisi aktif
            cur = Target(spec.bot_id, t_asof, {}, {})
        else:
            last = max(by_t) if by_t else None
            raise StaleBars(f"{spec.bot_id}: tidak ada target pada bar {t_asof} (target terakhir: {last}) - data basi atau terpotong")
    prev = by_t.get(t_asof - DAY_MS)
    return diff_signals(spec, prev, cur, data_fingerprint(spec, md), ref_prices(spec, md, t_asof), min_reweight)


# ---------------------------------------------------------------- komit-ungkap per bot per bar

@dataclass(frozen=True)
class Entry:
    signal: Signal
    salt: bytes
    leaf: bytes
    proof: Tuple[bytes, ...]


@dataclass(frozen=True)
class Batch:
    bot_id: str
    spec_sha: str
    t: int
    root: bytes                  # 32 byte nol bila bot diam pada bar ini
    entries: Tuple[Entry, ...]

    def asof(self) -> int:
        return (self.t + DAY_MS) // 1000


def build_batch(bot_id: str, spec_sha: str, t: int, signals: Sequence[Signal], salts: Sequence[bytes]) -> Batch:
    if len(signals) != len(salts):
        raise ValueError("satu salt per sinyal")
    if len(set(salts)) != len(salts):
        raise ValueError("salt harus unik per sinyal")
    for s in signals:
        if (s.bot_id, s.spec_sha, s.t) != (bot_id, spec_sha, t):
            raise ValueError("semua sinyal satu batch harus bot, spec, dan bar yang sama")
    leaves = [s.leaf(salt) for s, salt in zip(signals, salts)]
    root = chain.merkle_root(leaves)
    entries = tuple(Entry(s, salt, lf, tuple(chain.merkle_proof(leaves, lf))) for s, salt, lf in zip(signals, salts, leaves))
    return Batch(bot_id, spec_sha, t, root, entries)


def verify_entry(sinyal: dict, salt_hex: str, proof_hex: Sequence[str], root_hex: str) -> Tuple[bool, str]:
    """Pemeriksaan sisi pembeli: muatan + salt + bukti -> cocok dengan akar yang dikomit? Mengembalikan (ok, alasan)."""
    try:
        s = Signal.from_dict(sinyal)
        salt = chain.from_hex(salt_hex)
        proof = [chain.from_hex(p) for p in proof_hex]
        root = chain.from_hex(root_hex)
        leaf = s.leaf(salt)
    except (KeyError, ValueError, TypeError, ArithmeticError) as e:     # ArithmeticError: inf/nan/angka raksasa dari penjual
        return False, f"muatan tidak terbaca: {type(e).__name__}"
    if not chain.merkle_verify(proof, root, leaf):
        return False, "BEDA: daun (muatan+salt) tidak menuju akar yang dikomit"
    return True, "cocok"
