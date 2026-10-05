"""Meja AI v2 F1 (P153, F-D110): data luas dibaca FABIUS SENDIRI lewat kode -> fitur terukur yang sama untuk semua agent. Tidak ada AI di sini.

Sumber (akses diukur 5 Okt): Binance USDⓈ-M (klines 5m, premiumIndex, openInterestHist, takerlongshortRatio), DexScreener `tokens/v1` (batch per
alamat), RugCheck `report/summary` (Solana), FOMO API (leaderboard + thesis; kunci `FOMO_API_KEY`), berita (`tools/kabar.py`). Bubblemaps dilewati
(publik hanya ketersediaan peta), GMGN tidak (403).

Aturan:
- Data on-chain HANYA lewat REGISTRY alamat yang dikunci (sha dicetak); pencarian simbol tidak dipakai ("WIF" di DexScreener = token tiruan) - SK-M5.
- Tiap sumber punya cache + jeda minimum (ANGGARAN) supaya kuota tidak terlampaui; sumber gagal / tanpa kunci ditandai di `kesehatan`, fiturnya
  kosong (None), tidak pernah dikarang - SK-M4.
- Fitur = fungsi murni; snapshot per sumber di-hash (`sha`), seluruh snapshot di-hash; z-score 24 jam dihitung dari riwayat snapshot (>= 30 titik).
"""
from __future__ import annotations

import collections
import json
import math
import re
import time
import urllib.parse
import urllib.request
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import meja

REGISTRY_V = 1
# perp Binance -> token on-chain. Alamat dari CoinGecko `platforms` (diambil 5 Okt); chain = rantai likuiditas utama; kali = pengali kontrak Binance.
REGISTRY = {
    "1000PEPEUSDT": {"simbol": "PEPE", "chain": "ethereum", "alamat": "0x6982508145454ce325ddbe47a25d4ec3d2311933", "kali": 1000},
    "WIFUSDT": {"simbol": "WIF", "chain": "solana", "alamat": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm", "kali": 1},
    "1000BONKUSDT": {"simbol": "BONK", "chain": "solana", "alamat": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263", "kali": 1000},
    "POPCATUSDT": {"simbol": "POPCAT", "chain": "solana", "alamat": "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr", "kali": 1},
    "PNUTUSDT": {"simbol": "PNUT", "chain": "solana", "alamat": "2qEHjDLDLbuBgRYvsxhc5D6uDWAivNFZGan56P1tpump", "kali": 1},
    "TRUMPUSDT": {"simbol": "TRUMP", "chain": "solana", "alamat": "6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN", "kali": 1},
    "FARTCOINUSDT": {"simbol": "FARTCOIN", "chain": "solana", "alamat": "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump", "kali": 1},
    "MOODENGUSDT": {"simbol": "MOODENG", "chain": "solana", "alamat": "ED5nyyWEzpPPiWimP8vYm7sD7TD3LAt3Q3gRTWHzPJBY", "kali": 1},
    "1000FLOKIUSDT": {"simbol": "FLOKI", "chain": "ethereum", "alamat": "0xcf0c122c6b73ff809c693db761e7baebe62b6a2e", "kali": 1000},
    "1000SHIBUSDT": {"simbol": "SHIB", "chain": "ethereum", "alamat": "0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce", "kali": 1000},
    "PENGUUSDT": {"simbol": "PENGU", "chain": "solana", "alamat": "2zMMhcVQEXDtdE6vsFS7S7D5oUodfJHE8vd1gnBouauv", "kali": 1},
    "BRETTUSDT": {"simbol": "BRETT", "chain": "base", "alamat": "0x532f27101965dd16442e59d40670faf5ebb142e4", "kali": 1},
}
# nama yang dicari di judul berita per aset mayor (kata utuh, tak peka huruf)
NAMA = {"BTCUSDT": ["BTC", "Bitcoin"], "ETHUSDT": ["ETH", "Ether", "Ethereum"], "BNBUSDT": ["BNB"], "SOLUSDT": ["SOL", "Solana"], "XRPUSDT": ["XRP", "Ripple"],
        "DOGEUSDT": ["DOGE", "Dogecoin"], "ADAUSDT": ["ADA", "Cardano"], "LINKUSDT": ["LINK", "Chainlink"], "LTCUSDT": ["LTC", "Litecoin"],
        "AVAXUSDT": ["AVAX", "Avalanche"], "TRXUSDT": ["TRX", "Tron"], "DOTUSDT": ["DOT", "Polkadot"], "BCHUSDT": ["BCH", "Bitcoin Cash"],
        "ETCUSDT": ["ETC"], "ATOMUSDT": ["ATOM", "Cosmos"], "NEARUSDT": ["NEAR"], "PAXGUSDT": ["PAXG", "gold"]}
ANGGARAN = {"binance_ekstra": 290, "dexscreener": 290, "rugcheck": 3600, "fomo_leaderboard": 7200, "fomo_thesis": 28800, "berita": 900}
FAPI = "https://fapi.binance.com"
UA = "fabius-meja-data/1.0 (+https://fabius-one.vercel.app)"
B3_THETA = 0.1
SEJARAH = 288                                                     # 24 jam siklus 5 menit untuk z-score
Z_MIN = 30


def registry_sha() -> str:
    return meja.sha({"v": REGISTRY_V, "registry": REGISTRY})


def _get(url: str, headers: Optional[dict] = None, timeout: int = 15):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})}), timeout=timeout) as r:
        return json.loads(r.read().decode())


