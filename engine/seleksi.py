"""P161: gerbang seleksi bot - peta jalur kandidat ujung-ke-ujung + PEMERIKSA JEJAK satu kandidat dari rekaman publik.

Jalur harian (B1; intraday B2 belum, lihat vault TL44): kiriman bertanda tangan diterima gerbang (spesifikasi terikat tanda tangan EIP-712) ->
gerbang G1-G11 + KPI (laporan ber-sha) -> registri P83 (rantai hash, k keluarga) -> sha spesifikasi di-pin LockRegistry -> bayangan maju harian
60 hari (ledger paper) -> penantang di epoch buku (gerbang diulang terhadap BUKU SEKARANG) -> slot -> pembunuh terstruktur -> sinyal dikomit ke
SignalAnchor. Setiap tahap punya rekaman yang bisa diperiksa ulang siapa pun; `jejak` memeriksanya berurutan dan TIDAK PERNAH melaporkan OK untuk
sesuatu yang tidak ia periksa:

  OK              rekaman ada dan cocok dengan rekaman sebelumnya (sha / tanda tangan / rantai hash dihitung ulang di sini)
  BELUM           tahap belum dicapai (bayangan 12/60 hari, belum ada epoch sesudahnya) - bukan galat
  GAGAL           rekaman ada tetapi TIDAK cocok (diubah, rantai putus, sha beda): jejak RUSAK di sini, tahap sesudahnya tidak dinilai
  TAK_TERPERIKSA  tidak bisa diperiksa di mesin ini (eth-account tidak ada, chain tidak dibaca, bar sudah berubah) - BUKAN OK
  TIDAK_BERLAKU   tahap tidak berlaku (vonis TOLAK berhenti di gerbang; feed tanpa slot sampai terbukti)

Juga di sini: `petahana_buku` = PnL replay SEMUA penghuni buku (bot Fabius dari SPECS + bot penerbit template/rule dari BotSpec registri) untuk G10
di epoch dan di tinjauan; penghuni yang tidak bisa direplay (feed / code) dicatat dengan alasannya, tidak ditebak.
Fungsi murni terhadap folder `root` (salinan repo) + pembaca chain opsional (baca saja); tanpa jaringan sendiri, tanpa kunci, tanpa menulis.
"""
from __future__ import annotations

import copy
import dataclasses
import glob
import json
import os
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import book as bookmod, book_live, forward, ledger, registri, submission, terdaftar
from .slots import FABIUS, Entry, SlotParams
from .spec import SPECS, sha0x

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KONTAK_PRIVAT = "disimpan privat di gerbang"          # sama dengan tools/tinjau_pengajuan.py + engine/terdaftar.py (kontak tidak ikut hash)

OK, BELUM, GAGAL, TAK, TB = "OK", "BELUM", "GAGAL", "TAK_TERPERIKSA", "TIDAK_BERLAKU"
TAHAP = (
    ("diterima", "kiriman bertanda tangan diterima gerbang; spesifikasi terikat tanda tangan EIP-712 (specSha + submissionSha di pesan)"),
    ("gerbang", "G1-G11 + KPI pada bar repo; laporan ber-sha ledger/pengajuan/laporan/<sha>.json"),
    ("registri", "catatan hash-berantai P83 ledger/pengajuan/registri.jsonl (k keluarga dihitung ulang)"),
    ("dipin", "spec_sha LOLOS_SHADOW di LockRegistry chain 97 (worker) + ledger/pengajuan/spec/<bot>.json"),
    ("bayangan", "ledger maju harian sejak genesis (ledger/paper; feed: ledger/feed); syarat slot 60 hari"),
    ("penantang", "dinilai di epoch buku hidup terhadap buku sekarang (ledger/book/buku.jsonl + laporan ber-sha)"),
    ("slot", "penghuni buku slot sekarang (book_sha di-pin per epoch)"),
    ("pembunuh", "pembunuh terstruktur penerbit ditegakkan di epoch (slots.killer_triggered)"),
    ("sinyal_chain", "sinyal penghuni dikomit ke SignalAnchor oleh worker (sakelar KOMIT_PENERBIT)"),
)


@dataclasses.dataclass
class Tahap:
    nama: str
    status: str
    bukti: str = ""
    catatan: str = ""


# ---------------------------------------------------------------- baca rekaman

def _json(path: str) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _pengajuan_dir(root: str) -> str:
    return os.path.join(root, "ledger", "pengajuan")


def _registri(root: str) -> Tuple[List[dict], List[str]]:
    p = os.path.join(_pengajuan_dir(root), "registri.jsonl")
    if not os.path.exists(p):
        return [], []
    try:
        entries = registri.load(p)
    except registri.RegistriError as e:
        return [], [f"registri tak terbaca: {e}"]
    return entries, registri.verify(entries)


