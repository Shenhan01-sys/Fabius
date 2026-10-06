"""P167a (epik 12, F-D125): aturan deklaratif JSON untuk `kind=rule` - validator + evaluator murni (stdlib), dijalankan MESIN kami.

Penerbit menulis aturan (JSON); mesin yang menghitung target. Tidak ada kode asing: kosakata tertutup, batas ukuran / kedalaman / jendela, dan
**tidak ada cara mengintip masa depan oleh konstruksi**: fitur di hari i hanya membaca bar <= i, `lag` hanya menggeser KE BELAKANG, operator
bekerja per hari. Nilai tak terdefinisi (data kurang, bagi nol) tidak pernah memicu apa pun: logika tiga-nilai (`not` atas tak terdefinisi tetap
tak terdefinisi), dan di tingkat atas hanya "benar" yang dihitung.

Konvensi waktu (persis konvensi bot template, supaya bukti ekuivalensi B1/B6/B2 bit-ke-bit benar oleh konstruksi): grid = hari-UTC gabungan
universe. `ret(n)` = c[i]/c[i-n] - 1 dengan i-n di grid (B1/B2; bar hilang di ujung = tak terdefinisi); fitur jendela lain memakai n bar harian
TERAKHIR milik aset itu, bolong data dilewati (B6), lalu ditaruh di grid menurut tanggal. Sinyal dihitung di penutupan bar i dan berlaku untuk
return bar i+1 (konvensi mesin, `replay`). Fungsi rolling = `series.rolling_mean/std` yang sama dengan B6.

Bentuk aturan (kosakata disetujui builder 6 Okt 2026, [[vault/08-Backlog/12 - Epik Pengajuan Terbuka dan Peninjau LLM]] §3.1 dan §3.1.1):

    rule  = {"mode": "per_aset" | "peringkat", "params": {nama: angka}, ...mode, "bobot": {"skema": "sama" | "inv_vol", "gross_maks": g[, "n": jendela]}}
    per_aset : masuk_long?, keluar_long?, masuk_short?, keluar_short?     (COND; mesin keadaan per aset: flat -> long/short -> flat)
    peringkat: {"skor": EXPR, "long_teratas": k, "short_terbawah": k, "min_aset": m, "rotasi": "harian" | "tujuh_sub_buku"}
    EXPR := {"c": angka} | {"p": nama} | {"f": FITUR[, "n": angka|{"p"}][, "lag": 0..30|{"p"}]} | {"op": + - * /, "a", "b"} | {"fn": abs|neg|min|max, "args": [..]}
    COND := {"cmp": > < >= <=, "a": EXPR, "b": EXPR} | {"and": [COND..]} | {"or": [COND..]} | {"not": COND}
"""
from __future__ import annotations

import datetime as dt
import math
import re
from typing import Any, Dict, Iterator, List, Optional, Tuple

from .data import MarketData
from .series import Series, pct_change, rolling_mean, rolling_std
from .spec import BotSpec
from .target import Target

RULE_METHOD = "RULE"                         # `BotSpec.template` bot rule: kunci ke REGISTRY / replay
PARAM_NAMA = "aturan"                        # `BotSpec.param_nama` bot rule (parameter yang bisa digeser ada di dalam aturan)
PENGGARIS = {"fee_bps_sisi": 7, "funding": "nyata dua sisi"}      # milik kami (sama dengan B1/B2); penerbit tidak menentukan biaya

MODES = ("per_aset", "peringkat")
ROTASI = ("harian", "tujuh_sub_buku")
SKEMA_BOBOT = ("sama", "inv_vol")
PRICE_FEATURES = ("close", "open", "high", "low", "volume")
WINDOW_FEATURES = ("ret", "sma", "ema", "std", "zscore", "rsi", "atr_pct", "max_high", "min_low", "vol_ratio", "drawdown")
CMPS = (">", "<", ">=", "<=")
OPS = ("+", "-", "*", "/")
FNS = {"abs": (1, 1), "neg": (1, 1), "min": (2, 4), "max": (2, 4)}
LIMITS = {"max_simpul": 64, "max_kedalaman": 8, "jendela_min": 2, "jendela_maks": 365, "lag_maks": 30, "max_parameter": 6, "anggaran_jendela": 1500,
          "konstanta_maks": 1_000_000, "k_maks": 8, "min_aset_maks": 40, "gross_maks": {"per_aset": 1.0, "peringkat": 2.0}}
PARAM_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,15}")
_MODE_KEYS = {"per_aset": {"mode", "params", "masuk_long", "keluar_long", "masuk_short", "keluar_short", "bobot"},
              "peringkat": {"mode", "params", "skor", "long_teratas", "short_terbawah", "min_aset", "rotasi", "bobot"}}
