"""P161 B1b: peninjau pengajuan bot di repo publik. Dijalankan `.github/workflows/bot-review.yml` (dipicu rantai paper-ledger sekali sehari).

Untuk tiap kiriman di antrean gerbang (`GET /bots/submissions`) yang belum ada di registri P83, urut waktu terima:
  1. salinan publik kiriman -> `ledger/pengajuan/masuk/<sha>.json` (formulir tanpa kontak + tanda tangan + nonce + deadline + t terima);
  2. `review.tinjau_tercatat` pada bar harian repo (`ledger/bars`, histori sejak 2020) dengan identitas diverifikasi ULANG pada `now = t terima`
     (tanda tangan berlaku <= 1 jam; gerbang sudah memeriksanya saat masuk, di sini siapa pun bisa mengulangnya) -> registri hash-berantai + vonis;
  3. laporan ber-sha -> `ledger/pengajuan/laporan/<sha>.json`;
  4. vonis LOLOS_SHADOW -> spesifikasi tercatat `ledger/pengajuan/spec/<bot_id>.json` (sumber ledger maju B1c; sha-nya di-pin on-chain oleh worker);
  5. kiriman yang tidak dijalankan gerbang (masa tunggu keluarga, formulir ditolak sebelum gerbang) -> `ledger/pengajuan/status.json`.
Kontak penerbit tidak ikut hash dan tidak pernah sampai ke repo: validasi memakai pengganti "disimpan privat".

Pakai:  python -X utf8 tools/tinjau_pengajuan.py [--gerbang URL] [--maks 5]
"""
from __future__ import annotations

import argparse
import copy
import dataclasses
import json
import os
import sys
import urllib.request
from typing import Callable, Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine import registri, review as reviewmod, submission       # noqa: E402

GERBANG = "https://fabius-x402-production.up.railway.app"
DIR = os.path.join(ROOT, "ledger", "pengajuan")
KONTAK_PRIVAT = "disimpan privat di gerbang"


def ambil(gerbang: str) -> List[dict]:
    req = urllib.request.Request(f"{gerbang}/bots/submissions", headers={"User-Agent": "fabius-bot-review"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())["submissions"]


def _tulis(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def tinjau(rows: List[dict], folder: str, data, incumbents, gate_params=None, maks: int = 5, log: Callable[[str], None] = print) -> List[dict]:
    """-> ringkasan per kiriman yang diproses. Berkas ditulis di `folder` (biasanya ledger/pengajuan)."""
    reg_path = os.path.join(folder, "registri.jsonl")
    status_path = os.path.join(folder, "status.json")
    status: Dict[str, dict] = json.load(open(status_path, encoding="utf-8")) if os.path.exists(status_path) else {}
    sudah = {e.get("submission_sha") for e in (registri.load(reg_path) if os.path.exists(reg_path) else [])}
    out = []
    for row in sorted(rows, key=lambda r: r["t"]):
        sha = row["submission_sha"]
        if sha in sudah or status.get(sha, {}).get("final"):
            continue
        if len(out) >= maks:
            break
        pub = row["submission"]
        sub = copy.deepcopy(pub)
        sub["identity"]["contact"] = KONTAK_PRIVAT                            # tidak ikut hash: sha + tanda tangan tidak berubah
        if submission.submission_sha(sub) != sha:
            status[sha] = {"status": "rejected", "alasan": "submission_sha tidak cocok dengan isi antrean", "final": True, "t": row["t"]}
            out.append({"id": sha, "vonis": "SHA_TIDAK_COCOK"})
            continue
        _tulis(os.path.join(folder, "masuk", f"{sha}.json"), {k: row[k] for k in ("t", "submission_sha", "spec_sha", "bot_id", "issuer", "payout",
                                                                                     "chain_id", "nonce", "deadline", "signature", "payout_signature",
                                                                                     "submission")})
        ident = {"signature": row["signature"], "payout_signature": row.get("payout_signature"), "chain_id": row.get("chain_id", 97),
                 "nonce": row["nonce"], "deadline": row["deadline"], "now_s": row["t"]}
        rc, rep, msgs = reviewmod.tinjau_tercatat(sub, data, incumbents, path=reg_path, now_s=row["t"], catat=True, identity=ident,
                                                  gate_params=gate_params)
        for m in msgs:
            log(f"{row['bot_id']}: {m}")
        if rep is None:                                                       # masa tunggu keluarga / registri: belum dinilai, dicoba lagi besok
            status[sha] = {"status": "queued", "alasan": "; ".join(msgs)[:300], "final": False, "t": row["t"]}
            out.append({"id": sha, "vonis": None, "pesan": msgs})
            continue
        _tulis(os.path.join(folder, "laporan", f"{sha}.json"), rep)
        if rep["vonis"] in registri.TANPA_UJI or not rep.get("mengikat", True):
            status[sha] = {"status": "rejected", "alasan": rep["vonis"], "final": True, "t": row["t"]}
        if rep["vonis"] == registri.LOLOS:
            spec = submission.to_botspec(sub)
            _tulis(os.path.join(folder, "spec", f"{row['bot_id']}.json"),
                   {"bot_id": row["bot_id"], "submission_sha": sha, "spec_sha": rep["spec_sha"], "report_sha": rep.get("report_sha"),
                    "t_lolos": row["t"], "issuer": row["issuer"], "payout": row["payout"], "botspec": dataclasses.asdict(spec),
                    "pembunuh": pub["theory"]["pembunuh"]})                          # terstruktur: ditegakkan slots.killer_triggered (B1d)
        out.append({"id": sha, "bot_id": row["bot_id"], "vonis": rep["vonis"], "rc": rc})
    if status:
        _tulis(status_path, status)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gerbang", default=GERBANG)
    ap.add_argument("--maks", type=int, default=5, help="kiriman per putaran (gerbang G1-G11 berat: placebo + bootstrap)")
    ap.add_argument("--data", default=os.path.join(ROOT, "ledger", "bars"))
    a = ap.parse_args()
    from engine import cli
    from engine.data import load_csv_dir
    rows = ambil(a.gerbang)
    baru = [r for r in rows if r["status"] in ("waiting for review", "queued")]          # tertahan masa tunggu dicoba lagi tiap hari
    print(f"antrean gerbang: {len(rows)} kiriman, {len(baru)} menunggu tinjauan")
    if not baru:
        return 0
    md = load_csv_dir(a.data, cli.DATA_SYMBOLS)
    hasil = tinjau(baru, DIR, md, cli._incumbents(md, "book"), maks=a.maks)
    for h in hasil:
        print(json.dumps(h, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