def _masuk(root: str) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for p in sorted(glob.glob(os.path.join(_pengajuan_dir(root), "masuk", "*.json"))):
        sha = os.path.basename(p)[:-5]
        try:
            out[sha] = _json(p)
        except (OSError, ValueError) as e:
            out[sha] = {"_galat": f"{type(e).__name__}"}
    return out


def _form(m: dict) -> dict:
    sub = copy.deepcopy(m["submission"])
    sub["identity"]["contact"] = KONTAK_PRIVAT
    return sub


def buku_hidup(root: str = ROOT) -> Tuple[List[Entry], List[dict], List[str]]:
    """-> (buku sekarang, catatan buku, masalah). Tanpa berkas buku = buku genesis (bot identitas, F-D73) dan catatan kosong."""
    p = os.path.join(root, "ledger", "book", "buku.jsonl")
    if not os.path.exists(p):
        return bookmod.genesis_book(0), [], []
    try:
        recs = ledger.load(p)
    except ledger.LedgerError as e:
        return [], [], [f"buku hidup tak terbaca: {e}"]
    try:
        probs = book_live.verify_book(recs) if recs else ["buku hidup kosong"]
    except (KeyError, TypeError, ValueError) as e:                     # catatan rusak: pemeriksa tidak boleh menebak
        probs = [f"catatan buku rusak ({type(e).__name__}: {e})"]
    if probs:
        return [], recs, probs
    return book_live.current_book(recs), recs, []


def petahana_buku(book: Sequence[Entry], md, root: str = ROOT) -> Tuple[Dict[str, list], Dict[str, str]]:
    """PnL replay SEMUA penghuni `book` (G10 = buku sekarang, bukan genesis): bot Fabius dari `SPECS`, bot penerbit dari BotSpec yang disusun ulang
    dari registri (`terdaftar.rincian`, sha harus sama dengan entri buku). -> (pnl per bot, {bot: alasan tidak direplay})."""
    from .replay import replay
    luar = terdaftar.rincian(root)[0] if any(e.issuer != FABIUS for e in book) else {}
    out: Dict[str, list] = {}
    tak: Dict[str, str] = {}
    for e in book:
        sp = SPECS.get(e.bot_id) if e.issuer == FABIUS else (luar.get(e.bot_id) or {}).get("spec")
        if sp is None:
            tak[e.bot_id] = "spesifikasi tidak ditemukan (bot Fabius tidak dikenal / penerbit tidak ada di registri sah)"
            continue
        if sp.sha() != e.spec_sha:
            tak[e.bot_id] = f"spec_sha buku {e.spec_sha[:14]}… != spesifikasi {sp.sha()[:14]}…"
            continue
        try:
            out[e.bot_id] = replay(sp, md)
        except NotImplementedError as x:                     # feed (tanpa replay), B4 (butuh deret per event)
            tak[e.bot_id] = f"tidak bisa direplay: {str(x)[:120]}"
        except Exception as x:  # noqa: BLE001 - code (pelari tidak ada / gagal): dicatat, tidak ditebak
            tak[e.bot_id] = f"tidak bisa direplay: {type(x).__name__}"
    return out, tak


# ---------------------------------------------------------------- jejak

def _cari(root: str, kunci: str, entries: Sequence[dict], masuk: Dict[str, dict]) -> Tuple[Optional[str], Optional[str]]:
    """kunci = submission_sha (0x + 64 hex) atau bot_id -> (submission_sha, bot_id). Bot dengan beberapa kiriman: catatan registri TERAKHIR."""
    if kunci.startswith("0x") and len(kunci) == 66:
        bot = next((e["bot_id"] for e in entries if e.get("submission_sha") == kunci), None)
        if bot is None and kunci in masuk and isinstance(masuk[kunci].get("submission"), dict):
            bot = masuk[kunci]["submission"].get("spec", {}).get("bot_id")
        return (kunci if bot or kunci in masuk else None), bot
    hits = [e for e in entries if e.get("bot_id") == kunci]
    if hits:
        return hits[-1]["submission_sha"], kunci
    m = [(v.get("t", 0), s) for s, v in masuk.items() if (v.get("submission") or {}).get("spec", {}).get("bot_id") == kunci]
    if m:
        return max(m)[1], kunci
    return None, None


