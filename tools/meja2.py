"""Meja AI v2 (P154 format + P155 mesin; F-D110 diubah F-D112 opsi D): tiap 5 menit tiga agent memilih BOT + INSTRUMEN dari data luas F1
(tools/meja_data.py); rumus terkunci memilih bot dominan + instrumen; ARAH tiap instrumen dihitung KODE dengan aturan bot terkunci
(`engine.bots.REGISTRY`, spec yang sama, universe = instrumen terpilih) pada candle harian Binance live. Tidak ada arah yang dikarang AI.

Kecocokan aturan (SK-M15): B1/B2/B6 memakai universe -> bisa diterapkan (B2 butuh >= min_aset 8); B3 butuh kaki spot + funding -> meja perp-only
DATAR; B4 bekerja dari event listing -> hanya instrumen yang baru listing (`onboardDate` <= H hari); B5 terkunci BTC + emas -> instrumen tetap.
Hasil meja = strategi baru (universe pilihan AI + aturan terkunci), BUKAN rekam jejak bot (F-D16 tidak disentuh).
"""
from __future__ import annotations

import dataclasses
import json
import math
import re
import time
from typing import Callable, Dict, List, Optional, Tuple

import meja
import meja_data as md
import meja_slot as ms
from engine.bots import REGISTRY as ATURAN
from engine.data import ListingEvent, MarketData
from engine.series import Series
from engine.spec import SPECS

PARAMS2 = {"v": 4, "maks_instrumen": 8, "universe_top": 50, "hysteresis_poin": 15, "pegang_min_siklus": 3, "harian_limit": 120,
           "likuiditas_min_usd": 50_000, "rugi_harian_maks": 0.03,
           # F-D113 #3: ambang proporsional terhadap n kursi AKTIF (n = 3 -> kuorum 2, instrumen/veto >= 2 agent, skor instrumen >= 1,2 = nilai v1)
           "ambang": "kuorum max(2, ceil(n/2)); instrumen + veto max(2, ceil(n/3)) agent; skor instrumen 0,4 n",
           "instrumen_dari": "agent yang memilih bot akhir; tanpa pemilih + bot ditahan -> instrumen siklus lalu",
           # v3 (koreksi 6 Okt): aturan dengan jumlah aset minimum (B2-RS min_aset 8) diisi skor tertinggi pemilih bot akhir sampai minimum
           "isi_minimum_aturan": "konstanta min_aset spesifikasi bot akhir",
           # r4 (F-D116, dikunci 6 Okt atas kata builder "Gas"): buku Fabius = slot posisi; target aturan tetap dihitung + direkam (pembanding r3)
           "eksekusi": "slot posisi meja_slot.PARAMS_SLOT; buka hanya dari konsensus sah (kuorum tercapai); aturan keluar gagal dibaca -> posisi tetap",
           "slot": ms.PARAMS_SLOT}
# P160 (F-D113): kursi agent LLM, kriteria DIKUNCI atas kata builder 5 Okt ("Gas"); sha di Decisions F-D113. Kursi hanya berubah di evaluasi harian 00:00 UTC.
PARAMS_KURSI = {"v": 2, "status": "terkunci", "maks_aktif": 7, "maks_uji": 3, "jendela_siklus": 288, "naik_sah_min": 0.95, "tukar_unggul_min": 0.005,
                "turun_sah_maks": 0.80,
                # F-D119 (builder 6 Okt "< 80 % sah -> antre, 2x -> keluar"): kursi UJI yang terus gagal tidak lagi menahan antrean
                "uji_turun_sah_maks": 0.80, "uji_amati_min": 144, "uji_gagal_keluar": 2, "antre_tunggu_s": 86_400,
                # F-D121 #9 (builder 6 Okt "saya sepakat"; digabung ke v2 atas kata builder, F-D126: tidak ada v3): kursi uji tidak boleh ditahan tanpa batas waktu
                # (>= 2016 siklus = 7 hari tanpa naik -> belakang antrean bila ada yang menunggu); agent luar paling banyak 2 dari 7 kursi aktif
                "uji_maks_siklus": 2016, "maks_aktif_luar": 2}


def ambang(n_aktif: int) -> dict:
    n = max(1, int(n_aktif))
    return {"kuorum": max(2, math.ceil(n / 2)), "min_agent_instrumen": max(2, math.ceil(n / 3)), "veto_min_agent": max(2, math.ceil(n / 3)),
            "ambang_instrumen": round(0.4 * n, 4)}
BOTS = sorted(SPECS)
EMAS = "PAXGUSDT"
FAPI = meja.FAPI

SYSTEM2 = ("You are an AI analyst on Fabius' 5-minute desk (Binance USDT-M futures, paper only). Every 5 minutes you choose ONE of Fabius' locked bots "
           "(a fixed rule) and up to 8 instruments to apply that rule to. You do NOT choose direction: Fabius' code computes long/short/flat for each "
           "instrument with the bot's locked rule on daily candles. Score every bot, ground every choice in the listed feature names, and be calibrated. "
           "Changes cost 0.05% per side. Write all text in English. Answer with ONE JSON object and nothing else.")
ATURAN_EN = {"B1-TREND": "long when the daily close is above the close 60 days earlier, else flat (equal weight)",
             "B2-RS": "rank by 28-day return: long top 3, short bottom 3 (needs >= 8 instruments)",
             "B3-CARRY": "spot + short perp when 7-day funding > 10%/yr - NOT available on this perp-only desk (always flat)",
             "B4-LISTING-FADE": "short perps listed in the last 14 days (only new listings qualify)",
             "B5-CORE-RWA": "BTC and gold weighted by 1/volatility over 90 days (instruments fixed: BTCUSDT + PAXGUSDT)",
             "B6-BOUNCE": "long when the 10-day price z-score < -2, exit at z >= 0"}


# ---------------------------------------------------------------- data harian + universe (cache)

