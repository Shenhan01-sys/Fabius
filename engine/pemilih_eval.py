"""P74 (epik 05 §5 + §12): lapisan pemilih + EVALUASI - kebijakan pembanding (IDENTITAS, EW, TRAILING "bot terbaik 60 hari", ACAK, NONE), ongkos
ganti, uji berpasangan + Benjamini-Hochberg, skor Brier, vonis. Aturan + angka dipra-registrasi di `PARAMS_P74` (berkas usulan ber-sha
`engine/locks/pemilih_eval.usulan.json`) SEBELUM hasil dilihat; kunci hanya atas kata builder.

HANYA MENGUKUR: tidak mengubah bot aktif (`engine/pemilih.py`, terkunci), buku slot, atau apa pun yang hidup.

Konvensi waktu (sama dengan `engine/replay.py` dan `settle` ledger): `net[bot][T]` = net paper bot pada bar T (waktu BUKA, ms) dari target penutupan
bar sebelumnya. Kebijakan memutuskan bot untuk bar T HANYA dari net bar < T (kausal oleh konstruksi; tes mengganggu masa depan).
Fungsi murni (kecuali kunci): tidak membaca berkas data, jaringan, atau jam. CLI di `tools/pemilih_eval.py`.
"""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import math
import os
import random
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .fd16 import bh_reject, block_bootstrap_means
from .locks import LOCK_DIR
from .spec import sha0x

LOCK_FILE = os.path.join(LOCK_DIR, "pemilih_eval.lock.json")
USULAN_FILE = os.path.join(LOCK_DIR, "pemilih_eval.usulan.json")

NONE = "NONE"
IDENTITAS, EW, TRAILING, ACAK = "IDENTITAS", "EW", "TRAILING", "ACAK"
PEMBANDING = (EW, TRAILING, IDENTITAS)                       # + ACAK lewat distribusi
MAJU, MUNDUR = "maju", "mundur"
UNGGUL, TIDAK_UNGGUL, BELUM, EKSPLORATIF = "UNGGUL", "TIDAK UNGGUL", "BELUM CUKUP DATA", "EKSPLORATIF"

PARAMS_P74: Dict[str, Any] = {
    "v": 1,
    "angka": {"identitas": "B1-TREND", "jendela_trailing": 60, "jeda_min": 5, "n_acak": 1000, "blok_hari": 5, "boot_n": 10_000,
              "alpha_bh": 0.10, "hari_min": 60, "brier_min_n": 30, "kalibrasi_ember": 5, "brier_acuan_biner": 0.5},
    "aturan": {
        "waktu": "net[bot][T] = net paper bar T (waktu buka) dari target penutupan bar sebelumnya; kebijakan untuk bar T hanya dari net bar < T",
        "kalender": "bar tempat SEMUA kandidat punya net (irisan)",
        "IDENTITAS": "selalu bot identitas",
        "EW": "rata-rata net harian semua kandidat; tanpa ongkos ganti",
        "TRAILING": "bot dengan jumlah net jendela_trailing bar kalender terakhir (< T) tertinggi; seri -> identitas bila ikut seri, selain itu abjad; "
                    "riwayat < jendela -> identitas; ganti hanya bila >= jeda_min bar sejak ganti terakhir",
        "ACAK": "tiap jeda_min bar pilih seragam (random.Random(benih), kandidat urut abjad); distribusi n_acak tarikan, benih = sha masukan + nomor tarikan",
        "NONE": "datar, net 0, gross 0",
        "tanpa_pilihan": "pemilih tanpa pilihan pada satu bar = bot identitas; pilihan bot di luar kandidat = bar itu tak terukur untuk pemilih itu (dicetak)",
        "ongkos_ganti": "bar pertama sesudah ganti A -> B: gross_A(bar sebelumnya) x biaya_A + gross_B(bar itu) x biaya_B (keluar + masuk penuh, tanpa "
                        "netting); biaya = penggaris spesifikasi per sisi (per kaki x 2 untuk dua kaki); gross tanpa data = 1,0",
        "uji": "rerata selisih net harian pemilih - pembanding pada bar bersama; p satu sisi bootstrap blok melingkar terpusat; vs ACAK: "
               "p = (1 + #tarikan dengan jumlah net >= pemilih) / (n_acak + 1)",
        "bh": "Benjamini-Hochberg alpha_bh lintas SEMUA hipotesis (pemilih x pembanding) dalam satu laporan",
        "brier": "dicetak SEBELUM PnL. Biner: p = keyakinan/100 untuk 'net bot pilihan > net bot identitas' (pilihan = identitas / net sama dikecualikan), "
                 "acuan p = 0,5. Multi: p per bot, kelas = bot terbaik bar itu (seri dibagi rata), acuan seragam 1/N. skill = 1 - Brier / Brier acuan",
        "vonis": "maju: hari < hari_min -> BELUM CUKUP DATA; prakiraan ada tetapi n < brier_min_n -> BELUM CUKUP DATA; semua hipotesis lolos BH dan "
                 "(bila ada prakiraan) skill > 0 -> UNGGUL; selain itu TIDAK UNGGUL. mundur -> EKSPLORATIF (dalam-sampel, tanpa vonis)",
    },
}


