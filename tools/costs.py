"""Satu model ongkos untuk semua jalur uji - supaya tidak ada dua kebenaran.

P10. Sebelum modul ini, angka round-trip hidup di enam tempat: `backtest.py`, `ledger.py`,
`screen_universe.py`, `smartmoney_score.py`, `flow_test.py` memakai **20 bps** (warisan model
`edge_lab` dari proyek rujukan: 5,5 bps fee + 4,5 bps slip per sisi, **diasumsikan**), sedangkan
`maker_ledger.py` memakai **59 bps** (yang pernah kami UKUR). Deret hasil yang sama lalu dinilai
dengan dua penggaris berbeda, dan artefaknya tidak bilang mana yang dipakai.

Dua angka itu bukan pesaing yang setara:

| nama | nilai | provenance | venue |
|---|---|---|---|
| `MEASURED_RT_BPS` | **59,0** | `forge test test_round_trip_*` + realisasi event `Closed` di chain 97 (`tools/winlog.py`, `decisions/execution-trail.jsonl`) | **pool demo kami sendiri** (kurva x·y=k + fee 30 bps/sisi, posisi 1 unit) |
| `ASSUMED_RT_BPS` | 20,0 | model biaya proyek rujukan (`edge_lab`), tidak pernah direplikasi di repo ini | venue likuid imajiner (perp/major) |

Default evaluasi = **yang terukur**. Itu sengaja keras kepala: 59 bps adalah apa yang benar-benar
kami bayar di venue tempat kami benar-benar mengisi order. Memakainya pada backtest bar perp juga
lebih keras, bukan setara - fee taker perp sungguhan biasanya di bawah itu. Jadi angka yang lolos
penggaris 59 bps punya alasan lebih kuat untuk dipercaya daripada yang lolos 20 bps; dan yang tidak
lolos tidak berubah jadi "hampir lolos" cuma karena penggarisnya ditukar.

`rt_cost(cli)` satu pintu untuk override `--cost`: kalau angka datang dari command line, ia tidak
lagi bernilai terukur - dan `cost_basis()` bilang persis itu, supaya artefak JSON bisa dibaca orang
lain tanpa perlu menebak.

    python -X utf8 tools/costs.py           # cetak model + dari mana asalnya
    python -X utf8 tools/costs.py --self-test
"""
import argparse
import os
import sys

MEASURED_RT_BPS = 59.0
ASSUMED_RT_BPS = 20.0
FEE_SIDE_BPS = 30.0            # fee pool demo kami per sisi (DemoPair.sol `FEE_BPS = 30`)
GATE_MULT = 2.0                # ambang efektif = 2x ongkos: lihat alasan di bawah

BASIS_MEASURED = "measured-own-venue"
BASIS_ASSUMED = "assumed-inherited"
BASIS_OVERRIDE = "cli-override"


def rt_cost(cli=None):
    """Ongkos round-trip (bps) yang dipakai sebuah uji. `cli` menang, tapi mengubah basis."""
    return MEASURED_RT_BPS if cli is None else float(cli)


def cost_basis(cli=None):
    if cli is not None:
        return BASIS_OVERRIDE
    return BASIS_MEASURED


def gate_gross_bps(rt=None):
    """Ambang gross agar net tetap positif setelah ongkos: 2x round-trip.

    Rantai alasannya (dan ini yang membuat `gross > 40 bps` di kode lama bukan sekadar angka):
    sebuah kandidat dipilih kalau gross-nya di atas satu round-trip; setelah itu kita membayar
    round-trip yang sama untuk benar-benar menutup posisi. Sisanya nol. Maka yang harus
    dilampaui adalah dua kali - diukur dengan 59 bps, itu **118 bps** per trade.
    """
    return (MEASURED_RT_BPS if rt is None else float(rt)) * GATE_MULT


def provenance():
    return [
        (MEASURED_RT_BPS, BASIS_MEASURED,
         "forge test test_round_trip_* + event Closed di chain 97; venue = pool x*y=k fee 30 bps/sisi"),
        (ASSUMED_RT_BPS, BASIS_ASSUMED,
         "model biaya proyek rujukan (5,5 fee + 4,5 slip per sisi); tidak pernah direplikasi di sini"),
    ]


