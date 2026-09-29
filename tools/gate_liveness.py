"""P61 - apakah buku beku itu karakter KAMI atau karakter long-tail perp?

E20 (F-D56) menemukan bahwa dari 41 simbol yang kabar ⑦-nya sampai ke venue perp kami, hanya **5** yang
 harganya bergerak pada resolusi menit; sisanya 96-99 % menitnya tanpa transaksi. Sebelum kesimpulan itu
 dipakai untuk memilih arah produk - "ganti venue" atau "ganti kelas aset" - pertanyaan yang harus dijawab
 duluan adalah apakah fenotipenya milik kami atau milik semua long-tail perp.

Jawaban hanya sah kalau penggarisnya sama. Karena itu alat ini **tidak** mendefinisikan ulang kelasnya:
ia mengimpor `suhu()`/`kelas()` dari `tools/perp_liveness.py` dan memakainya pada deret 1 m venue
pembanding, untuk **daftar simbol yang sama**, pada jendela 24 jam yang sama.

Pakai:  python -X utf8 tools/gate_liveness.py            # banding penuh (35 simbol, ~1 menit)
         python -X utf8 tools/gate_liveness.py --limit 10 # subset cepat
         python -X utf8 tools/gate_liveness.py --self-test

Catatan yang tidak boleh hilang: volume di Gate adalah **jumlah kontrak**, bukan unit basis maupun USD.
Yang dipakai di sini hanya uji "nol vs bukan nol" dan lama harga tidak berubah - dua-duanya tidak
bergantung skala. Kalau nanti angka volume dibandingkan antar venue, itu wajib konversi lebih dulu.
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import perp_liveness as PL  # noqa: E402

GATE = "https://api.gateio.ws/api/v4/futures/usdt"
UA = {"User-Agent": "Mozilla/5.0 (compatible; fabius-liveness/1.0)", "Accept": "application/json"}
BAR_MAX = 1000              # cap endpoint; 1000 menit dari 1440 tetap jendela yang sama untuk uji ini


def aman(u):
    """Percent-encode path - kontrak non-Latin (牛来_USDT) membuat urllib melempar
    UnicodeEncodeError, dan itu akan terbaca sebagai 'venue tidak punya data' padahal
    yang salah adalah URL-ku."""
    dari, _, query = u.partition("?")
    from urllib.parse import quote
    # query juga: kontrak non-Latin (牛来_USDT) ada di NILAI, bukan di path - mengquote
    # path saja meninggalkan UnicodeEncodeError yang akan terbaca sebagai "venue tak berisi"
    return quote(dari, safe=":/") + ("?" + quote(query, safe="=&%/,") if query else "")


def get(u, timeout=45):
    try:
        with urllib.request.urlopen(urllib.request.Request(aman(u), headers=UA), timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "_body": e.read().decode("utf-8", "replace")[:160]}
    except Exception as e:
        return {"_err": repr(e)[:160]}


def daftar_kontrak():
    d = get(GATE + "/contracts")
    if isinstance(d, dict):
        raise SystemExit("daftar kontrak Gate tidak terbaca: %s" % json.dumps(d)[:180])
    m = {}
    for x in d:
        n = str(x.get("name") or "")
        if not n.endswith("_USDT") or x.get("in_delisting"):
            continue
        m.setdefault(n[: -len("_USDT")].upper(), n)
    return m


def klines_1m(kontrak, butuh=1440):
    """Deret Gate dalam BENTUK yang sama dengan Aster, supaya `suhu()` tidak perlu tahu asalnya.

    Endpoint membatasi 1000 bar per permintaan, jadi halaman kedua diambil dengan `to` = bar
    pertama - 60 d. Tanpa itu jendela pembandingnya 1000 menit sementara Aster 1440 - dan dua
    jendela berbeda bukan pembandingan (F-D54).
    """
    out, hal, atas = [], 0, None
    while len(out) < butuh and hal < 3:
        u = "%s/candlesticks?contract=%s&interval=1m&limit=%d" % (
            GATE, kontrak, min(BAR_MAX, butuh - len(out)))
        if atas is not None:
            u += "&to=%d" % atas
        d = get(u)
        if isinstance(d, dict):
            return out, d
        for b in d:
            try:
                out.append({"t": int(float(b["t"])) * 1000, "c": float(b["c"]),
                            "v": float(b.get("v") or 0), "o": float(b.get("o") or 0),
                            "h": float(b.get("h") or 0), "l": float(b.get("l") or 0)})
            except (KeyError, TypeError, ValueError):
                continue
        if not d:
            break
        atas = int(min(float(x["t"]) for x in d)) - 60
        hal += 1
    bersih, seen = [], set()
    for x in sorted(out, key=lambda y: y["t"]):
        if x["t"] in seen:
            continue
        seen.add(x["t"])
        bersih.append(x)
    return bersih[-butuh:], {}


def baca_aster_terbaru():
    fs = sorted(glob.glob(os.path.join(ROOT, "decisions", "e20-perp-liveness-*.json")))
    if not fs:
        return {}, None
    d = json.load(io.open(fs[-1], encoding="utf-8"))
    return {r["simbol"]: r for r in d["rows"]}, os.path.basename(fs[-1])


def jalan(limit, hemat):
    gm = daftar_kontrak()
    peta = PL.daftar_venue()
    per, _ = PL.kabar_beli()
    inter = sorted(((y, n) for y, n in per.items() if y in set(peta)), key=lambda kv: -kv[1])
    ada = [(y, n) for y, n in inter if y in gm]
    tidak = [(y, n) for y, n in inter if y not in gm]
    if limit:
        ada = ada[:limit]
    aster, nama_berkas = baca_aster_terbaru()
    print("P61 | %d simbol reachable kami; %d ada juga di Gate Futures, %d tidak"
          % (len(inter), len(ada), len(tidak)))
    print("   pembanding Aster: %s" % (nama_berkas or "TIDAK ADA ARTEFAK E20 - jalankan E20 lebih dulu"))
    if not aster:
        raise SystemExit("tanpa artefak E20 tidak ada penggaris pembanding - ini BUKAN kegagalan "
                         "pengukuran, ini urutan kerja")
    baris = []
    for y, n in ada:
        der, err = klines_1m(gm[y])
        m = PL.suhu(der, jam=24)
        k = PL.kelas(m) if der else ("GAGAL-DIBACA" if err else "TIDAK-ADA-DATA")
        la = aster.get(y + "USDT") or {}
        if not la:
            for sym, v in aster.items():
                if sym.upper().startswith(y):
                    la = v
                    break
        baris.append({"basis": y, "kontrak": gm[y], "kabar_beli": n, "kelas_gate": k,
                      "kelas_aster": la.get("kelas", "TIDAK-DIUKUR"),
                      "nol_volume_gate": m.get("nol_volume_persen"),
                      "harga_berbeda_gate": m.get("harga_berbeda"),
                      "beku_gate": m.get("beku_menit_maks"), "bar_gate": m.get("bar"),
                      "err": err or None})
        print("   %-16s kabar %-4d | aster %-14s | gate %-6s | nol-vol %-6s%% | beda harga %-5s | "
              "beku %-4s m%s" % (gm[y], n, la.get("kelas", "-"), k, m.get("nol_volume_persen"),
                                 m.get("harga_berbeda"), m.get("beku_menit_maks"),
                                 (" | " + json.dumps(err)[:70]) if err else ""))
    tot = sum(r["kabar_beli"] for r in baris)
    print("\nRINGKASAN pada %d simbol yang sama (kabar %d):" % (len(baris), tot))
    for nama in ("HIDUP", "TIPIS", "MATI", "TIDAK-ADA-DATA", "GAGAL-DIBACA", "TIDAK-DIUKUR"):
        kg = [r for r in baris if r["kelas_gate"] == nama]
        ka = [r for r in baris if r["kelas_aster"] == nama]
        if kg or ka:
            print("   %-14s gate %2d simbol / %4d kabar | aster %2d simbol / %4d kabar"
                  % (nama, len(kg), sum(r["kabar_beli"] for r in kg), len(ka),
                     sum(r["kabar_beli"] for r in ka)))
    naik = [r["kontrak"] for r in baris if r["kelas_gate"] == "HIDUP" and r["kelas_aster"] != "HIDUP"]
    turun = [r["kontrak"] for r in baris if r["kelas_gate"] != "HIDUP" and r["kelas_aster"] == "HIDUP"]
    sama = [r["kontrak"] for r in baris if r["kelas_gate"] == r["kelas_aster"]]
    print("   HIDUP di Gate tapi tidak di Aster : %s" % (", ".join(naik) or "tidak ada"))
    print("   HIDUP di Aster tapi tidak di Gate : %s" % (", ".join(turun) or "tidak ada"))
    print("   kelas sama di kedua venue         : %d dari %d" % (len(sama), len(baris)))
    print("\n   yang boleh disimpulkan: kalau distribusi Gate menyerupai Aster, 'buku beku' adalah sifat "
          "long-tail perp, bukan cacat venue kami - dan itu menutup jalur 'ganti venue' sebagai jawaban.")
    d = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "venue": "gate-futures-usdt",
         "penggaris": "tools/perp_liveness.suhu()/kelas() - fungsi yang sama, bukan salinan",
         "jendela_menit": 24 * 60, "simbol_dibandingkan": len(baris), "kabar_total": tot,
         "tidak_ada_di_gate": [{"basis": y, "kabar": n} for y, n in tidak],
         "hidup_gate": sorted(naik), "hidup_aster_saja": sorted(turun),
         "kelas_sama": len(sama), "rows": baris,
         "perintah": "python -X utf8 tools/gate_liveness.py",
         "catatan_skala": "v Gate = jumlah kontrak, bukan USD; hanya uji nol/bukan-nol dan lamanya beku "
                          "yang dipakai di sini"}
    if not hemat:
        out = os.path.join(ROOT, "decisions", "e20b-gate-liveness-%s.json"
                           % d["dibuat_utc"].replace(":", "").replace("-", ""))
        blob = json.dumps(d, indent=2, ensure_ascii=False, sort_keys=True)
        io.open(out, "w", encoding="utf-8", newline="\n").write(blob)
        print("   artefak:", os.path.relpath(out, ROOT))
    return d


def self_test():
    b = lambda t, c, v: {"t": t, "c": c, "v": v, "o": c, "h": c, "l": c}
    hidup = [b(1_000_000_000 + i * 60000, 1.0 + i * 0.0007, 4000.0 + i) for i in range(1000)]
    beku = [b(1_000_000_000 + i * 60000, 1.0, 0.0) for i in range(1000)]
    assert PL.kelas(PL.suhu(hidup, jam=24)) == "HIDUP"
    assert PL.kelas(PL.suhu(beku, jam=24)) == "MATI"
    mentah = [{"t": "1790691480", "c": "0.023949", "v": "4306", "o": "0.023924", "h": "0.024069",
               "l": "0.023889"}]
    ubah = [{"t": int(x["t"]) * 1000, "c": float(x["c"]), "v": float(x["v"])} for x in mentah]
    assert ubah[0]["t"] == 1790691480000 and abs(ubah[0]["v"] - 4306.0) < 1e-6, ubah
    assert PL.kelas(PL.suhu(ubah, jam=24)) == "TIDAK-ADA-DATA"   # 1 bar -> di bawah ambang baris
    g = get(GATE + "/contracts")
    assert isinstance(g, list) and g, "endpoint kontrak Gate mati - jangan sebut ini 'venue tidak hidup'"
    gm = daftar_kontrak()
    assert "DOGE" in gm and gm["DOGE"] == "DOGE_USDT", gm.get("DOGE")
    der, err = klines_1m("DOGE_USDT", butuh=120)
    assert len(der) >= 60 and not err, (len(der), err)
    assert all(x["t"] % 60000 == 0 for x in der[:5]), der[:2]
    print("self-test P61 OK: penggaris yang sama dipakai ke bentuk Gate | payload mentah dikonversi "
          "dengan benar | 1 bar -> TIDAK-ADA-DATA | endpoint Gate hidup dan DOGE_USDT memberi klines")


def utama():
    ap = argparse.ArgumentParser(description="P61 banding liveness venue pembanding")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--hemat", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    return jalan(a.limit, a.hemat)


if __name__ == "__main__":
    utama()
