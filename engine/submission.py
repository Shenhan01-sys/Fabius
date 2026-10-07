"""Formulir pengajuan bot penerbit (program kolaborasi terbuka, F-D71/F-D72): skema tertutup, validasi ketat, identitas bertanda tangan.

Prinsip:
  - **Skema tertutup**: field tak dikenal ditolak (tidak ada tempat menyelundupkan instruksi). Teks bebas dibatasi panjangnya dan
    ditolak bila memuat karakter kontrol/format/privat atau karakter tak terlihat (daftar-izin berdasarkan kategori Unicode, bukan
    daftar-hitam). Seluruh isi formulir adalah INPUT MUSUH bagi pembacanya (FE, peninjau-bot, orang): string API = input musuh.
    Pesan masalah tidak pernah memantulkan teks mentah dari kiriman (hanya `repr` yang dipotong).
  - **Satu metode + satu parameter**: untuk `kind = template` penerbit hanya memilih template yang sudah ada di mesin, SATU nilai
    parameter, dan universe. Konstanta dan penggaris biaya milik kami (penerbit tidak boleh menentukan penggaris-nya sendiri).
  - **Identitas jelas**: dompet penerbit dan dompet bagi hasil berformat checksum EIP-55; seluruh pengajuan ditandatangani
    (EIP-712) oleh dompet penerbit; dompet bagi hasil yang berbeda harus ikut menandatangani (kalau tidak, orang bisa menunjuk dompet
    korban untuk memblokirnya). Kontak TIDAK ikut hash/tanda tangan (hash tanda tangan publik tidak boleh jadi oracle tebak-kontak).
  - **Pembunuh = data**: syarat mematikan bot berbentuk terstruktur (metrik, pembanding, ambang berbatas, jendela) supaya bisa
    ditegakkan kode (`slots.killer_triggered`), bukan janji.
  - Angka di bagian `evidence.klaim` adalah KLAIM penerbit; yang dihitung sebagai bukti hanya keluaran peninjau-bot kami.
  - **Dibuka bertahap** (`ENABLED_KINDS`; jenis yang belum dibuka ada di skema tetapi ditolak `validate`): `template` (2 Okt malam), `rule`
    (P167a, 7 Okt; epik 12). Skema v2 (7 Okt): metode SEPENUHNYA dari penerbit (builder: "biarkan semua input itu dari user").
    `code` (P167b) dibangun tetapi TETAP TERTUTUP sampai builder menyetujui jalur privat / repo privat; `feed` (P167c) lihat `ENABLED_KINDS`.

Jenis bot: `template` (metode yang sudah ada di mesin + SATU parameter; dipertahankan, tidak lagi jalur utama), `rule` (aturan deklaratif JSON,
`engine/rule.py`, dijalankan mesin kami; replay penuh), `code` (fungsi kode pengguna di sandbox, `engine/kode.py`; PRIVAT: formulir publik hanya
memuat `spec.kode` = {sha, ukuran, params}, teks kode dikirim terpisah dan disimpan privat; P167b), `feed` (penerbit menjalankan programnya sendiri
dan mengomit bobot target bertanda tangan SEBELUM penutupan tiap bar lewat `POST /bots/feed/commit`, `engine/feed.py`; satu-satunya bukti = rekam
jejak maju yang ter-anchor; gerbang replay N/A; P167c).
"""
from __future__ import annotations

import copy
import dataclasses
import datetime as dt
import ipaddress
import math
import re
import unicodedata
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlsplit

from . import chain, feed as feedmod, kode as kodemod, rule as rulemod
from .bots import REGISTRY
from .spec import PERP_UNIVERSE, SPECS, BotSpec, sha0x

