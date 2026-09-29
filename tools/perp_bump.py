"""E26 - kalau venue-nya benar-benar bergerak, apakah bump pasca-buy ada di HARGA PERP?

Rantaiannya begini. E11 mengukur bump **+192,7 @2 m → +202,6 @5 m** pada deret harga *spot* BSC
(GMGN `wp`). F-D43 lalu memotong harapan itu jadi 3,1 % kabar karena sisanya terjadi di token yang
tidak kami perdagangkan. F-D54 membetulkan kecepatan kami (umur keputusan 61 d) dan menemukan bahwa
masuk 58 d sesudah whale tetap **-519 bps**. `tools/perp_liveness.py` (E20) menutup lubang terakhir
dengan angka, bukan asumsi: dari 41 simbol yang reachable, hanya **5** yang harga perp-nya bergerak
pada resolusi menit - sisanya beku (kelas MATI median **97,4 %** menit tanpa transaksi, run tanpa
perubahan harga terpanjang **679 menit**; kelas TIPIS median 77,9 %).

Yang diuji di sini karena itu: **di deret harga substrate yang bisa kami eksekusi**, setelah buy kerumunan
pintar, apakah horison pendek masih menang atas horison panjang - dan berapa yang tersisa kalau masuk
kami telatkan satu menit (yang nyata, bukan yang diandaikan). Dua titik masuk dilaporkan selalu
berdampingan karena F-D54 sudah menunjukkan siapa yang menentukan jawabannya.

Pakai:  python -X utf8 tools/perp_bump.py                 # uji penuh (butuh cache 1m dari E20)
         python -X utf8 tools/perp_bump.py --kelas TIPIS   # sensitivitas: apa jawaban kelas tipis?
         python -X utf8 tools/perp_bump.py --self-test

Alat ini TIDAK mengunci apa pun dan TIDAK mengirim order. Angka di bawah adalah eksplorasi pada satu
hari, dan itu yang membuatnya layak ditulis apa adanya.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import bars as BR  # noqa: E402
import flow_cluster_test as FC  # noqa: E402
import perp_liveness as PL  # noqa: E402

WINS = 2000.0
MIN = 60
JENDELAPAS = 3 * MIN
H = (2, 5, 30)
MASUK_TELAT_MENIT = 1        # umur keputusan nyata kami: median 58-61 d (F-D54) -> bulatkan 1 m
DEDUPE_MENIT = 30
HARI_CACHE = 3   # P59: 24 jam kejadian + 30 m horison + tepi jendela membuat cache 1 hari tidak cukup


def w(x):
    return max(-WINS, min(WINS, x))


def harga_pada(deret, t_ms):
    """Close bar yang memuat `t_ms` (bar terakhir dengan open <= t). None kalau di luar rentang."""
    idx = [i for i, b in enumerate(deret) if b["t"] <= t_ms]
    if not idx:
        return None
    return float(deret[idx[-1]]["c"])


def jendela_median(deret, t_ms, h_menit):
    awal, akhir = t_ms + (h_menit * MIN - JENDELAPAS) * 1000, t_ms + (h_menit * MIN + JENDELAPAS) * 1000
    js = [float(b["c"]) for b in deret if awal <= b["t"] <= akhir]
    return FC.med(js) if js else None


def kejadian(per_symbol, kelas_ok):
    """Buy ⑦ 24 jam terakhir pada simbol kelas `kelas_ok`, dedupe 1 per 30 m per simbol."""
    peta = PL.daftar_venue()
    rows = []
    for ln in io.open(PL.VB.FLOW, encoding="utf-8", errors="replace"):
        if not ln.startswith("{"):
            continue
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if r.get("k") not in ("tx", "txc") or not r.get("b"):
            continue
        y = str(r.get("y") or "").strip().upper()
        if y not in per_symbol or per_symbol[y] not in kelas_ok:
            continue
        t = int(r.get("t") or 0)
        if not t:
            continue
        rows.append({"y": y, "sym": peta.get(y) or (y + "USDT"), "t": t,
                     "usd": float(r.get("u") or 0), "tx_p": float(r.get("p") or 0)})
    rows.sort(key=lambda x: (x["y"], x["t"]))
    out, last = [], {}
    for r in rows:
        if r["y"] in last and r["t"] - last[r["y"]] < DEDUPE_MENIT * MIN:
            continue
        last[r["y"]] = r["t"]
        out.append(r)
    return out


def nilai(deret, ev, h, masuk_telat_m=0):
    p0 = harga_pada(deret, (ev["t"] + masuk_telat_m * 60) * 1000)
    p1 = jendela_median(deret, (ev["t"] + masuk_telat_m * 60) * 1000, h)
    if p0 is None or p1 is None or p0 <= 0:
        return None
    return 10000.0 * (p1 - p0) / p0


def jalan(kelas_ok, draws):
    d = PL.jalan(0, True)
    peta = PL.daftar_venue()
    per_symbol = {}
    for r in d["rows"]:
        base = next((k for k, v in peta.items() if v == r["simbol"]), None)
        if base:
            per_symbol[base] = r["kelas"]
    ev = kejadian(per_symbol, kelas_ok)
    print("E26 | simbol kelas %s: %d kejadian (dedupe %d m/simbol, 24 jam)"
          % ("/".join(sorted(kelas_ok)), len(ev), DEDUPE_MENIT))
    if len(ev) < 5:
        print("   n terlalu kecil untuk statement apa pun - ini BELUM BISA DIUJI, bukan nol")
        return {"vonis": "BELUM BISA DIUJI", "n": len(ev)}
    seri, ambil_ulang = {}, []
    for y in sorted({e["y"] for e in ev}):
        sym = peta.get(y, y + "USDT")
        p = os.path.join(BR.CACHE, "%s_1m.json" % sym)
        deret = []
        if os.path.exists(p):
            deret = json.load(io.open(p, encoding="utf-8"))["bars"]
        if len(deret) < int(HARI_CACHE * 1440 * 0.9):
            try:
                deret, _ = BR.fetch(sym, "1m", HARI_CACHE, verbose=False)
                if deret:
                    BR.save(sym, "1m", deret, {"pages": (len(deret) // 1500) + 1})
                    ambil_ulang.append(sym)
            except SystemExit as e2:
                print("   %s gagal diambil ulang: %s" % (sym, e2))
                deret = []
        if deret:
            seri[y] = deret
        else:
            print("   %s: tidak ada deret 1 m - KEHILANGAN, bukan nol" % sym)
    if ambil_ulang:
        print("   cache diperpanjang ke %d hari untuk %d simbol (P59): %s"
              % (HARI_CACHE, len(ambil_ulang), ", ".join(ambil_ulang)))
    pakai = [e for e in ev if e["y"] in seri]
    print("   kejadian dengan deret perp 1 m: %d dari %d (symbol %d)"
          % (len(pakai), len(ev), len({e["y"] for e in pakai})))
    hasil = {}
    for h in H:
        a = [x for x in (nilai(seri[e["y"]], e, h) for e in pakai) if x is not None]
        b = [x for x in (nilai(seri[e["y"]], e, h, MASUK_TELAT_MENIT) for e in pakai) if x is not None]
        if not a:
            print("      @%d m: 0 dari %d kejadian - tidak ada apa pun untuk dirata-ratakan"
                  % (h, len(pakai)))
            continue
        print("      @%d m: %d dari %d kejadian dinilai (%d keluar jendela seri - kehilangan, BUKAN "
              "nol bps)" % (h, len(a), len(pakai), len(pakai) - len(a)))
        rng = random.Random(20260929)
        pla = []
        for e in pakai:
            sft = rng.randrange(30, 91) * MIN
            x = nilai(seri[e["y"]], dict(e, t=e["t"] + sft), h)
            if x is not None:
                pla.append(x)
        hasil[h] = {"n": len(a), "mean_winso": round(sum(w(x) for x in a) / len(a), 1),
                    "median": round(FC.med(a), 1), "P_ge_500": round(100.0 * sum(1 for x in a if x >= 500) / len(a), 1),
                    "telat1m_mean": round(sum(w(x) for x in b) / len(b), 1) if b else None,
                    "telat1m_median": round(FC.med(b), 1) if b else None,
                    "placebo_mean": round(sum(w(x) for x in pla) / len(pla), 1) if pla else None}
        print("   @%-2d m | n=%-3d | masuk dari harga kejadian: mean %+7.1f median %+7.1f | "
              "masuk +1 m: mean %+7.1f median %+7.1f | placebo %+7.1f"
              % (h, hasil[h]["n"], hasil[h]["mean_winso"], hasil[h]["median"],
                 -999 if hasil[h]["telat1m_mean"] is None else hasil[h]["telat1m_mean"],
                 -999 if hasil[h]["telat1m_median"] is None else hasil[h]["telat1m_median"],
                 -999 if hasil[h]["placebo_mean"] is None else hasil[h]["placebo_mean"]))
    if 5 in hasil and 30 in hasil:
        pair = [(nilai(seri[e["y"]], e, 5), nilai(seri[e["y"]], e, 30)) for e in pakai]
        pair = [(x, y) for x, y in pair if x is not None and y is not None]
        men = sum(1 for x, y in pair if x > y)
        ka = sum(1 for x, y in pair if x < y)
        print("   berpasangan 5 m vs 30 m pada POSISI yang sama: %+0.1f bps median delta | menang %d "
              "kalah %d | p=%.5f"
              % (FC.med([x - y for x, y in pair]), men, ka, FC.sign_p(men, men + ka) if men + ka >= 5 else -1))
    print("\n   baca yang diizinkan: kalau masuk +1 m berubah tanda terhadap masuk dari harga kejadian,")
    print("   yang kami temukan bukan 'kapan masuk' tapi 'seberapa besar bump itu sudah terpakai sebelum")
    print("   kami sampai' - dan di substrate beku (E20) horison menit tidak terukur sama sekali.")
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "kelas": sorted(kelas_ok),
           "n_kejadian": len(pakai), "masuk_telat_menit": MASUK_TELAT_MENIT, "winsor_bps": WINS,
           "horison": hasil, "perintah": "python -X utf8 tools/perp_bump.py",
           "batas": "satu hari; n=%d; tanpa kedalaman buku; harga perp != harga isi kami; EKSPLORASI, "
                    "belum dikunci" % len(pakai)}
    p = os.path.join(ROOT, "decisions", "e26-perp-bump-%s.json"
                    % out["dibuat_utc"].replace(":", "").replace("-", ""))
    io.open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(out, indent=2, ensure_ascii=False,
                                                                     sort_keys=True))
    print("   artefak:", os.path.relpath(p, ROOT))
    return out


def self_test():
    b = lambda t, c, v: {"t": t, "c": c, "v": v, "o": c, "h": c, "l": c}
    t0 = 1_000_000_000
    naik = [b((t0 + i * MIN) * 1000, 1.0 * (1.0 + 0.002 * min(i, 4)), 5000.0) for i in range(240)]
    for h in H:
        assert nilai(naik, {"t": t0}, h) is not None
    assert nilai(naik, {"t": t0}, 2) > 0, nilai(naik, {"t": t0}, 2)
    assert harga_pada(naik, (t0 - 10 * 60) * 1000) is None      # di luar rentang = None, bukan 0
    assert jendela_median(naik, t0 * 1000, 2) is not None
    assert jendela_median(naik, (t0 + 400 * MIN) * 1000, 2) is None   # di luar seri -> None
    datar = [b((t0 + i * MIN) * 1000, 1.0, 0.0) for i in range(240)]
    assert abs(nilai(datar, {"t": t0}, 5)) < 1e-9, nilai(datar, {"t": t0}, 5)
    assert nilai(naik, {"t": t0}, 5, masuk_telat_m=999) is None
    print("self-test E26 OK: bump terdeteksi di deret naik | deret beku = 0 (bukan acak) | "
          "di luar rentang -> None, bukan nol | telat di luar seri -> None")


def utama():
    ap = argparse.ArgumentParser(description="E26 bump pasca-buy pada harga perp")
    ap.add_argument("--kelas", default="HIDUP")
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    return jalan({x.strip().upper() for x in a.kelas.split(",")}, a.draws)


if __name__ == "__main__":
    utama()