_SATU_PARAM = lambda v: isinstance(v, dict) and set(v) == {"p"}      # noqa: E731


def vocabulary() -> Dict[str, Any]:
    """Kosakata + batas, untuk pembangun aturan di web (dibagikan gerbang lewat `GET /bots/schema`) dan untuk tes: satu sumber kebenaran."""
    return {"modes": list(MODES), "price": list(PRICE_FEATURES), "window": list(WINDOW_FEATURES), "cmps": list(CMPS), "ops": list(OPS),
            "fns": {k: list(v) for k, v in FNS.items()}, "rotasi": list(ROTASI), "skema": list(SKEMA_BOBOT),
            "limits": {k: (dict(v) if isinstance(v, dict) else v) for k, v in LIMITS.items()}, "penggaris": dict(PENGGARIS)}


# ---------------------------------------------------------------- validasi (input musuh: tidak pernah melempar, pesan tidak memantulkan teks mentah)

def _safe(x: Any) -> str:
    return repr(str(x))[:40]


def _num(v: Any) -> bool:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    if isinstance(v, float) and not math.isfinite(v):
        return False
    return abs(v) <= LIMITS["konstanta_maks"]


def _int_value(v: Any) -> bool:
    """Bilangan bulat; desimal bulat (60.0) diterima dan dikanonikkan jadi int."""
    return _num(v) and float(v) == int(v)


class _Stop(Exception):
    """Batas simpul terlampaui: hentikan penelusuran (tidak ada gunanya memeriksa sisa pohon raksasa)."""


class _Ctx:
    def __init__(self, params: Dict[str, Any]):
        self.out: List[str] = []
        self.nodes = 0
        self.maxdepth = 0
        self.params = params
        self.used: set = set()
        self.windows: set = set()

    def err(self, msg: str) -> None:
        self.out.append(msg)

    def node(self, depth: int, path: str) -> bool:
        self.nodes += 1
        if self.nodes > LIMITS["max_simpul"]:
            self.err(f"{path}: lebih dari {LIMITS['max_simpul']} simpul")
            raise _Stop()
        self.maxdepth = max(self.maxdepth, depth)
        if depth > LIMITS["max_kedalaman"]:
            self.err(f"{path}: lebih dari {LIMITS['max_kedalaman']} tingkat bersarang")
            return False
        return True


def _ref(c: _Ctx, v: Any, path: str) -> Optional[str]:
    """Nama parameter dari {"p": nama}; None (dan pesan) bila bentuknya salah atau tidak dideklarasikan."""
    name = v.get("p")
    if not isinstance(name, str) or not PARAM_NAME.fullmatch(name):
        c.err(f"{path}: nama parameter tidak valid")
        return None
    if name not in c.params:
        c.err(f"{path}: parameter {_safe(name)} tidak dideklarasikan di params")
        return None
    c.used.add(name)
    return name


def _intarg(c: _Ctx, v: Any, path: str, lo: int, hi: int, what: str) -> Optional[int]:
    """Argumen bilangan bulat dalam [lo, hi]: literal atau {"p": nama} yang nilainya sah. -> nilai terselesaikan (untuk anggaran kerja) atau None."""
    if isinstance(v, dict):
        if not _SATU_PARAM(v):
            c.err(f"{path}: {what} harus bilangan bulat atau {{\"p\": nama}}")
            return None
        name = _ref(c, v, path)
        if name is None:
            return None
        val = c.params[name]
        if not (_int_value(val) and lo <= val <= hi):
            c.err(f"{path}: parameter {_safe(name)} dipakai sebagai {what}, nilainya harus bilangan bulat dalam [{lo}, {hi}]")
            return None
        return int(val)
    if not (_int_value(v) and lo <= v <= hi):
        c.err(f"{path}: {what} harus bilangan bulat dalam [{lo}, {hi}]")
        return None
    return int(v)


