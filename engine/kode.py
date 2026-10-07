"""P167b (epik 12 §3.2, F-D125): jenis `code` - fungsi kode penerbit, dijalankan di sandbox berlapis. Kode PRIVAT (keputusan builder 6 Okt malam).

Kontrak penerbit (Python, <= 16 KB):

    PARAMS = {"N": 60}                       # angka BERNAMA yang boleh digeser G5 (<= 6, bukan nol)
    def target(bars, params):                # dipanggil SEKALI per bar i; bars = {aset: {"t","o","h","l","c","v": tuple sampai bar i}}
        c = bars["BTCUSDT"]["c"]             #   (pemetaan + tuple tak bisa diubah; tidak pernah memuat bar sesudah i)
        return {"BTCUSDT": 1.0} if len(c) > params["N"] and c[-1] > c[-1 - params["N"]] else {}

Bobot berlaku untuk return bar i+1 (konvensi mesin, sama dengan `rule`). Pagar (lapis demi lapis):
  1. `periksa` - analisis statis AST DAFTAR-IZIN: definisi fungsi, aritmetika, perbandingan, if/for/while, comprehension, lambda; impor hanya
     `math` + `statistics` (anggota yang diizinkan saja); nama berawalan `_` ditolak (dunder); atribut hanya dari daftar-izin (tanpa `format`,
     tanpa `gi_frame`/`f_globals`); tanpa try/with/class/global/nonlocal/yield; tanpa open/eval/exec/compile/getattr/print/id/hash; <= 16 KB.
  2. `instrumentasi` - `_l()` di tiap badan fungsi, perulangan, comprehension, lambda: anggaran langkah PER panggilan `target`.
  3. Proses anak (`engine/kode_anak.py`, `python -s -S -P`, lingkungan kosong) memasang batas CPU / memori / ukuran berkas 0 / deskriptor pada
     dirinya sendiri, builtins terbatas, tanpa modul jaringan; induk menegakkan batas waktu dinding.
  4. Dijalankan DUA kali di dua proses dengan `PYTHONHASHSEED` berbeda: keluaran harus IDENTIK (menangkap urutan set/hash); bobot terhingga,
     gross <= 1, kunci = aset yang punya bar.
  5. Uji kausalitas: sampel bar dihitung ulang di namespace SEGAR pada data terpotong; bobot harus sama dengan jalan berurutan (menangkap keadaan
     global / argumen bawaan yang bisa diubah). Kausal oleh konstruksi; uji ini menangkap ketergantungan pada riwayat panggilan.
  6. PRIVAT: kode tidak pernah masuk repo / GitHub Actions publik. Salinan publik formulir hanya memuat `spec.kode` = {sha, ukuran, params}. Kode
     disimpan di volume gerbang dan dijalankan PELARI terpisah tanpa rahasia (`tools/pelari_kode.py`, layanan Railway sendiri) yang hanya
     mengembalikan DATA berbatas (bobot per bar per varian + hasil uji); `PelariData` memvalidasi DATA itu lagi di pihak tepercaya, lalu G1-G11.

Jenis `code` BELUM dibuka untuk pengguna luar (`submission.ENABLED_KINDS`): menunggu persetujuan builder atas jalur privat atau repo privat.
Label kepercayaan: `LABEL_KEPERCAYAAN`.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import random
import re
import statistics
import subprocess
import sys
import tempfile
import unicodedata
from typing import Any, Dict, List, Optional, Sequence, Tuple

KODE_METHOD = "CODE"                         # `BotSpec.template` bot code: kunci ke REGISTRY / replay
PARAM_NAMA = "kode"                          # `BotSpec.param_nama`; `param` = sha kode
PENGGARIS = {"fee_bps_sisi": 7, "funding": "nyata dua sisi"}      # milik kami (sama dengan rule / B1 / B2): penerbit tidak menentukan biaya
LABEL_KEPERCAYAAN = "kode privat, tidak bisa diulang publik"
CATATAN_PENINJAU = "kode dikirim ke penyedia model peninjau (xkiro) untuk tahap 2; laporan publik tidak mengutip kode"
ANAK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kode_anak.py")
PARAM_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,15}")
SHA_RE = re.compile(r"0x[0-9a-f]{64}")
MODUL = ("math", "statistics")

LIMITS: Dict[str, Any] = {
    "ukuran_maks": 16 * 1024, "simpul_maks": 4000, "teks_maks": 64, "max_parameter": 6, "nilai_maks": 1_000_000,
    "langkah_per_panggilan": 200_000, "rekursi_maks": 200, "cpu_s": 120, "memori_mb": 768, "waktu_dinding_s": 180,
    "keluaran_maks_byte": 48 * 1024 * 1024, "varian_maks": 40,
}

# Anggota modul yang boleh dipakai (proksi di anak hanya berisi ini). `statistics` sengaja tanpa NormalDist (samples() memakai acak) dan tanpa
# atribut modul (`statistics.sys`, `statistics.random` = pintu keluar).
IZIN_MODUL = {
    "math": tuple(sorted(n for n in dir(math) if not n.startswith("_"))),
    "statistics": ("correlation", "covariance", "fmean", "geometric_mean", "harmonic_mean", "linear_regression", "mean", "median",
                   "median_grouped", "median_high", "median_low", "mode", "multimode", "pstdev", "pvariance", "quantiles", "stdev", "variance"),
}
IZIN_MODUL["statistics"] = tuple(n for n in IZIN_MODUL["statistics"] if hasattr(statistics, n))
METODE = ("append", "extend", "insert", "pop", "remove", "index", "count", "sort", "reverse", "copy", "clear", "get", "items", "keys", "values",
          "update", "setdefault", "add", "discard", "union", "intersection", "difference", "issubset", "issuperset", "startswith", "endswith",
          "upper", "lower", "strip", "split", "join", "replace", "is_integer")
ATRIBUT = frozenset(METODE) | frozenset(IZIN_MODUL["math"]) | frozenset(IZIN_MODUL["statistics"])
BUILTINS = ("abs", "all", "any", "bool", "dict", "divmod", "enumerate", "filter", "float", "frozenset", "int", "isinstance", "len", "list", "map",
            "max", "min", "pow", "range", "reversed", "round", "set", "sorted", "str", "sum", "tuple", "zip")
NAMA_TERLARANG = frozenset((
    "eval", "exec", "compile", "open", "getattr", "setattr", "delattr", "hasattr", "globals", "locals", "vars", "dir", "type", "object",
    "super", "input", "print", "breakpoint", "help", "id", "hash", "memoryview", "bytearray", "bytes", "exit", "quit", "classmethod",
    "staticmethod", "property", "iter", "next", "callable", "issubclass", "format", "repr", "ascii", "license", "credits", "copyright",
    "aiter", "anext", "builtins", "import_module", "os", "sys", "subprocess", "socket"))
_SIMPUL = (
    ast.Module, ast.Expr, ast.Import, ast.ImportFrom, ast.alias, ast.Assign, ast.AugAssign, ast.FunctionDef, ast.arguments, ast.arg, ast.Return,
    ast.If, ast.For, ast.While, ast.Break, ast.Continue, ast.Pass, ast.BoolOp, ast.And, ast.Or, ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div,
    ast.FloorDiv, ast.Mod, ast.Pow, ast.UnaryOp, ast.USub, ast.UAdd, ast.Not, ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.In, ast.NotIn, ast.Is, ast.IsNot, ast.IfExp, ast.Call, ast.keyword, ast.Name, ast.Load, ast.Store, ast.Constant, ast.Tuple, ast.List,
    ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp, ast.comprehension, ast.Subscript, ast.Slice, ast.Attribute,
    ast.Lambda)


class KodeError(Exception):
    """Pelari menolak / kode gagal di sandbox. Pesan tidak memuat teks kode pengguna."""


# ---------------------------------------------------------------- 1. analisis statis (input musuh: tidak pernah melempar)

def _num(v: Any) -> bool:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    return math.isfinite(v) and abs(v) <= LIMITS["nilai_maks"]


def _teks_jahat(src: str) -> Optional[str]:
    for ch in src:
        if ch in "\n\t\r":
            continue
        cat = unicodedata.category(ch)
        if cat in ("Cc", "Cf", "Cs", "Co", "Cn", "Zl", "Zp"):
            return "karakter kontrol/format tersembunyi"
    return None


def _docstrings(tree: ast.Module) -> set:
    """id simpul Constant yang menjadi docstring modul / fungsi: dikecualikan dari batas panjang teks (tetap <= 2000 karakter)."""
    out = set()
    for node in [tree] + [x for x in ast.walk(tree) if isinstance(x, ast.FunctionDef)]:
        b = node.body
        if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) and isinstance(b[0].value.value, str):
            out.add(id(b[0].value))
    return out


def _simpul(n: ast.AST, docs: set, out: List[str]) -> None:
    if not isinstance(n, _SIMPUL):
        out.append(f"baris {getattr(n, 'lineno', '?')}: konstruksi {type(n).__name__} tidak diizinkan")
        return
    if isinstance(n, ast.Name):
        if n.id.startswith("_"):
            out.append(f"baris {n.lineno}: nama berawalan '_' tidak diizinkan")
        elif n.id in NAMA_TERLARANG:
            out.append(f"baris {n.lineno}: nama {n.id!r} tidak diizinkan")
    elif isinstance(n, ast.Attribute):
        if not isinstance(n.ctx, ast.Load):
            out.append(f"baris {n.lineno}: menulis atribut tidak diizinkan")
        elif n.attr.startswith("_") or n.attr not in ATRIBUT:
            out.append(f"baris {n.lineno}: atribut {n.attr[:20]!r} tidak ada di daftar-izin")
    elif isinstance(n, ast.Import):
        for a in n.names:
            if a.name not in MODUL or (a.asname or "").startswith("_"):
                out.append(f"baris {n.lineno}: impor hanya {list(MODUL)}")
    elif isinstance(n, ast.ImportFrom):
        if n.level != 0 or n.module not in MODUL:
            out.append(f"baris {n.lineno}: impor hanya {list(MODUL)}")
        else:
            for a in n.names:
                if a.name not in IZIN_MODUL[n.module] or (a.asname or "").startswith("_"):
                    out.append(f"baris {n.lineno}: {n.module}.{a.name[:20]} tidak ada di daftar-izin")
    elif isinstance(n, ast.Constant):
        v = n.value
        if not (v is None or isinstance(v, (bool, int, float, str))):
            out.append(f"baris {n.lineno}: konstanta {type(v).__name__} tidak diizinkan")
        elif isinstance(v, str) and len(v) > (2000 if id(n) in docs else LIMITS["teks_maks"]):
            out.append(f"baris {n.lineno}: teks lebih dari {LIMITS['teks_maks']} karakter")
    elif isinstance(n, ast.FunctionDef):
        a = n.args
        if n.decorator_list or n.returns is not None or a.vararg or a.kwarg or a.kwonlyargs or a.posonlyargs or getattr(n, "type_params", None):
            out.append(f"baris {n.lineno}: fungsi tanpa dekorator, anotasi, *args/**kwargs")
        if n.name.startswith("_"):
            out.append(f"baris {n.lineno}: nama fungsi berawalan '_' tidak diizinkan")
        for x in a.args:
            if x.annotation is not None or x.arg.startswith("_"):
                out.append(f"baris {n.lineno}: argumen tanpa anotasi dan tanpa awalan '_'")
    elif isinstance(n, ast.Lambda):
        a = n.args
        if a.vararg or a.kwarg or a.kwonlyargs or a.posonlyargs or any(x.arg.startswith("_") for x in a.args):
            out.append(f"baris {n.lineno}: lambda tanpa *args/**kwargs dan tanpa awalan '_'")
    elif isinstance(n, ast.comprehension):
        if n.is_async:
            out.append("comprehension async tidak diizinkan")
    elif isinstance(n, ast.keyword):
        if n.arg is None or n.arg.startswith("_"):
            out.append(f"baris {getattr(n, 'lineno', '?')}: **kwargs / kata kunci berawalan '_' tidak diizinkan")
    elif isinstance(n, (ast.Assign, ast.AugAssign)):
        for t in (n.targets if isinstance(n, ast.Assign) else [n.target]):
            for x in ast.walk(t):
                if isinstance(x, ast.Attribute):
                    out.append(f"baris {n.lineno}: menulis atribut tidak diizinkan")


def periksa(src: Any) -> Tuple[List[str], Dict[str, Any]]:
    """-> (masalah, info). info = {sha, ukuran, params, simpul}. Gagal TERTUTUP: apa pun yang tak terduga = ditolak, bukan dilempar."""
    try:
        return _periksa(src)
    except Exception as e:                                                      # noqa: BLE001
        return [f"analisis kode gagal tak terduga ({type(e).__name__}): ditolak"], {}


def sha_kode(src: str) -> str:
    return "0x" + hashlib.sha256(src.encode("utf-8")).hexdigest()


def _periksa(src: Any) -> Tuple[List[str], Dict[str, Any]]:
    if not isinstance(src, str) or not src.strip():
        return ["kode harus teks tak kosong"], {}
    raw = src.encode("utf-8", errors="strict")
    if len(raw) > LIMITS["ukuran_maks"]:
        return [f"kode {len(raw)} byte > {LIMITS['ukuran_maks']} byte"], {}
    bad = _teks_jahat(src)
    if bad:
        return [bad], {}
    try:
        tree = ast.parse(src, mode="exec")
    except SyntaxError as e:
        return [f"kode tidak bisa di-parse (baris {e.lineno})"], {}
    except (ValueError, RecursionError, MemoryError) as e:
        return [f"kode tidak bisa di-parse ({type(e).__name__})"], {}
    out: List[str] = []
    nodes = list(ast.walk(tree))
    if len(nodes) > LIMITS["simpul_maks"]:
        return [f"kode lebih dari {LIMITS['simpul_maks']} simpul AST"], {}
    docs = _docstrings(tree)
    for n in nodes:
        _simpul(n, docs, out)
        if len(out) >= 30:
            break
    params: Optional[Dict[str, Any]] = None
    n_target = 0
    for i, st in enumerate(tree.body):
        if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant) and isinstance(st.value.value, str) and i == 0:
            continue
        if isinstance(st, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(st, ast.FunctionDef):
            if st.name == "target":
                n_target += 1
                if len(st.args.args) != 2 or st.args.defaults:
                    out.append(f"baris {st.lineno}: target harus menerima tepat dua argumen (bars, params) tanpa nilai bawaan")
            continue
        if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
            name = st.targets[0].id
            try:
                val = ast.literal_eval(st.value)
            except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
                out.append(f"baris {st.lineno}: tingkat modul hanya boleh konstanta literal (hitungan masuk ke fungsi)")
                continue
            if name == "PARAMS":
                if params is not None:
                    out.append(f"baris {st.lineno}: PARAMS didefinisikan dua kali")
                params = val if isinstance(val, dict) else {}
                if not isinstance(val, dict):
                    out.append(f"baris {st.lineno}: PARAMS harus dict {{nama: angka}}")
            continue
        out.append(f"baris {getattr(st, 'lineno', '?')}: tingkat modul hanya docstring, impor, konstanta, dan def")
    if n_target != 1:
        out.append("kode harus mendefinisikan tepat satu fungsi target(bars, params)")
    if params is None:
        out.append("kode harus mendefinisikan PARAMS = {nama: angka} (boleh kosong, tetapi tanpa parameter bernama G5 gagal)")
        params = {}
    out += validate_params(params, "PARAMS")
    if out:
        return out[:30], {}
    return [], {"sha": sha_kode(src), "ukuran": len(raw), "params": canonical_params(params), "simpul": len(nodes)}


def validate_params(params: Any, path: str) -> List[str]:
    if not isinstance(params, dict) or len(params) > LIMITS["max_parameter"]:
        return [f"{path}: harus objek dengan paling banyak {LIMITS['max_parameter']} parameter bernama"]
    out = []
    for k, v in params.items():
        if not isinstance(k, str) or not PARAM_NAME.fullmatch(k):
            out.append(f"{path}.{str(k)[:20]!r}: nama parameter tidak valid ([A-Za-z][A-Za-z0-9_]{{0,15}})")
        elif not _num(v) or v == 0:
            out.append(f"{path}.{k}: harus angka hingga bukan nol, |x| <= {LIMITS['nilai_maks']:g} (nol tidak bisa digeser G5)")
    return out


def canonical_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Tipe dihormati: bilangan bulat tetap int, desimal tetap float (60 != 60.0: sumber kodenya pun berbeda); kunci terurut."""
    return {k: (int(v) if isinstance(v, int) and not isinstance(v, bool) else float(v)) for k, v in sorted(params.items())}