# ==================== MODEL ISI (P42) ====================
# MEASURED_RT_BPS di atas hanyalah FEE. Bagian kedua dari ongkos sebenarnya adalah apa yang kita
# bayar karena order kita sendiri menggeser harga - dan sampai 29 Sep bagian itu dihitung dengan
# satuan yang salah (F-D46): `haircut()` memakai `size_quote` dalam BNB dibagi `liq` dalam USD,
# jadi dampaknya terbaca ~600x terlalu kecil. Artinya buku paper murah hati pada arah yang salah,
# dan angka "rugi" pun masih terlalu optimis.

ISI_V1 = "v1-bnb-dianggap-usd"      # yang dipakai paper_book/entry_lab sampai 29 Sep
ISI_V2 = "v2-terukur+floor"         # yang dipakai paper_book dengan --isi v2
LIQ_LANTAI_USD = 50_000.0           # syarat kursi ⑥ (direction.py LIQ_MIN_USD; vault 01-Agent §3)
HARGA_BNB_MAKS_UMUR = 180           # menit; di atas itu v2 menolak, bukan pakai harga basi


def harga_bnb(maks_umur_menit=None, verbose=False):
    """Harga BNB/USD TERUKUR dari klines Aster BNBUSDT - bukan asumsi 650 yang dipakai kode lama.

    Umur harga ikut dilaporkan: cache `data/klines/` tidak ikut di-git, jadi angka ini harus bisa
    dibuat ulang dari clone, dan kalau tidak bisa, itu harus terlihat sebagai TIDAK SAH.
    """
    import time as _t
    import bars as BR
    batas = HARGA_BNB_MAKS_UMUR if maks_umur_menit is None else maks_umur_menit
    muat = BR.load("BNBUSDT", "1h")            # load() mengembalikan {"meta":..,"bars":[..]}
    deret = (muat or {}).get("bars") or []

    def umur_baris(d):
        return (_t.time() - d[-1]["t"] / 1000.0) / 60.0 - 60.0 if d else 1e9

    # cache yang basi harus DiAMBIL ULANG, bukan cuma ditolak: kalau tidak, guard kesegaran ini
    # membuat v2 tidak bisa jalan selamanya di mesin yang cache-nya menua (terjadi 29 Sep:
    # cache BNBUSDT berumur 6.974 menit dan v2 menolak tanpa pernah mencoba menyegarkan).
    if umur_baris(deret) > batas:
        try:
            baru_deret, _m = BR.fetch("BNBUSDT", "1h", 2, verbose=verbose)
            if baru_deret:
                deret = baru_deret
                BR.save("BNBUSDT", "1h", deret, {"pages": 1})
        except SystemExit:
            pass                                   # biarkan umur basi melaporkan TIDAK SAH-nya
    if not deret:
        return {"px": None, "umur_menit": None, "sumber": "aster BNBUSDT 1h", "sah": False,
                "alasan": "klines BNBUSDT tidak bisa diambil"}
    umur = max(0.0, round((_t.time() - deret[-1]["t"] / 1000.0) / 60.0 - 60.0, 1))
    sah = umur <= batas
    return {"px": float(deret[-1]["c"]), "umur_menit": umur, "sumber": "aster BNBUSDT 1h",
            "sah": sah, "alasan": None if sah else "harga BNB berumur %s m > %s m" % (umur, batas)}


