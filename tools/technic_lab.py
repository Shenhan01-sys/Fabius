"""P32 - teknikal klasik DIUJI, bukan dirapikan: MA / RSI / MACD / Bollinger / Fibonacci / breakout /
lonjakan volum / volatilitas - pada deret harga PERISTIVA dari aliran kami sendiri.

Kenapa alat ini ada (28 Sep, pertanyaan builder): seluruh lapisan `03-Sinyal` + `04-Setup` ditulis
rapi tapi audit `_research/audit_ujian_pengetahuan.py` menemukan hanya 31 dari 86 catatan tanpa
penanda "belum diuji", dan `04-Setup` punya NOL perintah alat. Jadi klaim "kami sudah mempelajari
Fibonacci/swing/scalping" belum berbentuk angka. Alat ini mengubahnya jadi angka - dengan aturan
yang sama yang membatalkan F-D30/F-D32, karena pelajaran hari ini bukan "jangan coba", tapi
"jangan coba tanpa control".

Definisi fitur (SEMUA point-in-time, hanya baris dengan `t' <= t`):
  deret   = harga transaksi per waktu (detik), didedup per stempel (`dedupe_px`)
  MA      = SMA(20) > SMA(50) dari 50 transaksi terakhir; golden-cross bila silangnya < 15 m lalu
  RSI     = Wilder sederhana atas 14 perubahan; <30 jenuh jual, >70 jenuh beli
  MACD    = EMA12-EMA26 vs EMA9 sinyal; bullish bila histogram > 0 dan naik
  BOLL    = p0 < lower(2σ,20) -> reversion; p0 > upper -> momentum
  FIB     = swing high/low 60 m terakhir dengan kaki naik >= 10 %; masuk bila p0 berada di pita
           retracement 0,38-0,62 (pullback terdalam) - ini "Fibonacci" dalam bentuk yang bisa diuji
  BREAK   = p0 >= max(60 m sebelum t) (menembus tertinggi lokal)
  VOLSPIKE= USD beli 5 m terakhir >= 3x median per-5-m dari 30 m sebelumnya
  VOL     = volatilitas realisasi 20 perubahan terakhir, tinggi vs rendah (median split)

Vonis yang dipakai: BUKAN median (hari ini terbukti median menipu pada payoff miring kanan), tapi
  (1) mean winso +-2.000 bps dengan CI bootstrap,
  (2) DI ATAS CI atas control acak dari pool yang sama,
  (3) ekor P(net >= +500 bps) naik: Fisher SATU arah,
  (4) Mann-Whitney sebagai uji tengah, BH alpha 0,10 di antara semua fitur, n >= 20.
Spesifikasi dikunci sebelum hasil dilihat: sha dicetak + `decisions/prereg-technic-lock.json`.
"""
from __future__ import annotations

import bisect
import hashlib
import io
import json
import math
import os
import random
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import costs  # noqa: E402
import flow_cluster_test as FC  # noqa: E402
import prices as PR  # noqa: E402
import tx_prices as TP  # noqa: E402

MIN = 60
FITUR = ["ma_tren", "golden_cross", "rsi_jenuh_jual", "rsi_jenuh_beli", "macd_bull",
         "boll_bawah", "boll_atas", "fib_pullback", "breakout", "vol_spikes", "vol_rendah",
         "vol_tinggi"]
SPES = {"versi": "1", "horison_menit": [30, 120], "sumber_harga": "peristiwa (tx)",
        "dedup": "median per (token,stempel)", "jendela_keluar_menit": 15,
        "ongkos_bps_rt": 59.0, "winsor_bps": 2000.0, "n_min": 20, "draws_mean": 4000,
        "draws_control": 400, "kontrol": "acak-dari-pool-yang-sama-CI-atas",
        "ma": [20, 50], "rsi_period": 14, "rsi_jual": 30.0, "rsi_beli": 70.0,
        "macd": [12, 26, 9], "boll": [20, 2.0], "fib_jendela_menit": 60, "fib_kaki_min": 0.10,
        "fib_pita": [0.38, 0.62], "break_jendela_menit": 60, "vol_spike_rasio": 3.0,
        "vol_real_period": 20}


def wINS(x):
    return max(-SPES["winsor_bps"], min(SPES["winsor_bps"], x))