def jejak(root: str, kunci: str, *, chain: Any = None, hitung_ulang: bool = False, now_s: Optional[int] = None,
          bars_dir: Optional[str] = None, params: SlotParams = SlotParams()) -> Dict[str, Any]:
    """Jejak satu kandidat (bot_id atau submission_sha) di salinan repo `root`. `chain` = pembaca chain opsional (baca saja) dengan
    `committer`, `locked_at(label, sha) -> int`, `komit(bot_id, spec_sha, tick) -> dict | None`. `hitung_ulang` = hitung ulang ledger maju dari
    bar + cari potongan bar yang menghasilkan `data_hash` laporan (`bars_dir`, bawaan root/ledger/bars). -> {ditemukan, tahap[], rusak_di, ...}."""
    now_s = int(time.time()) if now_s is None else int(now_s)
    entries, reg_probs = _registri(root)
    masuk = _masuk(root)
    sha, bot = _cari(root, kunci, entries, masuk)
    if sha is None:
        return {"kunci": kunci, "ditemukan": False, "tahap": [], "rusak_di": None, "ringkas": "tidak ada kiriman / catatan untuk kunci ini"}
    tahap: List[Tahap] = []
    ctx: Dict[str, Any] = {"root": root, "sha": sha, "bot": bot, "now_s": now_s, "chain": chain, "hitung_ulang": hitung_ulang,
                           "bars_dir": bars_dir or os.path.join(root, "ledger", "bars"), "p": params, "entries": entries,
                           "reg_probs": reg_probs, "masuk": masuk}
    for nama, fn in ((n, _PEMERIKSA[n]) for n, _ in TAHAP):
        if any(t.status == GAGAL for t in tahap):
            tahap.append(Tahap(nama, TB, catatan="tidak dinilai: jejak sudah rusak di tahap sebelumnya"))
            continue
        tahap.append(fn(ctx))
    rusak = next((t.nama for t in tahap if t.status == GAGAL), None)
    sah = [t.nama for t in tahap if t.status == OK]
    ring = (f"RUSAK di {rusak}: {next(t.catatan for t in tahap if t.nama == rusak)}" if rusak else
            f"OK: {', '.join(sah) or '-'}" + "".join(f" | {t.nama} {t.status}" + (f" ({t.catatan})" if t.catatan else "")
                                                     for t in tahap if t.status in (BELUM, TAK)))
    return {"kunci": kunci, "ditemukan": True, "submission_sha": sha, "bot_id": ctx.get("bot"), "kind": ctx.get("kind"),
            "vonis": ctx.get("vonis"), "tahap": [dataclasses.asdict(t) for t in tahap], "rusak_di": rusak, "ringkas": ring}


def _t_diterima(c: dict) -> Tahap:
    sha, masuk = c["sha"], c["masuk"]
    m = masuk.get(sha)
    if m is None:
        if any(e.get("submission_sha") == sha for e in c["entries"]):
            return Tahap("diterima", GAGAL, catatan="catatan registri tanpa salinan formulir publik (masuk/<sha>.json)")
        return Tahap("diterima", BELUM, catatan="belum ada salinan publik di repo (antrean gerbang: GET /bots/submissions)")
    if "_galat" in m or not isinstance(m.get("submission"), dict):
        return Tahap("diterima", GAGAL, f"masuk/{sha}.json", f"salinan formulir tak terbaca ({m.get('_galat', 'bentuk salah')})")
    try:
        sub = _form(m)
        hit = submission.submission_sha(sub)
    except Exception as e:  # noqa: BLE001 - formulir rusak = tidak bisa dicocokkan
        return Tahap("diterima", GAGAL, f"masuk/{sha}.json", f"formulir tak bisa di-hash ({type(e).__name__})")
    if hit != sha or m.get("submission_sha") != sha:
        return Tahap("diterima", GAGAL, f"masuk/{sha}.json", f"submission_sha dihitung ulang {hit[:14]}… != {sha[:14]}… (formulir diubah)")
    c["sub"], c["m"], c["kind"] = sub, m, sub.get("kind")
    c["bot"] = sub["spec"]["bot_id"]                                     # yang mengikat = formulir bertanda tangan, bukan kunci pencarian
    try:
        c["spec"] = submission.to_botspec(sub)
    except Exception:  # noqa: BLE001 - formulir yang ditolak sebelum gerbang mungkin tidak bisa disusun jadi BotSpec
        c["spec"] = None
    issuer = sub["identity"]["issuer_wallet"]
    dipakai = [v.get("nonce") for s, v in masuk.items() if s != sha and isinstance(v.get("submission"), dict)
               and (v["submission"].get("identity") or {}).get("issuer_wallet") == issuer]
    if m.get("nonce") in dipakai:
        return Tahap("diterima", GAGAL, f"masuk/{sha}.json", "nonce penerbit dipakai dua kali (pemakaian ulang tanda tangan)")
    try:
        probs = submission.verify_identity(sub, m["signature"], int(m.get("chain_id", 97)), int(m["nonce"]), int(m["deadline"]), int(m["t"]),
                                           payout_signature_hex=m.get("payout_signature"))
    except RuntimeError:
        return Tahap("diterima", TAK, f"masuk/{sha}.json", "verifikasi tanda tangan butuh eth-account (tidak terpasang di mesin ini)")
    except (KeyError, TypeError, ValueError) as e:
        return Tahap("diterima", GAGAL, f"masuk/{sha}.json", f"medan tanda tangan tidak lengkap ({type(e).__name__})")
    if probs:
        return Tahap("diterima", GAGAL, f"masuk/{sha}.json", "identitas: " + "; ".join(probs)[:200])
    return Tahap("diterima", OK, f"masuk/{sha}.json · issuer {issuer} · t {ledger.utc_iso(int(m['t']) * 1000)}",
                 "tanda tangan EIP-712 sah pada t terima; mengikat specSha + submissionSha")


