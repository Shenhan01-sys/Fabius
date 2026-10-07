"""P167c (epik 12 §3.3, F-D125): jenis `feed` - program penerbit menerbitkan bobot target sendiri; kami TIDAK bisa me-replay metodenya.

Satu-satunya bukti = rekam jejak MAJU. Aturan (pola `SelectionAnchor`: komit sebelum `barClose`, satu per bar, hash di rantai):
  - Komit = bobot target bertanda tangan EIP-712 (`FeedCommit`, domain sama dengan formulir pengajuan: "Fabius Bot Issuer" versi skema) untuk
    satu `barClose` (00:00 UTC). Bobot = bilangan bulat per sejuta (ppm; 250000 = 0,25) supaya kanonik lintas bahasa (tanpa format float),
    terhingga oleh konstruksi, gross <= 1 000 000, kunci = simbol universe bot yang terdaftar.
  - Diterima gerbang hanya bila `now < barClose - BATAS_SEBELUM_TUTUP_S` dan `barClose <= now + MAKS_KE_DEPAN_S`; satu per (bot, barClose);
    penanda tangan = dompet penerbit yang terdaftar.
  - Jalur off-chain-lalu-anchor (kontrak yang SUDAH ada, tanpa deploy baru): sesudah batas terima, gerbang menghitung akar Merkle (OZ, pasangan
    terurut) atas semua komit untuk `barClose` itu dan mengunci akarnya di `LockRegistry` (label `LABEL_ANCHOR`) SEBELUM `barClose`.
    `lockedAt(gerbang, label, akar)` < `barClose` = bukti publik bahwa bobot itu ada sebelum bar dibuka. Akar yang tidak ter-anchor sebelum
    penutupan = komit itu TIDAK dinilai (gap, tak terukur), bukan dinilai dengan kepercayaan pada jam gerbang.
  - Dinilai MAJU di ledger paper yang sama (`engine/ledger.py`: tick / gap / settle lewat `replay` yang sama); tick feed asof = barClose - 1 hari
    (posisi dipegang selama bar yang dibuka di barClose). Tanpa komit sah = `gap` (UNGKAPKAN), komit tidak pernah diisi belakangan.
  - Gerbang replay G1-G11 + KPI TIDAK BERLAKU (N/A, bukan LOLOS): vonis tinjauan `MAJU_FEED`, bayangan maju 120 hari (`BAYANGAN_HARI`), TANPA slot
    (bot feed tidak pernah menjadi penantang buku; jalur slot sesudah 120 hari menunggu keputusan builder tentang apa itu "terbukti").
  - Label kepercayaan di semua tampilan: `LABEL_KEPERCAYAAN`.
"""
from __future__ import annotations

import hashlib
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from . import chain
from .series import DAY_MS
from .spec import BotSpec

FEED_METHOD = "FEED"
PARAM_NAMA = "feed"
PENGGARIS = {"fee_bps_sisi": 7, "funding": "nyata dua sisi"}         # milik kami (sama dengan rule / code)
BAYANGAN_HARI = 120                                                    # disetujui builder (2x bayangan bot replay)
BATAS_SEBELUM_TUTUP_S = 600                                            # komit ditutup 10 menit sebelum penutupan: waktu untuk anchor SEBELUM penutupan
JEDA_ANCHOR_S = 30                                                     # anchor tidak dikirim < 30 s sebelum penutupan (tx bisa jatuh sesudahnya)
MAKS_KE_DEPAN_S = 2 * 86_400                                           # sama dengan SelectionAnchor.MAX_AHEAD
LABEL_KEPERCAYAAN = "tidak bisa diverifikasi ulang"
LABEL_ANCHOR = "FABIUS-FEED"                                           # botId LockRegistry untuk akar komit feed (dikunci dompet gerbang)
PPM = 1_000_000
VONIS = "MAJU_FEED"
DAY_S = 86_400

FEED_TYPES = [{"name": "issuer", "type": "address"}, {"name": "botId", "type": "bytes32"}, {"name": "specSha", "type": "bytes32"},
              {"name": "barClose", "type": "uint64"}, {"name": "weightsSha", "type": "bytes32"}]