def boot_mean(xs, draws, seed=20260928):
    if not xs:
        return 0.0, 0.0
    rnd = random.Random(seed)
    n = len(xs)
    m = sorted(sum(xs[rnd.randrange(n)] for _ in range(n)) / n for _ in range(draws))
    return m[int(0.025 * draws)], m[int(0.975 * draws)]


def sma(v, k):
    return sum(v[-k:]) / k if len(v) >= k else None


def ema_series(v, k):
    if len(v) < k:
        return None
    a = 2.0 / (k + 1.0)
    out = [sum(v[:k]) / k]
    for x in v[k:]:
        out.append(a * x + (1 - a) * out[-1])
    return out


def rsi(v, k=14):
    if len(v) < k + 1:
        return None
    ch = [v[i] - v[i - 1] for i in range(1, len(v))]
    g = sum(max(x, 0.0) for x in ch[-k:]) / k
    l = sum(max(-x, 0.0) for x in ch[-k:]) / k
    if l == 0:
        return 100.0
    return 100.0 - 100.0 / (1.0 + g / l)


def fitur_serupa(closes, t, rows, tx_rows, p0):
    """Dict fitur boolean untuk satu kejadian (hanya data <= t).

    `rows`   = pasangan (harga, waktu) dari EKOR deret harga peristiwa - dipakai untuk silang MA,
               swing Fib, dan pembanding breakout.
    `tx_rows`= baris transaksi (dict) dari ekor yang sama - dipakai untuk lonjakan VOLUM, yang
               tidak bisa dihitung dari harga saja.
    """
    out = {k: False for k in FITUR}
    if len(closes) < 25:
        return out
    f, s = sma(closes, SPES["ma"][0]), sma(closes, SPES["ma"][1])
    if f and s:
        out["ma_tren"] = f > s
        silam = [c for c, tt in rows if tt <= t - 15 * MIN]
        if len(silam) >= SPES["ma"][1]:
            fp, sp = sma(silam, SPES["ma"][0]), sma(silam, SPES["ma"][1])
            if fp and sp:
                out["golden_cross"] = (fp <= sp) and (f > s)
    r = rsi(closes, SPES["rsi_period"])
    if r is not None:
        out["rsi_jenuh_jual"] = r < SPES["rsi_jual"]
        out["rsi_jenuh_beli"] = r > SPES["rsi_beli"]
    e12, e26 = ema_series(closes, 12), ema_series(closes, 26)
    if e12 and e26:
        m = min(len(e12), len(e26))
        macd = [e12[-m + i] - e26[-m + i] for i in range(m)]
        sg = ema_series(macd, 9)
        if sg and len(macd) >= 2:
            h0 = macd[-1] - sg[-1]
            h1 = macd[-2] - sg[-2] if len(macd) > 1 and len(sg) > 1 else h0
            out["macd_bull"] = h0 > 0 and h0 >= h1
    m20, sd20 = sma(closes, 20), statistics.pstdev(closes[-20:])
    if m20 and sd20:
        out["boll_bawah"] = p0 < m20 - SPES["boll"][1] * sd20
        out["boll_atas"] = p0 > m20 + SPES["boll"][1] * sd20
    j = SPES["fib_jendela_menit"] * MIN
    win = [c for c, tt in rows if t - j <= tt <= t]
    if len(win) >= 10:
        hi, lo = max(win), min(win)
        if lo > 0 and hi / lo - 1.0 >= SPES["fib_kaki_min"]:
            retr = (hi - p0) / (hi - lo)
            out["fib_pullback"] = SPES["fib_pita"][0] <= retr <= SPES["fib_pita"][1]
    lalu = [c for c, tt in rows if t - SPES["break_jendela_menit"] * MIN <= tt < t]
    if len(lalu) >= 10:
        out["breakout"] = p0 >= max(lalu) * 0.999
    b5 = sum(r["u"] for r in tx_rows if t - 5 * MIN <= r["t"] <= t and r["buy"])
    pra = [sum(r["u"] for r in tx_rows if t - (a + 5) * MIN <= r["t"] < t - a * MIN and r["buy"])
           for a in (5, 10, 15, 20, 25)]
    if pra and FC.med([x for x in pra if x > 0] or [0]) > 0:
        out["vol_spikes"] = b5 >= SPES["vol_spike_rasio"] * FC.med([x for x in pra if x > 0])
    ch = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes)) if closes[i - 1] > 0]
    if len(ch) >= SPES["vol_real_period"]:
        v = statistics.pstdev(ch[-SPES["vol_real_period"]:])
        out["_vol"] = v
    return out