SCHEMA_V = 2
KINDS = ("template", "rule", "code", "feed")
ENABLED_KINDS = ("template", "rule", "feed")        # P167c dibuka 7 Okt (deploy = langkah builder); code (P167b) TERTUTUP
TEMPLATES = tuple(sorted(k for k in SPECS if k in REGISTRY))     # metode bawaan mesin untuk kind=template (RULE bukan template)
MECHANISMS = ("premi_risiko", "perilaku", "arus_paksa_struktural", "informasi", "lainnya")
KILL_METRICS = ("net_pnl_bps", "sharpe", "mdd_pct", "rata_net_per_sinyal_bps")
KILL_COMPARATORS = ("<", "<=")
# Batas ambang pembunuh per metrik: mencegah pembunuh yang mustahil terpicu (hampa) atau langsung terpicu.
KILL_BOUNDS = {"net_pnl_bps": (-5000.0, 5000.0), "sharpe": (-3.0, 3.0), "mdd_pct": (-90.0, -5.0), "rata_net_per_sinyal_bps": (-1000.0, 1000.0)}
ENTITY_TYPES = ("individu", "organisasi")
KNOWN_SYMBOLS = frozenset(PERP_UNIVERSE) | {"PAXGUSDT", "XAUUSDT"}
RESERVED_ID = re.compile(r"^B\d+-")            # B1-, B2- ... milik bot Fabius sendiri (cegah peniruan)
RESERVED_NAMES = ("fabius", "official", "resmi")
EIP712_NAME = "Fabius Bot Issuer"
MAX_ABS = 10 ** 15                              # batas angka: int raksasa meledakkan float()/json.dumps (batas 4300 digit)

# Karakter tak terlihat/pengisi yang kategori Unicode-nya tampak biasa (Lo/Mn/So): ditolak eksplisit.
_INVISIBLE_CP = {0x00AD, 0x034F, 0x061C, 0x115F, 0x1160, 0x17B4, 0x17B5, 0x180E, 0x2800, 0x3164, 0xFFA0}


def _f(t: str, label: str, **kw: Any) -> Dict[str, Any]:
    d: Dict[str, Any] = {"t": t, "label": label}
    d.update(kw)
    return d


