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
    python -X utf8 -m engine.cli review ... [--catat]                                             # P83: k keluarga dari registri; --catat = resmi (alpha A1/k)
    python -X utf8 -m engine.cli lock   [--write --note "disetujui Hans <tanggal>" [--supersede]]  # kunci ambang (perlu kata builder)
    python -X utf8 -m engine.cli book                                                             # buku genesis: bot identitas Fabius (F-D73)
    python -X utf8 -m engine.cli book epoch [--write] [--no-gates] [--now ISO]                    # buku HIDUP (P87, F-D85): satu catatan per epoch
    python -X utf8 -m engine.cli book verify                                                      # rantai + hitung ulang keputusan tiap epoch
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


BOOK_FILE = os.path.join(REPO_ROOT, "ledger", "book", "buku.jsonl")


def _verified_ledgers(ledger_dir: str, view) -> dict:
    """Ledger maju yang SAH saja (rantai + hitung ulang dari bar); yang lain dicetak dan tidak dipakai. P161 B1c: bot penerbit LOLOS_SHADOW ikut."""
    from . import terdaftar
    specs = terdaftar.semua()
    ok = {}
    for path in sorted(glob.glob(os.path.join(ledger_dir, "*.jsonl"))):
        try:
            recs = ledgermod.load(path)
        except ledgermod.LedgerError as e:
            print(f"  {os.path.basename(path)}: RUSAK ({e}) - tidak dipakai")
            continue
        spec = specs.get(recs[0].get("bot_id")) if recs else None
        probs = ledgermod.verify_chain(recs)
        if spec is not None and not probs:
            probs = ledgermod.verify_against_data(spec, recs, view("targets" if spec.method == "B3-CARRY" else "actual"), view("actual"))
        if spec is None or probs:
            print(f"  {os.path.basename(path)}: ledger TIDAK SAH - tidak dipakai ({(probs or ['bot tidak dikenal'])[0]})")
            continue
        ok[spec.bot_id] = recs
    return ok


def _book_killers(book, ok: dict, view, end_ms: int) -> dict:
    """Status pembunuh penghuni untuk catatan epoch (P107). Bot Fabius: terjemahan terstruktur (`engine/pembunuh.py`) HANYA bila kuncinya TERKUNCI
    dan ledgernya sah -> YA / BELUM / TIDAK; selain itu "TEKS" (kalimat spesifikasi, dinilai manusia). Penerbit luar belum ada -> "TIDAK"."""
    from . import pembunuh, terdaftar
    from .slots import killer_triggered
    locked = pembunuh.status()["state"] == "TERKUNCI"
    luar = terdaftar.rincian()[0]
    out = {}
    for e in book:
        if e.bot_id in luar:                                   # P161 B1d: pembunuh terstruktur kiriman penerbit, ditegakkan kode
            if e.bot_id not in ok:
                out[e.bot_id] = "TEKS"
                continue
            k = luar[e.bot_id]["pembunuh"]
            pnl, n = terdaftar.pnl_sejak_sinyal(ok[e.bot_id], int(k["window_sinyal"]))
            out[e.bot_id] = "YA" if killer_triggered(k, pnl, n) else ("BELUM" if n < int(k["window_sinyal"]) else "TIDAK")
        elif e.bot_id not in SPECS:
            out[e.bot_id] = "TIDAK"
        elif locked and e.bot_id in pembunuh.USULAN and e.bot_id in ok:
            out[e.bot_id] = pembunuh.evaluate(e.bot_id, ok[e.bot_id], view("actual"), end_ms)["vonis"]
        else:
            out[e.bot_id] = "TEKS"
    return out


