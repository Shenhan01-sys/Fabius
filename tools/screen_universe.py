"""Screener universe BSC di atas snapshot point-in-time — menolak dulu, baru menilai.

Filosofi: keluarkan angka penolakan, bukan angka cuan. Untuk tiap token yang lolos penyaringan
kita catat apa yang terjadi padanya pada window-window berikutnya, dan untuk tiap token yang
DITOLAK kita catat hal yang sama. Perbandingan itulah hasilnya: apakah alasan penolakan punya
isi, atau cuma seremoni. Tidak ada satu pun klaim return di sini.

Aturan baca dataset (dikutip dari _research/universe/README.md):
  - satu jendela = satu bucket `epoch // 3600`, baris PERTAMA bucket itu yang dipakai;
    baris tambahan dalam jam yang sama adalah duplikat dari jalankan-sekali manual, BUKAN sampel;
  - baris tanpa kunci "schema" memakai semantik lama (veto volume tidak jalan untuk baris GMGN,
    belum ada blind_spots) -> dihitung tapi dilaporkan terpisah;
  - `age` dan `liquidity` adalah alasan penolakan struktural, bukan kegagalan agen.

Konstanta yang dirujuk (semua dari kode, bukan dari dokumen turunan — lihat
Vault/05-research/Metodologi-Validasi-Edge-Audit.md):
  biaya per sisi  = 5,5 bps taker + 4,5 bps spread/slippage = 10 bps  (edge_lab.py:23,24,28)
  round-trip      = 2 * COST = 20 bps                                 (edge_lab.py:110,123)
  ambang eig      = net > 20 bps -> gross > 40 bps                    (edge_lab.py:121,125)
  floor sampel    = 20 trade OOS non-overlap 24 jam                   (edge_lab.py:30,126)
  FDR             = Benjamini-Hochberg alpha 0.10, step-up benar       (edge_lab.py:67,71-82)
  yang TIDAK ADA di kode rujukan: koreksi FDR LINTAS ASET (hanya per-aset, m<=4).
  Di file ini keluarga multipelnya dihitung global, dan itu memang salah satu
  perbaikan yang kami klaim.

Tidak butuh API, tidak butuh kunci, tidak mengirim transaksi.
Pakai:  python tools/screen_universe.py            # ringkasan + tulis out/screen_report.json
       python tools/screen_universe.py --windows   # sertakan tabel per window
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))          # .../TradingAgent/tools
PROJECT = os.path.dirname(os.path.dirname(HERE))           # .../Bnb-Indonesia-Hackathon
DATA = os.path.join(PROJECT, "_research", "universe", "bsc-universe.jsonl")
OUT_DIR = os.path.join(HERE, "out")

# ---- konstanta biaya, diekstrak dari kode rujukan (lihat docstring) ----
FEE_SIDE = 0.00055          # 5,5 bps taker per sisi
SLIP_SIDE = 0.00045         # 4,5 bps spread+slippage per sisi
COST_SIDE = FEE_SIDE + SLIP_SIDE
RT_COST_BPS = 2 * COST_SIDE * 1e4      # 20,0 bps round-trip (2 kaki)
GATE_NET_BPS = RT_COST_BPS             # syarat: net harus > biaya satu round-trip lagi
GATE_GROSS_BPS = RT_COST_BPS + GATE_NET_BPS   # -> gross > 40 bps
BH_ALPHA = 0.10
MIN_SAMPLES = 20


def pval_mean_positive(rets):
    """p-value satu arah H0: mean(ret) <= 0, aproksimasi normal.

    Catatan penting: kode rujukan memakai normal approx dengan n=20-40 dan itu membuat p-value
    sistematis terlalu kecil (seharusnya t-Student). Kami pakai di sini supaya angkanya sebanding,
    tapi TIDAK mengklaimnya tepat; floor MIN_SAMPLES dan BH global di bawah yang menahan kebodohan,
    dan selisihnya dicatat sebagai batas, bukan disembunyikan.
    """
    n = len(rets)
    if n < 2:
        return 1.0
    mean = sum(rets) / n
    var = sum((r - mean) ** 2 for r in rets) / (n - 1)
    if var <= 0:
        return 1.0
    z = mean / math.sqrt(var / n)
    return 0.5 * math.erfc(-z / math.sqrt(2.0))


def benjamini_hochberg(pvals, alpha=BH_ALPHA):
    """Step-up BH. Keluarga = semua pengujian yang benar-benar dijalankan, BUKAN per-aset."""
    items = sorted(((k, v) for k, v in pvals.items() if v is not None), key=lambda kv: kv[1])
    m = len(items)
    passed = {k: False for k in pvals}
    if m == 0:
        return passed, 0
    kmax = 0
    for i, (_, p) in enumerate(items, start=1):
        if p <= alpha * i / m:
            kmax = i
    for i, (k, _) in enumerate(items, start=1):
        passed[k] = i <= kmax
    return passed, m


def load_windows(path=DATA):
    """Baca JSONL, dedupe per jam, pisahkan skema lama vs baru."""
    if not os.path.exists(path):
        raise SystemExit(f"dataset belum ada: {path}")
    by_window, legacy = {}, 0
    total_lines = 0
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        total_lines += 1
        snap = json.loads(line)
        w = int(snap["epoch"]) // 3600
        if snap.get("schema") != 2:
            legacy += 1
            if w not in by_window:      # window lama tetap dihitung, ditandai di laporan
                by_window[w] = (snap, False)
            continue
        if w not in by_window or (by_window[w][1] is False):
            by_window[w] = (snap, True)
    windows = [by_window[w] for w in sorted(by_window)]
    return windows, {"lines": total_lines, "legacy_lines": legacy, "windows": len(windows)}


def build_observations(windows):
    """Seri per token lintas window: umur, likuiditas, harga, dan status veto tiap window."""
    obs = defaultdict(list)
    for snap, modern in windows:
        ts = int(snap["epoch"])
        for row in snap.get("rows", []):
            addr = (row.get("address") or row.get("base_token") or "").lower()
            if not addr:
                continue
            obs[addr].append({
                "window": ts // 3600,
                "modern": modern,
                "label": row.get("symbol") or row.get("name") or addr[:10],
                "price": row.get("price") if row.get("price") is not None else row.get("price_usd"),
                "liquidity": row.get("liquidity"),
                "age_sec": row.get("age_sec"),
                "vetoes": row.get("vetoes") or [],
                "survived": bool(row.get("survivable")),
                "blind": len(row.get("blind_spots") or []),
                "holders": row.get("holder_count"),
                "bundler": row.get("bundler_rate"),
                "lock": row.get("lock_percent"),
                "top10": row.get("top_10_holder_rate"),
            })
    for a in obs:
        obs[a].sort(key=lambda r: r["window"])
    return obs


def forward_moves(obs):
    """Perubahan harga forward untuk tiap (token, window) yang punya pasangan.

    Sengaja jujur soal covisibility: tidak semua token muncul di window berikutnya, dan token yang
    hilang dari daftar trending biasanya karena sudah tidak likuid - itu bukan 'hasil 0%'. Yang
    hilang kami catat sebagai hilang, bukan sebagai nol.
    """
    out = []
    lost = 0
    for addr, rows in obs.items():
        priced = [(r["window"], r["price"], r) for r in rows if r.get("price")]
        for i in range(len(priced) - 1):
            w0, p0, r0 = priced[i]
            w1, p1, _ = priced[i + 1]
            gap = w1 - w0
            if p0 <= 0 or gap <= 0:
                continue
            out.append({"addr": addr, "label": r0["label"], "gap_windows": gap,
                        "ret": (p1 / p0) - 1.0, "survived": r0["survived"],
                        "vetoes": r0["vetoes"], "modern": r0["modern"]})
        if priced:
            last_w = priced[-1][0]
            if last_w < max(r["window"] for rs in obs.values() for r in rs) - 1:
                lost += 1
    return out, lost


def cohort_stats(items):
    if not items:
        return {"n": 0}
    rets = [it["ret"] for it in items]
    n = len(rets)
    mean = sum(rets) / n
    med = sorted(rets)[n // 2]
    return {
        "n": n,
        "mean_bps": round(mean * 1e4, 1),
        "median_bps": round(med * 1e4, 1),
        "share_negative_pct": round(100.0 * sum(1 for r in rets if r < 0) / n, 1),
        "worst_bps": round(min(rets) * 1e4, 1),
        "best_bps": round(max(rets) * 1e4, 1),
    }


def reason_breakdown(items):
    """Per alasan penolakan: berapa kali muncul, dan apa yang terjadi pada korbannya."""
    agg = defaultdict(list)
    for it in items:
        if not it["vetoes"]:
            continue
        for v in it["vetoes"]:
            agg[v.split("<")[0] + ("<thr" if "<" in v else "")].append(it)
    return {k: {"n": len(v), **cohort_stats(v)} for k, v in sorted(agg.items(), key=lambda kv: -len(kv[1]))}


def token_level(moves):
    """Ringkas pasangan forward MENURUT TOKEN, bukan menurut pasangan.

    Ini koreksi atas kesalahan yang persis sama yang kami temukan di metodologi rujukan:
    menghitung ulang observasi yang berkerumun. Satu token yang muncul di 6 window menghasilkan
    5 pasangan, tapi itu SATU token - bukan 5 sampel bebas. Angka yang boleh dikutip sebagai n
    adalah jumlah token, dan selisihnya harus terlihat, bukan disembunyikan."""
    per = defaultdict(list)
    for m in moves:
        per[m["addr"]].append(m["ret"])
    return per


def cohort_by_token(moves):
    per = token_level(moves)
    if not per:
        return {"tokens": 0, "pairs": 0}
    means = [sum(v) / len(v) for v in per.values()]
    n = len(means)
    return {
        "tokens": n,
        "pairs": sum(len(v) for v in per.values()),
        "median_of_token_means_bps": round(sorted(means)[n // 2] * 1e4, 1),
        "share_tokens_negative_pct": round(100.0 * sum(1 for m in means if m < 0) / n, 1),
        "worst_token_bps": round(min(min(v) for v in per.values()) * 1e4, 1),
        "mean_pairs_per_token": round(sum(len(v) for v in per.values()) / n, 2),
    }


def main():
    show_windows = "--windows" in sys.argv
    windows, meta = load_windows()
    obs = build_observations(windows)
    moves, lost = forward_moves(obs)

    survived = [m for m in moves if m["survived"]]
    refused = [m for m in moves if not m["survived"]]

    # Keluarga multipel GLOBAL: satu tes = (token, horizon) yang benar-benar diuji.
    # Ini yang tidak ada padanan kodenya di metodologi rujukan.
    pvals = {}
    buckets = defaultdict(list)
    for m in moves:
        key = f"{m['addr'][:12]}@{m['gap_windows']}"
        buckets[key].append(m["ret"])
    for key, rets in buckets.items():
        if len(rets) >= 2:
            pvals[key] = pval_mean_positive(rets)
    passed, m_family = benjamini_hochberg(pvals)
    n_signif = sum(1 for v in passed.values() if v)

    print("=" * 78)
    print("BSC memecoin screener — apa yang kami TOLAK, dan apa yang terjadi selanjutnya")
    print("=" * 78)
    print(f"baris dataset   : {meta['lines']}  (legacy pra-skema2: {meta['legacy_lines']})")
    print(f"jendela jam riil: {meta['windows']}   <- ini n sebenarnya, bukan jumlah baris")
    print(f"token berbeda   : {len(obs)}")
    print(f"pasangan harga forward: {len(moves)}   token yang hilang dari daftar: {lost}"
          "   (hilang != return 0%)")
    print()
    print(f"{'koort':<34}{'n':>7}{'mean bps':>11}{'median':>9}{'% negatif':>11}{'worst':>10}")
    for label, items in (("LOLOS semua veto (survived)", survived), ("DITOLAK (setidaknya 1 veto)", refused)):
        s = cohort_stats(items)
        if s.get("n"):
            print(f"{label:<34}{s['n']:>7}{s['mean_bps']:>11}{s['median_bps']:>9}"
                  f"{s['share_negative_pct']:>11}{s['worst_bps']:>10}")
        else:
            print(f"{label:<34}{0:>7}{'-':>11}{'-':>9}{'-':>11}{'-':>10}")
    print()
    print("per alasan penolakan (korban vs hasil):")
    for reason, st in list(reason_breakdown(refused).items())[:10]:
        print(f"  {reason:<26} n={st['n']:>5}  mean {st.get('mean_bps','-'):>9} bps  "
              f"median {st.get('median_bps','-'):>9} bps  negatif {st.get('share_negative_pct','-')}%")
    print()
    tok_surv = cohort_by_token(survived)
    tok_ref = cohort_by_token(refused)

    print(f"unit sebenarnya = TOKEN, bukan pasangan:")
    for label, st in (("LOLOS semua veto", tok_surv), ("DITOLAK", tok_ref)):
        if st.get("tokens"):
            print(f"  {label:<16} tokens={st['tokens']:>4}  pasangan={st['pairs']:>4} "
                  f"(rata-rata {st['mean_pairs_per_token']} obs/token)  "
                  f"median {st['median_of_token_means_bps']} bps  "
                  f"negatif {st['share_tokens_negative_pct']}%  terburuk {st['worst_token_bps']} bps")
        else:
            print(f"  {label:<16} tokens=0   <- kohort ini TIDAK terukur: tidak ada barisnya yang "
                  f"punya harga pada window berikutnya")

    print()
    print(f"FDR global (Benjamini-Hochberg, alpha={BH_ALPHA}): keluarga {m_family} tes, "
          f"{n_signif} lolos")
    print("  KERANGKANYA benar, angkanya BELUM boleh dikutip: satu tes di sini masih per "
          "(token x horizon), dan token yang sama menyumbang beberapa horizon -> keluarga "
          "p-value-nya berkerumun. Perbaiki unitnya dulu (satu tes per token) sebelum menyebut "
          "angka ini di depan siapa pun.")
    enough = tok_ref.get("tokens", 0) >= MIN_SAMPLES and tok_surv.get("tokens", 0) >= MIN_SAMPLES
    print(f"  floor sampel {MIN_SAMPLES} per kohort: refused={tok_ref.get('tokens', 0)} "
          f"survived={tok_surv.get('tokens', 0)} -> "
          f"{'memadai untuk perbandingan awal' if enough else 'BELUM memadai; yang dilaporkan baru distribusi penolakan, bukan kesimpulan edge'}")
    print("\nBatas yang tidak dihapus alat ini:")
    print("  - perubahan harga antar-window bukan trade yang bisa dieksekusi: tidak ada slippage")
    print("    nyata, tidak ada ukuran posisi, dan token trending menyempit saat dicoba dijual;")
    print("  - skor penolakan mengukur 'apakah yang kami tolak ternyata buruk', BUKAN")
    print("    'apakah yang kami loloskan untung' - yang kedua butuh jendela jauh lebih panjang;")
    print("  - tidak ada satu pun angka di halaman ini yang boleh dikutip sebagai prediksi return.")

    os.makedirs(OUT_DIR, exist_ok=True)
    report = {
        "meta": meta, "distinct_tokens": len(obs), "forward_pairs": len(moves),
        "dropped_from_list": lost,
        "cohorts": {"survived": cohort_stats(survived), "refused": cohort_stats(refused)},
        "by_reason": reason_breakdown(refused),
        "fdr": {"family_tests": m_family, "alpha": BH_ALPHA, "passed": n_signif},
        "constants": {"FEE_SIDE": FEE_SIDE, "SLIPPAGE_SIDE": SLIP_SIDE, "COST_SIDE": COST_SIDE,
                      "RT_COST_BPS": RT_COST_BPS, "GATE_GROSS_BPS": GATE_GROSS_BPS,
                      "MIN_SAMPLES": MIN_SAMPLES, "BH_ALPHA": BH_ALPHA},
        "limits": ["bukan trade yang bisa dieksekusi", "tanpa slippage nyata",
                   "tanpa ukuran posisi", "bukan prediksi return"],
    }
    path = os.path.join(OUT_DIR, "screen_report.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    print(f"\ntertulis: {path}")

    if show_windows:
        print("\nwindow per window:")
        for snap, modern in windows:
            print(f"  {snap['snapshot_utc']}  schema2={'ya' if modern else 'TIDAK  '}  "
                  f"universe={snap.get('universe_size')}  lolos={snap.get('survivable_count')}  "
                  f"dinilai_penuh={snap.get('fully_evaluated_count', '-')}")


if __name__ == "__main__":
    main()
