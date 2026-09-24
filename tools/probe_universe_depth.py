"""Seberapa besar daftar aset yang BENAR-BENAR bisa dijadikan kandidat long/short?

Kenapa: usulan builder = agen memilih sendiri asetnya tiap hari (maks 5), lalu dipertahankan/dilepas
berdasarkan hasil. Itu butuh (a) daftar aset yang punya DERET cukup panjang, dan (b) ukuran berapa
sering "ganti aset" boleh terjadi supaya tidak sekadar mengejar keberuntungan. Keduanya angka,
bukan opini.

Sonde pertama kita (Hyperliquid BNB perp 1h) memberi 5.001 bar / 208 hari. Pertanyaan yang
dijawab di sini: apakah itu keistimewaan BNB, atau berlaku umum? Kalau ya, maka "agen bebas
memilih" itu nyata dan universe-nya ratusan aset - bukan satu.

Kebijakan uji: panggil candleSnapshot untuk beberapa coin dengan umur/volume berbeda (blue-chip,
mid-cap, dan aset yang dulu jadi satu-satunya edge tervalidasi di korpus: HYPE), lalu laporkan
jumlah bar + rentang hari. Batas respons 5.001 bar adalah langit-langit server, jadi yang diukur
di sini adalah "apakah mentok di langit-langit".

Pakai: python tools/probe_universe_depth.py [COIN COIN ...]
"""
import json
import sys
import time
import urllib.error
import urllib.request

INFO = "https://api.hyperliquid.xyz/info"
UA = {"User-Agent": "Mozilla/5.0 (compatible; lencana-depth/1.0)", "Content-Type": "application/json"}

# sample yang mewakili kelas berbeda, bukan yang paling enak dilihat
DEFAULT = ["BTC", "ETH", "SOL", "HYPE", "SUI", "DOGE", "WIF", "BNB", "CAKE", "LTC"]

# kebutuhan aturan validasi kita (lihat vault/02-Ambang.md): >=20 trade OOS non-overlap 24 jam
NEED_20 = 20 * 24            # 480 bar hourly untuk 20 trade saja
NEED_WF5 = 5 * 20 * 24       # 2.400 bar untuk 5-fold walk-forward dengan 20 trade/fold


def post(payload, timeout=45):
    req = urllib.request.Request(INFO, data=json.dumps(payload).encode(), headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:220]
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {str(e)[:160]}"


st, meta = post({"type": "meta"})
uni = [u.get("name") for u in (meta.get("universe") or [])] if st == 200 else []
print(f"Hyperliquid perp universe: HTTP {st}, {len(uni)} aset")

coins = sys.argv[1:] or DEFAULT
print(f"{'aset':8}{'ada di perp?':14}{'bar 1h':>9}{'rentang hari':>14}  kelas")
print("-" * 72)
kelas = {"BTC": "blue-chip", "ETH": "blue-chip", "SOL": "besar", "HYPE": "edge tervalidasi lama",
         "SUI": "mid", "DOGE": "meme besar", "WIF": "meme", "BNB": "blue-chip eco",
         "CAKE": "DEX BSC", "LTC": "lama"}
rows = []
for c in coins:
    inuni = "YA" if c in uni else "TIDAK"
    end = int(time.time() * 1000)
    st2, d = post({"type": "candleSnapshot",
                   "req": {"coin": c, "interval": "1h", "startTime": end - 1000 * 3600 * 700,
                           "endTime": end}})
    if st2 == 200 and isinstance(d, list):
        n = len(d)
        days = round((d[-1]["t"] - d[0]["t"]) / 3600000 / 24, 1) if n > 1 else 0
        verdict = "mentok 5001" if n >= 5000 else ("cukup 20 trade" if n >= NEED_20 else
                                                  ("cukup 5-fold" if n >= NEED_WF5 else "terlalu pendek"))
        ok = "✅" if n >= NEED_20 else "❌"
        print(f"{c:8}{inuni:14}{n:>9}{days:>14.1f}  {kelas.get(c,'')}  {ok} {verdict}")
        rows.append((c, n, days))
    else:
        print(f"{c:8}{inuni:14}{'-':>9}{'-':>14}  GAGAL {st2} {str(d)[:90]}")
    time.sleep(0.8)

n_ok = sum(1 for _, n, _ in rows if n >= NEED_20)
n_wf = sum(1 for _, n, _ in rows if n >= NEED_WF5)
print(f"\nsample {len(rows)} aset: {n_ok} memenuhi >=20 trade OOS, {n_wf} memenuhi 5-fold penuh")
print(f"kalau ini mewakili {len(uni)} aset -> kandidat long/short yang punya deret cukup: "
      f"sekitar {round(n_ok / max(1, len(rows)) * len(uni))} aset")
print(
    "\nBatas pembacaan: ini bar HISTORIS, bukan bukti ada edge. Yang dia jawab hanya 'bolehkah\n"
    "kami memilih aset secara bebas' - dan untuk itu jawabannya bukan satu aset, tapi ratusan.\n"
    "Yang tetap tidak bisa: aset tanpa deret (memecoin baru) - di sana yang kita ukur kelayakan\n"
    "keluar, bukan arah."
)