# ---------------------------------------------------------------- fitur (fungsi murni)

def f_binance(ps_aset: Optional[dict], oi: Optional[list], taker: Optional[list]) -> dict:
    f = {k: (ps_aset or {}).get(k) for k in ("r_5m", "r_1j", "r_4j", "vol_1j", "funding")}
    if oi and len(oi) >= 13 and float(oi[0]["sumOpenInterest"]) > 0:
        f["oi_ubah_1j"] = round(float(oi[-1]["sumOpenInterest"]) / float(oi[0]["sumOpenInterest"]) - 1, 6)
    else:
        f["oi_ubah_1j"] = None
    f["taker_beli_jual"] = round(float(taker[-1]["buySellRatio"]), 4) if taker else None
    return f


def pasangan_terbaik(pairs: Iterable[dict], alamat: str) -> Optional[dict]:
    """Pasangan DEX dengan likuiditas terbesar yang base token-nya = alamat REGISTRY (bukan simbol)."""
    cocok = [p for p in pairs if str((p.get("baseToken") or {}).get("address", "")).lower() == alamat.lower()]
    return max(cocok, key=lambda p: (p.get("liquidity") or {}).get("usd") or 0, default=None)


def f_dex(p: Optional[dict], mark: Optional[float], kali: int) -> dict:
    if not p:
        return {"dex_vol_1j_rel": None, "dex_beli_porsi_1j": None, "dex_likuiditas_usd": None, "dex_basis": None}
    vol, tx = p.get("volume") or {}, (p.get("txns") or {}).get("h1") or {}
    h24 = vol.get("h24") or 0
    n = (tx.get("buys") or 0) + (tx.get("sells") or 0)
    harga = float(p["priceUsd"]) * kali if p.get("priceUsd") else None
    return {"dex_vol_1j_rel": round((vol.get("h1") or 0) * 24 / h24, 4) if h24 else None,
            "dex_beli_porsi_1j": round((tx.get("buys") or 0) / n, 4) if n else None,
            "dex_likuiditas_usd": round((p.get("liquidity") or {}).get("usd") or 0),
            "dex_basis": round(harga / mark - 1, 6) if harga and mark else None}


def f_rug(r: Optional[dict]) -> dict:
    if not r:
        return {"rug_skor": None, "rug_lp_terkunci": None, "rug_bahaya": None}
    return {"rug_skor": r.get("score_normalised"), "rug_lp_terkunci": r.get("lpLockedPct"),
            "rug_bahaya": any(str(x.get("level", "")).lower() == "danger" for x in (r.get("risks") or []))}