class Pasar2:
    def __init__(self, get: Callable = md._get, now: Callable[[], float] = time.time):
        self.get, self.now = get, now
        self.cache: Dict[str, Tuple[float, object]] = {}

    def _c(self, key: str, ttl: int, fn):
        t, v = self.cache.get(key, (0.0, None))
        if v is not None and self.now() - t < ttl:
            return v
        v = fn()
        self.cache[key] = (self.now(), v)
        return v

    def _ticker(self) -> List[dict]:
        return self._c("ticker", 600, lambda: [r for r in self.get(f"{FAPI}/fapi/v1/ticker/24hr") if r["symbol"].endswith("USDT") and "_" not in r["symbol"]])

    def universe(self) -> List[str]:
        """50 perp USDT teratas menurut volume kuotasi 24 jam + token registry (urut, tanpa ganda)."""
        top = [r["symbol"] for r in sorted(self._ticker(), key=lambda r: -float(r.get("quoteVolume") or 0))[:PARAMS2["universe_top"]]]
        return sorted(set(top) | set(md.REGISTRY) | {"BTCUSDT", EMAS})

    def tick(self) -> Dict[str, dict]:
        return {r["symbol"]: {"r_24j": round(float(r["priceChangePercent"]) / 100, 6), "volume_24j": round(float(r.get("quoteVolume") or 0))} for r in self._ticker()}

    def onboard(self) -> Dict[str, int]:
        return self._c("onboard", 21_600, lambda: {s["symbol"]: int(s.get("onboardDate") or 0) for s in self.get(f"{FAPI}/fapi/v1/exchangeInfo")["symbols"]})

    def harian(self, a: str) -> Series:
        def f():
            k = self.get(f"{FAPI}/fapi/v1/klines?symbol={a}&interval=1d&limit={PARAMS2['harian_limit']}")
            tutup = [x for x in k if int(x[6]) < self.now() * 1000]                     # hanya candle harian yang SUDAH tutup
            return Series.from_rows([(int(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[7])) for x in tutup])
        return self._c(f"harian:{a}", 3600, f)


def arah(bot: str, instrumen: List[str], p: Pasar2) -> Tuple[Dict[str, float], Dict[str, str]]:
    """-> (bobot aturan per aset, alasan untuk aset yang datar/ditolak). Aturan terkunci dijalankan apa adanya pada universe = instrumen."""
    spec, why = SPECS[bot], {}
    if bot == "B3-CARRY":
        return {}, {a: "B3 needs a spot leg + funding; this desk is perp-only -> flat" for a in instrumen}
    if bot == "B5-CORE-RWA":
        instrumen = ["BTCUSDT", EMAS]
    data = MarketData()
    for a in instrumen:
        try:
            s = p.harian(a)
            data.perp[a] = s
            data.spot[a] = s                                                                # B5 memakai `spot`; perp harian sebagai proksi (dicatat)
        except Exception as e:  # noqa: BLE001
            why[a] = f"daily candles failed: {type(e).__name__}"
    if bot == "B4-LISTING-FADE":
        ob, h_ms = p.onboard(), int(spec.param) * 86_400_000
        for a in list(data.perp):
            t0 = ob.get(a, 0)
            s = data.perp[a]
            if not t0 or p.now() * 1000 - t0 > h_ms + 86_400_000 or not s.t:
                why[a] = "B4 applies only to perps listed within H days"
                continue
            data.events.append(ListingEvent(a, int(s.t[0]), float(s.c[0]), float(s.v[0])))
    tg = ATURAN[bot](dataclasses.replace(spec, universe=tuple(sorted(data.perp))), data)
    w = dict(tg[-1].weights) if tg else {}
    for a in instrumen:
        if a not in why and abs(w.get(a, 0.0)) < 1e-12:
            why[a] = "rule gives flat" if tg else "not enough daily bars for the lookback / rule condition"
    return w, why


def aturan_terbaca(bot: str, instrumen: List[str], p: Pasar2) -> Optional[Dict[str, float]]:
    """r4 aturan keluar (SK-M27): bobot aturan, atau None bila aturan tidak terbaca - galat, atau candle harian SATU aset universe gagal (`arah`
    menangkapnya per aset dan menghitung pada universe yang bolong; datar karena data hilang BUKAN sinyal keluar). None -> posisi tetap, SL/TP menjaga."""
    try:
        w, why = arah(bot, instrumen, p)
    except Exception:  # noqa: BLE001
        return None
    return None if any(str(v).startswith("daily candles failed") for v in why.values()) else w


N1, N2, N6 = int(SPECS["B1-TREND"].param), int(SPECS["B2-RS"].param), int(SPECS["B6-BOUNCE"].param)
FITUR_ATURAN = [f"tren_{N1}h", f"r_{N2}h", f"z_{N6}h", "umur_listing_h", "hari_data"]