SCHEMA: Dict[str, Any] = {
    "v": _f("int", "Versi skema", const=SCHEMA_V),
    "kind": _f("enum", "Jenis bot", values=KINDS,
               help="rule = aturan deklaratif Anda sendiri, dijalankan mesin kami; template = metode bawaan mesin + satu parameter (bukan jalur "
                    "utama); code = fungsi kode Anda di sandbox (privat; kode dikirim ke penyedia model peninjau); feed = program Anda sendiri mengomit "
                    "bobot target bertanda tangan sebelum penutupan tiap bar, dinilai maju saja (120 hari bayangan, tanpa slot sampai terbukti). "
                    "Jenis yang dibuka: lihat kinds_open"),
    "spec": {
        "bot_id": _f("str", "ID bot", pattern=r"[A-Z][A-Z0-9-]{2,30}", help="Awalan B<angka>- dicadangkan untuk bot Fabius"),
        "metode": _f("text", "Metode dalam satu kalimat", min=20, max=300),
        "template": _f("str", "Template (hanya kind=template)", optional=True, max=32),
        "param_nama": _f("str", "Nama SATU-satunya parameter (hanya kind=template)", optional=True, pattern=r"[A-Za-z][A-Za-z0-9_]{0,15}"),
        "param": _f("number", "Nilai parameter (hanya kind=template)", optional=True, min=0, max=1_000_000),
        "konstanta": _f("object", "Konstanta terkunci (kosong untuk kind=template dan rule)", optional=True),
        "rule": _f("rule", "Aturan deklaratif (hanya kind=rule; kosakata di `rule.vocabulary()`)", optional=True),
        "kode": _f("kode", "Kode (hanya kind=code): {sha, ukuran, params}; teks kode dikirim terpisah, privat, tidak ikut formulir publik", optional=True),
        "universe": _f("list", "Universe simbol", min=1, max=40,
                       item=_f("str", "Simbol", pattern=r"[A-Z0-9]{3,20}")),
        "horizon": _f("enum", "Ukuran bar", values=("1d",), help="Mesin saat ini hanya bar harian"),
    },
    "identity": {
        "issuer_wallet": _f("address", "Dompet penerbit (EIP-55)"),
        "payout_wallet": _f("address", "Dompet penerima bagi hasil (EIP-55); bila beda dari penerbit, ia harus ikut menandatangani"),
        "handle": _f("str", "Nama publik", min=2, max=60),
        "contact": _f("str", "Kontak (tidak dipublikasikan, tidak ke chain, tidak ikut hash)", min=5, max=120),
        "entity_type": _f("enum", "Jenis penerbit", values=ENTITY_TYPES),
        "erc8004_agent_id": _f("int", "ID identitas ERC-8004 (opsional)", optional=True, min=0),
        "conflicts": _f("text", "Kepentingan atau posisi yang relevan (tulis 'tidak ada' bila memang tidak ada)", min=4, max=500),
    },
    "theory": {
        "mekanisme_jenis": _f("enum", "Jenis mekanisme", values=MECHANISMS),
        "mekanisme": _f("text", "Mengapa metode ini menghasilkan uang", min=80, max=1500),
        "pihak_seberang": _f("text", "Siapa yang membayar edge ini dan mengapa tidak diarbitrase habis", min=40, max=800),
        "kapasitas_usd": _f("number", "Perkiraan kapasitas (USD)", optional=True, min=0),
        "referensi": _f("list", "Rujukan (minimal satu; keberadaannya diperiksa kode, bukan dipercaya)", min=1, max=10, item={
            "judul": _f("str", "Judul", min=3, max=200),
            "url": _f("url", "URL https publik"),
            "klaim": _f("text", "Apa yang ditunjukkan rujukan ini", min=20, max=400),
        }),
        "rezim": _f("text", "Kapan bekerja dan kapan gagal", min=40, max=800),
        "mode_gagal": _f("text", "Mode gagal dan risiko ekor", min=40, max=800),
        "peluruhan": _f("text", "Masih bekerja di 24 bulan terakhir atau setelah dipublikasikan? Buktinya?", min=40, max=800),
        "pembunuh": {
            "metric": _f("enum", "Metrik pembunuh", values=KILL_METRICS),
            "comparator": _f("enum", "Pembanding", values=KILL_COMPARATORS),
            "threshold": _f("number", "Ambang (berbatas per metrik, lihat KILL_BOUNDS)"),
            "window_sinyal": _f("int", "Jendela (jumlah sinyal)", min=10, max=500),
        },
    },
    "evidence": {
        "sumber_data": _f("list", "Sumber data", min=1, max=10, item=_f("str", "Sumber", min=3, max=120)),
        "insample_mulai": _f("date", "In-sample mulai"),
        "insample_akhir": _f("date", "In-sample akhir"),
        "oos_mulai": _f("date", "Di luar sampel mulai (opsional)", optional=True),
        "oos_akhir": _f("date", "Di luar sampel akhir (opsional)", optional=True),
        "percobaan": _f("int", "Jumlah varian atau parameter yang pernah dicoba sebelum memilih ini (jujur; menaikkan ambang Sharpe G3)", min=1, max=1_000_000),
        "klaim": {
            "sharpe_net": _f("number", "Klaim Sharpe net", min=-10, max=20),
            "mdd_pct": _f("number", "Klaim MDD (%, negatif)", min=-100, max=0),
            "n_sinyal": _f("int", "Klaim jumlah sinyal", min=0, max=10_000_000),
            "tahunan_pct": _f("number", "Klaim return tahunan (%)", min=-100, max=10_000),
        },
        "komit_maju": _f("list", "Komit maju ter-anchor (kind=feed)", optional=True, min=0, max=1000, item={
            "root": _f("str", "Akar komit 0x...", pattern=r"0x[0-9a-fA-F]{64}"),
            "bar": _f("date", "Tanggal bar"),
        }),
    },
    "declarations": {
        "tanpa_lookahead": _f("bool", "Tidak ada look-ahead", const=True),
        "tanpa_info_orang_dalam": _f("bool", "Tidak memakai informasi orang dalam", const=True),
        "tanpa_wash_trading": _f("bool", "Tidak ada wash trading atau manipulasi", const=True),
        "menerima_protokol": _f("bool", "Menerima protokol seleksi, rolling, dan pencabutan", const=True),
        "izin_publikasi": _f("bool", "Mengizinkan publikasi hasil evaluasi (termasuk yang buruk)", const=True),
        "lisensi": _f("enum", "Lisensi metode", values=("tertutup", "terbuka")),
    },
}


# ---------------------------------------------------------------- kebersihan teks (input musuh)

def _safe(x: Any) -> str:
    """Bentuk aman-cetak untuk memantulkan nilai dari kiriman ke pesan: repr (escape ESC dkk) dan dipotong."""
    return repr(str(x))[:40]


