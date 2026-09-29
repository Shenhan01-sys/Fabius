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
import bisect
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
PX_DUPES = 0   # diisi load(): berapa baris px yang harus dilebur jadi satu harga per stempel


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def dedupe_px(series):
    """Kanonik: SATU harga per (token, stempel waktu) = median harga pada stempel itu.

    Kenapa perlu (ditemukan 28 Sep saat dua alat kami memberi angka berbeda untuk kejadian yang
    sama): perekam menulis beberapa baris `px` dengan `t` yang sama untuk satu token - batch
    trending datang per sumber, dan `smartmoney` + `kol` melihat pool yang sama di siklus yang
    sama. Selama duplikat itu dibiarkan, "harga masuk" bergantung pada cara kita MENGURUTKAN
    (`.sort()` pada tuple ikut memakai harga sebagai pemecah seri; `.sort(key=t)` tidak) - dan dua
    alat yang jujur menghasilkan dua outcome berbeda. Aturan pembatal ambiguitas harus ada di data,
    bukan di kebetulan urutan.
    """
    by_t = {}
    for t, p in series:
        by_t.setdefault(t, []).append(p)
    out = [(t, med(v)) for t, v in sorted(by_t.items())]
    return out


def load():
    buys, pxr = {}, {}
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
                pxr.setdefault(tk, []).append((t, p))
    px = {}
    for tk, s in pxr.items():
        px[tk] = dedupe_px(s)
    global PX_DUPES
    PX_DUPES = sum(len(s) - len(px[tk]) for tk, s in pxr.items())
    for tk in buys:
        buys[tk].sort()
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


def mann_whitney_p(a, b):
    """p satu arah: distribusi `a` bergeser NAIK terhadap `b` (kohor vs maker-tunggal).

    DIPERBAIKI 29 Sep 2026 - dan ini bukan kosmetik. Versi pertama menyusun daftar untuk ranking
    dengan `sorted(a) + sorted(b)`, jadi dua kelompok yang tidak tumpang tindih masuk dalam urutan
    TURUN dan `a` dapat peringkat paling rendah: pada A=+120..+144 vs B=-300..-324 (A jelas menang)
    alat ini mengembalikan p=1,0, bukan p~0. Bug kedua: pada nilai sama (ties), tiap elemen `a`
    dijumlah dengan `sum(ranks[v])` = rata-rata peringkat x jumlah anggota kelompok, bukan rata-rata
    peringkatnya sendiri. Keduanya membuat p bergantung pada bentuk data, bukan pada arahnya - dan
    harga yang "diam" di feed kami penuh ties. Semua angka yang dikutip dari fungsi ini di vault
    WAJIB dihitung ulang (registry T1 baris 38 mencatat perintahnya).
    """
    na, nb = len(a), len(b)
    if na < 5 or nb < 5:
        return None
    vals = sorted(list(a) + list(b))
    rank, i, tie_groups = {}, 0, []
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[j + 1] == vals[i]:
            j += 1
        avg = (i + j) / 2.0 + 1.0          # peringkat rata-rata untuk semua anggota ties
        rank[vals[i]] = avg
        if j > i:
            tie_groups.append(j - i + 1)
        i = j + 1
    ra = sum(rank[v] for v in a)
    mu = na * (na + nb + 1) / 2.0
    n = na + nb
    tie_corr = sum(t ** 3 - t for t in tie_groups) / 12.0
    var = na * nb / 12.0 * ((n + 1) - tie_corr / (n * (n - 1.0)))
    if var <= 0:
        return None
    z = (ra - mu) / math.sqrt(var)
    return 0.5 * math.erfc(z / math.sqrt(2.0)) if z > 0 else 1.0 - 0.5 * math.erfc(-z / math.sqrt(2.0))


def mw_self_test():
    """Dua kasus yang versi lama jawab SALAH, plus satu kasus ties."""
    a = [120.0 + i for i in range(25)]
    b = [-300.0 - i for i in range(25)]
    p = mann_whitney_p(a, b)
    assert p is not None and p < 1e-6, ("A jelas di atas B tapi p=%s" % p)
    assert mann_whitney_p(b, a) > 0.999, "arah terbalik harus memberi p besar"
    x = [1.0] * 20 + [2.0] * 5
    y = [1.0] * 20 + [0.0] * 5
    assert mann_whitney_p(x, y) < 0.05, "ties: x seharusnya di atas y"
    assert abs(mann_whitney_p([1.0, 2.0, 3.0, 4.0, 5.0], [1.0, 2.0, 3.0, 4.0, 5.0]) - 0.5) < 0.06
    print("self-test mann_whitney_p OK: arah, terpisah total, ties, identik -> 0,5")


