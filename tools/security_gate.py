"""Bidang ④ (keamanan kontrak) untuk KANDIDAT ARAH: ukur, jangan asumsikan.

Kenapa file ini ada: `vault/08` §3 menjadikan "④ terukur (`honeypot`/`can_not_sell` TIDAK null)"
salah satu syarat kursi, tapi sampai 25 Sep jalur arah tidak memanggil satu pun endpoint
keamanan - jadi angka `honeypot=0` di manapun sebenarnya berarti **tidak diukur**, bukan bersih.
Eksit yang dijamin oleh `exit-size <= 1% likuiditas` mengasumsikan jualan DITERIMA kontrak.

Kenapa di jalur arah baru sekarang layak: `vault/05` #12 sudah mengukur tiga jalur ④ mati untuk
jalur SCREEN (40 alamat/snapshot melampaui kuota), tapi kandidatnya arah hanyalah **<= 5** setelah
gerbang arah - dan itu 5 panggilan per siklus. Skala mengubah kesimpulan, jadi yang lama tidak
diulang, hanya dibatasi.

Tiga keadaan yang TIDAK boleh disatukan (ini isi file ini):
  OK         = sumber bilang bisa dijual  (terukur bersih)
  BLOCKED    = honeypot / can_not_sell    (terukur beracun)
  UNMEASURED = field null / HTTP gagal / sumber tidak sepakat pada hal material
               -> BUKAN bersih. Kursi tidak boleh diisi oleh ini.

Dan arah dampaknya sengaja satu-arah seperti di `judge.py`: gerbang ini boleh MEMBATALKAN atau
menandai belum-terverifikasi, tidak pernah membuka posisi yang gerbang lain tolak.

Catatan kelas aset: untuk C1 (meme ber-perp) yang tidak bisa dijual adalah TOKEN DASARNYA, bukan
kontrak perped-nya. Alasannya tetap sah untuk memblokir: harga referensi perp datang dari pasar
spot token yang sama, dan token yang tidak bisa dijual adalah oracle yang bisa disandera.

Pakai:  python tools/security_gate.py                       # kandidat arah dari snapshot terakhir
         python tools/security_gate.py --symbols BREW GENIUS
         python tools/security_gate.py --address 0x... --address 0x...
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

# SATU sumber bentuk permintaan: perekam punya gmgn_url() yang menambahkan timestamp+client_id
# (kunci PRIVAT menagihnya; demo key tidak - lihat vault/06). Mengimpor fungsi itu lebih baik
# daripada menyalin query string, karena salinan adalah cara bug kembali masuk tanpa terlihat.
_SPEC = importlib.util.spec_from_file_location(
    "rec", os.path.join(ROOT, "universe", "record_bsc_universe.py"))
rec = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(rec)

GOPLUS = "https://api.gopluslabs.io/api/v1/token_security/56?contract_addresses="
UA = {"User-Agent": "Mozilla/5.0 (compatible; fabius-security/1.0)", "Accept": "application/json"}

# Field yang menentukan, dan nama aslinya di tiap sumber (mereka TIDAK sama - itu sebabnya
# keduanya dibaca, bukan dipilih satu).
GMGN_KEY_FIELDS = ("is_honeypot", "can_not_sell", "can_sell", "buy_tax", "sell_tax",
                   "blacklist", "hidden_owner", "is_proxy", "is_mintable", "selfdestruct")
TRUTHY = ("1", "true", "yes")


def _t(v):
    """True/False/None - dengan None sebagai TIDAK DIUKUR, bukan False."""
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("", "null", "none", "-"):
        return None
    return s in TRUTHY


def gmgn_security(addr):
    st, body = rec.get(rec.gmgn_url("/v1/token/security", chain="bsc", address=addr),
                       {"X-APIKEY": rec.GMGN_KEY})
    if not isinstance(body, dict) or body.get("_error"):
        return {"_http": st, "_err": str(body.get("_error") or body)[:160]}
    d = body.get("data") if isinstance(body.get("data"), dict) else body
    out = {k: d.get(k) for k in GMGN_KEY_FIELDS if k in d}
    out["_fields"] = len(d)
    out["_sha"] = "0x" + hashlib.sha256(
        json.dumps(d, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
    return out


def goplus_security(addr):
    try:
        import urllib.request
        with urllib.request.urlopen(urllib.request.Request(GOPLUS + addr, headers=UA), timeout=25) as r:
            j = json.loads(r.read().decode())
    except Exception as e:  # noqa: BLE001
        return {"_err": f"{type(e).__name__}: {str(e)[:140]}"}
    res = j.get("result") or {}
    one = res.get(addr.lower()) or res.get(addr) or {}
    if not one:
        return {"_err": "hasil kosong (alamat tidak dikenal GoPlus / belum terindeks)"}
    out = {"is_honeypot": one.get("is_honeypot"), "buy_tax": one.get("buy_tax"),
           "sell_tax": one.get("sell_tax"), "is_proxy": one.get("is_proxy"),
           "is_mintable": one.get("is_mintable"), "holder_count": one.get("holder_count"),
           "_sha": "0x" + hashlib.sha256(
               json.dumps(one, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}
    # GoPlus TIDAK punya can_not_sell - dicatat sebagai ketiadaan field, bukan sebagai nol.
    out["_no_can_not_sell"] = True
    return out


def judge_one(g, p):
    """Gabungan dua sumber -> (status, alasan, detail). Status != OK tidak pernah membuka apa pun."""
    gh, gc = _t(g.get("is_honeypot")), _t(g.get("can_not_sell"))
    ph = _t(p.get("is_honeypot"))
    why, status = [], None
    if gh is True or gc is True or ph is True:
        status = "BLOCKED"
        why.append(f"honeypot gmgn={g.get('is_honeypot')} goplus={p.get('is_honeypot')} "
                   f"can_not_sell={g.get('can_not_sell')}")
    elif gh is None and ph is None:
        status = "UNMEASURED"
        why.append("tidak ada satu pun sumber yang membalas is_honeypot")
    elif gh is None or gc is None:
        status = "UNMEASURED"
        why.append(f"GMGN membalas tapi field kunci null (honeypot={g.get('is_honeypot')} "
                   f"can_not_sell={g.get('can_not_sell')})")
    else:
        status = "OK"
        why.append(f"gmgn honeypot={gh} can_not_sell={gc}; goplus honeypot={ph}")
    # Pajak: selisih ANTAR SUMBER dicatat, dan kalau selisihnya material (>= 5 %) status diturunkan.
    def tax(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return None
    bt_g, bt_p = tax(g.get("buy_tax")), tax(p.get("buy_tax"))
    st_g, st_p = tax(g.get("sell_tax")), tax(p.get("sell_tax"))
    if None not in (st_g, st_p) and abs(st_g - st_p) >= 0.05 and status == "OK":
        status = "DISAGREE"
        why.append(f"sumber beda material soal pajak jual: GMGN {st_g:.2%} vs GoPlus {st_p:.2%}")
    return status, why, {"tax_buy": [bt_g, bt_p], "tax_sell": [st_g, st_p]}


def candidates(symbols=None, addresses=None):
    """Ambil (simbol, alamat) dari snapshot universe terakhir - alamatnya ADA di baris universe."""
    snap = None
    for line in open(os.path.join(ROOT, "universe", "bsc-universe.jsonl"), encoding="utf-8"):
        line = line.strip()
        if line:
            d = json.loads(line)
            if d.get("schema"):
                snap = d
    if not snap:
        raise SystemExit("universe/ kosong - jalankan perekam dulu")
    want_addr = {a.lower() for a in (addresses or [])}
    want_sym = {s.upper() for s in (symbols or [])}
    out = []
    for r in snap["rows"]:
        addr = (r.get("address") or "").lower()
        sym = str(r.get("symbol") or "").upper()
        if not addr or len(addr) != 42:
            continue
        if want_addr and addr not in want_addr:
            continue
        if want_sym and sym not in want_sym:
            continue
        if any(o[1].lower() == addr for o in out):
            continue
        out.append((r.get("symbol") or "?", addr, r))
    return snap, out


def gate_rows(pairs, snap_sha=None):
    """Uji daftar (simbol, alamat) -> daftar rekaman. Dipakai juga oleh `direction.py`.

    Sengaja fungsi, bukan hanya `main()`: gerbang yang cuma bisa dijalankan manusia dari terminal
    akan tertinggal satu langkah di belakang agen, dan `gatesHash` akan mengklaim pemeriksaan yang
    sebenarnya belum terjadi.
    """
    out = []
    for sym, addr in pairs:
        g, p = gmgn_security(addr), goplus_security(addr)
        status, why, det = judge_one(g, p)
        out.append({"kind": "security", "symbol": sym, "address": addr, "status": status,
                    "why": why, "gmgn": {k: v for k, v in g.items() if k != "_raw"},
                    "goplus": p, "tax": det, "universe_snapshot": snap_sha,
                    "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    return out


def table(rows):
    print(f"{'simbol':12}{'status':>12}{'honeypot':>10}{'can_not_sell':>14}{'taxJual(g/g+)':>16}  alasan")
    print("-" * 118)
    for x in rows:
        g = x["gmgn"]
        ts = f"{(x['tax']['tax_sell'][0] if x['tax']['tax_sell'][0] is not None else '-')}" \
             f"/{(x['tax']['tax_sell'][1] if x['tax']['tax_sell'][1] is not None else '-')}"
        print(f"{str(x['symbol'])[:12]:12}{x['status']:>12}{str(g.get('is_honeypot', '-')):>10}"
              f"{str(g.get('can_not_sell', '-')):>14}{ts:>16}  {'; '.join(x['why'])[:70]}")
        if g.get("_err") or x["goplus"].get("_err"):
            print(f"{'':12}  gmgn_err={str(g.get('_err'))[:60]} | "
                  f"goplus_err={str(x['goplus'].get('_err'))[:60]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="*", default=None)
    ap.add_argument("--address", action="append", default=None)
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--limit", type=int, default=5)
    a = ap.parse_args()

    snap, cands = candidates(a.symbols, a.address)
    cands = cands[:a.limit]
    print(f"universe {snap['snapshot_utc']} | kandidat [4] yang akan diukur: {len(cands)} "
          f"(bukan {snap['universe_size']} - itu beban jalur screen yang sudah terbukti tak terbayar)\n")
    if not cands:
        print("Tidak ada kandidat dengan alamat. Periksa --symbols / isi universe.")
        return

    # Satu jalur kode untuk CLI dan untuk `direction.py` (mereka pakai gate_rows/table yang sama),
    # supaya "apa yang dilihat manusia di terminal" adalah "apa yang dilihat agen".
    rows = gate_rows([(s, a) for s, a, _r in cands], snap_sha=snap["sha256"])
    table(rows)

    n_ok = sum(1 for x in rows if x["status"] == "OK")
    n_un = sum(1 for x in rows if x["status"] in ("UNMEASURED", "DISAGREE"))
    n_bl = sum(1 for x in rows if x["status"] == "BLOCKED")
    print(f"\nOK={n_ok}  UNMEASURED/DISAGREE={n_un}  BLOCKED={n_bl}  "
          f"panggilan={len(rows) * 2} (GMGN + GoPlus per kandidat)")
    print("Aturan yang ditegakkan di sini: UNMEASURED TIDAK dihitung sebagai bersih - lihat "
          "vault/08 §3 (syarat kursi) dan judge.py §1 (satu arah).")

    if a.emit:
        os.makedirs(os.path.join(ROOT, "decisions"), exist_ok=True)
        p = os.path.join(ROOT, "decisions", f"security-{time.strftime('%Y%m%d', time.gmtime())}Z.jsonl")
        with open(p, "a", encoding="utf-8") as fh:
            for x in rows:
                fh.write(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"tertulis: {p}")
    return rows


if __name__ == "__main__":
    main()