def _hostile(v: str, multiline: bool) -> Optional[str]:
    """Daftar-IZIN berdasarkan kategori Unicode: tolak kontrol (Cc), format (Cf: pengarah-teks, tag, lebar-nol), surrogat (Cs), privat (Co),
    tak-terdefinisi (Cn), pemisah baris/paragraf (Zl/Zp), spasi non-ASCII (Zs), pemilih-varian, dan pengisi tak terlihat."""
    for ch in v:
        cp = ord(ch)
        if multiline and ch in "\n\t":
            continue
        cat = unicodedata.category(ch)
        if cat in ("Cc", "Cf", "Cs", "Co", "Cn", "Zl", "Zp"):
            return "karakter kontrol/format/privat tersembunyi"
        if cat == "Zs" and ch != " ":
            return "spasi non-standar"
        if cp in _INVISIBLE_CP or 0xFE00 <= cp <= 0xFE0F or 0xE0100 <= cp <= 0xE01EF:
            return "karakter tak terlihat"
    return None


def _visible_len(v: str) -> int:
    """Panjang yang TERLIHAT setelah NFKC: spasi, pengisi, dan pemilih-varian tidak dihitung (cegah teks 'kosong' memenuhi min-panjang)."""
    n = 0
    for ch in unicodedata.normalize("NFKC", v):
        cp = ord(ch)
        if ch.isspace() or cp in _INVISIBLE_CP or 0xFE00 <= cp <= 0xFE0F or 0xE0100 <= cp <= 0xE01EF:
            continue
        if unicodedata.category(ch)[0] in ("Z", "C"):
            continue
        n += 1
    return n


def _url_problem(v: str) -> Optional[str]:
    if not re.fullmatch(r"https://[^\s]{4,290}", v):
        return "harus URL https tanpa spasi (maks 300 karakter)"
    try:
        parts = urlsplit(v)
        port = parts.port
    except ValueError:
        return "URL tidak sah"
    if parts.username is not None or parts.password is not None or "@" in parts.netloc:
        return "URL berisi userinfo (penyamaran host)"
    host = parts.hostname
    if not host or not host.isascii():
        return "host harus ASCII (punycode)"
    if "." not in host or host == "localhost" or host.endswith((".local", ".localhost", ".internal", ".lan")):
        return "host lokal/tidak publik"
    try:
        ipaddress.ip_address(host)
        return "host berupa alamat IP tidak diizinkan"
    except ValueError:
        pass
    if port not in (None, 443):
        return "port non-standar"
    return None


# ---------------------------------------------------------------- validasi generik

def _is_node(n: Dict[str, Any]) -> bool:
    return "t" in n


def _num(v: Any) -> bool:
    if isinstance(v, bool):
        return False
    if isinstance(v, int):
        return abs(v) <= MAX_ABS
    return isinstance(v, float) and math.isfinite(v) and abs(v) <= MAX_ABS


