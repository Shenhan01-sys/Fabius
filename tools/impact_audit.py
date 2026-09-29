"""E15 - audit SATUAN dampak: apakah "haircut 2·s/L" di buku paper benar-benar dampak?

Ditemukan 29 Sep ±09:0xZ saat mengejar satu kalimat di README: buku paper melaporkan
`ongkos 59 bps RT + dampak s/L`. Kami ukur apa yang sebenarnya terjadi pada 702 slot:

    liq_usd diketahui: 219 | median $132.022 | p10 $1 | min $0 | max $3.688.624
    dampak_bps tercatat: median 0,00 | p90 0,20 | max 15.124,00

Dua hal salah sekaligus, dan keduanya ke arah yang berlawanan:

1. **Satuan.** `haircut(net, liq, size_quote)` memakai `2 * size_quote / liq` dengan `size_quote`
   dalam **BNB** (0,01) dan `liq` dalam **USD**. Jadi dampak dihitung seolah 0,01 BNB = $0,01 -
   kurang ajar sekitar satu harga BNB (±600-900x) untuk mayoritas pool yang likuid.
2. **Bahan bakunya busuk di ekor bawah.** `liq` dilaporkan $1 dan $0 pada desil terbawah. Kalau
   satuan dibetulkan begitu saja, x·y=k di pool $1 memberi dampak 120.000 bps - bukan kebenaran,
   cuma sampah yang lebih besar. Karena itu median `dampak` hari ini 0,00 (satuan) sementara
   max-nya 15.124 (liq hampir nol): **rata-rata buku kami dicemari oleh kedua-duanya sekaligus.**

Alat ini TIDAK mengubah `paper_book.py` dan TIDAK menyentuh slot yang sudah tercatat: E9 sudah
terkunci dengan definisi `net_bps` seperti yang dicatat buku, dan mengganti alat di tengah uji
terkunci adalah cara paling mudah memenangkan eksperimen. Yang dilakukan: menghitung ulang ketiga
varian pada data yang sama dan mencetaknya berdampingan, supaya setiap angka dampak yang kami kutip
punya alamat.

Pakai:  python -X utf8 tools/impact_audit.py
       python -X utf8 tools/impact_audit.py --bnb-usd 650 --liq-floor 1000
       python -X utf8 tools/impact_audit.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import flow_cluster_test as FC  # noqa: E402

SLOT = os.path.join(ROOT, "decisions", "paper-book-positions.jsonl")
WINS = 2000.0


def w(x):
    return max(-WINS, min(WINS, x))


def baca():
    out = []
    for ln in io.open(SLOT, encoding="utf-8", errors="replace"):
        if not ln.startswith("{"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("status") == "dinilai" and isinstance(d.get("net_bps"), (int, float)):
            out.append(d)
    return out


def varian(sl, bnb_usd, liq_floor):
    """Tiga angka pada posisi yang sama: tercatat / satuan-dibetulkan / hanya-yang-sah."""
    tercatat, dibetulkan, sah = [], [], []
    tahu_liq = nol_liq = di_bawah_floor = 0
    for r in sl:
        L = r.get("liq_usd")
        s = r.get("size_quote_paper")
        n = float(r["net_bps"])
        tercatat.append(w(n))
        if not isinstance(L, (int, float)) or L <= 0 or not s:
            nol_liq += 1
            continue
        tahu_liq += 1
        benar = 10000.0 * (2.0 * s * bnb_usd / L)
        sudah = float(r.get("dampak_bps") or 0.0)
        dibetulkan.append(w(n - (benar - sudah)))
        if L >= liq_floor:
            sah.append(w(n - (benar - sudah)))
        else:
            di_bawah_floor += 1

    def ringkas(xs):
        if not xs:
            return {"n": 0}
        return {"n": len(xs), "mean_winso": round(sum(xs) / len(xs), 1),
                "median": round(FC.med(xs), 1),
                "P>=500": round(100.0 * sum(1 for x in xs if x >= 500) / len(xs), 1),
                "positif": round(100.0 * sum(1 for x in xs if x > 0) / len(xs), 1)}
    return {"tercatat": ringkas(tercatat), "satuan_dibetulkan": ringkas(dibetulkan),
            "hanya_liq_sah": ringkas(sah),
            "sensor": {"slot": len(sl), "liq_diketahui": tahu_liq, "liq_nol_atau_absen": nol_liq,
                       "di_bawah_floor": di_bawah_floor, "liq_floor_usd": liq_floor,
                       "bnb_usd": bnb_usd}}


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bnb-usd", type=float, default=650.0,
                    help="harga BNB/USD untuk konversi - ASUMSI yang dicetak, bukan kebenaran")
    ap.add_argument("--liq-floor", type=float, default=1000.0,
                    help="pool di bawah ini tidak boleh diberi x*y=k (sampahnya lebih besar dari "
                         "modelnya)")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sl = [{"net_bps": 100.0, "liq_usd": 200000.0, "size_quote_paper": 0.01, "status": "dinilai"},
              {"net_bps": 100.0, "liq_usd": 1.0, "size_quote_paper": 0.01, "status": "dinilai"},
              {"net_bps": 100.0, "liq_usd": None, "size_quote_paper": 0.01, "status": "dinilai"}]
        v = varian(sl, 650.0, 1000.0)
        assert v["sensor"]["liq_diketahui"] == 2 and v["sensor"]["liq_nol_atau_absen"] == 1, v
        assert v["sensor"]["di_bawah_floor"] == 1, v
        assert abs(v["tercatat"]["mean_winso"] - 100.0) < 1e-6, v
        assert v["satuan_dibetulkan"]["mean_winso"] < 0, "dengan liq=$1 dampak harus menghancurkannya"
        assert v["hanya_liq_sah"]["n"] == 1 and abs(v["hanya_liq_sah"]["mean_winso"] - 99.35) < 0.1, v
        # dampak yang benar di liq $200k untuk 0,01 BNB @ $650 = 2*6,5/200.000 = 0,000065 -> 0,65 bps
        # (bukan 0,00 seperti yang tercatat, dan bukan 130.000 seperti di pool $1). "sah" berarti
        # poolnya cukup tebal supaya x*y=k boleh dipakai, bukan sekadar angkanya tersedia.
        print("self-test E15 OK: tiga varian terpisah benar, liq di bawah floor dikeluarkan, dan "
              "konversi BNB->USD benar-benar dipakai")
        return
    sl = baca()
    if not sl:
        raise SystemExit("tidak ada slot dinilai - ini BUKAN 'dampak nol'")
    print("E15 audit satuan dampak | %d slot dinilai | --bnb-usd %.0f (asumsi, dicetak) | "
          "liq floor $%.0f" % (len(sl), a.bnb_usd, a.liq_floor))
    v = varian(sl, a.bnb_usd, a.liq_floor)
    print("   sensor %s" % json.dumps(v["sensor"], sort_keys=True))
    print("\n   %-22s %7s %12s %10s %9s %9s" % ("varian", "n", "mean winso", "median", "P>=500",
                                                "positif"))
    for k in ("tercatat", "satuan_dibetulkan", "hanya_liq_sah"):
        r = v[k]
        if not r.get("n"):
            print("   %-22s %7s  -" % (k, 0))
            continue
        print("   %-22s %7d %+12.1f %+10.1f %8.1f%% %8.1f%%"
              % (k, r["n"], r["mean_winso"], r["median"], r["P>=500"], r["positif"]))
    print("\nYang boleh disimpulkan: buku paper kami selama ini memanggil 'dampak' pada angka yang"
          "\nsalah satuan ±600x di mayoritas pool dan meledak di pool $1. E9 TIDAK dihitung ulang:"
          "\nkuncinya menyebut `net_bps` seperti yang dicatat, dan mengganti alat di tengah uji"
          "\nterkunci adalah cara paling mudah memenangkan eksperimen. Yang berubah: setiap angka"
          "\ndampak yang kami kutip sesudah ini wajib menyebut varian mana.")
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "slot": len(sl),
           "asumsi_bnb_usd": a.bnb_usd, "liq_floor_usd": a.liq_floor, "hasil": v,
           "perintah": "python -X utf8 tools/impact_audit.py --bnb-usd %s --liq-floor %s"
                       % (a.bnb_usd, a.liq_floor)}
    out["sha"] = "0x" + hashlib.sha256(json.dumps(v, sort_keys=True).encode()).hexdigest()
    p = os.path.join(ROOT, "decisions", "impact-audit-%s.json"
                     % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("artefak: decisions/%s" % os.path.basename(p))


if __name__ == "__main__":
    utama()