def _A(P: Optional[dict] = None) -> Dict[str, Any]:
    return (P if P is not None else PARAMS_P74)["angka"]


# ---------------------------------------------------------------- kalender + kebijakan pembanding

def kalender(net: Mapping[str, Mapping[int, float]], bots: Sequence[str]) -> List[int]:
    """Bar tempat SEMUA kandidat punya net (irisan), urut waktu."""
    if not bots:
        return []
    common = set(net.get(bots[0]) or {})
    for b in bots[1:]:
        common &= set(net.get(b) or {})
    return sorted(common)


def _pilih_seri(nilai: Mapping[str, float], identitas: str) -> str:
    top = max(nilai.values())
    tied = sorted(b for b, v in nilai.items() if v == top)
    return identitas if identitas in tied else tied[0]


def kebijakan_identitas(cal: Sequence[int], identitas: str) -> Dict[int, str]:
    return {T: identitas for T in cal}


def kebijakan_trailing(net: Mapping[str, Mapping[int, float]], cal: Sequence[int], bots: Sequence[str], identitas: str, jendela: int,
                       jeda_min: int) -> Dict[int, str]:
    """"Bot terbaik `jendela` bar": untuk bar cal[i] hanya jumlah net cal[i-jendela .. i-1] (semuanya < T) - masa depan tidak terbaca."""
    pref: Dict[str, List[float]] = {}
    for b in bots:
        s, acc = 0.0, [0.0]
        for T in cal:
            s += net[b][T]
            acc.append(s)
        pref[b] = acc
    out: Dict[int, str] = {}
    cur, terakhir = identitas, None
    for i, T in enumerate(cal):
        want = identitas if i < jendela else _pilih_seri({b: pref[b][i] - pref[b][i - jendela] for b in bots}, identitas)
        if want != cur and (terakhir is None or i - terakhir >= jeda_min):
            cur, terakhir = want, i
        out[T] = cur
    return out


def kebijakan_acak(cal: Sequence[int], bots: Sequence[str], jeda_min: int, rng: random.Random) -> Dict[int, str]:
    pil, out, cur = sorted(bots), {}, None
    for i, T in enumerate(cal):
        if i % jeda_min == 0:
            cur = rng.choice(pil)
        out[T] = cur
    return out


def biaya_dari_penggaris(penggaris: Mapping[str, Any]) -> float:
    """Biaya per unit gross per sisi dari penggaris spesifikasi: `fee_bps_sisi`, atau `fee_bps_sisi_per_kaki` x 2 kaki (B3)."""
    if "fee_bps_sisi_per_kaki" in penggaris:
        return 2 * float(penggaris["fee_bps_sisi_per_kaki"]) / 1e4
    if "fee_bps_sisi" in penggaris:
        return float(penggaris["fee_bps_sisi"]) / 1e4
    raise ValueError("penggaris tanpa fee per sisi: ongkos ganti tidak bisa dihitung")


def _gross(gross: Optional[Mapping[str, Mapping[int, float]]], b: str, T: int) -> float:
    if b == NONE:
        return 0.0
    g = ((gross or {}).get(b) or {}).get(T)
    return 1.0 if g is None else float(g)