def _expr(c: _Ctx, n: Any, depth: int, path: str) -> None:
    if not c.node(depth, path):
        return
    if not isinstance(n, dict) or not n:
        c.err(f"{path}: ekspresi harus objek tak kosong")
        return
    keys = set(n)
    if keys == {"c"}:
        if not _num(n["c"]):
            c.err(f"{path}.c: harus angka hingga (|x| <= {LIMITS['konstanta_maks']:g})")
    elif keys == {"p"}:
        _ref(c, n, f"{path}.p")
    elif "f" in keys:
        if not keys <= {"f", "n", "lag"}:
            c.err(f"{path}: fitur hanya boleh punya f, n, lag")
            return
        f = n["f"]
        if f in PRICE_FEATURES:
            if "n" in n:
                c.err(f"{path}: fitur {f} tidak punya jendela n (pakai lag)")
        elif f in WINDOW_FEATURES:
            if "n" not in n:
                c.err(f"{path}: fitur {f} wajib punya jendela n")
            else:
                w = _intarg(c, n["n"], f"{path}.n", LIMITS["jendela_min"], LIMITS["jendela_maks"], "jendela")
                if w is not None:
                    c.windows.add((f, w))
        else:
            c.err(f"{path}.f: harus salah satu dari {list(PRICE_FEATURES + WINDOW_FEATURES)}")
        if "lag" in n:
            _intarg(c, n["lag"], f"{path}.lag", 0, LIMITS["lag_maks"], "lag")
    elif "op" in keys:
        if keys != {"op", "a", "b"} or n["op"] not in OPS:
            c.err(f"{path}: operator harus {{op, a, b}} dengan op salah satu dari {list(OPS)}")
            return
        _expr(c, n["a"], depth + 1, f"{path}.a")
        _expr(c, n["b"], depth + 1, f"{path}.b")
    elif "fn" in keys:
        if keys != {"fn", "args"} or n["fn"] not in FNS or not isinstance(n["args"], list):
            c.err(f"{path}: fungsi harus {{fn, args}} dengan fn salah satu dari {list(FNS)}")
            return
        lo, hi = FNS[n["fn"]]
        if not lo <= len(n["args"]) <= hi:
            c.err(f"{path}.args: {n['fn']} butuh {lo}..{hi} argumen")
            return
        for i, a in enumerate(n["args"]):
            _expr(c, a, depth + 1, f"{path}.args[{i}]")
    else:
        c.err(f"{path}: bukan ekspresi (c | p | f | op | fn)")


def _cond(c: _Ctx, n: Any, depth: int, path: str) -> None:
    if not c.node(depth, path):
        return
    if not isinstance(n, dict) or len(n) not in (1, 3):
        c.err(f"{path}: kondisi harus objek (cmp | and | or | not)")
        return
    if "cmp" in n:
        if set(n) != {"cmp", "a", "b"} or n["cmp"] not in CMPS:
            c.err(f"{path}: perbandingan harus {{cmp, a, b}} dengan cmp salah satu dari {list(CMPS)}")
            return
        _expr(c, n["a"], depth + 1, f"{path}.a")
        _expr(c, n["b"], depth + 1, f"{path}.b")
    elif set(n) in ({"and"}, {"or"}):
        k = next(iter(n))
        xs = n[k]
        if not isinstance(xs, list) or not 2 <= len(xs) <= 4:
            c.err(f"{path}.{k}: harus daftar 2..4 kondisi")
            return
        for i, x in enumerate(xs):
            _cond(c, x, depth + 1, f"{path}.{k}[{i}]")
    elif set(n) == {"not"}:
        _cond(c, n["not"], depth + 1, f"{path}.not")
    else:
        c.err(f"{path}: bukan kondisi (cmp | and | or | not)")


