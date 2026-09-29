"""E20 - apakah simbol yang TERDAFTAR di venue kami benar-benar HIDUP pada resolusi menit?

Tembok yang kami kutip selama ini adalah **keberadaan**: `tools/venue_bridge.py` mengukur bahwa hanya
**3,1 %** kabar beli ⑦ terjadi di token yang ada di venue perp kami. Tapi "ada di daftar" bukan
"bisa diperdagangkan", dan bukan pula "punya harga yang bergerak". F-D54 memberi bukti yang arahannya
sama dari sisi lain: kami masuk rata-rata 58 d sesudah whale beli dan kehilangan 519 bps di menit ke-5 -
dan salah satu penjelasan yang belum diuji adalah bahwa yang kami beli bukan pasar, tapi **tangga
beku**: harga yang tidak bergerak berjam-jam, lalu melompat.

Alat ini mengukur suhu venue sebelum ada satu pun hipotesis sinyal diujinya: untuk tiap simbol yang
ada di irisan (kabar ⑦ x venue perp), tarik 1 m klines 24 jam terakhir dan hitung berapa menit yang
**benar-benar berisi transaksi**, berapa harga berbeda yang pernah terlihat, dan berapa lama harga
terakhir diam tak berubah. Kelasnya kemudian menentukan apakah bump E11 UNGGUN diuji di sana: menguji
horison dua menit pada deret yang 95 % menitnya nol volume bukan uji, itu mengukur keterlambatan
pengamatan sendiri.

Pakai:  python -X utf8 tools/perp_liveness.py                # jalan penuh, tulis artefak
         python -X utf8 tools/perp_liveness.py --limit 12     # subset tercepat
         python -X utf8 tools/perp_liveness.py --self-test

Yang TIDAK dilakukan alat ini: mengirim order, mengklaim likuiditas (volume klines bukan kedalaman
buku - lihat ⑨), atau mengubah alat yang sedang terkunci.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import bars as BR  # noqa: E402
import venue_bridge as VB  # noqa: E402
import flow_cluster_test as FC  # noqa: E402

HARI = 1
AMBANG_HIDUP_0VOL = 20.0     # % menit tanpa transaksi - dibulatkan ke bawah: 1 dari 5 menit mati
AMBANG_HIDUP_HARGA = 200     # harga berbeda dalam 24 jam (dari ~1440 bar)
BEKU_PANIK = 120             # menit tanpa perubahan harga = deret ini tidak bisa horison 2 m

KELAS = {"HIDUP": "layak diuji horison menit", "TIPIS": "ujinya harus lebih panjang dari 2 m",
         "MATI": "bukan pasar - deretnya beku"}


def suhu(deret, jam=24):
    """Ukuran 'hidup' satu deret 1 m pada `jam` jam TERAKHIR, bukan pada seluruh berkas cache.

    E20 mendefinisikan kelasnya pada jendela 24 jam. Kalau cache-nya lebih panjang (P59 mengambil
    3 hari supaya jendela E26 tidak bolong), pemotongan harus terjadi DI SINI, supaya klasifikasi
    tidak berubah hanya karena berkasnya memanjang - itu penggantian penggaris di tengah pengukuran
    (F-D54).
    """
    if not deret:
        return {"bar": 0}
    if jam and len(deret) > jam * 60:
        deret = deret[-jam * 60:]
    v = [float(x.get("v") or 0) for x in deret]
    c = [float(x.get("c") or 0) for x in deret]
    nol = 100.0 * sum(1 for x in v if x <= 0) / len(v)
    beda = len({round(x, 12) for x in c})
    run = kini = 0
    for i in range(1, len(c)):
        if c[i] == c[i - 1]:
            kini += 1
            run = max(run, kini)
        else:
            kini = 0
    ret = [abs(c[i] - c[i - 1]) / c[i - 1] * 1e4 for i in range(1, len(c)) if c[i - 1]]
    return {"bar": len(deret), "nol_volume_persen": round(nol, 1), "harga_berbeda": beda,
            "beku_menit_maks": run, "median_perubahan_bps": round(FC.med(ret), 2) if ret else None,
            "jam_akhir_bergerak": (deret[-1]["t"] - deret[max(0, len(deret) - 1 - run)]["t"]) / 60000.0}


def kelas(m):
    if not m or m.get("bar", 0) < 60:
        return "TIDAK-ADA-DATA"
    if m["beku_menit_maks"] >= BEKU_PANIK or m["harga_berbeda"] < 30:
        return "MATI"
    if m["nol_volume_persen"] <= AMBANG_HIDUP_0VOL and m["harga_berbeda"] >= AMBANG_HIDUP_HARGA:
        return "HIDUP"
    return "TIPIS"


def daftar_venue():
    """basis -> string simbol ASLI dari daftar venue (bukan `basis + "USDT"` yang ditebak).

    Daftar Aster memuat sufiks kuotasi yang tidak seragam; menebaknya membuat dua simbol non-Latin
    (牛来, 哈基米) membuang `bar 0` - kehilangan yang saat itu terbaca sebagai "tidak ada data", padahal
    yang salah adalah pemetaanku.
    """
    d = json.load(io.open(VB.SYMS, encoding="utf-8"))
    cand = d if isinstance(d, list) else (d.get("symbols") or d.get("data")
                                          or next((v for v in d.values() if isinstance(v, list)), []))
    m = {}
    for x in cand or []:
        s = str((x or {}).get("symbol") or "").strip().upper()
        if not s:
            continue
        base = str((x or {}).get("base") or (x or {}).get("baseAsset") or "").strip().upper()
        m[base or VB.potong(s)] = s
    return m


def kabar_beli(hari=1):
    """Peristiwa beli ⑦ dalam `hari` terakhir, dikelompokkan per simbol, plus tokennya."""
    batas = int(time.time()) - hari * 86400
    per, tok = {}, {}
    for ln in io.open(VB.FLOW, encoding="utf-8", errors="replace"):
        if not ln.startswith("{"):
            continue
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if r.get("k") not in ("tx", "txc") or not r.get("b"):
            continue
        t = int(r.get("t") or 0)
        y = str(r.get("y") or "").strip().upper()
        if t < batas or not y:
            continue
        per[y] = per.get(y, 0) + 1
        tok.setdefault(y, str(r.get("tk") or "").lower())
    return per, tok


def jalan(limit, hemat):
    peta = daftar_venue()
    vb_aset = set(peta)                        # basis ASET: BTC dari BTCU / BTCUSD1 / BTCUSDT
    vb_pasangan = VB.venue()                   # yang diukur F-D43: string simbol dipotong sufiks
    per, tok = kabar_beli()
    tot_all = sum(per.values())
    inter = sorted(((y, n) for y, n in per.items() if y in vb_aset), key=lambda kv: -kv[1])
    strict = sum(n for y, n in per.items() if y in vb_pasangan)
    print("kabar beli %d hari: %d kejadian pada %d simbol" % (HARI, tot_all, len(per)))
    print("   reachable sebagai ASET yang sama (BTC/ETH/SOL ikut): %d simbol, %d kabar (%.2f %%)"
          % (len(inter), sum(n for _, n in inter), 100.0 * sum(n for _, n in inter) / max(1, tot_all)))
    print("   reachable sebagai PASANGAN yang stringnya ketemu parser lama: %d kabar (%.2f %%)"
          % (strict, 100.0 * strict / max(1, tot_all)))
    print("   -> selisihnya bukan kabar baru: parser lama membuang 17 entri daftar yang sufiksnya")
    print("      bukan USDT (BTCU, BTCUSD1, SKHYNIXUSD1, ...). Ini dua pertanyaan berbeda -")
    print("      'aset yang sama' vs 'pasangan yang sama' - jangan saling menggantikan (F-D57).")
    if limit:
        inter = inter[:limit]
    print("   (lanjutan) simbol yang diurut berdasarkan kabar: %d kandidat, %d yang diambil"
          % (len(sorted(((y, n) for y, n in per.items() if y in vb_aset))), len(inter)))
    rows = []
    for y, n in inter:
        sym = peta.get(y) or (y + "USDT")
        deret = []
        try:
            p = os.path.join(BR.CACHE, "%s_1m.json" % sym)
            if os.path.exists(p) and time.time() - os.path.getmtime(p) < 6 * 3600:
                deret = json.load(io.open(p, encoding="utf-8"))["bars"]
                if len(deret) < int(HARI * 1440 * 0.9):
                    deret = []        # cache lebih pendek dari jendela yang dijanjikan -> ambil ulang
            if not deret:
                deret, _ = BR.fetch(sym, "1m", HARI, verbose=False)
                if deret and not hemat:
                    BR.save(sym, "1m", deret, {"pages": 1})
        except SystemExit as e:
            print("   %-14s gagal: %s" % (sym, e))
        m = suhu(deret, jam=24)
        k = kelas(m)
        rows.append({"simbol": sym, "kabar_beli": n, "kelas": k, **m})
        print("   %-16s kabar %-4d | bar %-4s | nol-vol %-6s%% | harga berbeda %-5s | beku maks %-5s m | %s"
              % (sym, n, m.get("bar"), m.get("nol_volume_persen"), m.get("harga_berbeda"),
                 m.get("beku_menit_maks"), k))
    hit = [r for r in rows if r["kelas"] == "HIDUP"]
    tip = [r for r in rows if r["kelas"] == "TIPIS"]
    mati = [r for r in rows if r["kelas"] == "MATI"]
    tot_inter = sum(r["kabar_beli"] for r in rows)
    print("\nRINGKASAN %d simbol irisan (%d kabar beli dalam %d hari):" % (len(rows), tot_inter, HARI))
    print("   HIDUP %d (%.1f %% dari kabar) | TIPIS %d (%.1f %%) | MATI %d (%.1f %%)"
          % (len(hit), 100.0 * sum(r["kabar_beli"] for r in hit) / max(1, tot_inter),
             len(tip), 100.0 * sum(r["kabar_beli"] for r in tip) / max(1, tot_inter),
             len(mati), 100.0 * sum(r["kabar_beli"] for r in mati) / max(1, tot_inter)))
    if hit:
        print("   yang HIDUP: " + ", ".join("%s(%d)" % (r["simbol"], r["kabar_beli"]) for r in hit[:12]))
    print("   batas yang TIDAK boleh dilewati: klines berisi transaksi yang terjadi, bukan kedalaman "
          "buku; 'HIDUP' di sini = layak diuji pada horison menit, BUKAN layak dieksekusi besar.")
    d = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "hari": HARI, "jendela_klasifikasi_jam": 24,
         "ambang": {"nol_volume_maks_persen": AMBANG_HIDUP_0VOL, "harga_berbeda_min": AMBANG_HIDUP_HARGA,
                    "beku_panik_menit": BEKU_PANIK},
         "simbol_irisan": len(rows), "kabar_beli_irisan": tot_inter,
         "kabar_beli_semua_simbol": tot_all, "kabar_beli_pasangan_lama": strict,
         "hidup": len(hit), "tipis": len(tip), "mati": len(mati),
         "kabar_hidup": sum(r["kabar_beli"] for r in hit),
         "per_sent_kabar_hidup": round(100.0 * sum(r["kabar_beli"] for r in hit) / max(1, tot_inter), 2),
         "rows": rows, "perintah": "python -X utf8 tools/perp_liveness.py"}
    if not hemat:
        out = os.path.join(ROOT, "decisions", "e20-perp-liveness-%s.json"
                           % d["dibuat_utc"].replace(":", "").replace("-", ""))
        io.open(out, "w", encoding="utf-8", newline="\n").write(json.dumps(d, indent=2,
                                                                          ensure_ascii=False,
                                                                          sort_keys=True))
        print("   artefak:", os.path.relpath(out, ROOT))
    return d


def self_test():
    b = lambda t, c, v: {"t": t, "c": c, "v": v, "o": c, "h": c, "l": c}
    hidup = [b(1_000_000 + i * 60000, 1.0 + i * 0.0007, 5000.0 + i) for i in range(1440)]
    # TIPIS: harga bergerak (run beku pendek) tapi kebanyakan menit tanpa transaksi
    tipis = [b(1_000_000 + i * 60000, 1.0 + (i // 3) * 0.0007, 0.0 if i % 3 else 80.0)
             for i in range(1440)]
    # MATI: satu harga sepanjang hari - deret beku, horison menit apa pun di sini mengukur nol
    mati = [b(1_000_000 + i * 60000, 1.0 if i < 300 else 1.0002, 0.0) for i in range(1440)]
    mh, mt, mm = suhu(hidup), suhu(tipis), suhu(mati)
    assert kelas(mh) == "HIDUP", mh
    assert kelas(mt) == "TIPIS", mt
    assert kelas(mm) == "MATI", mm
    assert mt["beku_menit_maks"] <= 3 and mt["nol_volume_persen"] > 60, mt
    assert mm["beku_menit_maks"] > 100 and mm["harga_berbeda"] <= 2, (mt, mm)
    assert kelas(suhu([])) == "TIDAK-ADA-DATA"
    # jendela tetap: cache 3 hari tidak boleh mengubah kelas yang sama (F-D54)
    panjang = [b(1_000_000 + i * 60000, 1.0 + i * 0.0007, 5000.0 + i)
               for i in range(3 * 1440)]
    mp = suhu(panjang, jam=24)
    assert mp["bar"] == 1440 and kelas(mp) == "HIDUP", mp
    print("self-test E20 OK: tiga kelas terpisah (HIDUP/TIPIS/MATI) | run beku terukur | "
          "deret kosong -> TIDAK-ADA-DATA, bukan '0 %'")


def utama():
    ap = argparse.ArgumentParser(description="E20 suhu venue perp pada resolusi menit")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--hemat", action="store_true", help="hitung kelas tanpa menulis artefak/cache")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    return jalan(a.limit, a.hemat)


if __name__ == "__main__":
    utama()