def _t_gerbang(c: dict) -> Tahap:
    sha = c["sha"]
    if "sub" not in c:
        return Tahap("gerbang", BELUM, catatan="kiriman belum punya salinan publik")
    path = os.path.join(_pengajuan_dir(c["root"]), "laporan", f"{sha}.json")
    st = _status(c["root"]).get(sha) or {}
    if not os.path.exists(path):
        if st.get("status") == "queued":
            return Tahap("gerbang", BELUM, catatan=f"tertahan: {str(st.get('alasan'))[:160]}")
        if st.get("final"):
            c["vonis"] = st.get("alasan")
            return Tahap("gerbang", OK, "ledger/pengajuan/status.json", f"ditolak sebelum gerbang: {str(st.get('alasan'))[:160]}")
        return Tahap("gerbang", BELUM, catatan="belum ditinjau (bot-review harian)")
    try:
        rep = _json(path)
    except (OSError, ValueError) as e:
        return Tahap("gerbang", GAGAL, f"laporan/{sha}.json", f"laporan tak terbaca ({type(e).__name__})")
    body = {k: v for k, v in rep.items() if k != "report_sha"}
    if sha0x(body) != rep.get("report_sha"):
        return Tahap("gerbang", GAGAL, f"laporan/{sha}.json", "report_sha tidak cocok dengan isi laporan (laporan diubah)")
    c["rep"], c["vonis"] = rep, rep.get("vonis")
    if rep.get("vonis") == "TOLAK_FORMULIR":
        return Tahap("gerbang", OK, f"laporan/{sha}.json · {rep['report_sha'][:18]}…", "formulir ditolak sebelum gerbang (tidak memakan alpha)")
    spec = c.get("spec")
    want = {"submission_sha": sha, "bot_id": c["bot"], "spec_sha": spec.sha() if spec else None}
    beda = [k for k, v in want.items() if rep.get(k) != v]
    if beda:
        return Tahap("gerbang", GAGAL, f"laporan/{sha}.json", f"laporan tidak cocok dengan formulir: {', '.join(beda)}")
    catatan = f"vonis {rep['vonis']}; gagal {rep.get('gagal') or '-'}; tak terukur {rep.get('tak_terukur') or '-'}"
    if not (rep.get("identitas") or {}).get("diverifikasi"):
        catatan += "; identitas TIDAK terverifikasi (laporan indikatif)"
    if c["hitung_ulang"] and spec is not None and rep.get("data_hash"):
        cocok = _cari_potongan(c, spec, rep["data_hash"], int(c["m"]["t"]))
        if cocok is None:
            return Tahap("gerbang", TAK, f"laporan/{sha}.json", "tidak ada potongan bar repo yang menghasilkan data_hash laporan (bar diperbarui "
                                                                 "sesudah tinjauan?); vonis tidak bisa diulang di mesin ini")
        catatan += f"; data_hash = bar repo s/d {cocok}"
    return Tahap("gerbang", OK, f"laporan/{sha}.json · report_sha {rep['report_sha'][:18]}…", catatan)


def _cari_potongan(c: dict, spec, data_hash: str, t_s: int) -> Optional[str]:
    """Tanggal bar terakhir yang membuat data_fingerprint(spec, bar s/d tanggal itu) = data_hash laporan (tinjauan berjalan 0-6 hari sesudah terima)."""
    from .data import load_csv_dir
    from .sinyal import data_fingerprint
    from .spec import PERP_UNIVERSE
    md = c.get("_md") or load_csv_dir(c["bars_dir"], list(PERP_UNIVERSE) + ["PAXGUSDT", "XAUUSDT"])
    c["_md"] = md
    base = ledger.last_closed_bar(t_s * 1000)
    for k in range(-1, 8):
        cut = base + k * 86_400_000
        if data_fingerprint(spec, md.upto(cut)) == data_hash:
            return ledger.date_of(cut)
    return None


