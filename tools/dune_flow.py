"""Ambil ALIRAN dompet per (token, jam) dari Dune - AGREGAT, bukan baris mentah.

Kenapa bentuknya agregat: Dune menagih kredit SEBESAR KOMPUTE yang dipakai, dan yang mahal di
sini adalah MENGIRIM BARIS (kueri 10-hari yang lalu = 51.863 baris = 503 detik). Padahal yang
dibutuhkan alat statistik cuma satu baris per (token, jam): berapa yang beli, berapa yang jual,
berapa dompet unik, berapa USD-nya. Agregasi di sisi server = baris keluar menyusut puluhan kali,
kredit menyusul, dan analisis kita TIDAK berubah sedikit pun.

Kenapa ini worth dibayar sekarang: ini SATU-SATUNYA bidang yang tidak bisa kami dapat dari tempat
lain. GMGN memberi kami arus 8 menit tanpa paging (jadi tidak punya masa lalu), Aster memberi
harga tapi tidak memberi siapa yang beli/jual. Dune memberi kedua-duanya sekaligus untuk 90 hari
ke belakang. Setelah ini ada TIGA jalur yang diuji terhadap hasil: aturan harga (mati, vault/09),
label smart money (mati, vault/09 4c), dan ALIRAN KERUMUNAN - satu-satunya yang belum pernah
dipegang sama sekali.

Peta biaya yang dipakai supaya kredit tidak habis tanpa jejak:
  --window 3   -> kalibrasi: berapa kredit/detik untuk 3 hari (dijalankan dulu, selalu)
  --window 30  -> jendela kerja setelah biaya per-hari terukur
  --window 90  -> hanya kalau 30 hari pertama murah DAN kita benar-benar butuh 90 hari
Cache: data/flow/flow-{window}d.jsonl (di-gitignore; analisis ulang tidak memanggil Dune).

Pakai:  python tools/dune_flow.py --window 3            # kalibrasi biaya
         python tools/dune_flow.py --window 30           # jendela kerja
         python tools/dune_flow.py --report              # baca cache saja, nol kueri
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

DUNE = "https://api.dune.com"
CACHE = os.path.join(ROOT, "data", "flow")


def dune_key():
    k = (os.environ.get("DUNE_API_KEY") or "").strip()
    if k:
        return k
    for p in (os.path.join(ROOT, ".dune.env"), os.path.expanduser("~/.config/dune/.env")):
        try:
            for ln in open(p, encoding="utf-8"):
                if ln.startswith("DUNE_API_KEY="):
                    return ln.split("=", 1)[1].strip()
        except OSError:
            pass
    return ""


def api(path, key, body=None, timeout=120, method=None):
    h = {"X-Dune-Api-Key": key, "Accept": "application/json",
         "User-Agent": "Mozilla/5.0 (compatible; fabius-flow/1.0)"}
    data = json.dumps(body).encode() if body is not None else None
    if data:
        h["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(
                DUNE + path, data=data, headers=h, method=method or ("POST" if data else "GET")),
                timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        t = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(t)
        except Exception:  # noqa: BLE001
            return e.code, {"_raw": t[:240]}
    except Exception as e:  # noqa: BLE001
        return None, {"_error": f"{type(e).__name__}: {str(e)[:140]}"}


def run_sql(key, sql, wait=900):
    """Eksekusi + polling + halaman berulang. Mengembalikan (rows, catatan, selesai)."""
    st, body = api("/api/v1/sql/execute", key, {"sql": sql, "performance": "medium"})
    eid = (body or {}).get("execution_id")
    if not eid:
        return None, f"POST {st}: {json.dumps(body)[:200]}", False
    t0, stat = time.time(), {}
    while time.time() - t0 < wait:
        _, stat = api(f"/api/v1/execution/{eid}/status", key)
        state = str(stat.get("state", ""))
        if state and state not in ("QUERY_STATE_EXECUTING", "QUERY_STATE_PENDING",
                                   "QUERY_STATE_STARTING"):
            break
        time.sleep(3)
    if "COMPLETED" not in state:
        return None, f"{state}: {str(stat.get('error', {}).get('message'))[:200]}", False
    rows, cur, complete = [], None, True
    while True:
        p = f"/api/v1/execution/{eid}/results?limit=5000" + (f"&offset={cur}" if cur else "")
        ok, res = None, None
        for t in range(3):
            sc, res = api(p, key, timeout=150)
            if sc == 200:
                ok = True
                break
            time.sleep(4 + 4 * t)
        if not ok:
            complete = False
            print(f"  HALAMAN GAGAL di offset {cur} -> hasil TIDAK lengkap (dibaca sebagai terpotong)")
            break
        got = ((res.get("result") or {}).get("rows") or [])
        rows.extend(got)
        meta = ((res.get("result") or {}).get("metadata") or {})
        nxt = meta.get("next_offset") or res.get("next_offset")
        if not nxt or nxt == cur or not got:
            break
        cur = nxt
        print(f"  ... {len(rows)} baris", flush=True)
    dur = (stat.get("total_duration_ms") or (time.time() - t0) * 1000) / 1000
    return rows, (f"baris={len(rows)} durasi_dune={dur:.0f}s waktu_total={time.time()-t0:.0f}s"
                  + ("" if complete else " [TERPOTONG]")), complete


def perp_tokens(window_tokens):
    """Base asset yang punya kontrak perp di Aster -> simbol -> alamat ERC-20 lewat Dune.

    Sengaja TIDAK mengambil alamat dari universe kami: universe cuma 140 baris per jendela dan
    hanya ~9 di antaranya yang ber-perp, padahal Aster punya 584 kontrak. Membatasi diri ke itu
    membuang 98 % dari yang bisa kita uji. Jadi kami minta peta simbol->alamat ke Dune, lalu
    INTERSEKSI dengan daftar perp. Alamat ganda untuk satu simbol (token kembar) tetap mungkin -
    itu sebabnya baris hasil membawa `token` mentah, bukan simbol.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("direction", os.path.join(HERE, "direction.py"))
    D = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(D)
    bases = sorted({str(s.get("base") or "").upper() for s in D.perp_symbols()} - {""})
    # symbol panjang 2-12 karakter, huruf/angka saja, bukan pasangan stable
    skip = {"USDT", "USDC", "USD1", "DAI", "WBNB", "WBTC", "BTCB", "BTC", "ETH", "SOL", "XRP"}
    cand = [b for b in bases if 2 <= len(b) <= 12 and b not in skip][:window_tokens]
    return cand


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int, default=3, help="hari ke belakang")
    ap.add_argument("--tokens", type=int, default=120, help="batas simbol perp yang dipetakan")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    os.makedirs(CACHE, exist_ok=True)
    fp = os.path.join(CACHE, f"flow-{a.window}d.jsonl")

    if a.report:
        n = sum(1 for _ in open(fp, encoding="utf-8")) if os.path.exists(fp) else 0
        toks = len({json.loads(l)["token"] for l in open(fp, encoding="utf-8")}) if n else 0
        print(f"{os.path.basename(fp)}: {n} baris (token,jam) | {toks} token")
        return

    key = dune_key()
    if not key:
        raise SystemExit("tidak ada DUNE_API_KEY")

    syms = perp_tokens(a.tokens)
    print(f"kontrak perp aktif di Aster -> {len(syms)} simbol akan dicari alamatnya")

    # 1) Peta simbol -> alamat, DIPILIH LEWAT VOLUME PERDAGANGAN, bukan `LIMIT`/urutan abjad.
    # Kalibrasi 26 Sep menangkap dua jebakan di langkah ini:
    #   - `0G` punya 112 kontrak ERC-20 bernama sama di BSC (`1000CAT` 6, `1000CHEEMS` 5).
    #     Versi pertama mengambil v[0] - alamat ARBITRER - jadi "aliran 0G" bisa saja aliran token
    #     nyasar yang kebetulan memakai simbol yang sama. Salah yang tidak berteriak.
    #   - `ORDER BY symbol LIMIT 4000` memotong tepat di 4000 baris, jadi "25 dari 120 simbol"
    #     sebagian artefak pemotongan, bukan kenyataan.
    # Jawabannya satu bentuk yang sama: agregasi dulu, barisnya jadi = (alamat, simbol) yang
    # benar-benar diperdagangkan, dan pemotongan tidak lagi menentukan siapa yang ikut.
    def bare(a):
        # `to_hex()` Trino membalik 40 karakter TANPA prefiks; `0x` panjangnya 42. Versi pertama
        # memeriksa len==42 saja dan membuang 488 baris alamat yang benar - filter yang terlalu
        # ketat terlihat persis seperti "tidak ada data", jadi panjang normalisasi, bukan asumsi.
        a = str(a or "").strip().lower()
        if a.startswith("0x"):
            a = a[2:]
        return a if len(a) == 40 else ""

    map_fp = os.path.join(CACHE, "map-perp.json")
    in_s = ", ".join(f"'{s}'" for s in syms)
    sql_map = (
        "SELECT to_hex(d.token_bought_address) AS addr, upper(t.symbol) AS symbol, "
        "count(*) AS trades, sum(d.amount_usd) AS usd "
        "FROM dex.trades d JOIN tokens.erc20 t "
        "  ON d.token_bought_address = t.contract_address AND t.blockchain = 'bnb' "
        "WHERE d.blockchain = 'bnb' AND upper(t.symbol) IN (" + in_s + ") "
        f"AND d.block_time > now() - INTERVAL '{max(3, a.window)}' DAY "
        "GROUP BY 1,2 ORDER BY trades DESC LIMIT 3000")
    if os.path.exists(map_fp):
        mrows = json.load(open(map_fp, encoding="utf-8"))
        print(f"kueri 1/2: dilewati - peta alamat dibaca dari cache ({len(mrows)} baris, "
              "kredit tidak dibayar ulang)")
    else:
        print("kueri 1/2: alamat yang benar-benar diperdagangkan untuk simbol perp ...")
        mrows, note, _ = run_sql(key, sql_map)
        print(f"  {note if mrows is not None else 'GAGAL: ' + str(note)}")
        if not mrows:
            raise SystemExit("peta alamat gagal - berhenti (jangan uji udara)")
        json.dump(mrows, open(map_fp, "w", encoding="utf-8"), ensure_ascii=False)
    by_sym = {}
    for r in mrows:                       # sudah terurut trades DESC -> alamat teraktif menang
        s, addr = str(r.get("symbol") or "").upper(), bare(r.get("addr"))
        if not addr or s not in syms:
            continue
        by_sym.setdefault(s, addr)
    amb = sum(1 for r in mrows if bare(r.get("addr")) and
              str(r.get("symbol") or "").upper() in by_sym
              and bare(r.get("addr")) != by_sym[str(r.get("symbol") or "").upper()])
    addrs = sorted(set(by_sym.values()))
    print(f"  {len(by_sym)} simbol terpetakan ke alamat TERAKTIF "
          f"({amb} baris alamat lain dengan simbol sama DIBUANG - pilihan sadar, bukan lupa)")
    print(f"  token uji = {len(addrs)}")
    if len(addrs) < 20:
        raise SystemExit(f"cakupan {len(addrs)} token terlalu kecil untuk disimpulkan apa pun - "
                         "perlebar --window atau --tokens, jangan paksakan uji")

    # 2) aliran per (token, jam), dua sisi dihitung dari tabel yang sama
    in_a = ", ".join(f"from_hex('{x}')" for x in addrs)
    sql = (
        "WITH side AS ("
        "  SELECT block_time, taker, amount_usd, to_hex(token_bought_address) AS tok, 'buy' AS s"
        "  FROM dex.trades WHERE blockchain='bnb' AND token_bought_address IN (" + in_a + ")"
        "  UNION ALL"
        "  SELECT block_time, taker, amount_usd, to_hex(token_sold_address) AS tok, 'sell' AS s"
        "  FROM dex.trades WHERE blockchain='bnb' AND token_sold_address IN (" + in_a + ")"
        # `tok` sudah varchar hasil to_hex di CTE - membungkusnya dengan to_hex lagi adalah error
        # tipe yang dibayar dengan kueri gagal (terukur 26 Sep: "Unexpected parameters (varchar)
        # for function to_hex"). Tidak ditagih, tapi tetap membuang satu siklus kalibrasi.
        ") SELECT tok AS token, date_trunc('hour', block_time) AS jam, "
        # `count_if` memang ada di Trino, tapi `CASE WHEN` dimengerti SEMUA dialek: satu tempat
        # yang tidak bisa gagal karena varian mesin bukan tempat untuk bertaruh kredit.
        "count(CASE WHEN s='buy' THEN 1 END) AS beli, "
        "count(CASE WHEN s='sell' THEN 1 END) AS jual, "
        "count(distinct CASE WHEN s='buy' THEN taker END) AS pembeli, "
        "count(distinct CASE WHEN s='sell' THEN taker END) AS penjual, "
        "sum(CASE WHEN s='buy' THEN amount_usd ELSE 0 END) AS usd_beli, "
        "sum(CASE WHEN s='sell' THEN amount_usd ELSE 0 END) AS usd_jual "
        f"FROM side WHERE block_time > now() - INTERVAL '{a.window}' DAY "
        "GROUP BY 1,2 ORDER BY 1,2")
    print(f"kueri 2/2: agregat aliran {a.window} hari untuk {len(addrs)} token ...")
    rows, note, complete = run_sql(key, sql)
    print(f"  {note if rows is not None else 'GAGAL: ' + str(note)}")
    if not rows:
        raise SystemExit("kueri aliran gagal - tidak ada yang ditulis")
    with open(fp, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps({**r, "window_d": a.window,
                                 "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                                ensure_ascii=False, sort_keys=True) + "\n")
    json.dump({s: v for s, v in by_sym.items()},
              open(os.path.join(CACHE, f"addr-{a.window}d.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    toks = {r.get("token") for r in rows}
    print(f"\ntertulis: {os.path.relpath(fp, ROOT)}  {len(rows)} baris (token,jam) | {len(toks)} token muncul")
    print(f"lengkap: {'YA' if complete else 'TIDAK - hasil terpotong, jangan dipakai menyimpulkan'}")
    if len(toks) < len(addrs):
        print(f"CATATAN: {len(addrs) - len(toks)} token TIDAK punya satu pun swap di jendela "
              f"{a.window} hari -> bukan error, tapi mereka tidak akan memberi sampel. Jendela "
              "lebih panjang menaikkan cakupannya, dan itu yang diukur di kalibrasi berikutnya.")


if __name__ == "__main__":
    main()
