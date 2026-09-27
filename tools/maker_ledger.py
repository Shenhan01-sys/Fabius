"""Nilai maker dari siklus bukanya sendiri — bukan dari label siapa pun.

Pertanyaan yang dijawab: *dompet mana, di kolam mana, yang setelah ongkos benar-benar menambah
informasi?* Jawabannya tidak boleh diambil dari tag `smart_degen`/`kol` — itu label hari ini tentang
sejarah yang sudah terjadi (vault [[06-Results/06 - Pre-registration Horizon]] +
[[Concepts/Lookahead Bound]]). Jadi alat ini membaca rekaman ⑦ kami dan merekonstruksi perdagangan
yang **tertutup**:

  - `b=1, c=1`  membuka lot (qty = USD/harga)
  - `b=0, c=0`  menutup lot FIFO; gross bps = (nilai keluar - nilai masuk) / nilai masuk
  - lot yang masih terbuka pada `as_of` TIDAK dinilai — cuma dilaporkan
  - jual tanpa lot terbuka dihitung `jual_yatim`: itu batas feed, bukan kerugian (mengasumsikannya
    nol akan membuat maker terlihat jelek karena sebab yang bukan dirinya)

Semuanya kronologis dan hanya memakai baris `t <= as_of`, jadi skor boleh diminta pada titik waktu
apa pun dalam riwayat (`--as-of`) — itu yang membuat evaluasi prospektif tidak perlu menunggu besok.

Kolam ditentukan dari **ko-occurrence maker↔token** (>= MIN_EDGE maker yang sama menyentuh kedua
token), bukan dari nama: "kolam degen" dan "kolam major" memisah sendiri, sehingga whale BTC hanya
boleh dipakai untuk keputusan BTC.

Pakai:
    python -X utf8 tools/maker_ledger.py
    python -X utf8 tools/maker_ledger.py --as-of 2026-09-27T00:00:00Z --min-trades 8
Artefak: decisions/maker-scores-<as_of>.json (dengan rows_sha256 supaya bisa dibuktikan ulang)
"""
import argparse
import collections
import hashlib
import io
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FLOW = os.path.join(ROOT, "universe", "wallet-flow.jsonl")
UNIV = os.path.join(ROOT, "universe", "bsc-universe.jsonl")
OUT_DIR = os.path.join(ROOT, "decisions")

RT_COST_BPS = 59.0        # satu-satunya round-trip yang pernah kami UKUR (venue sendiri; forge test
                          # + fill nyata di 97). Bukan 20 bps asumsi lama.
MIN_EDGE = 4              # maker bersama minimum agar dua token dianggap satu kolam
                          # (2 membuat graf kecil-dunia: satu kolam menyerap 378 simbol)
MIN_TRADES = 8            # di bawah ini tidak boleh ada label "terampil"

if not os.path.isfile(FLOW):
    raise SystemExit(f"tidak ada {FLOW} - jalankan universe/record_wallet_flow.py dulu")


def last_snapshot_utc():
    last = None
    if os.path.isfile(UNIV):
        for line in io.open(UNIV, encoding="utf-8", errors="replace"):
            if line.strip():
                last = line.strip()
    try:
        return json.loads(last or "{}").get("snapshot_utc")
    except json.JSONDecodeError:
        return None