def _status(root: str) -> Dict[str, dict]:
    p = os.path.join(_pengajuan_dir(root), "status.json")
    try:
        return _json(p) if os.path.exists(p) else {}
    except (OSError, ValueError):
        return {}


def _t_registri(c: dict) -> Tahap:
    if c["reg_probs"]:
        return Tahap("registri", GAGAL, "ledger/pengajuan/registri.jsonl", f"registri tidak sah: {c['reg_probs'][0]}")
    e = next((x for x in c["entries"] if x.get("submission_sha") == c["sha"]), None)
    rep = c.get("rep")
    if e is None:
        if rep is None:
            return Tahap("registri", BELUM if c.get("vonis") is None else TB, catatan="belum dinilai gerbang" if c.get("vonis") is None else
                         f"ditolak sebelum gerbang ({c.get('vonis')}): tidak dicatat, tidak memakan alpha")
        if rep.get("vonis") in registri.TANPA_UJI:
            return Tahap("registri", TB, catatan="formulir ditolak sebelum gerbang: tidak dicatat, tidak memakan alpha")
        if not (rep.get("identitas") or {}).get("diverifikasi"):
            return Tahap("registri", TB, catatan="identitas tidak terverifikasi: laporan indikatif, tidak dicatat")
        return Tahap("registri", GAGAL, catatan="laporan mengikat ada tetapi catatan registri tidak ada")
    sub = c.get("sub")
    want = {"report_sha": (rep or {}).get("report_sha"), "vonis": (rep or {}).get("vonis"), "spec_sha": (rep or {}).get("spec_sha"),
            "bot_id": c["bot"], "issuer": sub["identity"]["issuer_wallet"] if sub else None,
            "payout": sub["identity"]["payout_wallet"] if sub else None, "t_s": int(c["m"]["t"]) if c.get("m") else None}
    beda = [k for k, v in want.items() if (int(e.get(k)) if k == "t_s" else e.get(k)) != v]
    if beda:
        return Tahap("registri", GAGAL, "ledger/pengajuan/registri.jsonl", f"catatan registri tidak cocok: {', '.join(beda)}")
    c["e"] = e
    return Tahap("registri", OK, f"registri.jsonl h {e['h'][:18]}…", f"k {e['k']} alpha {e['alpha']:.6g} (dihitung ulang dari catatan sebelumnya)")


def _lolos(c: dict) -> bool:
    return (c.get("e") or {}).get("vonis") == registri.LOLOS


def _feed(c: dict) -> bool:
    return (c.get("e") or {}).get("vonis") == registri.MAJU_FEED


def _berhenti(c: dict, nama: str) -> Optional[Tahap]:
    if c.get("e") is None:
        return Tahap(nama, TB if c.get("vonis") else BELUM, catatan=f"berhenti sebelum registri ({c.get('vonis') or 'belum dinilai'})")
    if not (_lolos(c) or _feed(c)):
        return Tahap(nama, TB, catatan=f"vonis {c['e']['vonis']}: jalur berhenti di gerbang")
    return None


def _t_dipin(c: dict) -> Tahap:
    stop = _berhenti(c, "dipin")
    if stop:
        return stop
    if _feed(c):
        return Tahap("dipin", TB, catatan="feed: akar komit per bar dikunci di LockRegistry oleh gerbang (TL42), bukan pin spesifikasi")
    e = c["e"]
    path = os.path.join(_pengajuan_dir(c["root"]), "spec", f"{e['bot_id']}.json")
    if not os.path.exists(path):
        return Tahap("dipin", GAGAL, catatan="vonis LOLOS_SHADOW tanpa berkas spec/<bot>.json")
    try:
        s = _json(path)
    except (OSError, ValueError) as x:
        return Tahap("dipin", GAGAL, f"spec/{e['bot_id']}.json", f"tak terbaca ({type(x).__name__})")
    if (s.get("submission_sha"), s.get("spec_sha"), s.get("bot_id")) != (e["submission_sha"], e["spec_sha"], e["bot_id"]):
        return Tahap("dipin", GAGAL, f"spec/{e['bot_id']}.json", "berkas spec tidak cocok dengan catatan registri (tidak akan di-pin)")
    if c.get("spec") is not None and s.get("botspec") != json.loads(json.dumps(dataclasses.asdict(c["spec"]))):
        return Tahap("dipin", GAGAL, f"spec/{e['bot_id']}.json", "botspec di berkas != BotSpec yang disusun ulang dari formulir")
    ch = c["chain"]
    if ch is None:
        return Tahap("dipin", TAK, f"spec/{e['bot_id']}.json", "lockedAt tidak dibaca (jalankan dengan --chain)")
    try:
        at = int(ch.locked_at(e["bot_id"], e["spec_sha"]))
    except Exception as x:  # noqa: BLE001 - gagal baca != belum di-pin
        return Tahap("dipin", TAK, f"spec/{e['bot_id']}.json", f"lockedAt gagal dibaca ({type(x).__name__})")
    if not at:
        return Tahap("dipin", BELUM, f"spec/{e['bot_id']}.json", f"belum di-pin oleh committer {ch.committer} (worker: satu pin per putaran)")
    c["pin_s"] = at
    return Tahap("dipin", OK, f"LockRegistry lockedAt {ledger.utc_iso(at * 1000)}", f"label {e['bot_id']} spec_sha {e['spec_sha'][:18]}…")