def _biaya(biaya: Mapping[str, float], b: str) -> float:
    if b == NONE:
        return 0.0
    if b not in biaya:
        raise ValueError(f"biaya sisi {b} tidak diketahui: ongkos ganti tidak boleh dianggap nol")
    return float(biaya[b])


def jalankan(pilihan: Mapping[int, str], net: Mapping[str, Mapping[int, float]], cal: Sequence[int],
             gross: Optional[Mapping[str, Mapping[int, float]]], biaya: Mapping[str, float]) -> Dict[str, Any]:
    """Net harian kebijakan pada `cal` (urut): net bot yang dipegang, dikurangi ongkos ganti pada bar pertama sesudah ganti.
    -> {seri: {T: net}, ganti, ongkos}. NONE = net 0, gross 0."""
    seri: Dict[int, float] = {}
    ganti, ongkos, prev, prev_T = 0, 0.0, None, None
    for T in cal:
        b = pilihan[T]
        x = 0.0 if b == NONE else float(net[b][T])
        if prev is not None and b != prev:
            c = _gross(gross, prev, prev_T) * _biaya(biaya, prev) + _gross(gross, b, T) * _biaya(biaya, b)
            x -= c
            ganti += 1
            ongkos += c
        seri[T] = x
        prev, prev_T = b, T
    return {"seri": seri, "ganti": ganti, "ongkos": ongkos}


def seri_ew(net: Mapping[str, Mapping[int, float]], cal: Sequence[int], bots: Sequence[str]) -> Dict[int, float]:
    return {T: sum(float(net[b][T]) for b in bots) / len(bots) for T in cal}


# ---------------------------------------------------------------- statistik

def _kuantil(xs: Sequence[float], q: float) -> Optional[float]:
    if not xs:
        return None
    pos = q * (len(xs) - 1)
    lo = math.floor(pos)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def ringkas(x: Sequence[float]) -> Dict[str, Any]:
    n = len(x)
    if n == 0:
        return {"n": 0, "rata_bps": None, "jumlah_pct": None, "sharpe": None, "mdd_pct": None, "hari_positif": 0}
    m = sum(x) / n
    sd = math.sqrt(sum((v - m) ** 2 for v in x) / (n - 1)) if n > 1 else 0.0
    cum = peak = mdd = 0.0
    for v in x:
        cum += v
        peak = max(peak, cum)
        mdd = max(mdd, peak - cum)
    return {"n": n, "rata_bps": m * 1e4, "jumlah_pct": sum(x) * 100, "sharpe": (m / sd * math.sqrt(365)) if sd > 0 else None,
            "mdd_pct": mdd * 100, "hari_positif": sum(1 for v in x if v > 0)}


def uji_berpasangan(a: Sequence[float], b: Sequence[float], blok: int, boot_n: int, benih: int) -> Dict[str, Any]:
    """H0: rerata (a - b) <= 0. p satu sisi dari bootstrap blok melingkar yang dipusatkan (pola `engine/fd16.py`)."""
    d = [x - y for x, y in zip(a, b)]
    n = len(d)
    if n < 2:
        return {"n": n, "selisih_bps": None, "ci_lo_bps": None, "ci_hi_bps": None, "p": None}
    m = sum(d) / n
    boots = sorted(block_bootstrap_means(d, blok, boot_n, random.Random(benih)))
    p = (1 + sum(1 for v in boots if v - m >= m)) / (len(boots) + 1)
    return {"n": n, "selisih_bps": m * 1e4, "ci_lo_bps": _kuantil(boots, 0.025) * 1e4, "ci_hi_bps": _kuantil(boots, 0.975) * 1e4, "p": p}


def p_acak(nilai: float, distribusi: Sequence[float]) -> Optional[float]:
    if not distribusi:
        return None
    return (1 + sum(1 for v in distribusi if v >= nilai)) / (len(distribusi) + 1)


def benih_dari(net: Mapping[str, Mapping[int, float]], cal: Sequence[int], bots: Sequence[str], label: str = "") -> int:
    """Benih deterministik = sha masukan: siapa pun yang menghitung ulang dari data yang sama mendapat p dan distribusi acak yang sama."""
    blob = json.dumps({"label": label, "cal": list(cal), "net": {b: [float(net[b][T]) for T in cal] for b in sorted(bots)}},
                      sort_keys=True, separators=(",", ":"))
    return int(hashlib.sha256(blob.encode()).hexdigest()[:16], 16)


