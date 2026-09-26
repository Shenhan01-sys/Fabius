"""Perekam aliran wallet (bidang ⑦): smart money & KOL di BSC, disimpan SEBELUM hasilnya ada.

Kenapa file ini ada, dan kenapa dia lebih Buru-From dari semua pekerjaan lain minggu ini:
terukur 25 Sep lewat `probe_gmgn_wallet_stream.py` bahwa aliran `user/smartmoney` cuma menutup
**8,1 menit** ke belakang, `user/kol` **12,7 menit**, dan SEMUA parameter paging (`offset`, `page`,
`page_no`, `end_ts`) DIABAIKAN server - balasannya head yang sama (overlap 98/100, baris baru 1).

Beda itu menentukan. Kline Aster bisa ditarik mundur 400 hari; aliran ini TIDAK. Artinya setiap
menit kita tidak merekam adalah transaksi yang hilang permanen dan tidak bisa disusulkan besok.
Sementara cadence perekam universe adalah per jam (dan itu pun bolong - 5 gap > 2 jam, terbesar
16,31 jam), jadi sekarang kita cuma menangkap ±8 menit dari tiap 60 menit.

Kuirensi yang ditambal di sini: cron per 10 menit, tiap jalanan menarik 2x berjarak 5 menit,
sehingga dua jendela 8 menit menutup 0-15 menit tanpa lubang. Bentuk loop-nya ada di
`.github/workflows/wallet-flow.yml` - SATU penulis untuk SATU berkas (aturan yang sudah dua kali
berbayar mahal karena dilanggar: konflik JSONL bukan soal estetika).

Kenapa kita merekam aliran dan bukan "riwayat wallet":
  `user/positions|history|trades|activity|token_activity|pnl|holdings|user/{addr}/tokens` -> 404.
  Jalur "tempel alamat, lihat masa lalu" memang tidak ada untuk kita. Yang ada justru lebih jujur:
  panel dompet yang bergerak, dicatat sekarang, dinilai ke depan. Label sewaan (Nansen/Arkham)
  mengandung lookahead - sebuah wallet diberi label pintar SETELAH seluruh sejarahnya diketahui.
  Karena kita tidak bisa membeli label itu, kita terpaksa melakukan cara yang benar.
  Karena itu `tags` (mis. `smart_degen`) ikut disimpan: dia menandai panel mana yang dipilih GMGN,
  dan itu bias yang harus bisa kami tunjukkan, bukan kami lupa.

Harga token ikut dicatat tiap tarikan (baris `k:"px"`) - TANPA itu kita tidak akan pernah bisa
menilai hasil 4 jam nanti tanpa mengandalkan orang lain, dan bergantung ke orang lain adalah cara
klaim kita berhenti bisa diverifikasi.

Read-only. Tidak ada order, tidak ada kunci trading, tidak ada dana.
Pakai:  python universe/record_wallet_flow.py --pulls 2 --gap 300     # sekali jalan + commit offline
         python universe/record_wallet_flow.py --pulls 1 --gap 0 --report
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import record_bsc_universe as rec  # noqa: E402  SATU sumber bentuk permintaan + kunci

FLOW = os.path.join(HERE, "wallet-flow.jsonl")
MANIFEST = os.path.join(HERE, "wallet-flow-manifest.txt")
SCHEMA = 1
ROUTES = {"sm": "/v1/user/smartmoney", "kol": "/v1/user/kol"}
LIMIT = 100
# Demo key publik perekam (record_bsc_universe.py:64). Dibandingkan lewat SALINAN bernama, bukan
# diimpor dari konstanta: perekar tidak memilikinya sebagai nama, dan menebak nama konstanta adalah
# cara klasik dapat `AttributeError` di runner yang tidak pernah kelihatan di layar.
DEMO_KEY = "gmgn_solbscbaseethmonadtron"


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load_seen():
    """Set transaksi yang SUDAH pernah kita simpan + hash baris terakhir (rantai anti-sunting)."""
    seen, last_sha, n, first_t, last_t = set(), None, 0, None, None
    if not os.path.exists(FLOW):
        return seen, last_sha, n, first_t, last_t
    with open(FLOW, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            try:
                d = json.loads(ln)
            except Exception:  # noqa: BLE001
                continue
            n += 1
            last_sha = "0x" + hashlib.sha256(ln.encode()).hexdigest()
            if d.get("k") == "tx":
                seen.add(d.get("h"))
                t = d.get("t")
            elif d.get("k") == "pull":
                t = d.get("t")
            else:
                t = None
            if t:
                first_t = min(first_t, t) if first_t else t
                last_t = max(last_t, t) if last_t else t
    return seen, last_sha, n, first_t, last_t


def normalize(src, row):
    """Satu baris GMGN -> baris rekaman yang ramping (ukuran berkas = biaya, tiap byte dibayar juri)."""
    tags = ((row.get("maker_info") or {}).get("tags") or [])
    return {"k": "tx", "s": src,
            "h": str(row.get("transaction_hash") or ""),
            "m": str(row.get("maker") or "").lower(),
            "t": int(row.get("timestamp") or 0),
            "b": 1 if str(row.get("side")).lower() == "buy" else 0,
            "c": 1 if row.get("is_open_or_close") in (1, "1", True) else 0,
            "tk": str(row.get("base_address") or "").lower(),
            "y": str(((row.get("base_token") or {}).get("symbol")) or "")[:16],
            "p": row.get("price_usd"),
            "u": round(float(row.get("amount_usd") or 0), 4),
            "g": [str(x) for x in tags][:4]}


def pull(src, path, hdr, seen):
    st, body = rec.get(rec.gmgn_url(path, chain="bsc", limit=str(LIMIT)), hdr)
    now = int(time.time())
    if not isinstance(body, dict):
        return {"k": "err", "s": src, "t": now, "http": st, "why": str(body)[:160]}, [], []
    lst = ((body.get("data") or {}).get("list")) or []
    rows, new, prices = [], [], {}
    for r in lst:
        d = normalize(src, r)
        rows.append(d)
        if d["h"] and d["h"] not in seen:
            new.append(d)
        if d["tk"] and isinstance(d["p"], (int, float)) and d["p"]:
            prices[d["tk"]] = (float(d["p"]), d["y"])
    px = [{"k": "px", "t": now, "tk": tk, "y": v[1], "p": v[0]} for tk, v in sorted(prices.items())]
    pl = {"k": "pull", "s": src, "t": now, "http": st, "n": len(lst),
          "new": len(new), "mk": len({r["m"] for r in rows}),
          "tk": len(prices),
          "span": (max((r["t"] for r in rows), default=0) - min((r["t"] for r in rows), default=0))}
    return pl, new, px


def write_manifest(prev_sha):
    """Rantai sha256 per-file + rentang event dihitung ULANG dari berkasnya, bukan dari ingatan.

    Versi pertama menerima `count/first_t/last_t` sebagai argumen - akibatnya rentang di manifest
    selalu telat satu jalanan (nilainya dari SEBELUM tarikan ini ditulis). Manifest yang mendeskripsikan
    keadaan lama sambil bertimestamp sekarang adalah cara halus untuk bikin laporan yang salah.
    """
    count = first_t = last_t = 0
    ntx = 0
    makers, tokens = set(), set()
    with open(FLOW, encoding="utf-8") as fh:
        raw = fh.read()
    now = int(time.time())
    lines_raw = [x.strip() for x in raw.splitlines() if x.strip()]
    for ln in lines_raw:
        count += 1
        try:
            d = json.loads(ln)
        except Exception:  # noqa: BLE001
            continue
        k = d.get("k")
        if k == "tx":
            ntx += 1
            if d.get("m"):
                makers.add(d["m"])
            if d.get("tk"):
                tokens.add(d["tk"])
        t = d.get("t")
        if isinstance(t, int) and t:
            first_t = min(first_t, t) if first_t else t
            last_t = max(last_t, t) if last_t else t
    last_hash = "0x" + hashlib.sha256(lines_raw[-1].encode()).hexdigest() if lines_raw else None
    data = raw.encode()
    fsha = "0x" + hashlib.sha256(data).hexdigest()
    lines = [
        "# wallet-flow manifest - dihasilkan universe/record_wallet_flow.py",
        f"generated_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        f"schema: {SCHEMA}",
        f"baris: {count}",
        f"baris_transaksi: {ntx}",
        f"maker_unik: {len(makers)}",
        f"token_unik: {len(tokens)}",
        f"usia_aliran_jam: {((now - last_t) / 3600 if last_t else 0):.2f}",
        f"sha256_berkas: {fsha}",
        # Hash baris terakhir dihitung DARI BERKAS SEKARANG, bukan dibawa dari memori jalanan
        # sebelumnya. Itu yang membuat "rantai"-nya nyata: jalanan berikutnya membandingkan nilai
        # ini dengan apa yang dia temukan di ekor berkas, jadi sisip/sunting di tengah terdeteksi.
        f"hash_baris_terakhir: {last_hash}",
        f"mata_rantai_dipakai_run_ini: {prev_sha or '-'}",
        (f"rentang_event_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(first_t))}"
         f" -> {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(last_t))}"
         f" ({(last_t - first_t) / 3600:.2f} jam)" if first_t and last_t else "rentang_event_utc: -"),
        "",
        "Batas yang wajib dibaca bersama berkas ini: keanggotaan panel `sm`/`kol` ADALAH pilihan",
        "GMGN (lihat field `g`/tags), jadi panel awal tidak netral. Yang kita ukur sendiri hanyalah",
        "HASILNYA, dari harga yang kita catat sendiri (baris `px`). Karena itu penilaian wallet",
        "harus selalu memakai kelompok kontrol, bukan sekadar membandingkan smart money vs nol.",
        "",
    ]
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return fsha


def read_manifest_tail():
    """Nilai `hash_baris_terakhir` yang dijanjikan manifest SEBELUM run ini, atau None."""
    try:
        want = None
        for ln in open(MANIFEST, encoding="utf-8"):
            if ln.startswith("hash_baris_terakhir:"):
                want = ln.split(":", 1)[1].strip()
        return want
    except OSError:
        return "ERR"


def chain_check(prev_sha, want):
    """Bandingkan ekor berkas dengan apa yang manifest run SEBELUMNYA klaim.

    Sengaja `want` dibaca DI MUKA (sebelum `write_manifest`), bukan di dalam fungsi ini: versi
    pertama membandingkannya setelah manifest ditulis ulang, jadi run PERTAMA pun langsung
    mencetak "PUTUS" - alarm palsu dari alat yang sama sekali belum mendeteksi apa pun. Alat
    pelacak integritas yang salah lapor lebih bahaya daripada tidak ada, karena orang mulai
    mengabaikan laporannya.
    """
    if want == "ERR":
        return "MANIFEST-TERBACA-GAGAL"
    if want is None:
        return "MANIFEST-BELUM-ADA (run pertama, tidak ada yang bisa dibandingkan)"
    if want in ("-", ""):
        return "MANIFEST-TANPA-HASH"
    if prev_sha == want:
        return "TERSAMBUNG"
    return (f"PUTUS (berkas={str(prev_sha)[:14]}… manifest_lama={want[:14]}…) "
            "-> ekor berkas berubah antar-run")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pulls", type=int, default=2, help="berapa kali menarik per proses (loop dgn jarak)")
    ap.add_argument("--gap", type=int, default=300, help="detik antar tarikan")
    ap.add_argument("--report", action="store_true", help="cetak keadaan berkas saja, jangan tarik")
    a = ap.parse_args()

    seen, prev_sha, n, first_t, last_t = load_seen()
    want = read_manifest_tail()          # dibaca SEBELUM manifest ditimpa run ini
    if a.report:
        print(f"wallet-flow.jsonl: {n} baris | transaksi unik tersimpan: {len(seen)} | "
              f"rentang {first_t} -> {last_t}")
        return

    hdr = {"X-APIKEY": rec.GMGN_KEY, "User-Agent": "Mozilla/5.0 (compatible; fabius-wallet-flow/1.0)",
           "Accept": "application/json"}
    if not rec.GMGN_KEY or rec.GMGN_KEY == DEMO_KEY:
        print("PERINGATAN: tidak ada kunci GMGN privat - pakai demo key, kemungkinan besar 401. "
              "Data yang hilang karena ini TIDAK BISA disusulkan.")

    appended = 0
    for i in range(max(1, a.pulls)):
        for src, path in ROUTES.items():
            pl, new, px = pull(src, path, hdr, seen)
            with open(FLOW, "a", encoding="utf-8") as fh:
                fh.write(canon(pl) + "\n")
                for d in new:
                    fh.write(canon(d) + "\n")
                    seen.add(d["h"])
                    appended += 1
                for d in px:
                    fh.write(canon(d) + "\n")
            if pl.get("k") == "err":
                print(f"  tarikan {i + 1} {src:4} GAGAL: {pl.get('why')[:110]}")
            else:
                span = (pl.get("span") or 0) / 60
                print(f"  tarikan {i + 1} {src:4}: HTTP {pl['http']} n={pl['n']} "
                      f"baru={pl['new']:>3} maker={pl['mk']:>3} token={pl['tk']:>3} "
                      f"jendela={span:.1f}mnt")
        if i + 1 < a.pulls:
            time.sleep(a.gap)

    fsha = write_manifest(prev_sha)
    link = chain_check(prev_sha, want)
    print(f"\ntransaksi baru ditulis: {appended} | transaksi unik tersimpan: {len(seen)}")
    print(f"rantai: {link}")
    print(f"manifest: {os.path.basename(MANIFEST)}  sha256_berkas={fsha[:18]}…")
    print("Ingat: jendela aliran ini 8-13 menit DAN tanpa paging. Berkas ini satu-satunya cara")
    print("kita punya riwayat; kalau detaknya berhenti, datanya tidak bisa diambil kemudian.")


if __name__ == "__main__":
    main()
