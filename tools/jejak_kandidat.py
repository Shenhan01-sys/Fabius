"""P161: pemeriksa JEJAK kandidat bot - dari kiriman bertanda tangan sampai slot buku, tiap tahap diperiksa dari rekaman publik repo.

Tahap (engine/seleksi.py TAHAP): diterima -> gerbang -> registri -> dipin -> bayangan -> penantang -> slot -> pembunuh -> sinyal_chain.
Status: OK / BELUM / GAGAL (rekaman tidak cocok: jejak rusak di sini) / TAK_TERPERIKSA (tidak bisa diperiksa di mesin ini; bukan OK) / TIDAK_BERLAKU.

Pakai:  python -X utf8 tools/jejak_kandidat.py <bot_id | submission_sha> [--chain] [--hitung-ulang] [--json] [--root DIR]
        python -X utf8 tools/jejak_kandidat.py --semua [--json]
  --chain         baca LockRegistry.lockedAt + SignalAnchor.getCommit lewat RPC publik chain 97 (BACA SAJA; alamat dari deployments/97.json)
  --hitung-ulang  hitung ulang ledger maju dari bar repo + cari potongan bar yang menghasilkan data_hash laporan gerbang
Kode keluar: 0 tidak ada GAGAL · 2 ada tahap GAGAL · 3 kandidat tidak ditemukan.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, ROOT]

from engine import seleksi                                           # noqa: E402


class BacaChain:
    """Pembaca chain 97 BACA SAJA (eth_call): tidak ada kunci, tidak ada transaksi."""

    def __init__(self, root: str = ROOT):
        import evm
        import signal_commit as sc
        self.sc = sc
        addrs = sc.load_addresses(os.path.join(root, "deployments", f"{sc.CHAIN_ID}.json"))
        if not (addrs.get("anchor") and addrs.get("registry") and addrs.get("committer")):
            raise RuntimeError("deployments/97.json tidak memuat SignalAnchor + LockRegistry + committer")
        self.committer = addrs["committer"]
        ev = evm.Evm(sc.rpc_urls(), sc.CHAIN_ID)
        ev.chain_check()
        self.cv = sc.AnchorView(ev, addrs["anchor"], addrs["registry"])

    def locked_at(self, label: str, sha: str) -> int:
        return int(self.cv.locked_at(self.committer, label, sha))

    def komit(self, bot_id: str, spec_sha: str, tick: dict):
        c = self.cv.get_commit(self.sc.commit_id(self.committer, bot_id, spec_sha, self.sc.asof_s_of(tick)))
        return c if int(str(c["committer"]), 16) else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("kunci", nargs="?", help="bot_id atau submission_sha (0x...)")
    ap.add_argument("--semua", action="store_true", help="jejak semua kiriman di registri + salinan publik")
    ap.add_argument("--chain", action="store_true", help="baca lockedAt + komit sinyal dari chain 97 (baca saja)")
    ap.add_argument("--hitung-ulang", action="store_true", help="hitung ulang ledger maju + data_hash laporan dari bar repo")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--root", default=ROOT, help="salinan repo (bawaan: repo ini)")
    a = ap.parse_args()
    if not a.semua and not a.kunci:
        ap.error("beri <bot_id | submission_sha> atau --semua")
    ch = BacaChain(a.root) if a.chain else None
    kw = {"chain": ch, "hitung_ulang": a.hitung_ulang}
    hasil = seleksi.semua(a.root, **kw) if a.semua else [seleksi.jejak(a.root, a.kunci, **kw)]
    if a.json:
        print(json.dumps(hasil if a.semua else hasil[0], ensure_ascii=False, indent=1))
    else:
        if a.semua and not hasil:
            print("registri + salinan publik kosong: belum ada kiriman yang ditinjau")
        for j in hasil:
            print(seleksi.teks(j))
            print()
    if not a.semua and not hasil[0]["ditemukan"]:
        return 3
    return 2 if any(j.get("rusak_di") for j in hasil) else 0


if __name__ == "__main__":
    raise SystemExit(main())
