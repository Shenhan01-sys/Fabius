"""Mode bayangan tahap 2+3 (P99/P100; F-D83): tick dari REST Binance beberapa menit sesudah penutupan bar, DIBANDINGKAN dengan tick resmi rantai GitHub
(dari zip Vision, ±9-10 jam kemudian). Tidak menulis ledger resmi, tidak menyentuh chain, tanpa kunci: hasilnya log + berkas keadaan lokal.

Per hari (bar D tertutup 00:00Z hari D+1):
  1. sinkron ledger + bar resmi dari GitHub (clone sparse yang sama dengan worker);
  2. baca REST paling cepat +2 menit sesudah penutupan (P98: bacaan pertama belum final), lalu baca lagi >= 60 s kemudian; diterima hanya bila dua
     bacaan berurutan IDENTIK (SK-R1). Masih berubah sesudah MAX_READS = menyerah untuk putaran itu (TUNDA, dicatat), dicoba lagi putaran berikutnya;
  3. salinan bar resmi + baris REST: kline perp/spot (divalidasi seperti `feed_bars`) dan ESTIMASI funding dari indeks premium 1m REST (rumus
     `engine/funding_est.py`). Funding AKTUAL sengaja TIDAK ditulis (SK-R2): `update_funding_est` mulai sesudah peristiwa aktual terakhir, jadi aktual
     yang masuk duluan membuat estimasi hari itu tidak pernah terbentuk dan tick B3 ditolak. Rantai resmi juga belum punya aktual (zip bulanan);
  4. `ledger.make_tick` (fungsi yang sama dengan `paper_tick`) di atas salinan itu -> tick bayangan, dicatat + disimpan;
  5. tiap putaran: tick bayangan yang tick resminya sudah ada dibandingkan (targets, data_hash, signal_ids, n_aset) -> IDENTIK / BEDA / RESMI GAP, dan
     baris REST dibandingkan dengan baris Vision resmi (kline 5 kolom, estimasi funding) -> beda = ALARM dicatat, tidak ada yang diubah (SK-R4).

Railway (service `fabius-probe`, tanpa variabel rahasia):  FABIUS_JOB=shadow_tick  (lalu `railway logs --service fabius-probe`)
Lokal:  python -X utf8 tools/shadow_tick.py --once      (fapi tertutup dari laptop builder dan runner GitHub; jalannya dari Railway Singapura)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
import time
from typing import Callable, Dict, List, Optional, Sequence, Tuple

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from engine import funding_est as fest, ledger         # noqa: E402
from engine.freshness import StaleBars                 # noqa: E402
from engine.series import DAY_MS                       # noqa: E402
from engine.spec import PERP_UNIVERSE, SPECS           # noqa: E402

FAPI = "https://fapi.binance.com"
SPOT = "https://api.binance.com"
BOTS = [b.strip() for b in os.environ.get("FABIUS_BOTS", "B1-TREND,B3-CARRY").split(",") if b.strip()]
WORKDIR = os.environ.get("SHADOW_WORKDIR", os.path.join("/tmp", "fabius-shadow-ledger"))
STATE_DIR = os.environ.get("SHADOW_STATE", os.path.join("/tmp", "fabius-shadow"))
POLL_S = int(os.environ.get("POLL_S", "600"))
FIRST_READ_S = 120            # P98: bar hadir <= 11 s, tetapi berubah sampai +15 s; jarak aman
READ_GAP_S = 60
MAX_READS = 6
PROBLEM_WAIT_S = 3600         # baris REST yang hilang/tidak sah: TUNDA selama jam pertama, sesudahnya tick dibuat dan make_tick yang memutuskan
TICK_FIELDS = ("targets", "data_hash", "signal_ids", "n_aset")
KL_FIELDS = ("o", "h", "l", "c", "v")


# ---------------------------------------------------------------- sumber REST
class RestSource:
    """Kline harian tertutup (perp fapi / spot api) dan close indeks premium 1m (fapi) - hanya baca, tanpa kunci."""

    def __init__(self, rest=None):
        if rest is None:
            import rest_vs_vision
            rest = rest_vs_vision.Rest()
        self.rest = rest

    def klines(self, kind: str, sym: str, t_from: int, now_ms: int) -> List[tuple]:
        base, path, limit = (FAPI, "/fapi/v1/klines", 1500) if kind == "fut" else (SPOT, "/api/v3/klines", 1000)
        got = self.rest.klines(base, path, sym, t_from, now_ms, limit)
        return [(t, *got[t]) for t in sorted(got)]

    def premium(self, sym: str, t_from: int, t_to: int, now_ms: int) -> Dict[int, float]:
        out: Dict[int, float] = {}
        cur = t_from
        while cur < t_to:
            rows = self.rest.get(f"{FAPI}/fapi/v1/premiumIndexKlines?symbol={sym}&interval=1m&startTime={cur}&endTime={t_to - 1}&limit=1500")
            if not rows:
                break
            for r in rows:
                if int(r[6]) < now_ms and t_from <= int(r[0]) < t_to:
                    out[int(r[0])] = float(r[4])
            if len(rows) < 1500:
                break
            cur = int(rows[-1][0]) + 60_000
        return out


# ---------------------------------------------------------------- bacaan (murni terhadap `src`)
def est_start(bars: str, sym: str) -> Optional[int]:
    """Hari pertama yang estimasinya belum ditulis (aturan `feed_bars.update_funding_est`): sesudah peristiwa aktual/estimasi terakhir. None = tak bisa."""
    import feed_bars as fb
    la, le = fb.last_t(os.path.join(bars, f"fund_{sym}.csv")), fb.last_t(os.path.join(bars, f"fund_est_{sym}.csv"))
    if la is None:
        return None
    base = max(la, le or 0)
    nxt = (base // fest.H8_MS) * fest.H8_MS + fest.H8_MS
    return None if nxt % DAY_MS else nxt


def series_files(bars: str) -> List[Tuple[str, str]]:
    out = []
    for sym in PERP_UNIVERSE:
        for kind, name in (("fut", f"fut_{sym}_1d.csv"), ("spot", f"spot_{sym}_1d.csv")):
            if os.path.isfile(os.path.join(bars, name)):
                out.append((kind, sym))
        if os.path.isfile(os.path.join(bars, f"fund_{sym}.csv")):
            out.append(("prem", sym))
    return out


def read_snapshot(src, bars: str, day_ms: int, now_ms: int) -> dict:
    """Semua nilai REST yang dibutuhkan untuk memperpanjang bar resmi sampai bar `day_ms`: {"fut:SYM": [[t,o,h,l,c,v],..], "prem:SYM": [[t,close],..]}."""
    import feed_bars as fb
    snap: dict = {}
    for kind, sym in series_files(bars):
        if kind in ("fut", "spot"):
            lt = fb.last_t(os.path.join(bars, f"{kind}_{sym}_1d.csv"))
            if lt is not None and lt < day_ms:
                snap[f"{kind}:{sym}"] = [list(r) for r in src.klines(kind, sym, lt + DAY_MS, now_ms) if r[0] <= day_ms]
        else:
            nxt = est_start(bars, sym)
            if nxt is not None and nxt <= day_ms:
                m = src.premium(sym, nxt - fest.H8_MS, day_ms + 2 * fest.H8_MS, now_ms)
                snap[f"prem:{sym}"] = [[t, m[t]] for t in sorted(m)]
    return snap


def digest(snap: dict) -> str:
    return "0x" + hashlib.sha256(json.dumps(snap, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read_final(src, bars: str, day_ms: int, now_fn: Callable[[], int], sleep: Callable[[float], None], log: Callable[[str], None],
               max_reads: int = MAX_READS, gap_s: int = READ_GAP_S) -> Optional[Tuple[dict, int]]:
    """SK-R1: baca, tunggu >= gap_s, baca lagi; diterima hanya bila dua bacaan berurutan identik. -> (snapshot, jumlah baca) atau None (TUNDA)."""
    prev = read_snapshot(src, bars, day_ms, now_fn())
    for n in range(2, max_reads + 1):
        sleep(gap_s)
        cur = read_snapshot(src, bars, day_ms, now_fn())
        if digest(cur) == digest(prev):
            return cur, n
        changed = sorted(k for k in set(cur) | set(prev) if cur.get(k) != prev.get(k))
        log(f"  bacaan {n} beda dari bacaan {n - 1} di {len(changed)} deret ({', '.join(changed[:4])}); baca lagi")
        prev = cur
    log(f"  TUNDA: {max_reads} bacaan, belum ada dua yang identik")
    return None


# ---------------------------------------------------------------- baris + salinan bar
def build_rows(snap: dict, bars: str, day_ms: int, est_fn: Callable = None) -> Tuple[Dict[str, list], List[str]]:
    """Baris yang akan ditambahkan per berkas, dengan aturan `feed_bars`: hari berurutan tanpa loncatan, bar divalidasi, estimasi hanya hari LENGKAP.
    -> ({"fut:SYM": [rows], "spot:SYM": [rows], "fest:SYM": [(t, rate)]}, masalah). Deret yang bermasalah berhenti di situ (tidak ada baris sesudah lubang)."""
    import feed_bars as fb
    est_fn = est_fn or fest.estimate_day
    rows: Dict[str, list] = {}
    problems: List[str] = []
    for key in sorted(snap):
        kind, sym = key.split(":")
        if kind in ("fut", "spot"):
            have = {int(r[0]): tuple(r) for r in snap[key]}
            t = fb.last_t(os.path.join(bars, f"{kind}_{sym}_1d.csv")) + DAY_MS
            out = []
            while t <= day_ms:
                r = have.get(t)
                bad = "tidak ada di REST" if r is None else fb._valid_bar((int(r[0]), *map(float, r[1:6])), t)
                if bad:
                    problems.append(f"{kind} {sym} {ledger.date_of(t)}: {bad}")
                    break
                out.append((int(r[0]), *map(float, r[1:6])))
                t += DAY_MS
            rows[key] = out
        else:
            minutes = {int(t): float(c) for t, c in snap[key]}
            d, out = est_start(bars, sym), []
            while d is not None and d <= day_ms:
                ev = est_fn(sym, minutes, d)
                if ev is None:
                    problems.append(f"estimasi {sym} {ledger.date_of(d)}: menit indeks premium hilang")
                    break
                out.extend(ev)
                d += DAY_MS
            rows[f"fest:{sym}"] = out
    return rows, problems


def make_shadow_bars(official: str, rows: Dict[str, list], out: str) -> str:
    """Salinan bar resmi + baris REST. Berkas funding AKTUAL (`fund_<SYM>.csv`) disalin apa adanya dan tidak pernah ditambah (SK-R2)."""
    if os.path.exists(out):
        shutil.rmtree(out)
    shutil.copytree(official, out)
    for key, rs in rows.items():
        if not rs:
            continue
        kind, sym = key.split(":")
        path = os.path.join(out, f"fund_est_{sym}.csv" if kind == "fest" else f"{kind}_{sym}_1d.csv")
        new_file = not os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            if new_file and kind == "fest":
                w.writerow(["t", "rate"])
            for r in rs:
                w.writerow(list(r))
    return out


def shadow_ticks(ledger_dir: str, bars: str, bots: Sequence[str], now_ms: int) -> Dict[str, dict]:
    """Tick bayangan per bot untuk bar tertutup terakhir: {"tick": catatan} atau {"tolak": alasan}. Pandangan data = sama dengan `paper_tick.tick_bot`."""
    from paper_tick import Views
    views = Views(bars)
    out: Dict[str, dict] = {}
    for bot in bots:
        spec = SPECS[bot]
        recs = ledger.load(os.path.join(ledger_dir, f"{bot}.jsonl"))
        if not recs:
            out[bot] = {"tolak": "belum ada ledger resmi"}
            continue
        try:
            out[bot] = {"tick": ledger.make_tick(spec, views.get("targets" if spec.method == "B3-CARRY" else "actual"), now_ms, recs[0])}
        except (StaleBars, ledger.LedgerError) as e:
            out[bot] = {"tolak": str(e)[:240]}
    return out


# ---------------------------------------------------------------- pembandingan
def compare_tick(shadow: dict, official: Optional[dict]) -> Tuple[str, List[str]]:
    if official is None:
        return "MENUNGGU", []
    if official["type"] == "gap":
        return "RESMI GAP", []
    diff = [k for k in TICK_FIELDS if shadow.get(k) != official.get(k)]
    return ("IDENTIK" if not diff else "BEDA"), diff


def compare_rows(rows: Dict[str, list], official_bars: str) -> dict:
    """Baris REST vs baris resmi (Vision) pada waktu yang sama. Kline: 5 kolom persis; estimasi funding: rate persis. Baris resmi yang belum ada = menunggu."""
    import rest_vs_vision as rvv
    res = {"sama": 0, "beda_harga": [], "beda_volume": 0, "beda_estimasi": [], "menunggu": 0}
    for key, rs in rows.items():
        kind, sym = key.split(":")
        if kind == "fest":
            p = os.path.join(official_bars, f"fund_est_{sym}.csv")
            off = dict(rvv.read_funding_csv(p)) if os.path.isfile(p) else {}
            for t, r in rs:
                if t not in off:
                    res["menunggu"] += 1
                elif off[t] == r:
                    res["sama"] += 1
                else:
                    res["beda_estimasi"].append(f"{sym} {ledger.utc_iso(t)} rest {r!r} resmi {off[t]!r}")
            continue
        off = rvv.read_klines_csv(os.path.join(official_bars, f"{kind}_{sym}_1d.csv"))
        for r in rs:
            o = off.get(int(r[0]))
            if o is None:
                res["menunggu"] += 1
                continue
            bad = [(f, a, b) for f, a, b in zip(KL_FIELDS, r[1:6], o) if a != b]
            if not bad:
                res["sama"] += 1
            elif any(f != "v" for f, _, _ in bad):
                res["beda_harga"] += [f"{kind} {sym} {ledger.date_of(int(r[0]))} {f}: rest {a!r} resmi {b!r}" for f, a, b in bad if f != "v"]
            else:
                res["beda_volume"] += 1
    return res


# ---------------------------------------------------------------- keadaan + putaran
class Shadow:
    def __init__(self, workdir: str = WORKDIR, state_dir: str = STATE_DIR, src=None, bots: Sequence[str] = BOTS,
                 log: Callable[[str], None] = print, sleep: Callable[[float], None] = time.sleep, now_fn: Callable[[], int] = None,
                 est_fn: Callable = None):
        self.workdir, self.state_dir, self.bots = workdir, state_dir, list(bots)
        self.est_fn = est_fn
        self.src = src
        self.log, self.sleep = log, sleep
        self.now_fn = now_fn or (lambda: int(time.time() * 1000))
        os.makedirs(state_dir, exist_ok=True)
        self.path = os.path.join(state_dir, "state.json")
        self.state = {"hari": {}}
        if os.path.isfile(self.path):
            with open(self.path, encoding="utf-8") as f:
                self.state = json.load(f)

    def save(self) -> None:
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.state, f, sort_keys=True)
        os.replace(tmp, self.path)

    def due(self, now_ms: int) -> Optional[int]:
        """Bar yang harus dibayangkan sekarang: bar tertutup terakhir, belum diterima, sudah >= +2 menit, masih di bawah batas 12 jam."""
        d = ledger.last_closed_bar(now_ms)
        lag = now_ms - (d + DAY_MS)
        if ledger.date_of(d) in self.state["hari"] or lag < FIRST_READ_S * 1000 or lag > ledger.MAX_LAG_S * 1000:
            return None
        return d

    def run_day(self, d: int) -> bool:
        bars, led = os.path.join(self.workdir, "ledger", "bars"), os.path.join(self.workdir, "ledger", "paper")
        date = ledger.date_of(d)
        t_first = self.now_fn()
        got = read_final(self.src, bars, d, self.now_fn, self.sleep, self.log)
        if got is None:
            return False
        snap, n_reads = got
        rows, problems = build_rows(snap, bars, d, self.est_fn)
        if problems:
            if self.now_fn() - (d + DAY_MS) < PROBLEM_WAIT_S * 1000:
                self.log(f"bayangan {date}: TUNDA - " + "; ".join(problems[:4]))
                return False
            self.log(f"bayangan {date}: {len(problems)} deret berhenti (diteruskan; make_tick yang memutuskan) - " + "; ".join(problems[:4]))
        n_rest = sum(len(v) for v in rows.values())
        if n_rest == 0:
            self.log(f"bayangan {date}: bar resmi sudah memuat hari ini - bayangan TIDAK menguji REST (dicatat, bukan bukti)")
        sb = make_shadow_bars(bars, rows, os.path.join(self.state_dir, "bars"))
        now = self.now_fn()
        ticks = shadow_ticks(led, sb, self.bots, now)
        day = {"bar": d, "baca_pertama_utc": ledger.utc_iso(t_first), "diterima_utc": ledger.utc_iso(now), "n_baca": n_reads, "digest": digest(snap),
               "n_baris": {k: len(v) for k, v in rows.items() if v}, "uji_rest": n_rest > 0,
               "masalah": problems[:20], "bot": {}}
        for bot, r in ticks.items():
            if "tick" in r:
                tk = r["tick"]
                day["bot"][bot] = {"tick": {k: tk[k] for k in TICK_FIELDS}, "lag_s": tk["lag_s"], "vonis": None}
                self.log(f"bayangan {bot} {date}: tick {tk['lag_s']} s sesudah penutupan | {len(tk['targets'])} aset | {len(tk['signal_ids'])} sinyal | "
                         f"data_hash {tk['data_hash'][:14]}… | {n_reads} bacaan")
            else:
                day["bot"][bot] = {"tolak": r["tolak"], "vonis": None}
                self.log(f"bayangan {bot} {date}: DITOLAK - {r['tolak']}")
        with open(os.path.join(self.state_dir, f"baris-{date}.json"), "w", encoding="utf-8") as f:
            json.dump(rows, f)
        self.state["hari"][date] = day
        self.save()
        return True

    def compare_pending(self) -> List[str]:
        bars, led = os.path.join(self.workdir, "ledger", "bars"), os.path.join(self.workdir, "ledger", "paper")
        out = []
        for date, day in sorted(self.state["hari"].items()):
            for bot, b in day["bot"].items():
                if b.get("vonis") not in (None, "MENUNGGU"):
                    continue
                recs = ledger.load(os.path.join(led, f"{bot}.jsonl"))
                off = next((r for r in recs if r["type"] in ("tick", "gap") and r["asof"] == day["bar"]), None)
                if off is None:
                    continue
                if "tolak" in b:
                    v, diff = ("RESMI ADA, BAYANGAN DITOLAK" if off["type"] == "tick" else "SAMA-SAMA TIDAK ADA"), []
                else:
                    v, diff = compare_tick(b["tick"], off)
                b["vonis"], b["beda"] = v, diff
                if off is not None and off["type"] == "tick":
                    b["lag_resmi_s"] = off["lag_s"]
                line = (f"VONIS bayangan {bot} {date}: {v}" + (f" ({', '.join(diff)})" if diff else "") +
                        (f" | bayangan {b['lag_s'] / 60:.1f} menit vs resmi {off['lag_s'] / 3600:.1f} jam sesudah penutupan" if "lag_s" in b and off and off["type"] == "tick" else ""))
                self.log(line)
                out.append(line)
            p = os.path.join(self.state_dir, f"baris-{date}.json")
            if not day.get("baris_vonis") and os.path.isfile(p):
                with open(p, encoding="utf-8") as f:
                    rows = {k: [tuple(x) for x in v] for k, v in json.load(f).items()}
                c = compare_rows(rows, bars)
                if c["menunggu"] == 0:
                    alarm = c["beda_harga"] or c["beda_estimasi"]
                    day["baris_vonis"] = "ALARM" if alarm else "SAMA"
                    line = (f"VONIS baris REST {date}: {'ALARM - ' if alarm else ''}{c['sama']} sama persis, beda harga {len(c['beda_harga'])}, "
                            f"beda estimasi funding {len(c['beda_estimasi'])}, beda volume saja {c['beda_volume']}")
                    self.log(line)
                    for x in (c["beda_harga"] + c["beda_estimasi"])[:20]:
                        self.log("  ! " + x)
                    out.append(line)
        self.save()
        return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Mode bayangan tahap 2+3: tick dari REST, dibandingkan dengan tick resmi.")
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()
    import operator_loop as ol
    sh = Shadow(src=RestSource(), log=ol.log)
    ol.log(f"bayangan mulai | bot {','.join(sh.bots)} | baca pertama +{FIRST_READ_S}s, dua bacaan identik >= {READ_GAP_S}s | "
           f"region {os.environ.get('RAILWAY_REPLICA_REGION', '?')} | keadaan {len(sh.state['hari'])} hari")
    last_beat = 0.0
    while True:
        try:
            head = ol.sync(sh.workdir)
            now = sh.now_fn()
            d = sh.due(now)
            if d is not None:
                sh.run_day(d)
            sh.compare_pending()
            if time.time() - last_beat >= 6 * 3600:
                ol.log(f"detak bayangan: repo {head[:10]} | hari tercatat {len(sh.state['hari'])}")
                last_beat = time.time()
        except Exception as e:  # noqa: BLE001 - putaran gagal dicatat, diulang (SK-W1)
            ol.log(f"putaran bayangan GAGAL: {type(e).__name__}: {str(e)[:240]}")
        if a.once:
            return 0
        now = sh.now_fn()
        next_read = ledger.last_closed_bar(now) + 2 * DAY_MS + FIRST_READ_S * 1000
        time.sleep(max(5.0, min(POLL_S, (next_read - now) / 1000 + 1)))


if __name__ == "__main__":
    raise SystemExit(main())
