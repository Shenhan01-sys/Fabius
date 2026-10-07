"""P74: evaluasi lapisan pemilih bot (aturan + angka di `engine/pemilih_eval.py`, pra-registrasi `engine/locks/pemilih_eval.usulan.json`).

    python -X utf8 tools/pemilih_eval.py status
    python -X utf8 tools/pemilih_eval.py usulan --catatan "..."                        # pra-registrasi SEBELUM hasil (usulan beda -> history)
    python -X utf8 tools/pemilih_eval.py kunci  --catatan "disetujui Hans <tanggal>"   # HANYA atas kata builder; sha = berkas usulan
    python -X utf8 tools/pemilih_eval.py mundur [--bars ledger/bars] [--json out.json] # EKSPLORATIF: replay dalam-sampel, tanpa vonis
    python -X utf8 tools/pemilih_eval.py maju   [--ledger ledger/paper] [--analis ledger/analis] [--bars ledger/bars] [--json out.json]

`maju` = MENGIKAT: hanya settle FINAL `ledger/paper` + pilihan agent yang dikomit `ledger/analis`; settle PROVISIONAL (funding estimasi) dicetak
terpisah tanpa vonis. Pemilih yang dinilai: aturan hidup `engine/pemilih.py` (direkonstruksi per penutupan dari pilihan + skor sebelum penutupan
itu) dan tiap agent analis (pilihannya sendiri, keyakinan -> Brier). Tidak menyentuh jaringan, kunci, atau chain; tidak menulis apa pun selain
berkas usulan / kunci / --json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Mapping, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

from engine import book as bookmod, ledger as ledgermod, pemilih, pemilih_eval as pe   # noqa: E402
from engine.bots import REGISTRY                                                       # noqa: E402
from engine.data import load_csv_dir                                                   # noqa: E402
from engine.replay import prepare, replay                                              # noqa: E402
from engine.series import DAY_MS                                                       # noqa: E402
from engine.spec import PERP_UNIVERSE, SPECS                                           # noqa: E402

DATA_SYMBOLS = list(PERP_UNIVERSE) + ["PAXGUSDT", "XAUUSDT"]                           # sama dengan engine/cli.py
BOTS_MUNDUR = ("B1-TREND", "B2-RS", "B3-CARRY", "B5-CORE-RWA", "B6-BOUNCE")             # B4 tidak bisa direplay (deret per event)
BARS = os.path.join(ROOT, "ledger", "bars")
LEDGER = os.path.join(ROOT, "ledger", "paper")
ANALIS = os.path.join(ROOT, "ledger", "analis")


def biaya_semua(bots) -> Dict[str, float]:
    return {b: pe.biaya_dari_penggaris(SPECS[b].penggaris) for b in bots}


# ---------------------------------------------------------------- mundur: replay dalam-sampel

def data_mundur(bars_dir: str = BARS, bots=BOTS_MUNDUR) -> Tuple[Dict[str, Dict[int, float]], Dict[str, Dict[int, float]]]:
    """-> (net, gross) per bot dari `replay()` yang SAMA dengan gerbang; gross bar T = jumlah abs bobot target penutupan bar sebelumnya."""
    md = load_csv_dir(bars_dir, DATA_SYMBOLS, funding_view="actual")
    tb = prepare(md)
    net, gross = {}, {}
    for b in bots:
        spec = SPECS[b]
        tg = REGISTRY[spec.method](spec, md)
        net[b] = {int(T): float(x) for T, x in replay(spec, md, tg, tb)}
        gross[b] = {int(tg[k].t): sum(abs(float(w)) for w in tg[k - 1].weights.values()) for k in range(1, len(tg))}
    return net, gross


# ---------------------------------------------------------------- maju: ledger paper + pilihan agent

def data_maju(ledger_dir: str = LEDGER, bars_dir: str = BARS, provisional: bool = True) -> Dict[str, Any]:
    """Settle FINAL per bot (+ PROVISIONAL terpisah), gross dari tick, dan ledger yang rusak (tidak dipakai, dicetak)."""
    final: Dict[str, Dict[int, float]] = {}
    prov: Dict[str, Dict[int, float]] = {}
    gross: Dict[str, Dict[int, float]] = {}
    rusak: Dict[str, str] = {}
    md_prov = None
    for b in bookmod.FORWARD_BOTS:
        path = os.path.join(ledger_dir, f"{b}.jsonl")
        if not os.path.exists(path):
            continue
        try:
            recs = ledgermod.load(path)
        except ledgermod.LedgerError as e:
            rusak[b] = f"ledger rusak: {e}"
            continue
        masalah = ledgermod.verify_chain(recs)
        if masalah:
            rusak[b] = f"rantai: {masalah[0]}"
            continue
        final[b] = {int(r["bar"]): float(r["net"]) for r in recs if r.get("type") == "settle"}
        gross[b] = {int(r["asof"]) + DAY_MS: sum(abs(float(w)) for w in (r.get("targets") or {}).values())
                    for r in recs if r.get("type") == "tick"}
        if provisional:
            if md_prov is None:
                md_prov = load_csv_dir(bars_dir, DATA_SYMBOLS, funding_view="provisional")
            p = dict(final[b])
            try:
                for rec in ledgermod.provisional_settles(SPECS[b], md_prov, recs):
                    p.setdefault(int(rec["bar"]), float(rec["net"]))
            except Exception as e:  # noqa: BLE001 - bot tanpa jalur provisional (B4) = tidak ada angka, bukan angka karangan
                rusak[f"{b} (provisional)"] = f"{type(e).__name__}: {str(e)[:80]}"
            prov[b] = p
    return {"final": final, "provisional": prov, "gross": gross, "rusak": rusak}


def baca_pilihan(analis_dir: str = ANALIS) -> List[dict]:
    """Pilihan agent dari `ledger/analis/<bar_close>.jsonl`: satu per (agent, bar_close), yang dikomit menang (aturan `tools/analis.records`)."""
    best: Dict[tuple, dict] = {}
    if not os.path.isdir(analis_dir):
        return []
    for name in sorted(os.listdir(analis_dir)):
        if not name.endswith(".jsonl"):
            continue
        with open(os.path.join(analis_dir, name), encoding="utf-8") as f:
            for ln in f:
                if not ln.strip():
                    continue
                r = json.loads(ln)
                a = r.get("alasan") or {}
                k = (r.get("agent"), int(a.get("bar_close") or name[:-6]))
                if k not in best or (r.get("status") == "dikomit" and best[k].get("status") != "dikomit"):
                    best[k] = {"agent": r.get("agent"), "agent_id": int(a.get("agent_id") or 0), "bar_close": k[1], "bot": r.get("bot"),
                               "keyakinan": r.get("keyakinan"), "status": r.get("status")}
    return [best[k] for k in sorted(best, key=lambda k: (k[1], str(k[0])))]


def pemilih_dari_pilihan(picks: List[dict], net: Mapping[str, Mapping[int, float]], identitas: str) -> Dict[str, Any]:
    """Subjek yang dinilai dari pilihan dikomit: `PEMILIH` = aturan hidup `engine/pemilih.py` per penutupan C (skor = selisih net bot pilihan vs bot
    identitas pada bar pilihan-pilihan SEBELUM C, dari `net` yang diberikan), dan `agent:<slug>` = pilihan agent itu sendiri (+ keyakinan).
    Bar pilihan untuk penutupan C = bar yang DIBUKA di C (posisi tick penutupan C), sama dengan `tools/analis.skor`."""
    by_close: Dict[int, Dict[int, str]] = {}
    agen: Dict[str, Dict[int, str]] = {}
    yakin: Dict[str, Dict[int, Tuple[str, float]]] = {}
    for r in picks:
        if r.get("status") != "dikomit" or not r.get("bot"):
            continue
        C, T = int(r["bar_close"]), int(r["bar_close"]) * 1000
        by_close.setdefault(C, {})[int(r["agent_id"])] = r["bot"]
        nama = f"agent:{r['agent']}"
        agen.setdefault(nama, {})[T] = r["bot"]
        if r.get("keyakinan") is not None:
            yakin.setdefault(nama, {})[T] = (r["bot"], float(r["keyakinan"]))
    closes = sorted(by_close)
    aktif: Dict[int, str] = {}
    for C in closes:
        sk: Dict[int, List[Tuple[int, float]]] = {}
        for C2 in closes:
            if C2 >= C:
                break
            T2 = C2 * 1000
            for aid, bot in by_close[C2].items():
                if T2 in (net.get(bot) or {}) and T2 in (net.get(identitas) or {}):
                    sk.setdefault(aid, []).append((C2, float(net[bot][T2]) - float(net[identitas][T2])))
        aktif[C * 1000] = pemilih.aktif(by_close[C], sk, identitas, C)[0]
    return {"pemilih": {"PEMILIH": aktif, **agen}, "keyakinan": yakin}


# ---------------------------------------------------------------- perintah

def cmd_status(a) -> int:
    st = pe.status()
    print(f"P74 evaluasi pemilih: {st['state']} | sha kode {st['sha_kini']} | sha berkas {st.get('sha_berkas')} | {st.get('berkas') or '-'}"
          + (f" | {st['galat']}" if st.get("galat") else ""))
    return 0 if st["state"] in ("USULAN", "TERKUNCI") else 1


def cmd_usulan(a) -> int:
    d = pe.tulis_usulan(a.catatan)
    print(f"pra-registrasi P74: {d['status']} sha {d['sha']} ({d['diusulkan']})")
    return 0


def cmd_kunci(a) -> int:
    d = pe.tulis_kunci(a.catatan)
    print(f"kunci P74: {d['status']} sha {d['sha']} ({d['dikunci']})")
    return 0


def _peringatan_status() -> str:
    st = pe.status()
    return "" if st["state"] in ("USULAN", "TERKUNCI") else f"PERINGATAN: aturan kode {st['state']} terhadap berkas pra-registrasi - laporan ini bukan pra-registrasi"


def cmd_mundur(a) -> int:
    net, gross = data_mundur(a.bars)
    lap = pe.evaluasi(net, list(net), gross=gross, biaya=biaya_semua(net), mode=pe.MUNDUR)
    w = _peringatan_status()
    if w:
        print(w)
    print(pe.teks(lap, "(replay ledger/bars)"))
    if a.json:
        _tulis(a.json, {"mundur": lap})
    return 0


def cmd_maju(a) -> int:
    d = data_maju(a.ledger, a.bars, provisional=not a.tanpa_provisional)
    picks = baca_pilihan(a.analis)
    ident = pe.PARAMS_P74["angka"]["identitas"]
    w = _peringatan_status()
    if w:
        print(w)
    for b, why in sorted(d["rusak"].items()):
        print(f"  {b}: DIKECUALIKAN - {why}")
    out = {}
    for label, net in (("final", d["final"]), ("provisional", d["provisional"])):
        if label == "provisional" and a.tanpa_provisional:
            continue
        bots = sorted(b for b, xs in net.items() if xs)
        sub = pemilih_dari_pilihan(picks, net, ident)
        lap = pe.evaluasi(net, bots, pemilih=sub["pemilih"], gross=d["gross"], biaya=biaya_semua(bots),
                          keyakinan=sub["keyakinan"], mode=pe.MAJU)
        if label == "provisional":
            for s in lap["subjek"].values():                                     # provisional TIDAK PERNAH memberi vonis
                s["vonis"], s["alasan"] = "PROVISIONAL (bukan vonis)", ["funding estimasi; vonis hanya dari settle final"] + s.get("alasan", [])
        print(pe.teks(lap, f"[{label.upper()}] pilihan {len(picks)} catatan"))
        print()
        out[label] = lap
    if a.json:
        _tulis(a.json, out)
    return 0


def _tulis(path: str, obj: dict) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    print(f"tertulis {path}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    for name in ("usulan", "kunci"):
        x = sub.add_parser(name)
        x.add_argument("--catatan", required=True)
    m = sub.add_parser("mundur")
    m.add_argument("--bars", default=BARS)
    m.add_argument("--json")
    j = sub.add_parser("maju")
    j.add_argument("--ledger", default=LEDGER)
    j.add_argument("--analis", default=ANALIS)
    j.add_argument("--bars", default=BARS)
    j.add_argument("--tanpa-provisional", action="store_true")
    j.add_argument("--json")
    a = p.parse_args(argv)
    return {"status": cmd_status, "usulan": cmd_usulan, "kunci": cmd_kunci, "mundur": cmd_mundur, "maju": cmd_maju}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
