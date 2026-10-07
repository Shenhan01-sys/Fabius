"""Meja AI v2 F4 (P156; F-D110 #4, epik 11 §6): evaluasi + perbaikan diri, dibangun dan dijalankan sebagai BAYANGAN.

Mesin hidup hari ini (rumus r4, F-D116) memilih bot dominan = argmax rata-rata (keyakinan x skor_bot) atas kursi AKTIF dengan bobot agent SAMA
(`meja2.konsensus2`), lalu buku Fabius = slot posisi (`meja_slot`). Teks epik §5-§6 (V_b berbobot W + prior lambda x Q_b) mendahului r4: prior Q_b
tidak pernah dikunci dan tidak ada di mesin hidup, jadi F4 tidak memakainya (lambda = 0, sama dengan mesin hidup). F4 menghitung di samping mesin
hidup, TANPA menyentuh keputusan, buku, prompt, Merkle root, atau konfigurasi hidup:

  1. NILAI per siklus. Portofolio tiap bot = aturan terkunci bot itu (`meja2.arah`) pada SEMUA aset berharga isi siklus itu, bobot / max(1, gross)
     (= `meja2.posisi` pada eksposur 1, tanpa veto). Return 5 menit dan 1 jam kemudian dari harga isi tercatat siklus t+1 dan t+12. Per agent sah:
     IC = korelasi peringkat Spearman (skor_bot 6 bot vs return 6 bot, peringkat rata-rata untuk seri), hit = bot pilihan termasuk return tertinggi
     (acak = jumlah bot seri tertinggi / 6), keyakinan agent untuk kalibrasi. Data hilang = siklus tidak dinilai + alasan (SK-M36), tidak dikarang.
  2. BOBOT agent W (`PARAMS_F4["bobot"]`, usulan + kunci lewat `engine/locks/meja_f4.*`): tiap jam dari IC 1 jam 24 jam terakhir,
     W = clamp(1 + kappa x rata-rata IC, 0,5, 2); netral 1 selama pemanasan / data kurang / bukan bilangan hingga (SK-M37).
  3. DUNIA bayangan (buku slot r4 + state hysteresis masing-masing, langkah = ekor `meja2.siklus2`): `penuh` (W = 1, tanpa dibuang; WAJIB SETIA ke
     buku Fabius tercatat tiap siklus, SK-M40), `bobot` (konsensus dengan W), `tanpa:<agent>` per kursi aktif, `tanpa_sumber:<Y>` per sumber data
     (atribusi sitasi `faktor` + veto keras data Y dihapus; BUKAN kontrafaktual "agent tidak pernah melihat Y" - itu butuh panggilan model kedua).
  4. RAPOR per agent tiap jam (teks + sha) DIREKAM, tidak masuk prompt hidup. Menyalakan bobot / rapor di mesin hidup = revisi rumus atau prompt
     baru + kunci + kata builder, bukan sakelar (SK-M41).
  5. EVALUATOR harian (aturan kode; LLM opsional lewat CLI) menulis USULAN. Usulan hanya lewat versi bayangan >= 288 siklus dengan kriteria lulus
     yang ditulis lebih dulu, lalu kunci hash + kata builder; tidak ada status "hidup" dan tidak ada jalur kode yang menulis konfigurasi hidup
     (SK-M13, SK-M38).

Gerbang: `FABIUS_F4=bayangan` (bawaan MATI) -> `x402_sinyal.v2_siklus` menjalankan `bayangan_utas` di utas sendiri SESUDAH hasil siklus hidup siap
(komit tidak menunggu); hasilnya digabung di awal siklus berikutnya (`gabung`) dan direkam ke `/data/meja/evaluasi/<tgl>.jsonl`, terbaca lewat
`GET /desk/archive/<tgl>` (`evaluation`, + `agent_records`). Rekaman F4 tidak masuk Merkle root: semuanya dihitung ulang dari rekaman yang dikomit.

Pakai:
  python -X utf8 tools/meja_eval.py rapor --dari 2026-10-08 --sampai 2026-10-10            # arsip gerbang (gerbang harus terjangkau)
  python -X utf8 tools/meja_eval.py rapor --berkas arsip.json                               # luring
  python -X utf8 tools/meja_eval.py contoh --keluar f4-contoh.json                          # arsip SINTETIS: meja hidup asli + pasar/model palsu
  python -X utf8 tools/meja_eval.py kunci [--usulan | --tulis] --catatan "..."              # status / berkas usulan / kunci (kata builder)
  python -X utf8 tools/meja_eval.py usulan --berkas arsip.json [--model <slug>]             # evaluator (tidak menulis apa pun yang hidup)
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import math
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Callable, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]                                                # tools + akar repo (engine)
import meja  # noqa: E402
import meja2  # noqa: E402
import meja_slot as ms  # noqa: E402
from engine.locks import LOCK_DIR  # noqa: E402
from engine.spec import sha0x  # noqa: E402

BOTS = meja2.BOTS
SIKLUS_S = meja.PARAMS["siklus_s"]
GERBANG = "https://fabius-x402-production.up.railway.app"
LOCK_FILE = os.path.join(LOCK_DIR, "meja_f4.lock.json")
USULAN_FILE = os.path.join(LOCK_DIR, "meja_f4.usulan.json")

# fitur -> sumber data (nama fitur = `meja_data` F1 + masukan aturan `meja2.fitur_aturan` + ticker). Satu fitur = satu sumber; dikunci bersama rumus.
SUMBER = {
    "binance": ["r_5m", "r_1j", "r_4j", "vol_1j", "funding", "z_r_1j", "r_24j", "volume_24j", "pnl_1j", "breadth_naik_1j", "sebaran_r4j",
                "funding_tahunan", "funding_vs_theta", "memecoin_naik_1j", "vol_btc_per_emas", "porsi_oversold"],
    "binance_ekstra": ["oi_ubah_1j", "taker_beli_jual", "z_oi_ubah_1j", "z_taker_beli_jual"],
    "dexscreener": ["dex_vol_1j_rel", "dex_beli_porsi_1j", "dex_likuiditas_usd", "dex_basis", "z_dex_vol_1j_rel"],
    "rugcheck": ["rug_skor", "rug_lp_terkunci", "rug_bahaya", "target_rug_bahaya"],
    "fomo": ["fomo_trader_top", "fomo_thesis"],
    "berita": ["berita_sebut_6j", "binance_listing", "binance_delisting", "z_berita_sebut_6j"],
    "candle_harian": ["tren_60h", "r_28h", "z_10h", "umur_listing_h", "hari_data"],
    "ledger_bot": ["n_posisi"],
}

PARAMS_F4 = {                                                                                 # tanpa nomor versi (F-D125 #7): dikenali dari sha
    "horizon_siklus": [1, 12],
    "portofolio_bot": "aturan terkunci bot (meja2.arah) pada semua aset berharga isi siklus itu (universe v2 + aset dipegang); bobot / max(1, gross) "
                      "= meja2.posisi pada eksposur 1 tanpa veto; candle harian satu aset gagal -> portofolio bot itu tidak terbaca",
    "return_bot": "sum_a w_a x (P_a(t+h) / P_a(t) - 1) pada harga isi tercatat siklus t dan t+h (tepat, bukan siklus terdekat); satu harga hilang = "
                  "siklus itu tidak dinilai",
    "ic": "korelasi peringkat Spearman skor_bot agent (6 bot) vs return 6 bot, peringkat rata-rata untuk seri; salah satu sisi konstan = tanpa IC",
    "hit": "1 bila bot pilihan agent termasuk return tertinggi (seri dihitung kena); acak = jumlah bot seri tertinggi / 6",
    "kalibrasi_ember": [0, 50, 65, 80, 101],
    "bobot": {"horizon_siklus": 12, "jendela_siklus": 288, "pemanasan": 288, "n_min_jendela": 144, "kappa": 5.0, "min": 0.5, "maks": 2.0,
              "tiap_s": 3600,
              "rumus": "W_i = clamp(1 + kappa x rata-rata IC 1 jam agent i atas siklus yang hasil 1 jamnya sudah ada dalam 288 siklus terakhir, "
                       "min, maks); W_i = 1 bila nilai IC kumulatif agent < pemanasan, IC dalam jendela < n_min_jendela, atau ada nilai tidak "
                       "hingga; dihitung di siklus pertama tiap jam UTC baru, di antaranya tetap"},
    "konsensus_bobot": "meja2.konsensus2 dengan keyakinan agent, keyakinan instrumen, dan eksposur agent sah dikali f_i = W_i x n / sum W "
                       "(n = agent aktif sah): nilai bot = sum W k s / sum W, eksposur = sum W e / sum W; W = 1 -> identik bit demi bit",
    "ablasi": {"agent": "tanpa agent X (kursi aktif): keputusan X dibuang, ambang dari n aktif - 1, bobot sama",
               "sumber": "tanpa sumber Y: instrumen yang SEMUA faktornya dari Y dibuang; keputusan yang SEMUA faktor utamanya dari Y dibuang; "
                         "veto agent berfaktor Y dibuang; fitur Y di snapshot dikosongkan (veto keras RugCheck / likuiditas DEX hilang)",
               "setia_toleransi_usdt": 0.01},
    "sumber": SUMBER,
    "rapor": {"jendela_siklus": 288, "horizon_siklus": 12, "maks_karakter": 600},
    "usulan": {"bayangan_min_siklus": 288, "maks_per_hari": 3, "n_min": 144, "ic_buruk": 0.0, "sumber_unggul_pp": 0.5, "lulus_sumber_pp": 0.25,
               "lulus_ic_selisih": 0.02, "lulus_sah_min": 0.95},
}


# ---------------------------------------------------------------- kunci (pola engine/pemilih.py; usulan dulu, kunci atas kata builder)

def params_sha(P: Optional[dict] = None) -> str:
    return sha0x(P if P is not None else PARAMS_F4)


def _baca(path: str) -> Tuple[Optional[dict], Optional[str]]:
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return (d, None) if sha0x(d["params"]) == d["sha"] else (d, "sha berkas != sha isi")
    except (OSError, ValueError, KeyError, TypeError) as e:
        return None, f"{type(e).__name__}"


def status(P: Optional[dict] = None, lock_path: str = LOCK_FILE, usulan_path: str = USULAN_FILE) -> dict:
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
    """Pra-registrasi rumus + parameter F4 SEBELUM data bayangan: berkas usulan ber-sha. Usulan lama yang berbeda dipindah ke `locks/history/`
    (tetap terlihat). Ditolak bila kunci sudah ada (rumus baru = kunci baru lewat keputusan baru, bukan menimpa)."""
    if not (catatan or "").strip():
        raise ValueError("catatan wajib (apa dan kenapa)")
    if os.path.exists(lock_path):
        raise FileExistsError("kunci F4 sudah ada: rumus baru = keputusan baru + kunci baru, bukan usulan ulang")
    params = copy.deepcopy(P if P is not None else PARAMS_F4)
    if os.path.exists(path):
        lama, _ = _baca(path)
        if lama and lama.get("sha") == sha0x(params):
            return lama
        hist = os.path.join(os.path.dirname(path), "history")
        os.makedirs(hist, exist_ok=True)
        os.replace(path, os.path.join(hist, f"meja_f4.usulan-{str((lama or {}).get('sha', '0xrusak'))[2:14]}.json"))
    d = {"status": "usulan", "sha": sha0x(params), "params": params, "catatan": catatan.strip(),
         "diusulkan": now_iso or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    _tulis_json(path, d)
    return d


def tulis_kunci(catatan: str, now_iso: Optional[str] = None, P: Optional[dict] = None, path: str = LOCK_FILE, usulan_path: str = USULAN_FILE) -> dict:
    """Kunci atas kata builder: hanya untuk sha yang SAMA dengan berkas usulan (yang disetujui = yang dipra-registrasi). Tidak menimpa."""
    if not (catatan or "").strip():
        raise ValueError("catatan wajib (siapa yang menyetujui dan kapan)")
    if os.path.exists(path):
        raise FileExistsError("kunci F4 sudah ada: rumus baru = keputusan baru + kunci baru, bukan timpa")
    params = copy.deepcopy(P if P is not None else PARAMS_F4)
    us, galat = _baca(usulan_path)
    if galat or us is None or us["sha"] != sha0x(params):
        raise ValueError("berkas usulan tidak ada / rusak / sha-nya beda dengan params kode: usulkan dulu, kunci sha yang sama")
    d = {"status": "terkunci", "sha": sha0x(params), "params": params, "catatan": catatan.strip(), "usulan_diusulkan": us.get("diusulkan"),
         "dikunci": now_iso or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    _tulis_json(path, d)
    return d


# ---------------------------------------------------------------- mode gerbang (SK-M41)

def mode(nilai: Optional[str] = None) -> str:
    """`FABIUS_F4`: "bayangan" = hitung + rekam, tidak berdagang. Kosong / "mati" / nilai lain (termasuk "hidup") = MATI: bobot dinamis atau rapor
    di mesin hidup bukan sakelar, melainkan revisi rumus / prompt baru + kunci + kata builder."""
    v = (os.environ.get("FABIUS_F4", "") if nilai is None else nilai).strip().lower()
    return "bayangan" if v == "bayangan" else "mati"


# ---------------------------------------------------------------- nilai per siklus (fungsi murni)

def peringkat(x: List[float]) -> List[float]:
    """Peringkat 1..n, seri = rata-rata peringkatnya."""
    idx = sorted(range(len(x)), key=lambda i: x[i])
    r, i = [0.0] * len(x), 0
    while i < len(idx):
        j = i
        while j + 1 < len(idx) and x[idx[j + 1]] == x[idx[i]]:
            j += 1
        for k in range(i, j + 1):
            r[idx[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(x: List[float], y: List[float]) -> Optional[float]:
    """Korelasi peringkat (Pearson atas peringkat rata-rata). None bila panjang beda, < 3 titik, atau salah satu sisi konstan."""
    if len(x) != len(y) or len(x) < 3:
        return None
    rx, ry = peringkat(x), peringkat(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    sxy = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sxx, syy = sum((a - mx) ** 2 for a in rx), sum((b - my) ** 2 for b in ry)
    if sxx <= 0 or syy <= 0:
        return None
    return round(sxy / math.sqrt(sxx * syy), 6)


def bobot_normal(w: Dict[str, float]) -> Dict[str, float]:
    g = max(1.0, sum(abs(v) for v in w.values()))
    return {a: round(v / g, 10) for a, v in sorted(w.items()) if abs(v) > 1e-12}


def portofolio_bot(bot: str, uni: List[str], p) -> Optional[Dict[str, float]]:
    """Bobot portofolio bot pada universe evaluasi; None bila aturan tidak terbaca (galat, atau candle harian satu aset gagal)."""
    try:
        w, why = meja2.arah(bot, list(uni), p)
    except Exception:  # noqa: BLE001
        return None
    if any(str(v).startswith("daily candles failed") for v in why.values()):
        return None
    return bobot_normal(w)


def return_portofolio(w: Optional[Dict[str, float]], p0: Dict[str, float], p1: Dict[str, float]) -> Optional[float]:
    if w is None:
        return None
    tot = 0.0
    for a, x in sorted(w.items()):
        if not p0.get(a) or not p1.get(a):
            return None
        tot += x * (p1[a] / p0[a] - 1)
    return round(tot, 10)


def nilai_agent(skor: Dict[str, float], pilihan: str, R: Dict[str, float]) -> dict:
    top = max(R[b] for b in BOTS)
    seri = [b for b in BOTS if R[b] == top]
    return {"ic": spearman([float(skor[b]) for b in BOTS], [R[b] for b in BOTS]), "hit": 1 if pilihan in seri else 0,
            "acak": round(len(seri) / len(BOTS), 6), "r_pilihan": R[pilihan], "terbaik": seri[0], "r_terbaik": top}


def entri(t0: int, harga: Dict[str, float], w_bot: Dict[str, Optional[dict]], rek: List[dict]) -> dict:
    """Satu siklus yang menunggu dinilai: portofolio bot + harga isi asetnya + skor tiap agent yang menjawab sah (aktif DAN uji)."""
    aset = sorted({a for w in w_bot.values() if w for a in w})
    kep = {}
    for r in rek:
        k = r.get("keputusan") or {}
        if str(r.get("agent", "")).startswith("v2:") and r.get("status") == "ok" and k.get("skor_bot"):
            kep[r["agent"].split(":", 1)[1]] = {"skor": dict(k["skor_bot"]), "bot": k["bot"], "k": k["k"], "kursi": r.get("kursi")}
    return {"t": t0, "harga": {a: harga[a] for a in aset if a in harga}, "w": w_bot, "kep": kep}


def nilai_entri(e: dict, harga1: Dict[str, float], h: int) -> Tuple[List[dict], Optional[Dict[str, float]], Optional[str]]:
    """SK-M36: entri siklus t dinilai pada harga isi siklus t+h -> (baris per agent, return per bot, alasan bila TIDAK dinilai)."""
    R = {}
    for b in BOTS:
        w = (e.get("w") or {}).get(b)
        if w is None:
            return [], None, f"portofolio {b} tidak terbaca"
        r = return_portofolio(w, e.get("harga") or {}, harga1)
        if r is None:
            return [], None, f"harga hilang ({b})"
        R[b] = r
    rows = [{"siklus": e["t"], "h": h, "agent": s, "kursi": k.get("kursi"), "bot": k["bot"], "k": k["k"], **nilai_agent(k["skor"], k["bot"], R)}
            for s, k in sorted((e.get("kep") or {}).items())]
    return rows, R, None


def _rata(xs: List[float]) -> Optional[float]:
    return round(sum(xs) / len(xs), 6) if xs else None


def ringkas(rows: List[dict], P: dict = PARAMS_F4) -> dict:
    """Metrik satu agent atas baris nilai (satu horizon): IC rata-rata, hit vs acak, ember kalibrasi keyakinan, kesalahan terbesar."""
    ics = [r["ic"] for r in rows if isinstance(r.get("ic"), (int, float)) and math.isfinite(r["ic"])]
    ed = P["kalibrasi_ember"]
    ember = []
    for lo, hi in zip(ed[:-1], ed[1:]):
        b = [r for r in rows if lo <= round(r["k"] * 100) < hi]
        bi = [r["ic"] for r in b if isinstance(r.get("ic"), (int, float))]
        ember.append({"dari": lo, "sampai": hi - 1, "n": len(b), "keyakinan": _rata([r["k"] * 100 for r in b]), "hit": _rata([r["hit"] for r in b]),
                      "ic": _rata(bi)})
    salah = max(rows, key=lambda r: (r["r_terbaik"] - r["r_pilihan"], -r["siklus"]), default=None)
    return {"n": len(rows), "n_ic": len(ics), "ic": _rata(ics), "hit": _rata([r["hit"] for r in rows]), "acak": _rata([r["acak"] for r in rows]),
            "kalibrasi": ember,
            "salah_terbesar": ({k: salah[k] for k in ("siklus", "bot", "r_pilihan", "terbaik", "r_terbaik")} if salah and salah["r_terbaik"] > salah["r_pilihan"] else None)}


# ---------------------------------------------------------------- bobot agent (rumus usulan; dikunci atas kata builder)

def hitung_bobot(riwayat: Dict[str, List[list]], n_kum: Dict[str, int], t0: int, P: dict = PARAMS_F4) -> Tuple[Dict[str, float], Dict[str, str]]:
    """riwayat[slug] = baris [siklus, ic, ...] horizon 1 jam (siklus = waktu keputusan; nilainya ada di siklus + 1 jam). -> (W, alasan) (SK-M37)."""
    B = P["bobot"]
    batas = t0 - (B["horizon_siklus"] + B["jendela_siklus"]) * SIKLUS_S
    W, why = {}, {}
    for s in sorted(riwayat):
        baris = [r for r in riwayat[s] if r[0] > batas and r[0] + B["horizon_siklus"] * SIKLUS_S <= t0 and r[1] is not None]
        ics = [r[1] for r in baris]
        if any(not isinstance(x, (int, float)) or not math.isfinite(x) for x in ics):
            W[s], why[s] = 1.0, "IC tidak hingga di riwayat -> netral 1"
        elif n_kum.get(s, 0) < B["pemanasan"]:
            W[s], why[s] = 1.0, f"pemanasan {n_kum.get(s, 0)}/{B['pemanasan']}"
        elif len(ics) < B["n_min_jendela"]:
            W[s], why[s] = 1.0, f"IC dalam jendela {len(ics)} < {B['n_min_jendela']}"
        else:
            m = sum(ics) / len(ics)
            w = 1.0 + B["kappa"] * m
            if not math.isfinite(w):
                W[s], why[s] = 1.0, "bobot tidak hingga -> netral 1"
            else:
                W[s] = round(max(B["min"], min(B["maks"], w)), 6)
                why[s] = f"IC rata-rata {m:+.4f} atas {len(ics)} siklus"
    return W, why


def perlu_bobot(t0: int, t_lalu: Optional[int], P: dict = PARAMS_F4) -> bool:
    """Bobot dihitung di siklus PERTAMA tiap jam UTC baru (tahan terhadap siklus yang bolong), di antaranya tetap."""
    s = P["bobot"]["tiap_s"]
    return t_lalu is None or t0 // s != t_lalu // s


def berbobot(sah: Dict[str, dict], W: Dict[str, float]) -> Dict[str, dict]:
    """Masukan `konsensus2` berbobot: keyakinan, keyakinan instrumen, eksposur x f_i = W_i x n / sum W. W = 1 semua -> f = 1,0 persis (identik)."""
    if not sah:
        return {}
    n, tot = len(sah), sum(float(W.get(s, 1.0)) for s in sah)
    out = {}
    for s, d in sah.items():
        f = float(W.get(s, 1.0)) * n / tot
        out[s] = {**d, "k": d["k"] * f, "eksposur": d["eksposur"] * f, "instrumen": [{**it, "k": it["k"] * f} for it in d.get("instrumen") or []]}
    return out


# ---------------------------------------------------------------- ablasi

def peta_sumber(P: dict = PARAMS_F4) -> Dict[str, str]:
    return {f: y for y, fs in P["sumber"].items() for f in fs}


def sumber_dari(f: str, peta: Dict[str, str]) -> str:
    return peta.get(f) or (peta.get(f[2:]) if f.startswith("z_") else None) or "lain"


def sumber_keputusan(d: dict, peta: Dict[str, str]) -> List[str]:
    """Sumber yang disitasi satu keputusan agent (faktor utama + faktor instrumen + faktor veto)."""
    fs = list(d.get("faktor") or []) + [f for it in d.get("instrumen") or [] for f in it.get("faktor") or []] + \
        [v.get("faktor") for v in d.get("veto") or [] if v.get("faktor")]
    return sorted({sumber_dari(f, peta) for f in fs})


def tanpa_sumber(sah: Dict[str, dict], snap: Optional[dict], y: str, peta: Dict[str, str]) -> Tuple[Dict[str, dict], Optional[dict]]:
    """Dunia tanpa sumber Y (atribusi sitasi, bukan kontrafaktual prompt): lihat PARAMS_F4["ablasi"]["sumber"]."""
    dari_y = lambda fs: bool(fs) and all(sumber_dari(f, peta) == y for f in fs)  # noqa: E731
    out = {}
    for s, d in sah.items():
        if dari_y(d.get("faktor") or []):
            continue                                                                         # keputusan bertumpu hanya pada Y: seperti tidak menjawab
        out[s] = {**d, "instrumen": [it for it in d.get("instrumen") or [] if not dari_y(it.get("faktor") or [])],
                  "veto": [v for v in d.get("veto") or [] if sumber_dari(str(v.get("faktor") or ""), peta) != y]}
    if snap is None:
        return out, None
    fa = {a: {k: (None if sumber_dari(k, peta) == y else v) for k, v in (f or {}).items()} for a, f in (snap.get("fitur_aset") or {}).items()}
    return out, {**snap, "fitur_aset": fa}


# ---------------------------------------------------------------- dunia bayangan (langkah = ekor meja2.siklus2, pola P163 replay_slot)

def pra_siklus(books: dict) -> dict:
    """Salinan state + buku Fabius SEBELUM siklus hidup berjalan (dunia bayangan dimulai / disinkron dari sini)."""
    return copy.deepcopy({"state": books.get("_v2_state") or {}, "buku": books.get("v2") or meja.buku_baru()})


def dunia_baru(pra: dict, t0: int) -> dict:
    return {"state": copy.deepcopy(pra["state"]), "buku": copy.deepcopy(pra["buku"]), "mulai": t0}


def langkah_dunia(w: dict, kep: Dict[str, dict], aktif: List[str], snap: Optional[dict], p, t0: int, harga: Dict[str, float],
                  atr: Callable[[str], Optional[float]], keluar: Callable[[dict], bool]) -> dict:
    """Satu siklus satu dunia: SAMA dengan ekor `meja2.siklus2` (konsensus2 -> posisi -> rem rugi -> kandidat slot -> migrasi + langkah)."""
    state, buku = w["state"], w["buku"]
    bot_lalu = state.get("bot")
    kk, _ = meja2.konsensus2(kep, state, snap, n_aktif=len(aktif))
    tg, _ = meja2.posisi(kk.get("bot"), kk.get("instrumen", []), kk.get("eksposur", 0.0), kk.get("veto", []), p)
    hari, e_now = time.strftime("%Y-%m-%d", time.gmtime(t0)), meja.ekuitas(buku, harga)
    if state.get("hari") != hari:
        state.update(hari=hari, ekuitas_awal_hari=round(e_now, 4))
    rem = e_now / max(state["ekuitas_awal_hari"], 1e-9) - 1 <= -meja2.PARAMS2["rugi_harian_maks"]
    rk = {**kk, "ambang": meja2.ambang(len(aktif)), "aktif": sorted(aktif), "target": tg}
    kand = [] if rem or "skor_instrumen" not in kk else ms.kandidat(rk, atr)
    isi = ms.migrasi(buku, harga, bot_lalu) + ms.langkah(buku, t0, harga, kand, keluar, rem)
    slot = ms.snapshot(buku, harga)
    buku["target"] = {x["aset"]: {"w": x["w"], "k": 1.0} for x in slot}
    return {"bot": kk.get("bot"), "instrumen": kk.get("instrumen") or [], "target": tg, "isi": isi, "slot": slot,
            "ekuitas": round(meja.ekuitas(buku, harga), 4), "rem": rem}


def banding(x: Optional[dict], lv: dict, tol: float) -> List[str]:
    """SK-M40: dunia `penuh` vs rekaman Fabius tercatat -> daftar field yang beda (kosong = SETIA)."""
    if x is None:
        return ["dunia penuh tidak terhitung"]
    beda = [k for k in ("bot", "instrumen", "target", "slot", "isi") if meja.canon(x.get(k)) != meja.canon(lv.get(k))]
    if abs(float(x["ekuitas"]) - float(lv.get("ekuitas") or 0.0)) > tol:
        beda.append("ekuitas")
    return beda


# ---------------------------------------------------------------- rapor (direkam; TIDAK masuk prompt hidup)

def _jam(t: int) -> str:
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%m-%d %H:%M")


def rapor_teks(slug: str, m: dict, P: dict = PARAMS_F4) -> str:
    """Rapor bahasa Inggris (bahasa prompt meja) untuk SATU agent. Disiapkan + direkam; menyalakannya di prompt hidup = revisi prompt + kunci."""
    if not m["n"]:
        return f"Report card for {slug}: no evaluated cycles yet."
    kal = "; ".join(f"conf {e['dari']}-{e['sampai']}: hit {e['hit']:.0%} (n {e['n']})" for e in m["kalibrasi"] if e["n"])
    ic = f"{m['ic']:+.3f}" if m["ic"] is not None else "n/a"
    s = (f"Your report card ({slug}), last 24h at the 1h horizon, {m['n']} cycles: rank IC of your bot scores vs realised bot returns {ic}; "
         f"your top bot was the best bot {m['hit']:.0%} of the time (random pick {m['acak']:.0%}); calibration {kal or 'n/a'}.")
    x = m.get("salah_terbesar")
    if x:
        s += (f" Biggest miss: {_jam(x['siklus'])}Z you picked {x['bot']} ({x['r_pilihan']:+.2%} in 1h), best was {x['terbaik']} "
              f"({x['r_terbaik']:+.2%}).")
    return s[:P["rapor"]["maks_karakter"]]


def prompt_dengan_rapor(prompt: str, teks: str) -> str:
    """Bentuk prompt BAYANGAN dengan rapor (untuk uji sebelum/sesudah). Tidak dipanggil mesin hidup."""
    return f"{prompt}\n\n{teks}"


def efek_rapor(rows: List[dict], t_mulai: int, P: dict = PARAMS_F4) -> dict:
    """Efek rapor sebelum/sesudah t_mulai (siklus rapor mulai masuk prompt, bila kelak dinyalakan): metrik 288 siklus terakhir sebelum vs 288
    siklus pertama sesudah, satu agent satu horizon. `cukup` hanya bila kedua sisi punya >= 288 IC."""
    n = P["rapor"]["jendela_siklus"]
    seb = sorted([r for r in rows if r["siklus"] < t_mulai], key=lambda r: r["siklus"])[-n:]
    ses = sorted([r for r in rows if r["siklus"] >= t_mulai], key=lambda r: r["siklus"])[:n]
    a, b = ringkas(seb, P), ringkas(ses, P)
    cukup = a["n_ic"] >= n and b["n_ic"] >= n
    return {"sebelum": a, "sesudah": b, "cukup": cukup,
            "selisih_ic": round(b["ic"] - a["ic"], 6) if a["ic"] is not None and b["ic"] is not None else None,
            "selisih_hit": round(b["hit"] - a["hit"], 6) if a["hit"] is not None and b["hit"] is not None else None}


# ---------------------------------------------------------------- usulan evaluator (SK-M13, SK-M38)

JENIS = ("fitur", "prompt")
ISI_BOLEH = {"fitur": ("buang_sumber", "buang_fitur"), "prompt": ("tambah_rapor", "tambah_teks")}
TRANSISI = {"usulan": ("bayangan", "ditolak"), "bayangan": ("lulus", "gagal"), "lulus": ("siap_kunci",)}
SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")


def validasi_usulan(u: dict, P: dict = PARAMS_F4) -> None:
    """Usulan sah atau ValueError. Usulan hanya boleh menyentuh fitur prompt / teks prompt dan WAJIB membawa kriteria lulus tertulis dengan
    >= 288 siklus bayangan. Jenis / isi lain (rumus, bobot, kursi, parameter, mode hidup) = perubahan hidup -> ditolak (SK-M38)."""
    U = P["usulan"]
    j = u.get("jenis")
    if j not in JENIS:
        raise ValueError(f"SK-M38: jenis {str(j)[:40]!r} = perubahan konfigurasi hidup / rumus; hanya {', '.join(JENIS)} lewat versi bayangan")
    isi = u.get("isi")
    if not isinstance(isi, dict) or not isi or any(k not in ISI_BOLEH[j] for k in isi):
        raise ValueError(f"SK-M38: isi usulan {j} hanya boleh {', '.join(ISI_BOLEH[j])} (perubahan konfigurasi hidup ditolak)")
    if "buang_sumber" in isi and isi["buang_sumber"] not in P["sumber"]:
        raise ValueError("buang_sumber bukan sumber yang dikenal")
    if "buang_fitur" in isi and (not isinstance(isi["buang_fitur"], list) or not isi["buang_fitur"]
                                 or any(sumber_dari(str(f), peta_sumber(P)) == "lain" for f in isi["buang_fitur"])):
        raise ValueError("buang_fitur harus daftar nama fitur yang dikenal")
    if "tambah_rapor" in isi and isi["tambah_rapor"] is not True:
        raise ValueError("tambah_rapor harus true")
    if "tambah_teks" in isi and (not isinstance(isi["tambah_teks"], str) or not 0 < len(isi["tambah_teks"]) <= 400):
        raise ValueError("tambah_teks 1..400 karakter")
    sas = str(u.get("sasaran") or "")
    if not (sas == "semua" or (sas.startswith("agent:") and SLUG.match(sas[6:]))):
        raise ValueError("sasaran = 'semua' atau 'agent:<slug>'")
    kr = u.get("kriteria_lulus")
    if not isinstance(kr, dict) or not str(kr.get("lulus_bila") or "").strip() or not str(kr.get("metrik") or "").strip():
        raise ValueError("SK-M13: kriteria lulus (metrik + lulus_bila) wajib ditulis SEBELUM bayangan")
    if not isinstance(kr.get("minimal_siklus"), int) or kr["minimal_siklus"] < U["bayangan_min_siklus"]:
        raise ValueError(f"SK-M13: bayangan minimal {U['bayangan_min_siklus']} siklus")


def usulan_baru(jenis: str, sasaran: str, isi: dict, alasan: str, kriteria: dict, oleh: str, t0: int, bukti: Optional[dict] = None,
                P: dict = PARAMS_F4) -> dict:
    u = {"dibuat": t0, "oleh": oleh, "jenis": jenis, "sasaran": sasaran, "isi": isi, "alasan": str(alasan or "")[:400],
         "bukti": bukti or {}, "kriteria_lulus": kriteria, "params_f4_sha": params_sha(P)}
    validasi_usulan(u, P)
    u["sha"] = meja.sha(u)                                                                   # sha atas usulan + kriteria, SEBELUM bayangan
    u.update(id=f"U-{time.strftime('%Y%m%d', time.gmtime(t0))}-{u['sha'][2:10]}", status="usulan", riwayat=[[t0, None, "usulan"]])
    return u


def ubah_status(u: dict, ke: str, t0: int, P: dict = PARAMS_F4, **bukti) -> dict:
    """Mesin status usulan. Tidak ada status "hidup": menerapkan usulan yang `siap_kunci` = revisi rumus / prompt baru oleh manusia + kunci hash +
    kata builder, di luar modul ini (SK-M13)."""
    if ke not in TRANSISI.get(u.get("status"), ()):
        raise ValueError(f"SK-M13: {u.get('status')} -> {ke} tidak diizinkan (usulan tidak punya jalur ke konfigurasi hidup)")
    validasi_usulan(u, P)
    if meja.sha({k: v for k, v in u.items() if k not in ("sha", "id", "status", "riwayat", "bayangan", "hasil", "kunci")}) != u["sha"]:
        raise ValueError("SK-M13: isi / kriteria usulan berubah sesudah dibuat (sha beda)")
    v = copy.deepcopy(u)
    if ke == "bayangan":
        if u["jenis"] == "prompt" and not bukti.get("izin_biaya"):
            raise ValueError("bayangan prompt butuh panggilan model kedua per siklus: izin biaya dari builder wajib")
        v["bayangan"] = {"mulai": t0, "siklus": 0, "tidak_setia": 0, "eq_mulai": bukti.get("eq_mulai"), "izin_biaya": bukti.get("izin_biaya")}
    elif ke in ("lulus", "gagal"):
        n = (u.get("bayangan") or {}).get("siklus", 0)
        if n < u["kriteria_lulus"]["minimal_siklus"]:
            raise ValueError(f"SK-M13: bayangan baru {n} siklus < {u['kriteria_lulus']['minimal_siklus']}")
        v["hasil"] = bukti.get("hasil")
    elif ke == "siap_kunci":
        if not str(bukti.get("kata_builder") or "").strip() or not re.fullmatch(r"0x[0-9a-f]{64}", str(bukti.get("sha_kunci") or "")):
            raise ValueError("SK-M13: siap_kunci butuh kata builder + sha kunci versi baru")
        v["kunci"] = {"kata_builder": str(bukti["kata_builder"])[:300], "sha_kunci": bukti["sha_kunci"]}
    v["status"] = ke
    v["riwayat"] = v["riwayat"] + [[t0, u["status"], ke]]
    return v


def nilai_usulan(u: dict, eq_kini: Dict[str, float], P: dict = PARAMS_F4) -> dict:
    """Usulan `buang_sumber` Y dinilai terhadap kriteria tertulis: selisih % dunia `tanpa_sumber:Y` vs buku Fabius sejak bayangan mulai, dunia
    `penuh` SETIA tiap siklus bayangan. Usulan prompt tidak dinilai otomatis (butuh bayangan model)."""
    b = u.get("bayangan") or {}
    y = (u.get("isi") or {}).get("buang_sumber")
    e0 = b.get("eq_mulai") or {}
    nama = f"tanpa_sumber:{y}"
    if not y or nama not in e0 or "fabius" not in e0 or nama not in eq_kini or "fabius" not in eq_kini:
        return {"lulus": False, "alasan": "ekuitas awal / kini tidak lengkap"}
    pp = ((eq_kini[nama] / e0[nama] - 1) - (eq_kini["fabius"] / e0["fabius"] - 1)) * 100
    ok = b.get("tidak_setia", 0) == 0 and pp >= P["usulan"]["lulus_sumber_pp"]
    return {"lulus": ok, "selisih_pp": round(pp, 4), "tidak_setia": b.get("tidak_setia", 0), "siklus": b.get("siklus", 0)}


def evaluator_aturan(m_agent: Dict[str, dict], delta_sumber: Dict[str, Optional[float]], setia_ok: bool, terbuka: List[dict], t0: int,
                     P: dict = PARAMS_F4, oleh: str = "evaluator-kode") -> List[dict]:
    """Evaluator harian deterministik. E1: agent dengan IC 1 jam rata-rata <= ic_buruk atas >= n_min siklus -> usulan prompt "lampirkan rapor".
    E2: sumber Y yang dunia tanpa-Y-nya unggul >= sumber_unggul_pp atas buku Fabius dalam 24 jam (dunia penuh SETIA) -> usulan fitur "buang Y".
    Tidak ada usulan ganda untuk (jenis, sasaran, isi) yang masih terbuka; maks `maks_per_hari`."""
    U = P["usulan"]
    buka = {(u["jenis"], u["sasaran"], meja.canon(u["isi"])) for u in terbuka if u.get("status") in ("usulan", "bayangan", "lulus")}
    out: List[dict] = []

    def tambah(**kw):
        key = (kw["jenis"], kw["sasaran"], meja.canon(kw["isi"]))
        if key not in buka and len(out) < U["maks_per_hari"]:
            out.append(usulan_baru(oleh=oleh, t0=t0, P=P, **kw))
            buka.add(key)
    for s, m in sorted(m_agent.items()):
        if m.get("n_ic", 0) >= U["n_min"] and m.get("ic") is not None and m["ic"] <= U["ic_buruk"]:
            tambah(jenis="prompt", sasaran=f"agent:{s}", isi={"tambah_rapor": True},
                   alasan=f"IC 1 jam rata-rata {m['ic']:+.4f} atas {m['n_ic']} siklus (<= {U['ic_buruk']})", bukti={"ic": m["ic"], "n_ic": m["n_ic"]},
                   kriteria={"metrik": "ic_1j", "minimal_siklus": U["bayangan_min_siklus"],
                             "lulus_bila": f"IC 1 jam versi bayangan (prompt + rapor) - IC 1 jam versi hidup pada siklus yang sama >= {U['lulus_ic_selisih']} "
                                           f"DAN jawaban sah versi bayangan >= {U['lulus_sah_min']:.0%}"})
    if setia_ok:
        for y, d in sorted(delta_sumber.items(), key=lambda kv: -(kv[1] or -1e9)):
            if d is not None and d >= U["sumber_unggul_pp"]:
                tambah(jenis="fitur", sasaran="semua", isi={"buang_sumber": y},
                       alasan=f"dunia tanpa {y} unggul {d:+.3f} pp atas buku Fabius dalam 24 jam (dunia penuh SETIA)", bukti={"selisih_pp_24j": d},
                       kriteria={"metrik": "selisih_pp_tanpa_sumber", "minimal_siklus": U["bayangan_min_siklus"],
                                 "lulus_bila": f"selama >= {U['bayangan_min_siklus']} siklus bayangan berikutnya dunia tanpa_sumber:{y} unggul >= "
                                               f"{U['lulus_sumber_pp']} pp atas buku Fabius DAN dunia penuh SETIA di semua siklus itu"})
    return out


SYSTEM_EVALUATOR = (
    "You are Fabius' daily desk evaluator. You read measured metrics of the 5-minute AI desk (per-agent rank IC of bot scores vs realised bot "
    "returns, top-pick hit rate, calibration, and shadow books without each agent / without each data source). You may only PROPOSE: kind "
    "\"fitur\" (isi: buang_sumber <source> or buang_fitur [feature names]) or kind \"prompt\" (isi: tambah_rapor true or tambah_teks <one sentence>), "
    "each with sasaran \"semua\" or \"agent:<slug>\", a short alasan, and kriteria_lulus {metrik, lulus_bila, minimal_siklus >= 288} written BEFORE any "
    "shadow run. You cannot change formulas, weights, seats, parameters or anything live: such proposals are rejected. Propose nothing when the "
    "evidence is weak. Answer with ONE JSON object {\"usulan\": [...]} and nothing else.")


def prompt_evaluator(ringkasan: dict) -> str:
    return "Measured desk metrics (JSON):\n" + json.dumps(ringkasan, sort_keys=True, ensure_ascii=False)[:12000]


def parse_usulan_llm(text: str, t0: int, P: dict = PARAMS_F4) -> Tuple[List[dict], List[dict]]:
    """Jawaban evaluator LLM = data tak tepercaya: tiap usulan divalidasi sama dengan usulan kode; yang mencoba perubahan hidup ditolak + dicatat."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return [], [{"galat": "tanpa JSON"}]
    try:
        items = json.loads(m.group(0)).get("usulan") or []
    except (ValueError, AttributeError):
        return [], [{"galat": "JSON rusak"}]
    sah, tolak = [], []
    for it in items[:P["usulan"]["maks_per_hari"] * 2] if isinstance(items, list) else []:
        try:
            it = it if isinstance(it, dict) else {}
            sah.append(usulan_baru(jenis=it.get("jenis"), sasaran=it.get("sasaran"), isi=it.get("isi"), alasan=it.get("alasan"),
                                   kriteria=it.get("kriteria_lulus"), oleh="evaluator-llm", t0=t0, P=P))
        except (ValueError, TypeError) as e:
            tolak.append({"usulan": json.dumps(it, ensure_ascii=False, sort_keys=True)[:300], "galat": str(e)[:200]})
    return sah[:P["usulan"]["maks_per_hari"]], tolak


