"""P161: UJI KERING jalur kandidat bot ujung-ke-ujung dengan KODE SUNGGUHAN, di folder sementara, pada bar repo, dengan jam simulasi.

Urutan (sama dengan produksi, tiap langkah memanggil modul yang dipakai produksi):
  1. kiriman `kind=template|rule` ditandatangani kunci SEKALI-PAKAI (dibuat di memori, tidak dicetak, tidak disimpan) -> `pengajuan.Antrean.terima`
     (gerbang: skema + tanda tangan EIP-712 + nonce) pada t terima;
  2. tinjauan harian berikutnya 08:45Z: `tinjau_pengajuan.tinjau` (G1-G11 + KPI pada bar s/d bar tertutup terakhir; petahana G10 = buku hidup)
     -> registri P83 + laporan ber-sha + spesifikasi lolos;
  3. pin spesifikasi: `pin_spec.sah` + tiruan LockRegistry BERLABEL SIMULASI (tidak ada transaksi);
  4. ledger maju harian 08:40Z: `paper_tick.init_bot` (genesis otomatis bot penerbit) + `paper_tick.tick_bot`, bar dipotong pada jam simulasi;
  5. epoch buku 08:44Z: `engine.cli._book_epoch` (idempoten per epoch 30 hari; gerbang penantang terhadap buku sekarang, bar dipotong);
  6. pemeriksa jejak `seleksi.jejak` (hitung ulang dari bar) + rencana komit worker (`operator_loop.bot_komit` mode `slot` + `signal_commit.plan`,
     tanpa kunci = hanya rencana).
Tidak ada jaringan, kunci asli, transaksi, atau berkas repo yang ditulis (semua di folder sementara; `--simpan DIR` menyimpannya untuk diperiksa).
Batas: kode + kunci HARI INI dijalankan pada jam lampau = bukti MEKANISME, bukan klaim kinerja historis, bukan bukti edge.

Pakai:  python -X utf8 tools/uji_jalur_kandidat.py [--mulai 2026-05-01] [--hari 70] [--kind template|rule] [--cepat] [--simpan DIR] [--json]
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import time
from types import SimpleNamespace
from typing import Any, Callable, Dict, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, ROOT]

from engine import cli, ledger, registri, seleksi, submission        # noqa: E402
from engine.data import load_csv_dir                                 # noqa: E402
from engine.gates import GateParams                                  # noqa: E402

BARS = os.path.join(ROOT, "ledger", "bars")
CONTOH = {"template": os.path.join(ROOT, "engine", "examples", "submission.example.json"),
          "rule": os.path.join(ROOT, "engine", "examples", "submission.rule.example.json")}
ID_UJI = {"template": "UJI-TREND-ETH-30", "rule": "UJI-PULLBACK-1"}
DAY_S = 86_400
KOMITER_SIMULASI = "0x0000000000000000000000000000000000005151"      # bukan dompet sungguhan: hanya kunci kamus tiruan chain


class ChainSimulasi:
    """Tiruan LockRegistry + SignalAnchor BERLABEL SIMULASI: pin dicatat di memori, tidak ada transaksi, tidak ada komit sinyal."""
    committer = KOMITER_SIMULASI
    label = "SIMULASI (tiruan chain di memori, bukan chain 97)"

    def __init__(self):
        self.pins: Dict[tuple, int] = {}

    def pin(self, label: str, sha: str, t_s: int) -> None:
        self.pins.setdefault((label, sha), int(t_s))

    def locked_at(self, label: str, sha: str) -> int:
        return self.pins.get((label, sha), 0)

    def komit(self, bot_id: str, spec_sha: str, tick: dict):
        return None


class AnchorSimulasi:
    """Bentuk `signal_commit.AnchorView` di atas ChainSimulasi (untuk `signal_commit.plan`): kunci = pin simulasi, belum ada komit apa pun."""

    def __init__(self, ch: ChainSimulasi):
        self.ch = ch

    def max_lag(self) -> int:
        return 43_200

    def reveal_window(self) -> int:
        return 604_800

    def locked_at(self, committer: str, bot_id: str, spec_sha: str) -> int:
        return self.ch.locked_at(bot_id, spec_sha)

    def get_commit(self, cid: bytes) -> dict:
        import signal_commit as sc
        return {"committer": sc.ZERO_ADDR, "asof": 0, "committedAt": 0, "n": 0, "revealed": 0, "missed": False, "botId": sc.ZERO32,
                "specSha": sc.ZERO32, "root": sc.ZERO32}

    def is_revealed(self, cid: bytes, leaf: bytes) -> bool:
        return False


class BarDipotong:
    """`paper_tick.Views` yang memotong bar pada bar tertutup terakhir jam simulasi (tidak ada bar masa depan)."""

    def __init__(self, penuh: Dict[str, Any], cut_ms: int):
        self.bars_dir, self._penuh, self.cut, self._cache = BARS, penuh, cut_ms, {}

    def get(self, view: str):
        if view not in self._cache:
            if view not in self._penuh:
                self._penuh[view] = load_csv_dir(BARS, cli.DATA_SYMBOLS, funding_view=view)
            self._cache[view] = self._penuh[view].upto(self.cut)
        return self._cache[view]


def _iso(t_s: int) -> str:
    return ledger.utc_iso(int(t_s) * 1000)


def _hari(t_s: int, jam: int, menit: int) -> int:
    return (int(t_s) // DAY_S) * DAY_S + jam * 3600 + menit * 60


def kiriman(kind: str, acct) -> Dict[str, Any]:
    """Formulir contoh repo dengan dompet kunci sekali-pakai + bot_id uji (bukan nama yang dicadangkan)."""
    with open(CONTOH[kind], encoding="utf-8") as f:
        sub = json.load(f)
    sub["identity"]["issuer_wallet"] = sub["identity"]["payout_wallet"] = acct.address
    sub["spec"]["bot_id"] = ID_UJI[kind]
    return sub


def jalankan(mulai: str = "2026-05-01", hari: int = 70, kind: str = "template", cepat: bool = False, simpan: Optional[str] = None,
             log: Optional[Callable[[str], None]] = print) -> Dict[str, Any]:
    try:
        from eth_account import Account
        from eth_account.messages import encode_typed_data
    except ImportError as e:                                                  # pragma: no cover
        raise RuntimeError("uji kering butuh eth-account (kunci sekali-pakai untuk tanda tangan EIP-712)") from e
    import operator_loop as ol
    import paper_tick as pt
    import pengajuan as pj
    import pin_spec as ps
    import signal_commit as sc
    import tinjau_pengajuan as tp
    say = log or (lambda m: None)
    root = simpan or tempfile.mkdtemp(prefix="uji-jalur-")
    for d in ("ledger/pengajuan", "ledger/paper", "ledger/book", "gerbang"):
        os.makedirs(os.path.join(root, d), exist_ok=True)
    gp = GateParams.fast() if cepat else GateParams()
    penuh: Dict[str, Any] = {}
    ch = ChainSimulasi()
    out: Dict[str, Any] = {"root": root, "kind": kind, "gerbang_param": "cepat (uji)" if cepat else "terkunci (GateParams())", "chain": ch.label}

    # 1. kiriman -> gerbang
    t0 = ledger.iso_ms(f"{mulai}T12:00:00Z") // 1000
    acct = Account.create()                                                   # kunci sekali-pakai: tidak dicetak, tidak disimpan
    sub = kiriman(kind, acct)
    nonce, deadline = 1, t0 + 600
    sig = "0x" + acct.sign_message(encode_typed_data(full_message=submission.typed_data(sub, pj.CHAIN_ID, nonce, deadline))).signature.hex().removeprefix("0x")
    antre = pj.Antrean(os.path.join(root, "gerbang"), now=lambda: t0, kinds=submission.ENABLED_KINDS)
    code, resp = antre.terima({"submission": sub, "signature": sig, "nonce": nonce, "deadline": deadline})
    bot, sha = sub["spec"]["bot_id"], submission.submission_sha(sub)
    out.update(bot_id=bot, submission_sha=sha, issuer=acct.address, gerbang_http=code)
    say(f"1 DITERIMA   {_iso(t0)}  POST /bots/submit -> HTTP {code} {resp.get('status') or resp.get('error')}  bot {bot}  sha {sha[:18]}…")
    if code != 201:
        out["berhenti"] = f"gerbang menolak: {resp}"
        return out

    # 2. tinjauan harian berikutnya (rantai GitHub bot-review sesudah paper-ledger)
    t_rev = _hari(t0 + DAY_S, 8, 45)
    cut = ledger.last_closed_bar(t_rev * 1000)
    md = BarDipotong(penuh, cut).get("actual")
    rows = [r for r in antre.daftar() if r["status"] in ("waiting for review", "queued")]
    with contextlib.redirect_stdout(io.StringIO()):
        inc = cli._book_pnls(md, root)
    hasil = tp.tinjau(rows, os.path.join(root, "ledger", "pengajuan"), md, inc, gate_params=gp, log=lambda m: None)
    reg = registri.load(os.path.join(root, "ledger", "pengajuan", "registri.jsonl"))
    vonis = hasil[0]["vonis"] if hasil else None
    out.update(vonis=vonis, k=reg[-1]["k"] if reg else None, petahana_tinjauan=sorted(inc))
    rep = json.load(open(os.path.join(root, "ledger", "pengajuan", "laporan", f"{sha}.json"), encoding="utf-8")) if vonis else {}
    say(f"2 GERBANG    {_iso(t_rev)}  bar s/d {ledger.date_of(cut)}  vonis {vonis}  gagal {rep.get('gagal') or '-'}  "
        f"report_sha {str(rep.get('report_sha'))[:18]}…  petahana G10 {sorted(inc)}")
    say(f"3 REGISTRI   k {out['k']}  catatan {len(reg)}  verify {registri.verify(reg) or 'SAH'}")
    if vonis != registri.LOLOS:
        out["jejak"] = seleksi.jejak(root, sha, chain=ch, hitung_ulang=True, now_s=t_rev, bars_dir=BARS)
        say(f"   jalur berhenti di gerbang (vonis {vonis}): tahap sesudahnya TIDAK_BERLAKU")
        return _tutup(out, simpan, root, say)

    # 3b. pin spesifikasi (worker; di sini tiruan berlabel SIMULASI)
    specs, masalah = ps.sah(root)
    for s in specs:
        ch.pin(s["bot_id"], s["spec_sha"], t_rev + 300)
    say(f"3b DIPIN      {_iso(t_rev + 300)}  {len(specs)} spesifikasi (SIMULASI, tanpa transaksi){' masalah ' + masalah[0] if masalah else ''}")

    # 4-5. ledger maju harian + epoch buku harian (idempoten per epoch)
    paper = os.path.join(root, "ledger", "paper")
    buku = os.path.join(root, "ledger", "book", "buku.jsonl")
    epoch_lihat = set()
    akhir = t_rev
    for d in range(1, hari + 1):
        now = _hari(t_rev + d * DAY_S, 8, 40)
        views = BarDipotong(penuh, ledger.last_closed_bar(now * 1000))
        with contextlib.redirect_stdout(io.StringIO()):
            if not os.path.exists(os.path.join(paper, f"{bot}.jsonl")):
                pt.init_bot(bot, paper, now * 1000, False, root=root)
            pt.tick_bot(bot, paper, views, now * 1000, False, root=root)
            t_ep = now + 240
            a = SimpleNamespace(file=buku, ledger=paper, bars=BARS, now=_iso(t_ep), write=True, no_gates=False, root=root, gate_params=gp,
                                potong_ms=ledger.last_closed_bar(t_ep * 1000))
            cli._book_epoch(a)
        akhir = t_ep
        recs = ledger.load(buku)
        if recs and recs[-1].get("type") == "epoch" and recs[-1]["epoch"] not in epoch_lihat:
            epoch_lihat.add(recs[-1]["epoch"])
            for ln in _fmt(recs[-1]).splitlines():
                say(f"5 {ln}")
    g = ledger.load(os.path.join(paper, f"{bot}.jsonl"))
    st = seleksi.forward.stats_for(bot, g, seleksi.forward.common_end({bot: g}, ledger.last_closed_bar(akhir * 1000)))
    out.update(genesis=g[0].get("first_asof_date"), hari_bayangan=st.shadow_days, net_bayangan_bps=st.shadow_score_bps)
    say(f"4 BAYANGAN   genesis bar {g[0].get('first_asof_date')}  {st.shadow_days} hari  tick {st.n_tick} settle {st.n_settle}  "
        f"net {'-' if st.shadow_score_bps is None else f'{st.shadow_score_bps:+.1f}'} bps")
    recs = ledger.load(buku)
    di_buku = [e.bot_id for e in seleksi.book_live.current_book(recs)]
    keputusan = [(r["epoch"], k) for r in recs[1:] for k in r.get("keputusan") or [] if k[0] == bot]
    out.update(epoch=[r["epoch"] for r in recs[1:]], keputusan=keputusan, slot=bot in di_buku, buku=di_buku,
               verify_buku=seleksi.book_live.verify_book(recs) or "SAH")
    say(f"6 SLOT       buku {di_buku}  verify {out['verify_buku']}")

    # 6. pemeriksa jejak + rencana komit worker (KOMIT_PENERBIT=slot, tanpa kunci = rencana)
    bots, spc, cat = ol.bot_komit(root, "slot", bots=[])
    acts = sc.plan(bots, paper, BarDipotong(penuh, ledger.last_closed_bar(akhir * 1000)), AnchorSimulasi(ch), ch.committer, None, akhir,
                   specs=spc) if bots else []
    out["rencana_komit"] = {k: sum(1 for x in acts if x.kind == k) for k in ("commit", "reveal", "ok", "skip", "alarm")}
    say(f"7 WORKER     KOMIT_PENERBIT=slot -> bot {bots or '-'}  rencana {out['rencana_komit']}  ({'; '.join(cat)})")
    out["jejak"] = seleksi.jejak(root, sha, chain=ch, hitung_ulang=True, now_s=akhir, bars_dir=BARS)
    return _tutup(out, simpan, root, say)


def _fmt(r: dict) -> str:
    from engine import book_live
    return book_live.fmt_epoch(r)


def _tutup(out: Dict[str, Any], simpan: Optional[str], root: str, say) -> Dict[str, Any]:
    j = out["jejak"]
    for ln in seleksi.teks(j).splitlines():
        say(f"J {ln}")
    if not simpan:
        shutil.rmtree(root, ignore_errors=True)
        out["root"] = None
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mulai", default="2026-05-01", help="tanggal kiriman simulasi (UTC); kiriman 12:00Z, tinjauan esok 08:45Z")
    ap.add_argument("--hari", type=int, default=70, help="hari jam maju sesudah tinjauan (slot butuh >= 60 hari bayangan + batas epoch 30 hari)")
    ap.add_argument("--kind", choices=sorted(CONTOH), default="template")
    ap.add_argument("--cepat", action="store_true", help="GateParams.fast() (uji); bawaan = GateParams terkunci")
    ap.add_argument("--simpan", help="folder untuk menyimpan salinan repo simulasi (bawaan: folder sementara dihapus)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    t = time.time()
    out = jalankan(a.mulai, a.hari, a.kind, a.cepat, os.path.abspath(a.simpan) if a.simpan else None, log=None if a.json else print)
    out["detik"] = round(time.time() - t, 1)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
    else:
        print(f"selesai dalam {out['detik']} s | rusak_di {out['jejak'].get('rusak_di')}")
    return 2 if out.get("jejak", {}).get("rusak_di") else 0


if __name__ == "__main__":
    raise SystemExit(main())
