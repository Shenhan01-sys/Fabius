"""Perekam harga pantau (P17) — supaya kita bisa MELIHAT AKHIR dari posisi yang kita catat.

Masalah yang ini selesaikan, terukur 28 Sep oleh `tools/flow_cluster_test.py`:
  - `px` kami hanya ada selama token masih masuk daftar panas GMGN; median jendela harganya
    **27 menit**. Untuk horison 60 menit, **80,6 %** kejadian tidak punya harga keluar.
  - akibatnya semua angka "whale untung/rugi" di repo ini dihitung di atas 19 % sampel yang
    MASIH KELIHATAN akhirnya - yaitu sampel yang dipilih oleh nasib, bukan oleh kita.

Harga `px` yang ada sekarang gratis (ikut terbawa di payload trending GMGN). Yang butuh panggilan
tersendiri hanya memperpanjang pantauan, dan itu murah: satu panggilan DexScreener melayani
**30 alamat** (terukur 401 ms), dan daftar pantau 2 jam berisi **136 token = 5 panggilan per
siklus 202 detik = 89 panggilan/jam**. Untuk 24 jam: 927 token / 31 panggilan / 552 per jam -
enam kali lebih mahal dan isinya sebagian besar token mati. Karena itu jendela bakunya **120 menit**
(bisa diubah `--watch-min`), bukan 24 jam: persis sepanjang horison yang kita uji (30-120 menit).

Satu baris per token per siklus:
    {"k":"wp","t":<detik>,"tk":<alamat>,"y":<simbol>,"p":<harga USD>,"liq_usd":...,
     "fdv":...,"vol_h1":...,"buys_h1":...,"sells_h1":...,"pair":<alamat pool>,
     "src":"dexscreener","schema":1}
`buys_h1`/`sells_h1` ikut disimpan: itu bukti transaksi nyata dari venue, bukan label vendor -
bahan untuk aspek kedua dari analisis (lihat `tools/evidence_stack.py`).

Pakai:  python -u universe/record_watch_prices.py --report   # hitung saja, jangan menulis
       python -u universe/record_watch_prices.py            # rekam satu siklus
       python -u universe/record_watch_prices.py --self-test # periksa satuan + pengelompokan
Read-only: GET ke endpoint publik tanpa kunci. Tidak pernah mengirim order.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FLOW = os.path.join(HERE, "wallet-flow.jsonl")
OUT = os.path.join(HERE, "watch-prices.jsonl")
MANIFEST = os.path.join(HERE, "watch-prices-manifest.txt")
SCHEMA = 1
BATCH = 30                      # DexScreener menerima daftar alamat dalam satu panggilan
UA = {"User-Agent": "Mozilla/5.0 (compatible; fabius-watch-recorder/1.0)"}


def sha_line(line):
    return "0x" + hashlib.sha256(line.encode("utf-8")).hexdigest()


def watch_tokens(watch_min, until=None):
    """Token yang ada BELI-nya dalam `watch_min` terakhir, dari rekaman ⑦ kami.

    Acuan waktu = **stempel terakhir berkas itu sendiri**, bukan jam mesin. Alasannya sudah
    dibayar dua kali di vault ini (lihat `Concepts/Stale Local Copy`): disk lokal bisa tertinggal
    ratusan commit, dan memotong dengan `time.time()` di mesin yang basi menghasilkan daftar kosong
    yang terlihat seperti "tidak ada yang perlu dipantau".
    """
    hit, t_max = {}, 0
    if not os.path.exists(FLOW):
        raise SystemExit("tidak ada %s - jalankan record_wallet_flow.py dulu" % FLOW)
    for ln in io.open(FLOW, encoding="utf-8", errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        d = json.loads(ln)
        if d.get("k") != "tx" or not d.get("b"):
            continue
        t = int(d.get("t") or 0)
        tk = str(d.get("tk") or "").lower()
        if not t or not tk:
            continue
        t_max = max(t_max, t)
        hit.setdefault(tk, []).append(t)
    ref = t_max
    # waktu di berkas ini DETIK; kalau ada yang milidetik, pemotongan di bawah salah diam-diam
    assert ref < 4e9, "stempel waktu di wallet-flow.jsonl bukan detik: %s" % ref
    cut = ref - watch_min * 60
    inwin = [(tk, len([t for t in ts if t >= cut])) for tk, ts in hit.items()]
    out = sorted([(tk, c) for tk, c in inwin if c > 0], key=lambda kv: (-kv[1], kv[0]))
    return out, ref


def fetch_batch(addrs):
    url = "https://api.dexscreener.com/tokens/v1/bsc/" + ",".join(addrs)
    for tries in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return r.status, json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503):
                time.sleep(2.0 * (tries + 1))
                continue
            return e.code, []
        except Exception:
            time.sleep(2.0 * (tries + 1))
    return "gagal", []


def best_pair(rows, want):
    """Satu objek per token: pool dengan likuiditas USD terbesar."""
    by = {}
    for p in rows or []:
        bt = (p.get("baseToken") or {}).get("address")
        if not bt:
            continue
        bt = bt.lower()
        if bt not in want:
            continue
        liq = float(((p.get("liquidity") or {}).get("usd")) or 0.0)
        if bt not in by or liq > by[bt][0]:
            by[bt] = (liq, p)
    return by


def tanpa_harga(t_now, chunk, got):
    """Token yang BALAS tapi `priceUsd`-nya nol/buruk: bukan harga, bukan juga tidak ada pair.

    Keadaan ketiga ini harus punya nama, kalau tidak ia menghilang di antara dua pencacahan dan
    laporan 'kehilangan' jadi angka yang enak dibaca tapi tidak tertutup.
    """
    out = []
    for tk in sorted(set(chunk) & set(got)):
        try:
            px = float((got[tk][1] or {}).get("priceUsd") or 0.0)
        except (TypeError, ValueError):
            px = 0.0
        if px <= 0:
            out.append({"k": "wp0", "t": t_now, "tk": tk, "why": "answered-no-price",
                        "http": 200, "schema": SCHEMA})
    return out


def catatan_ketiadaan(t_now, chunk, got, code):
    """Baris `wp0` HANYA untuk batch yang balas 200.

    Diisolasi jadi fungsi murni supaya invarian ini bisa diuji tanpa menyentuh jaringan: kegagalan
    pemanggilan kami tidak boleh berubah menjadi kematian pool. (Kelas kesalahan yang sama, versi
    tes: penolakan yang 'lulus' karena perintahnya salah ketik.)
    """
    if code != 200:
        return []
    return [{"k": "wp0", "t": t_now, "tk": tk, "why": "answered-no-pair", "http": code,
             "schema": SCHEMA} for tk in sorted(set(chunk) - set(got))]


def build_rows(t_now, toks, max_batches, sleep_s=0.4):
    """Kembalikan (baris, tidak_terjawab, panggilan, hilang_tercatat, batch_gagal)."""
    rows, unresolved, calls = [], set(toks), 0
    hilang, butek = [], 0
    addr_list = sorted(toks)
    for i in range(0, len(addr_list), BATCH):
        if calls >= max_batches:
            break
        chunk = addr_list[i:i + BATCH]
        code, data = fetch_batch(chunk)
        calls += 1
        if code != 200:
            # BUKAN bukti ketiadaan: kegagalan kami bukan kematian pool.
            butek += len(chunk)
            print("  ! batch %d -> %s (tidak dicatat sebagai kehilangan)" % (calls, code))
            continue
        got = best_pair(data, set(chunk))
        hilang.extend(catatan_ketiadaan(t_now, chunk, got, code))
        tanpa = tanpa_harga(t_now, chunk, got)
        for r in tanpa:
            if r["tk"] in unresolved:
                unresolved.discard(r["tk"])
        hilang.extend(tanpa)
        for tk, (_liq, p) in sorted(got.items()):
            tx = (p.get("txns") or {}).get("h1") or {}
            try:
                px = float(p.get("priceUsd") or 0.0)
            except (TypeError, ValueError):
                px = 0.0
            if px <= 0:
                unresolved.discard(tk)      # dicatat oleh tanpa_harga()
                continue
            rows.append({"k": "wp", "t": t_now, "tk": tk, "y": str(
                (p.get("baseToken") or {}).get("symbol") or "")[:16],
                "p": px,
                "liq_usd": float(((p.get("liquidity") or {}).get("usd")) or 0.0),
                "fdv": float(p.get("fdv") or 0.0),
                "vol_h1": float((p.get("volume") or {}).get("h1") or 0.0),
                "buys_h1": int(tx.get("buys") or 0), "sells_h1": int(tx.get("sells") or 0),
                "pair": str(p.get("pairAddress") or "").lower(), "src": "dexscreener",
                "schema": SCHEMA})
            unresolved.discard(tk)
        time.sleep(sleep_s)
    rows.extend(hilang)
    rows.sort(key=lambda r: (r["t"], r.get("tk") or ""))
    return rows, sorted(unresolved), calls, len(hilang), butek


def write_manifest(t_now):
    stats = {}
    total = 0
    if os.path.exists(OUT):
        for ln in io.open(OUT, encoding="utf-8"):
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            total += 1
            d = json.loads(ln)
            s = stats.setdefault("all", {"n": 0, "t0": None, "t1": None, "tok": set(), "sha": None})
            s["n"] += 1
            s["tok"].add(d.get("tk"))
            s["t0"] = d["t"] if s["t0"] is None else min(s["t0"], d["t"])
            s["t1"] = d["t"] if s["t1"] is None else max(s["t1"], d["t"])
            s["sha"] = sha_line(ln)
    with io.open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# watch-prices-manifest.txt - ditulis %s UTC | %d baris | schema %d\n"
                 % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t_now)), total, SCHEMA))
        fh.write("# harga pantau per token (DexScreener, batch-30, tanpa kunci) - penutup sensor\n")
        s = stats.get("all")
        if s:
            fh.write("wp  baris=%d token_unik=%d rentang=%.1f jam | sha_last=%s\n"
                     % (s["n"], len(s["tok"]), (s["t1"] - s["t0"]) / 3600.0, (s["sha"] or "")[:14]))
        else:
            fh.write("wp  (belum ada baris)\n")


def self_test():
    """Satuan + pengelompokan pair diverifikasi tanpa jaringan."""
    t = 1790000000
    assert t < 4e9, "stempel uji harus detik"
    fake = [{"baseToken": {"address": "0xAAA", "symbol": "X"}, "priceUsd": "0.5",
             "liquidity": {"usd": "100"}, "fdv": 1e6, "volume": {"h1": 500},
             "txns": {"h1": {"buys": 7, "sells": 3}}, "pairAddress": "0xp1"},
            {"baseToken": {"address": "0xaaa", "symbol": "X"}, "priceUsd": "0.6",
             "liquidity": {"usd": "900"}, "fdv": 2e6, "volume": {"h1": 90},
             "txns": {"h1": {"buys": 1, "sells": 2}}, "pairAddress": "0xp2"}]
    got = best_pair(fake, {"0xaaa"})
    assert list(got) == ["0xaaa"] and got["0xaaa"][0] == 900.0, "harus ambil pool paling likuid"
    assert got["0xaaa"][1]["priceUsd"] == "0.6", "salah pair"
    toks, ref = {"0xaaa"}, t
    assert ref < 4e9
    # aturan ketiadaan: 200 = data, bukan-200 = JANGAN catat kematian
    a = catatan_ketiadaan(t, ["0xaaa", "0xbbb"], {"0xaaa": (1.0, {})}, 200)
    assert len(a) == 1 and a[0]["tk"] == "0xbbb" and a[0]["k"] == "wp0", a
    for kode in (429, 403, 0, 500):
        assert catatan_ketiadaan(t, ["0xaaa", "0xbbb"], {}, kode) == [], kode
    # keadaan ketiga: balasan tanpa harga harus tetap tercatat, bukan lenyap di antara cacahan
    buruk = {"0xccc": (0.0, {"priceUsd": "0"})}
    b = tanpa_harga(t, ["0xccc"], buruk)
    assert len(b) == 1 and b[0]["why"] == "answered-no-price", b
    assert tanpa_harga(t, ["0xccc"], {"0xccc": (5.0, {"priceUsd": "0.1"})}) == []
    print("self-test LOLOS (detik, satu baris per token, pair terlikuid menang, ketiadaan-hanya-bila-200)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch-min", type=int, default=120)
    ap.add_argument("--max-batches", type=int, default=8)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return

    (toks, t_ref) = watch_tokens(a.watch_min)
    addrs = [tk for tk, _ in toks]
    print("pantau %d menit -> %d token | %d batch dibutuhkan | batas batch %d"
          % (a.watch_min, len(addrs), -(-len(addrs) // BATCH), a.max_batches))
    rows, unresolved, calls, n_hilang, n_butek = build_rows(int(time.time()), set(addrs),
                                                            a.max_batches)
    harga = sorted(r["p"] for r in rows if r["k"] == "wp")
    print("panggilan %d | harga %d | kehilangan tercatat %d | batch gagal %d | TIDAK terjawab %d | harga median %.3e"
          % (calls, len(harga), n_hilang, n_butek, len(unresolved),
             (harga[len(harga) // 2] if harga else 0.0)))
    if unresolved[:5]:
        print("  contoh tidak terjawab: " + ", ".join(x[:10] for x in unresolved[:5]))
    if not harga:
        print("tidak ada harga - tidak menulis (baris kehilangan juga "
              "ditunda: tanpa satu pun harga, kita tidak tahu bedanya 'mati' dan 'buta').")
        return
    if a.report:
        print("(--report: %d baris TIDAK ditulis; contoh: %s)"
              % (len(rows), json.dumps(rows[0], ensure_ascii=False)[:200]))
        return

    seen = set()
    if os.path.exists(OUT):
        for ln in io.open(OUT, encoding="utf-8"):
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                d = json.loads(ln)
                seen.add((d.get("tk"), d.get("t")))
    with io.open(OUT, "a", encoding="utf-8", newline="\n") as fh:
        wrote = 0
        for r in rows:
            if (r["tk"], r["t"]) in seen:
                continue
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")
            wrote += 1
    write_manifest(int(time.time()))
    print("ditulis %d baris ke universe/%s" % (wrote, os.path.basename(OUT)))


if __name__ == "__main__":
    main()
