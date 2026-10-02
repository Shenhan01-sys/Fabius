"""Antarmuka baris perintah mesin enam bot: specs | replay | emit | verify | gaps | gate | schema | intake | review | lock.

    python -X utf8 -m engine.cli specs
    python -X utf8 -m engine.cli replay --data <dir> --bot B1-TREND [--since 2020-12-01] [--csv out.csv]
    python -X utf8 -m engine.cli emit   --data <dir> --bot ALL [--asof 2026-08-31] > batch.jsonl   # baris `batch` (akar) + sinyal
    python -X utf8 -m engine.cli verify --file batch.jsonl [--root 0x...]                          # sisi pembeli
    python -X utf8 -m engine.cli gaps   --data <dir>
    python -X utf8 -m engine.cli gate   --data <dir> --bot ALL [--n-trials 20] [--strict]         # gerbang G + KPI K pada bot Fabius sendiri
    python -X utf8 -m engine.cli schema                                                           # skema formulir penerbit (JSON)
    python -X utf8 -m engine.cli intake --file sub.json [--data <dir>]                            # validasi (+ gerbang untuk kind=template)
    python -X utf8 -m engine.cli review --file sub.json --data <dir> [--json] [--signature 0x..]  # peninjau-bot penuh, laporan ber-sha
    python -X utf8 -m engine.cli lock   [--write --note "disetujui Hans <tanggal>" [--supersede]]  # kunci ambang (perlu kata builder)
    python -X utf8 -m engine.cli book                                                             # buku genesis: bot identitas Fabius (F-D73)
    python -X utf8 -m engine.cli ledger verify|report [--ledger ledger/paper] [--bars ledger/bars] [--bot B1-TREND]   # ledger paper maju (M2)

`--data` = folder CSV keluaran `fetch.py` (vault/09-Inbox/Session-2026-10-02-skrip/). Tidak ada perintah di sini yang
menyentuh jaringan, kunci, atau chain (pengunduh bar ada di tools/feed_bars.py). STATUS: USULAN (angka replay = dalam-sampel;
ledger paper = maju tetapi paper).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import glob
import json
import os
import secrets
import sys
import time
from typing import List

from . import book as bookmod, chain, ledger as ledgermod, locks, review as reviewmod, submission
from .data import load_csv_dir
from .freshness import StaleBars, assert_fresh
from .gates import GateParams, format_results, run_gates, verdict
from .quality import gap_report, missing_days
from .replay import replay
from .report import date_ms, fmt, summary
from .series import DAY_MS
from .sinyal import Signal, build_batch, signals_at, verify_entry
from .slots import book_sha as slots_book_sha
from .spec import PERP_UNIVERSE, SPECS

DATA_SYMBOLS = list(PERP_UNIVERSE) + ["PAXGUSDT", "XAUUSDT"]
UTC = dt.timezone.utc
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _iso(t_ms: int) -> str:
    return dt.datetime.fromtimestamp(t_ms / 1000, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _bots(arg: str) -> List[str]:
    if arg.upper() == "ALL":
        return list(SPECS)
    if arg not in SPECS:
        raise SystemExit(f"bot tidak dikenal: {arg}. Pilihan: {', '.join(SPECS)} atau ALL")
    return [arg]


def cmd_specs(a) -> int:
    for b, sp in SPECS.items():
        print(f"{b:16} {sp.param_nama}={sp.param!s:<6} tier {sp.tier:10} sha {sp.sha()}")
    print("\nsha = sidik jari spesifikasi hari ini, BUKAN kunci (belum ada yang dikunci; Epik Enam Bot masih USULAN).")
    return 0


def cmd_replay(a) -> int:
    md = load_csv_dir(a.data, DATA_SYMBOLS)
    since = date_ms(a.since) if a.since else None
    rc = 0
    for b in _bots(a.bot):
        sp = SPECS[b]
        try:
            pnl = replay(sp, md)
        except NotImplementedError as e:
            print(f"{b:16} dilewati: {e}")
            continue
        print(f"{b:16} {fmt(summary(pnl, since))}")
        if a.csv and a.bot != "ALL":
            with open(a.csv, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["t", "date", "pnl"])
                for t, v in pnl:
                    if since is None or t >= since:
                        w.writerow([t, _iso(t)[:10], f"{v:.10f}"])
    print("\nDalam-sampel, biaya = penggaris spec, tanpa slippage; BUKAN hasil maju dan BUKAN klaim edge.")
    return rc


def cmd_gaps(a) -> int:
    md = load_csv_dir(a.data, DATA_SYMBOLS)
    rep = gap_report(md)
    if not rep:
        print("tidak ada bolong bar harian")
        return 0
    for k, gs in rep.items():
        for g in gs:
            print(f"{k:18} bolong {missing_days(g)} hari: bar {_iso(g[0])[:10]} -> {_iso(g[1])[:10]}")
    return 0


def cmd_emit(a) -> int:
    md = load_csv_dir(a.data, DATA_SYMBOLS)
    if a.asof:
        t_asof = date_ms(a.asof)
        now_ms = t_asof + DAY_MS + 60_000          # simulasi: semenit setelah penutupan bar itu
        live = False
    else:
        now_ms = int(dt.datetime.fromisoformat(a.now.replace("Z", "+00:00")).timestamp() * 1000) if a.now else int(time.time() * 1000)
        t_asof = ((now_ms - DAY_MS) // DAY_MS) * DAY_MS          # bar terakhir yang SUDAH tertutup
        live = True
    rc = 0
    for b in _bots(a.bot):
        sp = SPECS[b]
        if b == "B4-LISTING-FADE":
            print(f"# {b}: dilewati - event listing datang dari pengunduh (M2)", file=sys.stderr)
            continue
        try:
            if live:
                ref = md.spot.get("BTCUSDT") if b == "B5-CORE-RWA" else md.perp.get("BTCUSDT")
                if ref is None:
                    raise StaleBars(f"{b}: seri acuan BTCUSDT tidak ada")
                assert_fresh(f"{b} acuan BTCUSDT", ref.upto(t_asof), now_ms)
            sigs = signals_at(sp, md, t_asof)
        except StaleBars as e:
            print(f"# {b}: DITOLAK (data basi/terpotong): {e}", file=sys.stderr)
            rc = 2
            continue
        print(f"# {b}: sah pada penutupan bar {_iso(t_asof)[:10]} ({_iso(t_asof + DAY_MS)}), {len(sigs)} sinyal", file=sys.stderr)
        if a.seed:                              # hanya untuk uji: salt deterministik per sinyal
            seed = chain.from_hex(a.seed)
            salts = [chain.keccak256(seed + i.to_bytes(4, "big")) for i in range(len(sigs))]
        else:
            salts = [secrets.token_bytes(32) for _ in sigs]
        batch = build_batch(b, sp.sha(), t_asof, sigs, salts)
        print(json.dumps({"batch": {"bot_id": b, "spec_sha": sp.sha(), "asof": batch.asof(), "n": len(sigs),
                                    "root": chain.hex0x(batch.root)}}, sort_keys=True, ensure_ascii=False))
        for e in batch.entries:
            print(json.dumps({"id": e.signal.id(), "leaf": chain.hex0x(e.leaf), "salt": chain.hex0x(e.salt),
                              "proof": [chain.hex0x(p) for p in e.proof], "abi": chain.hex0x(e.signal.abi()),
                              "sinyal": e.signal.as_dict()}, sort_keys=True, ensure_ascii=False))
    return rc


def cmd_verify(a) -> int:
    """Sisi pembeli: baca baris JSON hasil `emit` (stdin atau --file) dan periksa tiap sinyal terhadap akar yang dikomit.
    Akar diambil dari baris `batch` yang mendahului, atau dari --root (mis. dibaca dari chain)."""
    src = open(a.file, encoding="utf-8") if a.file else sys.stdin
    root, bad, n = a.root, 0, 0
    for line in src:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            row = json.loads(line)
            if "batch" in row:
                root = a.root or row["batch"]["root"]
                continue
            n += 1
            if root is None:
                print("TOLAK: tidak ada akar (baris batch atau --root)")
                return 2
            ok, why = verify_entry(row["sinyal"], row["salt"], row["proof"], root)
            if ok and Signal.from_dict(row["sinyal"]).id() != row["id"]:
                ok, why = False, "BEDA: id tidak cocok dengan muatan"
            label = f"{row['sinyal']['bot_id']:16} {row['sinyal']['asset']:10} {row['sinyal']['aksi']:12}"
        except (ValueError, KeyError, TypeError, ArithmeticError) as e:    # baris bukan JSON / muatan rusak = GAGAL, bukan traceback
            n += 1
            ok, why, label = False, f"baris tidak terbaca: {type(e).__name__}", "?"
        bad += 0 if ok else 1
        print(f"{'OK  ' if ok else 'GAGAL'} {label} {why}")
    if src is not sys.stdin:
        src.close()
    print(f"{n - bad}/{n} cocok dengan akar")
    return 1 if bad or n == 0 else 0


def _incumbent_pnls(md) -> dict:
    """PnL semua bot Fabius yang bisa di-replay (dipakai `gate` untuk dogfood: petahana = bot lain)."""
    out = {}
    for b, sp in SPECS.items():
        try:
            out[b] = replay(sp, md)
        except NotImplementedError:
            pass
    return out


def _book_pnls(md) -> dict:
    """PnL petahana = BUKU SLOT SEKARANG (buku genesis: hanya bot identitas) - bukan enam bot Fabius. Entri penerbit luar kelak datang dari ledger
    shadow, bukan dari replay (orkestrator buku hidup: P87)."""
    out = {}
    for b, sp in bookmod.fabius_specs(bookmod.genesis_book(0)).items():
        try:
            out[b] = replay(sp, md)
        except NotImplementedError:
            pass
    return out


def _incumbents(md, mode: str) -> dict:
    return _book_pnls(md) if mode == "book" else _incumbent_pnls(md)


def cmd_book(a) -> int:
    book = bookmod.genesis_book(0)
    print(f"buku genesis (F-D73): {len(book)} entri; book_sha {slots_book_sha(book)}")
    for e in book:
        sp = SPECS[e.bot_id]
        print(f"  {e.bot_id:12} issuer {e.issuer} identitas={e.identity} instrumen-kripto-saja={bookmod.trades_crypto_only(sp)} "
              f"spec_sha {e.spec_sha[:18]}... fingerprint {e.fingerprint[:18]}...")
    print("bot Fabius lain (B2, B3, B5, B6) masuk lewat jalur yang sama dengan penerbit luar: gerbang -> shadow -> slot.")
    return 0


def cmd_gate(a) -> int:
    """Gerbang + KPI pada bot Fabius sendiri (dogfood); petahana untuk G10 = bot lain yang bisa di-replay. N percobaan bawaan 20:
    enam bot ini dipilih dari ±20 kandidat (Epik 05), jadi ambang Sharpe G3 dideflasi untuk N = 20."""
    md = load_csv_dir(a.data, DATA_SYMBOLS)
    params = GateParams(placebo_n=a.placebo_n, boot_n=a.boot_n, n_trials=a.n_trials)
    pnls = _incumbent_pnls(md)
    rc = 0
    for b in _bots(a.bot):
        sp = SPECS[b]
        res = run_gates(sp, md, {k: v for k, v in pnls.items() if k != b}, params)
        print(format_results(f"{b} ({sp.param_nama}={sp.param})", res))
        print()
        if a.strict and verdict(res)[0] != "LOLOS_SHADOW":
            rc = 1
    state = locks.status()["state"]
    note = "ambang v1 terkunci sementara, bukan teroptimasi" if state == "TERKUNCI" else "ambang = USULAN sampai dikunci"
    print(f"KUNCI PARAMETER: {state} ({note}). Lolos = boleh SHADOW maju; BUKAN slot, BUKAN uang nyata. "
          f"Angka dalam-sampel; N percobaan = {a.n_trials}.")
    return rc


def cmd_review(a) -> int:
    """Peninjau-bot penuh untuk satu pengajuan: validasi -> identitas (bila ada tanda tangan) -> gerbang -> KPI -> laporan ber-sha."""
    with open(a.file, encoding="utf-8") as f:
        sub = json.load(f)
    md = load_csv_dir(a.data, DATA_SYMBOLS)
    ident = None
    if a.signature:
        ident = {"signature": a.signature, "chain_id": a.chain_id, "nonce": a.nonce, "deadline": a.deadline,
                 "now_s": a.now if a.now is not None else int(time.time()), "payout_signature": a.payout_signature}
    gp = GateParams(placebo_n=a.placebo_n, boot_n=a.boot_n)
    rep = reviewmod.review(sub, md, _incumbents(md, a.incumbents), gate_params=gp, identity=ident, prior_family_submissions=a.prior_submissions)
    print(json.dumps(rep, indent=2, ensure_ascii=False, sort_keys=True) if a.json else reviewmod.render(rep))
    return 0 if rep["vonis"] == "LOLOS_SHADOW" else 1


def cmd_lock(a) -> int:
    st = locks.status()
    if a.write:
        try:
            lock = locks.write_lock(a.note or "", supersede=a.supersede)
        except (ValueError, FileExistsError) as e:
            print(f"GAGAL: {e}")
            return 1
        print(f"dikunci: {lock['sha']} pada {lock['dikunci']} ({lock['catatan']})")
        return 0
    p = locks.current_params()
    print(f"KUNCI: {st['state']}  sha kini {st['sha_kini']}  sha kunci {st['sha_kunci']}  berkas {st['berkas']}")
    if a.json:
        print(json.dumps(p, indent=2, sort_keys=True))
    else:
        g, k, s, e = p["gerbang"], p["kpi"], p["slot"], p["ekonomi"]
        print(f"gerbang: Sharpe >= {g['min_net_sharpe']} (+deflasi N percobaan), bootstrap p{int(g['boot_q'] * 100)} > 0, placebo p <= {g['placebo_max_p']} ({g['placebo_n']} acak), "
              f"plateau {g['plateau_factors']}, biaya {g['cost_mult']}x, dSharpe EW >= {g['marginal_min_dsharpe']}, korelasi <= {g['marginal_max_corr']}, seed {g['seed']}")
        print(f"KPI: tahunan net >= {(k['hurdle_ann'] + k['margin_ann']) * 100:.0f}% (hurdle {k['hurdle_ann'] * 100:.0f}% + margin {k['margin_ann'] * 100:.0f}%), "
              f"Calmar >= {k['min_calmar']}, sinyal >= {k['min_signals_year']:g}/tahun dan >= {k['min_signals_total']} total, basis bagi hasil: {k['fee_base']}")
        print(f"slot: shadow {s['shadow_days']} hari, masa tenggang {s['grace_days']} hari, jendela skor {s['score_window']} hari, margin {s['margin_bps']:g} bps + t >= {s['min_gap_tstat']:g}, "
              f"{s['max_replace_per_epoch']} penggantian per epoch ({s['epoch_days']} hari)")
        print(f"ekonomi: penerbit {e['issuer_bps'] / 100:.0f}% / Fabius {e['fabius_bps'] / 100:.0f}% dari pendapatan penjualan sinyal")
    return 0


def cmd_schema(a) -> int:
    print(json.dumps(submission.schema_json(), indent=2, ensure_ascii=False))
    return 0


def cmd_intake(a) -> int:
    with open(a.file, encoding="utf-8") as f:
        sub = json.load(f)
    problems = submission.validate(sub)
    if problems:
        for p in problems:
            print("TOLAK:", p)
        return 1
    print(f"formulir sah. submission_sha {submission.submission_sha(sub)}  spec_sha {submission.spec_sha_of(sub)}")
    if not a.data:
        print("TIDAK ADA GERBANG YANG DIJALANKAN: tambah --data <dir> (formulir sah belum berarti lolos apa pun).")
        return 2
    md = load_csv_dir(a.data, DATA_SYMBOLS)
    spec = submission.to_botspec(sub)
    res = run_gates(spec, md, _incumbents(md, a.incumbents), GateParams(placebo_n=a.placebo_n, boot_n=a.boot_n),
                    claims=sub["evidence"].get("klaim"))
    print(format_results(f"{spec.bot_id} (template {spec.template}, {spec.param_nama}={spec.param})", res))
    return 0 if verdict(res)[0] == "LOLOS_SHADOW" else 1


def cmd_ledger(a) -> int:
    """`ledger verify`: periksa rantai hash DAN hitung ulang setiap tick/settle dari deret bar (nol jaringan, nol kunci). `ledger report`: ringkasan."""
    files = sorted(glob.glob(os.path.join(a.ledger, "*.jsonl")))
    if a.bot:
        files = [f for f in files if os.path.basename(f) == f"{a.bot}.jsonl"]
    if not files:
        print(f"tidak ada ledger di {a.ledger}" + (f" untuk {a.bot}" if a.bot else ""))
        return 2
    md = load_csv_dir(a.bars, DATA_SYMBOLS) if a.action == "verify" else None
    rc = 0
    for path in files:
        name = os.path.basename(path)
        try:
            recs = ledgermod.load(path)
        except ledgermod.LedgerError as e:
            print(f"{name}: RUSAK: {e}")
            rc = 1
            continue
        if a.action == "report":
            print(ledgermod.render_report(recs))
            print()
            continue
        problems = ledgermod.verify_chain(recs)
        spec = SPECS.get(recs[0].get("bot_id")) if recs else None
        if spec is None:
            problems.append("bot_id genesis tidak dikenal oleh kode")
        elif not any(x.startswith(("catatan pertama", "ledger kosong")) for x in problems):
            problems += ledgermod.verify_against_data(spec, recs, md)
        st = ledgermod.stats(recs) if recs else {"n_tick": 0, "n_settle": 0, "n_gap": 0, "head": "-"}
        print(f"{name}: {'SAH' if not problems else 'GAGAL'}  tick {st['n_tick']} settle {st['n_settle']} gap {st['n_gap']}  "
              f"ujung {str(st['head'])[:14]}…  (rantai + hitung-ulang dari {a.bars})")
        for pr in problems[:30]:
            print("  -", pr)
        rc = rc or (1 if problems else 0)
    return rc


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="engine.cli", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("specs")
    r = sub.add_parser("replay")
    r.add_argument("--data", required=True)
    r.add_argument("--bot", required=True)
    r.add_argument("--since")
    r.add_argument("--csv")
    e = sub.add_parser("emit")
    e.add_argument("--data", required=True)
    e.add_argument("--bot", required=True)
    e.add_argument("--asof", help="YYYY-MM-DD = bar yang baru tertutup; tanpa ini = bar tertutup terakhir menurut jam sekarang")
    e.add_argument("--now", help="ISO UTC, mengganti jam sekarang (uji guard basi)")
    e.add_argument("--seed", help="benih hex 32 byte (hanya untuk uji): salt per sinyal diturunkan darinya; bawaan: acak per sinyal")
    v = sub.add_parser("verify")
    v.add_argument("--file", help="berkas baris JSON hasil `emit`; bawaan: stdin")
    v.add_argument("--root", help="akar komit 0x... (mis. dibaca dari chain); bawaan: baris `batch`")
    g = sub.add_parser("gaps")
    g.add_argument("--data", required=True)
    gt = sub.add_parser("gate")
    gt.add_argument("--data", required=True)
    gt.add_argument("--bot", default="ALL")
    gt.add_argument("--placebo-n", type=int, default=200)
    gt.add_argument("--boot-n", type=int, default=1000)
    gt.add_argument("--n-trials", type=int, default=20, help="jumlah percobaan untuk deflasi ambang Sharpe G3 (enam bot Fabius: ±20 kandidat)")
    gt.add_argument("--strict", action="store_true", help="kode keluar 1 bila ada bot yang tidak LOLOS_SHADOW")
    sub.add_parser("schema")
    it = sub.add_parser("intake")
    it.add_argument("--file", required=True)
    it.add_argument("--data")
    it.add_argument("--placebo-n", type=int, default=200)
    it.add_argument("--boot-n", type=int, default=1000)
    it.add_argument("--incumbents", choices=("book", "six"), default="book", help="petahana G10: buku slot sekarang (bawaan) atau enam bot Fabius")
    sub.add_parser("book")
    rv = sub.add_parser("review")
    rv.add_argument("--file", required=True)
    rv.add_argument("--data", required=True)
    rv.add_argument("--json", action="store_true")
    rv.add_argument("--signature", help="tanda tangan EIP-712 penerbit (0x...); tanpa ini laporan INDIKATIF (identitas belum terverifikasi)")
    rv.add_argument("--payout-signature", help="tanda tangan dompet payout bila berbeda dari penerbit")
    rv.add_argument("--chain-id", type=int, default=97)
    rv.add_argument("--nonce", type=int, default=0)
    rv.add_argument("--deadline", type=int, default=0)
    rv.add_argument("--now", type=int, help="detik Unix (bawaan: jam sekarang)")
    rv.add_argument("--prior-submissions", type=int, default=0, help="pengajuan sebelumnya oleh keluarga yang sama (dari registri)")
    rv.add_argument("--placebo-n", type=int, default=200)
    rv.add_argument("--boot-n", type=int, default=1000)
    rv.add_argument("--incumbents", choices=("book", "six"), default="book", help="petahana G10: buku slot sekarang (bawaan) atau enam bot Fabius")
    lg = sub.add_parser("ledger")
    lg.add_argument("action", choices=("verify", "report"))
    lg.add_argument("--ledger", default=os.path.join(REPO_ROOT, "ledger", "paper"), help="folder berkas <bot>.jsonl (bawaan: ledger/paper)")
    lg.add_argument("--bars", default=os.path.join(REPO_ROOT, "ledger", "bars"), help="folder CSV bar yang dipakai tick (bawaan: ledger/bars)")
    lg.add_argument("--bot")
    lk = sub.add_parser("lock")
    lk.add_argument("--write", action="store_true", help="tulis kunci dari parameter kode sekarang (perlu kata builder)")
    lk.add_argument("--note", help="catatan wajib saat --write: siapa menyetujui, kapan")
    lk.add_argument("--supersede", action="store_true", help="timpa kunci lama (kunci lama dipindah ke locks/history)")
    lk.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    return {"specs": cmd_specs, "replay": cmd_replay, "emit": cmd_emit, "verify": cmd_verify, "gaps": cmd_gaps,
            "gate": cmd_gate, "schema": cmd_schema, "intake": cmd_intake, "review": cmd_review, "lock": cmd_lock, "book": cmd_book,
            "ledger": cmd_ledger}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
