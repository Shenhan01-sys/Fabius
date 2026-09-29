"""Kebijakan KELUAR Fabius - perilaku kedua agen, diukur di POSISI YANG SAMA lebih dulu.

Kenapa alat ini ada (28-29 Sep 2026): semua pencarian "kapan boleh masuk" gagal. E7 top-k dalam
satu siklus (10 fitur, `tools/topk_test.py`): TIDAK ADA yang mengalahkan acak-siklus, dan di substrate
ticker `wp` harapan pool justru NEGATIF (-183,7 bps setelah ongkos). Yang bertahan adalah sisi
keluar, dan itu diukur pada posisi yang sama, bukan dua populasi berbeda:

    E8 (decisions/topk-test-20260929T045209Z.json): keluar SAAT kerumunan beli datang
      vs menahan sampai horison 30 menit
      posisi dipantau 122 | keluar dini menolong 69 | merugikan 45
      median delta +116,5 bps | mean winso delta +316,6 bps
      (persentil 5-95 = [-2.000; +2.000] - ekornya tebal di dua arah; jangan baca ini sebagai
       pendapatan tetap, ini perbaikan rata-rata pada pool yang sangat miring)

Aturan yang dipasang di sini (hanya data <= sekarang, tidak ada intip-masa-depan):
  CLOSE bila  >=2 maker BERBEDA membeli token ini dalam 15 menit terakhir  (kerumunan datang), ATAU
               harga ticker `wp` kini >= puncak 60 menit pertama posisi (kita di atas yang kita beli
               dan pasar baru saja membuat puncaknya sendiri), ATAU
               harga kini >= +X% di atas masuk (jaring: kunci profit tanpa menunggu kerumunan);
  HOLD  bila tidak ada satu pun di atas;
  TAK ADA DATA bila `wp` token ini lebih tua dari 15 menit - dan itu TIDAK diperlakukan seperti
  "bersih/hold" yang aman: ia dilaporkan apa adanya (aturan [[Concepts/Unmeasured Is Not Clean]]).

Alat ini TIDAK mengirim order. Keputusan menutup dikirim manusia lewat
`python -X utf8 tools/execute_live.py --close --symbol <SYMBOL>`; kami hanya mencetak alasan yang
bisa diaudit + menulis baris keputusan ke `decisions/exit-policy.jsonl` supaya "kenapa kami keluar"
punya tanggal, bukan narasi setelahnya.

Pakai:  python -X utf8 tools/exit_policy.py --token 0x... --entry-t <epoch> --entry-px <harga>
       python -X utf8 tools/exit_policy.py --open            # semua slot paper yang masih terbuka
       python -X utf8 tools/exit_policy.py --self-test
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import flow_cluster_test as FC  # noqa: E402
import prices as PR  # noqa: E402

MIN = 60
KLUSTER_MENIT = 15
SEGAR_WP_MENIT = 15
AMBIL_PUNCAK_MENIT = 60
KUNCI_PROFIT_PCT = 4.0          # jaring: +4% dari masuk langsung dikunci
LOG = os.path.join(ROOT, "decisions", "exit-policy.jsonl")


def wp_series():
    return PR.load(os.path.join(ROOT, "universe", "watch-prices.jsonl"), "wp")["rows"]


def flow_rows():
    out = {}
    for ln in io.open(os.path.join(ROOT, "universe", "wallet-flow.jsonl"), encoding="utf-8",
                      errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("k") not in ("tx", "txc"):
            continue
        tk = str(d.get("tk") or "").lower()
        t = int(d.get("t") or 0)
        if tk and t:
            out.setdefault(tk, []).append((t, str(d.get("m") or "").lower(), bool(d.get("b"))))
    for tk in out:
        out[tk].sort()
    return out


def putuskan(token, entry_t, entry_px, sekarang, wp, flow):
    tk = str(token or "").lower()
    s = wp.get(tk) or []
    st = [x[0] for x in s]
    i = max((k for k in range(len(s)) if s[k][0] <= sekarang), default=-1)
    alasan, aksi = [], "HOLD"
    harga_kini = s[i][1] if i >= 0 else None
    umur_wp = (sekarang - s[i][0]) if i >= 0 else None
    if harga_kini is None or umur_wp > SEGAR_WP_MENIT * MIN:
        return {"aksi": "TAK ADA DATA",
                "alasan": ["`wp` terakhir %s" % ("absen" if harga_kini is None else
                                                 "%d menit lalu" % (umur_wp // 60))],
                "harga_kini": harga_kini, "umur_wp_menit": None if umur_wp is None
                else round(umur_wp / 60.0, 1)}
    # 1) kerumunan beli datang
    jend = [r for r in flow.get(tk, []) if sekarang - KLUSTER_MENIT * MIN <= r[0] <= sekarang]
    maker_beli = {m for t, m, b in jend if b and m}
    if len(maker_beli) >= 2:
        aksi = "CLOSE"
        alasan.append("%d maker berbeda membeli dalam %d m terakhir" % (len(maker_beli),
                                                                       KLUSTER_MENIT))
    # 2) kita di atas puncak 60 m pertama posisi
    awal = [p for t, p in s if entry_t <= t <= entry_t + AMBIL_PUNCAK_MENIT * MIN]
    if len(awal) >= 3:
        pk = max(awal)
        if harga_kini >= pk:
            aksi = "CLOSE"
            alasan.append("harga kini %.6g >= puncak %d m pertama posisi %.6g" % (harga_kini,
                                                                                   AMBIL_PUNCAK_MENIT,
                                                                                   pk))
    # 3) jaring kunci profit
    if entry_px and harga_kini >= entry_px * (1 + KUNCI_PROFIT_PCT / 100.0):
        aksi = "CLOSE"
        alasan.append("+%.1f%% dari harga masuk (jaring kunci profit)" % KUNCI_PROFIT_PCT)
    if not alasan:
        alasan.append("tidak ada pemicu: kerumunan=%d maker, umur wp %.1f m" % (len(maker_beli),
                                                                                umur_wp / 60.0))
    selisih = round(10000.0 * (harga_kini - entry_px) / entry_px, 1) if entry_px else None
    return {"aksi": aksi, "alasan": alasan, "harga_kini": harga_kini, "maker_beli_15m": len(maker_beli),
            "umur_wp_menit": round(umur_wp / 60.0, 1), "selisih_bps_sekarang": selisih}


def slot_terbuka():
    if not os.path.exists(os.path.join(ROOT, "decisions", "paper-book-positions.jsonl")):
        return []
    out = []
    for ln in io.open(os.path.join(ROOT, "decisions", "paper-book-positions.jsonl"),
                     encoding="utf-8", errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        d = json.load(io.StringIO(ln))
        if d.get("status") == "dinilai" and d.get("mode") == "PAPER":
            out.append(d)
    return out


def self_test():
    """Pemicu harus hidup karena ATURANNYA, bukan karena kebetulan ada data."""
    now = 1_800_000_000
    wp = {"0xt": [(now - 60, 1.0), (now - 30, 1.02), (now, 1.05)]}
    fl = {"0xt": [(now - 100, "0xa", True), (now - 50, "0xb", True)]}
    r = putuskan("0xt", now - 600, 1.0, now, wp, fl)
    assert r["aksi"] == "CLOSE" and any("maker berbeda" in a for a in r["alasan"]), r
    fl2 = {"0xt": [(now - 100, "0xa", True)]}
    r2 = putuskan("0xt", now - 600, 1.0, now, wp, fl2)
    assert r2["aksi"] == "CLOSE" and any("puncak" in a for a in r2["alasan"]), r2
    # jaring diuji SENDIRIAN: harga kini +5% dari masuk tapi DI BAWAH puncak 60 m pertama, dan
    # tidak ada kerumunan. Versi pertama test ini memakai harga yang membuat pemicu puncak menang
    # duluan, jadi "jaring" tidak pernah benar-benar diuji.
    wp_jaring = {"0xt": [(now - 500, 1.10), (now - 60, 1.10), (now, 1.05)]}
    r3 = putuskan("0xt", now - 600, 1.00, now, wp_jaring, fl2)
    assert r3["aksi"] == "CLOSE" and any("jaring" in a for a in r3["alasan"]), r3
    assert not any("puncak" in a for a in r3["alasan"]), r3
    assert not any("maker berbeda" in a for a in r3["alasan"]), r3
    r4 = putuskan("0xt", now - 600, 1.0, now, {}, fl2)
    assert r4["aksi"] == "TAK ADA DATA", r4
    r5 = putuskan("0xt", now - 600, 1.0, now, {"0xt": [(now - 40 * MIN, 1.0)]}, fl2)
    assert r5["aksi"] == "TAK ADA DATA", r5
    print("self-test keluar OK: kerumunan / puncak / jaring / tanpa-data (wp absen & basi)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default=None)
    ap.add_argument("--entry-t", type=int, default=None)
    ap.add_argument("--entry-px", type=float, default=None)
    ap.add_argument("--open", action="store_true", help="nilai semua slot paper yang masih terbuka")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--now", type=int, default=None)
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return
    sekarang = a.now or int(time.time())
    wp, fl = wp_series(), flow_rows()
    baris = []
    if a.open:
        for d in slot_terbuka():
            # `calendar.timegm`, BUKAN `time.mktime`: jam yang mem-parse stempel UTC sebagai waktu
            # lokal meleset +7 jam di mesin ini - kelas kesalahan yang sudah tercatat di vault.
            t0 = calendar.timegm(time.strptime(d["open_utc"], "%Y-%m-%dT%H:%M:%SZ"))
            r = putuskan(d["tk"], t0, d.get("entry_px"), sekarang, wp, fl)
            r.update({"slot_id": d["slot_id"], "sumber": "paper", "entry_utc": d["open_utc"]})
            baris.append(r)
            print("  %s %-11s %s" % (d["slot_id"][:8], d["tk"][:10],
                                     "%-11s %s" % (r["aksi"], "; ".join(r["alasan"])[:96])))
        print("slot dinilai: %d | CLOSE %d | HOLD %d | TAK ADA DATA %d"
              % (len(baris), sum(1 for x in baris if x["aksi"] == "CLOSE"),
                 sum(1 for x in baris if x["aksi"] == "HOLD"),
                 sum(1 for x in baris if x["aksi"] == "TAK ADA DATA")))
    else:
        if not (a.token and a.entry_t and a.entry_px):
            raise SystemExit("perlu --token --entry-t --entry-px, atau --open, atau --self-test")
        r = putuskan(a.token, a.entry_t, a.entry_px, sekarang, wp, fl)
        r.update({"token": a.token.lower(), "entry_t": a.entry_t, "entry_px": a.entry_px})
        baris.append(r)
        print(json.dumps(r, indent=1, sort_keys=True, ensure_ascii=False))
    for r in baris:
        r["dibuat_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(sekarang))
        r["sha_input"] = "0x" + hashlib.sha256(json.dumps(
            {"t": r.get("slot_id") or r.get("token"), "now": sekarang, "aksi": r["aksi"]},
            sort_keys=True).encode()).hexdigest()[:16]
    with io.open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        for r in baris:
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")
    print("keputusan dicatat append-only di decisions/%s (alasan + sha, supaya 'kenapa kami keluar' "
          "tidak jadi narasi setelahnya)" % os.path.basename(LOG))


if __name__ == "__main__":
    main()
