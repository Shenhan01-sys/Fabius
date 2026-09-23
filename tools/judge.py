"""Lapisan penilai BISA-DICABUT: Jev kalau ada, LLM OpenAI-compatible lain kalau tidak, apa-apa
kalau dua-duanya tidak ada.

Kenapa berbentuk adapter dan bukan langsung panggil Jev: biaya Jev kecil (terukur: 669 token masuk
= ~$0,000028/panggilan) tapi tetap berbayar, dan keputusan "pakai yang bayar" bukan keputusan
teknis - itu keputusan builder. Jadi kodenya tidak boleh mengasumsikan jawaban ada. Aturan
desainnya, diurut:

1. **Gerbang menentukan, penilai hanya boleh MENAMBAH penolakan.** Hasil judge tidak pernah bisa
   mengubah ABSTAIN menjadi ENTER. Ini doktrin "repair-never-up" + "spend limits are enforced
   independently from model output".
2. **Tanpa kredensial = jalan terus.** `--judge auto` akan memakai Jev kalau kuncinya ada, lalu
   LLM OpenAI-compatible kalau base URL-nya ada, dan kalau tidak ada keduanya: mode deterministik
   murni, dengan status jujur di keluaran.
3. **Yang gagal selalu tercatat, tidak pernah dianggap lulus.** jawaban tak terparse, HTTP gagal,
   confidence tidak masuk ambang -> `judge_status` terisi dan kandidat TIDAK naik kelas.
4. **Biaya per panggilan dicatat** di artefak keputusan, supaya klaim "murah" bisa diperiksa,
   bukan diingat-ingat.

Provider di-url-kan lewat environment, jadi ganti model = ganti env, bukan ganti kode:
  JEV        : TYPESAFE_API_KEY  (+ OPSIONAL JEV_MODEL, default jev-latest)
  OpenAI-compat: HQ_BASE_URL + HQ_API_KEY + HQ_MODEL        (mis. openrouter /groq /pieverse)
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

JEV_URL_DEFAULT = "https://api.typesafe.ai/v1/systemone"
JEV_PRICE_IN_PER_MTOK = 0.042   # dari blog resmi, dikutip di vault/02-Ambang.md
JEV_PRICE_OUT_PER_MTOK = 0.0    # "Output tokens: FREE (too cheap to meter)"

STATE_SYSTEM = (
    "You are a risk gate for a BSC memecoin screening engine. You never open positions. "
    "Answer with JSON only: "
    '{"dominant_risk": one of ["illiquidity_exit","young_history","bundled_volume",'
    '"lp_pull","none"], "veto": true or false, "confidence": 0..1, "reason": <=90 chars}'
)


def _read_env_file(paths, name):
    for p in paths:
        try:
            for ln in open(p, encoding="utf-8"):
                ln = ln.strip()
                if ln.startswith(name + "="):
                    v = ln.split("=", 1)[1].strip().strip('"').strip("'")
                    if v:
                        return v, p
        except OSError:
            continue
    return "", None


def _key():
    k = (os.environ.get("TYPESAFE_API_KEY") or "").strip()
    if k:
        return k, "env"
    return _read_env_file([os.path.join(os.path.expanduser("~"), ".config", "typesafe", ".env")],
                          "TYPESAFE_API_KEY")


def _post(url, payload, headers, timeout=60):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers=headers)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace")), round(time.time() - t0, 2), None
    except urllib.error.HTTPError as e:
        return e.code, None, round(time.time() - t0, 2), f"HTTP {e.code}: {e.read().decode('utf-8','replace')[:180]}"
    except Exception as e:  # noqa: BLE001
        return None, None, round(time.time() - t0, 2), f"{type(e).__name__}: {str(e)[:170]}"


# ----------------------------------------------------------------------------- Jev (terpilih)

def judge_jev(state, risk_label):
    key, src = _key()
    if not key:
        return {"provider": "jev", "available": False, "why": "tidak ada TYPESAFE_API_KEY"}
    body = {
        "model": (os.environ.get("JEV_MODEL") or "jev-latest").strip(),
        "state": state,
        "questions": {
            "veto": {"type": "noul",
                     "instructions": f"A human who had to exit at today's liquidity within 24h "
                                      f"would lose a meaningful part of the position on {risk_label}"},
            "dominant_risk": {"type": "choice",
                              "instructions": "Which single risk is decisive for this candidate",
                              "criteria": {
                                  "illiquidity_exit": "cannot exit at size",
                                  "young_history": "no data to validate anything",
                                  "bundled_volume": "volume is one actor in disguise",
                                  "lp_pull": "liquidity withdrawable at any time",
                                  "none": "no dominant risk"}},
        },
    }
    st, d, lat, err = _post(JEV_URL_DEFAULT, body, {
        "Authorization": f"Bearer {key}", "Content-Type": "application/json",
        "Accept": "application/json", "User-Agent": "lencana-judge/1.0"})
    if st != 200 or not isinstance(d, dict):
        return {"provider": "jev", "available": True, "ok": False, "why": err or f"HTTP {st}",
                "latency_s": lat}
    ans = d.get("answers") or {}
    vetoq = ans.get("veto") or {}
    riskq = ans.get("dominant_risk") or {}
    usage = d.get("usage") or {}
    tin = int(usage.get("input_tokens") or 0)
    return {
        "provider": "jev", "available": True, "ok": True, "model": d.get("model"),
        "latency_s": lat,
        "veto_prob": vetoq.get("noul"),
        "dominant_risk": riskq.get("choice"),
        "confidence": riskq.get("confidence"),
        "probabilities": riskq.get("probabilities"),
        "cost_usd": round(tin / 1e6 * JEV_PRICE_IN_PER_MTOK, 8),
        "tokens_in": tin, "tokens_out": int(usage.get("output_tokens") or 0),
    }


# ------------------------------------------------------------- cadangan: LLM OpenAI-compatible

def judge_openai_compat(state, risk_label):
    base = (os.environ.get("HQ_BASE_URL") or "").strip().rstrip("/")
    key = (os.environ.get("HQ_API_KEY") or "").strip()
    model = (os.environ.get("HQ_MODEL") or "").strip()
    if not (base and key and model):
        return {"provider": "openai-compat", "available": False,
                "why": "butuh HQ_BASE_URL + HQ_API_KEY + HQ_MODEL"}
    body = {"model": model, "temperature": 0.0, "messages": [
        {"role": "system", "content": STATE_SYSTEM},
        {"role": "user", "content": state}]}
    st, d, lat, err = _post(f"{base}/chat/completions", body, {
        "Authorization": f"Bearer {key}", "Content-Type": "application/json",
        "Accept": "application/json", "User-Agent": "lencana-judge/1.0"})
    if st != 200 or not isinstance(d, dict):
        return {"provider": "openai-compat", "available": True, "ok": False, "why": err or f"HTTP {st}",
                "latency_s": lat}
    try:
        content = d["choices"][0]["message"]["content"]
        start = content.find("{")
        end = content.rfind("}")
        obj = json.loads(content[start:end + 1])
    except Exception as e:  # noqa: BLE001
        # jawaban tidak terparse BUKAN izin untuk lanjut: tetap dicatat dan kandidat tidak naik.
        return {"provider": "openai-compat", "available": True, "ok": False,
                "why": f"jawaban bukan JSON yang sah ({type(e).__name__})", "latency_s": lat}
    usage = d.get("usage") or {}
    return {
        "provider": "openai-compat", "available": True, "ok": True, "model": model,
        "latency_s": lat,
        "veto_prob": None,
        "veto": bool(obj.get("veto")),
        "dominant_risk": obj.get("dominant_risk"),
        "confidence": obj.get("confidence"),
        "probabilities": None,
        "cost_usd": None,   # harga beda per provider: jangan mengarang angka
        "tokens_in": int(usage.get("prompt_tokens") or 0),
        "tokens_out": int(usage.get("completion_tokens") or 0),
    }


def judge(mode, state, risk_label="this candidate"):
    """Kembalikan (hasil, catatan). mode: none | jev | openai | auto."""
    if mode in ("none", "", None):
        return None, {"judge": "none", "note": "hanya gerbang deterministik"}
    chain = {"jev": [judge_jev], "openai": [judge_openai_compat],
             "auto": [judge_jev, judge_openai_compat]}.get(mode, [judge_jev, judge_openai_compat])
    notes = []
    for fn in chain:
        out = fn(state, risk_label)
        if not out.get("available"):
            notes.append({"provider": out["provider"], "status": "tak tersedia",
                          "why": out.get("why", "")})
            continue
        if not out.get("ok"):
            notes.append({"provider": out["provider"], "status": "gagal",
                          "why": out.get("why", "")})
            return None, {"judge": out["provider"], "note": "judge gagal -> kandidat tidak naik kelas",
                          "attempts": notes}
        out["veto"] = bool(out.get("veto")) or (
            isinstance(out.get("veto_prob"), (int, float)) and out["veto_prob"] >= 0.5)
        return out, {"judge": out["provider"], "note": "ok", "attempts": notes}
    return None, {"judge": "none", "note": "tak ada provider yang tersedia " + json.dumps(notes)}
