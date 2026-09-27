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
        print(f"self-test LOLOS ({MEASURED_RT_BPS} terukur / {ASSUMED_RT_BPS} diasumsikan / "
              f"ambang gross {gate_gross_bps():.0f} bps)")
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