def f_fomo(lb: Optional[dict], th: Optional[dict], simbol: str, alamat: str) -> dict:
    def kena(obj) -> bool:
        s = json.dumps(obj, ensure_ascii=False).lower()
        return alamat.lower() in s or re.search(rf"(?<![a-z0-9]){re.escape(simbol.lower())}(?![a-z0-9])", s) is not None
    traders = (lb or {}).get("traders") or []
    theses = (th or {}).get("theses") or []
    return {"fomo_trader_top": sum(1 for t in traders if kena(t.get("topTokens") or [])) if lb else None,
            "fomo_thesis": sum(1 for t in theses if kena(t.get("token") or {}) or kena(t.get("text") or "")) if th else None}


def f_berita(judul: Optional[List[dict]], nama: List[str], now_s: int, jam: int = 6) -> dict:
    if judul is None:
        return {"berita_sebut_6j": None, "binance_listing": None, "binance_delisting": None}
    rx = re.compile(r"(?<![A-Za-z0-9])(" + "|".join(re.escape(n) for n in nama) + r")(?![A-Za-z0-9])", re.I)
    baru = [x for x in judul if rx.search(x["judul"])]
    return {"berita_sebut_6j": sum(1 for x in baru if now_s - x["waktu"] <= jam * 3600),
            "binance_listing": any(x["sumber"] == "binance-listing" for x in baru),
            "binance_delisting": any(x["sumber"] == "binance-delisting" for x in baru)}


def f_bot(bot: str, targets: Dict[str, float], fa: Dict[str, dict], memecoin: List[str]) -> dict:
    """Fitur kecocokan bot dengan kondisi pasar (Epik 11 §3) + PnL 1 jam portofolio target bot pada harga 5 menit."""
    def r(a, k):
        return (fa.get(a) or {}).get(k)
    pos = {a: w for a, w in targets.items() if abs(w) > 1e-12}
    pnl = [w * r(a, "r_1j") for a, w in pos.items() if r(a, "r_1j") is not None]
    out = {"n_posisi": len(pos), "pnl_1j": round(sum(pnl), 6) if pnl else None}
    maj = [a for a in meja.PARAMS["aset"] if r(a, "r_1j") is not None]
    if bot == "B1-TREND":
        out["breadth_naik_1j"] = round(sum(r(a, "r_1j") > 0 for a in maj) / len(maj), 4) if maj else None
    elif bot == "B2-RS":
        x = [r(a, "r_4j") for a in maj if r(a, "r_4j") is not None]
        mu = sum(x) / len(x) if x else 0
        out["sebaran_r4j"] = round(math.sqrt(sum((v - mu) ** 2 for v in x) / (len(x) - 1)), 6) if len(x) > 1 else None
    elif bot == "B3-CARRY":
        fu = [r(a, "funding") for a in maj if r(a, "funding") is not None]
        out["funding_tahunan"] = round(sum(fu) / len(fu) * 3 * 365, 6) if fu else None
        out["funding_vs_theta"] = round(out["funding_tahunan"] - B3_THETA, 6) if fu else None
    elif bot == "B4-LISTING-FADE":
        mc = [a for a in memecoin if r(a, "r_1j") is not None]
        out["memecoin_naik_1j"] = round(sum(r(a, "r_1j") > 0 for a in mc) / len(mc), 4) if mc else None
        out["target_rug_bahaya"] = sum(1 for a in pos if r(a, "rug_bahaya"))
    elif bot == "B5-CORE-RWA":
        vb, vg = r("BTCUSDT", "vol_1j"), r("PAXGUSDT", "vol_1j")
        out["vol_btc_per_emas"] = round(vb / vg, 4) if vb and vg else None
    elif bot == "B6-BOUNCE":
        z = [r(a, "r_4j") / (r(a, "vol_1j") * 2) for a in maj if r(a, "r_4j") is not None and r(a, "vol_1j")]
        out["porsi_oversold"] = round(sum(v < -2 for v in z) / len(z), 4) if z else None
    return out