def _book_epoch(a) -> int:
    """Satu epoch buku hidup: skor maju penghuni (P85) -> penantang (bot SHADOW_ELIGIBLE di luar buku; gerbang dijalankan terhadap BUKU SEKARANG) ->
    status pembunuh -> slots.decide_epoch -> catatan. Idempoten per epoch: epoch yang sudah tercatat tidak ditulis dua kali."""
    import dataclasses
    from . import book_live, forward
    from .sinyal import data_fingerprint
    from .slots import FABIUS, Challenger, SlotParams, epoch_id
    from .spec import sha0x
    p = SlotParams()
    now_s = ledgermod.iso_ms(a.now) // 1000 if a.now else int(time.time())
    records = ledgermod.load(a.file)
    if records:
        probs = book_live.verify_book(records, p)
        if probs:
            print("buku hidup TIDAK SAH - tidak menulis apa pun:\n  - " + "\n  - ".join(probs[:10]))
            return 1
        if records[-1].get("type") == "epoch" and records[-1]["epoch"] == epoch_id(now_s, p):
            print(f"epoch {records[-1]['epoch']} sudah tercatat; tidak menulis dua kali.")
            print(book_live.fmt_epoch(records[-1]))
            return 0
        book = book_live.current_book(records)
    else:
        book = bookmod.genesis_book(now_s)
        gen = book_live.make_genesis(book, locks.status()["sha_kunci"], now_s, "buku hidup (P87, F-D85): genesis = bot identitas B1-TREND (F-D73)")
        records = [book_live.append(a.file, gen, [])] if a.write else [ledgermod.seal(gen, ledgermod.ZERO)]
        print(f"genesis buku hidup {'DITULIS' if a.write else '(rencana)'}: book_sha {gen['book_sha'][:18]}…")
    views: dict = {}

    def view(name):
        if name not in views:
            views[name] = load_csv_dir(a.bars, DATA_SYMBOLS, funding_view=name)
        return views[name]

    ok = _verified_ledgers(a.ledger, view)
    end = forward.common_end(ok, ledgermod.last_closed_bar(now_s * 1000))
    scores = {e.bot_id: (forward.stats_for(e.bot_id, ok[e.bot_id], end, p).score_bps if e.bot_id in ok else None) for e in book}
    killers = _book_killers(book, ok, view, end)
    bsha = slots_book_sha(book)
    in_book = {e.bot_id for e in book}
    challengers = []
    from . import terdaftar
    luar = terdaftar.rincian()[0]                              # P161 B1d: penantang penerbit dari registri (LOLOS_SHADOW + ledger maju sah)
    for bot in list(bookmod.SHADOW_ELIGIBLE) + sorted(luar):
        if bot in in_book or bot not in ok:
            continue
        spec = luar[bot]["spec"] if bot in luar else SPECS[bot]
        if a.no_gates:
            v, rsha = "TIDAK_DIJALANKAN", "0x" + "00" * 32
        else:
            md = view("actual")
            inc = {b: replay(sp, md) for b, sp in bookmod.fabius_specs(book).items()}
            t0 = time.time()
            res = run_gates(spec, md, inc, GateParams())
            v, fails, nas = verdict(res)
            rep = {"v": 1, "bot_id": bot, "spec_sha": spec.sha(), "fingerprint": spec.fingerprint(), "data_hash": data_fingerprint(spec, md), "vonis": v,
                   "gagal": fails, "tak_terukur": nas, "kunci_v1": locks.status()["sha_kunci"], "book_sha": bsha, "petahana": sorted(inc),
                   "gerbang": [dataclasses.asdict(r) for r in res]}
            rsha = sha0x(rep)
            rep["report_sha"] = rsha
            print(f"  gerbang {bot} terhadap buku {bsha[:12]}…: {v} (gagal {fails or '-'}, tak terukur {nas or '-'}) dalam {time.time() - t0:.0f} s")
            if a.write:
                rp = os.path.join(os.path.dirname(a.file), "laporan", f"{rsha[2:14]}.json")
                os.makedirs(os.path.dirname(rp), exist_ok=True)
                with open(rp, "w", encoding="utf-8", newline="\n") as f:
                    json.dump(rep, f, indent=1, sort_keys=True, ensure_ascii=False)
                    f.write("\n")
        challengers.append(Challenger(bot_id=bot, issuer=luar[bot]["issuer"] if bot in luar else FABIUS, spec_sha=spec.sha(),
                                      fingerprint=spec.fingerprint(), gate_verdict=v, report_sha=rsha, book_sha=bsha,
                                      payout=luar[bot]["payout"] if bot in luar else "",
                                      **forward.challenger_fields(bot, ok, [e.bot_id for e in book], end, p)))
    rec = book_live.build_epoch(book, now_s, end, scores, challengers, killers, p)
    print(book_live.fmt_epoch(rec))
    if not a.write:
        print("RENCANA: tidak ada yang ditulis. --write untuk menambah catatan epoch (penulis tunggal buku).")
        return 0
    sealed = book_live.append(a.file, rec, records)
    print(f"ditulis: {os.path.relpath(a.file, REPO_ROOT)} epoch {sealed['epoch']} ujung {sealed['h'][:14]}… | pin book_sha: python -X utf8 tools/pin_book.py --send")
    return 0


