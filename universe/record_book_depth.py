"""Perekam ORDER BOOK venue (⑨) - karena teori buku order tidak bisa diuji tanpa historinya.

Kenapa berkas ini ada (29 Sep 2026, permintaan builder): dia membawa teori dari trader yang dia
hormati - baca order book, jumlahkan "variasi harga" sisi beli, kurangi sisi jual; positif =
pemantulan, negatif = turun - plus stop-loss trailing yang tidak boleh rugi. Teori itu masuk akal
DAN bisa diuji, tapi satu-satunya hal yang membatalkan kita hari ini adalah: **kami tidak punya
riwayat order book sama sekali.** Endpointnya ada (`/fapi/v1/depth` sudah diverifikasi hidup), tapi
data historis tidak bisa diciptakan setelahfakta. Jadi yang bisa dilakukan adalah memulai jamnya.

Yang direkam tiap siklus, per simbol:
  bids/asks multi-level (price, qty) apa adanya + mid, spread_bps, dan tiga variasi imbalance:
    bi1  = (Qbid_l1 - Qask_l1) / (Qbid_l1 + Qask_l1)
    bi5  = sama, dijumlah 5 level pertama
    bi20 = sama, dijumlah 20 level
    util = (Σ Qbid·d_bid - Σ Qask·d_ask) / Σ Q·d   dengan d = jarak ke mid, 20 level
  `util` inilah penerjemahan paling dekat dari "total variasi harga beli dikurangi jual": bobotnya
  jarak harga ke mid, bukan cuma jumlah - dan itu pilihan, bukan kanonis (dipisahkan supaya nanti
  bisa dibandingkan dengan varian lain, bukan dikubur di satu angka).

Yang TIDAK dilakukan: menebak-nebak saat HTTP gagal. Setiap kegagalan jadi baris sendiri
(`{"k":"bdx", "sym":..., "kode_http":...}`), supaya "buku order tidak dijawab" tidak pernah terbaca
sebagai "buku order sepi" - aturan yang sama yang memisahkan `wp0`/`wpc`/`wpv` di perekam harga.

Snapshot boleh identik dengan sebelumnya (venue tidak mengubah quote): itu dicatat sebagai
`lastUpdateId` yang sama, bukan dihitung sebagai data baru.

Pakai:  python -X utf8 universe/record_book_depth.py --self-test
       python -X utf8 universe/record_book_depth.py            # satu siklus (dipakai workflow)
       python -X utf8 universe/record_book_depth.py --report
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = "https://fapi.asterdex.com/fapi/v1/depth"
OUT = os.path.join(ROOT, "universe", "book-depth.jsonl")
MANIFEST = os.path.join(ROOT, "universe", "book-depth-manifest.txt")
UA = {"User-Agent": "Fabius/0.1 (research; hackathon)"}
LEVELS = 20
# BTC/ETH/SOL = jangkar sehat (book tebal, spread sempit) supaya kami bisa membedakan
# "perekamnya rusak" dari "buku order token kecil memang tipis".
JANGKAR = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]


def normal(sym):
    """Daftar kami menyimpan BASIS (0G, APE); API minta `0GUSDT`.

    Kekeliruan ini menghasilkan 110 baris `Invalid symbol` vs 20 snapshot nyata sebelum
    ketahuan (29 Sep 09:5xZ). Perekam yang rajin mencatat kegagalan tetap harus mengoreksi
    dirinya sendiri - itu yang dilakukan `normal()` dan `--validasi-saja`.
    """
    y = str(sym or "").strip().upper()
    if not y:
        return None
    for suf in ("USDT", "USDC", "PERP"):
        if y.endswith(suf):
            return y
    return y + "USDT"


VEN = {"loaded": False, "sim": set()}


def venue_sejati():
    """Simbol yang benar-benar ada di exchangeInfo; dibaca sekali per proses."""
    if VEN["loaded"]:
        return VEN["sim"]
    try:
        req = urllib.request.Request("https://fapi.asterdex.com/fapi/v1/exchangeInfo",
                                     headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode())
        VEN["sim"] = {str((x or {}).get("symbol") or "").upper()
                      for x in (d.get("symbols") or [])} - {""}
        VEN["loaded"] = True
    except Exception as e:
        print("   exchangeInfo TIDAK terbaca (%s) - validasi dilewat; kegagalan tetap dicatat "
              "apa adanya, tidak ditelan" % str(e)[:70])
    return VEN["sim"]


def validasi(daftar):
    kn = venue_sejati()
    if not kn:
        return daftar, []
    return [x for x in daftar if x in kn], [x for x in daftar if x not in kn]


def baca_daftar(nama_berkas="universe/book-venue.txt"):
    p = os.path.join(ROOT, nama_berkas)
    if not os.path.exists(p):
        return []
    out = []
    for ln in io.open(p, encoding="utf-8", errors="replace"):
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            n = normal(ln)
            if n:
                out.append(n)
    return out


def derived(bids, asks):
    """mid/spread + EMPAT pembacaan buku, semuanya dicatat - tidak ada yang dipilih di sini.

    Teori builder berbunyi "jumlahkan total variasi harga sisi beli, kurangi sisi jual". Frasa itu
    ambigu secara sengaja, dan memaksakan satu rumus hari ini berarti memilih tanpa bukti. Yang
    dicatat per snapshot:
      bi1/bi5/bi20 : imbalance KUANTITAS pada 1 / 5 / 20 level. INI STATE, BUKAN order flow
                     imbalance (OFI) - OFI-nya Cont-Kukanov-Stoikov adalah JUMLAH ATAS EVENT
                     (arXiv:1011.6402v3) dan tidak dapat dipulihkan dari dua endpoint; menyebut
                     angka kami "OFI" adalah salah label (S1, halaman 04)
    bi25         : imbalance kuantitas tapi dalam JENDELA HARGA tetap (+/-2,5% x mid), gaya
                     tutorial hftbacktest -tanpa menjawab pertanyaan "berapa level?" yang tidak terjawab
                     oleh buku yang tebalnya berbeda antar simbol
    pmicro       : microprice (bobot terbalik dari ketebalan 20 level) - dipakai sebagai
                     REFERENSI nilai wajar untuk mengaudit harga fill/exit, BUKAN sebagai prediktor
      mi20         : imbalance NILAI UANG (sigma q*p) - bacaan "variasi harga" paling harfiah
      util20       : imbalance yang menghormati JARAK ke mid (sigma q*d) - ini menghargai likuiditas
                     JAUH, jadi kebalikan dari bi pada buku miring; kalau ketiganya bergerak searah
                     satu sama lain, salah satu tidak menambah informasi - dan itu yang mau kita
                     tahu nanti, bukan kita putuskan sekarang.
    Buku kosong/tidak sehat -> None, BUKAN 0, supaya "tidak terjawab" tidak terbaca "seimbang".
    """
    if not bids or not asks:
        return None
    pb, pa = float(bids[0][0]), float(asks[0][0])
    if pb <= 0 or pa <= 0 or pa < pb:
        return None
    mid = 0.5 * (pb + pa)
    if mid <= 0:
        return None

    def sisi(rows, n):
        return [(float(p), float(q)) for p, q in rows[:n]]

    B1, A1 = sisi(bids, 1), sisi(asks, 1)
    B5, A5 = sisi(bids, 5), sisi(asks, 5)
    B20, A20 = sisi(bids, LEVELS), sisi(asks, LEVELS)

    def imb(b, a):
        qb, qa = sum(q for _, q in b), sum(q for _, q in a)
        return round((qb - qa) / (qb + qa), 5) if (qb + qa) > 0 else None

    def imb_uang(b, a):
        vb, va = sum(q * p for p, q in b), sum(q * p for p, q in a)
        return round((vb - va) / (vb + va), 5) if (vb + va) > 0 else None

    def util(b, a):
        ub = sum(q * (mid - p) for p, q in b if p <= mid)
        ua = sum(q * (p - mid) for p, q in a if p >= mid)
        tot = ub + ua
        return round((ub - ua) / tot, 5) if tot > 0 else None

    def dalam_jendela(rows, frac):
        # hanya quote yang berada dalam +/- frac x mid dari mid (gaya tutorial hftbacktest);
        # buku yang tipis di dekat mid akan menghasilkan jendela kosong -> None, bukan 0
        lo, hi = mid * (1 - frac), mid * (1 + frac)
        return [(p, q) for p, q in rows if lo <= p <= hi]

    jd_b, jd_a = dalam_jendela(sisi(bids, LEVELS), 0.025), dalam_jendela(sisi(asks, LEVELS), 0.025)
    qb = sum(q for _, q in jd_b)
    qa = sum(q for _, q in jd_a)
    bi25 = round((qb - qa) / (qb + qa), 5) if (qb + qa) > 0 else None
    Qb = sum(q for _, q in B20)
    Qa = sum(q for _, q in A20)
    # microprice = mid digeser ke sisi yang tipis (H asumsinya order besar datang dari sisi tebal);
    # dipakai sebagai REFERENSI nilai wajar, bukan sebagai prediktor - lihat S3 di
    # vault/08-Backlog/04 - Riset Teori (Sitasi).md
    pmicro = round((Qb * pa + Qa * pb) / (Qb + Qa), 12) if (Qb + Qa) > 0 else None
    return {"mid": mid, "spread_bps": round(10000.0 * (pa - pb) / mid, 2),
            "bi1": imb(B1, A1), "bi5": imb(B5, A5), "bi20": imb(B20, A20),
            "mi20": imb_uang(B20, A20), "util20": util(B20, A20), "bi25": bi25,
            "pmicro": pmicro,
            "micro_minus_mid_bps": (round(10000.0 * (pmicro - mid) / mid, 2)
                                    if pmicro else None),
            "n_bid": len(bids), "n_ask": len(asks)}


def satu(sym, timeout=25):
    url = "%s?symbol=%s&limit=%d" % (BASE, sym, LEVELS)
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            kode = resp.getcode()
            d = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            pesan = json.loads(e.read().decode()).get("msg")
        except Exception:
            pesan = None
        return {"k": "bdx", "sym": sym, "kode_http": e.code, "msg": str(pesan or "")[:80],
                "detik": int(time.time())}
    except Exception as e:
        return {"k": "bdx", "sym": sym, "kode_http": -1, "galat": str(e)[:120],
                "detik": int(time.time())}
    if kode != 200:
        return {"k": "bdx", "sym": sym, "kode_http": kode, "detik": int(time.time())}
    dv = derived(d.get("bids") or [], d.get("asks") or [])
    if not dv:
        return {"k": "bdx", "sym": sym, "kode_http": 200, "galat": "buku kosong",
                "detik": int(time.time())}
    return {"k": "bd", "sym": sym, "t": int(d.get("T") or d.get("lastUpdateId") or time.time() * 1000),
            "detik": int(time.time()), "update_id": d.get("lastUpdateId"),
            "bids": d.get("bids") or [], "asks": d.get("asks") or [], **dv}


def siklus(simbol, gap=1.2):
    rows = []
    for sym in simbol:
        rows.append(satu(sym))
        time.sleep(gap)
    return rows


def laporan():
    if not os.path.exists(OUT):
        print("belum ada %s - perekam belum pernah jalan" % os.path.basename(OUT))
        return
    by, x, gagal, pesan, update_sama = {}, 0, {}, {}, 0
    tid = None
    for ln in io.open(OUT, encoding="utf-8", errors="replace"):
        if not ln.startswith("{"):
            continue
        d = json.loads(ln)
        x += 1
        if d.get("k") == "bdx":
            kode = str(d.get("kode_http"))
            gagal[kode] = gagal.get(kode, 0) + 1
            kk = "%s:%s" % (kode, d.get("msg") or "")
            pesan[kk] = pesan.get(kk, 0) + 1
            continue
        by.setdefault(d["sym"], []).append(d)
        if tid == d.get("update_id"):
            update_sama += 1
        tid = d.get("update_id")
    print("baris: %d | simbol tercatat: %d | kegagalan per kode HTTP: %s"
          % (x, len(by), json.dumps(gagal, sort_keys=True) if gagal else "tidak ada"))
    if pesan:
        print("   pesan API apa adanya: %s" % json.dumps(pesan, sort_keys=True)[:420])
    for sym in sorted(by)[:8]:
        r = by[sym]
        sp = [y["spread_bps"] for y in r]
        def med(k):
            xs = sorted(y[k] for y in r if isinstance(y.get(k), float))
            return xs[len(xs) // 2] if xs else 0.0
        print("   %-12s n=%4d | spread %7.2f bps | bi1 %+6.3f bi5 %+6.3f bi20 %+6.3f "
              "mi20 %+6.3f util20 %+6.3f" % (sym, len(r), sorted(sp)[len(sp) // 2], med("bi1"),
                                             med("bi5"), med("bi20"), med("mi20"), med("util20")))
    if update_sama:
        print("   catatan: %d baris punya lastUpdateId yang sama dengan sebelumnya - buku memang "
              "tidak bergerak, bukan data hilang" % update_sama)


def self_test():
    """Arah tiap pembacaan, None saat tidak sehat, deterministik - dan dua pembacaan boleh berbeda.

    Fixture kedua ini sengaja dibuat untuk MEMBANTU kita: bid tebal dekat mid, ask tipis tapi satu
    level sangat jauh -> `bi20` POSITIF (lebih banyak kuantitas di bid) sementara `util20` NEGATIF
    (jarak bobotnya dominated ask jauh). Teori "jumlahkan variasi harga" akan memberi jawaban
    berbeda tergantung pembacaan mana yang dipakai, dan perekam tidak boleh memilih satu di sini.
    """
    dekat_bid = [["100.9", "5"], ["100.8", "5"], ["100.7", "5"]]
    jauh_ask = [["102.0", "1"], ["104.0", "1"], ["106.0", "1"]]
    d = derived(dekat_bid, jauh_ask)
    assert d["bi1"] > 0 and d["bi20"] > 0 and d["util20"] > 0, d
    assert 0 < d["spread_bps"] < 5000, d

    bedir = derived([["101.0", "3"]], [["102.0", "1"], ["110.0", "1"]])
    assert bedir["bi20"] > 0 and bedir["util20"] < 0, bedir
    assert bedir["mi20"] > 0, bedir

    # cerminnya: bid tipis JAUH, ask tebal DEKAT -> bi dan util dua-duanya negatif (konsisten).
    # Dulu saya membalik daftar mentah dan dapat bid di atas ask; perekam menolak (None) dan itu
    # benar - buku bersilangan bukan "imbalance ekstrem", itu buku rusak.
    m = derived([["96.0", "1"], ["98.0", "1"], ["100.0", "1"]],
                [["101.6", "5"], ["101.7", "5"], ["101.8", "5"]])
    assert m["bi20"] < 0 and m["util20"] < 0 and m["mi20"] < 0, m
    assert derived([["106.0", "1"]], [["100.7", "1"]]) is None, "buku bersilangan harus ditolak"

    assert derived([["102.0", "1"]], [["100.0", "1"]]) is None
    assert derived([], []) is None and derived([["1", "1"]], []) is None
    assert derived([["0", "1"]], [["1", "1"]]) is None
    assert derived(dekat_bid, jauh_ask) == derived(dekat_bid, jauh_ask)
    print("self-test perekam buku OK: arah bi/mi/util benar, dua pembacaan bisa BERBEDA arah, "
          "buku tidak sehat -> None, deterministik")


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--validasi-saja", action="store_true",
                    help="cek daftar pantau terhadap exchangeInfo lalu berhenti")
    ap.add_argument("--limit-simbol", type=int, default=25)
    ap.add_argument("--gap", type=float, default=1.2)
    ap.add_argument("--symbols", default="", help="daftar manual, koma; gabungan dengan berkas daftar")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.report:
        return laporan()
    daftar = list(dict.fromkeys([x for x in (normal(y) for y in (
        JANGKAR + baca_daftar() + [z for z in a.symbols.split(",") if z.strip()])) if x]))
    if a.validasi_saja:
        ok, buang = validasi(daftar)
        print("validasi daftar ⑨: %d dikenal, %d TIDAK ada di exchangeInfo (dari %d)"
              % (len(ok), len(buang), len(daftar)))
        if buang:
            print("   contoh dibuang: %s" % ", ".join(buang[:10]))
        return
    daftar = validasi(daftar)[0]
    if not daftar:
        raise SystemExit("tidak ada simbol untuk direkam - tulis daftar ke universe/book-venue.txt")
    rows = siklus(daftar[:a.limit_simbol], a.gap)
    with io.open(OUT, "a", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")
    ok = sum(1 for r in rows if r.get("k") == "bd")
    print("⑨ buku order: %d/%d simbol terjawab | ditulis append-only ke universe/%s"
          % (ok, len(rows), os.path.basename(OUT)))
    sha = hashlib.sha256(("".join(json.dumps(r, sort_keys=True) for r in rows)).encode()).hexdigest()
    with io.open(MANIFEST, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("%s n=%d ok=%d sha=%s\n" % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                             len(rows), ok, sha[:16]))
    if ok == 0:
        print("   PERINGATAN: nol buku terjawab siklus ini - cek HTTP code di baris `bdx`")


if __name__ == "__main__":
    utama()