# ---------------------------------------------------------------- satu siklus bayangan (dipanggil gerbang di utas sendiri)

def state_baru(t0: int, P: dict = PARAMS_F4) -> dict:
    return {"params_f4_sha": params_sha(P), "mulai": t0, "terakhir": None, "antre": [], "riwayat": {}, "n_kum": {},
            "bobot": {"t": None, "W": {}, "alasan": {}}, "dunia": {}, "sinkron_ulang": False, "setia": [], "eq_jam": {}, "usulan": [],
            "hari_evaluator": None}


def _delta_sumber(st: dict, t0: int) -> Dict[str, Optional[float]]:
    """Selisih pp 24 jam dunia tanpa_sumber:Y vs buku Fabius dari potret ekuitas per jam."""
    fab = st["eq_jam"].get("fabius") or []
    lalu = next((x for x in fab if x[0] >= t0 - 86_400), None)
    out = {}
    for nama, rows in st["eq_jam"].items():
        if not nama.startswith("tanpa_sumber:") or not lalu or not fab:
            continue
        y0 = next((x for x in rows if x[0] == lalu[0]), None)
        out[nama.split(":", 1)[1]] = (round(((rows[-1][1] / y0[1] - 1) - (fab[-1][1] / lalu[1] - 1)) * 100, 4)
                                      if y0 and rows[-1][0] == fab[-1][0] and lalu[0] <= t0 - 86_400 + 3600 else None)
    return out