def fitur_aturan(p: Pasar2, uni: List[str]) -> Dict[str, dict]:
    """Masukan aturan per instrumen, dihitung KODE dari candle harian yang sudah tutup, rumus yang sama dengan aturan terkunci:
    tren_60h = c/c[-60]-1 (B1 long bila > 0), r_28h (B2 mengurutkan), z_10h (B6 long bila < -2, ddof=1), umur_listing_h (B4 bila <= 14)."""
    import concurrent.futures as cf
    from engine.series import rolling_mean, rolling_std
    try:
        ob = p.onboard()
    except Exception:  # noqa: BLE001
        ob = {}

    def satu(a: str) -> Tuple[str, dict]:
        try:
            c = list(p.harian(a).c)
        except Exception:  # noqa: BLE001 - gagal = tanpa fitur aturan (tidak dikarang)
            return a, {}
        f = {"hari_data": len(c)}
        if len(c) > N1:
            f[f"tren_{N1}h"] = round(c[-1] / c[-1 - N1] - 1, 4)
        if len(c) > N2:
            f[f"r_{N2}h"] = round(c[-1] / c[-1 - N2] - 1, 4)
        if len(c) >= N6:
            m, sd = rolling_mean(c, N6)[-1], rolling_std(c, N6)[-1]
            if sd:
                f[f"z_{N6}h"] = round((c[-1] - m) / sd, 3)
        if ob.get(a):
            f["umur_listing_h"] = int((p.now() * 1000 - ob[a]) // 86_400_000)
        return a, f
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        return dict(pool.map(satu, uni))


# ---------------------------------------------------------------- format v2

def nama_fitur(snap: Optional[dict]) -> List[str]:
    fa = (snap or {}).get("fitur_aset") or {}
    fb = (snap or {}).get("fitur_bot") or {}
    return sorted({k for f in fa.values() for k in f} | {k for f in fb.values() for k in f} | {"r_24j", "volume_24j"} | set(FITUR_ATURAN))


def prompt2(snap: Optional[dict], uni: List[str], tick: Dict[str, dict], buku: dict, harga: Dict[str, float], ring: Optional[str],
            fa_aturan: Optional[Dict[str, dict]] = None) -> str:
    fa, far = (snap or {}).get("fitur_aset") or {}, fa_aturan or {}
    rows = []
    for a in uni:
        f, t = {**(fa.get(a) or {}), **(far.get(a) or {})}, tick.get(a) or {}
        x = {k: v for k, v in f.items() if v is not None}
        rows.append(f"{a}: r_24j {t.get('r_24j')} volume_24j {t.get('volume_24j')} " + " ".join(f"{k} {v}" for k, v in sorted(x.items())))
    bots = "\n".join(f"- {b}: {ATURAN_EN[b]} | fit {json.dumps((snap or {}).get('fitur_bot', {}).get(b, {}), separators=(',', ':'))}" for b in BOTS)
    pos = {a: round(q['qty'] * harga.get(a, q['masuk']) / max(meja.ekuitas(buku, harga), 1e-9), 4) for a, q in buku.get("posisi", {}).items()}
    return (f"Your v2 paper book: equity {meja.ekuitas(buku, harga):.2f} (start {meja.PARAMS['modal_awal']:.0f}), positions {pos or 'flat'}.\n"
            f"Last cycle you wrote: {ring or '(first cycle)'}\n\nBots (locked rules) and measured fit features:\n{bots}\n\n"
            f"Instruments you may choose (top {PARAMS2['universe_top']} by 24h volume + registry tokens) with measured features (fractions; z_<name> = 24h "
            f"z-score of that feature). Rule inputs computed by Fabius from closed daily candles: tren_{N1}h (B1 is long only when > 0), r_{N2}h (B2 ranks by it), "
            f"z_{N6}h (B6 buys when < -2), umur_listing_h (B4 only when <= {int(SPECS['B4-LISTING-FADE'].param)}), hari_data (daily bars available):\n"
            + "\n".join(rows)
            + f"\n\nFeature names you may cite: {', '.join(nama_fitur(snap))}.\n"
            'Reply with exactly: {"ringkasan": "<max 400 chars>", "bot": "<one bot>", "skor_bot": {"<each of the 6 bots>": <-100..100>}, '
            '"keyakinan": <0-100>, "eksposur": <0-100 share of the bot rule to use>, "instrumen": [{"aset": "<symbol>", "keyakinan": <0-100>, '
            '"faktor": ["<feature names>"]}] (max 8), "veto_aset": [{"aset": "<symbol>", "faktor": "<feature name>", "alasan": "..."}], '
            '"faktor": ["<feature names>"], "alasan": "<max 400 chars>"}')


def parse2(text: str, uni: List[str], fitur: List[str]) -> dict:
    """Validasi format v2 (SK-M6, SK-M14). Salah struktural = ValueError (keputusan agent ditolak); entri salah per item = `ditolak`."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError("no JSON")
    o = json.loads(m.group(0))
    ring = str(o.get("ringkasan") or "").strip()[:400]
    if not ring:
        raise ValueError("empty ringkasan")
    sk = o.get("skor_bot") or {}
    if set(sk) != set(BOTS):
        raise ValueError(f"skor_bot must score all six bots (got {sorted(sk)})")
    skor = {b: int(sk[b]) for b in BOTS}
    if any(not -100 <= v <= 100 for v in skor.values()):
        raise ValueError("skor_bot outside -100..100")
    bot = str(o.get("bot", "")).upper()
    if bot not in BOTS or skor[bot] != max(skor.values()):
        raise ValueError(f"bot {bot!r} is not the top score")
    k, eks = int(o.get("keyakinan", -1)), int(o.get("eksposur", -1))
    if not (0 <= k <= 100 and 0 <= eks <= 100):
        raise ValueError("keyakinan / eksposur outside 0..100")
    fset, ditolak = set(fitur), []
    fk = [f for f in (o.get("faktor") or []) if f in fset]
    ditolak += [{"faktor": f, "galat": "not a feature name"} for f in (o.get("faktor") or []) if f not in fset]
    if not fk:
        raise ValueError("faktor empty / none from the feature list")
    ins = []
    for it in (o.get("instrumen") or [])[:PARAMS2["maks_instrumen"]]:
        a = str((it or {}).get("aset", "")).upper()
        if a not in uni:
            ditolak.append({"aset": a, "galat": "outside universe"})
            continue
        ins.append({"aset": a, "k": max(0, min(100, int(it.get("keyakinan", 0)))) / 100, "faktor": [f for f in (it.get("faktor") or []) if f in fset]})
    mn = int(SPECS[bot].konstanta.get("min_aset", 0))
    if mn and len(ins) < mn:                                                                 # dicatat, bukan ditolak: buku agent ini datar menurut aturan
        ditolak.append({"bot": bot, "galat": f"{bot} needs >= {mn} instruments, got {len(ins)}"})
    veto = [{"aset": str(v.get("aset", "")).upper(), "faktor": v.get("faktor")} for v in (o.get("veto_aset") or [])
            if str(v.get("aset", "")).upper() in uni and v.get("faktor") in fset]
    return {"ringkasan": ring, "bot": bot, "skor_bot": skor, "k": k / 100, "eksposur": eks / 100, "instrumen": ins, "veto": veto, "faktor": fk,
            "alasan": str(o.get("alasan", ""))[:400], "ditolak": ditolak}


# ---------------------------------------------------------------- konsensus v2 + posisi

def konsensus2(kep: Dict[str, dict], state: dict, snap: Optional[dict], n_aktif: int = 3) -> Tuple[dict, str]:
    """Bot dominan (hysteresis) + instrumen + eksposur + veto dari keputusan SAH kursi AKTIF. state = {"bot", "pegang"} dibawa antar siklus.
    Ambang dari `ambang(n_aktif)` (F-D113 #3)."""
    am = ambang(n_aktif)
    if len(kep) < am["kuorum"]:
        return {"bot": state.get("bot"), "instrumen": state.get("instrumen", []), "eksposur": state.get("eksposur", 0.0), "veto": []}, \
            f"quorum not reached ({len(kep)} valid)"
    n = len(kep)
    nilai = {b: round(sum(d["k"] * d["skor_bot"][b] for d in kep.values()) / n, 4) for b in BOTS}
    top = max(BOTS, key=lambda b: (nilai[b], b == state.get("bot")))
    cur, pegang = state.get("bot"), state.get("pegang", 0)
    if cur and top != cur and (nilai[top] - nilai[cur] < PARAMS2["hysteresis_poin"] or pegang < PARAMS2["pegang_min_siklus"]):
        top, why = cur, f"hold {cur} (hysteresis: {nilai[top] - nilai[cur]:+.1f} points, held {pegang} cycles)"
    else:
        why = f"dominant bot {top} ({nilai[top]:+.1f})"
    # koreksi 5 Okt (PARAMS2 v2): instrumen hanya dari agent yang memilih bot AKHIR - instrumen pilihan untuk bot lain tidak cocok dengan aturan
    # bot ini (16:25Z produksi: B2-RS ditahan hysteresis dengan BTC + PAXG pilihan B5 -> aturan B2 datar). Tak ada pemilihnya -> instrumen lama.
    skor_i: Dict[str, float] = {}
    jml: Dict[str, int] = {}
    pemilih = [d for d in kep.values() if d["bot"] == top]
    for d in pemilih:
        for it in d["instrumen"]:
            skor_i[it["aset"]] = skor_i.get(it["aset"], 0.0) + it["k"]
            jml[it["aset"]] = jml.get(it["aset"], 0) + 1
    ins = [a for a in sorted(skor_i, key=lambda a: (-skor_i[a], a))
           if jml[a] >= am["min_agent_instrumen"] or skor_i[a] >= am["ambang_instrumen"]][:PARAMS2["maks_instrumen"]]
    if not pemilih and top == cur:
        ins = list(state.get("instrumen", []))
    min_ins = int(SPECS[top].konstanta.get("min_aset", 0)) if top in SPECS else 0
    if min_ins and len(ins) < min_ins:                                                       # B2-RS: peringkat butuh >= 8 aset
        ins = (ins + [a for a in sorted(skor_i, key=lambda a: (-skor_i[a], a)) if a not in ins])[:max(min_ins, PARAMS2["maks_instrumen"])]
        why += f"; filled to {len(ins)} instruments for the {top} minimum of {min_ins}"
    vc: Dict[str, int] = {}
    for d in kep.values():
        for v in d["veto"]:
            vc[v["aset"]] = vc.get(v["aset"], 0) + 1
    fa = (snap or {}).get("fitur_aset") or {}
    keras = {a for a in ins if (fa.get(a) or {}).get("rug_bahaya")                      # SK-M9: veto keras dari data terukur, bukan dari agent
             or ((fa.get(a) or {}).get("dex_likuiditas_usd") is not None and fa[a]["dex_likuiditas_usd"] < PARAMS2["likuiditas_min_usd"])}
    veto = sorted({a for a, c in vc.items() if c >= am["veto_min_agent"]} | keras)
    eks = round(sum(d["eksposur"] for d in kep.values()) / n, 4)
    state.update(bot=top, pegang=pegang + 1 if top == cur else 1, instrumen=ins, eksposur=eks)
    return {"bot": top, "nilai_bot": nilai, "instrumen": ins, "skor_instrumen": {a: round(skor_i[a], 4) for a in ins if a in skor_i}, "eksposur": eks, "veto": veto}, why


def kursi_daftar(st: dict, slugs: List[str], t0: int, keluar: Optional[List[str]] = None) -> List[dict]:
    """P160: agent yang belum punya kursi -> aktif (hanya saat state kursi masih kosong = agent awal), lalu uji, lalu antre (SK-M19). Antre naik ke uji
    begitu ada kursi uji kosong. `keluar` = agent yang dinonaktifkan builder di config: kursinya dilepas (status `keluar`, SK-M23) supaya antrean maju;
    bila diaktifkan lagi ia masuk seperti agent baru. -> peristiwa kursi (ikut rekaman `kursi` yang di-hash)."""
    P, k = PARAMS_KURSI, st.setdefault("kursi", {})
    awal, ev = not k, []
    n = lambda status: sum(1 for v in k.values() if v["status"] == status)  # noqa: E731
    for s in sorted(set(keluar or []) & set(k)):
        if k[s]["status"] != "keluar":
            ev.append({"agent": s, "dari": k[s]["status"], "ke": "keluar", "alasan": "agent dinonaktifkan builder"})
            k[s] = {"status": "keluar", "sejak": t0}
    for s in slugs:
        if s in k and (k[s]["status"] != "keluar" or k[s].get("gagal")):            # F-D119: keluar karena gagal = tidak masuk otomatis lagi
            continue
        if awal and n("aktif") < P["maks_aktif"]:
            ke, why = "aktif", "agent awal meja v2"
        elif n("uji") < P["maks_uji"]:
            ke, why = "uji", "agent baru"
        else:
            ke, why = "antre", "kursi uji penuh"
        k[s] = {"status": ke, "sejak": t0}
        ev.append({"agent": s, "dari": None, "ke": ke, "alasan": why})
    for s in sorted((x for x, v in k.items() if v["status"] == "antre"), key=lambda x: k[x]["sejak"]):
        if n("uji") < P["maks_uji"] and k[s].get("tunggu_sampai", 0) <= t0:
            k[s] = {"status": "uji", "sejak": t0}
            ev.append({"agent": s, "dari": "antre", "ke": "uji", "alasan": "kursi uji kosong"})
    return ev


def kursi_paksa(st: dict, paksa: Optional[List[dict]], t0: int) -> List[dict]:
    """Keputusan kursi BUILDER (`config/agents.json` `kursi_builder`, SK-M24): tiap entri {id, slug, ke, alasan} diterapkan SEKALI (id dicatat di
    state) dan tercatat sebagai peristiwa `kursi` yang dikomit; batas 7 aktif / 3 uji tetap berlaku; agent tanpa kursi atau `keluar` ditolak. Sesudahnya
    evaluasi harian berjalan biasa. -> peristiwa."""
    P, k, ev = PARAMS_KURSI, st.setdefault("kursi", {}), []
    selesai = st.setdefault("paksa_selesai", [])
    n = lambda status: sum(1 for v in k.values() if v["status"] == status)  # noqa: E731
    for e in paksa or []:
        if e["id"] in selesai:
            continue
        selesai.append(e["id"])
        s, ke = e["slug"], e["ke"]
        cur = (k.get(s) or {}).get("status")
        tolak = ("agent tidak punya kursi" if cur in (None, "keluar") else
                 "kursi aktif penuh" if ke == "aktif" and cur != "aktif" and n("aktif") >= P["maks_aktif"] else
                 "kursi uji penuh" if ke == "uji" and cur != "uji" and n("uji") >= P["maks_uji"] else None)
        if tolak or cur == ke:
            ev.append({"agent": s, "dari": cur, "ke": cur, "alasan": f"builder decision {e['id']} not applied: {tolak or 'already there'}"})
            continue
        ev.append({"agent": s, "dari": cur, "ke": ke, "alasan": f"builder decision {e['id']}: {e['alasan']}"})
        k[s] = {"status": ke, "sejak": t0}
    return ev


def kursi_catat(st: dict, slug: str, sah: bool, ekuitas: float) -> None:
    """Riwayat bergulir per agent (jendela 288 siklus): jawaban sah 1/0 + ekuitas buku v2-nya - dasar evaluasi harian."""
    h = st.setdefault("riwayat", {}).setdefault(slug, {"sah": [], "eq": []})
    w = PARAMS_KURSI["jendela_siklus"]
    h["sah"] = (h["sah"] + [1 if sah else 0])[-w:]
    h["eq"] = (h["eq"] + [round(ekuitas, 4)])[-(w + 1):]


def kursi_evaluasi(st: dict, t0: int, luar: Optional[set] = None, tahan: Optional[Callable[[str, dict], Optional[str]]] = None) -> List[dict]:
    """P160 evaluasi harian (SK-M21, SK-M22): turun bila sah < 80 % dalam jendela penuh; naik bila >= jendela siklus di kursi uji, sah >= 95 % dan hasil
    jendela >= median aktif (kursi aktif kosong) atau unggul >= 0,5 pp dari aktif terburuk (tukar). `luar` = slug agent luar (F-D121 #9): paling banyak
    `maks_aktif_luar` kursi aktif; kursi uji yang >= `uji_maks_siklus` tanpa naik bergeser ke belakang antrean bila ada yang menunggu. -> peristiwa.
    P168b: `tahan(slug, entri_kursi)` -> alasan = peninjau LLM MENAHAN kenaikan calon yang SUDAH memenuhi aturan numerik (tercatat sebagai peristiwa);
    ia tidak pernah menaikkan siapa pun dan tidak mengubah PARAMS_KURSI."""
    P, k, r, ev = PARAMS_KURSI, st.get("kursi", {}), st.get("riwayat", {}), []
    w, luar = P["jendela_siklus"], set(luar or ())

    def stat(s):
        h = r.get(s) or {"sah": [], "eq": []}
        eq = h["eq"]
        return len(h["sah"]), (sum(h["sah"]) / len(h["sah"]) if h["sah"] else 0.0), (eq[-1] / eq[0] - 1 if len(eq) > 1 and eq[0] else 0.0)

    def pindah(s, ke, why, extra=None):
        ev.append({"agent": s, "dari": k[s]["status"], "ke": ke, "alasan": why, **(extra or {})})
        k[s] = {"status": ke, "sejak": t0}

    for s in sorted(x for x, v in k.items() if v["status"] == "aktif"):
        n, sah, _ = stat(s)
        if n >= w and sah < P["turun_sah_maks"]:
            pindah(s, "uji", f"valid answers {sah:.0%} < {P['turun_sah_maks']:.0%} over {n} cycles")
    # F-D119 (PARAMS_KURSI v2): kursi uji yang terus gagal -> belakang antrean (riwayat diulang, tunggu satu evaluasi harian); kedua kali -> keluar
    gagal = st.setdefault("gagal_uji", {})
    for s in sorted(x for x, v in k.items() if v["status"] == "uji" and v["sejak"] < t0):     # yang baru turun dari aktif dapat masa uji dulu
        n, sah, _ = stat(s)
        if n >= P["uji_amati_min"] and sah < P["uji_turun_sah_maks"]:
            gagal[s] = gagal.get(s, 0) + 1
            why = f"trial seat: valid answers {sah:.0%} < {P['uji_turun_sah_maks']:.0%} over {n} cycles (failure {gagal[s]} of {P['uji_gagal_keluar']})"
            r.pop(s, None)
            if gagal[s] >= P["uji_gagal_keluar"]:
                pindah(s, "keluar", why, {"gagal": True})
                k[s]["gagal"] = True
            else:
                pindah(s, "antre", why)
                k[s]["tunggu_sampai"] = t0 + P["antre_tunggu_s"]
    aktif = [x for x, v in k.items() if v["status"] == "aktif"]
    rets = sorted(stat(x)[2] for x in aktif)
    median = rets[len(rets) // 2] if len(rets) % 2 else (sum(rets[len(rets) // 2 - 1:len(rets) // 2 + 1]) / 2 if rets else 0.0)
    calon = []
    for s, v in k.items():
        n, sah, ret = stat(s)
        if v["status"] == "uji" and (t0 - v["sejak"]) // meja.PARAMS["siklus_s"] >= w and sah >= P["naik_sah_min"] and ret >= median:
            calon.append((ret, s, sah))
    for ret, s, sah in sorted(calon, reverse=True):
        try:
            ditahan = tahan(s, k[s]) if tahan else None
        except Exception as e:  # noqa: BLE001 - SK-N15: galat peninjau = TAHAN (bukan naik, bukan siklus gagal)
            ditahan = f"reviewer error: {type(e).__name__}"
        if ditahan:                                                                           # P168b: hanya MENAHAN (SK-N13)
            ev.append({"agent": s, "dari": "uji", "ke": "uji", "alasan": f"promotion held: {ditahan}"})
            continue
        aktif = [x for x, v in k.items() if v["status"] == "aktif"]
        aktif_luar = [x for x in aktif if x in luar]
        batas_luar = s in luar and len(aktif_luar) >= P["maks_aktif_luar"]                    # F-D121 #9b: agent luar paling banyak maks_aktif_luar kursi aktif
        if len(aktif) < P["maks_aktif"] and not batas_luar:
            pindah(s, "aktif", f"valid {sah:.0%}, return {ret:+.2%} >= active median {median:+.2%}")
            continue
        korban = aktif_luar if batas_luar else aktif                                          # batas luar tercapai: hanya boleh menukar agent luar aktif
        lama = [x for x in korban if (t0 - k[x]["sejak"]) // meja.PARAMS["siklus_s"] >= w]
        if not lama:
            continue
        worst = min(lama, key=lambda x: (stat(x)[2], x))
        if ret - stat(worst)[2] >= P["tukar_unggul_min"]:
            pindah(worst, "uji", f"swapped out by {s} (return {stat(worst)[2]:+.2%} vs {ret:+.2%})")
            pindah(s, "aktif", f"swapped in for {worst} (+{ret - stat(worst)[2]:.2%})")
    # F-D121 #9a: kursi uji >= uji_maks_siklus tanpa naik bergeser ke belakang antrean, sebanyak yang dibutuhkan agent yang menunggu dan boleh masuk
    tunggu = [x for x, v in k.items() if v["status"] == "antre" and v.get("tunggu_sampai", 0) <= t0]
    butuh = len(tunggu) - max(0, P["maks_uji"] - sum(1 for v in k.values() if v["status"] == "uji"))
    for s in sorted((x for x, v in k.items() if v["status"] == "uji" and (t0 - v["sejak"]) // meja.PARAMS["siklus_s"] >= P["uji_maks_siklus"]),
                    key=lambda x: (k[x]["sejak"], x)):
        if butuh <= 0:
            break
        n = (t0 - k[s]["sejak"]) // meja.PARAMS["siklus_s"]
        r.pop(s, None)
        pindah(s, "antre", f"trial seat held {n} cycles (max {P['uji_maks_siklus']}) without promotion and another agent is waiting")
        k[s]["tunggu_sampai"] = t0 + P["antre_tunggu_s"]
        butuh -= 1
    return ev


def posisi(bot: Optional[str], ins: List[str], eks: float, veto: List[str], p: Pasar2) -> Tuple[Dict[str, dict], dict]:
    """Bobot akhir = bobot aturan / max(1, gross aturan) x eksposur; veto dibuang; maks 25 % per aset; gross <= 1."""
    if not bot or not ins and bot != "B5-CORE-RWA":
        return {}, {}
    w, why = arah(bot, [a for a in ins if a not in veto], p)
    g = max(1.0, sum(abs(v) for v in w.values()))
    out = {a: {"w": round(max(-meja.PARAMS["maks_per_aset"], min(meja.PARAMS["maks_per_aset"], v / g * eks)), 6), "k": 1.0}
           for a, v in w.items() if abs(v) > 1e-12 and a not in veto}
    gross = sum(abs(x["w"]) for x in out.values())
    if gross > meja.PARAMS["maks_gross"]:
        for x in out.values():
            x["w"] = round(x["w"] * meja.PARAMS["maks_gross"] / gross, 6)
    return out, why


# ---------------------------------------------------------------- satu siklus v2 (berjalan paralel dengan v1; rekaman ikut Merkle root siklus yang sama)

def siklus2(t0: int, agents: List[dict], books: Dict[str, dict], ring: Dict[str, str], call: Callable[[dict, str, str], str], snap: Optional[dict],
            p: Pasar2, get: Callable = None, log: Callable[[str], None] = print, sampai: Optional[float] = None,
            keluar: Optional[List[str]] = None, paksa: Optional[List[dict]] = None,
            bukti: Optional[Callable[[str, int], Optional[dict]]] = None,
            tahan_naik: Optional[Callable[[str, dict], Optional[str]]] = None) -> Tuple[List[dict], Dict[str, float]]:
    """-> (rekaman per agent v2 + konsensus v2, harga isi). `sampai` = waktu mutlak batas jawab model (gerbang memasangnya supaya komit siklus tetap
    sempat); dihitung SESUDAH data aturan + harga dibaca, jadi cache dingin tidak memakan jatah komit."""
    import concurrent.futures as cf
    get = get or meja._get_json
    state = books.setdefault("_v2_state", {})
    kst = books.setdefault("_v2_kursi", {})
    ev_kursi = kursi_daftar(kst, [ag["slug"] for ag in agents], t0, keluar)
    ev_paksa = kursi_paksa(kst, paksa, t0)                                                   # SK-M24: keputusan builder, sekali, tercatat
    if ev_paksa:
        ev_kursi += ev_paksa + kursi_daftar(kst, [ag["slug"] for ag in agents], t0)           # kursi uji yang kosong diisi antrean
    if t0 % 86_400 == 0:                                                                     # SK-M21: kursi hanya berubah di siklus 00:00 UTC
        ev_kursi += kursi_evaluasi(kst, t0, {ag["slug"] for ag in agents if ag.get("luar")}, tahan=tahan_naik)      # P168b: peninjau LLM boleh MENAHAN naik
        ev_kursi += kursi_daftar(kst, [ag["slug"] for ag in agents], t0)                     # F-D119: kursi uji yang dilepas langsung diisi antrean
    kursi = {s: v["status"] for s, v in kst["kursi"].items()}
    agents = [ag for ag in agents if kursi.get(ag["slug"]) in ("aktif", "uji")]               # SK-M19: antre tidak dijalankan
    uni, tk = p.universe(), p.tick()
    fitur = nama_fitur(snap)
    far = fitur_aturan(p, uni)
    harga = meja.harga_isi(get, aset=sorted(set(uni) | set(ms.aset_dipegang(books.get("v2")))))       # r4: aset dipegang selalu diberi harga
    batas = meja.PARAMS["batas_jawab_s"] if sampai is None else max(1.0, min(meja.PARAMS["batas_jawab_s"], sampai - time.time()))
    for ag in agents:
        books.setdefault(f"v2:{ag['slug']}", meja.buku_baru())
    books.setdefault("v2", meja.buku_baru())
    prompts = {ag["slug"]: prompt2(snap, uni, tk, books[f"v2:{ag['slug']}"], harga, ring.get(f"v2:{ag['slug']}"), far) for ag in agents}
    hasil: Dict[str, dict] = {}
    pool = cf.ThreadPoolExecutor(max_workers=max(1, len(agents)))
    # P166 (F-D121): agent luar (`luar`) dijawab lewat PULL; `call` menerima siklus + pemeriksa format `parse2` supaya galat format dilaporkan saat itu juga
    argumen = lambda ag: ({**ag, "siklus": t0, "tenggat": time.time() + batas, "validasi": lambda raw: parse2(raw, uni, fitur)} if ag.get("luar") else ag)  # noqa: E731
    fut = {pool.submit(call, argumen(ag), SYSTEM2, prompts[ag["slug"]]): ag for ag in agents}
    try:
        for f in cf.as_completed(fut, timeout=batas):
            ag = fut[f]
            try:
                raw = f.result()
                hasil[ag["slug"]] = {"raw": raw, "kep": parse2(raw, uni, fitur)}
            except Exception as e:  # noqa: BLE001
                hasil[ag["slug"]] = {"galat": f"{type(e).__name__}: {str(e)[:160]}"}
    except cf.TimeoutError:
        pass
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    data_sha, data_t = (snap or {}).get("sha"), (snap or {}).get("t")
    rek = []
    for ag in agents:
        s, h, nb = ag["slug"], hasil.get(ag["slug"]), f"v2:{ag['slug']}"
        r = {"v": 2, "siklus": t0, "agent": nb, "agent_id": int(ag["agent_id"]), "model": ag["model"], "data_sha": data_sha, "data_t": data_t, "harga_isi_sha": meja.sha(harga),
             "prompt_sha": meja.sha(SYSTEM2.encode() + b"\n" + prompts[s].encode()), "kursi": kursi[s]}
        if h is None:
            r.update(status="terlambat", galat=f"no answer within {batas:.0f} s")
        elif "galat" in h:
            r.update(status="gagal", galat=h["galat"])
        else:
            k = h["kep"]
            tg, why = posisi(k["bot"], [i["aset"] for i in k["instrumen"]], k["eksposur"], [v["aset"] for v in k["veto"]], p)
            for a in tg:
                tg[a]["alasan"] = f"{k['bot']} rule"
            r.update(status="ok", jawaban_sha=meja.sha(h["raw"].encode()), keputusan={**k, "ringkasan": f"{k['bot']} on {', '.join(i['aset'] for i in k['instrumen']) or '-'}: {k['ringkasan']}",
                     "target": tg, "diubah": sorted(tg), "arah_alasan": why}, isi=meja.isi(books[nb], tg, harga))
            ring[nb] = k["ringkasan"]
            if ag.get("luar") and bukti and bukti(s, t0):                                      # bukti tanda tangan ikut rekaman yang di-hash + dikomit
                r["luar"] = bukti(s, t0)
        r["ekuitas"] = round(meja.ekuitas(books[nb], harga), 4)
        kursi_catat(kst, s, r["status"] == "ok", r["ekuitas"])
        rek.append(r)
    aktif = [ag["slug"] for ag in agents if kursi[ag["slug"]] == "aktif"]
    sah = {s: h["kep"] for s, h in hasil.items() if h and "kep" in h and s in aktif}             # SK-M20: kursi uji tidak dihitung
    bot_lalu = state.get("bot")
    kk, why = konsensus2(sah, state, snap, n_aktif=len(aktif))
    tg, arah_why = posisi(kk.get("bot"), kk.get("instrumen", []), kk.get("eksposur", 0.0), kk.get("veto", []), p)
    buku = books["v2"]
    hari, e_now = time.strftime("%Y-%m-%d", time.gmtime(t0)), meja.ekuitas(buku, harga)
    if state.get("hari") != hari:
        state.update(hari=hari, ekuitas_awal_hari=round(e_now, 4))
    rugi = e_now / max(state["ekuitas_awal_hari"], 1e-9) - 1
    rem = rugi <= -PARAMS2["rugi_harian_maks"]
    if rem:                                                                                  # SK-M10: rem rugi harian, datar sampai 00:00 UTC
        why = f"{why}; daily loss brake {rugi:+.2%} -> flat until 00:00 UTC"
    # r4 (F-D116): target aturan TIDAK diisi langsung; ia hanya sumber kandidat slot (dan tetap direkam utuh untuk pembanding r3)
    rk = {"v": 2, "siklus": t0, "agent": "v2", "rumus": f"v2 params {meja.sha(PARAMS2)[:18]}", "dasar": why, "masuk": sorted(sah), "aktif": sorted(aktif),
          "ambang": ambang(len(aktif)), "data_sha": data_sha, "data_t": data_t, **kk, "target": tg, "arah_alasan": arah_why, "harga_isi_sha": meja.sha(harga)}

    def atr(a: str) -> Optional[float]:
        try:
            return ms.atr_frac(p.harian(a), ms.PARAMS_SLOT["atr_hari"])
        except Exception:  # noqa: BLE001 - tanpa candle harian: tidak dibuka (SK-M27)
            return None
    aturan_keluar: Dict[tuple, Dict[str, float]] = {}

    def keluar(pos: dict) -> bool:
        key = (pos["bot"], tuple(sorted(pos.get("uni") or [])))
        if key not in aturan_keluar:
            aturan_keluar[key] = aturan_terbaca(pos["bot"], list(pos.get("uni") or []), p)
        w = aturan_keluar[key]
        if w is None:
            return False
        x = w.get(pos["aset"], 0.0)
        return (1 if x > 1e-12 else -1 if x < -1e-12 else 0) != pos["arah"]
    kand = [] if rem or "skor_instrumen" not in kk else ms.kandidat(rk, atr)                # buka hanya dari konsensus sah siklus ini
    rk["isi"] = ms.migrasi(buku, harga, bot_lalu) + ms.langkah(buku, t0, harga, kand, keluar, rem)
    rk["slot"] = ms.snapshot(buku, harga)
    buku["target"] = {x["aset"]: {"w": x["w"], "k": 1.0} for x in rk["slot"]}              # /desk "target" = slot terbuka, bukan target aturan
    rk["ekuitas"] = round(meja.ekuitas(buku, harga), 4)
    rek.append(rk)
    if ev_kursi:                                                                             # SK-M21: tiap perubahan kursi ikut Merkle root siklus ini
        rek.append({"v": 2, "siklus": t0, "agent": "kursi", "peristiwa": ev_kursi, "kursi": dict(sorted(kursi_now(kst).items())),
                    "params_kursi_sha": meja.sha(PARAMS_KURSI), "ekuitas": 0.0})
    for r in rek:
        r["hash"] = meja.sha(r)
    log(f"meja v2 {time.strftime('%H:%M', time.gmtime(t0))}Z: {why} | instrumen {kk.get('instrumen')} | eksposur {kk.get('eksposur')} | "
        + " | ".join(f"{r['agent']} {r.get('status', 'ok')} eq {r['ekuitas']:.2f}" for r in rek if r["agent"] != "kursi")
        + (f" | kursi: {'; '.join(e['agent'] + ' ' + str(e['dari']) + '->' + e['ke'] for e in ev_kursi)}" if ev_kursi else ""))
    return rek, harga


def buku_hidup(recs: List[dict], agen: Optional[List[dict]] = None, sik: Optional[dict] = None, maks_titik: int = 600, n_pita: int = 60) -> dict:
    """P164 Fabius Live Book: ringkasan SELURUH riwayat buku Fabius dari rekaman konsensus (agent "v2"), urut waktu.
    Atribusi per bot (dinyatakan jujur): rekaman r1-r3 - perubahan ekuitas siklus i = pasar (posisi yang diputuskan di siklus i-1) - fee isi siklus i;
    bagian pasar dicatat ke bot siklus i-1, fee ke bot siklus i. Rekaman r4 (punya `slot`, F-D116) - per posisi: untung/rugi yang direalisasi + fee
    tiap isi ke bot pembuka posisi itu, untung/rugi belum direalisasi slot terakhir ke bot pemiliknya; siklus per bot = siklus bot itu memegang slot.
    `agen` = rekaman agent siklus terakhir (strip pipeline), `sik` = root/tx/status siklus terakhir."""
    recs = sorted(recs, key=lambda r: r["siklus"])
    if not recs:
        return {"kosong": True}
    awal = meja.PARAMS["modal_awal"]
    eq = [float(r["ekuitas"]) for r in recs]
    puncak, dd = awal, 0.0
    for e in eq:
        puncak = max(puncak, e)
        dd = min(dd, e / puncak - 1)
    fee_i = [sum(float(f.get("fee", 0)) for f in r.get("isi") or []) for r in recs]
    per_bot: Dict[str, dict] = {}
    def pb(b):
        return per_bot.setdefault(b or "-", {"siklus": 0, "pasar": 0.0, "fee": 0.0, "isi": 0})
    slot_akhir = None
    for i, r in enumerate(recs):
        if "slot" in r:                                                                      # r4: per posisi
            for f in r.get("isi") or []:
                x = pb(f.get("bot"))
                x["pasar"] += float(f.get("pnl", 0.0))
                x["fee"] += float(f.get("fee", 0.0))
                x["isi"] += 1
            for b in {s_["bot"] for s_ in r["slot"]}:
                pb(b)["siklus"] += 1
            slot_akhir = r["slot"]
            continue
        x = pb(r.get("bot"))
        x["siklus"] += 1
        x["fee"] += fee_i[i]
        x["isi"] += len(r.get("isi") or [])
        if i:
            pb(recs[i - 1].get("bot"))["pasar"] += eq[i] - eq[i - 1] + fee_i[i]
    for s_ in slot_akhir or []:                                                              # slot masih terbuka: untung/rugi belum direalisasi
        pb(s_["bot"])["pasar"] += float(s_.get("pnl", 0.0))
    pita: List[dict] = []
    for r in recs:
        b = r.get("bot") or "-"
        if pita and pita[-1]["bot"] == b:
            pita[-1].update(sampai=r["siklus"], n=pita[-1]["n"] + 1)
        else:
            pita.append({"bot": b, "dari": r["siklus"], "sampai": r["siklus"], "n": 1})
    k = max(1, -(-len(recs) // maks_titik))
    seri = [[r["siklus"], round(float(r["ekuitas"]), 2)] for r in recs[::k]]
    if seri[-1][0] != recs[-1]["siklus"]:
        seri.append([recs[-1]["siklus"], round(eq[-1], 2)])
    akhir = recs[-1]
    nilai = akhir.get("nilai_bot") or {}
    return {
        "mulai": recs[0]["siklus"], "siklus_terakhir": akhir["siklus"], "modal_awal": awal, "ekuitas": round(eq[-1], 2),
        "hasil_pct": round((eq[-1] / awal - 1) * 100, 3), "drawdown_maks_pct": round(dd * 100, 3), "fee": round(sum(fee_i), 2),
        "transaksi": sum(len(r.get("isi") or []) for r in recs), "siklus": len(recs),
        "siklus_berposisi": sum(1 for r in recs if (r["slot"] if "slot" in r else r.get("target"))),
        "seri": seri, "pita": pita,
        "per_bot": {b: {"siklus": x["siklus"], "hasil": round(x["pasar"] - x["fee"], 2), "fee": round(x["fee"], 2), "isi": x["isi"]}
                    for b, x in sorted(per_bot.items(), key=lambda kv: -kv[1]["siklus"])},
        "pipa": {"siklus": akhir["siklus"], "rumus": f"r{PARAMS2['v']}", "bot": akhir.get("bot"), "skor_bot": nilai.get(akhir.get("bot")) if akhir.get("bot") else None,
                 "dasar": akhir.get("dasar"), "instrumen": akhir.get("instrumen") or [],
                 # r4: "target" pipa = slot yang benar-benar terbuka (bobot notional bertanda), bukan target aturan
                 "target": ({x["aset"]: x["w"] for x in akhir["slot"]} if "slot" in akhir else {a: t.get("w") for a, t in (akhir.get("target") or {}).items()}),
                 "slot": akhir.get("slot"), "maks_slot": ms.PARAMS_SLOT["maks_posisi"],
                 "isi": len(akhir.get("isi") or []), "masuk": akhir.get("masuk") or [], "aktif": akhir.get("aktif") or akhir.get("masuk") or [],
                 "agen": [{"slug": a["agent"].split(":", 1)[-1], "status": a.get("status", "ok"), "kursi": a.get("kursi"),
                           "bot": (a.get("keputusan") or {}).get("bot")} for a in (agen or [])],
                 "root": (sik or {}).get("root"), "tx": (sik or {}).get("tx"), "status": (sik or {}).get("status")},
        "pita_keputusan": [{"siklus": r["siklus"], "bot": r.get("bot"), "dasar": r.get("dasar"), "instrumen": r.get("instrumen") or [],
                            "masuk": len(r.get("masuk") or []), "isi": r.get("isi") or [], "ekuitas": r.get("ekuitas"), "hash": r.get("hash")}
                           for r in reversed(recs[-n_pita:])],
    }


def kursi_now(kst: dict) -> Dict[str, str]:
    return {s: v["status"] for s, v in kst.get("kursi", {}).items()}
