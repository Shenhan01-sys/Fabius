"""Daftar field setiap jenis rekaman + deteksi pergeseran skema.

Kenapa ini perkakas, bukan catatan tangan: skema rekaman adalah bagian dari klaim. `snapshotHash`
dan `decisionHash` dihitung atas struktur field tertentu; kalau field bertambah tanpa siapa pun
menyadari, dua hal buruk terjadi sekaligus - angka lama tidak sebanding dengan angka baru, dan
"perhitungan ulang dari repo" tidak lagi menghasilkan hash yang sama. Alat ini membandingkan
kumpulan field baris PERTAMA vs baris TERAKHIR per berkas, per jenis rekaman, dan berhenti
non-zero kalau beda.

    python -X utf8 vault/scripts/dump_schemas.py
"""
import io
import json
import os
import sys
# Windows: cmd.exe default cp1252 dan glyph yang kami cetak (`①④⑥` di arah, `⚠` di laporan)
# bukan bagian dari yang di-hash - jadi encoding stdout yang disetel, bukan stringnya.
# Tanpa ini, `print` bisa pecah DI TENGAH tabel dan separuh hasilnya terbaca seperti laporan penuh.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # stdout tanpa reconfigure (mis. tertangkap harness) = biarkan apa adanya

FAB = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.isfile(os.path.join(FAB, "foundry.toml")):
    sys.exit(f"FAB bukan akar Fabius: {FAB}\n     harus berisi foundry.toml - berhenti, jangan menebak.")

TARGETS = [
    ("universe/bsc-universe.jsonl", "snapshot universe"),
    ("universe/wallet-flow.jsonl", "aliran wallet (bidang ⑦)"),
    ("decisions/direction-20260924Z.jsonl", "keputusan arah"),
    ("decisions/direction-20260925.jsonl", "keputusan arah"),
    ("decisions/ledger-20260926Z.jsonl", "penilaian hasil"),
    ("decisions/security-20260924Z.jsonl", "gerbang ④"),
    ("decisions/whale-sweep-90d.json", "uji horison whale (artefak)"),
]

drift = 0
for rel, label in TARGETS:
    p = os.path.join(FAB, *rel.split("/"))
    if not os.path.isfile(p):
        print(f"\n### {rel}  ({label})\n    tidak ada di repo")
        continue
    rows = [l for l in io.open(p, encoding="utf-8", errors="replace") if l.strip()]
    if rel.endswith(".json") and not rel.endswith(".jsonl"):
        obj = json.loads(rows[0]) if len(rows) == 1 else json.loads(io.open(p, encoding="utf-8").read())
        print(f"\n### {rel}  ({label}) · 1 objek")
        print("    field:", ", ".join(sorted(obj)))
        for k in ("generated_utc", "prereg", "credit", "horizons", "wallets", "n"):
            if k in obj:
                v = json.dumps(obj[k])[:70] if not isinstance(obj[k], (int, str)) else obj[k]
                print(f"    {k} = {v}")
        continue
    first, last = json.loads(rows[0]), json.loads(rows[-1])
    # Perpindahan field TIDAK otomatis berarti drift. `wallet-flow.jsonl` memang polimorfik:
    # satu berkas, beberapa jenis baris (`tx`, `px`, `pull`, `err`) dengan shape berbeda.
    # Versi pertama alat ini membandingkan baris pertama vs terakhir dan melaporkan "drift" untuk
    # berkas yang sehat - jadi pembandingannya digolongkan dulu pada kunci jenis baris.
    if "k" in first or "k" in last:
        bykind = {}
        for l in rows:
            try:
                d = json.loads(l)
            except json.JSONDecodeError:
                continue
            bykind.setdefault(str(d.get("k")), []).append(set(d))
        print(f"\n### {rel}  ({label}) · {len(rows)} baris · {len(bykind)} jenis")
        for kk, sets in sorted(bykind.items()):
            common = set.intersection(*sets) if sets else set()
            union = set.union(*sets) if sets else set()
            print(f"    k={kk:6} n={len(sets):5}  tetap: {', '.join(sorted(common)) or '-'}")
            if union - common:
                print(f"           opsional: {', '.join(sorted(union - common))}")
        continue
    kf, kl = set(first), set(last)
    print(f"\n### {rel}  ({label}) · {len(rows)} baris")
    print("    field baris-1 :", ", ".join(sorted(kf)))
    print("    field terakhir:", ", ".join(sorted(kl)))
    if kf != kl:
        drift += 1
        print(f"    PERGESERAN  : baru={sorted(kl - kf)}  hilang={sorted(kf - kl)}")
        for k in ("schema", "snapshot_utc", "generated_utc"):
            if k in first or k in last:
                print(f"    {k}: baris-1={first.get(k)} terakhir={last.get(k)}")
print(f"\n{drift} berkas dengan perpindahan skema (field baris pertama != baris terakhir).")
sys.exit(1 if drift else 0)
