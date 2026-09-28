"""Uji hipotesis kohor (P11-pembanding): kolaborasi maker dalam 30 menit -> 60 menit berikutnya?

Pertanyaan builder, dalam bentuk yang bisa difalsifikasi: bukan "apakah whale untung" (sudah dijawab:
tidak vs kerumunan, §F), tapi **apakah KOLOBORASI beberapa dompet berlabel pada satu token dalam
jendela pendek memisahkan hasil ke depan**. Kalau ya, itu produk: sinyal yang tidak bisa dibuat
trader manual dengan kecepatan sama. Kalau tidak, hipotesis "cocokkan dengan whale" mati dengan
angka, bukan dengan perasaan.

Yang membedakan alat ini dari `smartmoney_score.py` (panel vs kerumunan pada Dune, 4 jam, GROSS):
  - bahan = rekaman KAMI sendiri (24.509 tx, 27.9k baris harga `px` per ±2 menit);
  - harga masuk = `p` dari baris transaksi itu sendiri (harga saat order diisi), bukan harga
    snapshot - jadi tidak ada selisih satuan yang bisa bersembunyi;
  - satuan waktu DIASUMSIKAN detik dan diperiksa (lihat `_cek_satuan`): `flow_cluster_test` versi
    pertama mencampur milidetik ke dataset detik dan hasilnya nol kejadian - itu alat yang salah,
    bukan pasar yang sepi, dan tanpa pemeriksaan ini bedanya tidak terlihat;
  - pembanding = kejadian maker-tunggal (K=1) pada token yang sama + "cuaca" = seluruh px→px pada
    token yang sama. Kontrol "arah acak pada token & jam yang sama" dari §B dibuat konkret di sini.

Definisi:
  K(T,t)     = jumlah maker BERBEDA yang membeli T pada [t-30m, t]
  masuk      = p transaksi pada t
  keluar     = median `px` di [t+H-15m, t+H+15m]   (H default 60 m)
  ekor       = ada `px` >= 2x / 4x masuk dalam (t, t+H]
  non-overlap= satu kejadian per token per H (yang pertama)
  statistik  = MEDIAN + bootstrap 4.000 (seed tetap) + proporsi ekor + tanda-uji eksak +
               BH α 0,10 lintas kelompok K. Mean dilaporkan, tidak dipakai sebagai kepala.

    python -X utf8 tools/flow_cluster_test.py
    python -X utf8 tools/flow_cluster_test.py --horizon 240 --window 30 --ks 2,3,5
Artefak: decisions/flow-cluster-<UTC>.json (+ rows_sha256)
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import costs  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

FLOW = os.path.join(ROOT, "universe", "wallet-flow.jsonl")
OUT_DIR = os.path.join(ROOT, "decisions")
MIN = 60


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load():
    buys, px = {}, {}
    n = 0
    for ln in io.open(FLOW, encoding="utf-8", errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        d = json.loads(ln)
        tk = str(d.get("tk") or "").lower()
        t = int(d.get("t") or 0)
        if not tk or not t:
            continue
        if d.get("k") == "tx" and d.get("b"):
            p = float(d.get("p") or 0.0)
            if p > 0:
                buys.setdefault(tk, []).append((t, str(d.get("m") or "").lower(), p))
                n += 1
        elif d.get("k") == "px":
            p = float(d.get("p") or 0.0)
            if p > 0:
                px.setdefault(tk, []).append(t if False else (t, p))
    for d in (buys, px):
        for tk in d:
            d[tk].sort()
    return buys, px, n


def _cek_satuan(buys, px):
    """Median px/tx-p untuk buy yang punya px dalam 5 menit. Harus ~1.

    Ini jebakan yang benar-benar terjadi: versi pertama alat ini memakai konstanta milidetik pada
    dataset detik, dan yang keluar adalah NOL KEJADIAN - terbaca seperti "tidak ada sinyal",
    padahal tidak ada satu pun perbandingan yang terjadi. Selisihnya terlihat di sini, di output,
    bukan di belakang tabel kosong.
    """
    r = []
    for tk, bl in buys.items():
        ps = px.get(tk) or []
        if not ps:
            continue
        for t, m, p in bl:
            near = [q for tt, q in ps if abs(tt - t) <= 5 * MIN]
            if near and p > 0:
                r.append(sum(near) / len(near) / p)
    if not r:
        return None, 0
    r.sort()
    return r[len(r) // 2], len(r)


def boot_median(xs, draws=4000, alpha=0.05):
    if len(xs) < 6:
        return None, None
    rnd = random.Random(20260928)
    n, out = len(xs), []
    for _ in range(draws):
        s = sorted(xs[rnd.randrange(n)] for _ in range(n))
        out.append(s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2]))
    out.sort()
    return out[int(alpha / 2 * draws)], out[int((1 - alpha / 2) * draws)]


def med(xs):
    s = sorted(xs)
    return s[len(s) // 2] if len(s) % 2 else 0.5 * (s[len(s) // 2 - 1] + s[len(s) // 2])


def sign_p(k, n):
    """p satu arah "lebih banyak menang daripada kalah".

    Eksak sampai n=1000; di atas itu `math.comb(n, k)/2**n` meluapkan float (terjadi 28 Sep pada
    baseline "cuaca" dengan n ribuan) dan jatuh ke aproksimasi normal - DILAPORKAN apa adanya,
    karena p dari aproksimasi pada n besar bukan angka yang bisa diperdebatkan urutannya.
    """
    if not n:
        return 1.0
    if n <= 1000:
        return min(1.0, sum(math.comb(n, i) for i in range(k, n + 1)) / (2.0 ** n))
    ph = k / n
    z = (ph - 0.5) / math.sqrt(0.25 / n)
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def bh(pairs, alpha=0.10):
    o = sorted(pairs, key=lambda kv: kv[1])
    m = len(o)
    return {lab for i, (lab, p) in enumerate(o, 1) if p <= alpha * i / m}


def kof(b, t, W):
    return len({m for tt, m, _ in b if t - W <= tt <= t and m})


def collect(buys, px, horizon, window, ks):
    H, W = horizon * MIN, window * MIN
    buckets = {k: [] for k in set(ks) | {1}}
    skip = {"tidak_ada_px_sama_sekali": 0, "tidak_ada_px_keluar": 0, "calon_diuji": 0}
    for tk, bl in buys.items():
        ps = px.get(tk) or []
        if not ps:
            skip["tidak_ada_px_sama_sekali"] += 1
            continue
        taken = []
        for t, m, p0 in bl:
            if any(abs(t - x) < H for x in taken):
                continue
            k = kof(bl, t, W)
            if k not in buckets:
                continue
            skip["calon_diuji"] += 1
            out = [q for tt, q in ps if t + H - 15 * MIN <= tt <= t + H + 15 * MIN]
            if not out:
                skip["tidak_ada_px_keluar"] += 1
                continue
            p1 = med(out)
            tail = [q for tt, q in ps if t < tt <= t + H]
            buckets[k].append({"tk": tk, "t": t, "K": k,
                               "net_bps": round(10000.0 * (p1 - p0) / p0 - costs.rt_cost(), 1),
                               "gross_bps": round(10000.0 * (p1 - p0) / p0, 1),
                               "x2": any(q >= 2 * p0 for q in tail),
                               "x4": any(q >= 4 * p0 for q in tail),
                               "half": any(q <= 0.5 * p0 for q in tail)})
            taken.append(t)
    weather = []
    for tk, ps in px.items():
        if tk not in buys or len(ps) < 4:
            continue
        for i, (t, p) in enumerate(ps):
            j = next((j for j in range(i + 1, len(ps)) if ps[j][0] >= t + H), None)
            if j is not None and ps[j][0] <= t + H + 15 * MIN:
                weather.append(10000.0 * (ps[j][1] - p) / p - costs.rt_cost())
    return buckets, skip, weather


def report(label, ev, ps_list=None):
    if len(ev) < 6:
        print("  %-16s %6d  sampel tidak cukup - TIDAK DIUJI (bukan nol)" % (label, len(ev)))
        return None
    xs = [e["net_bps"] for e in ev]
    lo, hi = boot_median(xs)
    wins = sum(1 for v in xs if v > 0)
    p = sign_p(wins, len(xs))
    # gross == 0 persis berarti harganya tidak BERGESER pada resolusi yang kami simpan. Kalau ini
    # besar, "median = -ongkos" bukan kesimpulan: itu batas ketelitian data, dan ia harus muncul
    # di baris yang sama dengan medianya, bukan di catatan kaki.
    frozen = sum(1 for e in ev if e.get("gross_bps") == 0.0)
    row = {"kelompok": label, "n": len(xs), "median_net_bps": round(med(xs), 1),
           "ci_lo": None if lo is None else round(lo, 1),
           "ci_hi": None if hi is None else round(hi, 1),
           "mean_net_bps": round(sum(xs) / len(xs), 1),
           "proporsi_net_positif": round(100.0 * wins / len(xs), 1),
           "proporsi_net_ge_2000bps": round(100.0 * sum(1 for v in xs if v >= 2000) / len(xs), 1),
           "proporsi_harga_diam": round(100.0 * frozen / len(xs), 1),
           "p_sign": round(p, 4)}
    print("  %-16s %6d med %+8.1f  CI %s  mean %+9.1f  >0 %5.1f%%  >=20x %5.1f%%  diam %5.1f%%  p %.4f"
          % (label, len(xs), row["median_net_bps"],
             ("[%+.0f; %+.0f]" % (lo, hi)) if lo is not None else "[ - ; - ]",
             row["mean_net_bps"], row["proporsi_net_positif"],
             row["proporsi_net_ge_2000bps"], row["proporsi_harga_diam"], p))
    if ps_list is not None:
        ps_list.append((label, p))
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizon", type=int, default=60, help="menit")
    ap.add_argument("--window", type=int, default=30, help="menit untuk menghitung maker berbeda")
    ap.add_argument("--ks", default="2,3,5")
    a = ap.parse_args()
    ks = sorted({int(x) for x in a.ks.split(",") if x.strip().isdigit()})
    rt = costs.rt_cost()

    buys, px, n_buy = load()
    ratio, nr = _cek_satuan(buys, px)
    print("bahan: %d baris beli | %d token dengan beli | %d token dengan px sendiri | ongkos %.1f bps (%s)"
          % (n_buy, len(buys), len(px), rt, costs.cost_basis()))
    print("cek satuan: median px/harga-transaksi = %s pada %d pasangan (harus ~1)\n"
          % (("%.3f" % ratio) if ratio else "TIDAK ADA PASANGAN", nr))
    if ratio is None:
        print("  ! tidak ada satu pun pasangan px/transaksi - joinnya rusak, berhenti.")
        return
    if not (0.5 <= ratio <= 2.0):
        print("  ! rasio px/transaksi %.2f - dua angka itu bukan satuan yang sama. "
              "JANGAN baca tabel di bawah sebagai hasil." % ratio)
        return

    print("aturan: K maker berbeda dalam %d m | horizon %d m | non-overlap per token | "
          "kepala = median + bootstrap, bukan mean\n" % (a.window, a.horizon))
    buckets, skip, weather = collect(buys, px, a.horizon, a.window, ks)
    rows, ps = [], []
    for k in sorted(buckets):
        lab = "pembanding K=1" if k == 1 else "kohor K>=%d" % k
        r = report(lab, buckets[k], None if k == 1 else ps)
        if r:
            r["K"] = k
            rows.append(r)
    rw = report("cuaca (semua px)", [{"net_bps": v} for v in weather]) if weather else None
    if rw:
        rows.append(rw)

    lolos = bh(ps)
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "horizon_menit": a.horizon, "window_menit": a.window, "cost_bps_rt": rt,
           "cost_basis": costs.cost_basis(), "rasio_satuan_px_terhadap_tx": ratio,
           "tx_dibaca": n_buy, "token_dengan_px": len(px), "skip": skip,
           "rows": rows, "lolos_bh": sorted(lolos),
           "verdict": ("TIDAK ADA KELOMPOK KOHOR YANG LOLOS BH" if not lolos
                       else "ADA: " + ", ".join(sorted(lolos))),
           "batas": ["K dari feed kami sendiri = batas bawah: maker yang tidak muncul di jendela "
                     "itu tidak dihitung, jadi K terkecil pun bisa sebenarnya lebih besar",
                     "panel = pilihan GMGN (smartmoney/kol) -> tercemar retrospektif, §B",
                     "horizon 60 m karena jendela px kami median 27 m; 240 m hanya punya ~479 token",
                     "harga keluar = median px dalam ±15 m; kalau token keluar dari sorotan sebelum "
                     "horizon, ia TIDAK DIUJI, bukan dinilai nol",
                     "ini uji satu jendela rekaman (±36 jam): bukan pengganti Uji A prospektif"]}
    out["rows_sha256"] = "0x" + hashlib.sha256(canon(rows).encode()).hexdigest()
    os.makedirs(OUT_DIR, exist_ok=True)
    p = os.path.join(OUT_DIR, "flow-cluster-%s.json" % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True,
              ensure_ascii=False)
    c = skip["calon_diuji"] or 1
    print("\nsensor (INI bagian dari hasilnya, bukan kaki): %d kandidat diuji, %d dibuang karena "
          "tidak ada harga pada jendela keluar (%.1f %%). Yang dibuang itu token yang KEHILANGAN "
          "dari sorotan sebelum horizon - persis kelompok yang hasilnya paling ingin kita tahu."
          % (skip["calon_diuji"], skip["tidak_ada_px_keluar"],
             100.0 * skip["tidak_ada_px_keluar"] / c))
    print("skip lain: %s" % {k: v for k, v in skip.items()
                              if k not in ("calon_diuji", "tidak_ada_px_keluar")})
    print("verdict: %s" % out["verdict"])
    print("artefak: decisions/%s rows_sha256=%s…" % (os.path.basename(p), out["rows_sha256"][:16]))


if __name__ == "__main__":
    main()
