"""Lapisan ARAH: long/short, kapan masuk, seberapa besar, seberapa lama - lalu di-hash.

Ini jawaban atas keberatan builder (25 Sep): "masa agentnya cuma enter doang tanpa prediksi naik
turunnya, gimana, kapan, seberapa banyak, seberapa lama".

Yang diubah dari rencana kemarin, dan alasannya (semua terukur):
  ①  deret harga: ASTER (BNB-native, tanpa API key) memberi 9.599 bar hourly / 400 hari lewat
     `tools/bars.py` - bukan Hyperliquid (chain sendiri) dan bukan GMGN (mentok 41,6 hari).
  ③  funding + OI: Aster `premiumIndex` / `openInterest`, interval funding = 4 jam = horizon kita.
  C  kelas: memecoin TERNYATA bisa arah asal punya kontrak perp (61 kontrak `Meme`), jadi gerbang
     "boleh dinilai arahnya" = punya kontrak, bukan "ini bukan memecoin".

Satu aturan yang tidak bisa ditawar dan ditegakkan di sini, bukan di niat:
  - model (Jev) hanya boleh MEMBATalkan/mengecilkan, tidak pernah membuka posisi yang gerbang tolak;
  - angka tanpa jejak tidak ditulis: tiap kandidat menyimpan `decisionHash` + `gatesHash` +
    `snapshotHash`, jadi "kapan kami tahu apa" bisa dibaca orang dari chain 97.

Dua rezim keluar (usulan builder, ditambal supaya tidak bohong):
  - yakin "cuma turun lalu naik jauh"  -> stop di struktur (ATR/swing), karena tesis punya bentuk
    yang bisa dibantah;
  - tidak yakin / perlu lama            -> BUKAN "jual saat 0" (saat rug, jualannya ditolak
    kontrak atau tidak ada likuiditas), tapi ukuran kecil + HARD TIME-STOP + exit-size <= 1% liq.
    Yang membatasi kerugian adalah ukuran x waktu, bukan level harga.

Pakai:  python tools/direction.py                      # siklus penuh, layar saja
         python tools/direction.py --emit              # + tulis decisions/direction-*.jsonl
         python tools/direction.py --top 3 --no-model   # tanpa panggilan model (hemat, deterministik)
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import statistics
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import bars  # noqa: E402  (tools/bars.py)

_spec = importlib.util.spec_from_file_location("judge", os.path.join(HERE, "judge.py"))
judge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(judge)

DATA_DIR = os.path.join(ROOT, "data")
PERP_CACHE = os.path.join(DATA_DIR, "aster_symbols.json")
BASE = "https://fapi.asterdex.com/fapi/v1"

# ---- ambang. Semua punya asal; jangan ada angka tanpa tempat.
NEED_BARS = 2400            # 5-fold walk-forward (vault/02-Ambang.md, edge_lab.py:30,126)
MIN_BARS_TINY = 720         # 30 hari: cukup utk fitur, TIDAK cukup utk klaim edge
ACF_EFFICIENT = 0.05        # |acf| di bawah ini = mendekati jalan acak (asset_efficiency.py:29)
ACF_STRUCTURED = 0.10       # >= ini = pola terukur; di antaranya = belum tahu
FUNDING_EXTREME = 0.0005    # 0,05% per 4 jam = biaya carry/teknik terlalu mahal
RISK_SAFE = 0.005            # 0,5% ekuitas per posisi saat tidak yakin
RISK_WARM = 0.010            # 1% (korpus lama: BASE_RISK 1%, CONVICTION 0,5-1,5%)
TIME_STOP_H = 24            # hard time-stop utk rezim "tidak yakin"
ATR_MULT_STOP = 1.5
ATR_MULT_TP = 3.0
STALE_UNIVERSE_H = 2.0      # di atas ini: universe cukup basi untuk dicatat DI DALAM hash-nya

# Diisi di main() dari snapshot yang sedang dipakai. Dibawa lewat modul karena `snap_hash_for`
# harus MENYIMPANNYA ke dalam snapshotHash: kalau "seberapa tua datanya" hanya dicetak di layar,
# ia hilang begitu siklus selesai - padahal itu bagian dari apa yang kami ketahui kapan.
UNIVERSE_UTC = [None]
UNIVERSE_AGE = [None]


def _get(path, timeout=30):
    req = urllib.request.Request(BASE + path,
                                 headers={"User-Agent": "Mozilla/5.0 (compatible; fabius-direction/1.0)",
                                          "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:  # noqa: BLE001
        return {"_error": f"{type(e).__name__}: {str(e)[:140]}"}


def perp_symbols(refresh=False):
    if os.path.exists(PERP_CACHE) and not refresh:
        try:
            return json.load(open(PERP_CACHE, encoding="utf-8"))
        except Exception:
            pass
    ei = _get("/exchangeInfo")
    syms = ei.get("symbols") or []
    out = [{"symbol": s.get("symbol"), "base": s.get("baseAsset"),
            "tags": s.get("underlyingSubType") or [], "status": s.get("status")}
           for s in syms if s.get("status") == "TRADING"]
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PERP_CACHE, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False)
    return out


def universe_snapshot():
    last = None
    for line in open(os.path.join(ROOT, "universe", "bsc-universe.jsonl"), encoding="utf-8"):
        line = line.strip()
        if line:
            d = json.loads(line)
            if d.get("schema"):
                last = d
    return last


def age_hours(stamp):
    """Berapa jam sejak stempel UTC "...Z" sampai sekarang. None kalau bentuknya tidak dikenal."""
    from datetime import datetime, timezone
    try:
        then = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None
    return (datetime.now(timezone.utc) - then).total_seconds() / 3600.0


def feats(closes, highs, lows, opens=None):
    """Fitur dari deret. Semua dihitung dari bar yang SUDAH selesai (bars.py membuang bar berjalan)."""
    n = len(closes)
    if n < 25:
        return {"n": n, "ok": False}
    r = [(closes[i] / closes[i - 1]) - 1.0 for i in range(1, n)]
    lr = [math.log(closes[i] / closes[i - 1]) for i in range(1, n) if closes[i] > 0]
    def acf(lag):
        if len(lr) <= lag + 30:
            return None
        a, b = lr[:-lag], lr[lag:]
        sa, sb = statistics.pstdev(a), statistics.pstdev(b)
        if sa == 0 or sb == 0:
            return None
        return abs(statistics.correlation(a, b)) if hasattr(statistics, "correlation") else None
    try:
        acfs = [x for x in (acf(1), acf(6), acf(24)) if x is not None]
        acf_mean = round(sum(acfs) / len(acfs), 4) if acfs else None
    except Exception:
        acf_mean = None
    tr = [max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
          for i in range(1, n)]
    atr = sum(tr[-24:]) / min(24, len(tr))
    sma = sum(closes[-24:]) / 24
    vol_ann = statistics.pstdev(lr) * (6 ** 0.5) if len(lr) > 30 else None   # 4 jam -> hari -> tahun
    last = closes[-1]
    return {"n": n, "ok": True, "last": last,
            "ret4": (last / closes[-5] - 1.0) if n >= 5 else None,
            "ret24": (last / closes[-25] - 1.0) if n >= 25 else None,
            "atr": atr, "atr_pct": atr / last if last else None,
            "sma_gap_pct": (last - sma) / sma if sma else None,
            "acf_abs": acf_mean, "vol_annual": vol_ann}


def funding_and_oi(sym):
    p = _get(f"/premiumIndex?symbol={sym}")
    o = _get(f"/openInterest?symbol={sym}")
    f = p.get("lastFundingRate") if isinstance(p, dict) else None
    return {"funding_4h": float(f) if f not in (None, "") else None,
            "mark": p.get("markPrice") if isinstance(p, dict) else None,
            "next_funding_ms": p.get("nextFundingTime") if isinstance(p, dict) else None,
            "oi": float(o.get("openInterest")) if isinstance(o, dict) and o.get("openInterest") else None,
            "err": (p.get("_error") or o.get("_error"))}


def build_state_table(rows):
    lines = ["Kandidat di venue perp BNB-native (funding per 4 jam). Tiap baris satu simbol: "
             "ret24h_pct, atr_pct, |autocorr| (>=0.10 pola, <0.05 mendekati acak), "
             "funding_4h_pct, oi, likuiditas_pool_usd, bundler_rate, jumlah bar."]
    for r in rows:
        lines.append(json.dumps({k: r.get(k) for k in
                                 ("symbol", "ret24_pct", "atr_pct", "acf_abs", "funding_4h_pct",
                                  "oi", "liq_usd", "bundler_rate", "bars")}, ensure_ascii=False))
    return "\n".join(lines)


def decide_one(f, fund, liq, model_ans):
    """Gabungan deterministik + model. Model hanya boleh MENGECILKAN atau MEMVETO."""
    why, side, conf = [], "flat", None
    if not f.get("ok"):
        return {"side": "flat", "why": ["deret terlalu pendek"], "regime": "unassessable"}
    if f["n"] < MIN_BARS_TINY:
        return {"side": "flat", "why": [f"bar={f['n']} < {MIN_BARS_TINY}"], "regime": "unassessable"}
    if f["n"] < NEED_BARS:
        why.append(f"bar={f['n']}<{NEED_BARS}: layak dinilai, TIDAK layak diklaim sebagai edge")
    a = f.get("acf_abs")
    if a is None:
        why.append("acf tidak terukur")
    elif a < ACF_EFFICIENT:
        why.append(f"|acf|={a} < {ACF_EFFICIENT} -> mendekati jalan acak, tidak ada arah")
        return {"side": "flat", "why": why, "regime": "efficient"}
    elif a >= ACF_STRUCTURED:
        why.append(f"|acf|={a} >= {ACF_STRUCTURED} -> pola terukur")
    else:
        why.append(f"|acf|={a} di zona abu-abu")
    fu = fund.get("funding_4h")
    if fu is not None and abs(fu) > FUNDING_EXTREME:
        why.append(f"funding 4j {fu*100:+.4f}% ekstrem -> biaya/desesperasi terlalu tinggi")
        return {"side": "flat", "why": why, "regime": "expensive-carry"}
    # arah dari data kita sendiri (bukan dari model): momentum vs sma + ret24
    m = f.get("sma_gap_pct") or 0
    r24 = f.get("ret24") or 0
    side = "long" if (m > 0.01 and r24 > 0) else "short" if (m < -0.01 and r24 < 0) else "flat"
    if side == "flat":
        why.append("struktur & 24h tidak searah -> flat")
    conf = None
    if model_ans:
        conf = model_ans.get("confidence")
        mp = model_ans.get("probabilities") or {}
        if model_ans.get("veto"):
            why.append(f"model veto ({model_ans.get('dominant_risk') or 'unspecified'} "
                       f"p={mp.get(model_ans.get('dominant_risk'))})")
            side = "flat"
        elif model_ans.get("side") in ("long", "short") and side != "flat":
            if model_ans["side"] != side:
                why.append(f"model bilang {model_ans['side']} vs data {side} -> turun ke OBSERVASI")
                conf = min(conf or 0.0, 0.5)
    # ukuran & horizon
    risk = RISK_SAFE if (conf is None or conf < 0.6) else RISK_WARM
    regime = "stop-loss" if (side != "flat" and conf and conf >= 0.6 and a and a >= ACF_STRUCTURED) \
        else "time-stop" if side != "flat" else "flat"
    atr = f.get("atr") or 0
    px = f["last"]
    out = {"side": side, "risk_pct": risk, "regime": regime,
           "entry_ref": round(px, 8), "why": why, "conf": conf, "acf": a,
           "horizon_h": TIME_STOP_H if regime == "time-stop" else 24}
    if side == "long":
        out["stop"], out["target"] = round(px - ATR_MULT_STOP * atr, 8), round(px + ATR_MULT_TP * atr, 8)
    elif side == "short":
        out["stop"], out["target"] = round(px + ATR_MULT_STOP * atr, 8), round(px - ATR_MULT_TP * atr, 8)
    if liq:
        out["exit_cap_1pct_liq_usd"] = round(liq * 0.01, 2)
    return out


def snap_hash_for(symbol, f, fund):
    """snapshotHash utk keputusan arah = ikatan ke data yang benar-benar dipakai saat itu."""
    # Fitur yang BENAR-BENAR dipakai keputusan ikut di-hash, bukan hanya harga mentahnya.
    # Alasannya: kalau nanti orang mau mereplikasi "kenapa side=short", cukup data ini + kode.
    obj = {"src": "aster", "symbol": symbol, "last_bar_t": f.get("t_last"),
           "bars": f.get("n"), "funding_4h": fund.get("funding_4h"),
           "oi": fund.get("oi"), "next_funding_ms": fund.get("next_funding_ms"),
           "last": f.get("last"), "ret24": f.get("ret24"), "acf_abs": f.get("acf_abs"),
           "atr_pct": f.get("atr_pct"), "sma_gap_pct": f.get("sma_gap_pct"),
           "universe_age_h": UNIVERSE_AGE[0], "universe_utc": UNIVERSE_UTC[0],
           "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    return "0x" + hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), obj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--no-model", action="store_true")
    a = ap.parse_args()

    ps = perp_symbols()
    by_base = {}
    for s in ps:
        by_base.setdefault(str(s.get("base") or "").upper(), []).append(s["symbol"])
    snap = universe_snapshot()
    UNIVERSE_UTC[0] = snap.get("snapshot_utc")
    UNIVERSE_AGE[0] = age_hours(UNIVERSE_UTC[0])
    print(f"universe {UNIVERSE_UTC[0]}: {snap['universe_size']} baris | perp aktif: {len(ps)}"
          + (f" | UMUR {UNIVERSE_AGE[0]:.1f} jam" if UNIVERSE_AGE[0] is not None else ""))
    if UNIVERSE_AGE[0] is not None and UNIVERSE_AGE[0] > STALE_UNIVERSE_H:
        # Jangan diam-diam: kandidat berumur X jam berarti "siapa yang baru masuk" tidak terjawab,
        # dan harga di Aster tetap segar - jadi yang basi adalah DAFTARNYA, bukan deret harganya.
        print(f"  PERINGATAN: snapshot universe berumur {UNIVERSE_AGE[0]:.1f} jam "
              f"(>{STALE_UNIVERSE_H} jam) -> perekam mungkin berhenti; umur ini ikut di-hash "
              "di snapshotHash supaya keputusan tidak bisa diklaim memakai data yang lebih baru "
              "dari yang kami punya.")

    rows, seen = [], set()
    for r in snap["rows"]:
        sym = str(r.get("symbol") or "").strip().upper()
        cand = by_base.get(sym)
        if not cand or sym in seen:
            continue
        seen.add(sym)
        psym = cand[0]
        # bars.load() mengembalikan DICT {"meta":…, "bars":[…]} - bukan tuple. Meng-unpack-nya
        # jadi (bs, _) akan menghasilkan karakter dict dan memaksa fetch ulang 7 halaman tiap siklus.
        cached = bars.load(psym, "1h")
        data = (cached or {}).get("bars") or []
        if not data:
            data, meta_fetch = bars.fetch(psym, "1h", 400, verbose=False)
            if data:
                # Meta dari fetch() diteruskan APA ADANYA - jumlah halaman, endpoint, masalah HTTP.
                # Baris ini sebelumnya mengarang {"pages": 1} untuk deret 400 hari yang butuh 7
                # halaman DAN membuang meta aslinya, jadi cache menyimpan provenance palsu.
                bars.save(psym, "1h", data, meta_fetch)
        if not data:
            rows.append({"symbol": psym, "base": sym, "bars": 0, "ok": False})
            continue
        closes = [b["c"] for b in data]
        highs = [b["h"] for b in data]
        lows = [b["l"] for b in data]
        f = feats(closes, highs, lows)
        f["t_last"] = data[-1]["t"]
        fund = funding_and_oi(psym)
        liq = r.get("liquidity")
        rows.append({"symbol": psym, "base": sym, "tags": (by_base[sym][0],), "liq_usd": liq,
                     "bundler_rate": r.get("bundler_rate"), "bars": f.get("n"),
                     "ret24_pct": round((f.get("ret24") or 0) * 100, 3) if f.get("ok") else None,
                     "atr_pct": round(f["atr_pct"] * 100, 3) if f.get("ok") and f.get("atr_pct") else None,
                     "acf_abs": f.get("acf_abs"),
                     "funding_4h_pct": round((fund.get("funding_4h") or 0) * 100, 5),
                     "oi": fund.get("oi"), "_f": f, "_fund": fund})

    judged = [r for r in rows if r.get("_f", {}).get("ok")]
    # Kandidat tanpa riwayat cukup tidak boleh memakan kursi: kalau tidak, 3 dari 5 kursi terisi
    # baris yang keputusannya pasti `flat` dan panggilan model ke mereka cuma pemborosan token.
    scored = [r for r in judged if (r.get("bars") or 0) >= MIN_BARS_TINY]
    thin = len(judged) - len(scored)
    scored.sort(key=lambda x: (abs(x.get("acf_abs") or 0)), reverse=True)
    pick = scored[:a.top]
    print(f"tertangkap {len(rows)} kandidat yang punya kontrak perp; dinilai {len(judged)}; "
          f"layak kursi {len(scored)} (buang {thin} karena bar<{MIN_BARS_TINY}); "
          f"dipilih {len(pick)} (urut |acf| terbesar)\n")

    model_out = {}
    if pick and not a.no_model:
        state = build_state_table(pick)
        qs = {}
        for r in pick:
            qs[f"side_{r['symbol']}"] = {"type": "choice",
                                         "instructions": f"Direction for {r['symbol']} over next 4 hours",
                                         "criteria": {"long": "higher", "short": "lower", "flat": "no edge"}}
            qs[f"veto_{r['symbol']}"] = {"type": "noul",
                                         "instructions": f"For {r['symbol']}: position cannot be closed "
                                                        f"near entry within 4 hours, or carry is too expensive"}
        r = judge.ask_jev(state, qs)
        model_out = r.get("answers") or {}
        print(f"model: provider={r.get('provider')} ok={r.get('ok')} asked={r.get('asked')} "
              f"answered={r.get('answered')} lat={r.get('latency_s')} "
              f"tokens={r.get('tokens_in')}/{r.get('tokens_out')} cost=${r.get('cost_usd')} "
              f"key={r.get('key_source')} {r.get('why') or ''}\n")

    out_rows = []
    for r in pick:
        m = None
        if model_out:
            side_a = (model_out.get(f"side_{r['symbol']}") or {})
            veto_a = (model_out.get(f"veto_{r['symbol']}") or {})
            m = {"side": side_a.get("choice"), "confidence": side_a.get("confidence"),
                 "probabilities": side_a.get("probabilities"),
                 "veto": bool((veto_a.get("noul") or 0) >= 0.5),
                 "veto_prob": veto_a.get("noul")}
        d = decide_one(r["_f"], r["_fund"], r.get("liq_usd"), m)
        sh, meta = snap_hash_for(r["symbol"], r["_f"], r["_fund"])
        rec = {"kind": "direction", "symbol": r["symbol"], "universe_snapshot": snap["sha256"],
              "data": meta, "decision": d, "model": m}
        dh = "0x" + hashlib.sha256(json.dumps(rec, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        gh = "0x" + hashlib.sha256(json.dumps({"why": d["why"], "regime": d["regime"]},
                                              sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        out_rows.append({**rec, "decisionHash": dh, "gatesHash": gh, "snapshotHash": sh})

    print(f"{'simbol':14}{'bar':>6}{'|acf|':>8}{'fund4j%':>10}{'model':>9}{'veto':>7}{'side':>7}"
          f"{'rezim':>13}{'risk':>7}  alasan")
    print("-" * 126)
    for o in out_rows:
        d, m, dt = o["decision"], (o.get("model") or {}), o["data"]
        acf = dt.get("acf_abs")
        vp = m.get("veto_prob")
        print(f"{o['symbol']:14}{dt['bars']:>6}{(f'{acf:.3f}' if acf is not None else '-'):>8}"
              f"{(dt['funding_4h'] * 100 if dt.get('funding_4h') is not None else 0):>10.4f}"
              f"{str(m.get('side') or '-'):>9}{('-' if vp is None else f'{vp:.2f}'):>7}"
              f"{d['side']:>7}{d['regime']:>13}"
              f"{d.get('risk_pct', 0) * 100:>6.1f}%  {'; '.join(d['why'])[:96]}")
        if d["side"] != "flat":
            print(f"{'':14}  entry={d.get('entry_ref')} stop={d.get('stop')} target={d.get('target')} "
                  f"horizon={d['horizon_h']}h conf={d.get('conf')} "
                  f"exit-cap<=1%liq=${d.get('exit_cap_1pct_liq_usd')}")

    if a.emit:
        os.makedirs(os.path.join(ROOT, "decisions"), exist_ok=True)
        # %Z/gmtime, BUKAN waktu lokal: tiap stempel di dalam file ini UTC, dan laptop ini WIB
        # (UTC+7). Dengan nama lokal, siklus 01:00 WIB 25 Sep tertulis "20260925" sementara
        # isinya berkata "2026-09-24T18:00Z" - dua tanggal untuk satu peristiwa, dan yang membaca
        # dataset tidak bisa tahu mana yang jadi acuan urutan.
        p = os.path.join(ROOT, "decisions",
                         f"direction-{time.strftime('%Y%m%d', time.gmtime())}Z.jsonl")
        with open(p, "a", encoding="utf-8") as fh:
            for o in out_rows:
                fh.write(json.dumps(o, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"\ntertulis: {p}")
    print("\nBatas: `side` di sini adalah keputusan yang bisa DIPERIKSA, bukan yang sudah terbukti "
          "untung. Registry tetap kosong sampai sebuah aset lolos n>=20 cost-aware + 2 konfirmasi "
          "data baru beruntun (vault/08 §3).")


if __name__ == "__main__":
    main()