def _date(v: Any) -> Optional[dt.date]:
    if not isinstance(v, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", v):
        return None
    try:
        return dt.date.fromisoformat(v)
    except ValueError:
        return None


def _leaf(n: Dict[str, Any], v: Any, path: str, out: List[str]) -> None:
    t = n["t"]
    lo, hi = n.get("min"), n.get("max")
    if t in ("str", "text", "url"):
        if not isinstance(v, str):
            out.append(f"{path}: harus teks")
            return
        bad = _hostile(v, multiline=(t == "text"))
        if bad:
            out.append(f"{path}: {bad}")
        if lo is not None and _visible_len(v) < lo:
            out.append(f"{path}: terlalu pendek (min {lo} karakter terlihat)")
        if hi is not None and len(v) > hi:
            out.append(f"{path}: terlalu panjang (maks {hi} karakter)")
        if n.get("pattern") and not re.fullmatch(n["pattern"], v):
            out.append(f"{path}: format tidak valid ({n['pattern']})")
        if t == "url":
            prob = _url_problem(v)
            if prob:
                out.append(f"{path}: {prob}")
    elif t == "int":
        if not isinstance(v, int) or isinstance(v, bool):
            out.append(f"{path}: harus bilangan bulat")
            return
        if abs(v) > MAX_ABS:
            out.append(f"{path}: angka terlalu besar")
            return
        if "const" in n and v != n["const"]:
            out.append(f"{path}: harus {n['const']}")
        if lo is not None and v < lo:
            out.append(f"{path}: minimal {lo}")
        if hi is not None and v > hi:
            out.append(f"{path}: maksimal {hi}")
    elif t == "number":
        if not _num(v):
            out.append(f"{path}: harus angka hingga")
            return
        if lo is not None and v < lo:
            out.append(f"{path}: minimal {lo}")
        if hi is not None and v > hi:
            out.append(f"{path}: maksimal {hi}")
    elif t == "bool":
        if not isinstance(v, bool):
            out.append(f"{path}: harus true/false")
        elif "const" in n and v is not n["const"]:
            out.append(f"{path}: harus {str(n['const']).lower()} (pernyataan wajib)")
    elif t == "enum":
        if v not in n["values"]:
            out.append(f"{path}: harus salah satu dari {list(n['values'])}")
    elif t == "address":
        if not chain.is_checksum_address(v):
            out.append(f"{path}: bukan alamat EVM berformat checksum EIP-55")
    elif t == "date":
        if _date(v) is None:
            out.append(f"{path}: harus tanggal YYYY-MM-DD yang sah")
    elif t == "object":
        if not isinstance(v, dict) or len(v) > 20:
            out.append(f"{path}: harus objek datar (maks 20 kunci)")
            return
        for k, x in v.items():
            if not isinstance(k, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,31}", k):
                out.append(f"{path}.{_safe(k)}: nama kunci tidak valid")
            ok = x is None or isinstance(x, bool) or _num(x) or (isinstance(x, str) and len(x) <= 80 and _hostile(x, False) is None)
            if not ok:
                out.append(f"{path}.{_safe(k)}: nilai harus skalar sederhana")
    elif t == "rule":
        out.extend(rulemod.validate(v, path))
    elif t == "kode":
        out.extend(kodemod.validate_meta(v, path))
    elif t == "list":
        if not isinstance(v, list):
            out.append(f"{path}: harus daftar")
            return
        if lo is not None and len(v) < lo:
            out.append(f"{path}: minimal {lo} butir")
        if hi is not None and len(v) > hi:
            out.append(f"{path}: maksimal {hi} butir")
        for i, x in enumerate(v[: (hi if hi is not None else len(v))]):
            _node(n["item"], x, f"{path}[{i}]", out)
    else:  # pragma: no cover - kesalahan skema, bukan input
        raise ValueError(f"tipe skema tak dikenal: {t}")


def _node(n: Dict[str, Any], v: Any, path: str, out: List[str]) -> None:
    if _is_node(n):
        _leaf(n, v, path, out)
        return
    if not isinstance(v, dict):
        out.append(f"{path or 'pengajuan'}: harus objek")
        return
    if len(v) > 2 * len(n) + 4:
        out.append(f"{path or 'pengajuan'}: terlalu banyak field")
        return
    for k in v:
        if k not in n:
            out.append(f"{path + '.' if path else ''}{_safe(k)}: field tidak dikenal (skema tertutup)")
    for k, sub in n.items():
        p = f"{path}.{k}" if path else k
        if k not in v or v[k] is None:
            if not (_is_node(sub) and sub.get("optional")):
                out.append(f"{p}: wajib diisi")
            continue
        _node(sub, v[k], p, out)


def validate(sub: Dict[str, Any], existing_ids: Iterable[str] = (), enabled_kinds: Iterable[str] = ENABLED_KINDS) -> List[str]:
    """Daftar masalah (kosong = lolos validasi bentuk dan silang-field). TIDAK menilai kualitas teori: itu tugas peninjau-bot."""
    out: List[str] = []
    if not isinstance(sub, dict):
        return ["pengajuan harus objek"]
    try:
        _node(SCHEMA, sub, "", out)
        if out:                              # bentuk rusak: pemeriksaan silang-field tidak aman dijalankan
            return out[:50]
        out += _semantic(sub, set(existing_ids) | set(SPECS), tuple(enabled_kinds))
    except Exception as e:                   # input musuh tidak boleh menjatuhkan pemanggil: gagal TERTUTUP (tolak)
        return [f"validasi gagal tak terduga ({type(e).__name__}): pengajuan ditolak"]
    return out[:50]


def _norm_name(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKC", s).lower())


def _semantic(sub: Dict[str, Any], taken: set, enabled: tuple) -> List[str]:
    out: List[str] = []
    sp, ident, ev, th = sub["spec"], sub["identity"], sub["evidence"], sub["theory"]
    kind = sub["kind"]
    if kind not in enabled:
        out.append(f"kind: '{kind}' belum dibuka (dibuka sekarang: {list(enabled)})")
    if sp["bot_id"] in taken:
        out.append("spec.bot_id: sudah dipakai")
    if RESERVED_ID.match(sp["bot_id"]):
        out.append("spec.bot_id: awalan B<angka>- dicadangkan untuk bot Fabius")
    for nm, label in ((_norm_name(sp["bot_id"]), "spec.bot_id"), (_norm_name(ident["handle"]), "identity.handle")):
        if any(r in nm for r in RESERVED_NAMES):
            out.append(f"{label}: memuat nama yang dicadangkan ({', '.join(RESERVED_NAMES)}): peniruan Fabius")
    kons = sp.get("konstanta") or {}
    if sp.get("param_nama") is not None and sp["param_nama"] in kons:
        out.append("spec.konstanta: parameter tidak boleh juga muncul sebagai konstanta (satu metode, SATU parameter)")
    if kind == "template":
        for f in ("param_nama", "param"):
            if sp.get(f) is None:
                out.append(f"spec.{f}: wajib untuk kind=template")
        if sp.get("rule") is not None:
            out.append("spec.rule: hanya untuk kind=rule")
        tpl = sp.get("template")
        if tpl not in TEMPLATES:
            out.append(f"spec.template: harus salah satu dari {list(TEMPLATES)}")
        elif sp.get("param_nama") is not None and sp.get("param") is not None:
            base = SPECS[tpl]
            if sp["param_nama"] != base.param_nama:
                out.append(f"spec.param_nama: template {tpl} hanya punya parameter '{base.param_nama}'")
            if isinstance(base.param, int) and not isinstance(base.param, bool):
                if float(sp["param"]) != int(sp["param"]) or int(sp["param"]) < 2:
                    out.append(f"spec.param: harus bilangan bulat >= 2 untuk template {tpl}")
            elif sp["param"] <= 0:
                out.append("spec.param: harus > 0")
        if kons:
            out.append("spec.konstanta: untuk kind=template konstanta milik template (kosongkan)")
    elif kind == "rule":
        if sp.get("rule") is None:
            out.append("spec.rule: wajib untuk kind=rule")
        else:
            out += rulemod.validate_universe(sp["rule"], len(sp["universe"]))
        for f in ("template", "param_nama", "param"):
            if sp.get(f) is not None:
                out.append(f"spec.{f}: tidak dipakai untuk kind=rule (parameter bernama ada di dalam spec.rule.params)")
        if kons:
            out.append("spec.konstanta: untuk kind=rule kosongkan (konstanta ditulis di dalam aturan)")
    else:                                                   # code / feed: metode di luar formulir (kode privat / program penerbit)
        if kind == "code" and sp.get("kode") is None:
            out.append("spec.kode: wajib untuk kind=code ({sha, ukuran, params}; teks kode dikirim terpisah)")
        for f in ("template", "param_nama", "param", "rule") + (("kode",) if kind == "feed" else ()):
            if sp.get(f) is not None:
                out.append(f"spec.{f}: tidak dipakai untuk kind={kind}")
        if kons:
            out.append(f"spec.konstanta: untuk kind={kind} kosongkan")
    if kind in ("template", "rule") and sp.get("kode") is not None:
        out.append("spec.kode: hanya untuk kind=code")
    for s in sp["universe"]:
        if s not in KNOWN_SYMBOLS:
            out.append(f"spec.universe: {_safe(s)} tidak punya data di mesin")
    if len(set(sp["universe"])) != len(sp["universe"]):
        out.append("spec.universe: simbol ganda")
    a, b = _date(ev["insample_mulai"]), _date(ev["insample_akhir"])
    if a and b and not a < b:
        out.append("evidence.insample: akhir harus setelah mulai")
    has_o = ev.get("oos_mulai") is not None, ev.get("oos_akhir") is not None
    if any(has_o) and not all(has_o):
        out.append("evidence.oos: isi mulai DAN akhir, atau keduanya kosong")
    elif all(has_o):
        c, d = _date(ev["oos_mulai"]), _date(ev["oos_akhir"])
        if c and d and not (c < d):
            out.append("evidence.oos: akhir harus setelah mulai")
        if b and c and not (c > b):
            out.append("evidence.oos: harus SETELAH in-sample (tidak boleh beririsan)")
    urls = [r["url"] for r in th["referensi"]]
    if len(set(urls)) != len(urls):
        out.append("theory.referensi: URL ganda")
    k = th["pembunuh"]
    lo, hi = KILL_BOUNDS[k["metric"]]
    if not lo <= k["threshold"] <= hi:
        out.append(f"theory.pembunuh.threshold: untuk {k['metric']} harus dalam [{lo:g}, {hi:g}] (cegah pembunuh yang hampa atau langsung terpicu)")
    if kind == "feed" and ev.get("komit_maju"):
        out.append("evidence.komit_maju: kosongkan; komit maju feed dikirim SESUDAH terdaftar lewat POST /bots/feed/commit (sebelum penutupan tiap bar)")
    if ident["issuer_wallet"] == chain.to_checksum_address("0x" + "00" * 20) or ident["payout_wallet"] == chain.to_checksum_address("0x" + "00" * 20):
        out.append("identity: alamat nol")
    return out


# ---------------------------------------------------------------- hash, spesifikasi, tanda tangan

def _hashable(sub: Dict[str, Any]) -> Dict[str, Any]:
    s = copy.deepcopy(sub)
    s["identity"].pop("contact", None)          # tanda tangan/hash bersifat publik: kontak tidak boleh ikut (oracle tebak-kontak)
    return s


def submission_sha(sub: Dict[str, Any]) -> str:
    return sha0x(_hashable(sub))


def spec_sha_of(sub: Dict[str, Any]) -> str:
    return sha0x(sub["spec"])


def kill_text(k: Dict[str, Any]) -> str:
    return f"{k['metric']} {k['comparator']} {k['threshold']} pada {k['window_sinyal']} sinyal terakhir"


def to_botspec(sub: Dict[str, Any]) -> BotSpec:
    """BotSpec yang dijalankan mesin kami. `template`: konstanta, penggaris, dan metode milik template; penerbit hanya memberi bot_id, SATU nilai
    parameter (dipaksa ke tipe parameter template), dan universe. `rule`: aturan KANONIK (`rule.canonical`) di `konstanta["rule"]`, `param` = sha
    aturan itu, penggaris standar milik kami (penerbit tidak menentukan biaya). Pembunuh diterjemahkan ke teks; penegakannya oleh
    `slots.killer_triggered` memakai `theory.pembunuh` terstruktur."""
    sp = sub["spec"]
    pembunuh = kill_text(sub["theory"]["pembunuh"])
    if sub["kind"] == "rule":
        rc = rulemod.canonical(sp["rule"])
        return BotSpec(bot_id=sp["bot_id"], metode=sp["metode"], param_nama=rulemod.PARAM_NAMA, param=sha0x(rc), konstanta={"rule": rc},
                       universe=tuple(sp["universe"]), penggaris=dict(rulemod.PENGGARIS), tier="?", pembunuh=pembunuh, versi=1,
                       template=rulemod.RULE_METHOD)
    if sub["kind"] == "code":                              # P167b: kode PRIVAT; spesifikasi publik hanya memuat sha + ukuran + params
        meta = sp["kode"]
        km = {"sha": meta["sha"], "ukuran": int(meta["ukuran"]), "params": kodemod.canonical_params(meta["params"])}
        return BotSpec(bot_id=sp["bot_id"], metode=sp["metode"], param_nama=kodemod.PARAM_NAMA, param=meta["sha"], konstanta={"kode": km},
                       universe=tuple(sp["universe"]), penggaris=dict(kodemod.PENGGARIS), tier="?", pembunuh=pembunuh, versi=1,
                       template=kodemod.KODE_METHOD)
    if sub["kind"] == "feed":                              # P167c: tidak ada metode yang dijalankan; target = komit maju bertanda tangan
        return BotSpec(bot_id=sp["bot_id"], metode=sp["metode"], param_nama=feedmod.PARAM_NAMA, param=spec_sha_of(sub),
                       konstanta={"feed": {"bayangan_hari": feedmod.BAYANGAN_HARI, "anchor": feedmod.LABEL_ANCHOR}},
                       universe=tuple(sp["universe"]), penggaris=dict(feedmod.PENGGARIS), tier="?", pembunuh=pembunuh, versi=1,
                       template=feedmod.FEED_METHOD)
    if sub["kind"] != "template":
        raise ValueError("kind tidak dikenal")
    base = SPECS[sp["template"]]
    p = sp["param"]
    p = int(p) if isinstance(base.param, int) and not isinstance(base.param, bool) else float(p)
    return dataclasses.replace(base, bot_id=sp["bot_id"], template=sp["template"], param=p, universe=tuple(sp["universe"]),
                               tier="?", pembunuh=pembunuh, versi=1)


def typed_data(sub: Dict[str, Any], chain_id: int, nonce: int, deadline: int) -> Dict[str, Any]:
    """Pesan EIP-712 yang ditandatangani dompet penerbit (dan dompet payout bila berbeda). `nonce` + `deadline` mencegah pemakaian ulang."""
    return {
        "types": {
            "EIP712Domain": [{"name": "name", "type": "string"}, {"name": "version", "type": "string"},
                             {"name": "chainId", "type": "uint256"}],
            "Submission": [{"name": "issuer", "type": "address"}, {"name": "payout", "type": "address"},
                           {"name": "botId", "type": "bytes32"}, {"name": "specSha", "type": "bytes32"},
                           {"name": "submissionSha", "type": "bytes32"}, {"name": "nonce", "type": "uint256"},
                           {"name": "deadline", "type": "uint64"}],
        },
        "primaryType": "Submission",
        "domain": {"name": EIP712_NAME, "version": str(SCHEMA_V), "chainId": chain_id},
        "message": {"issuer": sub["identity"]["issuer_wallet"], "payout": sub["identity"]["payout_wallet"],
                    "botId": chain.hex0x(chain.ascii32(sub["spec"]["bot_id"])), "specSha": spec_sha_of(sub),
                    "submissionSha": submission_sha(sub), "nonce": nonce, "deadline": deadline},
    }


def recover_signer(sub: Dict[str, Any], signature_hex: str, chain_id: int, nonce: int, deadline: int) -> str:
    """Alamat (EIP-55) penanda tangan. Butuh paket `eth-account` (dipasang di repo ini untuk tools/); tanpa itu gagal TERTUTUP."""
    try:
        from eth_account import Account
        from eth_account.messages import encode_typed_data
    except ImportError as e:                       # pragma: no cover
        raise RuntimeError("verifikasi tanda tangan butuh eth-account; tanpa itu pengajuan tidak bisa diterima") from e
    msg = encode_typed_data(full_message=typed_data(sub, chain_id, nonce, deadline))
    return Account.recover_message(msg, signature=signature_hex)


def verify_identity(sub: Dict[str, Any], signature_hex: str, chain_id: int, nonce: int, deadline: int, now_s: int, *,
                    used_nonces: Optional[Iterable[int]] = None, max_ttl_s: int = 3600,
                    payout_signature_hex: Optional[str] = None) -> List[str]:
    """Masalah identitas (kosong = tanda tangan sah, belum kedaluwarsa, TTL wajar, nonce segar, dan dompet payout setuju).
    `used_nonces` = nonce yang sudah dipakai menurut penyimpanan server (pemeriksaan di sini hanya sebaik penyimpanan itu)."""
    if deadline < now_s:
        return ["tanda tangan kedaluwarsa"]
    if deadline - now_s > max_ttl_s:
        return [f"deadline terlalu jauh (TTL maksimum {max_ttl_s} detik)"]
    if used_nonces is not None and nonce in set(used_nonces):
        return ["nonce sudah dipakai (pemakaian ulang tanda tangan)"]
    problems: List[str] = []
    try:
        who = recover_signer(sub, signature_hex, chain_id, nonce, deadline)
    except RuntimeError:
        raise
    except Exception as e:                          # tanda tangan rusak: tolak, jangan lempar
        return [f"tanda tangan tidak terbaca: {type(e).__name__}"]
    if who != sub["identity"]["issuer_wallet"]:
        problems.append(f"penanda tangan {who} bukan issuer_wallet")
    payout = sub["identity"]["payout_wallet"]
    if payout != sub["identity"]["issuer_wallet"]:
        if not payout_signature_hex:
            problems.append("dompet payout berbeda dari penerbit dan belum menandatangani (cegah menunjuk dompet korban)")
        else:
            try:
                who2 = recover_signer(sub, payout_signature_hex, chain_id, nonce, deadline)
                if who2 != payout:
                    problems.append(f"penanda tangan payout {who2} bukan payout_wallet")
            except RuntimeError:
                raise
            except Exception as e:
                problems.append(f"tanda tangan payout tidak terbaca: {type(e).__name__}")
    return problems


def schema_json() -> Dict[str, Any]:
    """Skema yang bisa dirender FE sebagai formulir (label, bantuan, batas). Salinan dalam: aman diubah pemanggil."""
    return copy.deepcopy(SCHEMA)