def cmd_book(a) -> int:
    from . import book_live
    if getattr(a, "action", "status") == "epoch":
        return _book_epoch(a)
    if getattr(a, "action", "status") == "verify":
        recs = ledgermod.load(a.file)
        probs = book_live.verify_book(recs)
        print(f"{os.path.relpath(a.file, REPO_ROOT)}: {'SAH' if not probs else 'GAGAL'}  catatan {len(recs)}  ujung {ledgermod.head(recs)[:14]}…"
              + (f"  book_sha {recs[-1]['book_sha'][:18]}…" if recs else ""))
        for pr in probs[:20]:
            print("  -", pr)
        return 1 if probs else 0
    if os.path.exists(getattr(a, "file", BOOK_FILE)):
        recs = ledgermod.load(a.file)
        print(f"buku HIDUP {os.path.relpath(a.file, REPO_ROOT)}: {len(recs)} catatan, {'SAH' if not book_live.verify_book(recs) else 'TIDAK SAH'}")
        if recs and recs[-1].get("type") == "epoch":
            print(book_live.fmt_epoch(recs[-1]))
        print()
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
    if a.prior_submissions is not None:
        # jalur MANUAL (lama): k diketik operator -> laporan selalu indikatif (sumber 'manual')
        rep = reviewmod.review(sub, md, _incumbents(md, a.incumbents), gate_params=gp, identity=ident, prior_family_submissions=a.prior_submissions)
        rc, msgs = (0 if rep["vonis"] == "LOLOS_SHADOW" else 1), ["k dari --prior-submissions (manual): laporan tidak mengikat"]
    else:
        # P83: k dari registri pengajuan; registri tak terbaca/rusak = keluar 3 (TOLAK), k tidak ditebak
        now = a.now if a.now is not None else int(time.time())
        rc, rep, msgs = reviewmod.tinjau_tercatat(sub, md, _incumbents(md, a.incumbents), path=a.registri, now_s=now, catat=a.catat,
                                                  identity=ident, gate_params=gp)
    for m in msgs:
        print(m, file=sys.stderr if a.json else sys.stdout)
    if rep is not None:
        print(json.dumps(rep, indent=2, ensure_ascii=False, sort_keys=True) if a.json else reviewmod.render(rep))
    return rc


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
    what = f"rule, sha aturan {spec.param[:18]}…" if spec.template == "RULE" else f"template {spec.template}, {spec.param_nama}={spec.param}"
    print(format_results(f"{spec.bot_id} ({what})", res))
    return 0 if verdict(res)[0] == "LOLOS_SHADOW" else 1


def _ledger_fd16(files, view) -> int:
    """`ledger fd16` (P88): F-D16 pada data maju - hanya ledger yang SAH (rantai + hitung ulang dari bar) yang dinilai; BH lintas bot yang dinilai bersama."""
    from . import fd16
    p = fd16.Fd16Params()
    ok: dict = {}
    for path in files:
        name = os.path.basename(path)
        try:
            recs = ledgermod.load(path)
        except ledgermod.LedgerError as e:
            print(f"{name}: RUSAK ({e}) - tidak dinilai")
            continue
        spec = SPECS.get(recs[0].get("bot_id")) if recs else None
        probs = ledgermod.verify_chain(recs)
        if spec is not None and not probs:
            probs = ledgermod.verify_against_data(spec, recs, view("targets" if spec.method == "B3-CARRY" else "actual"), view("actual"))
        if spec is None or probs:
            print(f"{name}: ledger TIDAK SAH - tidak dinilai ({(probs or ['bot tidak dikenal'])[0]})")
            continue
        ok[spec.bot_id] = recs
    st = fd16.status(p)
    label = {"TERKUNCI": f"parameter TERKUNCI sha {str(st['sha_kunci'])[:18]}… (dikunci {st['dikunci']}, F-D84)",
             "BELUM_DIKUNCI": "parameter USULAN (belum dikunci)",
             "MENYIMPANG": f"PERINGATAN: parameter kode MENYIMPANG dari kunci {str(st['sha_kunci'])[:18]}… - vonis di bawah TIDAK mengikat",
             "RUSAK": "PERINGATAN: berkas kunci F-D16 RUSAK - vonis di bawah TIDAK mengikat"}[st["state"]]
    print(f"F-D16 MAJU ({label}): sinyal >= {p.n_sinyal_min}, hari >= {p.hari_min}, bulan >= {p.bulan_min}, "
          f"CI {int(p.ci_level * 100)} % bootstrap blok {p.blok_hari} hari x {p.boot_n}, buang bulan terbaik, BH alpha {p.alpha_bh} lintas {len(ok)} bot")
    res = fd16.check(ok, p)
    for r in res:
        print(fd16.fmt(r, p))
    print("Paper maju; LOLOS di sini BUKAN izin uang nyata (masih butuh telaah hukum P75/P80) dan BUKAN klaim edge.")
    return 0