def _check(rule: Any, out: List[str], path: str) -> Optional[_Ctx]:
    """Isi `out` dengan masalah; kembalikan konteks penelusuran (ukuran) bila pohonnya selesai ditelusuri, selain itu None."""
    if not isinstance(rule, dict):
        out.append(f"{path}: harus objek")
        return None
    mode = rule.get("mode")
    if mode not in MODES:
        out.append(f"{path}.mode: harus salah satu dari {list(MODES)}")
        return None
    for k in rule:
        if k not in _MODE_KEYS[mode]:
            out.append(f"{path}.{_safe(k)}: field tidak dikenal untuk mode {mode} (skema tertutup)")
    params = rule.get("params", {})
    if not isinstance(params, dict) or len(params) > LIMITS["max_parameter"]:
        out.append(f"{path}.params: harus objek dengan paling banyak {LIMITS['max_parameter']} parameter bernama")
        return None
    for k, v in params.items():
        if not isinstance(k, str) or not PARAM_NAME.fullmatch(k):
            out.append(f"{path}.params.{_safe(k)}: nama parameter tidak valid ([A-Za-z][A-Za-z0-9_]{{0,15}})")
        elif not _num(v) or v == 0:
            out.append(f"{path}.params.{k}: harus angka hingga bukan nol (nol tidak bisa digeser G5; pakai {{\"c\": 0}} untuk konstanta)")
    if out:
        return None
    c = _Ctx(params)
    try:
        if mode == "per_aset":
            conds = [k for k in ("masuk_long", "masuk_short", "keluar_long", "keluar_short") if rule.get(k) is not None]
            if not ({"masuk_long", "masuk_short"} & set(conds)):
                c.err(f"{path}: per_aset butuh masuk_long dan/atau masuk_short")
            for k, base in (("keluar_long", "masuk_long"), ("keluar_short", "masuk_short")):
                if k in conds and base not in conds:
                    c.err(f"{path}.{k}: butuh {base}")
            for k in conds:
                _cond(c, rule[k], 1, f"{path}.{k}")
        else:
            if rule.get("skor") is None:
                c.err(f"{path}.skor: wajib")
            else:
                _expr(c, rule["skor"], 1, f"{path}.skor")
            kl = rule.get("long_teratas", 0)
            ks = rule.get("short_terbawah", 0)
            for k, x in (("long_teratas", kl), ("short_terbawah", ks)):
                if not (_int_value(x) and 0 <= x <= LIMITS["k_maks"]):
                    c.err(f"{path}.{k}: harus bilangan bulat 0..{LIMITS['k_maks']}")
            ma = rule.get("min_aset")
            if not (_int_value(ma) and 2 <= ma <= LIMITS["min_aset_maks"]):
                c.err(f"{path}.min_aset: harus bilangan bulat 2..{LIMITS['min_aset_maks']}")
            elif _int_value(kl) and _int_value(ks) and ma < kl + ks:
                c.err(f"{path}.min_aset: minimal long_teratas + short_terbawah ({int(kl) + int(ks)}) supaya kaki tidak saling tumpang")
            if _int_value(kl) and _int_value(ks) and kl + ks == 0:
                c.err(f"{path}: peringkat butuh long_teratas dan/atau short_terbawah >= 1")
            if rule.get("rotasi") not in ROTASI:
                c.err(f"{path}.rotasi: harus salah satu dari {list(ROTASI)}")
        _bobot(c, rule.get("bobot"), mode, f"{path}.bobot")
    except _Stop:
        pass
    out.extend(c.out)
    if c.out:
        return None
    for name in params:
        if name not in c.used:
            out.append(f"{path}.params.{name}: parameter tidak dipakai di aturan (parameter yatim tidak bisa diuji G5)")
    work = sum(n for _, n in c.windows)
    if work > LIMITS["anggaran_jendela"]:
        out.append(f"{path}: anggaran kerja jendela {work} > {LIMITS['anggaran_jendela']} (jumlah jendela semua fitur berbeda)")
    return c


def _bobot(c: _Ctx, b: Any, mode: str, path: str) -> None:
    if not isinstance(b, dict):
        c.err(f"{path}: wajib objek {{skema, gross_maks}}")
        return
    if not set(b) <= {"skema", "gross_maks", "n"}:
        c.err(f"{path}: hanya skema, gross_maks, n")
    if b.get("skema") not in SKEMA_BOBOT:
        c.err(f"{path}.skema: harus salah satu dari {list(SKEMA_BOBOT)}")
        return
    cap = LIMITS["gross_maks"][mode]
    g = b.get("gross_maks")
    if not (_num(g) and 0 < g <= cap):
        c.err(f"{path}.gross_maks: harus angka dalam (0, {cap:g}] untuk mode {mode}")
    if b["skema"] == "inv_vol":
        if "n" not in b:
            c.err(f"{path}.n: inv_vol wajib punya jendela volatilitas n")
        else:
            w = _intarg(c, b["n"], f"{path}.n", LIMITS["jendela_min"], LIMITS["jendela_maks"], "jendela")
            if w is not None:
                c.windows.add(("vol", w))
    elif "n" in b:
        c.err(f"{path}.n: hanya untuk inv_vol")


def validate(rule: Any, path: str = "spec.rule") -> List[str]:
    """Daftar masalah (kosong = sah). Gagal TERTUTUP: apa pun yang tak terduga = ditolak, bukan dilempar."""
    out: List[str] = []
    try:
        _check(rule, out, path)
    except Exception as e:                                                          # noqa: BLE001
        return [f"{path}: validasi aturan gagal tak terduga ({type(e).__name__}): ditolak"]
    return out[:30]


def ukuran(rule: Any) -> Optional[Dict[str, int]]:
    """{simpul, kedalaman, jendela} aturan yang SAH (jendela = anggaran kerja: jumlah jendela semua fitur berbeda); None bila aturan tidak sah.
    Penghitung di web (`web/src/lib/rule.ts`) harus sama persis: tes paritas `WebContractTests`."""
    out: List[str] = []
    try:
        c = _check(rule, out, "rule")
    except Exception:                                                               # noqa: BLE001
        return None
    if c is None or out:
        return None
    return {"simpul": c.nodes, "kedalaman": c.maxdepth, "jendela": sum(n for _, n in c.windows)}