def zskor(nilai: Optional[float], riwayat: List[float]) -> Optional[float]:
    if nilai is None or len(riwayat) < Z_MIN:
        return None
    mu = sum(riwayat) / len(riwayat)
    sd = math.sqrt(sum((x - mu) ** 2 for x in riwayat) / (len(riwayat) - 1))
    return round((nilai - mu) / sd, 4) if sd > 0 else 0.0


# ---------------------------------------------------------------- pengumpul (cache + anggaran)

class Pengumpul:
    def __init__(self, get: Callable = _get, fomo_key: Optional[str] = None, kabar_fn: Optional[Callable[[int], dict]] = None,
                 now: Callable[[], float] = time.time):
        self.get, self.fomo_key, self.kabar_fn, self.now = get, fomo_key, kabar_fn, now
        self.cache: Dict[str, Tuple[float, object]] = {}
        self.status: Dict[str, str] = {}
        self.riwayat: Dict[str, collections.deque] = collections.defaultdict(lambda: collections.deque(maxlen=SEJARAH))

    def _ambil(self, name: str, fn: Callable[[], object]):
        t, data = self.cache.get(name, (0.0, None))
        if data is not None and self.now() - t < ANGGARAN[name.split(":")[0]]:
            self.status[name.split(":")[0]] = self.status.get(name.split(":")[0], "ok")
            return data
        try:
            data = fn()
            self.cache[name] = (self.now(), data)
            self.status[name.split(":")[0]] = "ok"
            return data
        except Exception as e:  # noqa: BLE001 - sumber gagal: dicatat, fitur kosong (SK-M4)
            self.status[name.split(":")[0]] = f"galat {type(e).__name__}: {str(e)[:80]}"
            return None

    def binance_ekstra(self, aset: List[str]) -> Dict[str, tuple]:
        out = {}
        for a in aset:
            out[a] = (self._ambil(f"binance_ekstra:oi:{a}", lambda a=a: self.get(f"{FAPI}/futures/data/openInterestHist?symbol={a}&period=5m&limit=13")),
                      self._ambil(f"binance_ekstra:tk:{a}", lambda a=a: self.get(f"{FAPI}/futures/data/takerlongshortRatio?symbol={a}&period=5m&limit=1")))
        return out

    def dex(self) -> Dict[str, Optional[dict]]:
        out = {}
        per_chain: Dict[str, List[str]] = collections.defaultdict(list)
        for perp, r in REGISTRY.items():
            per_chain[r["chain"]].append(perp)
        for chain, perps in per_chain.items():
            alamat = ",".join(REGISTRY[p]["alamat"] for p in perps)
            pairs = self._ambil(f"dexscreener:{chain}", lambda c=chain, al=alamat: self.get(f"https://api.dexscreener.com/tokens/v1/{c}/{al}")) or []
            for p in perps:
                out[p] = pasangan_terbaik(pairs, REGISTRY[p]["alamat"])
        return out

    def rugcheck(self) -> Dict[str, Optional[dict]]:
        return {p: self._ambil(f"rugcheck:{p}", lambda r=r: self.get(f"https://api.rugcheck.xyz/v1/tokens/{r['alamat']}/report/summary"))
                for p, r in REGISTRY.items() if r["chain"] == "solana"}

    def fomo(self) -> Tuple[Optional[dict], Optional[dict]]:
        if not self.fomo_key:
            self.status["fomo_leaderboard"] = self.status["fomo_thesis"] = "tanpa kunci (FOMO_API_KEY belum di layanan ini)"
            return None, None
        h = {"authorization": f"Bearer {self.fomo_key}"}
        return (self._ambil("fomo_leaderboard", lambda: self.get("https://api.fomoapi.io/v2/leaderboard/24h", h)),
                self._ambil("fomo_thesis", lambda: self.get("https://api.fomoapi.io/v2/thesis?sort=recent&limit=50", h)))

    def berita(self) -> Optional[List[dict]]:
        if self.kabar_fn is None:
            import kabar
            self.kabar_fn = kabar.kabar
        return self._ambil("berita", lambda: self.kabar_fn(int(self.now()))["judul"])

    def kumpul(self, t0: int, ps: dict, targets_bot: Dict[str, Dict[str, float]]) -> dict:
        """Satu snapshot F1: fitur per aset + per bot, kesehatan per sumber, sha per sumber dan seluruhnya."""
        self.status = {}
        aset_target = sorted({a for tg in targets_bot.values() for a, w in tg.items() if abs(w) > 1e-12})
        aset = sorted(set(meja.PARAMS["aset"]) | set(aset_target) | set(REGISTRY) | {"PAXGUSDT"})
        ekstra = [a for a in aset if a not in ps.get("aset", {})]
        if ekstra:
            px = meja.pasar(t0, self.get, ekstra)
            ps = {**ps, "aset": {**ps.get("aset", {}), **px["aset"]}, "galat": {**ps.get("galat", {}), **px["galat"]}}
        mark = {a: f.get("harga") for a, f in ps["aset"].items()}
        bx = self.binance_ekstra(sorted(set(meja.PARAMS["aset"]) | set(aset_target)))
        dx, rg, (lb, th), jd = self.dex(), self.rugcheck(), self.fomo(), self.berita()
        fa: Dict[str, dict] = {}
        for a in aset:
            f = f_binance(ps["aset"].get(a), *(bx.get(a) or (None, None)))
            if a in REGISTRY:
                r = REGISTRY[a]
                f.update(f_dex(dx.get(a), mark.get(a), r["kali"]))
                f.update(f_rug(rg.get(a)) if r["chain"] == "solana" else {"rug_skor": None, "rug_lp_terkunci": None, "rug_bahaya": None})
                f.update(f_fomo(lb, th, r["simbol"], r["alamat"]))
                nama = [r["simbol"]]
            else:
                nama = NAMA.get(a, [a.replace("USDT", "")])
            f.update(f_berita(jd, nama, t0))
            for k in ("r_1j", "oi_ubah_1j", "taker_beli_jual", "dex_vol_1j_rel", "berita_sebut_6j"):
                v = f.get(k)
                f[f"z_{k}"] = zskor(v if isinstance(v, (int, float)) and not isinstance(v, bool) else None, list(self.riwayat[f"{a}:{k}"]))
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    self.riwayat[f"{a}:{k}"].append(float(v))
            fa[a] = f
        fb = {b: f_bot(b, tg, fa, list(REGISTRY)) for b, tg in sorted(targets_bot.items())}
        sumber = {"binance": ps.get("galat") or {}, "dex": sum(1 for v in dx.values() if v), "rugcheck": sum(1 for v in rg.values() if v),
                  "fomo": [lb is not None, th is not None], "berita": len(jd) if jd is not None else None}
        snap = {"v": 1, "t": t0, "registry_sha": registry_sha(), "kesehatan": self.kesehatan(fa, dx, rg, lb, th, jd), "sumber": sumber,
                "fitur_aset": fa, "fitur_bot": fb}
        snap["sha"] = meja.sha(snap)
        return snap

    def kesehatan(self, fa, dx, rg, lb, th, jd) -> Dict[str, dict]:
        maj = meja.PARAMS["aset"]
        cak = lambda xs: round(sum(1 for x in xs if x) / len(xs), 4) if xs else None    # noqa: E731
        return {
            "binance": {"status": "ok" if all(fa.get(a, {}).get("r_1j") is not None for a in maj) else "sebagian",
                        "cakupan": cak([fa.get(a, {}).get("r_1j") is not None for a in fa])},
            "binance_ekstra": {"status": self.status.get("binance_ekstra", "ok"), "cakupan": cak([fa[a].get("oi_ubah_1j") is not None for a in maj if a in fa])},
            "dexscreener": {"status": self.status.get("dexscreener", "ok"), "cakupan": cak([dx.get(p) is not None for p in REGISTRY])},
            "rugcheck": {"status": self.status.get("rugcheck", "ok"), "cakupan": cak(list(v is not None for v in rg.values()))},
            "fomo": {"status": self.status.get("fomo_leaderboard", "ok"), "cakupan": cak([lb is not None, th is not None])},
            "berita": {"status": self.status.get("berita", "ok"), "cakupan": 1.0 if jd else 0.0},
        }
