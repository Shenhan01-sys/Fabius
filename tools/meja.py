"""Meja AI 5 menit Fabius (P152, F-D109): tiap 5 menit SETIAP agent analis WAJIB memutuskan target posisi (format baku), keputusan digabung
dengan rumus konsensus terkunci, diisi di buku paper (fee nyata), di-hash, dan Merkle root semuanya dikomit ke DeskAnchor SEBELUM siklus berakhir.

Terpisah dari enam bot harian yang terkunci (spesifikasi + uji maju F-D16 tidak disentuh). Paper saja, testnet; harga = Binance USDⓈ-M futures.

Format keputusan agent (JSON, satu objek):
  {"ringkasan": "<bacaan pasar, wajib>",
   "target": {"BTCUSDT": {"arah": "long|short|flat", "ukuran": 0.0-0.25, "keyakinan": 0-100, "alasan": "<singkat>"}, ...}}
  Aset yang tidak disebut = target agent itu sebelumnya (tahan). Target kosong = tahan semua (ringkasan menjelaskan kenapa).

Rumus konsensus v1 (PARAMS, dikunci sebelum siklus pertama; sha dicetak di log gerbang + vault):
  agent yang menjawab sah di siklus ini = R; |R| < kuorum -> konsensus menahan target sebelumnya.
  T_a = sum_{i in R} W_i * (keyakinan_{i,a} / 100) * w_{i,a} / sum_{i in R} W_i, W_i = 1 (bobot sama), w = +/- ukuran (flat = 0);
  |T_a| <= maks_per_aset, sum |T_a| <= maks_gross (diskala proporsional); perubahan < ubah_min ekuitas tidak ditransaksikan.
Buku: satu per agent + satu "konsensus". Isi pada harga mark yang diambil SESUDAH semua keputusan masuk (tanpa keuntungan latensi), fee per sisi
pada notional yang berubah; PnL ditandai tiap siklus.
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import math
import re
import time
import urllib.request
from typing import Callable, Dict, List, Optional, Tuple

PARAMS = {"v": 1, "siklus_s": 300, "modal_awal": 10_000.0, "fee": 0.0005, "maks_per_aset": 0.25, "maks_gross": 1.0, "batas_jawab_s": 210,
          "kuorum": 2, "ubah_min": 0.02, "bobot_agent": "sama", "keyakinan_pengali": True, "effort": "high",
          "aset": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "LINKUSDT", "LTCUSDT", "AVAXUSDT", "TRXUSDT",
                   "DOTUSDT", "BCHUSDT", "ETCUSDT", "ATOMUSDT", "NEARUSDT"]}
FAPI = "https://fapi.binance.com"
UA = "fabius-meja/1.0 (+https://fabius-one.vercel.app)"
KONSENSUS = "konsensus"

SYSTEM = ("You are an AI analyst on Fabius' 5-minute paper trading desk (Binance USDT-M futures, paper only, BNB testnet proofs). Every 5 minutes you MUST "
          "state your target positions. Every change pays 0.05% per side on the traded notional, so churning loses money: change a target only when you "
          "expect the move over the next minutes to beat the fee. Holding is allowed but explain it. Your decision is hashed and anchored on-chain before "
          "these 5 minutes end, and it is scored against the price at the end of the cycle. Write all text in English. Answer with ONE JSON object and "
          "nothing else.")


def canon(o) -> bytes:
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha(o) -> str:
    return "0x" + hashlib.sha256(o if isinstance(o, bytes) else canon(o)).hexdigest()


def params_sha() -> str:
    return sha(PARAMS)


# ---------------------------------------------------------------- data pasar (Binance USDⓈ-M, publik)

def _get_json(url: str, timeout: int = 15):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout) as r:
        return json.loads(r.read().decode())


def _ret(c: List[float], n: int) -> Optional[float]:
    return round(c[-1] / c[-1 - n] - 1, 6) if len(c) > n and c[-1 - n] > 0 else None


def pasar(now_s: int, get: Callable = _get_json, aset: Optional[List[str]] = None) -> dict:
    """Candle 5 menit yang SUDAH tutup (4 jam terakhir) + funding -> fitur per aset. Aset yang gagal dibaca dicatat, tidak dikarang."""
    aset = aset or PARAMS["aset"]
    prem = {r["symbol"]: r for r in get(f"{FAPI}/fapi/v1/premiumIndex")}
    out, galat = {}, {}
    for a in aset:
        try:
            k = [x for x in get(f"{FAPI}/fapi/v1/klines?symbol={a}&interval=5m&limit=50") if int(x[6]) < now_s * 1000]
            c = [float(x[4]) for x in k]
            r5 = [c[i] / c[i - 1] - 1 for i in range(len(c) - 12, len(c))] if len(c) > 13 else []
            mu = sum(r5) / len(r5) if r5 else 0.0
            out[a] = {"harga": c[-1], "r_5m": _ret(c, 1), "r_1j": _ret(c, 12), "r_4j": _ret(c, 48),
                      "vol_1j": round(math.sqrt(sum((x - mu) ** 2 for x in r5) / (len(r5) - 1)), 6) if len(r5) > 1 else None,
                      "volume_1j_usd": round(sum(float(x[7]) for x in k[-12:])),
                      "funding": float(prem[a]["lastFundingRate"]) if a in prem else None}
        except Exception as e:  # noqa: BLE001
            galat[a] = f"{type(e).__name__}: {str(e)[:80]}"
    return {"t": now_s, "aset": out, "galat": galat}


def harga_isi(get: Callable = _get_json, aset: Optional[List[str]] = None) -> Dict[str, float]:
    """Harga mark saat pengisian (satu panggilan)."""
    aset = set(aset or PARAMS["aset"])
    return {r["symbol"]: float(r["markPrice"]) for r in get(f"{FAPI}/fapi/v1/premiumIndex") if r["symbol"] in aset}


# ---------------------------------------------------------------- keputusan agent

def prompt(ps: dict, buku: dict, harga: Dict[str, float], ringkasan_lalu: Optional[str], judul: Optional[List[dict]] = None) -> str:
    e = ekuitas(buku, harga)
    rows = []
    for a, f in sorted(ps["aset"].items()):
        tg = (buku.get("target") or {}).get(a) or {}
        rows.append(f"{a}: price {f['harga']} | r5m {f['r_5m']} r1h {f['r_1j']} r4h {f['r_4j']} | vol1h {f['vol_1j']} | vol_usd_1h {f['volume_1j_usd']} | "
                    f"funding {f['funding']} | your target {tg.get('w', 0.0):+.3f} (conf {round(tg.get('k', 0) * 100)})")
    berita = ""
    if judul:
        berita = "\n\nRecent headlines (newest first):\n" + "\n".join(f"- [{x['sumber']}] {x['judul']}" for x in judul[:12])
    return (f"Cycle start {dt.datetime.fromtimestamp(ps['t'], dt.timezone.utc).strftime('%Y-%m-%d %H:%M')}Z. Your paper book: equity {e:.2f} USDT "
            f"(start {PARAMS['modal_awal']:.0f}), fees paid {buku.get('biaya', 0):.2f}, trades {buku.get('n_trade', 0)}.\n"
            f"Last cycle you wrote: {ringkasan_lalu or '(first cycle)'}\n\nMarket (closed 5-minute candles; returns as fractions):\n" + "\n".join(rows) + berita
            + f"\n\nRules: target weight per asset = fraction of equity, max {PARAMS['maks_per_aset']} per asset, gross max {PARAMS['maks_gross']}; "
            "assets you omit keep your current target. Reply with exactly this JSON: "
            '{"ringkasan": "<what you read in the market, max 400 chars>", "target": {"<ASSET>": {"arah": "long|short|flat", "ukuran": <0.0-0.25>, '
            '"keyakinan": <integer 0-100>, "alasan": "<max 160 chars>"}}}')


def parse(text: str, sebelum: Dict[str, dict]) -> dict:
    """Jawaban -> {"ringkasan", "target" (vektor penuh, tidak disebut = sebelumnya), "diubah", "ditolak", "diskala"}. Galat = ValueError."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError("tidak ada JSON di jawaban")
    o = json.loads(m.group(0))
    ring = str(o.get("ringkasan") or "").strip()[:400]
    if not ring:
        raise ValueError("ringkasan kosong (keputusan wajib dijelaskan)")
    target = {a: dict(v) for a, v in (sebelum or {}).items()}
    diubah, ditolak = [], []
    for a, v in (o.get("target") or {}).items():
        a = str(a).upper().strip()
        try:
            if a not in PARAMS["aset"]:
                raise ValueError("aset di luar daftar")
            arah = str(v.get("arah", "")).lower()
            if arah not in ("long", "short", "flat"):
                raise ValueError(f"arah {arah!r}")
            u = 0.0 if arah == "flat" else float(v.get("ukuran"))
            if not 0.0 <= u <= PARAMS["maks_per_aset"] + 1e-9:
                raise ValueError(f"ukuran {u} di luar 0..{PARAMS['maks_per_aset']}")
            k = int(v.get("keyakinan", 0))
            if not 0 <= k <= 100:
                raise ValueError(f"keyakinan {k}")
        except (ValueError, TypeError, AttributeError) as e:
            ditolak.append({"aset": a, "galat": str(e)[:80]})
            continue
        target[a] = {"w": round(u if arah == "long" else -u if arah == "short" else 0.0, 6), "k": k / 100, "alasan": str(v.get("alasan", ""))[:160]}
        diubah.append(a)
    gross = sum(abs(t["w"]) for t in target.values())
    skala = PARAMS["maks_gross"] / gross if gross > PARAMS["maks_gross"] else 1.0
    if skala < 1.0:
        for t in target.values():
            t["w"] = round(t["w"] * skala, 6)
    return {"ringkasan": ring, "target": target, "diubah": sorted(diubah), "ditolak": ditolak, "diskala": round(skala, 6) if skala < 1 else None}