def validate_universe(rule: Dict[str, Any], n_universe: int, path: str = "spec.rule") -> List[str]:
    """Silang-field dengan universe: peringkat butuh min_aset <= jumlah aset universe (kalau tidak, tidak pernah ada buku)."""
    if rule.get("mode") == "peringkat" and _int_value(rule.get("min_aset")) and rule["min_aset"] > n_universe:
        return [f"{path}.min_aset: {int(rule['min_aset'])} lebih besar dari jumlah aset universe ({n_universe})"]
    return []


# ---------------------------------------------------------------- bentuk kanonik, penggunaan parameter

def _iter_refs(node: Any, role: str = "bebas") -> Iterator[Tuple[str, str]]:
    """(nama parameter, peran) untuk setiap {"p": nama}; peran "n" (jendela), "lag", atau "bebas" menurut kunci induknya."""
    if isinstance(node, dict):
        if _SATU_PARAM(node):
            yield node["p"], role
            return
        for k, v in node.items():
            if k != "params":
                yield from _iter_refs(v, k if k in ("n", "lag") else "bebas")
    elif isinstance(node, list):
        for x in node:
            yield from _iter_refs(x, "bebas")


def param_jenis(rule: Dict[str, Any]) -> Dict[str, int]:
    """{parameter bertipe bulat: batas bawah}. Parameter yang dipakai sebagai jendela (n) atau lag harus bulat; bawah 2 untuk jendela, 0 untuk lag saja."""
    out: Dict[str, int] = {}
    for name, role in _iter_refs(rule):
        if role == "n":
            out[name] = 2
        elif role == "lag":
            out.setdefault(name, 0)
    return out


def canonical(rule: Dict[str, Any]) -> Dict[str, Any]:
    """Bentuk kanonik aturan SAH: bulat untuk jendela / lag / k, desimal untuk lainnya (`2` == `2.0`); dipakai sha dan `fingerprint` (dedupe)."""
    ints = param_jenis(rule)

    def walk(n: Any, key: str = "") -> Any:
        if isinstance(n, dict):
            return {k: walk(v, k) for k, v in n.items() if v is not None}
        if isinstance(n, list):
            return [walk(x, key) for x in n]
        if isinstance(n, str):
            return n
        if key in ("n", "lag", "long_teratas", "short_terbawah", "min_aset"):
            return int(n)
        return float(n)
    out = walk({k: v for k, v in rule.items() if k != "params"})
    out["params"] = {k: (int(v) if k in ints else float(v)) for k, v in rule.get("params", {}).items()}
    if out["mode"] == "peringkat":
        out.setdefault("long_teratas", 0)
        out.setdefault("short_terbawah", 0)
    return out


def varian_g5(rule: Dict[str, Any], n_faktor: int) -> int:
    """Jumlah varian nominal yang dievaluasi G5 untuk aturan ini (SATU per parameter + satu kelompok 'semua' bila > 1 parameter); ikut hitungan percobaan."""
    m = len(rule.get("params", {}))
    return n_faktor * (m + (1 if m > 1 else 0))


def kelompok_plateau(rule: Dict[str, Any], faktor: Tuple[float, ...]) -> List[Tuple[str, List[Tuple[str, Dict[str, Any]]]]]:
    """Kelompok varian G5: [(nama kelompok, [(label varian, aturan varian)])]. Satu kelompok per parameter bernama + 'semua' bila > 1 parameter.
    Varian yang nilainya sama dengan dasar atau dengan varian lain dalam kelompok dibuang (tidak ada gunanya diuji dua kali)."""
    ints = param_jenis(rule)
    base = rule.get("params", {})

    def geser(name: str, f: float) -> Any:
        v = base[name]
        return max(ints[name], int(round(v * f))) if name in ints else float(v) * f

    def kelompok(nama: str, names: List[str]) -> Tuple[str, List[Tuple[str, Dict[str, Any]]]]:
        seen = {tuple(base[k] for k in names)}
        rows: List[Tuple[str, Dict[str, Any]]] = []
        for f in faktor:
            vals = tuple(geser(k, f) for k in names)
            if vals in seen:
                continue
            seen.add(vals)
            r = dict(rule)
            r["params"] = {**base, **dict(zip(names, vals))}
            label = f"{vals[0]:g}" if len(names) == 1 else f"x{f:g}"
            rows.append((label, r))
        return nama, rows
    groups = [kelompok(k, [k]) for k in base]
    if len(base) > 1:
        groups.append(kelompok("semua", list(base)))
    return groups


