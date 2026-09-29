"""P31.1/P31.2 - laboratorium ALASAN MASUK: E1 (tenang-setelah-kerumunan) & E2 (jendela risiko).

Spesifikasi ditulis SEBELUM satu pun angka hasil dilihat (28 Sep ±11:3xZ); sha-nya dicetak tiap jalan
dan disimpan di `decisions/prereg-entry-lock.json`. Kalau blok spesifikasi itu diedit setelah dikunci,
alatnya mati. Ini bukan seremoni: dua klaim kami jatuh HARI INI karena aturan main berubah setelah
angkanya ada (F-D30 harga masuk beku, F-D32 control yang mempromosikan dirinya sendiri).

HIPOTESIS (semua fitur hanya dari data <= t)
  E1 tenang_setelah_kerumunan - kalau kerumunan beli memang pump-then-down pada 30 menit
     (terukur: berpasangan -313 s/d -491 bps), titik masuk yang benar bukan saat kerumunan, tapi
     SETELAH kerumunan berhenti dan harga masih di atas cluster:
       cluster : >=2 maker beli berbeda dan USD beli >= 500 pada (t-60m, t-15m]
       sepi    : <=1 maker beli dan USD beli <= 250 pada (t-15m, t]
       bertahan: harga(t) >= median harga peristiwa pada jendela cluster
  E2 jendela_risiko - payoff ekor mungkin milik rezim, bukan token:
       risk_on : USD beli AGREGAT seluruh token pada (t-60m, t] >= 1,5 x median 24 jam nilai itu
                 (median dihitung hanya dari titik <= t)
       dan tidak sedang ada kerumunan jual
  E3 sepi_total (kontrol untuk E1) - syarat "sepi" saja, tanpa syarat cluster. Kalau E3 == E1,
     berarti yang bekerja cuma "sepi", dan klaim "setelah kerumunan" itu hiasan.

ATURAN UJI yang tidak bisa ditawar
  - harga masuk = harga PERISTIVA pada t; keluar = median peristiwa pada t+[H-15, H+15] menit
  - net dipotong ongkos 59 bps (measured-own-venue) + dampak 2*s/L bila likuiditas diketahui
  - CONTROL wajib: pool yang sama (kejadian yang lolos veto) diacak sebanyak n hipotesis, 400 undian;
    hipotesis dinyatakan hidup hanya jika mean-nya DI ATAS CI-atas control
  - ekor: Fisher satu arah vs pool; tengah: Mann-Whitney vs pool TANPA menyertakan subgroup-nya;
    koreksi BH alpha 0,10; n < 20 tidak diuji (F-D16) dan itu dicetak, bukan disembunyikan
"""
from __future__ import annotations

import bisect
import hashlib
import io
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import costs  # noqa: E402
import flow_cluster_test as FC  # noqa: E402
import quintile_test as QT  # noqa: E402  (ekor_hipergeo + join snapshot point-in-time)

MIN, H, W = 60, 30, 15
SPEC = {"versi": "1", "horison_menit": H, "jendela_menit": W, "sepi_usd_maks": 250.0,
        "sepi_maker_maks": 1, "cluster_jendela_menit": 60, "cluster_maker_min": 2,
        "cluster_usd_min": 500.0, "risk_on_rasio": 1.5, "risk_on_jendela_menit": 60,
        "ukuran_bnb": 0.01, "winsor_bps": 2000.0, "n_min": 20, "draws_mean": 4000,
        "draws_control": 400, "sumber_harga": "peristiwa (tx)",
        "kontrol": "acak-dari-pool-lolos-veto-CI-atas-400-undian"}

# P42: dampak tidak lagi dihitung di sini. E1/E2/E3 DIKUNCI dengan rumus v1 (yang salah satuan,
# F-D46) - jadi alatnya sengaja memakai v1 supaya angka lama tetap bisa direproduksi, dan itu
# tercatat, bukan diam-diam. Mau melihat versi yang dibetulkan? ubah ke costs.ISI_V2 dan sebut
# bahwa kunci E1/E2/E3 tidak lagi setara.
SKEMA_ENTRY = costs.ISI_V1



def w(x):
    return max(-SPEC["winsor_bps"], min(SPEC["winsor_bps"], x))


def boot_mean(xs, draws, seed=20260928):
    if not xs:
        return 0.0, 0.0
    rnd = random.Random(seed)
    n = len(xs)
    m = sorted(sum(xs[rnd.randrange(n)] for _ in range(n)) / n for _ in range(draws))
    return m[int(0.025 * draws)], m[int(0.975 * draws)]


