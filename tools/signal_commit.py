"""Komit sinyal ledger paper ke SignalAnchor di chain 97 (M3; F-D80): tick ledger -> batch Merkle (`engine/sinyal.py`) -> `commit()` dalam batas
`maxLag` sesudah penutupan bar -> `reveal()` tiap sinyal.

Sumber kebenaran = ledger yang di-commit (`ledger/paper/<bot>.jsonl`; penulisnya SATU: rantai GitHub, F-D78). Alat ini TIDAK menulis ledger. Ia menghitung
ULANG sinyal setiap tick dari bar yang di-commit (`ledger/bars`), dan MENOLAK mengomit bila hasilnya beda dari tick (target, data_hash, id sinyal, n_aset):
yang dikomit selalu isi ledger, bukan tebakan worker.

Salt per sinyal = HMAC-SHA256(benih, id sinyal), benih = HMAC-SHA256(kunci committer, domain sendiri): deterministik, jadi pengungkapan tidak butuh
penyimpanan apa pun selain kunci itu. Konsekuensi yang harus diingat: mengganti kunci committer = ungkap dulu semua komit yang masih terbuka.

Aturan kirim (semua dicek SEBELUM transaksi, kontrak tetap menegakkan yang sama):
  - tick hanya dikomit bila (botId, specSha) sudah dikunci committer di LockRegistry dan kuncinya tidak lebih baru dari bar;
  - hanya bila masih >= LAG_MARGIN_S sebelum batas `maxLag` (blok bisa lebih lambat dari jam kita) - yang lewat dicatat TERLEWAT, tidak dipaksa;
  - komit yang sudah ada tetapi akarnya beda dari ledger = ALARM (tidak pernah ditimpa; satu komit per bar);
  - tidak mengirim apa pun selama committer masih punya transaksi tertunda (nonce bertumpuk = transaksi ganda).

Pakai (dari akar repo):
  python -X utf8 tools/signal_commit.py                         # rencana dari keadaan chain sekarang; tanpa kunci perlu --committer 0x...
  python -X utf8 tools/signal_commit.py --send                  # kirim komit/ungkap (COMMITTER_PRIVATE_KEY dari env atau .committer.env)
  python -X utf8 tools/signal_commit.py --now 2026-10-03T10:00:00Z     # simulasi jam (rencana saja)
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from engine import chain, ledger                       # noqa: E402
from engine.freshness import StaleBars                 # noqa: E402
from engine.series import DAY_MS                       # noqa: E402
from engine.sinyal import Batch, Entry, Signal, build_batch, signals_at     # noqa: E402
from engine.spec import SPECS                          # noqa: E402

BOTS_DEFAULT = ("B1-TREND", "B3-CARRY")
CHAIN_ID = 97
DEPLOYMENTS = os.path.join(ROOT, "deployments", f"{CHAIN_ID}.json")
COMMITTER_ENV = os.path.join(ROOT, ".committer.env")
KEY_VAR = "COMMITTER_PRIVATE_KEY"
SALT_DOMAIN = b"fabius-signal-salt-v1"
SEED_DOMAIN = b"fabius-signal-salt-seed-v1"
LAG_MARGIN_S = 300
LOOKBACK_DAYS = 10
ZERO32 = b"\x00" * 32
ZERO_ADDR = "0x" + "00" * 20

SIGNAL_TUPLE = "(uint8,bytes32,bytes32,uint64,bytes32,uint8,int256,int256,uint256,bytes32)"
SIG_COMMIT = "commit(bytes32,bytes32,uint64,bytes32,uint32)"
SIG_REVEAL = f"reveal(bytes32,{SIGNAL_TUPLE},bytes32,bytes32[])"
SIG_GET_COMMIT = "getCommit(bytes32)"
SIG_IS_REVEALED = "isRevealed(bytes32,bytes32)"
SIG_LOCKED_AT = "lockedAt(address,bytes32,bytes32)"
SIG_LOCK = "lock(bytes32,bytes32,string)"
COMMIT_OUT = ("(address,uint64,uint64,uint32,uint32,bool,bytes32,bytes32,bytes32)",)
ERRORS = ("ZeroValue()", "NotLocked()", "LockedAfterBar(uint64,uint64)", "BarNotClosed(uint64,uint64)", "TooLate(uint64,uint64,uint64)",
          "AlreadyCommitted(bytes32)", "EmptyMismatch()", "UnknownCommit(bytes32)", "SignalMismatch()", "BadProof()", "AlreadyRevealed(bytes32)",
          "TooManyReveals()", "WindowOpen(uint64)", "NothingMissing()", "AlreadyLocked(bytes32)")


# ---------------------------------------------------------------- murni (diuji tanpa jaringan)

def seed_from_key(pk: str) -> bytes:
    return hmac.new(chain.from_hex(pk), SEED_DOMAIN, hashlib.sha256).digest()


def salt_for(seed: bytes, sig: Signal) -> bytes:
    """Satu salt per sinyal: HMAC atas id sinyal (id sudah mengikat bot, spec, bar, aset, aksi, bobot, harga, data_hash)."""
    return hmac.new(seed, SALT_DOMAIN + b"|" + sig.id().encode("ascii"), hashlib.sha256).digest()


def commit_id(committer: str, bot_id: str, spec_sha: str, asof_s: int) -> bytes:
    """= SignalAnchor.commitId(committer, botId, specSha, asof)."""
    return chain.keccak256(chain.abi_encode(("address", "bytes32", "bytes32", "uint64"),
                                            (committer, chain.ascii32(bot_id), chain.from_hex(spec_sha), asof_s)))


def asof_s_of(tick: dict) -> int:
    return (tick["asof"] + DAY_MS) // 1000


def rebuild_signals(spec, tick: dict, views) -> Tuple[List[Signal], List[str]]:
    """Sinyal tick dihitung ulang dari bar yang di-commit + daftar masalah (kosong = isi tick terbukti sama). Pandangan data = sama dengan pembuat tick."""
    md = views.get("targets" if spec.method == "B3-CARRY" else "actual")
    t = tick["asof"]
    try:
        body = ledger.compute_tick(spec, md, t)
    except StaleBars as e:
        return [], [f"tick {tick.get('asof_date')} tak bisa dihitung ulang ({e})"]
    problems = [f"{k} beda dari hitung-ulang" for k in ("targets", "data_hash", "signal_ids", "n_aset") if tick.get(k) != body[k]]
    sigs = signals_at(spec, ledger.target_view(spec, md.upto(t)), t)
    if [s.id() for s in sigs] != tick.get("signal_ids"):
        problems.append("id sinyal hitung-ulang beda dari tick")
    return sigs, problems


def batch_for(spec, tick: dict, sigs: Sequence[Signal], seed: bytes) -> Batch:
    return build_batch(spec.bot_id, spec.sha(), tick["asof"], list(sigs), [salt_for(seed, s) for s in sigs])


def commit_calldata(spec, tick: dict, b: Batch) -> bytes:
    from evm import calldata
    return calldata(SIG_COMMIT, ("bytes32", "bytes32", "uint64", "bytes32", "uint32"),
                    (chain.ascii32(spec.bot_id), chain.from_hex(spec.sha()), asof_s_of(tick), b.root, len(b.entries)))


def reveal_calldata(cid: bytes, e: Entry) -> bytes:
    from evm import calldata
    return calldata(SIG_REVEAL, ("bytes32", SIGNAL_TUPLE, "bytes32", "bytes32[]"), (cid, tuple(e.signal.abi_fields()), e.salt, list(e.proof)))


# ---------------------------------------------------------------- keadaan chain

class AnchorView:
    """Pembaca SignalAnchor + LockRegistry lewat `evm.Evm`. Uji memakai tiruan dengan metode yang sama."""

    def __init__(self, evm, anchor: str, registry: str):
        self.evm, self.anchor, self.registry = evm, anchor, registry
        self._lag = self._window = None

    def max_lag(self) -> int:
        if self._lag is None:
            self._lag = self.evm.call_decode(self.anchor, "maxLag()", (), (), ("uint64",))[0]
        return self._lag

    def reveal_window(self) -> int:
        if self._window is None:
            self._window = self.evm.call_decode(self.anchor, "revealWindow()", (), (), ("uint64",))[0]
        return self._window

    def locked_at(self, committer: str, bot_id: str, spec_sha: str) -> int:
        return self.evm.call_decode(self.registry, SIG_LOCKED_AT, ("address", "bytes32", "bytes32"),
                                    (committer, chain.ascii32(bot_id), chain.from_hex(spec_sha)), ("uint64",))[0]

    def get_commit(self, cid: bytes) -> dict:
        (c,) = self.evm.call_decode(self.anchor, SIG_GET_COMMIT, ("bytes32",), (cid,), COMMIT_OUT)
        keys = ("committer", "asof", "committedAt", "n", "revealed", "missed", "botId", "specSha", "root")
        return dict(zip(keys, c))

    def is_revealed(self, cid: bytes, leaf: bytes) -> bool:
        return bool(self.evm.call_decode(self.anchor, SIG_IS_REVEALED, ("bytes32", "bytes32"), (cid, leaf), ("bool",))[0])


# ---------------------------------------------------------------- rencana

@dataclass
class Action:
    kind: str                   # commit | reveal | ok | skip | alarm
    bot: str
    asof_date: str
    detail: str
    tick: Optional[dict] = None
    cid: Optional[bytes] = None
    batch: Optional[Batch] = None
    entries: Tuple[Entry, ...] = field(default_factory=tuple)

    def line(self) -> str:
        return f"{self.bot} {self.asof_date} {self.kind.upper():6s} {self.detail}"


def plan(bots: Sequence[str], ledger_dir: str, views, cv, committer: str, seed: Optional[bytes], now_s: int,
         reveal_delay_s: int = 0, lookback_days: int = LOOKBACK_DAYS) -> List[Action]:
    """Apa yang harus dikirim sekarang. Murni terhadap `cv` (keadaan chain) dan berkas ledger/bar; tidak mengirim apa pun.
    Tanpa `seed` (rencana tanpa kunci) akar tidak bisa dihitung: komit yang dibutuhkan tetap dilaporkan, tanpa batch."""
    out: List[Action] = []
    max_lag = int(cv.max_lag())
    for bot in bots:
        spec = SPECS.get(bot)
        if spec is None:
            out.append(Action("alarm", bot, "-", "bot tidak dikenal di engine/spec.py"))
            continue
        path = os.path.join(ledger_dir, f"{bot}.jsonl")
        try:
            records = ledger.load(path)
        except ledger.LedgerError as e:
            out.append(Action("alarm", bot, "-", f"ledger rusak: {e}"))
            continue
        if not records:
            out.append(Action("skip", bot, "-", "belum ada ledger"))
            continue
        problems = ledger.verify_chain(records)
        if problems:
            out.append(Action("alarm", bot, "-", f"rantai ledger tidak sah ({problems[0]}); tidak ada yang dikomit"))
            continue
        if records[0].get("spec_sha") != spec.sha():
            out.append(Action("alarm", bot, "-", "spec_sha ledger != kode worker (image basi atau pivot?); tidak ada yang dikomit"))
            continue
        locked = int(cv.locked_at(committer, bot, spec.sha()))
        ticks = [r for r in records if r["type"] == "tick" and asof_s_of(r) >= now_s - lookback_days * 86400]
        for tk in ticks:
            asof_s, date = asof_s_of(tk), tk["asof_date"]
            cid = commit_id(committer, bot, spec.sha(), asof_s)
            c = cv.get_commit(cid)
            if int(str(c["committer"]), 16) == 0:
                if locked == 0:
                    out.append(Action("skip", bot, date, "spesifikasi belum dikunci committer di LockRegistry"))
                elif locked > asof_s:
                    out.append(Action("skip", bot, date, "tick lebih tua dari kunci committer (tidak bisa dikomit, by design)"))
                elif now_s < asof_s:
                    out.append(Action("skip", bot, date, "bar belum tertutup menurut jam ini"))
                elif now_s - asof_s > max_lag - LAG_MARGIN_S:
                    out.append(Action("skip", bot, date, f"TERLEWAT: {(now_s - asof_s) / 3600:.1f} jam sesudah penutupan (batas komit {max_lag / 3600:.0f} jam)"))
                else:
                    sigs, probs = rebuild_signals(spec, tk, views)
                    if probs:
                        out.append(Action("alarm", bot, date, "tick tidak bisa direproduksi dari bar: " + "; ".join(probs)[:200]))
                    elif seed is None:
                        out.append(Action("commit", bot, date, f"perlu komit: {len(sigs)} sinyal (akar dihitung saat --send)", tk, cid))
                    else:
                        b = batch_for(spec, tk, sigs, seed)
                        out.append(Action("commit", bot, date, f"{len(sigs)} sinyal, akar {chain.hex0x(b.root)[:18]}…", tk, cid, b, b.entries))
                continue
            n, rev = int(c["n"]), int(c["revealed"])
            if rev >= n:
                out.append(Action("ok", bot, date, f"dikomit, {rev}/{n} terungkap"))
                continue
            if now_s < int(c["committedAt"]) + reveal_delay_s:
                out.append(Action("skip", bot, date, f"ungkap menunggu jeda ({rev}/{n})"))
                continue
            if seed is None:
                out.append(Action("reveal", bot, date, f"perlu ungkap {n - rev} sinyal (butuh kunci untuk salt)", tk, cid))
                continue
            sigs, probs = rebuild_signals(spec, tk, views)
            if probs:
                out.append(Action("alarm", bot, date, "dikomit tetapi tick tidak bisa direproduksi: " + "; ".join(probs)[:200]))
                continue
            b = batch_for(spec, tk, sigs, seed)
            if b.root != bytes(c["root"]) or len(b.entries) != n:
                out.append(Action("alarm", bot, date, f"akar on-chain {chain.hex0x(bytes(c['root']))[:18]}… BEDA dari ledger {chain.hex0x(b.root)[:18]}…"))
                continue
            todo = tuple(e for e in b.entries if not cv.is_revealed(cid, e.leaf))
            out.append(Action("reveal", bot, date, f"ungkap {len(todo)} dari {n} sinyal", tk, cid, b, todo))
    return out


# ---------------------------------------------------------------- kirim

def execute(actions: Sequence[Action], evm, anchor: str, pk: str, log: Callable[[str], None] = print, settle_s: float = 4.0) -> Dict[str, int]:
    """Kirim komit lalu ungkap untuk aksi yang punya batch. Revert ketahuan saat estimasi gas (tidak ada gas terbakar). Mengembalikan hitungan.
    `settle_s`: jeda sesudah komit masuk blok sebelum ungkap pertama - RPC publik ber-load-balancer bisa menjawab dari node yang belum melihat blok itu
    (estimasi ungkap lalu gagal UnknownCommit; tidak berbahaya, diulang putaran berikutnya, tetapi jeda kecil menghindarinya)."""
    from evm import RpcError, address_of, error_name, receipt_ok
    me = address_of(pk)
    stats = {"commit": 0, "reveal": 0, "gagal": 0}
    if evm.has_pending(me):
        log("committer masih punya transaksi tertunda: tidak mengirim apa pun putaran ini")
        return stats

    def send(data: bytes, what: str) -> bool:
        try:
            r = evm.send(pk, anchor, data)
        except RpcError as e:
            log(f"  {what}: DITOLAK sebelum kirim ({error_name(e.data, ERRORS) or e}); nol gas terbakar")
            stats["gagal"] += 1
            return False
        if not receipt_ok(r):
            log(f"  {what}: status 0 tx {r.get('transactionHash')}")
            stats["gagal"] += 1
            return False
        log(f"  {what}: tx {r.get('transactionHash')} blok {evm.num(r.get('blockNumber'))} gas {evm.num(r.get('gasUsed'))}")
        return True

    for a in actions:
        if a.batch is None or a.kind not in ("commit", "reveal"):
            continue
        spec = SPECS[a.bot]
        if a.kind == "commit":
            if not send(commit_calldata(spec, a.tick, a.batch), f"{a.bot} {a.asof_date} commit n={len(a.batch.entries)}"):
                continue
            stats["commit"] += 1
            if a.entries and settle_s:
                time.sleep(settle_s)
        for e in a.entries:
            if send(reveal_calldata(a.cid, e), f"{a.bot} {a.asof_date} reveal {e.signal.asset} {e.signal.aksi}"):
                stats["reveal"] += 1
    return stats


# ---------------------------------------------------------------- konfigurasi

def read_env_file(path: str, var: str) -> Optional[str]:
    """Nilai SATU variabel dari berkas KEY=VALUE (boleh `export`, boleh berkutip). Tidak pernah dicetak; nama lain tidak dibaca keluar."""
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as f:
        for ln in f:
            s = ln.strip()
            if s.startswith("export "):
                s = s[7:].lstrip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            if k.strip() == var:
                v = v.strip().strip('"').strip("'")
                return v if v.startswith("0x") else "0x" + v
    return None


def committer_key() -> Optional[str]:
    return os.environ.get(KEY_VAR) or read_env_file(COMMITTER_ENV, KEY_VAR)


def load_addresses(path: str = DEPLOYMENTS) -> Dict[str, Optional[str]]:
    """Alamat SignalAnchor/LockRegistry: env (SIGNAL_ANCHOR_ADDRESS / LOCK_REGISTRY_ADDRESS) dulu, lalu deployments/97.json ter-track."""
    d = {}
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    cs = d.get("contracts", {}) or {}
    return {"anchor": os.environ.get("SIGNAL_ANCHOR_ADDRESS") or cs.get("SignalAnchor"),
            "registry": os.environ.get("LOCK_REGISTRY_ADDRESS") or cs.get("LockRegistry"),
            "committer": os.environ.get("COMMITTER_ADDRESS") or (d.get("m3", {}) or {}).get("committer")}


def rpc_urls() -> List[str]:
    """RPC_URL (bila ada) didahulukan, lalu daftar publik. RPC_PIN=1 = HANYA RPC_URL (gladi di anvil: tidak pernah jatuh ke chain 97 sungguhan)."""
    from evm import DEFAULT_RPCS
    first = (os.environ.get("RPC_URL") or "").strip()
    if os.environ.get("RPC_PIN") == "1":
        if not first:
            raise SystemExit("RPC_PIN=1 tanpa RPC_URL")
        return [first]
    return ([first] if first else []) + [u for u in DEFAULT_RPCS if u != first]


def main() -> int:
    ap = argparse.ArgumentParser(description="Komit + ungkap sinyal ledger paper ke SignalAnchor (default = rencana).")
    ap.add_argument("--bots", default=",".join(BOTS_DEFAULT))
    ap.add_argument("--ledger", default=os.path.join(ROOT, "ledger", "paper"))
    ap.add_argument("--bars", default=os.path.join(ROOT, "ledger", "bars"))
    ap.add_argument("--deployments", default=DEPLOYMENTS)
    ap.add_argument("--committer", help="alamat committer untuk rencana tanpa kunci")
    ap.add_argument("--send", action="store_true", help="kirim transaksi (butuh COMMITTER_PRIVATE_KEY)")
    ap.add_argument("--now", help="ISO UTC pengganti jam sekarang (hanya untuk rencana)")
    ap.add_argument("--reveal-delay", type=int, default=int(os.environ.get("REVEAL_DELAY_S", "0")))
    a = ap.parse_args()
    if a.send and a.now:
        print("--now hanya untuk rencana; kontrak memakai jam blok")
        return 2
    import evm as evmmod
    from paper_tick import Views
    addrs = load_addresses(a.deployments)
    if not addrs["anchor"] or not addrs["registry"]:
        print("SignalAnchor/LockRegistry belum ada di deployments/97.json (dan tidak di env): deploy dulu (tools/m3_setup.py)")
        return 3
    pk = committer_key()
    if a.send and not pk:
        print(f"--send butuh {KEY_VAR} (env atau .committer.env)")
        return 2
    committer = evmmod.address_of(pk) if pk else (a.committer or addrs["committer"])
    if not committer:
        print("tidak ada committer: beri --committer 0x..., atau kunci di env/.committer.env")
        return 2
    ev = evmmod.Evm(rpc_urls(), CHAIN_ID)
    ev.chain_check()
    cv = AnchorView(ev, addrs["anchor"], addrs["registry"])
    now_s = ledger.iso_ms(a.now) // 1000 if a.now else int(time.time())
    bots = [b.strip() for b in a.bots.split(",") if b.strip()]
    print(f"SignalAnchor {addrs['anchor']} | LockRegistry {addrs['registry']} | committer {committer} | maxLag {cv.max_lag()} s | jam {ledger.utc_iso(now_s * 1000)}")
    acts = plan(bots, a.ledger, Views(a.bars), cv, committer, seed_from_key(pk) if pk else None, now_s, a.reveal_delay)
    for x in acts:
        print(x.line())
    if not a.send:
        print("\nRENCANA (default): tidak ada yang dikirim. --send untuk mengirim.")
        return 1 if any(x.kind == "alarm" for x in acts) else 0
    st = execute(acts, ev, addrs["anchor"], pk)
    print(f"\nterkirim: {st['commit']} komit, {st['reveal']} ungkap, {st['gagal']} gagal")
    return 1 if st["gagal"] or any(x.kind == "alarm" for x in acts) else 0


if __name__ == "__main__":
    raise SystemExit(main())