# ---------------------------------------------------------------- evaluator

Arr = List[Optional[float]]


def _fin(v: Optional[float]) -> Optional[float]:
    return v if v is not None and math.isfinite(v) else None


class _Feat:
    """Fitur harga satu aset di atas grid hari (cache per (fitur, n)). Setiap elemen hanya membaca indeks <= hari itu (kausalitas oleh konstruksi).

    Dua konvensi, persis seperti bot template yang harus bisa dinyatakan ulang (bukti ekuivalensi):
      - `ret(n)` = c[i] / c[i-n] - 1 dengan i-n di GRID hari (B1/B2); bar hilang di salah satu ujung = tak terdefinisi;
      - fitur jendela lain memakai n bar harian TERAKHIR milik aset itu, bolong data dilewati (B6: rolling atas deret aset sendiri), lalu ditaruh di grid
        menurut tanggal bar. Hari tanpa bar = tak terdefinisi dan tidak mengubah keadaan.
    `lag` menggeser di grid (hari kalender)."""

    def __init__(self, s: Series, grid: List[int], pos: Dict[int, int]):
        self.N = len(grid)
        self.idx = [pos[t] for t in s.t]                              # indeks grid tiap bar aset ini (naik)
        self.own = {"close": list(s.c), "open": list(s.o), "high": list(s.h), "low": list(s.l), "volume": list(s.v)}
        self.col = {k: self._grid(v) for k, v in self.own.items()}
        self.cache: Dict[Tuple[str, int], Arr] = {}

    def _grid(self, arr: Arr) -> Arr:
        out: Arr = [None] * self.N
        for gi, v in zip(self.idx, arr):
            out[gi] = v
        return out

    def get(self, f: str, n: int) -> Arr:
        if f in self.col:
            return self.col[f]
        key = (f, n)
        if key not in self.cache:
            self.cache[key] = self._ret(n) if f == "ret" else self._grid(getattr(self, "_" + f)(n))
        return self.cache[key]

    def _ret(self, n: int) -> Arr:
        c = self.col["close"]
        return [c[i] / c[i - n] - 1.0 if i - n >= 0 and c[i] is not None and c[i - n] not in (None, 0) else None for i in range(self.N)]

    def _sma(self, n: int) -> Arr:
        return rolling_mean(self.own["close"], n)

    def _std(self, n: int) -> Arr:
        return rolling_std(self.own["close"], n)

    def _zscore(self, n: int) -> Arr:
        c, m, s = self.own["close"], self._sma(n), self._std(n)
        return [(c[i] - m[i]) / s[i] if m[i] is not None and s[i] not in (None, 0) else None for i in range(len(c))]

    def _ema(self, n: int) -> Arr:
        c, a = self.own["close"], 2.0 / (n + 1)
        out: Arr = [None] * len(c)
        if len(c) >= n:
            e = sum(c[:n]) / n
            out[n - 1] = e
            for i in range(n, len(c)):
                e = a * c[i] + (1.0 - a) * e
                out[i] = e
        return out

    def _rsi(self, n: int) -> Arr:
        c, out = self.own["close"], [None] * len(self.own["close"])
        for i in range(n, len(c)):
            d = [c[j] - c[j - 1] for j in range(i - n + 1, i + 1)]
            g, l = sum(x for x in d if x > 0) / n, sum(-x for x in d if x < 0) / n
            out[i] = (100.0 if g > 0 else None) if l == 0 else 100.0 - 100.0 / (1.0 + g / l)
        return out

    def _atr_pct(self, n: int) -> Arr:
        h, lo, c = self.own["high"], self.own["low"], self.own["close"]
        tr: Arr = [None] + [max(h[i] - lo[i], abs(h[i] - c[i - 1]), abs(lo[i] - c[i - 1])) for i in range(1, len(c))]
        atr = rolling_mean(tr, n)
        return [100.0 * atr[i] / c[i] if atr[i] is not None and c[i] != 0 else None for i in range(len(c))]

    def _roll(self, name: str, n: int, fn) -> Arr:
        x = self.own[name]
        out: Arr = [None] * len(x)
        for i in range(n - 1, len(x)):
            out[i] = fn(x[i - n + 1:i + 1])
        return out

    def _max_high(self, n: int) -> Arr:
        return self._roll("high", n, max)

    def _min_low(self, n: int) -> Arr:
        return self._roll("low", n, min)

    def _drawdown(self, n: int) -> Arr:
        c, mx = self.own["close"], self._roll("close", n, max)
        return [c[i] / mx[i] - 1.0 if mx[i] not in (None, 0) else None for i in range(len(c))]

    def _vol_ratio(self, n: int) -> Arr:
        v, out = self.own["volume"], [None] * len(self.own["volume"])
        for i in range(n, len(v)):
            m = sum(v[i - n:i]) / n
            if m != 0:
                out[i] = v[i] / m
        return out

    def vol(self, n: int) -> Arr:
        """sigma return harian n hari (ddof 1) di GRID: dasar bobot inv_vol; jendela yang memuat bolong tak terdefinisi (return lintas bolong bukan return harian)."""
        key = ("vol", n)
        if key not in self.cache:
            self.cache[key] = rolling_std(pct_change(self.col["close"]), n)
        return self.cache[key]