def _benih_k(benih: int, k: int) -> int:
    return int(hashlib.sha256(f"{benih}:{k}".encode()).hexdigest()[:16], 16)


def distribusi_acak(net: Mapping[str, Mapping[int, float]], cal: Sequence[int], bots: Sequence[str], gross, biaya: Mapping[str, float], n: int,
                    jeda_min: int, benih: int) -> List[float]:
    """Jumlah net `n` kebijakan ACAK (ongkos ganti ikut) pada kalender yang sama - pembanding berupa DISTRIBUSI, bukan satu tarikan."""
    return [sum(jalankan(kebijakan_acak(cal, bots, jeda_min, random.Random(_benih_k(benih, k))), net, cal, gross, biaya)["seri"].values())
            for k in range(n)]


# ---------------------------------------------------------------- Brier (prakiraan dinilai sebelum PnL)

def _cek_peluang(p: float, apa: str) -> float:
    p = float(p)
    if not (0.0 <= p <= 1.0) or math.isnan(p):
        raise ValueError(f"{apa}: {p} bukan peluang 0..1")
    return p


def brier_biner(pasangan: Sequence[Tuple[float, int]], acuan: float = 0.5, ember: int = 5) -> Dict[str, Any]:
    """`pasangan` = [(p, kejadian 0/1)]. -> n, Brier, Brier acuan (p tetap = `acuan`), skill = 1 - Brier / acuan, tabel kalibrasi per ember."""
    n = len(pasangan)
    if n == 0:
        return {"n": 0, "brier": None, "acuan": None, "skill": None, "kalibrasi": []}
    pas = [(_cek_peluang(p, "prakiraan"), int(o)) for p, o in pasangan]
    br = sum((p - o) ** 2 for p, o in pas) / n
    ref = sum((acuan - o) ** 2 for _, o in pas) / n
    kal = []
    for k in range(ember):
        lo, hi = k / ember, (k + 1) / ember
        xs = [(p, o) for p, o in pas if lo <= p < hi or (k == ember - 1 and p == 1.0)]
        if xs:
            kal.append({"ember": f"{lo:.1f}-{hi:.1f}", "n": len(xs), "rata_p": sum(p for p, _ in xs) / len(xs), "frekuensi": sum(o for _, o in xs) / len(xs)})
    return {"n": n, "brier": br, "acuan": ref, "skill": (1 - br / ref) if ref > 0 else None, "kalibrasi": kal}


def kejadian_keyakinan(pilihan: Mapping[int, Tuple[str, float]], net: Mapping[str, Mapping[int, float]], cal: Sequence[int],
                       identitas: str) -> List[Tuple[float, int]]:
    """Pilihan agent ber-keyakinan -> [(keyakinan / 100, 1 bila net bot pilihan > net bot identitas)] pada bar kalender. Pilihan = identitas, bot
    tanpa net, atau net sama dikecualikan (kejadiannya tidak terdefinisi)."""
    out = []
    for T in cal:
        x = pilihan.get(T)
        if x is None:
            continue
        bot, k = x
        p = _cek_peluang(float(k) / 100.0, f"keyakinan bar {T}")
        if bot == identitas or T not in (net.get(bot) or {}):
            continue
        a, b = float(net[bot][T]), float(net[identitas][T])
        if a == b:
            continue
        out.append((p, 1 if a > b else 0))
    return out


def brier_multi(prakiraan: Mapping[int, Mapping[str, float]], net: Mapping[str, Mapping[int, float]], cal: Sequence[int],
                bots: Sequence[str]) -> Dict[str, Any]:
    """Prakiraan peluang per bot ("bot mana yang terbaik bar ini") -> Brier multi-kelas vs acuan seragam 1/N. Kelas = bot net tertinggi; seri dibagi rata."""
    rows = []
    for T in cal:
        p = prakiraan.get(T)
        if p is None:
            continue
        if any(b not in bots for b in p):
            raise ValueError(f"prakiraan bar {T} menyebut bot di luar kandidat")
        pp = {b: _cek_peluang(p.get(b, 0.0), f"prakiraan bar {T} {b}") for b in bots}
        if abs(sum(pp.values()) - 1.0) > 1e-6:
            raise ValueError(f"prakiraan bar {T}: jumlah peluang {sum(pp.values()):.6f} != 1")
        top = max(float(net[b][T]) for b in bots)
        best = [b for b in bots if float(net[b][T]) == top]
        o = {b: (1.0 / len(best) if b in best else 0.0) for b in bots}
        rows.append((sum((pp[b] - o[b]) ** 2 for b in bots), sum((1.0 / len(bots) - o[b]) ** 2 for b in bots)))
    if not rows:
        return {"n": 0, "brier": None, "acuan": None, "skill": None}
    br, ref = sum(r[0] for r in rows) / len(rows), sum(r[1] for r in rows) / len(rows)
    return {"n": len(rows), "brier": br, "acuan": ref, "skill": (1 - br / ref) if ref > 0 else None}