def dampak_round_trip(size_bnb, liq_usd, bnb_usd=None, skema=ISI_V2, lantai=LIQ_LANTAI_USD):
    """Dampak round-trip (bps) order `size_bnb` BNB pada pool x*y=k berlikuiditas `liq_usd`.

    v1 : `2*size_bnb/liq_usd` - satuan campur (BNB dibagi USD) -> ~600x terlalu kecil (F-D46).
    v2 : ukuran dikonversi ke USD dengan harga BNB TERUKUR lebih dulu; di bawah lantai likuiditas
         hasilnya TIDAK SAH - bukan angka besar, karena di pool $1 yang terjadi bukan slippage,
         melainkan "tidak ada buku untuk diisi" (F-D61 mengukur nol kedalaman dalam +-10 bps).
    """
    out = {"skema": skema, "size_bnb": size_bnb, "liq_usd": liq_usd, "lantai_usd": lantai,
           "dampak_bps": None, "sah": False, "alasan": None, "ukuran_usd": None, "bnb_usd": bnb_usd}
    if skema == ISI_V1:
        if not liq_usd or liq_usd <= 0 or not size_bnb:
            out["dampak_bps"] = 0.0
            out["alasan"] = "liq/ukuran tidak ada -> dampak dianggap 0 (bukan 'tanpa dampak')"
            out["sah"] = True
            return out
        out["dampak_bps"] = round(10000.0 * (2.0 * size_bnb / float(liq_usd)), 6)
        out["sah"] = True
        return out
    if bnb_usd is None:
        h = harga_bnb()
        bnb_usd, out["umur_harga_bnb_menit"] = h["px"], h.get("umur_menit")
        if not h["sah"]:
            out["alasan"] = "harga BNB tidak terukur/segar: " + str(h["alasan"])
            return out
    out["bnb_usd"] = bnb_usd
    if not size_bnb or size_bnb <= 0:
        out["alasan"] = "ukuran tidak ada"
        return out
    if not liq_usd or liq_usd <= 0:
        out["alasan"] = "liq_usd tidak dilaporkan -> TIDAK SAH, bukan nol"
        return out
    if liq_usd < lantai:
        out["alasan"] = "liq $%s < lantai $%s - order ini tidak punya buku untuk diisi" % (
            format(int(liq_usd), ","), format(int(lantai), ","))
        return out
    ukuran_usd = float(size_bnb) * float(bnb_usd)
    out["ukuran_usd"] = round(ukuran_usd, 2)
    out["dampak_bps"] = round(10000.0 * (2.0 * ukuran_usd / float(liq_usd)), 6)
    out["sah"] = True
    return out