def to_epoch(s):
    return time.mktime(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ")) - time.timezone


def load_tx():
    rows = []
    for line in io.open(FLOW, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("k") != "tx":
            continue
        try:
            px = float(r.get("p") or 0.0)
            usd = float(r.get("u") or 0.0)
        except (TypeError, ValueError):
            continue
        if px <= 0 or usd <= 0 or not r.get("m") or not r.get("y"):
            continue
        rows.append({"t": int(r.get("t") or 0), "m": str(r["m"]).lower(), "y": str(r["y"]).upper(),
                     "tk": str(r.get("tk") or "").lower(), "usd": usd, "px": px,
                     "buy": bool(r.get("b")), "open": bool(r.get("c")),
                     "h": str(r.get("h") or ""), "tags": tuple(sorted(r.get("g") or [])[:3])})
    # urutan deterministik: waktu lalu hash, bukan urutan halaman API
    rows.sort(key=lambda x: (x["t"], x["h"], x["m"], x["y"]))
    return rows


def price_map(rows, as_of):
    """Harga terakhir yang KAMI LIHAT per simbol pada/before as_of (dari baris px dan tx).

    Dipakai untuk menandai-tauposisi yang belum tertutup. Tanpanya, skor hanya menghitung flip yang
    selesai - dan flip yang selesai adalah pemenang: token yang ruget sebelum maker-nya menjual
    tidak punya baris jual sama sekali, jadi ia hilang dari sampel, bukan dinilai rugi.
    """
    last = {}
    for r in rows:
        if r["t"] > as_of:
            break
        px = r.get("px") or 0.0
        if px > 0:
            last[r.get("tk") or r["y"]] = (px, r["t"])
    return last


def closed_trades(rows, as_of, last_px):
    lots = collections.defaultdict(collections.deque)
    trades, yatim, lain = [], 0, 0
    for r in rows:
        if r["t"] > as_of:
            break
        key = (r["m"], r["tk"] or r["y"])
        qty = r["usd"] / r["px"]
        if r["buy"] and r["open"]:
            lots[key].append([qty, r["px"], r["t"]])
            continue
        if (not r["buy"]) and (not r["open"]):
            dq, left, filled, entry_val = lots[key], qty, 0.0, 0.0
            while left > 1e-12 and dq:
                take = min(left, dq[0][0])
                entry_val += take * dq[0][1]
                filled += take
                dq[0][0] -= take
                left -= take
                if dq[0][0] <= 1e-12:
                    dq.popleft()
            if filled <= 1e-12:
                yatim += 1
                continue
            exit_val = filled * r["px"]
            bps = 10000.0 * (exit_val - entry_val) / entry_val if entry_val > 0 else 0.0
            trades.append({"maker": key[0], "token": key[1], "symbol": r["y"], "usd": round(entry_val, 2),
                           "entry_px": round(entry_val / filled, 10), "exit_px": r["px"],
                           "gross_bps": round(bps, 2), "net_bps": round(bps - RT_COST_BPS, 2),
                           "open_t": r["t"], "close_t": r["t"], "mtm": False})
            continue
        lain += 1

    # yang belum tertutup: ditandai-taup dengan harga TERAKHIR yang terlihat, BUKAN dibuang
    mtm = 0
    sym_of = {(r.get("tk") or r["y"]): r["y"] for r in rows}
    for (m, tok), dq in lots.items():
        for qty, px, t_open in dq:
            if qty <= 1e-12 or px <= 0:
                continue
            ref = last_px.get(tok)
            bps = 10000.0 * (ref[0] - px) / px if ref else 0.0
            trades.append({"maker": m, "token": tok, "symbol": sym_of.get(tok, tok),
                           "usd": round(qty * px, 2),
                           "entry_px": px, "exit_px": (ref[0] if ref else px),
                           "gross_bps": round(bps, 2), "net_bps": round(bps - RT_COST_BPS, 2),
                           "open_t": t_open, "close_t": (ref[1] if ref else t_open), "mtm": True})
            mtm += 1
    return trades, sum(len(v) for v in lots.values()), yatim, lain, mtm


def pools_from(rows, as_of):
    """Kolam dari ko-occurrence ALAMAT token (bukan ticker) antar maker.

    Dua pelajaran yang tertanam di sini:
      - kunci harus `tk`: ticker boleh dipakai dua token berbeda, dan menggabungkannya membuat
        satu "kolam" menyerap segalanya (versi pertama melaporkan 2 kolam, salah satunya 378 simbol)
      - komponen union-find di graf yang padat itu kecil-dunia, bukan kelompok yang berguna;
        karena itu ambang edge dinaikkan dan jumlah kolam + ukuran terbesar ikut dilaporkan,
        supaya pembaca tahu kalau grafnya runtuh jadi satu gumpalan.
    """
    tok_of = collections.defaultdict(set)
    for r in rows:
        if r["t"] > as_of:
            break
        tok_of[r["m"]].add(r.get("tk") or r["y"])
    pair = collections.Counter()
    for m in sorted(tok_of):
        ss = sorted(tok_of[m])
        for i in range(len(ss)):
            for j in range(i + 1, len(ss)):
                pair[(ss[i], ss[j])] += 1
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for (a, b), n in sorted(pair.items()):
        if n >= MIN_EDGE:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra
    groups = collections.defaultdict(set)
    for t in sorted(parent):
        groups[find(t)].add(t)
    gross = collections.Counter()
    nama = {}
    for r in rows:
        if r["t"] > as_of:
            break
        gross[r.get("tk") or r["y"]] += r["usd"]
        nama[r.get("tk") or r["y"]] = r["y"]
    lead_of, size = {}, {}
    for root in sorted(groups, key=lambda r: str(r)):
        toks = sorted(groups[root])
        lead = max(toks, key=lambda s: (gross[s], s))
        size[nama.get(lead, lead[:10])] = len(toks)
        for s in toks:
            lead_of[s] = nama.get(lead, lead[:10])
    return lead_of, size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--min-trades", type=int, default=MIN_TRADES)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    as_of_s = a.as_of or last_snapshot_utc()
    if not as_of_s:
        raise SystemExit("as_of tidak diketahui (snapshot kosong, --as-of tidak diisi)")
    as_of = to_epoch(as_of_s)
    rows = load_tx()
    last_px = price_map(rows, as_of)
    trades, unclosed, yatim, lain, mtm = closed_trades(rows, as_of, last_px)

    # Rem sehat sebelum satu pun angka dipercaya: kalau distribusi |net|-nya tidak masuk akal,
    # mean apa pun di bawahnya adalah artefak - bukan hasil. Ini yang menyelamatkan pembacaan 27 Sep:
    # satu maker keluar +3,5 JUTA bps dan penyebabnya kunci lot berupa ticker, bukan alamat token.
    ab = sorted(abs(x["net_bps"]) for x in trades) or [0.0]
    gila = sum(1 for v in ab if v > 2000.0)
    sanity = {"median_abs_bps": round(ab[len(ab) // 2], 1),
              "p90_abs_bps": round(ab[int(len(ab) * 0.9)], 1),
              "maks_abs_bps": round(ab[-1], 1), "lot_net_lebih_2000bps": gila,
              "persen_lot_gila": round(100.0 * gila / max(len(ab), 1), 1)}

    tags = collections.defaultdict(collections.Counter)
    for r in rows:
        if r["t"] > as_of:
            break
        for g in r["tags"]:
            tags[r["m"]][g] += 1

    by_maker = collections.defaultdict(list)
    for t in trades:
        by_maker[t["maker"]].append(t)
    lead_of, pool_size = pools_from(rows, as_of)

    scored = []
    for m, ts in by_maker.items():
        n = len(ts)
        tc = [x for x in ts if not x["mtm"]]      # hanya flip yang benar-benar selesai
        nc = len(tc)
        net = sum(x["net_bps"] for x in ts) / n
        gross = sum(x["gross_bps"] for x in ts) / n
        net_c = (sum(x["net_bps"] for x in tc) / nc) if nc else None
        hit = 100.0 * sum(1 for x in ts if x["net_bps"] > 0) / n
        sd = (sum((x["net_bps"] - net) ** 2 for x in ts) / max(n - 1, 1)) ** 0.5
        pool = collections.Counter(lead_of.get(x.get("token"), x["symbol"]) for x in ts)
        scored.append({"maker": m, "trades": n, "trades_selesai": nc, "trades_mtm": n - nc,
                       "gross_mean_bps": round(gross, 1), "net_mean_bps": round(net, 1),
                       "net_mean_selesai_bps": (round(net_c, 1) if net_c is not None else None),
                       "net_hit_pct": round(hit, 1),
                       "net_sd_bps": round(sd, 1), "usd": round(sum(x["usd"] for x in ts), 0),
                       "pool": max(sorted(pool), key=lambda k: (pool[k], k)),
                       "tag_hari_ini": sorted(tags.get(m, {})),
                       "layak_label": n >= a.min_trades})
    scored.sort(key=lambda s: (-s["trades"], -s["net_mean_bps"], s["maker"]))

    lab = [s for s in scored if s["layak_label"]]
    pos = [s for s in lab if s["net_mean_bps"] > 0]
    pos_c = [s for s in lab if (s["net_mean_selesai_bps"] or -1) > 0]
    tn = sum(s["trades"] for s in scored) or 1
    allm = sum(s["net_mean_bps"] * s["trades"] for s in scored) / tn
    tc_ = [(s["net_mean_selesai_bps"], s["trades_selesai"]) for s in scored
           if s["net_mean_selesai_bps"] is not None and s["trades_selesai"]]
    dn = sum(k for _, k in tc_) or 1
    onlyc = sum(v * k for v, k in tc_) / dn
    out = {"as_of_utc": as_of_s, "dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "rt_cost_bps": RT_COST_BPS, "min_trades_untuk_label": a.min_trades,
           "tx_dibaca": len(rows), "trade_tertam": len(trades), "lot_ditanda_taup": mtm,
           "jual_yatim": yatim, "baris_lain_dilewati": lain, "maker_bertanda": len(by_maker),
           "maker_layak_label": len(lab), "maker_net_positif_semua": len(pos),
           "maker_net_positif_hanya_selesai": len(pos_c),
           "net_timbang_bps_semua": round(allm, 1), "net_timbang_bps_selesai": round(onlyc, 1),
           "kolam": len(pool_size),
           "kolam_terbanyak_simbol": sorted(pool_size.items(), key=lambda kv: (-kv[1], kv[0]))[:6],
           "rows": scored}
    out["rows_sha256"] = "0x" + hashlib.sha256(
        json.dumps(scored, sort_keys=True).encode()).hexdigest()

    if a.json:
        print(json.dumps(out, indent=1, sort_keys=True, ensure_ascii=False))
    else:
        print(f"as_of {as_of_s} | ongkos round-trip yang dipakai {RT_COST_BPS} bps (terukur, bukan asumsi)")
        print(f"tx dibaca {len(rows):,} | lot dibuka yang belum ketutup (ditandai-taup) {mtm:,} | "
              f"jual yatim {yatim:,} | baris lain dilewati {lain:,}")
        print(f"maker dengan >=1 lot: {len(by_maker)} | layak label (n>={a.min_trades}): {len(lab)}")
        print(f"\n  REM SEHAT distribusi |net| per lot: median {sanity['median_abs_bps']:,.1f} bps | "
              f"p90 {sanity['p90_abs_bps']:,.1f} | maks {sanity['maks_abs_bps']:,.1f} | "
              f"lot >2000 bps: {sanity['lot_net_lebih_2000bps']:,} ({sanity['persen_lot_gila']} %)")
        if sanity["persen_lot_gila"] > 5 or sanity["median_abs_bps"] > 2000:
            print("     ^^ distribusi ini TIDAK masuk akal sebagai angka pasar. Mean di bawah jangan")
            print("        dikutip: perbaiki mekanikanya (kunci token, satuan harga) lebih dulu.")
        print(f"\n  DUA BACAAN YANG TIDAK SAMA:")
        print(f"    hanya flip selesai : net tertimbang {onlyc:+8.1f} bps | "
              f"{len(pos_c)}/{len(lab)} maker positif  <- BIAS: yang tidak selesai tidak dihitung")
        print(f"    semua lot (MTM)    : net tertimbang {allm:+8.1f} bps | "
              f"{len(pos)}/{len(lab)} maker positif  <- yang dipakai")
        print(f"\n  {'maker':44} {'n':>4} {'selesai':>7} {'gross':>9} {'NET':>9} {'NET(selesai)':>12} "
              f"{'hit%':>6} kolam / tag hari ini")
        for s in lab[:20]:
            ns = s["net_mean_selesai_bps"]
            print(f"  {s['maker']:44} {s['trades']:4} {s['trades_selesai']:7} {s['gross_mean_bps']:+9.1f} "
                  f"{s['net_mean_bps']:+9.1f} {(('%+.1f' % ns) if ns is not None else '-'):>12} "
                  f"{s['net_hit_pct']:6.1f} {s['pool'][:10]:10} {','.join(s['tag_hari_ini'])[:22]}")
        print("\n  Yang TIDAK boleh disimpulkan dari tabel ini:")
        print("  - populasinya maker yang MUNCUL di feed smart-money: survivorship di alat ukurnya")
        print("    sendiri, dan ini bukan sampel acak pasar BSC.")
        print("  - MTM memakai harga TERAKHIR yang kami lihat, jadi rug yang hilang dari feed")
        print("    sebelum harga jatuh masih terlihat lebih baik daripada kenyataan.")
        print("  - 'jual yatim' dan kolom NET(selesai) yang '-' itu batas jendela feed, bukan rugi.")

    os.makedirs(OUT_DIR, exist_ok=True)
    p = os.path.join(OUT_DIR, "maker-scores-%s.json" % as_of_s.replace(":", "").replace("-", ""))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print(f"\nartefak: decisions/{os.path.basename(p)}  rows_sha256={out['rows_sha256'][:18]}…")


if __name__ == "__main__":
    main()
