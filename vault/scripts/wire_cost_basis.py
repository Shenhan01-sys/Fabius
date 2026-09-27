"""Sekali-jalan: setiap artefak ongkos menyimpan BASIS-nya, bukan cuma nilainya.

P10 menghasilkan satu angka round-trip (59 bps terukur), tapi angka saja tidak menjawab pertanyaan
yang salah di repo ini: "net ini dihitung dengan penggaris apa?" `cost_bps_rt: 20` dan
`cost_bps_rt: 59` terbaca sama meyakinkannya di JSON. Jadi setiap artefak yang memuat ongkos kini
memuat `cost_basis` juga - `measured-own-venue`, `assumed-inherited`, atau `cli-override` ketika
seseorang memakai `--cost`.

Idempoten: baris yang sudah punya `cost_basis` tidak disentuh. Assert per situs: kalau pola tidak
ketemu persis satu kali, skrip berhenti dan melaporkan.

    python -X utf8 vault/scripts/wire_cost_basis.py           # jalankan
    python -X utf8 vault/scripts/wire_cost_basis.py --check    # laporkan saja
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "tools")
CHECK_ONLY = "--check" in sys.argv

# (berkas, fragmen yang harus ada persis sekali, pengganti)
SITES = [
    ("ledger.py",
     '"cost_bps_rt": RT_COST_BPS,',
     '"cost_bps_rt": RT_COST_BPS, "cost_basis": costs.cost_basis(),'),
    ("backtest.py",
     '"cost_bps_rt": cost,',
     '"cost_bps_rt": cost, "cost_basis": costs.cost_basis(a.cost),'),
    ("smartmoney_score.py",
     '"cost_bps_rt": RT_COST_BPS,',
     '"cost_bps_rt": RT_COST_BPS, "cost_basis": costs.cost_basis(),'),
    ("maker_ledger.py",
     '"rt_cost_bps": RT_COST_BPS,',
     '"rt_cost_bps": RT_COST_BPS, "rt_cost_basis": costs.cost_basis(),'),
    ("screen_universe.py",
     '"RT_COST_BPS": RT_COST_BPS,',
     '"RT_COST_BPS": RT_COST_BPS, "COST_BASIS": costs.cost_basis(),'),
]


def main():
    done = bad = 0
    for fname, old, new in SITES:
        p = os.path.join(TOOLS, fname)
        if not os.path.isfile(p):
            print(f"TIDAK ADA: {fname}")
            bad += 1
            continue
        t = io.open(p, encoding="utf-8").read()
        if "cost_basis" in t or "COST_BASIS" in t:
            print(f"sudah memakai basis  {fname}")
            continue
        n = t.count(old)
        if n != 1:
            print(f"POLA {n}x (harus 1x): {fname} :: {old}")
            bad += 1
            continue
        done += 1
        if CHECK_ONLY:
            print(f"akan ditulis basis    {fname}")
            continue
        io.open(p, "w", encoding="utf-8", newline="\n").write(t.replace(old, new))
        print(f"ditulis basis         {fname}")
    print(f"\n{len(SITES)} situs · {done} diubah · {bad} GAGAL.")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