def konsensus(keputusan: Dict[str, dict], sebelum: Dict[str, dict]) -> Tuple[Dict[str, dict], str]:
    """Rumus v1 (lihat docstring modul). `keputusan` = {agent: hasil parse} yang SAH di siklus ini."""
    if len(keputusan) < PARAMS["kuorum"]:
        return {a: dict(v) for a, v in (sebelum or {}).items()}, f"kuorum tidak tercapai ({len(keputusan)} < {PARAMS['kuorum']}): tahan"
    n = len(keputusan)
    t = {}
    for a in PARAMS["aset"]:
        s = sum(((d["target"].get(a) or {}).get("k", 0.0) if PARAMS["keyakinan_pengali"] else 1.0) * (d["target"].get(a) or {}).get("w", 0.0)
                for d in keputusan.values()) / n
        s = max(-PARAMS["maks_per_aset"], min(PARAMS["maks_per_aset"], s))
        if abs(s) > 1e-9:
            t[a] = {"w": round(s, 6), "k": 1.0}
    gross = sum(abs(v["w"]) for v in t.values())
    if gross > PARAMS["maks_gross"]:
        for v in t.values():
            v["w"] = round(v["w"] * PARAMS["maks_gross"] / gross, 6)
    return t, f"rata-rata keyakinan x target {n} agent ({', '.join(sorted(keputusan))})"