def siklus_bayangan(st: Optional[dict], pra: dict, rek: List[dict], harga: Dict[str, float], snap: Optional[dict], p, t0: int,
                    P: dict = PARAMS_F4) -> Tuple[dict, dict]:
    """Satu siklus F4 SESUDAH siklus hidup: (state baru, rekaman evaluasi). Tidak mengubah `pra`, `rek`, `harga`, `snap`."""
    sha_p = params_sha(P)
    st = copy.deepcopy(st) if st and st.get("params_f4_sha") == sha_p else state_baru(t0, P)
    lv = next((r for r in rek if r.get("agent") == "v2"), None)
    if lv is None:
        raise ValueError("rekaman konsensus Fabius tidak ada di siklus ini")
    out = {"siklus": t0, "agent": "f4", "mode": "bayangan", "params_f4_sha": sha_p, "status_kunci": status(P)["state"], "galat": [],
           "celah_siklus": max(0, (t0 - st["terakhir"]) // SIKLUS_S - 1) if st["terakhir"] is not None else 0}
    # (1) nilai yang jatuh tempo + portofolio bot siklus ini
    w_bot = {b: portofolio_bot(b, sorted(harga), p) for b in BOTS}
    nilai, ret, sisa, tanpa = [], {}, [], []
    for e in st["antre"]:
        umur, pas = divmod(t0 - e["t"], SIKLUS_S)
        if pas == 0 and umur in P["horizon_siklus"]:
            rows, R, why = nilai_entri(e, harga, umur)
            if why:
                tanpa.append({"siklus": e["t"], "h": umur, "alasan": why})
            else:
                nilai += rows
                ret[str(umur)] = {"siklus": e["t"], "r": R}
        if umur < max(P["horizon_siklus"]):
            sisa.append(e)
    st["antre"] = sisa + [entri(t0, harga, w_bot, rek)]
    hb = P["bobot"]["horizon_siklus"]
    for r in nilai:
        if r["h"] == hb:
            st["riwayat"].setdefault(r["agent"], []).append([r["siklus"], r["ic"], r["hit"], r["acak"], r["k"], r["bot"], r["r_pilihan"], r["terbaik"],
                                                             r["r_terbaik"]])
            if r["ic"] is not None:
                st["n_kum"][r["agent"]] = st["n_kum"].get(r["agent"], 0) + 1
    batas = t0 - (hb + P["bobot"]["jendela_siklus"]) * SIKLUS_S
    st["riwayat"] = {s: [x for x in rows if x[0] > batas] for s, rows in st["riwayat"].items() if any(x[0] > batas for x in rows)}
    out.update(portofolio_bot=w_bot, nilai=nilai, return_bot=ret, tanpa_data=tanpa)
    # (2) bobot agent per jam (SK-M37)
    jam_baru = perlu_bobot(t0, st["bobot"]["t"], P)
    if jam_baru:
        W, why = hitung_bobot(st["riwayat"], st["n_kum"], t0, P)
        st["bobot"] = {"t": t0, "W": W, "alasan": why}
    out["bobot"] = {**st["bobot"], "diperbarui": jam_baru}
    # (3) dunia bayangan
    aktif = list(lv.get("aktif") or [])
    sah = {r["agent"].split(":", 1)[1]: r["keputusan"] for r in rek
           if str(r.get("agent", "")).startswith("v2:") and r.get("status") == "ok" and r.get("kursi") == "aktif" and r.get("keputusan")}
    if out["celah_siklus"] or st.get("sinkron_ulang") or "penuh" not in st["dunia"]:
        st["dunia"]["penuh"] = dunia_baru(pra, t0)                                           # SK-M40: hanya dunia penuh yang disinkron ulang
        out["sinkron_ulang"] = True
        st["sinkron_ulang"] = False
    peta = peta_sumber(P)
    rencana = {"penuh": (sah, aktif, snap), "bobot": (berbobot(sah, st["bobot"]["W"]), aktif, snap)}
    for x in sorted(aktif):
        rencana[f"tanpa:{x}"] = ({s: d for s, d in sah.items() if s != x}, [a for a in aktif if a != x], snap)
    for y in sorted(P["sumber"]):
        k2, sn2 = tanpa_sumber(sah, snap, y, peta)
        rencana[f"tanpa_sumber:{y}"] = (k2, aktif, sn2)
    out["dunia_berhenti"] = sorted(n for n in st["dunia"] if n not in rencana)
    for n in out["dunia_berhenti"]:
        st["dunia"].pop(n)
    atr_c: Dict[str, Optional[float]] = {}
    kel_c: Dict[tuple, Optional[Dict[str, float]]] = {}

    def atr(a: str) -> Optional[float]:
        if a not in atr_c:
            try:
                atr_c[a] = ms.atr_frac(p.harian(a), ms.PARAMS_SLOT["atr_hari"])
            except Exception:  # noqa: BLE001 - sama dengan meja hidup (SK-M27)
                atr_c[a] = None
        return atr_c[a]

    def keluar(pos: dict) -> bool:
        key = (pos["bot"], tuple(sorted(pos.get("uni") or [])))
        if key not in kel_c:
            kel_c[key] = meja2.aturan_terbaca(pos["bot"], list(pos.get("uni") or []), p)
        w = kel_c[key]
        if w is None:
            return False
        x = w.get(pos["aset"], 0.0)
        return (1 if x > 1e-12 else -1 if x < -1e-12 else 0) != pos["arah"]
    hasil: Dict[str, dict] = {}
    for nama, (kep, akt, sn) in rencana.items():
        w = st["dunia"].setdefault(nama, dunia_baru(pra, t0))
        try:
            hasil[nama] = langkah_dunia(w, kep, akt, sn, p, t0, harga, atr, keluar)
        except Exception as e:  # noqa: BLE001 - satu dunia gagal tidak menghentikan yang lain; dicatat
            out["galat"].append(f"{nama}: {type(e).__name__}: {str(e)[:120]}")
    beda = banding(hasil.get("penuh"), lv, P["ablasi"]["setia_toleransi_usdt"])
    out["setia"], out["beda"] = not beda, beda
    if beda:
        st["sinkron_ulang"] = True
    st["setia"] = (st["setia"] + [[t0, 0 if beda else 1]])[-P["bobot"]["jendela_siklus"]:]
    out["dunia"] = {n: {"ekuitas": x["ekuitas"], "bot": x["bot"], "slot": len(x["slot"]), "isi": len(x["isi"]),
                        "fee": round(sum(f.get("fee", 0.0) for f in x["isi"]), 6), "rem": x["rem"], "mulai": st["dunia"][n]["mulai"]}
                    for n, x in sorted(hasil.items())}
    out["ekuitas_fabius"] = lv.get("ekuitas")
    if jam_baru:                                                                             # potret ekuitas per jam (evaluator E2)
        for n, x in [("fabius", {"ekuitas": lv.get("ekuitas")})] + sorted(hasil.items()):
            st["eq_jam"][n] = (st["eq_jam"].get(n, []) + [[t0, x["ekuitas"]]])[-25:]
        st["eq_jam"] = {n: v for n, v in st["eq_jam"].items() if n == "fabius" or n in hasil}
    # (4) rapor per jam - DIREKAM, tidak masuk prompt hidup
    if jam_baru:
        out["rapor"] = {}
        for s in sorted(st["riwayat"]):
            m = ringkas(_baris(st["riwayat"][s], s), P)
            teks = rapor_teks(s, m, P)
            out["rapor"][s] = {"teks": teks, "sha": meja.sha(teks.encode()), "n": m["n"], "ic": m["ic"], "hit": m["hit"]}
    # (5) usulan: hitung siklus bayangan, lalu evaluator harian di siklus pertama tiap hari UTC baru
    for u in st["usulan"]:
        if u["status"] == "bayangan":
            u["bayangan"]["siklus"] += 1
            u["bayangan"]["tidak_setia"] += 1 if beda else 0
    hari = t0 // 86_400
    out["usulan"] = []
    if st["hari_evaluator"] is None:
        st["hari_evaluator"] = hari
    elif st["hari_evaluator"] != hari:
        st["hari_evaluator"] = hari
        out["usulan"] = evaluator_harian(st, t0, {n: x["ekuitas"] for n, x in hasil.items()} | {"fabius": lv.get("ekuitas")}, P)
    st["terakhir"] = t0
    return st, out


def _baris(rows: List[list], slug: str) -> List[dict]:
    return [{"siklus": r[0], "ic": r[1], "hit": r[2], "acak": r[3], "k": r[4], "bot": r[5], "r_pilihan": r[6], "terbaik": r[7], "r_terbaik": r[8],
             "agent": slug} for r in rows]


def evaluator_harian(st: dict, t0: int, eq_kini: Dict[str, float], P: dict = PARAMS_F4) -> List[dict]:
    """(a) usulan bayangan yang sudah >= minimal_siklus dinilai terhadap kriteria tertulisnya; (b) usulan baru dari aturan. Usulan `fitur` mulai
    bayangan langsung (dunia tanpa_sumber sudah berjalan, tanpa biaya model, tanpa efek hidup); usulan `prompt` menunggu izin biaya builder."""
    ubah = []
    for i, u in enumerate(st["usulan"]):
        if u["status"] == "bayangan" and u["bayangan"]["siklus"] >= u["kriteria_lulus"]["minimal_siklus"] and u["jenis"] == "fitur":
            h = nilai_usulan(u, eq_kini, P)
            st["usulan"][i] = ubah_status(u, "lulus" if h["lulus"] else "gagal", t0, P, hasil=h)
            ubah.append(st["usulan"][i])
    m_agent = {s: ringkas(_baris(rows, s), P) for s, rows in st["riwayat"].items()}
    setia_ok = len(st["setia"]) >= P["bobot"]["jendela_siklus"] and all(x[1] for x in st["setia"])
    for u in evaluator_aturan(m_agent, _delta_sumber(st, t0), setia_ok, st["usulan"], t0, P):
        if u["jenis"] == "fitur":
            u = ubah_status(u, "bayangan", t0, P, eq_mulai={"fabius": eq_kini.get("fabius"), f"tanpa_sumber:{u['isi']['buang_sumber']}":
                                                             eq_kini.get(f"tanpa_sumber:{u['isi']['buang_sumber']}")})
        st["usulan"].append(u)
        ubah.append(u)
    st["usulan"] = st["usulan"][-50:]
    return ubah


def bayangan_utas(st: Optional[dict], pra: dict, rek: List[dict], harga: Dict[str, float], snap: Optional[dict], p, t0: int, hasil: dict,
                  log: Callable[[str], None] = print) -> None:
    """Badan utas gerbang (SK-M39): galat apa pun dicatat dan siklus F4 itu hilang; siklus hidup sudah selesai sebelum utas ini mulai."""
    try:
        st2, rec = siklus_bayangan(st, pra, rek, harga, snap, p, t0)
        hasil["f4"] = {"state": st2, "rekaman": rec}
        log(f"f4 bayangan {time.strftime('%H:%M', time.gmtime(t0))}Z: {'SETIA' if rec['setia'] else 'TIDAK SETIA ' + ','.join(rec['beda'])}, "
            f"nilai {len(rec['nilai'])}, W {rec['bobot']['W'] or '-'}, dunia {len(rec['dunia'])}" + (f", galat {rec['galat']}" if rec["galat"] else ""))
    except Exception as e:  # noqa: BLE001 - bayangan gagal tidak boleh mengganggu meja hidup
        log(f"f4 bayangan gagal: {type(e).__name__}: {str(e)[:200]}")


def gabung(books: dict, h2: dict, simpan: Callable[[dict], None], log: Callable[[str], None] = print) -> bool:
    """Di awal siklus berikutnya: state F4 siklus lalu masuk `books["_f4"]` + rekaman evaluasi disimpan, HANYA bila v2 siklus itu digabung ke
    buku hidup (`_digabung`) dan utas F4 selesai. Selain itu hasil F4 siklus itu dibuang (celah tercatat di siklus F4 berikutnya)."""
    if not h2 or not h2.get("_digabung") or "f4" not in h2:
        return False
    books["_f4"] = h2["f4"]["state"]
    try:
        simpan(h2["f4"]["rekaman"])
    except Exception as e:  # noqa: BLE001
        log(f"f4 rekaman gagal disimpan: {type(e).__name__}: {str(e)[:160]}")
    return True


# ---------------------------------------------------------------- laporan harian dari arsip (`GET /desk/archive/<tgl>`)

def muat_arsip(dari: str, sampai: str, gerbang: str = GERBANG, token: Optional[str] = None) -> List[dict]:
    out, d0, d1 = [], dt.date.fromisoformat(dari), dt.date.fromisoformat(sampai)
    while d0 <= d1:
        try:
            req = urllib.request.Request(f"{gerbang}/desk/archive/{d0}", headers={"User-Agent": "fabius-f4", **({"Authorization": f"Bearer {token}"} if token else {})})
            with urllib.request.urlopen(req, timeout=120) as r:
                out.append(json.loads(r.read().decode()))
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
        d0 += dt.timedelta(days=1)
    return out


def muat_berkas(path: str) -> List[dict]:
    with open(path, encoding="utf-8") as f:
        o = json.load(f)
    return o["days"] if isinstance(o, dict) and "days" in o else (o if isinstance(o, list) else [o])


def _tgl(t: int) -> str:
    return dt.datetime.fromtimestamp(int(t), dt.timezone.utc).strftime("%Y-%m-%d")


def nilai_dari_arsip(agen: List[dict], harga: Dict[int, Dict[str, float]], pasar_pada: Callable[[int], object], P: dict = PARAMS_F4) -> List[dict]:
    """Nilai dihitung ULANG dari arsip tanpa rekaman F4 (mis. hari sebelum F4 menyala): portofolio bot dari candle harian pada waktu t
    (`pasar_pada(t)`, mis. `meja_replay._pasar_arsip` atas Binance Vision), fungsi yang SAMA dengan bayangan hidup."""
    by_t: Dict[int, List[dict]] = {}
    for r in agen:
        by_t.setdefault(int(r["siklus"]), []).append(r)
    cache: Dict[tuple, dict] = {}
    rows = []
    for t in sorted(by_t):
        h0 = harga.get(t)
        if not h0:
            continue
        key = (t // 86_400, tuple(sorted(h0)))
        if key not in cache:
            p = pasar_pada(t)
            cache[key] = {b: portofolio_bot(b, sorted(h0), p) for b in BOTS}
        e = entri(t, h0, cache[key], by_t[t])
        for h in P["horizon_siklus"]:
            h1 = harga.get(t + h * SIKLUS_S)
            if h1:
                rows += nilai_entri(e, h1, h)[0]
    return rows


def laporan(days: List[dict], P: dict = PARAMS_F4, pasar_pada: Optional[Callable[[int], object]] = None) -> dict:
    """Metrik per agent + per sumber + buku ablasi per hari UTC dari arsip. Nilai: dari rekaman F4 bila ada, selain itu dihitung ulang
    (`pasar_pada`), selain itu kosong (dicetak apa adanya)."""
    agen = sorted((r for d in days for r in d.get("agent_records") or []), key=lambda r: (r["siklus"], r["agent"]))
    recs = sorted((r for d in days for r in d.get("records") or []), key=lambda r: r["siklus"])
    harga = {int(c["cycle"]): c.get("prices") or {} for d in days for c in d.get("cycles") or []}
    evals = sorted((e for d in days for e in d.get("evaluation") or []), key=lambda e: e["siklus"])
    sehat = [h for d in days for h in d.get("data_health") or [] if h.get("t")]
    rows = [r for e in evals for r in e.get("nilai") or []]
    asal = "rekaman F4 tercatat"
    if not rows and pasar_pada is not None and agen:
        rows, asal = nilai_dari_arsip(agen, harga, pasar_pada, P), "dihitung ulang dari arsip + candle harian"
    elif not rows:
        asal = "tidak ada (F4 belum tercatat; pakai --vision untuk menghitung ulang)"
    peta, hb = peta_sumber(P), P["bobot"]["horizon_siklus"]
    faktor = {(r["agent"].split(":", 1)[1], r["siklus"]): sumber_keputusan(r.get("keputusan") or {}, peta) for r in agen if r.get("status") == "ok"}
    tanggal = sorted({_tgl(r["siklus"]) for r in agen} | {_tgl(r["siklus"]) for r in recs} | {_tgl(e["siklus"]) for e in evals})
    out = {"asal_nilai": asal, "hari": {}}
    for tg in tanggal:
        ag = [r for r in agen if _tgl(r["siklus"]) == tg]
        rw = [r for r in rows if _tgl(r["siklus"]) == tg]
        ev = [e for e in evals if _tgl(e["siklus"]) == tg]
        rc = [r for r in recs if _tgl(r["siklus"]) == tg]
        slugs = sorted({r["agent"].split(":", 1)[1] for r in ag} | {r["agent"] for r in rw})
        W = (ev[-1].get("bobot") or {}) if ev else {}
        per_agent = {}
        for s in slugs:
            mine = [r for r in ag if r["agent"] == f"v2:{s}"]
            m = {str(h): ringkas([r for r in rw if r["agent"] == s and r["h"] == h], P) for h in P["horizon_siklus"]}
            per_agent[s] = {"siklus": len(mine), "sah": sum(1 for r in mine if r.get("status") == "ok"),
                            "kursi": next((r.get("kursi") for r in reversed(mine) if r.get("kursi")), None), "metrik": m,
                            "W": (W.get("W") or {}).get(s), "W_alasan": (W.get("alasan") or {}).get(s)}
        per_sumber = {}
        r1 = [r for r in rw if r["h"] == hb]
        n_kep = sum(1 for (s, t) in faktor if _tgl(t) == tg)
        for y in sorted(set(P["sumber"]) | {x for (s, t), ys in faktor.items() if _tgl(t) == tg for x in ys}):
            sit = [1 for (s, t), ys in faktor.items() if _tgl(t) == tg and y in ys]
            ya = [r["ic"] for r in r1 if r["ic"] is not None and y in faktor.get((r["agent"], r["siklus"]), [])]
            tidak = [r["ic"] for r in r1 if r["ic"] is not None and (r["agent"], r["siklus"]) in faktor and y not in faktor[(r["agent"], r["siklus"])]]
            cak = [((h.get("kesehatan") or {}).get(y) or {}).get("cakupan") for h in sehat if _tgl(h["t"]) == tg]
            cak = [x for x in cak if isinstance(x, (int, float))]
            per_sumber[y] = {"disitasi": len(sit), "dari": n_kep, "ic_disitasi": _rata(ya), "n_disitasi": len(ya), "ic_tidak": _rata(tidak), "n_tidak": len(tidak),
                             "cakupan": _rata(cak), "snapshot": len(cak)}
        dunia = {}
        if ev:
            for n in sorted({n for e in ev for n in e.get("dunia") or {}}):
                xs = [(e["siklus"], e["dunia"][n]) for e in ev if n in (e.get("dunia") or {})]
                fab = [(e["siklus"], e.get("ekuitas_fabius")) for e in ev if n in (e.get("dunia") or {}) and e.get("ekuitas_fabius")]
                e0, e1 = xs[0][1]["ekuitas"], xs[-1][1]["ekuitas"]
                pct = (e1 / e0 - 1) * 100 if e0 else None
                fpct = (fab[-1][1] / fab[0][1] - 1) * 100 if len(fab) > 1 and fab[0][1] else None
                dunia[n] = {"siklus": len(xs), "ekuitas_awal": e0, "ekuitas_akhir": e1, "pct": None if pct is None else round(pct, 4),
                            "selisih_pp_vs_fabius": None if pct is None or fpct is None else round(pct - fpct, 4),
                            "isi": sum(x["isi"] for _, x in xs), "fee": round(sum(x["fee"] for _, x in xs), 6)}
            for y, v in per_sumber.items():
                v["ablasi_pp"] = (dunia.get(f"tanpa_sumber:{y}") or {}).get("selisih_pp_vs_fabius")
        out["hari"][tg] = {"siklus_fabius": len(rc), "f4": len(ev), "setia": sum(1 for e in ev if e.get("setia")),
                           "sinkron_ulang": sum(1 for e in ev if e.get("sinkron_ulang")), "tanpa_data": sum(len(e.get("tanpa_data") or []) for e in ev),
                           "bobot_diperbarui": sum(1 for e in ev if (e.get("bobot") or {}).get("diperbarui")), "agent": per_agent, "sumber": per_sumber,
                           "dunia": dunia, "usulan": [u for e in ev for u in e.get("usulan") or []],
                           "status_kunci": ev[-1].get("status_kunci") if ev else None, "params_f4_sha": ev[-1].get("params_f4_sha") if ev else None}
    return out


def _f(x, fmt="{:+.3f}", kosong="-"):
    return kosong if x is None else fmt.format(x)


def cetak(lp: dict, tulis: Callable[[str], None] = print) -> None:
    tulis(f"F4 meja (P156) - nilai: {lp['asal_nilai']}")
    for tg, d in lp["hari"].items():
        tulis(f"\n=== {tg} | siklus Fabius {d['siklus_fabius']} | rekaman F4 {d['f4']} | SETIA {d['setia']}/{d['f4']} | sinkron ulang "
              f"{d['sinkron_ulang']} | tanpa data {d['tanpa_data']} | bobot diperbarui {d['bobot_diperbarui']}x | kunci {d['status_kunci'] or '-'} "
              f"{(d['params_f4_sha'] or '')[:18]}")
        tulis("AGENT        kursi   sah        IC 5m (n)        IC 1j (n)        hit 1j / acak     W bayangan")
        for s, a in d["agent"].items():
            m1, m12 = a["metrik"]["1"], a["metrik"]["12"]
            tulis(f"  {s:11s} {str(a['kursi'] or '-'):7s} {a['sah']:4d}/{a['siklus']:<4d}  {_f(m1['ic']):>7s} ({m1['n_ic']:4d})   {_f(m12['ic']):>7s} ({m12['n_ic']:4d})   "
                  f"{_f(m12['hit'], '{:.0%}'):>4s} / {_f(m12['acak'], '{:.0%}'):<4s}      {_f(a['W'], '{:.2f}')} {('(' + a['W_alasan'] + ')') if a['W_alasan'] else ''}")
        tulis("KALIBRASI 1j (keyakinan -> hit, n):")
        for s, a in d["agent"].items():
            tulis(f"  {s:11s} " + "  ".join(f"{e['dari']}-{e['sampai']}: {_f(e['hit'], '{:.0%}')} ({e['n']})" for e in a["metrik"]["12"]["kalibrasi"]))
        tulis("SUMBER          disitasi        IC 1j disitasi (n)    IC 1j tidak (n)     ablasi pp vs Fabius   cakupan F1 (snapshot)")
        for y, v in d["sumber"].items():
            tulis(f"  {y:14s} {v['disitasi']:4d}/{v['dari']:<5d}    {_f(v['ic_disitasi']):>7s} ({v['n_disitasi']:4d})      {_f(v['ic_tidak']):>7s} ({v['n_tidak']:4d})     "
                  f"{_f(v.get('ablasi_pp'), '{:+.4f}'):>8s}              {_f(v['cakupan'], '{:.3f}')} ({v['snapshot']})")
        if d["dunia"]:
            tulis("ABLASI (buku slot r4 bayangan; % = akhir vs awal hari ini; pp = selisih terhadap buku Fabius tercatat)")
            for n, x in d["dunia"].items():
                tulis(f"  {n:28s} ekuitas {x['ekuitas_akhir']:10.2f}  {_f(x['pct'], '{:+.4f}'):>8s} %  {_f(x['selisih_pp_vs_fabius'], '{:+.4f}'):>8s} pp  "
                      f"isi {x['isi']:4d}  fee {x['fee']:8.2f}")
        else:
            tulis("ABLASI: tidak ada rekaman F4 hari ini (buku ablasi hanya dari bayangan hidup)")
        for u in d["usulan"]:
            tulis(f"USULAN {u.get('id')} [{u.get('status')}] {u.get('jenis')} {u.get('sasaran')} {json.dumps(u.get('isi'), ensure_ascii=False)}: {u.get('alasan')}")


# ---------------------------------------------------------------- arsip SINTETIS (`contoh`): meja hidup asli + pasar / model palsu

class PasarContoh(meja2.Pasar2):
    """Pasar SINTETIS deterministik (tanpa jaringan): 12 perp, candle harian 100 hari sebelum awal, harga mark tiap siklus (jalan acak berbenih).
    X10USDT = listing 5 hari sebelum awal (B4); X9USDT = likuiditas DEX 20.000 USD di snapshot (veto keras DexScreener)."""
    ASET = ["BTCUSDT", "PAXGUSDT"] + [f"X{i}USDT" for i in range(1, 11)]

    def __init__(self, t_awal: int, n_siklus: int, seed: int = 7):
        self.t, self.t_awal = t_awal, t_awal
        super().__init__(get=None, now=lambda: self.t)
        rng = random.Random(seed)
        d0 = (t_awal // 86_400 - 100) * 86_400_000
        n_hari = 100 + n_siklus * SIKLUS_S // 86_400 + 3
        self.rows, self.mark = {}, {}
        for i, a in enumerate(self.ASET):
            drift, c, rows = (i - 5.5) * 0.003, 100.0 + 10 * i, []
            for d in range(n_hari):
                if a == "X10USDT" and d < 95:
                    continue
                o, c = c, c * (1 + drift + rng.gauss(0, 0.02))
                rows.append((d0 + d * 86_400_000, o, max(o, c) * 1.01, min(o, c) * 0.99, c, 5e6))
            self.rows[a] = rows
            p, path = rows[99 - (95 if a == "X10USDT" else 0)][4], []
            for _ in range(n_siklus + 14):
                p *= 1 + rng.gauss(0.00005 * (i - 5.5), 0.0012)
                path.append(p)
            self.mark[a] = path

    def universe(self):
        return list(self.ASET)

    def tick(self):
        return {a: {"r_24j": 0.0, "volume_24j": 1} for a in self.ASET}

    def onboard(self):
        return {"X10USDT": self.rows["X10USDT"][0][0]}

    def harian(self, a):
        from engine.series import Series
        rows = [r for r in self.rows[a] if r[0] + 86_400_000 <= self.t * 1000][-(meja2.PARAMS2["harian_limit"] - 1):]
        if not rows:
            raise ValueError(f"tidak ada candle harian {a}")
        return Series.from_rows(rows)

    def harga(self, t: int) -> Dict[str, float]:
        i = (t - self.t_awal) // SIKLUS_S
        return {a: round(self.mark[a][i], 6) for a in self.ASET}


def contoh_arsip(hari: int = 3, siklus: int = 36, seed: int = 7, t_awal: int = 1_791_540_000, P: dict = PARAMS_F4) -> List[dict]:
    """Arsip SINTETIS berbentuk `GET /desk/archive/<tgl>`: `hari` jendela x `siklus` siklus (10:00Z tiap hari) dijalankan oleh `meja2.siklus2`
    ASLI + `siklus_bayangan` ASLI dengan pasar + tiga agent palsu: `tajam` (skor = peringkat return 1 jam sungguhan, faktor candle_harian),
    `acak` (skor acak, faktor fomo), `balik` (kebalikan tajam, faktor binance + berita). Angka sintetis TIDAK berarti apa pun tentang meja hidup."""
    total = (hari - 1) * 288 + siklus
    pasar, rng = PasarContoh(t_awal, total, seed), random.Random(seed + 1)
    agents = [{"slug": s, "agent_id": i + 1, "model": "sintetis"} for i, s in enumerate(("tajam", "acak", "balik"))]
    books, ring, st, days = {}, {}, None, {}
    fit = {"X9USDT": {"dex_likuiditas_usd": 20_000, "rug_bahaya": False}}

    def r_bot(t: int) -> Dict[str, float]:
        h0, h1 = pasar.harga(t), pasar.harga(t + 12 * SIKLUS_S)
        pasar.t = t + 30
        return {b: return_portofolio(portofolio_bot(b, sorted(h0), pasar), h0, h1) or 0.0 for b in BOTS}

    for d in range(hari):
        for i in range(siklus):
            t0 = t_awal + d * 86_400 + i * SIKLUS_S
            R = r_bot(t0)
            tajam = {b: int(-100 + 40 * (r - 1)) for b, r in zip(BOTS, peringkat([R[b] for b in BOTS]))}   # seri return = seri skor
            skor = {"tajam": tajam, "acak": {b: rng.randint(-100, 100) for b in BOTS}, "balik": {b: -v for b, v in tajam.items()}}
            pasar.t = t0 + 30
            tren = sorted(pasar.ASET, key=lambda a: -(pasar.harian(a).c[-1] / pasar.harian(a).c[0]))
            fakt = {"tajam": ["tren_60h"], "acak": ["fomo_thesis"], "balik": ["r_1j", "berita_sebut_6j"]}
            ins = {"tajam": tren[:8], "balik": tren[:8], "acak": rng.sample(pasar.ASET, 8)}
            jawaban = {}                                                                     # dihitung DI SINI: model palsu dipanggil dari utas siklus2
            for s, sk in skor.items():
                jawaban[s] = json.dumps({"ringkasan": f"synthetic {s}", "bot": max(BOTS, key=lambda b: (sk[b], -BOTS.index(b))), "skor_bot": sk,
                                         "keyakinan": rng.randint(30, 95), "eksposur": 60,
                                         "instrumen": [{"aset": a, "keyakinan": 70, "faktor": fakt[s][:1]} for a in ins[s]],
                                         "veto_aset": [], "faktor": fakt[s], "alasan": "synthetic"})

            def jawab(ag, system, user, jawaban=jawaban):
                return jawaban[ag["slug"]]
            snap = {"sha": f"0x{t0:064x}", "t": t0, "fitur_aset": {a: {"r_1j": 0.0, "fomo_thesis": 1, "berita_sebut_6j": 0, **fit.get(a, {})}
                                                                for a in pasar.ASET}, "fitur_bot": {b: {"pnl_1j": 0.0} for b in BOTS}}
            pra = pra_siklus(books)
            h = pasar.harga(t0)
            get = lambda url, h=h: [{"symbol": a, "markPrice": str(v), "lastFundingRate": "0"} for a, v in h.items()]  # noqa: E731
            rek, harga = meja2.siklus2(t0, agents, books, ring, jawab, snap, pasar, get=get, log=lambda m: None)
            st, ev = siklus_bayangan(st, pra, rek, harga, snap, pasar, t0, P)
            dd = days.setdefault(_tgl(t0), {"date": _tgl(t0), "sintetis": True, "records": [], "agent_records": [], "cycles": [], "evaluation": []})
            dd["records"] += [r for r in rek if r["agent"] == "v2"]
            dd["agent_records"] += [r for r in rek if r["agent"].startswith("v2:")]
            dd["cycles"].append({"cycle": t0, "prices": harga, "root": meja.root_of([r["hash"] for r in rek]), "tx": None, "status": "sintetis", "leaves": len(rek)})
            dd["evaluation"].append(ev)
    return [days[k] for k in sorted(days)]


# ---------------------------------------------------------------- CLI

def _pasar_vision(days: List[dict]) -> Callable[[int], object]:
    import meja_replay as mr
    t_max = max(int(c["cycle"]) for d in days for c in d.get("cycles") or [])
    store = mr.CandleVision((t_max // 86_400 + 1) * 86_400_000)
    return lambda t: mr._pasar_arsip(store, t)


def ringkasan_evaluator(lp: dict) -> Tuple[Dict[str, dict], Dict[str, Optional[float]], bool]:
    """Masukan evaluator dari laporan arsip (hari terakhir): metrik 1 jam per agent, ablasi pp per sumber, SETIA penuh."""
    if not lp["hari"]:
        return {}, {}, False
    d = lp["hari"][max(lp["hari"])]
    return ({s: a["metrik"]["12"] for s, a in d["agent"].items()}, {y: v.get("ablasi_pp") for y, v in d["sumber"].items()},
            d["f4"] > 0 and d["setia"] == d["f4"])


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nama in ("rapor", "usulan"):
        x = sub.add_parser(nama)
        x.add_argument("--dari")
        x.add_argument("--sampai")
        x.add_argument("--gerbang", default=GERBANG)
        x.add_argument("--token", default=os.environ.get("FABIUS_PRIVY_TOKEN"), help="token Privy anggota (P165); tanpa ini arsip publik >= 24 jam")
        x.add_argument("--berkas", help="arsip luring (JSON: daftar hari atau {'days': [...]})")
        x.add_argument("--vision", action="store_true", help="hitung ulang nilai dari candle harian Binance Vision bila rekaman F4 belum ada")
        x.add_argument("--json", action="store_true")
    sub.choices["usulan"].add_argument("--model", help="slug agent di config/agents.json sebagai evaluator LLM (memanggil model sungguhan)")
    sub.choices["usulan"].add_argument("--keluar", help="tulis usulan ke berkas JSONL ini (tidak ada yang hidup disentuh)")
    c = sub.add_parser("contoh")
    c.add_argument("--keluar", required=True)
    c.add_argument("--hari", type=int, default=3)
    c.add_argument("--siklus", type=int, default=36)
    k = sub.add_parser("kunci")
    k.add_argument("--usulan", action="store_true", help="tulis berkas usulan (pra-registrasi) dari PARAMS_F4")
    k.add_argument("--tulis", action="store_true", help="kunci (KATA BUILDER): sha harus sama dengan berkas usulan")
    k.add_argument("--catatan", default="")
    a = ap.parse_args(argv)
    if a.cmd == "kunci":
        if a.usulan:
            d = tulis_usulan(a.catatan)
            print(f"USULAN {d['sha']} -> {os.path.relpath(USULAN_FILE, os.path.dirname(HERE))} ({d['diusulkan']})")
        if a.tulis:
            d = tulis_kunci(a.catatan)
            print(f"DIKUNCI {d['sha']} -> {os.path.relpath(LOCK_FILE, os.path.dirname(HERE))} ({d['dikunci']})")
        s = status()
        print(f"status {s['state']} | sha kode {s['sha_kini']} | sha berkas {s['sha_berkas']}")
        print(f"rumus bobot: {PARAMS_F4['bobot']['rumus']}")
        return 0 if s["state"] in ("USULAN", "TERKUNCI") else 2
    if a.cmd == "contoh":
        days = contoh_arsip(a.hari, a.siklus)
        with open(a.keluar, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"sintetis": True, "catatan": "arsip SINTETIS dari tools/meja_eval.py contoh (meja hidup asli + pasar/model palsu)", "days": days}, f,
                      ensure_ascii=False, sort_keys=True)
        print(f"arsip sintetis {len(days)} hari, {sum(len(d['cycles']) for d in days)} siklus, rekaman F4 {sum(len(d['evaluation']) for d in days)} "
              f"(SETIA {sum(1 for d in days for e in d['evaluation'] if e['setia'])}) -> {a.keluar}")
        return 0
    if a.berkas:
        days = muat_berkas(a.berkas)
    elif a.dari and a.sampai:
        days = muat_arsip(a.dari, a.sampai, a.gerbang, a.token)
    else:
        ap.error("--berkas atau --dari + --sampai")
    if not days:
        print("tidak ada arsip")
        return 1
    lp = laporan(days, PARAMS_F4, _pasar_vision(days) if a.vision else None)
    if a.cmd == "rapor":
        if a.json:
            print(json.dumps(lp, indent=1, ensure_ascii=False, sort_keys=True))
        else:
            cetak(lp)
        return 0
    m_agent, delta, setia_ok = ringkasan_evaluator(lp)
    t0 = max(int(c["cycle"]) for d in days for c in d.get("cycles") or []) + SIKLUS_S
    us = evaluator_aturan(m_agent, delta, setia_ok, [], t0)
    tolak: List[dict] = []
    if a.model:
        import analis as an
        ag = next(x for x in an.AGENTS if x["slug"] == a.model)
        raw = an.call_model(ag, SYSTEM_EVALUATOR, prompt_evaluator({"agent": m_agent, "ablasi_sumber_pp": delta, "setia": setia_ok}))
        llm, tolak = parse_usulan_llm(raw, t0)
        us += llm
    for u in us:
        print(f"USULAN {u['id']} [{u['status']}] oleh {u['oleh']}: {u['jenis']} {u['sasaran']} {json.dumps(u['isi'], ensure_ascii=False)} | {u['alasan']}\n"
              f"  kriteria lulus (ditulis sebelum bayangan): {u['kriteria_lulus']['lulus_bila']} | sha {u['sha']}")
    for x in tolak:
        print(f"DITOLAK: {x['galat']} | {x.get('usulan', '')}")
    if not us:
        print("tidak ada usulan (bukti di bawah ambang aturan evaluator)")
    if a.keluar:
        with open(a.keluar, "a", encoding="utf-8", newline="\n") as f:
            for u in us:
                f.write(json.dumps(u, ensure_ascii=False, sort_keys=True) + "\n")
    print("Tidak ada yang hidup disentuh: usulan berlaku hanya lewat bayangan >= 288 siklus + kriteria lulus + kunci hash + kata builder (SK-M13).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