def _intval(x: Any, params: Dict[str, Any]) -> int:
    return int(params[x["p"]]) if isinstance(x, dict) else int(x)


def _eval(n: Dict[str, Any], ft: _Feat, params: Dict[str, Any]) -> Arr:
    N = ft.N
    if "c" in n:
        return [float(n["c"])] * N
    if "p" in n:
        return [float(params[n["p"]])] * N
    if "f" in n:
        w = _intval(n["n"], params) if "n" in n else 0
        a = ft.get(n["f"], w)
        lag = _intval(n["lag"], params) if "lag" in n else 0
        if lag:
            return [None] * min(lag, N) + a[:max(N - lag, 0)]
        return a
    if "op" in n:
        a, b, op = _eval(n["a"], ft, params), _eval(n["b"], ft, params), n["op"]
        if op == "+":
            return [_fin(x + y) if x is not None and y is not None else None for x, y in zip(a, b)]
        if op == "-":
            return [_fin(x - y) if x is not None and y is not None else None for x, y in zip(a, b)]
        if op == "*":
            return [_fin(x * y) if x is not None and y is not None else None for x, y in zip(a, b)]
        return [_fin(x / y) if x is not None and y not in (None, 0) else None for x, y in zip(a, b)]
    args = [_eval(x, ft, params) for x in n["args"]]
    fn = n["fn"]
    if fn == "abs":
        return [abs(x) if x is not None else None for x in args[0]]
    if fn == "neg":
        return [-x if x is not None else None for x in args[0]]
    pick = min if fn == "min" else max
    return [None if any(v is None for v in vs) else pick(vs) for vs in zip(*args)]


_CMP = {">": lambda x, y: x > y, "<": lambda x, y: x < y, ">=": lambda x, y: x >= y, "<=": lambda x, y: x <= y}


def _cond_eval(n: Dict[str, Any], ft: _Feat, params: Dict[str, Any]) -> List[Optional[bool]]:
    if "cmp" in n:
        a, b, f = _eval(n["a"], ft, params), _eval(n["b"], ft, params), _CMP[n["cmp"]]
        return [f(x, y) if x is not None and y is not None else None for x, y in zip(a, b)]
    if "not" in n:
        return [None if v is None else not v for v in _cond_eval(n["not"], ft, params)]
    key = "and" if "and" in n else "or"
    cols = [_cond_eval(x, ft, params) for x in n[key]]
    out: List[Optional[bool]] = []
    for vs in zip(*cols):
        if key == "and":
            out.append(False if any(v is False for v in vs) else (None if any(v is None for v in vs) else True))
        else:
            out.append(True if any(v is True for v in vs) else (None if any(v is None for v in vs) else False))
    return out


def _posisi(conds: Dict[str, Optional[List[Optional[bool]]]], close: Arr) -> List[int]:
    """Mesin keadaan satu aset: 0 flat, +1 long, -1 short. Keadaan hanya berubah di hari ada bar; kondisi tak terdefinisi tidak pernah memicu."""
    li, lo, si, so = conds["masuk_long"], conds["keluar_long"], conds["masuk_short"], conds["keluar_short"]
    pos, cur = [0] * len(close), 0
    for i in range(len(close)):
        if close[i] is None:
            continue
        if cur == 0:
            a = li is not None and li[i] is True
            b = si is not None and si[i] is True
            cur = 1 if (a and not b) else -1 if (b and not a) else 0       # long dan short sama-sama benar = konflik: tetap flat
        elif cur == 1:
            if (lo[i] is True) if lo is not None else (li is None or li[i] is not True):
                cur = 0
        else:
            if (so[i] is True) if so is not None else (si is None or si[i] is not True):
                cur = 0
        pos[i] = cur
    return pos


def _weekday(t_ms: int) -> int:
    return dt.datetime.fromtimestamp(t_ms / 1000, dt.timezone.utc).weekday()