def fisher_p(a_pos, a_n, b_pos, b_n):
    """Eksak satu arah "proporsi positif di A lebih besar dari di B" (hipergeometrik, lgamma)."""
    from math import lgamma

    def lchoose(n, k):
        if k < 0 or k > n:
            return float("-inf")
        return lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1)

    tot_pos, tot_n = a_pos + b_pos, a_n + b_n
    if tot_pos == 0 or tot_n == 0 or a_n == 0 or b_n == 0:
        return None

    def p_of(x):
        return math.exp(lchoose(a_n, x) + lchoose(b_n, tot_pos - x) - lchoose(tot_n, tot_pos))

    lo, hi = max(0, tot_pos - b_n), min(a_n, tot_pos)
    obs = p_of(a_pos)
    if obs <= 0:
        return None
    tail = sum(p_of(x) for x in range(lo, hi + 1) if p_of(x) <= obs * (1 + 1e-9) and x >= a_pos)
    return min(1.0, tail / sum(p_of(x) for x in range(lo, hi + 1)))


def bh(pairs, alpha=0.10):
    o = sorted(pairs, key=lambda kv: kv[1])
    m = len(o)
    return {lab for i, (lab, p) in enumerate(o, 1) if p <= alpha * i / m}


def kof(b, t, W):
    return len({m for tt, m, _ in b if t - W <= tt <= t and m})


def bucket_of(k, ks):
    """KELAS KUMULATIF, bukan nilai persis.

    Versi pertama menyimpan kejadian di bucket `k` hanya kalau `k` kebetulan ada di daftar (1,2,3,5).
    Akibatnya, diukur hari ini: (a) label "K>=2" salah - yang terukur adalah "TEPAT 2 dompet";
    (b) 53 dari 2.592 kejadian (2,0 %) dengan K=4 atau K>=6 DIBUANG - persis kerumunan paling padat
    yang paling ingin kita tahu. Sekarang satu kejadian masuk ke semua kelas ">=kk" yang dia penuhi;
    acuannya tetap "tepat satu maker". Kelas jadi bersarang (K>=3 subset dari K>=2), jadi angka
    antar-baris TIDAK boleh dijumlahkan dan tumpang tindih itu harus disebut.
    """
    if k == 1:
        return [1]
    return [kk for kk in ks if k >= kk]


def collect(buys, px, horizon, window, ks, entry="tx"):
    H, W = horizon * MIN, window * MIN
    buckets = {k: [] for k in set(ks) | {1}}
    skip = {"tidak_ada_px_sama_sekali": 0, "tidak_ada_px_keluar": 0, "calon_diuji": 0,
            "tidak_ada_px_masuk": 0}
    for tk, bl in buys.items():
        ps = px.get(tk) or []
        if not ps:
            skip["tidak_ada_px_sama_sekali"] += 1
            continue
        ts_list = [tt for tt, _ in ps]
        taken = []
        for t, m, p0 in bl:
            if any(abs(t - x) < H for x in taken):
                continue
            k = kof(bl, t, W)
            kelas = bucket_of(k, ks)
            if not kelas:
                continue
            skip["calon_diuji"] += 1
            if entry == "px":
                # SATU sumber harga untuk kedua ujung. Versi pertama memakai `p` transaksi untuk
                # masuk dan `px` pool untuk keluar - dan median rasionya 0,946 (terukur), artinya
                # tiap posisi mulai dengan handicap ~5 % yang bukan bagian dari pasar mana pun.
                i = bisect.bisect_right(ts_list, t) - 1
                if i < 0 or t - ts_list[i] > 10 * MIN:
                    skip["tidak_ada_px_masuk"] += 1
                    continue
                p0 = ps[i][1]
            out = [q for tt, q in ps if t + H - 15 * MIN <= tt <= t + H + 15 * MIN]
            if not out:
                skip["tidak_ada_px_keluar"] += 1
                continue
            p1 = med(out)
            tail = [q for tt, q in ps if t < tt <= t + H]
            ev = {"tk": tk, "t": t, "K": k,
                  "net_bps": round(10000.0 * (p1 - p0) / p0 - costs.rt_cost(), 1),
                  "gross_bps": round(10000.0 * (p1 - p0) / p0, 1),
                  "x2": any(q >= 2 * p0 for q in tail),
                  "x4": any(q >= 4 * p0 for q in tail),
                  "half": any(q <= 0.5 * p0 for q in tail)}
            for kk in kelas:
                buckets[kk].append(dict(ev, kelas=kk))
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