def validate_meta(meta: Any, path: str = "spec.kode") -> List[str]:
    """`spec.kode` di formulir publik: {sha, ukuran, params}. Teks kode TIDAK ada di formulir (privat; dicocokkan dengan sha saat diterima)."""
    if not isinstance(meta, dict) or set(meta) != {"sha", "ukuran", "params"}:
        return [f"{path}: harus objek {{sha, ukuran, params}} (teks kode dikirim terpisah dan tidak pernah publik)"]
    out = []
    if not isinstance(meta["sha"], str) or not SHA_RE.fullmatch(meta["sha"]):
        out.append(f"{path}.sha: harus sha256 0x + 64 hex kecil")
    u = meta["ukuran"]
    if isinstance(u, bool) or not isinstance(u, int) or not 1 <= u <= LIMITS["ukuran_maks"]:
        out.append(f"{path}.ukuran: bilangan bulat 1..{LIMITS['ukuran_maks']}")
    out += validate_params(meta["params"], f"{path}.params")
    return out


def cocok_meta(src: str, meta: Dict[str, Any]) -> List[str]:
    """Teks kode yang dikirim harus cocok dengan `spec.kode` yang ditandatangani: sha, ukuran, PARAMS, dan lolos analisis statis."""
    masalah, info = periksa(src)
    if masalah:
        return [f"kode: {m}" for m in masalah]
    out = []
    if info["sha"] != meta.get("sha"):
        out.append("kode: sha tidak cocok dengan spec.kode.sha yang ditandatangani")
    if info["ukuran"] != meta.get("ukuran"):
        out.append("kode: ukuran tidak cocok dengan spec.kode.ukuran")
    if json.dumps(info["params"], sort_keys=True) != json.dumps(canonical_params(meta.get("params") or {}), sort_keys=True):
        out.append("kode: PARAMS di kode tidak sama dengan spec.kode.params")
    return out