def _ledger_pembunuh(a, view) -> int:
    """`ledger pembunuh` (P107): terjemahan terstruktur kalimat pembunuh B1/B3 dinilai pada ledger maju yang SAH. `--kunci "catatan"` menulis kuncinya
    (hanya atas kata builder; menolak menimpa)."""
    import time
    from . import forward, pembunuh
    if a.kunci:
        try:
            lock = pembunuh.write_lock(a.kunci)
        except (ValueError, FileExistsError) as e:
            print(f"TIDAK dikunci: {e}")
            return 1
        print(f"DIKUNCI {lock['dikunci']}: sha {lock['sha']} -> engine/locks/pembunuh.lock.json | pin: python -X utf8 tools/lock_spec.py "
              f"--file engine/locks/pembunuh.lock.json --name FABIUS-PEMBUNUH-v1 --send")
    st = pembunuh.status()
    label = {"TERKUNCI": f"TERKUNCI sha {str(st['sha_kunci'])[:18]}… (dikunci {st['dikunci']})",
             "BELUM_DIKUNCI": f"USULAN, belum dikunci (sha {st['sha_kini'][:18]}…); buku slot tetap mencatat TEKS",
             "MENYIMPANG": f"PERINGATAN: terjemahan/spesifikasi di kode MENYIMPANG dari kunci {str(st['sha_kunci'])[:18]}… - TIDAK mengikat",
             "RUSAK": "PERINGATAN: berkas kunci pembunuh RUSAK - TIDAK mengikat"}[st["state"]]
    ok = _verified_ledgers(a.ledger, view)
    end = forward.common_end(ok, ledgermod.last_closed_bar(int(time.time() * 1000)))
    print(f"PEMBUNUH TERSTRUKTUR ({label}); ujung jendela {ledgermod.date_of(end)}")
    for bot, syarat in sorted(pembunuh.USULAN.items()):
        print(f"{bot}: \"{SPECS[bot].pembunuh}\"")
        for k in syarat:
            print(f"  {k['id']} {k['aturan']}")
        if bot not in ok:
            print("  ledger tidak ada atau TIDAK SAH - tidak dinilai")
            continue
        print(pembunuh.fmt(pembunuh.evaluate(bot, ok[bot], view("actual"), end)))
    print("Paper maju. Pembunuh yang terpicu mengeluarkan bot dari buku pada epoch berikutnya (kecuali bot identitas terakhir), hanya bila kuncinya TERKUNCI.")
    return 0


def _ledger_skor(files, view) -> int:
    """`ledger skor` (P85): skor maju per bot + statistik berpasangan pada satu ujung jendela bersama - bahan `slots.decide`. Hanya ledger SAH."""
    import time
    from . import forward
    from .slots import SlotParams
    p = SlotParams()
    ok: dict = {}
    for path in files:
        name = os.path.basename(path)
        try:
            recs = ledgermod.load(path)
        except ledgermod.LedgerError as e:
            print(f"{name}: RUSAK ({e}) - tidak dinilai")
            continue
        spec = SPECS.get(recs[0].get("bot_id")) if recs else None
        probs = ledgermod.verify_chain(recs)
        if spec is not None and not probs:
            probs = ledgermod.verify_against_data(spec, recs, view("targets" if spec.method == "B3-CARRY" else "actual"), view("actual"))
        if spec is None or probs:
            print(f"{name}: ledger TIDAK SAH - tidak dinilai ({(probs or ['bot tidak dikenal'])[0]})")
            continue
        ok[spec.bot_id] = recs
    end = forward.common_end(ok, ledgermod.last_closed_bar(int(time.time() * 1000)))
    print(f"SKOR MAJU (SlotParams kunci v1: jendela {p.score_window} hari kalender, cakupan minimal {p.min_coverage:.0%}, shadow minimal {p.shadow_days} hari; "
          f"ujung bersama {ledgermod.date_of(end)}; hanya settle final)")
    for b in sorted(ok):
        print(forward.fmt(forward.stats_for(b, ok[b], end, p), p))
    pt = forward.paired_table(ok, end, p)
    for (x, y), v in sorted(pt.items()):
        print(f"  berpasangan {x} - {y}: " + ("tak terukur (cakupan hari yang sama kurang)" if v is None else f"{v[0]:+.1f} bps, t = {v[1]:.2f}"))
    print("Skor = paper maju; menentukan slot (hak rendah), BUKAN bukti edge dan BUKAN F-D16 (lihat `ledger fd16`).")
    return 0


