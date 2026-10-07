"""P168 (F-D122, F-D125): jalur sungguhan peninjau LLM "agent pemilik Fabius" - panggilan xkiro `z-ai/glm-5.3` (effort bawaan), putaran di gerbang
`fabius-x402` (Railway: satu-satunya tempat `XKIRO_API_KEY`), kait penahan kursi P168b, tarikan laporan publik oleh tinjauan harian GitHub, kalibrasi.

Logika murni (brief persis + sha, skema ketat, paksaan "hanya membatasi", tahap 1 agent, penilai kalibrasi, KUNCI JALUR) ada di `engine/peninjau.py`.
Selama `status` mencetak "belum dikalibrasi", putaran gerbang TIDAK memanggil model dan tidak menahan apa pun (peninjau belum di jalur).

    python -X utf8 tools/peninjau_llm.py status                                            # kunci jalur bot + agent (tanpa kunci API, tanpa jaringan)
    python -X utf8 tools/peninjau_llm.py kalibrasi --jenis bot --palsu                     # uji pipa dengan model palsu (BUKAN kalibrasi sah, tidak ditulis ke ledger)
    railway run --service fabius-x402 python -X utf8 tools/peninjau_llm.py kalibrasi --jenis bot     # set kalibrasi vs model sungguhan (berbiaya xkiro)
    railway run --service fabius-x402 python -X utf8 tools/peninjau_llm.py kalibrasi --jenis agent
Kalibrasi sungguhan menulis `ledger/peninjau/kalibrasi/<UTC>-<jenis>.json` (jawaban mentah + sha + usage); setelah di-commit + di-push, gerbang membacanya dari
klon repo dan peninjau aktif HANYA bila rekaman itu lulus saat dinilai ulang (`engine/peninjau.py::status_kalibrasi`).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Callable, Dict, Iterable, List, Optional, Tuple

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from engine import peninjau as pn                                               # noqa: E402

KALIBRASI_DIR = os.path.join(ROOT, "ledger", "peninjau", "kalibrasi")
HARGA_PER_TOKEN = {"masuk": 1.40e-6, "keluar": 4.40e-6}    # z-ai/glm-5.3 di xkiro, dibaca 6 Okt (Test Commands #109); untuk perkiraan biaya saja
UA = {"User-Agent": "fabius-peninjau"}


# ---------------------------------------------------------------- panggilan model

def _bersih(s: str, kunci: str) -> str:
    s = str(s)
    return s.replace(kunci, "<kunci>") if kunci else s


def panggil_xkiro(system: str, user: str, post: Optional[Callable] = None, timeout: Optional[int] = None) -> dict:
    """Satu panggilan: `analis.call_model` dengan effort BAWAAN (`reasoning_effort` DIHILANGKAN). -> {"teks", "meta"}. Galat apa pun (kunci tidak ada,
    HTTP 402 saldo habis, 429, batas waktu, jaringan) dinaikkan sebagai RuntimeError tanpa kunci di pesannya -> `peninjau.tinjau` mencatatnya TAHAN."""
    import analis as an
    p = pn.PARAMS
    kunci = os.environ.get(an.PROVIDERS[p["provider"]]["key_var"]) or ""
    tangkap: Dict[str, dict] = {}

    def post_tangkap(url, headers, body, t):
        r = (post or an._post)(url, headers, body, t)
        tangkap["r"] = r
        return r
    agent = {"provider": p["provider"], "model": p["model"], "effort": an.EFFORT_BAWAAN, "max_tokens": p["max_tokens"], "temperature": p["temperature"]}
    try:
        teks = an.call_model(agent, system, user, post=post_tangkap, timeout=timeout or p["timeout_s"])
    except urllib.error.HTTPError as e:
        try:
            isi = e.read()[:300].decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            isi = ""
        raise RuntimeError(f"HTTP {e.code}: {_bersih(isi, kunci)}") from None
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"{type(e).__name__}: {_bersih(str(e)[:200], kunci)}") from None
    r = tangkap.get("r") or {}
    ch = (r.get("choices") or [{}])[0] if isinstance(r, dict) else {}
    msg = ch.get("message") or {}
    return {"teks": teks, "meta": {"finish_reason": ch.get("finish_reason"), "usage": r.get("usage") if isinstance(r, dict) else None,
                                   "ada_penalaran": bool(msg.get("reasoning_content")), "model": r.get("model") if isinstance(r, dict) else None}}


def contoh_jawaban(masukan: dict, vonis: str = "TAHAN", tags: Iterable[str] = ("OTHER", "OTHER", "OTHER"), severity: str = "major",
                   injection: Iterable[str] = (), data_gaps: Iterable[str] = (), kunci: Optional[str] = None) -> str:
    """Jawaban berskema sah (untuk model palsu: uji pipa + tes). `kunci` = evidence_key yang dikutip (bawaan: kunci pertama yang ADA di masukan)."""
    tags = tuple(tags)
    if kunci is None:
        t = masukan["tepercaya"]
        kunci = "gates.G1.value" if "gates" in t and "G1" in t["gates"] else "stage1.answers.valid_pct" if "stage1" in t and "answers" in t["stage1"] else \
            next(iter(t)) if t else ""
    sc = {"score": 3, "evidence_key": kunci, "note": "n"}
    o = {"verdict": vonis, "confidence": 60, "one_line": "palsu", "restated_strategy": "s", "case_for": "a", "case_against": "b",
         "premortem": [{"cause": "c", "evidence_key": kunci}], "replication": {"simplest_alternative": "x", "overlap": "y", "evidence_keys": [kunci]},
         "scores": {d: dict(sc) for d in pn.DIMENSI},
         "objections": [{"tag": t, "severity": severity, "claim": "c", "fact": "f", "inference": "i", "evidence_key": kunci} for t in tags],
         "no_objection_reason": None if len(tags) >= 3 else "palsu", "what_would_change_my_mind": [], "required_changes": [],
         "improvements": [{"change": "c", "why": "w", "priority": 1}], "monitoring": [], "data_gaps": list(data_gaps),
         "injection_findings": [{"quote": q} for q in injection]}
    return json.dumps(o)


def panggil_palsu(system: str, user: str) -> dict:
    """Model palsu deterministik: selalu TAHAN berskema sah (menguji pipa kalibrasi tanpa biaya; tidak pernah menghasilkan kalibrasi sah)."""
    jenis = "bot" if system == pn.BRIEF_BOT else "agent"
    kunci = "gates.G1.value" if jenis == "bot" else "stage1.answers.valid_pct"
    return {"teks": contoh_jawaban({"tepercaya": {}}, kunci=kunci), "meta": {"finish_reason": "stop", "usage": None, "model": "palsu"}}


# ---------------------------------------------------------------- gerbang: arsip, putaran, rute, kait kursi

def arsip(gate) -> pn.Arsip:
    return gate.__dict__.setdefault("_peninjau_arsip", pn.Arsip(os.path.join(os.path.dirname(gate.analis_dir), "peninjau")))


def status(gate, jenis: str, umur_s: int = 60) -> dict:
    """`status_kalibrasi` untuk jalur permintaan HTTP / kait kursi: dinilai ulang paling sering tiap `umur_s` detik (putaran selalu menilai segar)."""
    c = gate.__dict__.setdefault("_peninjau_status", {})
    t, st = c.get(jenis, (0.0, None))
    if st is None or time.time() - t > umur_s:
        st = pn.status_kalibrasi(gate.data.workdir, jenis)
        c[jenis] = (time.time(), st)
    return st


def _baca_json(path: str) -> Optional[dict]:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def calon_bot(root: str, ar: pn.Arsip, log: Callable[[str], None] = print, kode: Optional[Callable[[str], Optional[str]]] = None):
    """Bot penerbit yang BARU lolos tahap 1 (LOLOS_SHADOW di registri publik) dan belum punya laporan final -> (kunci, masukan, kind). Registri rusak =
    tidak ada calon (tahap 1 yang tidak bisa diverifikasi tidak ditinjau)."""
    from engine import registri, submission
    path = os.path.join(root, "ledger", "pengajuan", "registri.jsonl")
    if not os.path.exists(path):
        return
    try:
        entries = registri.load(path)
    except registri.RegistriError as e:
        log(f"peninjau: registri tak terbaca ({e}) - tidak ada yang ditinjau")
        return
    if registri.verify(entries):
        log("peninjau: registri rusak - tidak ada yang ditinjau")
        return
    buku = _anggota_buku(root)
    for e in entries:
        sha = e.get("submission_sha")
        if e.get("vonis") != registri.LOLOS or not pn.KUNCI_OK.match(sha or "") or pn.final(ar.ambil("bot", sha)):
            continue
        lap = _baca_json(os.path.join(root, "ledger", "pengajuan", "laporan", f"{sha}.json"))
        masuk = _baca_json(os.path.join(root, "ledger", "pengajuan", "masuk", f"{sha}.json"))
        if not lap or not masuk or lap.get("vonis") != registri.LOLOS or lap.get("report_sha") != e.get("report_sha"):
            log(f"peninjau: {e.get('bot_id')}: laporan tahap 1 / salinan formulir tidak ada atau tidak cocok registri - belum ditinjau")
            continue
        form = masuk["submission"]
        teks_kode = None
        if form.get("kind") == "code":
            teks_kode = kode(sha) if kode else None
            if teks_kode is None:
                log(f"peninjau: {e.get('bot_id')}: kode privat tidak tersedia di gerbang - belum ditinjau (tetap TAHAN bila peninjau aktif)")
                continue
        yield sha, pn.masukan_bot(lap, form, buku=buku, attribution=_atribusi(root, form), kode=teks_kode), form.get("kind")


def _anggota_buku(root: str) -> List[str]:
    try:
        from engine import book_live, ledger
        return [e.bot_id for e in book_live.current_book(ledger.load(os.path.join(root, "ledger", "book", "buku.jsonl")))]
    except Exception:  # noqa: BLE001 - buku tak terbaca: daftar kosong (model melihat "members": [])
        return []


def _atribusi(root: str, form: dict) -> dict:
    try:
        import copy
        from engine import cli, submission
        from engine.data import load_csv_dir
        sub = copy.deepcopy(form)
        sub["identity"]["contact"] = "disimpan privat di gerbang"
        spec = submission.to_botspec(sub)
        return pn.atribusi(spec, load_csv_dir(os.path.join(root, "ledger", "bars"), cli.DATA_SYMBOLS))
    except Exception as e:  # noqa: BLE001
        return {"available": False, "reason": type(e).__name__}


def baca_rekaman(gate, sejak: int, now_s: int, maks_hari: int = 9) -> List[dict]:
    """Rekaman meja (`<meja>/rekaman/<tgl>.jsonl`) dari hari `sejak` sampai hari ini, paling banyak `maks_hari` berkas."""
    out = []
    for d in range(max(sejak // 86_400, now_s // 86_400 - maks_hari + 1), now_s // 86_400 + 1):
        p = gate._meja_path("rekaman", d * 86_400)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                out += [json.loads(ln) for ln in f if ln.strip()]
    return out


def pembaca_fitur(gate) -> Callable[[dict], Optional[dict]]:
    """rekaman agent -> {aset: {faktor: nilai}} dari snapshot data meja yang dibaca siklus itu (`data_t`), terbatas pada aset + faktor yang dikutip."""
    cache: Dict[str, Dict[int, dict]] = {}

    def f(r: dict) -> Optional[dict]:
        t = r.get("data_t")
        if not t:
            return None
        p = gate._meja_path("fitur", int(t))
        if p not in cache:
            cache[p] = {}
            if os.path.exists(p):
                with open(p, encoding="utf-8") as fh:
                    for ln in fh:
                        if ln.strip():
                            s = json.loads(ln)
                            cache[p][int(s.get("t") or 0)] = s.get("fitur_aset") or {}
        fa = cache[p].get(int(t))
        if fa is None:
            return None
        k = r.get("keputusan") or {}
        faktor = set(k.get("faktor") or []) | {x for i in k.get("instrumen") or [] for x in i.get("faktor") or []}
        return {i["aset"]: {x: (fa.get(i["aset"]) or {}).get(x) for x in sorted(faktor) if x in (fa.get(i["aset"]) or {})}
                for i in k.get("instrumen") or [] if i.get("aset")}
    return f


def calon_agent(gate, ar: pn.Arsip, now_s: int):
    """Agent LUAR di kursi uji yang sudah >= N siklus dan belum punya laporan final untuk masa uji ini -> (kunci, masukan, ekstra). Agent rumah tidak ditinjau."""
    import analis as an
    kursi = ((gate.meja_muat()[0].get("_v2_kursi") or {}).get("kursi") or {})
    n = pn.PARAMS["n_siklus_agent"]
    for slug, e in sorted(kursi.items()):
        a = gate.luar.agen.get(slug)
        if e.get("status") != "uji" or not a or (now_s - int(e["sejak"])) // 300 < n:
            continue
        kunci = f"agent-{a['agent_id']}-{int(e['sejak'])}"
        if pn.final(ar.ambil("agent", kunci)):
            continue
        m = pn.tahap1_agent(baca_rekaman(gate, int(e["sejak"]), now_s), slug=slug, terdaftar=a, sejak=int(e["sejak"]),
                            rumah=[x["slug"] for x in an.AGENTS], fitur=pembaca_fitur(gate))
        if m is None:
            continue
        yield kunci, m, {"agent_id": a["agent_id"], "slug": slug, "jendela_akhir": m["tepercaya"]["stage1"]["trial"]["last_cycle"]}


def tinjau_simpan(ar: pn.Arsip, jenis: str, kunci: str, masukan: dict, kind: Optional[str], panggil, now_s: int, ekstra: Optional[dict] = None) -> dict:
    lama = ar.ambil(jenis, kunci)
    rek = pn.tinjau(jenis, masukan, panggil, kunci=kunci, kind=kind, now_s=now_s, ekstra=ekstra)
    if lama and not pn.final(lama):
        rek = pn.coba_lagi(lama, rek)
    ar.simpan(rek)
    return rek


def putaran(gate, panggil: Callable[[str, str], dict] = panggil_xkiro, now_s: Optional[int] = None, log: Callable[[str], None] = print,
            kode: Optional[Callable[[str], Optional[str]]] = None) -> dict:
    """Satu putaran gerbang. Peninjau yang belum dikalibrasi tidak memanggil model sama sekali. Batas biaya: `maks_panggilan_hari` panggilan per hari UTC."""
    root, ar = gate.data.workdir, arsip(gate)
    now = int(now_s if now_s is not None else gate.now())
    out = {"status": {j: pn.status_kalibrasi(root, j) for j in pn.JENIS}, "bot": [], "agent": []}
    sisa = pn.PARAMS["maks_panggilan_hari"] - ar.panggilan_hari(now)
    sumber = []
    if out["status"]["bot"]["aktif"]:
        sumber.append(("bot", ((k, m, kind, None) for k, m, kind in calon_bot(root, ar, log, kode))))
    if out["status"]["agent"]["aktif"]:
        sumber.append(("agent", ((k, m, None, x) for k, m, x in calon_agent(gate, ar, now))))
    for jenis, it in sumber:
        for kunci, masukan, kind, ekstra in it:
            if sisa <= 0:
                log(f"peninjau: batas {pn.PARAMS['maks_panggilan_hari']} panggilan/hari tercapai - sisanya besok (tetap TAHAN)")
                return out
            rek = tinjau_simpan(ar, jenis, kunci, masukan, kind, panggil, now, ekstra)
            sisa -= 1
            out[jenis].append((kunci, rek["hasil"]["vonis"]))
            log(f"peninjau {jenis} {kunci[:24]}: {rek['hasil']['sumber']} -> {rek['hasil']['vonis']}"
                + (f" (model {rek['hasil']['vonis_model']})" if rek["hasil"].get("vonis_model") else "")
                + (f" | {rek['hasil'].get('galat')}" if rek["hasil"].get("galat") else ""))
    return out


def loop(gate, stop, every_s: int = 600) -> None:
    """Thread gerbang. Galat satu putaran dicatat; penjualan sinyal / meja tidak terganggu."""
    while not stop.wait(every_s):
        try:
            gate.data.refresh()
            putaran(gate, log=gate.log)
        except Exception as e:  # noqa: BLE001
            gate.log(f"peninjau gagal: {type(e).__name__}: {str(e)[:200]}")


def tahan_naik(gate, slug: str, entri: dict) -> Optional[str]:
    """Kait P168b untuk `meja2.kursi_evaluasi`: alasan MENAHAN kenaikan kursi uji -> aktif, atau None. Agent rumah / peninjau belum dikalibrasi = None."""
    a = gate.luar.agen.get(slug)
    if a is None:
        return pn.tahan_naik_agent(None, False, False)
    aktif = status(gate, "agent")["aktif"]
    rek = arsip(gate).ambil("agent", f"agent-{a['agent_id']}-{int(entri.get('sejak') or 0)}") if aktif else None
    return pn.tahan_naik_agent(rek, aktif, True)


def _daftar_publik(ar: pn.Arsip, jenis: str, now_s: int, tunda_s: int) -> List[dict]:
    out = []
    for r in ar.daftar(jenis):
        p = pn.publik(r, now_s, tunda_s)
        out.append({"kunci": r["kunci"], "kind": r.get("kind"), "t": r.get("t"), "verdict": (r.get("hasil") or {}).get("vonis"),
                    "source": (r.get("hasil") or {}).get("sumber"), "sha": p.get("ringkasan_sha") or p.get("laporan_sha"),
                    "summarized": bool(p.get("diringkas")), "embargo_until": p.get("embargo_sampai")})
    return out


def rute(gate, parts: List[str], now_s: int, tunda_s: int = 86_400) -> Optional[Tuple[int, dict]]:
    """GET publik: /bots/analysis[/<kunci>] (bot) dan /desk/external/review[/<kunci>] (agent). Teks model = teks biasa (JSON string; web merender sebagai teks)."""
    if parts[:2] == ["bots", "analysis"] and len(parts) in (2, 3):
        jenis = "bot"
    elif parts[:3] == ["desk", "external", "review"] and len(parts) in (3, 4):
        jenis = "agent"
    else:
        return None
    ar = arsip(gate)
    kunci = parts[2] if jenis == "bot" and len(parts) == 3 else parts[3] if jenis == "agent" and len(parts) == 4 else None
    if kunci is None:
        st = status(gate, jenis)
        return 200, {"reviewer": {k: st.get(k) for k in ("status", "aktif", "berkas", "n_lulus", "n_kasus", "alasan")}, "model": pn.PARAMS["model"],
                     "brief_sha": pn.BRIEF_SHA[jenis], "reviews": _daftar_publik(ar, jenis, now_s, tunda_s),
                     "note": "LLM review can only HOLD or REJECT; LANJUT is not a slot. Texts are model output, shown as plain text."}
    if not pn.KUNCI_OK.match(kunci):
        return 400, {"error": "bad key"}
    rek = ar.ambil(jenis, kunci)
    if rek is None:
        return 404, {"error": "no such review"}
    return 200, pn.publik(rek, now_s, tunda_s)


def hias(gate, rows: List[dict]) -> List[dict]:
    """Antrean publik `/bots/submissions`: tiap kiriman yang lolos tahap 1 diberi `owner_review` (kartu teks biasa) atau keadaan peninjau."""
    ar, aktif = arsip(gate), status(gate, "bot")["aktif"]
    for r in rows:
        if (r.get("review") or {}).get("vonis") == "LOLOS_SHADOW":
            r["owner_review"] = pn.kartu(ar.ambil("bot", r["submission_sha"]), aktif)
    return rows


# ---------------------------------------------------------------- tinjauan harian GitHub: tarik laporan publik ke repo

def _get_json(url: str, timeout: int = 60) -> dict:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return json.loads(r.read().decode())


def tarik(gerbang: str, folder: str, get: Callable[[str], dict] = _get_json, log: Callable[[str], None] = print) -> Dict[str, int]:
    """Laporan peninjau dari gerbang -> `<folder>/analisis/<jenis>/<kunci>.json` (biasanya ledger/pengajuan). Hanya yang lolos `periksa_rekaman`
    (sha brief / masukan / prompt / jawaban + vonis diurai ulang) dan, untuk bot, yang tahap 1-nya = laporan publik di repo; yang masih embargo dilewati.
    Gerbang tidak terbaca = tidak menulis apa pun (bukan "tidak ada laporan")."""
    hitung = {"ditulis": 0, "sama": 0, "ditolak": 0, "embargo": 0}
    for jenis, rute_ in (("bot", "/bots/analysis"), ("agent", "/desk/external/review")):
        try:
            daftar = get(f"{gerbang}{rute_}")["reviews"]
        except Exception as e:  # noqa: BLE001
            log(f"analisis {jenis}: gerbang tidak terbaca ({type(e).__name__}) - tidak ada yang ditulis, dicoba lagi besok")
            continue
        for d in daftar:
            kunci = d.get("kunci")
            if not isinstance(kunci, str) or not pn.KUNCI_OK.match(kunci):
                continue
            if d.get("embargo_until"):
                hitung["embargo"] += 1
                continue
            path = os.path.join(folder, "analisis", jenis, f"{kunci}.json")
            lama = _baca_json(path)
            if lama and (lama.get("ringkasan_sha") or lama.get("laporan_sha")) == d.get("sha"):
                hitung["sama"] += 1
                continue
            try:
                rek = get(f"{gerbang}{rute_}/{kunci}")
            except Exception as e:  # noqa: BLE001
                log(f"analisis {jenis} {kunci[:18]}: tidak terbaca ({type(e).__name__})")
                continue
            masalah = pn.periksa_rekaman(rek) + ([] if rek.get("kunci") == kunci else ["kunci tidak cocok"])
            if jenis == "bot" and not masalah and not rek.get("diringkas"):
                masalah += _cocok_tahap1(folder, kunci, rek)
            if masalah:
                hitung["ditolak"] += 1
                log(f"analisis {jenis} {kunci[:18]}: DITOLAK - {'; '.join(masalah[:3])}")
                continue
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                json.dump(rek, f, ensure_ascii=False, indent=1, sort_keys=True)
                f.write("\n")
            hitung["ditulis"] += 1
            log(f"analisis {jenis} {kunci[:18]}: {rek['hasil']['vonis']} ditulis")
    return hitung


def _cocok_tahap1(folder: str, sha: str, rek: dict) -> List[str]:
    """Masukan bot yang dikirim ke model harus memuat laporan tahap 1 + formulir yang SAMA dengan salinan publik di repo."""
    import copy
    from engine import submission
    lap = _baca_json(os.path.join(folder, "laporan", f"{sha}.json")) or {}
    st = rek["masukan"]["tepercaya"]["stage1"]
    m = []
    if not lap or st.get("report_sha") != lap.get("report_sha") or st.get("verdict") != "LOLOS_SHADOW":
        m.append("tahap 1 di masukan bukan laporan LOLOS_SHADOW di repo")
    form = copy.deepcopy(rek["masukan"]["submission"])
    form.pop("code_text", None)
    try:
        form["identity"]["contact"] = "disimpan privat di gerbang"
        if submission.submission_sha(form) != sha:
            m.append("formulir di masukan bukan formulir kiriman ini")
    except Exception:  # noqa: BLE001
        m.append("formulir di masukan tidak terbaca")
    return m


# ---------------------------------------------------------------- CLI

def cmd_status(a) -> int:
    for j in pn.JENIS:
        st = pn.status_kalibrasi(ROOT, j)
        print(f"peninjau {j}: {st['status'].upper()} | aktif {'ya' if st['aktif'] else 'TIDAK'} | brief {pn.BRIEF_SHA[j][:18]}… | model {pn.PARAMS['model']} "
              f"| kasus {len(pn.muat_kasus(j))} | berkas {st.get('berkas') or '-'}" + (f" | {st['alasan']}" if st.get("alasan") else ""))
    print(f"params_sha {pn.PARAMS_SHA} | skema_sha {pn.SKEMA_SHA}")
    return 0


def jalankan_kalibrasi(jenis: str, panggil: Callable[[str, str], dict], *, jalan: int = pn.PARAMS["jalan_kalibrasi"], hanya: Optional[List[str]] = None,
                       model: Optional[str] = None, now_s: Optional[int] = None, log: Callable[[str], None] = print) -> dict:
    """Set kasus `jenis` x `jalan` panggilan -> rekaman kalibrasi (jawaban mentah + sha + meta per jalan). Penilaian di rekaman hanya informasi: kunci jalur
    selalu menilai ULANG dari jawaban mentah (`peninjau.status_kalibrasi`)."""
    semua = pn.muat_kasus(jenis)
    kasus = [k for k in semua if not hanya or k["id"] in hanya]
    now = int(now_s if now_s is not None else time.time())
    rec = {"v": 1, "jenis": jenis, "t": now, "t_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)), "provider": pn.PARAMS["provider"],
           "model": model or pn.PARAMS["model"], "params_sha": pn.PARAMS_SHA, "brief_sha": pn.BRIEF_SHA[jenis], "skema_sha": pn.SKEMA_SHA,
           "kasus_sha": pn.kasus_sha(semua), "jalan_diminta": jalan, "sebagian": bool(hanya), "kasus": []}
    masuk = keluar = 0
    for k in kasus:
        jl = []
        for i in range(jalan):
            r = pn.tinjau(jenis, k["masukan"], panggil, kunci=f"kal-{k['id']}-{i + 1}", now_s=now)
            u = (r.get("meta") or {}).get("usage") or {}
            masuk += int(u.get("prompt_tokens") or 0)
            keluar += int(u.get("completion_tokens") or 0)
            jl.append({"jawaban_mentah": r["jawaban_mentah"], "jawaban_sha": r["jawaban_sha"], "prompt_sha": r["prompt_sha"], "masukan_sha": r["masukan_sha"],
                       "meta": r["meta"], "galat": r["hasil"].get("galat"), "vonis_model": r["hasil"].get("vonis_model"), "vonis": r["hasil"]["vonis"]})
            log(f"  {k['id']} jalan {i + 1}: {r['hasil']['sumber']} model={r['hasil'].get('vonis_model')} akhir={r['hasil']['vonis']} "
                f"({(r.get('meta') or {}).get('detik')} s, finish {(r.get('meta') or {}).get('finish_reason')})")
        rec["kasus"].append({"id": k["id"], "harus": k["harus"], "jalan": jl})
    rec["usage_total"] = {"prompt_tokens": masuk, "completion_tokens": keluar,
                          "perkiraan_usd": round(masuk * HARGA_PER_TOKEN["masuk"] + keluar * HARGA_PER_TOKEN["keluar"], 4)}
    n = pn.nilai_kalibrasi(rec, semua)
    rec["nilai_saat_ditulis"] = {"lulus": n["lulus"], "n_lulus": n["n_lulus"], "n_kasus": n["n_kasus"]}
    return rec


def cmd_kalibrasi(a) -> int:
    import analis as an
    if a.palsu:
        panggil = panggil_palsu
    else:
        if not os.environ.get(an.PROVIDERS[pn.PARAMS["provider"]]["key_var"]):
            print(f"{an.PROVIDERS[pn.PARAMS['provider']]['key_var']} tidak ada di env: jalankan lewat `railway run --service fabius-x402 python -X utf8 "
                  f"tools/peninjau_llm.py kalibrasi --jenis {a.jenis}` (kunci hanya di Railway)")
            return 2
        panggil = panggil_xkiro
    rec = jalankan_kalibrasi(a.jenis, panggil, jalan=a.jalan, hanya=a.kasus, model="palsu" if a.palsu else None, log=lambda m: print(m, flush=True))
    n = pn.nilai_kalibrasi(rec)
    for p in n["kasus"]:
        print(f"{'LULUS' if p['lulus'] else 'GAGAL'} {p['id']}: vonis {p['vonis']}" + (f" | {'; '.join(p['masalah'][:3])}" if p["masalah"] else ""))
    u = rec["usage_total"]
    print(f"kalibrasi {a.jenis}: {'LULUS' if n['lulus'] else 'GAGAL'} ({n['n_lulus']}/{n['n_kasus']} kasus)" + (f" | {'; '.join(n['masalah'])}" if n["masalah"] else "")
          + f" | token {u['prompt_tokens']} masuk + {u['completion_tokens']} keluar ≈ ${u['perkiraan_usd']}")
    if a.palsu and not a.keluar:
        print("--palsu: tidak ditulis ke ledger (bukan kalibrasi sah). Pakai --keluar <berkas> untuk menyimpannya.")
        return 0 if n["lulus"] else 1
    path = a.keluar or os.path.join(KALIBRASI_DIR, time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(rec["t"])) + f"-{a.jenis}.json")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    print(f"ditulis {os.path.relpath(path, ROOT)} - commit + push supaya gerbang membacanya; status: python -X utf8 tools/peninjau_llm.py status")
    return 0 if n["lulus"] else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    k = sub.add_parser("kalibrasi")
    k.add_argument("--jenis", choices=pn.JENIS, required=True)
    k.add_argument("--jalan", type=int, default=pn.PARAMS["jalan_kalibrasi"])
    k.add_argument("--kasus", nargs="*", help="hanya kasus ini (rekaman SEBAGIAN tidak pernah mengaktifkan peninjau)")
    k.add_argument("--palsu", action="store_true", help="model palsu tanpa biaya: menguji pipa, bukan kalibrasi")
    k.add_argument("--keluar", help="tulis rekaman ke berkas ini (bawaan: ledger/peninjau/kalibrasi/<UTC>-<jenis>.json)")
    a = ap.parse_args()
    return {"status": cmd_status, "kalibrasi": cmd_kalibrasi}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