def isi_buku(levels, mid, size_usd):
    """Harga rata-rata tertimbang untuk menghabiskan `size_usd` pada satu sisi buku (⑨).

    Ini model isi paling jujur yang bisa dibangun dari data kami: jalan level demi level, tidak
    mengasumsikan bentuk kurva apa pun. Kalau buku tidak cukup, `penuh=False` dan sisanya disebut -
    itu jawaban, bukan kegagalan alat.
    """
    if not levels or not mid or not size_usd or size_usd <= 0:
        return {"sah": False, "alasan": "buku/mid/ukuran tidak ada", "vw_price": None,
                "dampak_bps": None, "sisa_usd": float(size_usd or 0.0), "penuh": False}
    sisa, unit, terpakai = float(size_usd), 0.0, 0.0
    for px, qty in levels:
        try:
            p, q = float(px), float(qty)
        except (TypeError, ValueError):
            continue
        if p <= 0 or q <= 0:
            continue
        ambil = min(sisa, p * q)
        unit += ambil / p
        terpakai += ambil
        sisa -= ambil
        if sisa <= 1e-9:
            break
    if terpakai <= 0 or unit <= 0:
        return {"sah": False, "alasan": "tidak ada level yang bisa diambil", "vw_price": None,
                "dampak_bps": None, "sisa_usd": sisa, "penuh": False}
    vw = terpakai / unit
    return {"sah": True, "vw_price": round(vw, 12), "dampak_bps": round((vw - mid) / mid * 1e4, 2),
            "sisa_usd": round(sisa, 6), "penuh": sisa <= 1e-6,
            "alasan": None if sisa <= 1e-6 else "buku habis sebelum order terisi penuh",
            "terpakai_usd": round(terpakai, 2)}



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        assert rt_cost() == MEASURED_RT_BPS, "default harus angka yang diukur"
        assert cost_basis() == BASIS_MEASURED
        assert rt_cost(20.0) == 20.0 and cost_basis(20.0) == BASIS_OVERRIDE, "override harus mengubah basis"
        assert gate_gross_bps() == 2 * MEASURED_RT_BPS, "ambang harus 2x ongkos"
        # Angka 59 bukan bulatan sembarang: ia dua fee 30 bps yang berkomposisi, bukan dijumlah.
        # 1 - (1 - 0,0030)^2 = 0,005991 -> 59,9 bps. forge test `test_round_trip_biaya_tetap_
        # terasa_sekitar_dua_kali_fee` mengukur 59. Kalau ini pecah, yang berubah adalah fee pool
        # (DemoPair.sol `FEE_BPS`) atau angkanya memang sudah tidak dari mana-mana.
        composed = (1.0 - (1.0 - FEE_SIDE_BPS / 1e4) ** 2) * 1e4
        assert abs(composed - MEASURED_RT_BPS) <= 1.5, \
            f"59 bps harus = dua fee {FEE_SIDE_BPS:.0f} bps/sisi berkomposisi ({composed:.1f})"
        # ---- model isi (P42): satuan, lantai, dan jalan buku ----
        v1 = dampak_round_trip(0.01, 132022.0, bnb_usd=650.0, skema=ISI_V1)
        v2 = dampak_round_trip(0.01, 132022.0, bnb_usd=650.0, skema=ISI_V2)
        assert v1["sah"] and v2["sah"], (v1, v2)
        # inilah F-D46 dalam dua baris: model lama menyebut dampak 0,0015 bps (dibulat ke 0,0 =
        # "gratis"), model baru 0,9847 bps. Rasionya = harga BNB, karena itulah yang hilang.
        assert v1["dampak_bps"] < 0.002 and v2["dampak_bps"] > 0.9, (v1, v2)
        assert abs(v2["dampak_bps"] / v1["dampak_bps"] - 650.0) < 1.0, (v1, v2)
        # lantai: pool $1 tidak "mahal", dia TIDAK SAH
        kcil = dampak_round_trip(0.01, 1.0, bnb_usd=650.0)
        assert not kcil["sah"] and kcil["dampak_bps"] is None, kcil
        assert dampak_round_trip(0.01, 0, bnb_usd=650.0)["alasan"].startswith("liq_usd")
        # buku ⑨: level 100@1.0 (daya $100) lalu 101@1.0 (daya $101) -> total daya $201
        bk = [["100", "1.0"], ["101", "1.0"]]
        a = isi_buku(bk, 100.0, 150.0)          # 100 di L1 + 50 di L2 -> VWAP 100,3311
        assert a["sah"] and a["penuh"], a
        assert abs(a["vw_price"] - 150.0 / (1.0 + 50.0 / 101.0)) < 1e-6, a
        # dampak_bps dibulat 2 desimal, jadi bandingkan dengan nilai bulat yang sama
        assert abs(a["dampak_bps"] - round((a["vw_price"] / 100.0 - 1.0) * 1e4, 2)) < 1e-9, a
        assert 33.0 < a["dampak_bps"] < 33.3, a
        d = isi_buku(bk, 100.0, 100.0)           # pas satu level -> tanpa dampak
        assert d["penuh"] and abs(d["vw_price"] - 100.0) < 1e-9 and d["dampak_bps"] == 0.0, d
        b = isi_buku(bk, 100.0, 500.0)           # daya buku cuma $201 -> 299 USD tidak terisi
        assert b["sah"] and not b["penuh"] and abs(b["sisa_usd"] - 299.0) < 1e-6, b
        c = isi_buku([], 100.0, 10.0)
        assert not c["sah"] and c["dampak_bps"] is None, c
        print(f"self-test LOLOS ({MEASURED_RT_BPS} terukur / {ASSUMED_RT_BPS} diasumsikan / "
              f"ambang gross {gate_gross_bps():.0f} bps / model isi {ISI_V2} "
              f"lantai ${LIQ_LANTAI_USD:,.0f})")
        return

    print(f"ongkos round-trip yang DIPAKAI   : {MEASURED_RT_BPS:.1f} bps   (basis {BASIS_MEASURED})")
    print(f"ongkos round-trip yang DIASUMSIKAN: {ASSUMED_RT_BPS:.1f} bps   "
          f"(tidak dipakai sebagai default lagi)")
    print(f"ambang gross yang harus dilampaui : {gate_gross_bps():.1f} bps   (= 2x yang dipakai)")
    for v, basis, why in provenance():
        print(f"  {v:6.1f} bps [{basis}] <- {why}")
    print("\nOverride sekali-pakai: `--cost <bps>` -> basis tercatat "
          f"`{BASIS_OVERRIDE}` di artefak, jangan dikutip sebagai angka terukur.")


if __name__ == "__main__":
    main()