# ---------------------------------------------------------------- evaluasi + vonis

def evaluasi(net: Mapping[str, Mapping[int, float]], bots: Sequence[str], pemilih: Optional[Mapping[str, Mapping[int, str]]] = None,
             gross: Optional[Mapping[str, Mapping[int, float]]] = None, biaya: Optional[Mapping[str, float]] = None,
             keyakinan: Optional[Mapping[str, Mapping[int, Tuple[str, float]]]] = None,
             prakiraan: Optional[Mapping[str, Mapping[int, Mapping[str, float]]]] = None, mode: str = MAJU, P: Optional[dict] = None) -> Dict[str, Any]:
    """Satu laporan evaluasi. `pemilih` = {nama: {T: bot}} (bar tanpa pilihan = identitas; bot di luar kandidat = bar itu tak terukur untuk pemilih
    itu). Mode `mundur` tanpa pemilih menilai TRAILING sebagai subjek eksploratif. Tidak pernah melempar karena data kurang: itu vonis BELUM CUKUP DATA."""
    if mode not in (MAJU, MUNDUR):
        raise ValueError(f"mode {mode!r} tidak dikenal")
    A = _A(P)
    ident = A["identitas"]
    bots = sorted(bots)
    biaya = dict(biaya or {})
    lap: Dict[str, Any] = {"mode": mode, "params_sha": sha0x(P if P is not None else PARAMS_P74), "kandidat": bots, "identitas": ident,
                           "dasar": {}, "acak": None, "subjek": {}, "hipotesis": [], "galat": None}
    cal = kalender(net, bots)
    lap["kalender"] = {"n": len(cal), "dari": cal[0] if cal else None, "sampai": cal[-1] if cal else None}
    subjek_in = dict(pemilih or {})
    if ident not in bots:
        lap["galat"] = f"bot identitas {ident} tidak punya net di data ini"
    elif not cal:
        lap["galat"] = "kalender kosong: tidak ada bar tempat semua kandidat punya net"
    if lap["galat"]:
        for nama in subjek_in:
            lap["subjek"][nama] = {"vonis": EKSPLORATIF if mode == MUNDUR else BELUM, "alasan": [lap["galat"]]}
        return lap
    benih = benih_dari(net, cal, bots, mode)
    pil_dasar = {IDENTITAS: kebijakan_identitas(cal, ident),
                 TRAILING: kebijakan_trailing(net, cal, bots, ident, A["jendela_trailing"], A["jeda_min"]),
                 NONE: {T: NONE for T in cal}}
    runs = {k: jalankan(v, net, cal, gross, biaya) for k, v in pil_dasar.items()}
    runs[EW] = {"seri": seri_ew(net, cal, bots), "ganti": 0, "ongkos": 0.0}
    for k, r in runs.items():
        lap["dasar"][k] = {**ringkas(list(r["seri"].values())), "ganti": r["ganti"], "ongkos_pct": r["ongkos"] * 100}
    lap["per_bot"] = {b: ringkas([float(net[b][T]) for T in cal]) for b in bots}                 # konteks, bukan hipotesis
    if mode == MUNDUR and not subjek_in:
        subjek_in = {TRAILING: pil_dasar[TRAILING]}
    acak_cache: Dict[Tuple[int, ...], List[float]] = {}

    def acak_untuk(c: Sequence[int]) -> List[float]:
        key = tuple(c)
        if key not in acak_cache:
            acak_cache[key] = sorted(distribusi_acak(net, c, bots, gross, biaya, A["n_acak"], A["jeda_min"], _benih_k(benih, len(c))))
        return acak_cache[key]

    full = acak_untuk(cal)
    if full:
        lap["acak"] = {"n": len(full), "jumlah_pct_p05": _kuantil(full, 0.05) * 100, "jumlah_pct_p50": _kuantil(full, 0.5) * 100,
                       "jumlah_pct_p95": _kuantil(full, 0.95) * 100}
    pvals: Dict[str, float] = {}
    for nama in sorted(subjek_in):
        mp = subjek_in[nama]
        pilihan = {T: mp.get(T, ident) for T in cal}
        tak = sorted(T for T, b in pilihan.items() if b != NONE and b not in bots)
        c = [T for T in cal if T not in set(tak)]
        s: Dict[str, Any] = {"tak_terukur": len(tak), "tanpa_pilihan": sum(1 for T in cal if T not in mp), "uji": {}, "brier": {}, "alasan": []}
        if len(c) < 2:
            s.update(vonis=EKSPLORATIF if mode == MUNDUR else BELUM, alasan=[f"bar terukur {len(c)} < 2"])
            lap["subjek"][nama] = s
            continue
        run = jalankan({T: pilihan[T] for T in c}, net, c, gross, biaya)
        x = [run["seri"][T] for T in c]
        s.update(ringkas(x), ganti=run["ganti"], ongkos_pct=run["ongkos"] * 100)
        for k in PEMBANDING:
            if k == nama:
                continue
            u = uji_berpasangan(x, [runs[k]["seri"][T] for T in c], A["blok_hari"], A["boot_n"], _benih_k(benih, hash_label(nama, k)))
            s["uji"][k] = u
            if u["p"] is not None:
                pvals[f"{nama} vs {k}"] = u["p"]
        pa = p_acak(sum(x), acak_untuk(c))
        s["uji"][ACAK] = {"n": len(c), "jumlah_pct": sum(x) * 100, "p": pa}
        if pa is not None:
            pvals[f"{nama} vs {ACAK}"] = pa
        if keyakinan and nama in keyakinan:
            s["brier"]["biner"] = brier_biner(kejadian_keyakinan(keyakinan[nama], net, c, ident), A["brier_acuan_biner"], A["kalibrasi_ember"])
        if prakiraan and nama in prakiraan:
            s["brier"]["multi"] = brier_multi(prakiraan[nama], net, c, bots)
        lap["subjek"][nama] = s
    keputusan = bh_reject(pvals, A["alpha_bh"]) if pvals else {}
    lap["hipotesis"] = [{"h": h, "p": pvals[h], "lolos_bh": keputusan[h]} for h in sorted(pvals, key=lambda h: (pvals[h], h))]
    for nama, s in lap["subjek"].items():
        if "vonis" in s:
            continue
        s["vonis"], s["alasan"] = _vonis(nama, s, keputusan, mode, A)
    return lap