def baca():
    txs, series = {}, {}
    for ln in io.open(os.path.join(ROOT, "universe", "wallet-flow.jsonl"), encoding="utf-8",
                      errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        d = json.loads(ln)
        if d.get("k") not in ("tx", "txc"):
            continue
        tk = str(d.get("tk") or "").lower()
        t, p = int(d.get("t") or 0), float(d.get("p") or 0)
        if not tk or not t or p <= 0:
            continue
        txs.setdefault(tk, []).append({"t": t, "m": str(d.get("m") or "").lower(),
                                       "buy": bool(d.get("b")), "u": float(d.get("u") or 0)})
        series.setdefault(tk, []).append((t, p))
    for tk in txs:
        txs[tk].sort(key=lambda r: r["t"])
    ser = {tk: FC.dedupe_px(sorted(v, key=lambda r: r[0])) for tk, v in series.items()}
    return txs, ser


def waktu_pasar(txs):
    """USD beli agregat (semua token) pada jendela 60 m, dihitung hanya dari transaksi <= t."""
    beli = sorted((r["t"], r["u"]) for rows in txs.values() for r in rows if r["buy"])
    ts = [x[0] for x in beli]
    cum = [0.0]
    for _, u in beli:
        cum.append(cum[-1] + u)
    def jendela(t, menit):
        a = bisect.bisect_left(ts, t - menit * MIN)
        b = bisect.bisect_right(ts, t)
        return cum[b] - cum[a]
    return ts, jendela


def kejadian():
    txs, ser = baca()
    snap = QT.snapshots()
    pts, jendela = waktu_pasar(txs)
    # median 24 jam dari aktivitas pasar, di titik-titik yang sudah lewat saja
    sampel = sorted(set(pts[::max(1, len(pts) // 400)]))
    base = [(t, jendela(t, SPEC["risk_on_jendela_menit"])) for t in sampel]
    out, taken = [], {}
    for tk, rows in txs.items():
        ss = ser.get(tk) or []
        st = [x[0] for x in ss]
        for r in [x for x in rows if x["buy"]]:
            t = r["t"]
            if t - taken.get(tk, -10 ** 15) < H * MIN:
                continue
            i = bisect.bisect_right(st, t) - 1
            if i < 0:
                continue
            p0 = ss[i][1]
            ex = [p for tt, p in ss if t + (H - W) * MIN <= tt <= t + (H + W) * MIN]
            if not ex:
                continue
            taken[tk] = t
            w15 = [q for q in rows if t - W * MIN < q["t"] <= t]
            wcl = [q for q in rows if t - SPEC["cluster_jendela_menit"] * MIN < q["t"] <= t - W * MIN]
            b15 = [q for q in w15 if q["buy"]]
            bcl = [q for q in wcl if q["buy"]]
            mk15 = {q["m"] for q in b15 if q["m"]}
            mkc = {q["m"] for q in bcl if q["m"]}
            s15 = [q for q in w15 if not q["buy"]]
            mk_s = {q["m"] for q in s15 if q["m"]}
            usd_s = sum(q["u"] for q in s15)
            usd_b15 = sum(q["u"] for q in b15)
            usd_bcl = sum(q["u"] for q in bcl)
            pcl = [p for tt, p in ss
                   if t - SPEC["cluster_jendela_menit"] * MIN < tt <= t - W * MIN]
            net = round(10000.0 * (FC.med(ex) - p0) / p0 - costs.rt_cost(), 1)
            f = QT.ambil(snap, tk, t) or {}
            liq = f.get("liquidity")
            liq = liq if isinstance(liq, (int, float)) and liq > 0 else None
            dk = costs.dampak_round_trip(SPEC["ukuran_bnb"], liq, skema=SKEMA_ENTRY)
            if dk["sah"] and dk["dampak_bps"]:
                net = round(net - dk["dampak_bps"], 1)
            risk = jendela(t, SPEC["risk_on_jendela_menit"])
            lalu = [v for tt, v in base if tt <= t and tt >= t - 24 * 3600]
            m24 = FC.med(lalu) if len(lalu) >= 20 else None
            out.append({"tk": tk, "t": t, "net": net, "liq": liq,
                        "veto": len(mk_s) >= 2 or (len(mk_s) >= 2 and usd_s >= 1.5 * usd_b15)
                                or (usd_s >= 1.5 * max(usd_b15, 1.0) and len(mk_s) >= 2),
                        "jual2": len(mk_s) >= 2, "jual_bersih": usd_s >= 1.5 * usd_b15,
                        "e1": (len(mkc) >= SPEC["cluster_maker_min"] and usd_bcl >= SPEC["cluster_usd_min"]
                               and len(mk15) <= SPEC["sepi_maker_maks"]
                               and usd_b15 <= SPEC["sepi_usd_maks"]
                               and bool(pcl) and p0 >= FC.med(pcl)),
                        "e3_sepi": len(mk15) <= SPEC["sepi_maker_maks"]
                                   and usd_b15 <= SPEC["sepi_usd_maks"],
                        "e2": (m24 is not None and risk >= SPEC["risk_on_rasio"] * m24)})
    for e in out:
        e["veto"] = e["jual2"] or e["jual_bersih"]
    return out


def main():
    spec_sha = "0x" + hashlib.sha256(json.dumps(SPEC, sort_keys=True).encode()).hexdigest()
    lock = os.path.join(ROOT, "decisions", "prereg-entry-lock.json")
    print("spesifikasi sha=%s...  (ditulis sebelum hasil dilihat)" % spec_sha[:19])
    if os.path.exists(lock):
        lama = json.load(io.open(lock, encoding="utf-8"))
        if lama.get("spec_sha256") != spec_sha:
            raise SystemExit("SPESIFIKASI DIUBAH SETELAH DIKUNCI (%s... != %s...) - tidak ada hasil"
                             % (str(lama.get("spec_sha256"))[:19], spec_sha[:19]))
    else:
        json.dump({"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "spec": SPEC, "spec_sha256": spec_sha,
                   "catatan": "E1/E2/E3 ditetapkan 28 Sep sebelum satu pun angka hasil dilihat"},
                  io.open(lock, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
        print("kunci ditulis: decisions/prereg-entry-lock.json")
    ev = kejadian()
    pool = [e for e in ev if not e["veto"]]
    if len(pool) < 50:
        raise SystemExit("pool terlalu kecil (%d) - tidak ada yang diuji" % len(pool))
    pn = [w(e["net"]) for e in pool]
    p500 = sum(1 for v in pn if v >= 500)
    print("kejadian %d | pool lolos veto %d | dampak dihitung untuk %d | pool mean winso %+0.1f "
          "| P>=500 %.1f %%" % (len(ev), len(pool), sum(1 for e in pool if e["liq"]),
                                sum(pn) / len(pn), 100.0 * p500 / len(pn)))
    rnd = random.Random(20260928)
    hasil = []
    for nama in ("e1", "e2", "e3_sepi"):
        sub = [e for e in pool if e[nama]]
        if len(sub) < SPEC["n_min"]:
            print("\n%-9s n=%d < %d -> TIDAK DIUJI (F-D16)" % (nama, len(sub), SPEC["n_min"]))
            continue
        vs = [w(e["net"]) for e in sub]
        lo, hi = boot_mean(vs, SPEC["draws_mean"])
        luar = [v for e, v in zip(pool, pn) if not e[nama]]
        s500 = sum(1 for v in luar if v >= 500)
        mw = FC.mann_whitney_p(vs, luar)
        fis = QT.ekor_hipergeo(sum(1 for v in vs if v >= 500), len(vs), s500, len(luar))
        ctrls = []
        for _ in range(SPEC["draws_control"]):
            c = [rnd.choice(pn) for _ in range(len(vs))]
            ctrls.append(sum(c) / len(c))
        ctrls.sort()
        c_atas = ctrls[int(0.975 * len(ctrls))]
        di_atas = sum(vs) / len(vs) > c_atas
        hasil.append((nama, fis, sum(vs) / len(vs), di_atas))
        print("\n%-9s n=%d (%.1f %% dari pool)" % (nama, len(sub), 100.0 * len(sub) / len(pool)))
        print("   mean winso %+9.1f  CI [%+.1f; %+.1f] | median %+8.1f | P>=500 %5.1f %% | "
              "%4.1f %% positif" % (sum(vs) / len(vs), lo, hi, FC.med(vs),
                                    100.0 * sum(1 for v in vs if v >= 500) / len(vs),
                                    100.0 * sum(1 for v in vs if v > 0) / len(vs)))
        print("   control acak n=%d: CI atas %+0.1f -> %s" % (len(vs), c_atas,
              "DI ATAS control" if di_atas else "belum di atas control"))
        print("   Mann-Whitney vs pool-luar-subgroup p=%s | Fisher satu arah (ekor) p=%s"
              % (("%.4f" % mw) if mw is not None else "-", ("%.4f" % fis) if fis is not None else "-"))
    lulus = FC.bh([(a, p) for a, p, m, d in hasil if p is not None])
    atas = [a for a, p, m, d in hasil if d]
    print("\nBH alpha 0,10 pada uji ekor: %s" % (sorted(lulus) or "TIDAK ADA"))
    print("di atas control acak    : %s" % (sorted(atas) or "TIDAK ADA"))
    hidup = sorted(set(lulus) & set(atas))
    print("\nVONIS P31 malam ini: %s" % (("kandidat layak dibawa ke hari kedua: " + ", ".join(hidup))
                                         if hidup else
                                         "BELUM ADA alasan masuk. E1/E2/E3 tidak menaikkan ekor di "
                                         "atas pool DAN tidak di atas control."))
    out = {"dibuat_utc": time.strftime("%Y%m%dT%H:%M:%SZ", time.gmtime()), "spec_sha256": spec_sha,
           "spec": SPEC, "pool_n": len(pool), "vonis_hidup": hidup,
           "hasil": [{"h": a, "fisher_ekor": p, "mean_winso": round(m, 1), "di_atas_control": d}
                     for a, p, m, d in hasil]}
    p = os.path.join(ROOT, "decisions", "entry-lab-%s.json"
                     % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("artefak: decisions/%s" % os.path.basename(p))


if __name__ == "__main__":
    main()