def targets(spec: BotSpec, data) -> list:
    """REGISTRY["FEED"]: tidak ada metode yang bisa dijalankan. Gerbang replay yang terpanggil untuk feed = tak terukur (bukan lolos, bukan gagal)."""
    raise NotImplementedError("feed tidak bisa direplay: hanya bukti maju bertanda tangan yang dikomit sebelum penutupan bar (N/A, bukan LOLOS)")


# ---------------------------------------------------------------- bobot + pesan bertanda tangan

def validate_bobot(bobot: Any, universe: Sequence[str]) -> List[str]:
    """Bobot ppm: dict {simbol universe: int}; |w| <= 1e6; gross <= 1e6; kosong = flat (sah). Angka desimal / NaN / bool / teks ditolak."""
    if not isinstance(bobot, dict):
        return ["bobot harus objek {simbol: bilangan bulat ppm}"]
    if len(bobot) > len(universe):
        return ["bobot memuat lebih banyak aset dari universe"]
    out, gross = [], 0
    uni = set(universe)
    for k, v in bobot.items():
        if not isinstance(k, str) or k not in uni:
            out.append(f"bobot: {repr(str(k))[:24]} bukan simbol universe bot ini")
            continue
        if isinstance(v, bool) or not isinstance(v, int):
            out.append(f"bobot.{k}: harus bilangan bulat ppm (1000000 = 1,0), bukan {type(v).__name__}")
            continue
        if abs(v) > PPM:
            out.append(f"bobot.{k}: |w| > {PPM}")
            continue
        gross += abs(v)
    if not out and gross > PPM:
        out.append(f"bobot: gross {gross} ppm > {PPM} (gross <= 1)")
    return out[:20]


def bobot_kanonik(bobot: Dict[str, int]) -> str:
    """Teks kanonik: 'BTCUSDT:250000,ETHUSDT:-100000' (urut simbol, nol dibuang); kosong = flat. Sama persis di web (lihat TL42)."""
    return ",".join(f"{a}:{int(bobot[a])}" for a in sorted(bobot) if int(bobot[a]) != 0)


def weights_sha(bobot: Dict[str, int]) -> str:
    return "0x" + hashlib.sha256(bobot_kanonik(bobot).encode("ascii")).hexdigest()


def typed_data(bot_id: str, spec_sha: str, issuer: str, bar_close: int, bobot: Dict[str, int], chain_id: int,
               name: str = "Fabius Bot Issuer", version: str = "2") -> Dict[str, Any]:
    return {
        "types": {"EIP712Domain": [{"name": "name", "type": "string"}, {"name": "version", "type": "string"}, {"name": "chainId", "type": "uint256"}],
                  "FeedCommit": FEED_TYPES},
        "primaryType": "FeedCommit",
        "domain": {"name": name, "version": version, "chainId": chain_id},
        "message": {"issuer": issuer, "botId": chain.hex0x(chain.ascii32(bot_id)), "specSha": spec_sha, "barClose": int(bar_close),
                    "weightsSha": weights_sha(bobot)},
    }


def recover(td: Dict[str, Any], signature_hex: str) -> str:
    try:
        from eth_account import Account
        from eth_account.messages import encode_typed_data
    except ImportError as e:                                                    # pragma: no cover
        raise RuntimeError("verifikasi komit feed butuh eth-account; tanpa itu komit tidak bisa diterima") from e
    return Account.recover_message(encode_typed_data(full_message=td), signature=signature_hex)


def periksa_waktu(bar_close: Any, now_s: int) -> Optional[str]:
    """None bila `bar_close` sah untuk komit pada `now_s` (pola SelectionAnchor + batas anchor)."""
    if isinstance(bar_close, bool) or not isinstance(bar_close, int) or bar_close <= 0 or bar_close % DAY_S:
        return "bar_close harus detik UNIX penutupan bar harian (kelipatan 86400, 00:00 UTC)"
    if now_s >= bar_close - BATAS_SEBELUM_TUTUP_S:
        return f"terlambat: komit untuk bar ini ditutup {BATAS_SEBELUM_TUTUP_S} detik sebelum penutupan (anchor harus sempat sebelum bar dibuka)"
    if bar_close > now_s + MAKS_KE_DEPAN_S:
        return f"terlalu jauh ke depan (maks {MAKS_KE_DEPAN_S // 3600} jam)"
    return None


