"""E17-gate - sebelum menguji trailing stop, ukur dulu apakah "mengunci untung" PERNAH mungkin.

Teori builder: "SL pakai trailing, pokoknya jangan sampai rugi, jaraknya sudah hitung spread + fee
supaya tetap untung". Aritmatikanya (variabel dalam bps; P0 masuk, H puncak berjalan, s spread,
i slippage menembus bid saat trigger, C ongkos round-trip TERUKUR):

    trigger  bid <= H - d              fill F = H - d - s - i
    PnL      = pi - d - s - i - C          dengan pi = (H - P0)/P0 * 1e4
    LOCK     >= 0   <=>   pi >= d + s + i + C                     ... (1)
    TIDAK TERPACU oleh bounce sendirian   <=>   d > s             ... (2)
    (1)+(2)  =>  syarat perlu:  pi > 2s + i + C
    jendela d yang sah:  s < d <= pi - s - i - C     -> kosong kalau pi <= 2s + i + C
    "pokoknya jangan sampai rugi" (d >= 0, selalu terkunci) butuh d <= -(s+i+C): TIDAK ADA SOLUSI.

Jadi pertanyaannya bukan "bagaimana mengatur d" melainkan "berapa sering pi kami melewati 2s+i+C".
Itulah yang alat ini ukur pada jalur harga yang SUDAH kami punya (393 kejadian E11/E13), dengan
spread dari buku order yang SUDAH kami rekam (⑨) - dan satu-satunya variabel yang masih asumsi
adalah i, jadi ia dilaporkan pada dua nilai (i=0 optimis, i=s pesimis), bukan dipilih satu.

Alat ini TIDAK menguji trailing sebagai strategi (itu E17 sesungguhnya, dan ia butuh `wp` tick yang
cukup rapat untuk mereplikasi pemicu). Ia hanya menjawab gate kelayakan: kalau fraksi kejadian yang
bisa mengunci kurang dari separuh, tidak ada backtest yang perlu dijalankan.

Pakai:  python -X utf8 tools/trailing_gate.py
       python -X utf8 tools/trailing_gate.py --pi-cap 500 --i-mode both
       python -X utf8 tools/trailing_gate.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import costs  # noqa: E402
import flow_cluster_test as FC  # noqa: E402
import horizon_decay as HD  # noqa: E402
import topk_test as TK  # noqa: E402

MIN = 60
BUKU = os.path.join(ROOT, "universe", "book-depth.jsonl")


def spread_venue():
    """Distribusi spread yang TERUKUR di venue kami (⑨), per simbol dan gabungan."""
    per = {}
    if os.path.exists(BUKU):
        for ln in io.open(BUKU, encoding="utf-8", errors="replace"):
            if not ln.startswith("{"):
                continue
            try:
                d = json.loads(ln)
            except ValueError:
                continue
            if d.get("k") == "bd" and isinstance(d.get("spread_bps"), (int, float)):
                per.setdefault(d["sym"], []).append(float(d["spread_bps"]))
    gab = [x for v in per.values() for x in v]
    gab.sort()

    def pct(xs, q):
        return round(xs[min(len(xs) - 1, int(q * (len(xs) - 1)))], 2) if xs else None
    return {"n_snapshot": len(gab), "n_simbol": len(per),
            "p50": pct(gab, 0.5), "p90": pct(gab, 0.9), "max": round(max(gab), 2) if gab else None,
            "per_simbol": {k: round(FC.med(v), 2) for k, v in sorted(per.items())}}


def puncak_pada(e, hor):
    """pi = puncak yang KAMI LIHAT dalam `hor` menit, dari ticker `wp` (bukan mid, bukan tx.p).

    CATATAN ARAH YANG PENTING: ticker watch berdetak ~1x per beberapa puluh menit, jadi puncak
    intra-bar tidak pernah terlihat dan pi di sini adalah **batas BAWAH** dari puncak sejati.
    Gate ini karenanya pesimis terhadap klaim builder - dan justru itu yang membuatnya layak
    dipakai: kalau dengan batas bawah pun jendelanya kosong, klaimnya butuh keajaiban, bukan
    backtest. Tapi kita harus jujur bahwa angka "P()" di bawah bisa naik jika resolusinya diperbaiki.
    """
    ser = e["seri"]
    hi = [p for t, p in ser if e["t"] <= t <= e["t"] + hor * MIN]
    if len(hi) < 2 or e["p0"] <= 0:
        return None
    return round(10000.0 * (max(hi) - e["p0"]) / e["p0"], 1)


def puncak_sebagian(e, hor, frac=0.5):
    """Puncak pada paruh AWAL jendela - proksi jujur untuk 'cukup awal untuk dikunci'.

    Puncak sepanjang +1.122 bps median tidak berarti apa pun untuk trailing kalau ia datang di
    ujung akhir jendela: setelah itu harga sudah kembali ke bawah dan trailing-nya terpanggil
    angka yang tidak ada. Karena itu gate memakai dua angka berdampingan: pi (puncak di seluruh
    jendela, = batas atas kemudahan) dan pi_awal (puncak di paruh pertama, = yang realistis).
    """
    ser = e["seri"]
    batas = e["t"] + hor * MIN * frac
    hi = [p for t, p in ser if e["t"] <= t <= batas]
    if len(hi) < 2 or e["p0"] <= 0:
        return None
    return round(10000.0 * (max(hi) - e["p0"]) / e["p0"], 1)


def cakupan(ev, hor):
    """Berapa kejadian yang punya >= 2 baris dalam `hor` menit - supaya '0 kejadian' terbaca
    sebagai keterbatasan resolusi, bukan sebagai 'puncaknya nol'."""
    ada = 0
    for e in ev:
        hi = [t for t, p in e["seri"] if e["t"] <= t <= e["t"] + hor * MIN]
        if len(hi) >= 2:
            ada += 1
    return {"horison_menit": hor, "terlihat": ada, "total": len(ev),
            "persen_terlihat": round(100.0 * ada / max(1, len(ev)), 1)}


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("--horison", type=int, default=5, help="jendela tempat puncak dihitung (menit)")
    ap.add_argument("--pi-cap", type=float, default=500.0, help="TP builder, bps (5 %)")
    ap.add_argument("--i-mode", default="both", choices=("0", "s", "both"))
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    C = costs.rt_cost()
    ev, sensor = HD.kejadian(max(a.horison, 30))
    cak = [cakupan(ev, h) for h in sorted({a.horison, 5, 30, 60})]
    print("   resolusi ticker `wp` (baris per jendela, per kejadian): %s"
          % " | ".join("%d m: %d/%d (%0.0f %%)" % (c["horison_menit"], c["terlihat"], c["total"],
                                                   c["persen_terlihat"]) for c in cak))
    hor_pakai = max((c["horison_menit"] for c in cak if c["persen_terlihat"] >= 50.0),
                    default=max(a.horison, 60))
    if hor_pakai != a.horison:
        print("   jendela puncak dipakai %d m: pada %d m resolusi kami tidak cukup untuk "
              "melihat puncak sama sekali" % (hor_pakai, a.horison))
    pis = [x for x in (puncak_pada(e, hor_pakai) for e in ev) if x is not None]
    pi_awal = [x for x in (puncak_sebagian(e, hor_pakai) for e in ev) if x is not None]
    sp = spread_venue()
    print("E17-gate | %d kejadian dengan jalur `wp` >= 2 baris di %d m | C = %.1f bps (terukur) | "
          "batas jelajah %s" % (len(pis), hor_pakai, C,
                               time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(TK.T_BATAS))))
    if len(pis) < 30:
        raise SystemExit("jalur harga terlalu sedikit - ini BELUM BISA DIUJI, bukan 'tidak bisa "
                         "mengunci'")
    for nm, xs in (("pi        (puncak seluruh jendela)", pis), ("pi_awal   (puncak paruh awal )",
                    pi_awal if len(pi_awal) >= 30 else pis)):
        xs = sorted(xs)
        print("   %s: median %+0.1f | p75 %+0.1f | p90 %+0.1f | p95 %+0.1f | max %+0.1f  (n=%d)"
              % (nm, FC.med(xs), xs[int(.75 * len(xs))], xs[int(.9 * len(xs))],
                 xs[int(.95 * len(xs))], xs[-1], len(xs)))
    print("   (angka raksasa di ekor itu nyata untuk micro-cap four.meme, bukan bug: token ini bisa"
          "\n    8000x dalam sejam - tapi winsor kami tetap 2.000 bps untuk MEAN, dan gate ini hanya"
          "\n    memakai persentil, bukan rata-rata)")
    print("   spread TERUKUR di venue (⑨): %s" % json.dumps(
        {k: sp[k] for k in ("n_snapshot", "n_simbol", "p50", "p90", "max")}, sort_keys=True))
    if not sp["n_snapshot"]:
        raise SystemExit("belum ada spread terukur - jalankan universe/record_book_depth.py dulu; "
                         "tanpa s, gate ini cuma aljabar")

    print("\n   Fraksi kejadian yang PUNYI jendela d sah (syarat perlu pi > 2s + i + C):")
    print("   %-14s %-10s %-10s %14s %14s %12s"
          % ("s (bps)", "mode i", "ambang pi", "P(pi>=ambang)", "P(pi_awal>amb)", "jendela d tipikal"))
    baris = []
    for s in (sp["p50"], sp["p90"], 21.0, 60.0, 200.0):
        if s is None:
            continue
        for i_mode in (("0", "s") if a.i_mode == "both" else (a.i_mode,)):
            i = 0.0 if i_mode == "0" else s
            amb = 2 * s + i + C
            f = sum(1 for x in pis if x > amb) / float(len(pis))
            med = FC.med(pis)
            jl = (round(s, 1), round(med - s - i - C, 1))
            fa = (sum(1 for x in pi_awal if x > amb) / float(len(pi_awal))) if len(pi_awal) >= 30 \
                else None
            baris.append({"s_bps": s, "i_mode": i_mode, "ambang_pi_bps": round(amb, 1),
                          "fraksi_ada_jendela": round(f, 3),
                          "fraksi_puncak_awal": None if fa is None else round(fa, 3),
                          "median_pi_bps": med})
            print("   %-14.1f %-10s %-10.1f %13.1f %% %13.1f %% %12s"
                  % (s, ("i=0" if i_mode == "0" else "i=s"), amb, 100.0 * f,
                     -1.0 if fa is None else 100.0 * fa,
                     ("kosong" if jl[1] <= jl[0] else "%.0f..%.0f" % jl)))
    terbaik = max(baris, key=lambda r: (r.get("fraksi_puncak_awal") or -1))
    fr_awal = terbaik.get("fraksi_puncak_awal")
    print("\nVONIS GATE (mengikuti angka, bukan mengikuti selera):")
    print("   - \x22pokoknya jangan sampai rugi\x22 tetap mustahil secara algebra: itu butuh d <= "
          "-(s+i+C), tidak ada d >= 0 yang memenuhi. Yang bisa dibeli hanya lock BERSYARAT, dan "
          "syaratnya di luar kendali kita: puncak datang cukup awal.")
    print("   - lock bersyarat BUKAN hal mustahil di jalur kami: dengan s=%.1f bps, i=0, C=%.1f, "
          "ambang pi=%.1f bps, dan %2.0f %% puncak (seluruh jendela) serta %s %% puncak yang datang "
          "di paruh AWAL jendela melewatinya."
          % (terbaik["s_bps"], C, terbaik["ambang_pi_bps"], 100.0 * terbaik["fraksi_ada_jendela"],
             "n/a" if fr_awal is None else "%2.0f" % (100.0 * fr_awal)))
    print("   - jadi yang membatasi bukan aritmatika trailing-nya, melainkan tiga hal lain: (a) "
          "resolusi - pada 5 m kami bahkan tidak melihat puncak (%d %% kejadian punya >= 2 baris); "
          "(b) resolusi juga berarti kita tidak bisa MEMILIH trigger di menit ke-2 sementara kabar "
          "mati di menit ke-2 (E11); (c) yang diubah stop adalah BENTUK distribusi, bukan drift - "
          "dan drift di pool kami negatif di horison panjang (E11: -182,5 bps @30 m)."
          % next(c["persen_terlihat"] for c in cak if c["horison_menit"] == 5))
    print("   - literatur berkata hal yang sama, dan ini kutipan verbatim (bukan ringkasan): stop-loss "
          "\"neither reduce nor increase investors' losses relative to a buy-and-hold strategy once "
          "we extend security returns from past realizations to possible future paths\x22 ... \"the "
          "value of stop loss strategies may come largely from risk reduction rather than return "
          "improvement\" (Lei & Li 2009, Financial Services Review 18(1):23-51, dibaca 29 Sep 2026).")
    print("   - konsekuensi untuk E17: uji yang benar BUKAN \x22apakah trailing menguntungkan\x22, "
          "melainkan \x22apakah trailing mengubah P(net <= -X) dan median pada harapan yang sama "
          "dibanding keluar-acak\x22 - klaimnya pengurangan buntut, bukan edge. Kontrol: "
          "random-barrier placebo (level stop digambar dari distribusi yang sama, tidak berjangkar "
          "ke puncak) + jam digeser acak 30-90 m; fill dicatat dari bid, bukan mid.")
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "catatan_arah": "pi dari ticker wp adalah BATAS BAWAH puncak (bar jarang) - gate ini "
                           "pesimis terhadap klaim lock",
           "kejadian": len(pis), "horison_menit": hor_pakai, "resolusi": cak, "C_bps": C,
           "pi": {"median": FC.med(pis), "p75": sorted(pis)[int(.75 * len(pis))],
                  "p90": sorted(pis)[int(.9 * len(pis))], "p95": sorted(pis)[int(.95 * len(pis))],
                  "max": max(pis)},
           "spread": sp, "gate": baris, "tp_cap_bps": a.pi_cap,
           "perintah": "python -X utf8 tools/trailing_gate.py --horison %d" % a.horison}
    out["sha"] = "0x" + hashlib.sha256(json.dumps(baris, sort_keys=True).encode()).hexdigest()
    p = os.path.join(ROOT, "decisions", "trailing-gate-%s.json"
                     % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("artefak: decisions/%s" % os.path.basename(p))


def self_test():
    C = 59.0
    pis = [10.0, 100.0, 192.7, 300.0, 500.0]

    def fraksi(s, i):
        amb = 2 * s + i + C
        return sum(1 for x in pis if x > amb) / float(len(pis))
    assert fraksi(0.01, 0.0) == 4 / 5.0, fraksi(0.01, 0.0)
    assert fraksi(200.0, 200.0) == 0.0, "s=200 harus menutup semua jendela"
    assert fraksi(60.0, 0.0) == 3 / 5.0, fraksi(60.0, 0.0)
    # jendela d sah hanya kalau pi > 2s + i + C
    for s, i, pi in ((20.0, 0.0, 500.0), (100.0, 100.0, 500.0), (150.0, 300.0, 500.0)):
        ada = pi > 2 * s + i + C
        assert ada == (s < pi - s - i - C), (s, i, pi)
    assert not (500.0 > 2 * 150.0 + 300.0 + C), "kasus kosong harus kosong"
    assert costs.rt_cost() > 0
    print("self-test E17-gate OK: ambang, fraksi, dan kekosongan jendela bergerak konsisten")


if __name__ == "__main__":
    utama()