def report(label, ev, ps_list=None, quiet=False):
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
    if not quiet:
        print("  %-16s %6d med %+8.1f  CI %s  mean %+9.1f  >0 %5.1f%%  >=20x %5.1f%%  diam %5.1f%%  p %.4f"
              % (label, len(xs), row["median_net_bps"],
                 ("[%+.0f; %+.0f]" % (lo, hi)) if lo is not None else "[ - ; - ]",
                 row["mean_net_bps"], row["proporsi_net_positif"],
                 row["proporsi_net_ge_2000bps"], row["proporsi_harga_diam"], p))
    if ps_list is not None:
        ps_list.append((label, p))
    return row


def paired(buckets, ks):
    """Bandingkan K=1 vs K>=k HANYA pada token yang memproduksi keduanya.

    Tanpa ini, "kohor lebih sering positif" bisa berarti apa pun: token yang ramai dibeli memang
    token yang sedang naik dan yang harganya terus kami pull. Di dalam token yang sama, pertanyaan
    "apakah kerumunan menambah probabilitas" punya jawaban yang tidak bisa diborong oleh nasib
    satu ticker.
    """
    base = {}
    for e in buckets.get(1) or []:
        base.setdefault(e["tk"], []).append(e)
    out = []
    for k in ks:
        d, toks = [], set()
        for e in buckets.get(k) or []:
            peers = base.get(e["tk"]) or []
            if not peers:
                continue
            d.append(e["net_bps"] - med([q["net_bps"] for q in peers]))
            toks.add(e["tk"])
        if len(d) < 6:
            out.append({"kelompok": "K>=%d" % k, "berpasangan": True, "n": len(d),
                        "status": "TIDAK ADA TOKEN BERPASANGAN"})
            continue
        lo, hi = boot_median(d)
        wins = sum(1 for v in d if v > 0)
        out.append({"kelompok": "K>=%d" % k, "berpasangan": True, "token": len(toks), "n": len(d),
                    "median_selisih_bps": round(med(d), 1),
                    "ci_lo": None if lo is None else round(lo, 1),
                    "ci_hi": None if hi is None else round(hi, 1),
                    "proporsi_selisih_positif": round(100.0 * wins / len(d), 1),
                    "p_sign": round(sign_p(wins, len(d)), 4)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizon", type=int, default=60, help="menit")
    ap.add_argument("--window", type=int, default=30, help="menit untuk menghitung maker berbeda")
    ap.add_argument("--ks", default="2,3,5")
    ap.add_argument("--entry", default="px", choices=("px", "tx"),
                    help="sumber harga masuk; 'px' = satu sumber untuk kedua ujung (baku), "
                         "'tx' = harga transaksi (punya offset ~5 % vs px - untuk perbandingan)")
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

    print("aturan: K maker berbeda dalam %d m | horizon %d m | harga masuk = %s | "
          "non-overlap per token | kepala = median + bootstrap, bukan mean\n"
          % (a.window, a.horizon, a.entry))
    buckets, skip, weather = collect(buys, px, a.horizon, a.window, ks, a.entry)
    rows, ps, ps_f = [], [], []
    ref = [e["net_bps"] for e in (buckets.get(1) or [])]
    ref_pos = sum(1 for e in (buckets.get(1) or []) if e["net_bps"] > 0)
    print("  %-16s %6s %9s %-19s %8s %8s %8s %8s %9s %9s"
          % ("kelompok", "n", "median", "CI 95 % median", ">0", ">=20x", "diam",
             "p_satu", "p_MW vs K1", "p_Fisher"))
    for k in sorted(buckets):
        ev = buckets[k]
        lab = "pembanding K=1" if k == 1 else "kohor K>=%d" % k
        r = report(lab, ev, None, quiet=True)
        if not r:
            print("  %-16s %6d  sampel tidak cukup - TIDAK DIUJI (bukan nol)" % (lab, len(ev)))
            rows.append({"kelompok": lab, "K": k, "n": len(ev), "status": "SAMPEL TIDAK CUKUP"})
            continue
        pmw = pfish = None
        if k != 1:
            xs = [e["net_bps"] for e in ev]
            pmw = mann_whitney_p(xs, ref)
            pfish = fisher_p(sum(1 for v in xs if v > 0), len(xs), ref_pos, len(ref))
            if pmw is not None:
                ps.append((lab, pmw))
            if pfish is not None:
                ps_f.append((lab, pfish))
        print("  %-16s %6d %9.1f %-19s %7.1f%% %7.1f%% %7.1f%% %8.4f %9s %9s"
              % (lab, r["n"], r["median_net_bps"],
                 "[%+.0f; %+.0f]" % (r["ci_lo"], r["ci_hi"]) if r["ci_lo"] is not None else "[ - ; - ]",
                 r["proporsi_net_positif"], r["proporsi_net_ge_2000bps"], r["proporsi_harga_diam"],
                 r["p_sign"],
                 ("%.5f" % pmw) if pmw is not None else "-",
                 ("%.5f" % pfish) if pfish is not None else "-"))
        r["kelompok"], r["K"] = lab, k
        r["p_mannwhitney_vs_K1"] = None if pmw is None else round(pmw, 6)
        r["p_fisher_proporsi_positif"] = None if pfish is None else round(pfish, 6)
        rows.append(r)
    rw = report("cuaca (semua px)", [{"net_bps": v} for v in weather], quiet=True) if weather else None
    if rw:
        rw["kelompok"] = "cuaca (semua px)"
        rows.append(rw)
        print("  %-16s %6d %9.1f %-19s %7.1f%% %7.1f%% %7.1f%% %8.4f %9s %9s"
              % ("cuaca (semua px)", rw["n"], rw["median_net_bps"],
                 "[%+.0f; %+.0f]" % (rw["ci_lo"], rw["ci_hi"]), rw["proporsi_net_positif"],
                 rw["proporsi_net_ge_2000bps"], rw["proporsi_harga_diam"], rw["p_sign"], "-", "-"))

    lolos = bh(ps)
    lolos_f = bh(ps_f)
    pr = paired(buckets, ks)
    ps_p = [("K>=%d" % k, r["p_sign"]) for k, r in zip(ks, pr) if r.get("p_sign") is not None]
    lolos_p = bh(ps_p)
    print("\n  berpasangan DALAM TOKEN YANG SAMA (buang confound 'token ramai memang sedang naik'):")
    print("  %-16s %6s %6s %9s %-19s %8s %8s %s"
          % ("kelompok", "token", "n", "med selisih", "CI 95 %", ">0", "p_sign", "lolos BH"))
    for k, r in zip(ks, pr):
        if r.get("status"):
            print("  %-16s %6s %6d  %s" % (r["kelompok"], "-", r["n"], r["status"]))
            continue
        lab = "K>=%d" % k
        print("  %-16s %6d %6d %9.1f %-19s %7.1f%% %8.4f %s"
              % (lab, r["token"], r["n"], r["median_selisih_bps"],
                 "[%+.0f; %+.0f]" % (r["ci_lo"], r["ci_hi"]) if r["ci_lo"] is not None else "[ - ; - ]",
                 r["proporsi_selisih_positif"], r["p_sign"],
                 "YA" if lab in lolos_p else "-"))
    c_uji = skip["calon_diuji"] or 1
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "horizon_menit": a.horizon, "window_menit": a.window, "sumber_harga_masuk": a.entry,
           "cost_bps_rt": rt,
           "cost_basis": costs.cost_basis(), "rasio_satuan_px_terhadap_tx": ratio,
           "tx_dibaca": n_buy, "token_dengan_px": len(px), "skip": skip,
           "rows": rows, "berpasangan_dalam_token": pr, "lolos_bh_terpasang": sorted(lolos_p),
           "lolos_bh": sorted(lolos), "lolos_bh_fisher_proporsi": sorted(lolos_f),
           "dua_keluarga_tes": {"mannwhitney_per_kelompok": {k: round(v, 6) for k, v in ps},
                                "fisher_proporsi_positif": {k: round(v, 6) for k, v in ps_f}},
           "verdict": ("TIDAK ADA KELOMPOK KOHOR YANG LOLOS BH (dua keluarga tes)"
                       if not (lolos or lolos_f) else
                       "ADA: MW " + (", ".join(sorted(lolos)) or "-") +
                       " | FISHER " + (", ".join(sorted(lolos_f)) or "-")),
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