def hash_label(*xs: str) -> int:
    return int(hashlib.sha256("|".join(xs).encode()).hexdigest()[:8], 16)


def _vonis(nama: str, s: Dict[str, Any], keputusan: Mapping[str, bool], mode: str, A: Mapping[str, Any]) -> Tuple[str, List[str]]:
    if mode == MUNDUR:
        return EKSPLORATIF, ["mode mundur: dalam-sampel (parameter bot dipilih pada periode yang sama), tidak pernah vonis"]
    alasan = []
    if s["n"] < A["hari_min"]:
        alasan.append(f"hari terukur {s['n']} < {A['hari_min']}")
    for jenis, b in s["brier"].items():
        if b["n"] < A["brier_min_n"]:
            alasan.append(f"prakiraan {jenis} {b['n']} < {A['brier_min_n']}")
    if alasan:
        return BELUM, alasan
    for h, ok in keputusan.items():
        if h.startswith(f"{nama} vs ") and not ok:
            alasan.append(f"{h}: tidak lolos BH")
    hyps = [h for h in keputusan if h.startswith(f"{nama} vs ")]
    if len(hyps) < len(PEMBANDING) + 1 - (1 if nama in PEMBANDING else 0):
        alasan.append("tidak semua pembanding bisa diuji")
    for jenis, b in s["brier"].items():
        if b["skill"] is None or b["skill"] <= 0:
            alasan.append(f"skill Brier {jenis} {b['skill']} <= 0")
    return (TIDAK_UNGGUL, alasan) if alasan else (UNGGUL, ["semua hipotesis lolos BH" + (" dan skill Brier > 0" if s["brier"] else "")])


