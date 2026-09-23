"""Regenerasi `universe/manifest.txt` dari dataset — bukti kecil yang boleh masuk Git.

Dataset mentahnya (bsc-universe.jsonl, 90 baris per jam, terus membesar) sengaja tidak di-commit:
`.gitignore` mengecualikan `*.jsonl`. Yang di-commit gantinya adalah file ini — satu baris per
snapshot, memuat sha256 snapshot itu sendiri.

Kenapa ini bukan mainan: tiap `sha256` dihitung saat pengambilan data, dari kanonisasi
`json.dumps(sort_keys=True, separators=(",", ":"))`. Menaruh daftar hash itu ke dalam riwayat git
memberi catatan yang tidak bisa ditulis mundur — kamu tidak bisa menyisipkan "snapshot dari minggu
lalu" ke dalam commit yang baru dibuat hari ini tanpa mengubah riwayat yang bisa dilihat publik.
Kurang lebih itu pengganti terbaik dari "timestamp eksternal" tanpa perlu mengirim apa pun ke luar
mesin, dan nanti bisa dinaikkan jadi satu baris on-chain lewat DecisionAnchor.

Ditulis ulang penuh setiap dijalankan (bukan append), jadi idempoten dan tidak bisa menghasilkan
baris ganda. sha256 diambil dari file, bukan dihitung ulang: kalau datanya diubah setelah
penulisan, mismatch ini akan terlihat.

Pakai:  python write_universe_manifest.py
"""
import json
import os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
UNIV = HERE
DATA = os.path.join(UNIV, "bsc-universe.jsonl")
OUT = os.path.join(UNIV, "manifest.txt")


def main():
    if not os.path.exists(DATA):
        raise SystemExit(f"dataset belum ada: {DATA}")

    rows = []
    mismatched = 0
    for line in open(DATA, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        stored = d.get("sha256")
        # Verifikasi: hash yang tersimpan harus cocok dengan isi baris, tanpa kunci sha256-nya.
        probe = {k: v for k, v in d.items() if k != "sha256"}
        recomputed = json.dumps(probe, sort_keys=True, separators=(",", ":")).encode()
        import hashlib
        ok = "0x" + hashlib.sha256(recomputed).hexdigest()
        if stored and ok != stored:
            mismatched += 1
        priced = sum(1 for r in d.get("rows", []) if r.get("pool") and r.get("price_usd"))
        rows.append("\t".join([
            str(d.get("snapshot_utc")),
            str(d.get("schema", "1")),
            str(d.get("universe_size", 0)),
            str(d.get("survivable_count", 0)),
            str(d.get("fully_evaluated_count", "-")),
            str(priced),
            str(stored or "-"),
        ]))

    header = "\t".join(["snapshot_utc", "schema", "universe", "lolos", "dinilai_penuh",
                        "pool_berharga", "sha256_snapshot"])
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = (f"# manifest dibuat ulang {stamp} — file ini dihasilkan oleh "
            f"_research/write_universe_manifest.py, jangan disunting manual\n"
            f"# dataset sumber: bsc-universe.jsonl ({len(rows)} snapshot)\n"
            f"# kolom sha256 = hash kanonik snapshot pada saat pengambilan, bukan hash baris ini\n"
            + header + "\n" + "\n".join(rows) + "\n")
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(body)

    print(f"{len(rows)} snapshot -> {OUT}")
    if mismatched:
        print(f"⚠️  {mismatched} snapshot TIDAK cocok dengan sha256 yang tersimpan "
              f"-> datanya berubah setelah ditulis. Jangan percaya isinya, laporkan.")
    else:
        print("semua sha256 cocok dengan isi barisnya (integritas file utuh)")


if __name__ == "__main__":
    main()
