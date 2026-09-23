"""Perekam universe memecoin BSC secara POINT-IN-TIME, append-only, siap di-anchor.

Kenapa berkas ini ada, dan kenapa ia harus jalan SEKARANG:
  Agen yang memilih memecoin mengambil keputusan berdasarkan "apa yang sedang hot SAAT ITU".
  Tidak ada API yang bisa mengembalikan daftar trending 3 hari yang lalu - trending_pools dan
  new_pools hanya menyajikan keadaan KINI. Jadi satu-satunya cara membuat klaim seleksi tidak
  bisa dituduh hindsight adalah MEREKAM SEJAK HARI INI. Yang tidak terekam hari ini tidak akan
  pernah bisa dibuktikan besok. (Aturan yang sama yang membuat commit history tidak bisa dibeli
  kembali - lihat Vault/Notes/Log-Keputusan D26.)

Yang dicatat per snapshot, dan asal setiap angka:
  - GeckoTerminal trending_pools / new_pools  : umur pool, likuiditas, volume 24h  (terukur HTTP 200)
  - GMGN /v1/market/rank?chain=bsc            : bundler_rate, sniper_count, smart_degen_count,
                                                rug_ratio, top_10_holder_rate, lock_percent,
                                                is_honeypot, holder_count, liquidity  (TERBUKTI ADA
                                                di respons nyata - _research/gmgn_memecoin_fields.py)
  - Vetoes                                    : dihitung DI DALAM snapshot, jadi alasannya tercatat
                                                pada waktunya, bukan direkonstruksi setelah tahu hasil.
  - sha256                                    : kanonik (sorted keys, compact) - konvensi yang sama
                                                dengan record_hash() di agents/firm/onchain_recorder.py,
                                                jadi siap di-anchor ke BSC tanpa perubahan bentuk.

Kebenaran diutamakan: kalau sebuah sumber mati, snapshot mencatat status HTTP-nya dan TIDAK
mengarang baris. Same rule as the frontend: unreachable, never fake.

Pakai:
  python record_bsc_universe.py            sekali (satu snapshot)
  python record_bsc_universe.py --loop     terus-menerus tiap 60 menit
  BSC_UNIVERSE_INTERVAL_MIN=15 python record_bsc_universe.py --loop   ubah jaraknya
"""
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_FILE = os.path.join(OUT_DIR, "bsc-universe.jsonl")