def daun(rec: Dict[str, Any]) -> bytes:
    """Daun Merkle satu komit = keccak256(abi.encode(issuer, botId, specSha, barClose, weightsSha)) - statis, bisa diulang di Solidity."""
    return chain.keccak256(chain.abi_encode(("address", "bytes32", "bytes32", "uint64", "bytes32"),
                                            (rec["issuer"], chain.ascii32(rec["bot_id"]), chain.from_hex(rec["spec_sha"]), int(rec["bar_close"]),
                                             chain.from_hex(rec["weights_sha"]))))


def akar(recs: Sequence[Dict[str, Any]]) -> Tuple[bytes, Dict[str, List[str]]]:
    """(akar, {daun hex: bukti hex}) atas komit SATU bar_close (urutan masuk tidak berpengaruh)."""
    leaves = [daun(r) for r in recs]
    root = chain.merkle_root(leaves)
    return root, {chain.hex0x(lf): [chain.hex0x(p) for p in chain.merkle_proof(leaves, lf)] for lf in leaves}


def uri_anchor(bar_close: int, n: int) -> str:
    return f"fabius-feed:{bar_close}:{n}"


def lock_calldata(root: bytes, bar_close: int, n: int) -> bytes:
    """Calldata `LockRegistry.lock(bytes32 botId, bytes32 specSha, string uri)` untuk akar komit feed satu bar (kontrak yang sudah ada)."""
    sel = chain.keccak256(b"lock(bytes32,bytes32,string)")[:4]
    uri = uri_anchor(bar_close, n).encode("ascii")
    pad = uri + b"\x00" * (-len(uri) % 32)
    return sel + chain.ascii32(LABEL_ANCHOR) + root + (96).to_bytes(32, "big") + len(uri).to_bytes(32, "big") + pad


def periksa_komit(rec: Dict[str, Any], issuer: str, spec_sha: str, universe: Sequence[str], chain_id: int,
                  locked_at: Optional[Callable[[str, str], Optional[int]]] = None, locker: Optional[str] = None) -> List[str]:
    """Pemeriksaan ULANG satu komit publik (siapa pun bisa): tanda tangan = penerbit, waktu terima < batas, bobot sah, daun -> bukti -> akar,
    anchor: 0 < lockedAt < barClose (dibaca ulang dari chain bila `locked_at` diberikan; galat baca DILEMPAR = TUNDA, bukan 'tidak ada'),
    dikunci alamat gerbang `locker` bila diberikan (akar yang dikunci alamat lain bukan anchor Fabius)."""
    out: List[str] = []
    try:
        bc = int(rec["bar_close"])
        out += validate_bobot(rec["bobot"], universe)
        if rec.get("spec_sha") != spec_sha or rec.get("issuer") != issuer:
            out.append("komit bukan untuk spesifikasi / penerbit terdaftar")
        if rec.get("weights_sha") != weights_sha(rec["bobot"]):
            out.append("weights_sha tidak cocok dengan bobot")
        if int(rec["t_terima"]) >= bc - BATAS_SEBELUM_TUTUP_S:
            out.append("diterima sesudah batas (terlambat)")
        td = typed_data(rec["bot_id"], spec_sha, issuer, bc, rec["bobot"], chain_id)
        try:
            if recover(td, rec["signature"]) != issuer:
                out.append("tanda tangan bukan dompet penerbit")
        except RuntimeError:
            raise
        except Exception as e:                                                  # noqa: BLE001 - tanda tangan rusak = tolak
            out.append(f"tanda tangan tidak terbaca ({type(e).__name__})")
        lf = daun(rec)
        if chain.hex0x(lf) != rec.get("leaf"):
            out.append("daun tidak cocok dengan isi komit")
        anc = rec.get("anchor") or {}
        root = rec.get("root")
        if not root or not chain.merkle_verify([chain.from_hex(p) for p in rec.get("proof") or []], chain.from_hex(root), lf):
            out.append("bukti Merkle tidak menuju akar")
        la = anc.get("locked_at")
        if not isinstance(la, int) or not 0 < la < bc:
            out.append("akar tidak ter-anchor sebelum penutupan bar (tak terukur)")
        elif locker is not None and str(anc.get("locker", "")).lower() != locker.lower():
            out.append("akar dikunci alamat lain, bukan gerbang Fabius")
        elif locked_at is not None:
            got = locked_at(anc.get("locker", ""), root)
            if got != la:
                out.append(f"lockedAt on-chain {got} != tercatat {la}")
    except (KeyError, TypeError, ValueError) as e:
        out.append(f"komit tidak lengkap ({type(e).__name__})")
    return out


