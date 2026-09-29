"""Buku PAPER Fabius: agen membuka posisi boongan dari aliran ⑦, dan skornya dijalankan terus.

Kenapa alat ini ada (koreksi arah, 28 Sep sore): sepanjang hari aku memperlakukan "belum bisa
membuktikan harapan positif dengan uang nyata" seolah itu batas untuk *mengambil posisi sama sekali*.
Builder meluruskan: yang diminta bukan order sungguhan, tapi **paper trading** - dan di buku paper
hambatan "fill/kedalaman" turun kelas jadi kewajiban melapor, bukan larangan. Jadi alat ini:

  1. membangun kejadian dari aliran ⑦ dengan harga PERISTIWA (`tx.t`,`tx.p`) - bukan `px` beku
     (kesalahan yang dibatalkan F-D30),
  2. memakai gerbang yang BENAR-BENAR terbukti: kerumunan jual = VETO (`jual_2`/`jual_bersih`),
  3. memilih posisi dalam budget paper (default 20/hari - `dailyCap` kontrak 5 disebut terpisah,
     karena di paper budget kita yang menentukan, bukan kontrak),
  4. memotong ongkos round-trip TERUKUR (59 bps, `measured-own-venue`) ditambah **haircut dampak**
     s/L per sisi dari likuiditas snapshot - jadi "boongan" tidak berarti "murah",
  5. menilai terhadap TIGA pembanding yang sama: acak, pertama-yang-datang, dan tanpagerbang.

Yang TIDAK diklaim: ini bukan PnL. Ini harapan per posisi boongan pada harga transaksi, pada satu
jendela, dan angka ranking-nya (`lock_percent`) masih kandidat yang belum melewati hari kedua.

LABEL, dan ini bagian yang builder minta eksplisit (28 Sep sore): posisi di sini adalah **slot yang
nanti ditambal oleh posisi asli**, bukan laporan paralel. Karena itu tiap posisi membawa
`mode: "PAPER"` + `slot_id` yang tetap, dan kolom `pengganti_real` yang kosong sampai order
sungguhan mengisinya. Aturan naiknya juga hidup di sini, bukan di kepala: `--promote-after 2` berarti
sebuah kebijakan baru boleh menurunkan posisi ASLI setelah N prediksi paper benar beruntun - dan
alatnya mencetak status itu tiap hari, supaya "berani" kita punya tanggal mulai, bukan perasaan.

Pakai:  python -X utf8 tools/paper_book.py
       python -X utf8 tools/paper_book.py --rank lock --per-day 20 --size-quote 0.01 --emit
       python -X utf8 tools/paper_book.py --per-day 200 --promote-after 3
Artefak: decisions/paper-book-<UTC>.json (+ rows_sha256) dan, dengan --emit, satu berkas
         append-only `decisions/paper-book-positions.jsonl` yang dibaca `tools/winlog.py` sebagai
         seri KETIGA - tidak pernah dicampur dengan PAPER ter-anchor maupun CHAIN
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import prices as PR  # noqa: E402
import random
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import costs  # noqa: E402
import flow_cluster_test as FC  # noqa: E402
import mirror_test as MT  # noqa: E402  (SATU definisi kejadian + harga peristiwa)
import quintile_test as QT  # noqa: E402  (join snapshot universe point-in-time)

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
HARI = 86400
OUT_DIR = os.path.join(ROOT, "decisions")
SLOT = os.path.join(OUT_DIR, "paper-book-positions.jsonl")


def wINS(x):
    return max(-2000.0, min(2000.0, x))


def boot_mean(xs, draws=4000, seed=20260928):
    """CI bootstrap rata-rata (bukan median): yang menentukan 'layak real' adalah harapan, dan
    harapan pada payoff miring kanan harus dilaporkan dengan intervalnya, bukan titik saja."""
    import random as _r
    if not xs:
        return 0.0, 0.0
    rnd = _r.Random(seed)
    n = len(xs)
    means = sorted(sum(xs[rnd.randrange(n)] for _ in range(n)) / n for _ in range(draws))
    return means[int(0.025 * draws)], means[int(0.975 * draws)]


def haircut(net, liq, size_quote):
    """Dampak harga s/L per sisi, x·y=k, dua sisi -> dikurangkan dari net bps.

    Asal aritmetika: [[TradingKnowledge/FD3 - Slippage dan Likuiditas]] (s/L, komposisi dua kaki).
    Likuiditas tidak diketahui -> TIDAK dianggap besar: nilainya 0 dan kejadiannya dihitung terpisah,
    supaya "tanpa data" tidak menyamar sebagai "tanpa dampak".
    """
    if not liq or liq <= 0 or not size_quote:
        return net, False
    imp = 10000.0 * (2.0 * size_quote / liq)
    return net - imp, True


_WP = {}


def wp_map():
    if not _WP:
        _WP.update(PR.load(os.path.join(ROOT, "universe", "watch-prices.jsonl"), "wp")["rows"])
    return _WP


def vol_sebelum(tk, t, ekor=40):
    """Volatilitas dari `ekor` baris ticker `wp` TERAKHIR sebelum masuk - definisi yang SAMA dengan
    yang diukur `tools/topk_test.py`, bukan "window 30 menit" yang mirip.

    Versi pertama fungsi ini membatasi jendelanya ke 30 menit dan mengembalikan None untuk SEMUA
    kejadian: ticker watch hanya berdetak sekali per siklus rekaman (±35 menit), jadi 12 baris dalam
    30 menit tidak pernah ada. Kalau A/B hidup memakai definisi yang berbeda dari backtest, yang
    diuji adalah aturan lain - dan itu kegagalan yang tidak kelihatan dari angkanya sendiri.
    """
    ser = wp_map().get(str(tk or "").lower()) or []
    ps = [p for tt, p in ser if tt <= t][-ekor:]
    if len(ps) < 12:
        return None
    dr = [b / a - 1.0 for a, b in zip(ps[:-1], ps[1:]) if a > 0]
    if len(dr) < 8:
        return None
    return statistics.pstdev(dr)


def e9_kunci():
    """`t_kunci` E9 (kalau ada) - dibaca tiap jalan, bukan disalin sebagai angka."""
    p = os.path.join(ROOT, "decisions", "prereg-vol-lock.json")
    if not os.path.exists(p):
        return None
    try:
        return int(json.load(io.open(p, encoding="utf-8")).get("t_kunci") or 0) or None
    except (ValueError, OSError):
        return None


def bangun(kebijakan, horizon, per_hari, ukuran, seed=20260928):
    ev = MT.bangun(horizon, 15)
    snap = QT.snapshots()
    for e in ev:
        f = QT.ambil(snap, e["tk"], e["t"]) or {}
        e["liq"] = f.get("liquidity")
        e["lock"] = f.get("lock_percent")
        e["vol24"] = f.get("volume_24h")
        raw = e["net"]
        e["net_persenliq"], e["hcd"] = haircut(raw, e["liq"], ukuran)
        e["vol"] = vol_sebelum(e["tk"], e["t"])
    boleh = [e for e in ev if not (e["jual_2"] or e["jual_bersih"])]
    hari = sorted({e["t"] // HARI for e in boleh})
    dipilih, rnd = [], random.Random(seed)
    for d in hari:
        k = sorted([e for e in boleh if e["t"] // HARI == d], key=lambda e: e["t"])
        if kebijakan == "first":
            dipilih += k[:per_hari]
        elif kebijakan == "random":
            c = k[:]
            rnd.shuffle(c)
            dipilih += c[:per_hari]
        elif kebijakan == "lock":
            tahu = [e for e in k if isinstance(e["lock"], (int, float))]
            buta = [e for e in k if not isinstance(e["lock"], (int, float))]
            dipilih += sorted(tahu, key=lambda e: -(e["lock"] or 0))[:per_hari]
            if len(dipilih) < per_hari * (hari.index(d) + 1):
                dipilih += buta[:max(0, per_hari - len(tahu))]
        elif kebijakan in ("vol-rendah", "vol-tinggi"):
            # A/B HIDUP dari kandidat E7. Yang boleh dipilih hanya yang volatilitasnya TERUKUR;
            # sisanya dicatat, tidak diisi diam-diam dengan urutan waktu.
            #
            # `open_utc` slot adalah WAKTU PERISTIWA, bukan waktu jalan. Tanpa penyaring ini,
            # semua slot yang dibuka hari pertama justru berselang 05:13Z-nya kunci E9 dan
            # `tools/vol_ab.py` membuangnya sebagai prefill: alatnya kelihatan hijau, eksperimennya
            # kosong. Yang dipegang hidup hanyalah kejadian setelah kunci.
            tk9 = e9_kunci()
            if tk9 is not None:
                k = [e for e in k if e["t"] > tk9]
            tahu = [e for e in k if isinstance(e.get("vol"), (int, float))]
            separuh = max(1, len(tahu) // 2)
            xs = sorted(tahu, key=lambda e: e["vol"])
            ambil = xs[:separuh] if kebijakan == "vol-rendah" else xs[-separuh:]
            rnd.shuffle(ambil)
            dipilih += sorted(ambil, key=lambda e: e["t"])[:per_hari]
        elif kebijakan == "tanpa-gerbang":
            dipilih += sorted([e for e in ev if e["t"] // HARI == d], key=lambda e: e["t"])[:per_hari]
    return ev, boleh, dipilih


def ringkas(xs, label):
    if not xs:
        return {"kebijakan": label, "n": 0}
    net = [e["net_persenliq"] for e in xs]
    raw = [e["net"] for e in xs]
    return {"kebijakan": label, "n": len(xs),
            "hari": len({e["t"] // HARI for e in xs}),
            "mean_winso_bps": round(sum(wINS(x) for x in net) / len(net), 1),
            "mean_winso_sebelum_dampak": round(sum(wINS(x) for x in raw) / len(raw), 1),
            "median_bps": round(FC.med(net), 1),
            "p_ge_500": round(100.0 * sum(1 for x in net if x >= 500) / len(net), 1),
            "p_positif": round(100.0 * sum(1 for x in net if x > 0) / len(net), 1),
            "total_bps": round(sum(wINS(x) for x in net), 0),
            "tanpa_liq": sum(1 for e in xs if not e["hcd"])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizon", type=int, default=30)
    ap.add_argument("--per-day", type=int, default=20, help="budget posisi PAPER per hari")
    ap.add_argument("--size-quote", type=float, default=1.0, help="nominal BNB per posisi (paper)")
    ap.add_argument("--rank", default="lock", choices=("lock", "first", "random", "tanpa-gerbang", "vol-rendah", "vol-tinggi"))
    ap.add_argument("--kontrak-cap", type=int, default=5,
                    help="dailyCap kontrak - dicetak sebagai pembanding, BUKAN dipakai di paper")
    ap.add_argument("--promote-after", type=int, default=2,
                    help="N prediksi paper benar BERUNTUN sebelum kebijakan boleh menurunkan "
                         "posisi ASLI (aturan builder 28 Sep: '2 kali benar dulu baru berani')")
    ap.add_argument("--emit", action="store_true",
                    help="tulis slot ke decisions/paper-book-positions.jsonl (append-only)")
    a = ap.parse_args()
    rt = costs.rt_cost()
    baris = []
    print("buku PAPER | harga peristiwa | ongkos %.1f bps RT + dampak s/L | budget paper %d/hari "
          "(kontrak: %d/hari) | nominal %.2f BNB/posisi" % (rt, a.per_day, a.kontrak_cap,
                                                            a.size_quote))
    for pol in ("first", "random", "lock", "tanpa-gerbang", "vol-rendah", "vol-tinggi"):
        ev, boleh, dip = bangun(pol, a.horizon, a.per_day, a.size_quote)
        r = ringkas(dip, pol)
        baris.append(r)
        if r.get("n"):
            print("  %-14s n=%-5d/%-5d hari=%-3d mean_winso %+8.1f (sebelum dampak %+8.1f) | median "
                  "%+8.1f | P>=500 %5.1f%% | positif %5.1f%% | tanpa-liq %d"
                  % (pol, r["n"], len(boleh), r["hari"], r["mean_winso_bps"],
                     r["mean_winso_sebelum_dampak"], r["median_bps"], r["p_ge_500"], r["p_positif"],
                     r["tanpa_liq"]))
        else:
            print("  %-14s tidak ada posisi" % pol)
    ev, boleh, dip = bangun(a.rank, a.horizon, a.per_day, a.size_quote)
    harian = {}
    for e in dip:
        harian.setdefault(e["t"] // HARI, []).append(wINS(e["net_persenliq"]))
    print("\nharian (kebijakan %s):" % a.rank)
    for d in sorted(harian):
        xs = harian[d]
        print("   hari +%d  posisi=%-3d mean %+8.1f bps | median %+8.1f | %5.1f%% positif"
              % (d * HARI / 86400.0, len(xs), sum(xs) / len(xs), FC.med(xs),
                 100.0 * sum(1 for x in xs if x > 0) / len(xs)))
    def iso(t):
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))

    slots, streak = [], 0
    for e in sorted(dip, key=lambda x: x["t"]):
        net = e["net_persenliq"]
        streak = streak + 1 if net > 0 else 0
        slots.append({
            "slot_id": hashlib.sha256(("%s|%d|%s" % (e["tk"], e["t"], a.rank)).encode()).hexdigest()[:16],
            "mode": "PAPER",
            "label": "PAPER - slot ini diganti posisi ASLI kalau kebijakan sudah dipromosikan",
            "kebijakan": a.rank, "tk": e["tk"], "side": "LONG",
            "open_utc": iso(e["t"]), "due_utc": iso(e["t"] + int(e.get("horizon_m", a.horizon)) * 60),
            "entry_px": e.get("p0"), "exit_px": e.get("p1"),
            "gross_bps": round(e["net"] + rt, 1), "net_bps": net,
            "dampak_bps": round(e["net"] - net, 1) if e.get("hcd") else 0.0,
            "likuiditas_diketahui": bool(e.get("hcd")), "liq_usd": e.get("liq"),
            "size_quote_paper": a.size_quote, "streak_benar": streak,
            "promosi": "STREAK CUKUP" if streak >= a.promote_after else "BELUM",
            "pengganti_real": None, "status": "dinilai"})
    siap = [x for x in slots if x["promosi"] == "STREAK CUKUP"]
    puncak = 0
    for x in slots:
        puncak = max(puncak, x["streak_benar"])
    # Streak saja tidak cukup - dan ini bisa dihitung, bukan diperdebatkan. Kalau peluang menang per
    # posisi ~40 % (terukur di buku ini), dua menang beruntun terjadi ~16 % dari waktu itu: dia bukan
    # kredensial, dia kebetulan yang urutannya kita pilih sendiri. Karena itu keputusan "layak REAL"
    # memakai gerbang F-D16/F-D22 yang sudah ada di vault: n>=20 DAN harapan bersih > 0 DAN batas
    # bawah CI bootstrap > 0 - streak tetap dicetak, karena itu permintaanmu, tapi dia bukan vonis.
    xs = [x["net_bps"] for x in slots]
    ws = [wINS(v) for v in xs]
    wr = sum(1 for v in xs if v > 0) / max(len(xs), 1)
    lo, hi = boot_mean(ws)
    mean_w = sum(ws) / max(len(ws), 1)
    mean_raw = sum(xs) / max(len(xs), 1)
    n_cukup = len(xs) >= 20
    # CONTROL. Ini yang membuat vonis berarti: `random` + gerbang yang sama BUKAN sebuah kebijakan,
    # dia baseline universe. Kalau kebijakan menyamai acaknya, yang diukur adalah "feed ini
    # menunjukkan token yang sedang naik" - bukan "Fabius bisa memilih".
    control = next((b for b in baris if b.get("kebijakan") == "random"), None)
    c_mean = (control or {}).get("mean_winso_bps")
    # `random` adalah CONTROL, bukan kebijakan: dia tidak bisa mempromosikan dirinya sendiri, dan
    # membandingkannya dengan dirinya sendiri hanya menghasilkan True karena pembulatan.
    di_atas_acak = (a.rank != "random") and (c_mean is not None) and (round(mean_w, 1) > c_mean)
    layak = (n_cukup and mean_w > 0 and lo > 0 and puncak >= a.promote_after and di_atas_acak)
    for x in slots:
        x["kebijakan_layak_real"] = "YA" if layak else "BELUM"
    print("\npeluang menang per posisi paper = %.1f %% -> %d menang beruntun terjadi ~%.0f %% dari "
          "waktu itu KALAU tidak ada efek apa pun"
          % (100.0 * wr, a.promote_after, 100.0 * (wr ** a.promote_after)))
    print("   mean: RAW %+9.1f bps (tidak dilaporkan sebagai harapan - ekornya menelan) | "
          "WINSO %+8.1f bps  CI [%+.1f; %+.1f]" % (mean_raw, mean_w, lo, hi))
    print("   control (random + gerbang yang sama) = %+0.1f bps winso -> kebijakan harus DI ATAS "
          "ini, kalau tidak: yang terukur universe, bukan pilihan" % (c_mean if c_mean is not None
                                                                       else 0.0))
    print("vonis kebijakan %s: %s   (n=%d>=20:%s | winso %+0.1f CI lo %+0.1f | di atas acak:%s | "
          "streak maks %d>=%d:%s)"
          % (a.rank,
             "LAYAK POSISI ASLI" if layak else (
                 "CONTROL - tidak pernah dipromosikan; dialah pengukurnya" if a.rank == "random"
                 else ("BELUM LAYAK - belum di atas control" if not di_atas_acak else
                       "BELUM LAYAK - tetap berlabel PAPER")),
             len(xs), n_cukup, mean_w, lo, di_atas_acak, puncak, a.promote_after,
             puncak >= a.promote_after))
    print("\npromosi per slot (aturan streak: %d prediksi paper benar BERUNTUN):" % a.promote_after)
    print("   streak terpanjang pada jendela ini : %d" % puncak)
    print("   slot yang mencapai streak           : %d dari %d  (STREAK CUKUP != kebijakan layak)"
          % (len(siap), len(slots)))
    if siap:
        print("   slot pertama yang mencapai streak: %s %s (streak %d, net %+0.1f bps)"
              % (siap[0]["slot_id"], siap[0]["open_utc"], siap[0]["streak_benar"], siap[0]["net_bps"]))
    else:
        print("   -> belum ada. Semua posisi malam ini tetap berlabel PAPER, dan tidak ada yang "
              "boleh ditulis 'akan dipasang'")
    if a.emit:
        ada = set()
        if os.path.exists(SLOT):
            for ln in io.open(SLOT, encoding="utf-8", errors="replace"):
                ln = ln.strip()
                if ln and not ln.startswith("#"):
                    try:
                        ada.add(json.loads(ln).get("slot_id"))
                    except ValueError:
                        pass
        baru = [x for x in slots if x["slot_id"] not in ada]
        with io.open(SLOT, "a", encoding="utf-8", newline="\n") as fh:
            for x in baru:
                fh.write(json.dumps(x, sort_keys=True, ensure_ascii=False) + "\n")
        print("   emit: %d slot baru ditulis ke decisions/%s (sebelumnya %d tersimpan)"
              % (len(baru), os.path.basename(SLOT), len(ada)))
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "promote_after": a.promote_after, "slot_total": len(slots),
           "slot_streak_cukup": len(siap), "streak_terpanjang": puncak,
           "vonis_kebijakan": {"kebijakan": a.rank, "layak_real": bool(layak), "n": len(xs),
                               "peluang_menang": round(100.0 * wr, 1),
                               "mean_winso_bps": round(mean_w, 1),
                               "mean_raw_bps_JANGAN_dipakai": round(mean_raw, 1),
                               "ci_lo_mean_winso": round(lo, 1), "ci_hi_mean_winso": round(hi, 1),
                               "control_random_winso": c_mean, "di_atas_acak": bool(di_atas_acak),
                               "streak_terpanjang": puncak,
                               "gerbang": "F-D16 (n>=20 DAN harapan>0 DAN CI bawah>0) + wajib di "
                                          "atas control random; streak dicatat, bukan jadi vonis"},
           "horizon_menit": a.horizon, "budget_paper_per_hari": a.per_day,
           "daily_cap_kontrak": a.kontrak_cap, "size_quote_paper": a.size_quote,
           "ongkos_bps_rt": rt, "sumber_harga": "peristiwa (tx.t,tx.p)", "kebijakan_aktif": a.rank,
           "perbandingan": baris,
           "bata": ["paper, bukan PnL: tidak ada order, tidak ada antrean, tidak ada likuiditas "
                    "sungguhan di kaki keluar",
                    "dampak s/L memakai likuiditas snapshot; %d posisi tidak punya angka likuiditas "
                    "-> haircut 0 (dilaporkan, tidak dianggap kecil)" % ringkas(dip, a.rank).get(
                        "tanpa_liq", 0),
                    "ranking `lock` masih KANDIDAT (lolos 2 uji tapi kuintil 24-51 kejadian) - belum "
                    "lewat hari kedua",
                    "satu jendela ~50 jam, satu rezim"],
           "jumlah_posisi_aktif": len(dip)}
    # hash yang berguna = hash ISI buku (slot), bukan hash tabel perbandingan: yang mau ditambal
    # posisi asli adalah slotnya, jadi sha ini yang harus cocok saat seorang memeriksa chain
    out["rows_sha256"] = "0x" + hashlib.sha256(
        json.dumps(slots, sort_keys=True, separators=(",", ":"),
                   default=str).encode()).hexdigest()
    out["sha_perbandingan"] = "0x" + hashlib.sha256(
        json.dumps(baris, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    os.makedirs(OUT_DIR, exist_ok=True)
    p = os.path.join(OUT_DIR, "paper-book-%s.json" % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True,
              ensure_ascii=False)
    print("\nkebijakan aktif %s: %d posisi paper | rows_sha256=%s..." % (a.rank, len(dip),
                                                                        out["rows_sha256"][:16]))
    print("artefak: decisions/%s" % os.path.basename(p))


if __name__ == "__main__":
    main()