# ---------------------------------------------------------------- 2. instrumentasi anggaran langkah

class _Langkah(ast.NodeTransformer):
    @staticmethod
    def _call() -> ast.Call:
        return ast.Call(func=ast.Name(id="_l", ctx=ast.Load()), args=[], keywords=[])

    def _badan(self, n):
        self.generic_visit(n)
        n.body.insert(0, ast.Expr(value=self._call()))
        return n

    visit_FunctionDef = _badan
    visit_For = _badan
    visit_While = _badan

    def visit_comprehension(self, n):
        self.generic_visit(n)
        n.ifs.insert(0, self._call())
        return n

    def visit_Lambda(self, n):
        self.generic_visit(n)
        n.body = ast.BoolOp(op=ast.And(), values=[self._call(), n.body])
        return n


def instrumentasi(src: str) -> str:
    """Sumber yang SUDAH lolos `periksa` -> sumber dengan `_l()` (anggaran langkah). Nama `_l` tidak bisa dibayangi pengguna (awalan `_` ditolak)."""
    tree = _Langkah().visit(ast.parse(src))
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


# ---------------------------------------------------------------- 3. pelari (lokal = proses anak; data = keluaran pelari terpisah)

def bars_payload(md, universe: Sequence[str]) -> Dict[str, Dict[str, list]]:
    """Bar publik (perp) aset universe yang punya data: kolom t o h l c v. Ini SATU-SATUNYA masukan kode selain params."""
    out: Dict[str, Dict[str, list]] = {}
    for a in sorted(set(universe)):
        s = md.perp.get(a)
        if s is not None and len(s):
            out[a] = {"t": list(s.t), "o": list(s.o), "h": list(s.h), "l": list(s.l), "c": list(s.c), "v": list(s.v)}
    return out