def kejadian(horison):
    txs, _ = {}, None
    for ln in io.open(os.path.join(ROOT, "universe", "wallet-flow.jsonl"), encoding="utf-8",
                      errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        d = json.loads(ln)
        if d.get("k") not in ("tx", "txc"):
            continue
        tk = str(d.get("tk") or "").lower()
        t, p = int(d.get("t") or 0), float(d.get("p") or 0)
        if tk and t and p > 0:
            txs.setdefault(tk, []).append({"t": t, "p": p, "u": float(d.get("u") or 0),
                                           "buy": bool(d.get("b"))})
    ser = TP.load_tx_series()["rows"]
    out, ditolak = [], 0
    for tk, rows in txs.items():
        ss = ser.get(tk) or []
        st = [x[0] for x in ss]
        rows.sort(key=lambda r: r["t"])
        taken = -10 ** 15
        for r in [x for x in rows if x["buy"]]:
            t = r["t"]
            if t - taken < horison * MIN:
                ditolak += 1
                continue
            i = PR_pre(ss, st, t)
            if i is None:
                continue
            p0 = ss[i][1]
            import bisect
            a = bisect.bisect_left(st, t + (horison - 15) * MIN)
            b = bisect.bisect_right(st, t + (horison + 15) * MIN)
            ex = [ss[j][1] for j in range(a, b)]
            if not ex:
                continue
            taken = t
            # EKOR 320 transaksi saja: MA50/RSI/Bollinger cukup jauh di bawah itu, dan jendela
            # waktu 60 m tetap dipotong dari ekor ini. Tanpa batas, fitur dihitung dari seluruh
            # riwayat tiap kejadian dan alatnya tidak selesai (deret terpanjang ribuan baris).
            ekor = ss[max(0, i - 320):i + 1]
            closes = [p for _, p in ekor]
            tx_ekor = [x for x in rows if t - 35 * MIN <= x["t"] <= t]
            fs = fitur_serupa(closes, t, [(p, tt) for tt, p in ekor], tx_ekor, p0)
            vol = fs.pop("_vol", None)
            net = round(10000.0 * (FC.med(ex) - p0) / p0 - costs.rt_cost(), 1)
            ev = {"tk": tk, "t": t, "net": net, "vol": vol}
            ev.update(fs)
            out.append(ev)
    med = statistics.median([e["vol"] for e in out if e["vol"] is not None]) if out else None
    for e in out:
        if e["vol"] is not None and med is not None:
            e["vol_rendah"] = e["vol"] < med
            e["vol_tinggi"] = e["vol"] >= med
    return out, ditolak


def PR_pre(ss, st, t):
    import bisect
    i = bisect.bisect_right(st, t) - 1
    return i if i >= 0 else None


def ringkas(pool, xs, nama, rnd, pn):
    vs = [wINS(e["net"]) for e in xs]
    lo, hi = boot_mean(vs, SPES["draws_mean"])
    luar = [wINS(e["net"]) for e in pool if not e[nama]]
    s500 = sum(1 for v in luar if v >= 500)
    fis = ekor_hipergeo(sum(1 for v in vs if v >= 500), len(vs), s500, len(luar))
    mw = FC.mann_whitney_p(vs, luar)
    ctrls = []
    for _ in range(SPES["draws_control"]):
        c = [rnd.choice(pn) for _ in range(len(vs))]
        ctrls.append(sum(c) / len(c))
    ctrls.sort()
    c_atas = ctrls[int(0.975 * len(ctrls))]
    mean = sum(vs) / len(vs)
    return {"h": nama, "n": len(xs), "mean": round(mean, 1), "lo": round(lo, 1), "hi": round(hi, 1),
            "median": round(FC.med(vs), 1), "p500": round(100.0 * sum(1 for v in vs if v >= 500)
                                                          / len(vs), 1),
            "pos": round(100.0 * sum(1 for v in vs if v > 0) / len(vs), 1),
            "c_atas": round(c_atas, 1), "di_atas": mean > c_atas, "mw": mw, "fis": fis}


def ekor_hipergeo(a_pos, a_n, b_pos, b_n):
    from math import exp, lgamma

    def lc(n, k):
        if k < 0 or k > n:
            return float("-inf")
        return lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1)
    N, K, n = a_n + b_n, a_pos + b_pos, a_n
    if N <= 0 or K <= 0 or n <= 0 or K >= N:
        return None
    lo, hi = max(0, K - (N - n)), min(n, K)
    den = lc(N, K)
    pk = [exp(lc(n, k) + lc(N - n, K - k) - den) for k in range(lo, hi + 1)]
    if not pk or sum(pk) <= 0:
        return None
    return min(1.0, sum(pk[a_pos - lo:]) if a_pos >= lo else 1.0)