# ---------------------------------------------------------------- buku paper

def buku_baru() -> dict:
    return {"saldo": PARAMS["modal_awal"], "posisi": {}, "biaya": 0.0, "n_trade": 0, "target": {}}


def ekuitas(b: dict, harga: Dict[str, float]) -> float:
    return b["saldo"] + sum(p["qty"] * (harga.get(a, p["masuk"]) - p["masuk"]) for a, p in b["posisi"].items())


def isi(b: dict, target: Dict[str, dict], harga: Dict[str, float]) -> List[dict]:
    """Ubah posisi ke target (bobot x ekuitas) pada `harga`; perubahan < ubah_min x ekuitas dilewati. PnL berjalan direalisasi saat posisi berubah."""
    e = ekuitas(b, harga)
    fills = []
    for a in sorted(set(target) | set(b["posisi"])):
        p = harga.get(a)
        if not p:
            continue
        cur = b["posisi"].get(a, {"qty": 0.0, "masuk": p})
        want = (target.get(a) or {}).get("w", 0.0) * e / p
        if abs(want - cur["qty"]) * p < PARAMS["ubah_min"] * e:
            continue
        b["saldo"] += cur["qty"] * (p - cur["masuk"])
        fee = PARAMS["fee"] * abs(want - cur["qty"]) * p
        b["saldo"] -= fee
        b["biaya"] = round(b["biaya"] + fee, 6)
        b["n_trade"] += 1
        fills.append({"aset": a, "dari": round(cur["qty"] * p / e, 6), "ke": round(want * p / e, 6), "harga": p, "fee": round(fee, 6)})
        if abs(want) < 1e-12:
            b["posisi"].pop(a, None)
        else:
            b["posisi"][a] = {"qty": want, "masuk": p}
    b["target"] = {a: dict(v) for a, v in target.items()}
    return fills


# ---------------------------------------------------------------- satu siklus