# ---------------------------------------------------------------- ledger maju (memakai primitif `engine/ledger.py`)

def tick_body(spec: BotSpec, md, rec: Dict[str, Any], prev_targets: Optional[Dict[str, float]]) -> Dict[str, Any]:
    """Isi tick feed pada asof = bar_close - 1 hari: target = bobot komit / 1e6; data_hash + sinyal + n_aset dihitung dari bar seperti bot lain."""
    from .ledger import present_assets
    from .sinyal import data_fingerprint, diff_signals, ref_prices
    from .target import Target
    asof = int(rec["bar_close"]) * 1000 - DAY_MS
    pit = md.upto(asof)
    cur = Target(spec.bot_id, asof, {a: rec["bobot"][a] / PPM for a in sorted(rec["bobot"]) if rec["bobot"][a]}, {})
    prev = Target(spec.bot_id, asof - DAY_MS, dict(prev_targets), {}) if prev_targets is not None else None
    dh = data_fingerprint(spec, pit)
    sigs = diff_signals(spec, prev, cur, dh, ref_prices(spec, pit, asof))
    return {"targets": dict(cur.weights), "data_hash": dh, "signal_ids": [s.id() for s in sigs], "n_aset": len(present_assets(spec, pit, asof)),
            "feed": {"leaf": rec["leaf"], "root": rec["root"], "weights_sha": rec["weights_sha"], "locked_at": rec["anchor"]["locked_at"],
                     "t_terima": int(rec["t_terima"])}}


def _komit_bar(komits: Sequence[Dict[str, Any]], bar_close_s: int) -> List[Dict[str, Any]]:
    return [r for r in komits if int(r.get("bar_close", -1)) == bar_close_s]


def step(spec: BotSpec, md, now_ms: int, records: Sequence[dict], komits: Optional[Sequence[Dict[str, Any]]], issuer: str, spec_sha: str,
         chain_id: int = 97, locked_at: Optional[Callable[[str, str], Optional[int]]] = None, locker: Optional[str] = None,
         md_settle=None) -> Tuple[List[dict], List[str]]:
    """Satu putaran harian ledger feed (padanan `ledger.step`). `komits` = None -> daftar komit tidak terbaca (gerbang mati): TIDAK ada tick / gap
    hari ini kecuali batas 12 jam lewat (TUNDA, bukan 'tidak ada komit'). Komit sah + ter-anchor -> tick; tidak ada / tidak sah -> gap dengan
    alasannya. Settle = `ledger.compute_settle` (replay yang sama). Tidak menulis berkas."""
    from . import ledger as L
    if not records or records[0].get("type") != "genesis":
        raise L.LedgerError("ledger feed belum punya genesis")
    g = records[0]
    if g["spec_sha"] != spec.sha():
        raise L.LedgerError(f"{spec.bot_id}: spesifikasi berubah sejak genesis (pivot = ledger baru)")
    chain_: List[dict] = list(records)
    new: List[dict] = []
    notes: List[str] = []

    def push(rec: dict) -> None:
        sealed = L.seal(rec, L.head(chain_))
        chain_.append(sealed)
        new.append(sealed)

    done = {r["asof"] for r in chain_ if r["type"] in ("tick", "gap")}
    last_closed = L.last_closed_bar(now_ms)
    d = max(g["first_asof"], (max(done) + DAY_MS) if done else g["first_asof"])
    while d <= last_closed:
        if d in done:
            d += DAY_MS
            continue
        late = now_ms > d + DAY_MS + L.MAX_LAG_S * 1000
        if komits is None:
            if late:
                push(L.make_gap(spec, d, "daftar komit feed tidak terbaca sampai batas 12 jam", now_ms))
                notes.append(f"gap {L.date_of(d)}: daftar komit tidak terbaca sampai batas 12 jam")
            else:
                notes.append(f"{L.date_of(d)} TUNDA: daftar komit feed tidak terbaca")
            d += DAY_MS
            continue
        bc = (d + DAY_MS) // 1000
        sah, alasan = None, "tidak ada komit untuk bar ini"
        for rec in _komit_bar(komits, bc):
            masalah = periksa_komit(rec, issuer, spec_sha, spec.universe, chain_id, locked_at, locker)
            if not masalah:
                sah = rec
                break
            alasan = "komit tidak sah: " + "; ".join(masalah[:3])
        if sah is None or late:
            why = alasan if sah is None else "tidak ada tick sebelum batas 12 jam"
            push(L.make_gap(spec, d, why, now_ms))
            notes.append(f"gap {L.date_of(d)}: {why}")
        else:
            prev = next((r for r in reversed(chain_) if r["type"] == "tick" and r["asof"] == d - DAY_MS), None)
            body = tick_body(spec, md, sah, prev["targets"] if prev else None)
            lag_s = (now_ms - (d + DAY_MS)) // 1000
            push({"type": "tick", "bot_id": spec.bot_id, "spec_sha": spec.sha(), "asof": d, "asof_date": L.date_of(d), "close_utc": L.utc_iso(d + DAY_MS),
                  "emitted_utc": L.utc_iso(now_ms), "lag_s": lag_s, **body})
            notes.append(f"tick {L.date_of(d)}: komit feed ter-anchor, {len(body['targets'])} aset dipegang")
        done.add(d)
        d += DAY_MS
    md_s = md_settle if md_settle is not None else md
    for bar in L.settleable_bars(chain_):
        rec = L.compute_settle(spec, md_s, chain_, bar)
        if rec is not None:
            push(rec)
            notes.append(f"settle {rec['bar_date']}: net {rec['net'] * 1e4:+.1f} bps")
    return new, notes


