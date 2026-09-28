"""Gerbang ⑦ sebagai PERILAKU agen: kerumunan jual = VETO membuka posisi. Satu tempat, cuma mengurangi.

Sampai 28 Sep jam 11:4xZ, gerbang ⑦ masih "hasil studi": angkanya ada di vault, tapi tidak ada satu
baris kode di jalur keputusan yang membacanya. Demo yang jujur butuh sebaliknya - agen yang **menolak**
sebuah posisi karena alasan yang terikat waktu, bukan tabel di slide.

Yang dipasang di sini adalah satu-satunya klaim ⑦ yang lolos uji (F-D31, `tools/policy_test.py`
+ `tools/mirror_test.py`): kerumunan JUAL menurunkan peluang jackpot. Terukur pada 1.014 kejadian:
`jual_2` memangkas P(net >= +500 bps) dari **33,9 % -> 22,5 %** (Fisher satu arah p=0,003-0,021,
lolos BH alpha 0,10), dan harapan yang di-winsor naik dari +82,7 ke **+162,3 bps/posisi** hanya
dengan menolak 13,6 % kejadian. Yang TIDAK ikut dipasang: kerumunan BELI sebagai sinyal masuk -
dia sudah dibatalkan F-D30 (artefak harga masuk) dan kalah dari control acak.

Aturan yang membuatnya aman untuk dipakai agen, bukan cuma akurat untuk kertas:
  - **satu arah**: hanya boleh mematikan/menahan `side`, tidak pernah menambah keyakinan;
  - **"tidak ada data" != "boleh"**: berkas aliran yang basi atau token yang tidak pernah terlihat
    mengembalikan `TAK ADA DATA` (dicatat, tidak lulus diam-diam) - [[Concepts/Unmeasured Is Not Clean]];
  - **segarnya diukur dari berkasnya sendiri**, bukan jam laptop: stempel baris terakhir vs `now`.

Pakai:  python -X utf8 tools/flow_gate.py --self-test
       python -X utf8 tools/flow_gate.py 0x<alamat>            # satu token, apa yang lihat agen
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FLOW = os.path.join(ROOT, "universe", "wallet-flow.jsonl")

JENDELA_M = 15          # jendela lihat - sama dengan `mirror_test.bangun(..., window=15)`
MAKER_MIN = 2           # >= 2 maker berbeda menjual -> kerumunan
RASIO_JUAL = 1.5        # atau USD jual >= 1,5 x USD beli di jendela yang sama
SEGAR_MENIT = 20        # berkas lebih tua dari ini -> TAK ADA DATA (rantai mati, bukan pasar sepi)

_BOBOT = {}             # cache per proses, di-invalidate oleh ISI ekor berkas (lihat `_tanda`)


def _tanda(path):
    """Tanda cache yang tidak bisa dibohongi oleh tulis-ulang berukuran sama.

    `mtime+size` saja TIDAK cukup: berkas test yang ditulis ulang dengan panjang identik
    mengembalikan isi LAMA, dan di produksi itu berarti agen mengambil keputusan dari potongan
    aliran yang sudah lewat. Jadi 2 KB terakhir berkas ikut di-hash - murah, dan cukup untuk
    membedakan dua kondisi yang berbeda.
    """
    try:
        st = os.stat(path)
    except OSError:
        return None
    ekor = b""
    try:
        with io.open(path, "rb") as fh:
            fh.seek(max(0, st.st_size - 2048))
            ekor = fh.read()
    except OSError:
        ekor = b""
    return (path, st.st_size, hashlib.sha256(ekor).hexdigest()[:16])


def _load(path):
    tanda = _tanda(path)
    if tanda is None:
        return {}, 0
    if _BOBOT.get("tanda") == tanda:
        return _BOBOT["isi"], _BOBOT["ekor"]
    isi, ekor = {}, 0
    for ln in io.open(path, encoding="utf-8", errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        t = int(d.get("t") or 0)
        if t > ekor:
            ekor = t
        if d.get("k") not in ("tx", "txc"):
            continue
        tk = str(d.get("tk") or "").lower()
        if not tk or not t:
            continue
        isi.setdefault(tk, []).append((t, str(d.get("m") or "").lower(), bool(d.get("b")),
                                       float(d.get("u") or 0.0)))
    for tk in isi:
        isi[tk].sort(key=lambda r: r[0])
    _BOBOT.update({"tanda": tanda, "isi": isi, "ekor": ekor})
    return isi, ekor


def state(address, now=None, path=FLOW, jendela=JENDELA_M):
    """Keadaan aliran ⑦ untuk satu token, sejujur-jujurnya."""
    tk = str(address or "").lower()
    isi, ekor = _load(path)
    kini = now or int(time.time())
    usia = round((kini - ekor) / 60.0, 1) if ekor else None
    dasar = {"sumber": os.path.relpath(path, ROOT).replace("\\", "/"), "stempel_terakhir": ekor,
             "usia_berkas_menit": usia, "jendela_menit": jendela, "token": tk or None}
    if not ekor:
        return {**dasar, "status": "TAK ADA DATA", "alasan": "berkas aliran kosong"}
    if ekor < kini - SEGAR_MENIT * 60:
        # Rantai perekam mati: bukan "tidak ada jual", tapi "kami tidak tahu apa-apa".
        return {**dasar, "status": "TAK ADA DATA",
                "alasan": "aliran basi %d menit (> %d) - perekam ⑦ berhenti"
                          % (int((kini - ekor) // 60), SEGAR_MENIT)}
    rows = isi.get(tk)
    if not rows:
        return {**dasar, "status": "TAK ADA DATA", "alasan": "token tidak pernah terlihat di ⑦"}
    lo = kini - jendela * 60
    w = [r for r in rows if lo <= r[0] <= kini]
    jual = [r for r in w if not r[2]]
    beli = [r for r in w if r[2]]
    mk_jual = {r[1] for r in jual if r[1]}
    usd_jual = sum(r[3] for r in jual)
    usd_beli = sum(r[3] for r in beli)
    hasil = {**dasar, "maker_jual": len(mk_jual), "jual_ada": len(jual), "beli_ada": len(beli),
             "usd_jual": round(usd_jual, 2), "usd_beli": round(usd_beli, 2),
             "stempel_baris_terakhir": rows[-1][0]}
    if len(mk_jual) >= MAKER_MIN:
        return {**hasil, "status": "VETO",
                "alasan": "%d maker berbeda menjual dalam %d m" % (len(mk_jual), jendela)}
    if usd_jual >= RASIO_JUAL * max(usd_beli, 1.0) and usd_jual > 0:
        return {**hasil, "status": "VETO",
                "alasan": "USD jual %.0f >= %.1fx USD beli %.0f dalam %d m (jual bersih)"
                          % (usd_jual, RASIO_JUAL, usd_beli, jendela)}
    return {**hasil, "status": "BOLEH", "alasan": "tidak ada kerumunan jual di jendela lihat"}


def apply(d, fg):
    """Hanya mengurangi. `d` adalah dict keputusan dari `decide_one`."""
    st = (fg or {}).get("status")
    why = d.setdefault("why", [])
    if st == "VETO":
        if d.get("side") and d["side"] != "flat":
            why.append("[7] kerumunan jual TERUKUR (%s) -> arah DIBATALKAN" % fg["alasan"])
        else:
            why.append("[7] kerumunan jual TERUKUR (%s)" % fg["alasan"])
        d["side"], d["regime"] = "flat", "flow-veto-7"
        d["seat_eligible"] = False
        d.setdefault("seat_blockers", []).append("[7]jual-ramai")
    elif st == "TAK ADA DATA":
        # Tidak mematikan kursi, tapi tidak pernah lulus diam-diam: ia tercatat dan ikut di-hash.
        why.append("[7] TAK ADA DATA (%s) - tidak dianggap bersih" % fg.get("alasan"))
        d["flow_note"] = "unmeasured"
    return d


def self_test():
    """Empat keadaan yang tidak boleh tertukar: veto maker, veto rasio, boleh, dan TAK ADA DATA."""
    now = 1_800_000_000
    tmp = os.path.join(ROOT, ".qwen", "tmp_flow_gate.jsonl")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)

    def tulis(baris):
        with io.open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            for b in baris:
                fh.write(json.dumps(b) + "\n")

    def tx(t, maker, buy, usd, tk="0xtok"):
        return {"k": "tx", "t": t, "tk": tk, "m": maker, "b": 1 if buy else 0, "u": usd, "p": 1.0,
                "y": "T", "h": "h%03d" % (t % 997)}
    tulis([tx(now - 60, "0xa", False, 400.0), tx(now - 120, "0xb", False, 300.0)])
    r = state("0xTOK", now=now, path=tmp)
    assert r["status"] == "VETO" and r["maker_jual"] == 2, r
    tulis([tx(now - 60, "0xa", False, 900.0), tx(now - 90, "0xa", True, 100.0)])
    r = state("0xtok", now=now, path=tmp)
    assert r["status"] == "VETO" and "jual bersih" in r["alasan"], r
    tulis([tx(now - 60, "0xa", False, 100.0), tx(now - 90, "0xa", True, 900.0)])
    r = state("0xtok", now=now, path=tmp)
    assert r["status"] == "BOLEH", r
    tulis([tx(now - (SEGAR_MENIT + 20) * 60, "0xa", False, 400.0)])   # ekor berkas basi
    r = state("0xtok", now=now, path=tmp)
    assert r["status"] == "TAK ADA DATA" and "basi" in r["alasan"], r
    tulis([tx(now - 60, "0xa", True, 10.0)])
    r = state("0xlain", now=now, path=tmp)                 # token tak dikenal
    assert r["status"] == "TAK ADA DATA" and "tidak pernah" in r["alasan"], r
    # apply() diuji dengan keadaan VETO yang direkayasa: yang mau dibuktikan di sini adalah "hanya
    # mengurangi" - side jadi flat, regime diganti, kursi dicabut, dan tidak ada jalur yang bisa
    # membuat `side` justru MUNCUL.
    d = apply({"side": "long", "regime": "stop-loss", "seat_eligible": True, "seat_blockers": []},
              {"status": "VETO", "alasan": "sintetis"})
    assert d["side"] == "flat" and d["regime"] == "flow-veto-7", d
    assert d["seat_eligible"] is False and d["seat_blockers"] == ["[7]jual-ramai"], d
    naik = apply({"side": "flat", "regime": "flat", "why": []}, {"status": "BOLEH"})
    assert naik["side"] == "flat" and "unmeasured" not in naik, naik
    ragu = apply({"side": "flat", "regime": "flat", "why": []}, {"status": "TAK ADA DATA",
                                                                 "alasan": "sintetis"})
    assert ragu.get("flow_note") == "unmeasured", ragu
    os.remove(tmp)
    print("self-test ⑦ OK: veto-maker / veto-rasio / boleh / berkas-basi / token-tak-dikenal / "
          "apply() hanya mengurangi")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        arg = sys.argv[1] if len(sys.argv) > 1 else None
        if not arg:
            isi, ekor = _load(FLOW)
            print("berkas: %s | baris transaksi per token: %d | ekor %s"
                  % (os.path.basename(FLOW), len(isi),
                     time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ekor)) if ekor else "-"))
        else:
            print(json.dumps(state(arg), indent=1, sort_keys=True, ensure_ascii=False))