# ---------------------------------------------------------------- teks laporan

def _f(x: Optional[float], fmt: str = "{:+.2f}") -> str:
    return "-" if x is None else fmt.format(x)


def _tgl(t_ms: Optional[int]) -> str:
    return "-" if t_ms is None else dt.datetime.fromtimestamp(t_ms / 1000, dt.timezone.utc).strftime("%Y-%m-%d")


def teks(lap: Mapping[str, Any], judul: str = "") -> str:
    k = lap["kalender"]
    out = [f"EVALUASI PEMILIH (P74) {judul} mode {lap['mode'].upper()} | params {lap['params_sha'][:18]}… | kandidat {', '.join(lap['kandidat']) or '-'} | "
           f"identitas {lap['identitas']} | kalender {k['n']} bar {_tgl(k['dari'])} .. {_tgl(k['sampai'])}"]
    if lap["mode"] == MUNDUR:
        out.append("  EKSPLORATIF: replay dalam-sampel (parameter bot dipilih pada periode yang sama) - BUKAN vonis, bukan klaim edge")
    if lap.get("galat"):
        out.append(f"  {lap['galat']}")
    sub = lap["subjek"]
    brier = [(n, j, b) for n, s in sorted(sub.items()) for j, b in (s.get("brier") or {}).items()]
    out.append("PRAKIRAAN (Brier, dinilai sebelum PnL):" + ("" if brier else " tidak ada prakiraan ber-peluang"))
    for n, j, b in brier:
        out.append(f"  {n:<22} {j:<6} n {b['n']:>4}  Brier {_f(b['brier'], '{:.4f}')}  acuan {_f(b['acuan'], '{:.4f}')}  skill {_f(b['skill'], '{:+.3f}')}")
        for e in b.get("kalibrasi") or []:
            out.append(f"      ember {e['ember']}: n {e['n']}, rata p {e['rata_p']:.2f}, frekuensi {e['frekuensi']:.2f}")
    if lap["dasar"]:
        out.append(f"{'kebijakan':<24}{'n':>6}{'rata bps':>10}{'jumlah %':>10}{'Sharpe':>8}{'MDD %':>8}{'ganti':>7}{'ongkos %':>10}"
                   "   (jumlah + MDD = penjumlahan net harian, bukan majemuk)")
        rows = [(n, d) for n, d in lap["dasar"].items()] + [(n, s) for n, s in sorted(sub.items()) if "rata_bps" in s and n not in lap["dasar"]]
        for n, d in rows:
            out.append(f"{n:<24}{d['n']:>6}{_f(d['rata_bps']):>10}{_f(d['jumlah_pct']):>10}{_f(d['sharpe']):>8}{_f(d['mdd_pct'], '{:.2f}'):>8}"
                       f"{d.get('ganti', 0):>7}{_f(d.get('ongkos_pct'), '{:.2f}'):>10}")
    for n, d in sorted((lap.get("per_bot") or {}).items()):
        out.append(f"  bot {n:<20}{d['n']:>6}{_f(d['rata_bps']):>10}{_f(d['jumlah_pct']):>10}{_f(d['sharpe']):>8}{_f(d['mdd_pct'], '{:.2f}'):>8}")
    if lap.get("acak"):
        a = lap["acak"]
        out.append(f"ACAK ({a['n']} tarikan, jeda sama): jumlah % p05 {a['jumlah_pct_p05']:+.2f} | p50 {a['jumlah_pct_p50']:+.2f} | p95 {a['jumlah_pct_p95']:+.2f}")
    for h in lap["hipotesis"]:
        out.append(f"  H {h['h']:<34} p {h['p']:.4f}  BH {'LOLOS' if h['lolos_bh'] else 'tidak'}")
    for n, s in sorted(sub.items()):
        extra = f" | tak terukur {s.get('tak_terukur', 0)} bar, tanpa pilihan {s.get('tanpa_pilihan', 0)} bar" if "tak_terukur" in s else ""
        out.append(f"VONIS {n}: {s['vonis']} - {'; '.join(s['alasan'])}{extra}")
    return "\n".join(out)