def _t_bayangan(c: dict) -> Tahap:
    stop = _berhenti(c, "bayangan")
    if stop:
        return stop
    e, p = c["e"], c["p"]
    sub_dir = "feed" if _feed(c) else "paper"
    path = os.path.join(c["root"], "ledger", sub_dir, f"{e['bot_id']}.jsonl")
    if not os.path.exists(path):
        return Tahap("bayangan", BELUM, catatan=f"ledger/{sub_dir}/{e['bot_id']}.jsonl belum ada (genesis ditulis putaran harian berikutnya)")
    try:
        recs = ledger.load(path)
    except ledger.LedgerError as x:
        return Tahap("bayangan", GAGAL, f"ledger/{sub_dir}/{e['bot_id']}.jsonl", f"tak terbaca ({x})")
    probs = ledger.verify_chain(recs)
    g = recs[0] if recs else {}
    if probs:
        return Tahap("bayangan", GAGAL, f"ledger/{sub_dir}/{e['bot_id']}.jsonl", f"rantai ledger tidak sah: {probs[0]}")
    if g.get("type") != "genesis" or g.get("bot_id") != e["bot_id"] or g.get("spec_sha") != e["spec_sha"]:
        return Tahap("bayangan", GAGAL, f"ledger/{sub_dir}/{e['bot_id']}.jsonl", "genesis tidak memakai spec_sha registri (bot lain / spesifikasi lain)")
    if int(g.get("first_asof", 0)) < (int(e["t_s"]) // 86_400) * 86_400_000:
        return Tahap("bayangan", GAGAL, f"ledger/{sub_dir}/{e['bot_id']}.jsonl", "bayangan dimulai SEBELUM kiriman diterima")
    c["ledger"] = recs
    if c["hitung_ulang"] and sub_dir == "paper" and c.get("spec") is not None:
        if not os.path.isdir(c["bars_dir"]):
            return Tahap("bayangan", TAK, f"ledger/{sub_dir}/{e['bot_id']}.jsonl", f"bar tidak ada di {c['bars_dir']}: tidak bisa dihitung ulang")
        from .data import load_csv_dir
        from .spec import PERP_UNIVERSE
        sym = list(PERP_UNIVERSE) + ["PAXGUSDT", "XAUUSDT"]
        md = load_csv_dir(c["bars_dir"], sym)
        md_t = load_csv_dir(c["bars_dir"], sym, funding_view="targets") if c["spec"].method == "B3-CARRY" else md
        hasil = ledger.verify_against_data(c["spec"], recs, md_t, md)
        tak = [x for x in hasil if "tak bisa dihitung ulang" in x]                 # bar hilang / terpotong di mesin ini != ledger dipalsukan
        beda = [x for x in hasil if x not in tak]
        if beda:
            return Tahap("bayangan", GAGAL, f"ledger/{sub_dir}/{e['bot_id']}.jsonl", f"hitung ulang dari bar: {beda[0]}")
        if tak:
            return Tahap("bayangan", TAK, f"ledger/{sub_dir}/{e['bot_id']}.jsonl", f"hitung ulang tidak lengkap: {tak[0]}")
    if sub_dir == "feed":
        from . import feed as feedmod
        hari = max(0, (c["now_s"] * 1000 - int(g["first_asof"])) // 86_400_000)
        return Tahap("bayangan", OK if hari >= feedmod.BAYANGAN_HARI else BELUM, f"ledger/feed/{e['bot_id']}.jsonl",
                     f"bayangan feed {hari}/{feedmod.BAYANGAN_HARI} hari (rantai utuh; komit ditandatangani dihitung ulang oleh feed.verify)")
    end = forward.common_end({e["bot_id"]: recs}, ledger.last_closed_bar(c["now_s"] * 1000))
    st = forward.stats_for(e["bot_id"], recs, end, p)
    teks = (f"{st.shadow_days}/{p.shadow_days} hari; tick {st.n_tick} gap {st.n_gap} settle {st.n_settle}; net sejak genesis "
            f"{'-' if st.shadow_score_bps is None else f'{st.shadow_score_bps:+.1f}'} bps" + ("; dihitung ulang dari bar" if c["hitung_ulang"] else ""))
    return Tahap("bayangan", OK if st.shadow_days >= p.shadow_days else BELUM, f"ledger/paper/{e['bot_id']}.jsonl genesis {g['first_asof_date']}", teks)


def _t_penantang(c: dict) -> Tahap:
    stop = _berhenti(c, "penantang")
    if stop:
        return stop
    if _feed(c):
        return Tahap("penantang", TB, catatan="feed tanpa slot sampai definisi 'terbukti' (LB9)")
    e = c["e"]
    book, recs, probs = buku_hidup(c["root"])
    if probs:
        return Tahap("penantang", GAGAL, "ledger/book/buku.jsonl", f"buku hidup tidak sah: {probs[0]}")
    c["book"], c["book_recs"] = book, recs
    nilai, lewat = [], []
    for r in recs[1:]:
        for d in r.get("dilewati") or []:
            if d.get("bot") == e["bot_id"]:
                lewat.append(f"epoch {r['epoch']}: dilewati - {d.get('alasan')}")
        keps = {k[0]: k for k in r.get("keputusan") or []}
        for ch in r.get("penantang") or []:
            if ch.get("bot_id") != e["bot_id"]:
                continue
            kep = keps.get(e["bot_id"]) or [e["bot_id"], "-", None, "keputusan tidak tercatat"]
            if ch.get("spec_sha") != e["spec_sha"]:
                return Tahap("penantang", GAGAL, f"buku epoch {r['epoch']}", "penantang memakai spec_sha lain dari registri")
            lp = os.path.join(c["root"], "ledger", "book", "laporan", f"{str(ch.get('report_sha'))[2:14]}.json")
            if os.path.exists(lp):
                try:
                    rep = _json(lp)
                except (OSError, ValueError):
                    return Tahap("penantang", GAGAL, lp, "laporan gerbang epoch tak terbaca")
                body = {k: v for k, v in rep.items() if k != "report_sha"}
                if sha0x(body) != rep.get("report_sha") or rep.get("report_sha") != ch.get("report_sha"):
                    return Tahap("penantang", GAGAL, lp, "laporan gerbang epoch tidak cocok dengan sha di catatan buku")
                if rep.get("vonis") != ch.get("gate_verdict") or rep.get("spec_sha") != e["spec_sha"] or rep.get("book_sha") != ch.get("book_sha"):
                    return Tahap("penantang", GAGAL, lp, "isi laporan gerbang epoch (vonis / spec / buku) beda dari catatan buku")
                bukti = "laporan ber-sha cocok"
            else:
                bukti = "laporan gerbang epoch tidak ada di repo (--no-gates atau tanpa --write)"
            nilai.append(f"epoch {r['epoch']}: gerbang {ch.get('gate_verdict')}, bayangan {ch.get('shadow_days')} hari -> {kep[1]}"
                         + (f" menggantikan {kep[2]}" if kep[2] else "") + f" ({kep[3]}; {bukti})")
    if not nilai:
        return Tahap("penantang", BELUM, "ledger/book/buku.jsonl", "; ".join(lewat) or "belum dinilai di epoch mana pun (epoch tiap 30 hari)")
    c["nilai"] = nilai
    return Tahap("penantang", OK, "ledger/book/buku.jsonl (keputusan dihitung ulang: verify_book)", " | ".join(nilai + lewat)[:600])


def _t_slot(c: dict) -> Tahap:
    stop = _berhenti(c, "slot")
    if stop:
        return stop
    if _feed(c):
        return Tahap("slot", TB, catatan="feed tanpa slot sampai terbukti (LB9)")
    e = c["e"]
    if "book" not in c:
        return Tahap("slot", BELUM, catatan="belum ada buku hidup yang bisa dibaca")
    ent = next((x for x in c["book"] if x.bot_id == e["bot_id"]), None)
    keluar = [f"epoch {r['epoch']}" for r in c["book_recs"][1:] if e["bot_id"] in (r.get("dikeluarkan") or [])]
    if ent is None:
        return Tahap("slot", BELUM, catatan="bukan penghuni buku sekarang" + (f"; dikeluarkan pembunuh di {', '.join(keluar)}" if keluar else ""))
    if ent.spec_sha != e["spec_sha"]:
        return Tahap("slot", GAGAL, "ledger/book/buku.jsonl", "entri buku memakai spec_sha lain dari registri")
    c["slot_s"] = int(ent.admitted_s)
    last = c["book_recs"][-1] if c["book_recs"] else {}
    return Tahap("slot", OK, f"book_sha {str(last.get('book_sha'))[:18]}…", f"penghuni sejak {ledger.utc_iso(int(ent.admitted_s) * 1000)}")


def _t_pembunuh(c: dict) -> Tahap:
    stop = _berhenti(c, "pembunuh")
    if stop:
        return stop
    if _feed(c):
        return Tahap("pembunuh", TB, catatan="feed tanpa slot")
    e = c["e"]
    for r in reversed(c.get("book_recs") or []):
        if e["bot_id"] in (r.get("dikeluarkan") or []):
            return Tahap("pembunuh", OK, f"epoch {r['epoch']}", "DIKELUARKAN oleh pembunuhnya sendiri")
    if "slot_s" not in c:
        return Tahap("pembunuh", BELUM, catatan="belum di slot (pembunuh dinilai untuk penghuni)")
    last = c["book_recs"][-1]
    v = (last.get("pembunuh") or {}).get(e["bot_id"])
    if v is None:
        return Tahap("pembunuh", BELUM, catatan="belum dinilai di epoch sesudah masuk slot")
    return Tahap("pembunuh", OK, f"epoch {last['epoch']}", f"status pembunuh {v}")


def _t_sinyal(c: dict) -> Tahap:
    stop = _berhenti(c, "sinyal_chain")
    if stop:
        return stop
    if _feed(c):
        return Tahap("sinyal_chain", TB, catatan="feed: bobot dikomit penerbit sendiri sebelum penutupan (TL42)")
    if "slot_s" not in c:
        return Tahap("sinyal_chain", BELUM, catatan="belum di slot (worker mengomit penghuni bila KOMIT_PENERBIT menyala)")
    ch, e = c["chain"], c["e"]
    ticks = [r for r in c.get("ledger") or [] if r.get("type") == "tick" and int(r["asof"]) // 1000 >= c["slot_s"] - 86_400]
    if not ticks:
        return Tahap("sinyal_chain", BELUM, catatan="belum ada tick sejak masuk slot")
    if ch is None:
        return Tahap("sinyal_chain", TAK, catatan=f"{len(ticks)} tick sejak masuk slot; komit tidak dibaca (jalankan dengan --chain)")
    try:
        ada = [t for t in ticks if ch.komit(e["bot_id"], e["spec_sha"], t)]
    except Exception as x:  # noqa: BLE001
        return Tahap("sinyal_chain", TAK, catatan=f"komit gagal dibaca ({type(x).__name__})")
    st = OK if len(ada) == len(ticks) else BELUM
    return Tahap("sinyal_chain", st, f"SignalAnchor committer {ch.committer}",
                 f"{len(ada)}/{len(ticks)} tick sejak masuk slot dikomit" + ("" if st == OK else " (KOMIT_PENERBIT mati atau belum sampai putaran worker)"))


_PEMERIKSA = {"diterima": _t_diterima, "gerbang": _t_gerbang, "registri": _t_registri, "dipin": _t_dipin, "bayangan": _t_bayangan,
              "penantang": _t_penantang, "slot": _t_slot, "pembunuh": _t_pembunuh, "sinyal_chain": _t_sinyal}


def semua(root: str = ROOT, **kw: Any) -> List[Dict[str, Any]]:
    """Jejak SEMUA kiriman yang punya salinan publik atau catatan registri (urut waktu terima)."""
    entries, _ = _registri(root)
    masuk = _masuk(root)
    shas = {e["submission_sha"] for e in entries} | set(masuk)
    urut = sorted(shas, key=lambda s: (int((masuk.get(s) or {}).get("t", 0) or 0), s))
    return [jejak(root, s, **kw) for s in urut]


def teks(j: Dict[str, Any]) -> str:
    """Tampilan satu jejak (angka dicetak dari rekaman, bukan dikarang)."""
    if not j["ditemukan"]:
        return f"{j['kunci']}: {j['ringkas']}"
    lines = [f"JEJAK {j['bot_id']} ({j['kind']}) submission_sha {j['submission_sha']} | vonis {j.get('vonis') or '-'}"]
    for t in j["tahap"]:
        lines.append(f"  {t['nama']:12s} {t['status']:15s} {t['bukti']}" + (f"\n  {'':12s} {'':15s} {t['catatan']}" if t["catatan"] else ""))
    lines.append(f"  -> {j['ringkas']}")
    return "\n".join(lines)