def data_sha(bars: Dict[str, Dict[str, list]]) -> str:
    return "0x" + hashlib.sha256(json.dumps(bars, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def sampel_kausal(grid: Sequence[int], n: int, seed: int = 20261002) -> List[int]:
    """Bar sampel uji kausalitas (seperti G1: dari hari ke-60 ke atas, dipilih dari seed, ditambah hari terakhir)."""
    days = list(grid)
    if not days:
        return []
    pool = days[60:-1] if len(days) > 62 else days[:-1]
    picks = sorted(random.Random(seed).sample(pool, min(n, len(pool)))) if pool else []
    return picks + [days[-1]]


# Sebab proses anak berhenti dari kode keluarnya. POSIX: sinyal (kode negatif) dari setrlimit. Windows: NTSTATUS dari Job Object
# (STATUS_QUOTA_EXCEEDED = waktu CPU per proses habis) atau kegagalan sistem lain.
SINYAL_POSIX = {24: "batas CPU", 9: "dihentikan (batas CPU/memori)", 25: "batas ukuran berkas"}
STATUS_WINDOWS = {0xC0000044: "batas CPU", 0xC0000017: "batas memori", 0xC00000FD: "rekursi terlalu dalam"}


def sebab_keluar(returncode: int) -> str:
    if os.name == "nt":
        return STATUS_WINDOWS.get(returncode & 0xFFFFFFFF, f"proses anak keluar {returncode}")
    return SINYAL_POSIX.get(-returncode if returncode < 0 else 0, f"proses anak keluar {returncode}")


def _anak(job: Dict[str, Any], benih: int, batas: Dict[str, Any]) -> Dict[str, Any]:
    """Satu proses anak. Lingkungan kosong kecuali PYTHONHASHSEED; cwd = folder sementara kosong; tanpa jalur repo di sys.path."""
    payload = json.dumps(job, separators=(",", ":"), allow_nan=False).encode("ascii")
    with tempfile.TemporaryDirectory(prefix="kode-") as cwd:
        try:
            p = subprocess.run([sys.executable, "-s", "-S", "-P", ANAK], input=payload, capture_output=True, cwd=cwd,
                               env={"PYTHONHASHSEED": str(int(benih))}, timeout=float(batas["waktu_dinding_s"]))
        except subprocess.TimeoutExpired:
            return {"ok": False, "galat": f"batas waktu dinding {batas['waktu_dinding_s']} s", "bar": None}
    if p.returncode != 0:
        return {"ok": False, "galat": sebab_keluar(p.returncode), "bar": None}
    if len(p.stdout) > int(batas["keluaran_maks_byte"]) + 1024:
        return {"ok": False, "galat": "keluaran terlalu besar", "bar": None}
    try:
        out = json.loads(p.stdout.decode("ascii"))
    except (ValueError, UnicodeDecodeError):
        return {"ok": False, "galat": "keluaran anak tidak terbaca", "bar": None}
    return out if isinstance(out, dict) else {"ok": False, "galat": "keluaran anak bukan objek", "bar": None}


def jalankan(src: str, bars: Dict[str, Dict[str, list]], varian: Dict[str, Dict[str, Any]], sampel: Sequence[int] = (), dasar: Optional[str] = None,
             batas: Optional[Dict[str, Any]] = None, dua_kali: bool = True) -> Dict[str, Any]:
    """Jalankan kode pada bar publik untuk tiap varian params (+ sampel kausalitas pada varian `dasar`). Dua proses dengan PYTHONHASHSEED 1 dan 2
    bila `dua_kali`. -> DATA: {v, kode_sha, data_sha, varian: {label: [[t, {aset: bobot}]]}, kausal: {n, beda}, deterministik, ok, galat, bar}.
    `ok` = semua jalan selesai tanpa galat (bobot sah); `deterministik` = None bila gagal, False bila dua jalan berbeda (vonis G1, bukan galat pelari).
    Inilah yang dikerjakan PELARI (`tools/pelari_kode.py`) - fungsi ini tidak butuh rahasia apa pun."""
    b = dict(LIMITS, **(batas or {}))
    masalah, info = periksa(src)
    base = {"v": 1, "kode_sha": sha_kode(src) if isinstance(src, str) else None, "data_sha": data_sha(bars), "varian": {}, "kausal": {"n": 0, "beda": []},
            "deterministik": None, "ok": False, "galat": None, "bar": None}
    if masalah:
        return dict(base, galat="analisis statis: " + "; ".join(masalah[:5]))
    if not varian or len(varian) > b["varian_maks"]:
        return dict(base, galat=f"jumlah varian harus 1..{b['varian_maks']}")
    for lab, p in varian.items():
        if validate_params(p, f"varian {str(lab)[:16]}") or set(p) != set(info["params"]):
            return dict(base, galat="varian params tidak sah atau namanya beda dari PARAMS")
    job = {"kode": instrumentasi(src), "bars": bars, "varian": varian, "sampel": list(sampel), "dasar_kausal": dasar,
           "batas": {k: b[k] for k in ("langkah_per_panggilan", "rekursi_maks", "cpu_s", "memori_mb", "keluaran_maks_byte")}, "izin_modul": IZIN_MODUL}
    r1 = _anak(job, 1, b)
    if not r1.get("ok"):
        return dict(base, galat=r1.get("galat"), bar=r1.get("bar"))
    det = True
    if dua_kali:
        r2 = _anak(job, 2, b)
        if not r2.get("ok"):
            return dict(base, galat="jalan kedua: " + str(r2.get("galat")), bar=r2.get("bar"))
        det = json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)
    out = dict(base, varian=r1["varian"], kausal=r1.get("kausal", {"n": 0, "beda": []}), deterministik=det if dua_kali else None, ok=True)
    if not det:
        out["galat"] = "dua jalan dengan PYTHONHASHSEED berbeda menghasilkan bobot berbeda (tidak deterministik)"
    return out


def validasi_data(d: Any, bars: Dict[str, Dict[str, list]], varian: Dict[str, Dict[str, Any]], universe: Sequence[str]) -> List[str]:
    """DATA dari pelari melewati batas kepercayaan: diperiksa lagi di pihak tepercaya. Bentuk, sha data, grid = gabungan bar, kunci = aset yang
    punya bar sampai hari itu, bobot terhingga, gross <= 1, semua varian yang diminta ada."""
    if not isinstance(d, dict) or d.get("v") != 1:
        return ["DATA pelari bukan objek v1"]
    if d.get("data_sha") != data_sha(bars):
        return ["DATA pelari dihitung pada bar lain (data_sha beda)"]
    if not d.get("ok"):
        return [f"pelari gagal: {str(d.get('galat'))[:200]}"]
    grid = sorted({t for a in bars for t in bars[a]["t"]})
    first = {a: bars[a]["t"][0] for a in bars}
    uni = set(universe)
    out: List[str] = []
    vs = d.get("varian")
    if not isinstance(vs, dict) or set(vs) != set(varian):
        return ["DATA pelari tidak memuat varian yang diminta persis"]
    for lab, rows in vs.items():
        if not isinstance(rows, list) or len(rows) != len(grid):
            out.append(f"varian {lab}: jumlah bar {len(rows) if isinstance(rows, list) else '?'} != grid {len(grid)}")
            continue
        for (t, w), g in zip(rows, grid):
            if t != g or not isinstance(w, dict):
                out.append(f"varian {lab}: bar {t} tidak urut dengan grid")
                break
            gross = 0.0
            for a, x in w.items():
                if a not in uni or a not in first or first[a] > t or isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
                    out.append(f"varian {lab}: bobot tidak sah di bar {t}")
                    break
                gross += abs(x)
            if gross > 1.0 + 1e-9:
                out.append(f"varian {lab}: gross > 1 di bar {t}")
            if out:
                break
    k = d.get("kausal")
    if not isinstance(k, dict) or not isinstance(k.get("beda"), list) or not isinstance(k.get("n"), int):
        out.append("DATA pelari tanpa hasil uji kausalitas")
    if not isinstance(d.get("deterministik"), bool):
        out.append("DATA pelari tanpa hasil uji determinisme (pelari wajib menjalankan dua kali)")
    return out[:20]


class PelariLokal:
    """Pelari di mesin ini (proses anak). Teks kode diambil dari `sumber` (sha -> teks) yang diisi pemegang kode privat (volume gerbang / tes)."""

    def __init__(self, sumber: Optional[Dict[str, str]] = None, batas: Optional[Dict[str, Any]] = None):
        self.sumber = dict(sumber or {})
        self.batas = batas
        self._memo: Dict[Tuple[str, str, str, bool], Dict[str, Any]] = {}

    def daftarkan(self, src: str) -> str:
        sha = sha_kode(src)
        self.sumber[sha] = src
        return sha

    def hasil(self, sha: str, bars: Dict[str, Dict[str, list]], varian: Dict[str, Dict[str, Any]], sampel: Sequence[int] = (),
              dasar: Optional[str] = None, dua_kali: bool = False) -> Dict[str, Any]:
        if sha not in self.sumber:
            raise KodeError("teks kode tidak tersedia di pelari ini (kode privat: hanya pemegang volume gerbang)")
        key = (sha, data_sha(bars), json.dumps([varian, list(sampel), dasar], sort_keys=True), dua_kali)
        if key not in self._memo:
            if len(self._memo) > 64:
                self._memo.clear()
            self._memo[key] = jalankan(self.sumber[sha], bars, varian, sampel, dasar, self.batas, dua_kali=dua_kali)
        return self._memo[key]


class PelariData:
    """Pihak TEPERCAYA tanpa teks kode: menyajikan DATA pelari terpisah yang SUDAH divalidasi (`validasi_data`). Permintaan pada data atau varian
    lain = galat (gagal tertutup), bukan tebakan."""

    def __init__(self, sha: str, bars: Dict[str, Dict[str, list]], data: Dict[str, Any], varian: Dict[str, Dict[str, Any]], universe: Sequence[str]):
        masalah = validasi_data(data, bars, varian, universe)
        if data.get("kode_sha") != sha:
            masalah.insert(0, "DATA pelari untuk kode lain (kode_sha beda)")
        if masalah:
            raise KodeError("; ".join(masalah[:3]))
        self.sha, self.dsha, self.data = sha, data_sha(bars), data
        self.by_params = {json.dumps(canonical_params(p), sort_keys=True): lab for lab, p in varian.items()}

    def hasil(self, sha: str, bars: Dict[str, Dict[str, list]], varian: Dict[str, Dict[str, Any]], sampel: Sequence[int] = (),
              dasar: Optional[str] = None, dua_kali: bool = False) -> Dict[str, Any]:
        if sha != self.sha or data_sha(bars) != self.dsha:
            raise KodeError("DATA pelari tidak mencakup kode / bar ini (mis. data terpotong): gagal tertutup")
        out = {}
        for lab, p in varian.items():
            key = json.dumps(canonical_params(p), sort_keys=True)
            if key not in self.by_params:
                raise KodeError("varian params ini tidak dihitung pelari")
            out[lab] = self.data["varian"][self.by_params[key]]
        return dict(self.data, varian=out)


_PELARI: List[Any] = [PelariLokal()]


def pelari() -> Any:
    return _PELARI[0]


def pasang_pelari(p: Any) -> Any:
    """Ganti pelari aktif (pihak tepercaya: `PelariData`; pemegang kode / tes: `PelariLokal`). -> pelari sebelumnya."""
    lama = _PELARI[0]
    _PELARI[0] = p
    return lama


# ---------------------------------------------------------------- 4. integrasi mesin: target, G1, G5, percobaan

def _rows_ke_target(bot_id: str, rows: List[list], bars: Dict[str, Dict[str, list]]):
    from .target import Target
    ada = {a: set(bars[a]["t"]) for a in bars}
    return [Target(bot_id, int(t), {a: float(x) for a, x in sorted(w.items())}, {"n_aset": sum(1 for a in ada if t in ada[a])}) for t, w in rows]


def targets(spec, data):
    """REGISTRY["CODE"]: target harian bot code dari pelari aktif (varian dasar = params di spesifikasi). Gagal = KodeError (gerbang gagal tertutup)."""
    meta = spec.konstanta["kode"]
    bars = bars_payload(data, spec.universe)
    if not bars:
        return []
    r = pelari().hasil(meta["sha"], bars, {"dasar": meta["params"]})
    if not r.get("ok") or "dasar" not in (r.get("varian") or {}):
        raise KodeError(f"kode gagal di sandbox: {str(r.get('galat'))[:200]}")
    return _rows_ke_target(spec.bot_id, r["varian"]["dasar"], bars)


def uji_kausal(spec, data, n_sampel: int, seed: int) -> Tuple[bool, str]:
    """G1 untuk bot code: sampel bar dihitung ulang di namespace segar pada data terpotong (harus sama) + dua proses PYTHONHASHSEED berbeda (harus sama)."""
    meta = spec.konstanta["kode"]
    bars = bars_payload(data, spec.universe)
    grid = sorted({t for a in bars for t in bars[a]["t"]})
    samp = sampel_kausal(grid, n_sampel, seed)
    r = pelari().hasil(meta["sha"], bars, {"dasar": meta["params"]}, samp, "dasar", dua_kali=True)
    if not r.get("ok"):
        return False, f"kode gagal di sandbox: {str(r.get('galat'))[:160]}"
    k = r.get("kausal") or {}
    beda = k.get("beda") or []
    n = int(k.get("n") or 0)
    det = bool(r.get("deterministik"))
    ok = det and n > 0 and not beda
    return ok, (f"{n - len(beda)}/{n} sampel identik (namespace segar, data terpotong); deterministik {'ya' if det else 'TIDAK'} "
                f"(dua proses, PYTHONHASHSEED 1 dan 2)")


def geser(v: Any, f: float) -> Any:
    """Varian G5 satu parameter: bulat tetap bulat (tanda dipertahankan, |x| >= 1), desimal tetap desimal."""
    if isinstance(v, int) and not isinstance(v, bool):
        x = int(round(v * f))
        return max(1, x) if v > 0 else min(-1, x)
    return float(v) * f


def kelompok_plateau(params: Dict[str, Any], faktor: Tuple[float, ...]) -> List[Tuple[str, List[Tuple[str, Dict[str, Any]]]]]:
    """Sama dengan `rule.kelompok_plateau`: satu kelompok per parameter bernama + 'semua' bila > 1 parameter; varian kembar dibuang."""
    def kelompok(nama: str, names: List[str]):
        seen = {tuple(params[k] for k in names)}
        rows = []
        for f in faktor:
            vals = tuple(geser(params[k], f) for k in names)
            if vals in seen:
                continue
            seen.add(vals)
            rows.append((f"{vals[0]:g}" if len(names) == 1 else f"x{f:g}", {**params, **dict(zip(names, vals))}))
        return nama, rows
    groups = [kelompok(k, [k]) for k in params]
    if len(params) > 1:
        groups.append(kelompok("semua", list(params)))
    return groups


def varian_semua(params: Dict[str, Any], faktor: Tuple[float, ...]) -> Dict[str, Dict[str, Any]]:
    """Semua varian yang dibutuhkan gerbang (dasar + G5) - yang diminta pihak tepercaya dari pelari sekali jalan."""
    out = {"dasar": dict(params)}
    for nama, rows in kelompok_plateau(params, faktor):
        for label, p in rows:
            out[f"{nama}:{label}"] = p
    return out


def varian_g5(params: Dict[str, Any], n_faktor: int) -> int:
    m = len(params)
    return n_faktor * (m + (1 if m > 1 else 0))
