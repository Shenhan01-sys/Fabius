"""Menilai prediksi arah yang SUDAH di-anchor: menang/kalah setelah ongkos, atau BELUM JATUH TEMPO.

Kenapa file ini ada: sampai kemarin jejak kita cuma membuktikan keterikatan dan waktu. Yang belum
pernah dijawab adalah pertanyaan yang paling jelas: apakah short MARSCOIN itu jadi untung? Tanpa
file ini, jawaban yang muncul nanti adalah ingatanku atau perasaanku - dan itu persis jenis angka
yang tidak boleh masuk submission.

Yang membuatnya tidak bisa dipakai curang, dan ini isi sebenarnya dari file ini:

1. **Harga masuk diambil dari REKAMAN, bukan dihitung ulang.** `decision.entry_ref` ikut terikat
   `decisionHash` (dan `snapshotHash` sudah di chain). Menulis ulang entry = mengubah hash =
   jejak on-chain-nya berhenti cocok. Jadi ledger ini tidak punya cara diam-diam untuk
   me-rebase prediksi yang sudah salah.
2. **"Belum jatuh tempo" bukan "untung" dan bukan "rugi".** Ia punya status sendiri, detik
   sisanya dicetak, dan tidak ikut agregat apa pun. Kebocoran paling umum di trading report
   adalah masa depan yang dihitung sebagai hasil.
3. **Urutan sentuh diperiksa, bukan diandaikan.** Untuk rezim stop-loss, mana yang lebih dulu
   kena (stop atau target) menentukan hasilnya; kalau keduanya tersentuh di bar yang SAMA,
   hasilnya ditulis AMBIGU - bukan dipilih yang lebih enak.
4. **Ongkos nyata dipakai sejak awal** (20 bps RT, vault/08 §3), dan yang dilaporkan adalah NET.

Rezimu ikut dibaca dari rekaman: `time-stop` = keluar di horizon (atau di stop/target kalau
tersentuh, karena time-stop adalah plafon waktu, bukan larangan keluar), `stop-loss` = stop aktif.

Pakai:  python tools/ledger.py                      # semua keputusan arah yang terikat chain
         python tools/ledger.py --emit              # + tulis decisions/ledger-*.jsonl
         python tools/ledger.py --only MARSCOINUSDT
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import bars as barsmod  # noqa: E402
import direction as D   # noqa: E402  (ongkos & ambang satu sumber; tidak ada angka kedua)

RT_COST_BPS = 20.0          # vault/08 §3 (5,5 + 4,5 per sisi) - sama dengan yang dipakai backtest
BARS_DIR = os.path.join(ROOT, "decisions")


def load_decisions():
    """Semua rekaman arah dari decisions/direction-*.jsonl."""
    out = []
    for p in sorted(glob.glob(os.path.join(BARS_DIR, "direction-*.jsonl"))):
        for ln in open(p, encoding="utf-8"):
            ln = ln.strip()
            if not ln:
                continue
            r = json.loads(ln)
            if r.get("kind") == "direction":
                r["_src"] = os.path.basename(p)
                out.append(r)
    return out


def window_bars(symbol, from_ms, to_ms, refresh=True):
    """Bar [from_ms, to_ms] untuk menilai apa yang terjadi SETELAH entry. None = datanya belum ada."""
    cached = barsmod.load(symbol, "1h")
    data = (cached or {}).get("bars") or []
    # Ambil ulang kalau cache belum menyentuh batas waktu yang diminta. Ini penting: cache yang
    # berhenti di jam 19:00 tidak boleh dipakai untuk menilai horizon yang jatuh tempo 19:00
    # keesokan harinya - dia akan bilang "belum ada data" selamanya sambil terlihat benar.
    if refresh and (not data or data[-1]["t"] < to_ms):
        got, meta = barsmod.fetch(symbol, "1h", 20, verbose=False)
        if got:
            barsmod.save(symbol, "1h", got, meta)
            data = got
    if not data:
        return None
    return [b for b in data if from_ms <= b["t"] <= to_ms]


def score_one(rec, now_ms):
    d = rec.get("decision") or {}
    side = d.get("side")
    dt = rec.get("data") or {}
    if side not in ("long", "short"):
        return {"symbol": rec.get("symbol"), "status": "BUKAN POSISI", "side": side,
                "regime": d.get("regime"), "sellability": d.get("sellability"),
                # Catatan pendek dan utuh: versi lama memuat frasa panjang yang terpotong di
                # tengah kata ("... -> tid") saat dicetak, dan kalimat terpotong dibaca sebagai
                # alat yang rusak, bukan sebagai informasi.
                "note": "flat/unassessable: tidak ada posisi yang bisa dinilai",
                "seat_eligible": d.get("seat_eligible")}
    entry = d.get("entry_ref")
    t_entry_ms = int(dt.get("last_bar_t") or 0)
    horizon_ms = int(d.get("horizon_h") or 24) * 3_600_000
    due_ms = t_entry_ms + horizon_ms
    base = {"symbol": rec.get("symbol"), "side": side, "regime": d.get("regime"),
            "entry": entry, "due_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(due_ms / 1000)),
            "horizon_h": d.get("horizon_h"), "sellability": d.get("sellability"),
            "seat_eligible": d.get("seat_eligible"), "decisionHash": rec.get("decisionHash")}
    if not entry or not t_entry_ms:
        return {**base, "status": "TIDAK DINILAI", "why": "rekaman tanpa entry_ref/last_bar_t"}
    if now_ms < due_ms:
        return {**base, "status": "BELUM JATUH TEMPO",
                "why": f"tersisa {(due_ms - now_ms) / 3.6e6:.1f} jam", "due_ms": due_ms}

    bars_win = window_bars(rec["symbol"], t_entry_ms + 3_600_000, due_ms)
    if not bars_win:
        return {**base, "status": "TIDAK DINILAI", "why": "tidak ada bar dalam jendela horizon"}

    exit_bar = bars_win[-1]
    sign = 1.0 if side == "long" else -1.0
    stop, target = d.get("stop"), d.get("target")

    # Cari mana yang lebih dulu tersentuh. Stop-loss rezim: itu hasil akhirnya.
    first = None      # ("stop"|"target", bar) - bar-nya disimpan, bukan diambil dari sisa loop
    for b in bars_win:
        if stop is not None and (b["h"] >= stop if side == "short" else b["l"] <= stop):
            first = ("stop", b)
            break
        if target is not None and (b["l"] <= target if side == "short" else b["h"] >= target):
            first = ("target", b)
            break
    if first and first[0] == "stop":
        fb = first[1]
        px = stop
        # Bar 1 jam tidak memberitahu URUTAN dalam bar itu sendiri. Kalau stop DAN target dua-duanya
        # mungkin di bar yang sama, hasilnya ditulis AMBIGU - bukan dipilih yang lebih enak, dan
        # bukan pula dianggap menang karena "mungkin kena target duluan".
        if (target is not None and
                ((side == "short" and fb["h"] >= stop and fb["l"] <= target) or
                 (side == "long" and fb["l"] <= stop and fb["h"] >= target))):
            outcome = "AMBIGU (stop & target di bar yang sama)"
        else:
            outcome = "STOP KENA"
    elif first and first[0] == "target":
        px, outcome = target, "TARGET KENA"
    else:
        px, outcome = exit_bar["c"], f"exit di horizon ({d.get('regime')})"

    gross = sign * (px / entry - 1.0) * 1e4
    net = gross - RT_COST_BPS
    return {**base, "status": "DINILAI", "outcome": outcome, "exit_px": round(float(px), 10),
            "gross_bps": round(gross, 1), "net_bps": round(net, 1),
            "win": net > 0, "bars_in_window": len(bars_win),
            "mfe_bps": round(sign * ((max(b["h"] for b in bars_win) if side == "long"
                                      else min(b["l"] for b in bars_win)) / entry - 1.0) * 1e4, 1),
            "exit_bar_t": exit_bar["t"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--emit", action="store_true")
    a = ap.parse_args()

    recs = load_decisions()
    if a.only:
        # Ekspresi lama punya `want.endswith(sym)` - kalau satu baris kebetulan punya symbol="",
        # kondisinya True untuk SEMUA baris dan filternya diam-diam tidak menyaring apa pun.
        # Di sini: persis, atau simbol + "USDT", tidak lebih kreatif dari itu.
        want = a.only.upper()
        alt = want if want.endswith("USDT") else want + "USDT"
        recs = [r for r in recs if str(r.get("symbol") or "").upper() in (want, alt)]
    if not recs:
        raise SystemExit("tidak ada rekaman arah di decisions/ - jalankan tools/direction.py --emit dulu")

    now_ms = int(time.time() * 1000)
    # Dedupe pada LEVEL PERISTIWA, bukan pada level hash. `decisionHash` selalu beda antar siklus
    # (ia memuat `ts_utc` generasi), jadi 5 rekaman MARSCOIN short yang masuk dari bar yang sama
    # dengan harga masuk yang sama adalah SATU peristiwa pasar - bukan 5 bukti. Kalau tidak
    # digabung, "n" laporan ini membengkak persis seperti yang membuat hasil trading orang tidak
    # bisa dipercaya. Yang di chain tetap 5 (itu jejak kapan kami menulis), tapi yang DINILAI 1.
    by_event, dup = {}, 0
    for r in recs:
        d = r.get("decision") or {}
        dt = r.get("data") or {}
        if d.get("side") in ("long", "short"):
            key = (r.get("symbol"), d.get("side"), d.get("entry_ref"),
                   int(dt.get("last_bar_t") or 0), d.get("horizon_h"))
        else:
            key = (r.get("symbol"), r.get("decisionHash"))
        if key in by_event:
            dup += 1
            continue
        by_event[key] = r
    rows = [score_one(r, now_ms) for r in by_event.values()]
    n_pos = sum(1 for x in rows if x.get("side") in ("long", "short"))
    print(f"rekaman dibaca: {len(recs)} | peristiwa posisi unik: {n_pos} "
          f"({dup} salinan identik digabung: hash-nya beda karena memuat waktu generasi, "
          f"peristiwanya sama)")

    print(f"sekarang {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now_ms / 1000))} | "
          f"ongkos {RT_COST_BPS:.0f} bps RT | entry dibaca dari rekaman (bukan dihitung ulang)\n")
    print(f"{'simbol':16}{'side':>7}{'rezim':>12}{'status':>20}{'gross':>8}{'NET':>8}{'hasil':>7}  catatan")
    print("-" * 122)
    for x in rows:
        if x["status"] == "BUKAN POSISI":
            print(f"{str(x['symbol'])[:16]:16}{'-':>7}{str(x['regime'])[:12]:>12}{x['status']:>20}"
                  f"{'':>8}{'':>8}{'-':>7}  {x['note'][:44]}")
            continue
        g = x.get("gross_bps")
        n = x.get("net_bps")
        w = x.get("win")
        print(f"{str(x['symbol'])[:16]:16}{str(x['side']):>7}{str(x['regime'])[:12]:>12}{x['status']:>20}"
              f"{('' if g is None else f'{g:+.1f}'):>8}{('' if n is None else f'{n:+.1f}'):>8}"
              f"{('-' if w is None else ('MENANG' if w else 'RUGI')):>7}  "
              f"{x.get('outcome') or x.get('why') or ''}"
              f"{'' if x.get('due_utc') is None else ' | due ' + x['due_utc']}")

    scored = [x for x in rows if x["status"] == "DINILAI"]
    pend = [x for x in rows if x["status"] == "BELUM JATUH TEMPO"]
    if scored:
        nets = [x["net_bps"] for x in scored]
        wr = sum(1 for x in scored if x["win"]) / len(scored)
        print(f"\nANGKA: {len(scored)} dinilai | WR {wr*100:.0f}% | net rata-rata "
              f"{sum(nets)/len(nets):+.1f} bps | total {sum(nets):+.1f} bps | "
              f"rugi bersih {sum(1 for x in scored if not x['win'])}")
    else:
        print(f"\nANGKA: belum ada yang bisa dinilai - {len(pend)} posisi masih dalam horizon. "
              "Ini hasil, bukan kegagalan: tidak ada angka yang boleh ditulis sebelum waktunya.")
    print("Agregat TIDAK memasukkan yang BELUM JATUH TEMPO, dan status AMBIGU tidak pernah "
          "dipilih sepihak.")

    if a.emit:
        p = os.path.join(BARS_DIR, f"ledger-{time.strftime('%Y%m%d', time.gmtime())}Z.jsonl")
        blob = json.dumps(rows, sort_keys=True, separators=(",", ":"))
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"kind": "ledger", "as_of_utc": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_ms / 1000)),
                "cost_bps_rt": RT_COST_BPS,
                "rows_sha256": "0x" + hashlib.sha256(blob.encode()).hexdigest(),
                "rows": rows}, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"tertulis: {p}")


if __name__ == "__main__":
    main()