def cmd_ledger(a) -> int:
    """`ledger verify`: periksa rantai hash DAN hitung ulang setiap tick/settle dari deret bar (nol jaringan, nol kunci). `ledger report`: ringkasan."""
    files = sorted(glob.glob(os.path.join(a.ledger, "*.jsonl")))
    if a.bot:
        files = [f for f in files if os.path.basename(f) == f"{a.bot}.jsonl"]
    if not files:
        print(f"tidak ada ledger di {a.ledger}" + (f" untuk {a.bot}" if a.bot else ""))
        return 2
    views = {}

    def view(name):                                    # pandangan funding dimuat sekali dan malas (F-D76)
        if name not in views:
            views[name] = load_csv_dir(a.bars, DATA_SYMBOLS, funding_view=name)
        return views[name]

    rc = 0
    if a.action == "fd16":
        return _ledger_fd16(files, view)
    if a.action == "skor":
        return _ledger_skor(files, view)
    if a.action == "pembunuh":
        return _ledger_pembunuh(a, view)
    for path in files:
        name = os.path.basename(path)
        try:
            recs = ledgermod.load(path)
        except ledgermod.LedgerError as e:
            print(f"{name}: RUSAK: {e}")
            rc = 1
            continue
        if a.action == "report":
            sp = SPECS.get(recs[0].get("bot_id")) if recs else None
            print(ledgermod.render_report(recs, ledgermod.provisional_settles(sp, view("provisional"), recs) if sp is not None and recs else None))
            print()
            continue
        problems = ledgermod.verify_chain(recs)
        spec = SPECS.get(recs[0].get("bot_id")) if recs else None
        if spec is None:
            problems.append("bot_id genesis tidak dikenal oleh kode")
        elif not any(x.startswith(("catatan pertama", "ledger kosong")) for x in problems):
            problems += ledgermod.verify_against_data(spec, recs, view("targets" if spec.method == "B3-CARRY" else "actual"), view("actual"))
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
    bk = sub.add_parser("book")
    bk.add_argument("action", nargs="?", default="status", choices=("status", "epoch", "verify"))
    bk.add_argument("--file", default=BOOK_FILE, help="berkas buku hidup (bawaan: ledger/book/buku.jsonl)")
    bk.add_argument("--ledger", default=os.path.join(REPO_ROOT, "ledger", "paper"))
    bk.add_argument("--bars", default=os.path.join(REPO_ROOT, "ledger", "bars"))
    bk.add_argument("--now", help="ISO UTC pengganti jam sekarang (uji)")
    bk.add_argument("--write", action="store_true", help="tulis catatan epoch (penulis tunggal buku hidup)")
    bk.add_argument("--no-gates", action="store_true", help="lewati gerbang penantang (vonis TIDAK_DIJALANKAN -> ditolak)")
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
    rv.add_argument("--prior-submissions", type=int, default=None, help="MANUAL: pengajuan sebelumnya keluarga ini (laporan tidak mengikat); bawaan: dihitung dari registri (P83)")
    rv.add_argument("--registri", default=os.path.join(REPO_ROOT, "ledger", "pengajuan", "registri.jsonl"), help="registri pengajuan (P83)")
    rv.add_argument("--catat", action="store_true", help="catat pengajuan ini di registri (resmi; hanya bila identitas terverifikasi): memakan anggaran A1/k keluarga")
    rv.add_argument("--placebo-n", type=int, default=200)
    rv.add_argument("--boot-n", type=int, default=1000)
    rv.add_argument("--incumbents", choices=("book", "six"), default="book", help="petahana G10: buku slot sekarang (bawaan) atau enam bot Fabius")
    lg = sub.add_parser("ledger")
    lg.add_argument("action", choices=("verify", "report", "fd16", "skor", "pembunuh"))
    lg.add_argument("--kunci", help="bersama `pembunuh`: tulis kunci terjemahan pembunuh dengan catatan ini (hanya atas kata builder)")
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