def targets(spec: BotSpec, data: MarketData) -> List[Target]:
    """Target harian bot rule: satu jalur kode untuk live, replay, dan gerbang (`REGISTRY["RULE"]`)."""
    rule = spec.konstanta["rule"]
    params = rule.get("params", {})
    assets = [a for a in spec.universe if a in data.perp]
    grid = sorted({t for a in assets for t in data.perp[a].t})
    pos_grid = {t: i for i, t in enumerate(grid)}
    ft = {a: _Feat(data.perp[a], grid, pos_grid) for a in assets}
    bobot = rule["bobot"]
    g = float(bobot["gross_maks"])
    inv = bobot["skema"] == "inv_vol"
    nvol = _intval(bobot["n"], params) if inv else 0
    sig = {a: ft[a].vol(nvol) for a in assets} if inv else {}
    close = {a: ft[a].col["close"] for a in assets}
    if rule["mode"] == "per_aset":
        pos = {a: _posisi({k: (_cond_eval(rule[k], ft[a], params) if rule.get(k) is not None else None)
                           for k in ("masuk_long", "keluar_long", "masuk_short", "keluar_short")}, close[a]) for a in assets}
        return _targets_per_aset(spec.bot_id, grid, assets, close, pos, sig, g, inv)
    score = {a: _eval(rule["skor"], ft[a], params) for a in assets}
    return _targets_peringkat(spec.bot_id, grid, assets, close, score, sig, g, inv, rule)


def _targets_per_aset(bot_id: str, grid: List[int], assets: List[str], close: Dict[str, Arr], pos: Dict[str, List[int]],
                      sig: Dict[str, Arr], g: float, inv: bool) -> List[Target]:
    out: List[Target] = []
    for i, t in enumerate(grid):
        avail = [a for a in assets if close[a][i] is not None]
        if not avail:
            continue
        w: Dict[str, float] = {}
        if inv:
            iv = {a: 1.0 / sig[a][i] for a in avail if sig[a][i] not in (None, 0)}
            tot = sum(iv.values())
            for a in avail:
                if pos[a][i] and a in iv:
                    w[a] = pos[a][i] * g * iv[a] / tot
        else:
            for a in avail:
                if pos[a][i]:
                    w[a] = pos[a][i] * g / len(avail)
        out.append(Target(bot_id, t, w, {"n_aset": len(avail)}))
    return out


def _bagi(members: List[str], budget: float, side: int, sig: Dict[str, Arr], i: int, inv: bool) -> Dict[str, float]:
    if not inv:
        return {a: side * budget / len(members) for a in members} if members else {}
    iv = {a: 1.0 / sig[a][i] for a in members if sig[a][i] not in (None, 0)}
    tot = sum(iv.values())
    return {a: side * budget * v / tot for a, v in iv.items()}


def _targets_peringkat(bot_id: str, grid: List[int], assets: List[str], close: Dict[str, Arr], score: Dict[str, Arr],
                       sig: Dict[str, Arr], g: float, inv: bool, rule: Dict[str, Any]) -> List[Target]:
    kl, ks, min_aset = int(rule["long_teratas"]), int(rule["short_terbawah"]), int(rule["min_aset"])
    tujuh = rule["rotasi"] == "tujuh_sub_buku"
    books: Dict[int, Dict[str, float]] = {}                     # hari-minggu -> bobot sub-buku itu (tujuh_sub_buku)
    out: List[Target] = []
    for i, t in enumerate(grid):
        wd = _weekday(t)
        book: Optional[Dict[str, float]] = None
        sc = {a: score[a][i] for a in assets if close[a][i] is not None and score[a][i] is not None}
        if len(sc) >= min_aset:
            longs = sorted(sc, key=lambda a: (-sc[a], a))[:kl]
            rest = [a for a in sc if a not in longs]
            shorts = sorted(rest, key=lambda a: (sc[a], a))[:ks]
            book = {}
            book.update(_bagi(longs, g / 2.0, 1, sig, i, inv))
            book.update(_bagi(shorts, g / 2.0, -1, sig, i, inv))
        if tujuh:
            if book is not None:
                books[wd] = book
            acc: Dict[str, float] = {}
            for b in books.values():
                for a, x in b.items():
                    acc[a] = acc.get(a, 0.0) + x
            n = len(books)
            cur = {a: x / n for a, x in acc.items() if abs(x) > 1e-12} if n else {}
        else:
            cur = book or {}
        if any(close[a][i] is not None for a in assets):
            out.append(Target(bot_id, t, cur, {"n_aset": sum(1 for a in assets if close[a][i] is not None)}))
    return out