# ---------------------------------------------------------------- pra-registrasi + kunci (pola tools/meja_eval.py)

def params_sha(P: Optional[dict] = None) -> str:
    return sha0x(P if P is not None else PARAMS_P74)


def _baca(path: str) -> Tuple[Optional[dict], Optional[str]]:
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return (d, None) if sha0x(d["params"]) == d["sha"] else (d, "sha berkas != sha isi")
    except (OSError, ValueError, KeyError, TypeError) as e:
        return None, f"{type(e).__name__}"


def status(P: Optional[dict] = None, lock_path: str = LOCK_FILE, usulan_path: str = USULAN_FILE) -> Dict[str, Any]:
    """BELUM_DIUSULKAN | USULAN (berkas usulan = params kode) | TERKUNCI (berkas kunci = params kode) | MENYIMPANG (kode != berkas) | RUSAK."""
    now = params_sha(P)
    for path, state in ((lock_path, "TERKUNCI"), (usulan_path, "USULAN")):
        if os.path.exists(path):
            d, galat = _baca(path)
            if galat:
                return {"state": "RUSAK", "sha_kini": now, "sha_berkas": (d or {}).get("sha"), "berkas": path, "galat": galat}
            return {"state": state if d["sha"] == now else "MENYIMPANG", "sha_kini": now, "sha_berkas": d["sha"], "berkas": path}
    return {"state": "BELUM_DIUSULKAN", "sha_kini": now, "sha_berkas": None, "berkas": None}


def _tulis_json(path: str, d: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def tulis_usulan(catatan: str, now_iso: Optional[str] = None, P: Optional[dict] = None, path: str = USULAN_FILE, lock_path: str = LOCK_FILE) -> dict:
    """Pra-registrasi aturan + angka SEBELUM hasil: berkas usulan ber-sha. Usulan lama yang berbeda dipindah ke `locks/history/` (tetap terlihat).
    Ditolak bila kunci sudah ada (aturan baru = keputusan baru + kunci baru, bukan usulan ulang)."""
    if not (catatan or "").strip():
        raise ValueError("catatan wajib (apa dan kenapa)")
    if os.path.exists(lock_path):
        raise FileExistsError("kunci P74 sudah ada: aturan baru = keputusan baru + kunci baru, bukan usulan ulang")
    params = copy.deepcopy(P if P is not None else PARAMS_P74)
    if os.path.exists(path):
        lama, _ = _baca(path)
        if lama and lama.get("sha") == sha0x(params):
            return lama
        hist = os.path.join(os.path.dirname(path), "history")
        os.makedirs(hist, exist_ok=True)
        os.replace(path, os.path.join(hist, f"pemilih_eval.usulan-{str((lama or {}).get('sha', '0xrusak'))[2:14]}.json"))
    d = {"status": "usulan", "sha": sha0x(params), "params": params, "catatan": catatan.strip(),
         "diusulkan": now_iso or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    _tulis_json(path, d)
    return d


def tulis_kunci(catatan: str, now_iso: Optional[str] = None, P: Optional[dict] = None, path: str = LOCK_FILE, usulan_path: str = USULAN_FILE) -> dict:
    """Kunci atas kata builder: hanya untuk sha yang SAMA dengan berkas usulan (yang disetujui = yang dipra-registrasi). Tidak menimpa."""
    if not (catatan or "").strip():
        raise ValueError("catatan wajib (siapa yang menyetujui dan kapan)")
    if os.path.exists(path):
        raise FileExistsError("kunci P74 sudah ada: aturan baru = keputusan baru + kunci baru, bukan timpa")
    params = copy.deepcopy(P if P is not None else PARAMS_P74)
    us, galat = _baca(usulan_path)
    if galat or us is None or us["sha"] != sha0x(params):
        raise ValueError("berkas usulan tidak ada / rusak / sha-nya beda dengan params kode: usulkan dulu, kunci sha yang sama")
    d = {"status": "terkunci", "sha": sha0x(params), "params": params, "catatan": catatan.strip(), "usulan_diusulkan": us.get("diusulkan"),
         "dikunci": now_iso or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    _tulis_json(path, d)
    return d
