"""Penulis ledger eksekusi (P119, epik 10 R-E10, F-D94): umpan Gist eksekutor -> DIPERIKSA -> `ledger/eksekusi/<venue>/` berantai hash + metrik §6.

Dijalankan rantai GitHub `paper-ledger.yml` (penulis tunggal ledger/) tiap putaran 5 menit. Runner GitHub tidak bisa membaca Binance sendiri (HTTP 451,
terukur 4 Okt), jadi eksekutor di Railway menyusun laporan dari venue dan menaruhnya di Gist publik (`tools/exec_feed.py`). Di sini laporan itu TIDAK
dipercaya begitu saja:

  integritas (gagal = baris DITOLAK, tidak ditulis, ALARM)   id tiap order = `ex.client_id(venue, bot, bar, aset, sisi)` dihitung ulang; bot dikenal;
                                                             bar punya tick di ledger paper; bar naik ketat
  keselamatan (gagal = DITULIS dengan `pelanggaran`, ALARM)  aset di universe; waktu kirim tiap order SESUDAH `committedAt` komit bar itu yang dibaca
                                                             SENDIRI dari SignalAnchor (R-E1); bot long-only tidak short; notional posisi <= modal (1x)

Metrik per catatan (deterministik dari bahan publik): fee bps nyata; slippage = harga isi vs harga tengah saat rencana (bila ada); geser = harga isi vs
penutupan bar (sama dengan `geser_harga_bps` kertas); selisih vs isi KERTAS bar yang sama (ledger/kertas, modal + jadwal komit yang sama) = seberapa
akurat model kertas; latensi komit -> isi terakhir; bobot terpenuhi. Tracking error harian dari tanda ekuitas 00:00Z: (Δekuitas / modal) - return paper
(definisi sama dengan kertas: funding tidak ada di pembanding paper, tetapi ADA di ekuitas venue - dicatat, bukan disembunyikan).

    python -X utf8 tools/eksekusi_ledger.py run        # tarik umpan, periksa, tulis (exit 0 / 1 ALARM / 3 umpan tak terbaca)
    python -X utf8 tools/eksekusi_ledger.py periksa    # penjaga luar: tick dikomit tanpa laporan eksekusi > 60 menit = ALARM
    python -X utf8 tools/eksekusi_ledger.py ringkas    # metrik vs ambang PRD §6
    python -X utf8 tools/eksekusi_ledger.py verify     # rantai hash + urutan
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import statistics
import sys
import time
import urllib.error
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
from engine.spec import SPECS, sha0x                                          # noqa: E402
import exec_feed as xf                                                        # noqa: E402
import signal_commit as sc                                                    # noqa: E402

OUT = os.path.join(ROOT, "ledger", "eksekusi")
PAPER = os.path.join(ROOT, "ledger", "paper")
KERTAS = os.path.join(ROOT, "ledger", "kertas")
OWNER = "Shenhan01-sys"                       # pemilik repo = pemilik Gist umpan (token builder)
API = "https://api.github.com"
VENUE_RE = re.compile(r"^binance-(demo|testnet|live)$")
TENGGANG_S = 3600                             # eksekutor jalan tiap 5 menit sesudah komit; 60 menit tanpa laporan = ALARM (PRD §4 penjaga luar)
MODAL_TOL = 0.01                              # harga bergerak antara rencana dan isi: 1 % kelonggaran sebelum disebut melewati modal
AMBANG = {"slip_median_bps": 5.0, "fee_max_bps": 7.0, "latensi_p95_s": 600, "te_median_bps": 10.0, "te_p95_bps": 30.0, "min_hari": 20}


class Unreadable(Exception):
    """Umpan atau chain tak terbaca: TUNDA, bukan vonis (T8 SK-E17)."""


# ---------------------------------------------------------------- umpan (Gist publik)

def _get(url: str, token: Optional[str]) -> Tuple[int, object]:
    h = {"Accept": "application/vnd.github+json", "User-Agent": "fabius-eksekusi-ledger/1.0"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as r:
            body = r.read().decode()
            return r.status, (json.loads(body) if body[:1] in "[{" else body)
    except urllib.error.HTTPError as e:
        return e.code, {}
    except Exception as e:  # noqa: BLE001
        raise Unreadable(f"{url.split('?')[0]}: tak terjangkau ({type(e).__name__})") from None


def read_feed(get: Callable[[str, Optional[str]], Tuple[int, object]] = _get, token: Optional[str] = None,
              gist_id: Optional[str] = None) -> Tuple[Optional[str], List[str]]:
    """(gist id, baris JSON). Gist belum ada = (None, []) - umpan belum dinyalakan builder (H7), bukan galat."""
    if not gist_id:
        code, body = get(f"{API}/users/{OWNER}/gists?per_page=100", token)
        if code != 200 or not isinstance(body, list):
            raise Unreadable(f"daftar gist {OWNER}: HTTP {code}")
        hit = [g for g in body if g.get("description") == xf.FEED_DESC]
        if not hit:
            return None, []
        gist_id = str(hit[0]["id"])
    code, g = get(f"{API}/gists/{gist_id}", token)
    if code != 200 or not isinstance(g, dict):
        raise Unreadable(f"gist {gist_id}: HTTP {code}")
    lines: List[str] = []
    for name in sorted((g.get("files") or {})):
        if not re.match(r"^fabius-exec-\d{4}-\d{2}\.jsonl$", name):
            continue
        f = g["files"][name]
        content = f.get("content") or ""
        if f.get("truncated"):
            code, raw = get(f["raw_url"], token)
            if code != 200 or not isinstance(raw, str):
                raise Unreadable(f"{name} terpotong dan raw tak terbaca: HTTP {code}")
            content = raw
        lines += [x for x in content.splitlines() if x.strip()]
    return gist_id, lines


# ---------------------------------------------------------------- bahan publik

def ticks_of(bot: str, paper_dir: str = PAPER) -> Dict[str, dict]:
    return {r["asof_date"]: r for r in ledger.load(os.path.join(paper_dir, f"{bot}.jsonl")) if r.get("type") == "tick"}


def kertas_fills(venue: str, bot: str, modal: float, bar: str, kertas_dir: str = KERTAS) -> Dict[Tuple[str, str], float]:
    """Harga isi kertas (venue nyata yang sama, modal sama, jadwal komit) untuk bar ini -> {(aset, sisi): px}. Tidak ada = {}."""
    base = venue.split("-")[0]
    p = os.path.join(kertas_dir, base, f"{bot}-{modal:g}-komit.jsonl")
    for r in ledger.load(p):
        if r.get("bar") == bar and r.get("status") == "DIEKSEKUSI":
            return {(o["aset"], o["sisi"]): float(o["px"]) for o in r.get("orders", [])}
    return {}


def bps(a: float, b: float) -> Optional[float]:
    return round((a / b - 1.0) * 1e4, 4) if a and b else None


def worse(side: str, x: Optional[float]) -> Optional[float]:
    """Bertanda: positif = lebih buruk bagi kita (beli lebih mahal / jual lebih murah)."""
    return None if x is None else (x if side == "BUY" else -x)


# ---------------------------------------------------------------- periksa satu laporan

def check(rec: dict, ticks: Dict[str, dict], commit_s: Optional[int]) -> Tuple[List[str], List[str]]:
    """(masalah integritas -> TOLAK, pelanggaran keselamatan -> UNGKAPKAN). `commit_s` dibaca dari chain; None = tidak ada komit."""
    integ: List[str] = []
    viol: List[str] = []
    venue, bot, bar = rec.get("venue", ""), rec.get("bot", ""), rec.get("bar", "")
    if not VENUE_RE.match(str(venue)):
        integ.append(f"venue tidak dikenal: {venue}")
    if bot not in SPECS:
        integ.append(f"bot tidak dikenal: {bot}")
        return integ, viol
    if bar not in ticks:
        integ.append(f"bar {bar} tidak punya tick di ledger paper {bot}")
    spec = SPECS[bot]
    uni = set(spec.universe)
    for o in rec.get("orders", []):
        want = ex.client_id(venue, bot, bar, o.get("aset", ""), o.get("sisi", ""))
        if o.get("id") != want:
            integ.append(f"id order {o.get('aset')} {o.get('sisi')} bukan hash (venue, bot, bar, aset, sisi): {o.get('id')}")
        if o.get("aset") not in uni:
            viol.append(f"{o.get('aset')}: di luar universe {bot}")
        if commit_s is None:
            viol.append(f"{o.get('aset')}: order tanpa komit di SignalAnchor (R-E1)")
        elif int(o.get("t_kirim") or 0) <= commit_s * 1000:
            viol.append(f"{o.get('aset')}: dikirim {ledger.utc_iso(int(o.get('t_kirim') or 0))} SEBELUM komit {ledger.utc_iso(commit_s * 1000)} (R-E1)")
    if spec.konstanta.get("long_only"):
        viol += [f"{a}: posisi short {q} pada bot long-only" for a, q in (rec.get("posisi") or {}).items() if float(q) < -1e-12]
    return integ, viol


def enrich(rec: dict, tick: dict, commit_s: Optional[int], close: Callable[[str, int], float], kertas: Dict[Tuple[str, str], float],
           integ_line_h: str) -> dict:
    """Catatan ledger: baris umpan + metrik yang dihitung DI SINI dari bahan publik (ledger bars, kertas, chain)."""
    bar_ms = int(tick["asof"])
    orders = []
    for o in rec.get("orders", []):
        px, qty, side = float(o.get("px") or 0), float(o.get("qty") or 0), o.get("sisi")
        try:
            ref = close(o["aset"], bar_ms)
        except Exception:  # noqa: BLE001 - bar belum ada di ledger/bars: metrik itu kosong, bukan dikarang
            ref = None
        notional = qty * px
        orders.append(dict(o, notional=round(notional, 8), fee_bps=round(float(o.get("fee") or 0) / notional * 1e4, 4) if notional else None,
                           ref_tutup=ref, geser_bps=worse(side, bps(px, ref) if ref else None),
                           slip_bps=worse(side, bps(px, float(o["px_rencana"])) if o.get("px_rencana") else None),
                           kertas_px=kertas.get((o["aset"], side)),
                           selisih_kertas_bps=worse(side, bps(px, kertas[(o["aset"], side)]) if (o["aset"], side) in kertas else None)))
    filled = [o for o in orders if o["qty"] > 0]
    modal = float(rec.get("modal") or 0)
    pos = rec.get("posisi") or {}
    last_px = {o["aset"]: float(o["px"]) for o in filled}
    gross = 0.0
    for a, q in pos.items():
        p = last_px.get(a)
        if p is None:
            try:
                p = close(a, bar_ms)
            except Exception:  # noqa: BLE001
                p = 0.0
        gross += abs(float(q)) * p
    out = {k: v for k, v in rec.items() if k not in ("orders", "v", "komit_s")}
    out.update(type="eksekusi", tick_h=tick.get("h"), umpan_h=integ_line_h, komit_s_laporan=rec.get("komit_s"),
               komit_utc=ledger.utc_iso(commit_s * 1000) if commit_s else None, orders=orders,
               n_order=len(orders), notional=round(sum(o["notional"] for o in orders), 8), fee=round(sum(float(o.get("fee") or 0) for o in orders), 10),
               latensi_s=(max(int(o.get("t_isi") or 0) for o in filled) // 1000 - commit_s) if (filled and commit_s) else None,
               bobot_terpenuhi=round(gross / modal, 6) if (modal and rec.get("posisi") is not None) else None)
    return out


# ---------------------------------------------------------------- ledger

def path_of(venue: str, name: str, out_dir: str = OUT) -> str:
    return os.path.join(out_dir, venue, f"{name}.jsonl")


def verify(recs: Sequence[dict]) -> List[str]:
    out, prev, last = [], ledger.ZERO, ""
    for i, r in enumerate(recs):
        if r.get("prev") != prev or r.get("h") != ledger.record_hash(r):
            out.append(f"#{i}: rantai hash putus")
        prev = r.get("h", "")
        k = r.get("bar") or r.get("tanggal") or ""
        if k <= last:
            out.append(f"#{i}: {k} tidak naik")
        last = k
    return out


def run(lines: Sequence[str], cv, committer: str, close: Callable[[str, int], float], out_dir: str = OUT, paper_dir: str = PAPER,
        kertas_dir: str = KERTAS, log=print) -> Tuple[int, List[str]]:
    """Tambahkan baris umpan baru ke ledger. -> (jumlah ditulis, ALARM). Satu galat baca chain = Unreadable (berhenti, tidak menebak)."""
    added, alarms = 0, []
    recs = []
    for i, x in enumerate(lines):
        try:
            recs.append((json.loads(x), "0x" + hashlib.sha256(x.encode()).hexdigest()))
        except ValueError:
            alarms.append(f"umpan baris {i + 1} bukan JSON - DITOLAK")
    recs.sort(key=lambda t: (t[0].get("type") != "tanda", xf.day_of(t[0])))
    ticks_cache: Dict[str, Dict[str, dict]] = {}
    for rec, lh in recs:
        venue = str(rec.get("venue", ""))
        if not VENUE_RE.match(venue):
            alarms.append(f"umpan: venue tidak dikenal {venue!r} - DITOLAK")
            continue
        if rec.get("type") == "tanda":
            p = path_of(venue, "tanda", out_dir)
            have = ledger.load(p)
            if any(r.get("tanggal") == rec.get("tanggal") for r in have):
                continue
            if have and rec.get("tanggal", "") <= have[-1]["tanggal"]:
                alarms.append(f"tanda {venue} {rec.get('tanggal')} mundur - DITOLAK")
                continue
            midnight = ledger.iso_ms(f"{rec.get('tanggal')}T00:00:00Z")
            late = not (0 <= int(rec.get("t_ms") or 0) - midnight <= xf.MARK_WINDOW_S * 1000)
            row = {k: v for k, v in rec.items() if k != "v"}
            row.update(type="tanda", umpan_h=lh, dipakai=not late, catatan="diambil > 30 menit sesudah 00:00Z: tidak dipakai untuk tracking" if late else None)
            ledger.append(p, ledger.seal(row, ledger.head(have)), have)
            added += 1
            log(f"+ tanda {venue} {rec.get('tanggal')} ekuitas {rec.get('ekuitas')}{' (TERLAMBAT, tidak dipakai)' if late else ''}")
            continue
        bot, bar = str(rec.get("bot", "")), str(rec.get("bar", ""))
        p = path_of(venue, bot or "_", out_dir)
        have = ledger.load(p)
        if any(r.get("bar") == bar for r in have):
            continue
        if bot not in ticks_cache and bot in SPECS:
            ticks_cache[bot] = ticks_of(bot, paper_dir)
        ticks = ticks_cache.get(bot, {})
        commit_s = None
        if bot in SPECS and bar in ticks:
            try:
                c = cv.get_commit(sc.commit_id(committer, bot, SPECS[bot].sha(), sc.asof_s_of(ticks[bar])))
            except Exception as e:  # noqa: BLE001
                raise Unreadable(f"komit {bot} {bar}: chain tak terbaca ({type(e).__name__}: {str(e)[:120]})") from None
            commit_s = int(c["committedAt"]) if int(str(c["committer"]), 16) else None
        integ, viol = check(rec, ticks, commit_s)
        if not integ and have and bar <= have[-1]["bar"]:
            integ.append(f"bar {bar} tidak naik (ujung ledger {have[-1]['bar']})")
        if integ:
            alarms.append(f"laporan {venue} {bot} {bar} DITOLAK: {integ[:3]}")
            continue
        row = enrich(rec, ticks[bar], commit_s, close, kertas_fills(venue, bot, float(rec.get("modal") or 0), bar, kertas_dir), lh)
        row["pelanggaran"] = viol
        ledger.append(p, ledger.seal(row, ledger.head(have)), have)
        added += 1
        if viol:
            alarms.append(f"PELANGGARAN {venue} {bot} {bar}: {viol[:3]}")
        log(f"+ eksekusi {venue} {bot} bar {bar}: {row['n_order']} order, fee {row['fee']:.4f}, latensi "
            f"{row['latensi_s']}s, bobot terpenuhi {row['bobot_terpenuhi']}, pelanggaran {len(viol)}")
    return added, alarms


# ---------------------------------------------------------------- penjaga luar + ringkasan

def periksa(cv, committer: str, now_s: int, out_dir: str = OUT, paper_dir: str = PAPER) -> Tuple[int, List[str]]:
    """Untuk tiap (venue, bot) yang SUDAH punya ledger eksekusi: tick resmi terakhir dikomit > 60 menit lalu tanpa laporan = ALARM (SK-E16).
    -> (0 OK / 1 ALARM / 2 MENUNGGU, baris)."""
    code, rows = 0, []
    if not os.path.isdir(out_dir):
        return 0, ["belum ada ledger eksekusi (umpan belum menyala)"]
    for venue in sorted(os.listdir(out_dir)):
        for name in sorted(os.listdir(os.path.join(out_dir, venue))):
            bot = name[:-6]
            if not name.endswith(".jsonl") or bot not in SPECS:
                continue
            have = {r["bar"] for r in ledger.load(os.path.join(out_dir, venue, name))}
            ticks = ticks_of(bot, paper_dir)
            if not ticks:
                continue
            bar = max(ticks)
            if bar in have:
                rows.append(f"{venue} {bot} {bar}: OK (laporan ada)")
                continue
            c = cv.get_commit(sc.commit_id(committer, bot, SPECS[bot].sha(), sc.asof_s_of(ticks[bar])))
            if not int(str(c["committer"]), 16):
                rows.append(f"{venue} {bot} {bar}: belum dikomit - eksekusi memang belum boleh")
                continue
            age = now_s - int(c["committedAt"])
            if age >= TENGGANG_S:
                code = 1
                rows.append(f"{venue} {bot} {bar}: ALARM dikomit {age // 60} menit lalu tanpa laporan eksekusi (eksekutor atau umpan diam)")
            else:
                code = max(code, 2) if code != 1 else 1
                rows.append(f"{venue} {bot} {bar}: MENUNGGU dikomit {age // 60} menit lalu (tenggang {TENGGANG_S // 60})")
    return code, rows


def _pct(xs: Sequence[float], q: float) -> Optional[float]:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, math.ceil(q * len(xs)) - 1))] if xs else None


def tracking(recs: Sequence[dict], marks: Sequence[dict], close: Callable[[str, int], float], paper_dir: str = PAPER) -> List[dict]:
    """TE harian untuk tick D: (ekuitas tanda D+2 - tanda D+1) / modal - return paper D (definisi kertas). Butuh dua tanda yang dipakai."""
    import kertas_eksekusi as ke
    eq = {m["tanggal"]: float(m["ekuitas"]) for m in marks if m.get("dipakai")}
    out = []
    for r in recs:
        ticks = ticks_of(r["bot"], paper_dir)
        order = sorted(ticks)
        bar = r["bar"]
        d1 = ledger.date_of(ledger.iso_ms(f"{bar}T00:00:00Z") + ledger.DAY_MS)
        d2 = ledger.date_of(ledger.iso_ms(f"{bar}T00:00:00Z") + 2 * ledger.DAY_MS)
        if d1 not in eq or d2 not in eq or not r.get("modal"):
            continue
        tk = ticks[bar]
        i = order.index(bar)
        w_new = {a: float(w) for a, w in tk.get("targets", {}).items()}
        w_old = {a: float(w) for a, w in ticks[order[i - 1]].get("targets", {}).items()} if i > 0 else {}
        bar_ms = int(tk["asof"])
        try:
            rr = {a: close(a, bar_ms + ledger.DAY_MS) / close(a, bar_ms) - 1.0 for a in set(w_new) | set(w_old)}
        except Exception:  # noqa: BLE001 - bar penutupan D+1 belum ada
            continue
        ret_x = (eq[d2] - eq[d1]) / float(r["modal"])
        ret_p = ke.paper_return(w_new, w_old, rr)
        out.append({"bar": bar, "ret_eksekusi": ret_x, "ret_paper": ret_p, "te_bps": (ret_x - ret_p) * 1e4})
    return out


def ringkas(close: Callable[[str, int], float], out_dir: str = OUT, log=print) -> dict:
    res = {}
    if not os.path.isdir(out_dir):
        log("belum ada ledger eksekusi")
        return res
    for venue in sorted(os.listdir(out_dir)):
        marks = ledger.load(path_of(venue, "tanda", out_dir))
        for name in sorted(os.listdir(os.path.join(out_dir, venue))):
            bot = name[:-6]
            if bot not in SPECS:
                continue
            recs = ledger.load(os.path.join(out_dir, venue, name))
            orders = [o for r in recs for o in r.get("orders", []) if o.get("qty")]
            slip = [o["slip_bps"] for o in orders if o.get("slip_bps") is not None]
            fee = [o["fee_bps"] for o in orders if o.get("fee_bps") is not None]
            kx = [o["selisih_kertas_bps"] for o in orders if o.get("selisih_kertas_bps") is not None]
            lat = [r["latensi_s"] for r in recs if r.get("latensi_s") is not None]
            te = [abs(x["te_bps"]) for x in tracking(recs, marks, close)]
            viol = sum(len(r.get("pelanggaran") or []) for r in recs)
            m = {"hari": len(recs), "order": len(orders), "slip_median_bps": statistics.median(slip) if slip else None,
                 "fee_median_bps": statistics.median(fee) if fee else None, "selisih_kertas_median_bps": statistics.median(kx) if kx else None,
                 "latensi_p95_s": _pct(lat, 0.95), "te_hari": len(te), "te_median_bps": statistics.median(te) if te else None,
                 "te_p95_bps": _pct(te, 0.95), "pelanggaran": viol}
            m["status"] = ("PELANGGARAN" if viol else "BELUM CUKUP HARI" if len(te) < AMBANG["min_hari"] else
                           "LULUS" if (m["te_median_bps"] <= AMBANG["te_median_bps"] and m["te_p95_bps"] <= AMBANG["te_p95_bps"]
                                       and (m["slip_median_bps"] is None or m["slip_median_bps"] <= AMBANG["slip_median_bps"])
                                       and (m["fee_median_bps"] is None or m["fee_median_bps"] <= AMBANG["fee_max_bps"])
                                       and (m["latensi_p95_s"] is None or m["latensi_p95_s"] <= AMBANG["latensi_p95_s"])) else "GAGAL")
            res[f"{venue}|{bot}"] = m
            log(f"{venue}|{bot}: {json.dumps(m, sort_keys=True)}")
    return res


def _closes():
    import kertas_eksekusi as ke
    uni = sorted({a for b in SPECS.values() for a in b.universe if a.endswith("USDT")})
    return ke.Closes(uni).at


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("run", "periksa", "ringkas", "verify"))
    ap.add_argument("--alert", action="store_true", help="kirim Telegram bila ALARM (ALERT_TELEGRAM_TOKEN/CHAT)")
    ap.add_argument("--state", help="berkas kunci alert yang sudah dikirim (loop GitHub memanggil proses baru tiap 5 menit; tanpa ini alert berulang)")
    a = ap.parse_args()
    if a.cmd == "verify":
        bad = 0
        for root, _, files in os.walk(OUT):
            for n in files:
                if n.endswith(".jsonl"):
                    errs = verify(ledger.load(os.path.join(root, n)))
                    print(f"{os.path.relpath(os.path.join(root, n), ROOT)}: {'OK' if not errs else errs[:3]}")
                    bad += bool(errs)
        return 1 if bad else 0
    if a.cmd == "ringkas":
        ringkas(_closes())
        return 0
    import worker_watch as ww
    addrs = sc.load_addresses()
    cv = ww.ChainView(ww.Reader(), addrs["anchor"], addrs["registry"])
    alarms: List[str] = []
    if a.cmd == "run":
        gid, lines = read_feed(token=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"), gist_id=os.environ.get("EXEC_FEED_GIST"))
        if gid is None:
            print("umpan eksekusi belum ada (gist 'fabius-exec feed v1' belum dibuat; langkah builder H7) - tidak ada yang ditulis")
            return 0
        n, alarms = run(lines, cv, addrs["committer"], _closes())
        print(f"eksekusi: gist {gid}, {len(lines)} baris umpan, {n} catatan baru, {len(alarms)} alarm")
    else:
        code, rows = periksa(cv, addrs["committer"], int(time.time()))
        print("\n".join(rows))
        if code == 1:
            alarms = [r for r in rows if "ALARM" in r]
        elif code == 2:
            return 2
    for x in alarms:
        print(f"ALARM: {x}")
    if alarms and a.alert:
        import alert as alertmod
        al = alertmod.Alerter(prefix="Fabius ledger eksekusi")
        seen = set()
        if a.state and os.path.exists(a.state):
            with open(a.state, encoding="utf-8") as f:
                seen = set(json.load(f))
        for x in alarms:
            # periksa: kunci = venue+bot+bar (teksnya memuat menit yang berubah tiap putaran); run: teks deterministik per laporan
            key = f"eksekusi-ledger:{' '.join(x.split()[:3]) if a.cmd == 'periksa' else sha0x(x)[:18]}"
            if key in seen:
                continue
            if al.send(key, x, sekali=True) in ("terkirim", "tanpa-kanal"):
                seen.add(key)
        if a.state:
            with open(a.state, "w", encoding="utf-8") as f:
                json.dump(sorted(seen), f)
    return 1 if alarms else 0


def guarded_main() -> int:
    """Umpan/chain tak terbaca atau galat alat sendiri = 3 (TUNDA), bukan 1: crash penjaga tidak boleh jadi tuduhan."""
    try:
        return main()
    except Unreadable as e:
        print(f"TAK TERBACA: {e} - bukan vonis; diulang putaran berikut")
        return 3
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        print(f"TAK TERBACA: galat penulis sendiri {type(e).__name__}: {str(e)[:200]}")
        return 3


if __name__ == "__main__":
    raise SystemExit(guarded_main())