def _load_gmgn_key():
    """Urutan pencarian mengikuti CLI resmi (Readme.md:329): env -> ~/.config/gmgn/.env -> demo key.
    Tanpa baca file ini, janji "cukup tulis GMGN_API_KEY ke .env dan perekam ikut pindah" itu SALAH:
    os.environ tidak pernah melihat file konfigurasi tersebut."""
    k = (os.environ.get("GMGN_API_KEY") or "").strip()
    if k:
        return k
    p = os.path.join(os.path.expanduser("~"), ".config", "gmgn", ".env")
    try:
        with open(p, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if ln.startswith("GMGN_API_KEY="):
                    v = ln.split("=", 1)[1].strip().strip('"').strip("'")
                    if v:
                        return v
    except OSError:
        pass
    return "gmgn_solbscbaseethmonadtron"   # demo key publik, read-only


GMGN_KEY = _load_gmgn_key()
GT = "https://api.geckoterminal.com/api/v2/networks/bsc"
UA = {"User-Agent": "Mozilla/5.0 (compatible; lencana-universe-recorder/1.0)", "Accept": "application/json"}


def gmgn_url(sub_path, **params):
    """Bangun URL route GMGN dengan auth mode "exist".

    Aturannya diambil dari komentar kepala src/client/OpenApiClient.ts resmi (GMGNAI/gmgn-skills):
        Exist  (market/token/portfolio): X-APIKEY + timestamp + client_id
        Signed (swap & order routes)   : X-APIKEY + timestamp + client_id + X-Signature
    Demo key publik tidak menagih dua parameter terakhir - karena itu pemanggilan awal kami lolos
    tanpanya. API key PRIVAT menagihnya dan membalas
        401 {"error":"AUTH_INVALID","message":"missing api key or client_id"}
    Jadi keduanya selalu kami kirim. timestamp = Unix SEKON (server memvalidasi rentang sekitar
    5 detik), client_id = UUID sekali-pakai (replay ditolak server). Kita hanya memakai route
    "exist", jadi kunci privat memang tidak pernah dibutuhkan."""
    q = dict(params)
    q["timestamp"] = int(time.time())
    q["client_id"] = str(uuid.uuid4())
    return "https://openapi.gmgn.ai" + sub_path + "?" + urllib.parse.urlencode(q)

# Ambang veto. Tiap angka dipilih karena alasannya bisa diucapkan, dan ikut ditulis ke dalam
# snapshot supaya bisa diuji ulang - bukan supaya hasilnya terlihat bagus.
MIN_LIQ_USD = 50_000.0        # di bawah ini exit-size apa pun menghancurkan harga
MIN_AGE_SEC = 24 * 3600       # <24 jam = nol bar, tidak ada satu pun yang bisa divalidasi
MAX_TOP10 = 0.45              # 45% supply di 10 alamat pertama = satu keputusan bisa menghapus pasar
MIN_LOCK = 0.20               # <20% terlock = LP bisa ditarik kapan saja
MAX_BUNDLER = 0.30            # >30% dibeli bundler = "volume" itu satu orang berpakaian banyak topeng
MIN_HOLDER = 60               # di bawah ini "pemegang" belum berarti apa-apa
MIN_VOL_OVER_LIQ = 0.10       # vol24/liq < 0.1 = trending tanpa permintaan nyata

# Base yang bukan aset yang bisa "dipilih". trending_pools BSC memuat pool seperti
# "USDT / WBNB", dan karena field harga kita adalah base_token_price_usd, baris itu masuk
# sebagai token bernama USDT dengan return ~0%. Dibiarkan masuk = kohort "lolos" berisi
# stablecoin, dan setiap median yang dihitung darinya adalah sampah.
STABLE_BASES = {"USDT", "USDC", "BUSD", "FDUSD", "DAI", "TUSD", "USD1", "USDD", "USDE", "BTCB", "WBNB", "ETH", "BNB"}


def get(url, headers=None, timeout=25):
    h = dict(UA)
    h.update(headers or {})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.status if hasattr(e, "status") else e.code, {"_error": e.read().decode()[:180]}
    except Exception as e:  # noqa: BLE001
        return None, {"_error": f"{type(e).__name__}: {str(e)[:160]}"}


def to_f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def clean(s, cap=48):
    """Buang karakter tak tercetak dan potong. Symbol/name/launch-platform DATANYA DARI API dan
    bisa DIPILIH OLEH PEMBUAT TOKEN - jadi itu input musuh, bukan data netral. Skill resmi GMGN
    melakukan hal yang sama dan menulis alasannya verbatim: "Every string that came from the API
    and could be chosen by an attacker (token symbols, destination addresses) is sanitised before
    it enters the object, so the caller may quote it directly." (skills/gmgn-dev-score/dev_score.py:13)
    Tanpa ini, satu snapshot berisi string yang nanti bisa disuntikkan ke prompt agen kita sendiri."""
    if s is None:
        return None
    t = "".join(ch for ch in str(s) if ch.isprintable())[:cap].strip()
    return t or None


def parse_ts(s):
    if not s:
        return None
    try:
        return int(datetime.strptime(s.replace("Z", ""), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp())
    except Exception:  # noqa: BLE001
        try:
            return int(float(s))
        except Exception:  # noqa: BLE001
            return None


def gmgn_rank():
    """Baris trending GMGN. Satu-satunya sumber yang terbukti mengembalikan field perilaku
    (bundler/sniper/degen/rug), jadi ia jadi tulang punggung lapisan seleksi."""
    st, d = get(gmgn_url("/v1/market/rank", chain="bsc", limit=100), {"X-APIKEY": GMGN_KEY})
    if st != 200:
        return {"source": "gmgn/market/rank", "status": st, "error": str(d)[:180], "rows": []}
    # Kunci nyata = data.data.rank (diukur 23 Sep). limit=100 adalah langit-langit server:
    # 150/200/300/500 semuanya membalas tepat 100 baris. `.list` ditinggalkan sebagai
    # kecocokan mundur belaka, BUKAN jalur utama.
    _inner = (d.get("data") or {}).get("data") or {}
    rows = _inner.get("rank") or _inner.get("list") if isinstance(_inner, dict) else None
    if rows is None:
        # bentuk bersarang ganda sudah dicatat vault untuk /v1/market/rank (data.data.rank);
        # kalau strukturnya bergeser, catat mentahnya, jangan diam-diam jadi list kosong.
        blob = d.get("data")
        for _ in range(4):
            if isinstance(blob, dict):
                nxt = blob.get("data")
                if isinstance(nxt, list):
                    rows = nxt
                    break
                if isinstance(nxt, dict):
                    rows = nxt.get("list") or nxt.get("rank")
                    if rows:
                        break
                    blob = nxt
                    continue
            break
    if rows is None:
        return {"source": "gmgn/market/rank", "status": 200, "error": "struktur tak dikenal",
                "keys": sorted((d or {}).keys()), "rows": []}
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        out.append({
            "symbol": clean(r.get("symbol") or r.get("name")),
            "address": r.get("address") or r.get("token_address"),
            "price": to_f(r.get("price")),
            "liquidity": to_f(r.get("liquidity")),
            # Satu nama untuk satu hal. Sebelumnya baris GMGN menyimpan "volume" sementara vetoes()
            # dan blind_spots() membaca "volume_24h" -> keduanya diam-diam tidak pernah melihat
            # angka itu, jadi veto "trending_without_demand" TIDAK PERNAH jalan untuk 50 baris GMGN,
            # dan setiap baris GMGN tercatat punya blind spot yang sebenarnya tidak ia miliki.
            "volume_24h": to_f(r.get("volume") or r.get("volume_24h") or r.get("volume_usd")),
            "holder_count": to_f(r.get("holder_count")),
            "bundler_rate": to_f(r.get("bundler_rate")),
            "sniper_rate": to_f(r.get("sniper_rate")),
            "sniper_count": to_f(r.get("sniper_count")),
            "smart_degen_count": to_f(r.get("smart_degen_count")),
            "dev_dig_ass_count": to_f(r.get("dev_dig_ass_count")),
            "rug_ratio": to_f(r.get("rug_ratio")),
            "top_10_holder_rate": to_f(r.get("top_10_holder_rate")),
            "lock_percent": to_f(r.get("lock_percent")),
            "is_honeypot": r.get("is_honeypot"),
            "can_not_sell": r.get("can_not_sell"),
            "created_at": r.get("created_timestamp") or r.get("created_at"),
            "launched": clean(r.get("launch_platform") or r.get("platform")),
        })
    return {"source": "gmgn/market/rank", "status": 200, "rows": out}


def gt_pools(kind):
    st, d = get(f"{GT}/{kind}_pools?page=1")
    if st != 200:
        return {"source": f"geckoterminal/{kind}", "status": st, "error": str(d)[:180], "rows": []}
    now = int(time.time())
    rows = []
    for p in d.get("data") or []:
        a = p.get("attributes") or {}
        rel = p.get("relationships") or {}
        created = parse_ts(a.get("pool_created_at"))
        base = ((rel.get("base_token") or {}).get("data") or {}).get("id") or ""
        vol = a.get("volume_usd") or {}
        rows.append({
            "pool": a.get("address") or (p.get("id") or "").split("_")[-1],
            "name": clean(a.get("name")),
            "base_token": base.split("_")[-1] or None,
            "created_at": a.get("pool_created_at"),
            "age_sec": (now - created) if created else None,
            "liquidity": to_f(a.get("reserve_in_usd")),
            "volume_24h": to_f(vol.get("h24") if isinstance(vol, dict) else None),
            # Harga token dasar WAJIB disimpan. Tanpa ini baris GT tidak bisa dinilai hasil
            # forward-nya, dan kohort "lolos vs ditolak" jadi tidak terbandingkan: satu-satunya
            # sumber yang berharga (GMGN rank) ternyata seluruhnya token berumur < 24 jam.
            "price_usd": to_f(a.get("base_token_price_usd")),
            "price_change_24h": to_f((a.get("price_change_percentage") or {}).get("h24")),
        })
    return {"source": f"geckoterminal/{kind}", "status": 200, "rows": rows}


def vetoes(rec):
    """Kembalikan daftar alasan penolakan. Kosong = lolos ke lapisan penilaian."""
    v = []
    liq, age, vol = rec.get("liquidity"), rec.get("age_sec"), rec.get("volume_24h")
    # Base pool GT ada di depan nama ("USDT / WBNB 0.01%"); GMGN memakai `symbol`.
    base = (rec.get("symbol") or (rec.get("name") or "").split("/")[0] or "").strip().upper()
    if base in STABLE_BASES:
        v.append("not_a_choosable_asset")
    if rec.get("is_honeypot") in (1, True, "1", "true"):
        v.append("honeypot")
    if rec.get("can_not_sell") in (1, True, "1", "true"):
        v.append("cannot_sell")
    if liq is None:
        v.append("no_liquidity_data")
    elif liq < MIN_LIQ_USD:
        v.append(f"liq<{MIN_LIQ_USD:.0f}")
    if age is None:
        v.append("no_age")
    elif age < MIN_AGE_SEC:
        v.append(f"age<{MIN_AGE_SEC // 3600}h_zero_bars")
    t10 = rec.get("top_10_holder_rate")
    if t10 is not None and t10 > MAX_TOP10:
        v.append(f"top10>{MAX_TOP10:.0%}")
    lk = rec.get("lock_percent")
    if lk is not None and lk < MIN_LOCK:
        v.append(f"lock<{MIN_LOCK:.0%}")
    bd = rec.get("bundler_rate")
    if bd is not None and bd > MAX_BUNDLER:
        v.append(f"bundler>{MAX_BUNDLER:.0%}")
    hc = rec.get("holder_count")
    if hc is not None and hc < MIN_HOLDER:
        v.append(f"holders<{MIN_HOLDER}")
    if liq and vol is not None and vol / max(liq, 1.0) < MIN_VOL_OVER_LIQ:
        v.append("trending_without_demand")
    return v


def blind_spots(rec):
    """Bagian yang TIDAK BISA dinilai karena datanya tidak ada. Bukan daftar kegagalan, dan bukan
    pula lulus: standar ini juga dipinjam dari skill resmi GMGN yang menulis labelnya sendiri,
    "DATA GAPS (unevaluated ≠ passed)", dan memperingatkan bahwa hasil kosong bisa tampak seperti
    jawaban padahal bukan ("returns zeros everywhere, which looks like an answer and is not one").
    Tanpa ini, baris yang buta total akan terbaca sama dengan baris yang lolos semua pemeriksaan."""
    keys = ("top_10_holder_rate", "lock_percent", "bundler_rate", "holder_count",
            "liquidity", "age_sec", "volume_24h")
    return [k for k in keys if rec.get(k) is None]


def build_snapshot():
    parts = [gmgn_rank(), gt_pools("trending"), gt_pools("new")]
    now = int(time.time())
    # Gabungkan: baris pool GT ditempelkan ke field perilaku GMGN lewat alamat token.
    # Kedua sisi dinormalkan ke lowercase: alamat EVM boleh checksum (0xAb...) atau lowercase, dan
    # kalau salah satu sisi tidak dinormalkan penggabungannya diam-diam 0 cocok -> baris GT akan
    # kehilangan SEMUA field perilaku tanpa error apa pun.
    by_addr = {(r.get("address") or "").lower(): r for r in parts[0]["rows"] if r.get("address")}
    merged = []
    for src in parts[1:]:
        for r in src["rows"]:
            g = by_addr.get((r.get("base_token") or "").lower(), {})
            row = dict(r)
            for k in ("bundler_rate", "sniper_count", "smart_degen_count", "rug_ratio",
                      "top_10_holder_rate", "lock_percent", "is_honeypot", "can_not_sell", "holder_count"):
                row[k] = g.get(k)
            row["age_sec"] = row.get("age_sec") or None
            row["vetoes"] = vetoes(row)
            row["blind_spots"] = blind_spots(row)
            row["survivable"] = not row["vetoes"]
            # Jujur soal dua tingkat: "lolos veto" belum tentu "semua aspek sudah dinilai".
            row["fully_evaluated"] = row["survivable"] and not row["blind_spots"]
            merged.append(row)
    for r in parts[0]["rows"]:                     # baris GMGN sendiri juga ikut dgn veto-nya
        row = dict(r)
        row["age_sec"] = max(0, now - int(parse_ts(str(r.get("created_at"))) or now))
        row["vetoes"] = vetoes(row)
        row["blind_spots"] = blind_spots(row)
        row["survivable"] = not row["vetoes"]
        row["fully_evaluated"] = row["survivable"] and not row["blind_spots"]
        merged.append(row)

    snap = {
        # Nomor skema WAJIB dibaca saat dianalisis. Riwayatnya:
        #   (tanpa kunci) = semantik lama: field "volume" belum dinormalkan, veto volume/liq tidak
        #     berjalan untuk baris GMGN, belum ada blind_spots, string API belum disanitasi.
        #   2 = ketiganya diperbaiki (22 Sep 01:31Z).
        #   3 = veto baru `not_a_choosable_asset` membuang base stablecoin/major (USDT, BTCB, WBNB…)
        #     yang sebelumnya bisa masuk kohort "lolos" dengan return ~0%. Jumlah `survivable_count`
        #     di baris skema 2 TIDAK sebanding dengan skema 3 -> jangan dicampur dalam satu deret.
        "schema": 3,
        "snapshot_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "epoch": now,
        "chain": "bsc",
        "thresholds": {"MIN_LIQ_USD": MIN_LIQ_USD, "MIN_AGE_SEC": MIN_AGE_SEC, "MAX_TOP10": MAX_TOP10,
                       "MIN_LOCK": MIN_LOCK, "MAX_BUNDLER": MAX_BUNDLER, "MIN_HOLDER": MIN_HOLDER,
                       "MIN_VOL_OVER_LIQ": MIN_VOL_OVER_LIQ},
        "sources": [{"source": p["source"], "status": p["status"], "rows": len(p["rows"]),
                     **({"error": p.get("error")} if p.get("error") else {})} for p in parts],
        "universe_size": len(merged),
        "survivable_count": sum(1 for r in merged if r["survivable"]),
        "fully_evaluated_count": sum(1 for r in merged if r["fully_evaluated"]),
        # Diagnosa penggabungan: kalau angka ini 0, GT dan GMGN tidak ketemu lewat alamat dan
        # semua baris GT kehilangan field perilakunya TANPA error apa pun. Harus terlihat.
        "gt_rows": sum(1 for r in merged if r.get("pool")),
        "gt_rows_with_gmgn_fields": sum(1 for r in merged
                                        if r.get("pool") and r.get("bundler_rate") is not None),
        "top_reasons": _tally(merged),
        "rows": merged,
    }
    # Hash kanonik dengan konvensi yang sama dengan onchain_recorder.record_hash():
    # json.dumps(sort_keys=True, separators=(",", ":")) -> sha256 -> 0x-hex. Siap di-anchor.
    blob = json.dumps(snap, sort_keys=True, separators=(",", ":")).encode()
    snap["sha256"] = "0x" + hashlib.sha256(blob).hexdigest()
    return snap


def _tally(rows):
    """Hitung alasan penolakan. Label dijaga terbaca: ambang numerik jadi `<threshold`,
    alasan kategoris (honeypot, trending_without_demand) tetap utuh."""
    c = {}
    for r in rows:
        for v in r["vetoes"]:
            key = (v.split("<")[0] + "<threshold") if "<" in v else v
            c[key] = c.get(key, 0) + 1
    return dict(sorted(c.items(), key=lambda kv: -kv[1]))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    loop = "--loop" in sys.argv
    interval = max(int(os.environ.get("BSC_UNIVERSE_INTERVAL_MIN", "60")), 1) * 60
    while True:
        try:
            snap = build_snapshot()
        except Exception as e:  # noqa: BLE001 - perekam tidak boleh mati karena satu sumber
            print(f"snapshot GAGAL: {type(e).__name__}: {e}")
            if not loop:
                raise
            snap = None
        if snap:
            with open(OUT_FILE, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(snap, ensure_ascii=False) + "\n")
            print(f"[{snap['snapshot_utc']}] universe={snap['universe_size']} "
                  f"lolos_veto={snap['survivable_count']} dinilai_penuh={snap['fully_evaluated_count']} "
                  f"sha256={snap['sha256'][:18]}…")
            print(f"  sumber: " + "  ".join(f"{s['source']}={s['status']}/{s['rows']}" for s in snap["sources"]))
            print(f"  alasan penolakan terbanyak: {json.dumps(snap['top_reasons'])}")
            print(f"  ditulis ke: {OUT_FILE}")
        if not loop:
            break
        # Selaraskan ke jam dinding; jangan tidur `interval` penuh SETELAH pekerjaan selesai.
        # Bukti kenapa perlu: 16 snapshot pertama punya dua celah >75 menit (23:03:05 -> 01:03:58,
        # dan 02:19:44 -> 03:53:31). sleep(interval) sesudah kerja menggeser titik ambil maju terus
        # setiap jam sampai satu tick jatuh. `epoch` tetap direkam di tiap baris, jadi celah berapa
        # pun selalu bisa dihitung ulang saat analisis tanpa perlu field tambahan.
        aligned = interval - (time.time() % interval)
        time.sleep(max(5.0, aligned))


if __name__ == "__main__":
    main()