def main():
    sha = "0x" + hashlib.sha256(json.dumps(SPES, sort_keys=True).encode()).hexdigest()
    lock = os.path.join(ROOT, "decisions", "prereg-technic-lock.json")
    print("spesifikasi teknikal sha=%s..." % sha[:19])
    if os.path.exists(lock):
        lama = json.load(io.open(lock, encoding="utf-8"))
        if lama.get("spec_sha256") != sha:
            raise SystemExit("SPESIFIKASI DIUBAH SETELAH DIKUNCI - tidak ada hasil")
    else:
        json.dump({"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "spec": SPES, "spec_sha256": sha,
                   "catatan": "teknikal klasik ditetapkan sebelum hasilnya dilihat"},
                  io.open(lock, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
        print("kunci ditulis: decisions/prereg-technic-lock.json")
    rnd = random.Random(20260928)
    hasil_all = {}
    for hor in SPES["horison_menit"]:
        ev, ditolak = kejadian(hor)
        pool = ev
        pn = [wINS(e["net"]) for e in pool]
        print("\n=== horison %d m | %d kejadian (%d ditolak karena tumpang tindih) ==="
              % (hor, len(pool), ditolak))
        print("   pool: mean winso %+0.1f | median %+0.1f | P>=500 %.1f %%"
              % (sum(pn) / len(pn), FC.med(pn), 100.0 * sum(1 for v in pn if v >= 500) / len(pn)))
        print("   %-15s %6s %10s %-20s %9s %8s %-15s %8s"
              % ("fitur", "n", "mean", "CI 95 %", "median", "P>=500", "vs control", "BH"))
        rows = []
        for nama in FITUR:
            xs = [e for e in pool if e.get(nama)]
            if len(xs) < SPES["n_min"]:
                print("   %-15s %6d  n<%d - TIDAK DIUJI" % (nama, len(xs), SPES["n_min"]))
                continue
            r = ringkas(pool, xs, nama, rnd, pn)
            rows.append(r)
            print("   %-15s %6d %+10.1f [%+8.1f; %+9.1f] %+9.1f %7.1f%% %+9.1f vs %+8.1f %s %s"
                  % (nama, r["n"], r["mean"], r["lo"], r["hi"], r["median"], r["p500"],
                     r["mean"], r["c_atas"], "DI ATAS" if r["di_atas"] else "di bawah",
                     ("%.4f" % r["fis"]) if r["fis"] is not None else "-"))
        lulus = FC.bh([(r["h"], r["fis"]) for r in rows if r["fis"] is not None])
        atas = [r["h"] for r in rows if r["di_atas"]]
        print("   BH alpha 0,10 (ekor naik): %s" % (sorted(lulus) or "TIDAK ADA"))
        print("   di atas control acak     : %s" % (sorted(atas) or "TIDAK ADA"))
        hasil_all[hor] = {"pool": len(pool), "rows": rows, "bh_ekor": sorted(lulus),
                          "di_atas_control": sorted(atas)}
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "spec_sha256": sha,
           "spec": SPES, "hasil": hasil_all}
    p = os.path.join(ROOT, "decisions", "technic-lab-%s.json"
                     % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("\nartefak: decisions/%s" % os.path.basename(p))


if __name__ == "__main__":
    main()