def siklus(t0: int, agents: List[dict], books: Dict[str, dict], ringkasan_lalu: Dict[str, str], call: Callable[[dict, str, str], str],
           get: Callable = _get_json, judul: Optional[List[dict]] = None, now: Callable[[], float] = time.time,
           log: Callable[[str], None] = print) -> Tuple[List[dict], dict]:
    """-> (rekaman per agent + konsensus, ringkasan siklus {siklus, daun, root}). Rekaman = yang di-hash; urutan: putuskan -> harga isi -> isi -> hash."""
    ps = pasar(t0, get)
    harga0 = {a: f["harga"] for a, f in ps["aset"].items()}
    for ag in agents:
        books.setdefault(ag["slug"], buku_baru())
    books.setdefault(KONSENSUS, buku_baru())
    prompts = {ag["slug"]: prompt(ps, books[ag["slug"]], harga0, ringkasan_lalu.get(ag["slug"]), judul if ag.get("berita") else None) for ag in agents}
    hasil: Dict[str, dict] = {}
    pool = cf.ThreadPoolExecutor(max_workers=max(1, len(agents)))
    fut = {pool.submit(call, ag, SYSTEM, prompts[ag["slug"]]): ag for ag in agents}
    try:
        for f in cf.as_completed(fut, timeout=PARAMS["batas_jawab_s"]):
            ag = fut[f]
            try:
                raw = f.result()
                hasil[ag["slug"]] = {"raw": raw, "kep": parse(raw, books[ag["slug"]].get("target") or {})}
            except Exception as e:  # noqa: BLE001
                hasil[ag["slug"]] = {"galat": f"{type(e).__name__}: {str(e)[:160]}"}
    except cf.TimeoutError:
        pass
    finally:
        pool.shutdown(wait=False, cancel_futures=True)                 # model yang menggantung tidak boleh menunda komit melewati akhir siklus
    harga = harga_isi(get)
    rek = []
    for ag in agents:
        s, h = ag["slug"], hasil.get(ag["slug"])
        r = {"v": 1, "siklus": t0, "agent": s, "agent_id": int(ag["agent_id"]), "model": ag["model"], "data_sha": sha(ps), "harga_isi_sha": sha(harga),
             "prompt_sha": sha(SYSTEM.encode() + b"\n" + prompts[s].encode())}
        if h is None:
            r.update(status="terlambat", galat=f"tidak menjawab dalam {PARAMS['batas_jawab_s']} s")
        elif "galat" in h:
            r.update(status="gagal", galat=h["galat"])
        else:
            r.update(status="ok", jawaban_sha=sha(h["raw"].encode()), keputusan=h["kep"], isi=isi(books[s], h["kep"]["target"], harga))
            ringkasan_lalu[s] = h["kep"]["ringkasan"]
        r["ekuitas"] = round(ekuitas(books[s], harga), 4)
        rek.append(r)
    sah = {s: h["kep"] for s, h in hasil.items() if h and "kep" in h}
    tk, why = konsensus(sah, books[KONSENSUS].get("target") or {})
    rk = {"v": 1, "siklus": t0, "agent": KONSENSUS, "rumus": f"v{PARAMS['v']} params {params_sha()[:18]}", "dasar": why, "masuk": sorted(sah),
          "target": tk, "harga_isi_sha": sha(harga), "isi": isi(books[KONSENSUS], tk, harga)}
    rk["ekuitas"] = round(ekuitas(books[KONSENSUS], harga), 4)
    rek.append(rk)
    for r in rek:
        r["hash"] = sha(r)
    daun = [r["hash"] for r in rek]
    log(f"meja {dt.datetime.fromtimestamp(t0, dt.timezone.utc).strftime('%H:%M')}Z: "
        + " | ".join(f"{r['agent']} {r.get('status', 'ok')} eq {r['ekuitas']:.2f} isi {len(r.get('isi') or [])}" for r in rek))
    return rek, {"siklus": t0, "daun": daun, "harga": harga, "selesai": int(now())}


def root_of(daun: List[str]) -> str:
    from engine import chain
    return "0x" + chain.merkle_root([bytes.fromhex(h[2:]) for h in daun]).hex()


def proof_of(daun: List[str], h: str) -> List[str]:
    from engine import chain
    return ["0x" + p.hex() for p in chain.merkle_proof([bytes.fromhex(x[2:]) for x in daun], bytes.fromhex(h[2:]))]
