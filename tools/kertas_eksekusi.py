"""Kertas-venue (P119 sebagian, F-D92): akurasi eksekusi diuji di KERTAS sebelum satu rupiah pun masuk venue.

Ledger paper resmi mengandaikan posisi dipegang tepat di penutupan bar (00:00Z) tanpa batas lot dan dengan biaya 7 bps. Kertas-venue mengulang
keputusan yang SAMA (target tick dari ledger resmi) seolah dieksekusi di venue sungguhan:
  - waktu: order paling cepat 2 menit sesudah komitnya ada di SignalAnchor (PRD R-E1; jadwal "komit") - atau andaian P99: 10 menit sesudah bar tutup
    (jadwal "p99", BUKAN kenyataan hari ini: komit resmi baru ada ±08:45Z);
  - harga: pembukaan menit itu dari kline 1m perp Binance Vision (berkas publik, bisa dihitung ulang siapa pun), dirugikan slippage model;
  - ukuran: bobot x ekuitas, dibulatkan ke lot, posisi di bawah min notional TIDAK dibuka (filter venue sungguhan, disimpan di catatan);
  - biaya: fee taker venue. Funding TIDAK dihitung di kedua sisi (kertas dan pembanding paper) - funding dinilai di settle ledger resmi.

Pembanding per hari bursa D+1 untuk tick bar D: return paper = sum w_a x (close_D+1 / close_D - 1) - turnover x 7 bps; return kertas = ekuitas
penutupan D+1 / ekuitas penutupan D - 1. Selisih = tracking error (bps). Satu catatan per tick, berantai hash, ditulis hanya bila semua bahan
ada (Vision 1m + bar penutupan D+1); bahan belum ada = TUNDA, tick sesudahnya tidak dilompati.

    python -X utf8 tools/kertas_eksekusi.py run [--venue binance aster] [--bot B1-TREND]   # tambah catatan baru ke ledger/kertas/
    python -X utf8 tools/kertas_eksekusi.py ringkas                                        # metrik vs ambang PRD §6
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import tempfile
import urllib.request
from typing import Callable, Dict, List, Optional, Sequence, Tuple

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from engine import eksekusi as ex, ledger                                      # noqa: E402
from engine.data import load_csv_dir                                          # noqa: E402
from engine.spec import SPECS, sha0x                                          # noqa: E402
import feed_bars                                                              # noqa: E402
import signal_commit as sc                                                    # noqa: E402
import venue_binance                                                          # noqa: E402

OUT = os.path.join(ROOT, "ledger", "kertas")
LEDGER = os.path.join(ROOT, "ledger", "paper")
BARS = os.path.join(ROOT, "ledger", "bars")
CACHE = os.path.join(tempfile.gettempdir(), "fabius-vision-1m")
DAY_MS = 86_400_000
PAPER_FEE_BPS = 7.0
MODALS = (2000.0, 10.0)
JADWAL = {"komit": "2 menit sesudah komit di SignalAnchor (kenyataan hari ini)", "p99": "10 menit sesudah bar tutup (ANDAIAN P99: tick + komit dari REST)"}
VENUES = {
    "binance": {"fee_bps": 5.0, "slip_bps": 1.0, "filters_url": "https://testnet.binancefuture.com/fapi/v1/exchangeInfo",
                "filters_label": "Binance USDⓈ-M TESTNET (prod terblokir dari jaringan builder; diganti prod saat diukur dari Railway, E2)"},
    "aster": {"fee_bps": 4.0, "slip_bps": 1.0, "filters_url": "https://fapi.asterdex.com/fapi/v1/exchangeInfo", "filters_label": "Aster prod (publik)"},
}
AMBANG = {"median_bps": 10.0, "p95_bps": 30.0, "min_hari": 10}
CADANGAN = 0.002                  # 0,2 % ekuitas tidak dipakai: fee + slippage tidak boleh membuat kas negatif (= leverage terselubung)
FILTER_DIR = os.path.join(OUT, "filter")


class Tunda(Exception):
    """Bahan belum ada (komit, kline 1m, atau bar penutupan): berhenti di tick ini, tidak melompat."""


# ---------------------------------------------------------------- bahan

def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "fabius-kertas/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def fetch_filters(venue: str, symbols: Sequence[str], now_iso: str, get: Callable[[str], dict] = _get_json) -> dict:
    """Ambil filter venue dari endpoint publik -> snapshot (ditulis ke ledger/kertas/filter/<venue>.json oleh perintah `filters`)."""
    f = venue_binance.parse_filters(get(VENUES[venue]["filters_url"]), symbols)
    return {"venue": venue, "diambil_utc": now_iso, "sumber": VENUES[venue]["filters_label"], "url": VENUES[venue]["filters_url"],
            "filters": {s: {"step": v.step, "min_qty": v.min_qty, "min_notional": v.min_notional} for s, v in sorted(f.items())}}


def venue_filters(venue: str, symbols: Sequence[str]) -> Dict[str, dict]:
    """Filter dari SNAPSHOT di repo (deterministik, bisa dihitung ulang; tidak bergantung jaringan runner). Snapshot hilang/kurang = Tunda."""
    p = os.path.join(FILTER_DIR, f"{venue}.json")
    if not os.path.exists(p):
        raise Tunda(f"snapshot filter {venue} belum ada: jalankan `kertas_eksekusi.py filters`")
    with open(p, encoding="utf-8") as f:
        snap = json.load(f)["filters"]
    miss = [s for s in symbols if s not in snap]
    if miss:
        raise Tunda(f"snapshot filter {venue} tanpa {miss}")
    return {s: snap[s] for s in symbols}


def minute_open(sym: str, t_ms: int, fetch: Callable[[str], Optional[bytes]] = feed_bars.http_get) -> float:
    """Harga buka kline 1m perp yang memuat t_ms (Binance Vision, berkas harian; belum terbit = Tunda)."""
    day = ledger.date_of(t_ms)
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"{sym}-1m-{day}.zip")
    if os.path.exists(path):
        blob = open(path, "rb").read()
    else:
        blob = fetch(f"{feed_bars.VISION}/futures/um/daily/klines/{sym}/1m/{sym}-1m-{day}.zip")
        if not blob:
            raise Tunda(f"kline 1m {sym} {day} belum terbit")
        with open(path, "wb") as f:
            f.write(blob)
    t0 = t_ms - t_ms % 60_000
    for row in feed_bars.parse_kline_zip(blob):
        if row[0] == t0:
            return float(row[1])
    raise Tunda(f"kline 1m {sym} {ledger.utc_iso(t0)} tidak ada di berkas {day}")


class Closes:
    def __init__(self, symbols: Sequence[str], bars_dir: str = BARS):
        md = load_csv_dir(bars_dir, list(symbols))
        self.c = {s: dict(zip(ser.t, ser.c)) for s, ser in md.perp.items()}

    def at(self, sym: str, bar_ms: int) -> float:
        v = self.c.get(sym, {}).get(bar_ms)
        if v is None:
            raise Tunda(f"bar {sym} {ledger.date_of(bar_ms)} belum ada di ledger/bars")
        return float(v)


def commit_time(tick: dict, bot: str, cv, committer: str) -> Optional[int]:
    """detik `committedAt` komit tick ini, None bila tick lebih tua dari kunci (tidak bisa dikomit). Komit belum ada = Tunda (T8 SK-E1)."""
    asof_s = sc.asof_s_of(tick)
    locked = cv.locked_at(committer, bot, SPECS[bot].sha())
    if locked == 0 or locked > asof_s:
        return None
    c = cv.get_commit(sc.commit_id(committer, bot, SPECS[bot].sha(), asof_s))
    if int(c["committer"], 16) == 0:
        raise Tunda(f"{bot} {tick['asof_date']}: komit belum ada di SignalAnchor - tidak ada eksekusi tanpa bukti (R-E1)")
    return int(c["committedAt"])


# ---------------------------------------------------------------- satu langkah (murni terhadap bahan)

def paper_return(w_new: Dict[str, float], w_old: Dict[str, float], r: Dict[str, float]) -> float:
    gross = sum(w * r[a] for a, w in w_new.items() if a in r)
    turn = sum(abs(w_new.get(a, 0.0) - w_old.get(a, 0.0)) for a in set(w_new) | set(w_old))
    return gross - turn * PAPER_FEE_BPS / 1e4


def step(prev: Optional[dict], tick: dict, w_old: Dict[str, float], *, venue: str, bot: str, modal: float, jadwal: str,
         commit_s: Optional[int], filters: Dict[str, dict], px_exec: Callable[[str, int], float], close: Callable[[str, int], float]) -> dict:
    """Satu catatan kertas untuk tick `tick`. `prev` = catatan sebelumnya (posisi, kas, ekuitas penutupan) atau None (mulai: kas = modal)."""
    v = VENUES[venue]
    bar = int(tick["asof"])
    bar_next = bar + DAY_MS
    targets = {a: float(w) for a, w in tick.get("targets", {}).items() if abs(float(w)) > 1e-12}
    pos = dict(prev["pos"]) if prev else {}
    cash = float(prev["kas"]) if prev else modal
    rec = {"type": "kertas", "venue": venue, "bot": bot, "modal_awal": modal, "jadwal": jadwal, "bar": tick["asof_date"],
           "tick_h": tick["h"], "filters_sha": sha0x(filters), "filters_sumber": v["filters_label"], "fee_bps": v["fee_bps"], "slip_bps": v["slip_bps"]}
    syms = sorted(set(targets) | set(pos))
    if commit_s is None:
        rec.update(status="SEBELUM_KUNCI", orders=[], dilewati=[], pos=pos, kas=cash, ekuitas=prev["ekuitas"] if prev else modal)
        return rec
    t_exec = (commit_s + 120) * 1000 if jadwal == "komit" else bar_next + 600_000
    t_exec -= t_exec % 60_000
    px = {s: px_exec(s, t_exec) for s in syms}
    equity_exec = cash + sum(q * px[a] for a, q in pos.items())
    fl = {a: ex.Filter(**f) for a, f in filters.items()}
    p = ex.plan(venue, bot, tick["asof_date"], targets, equity_exec * (1 - CADANGAN), pos, px, fl)
    problems = ex.guard(p, modal=equity_exec, universe=SPECS[bot].universe, price=px, long_only=bool(SPECS[bot].konstanta.get("long_only")))
    if problems:
        raise ValueError(f"pagar menolak rencana kertas {bot} {tick['asof_date']}: {problems}")
    fills = [(o, *ex.fill_paper(o, px[o.asset], v["fee_bps"], v["slip_bps"])) for o in p.orders]
    pos, cash = ex.apply_fills(pos, cash, fills)
    mark = {a: close(a, bar_next) for a in pos}
    eq_close = cash + sum(q * mark[a] for a, q in pos.items())
    eq_prev = float(prev["ekuitas"]) if prev else modal
    ref = {a: close(a, bar) for a in syms}
    r_next = {a: close(a, bar_next) / ref[a] - 1.0 for a in syms}
    ret_k = eq_close / eq_prev - 1.0
    ret_p = paper_return(targets, w_old, r_next)
    geser = [abs(px[o.asset] / ref[o.asset] - 1.0) * 1e4 for o in p.orders]
    rec.update(status="DIEKSEKUSI", komit_utc=ledger.utc_iso(commit_s * 1000), exec_utc=ledger.utc_iso(t_exec),
               orders=[{"aset": o.asset, "sisi": o.side, "qty": o.qty, "px": round(f_px, 10), "fee": round(fee, 10), "id": o.client_id, "alasan": o.alasan}
                       for o, f_px, fee in fills],
               dilewati=[list(x) for x in p.dilewati], pos={a: q for a, q in sorted(pos.items())}, kas=round(cash, 10),
               ekuitas=round(eq_close, 10), ret_kertas=round(ret_k, 12), ret_paper=round(ret_p, 12),
               tracking_bps=round((ret_k - ret_p) * 1e4, 4), geser_harga_bps=round(statistics.mean(geser), 4) if geser else 0.0,
               bobot_terpenuhi=round(sum(abs(q) * mark[a] for a, q in pos.items()) / eq_close, 6) if eq_close > 0 else 0.0)
    return rec


# ---------------------------------------------------------------- ledger kertas

def path_of(venue: str, bot: str, modal: float, jadwal: str) -> str:
    return os.path.join(OUT, venue, f"{bot}-{modal:g}-{jadwal}.jsonl")


def verify(recs: Sequence[dict]) -> List[str]:
    """Rantai hash utuh, bar naik ketat, kas tidak negatif (tanpa leverage terselubung)."""
    out, prev, last = [], ledger.ZERO, ""
    for i, r in enumerate(recs):
        if r.get("prev") != prev or r.get("h") != ledger.record_hash(r):
            out.append(f"#{i}: rantai hash putus")
        prev = r.get("h", "")
        if r.get("bar", "") <= last:
            out.append(f"#{i}: bar {r.get('bar')} tidak naik")
        last = r.get("bar", "")
        if float(r.get("kas", 0.0)) < -1e-9:
            out.append(f"#{i}: kas negatif {r.get('kas')}")
    return out


def run(venues: Sequence[str], bots: Sequence[str], cv, committer: str, log=print) -> int:
    added = 0
    for bot in bots:
        ticks = sorted((r for r in ledger.load(os.path.join(LEDGER, f"{bot}.jsonl")) if r["type"] == "tick"), key=lambda r: r["asof"])
        uni = list(SPECS[bot].universe)
        closes = Closes(uni)
        commits: Dict[str, Optional[int]] = {}
        for venue in venues:
            filt_now = None
            for modal in MODALS:
                for jadwal in JADWAL:
                    path = path_of(venue, bot, modal, jadwal)
                    recs = ledger.load(path)
                    bad = verify(recs)
                    if bad:
                        log(f"KERTAS RUSAK {path}: {bad[:3]} - tidak ditambah")
                        continue
                    done = {r["bar"] for r in recs}
                    w_old: Dict[str, float] = {}
                    prev = None
                    for r in recs:
                        prev = r
                    for tk in ticks:
                        if tk["asof_date"] in done:
                            w_old = {a: float(w) for a, w in tk.get("targets", {}).items()}
                            continue
                        try:
                            if tk["asof_date"] not in commits:
                                commits[tk["asof_date"]] = commit_time(tk, bot, cv, committer)
                            if filt_now is None:
                                filt_now = venue_filters(venue, uni)
                            rec = step(prev, tk, w_old, venue=venue, bot=bot, modal=modal, jadwal=jadwal, commit_s=commits[tk["asof_date"]],
                                       filters=filt_now, px_exec=minute_open, close=closes.at)
                        except Tunda as e:
                            log(f"TUNDA {venue} {bot} {modal:g} {jadwal} {tk['asof_date']}: {e}")
                            break
                        sealed = ledger.seal(rec, ledger.head(recs))
                        ledger.append(path, sealed, recs)
                        recs.append(sealed)
                        prev = sealed
                        w_old = {a: float(w) for a, w in tk.get("targets", {}).items()}
                        added += 1
                        log(f"+ {venue} {bot} modal {modal:g} {jadwal} bar {rec['bar']}: {rec['status']}"
                            + (f", {len(rec['orders'])} order, {len(rec['dilewati'])} dilewati, tracking {rec['tracking_bps']:+.1f} bps, "
                               f"geser harga {rec['geser_harga_bps']:.1f} bps, bobot terpenuhi {100 * rec['bobot_terpenuhi']:.1f} %" if rec["status"] == "DIEKSEKUSI" else ""))
    return added


def ringkas(log=print) -> dict:
    out = {}
    for venue in VENUES:
        for bot in ("B1-TREND",):
            for modal in MODALS:
                for jadwal in JADWAL:
                    recs = [r for r in ledger.load(path_of(venue, bot, modal, jadwal)) if r.get("status") == "DIEKSEKUSI"]
                    if not recs:
                        continue
                    tr = sorted(abs(r["tracking_bps"]) for r in recs)
                    med = statistics.median(tr)
                    p95 = tr[min(len(tr) - 1, math.ceil(0.95 * len(tr)) - 1)]
                    status = ("BELUM CUKUP HARI" if len(tr) < AMBANG["min_hari"] else
                              ("LULUS" if med <= AMBANG["median_bps"] and p95 <= AMBANG["p95_bps"] else "GAGAL"))
                    key = f"{venue}|{bot}|{modal:g}|{jadwal}"
                    out[key] = {"hari": len(tr), "median_bps": med, "p95_bps": p95, "status": status,
                                "bobot_terpenuhi_rata": statistics.mean(r["bobot_terpenuhi"] for r in recs),
                                "dilewati_rata": statistics.mean(len(r["dilewati"]) for r in recs)}
                    log(f"{key:34s} hari {len(tr):3d} | |tracking| median {med:7.1f} bps, p95 {p95:7.1f} bps | bobot terpenuhi "
                        f"{100 * out[key]['bobot_terpenuhi_rata']:5.1f} % | dilewati/tick {out[key]['dilewati_rata']:.1f} | {status}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("run", "ringkas", "filters"))
    ap.add_argument("--venue", nargs="+", default=list(VENUES))
    ap.add_argument("--bot", nargs="+", default=["B1-TREND"])
    a = ap.parse_args()
    if a.cmd == "ringkas":
        ringkas()
        return 0
    if a.cmd == "filters":
        import datetime as dt
        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        os.makedirs(FILTER_DIR, exist_ok=True)
        for venue in a.venue:
            snap = fetch_filters(venue, list(SPECS["B1-TREND"].universe), now)
            with open(os.path.join(FILTER_DIR, f"{venue}.json"), "w", encoding="utf-8", newline="\n") as f:
                json.dump(snap, f, indent=1, sort_keys=True)
                f.write("\n")
            mx = max(v["min_notional"] for v in snap["filters"].values())
            print(f"{venue}: {len(snap['filters'])} simbol, min notional maks {mx:g} -> modal B1 penuh >= {mx / 0.0625:,.0f} ({snap['sumber']})")
        return 0
    import worker_watch as ww
    with open(os.path.join(ROOT, "deployments", "97.json"), encoding="utf-8") as f:
        d = json.load(f)
    cv = ww.ChainView(ww.Reader(), d["contracts"]["SignalAnchor"], d["contracts"]["LockRegistry"])
    n = run(a.venue, a.bot, cv, d["m3"]["committer"])
    print(f"kertas: {n} catatan baru")
    ringkas()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