def verify(spec: BotSpec, records: Sequence[dict], md, komits: Sequence[Dict[str, Any]], issuer: str, spec_sha: str, chain_id: int = 97,
           locked_at: Optional[Callable[[str, str], Optional[int]]] = None, locker: Optional[str] = None, md_settle=None) -> List[str]:
    """Hitung ULANG ledger feed: rantai (`ledger.verify_chain`), tiap tick = komit sah + ter-anchor yang bobotnya SAMA, data_hash / sinyal / n_aset
    dari bar, tiap settle dari replay. Beda = ledger dipalsukan atau komit diganti."""
    from . import ledger as L
    p = L.verify_chain(records)
    if p:
        return p
    if records[0].get("spec_sha") != spec.sha():
        return ["spec_sha genesis tidak sama dengan spesifikasi feed sekarang"]
    md_s = md_settle if md_settle is not None else md
    for i, r in enumerate(records):
        if r["type"] == "tick":
            bc = (r["asof"] + DAY_MS) // 1000
            cands = [k for k in _komit_bar(komits, bc) if k.get("leaf") == (r.get("feed") or {}).get("leaf")]
            if not cands:
                p.append(f"#{i} tick {r['asof_date']}: komit dengan daun ini tidak ada")
                continue
            masalah = periksa_komit(cands[0], issuer, spec_sha, spec.universe, chain_id, locked_at, locker)
            if masalah:
                p.append(f"#{i} tick {r['asof_date']}: komit tidak sah ({masalah[0]})")
                continue
            prev = next((x for x in reversed(records[:i]) if x["type"] == "tick" and x["asof"] == r["asof"] - DAY_MS), None)
            want = tick_body(spec, md, cands[0], prev["targets"] if prev else None)
            for k in ("targets", "data_hash", "signal_ids", "n_aset", "feed"):
                if r.get(k) != want[k]:
                    p.append(f"#{i} tick {r['asof_date']}: {k} BEDA dari hitung-ulang")
        elif r["type"] == "settle":
            want = L.compute_settle(spec, md_s, records[:i], r["bar"])
            if want is None:
                p.append(f"#{i} settle {r['bar_date']}: tak bisa dihitung ulang")
                continue
            if abs(r["net"] - want["net"]) > L.SETTLE_TOL or r.get("turnover") != want["turnover"] or r.get("n_held") != want["n_held"]:
                p.append(f"#{i} settle {r['bar_date']}: BEDA dari hitung-ulang")
    return p
