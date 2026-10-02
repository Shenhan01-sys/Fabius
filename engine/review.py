"""Peninjau-bot penerbit (F-D72): validasi -> identitas -> gerbang G1-G11 -> KPI K1-K5 -> laporan ber-sha. TANPA agen LLM.

Keputusan builder 2 Okt 2026 (malam): meninjau bot kiriman sebaiknya pakai BOT (aturan deterministik + KPI minimal supaya Fabius juga
untung), bukan agen. Konsekuensi yang harus dikatakan terus terang: teks teori (`theory.*`) TIDAK dinilai kualitasnya oleh mesin - ia
wajib sebagai pengungkapan (untuk pembaca manusia dan FE), sedangkan yang MENENTUKAN adalah bukti terukur (gerbang + KPI) dan kelengkapan/
konsistensi mekanis (skema, rujukan yang wajib ada, klaim vs terukur). Manusia hanya boleh MEMVETO (menolak); tidak ada jalur manusia atau
model untuk menerima di luar vonis bot (satu arah, F-D11).

Laporan deterministik: tidak memuat jam dinding; memuat sha spesifikasi, sha pengajuan, sha data, sha parameter (kunci), dan sha laporan itu
sendiri (untuk di-anchor). `mengikat` hanya True bila: identitas terverifikasi, parameter = kunci, vonis LOLOS_SHADOW. Selain itu laporan
INDIKATIF (berguna untuk penerbit dan pengembangan, tidak membuka apa pun).
"""
from __future__ import annotations

import dataclasses
from typing import Any, Dict, Iterable, List, Optional

from . import locks, submission
from .data import MarketData
from .gates import GateParams, Pnl, format_results, run_gates, verdict
from .kpi import KpiParams
from .sinyal import data_fingerprint
from .slots import SlotParams
from .spec import sha0x

REPORT_V = 1


def review(sub: Dict[str, Any], data: MarketData, incumbents: Optional[Dict[str, Pnl]], *,
           gate_params: Optional[GateParams] = None, kpi_params: Optional[KpiParams] = None, slot_params: Optional[SlotParams] = None,
           enabled_kinds: Iterable[str] = submission.ENABLED_KINDS, existing_ids: Iterable[str] = (),
           identity: Optional[Dict[str, Any]] = None, prior_family_submissions: int = 0,
           epoch_seed: Optional[int] = None) -> Dict[str, Any]:
    """Tinjau satu pengajuan. `incumbents` = PnL harian BUKU SLOT SEKARANG + antrean (G10 bergantung padanya; laporan terikat ke buku lewat
    pemanggil: lihat `slots.book_sha`). `identity` = {'signature','chain_id','nonce','deadline','now_s', 'used_nonces', 'payout_signature'} bila
    ada. `prior_family_submissions` = jumlah pengajuan sebelumnya oleh keluarga yang sama (dari registri, bukan dari penerbit): ikut menaikkan
    ambang Sharpe G3. `epoch_seed` menggantikan seed bawaan (idealnya diturunkan dari hash blok SETELAH pengajuan di-komit)."""
    gp = gate_params or GateParams()
    kp = kpi_params or KpiParams()
    sp = slot_params or SlotParams()
    problems = submission.validate(sub, existing_ids=existing_ids, enabled_kinds=enabled_kinds)
    base: Dict[str, Any] = {"v": REPORT_V, "vonis": "TOLAK_FORMULIR", "masalah_formulir": problems, "gerbang": [], "gagal": [], "tak_terukur": [],
                            "mengikat": False}
    if problems:
        return _seal(base)
    kunci = locks.status(gp, kp, sp)
    percobaan = int(sub["evidence"]["percobaan"]) + int(prior_family_submissions) + 1
    gp2 = dataclasses.replace(gp, n_trials=max(gp.n_trials, percobaan), seed=epoch_seed if epoch_seed is not None else gp.seed)
    spec = submission.to_botspec(sub)
    ident = {"diverifikasi": False, "masalah": []}
    if identity:
        probs = submission.verify_identity(
            sub, identity["signature"], identity["chain_id"], identity["nonce"], identity["deadline"], identity["now_s"],
            used_nonces=identity.get("used_nonces"), payout_signature_hex=identity.get("payout_signature"))
        ident = {"diverifikasi": not probs, "masalah": probs}
    results = run_gates(spec, data, incumbents, gp2, kp, claims=sub["evidence"].get("klaim"))
    v, fails, nas = verdict(results)
    if identity and ident["masalah"]:
        v = "TOLAK_IDENTITAS"
    report = {"v": REPORT_V, "bot_id": spec.bot_id, "template": spec.template, "spec_sha": spec.sha(), "fingerprint": spec.fingerprint(),
              "submission_sha": submission.submission_sha(sub), "data_hash": data_fingerprint(spec, data),
              "vonis": v, "gagal": fails, "tak_terukur": nas, "n_trials": gp2.n_trials, "seed": gp2.seed,
              "identitas": ident, "kunci": {"state": kunci["state"], "sha_kini": kunci["sha_kini"], "sha_kunci": kunci["sha_kunci"]},
              "gerbang": [dataclasses.asdict(r) for r in results],
              "mengikat": bool(ident["diverifikasi"] and kunci["state"] == "TERKUNCI" and v == "LOLOS_SHADOW")}
    return _seal(report)


def _seal(report: Dict[str, Any]) -> Dict[str, Any]:
    body = {k: v for k, v in report.items() if k != "report_sha"}
    report["report_sha"] = sha0x(body)
    return report


def render(report: Dict[str, Any]) -> str:
    """Tampilan teks laporan (angka tetap dicetak ulang dari laporan, bukan dikarang)."""
    if report["vonis"] == "TOLAK_FORMULIR":
        lines = ["== PENGAJUAN DITOLAK (formulir) =="] + [f"  - {p}" for p in report["masalah_formulir"]]
        lines.append(f"report_sha {report['report_sha']}")
        return "\n".join(lines)
    from .gates import GateResult
    results: List[GateResult] = [GateResult(**g) for g in report["gerbang"]]
    head = f"{report['bot_id']} (template {report['template']})"
    text = format_results(head, results)
    ident = report["identitas"]
    text += (f"\nIDENTITAS: {'terverifikasi' if ident['diverifikasi'] else 'BELUM terverifikasi'}"
             + (f" - {'; '.join(ident['masalah'])}" if ident["masalah"] else ""))
    text += f"\nKUNCI PARAMETER: {report['kunci']['state']}"
    text += f"\nMENGIKAT: {'ya' if report['mengikat'] else 'TIDAK (indikatif)'} | vonis {report['vonis']} | N percobaan {report['n_trials']}"
    text += f"\nreport_sha {report['report_sha']}\nspec_sha {report['spec_sha']}\nsubmission_sha {report['submission_sha']}\ndata_hash {report['data_hash']}"
    return text
