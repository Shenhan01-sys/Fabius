"""P163: replay deterministik buku Fabius (meja v2) dari arsip siklus - diagnosis fee per sumber + uji kebijakan perputaran (usulan rumus r4).

Masukan = `GET /desk/archive/<YYYY-MM-DD>` per hari: rekaman konsensus Fabius (agent "v2": bot, instrumen, eksposur, target aturan per siklus, isi,
ekuitas) + harga isi v2 per siklus. Replay memakai `meja.isi` yang sama (fee 0,05 %/sisi, ubah minimum 2 % ekuitas); kebijakan hanya MENGUBAH
target sebelum diisi, arah dari aturan bot tidak disentuh. Replay r3 wajib mengulang ekuitas tercatat (SETIA) sebelum kebijakan lain boleh
dibandingkan; replay harus mulai dari hari pertama buku (buku 10.000 datar).

Pakai:  python -X utf8 tools/meja_replay.py --dari 2026-10-05 --sampai 2026-10-06
Batas:  sampel kecil (±1 hari); kebijakan dipilih menurut prinsip biaya, bukan dicocokkan ke sampel ini (anti-snooping, Epik 11). Siklus yang
        tercatat datar karena rem rugi tidak menyimpan target aturan, jadi tetap datar di semua kebijakan.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Callable, Dict, List, Optional, Tuple

sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]   # tools + akar repo (engine)
import meja  # noqa: E402

GERBANG = "https://fabius-x402-production.up.railway.app"
REM = "daily loss brake"
B2 = "B2-RS"
SUMBER = ("ganti bot", "ganti instrumen", "ubah eksposur", "pembalikan peringkat B2", "rem rugi",        # lima sumber kriteria keluar P163 (1)
          "aturan buka/tutup/balik (bot lain)", "geser bobot (harga/aturan)", "buka awal",              # sisa, supaya total fee utuh
          "buka slot", "SL", "TP", "aturan keluar bot", "r4 start")                                     # r4 (F-D116): sebab tercatat di isi
ALASAN_R4 = {"open": "buka slot", "SL": "SL", "TP": "TP", "daily loss brake": "rem rugi", "r4 start": "r4 start"}
SETIA_USDT = 0.01


def muat(dari: str, sampai: str, gerbang: str = GERBANG) -> Tuple[List[dict], Dict[int, Dict[str, float]]]:
    recs, harga = [], {}
    d0, d1 = dt.date.fromisoformat(dari), dt.date.fromisoformat(sampai)
    while d0 <= d1:
        try:
            req = urllib.request.Request(f"{gerbang}/desk/archive/{d0}", headers={"User-Agent": "fabius-replay"})
            with urllib.request.urlopen(req, timeout=120) as r:
                a = json.loads(r.read().decode())
            recs += a["records"]
            harga.update({int(c["cycle"]): c.get("prices") or {} for c in a["cycles"]})
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
        d0 += dt.timedelta(days=1)
    return sorted(recs, key=lambda r: r["siklus"]), harga


def _rem(r: Optional[dict]) -> bool:
    return bool(r) and REM in (r.get("dasar") or "")


# ---------------------------------------------------------------- kebijakan: target aturan -> target yang diisi

Policy = Callable[[dict, Optional[dict], dict, Dict[str, float]], Dict[str, dict]]


def _w_now(book: dict, harga: Dict[str, float]) -> Dict[str, float]:
    e = meja.ekuitas(book, harga)
    return {a: p["qty"] * harga.get(a, p["masuk"]) / e for a, p in book["posisi"].items()} if e else {}


def r3(rec: dict, prev: Optional[dict], st: dict, w_now: Dict[str, float]) -> Dict[str, dict]:
    return {a: dict(t) for a, t in (rec.get("target") or {}).items()}


def pita_ukuran(band: float = 0.5) -> Policy:
    """Posisi yang sudah dipegang searah TIDAK diubah ukurannya kecuali selisih >= band x ukuran sekarang. Buka, tutup, balik arah tetap jalan."""
    def f(rec, prev, st, w_now):
        tg = r3(rec, prev, st, w_now)
        for a, t in tg.items():
            cur = w_now.get(a, 0.0)
            if cur and t["w"] and (cur > 0) == (t["w"] > 0) and abs(t["w"] - cur) < band * abs(cur):
                t["w"] = cur
        return tg
    return f


def lekat_instrumen(n: int = 3) -> Policy:
    """Instrumen yang dipegang lalu keluar dari daftar instrumen konsensus tetap dipegang (bobot sekarang) sampai n siklus berturut tidak dipilih,
    selama bot sama. Instrumen yang masih dipilih tetapi didatarkan aturan TETAP ditutup (arah milik aturan); ganti bot + rem rugi langsung."""
    def f(rec, prev, st, w_now):
        tg = r3(rec, prev, st, w_now)
        if _rem(rec) or prev is None or rec.get("bot") != prev.get("bot"):
            st.clear()
            return tg
        now_i, prev_i = set(rec.get("instrumen") or []), set(prev.get("instrumen") or [])
        for a, w in w_now.items():
            if a in tg or a in now_i or a not in prev_i | set(st) or abs(w) < 1e-9:
                st.pop(a, None)
                continue
            st[a] = st.get(a, 0) + 1
            if st[a] < n:
                tg[a] = {"w": w, "k": 1.0}
        return tg
    return f


def jeda(siklus_min: int = 6) -> Policy:
    """Posisi hanya diubah tiap >= siklus_min siklus, kecuali bot berganti atau rem rugi (dua-duanya langsung)."""
    def f(rec, prev, st, w_now):
        tg = r3(rec, prev, st, w_now)
        if prev is None or rec.get("bot") != prev.get("bot") or _rem(rec) or rec["siklus"] - st.get("terakhir", -10 ** 12) >= siklus_min * 300:
            st["terakhir"] = rec["siklus"]
            return tg
        return {a: {"w": w, "k": 1.0} for a, w in w_now.items()}
    return f


def gabung(*ps: Policy) -> Policy:
    def f(rec, prev, st, w_now):
        tg = None
        for i, p in enumerate(ps):
            tg = p({**rec, "target": tg} if tg is not None else rec, prev, st.setdefault(i, {}), w_now)
        return tg
    return f


KEBIJAKAN: Dict[str, Policy] = {
    "r3 (sekarang)": r3,
    "pita ukuran 50%": pita_ukuran(0.5),
    "lekat instrumen 3 siklus": lekat_instrumen(3),
    "jeda 6 siklus (30 menit)": jeda(6),
    "lekat 3 + pita 50%": gabung(lekat_instrumen(3), pita_ukuran(0.5)),
}
KEPEKAAN: Dict[str, Policy] = {                                                                     # tetangga parameter (--kepekaan): hasil tidak boleh bergantung satu titik
    "jeda 3 siklus (15 menit)": jeda(3),
    "jeda 12 siklus (60 menit)": jeda(12),
    "lekat instrumen 6 siklus": lekat_instrumen(6),
    "pita ukuran 25%": pita_ukuran(0.25),
    "jeda 6 + lekat 3": gabung(lekat_instrumen(3), jeda(6)),
}


# ---------------------------------------------------------------- replay + diagnosis

def replay(recs: List[dict], harga: Dict[int, Dict[str, float]], pol: Policy = r3, rugi_maks: float = 0.03) -> dict:
    """Rem rugi harian (SK-M10) dihitung ulang dari ekuitas replay, sama dengan `meja2.siklus2`: ekuitas sebelum isi vs ekuitas awal hari UTC.
    Rekaman r4 (punya `slot`): target aturan direkam utuh dan rem di `dasar` milik buku slot, jadi diabaikan - bayangan r3 memakai remnya sendiri."""
    book, st, prev, hari = meja.buku_baru(), {}, None, {}
    eq, fee, isi, puncak, dd, kirim, rem = [], 0.0, 0, meja.PARAMS["modal_awal"], 0.0, [], 0
    for r in recs:
        h = harga.get(int(r["siklus"]))
        if not h:
            continue
        if "slot" in r:
            r = {**r, "dasar": (r.get("dasar") or "").replace(REM, "r4 slot brake")}
        e0 = meja.ekuitas(book, h)
        d = int(r["siklus"]) // 86_400
        hari.setdefault(d, e0)
        if e0 / hari[d] - 1 <= -rugi_maks and not _rem(r):
            r = {**r, "target": {}, "dasar": f"{r.get('dasar') or ''}; {REM} (replay)"}
            rem += 1
        f = meja.isi(book, pol(r, prev, st, _w_now(book, h)), h)
        kirim.append((r, f))
        fee += sum(x["fee"] for x in f)
        isi += len(f)
        e = meja.ekuitas(book, h)
        eq.append((r["siklus"], e))
        puncak = max(puncak, e)
        dd = min(dd, e / puncak - 1)
        prev = r
    akhir: Dict[str, float] = {}
    for t, e in eq:                                                                                  # ekuitas akhir tiap hari UTC
        akhir[dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d")] = e
    lalu, ph = meja.PARAMS["modal_awal"], {}
    for d in sorted(akhir):                                                                          # % per hari = akhir hari vs akhir hari lalu
        ph[d] = round((akhir[d] / lalu - 1) * 100, 3)
        lalu = akhir[d]
    return {"ekuitas": round(eq[-1][1], 2) if eq else None, "fee": round(fee, 2), "isi": isi, "dd_pct": round(dd * 100, 3),
            "rem_replay": rem, "per_hari_pct": ph, "seri": eq, "kirim": kirim, "buku": book, "hari": hari}


def sebab(x: dict, r: dict, prev: Optional[dict]) -> str:
    """Satu isi -> satu sebab (urutan = prioritas): rem rugi (tutup, atau buka lagi sesudah rem) > ganti bot > ganti instrumen (aset masuk/keluar
    daftar instrumen konsensus) > pembalikan peringkat B2 (B2-RS, aset tetap dipilih tetapi aturan membuka/menutup/membalik) > aturan bot lain >
    ubah eksposur (searah, eksposur konsensus berubah) > geser bobot (searah, eksposur sama: harga bergerak atau bobot aturan berubah)."""
    al = x.get("alasan")
    if al:                                                                                       # r4: sebab sudah tercatat di isi
        return ALASAN_R4.get(al) or ("aturan keluar bot" if al.startswith("exit rule") else al)
    d0, d1 = x["dari"], x["ke"]
    if prev is None:
        return "buka awal"
    if (_rem(r) and abs(d1) < 1e-9) or (_rem(prev) and not _rem(r)):
        return "rem rugi"
    if r.get("bot") != prev.get("bot"):
        return "ganti bot"
    if (x["aset"] in (r.get("instrumen") or [])) != (x["aset"] in (prev.get("instrumen") or [])):
        return "ganti instrumen"
    if abs(d0) < 1e-9 or abs(d1) < 1e-9 or (d0 > 0) != (d1 > 0):
        return "pembalikan peringkat B2" if r.get("bot") == B2 else "aturan buka/tutup/balik (bot lain)"
    if abs((r.get("eksposur") or 0) - (prev.get("eksposur") or 0)) > 1e-9:
        return "ubah eksposur"
    return "geser bobot (harga/aturan)"


def sumber_fee(recs: List[dict]) -> Dict[str, dict]:
    """Fee TERCATAT (isi di rekaman) dipecah per sebab; jumlah semua sebab = total fee tercatat."""
    out: Dict[str, dict] = {}
    prev = None
    for r in recs:
        for x in r.get("isi") or []:
            o = out.setdefault(sebab(x, r, prev), {"isi": 0, "fee": 0.0})
            o["isi"] += 1
            o["fee"] = round(o["fee"] + x["fee"], 6)
        prev = r
    return dict(sorted(out.items(), key=lambda kv: -kv[1]["fee"]))


def lama_pegang(recs: List[dict]) -> dict:
    """Lama hidup posisi TERCATAT (buka/arah baru -> tutup/balik), dalam siklus 5 menit, + fee buka+tutup posisi yang hidup <= 2 siklus."""
    buka, lama, fee_pendek = {}, [], 0.0
    for r in recs:
        for x in r.get("isi") or []:
            a, d0, d1, t = x["aset"], x["dari"], x["ke"], int(r["siklus"])
            if abs(d0) > 1e-9 and (abs(d1) < 1e-9 or (d0 > 0) != (d1 > 0)) and a in buka:
                t_buka, f_buka = buka.pop(a)
                lama.append((t - t_buka) // 300)
                fee_pendek += (f_buka + x["fee"]) if lama[-1] <= 2 else 0.0
            if abs(d1) > 1e-9 and (abs(d0) < 1e-9 or (d0 > 0) != (d1 > 0)):
                buka[a] = (t, x["fee"])
    lama.sort()
    n = len(lama) or 1
    return {"posisi": len(lama), "median_siklus": lama[len(lama) // 2] if lama else None,
            "maks_n_siklus_pct": {k: round(sum(1 for v in lama if v <= k) / n * 100, 1) for k in (1, 2, 6, 12)}, "fee_posisi_maks_2_siklus": round(fee_pendek, 2)}


def laporan(recs: List[dict], harga: Dict[int, Dict[str, float]], kepekaan: bool = False, store=None) -> dict:
    """Seluruh keluaran P163 dalam satu dict (dipakai CLI + tes integrasi). Rekaman dibagi menurut rumus: r1-r3 (tanpa `slot`) = analisis perputaran
    + kebijakan (replay r3 wajib SETIA); r4 (punya `slot`, F-D116) = buku slot tercatat vs BAYANGAN r3 (rumus r3 pada target aturan yang sama sejak
    siklus pertama, rem sendiri) - kriteria keluar P163 (4). `store` (candle harian) -> replay slot dilanjutkan dari buku r3 wajib SETIA juga."""
    r3s, r4s = [r for r in recs if "slot" not in r], [r for r in recs if "slot" in r]
    out = {"siklus": len(recs), "harga_siklus": sum(1 for r in recs if harga.get(int(r["siklus"]))), "ekuitas_tercatat": recs[-1]["ekuitas"],
           "fee_tercatat": round(sum(x["fee"] for r in recs for x in r.get("isi") or []), 6), "sumber": sumber_fee(recs),
           "lama_pegang": lama_pegang(r3s), "lama_pegang_r4": lama_pegang(r4s), "setia": True, "replay": {}}
    if r3s:
        pols = {**KEBIJAKAN, **(KEPEKAAN if kepekaan else {})}
        out["replay"] = {nama: {k: v for k, v in replay(r3s, harga, pol).items() if k not in ("seri", "kirim", "buku", "hari")} for nama, pol in pols.items()}
        out["ekuitas_tercatat_r3"] = r3s[-1]["ekuitas"]
        base = out["replay"]["r3 (sekarang)"]
        out["setia"] = base["ekuitas"] is not None and abs(base["ekuitas"] - r3s[-1]["ekuitas"]) <= SETIA_USDT
    if r4s:
        bay = replay(recs, harga, r3)
        r4 = {"siklus": len(r4s), "mulai": r4s[0]["siklus"], "ekuitas_tercatat": r4s[-1]["ekuitas"],
              "fee": round(sum(x["fee"] for r in r4s for x in r.get("isi") or []), 4), "isi": sum(len(r.get("isi") or []) for r in r4s),
              "slot_terbuka": len(r4s[-1]["slot"]), "bayangan_r3": {k: bay[k] for k in ("ekuitas", "fee", "isi", "dd_pct", "rem_replay")}}
        e_bay_mulai = next((e for t, e in reversed(bay["seri"]) if t < r4s[0]["siklus"]), meja.PARAMS["modal_awal"])
        r4["sejak_r4_pct"] = round((r4s[-1]["ekuitas"] / (r3s[-1]["ekuitas"] if r3s else meja.PARAMS["modal_awal"]) - 1) * 100, 3)
        r4["bayangan_r3"]["sejak_r4_pct"] = round((bay["ekuitas"] / e_bay_mulai - 1) * 100, 3) if bay["ekuitas"] else None
        if store is not None:
            awal = replay(r3s, harga, r3) if r3s else None
            x = replay_slot(r4s, harga, store, awal=(awal["buku"], awal["hari"]) if awal else None, bot_lalu=r3s[-1].get("bot") if r3s else None)
            r4["replay_slot_ekuitas"] = x["ekuitas"]
            r4["setia"] = x["ekuitas"] is not None and abs(x["ekuitas"] - r4s[-1]["ekuitas"]) <= SETIA_USDT
            out["setia"] = out["setia"] and r4["setia"]
        out["r4"] = r4
    return out


# ---------------------------------------------------------------- r4 slot posisi (F-D116, usulan): candle harian perp + replay

class CandleVision:
    """Candle harian perp dari Binance Vision (berkas statis, sama dengan REST: F-D83), `hari` hari sebelum `sampai_ms`, cache disk per aset.
    Baris = (t buka ms, o, h, l, c, volume kuotasi) seperti `meja2.Pasar2.harian`."""

    def __init__(self, sampai_ms: int, hari: int = 130, cache_dir: Optional[str] = None, fetch: Optional[Callable[[str], Optional[bytes]]] = None):
        import tempfile
        self.sampai, self.mulai = sampai_ms, sampai_ms - hari * 86_400_000
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "fabius-vision-1d")
        self.fetch = fetch
        self._rows: Dict[str, List[tuple]] = {}

    def _get(self, url: str) -> Optional[bytes]:
        if self.fetch is None:
            import feed_bars
            self.fetch = feed_bars.http_get
        return self.fetch(url)

    @staticmethod
    def _parse(blob: bytes) -> List[tuple]:
        import csv
        import io
        import zipfile
        z = zipfile.ZipFile(io.BytesIO(blob))
        with z.open(z.namelist()[0]) as f:
            return [(int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[7]))
                    for r in csv.reader(io.TextIOWrapper(f)) if r and r[0].strip().isdigit()]

    def _unduh(self, a: str) -> List[tuple]:
        base, rows = "https://data.binance.vision/data/futures/um", []
        d = dt.datetime.fromtimestamp(self.mulai / 1000, dt.timezone.utc).date().replace(day=1)
        akhir = dt.datetime.fromtimestamp(self.sampai / 1000, dt.timezone.utc).date()
        while d <= akhir:
            nxt = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
            blob = self._get(f"{base}/monthly/klines/{a}/1d/{a}-1d-{d:%Y-%m}.zip") if nxt <= akhir else None
            if blob:
                rows += self._parse(blob)
            else:                                                                                 # bulan berjalan / zip bulanan belum terbit
                h = d
                while h < min(nxt, akhir):
                    b = self._get(f"{base}/daily/klines/{a}/1d/{a}-1d-{h}.zip")
                    rows += self._parse(b) if b else []
                    h += dt.timedelta(days=1)
            d = nxt
        return sorted({r[0]: r for r in rows if r[0] < self.sampai}.values())

    def rows(self, a: str) -> List[tuple]:
        if a not in self._rows:
            path = os.path.join(self.cache_dir, f"{a}-{self.sampai}.json")
            if os.path.exists(path):
                self._rows[a] = [tuple(r) for r in json.load(open(path, encoding="utf-8"))]
            else:
                self._rows[a] = self._unduh(a)
                os.makedirs(self.cache_dir, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self._rows[a], f)
        return self._rows[a]


def _pasar_arsip(store, t: int, _cache: Dict[tuple, object] = {}):  # noqa: B006 - cache seri per (store, aset, hari) disengaja
    """`meja2.Pasar2` pada waktu `t`: candle harian yang sudah tutup sebelum t (panjang = `harian_limit` - 1 seperti REST hidup)."""
    import meja2
    from engine.series import Series

    class PasarArsip(meja2.Pasar2):
        def harian(self, a):
            key = (id(store), a, t // 86_400)
            if key not in _cache:
                rows = [r for r in store.rows(a) if r[0] + 86_400_000 <= t * 1000][-(meja2.PARAMS2["harian_limit"] - 1):]
                _cache[key] = Series.from_rows(rows) if rows else None
            if _cache[key] is None:
                raise ValueError(f"tidak ada candle harian {a}")
            return _cache[key]

        def onboard(self):                                                                       # perkiraan: candle pertama di jendela = listing
            return {a: (r[0][0] if r and r[0][0] > store.mulai + 86_400_000 else 0) for a, r in store._rows.items()}
    return PasarArsip(get=None, now=lambda: t)


def replay_slot(recs: List[dict], harga: Dict[int, Dict[str, float]], store, P: Optional[dict] = None, rugi_maks: float = 0.03,
                awal: Optional[tuple] = None, bot_lalu: Optional[str] = None) -> dict:
    """Replay r4 slot (F-D116) pada siklus + harga tercatat, langkah yang sama dengan `meja2.siklus2`: migrasi posisi r3, kandidat dari target aturan
    tercatat (hanya konsensus sah = ada `skor_instrumen`), aturan keluar bot dijalankan ulang oleh `meja2.arah` (kode terkunci) pada candle harian,
    rem rugi dari ekuitas buku sendiri. `awal` = (buku, hari) hasil replay r3 sebelum r4 mulai (transisi produksi); tanpa itu buku baru 10.000."""
    import copy
    import meja2
    import meja_slot as ms
    P = P or ms.PARAMS_SLOT
    b, hari = (copy.deepcopy(awal[0]), dict(awal[1])) if awal else (ms.buku_baru(), {})
    aturan, terakhir = {}, {}
    eq, kirim, alasan, pegang, puncak, dd, maks_buka, tanpa_harga = [], [], {}, [], meja.PARAMS["modal_awal"], 0.0, 0, 0
    for r in recs:
        t = int(r["siklus"])
        if not harga.get(t):
            continue
        tanpa_harga += sum(1 for a in b["posisi"] if a not in harga[t])
        terakhir.update(harga[t])
        h = {**terakhir, **harga[t]}                                  # aset dipegang yang keluar dari universe harga v2: harga terakhir (basi, dihitung)
        p = _pasar_arsip(store, t)
        e0 = ms.ekuitas(b, h)
        hari.setdefault(t // 86_400, e0)
        rem = e0 / hari[t // 86_400] - 1 <= -rugi_maks

        def atr(a, p=p):
            try:
                return ms.atr_frac(p.harian(a), P["atr_hari"])
            except Exception:  # noqa: BLE001
                return None

        def keluar(pos, p=p, t=t):                                                              # sama dengan `meja2.siklus2.keluar`
            key = (pos["bot"], tuple(sorted(pos.get("uni") or [])), t // 86_400)
            if key not in aturan:
                aturan[key] = meja2.aturan_terbaca(pos["bot"], list(pos.get("uni") or []), p)
            if aturan[key] is None:
                return False
            w = aturan[key].get(pos["aset"], 0.0)
            return (1 if w > 1e-12 else -1 if w < -1e-12 else 0) != pos["arah"]
        buka_t = {a: x.get("t", t) for a, x in b["posisi"].items()}
        f = ms.migrasi(b, h, bot_lalu) + ms.langkah(b, t, h, [] if rem or "skor_instrumen" not in r else ms.kandidat(r, atr), keluar, rem, P)
        bot_lalu = r.get("bot")
        for x in f:
            if x["alasan"] not in ("open", "r4 start"):
                key = "TP" if x["alasan"] == "TP" else "SL" if x["alasan"] == "SL" else "rem rugi" if x["alasan"] == "daily loss brake" else "aturan keluar bot"
                alasan[key] = alasan.get(key, 0) + 1
                pegang.append((t - buka_t[x["aset"]]) // 300)
        kirim.append((r, f))
        maks_buka = max(maks_buka, len(b["posisi"]))
        e = ms.ekuitas(b, h)
        eq.append((t, e))
        puncak = max(puncak, e)
        dd = min(dd, e / puncak - 1)
    akhir: Dict[str, float] = {}
    for t, e in eq:
        akhir[dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d")] = e
    lalu, ph = meja.PARAMS["modal_awal"], {}
    for d in sorted(akhir):
        ph[d] = round((akhir[d] / lalu - 1) * 100, 3)
        lalu = akhir[d]
    n_isi = sum(len(f) for _, f in kirim)
    return {"ekuitas": round(eq[-1][1], 2) if eq else None, "fee": round(b["biaya"], 2), "isi": n_isi, "dd_pct": round(dd * 100, 3),
            "per_hari_pct": ph, "buka": sum(1 for _, f in kirim for x in f if x["alasan"] == "open"), "tutup_per_alasan": alasan,
            "pegang_median_siklus": sorted(pegang)[len(pegang) // 2] if pegang else None, "maks_posisi_terbuka": maks_buka,
            "masih_terbuka": len(b["posisi"]), "siklus_posisi_tanpa_harga": tanpa_harga, "buku": b, "seri": eq, "kirim": kirim}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dari", required=True)
    ap.add_argument("--sampai", required=True)
    ap.add_argument("--gerbang", default=GERBANG)
    ap.add_argument("--json", action="store_true", help="cetak laporan sebagai JSON")
    ap.add_argument("--kepekaan", action="store_true", help="tambah tetangga parameter kebijakan (uji kepekaan)")
    ap.add_argument("--slot", action="store_true", help="replay usulan r4 slot posisi (F-D116); candle harian perp dari Binance Vision")
    a = ap.parse_args()
    recs, harga = muat(a.dari, a.sampai, a.gerbang)
    if not recs:
        print("tidak ada rekaman")
        return 1
    store = CandleVision((int(recs[-1]["siklus"]) // 86_400 + 1) * 86_400_000) if a.slot else None
    lp = laporan(recs, harga, a.kepekaan, store if any("slot" in r for r in recs) else None)
    if a.json:
        print(json.dumps(lp, indent=1, ensure_ascii=False))
        return 0 if lp["setia"] else 2
    print(f"rekaman Fabius: {lp['siklus']} siklus ({recs[0]['siklus']} .. {recs[-1]['siklus']}), berharga {lp['harga_siklus']}, "
          f"ekuitas tercatat {lp['ekuitas_tercatat']:.2f}")
    tot = lp["fee_tercatat"] or 1e-12
    print(f"\nFEE TERCATAT per sumber (total {lp['fee_tercatat']:.2f} USDT):")
    for k, v in lp["sumber"].items():
        print(f"  {k:36s} {v['isi']:4d} isi  {v['fee']:8.2f} USDT  ({v['fee'] / tot * 100:5.1f} %)")
    for judul, key in (("r1-r3", "lama_pegang"), ("r4", "lama_pegang_r4")):
        lp_ = lp[key]
        if lp_["posisi"]:
            print(f"\nLAMA PEGANG posisi tercatat {judul}: {lp_['posisi']} posisi, median {lp_['median_siklus']} siklus; ditutup <= 1/2/6/12 siklus: "
                  f"{' / '.join(f'{v} %' for v in lp_['maks_n_siklus_pct'].values())}; fee buka+tutup posisi <= 2 siklus {lp_['fee_posisi_maks_2_siklus']:.2f} USDT")
    if lp["replay"]:
        print("\nREPLAY r1-r3 (arah aturan bot sama, target diubah kebijakan):")
        for nama, x in lp["replay"].items():
            hari = "  ".join(f"{d[5:]} {v:+6.2f} %" for d, v in x["per_hari_pct"].items())
            print(f"  {nama:26s} ekuitas {x['ekuitas']:9.2f}  fee {x['fee']:7.2f}  isi {x['isi']:4d}  dd {x['dd_pct']:6.2f} %  rem+{x['rem_replay']:<3d} {hari}")
        base = lp["replay"]["r3 (sekarang)"]["ekuitas"]
        print(f"  replay r3 vs tercatat (akhir r1-r3): {base - lp['ekuitas_tercatat_r3']:+.4f} USDT")
    if "r4" in lp:
        r4, bay = lp["r4"], lp["r4"]["bayangan_r3"]
        print(f"\nR4 SLOT POSISI TERCATAT (F-D116, sejak {dt.datetime.fromtimestamp(r4['mulai'], dt.timezone.utc):%m-%d %H:%MZ}, {r4['siklus']} siklus): "
              f"ekuitas {r4['ekuitas_tercatat']:.2f} ({r4['sejak_r4_pct']:+.3f} % sejak r4), fee {r4['fee']:.2f}, isi {r4['isi']}, slot terbuka {r4['slot_terbuka']}")
        print(f"  BAYANGAN r3 (target aturan yang sama, rem sendiri): ekuitas {bay['ekuitas']:.2f} ({bay['sejak_r4_pct']:+.3f} % sejak r4), fee total {bay['fee']:.2f}, "
              f"isi total {bay['isi']}, dd {bay['dd_pct']:.2f} %")
        if "replay_slot_ekuitas" in r4:
            print(f"  replay slot vs tercatat: {r4['replay_slot_ekuitas'] - r4['ekuitas_tercatat']:+.4f} USDT -> {'SETIA' if r4['setia'] else 'TIDAK SETIA'}")
    if a.slot:                                                                                   # kontrafaktual: r4 seandainya jalan sejak siklus pertama
        x = replay_slot(recs, harga, store)
        hari = "  ".join(f"{d[5:]} {v:+6.2f} %" for d, v in x["per_hari_pct"].items())
        print(f"\nKONTRAFAKTUAL r4 sejak siklus pertama: ekuitas {x['ekuitas']:9.2f}  fee {x['fee']:7.2f}  isi {x['isi']:4d}  dd {x['dd_pct']:6.2f} %  {hari}")
        print(f"  buka {x['buka']}, tutup per alasan {x['tutup_per_alasan']}, median lama pegang {x['pegang_median_siklus']} siklus, "
              f"maks terbuka {x['maks_posisi_terbuka']}, masih terbuka {x['masih_terbuka']}, siklus-posisi berharga basi {x['siklus_posisi_tanpa_harga']}")
        for aset, ps in sorted(x["buku"]["posisi"].items()):
            print(f"    terbuka {aset:14s} {ps['bot']:16s} arah {ps['arah']:+d}  margin {ps['margin']:.3f} x {ps['leverage']:.2f}  masuk {ps['masuk']}")
    print(f"\nPUTUSAN: {'SETIA' if lp['setia'] else 'TIDAK SETIA (kebijakan lain tidak boleh dibandingkan)'}")
    return 0 if lp["setia"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
