"""Agent analis rumah Fabius (P142, F-D102): tiap bar, tiap agent (identitas ERC-8004 sendiri) memilih SATU dari bot berjam maju, lalu pilihan itu
dikomit ke `SelectionAnchor` dari dompet agent SEBELUM bar ditutup. Agent tidak pernah membuat trade: ia memilih bot yang aturannya terkunci.

Masukan (deterministik, di-hash `masukan_sha256`): fitur rezim pasar dari bar publik (tren/breadth/volatilitas/funding) + per bot: aturan, status,
vonis gerbang v1, teaser confidence maju (P137), eksposur tick terakhir dan perubahannya. Prompt di-hash (`prompt_sha256`), jawaban mentah di-hash.
Alasan lengkap = JSON (`reasonHash` = sha256 kanonisnya, on-chain); JSON-nya diterbitkan gerbang (`/analysts`, nama lama `/analis`) dan dicetak di log.

Penyedia: qwencloud (OpenAI-compatible, `reasoning_effort`) untuk DeepSeek V4.1 Flash (slot `glm`, sebelumnya GLM 5.3) + Qwen 3.8 Flash; Anthropic (Claude Sonnet 5.5) disiapkan tetapi NONAKTIF
sampai `ANTHROPIC_API_KEY` ada (builder 5 Okt: belum ada dana kredit API) - jalur Anthropic BELUM PERNAH diuji dengan kunci sungguhan.

    python -X utf8 tools/analis.py kunci                 # buat kunci dompet agent ke .analis.env (di-gitignore), cetak ALAMAT saja
    python -X utf8 tools/analis.py daftar [--send]       # isi tBNB dari committer + register(string) di IdentityRegistry per agent
    python -X utf8 tools/analis.py masukan               # cetak masukan hari ini (tanpa kunci, tanpa LLM)
    python -X utf8 tools/analis.py pilih [--send]        # panggil model + (dengan --send) komit pilihan untuk penutupan bar berikutnya
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from typing import Callable, Dict, List, Optional

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from engine import book as bookmod, chain, confidence, data as datamod, ledger, pemilih, rincian   # noqa: E402
from engine.spec import SPECS                                                             # noqa: E402
import signal_commit as sc                                                                # noqa: E402

ANALIS_ENV = os.path.join(ROOT, ".analis.env")
CARD_DIR = os.path.join(ROOT, "docs", "analis")
CARD_URL = "https://raw.githubusercontent.com/Shenhan01-sys/Fabius/master/docs/analis/{slug}.json"
PROVIDERS = {
    "qwencloud": {"base": "https://token-plan.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1", "key_var": "QWENCLOUD_API_KEY"},
    "anthropic": {"base": "https://api.anthropic.com/v1", "key_var": "ANTHROPIC_API_KEY"},
}
# Slot `glm` (agent 2558): builder 5 Okt mengganti model ke deepseek-v4.1-flash effort high (diuji di qwencloud: HTTP 200). Identitas ERC-8004, dompet, dan
# kartu (URI on-chain .../glm.json) TETAP; model tiap pilihan ikut di JSON alasan yang di-hash, riwayat model di kartu. GLM 5.3 dulu: effort hanya
# low|high|max ("medium" = HTTP 400).
AGENTS = [   # urutan tetap; `slug` = nama berkas kartu + variabel kunci
    {"slug": "glm", "name": "Fabius Analyst · DeepSeek V4.1 Flash", "provider": "qwencloud", "model": "deepseek-v4.1-flash", "effort": "high",
     "key_var": "ANALIS_GLM_PRIVATE_KEY", "riwayat": [{"model": "glm-5.3", "effort": "low", "sampai_bar_close": 1791244800}]},
    {"slug": "qwen", "name": "Fabius Analyst · Qwen 3.8 Flash", "provider": "qwencloud", "model": "qwen3.8-flash", "effort": "xhigh",
     "key_var": "ANALIS_QWEN_PRIVATE_KEY"},
    {"slug": "claude", "name": "Fabius Analyst · Claude Sonnet 5.5", "provider": "anthropic", "model": "claude-sonnet-5-5", "effort": "xhigh",
     "key_var": "ANALIS_CLAUDE_PRIVATE_KEY", "nonaktif": "builder 5 Okt: belum ada dana kredit API Anthropic"},
]
SIG_PICK = "pick(uint256,uint64,bytes32,uint8,bytes32)"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
FUND_WEI = 10 ** 16                 # 0,01 tBNB per agent (±20 pilihan + pendaftaran)
DAY_S = 86_400


def secret(var: str) -> Optional[str]:
    return os.environ.get(var) or sc.read_env_file(ANALIS_ENV, var)


def canon(o) -> bytes:
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(o) -> str:
    return "0x" + hashlib.sha256(o if isinstance(o, bytes) else canon(o)).hexdigest()


def next_close(now_s: int) -> int:
    return (now_s // DAY_S + 1) * DAY_S


# ---------------------------------------------------------------- masukan (murni dari repo; diuji)

def _ret(c, i, n):
    return c[i] / c[i - n] - 1 if i - n >= 0 and c[i - n] else None


def regime(workdir: str) -> dict:
    uni = list(SPECS["B1-TREND"].universe)
    md = datamod.load_csv_dir(os.path.join(workdir, "ledger", "bars"), uni)
    out, above60, above20 = {}, 0, 0
    for a in uni:
        s = md.perp.get(a)
        if not s or len(s.c) < 61:
            continue
        i = len(s.c) - 1
        above60 += s.c[i] > s.c[i - 60]
        above20 += s.c[i] > s.c[i - 20]
    btc = md.perp["BTCUSDT"]
    i = len(btc.c) - 1
    rets = [btc.c[k] / btc.c[k - 1] - 1 for k in range(i - 29, i + 1)]
    mu = sum(rets) / len(rets)
    vol = math.sqrt(sum((r - mu) ** 2 for r in rets) / (len(rets) - 1)) * math.sqrt(365)
    fund = []
    for a, f in (md.funding or {}).items():
        last = sorted(f.items())[-7:]
        if last:
            fund.append(sum(v for _, v in last) / len(last) * 365)
    out.update(bar_terakhir=rincian._date(btc.t[i]), btc_ret_30h=_ret(btc.c, i, 30), btc_ret_60h=_ret(btc.c, i, 60), btc_vol_30h_tahunan=vol,
               breadth_di_atas_60h=above60 / len(uni), breadth_di_atas_20h=above20 / len(uni),
               funding_rata_7h_tahunan=(sum(fund) / len(fund)) if fund else None)
    return {k: (round(v, 6) if isinstance(v, float) else v) for k, v in out.items()}


def bots_view(workdir: str) -> Dict[str, dict]:
    pdir = os.path.join(workdir, "ledger", "paper")
    led = {b: ledger.load(os.path.join(pdir, f"{b}.jsonl")) for b in bookmod.FORWARD_BOTS if os.path.exists(os.path.join(pdir, f"{b}.jsonl"))}
    tz = confidence.teasers(led, bookmod.STATUS, bookmod.GATE_V1)
    out = {}
    for b, recs in sorted(led.items()):
        ticks = [r for r in recs if r.get("type") == "tick"]
        last = ticks[-1] if ticks else {}
        prev = ticks[-2].get("targets", {}) if len(ticks) > 1 else None
        tg = last.get("targets", {})
        out[b] = {"aturan": SPECS[b].metode, "param": SPECS[b].param, "status": bookmod.STATUS.get(b), "gerbang_v1": bookmod.GATE_V1.get(b),
                  "confidence_maju": tz[b]["confidence_pct"], "label_confidence": tz[b]["label"], "fd16": tz[b]["fd16"], "kematangan": tz[b]["kematangan"],
                  "tick_terakhir": last.get("asof_date"), "posisi": sum(1 for w in tg.values() if abs(float(w)) > 1e-12),
                  "bobot_long": round(sum(float(w) for w in tg.values() if float(w) > 0), 6), "bobot_short": round(sum(-float(w) for w in tg.values() if float(w) < 0), 6),
                  "perubahan": rincian.perubahan(tg, prev)}
    return out


def masukan(workdir: str, bar_close: int) -> dict:
    return {"v": 1, "untuk_penutupan_bar": dt.datetime.fromtimestamp(bar_close, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "rezim_pasar": regime(workdir), "bot": bots_view(workdir)}


SYSTEM = ("You are an analyst agent for Fabius, a verifiable crypto signal operator. Each day you pick exactly ONE bot whose locked rule the operator "
          "follows for the next daily bar (from this bar's close to the next close). You never invent trades: every bot is a fixed, locked rule. Your pick "
          "is committed on-chain before the bar closes and scored later against the public ledger, so be calibrated, not promotional. Paper only, testnet. "
          "Answer with ONE JSON object and nothing else.")


def prompt(m: dict) -> str:
    return ("Data (JSON; status INTI = identity bot chosen by the builder, SEMENTARA = provisional; gerbang_v1 = locked backtest gate verdict, TOLAK = failed; "
            "confidence_maju = 1 - p of the locked forward test, null = not measured yet; posisi/bobot = the bot's latest targets; "
            "rezim_pasar = market regime from public daily bars):\n"
            + json.dumps(m, ensure_ascii=False, sort_keys=True)
            + "\n\nChoose the bot most likely to have the best net paper return over the NEXT daily bar given the regime. Write 'alasan' and 'risiko' "
            "in English. Reply with exactly this JSON: "
            '{"bot": "<one of ' + ", ".join(sorted(m["bot"])) + '>", "keyakinan": <integer 0-100>, "alasan": "<max 600 chars>", "risiko": "<max 300 chars>"}')


def parse(text: str, allowed: List[str]) -> dict:
    """JSON pertama di teks -> pilihan tervalidasi. Galat = ValueError (agent tidak memilih bar itu, tidak dikarang)."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError("tidak ada JSON di jawaban")
    o = json.loads(m.group(0))
    bot = str(o.get("bot", "")).strip().upper()
    if bot not in allowed:
        raise ValueError(f"bot tidak dikenal: {bot!r}")
    k = int(o.get("keyakinan"))
    if not 0 <= k <= 100:
        raise ValueError(f"keyakinan di luar 0..100: {k}")
    return {"bot": bot, "keyakinan": k, "alasan": str(o.get("alasan", ""))[:600], "risiko": str(o.get("risiko", ""))[:300]}


# ---------------------------------------------------------------- model

def _post(url: str, headers: dict, body: dict, timeout: int) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def call_model(agent: dict, system: str, user: str, post: Callable = _post, timeout: int = 600) -> str:
    p = PROVIDERS[agent["provider"]]
    key = os.environ.get(p["key_var"]) or sc.read_env_file(ANALIS_ENV, p["key_var"])
    if not key:
        raise RuntimeError(f"{p['key_var']} tidak ada")
    if agent["provider"] == "anthropic":                          # BELUM diuji dengan kunci sungguhan (lihat docstring)
        r = post(f"{p['base']}/messages", {"x-api-key": key, "anthropic-version": "2023-06-01"},
                 {"model": agent["model"], "max_tokens": 4000, "system": system, "messages": [{"role": "user", "content": user}]}, timeout)
        return "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text")
    r = post(f"{p['base']}/chat/completions", {"Authorization": f"Bearer {key}"},
             {"model": agent["model"], "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
              "reasoning_effort": agent["effort"], "temperature": 0.2}, timeout)
    return (r.get("choices") or [{}])[0].get("message", {}).get("content") or ""


def active_agents(cfg: dict) -> List[dict]:
    """Agent yang terdaftar (agent_id ada) DAN kunci penyedia + dompetnya tersedia."""
    out = []
    for a in AGENTS:
        if a.get("nonaktif"):
            continue
        reg = (cfg.get("agents") or {}).get(a["slug"]) or {}
        if not reg.get("agent_id"):
            continue
        if not (os.environ.get(PROVIDERS[a["provider"]]["key_var"]) or sc.read_env_file(ANALIS_ENV, PROVIDERS[a["provider"]]["key_var"])):
            continue
        if not secret(a["key_var"]):
            continue
        out.append({**a, **reg})
    return out


# ---------------------------------------------------------------- satu putaran pilihan (dipakai CLI dan thread gerbang)

def run_round(workdir: str, cfg: dict, ev, now_s: int, send: bool, log: Callable[[str], None] = print, post: Callable = _post,
              out_dir: Optional[str] = None) -> List[dict]:
    """Untuk penutupan bar berikutnya: tiap agent aktif yang belum memilih -> model -> pilihan -> komit. -> catatan per agent."""
    from evm import address_of, calldata, receipt_ok
    sel = cfg["selection"]
    close = next_close(now_s)
    m = masukan(workdir, close)
    allowed = sorted(m["bot"])
    user = prompt(m)
    res = []
    for ag in active_agents(cfg):
        got = ev.call_decode(sel, "getPick(uint256,uint64)", ("uint256", "uint64"), (int(ag["agent_id"]), close), ("(bytes32,uint8,bytes32,uint64)",))[0]
        if int(got[3]):
            res.append({"agent": ag["slug"], "status": "sudah"})
            continue
        try:
            raw = call_model(ag, SYSTEM, user, post)
            choice = parse(raw, allowed)
        except Exception as e:  # noqa: BLE001 - satu agent gagal tidak menghentikan yang lain; bar itu tanpa pilihannya (dicatat)
            log(f"analis {ag['slug']}: tidak memilih ({type(e).__name__}: {str(e)[:160]})")
            res.append({"agent": ag["slug"], "status": "gagal", "galat": f"{type(e).__name__}: {str(e)[:160]}"})
            continue
        reason = {"v": 1, "agent": ag["slug"], "agent_id": int(ag["agent_id"]), "nama": ag["name"], "penyedia": ag["provider"], "model": ag["model"],
                  "effort": ag["effort"], "bar_close": close, "masukan_sha256": sha(m), "prompt_sha256": sha(SYSTEM.encode() + b"\n" + user.encode()),
                  "jawaban_mentah_sha256": sha(raw.encode()), "pilihan": choice, "dibuat_utc": dt.datetime.fromtimestamp(now_s, dt.timezone.utc).isoformat()}
        rh = sha(reason)
        rec = {"agent": ag["slug"], "status": "rencana", "bot": choice["bot"], "keyakinan": choice["keyakinan"], "reasonHash": rh, "alasan": reason}
        if send:
            pk = secret(ag["key_var"])
            if address_of(pk).lower() != ag["wallet"].lower():
                rec.update(status="gagal", galat="kunci dompet bukan dompet terdaftar")
            else:
                r = ev.send(pk, sel, calldata(SIG_PICK, ("uint256", "uint64", "bytes32", "uint8", "bytes32"),
                                                (int(ag["agent_id"]), close, chain.ascii32(choice["bot"]), choice["keyakinan"], bytes.fromhex(rh[2:]))))
                rec.update(status="dikomit" if receipt_ok(r) else "gagal", tx=r.get("transactionHash"))
        log(f"PILIHAN {ag['slug']} -> {choice['bot']} ({choice['keyakinan']}) bar_close {close} {rec['status']} {rec.get('tx', '')} reasonHash {rh[:18]}… "
            + json.dumps(reason, ensure_ascii=False, sort_keys=True))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            with open(os.path.join(out_dir, f"{close}.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
        res.append(rec)
    return res


# ---------------------------------------------------------------- P143: pilihan on-chain -> skor -> reputasi -> bot aktif

REP_TAG = "fabius-pick-v1"
SIG_FEEDBACK = "giveFeedback(uint256,int128,uint8,string,string,string,string,bytes32)"


def onchain_picks(ev, sel: str, agents: Dict[str, dict]) -> List[dict]:
    """Semua pilihan agent terdaftar, DIBACA DARI SelectionAnchor (sumber kebenaran; arsip berkas hanya untuk alasan teks)."""
    out = []
    for slug, a in sorted(agents.items()):
        aid = int(a["agent_id"])
        n = int(ev.call_decode(sel, "barCount(uint256)", ("uint256",), (aid,), ("uint256",))[0])
        for i in range(n):
            c = int(ev.call_decode(sel, "barAt(uint256,uint256)", ("uint256", "uint256"), (aid, i), ("uint64",))[0])
            p = ev.call_decode(sel, "getPick(uint256,uint64)", ("uint256", "uint64"), (aid, c), ("(bytes32,uint8,bytes32,uint64)",))[0]
            out.append({"agent": slug, "agent_id": aid, "bar_close": c, "bot": bytes(p[0]).rstrip(b"\0").decode(), "keyakinan": int(p[1]),
                        "reasonHash": "0x" + bytes(p[2]).hex(), "committedAt": int(p[3])})
    return sorted(out, key=lambda r: (r["bar_close"], r["agent_id"]))


# ---------------------------------------------------------------- agent LUAR (P151, F-D107)
# SelectionAnchor sudah terbuka: identitas ERC-8004 mana pun (pemilik / dompet agent) boleh `pick`. Fabius menemukan mereka dari event `Picked`,
# membaca kartu ERC-8004 mereka (`tokenURI`), dan mengambil alasan dari URL di kartu HANYA sesudah bar tutup, disimpan HANYA bila sha256 kanonisnya
# = reasonHash on-chain DAN isinya menyebut agent, bar, dan bot yang sama. Agent luar dinilai + tampil di papan; BELUM ikut menentukan bot aktif
# dan belum diberi feedback reputasi (F-D107: klausul mayoritas bisa dibanjiri identitas Sybil; penerimaan butuh aturan terkunci baru).
PICKED_TOPIC = "0x885257223219a0b7ef22e0f10be61383789c95e280729027d2b944f2240e122e"   # Picked(uint256,uint64,bytes32,uint8,bytes32,address), dari log chain 97
CARD_MAX = 64 * 1024
LUAR_MAX = 50                      # agent luar yang dibaca per putaran (biaya RPC terbatas; urutan = id terkecil dulu)
SKEMA_ALASAN = {"agent_id": "int (agent ERC-8004 kamu)", "bar_close": "int (unix detik, penutupan bar yang dipilih)", "nama": "str (opsional)",
                "model": "str (opsional)", "pilihan": {"bot": "salah satu bot maju", "keyakinan": "int 0-100", "alasan": "str", "risiko": "str (opsional)"}}


def ambil(url: str, limit: int = CARD_MAX) -> bytes:
    """https:// atau data: (JSON base64 / percent-encoded), paling banyak `limit` byte; selain itu galat."""
    if url.startswith("data:"):
        head, _, data = url.partition(",")
        raw = base64.b64decode(data) if head.endswith(";base64") else urllib.parse.unquote_to_bytes(data)
    elif url.startswith("https://"):
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "fabius-analis/1.0"}), timeout=10) as r:
            raw = r.read(limit + 1)
    else:
        raise ValueError("hanya https:// atau data:")
    if len(raw) > limit:
        raise ValueError(f"lebih dari {limit} byte")
    return raw


def temukan_agent(ev, sel: str, from_block: int, state: dict, step: int = 40_000) -> List[int]:
    """agentId yang pernah memilih di SelectionAnchor (event `Picked`), dipindai bertahap dari `state["blok"]` (disimpan pemanggil)."""
    latest = int(ev.rpc("eth_blockNumber", []), 16)
    b, seen = int(state.get("blok") or from_block), set(state.get("agen") or [])
    while b <= latest:
        e = min(b + step - 1, latest)
        try:
            logs = ev.rpc("eth_getLogs", [{"address": sel, "fromBlock": hex(b), "toBlock": hex(e), "topics": [PICKED_TOPIC]}])
        except Exception:  # noqa: BLE001 - rentang terlalu lebar untuk RPC publik -> perkecil
            if step <= 500:
                raise
            step //= 2
            continue
        seen.update(int(lg["topics"][1], 16) for lg in logs)
        b = e + 1
    state["blok"], state["agen"] = b, sorted(seen)
    return state["agen"]


def kartu_luar(ev, identity: str, agent_id: int, fetch: Callable[[str], bytes] = ambil) -> dict:
    """Kartu ERC-8004 agent luar -> {agent_id, nama, alasan_url (berisi {bar_close}) | None, uri, galat}. Kartu rusak = agent tetap tampil tanpa alasan."""
    out = {"agent_id": agent_id, "nama": f"agent {agent_id}", "alasan_url": None, "uri": None, "galat": None}
    try:
        uri = ev.call_decode(identity, "tokenURI(uint256)", ("uint256",), (agent_id,), ("string",))[0]
        out["uri"] = uri[:300]
        card = json.loads(fetch(uri))
        if not isinstance(card, dict):
            raise ValueError("kartu bukan objek JSON")
        out["nama"] = str(card.get("name") or out["nama"])[:80]
        tpl = (card.get("fabius") or {}).get("reasons") if isinstance(card.get("fabius"), dict) else None
        if isinstance(tpl, str) and tpl.startswith("https://") and "{bar_close}" in tpl:
            out["alasan_url"] = tpl
        else:
            out["galat"] = "kartu tanpa fabius.reasons (https, berisi {bar_close})"
    except Exception as e:  # noqa: BLE001
        out["galat"] = f"{type(e).__name__}: {str(e)[:120]}"
    return out


def alasan_luar(picks: List[dict], kartu: Dict[int, dict], out_dir: str, now_s: int, fetch: Callable[[str], bytes] = ambil,
                log: Callable[[str], None] = print, coba: Optional[Dict[str, float]] = None, jeda_s: int = 3600) -> int:
    """Alasan agent luar untuk bar yang SUDAH tutup -> `<out_dir>/<bar_close>.jsonl`, hanya bila hash + skema cocok. Gagal dicoba lagi tiap `jeda_s`."""
    coba = {} if coba is None else coba
    have = {(r["agent"], int(r["alasan"]["bar_close"])) for r in records([out_dir])}
    n = 0
    for p in picks:
        key = f"{p['agent']}:{p['bar_close']}"
        tpl = (kartu.get(p["agent_id"]) or {}).get("alasan_url")
        if p["bar_close"] > now_s or (p["agent"], p["bar_close"]) in have or not tpl or now_s - coba.get(key, -jeda_s) < jeda_s:
            continue
        coba[key] = now_s
        try:
            a = json.loads(fetch(tpl.replace("{bar_close}", str(p["bar_close"]))))
            pl = a.get("pilihan") if isinstance(a, dict) else None
            if sha(a) != p["reasonHash"]:
                raise ValueError("sha256 alasan != reasonHash on-chain")
            if not isinstance(pl, dict) or int(a.get("agent_id", -1)) != p["agent_id"] or int(a.get("bar_close", -1)) != p["bar_close"] or pl.get("bot") != p["bot"]:
                raise ValueError("isi tidak menyebut agent/bar/bot yang sama dengan pilihan on-chain")
        except Exception as e:  # noqa: BLE001
            log(f"alasan luar {key} DITOLAK: {type(e).__name__}: {str(e)[:120]}")
            continue
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, f"{p['bar_close']}.jsonl"), "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({"agent": p["agent"], "bot": p["bot"], "keyakinan": p["keyakinan"], "reasonHash": p["reasonHash"], "status": "dikomit",
                                "luar": True, "alasan": a}, ensure_ascii=False, sort_keys=True) + "\n")
        n += 1
        log(f"alasan luar {key} {p['bot']} (hash + skema cocok)")
    return n


def net_of(bot: str, bar_ms: int, led: Dict[str, list], md_prov) -> tuple:
    """(status, net) return paper bot untuk bar `bar_ms`: settle FINAL di ledger bila ada; selain itu PROVISIONAL (funding estimasi, fungsi settle
    yang sama); selain itu menunggu (bar belum ditutup / data belum ada)."""
    recs = led.get(bot) or []
    for r in recs:
        if r.get("type") == "settle" and int(r["bar"]) == bar_ms:
            return "final", float(r["net"])
    if md_prov is None:
        return "menunggu", None
    try:
        rec = ledger.compute_settle(SPECS[bot], md_prov, recs, bar_ms)
    except Exception:  # noqa: BLE001 - rantai/data belum lengkap = belum terskor, tidak dikarang
        rec = None
    return ("provisional", float(rec["net"])) if rec else ("menunggu", None)


def skor(workdir: str, picks: List[dict], md_prov=None, identitas: Optional[str] = None) -> List[dict]:
    """Skor tiap pilihan: net bot pilihan pada bar yang DIBUKA di `bar_close` (posisi tick bar sebelumnya), selisih vs bot identitas bar yang sama."""
    pdir = os.path.join(workdir, "ledger", "paper")
    led = {b: ledger.load(os.path.join(pdir, f"{b}.jsonl")) for b in bookmod.FORWARD_BOTS if os.path.exists(os.path.join(pdir, f"{b}.jsonl"))}
    ident = identitas or bookmod.IDENTITY_BOT_ID
    out = []
    for pk in picks:
        bar_ms = pk["bar_close"] * 1000
        st, net = net_of(pk["bot"], bar_ms, led, md_prov)
        sb, nb = net_of(ident, bar_ms, led, md_prov)
        status = "menunggu" if net is None or nb is None else ("final" if st == sb == "final" else "provisional")
        out.append({**pk, "status_skor": status, "net": net, "net_identitas": nb, "selisih": (net - nb) if status != "menunggu" else None,
                    "bar_hasil": rincian._date(bar_ms)})
    return out


def papan(scored: List[dict], nama_luar: Optional[Dict[str, str]] = None) -> List[dict]:
    nama = {**{a["slug"]: a["name"] for a in AGENTS}, **(nama_luar or {})}
    rows: Dict[int, dict] = {}
    for r in scored:
        a = rows.setdefault(r["agent_id"], {"agent": r["agent"], "nama": nama.get(r["agent"], r["agent"]), "agent_id": r["agent_id"], "pilihan": 0,
                                             "luar": bool(r.get("luar")), "terskor": 0, "final": 0,
                                             "jumlah_net_bps": 0.0, "jumlah_selisih_bps": 0.0})
        a["pilihan"] += 1
        if r["status_skor"] != "menunggu":
            a["terskor"] += 1
            a["final"] += r["status_skor"] == "final"
            a["jumlah_net_bps"] += r["net"] * 1e4
            a["jumlah_selisih_bps"] += r["selisih"] * 1e4
    for a in rows.values():
        a["rata_selisih_bps"] = a["jumlah_selisih_bps"] / a["terskor"] if a["terskor"] else None
        a["jumlah_net_bps"], a["jumlah_selisih_bps"] = round(a["jumlah_net_bps"], 4), round(a["jumlah_selisih_bps"], 4)
    return sorted(rows.values(), key=lambda a: (-a["jumlah_selisih_bps"], a["agent_id"]))


def bot_aktif(picks: List[dict], scored: List[dict], bar_close: int, identitas: Optional[str] = None) -> dict:
    """Aturan TERKUNCI `engine/pemilih.py` untuk penutupan `bar_close` (skor hanya dari bar sebelum `bar_close`)."""
    ident = identitas or bookmod.IDENTITY_BOT_ID
    pil = {r["agent_id"]: r["bot"] for r in picks if r["bar_close"] == bar_close}
    sk: Dict[int, list] = {}
    for r in scored:
        if r["status_skor"] != "menunggu" and r["bar_close"] < bar_close:
            sk.setdefault(r["agent_id"], []).append((r["bar_close"], r["selisih"]))
    bot, why = pemilih.aktif(pil, sk, ident, bar_close)
    lead = pemilih.pemimpin(sk, bar_close)
    if not pil:
        en = "no analyst picks for this bar -> identity bot"
    elif lead is not None and lead[0] in pil:
        en = f"leader agent {lead[0]} (best excess vs identity bot over its last scored picks) picked {bot}"
    else:
        votes = {}
        for b in pil.values():
            votes[b] = votes.get(b, 0) + 1
        en = f"majority of analyst picks {dict(sorted(votes.items()))}" + (" (tie -> identity bot)" if list(votes.values()).count(max(votes.values())) > 1 else "")
    return {"bar_close": bar_close, "bot": bot, "alasan": why, "alasan_en": en, "pilihan": pil, "kunci": pemilih.status()["state"]}


def reputasi(ev, pk: str, rep: str, scored: List[dict], state_path: str, base_url: str, log: Callable[[str], None] = print, limit: int = 6) -> int:
    """Feedback ERC-8004 dari gerbang (klien) per pilihan terskor: value = selisih vs bot identitas dalam bps (2 desimal), tag1 = fabius-pick-v1,
    tag2 = provisional | final. Satu kali per (agent, bar, status); final datang sebagai feedback baru sesudah funding bulanan terbit."""
    from evm import calldata, receipt_ok
    done = {}
    if os.path.exists(state_path):
        with open(state_path, encoding="utf-8") as f:
            done = json.load(f)
    n = 0
    for r in scored:
        if r["status_skor"] == "menunggu":
            continue
        k = f"{r['agent_id']}:{r['bar_close']}:{r['status_skor']}"
        if k in done or n >= limit:
            continue
        val = int(round(r["selisih"] * 1e4 * 100))
        rec = {k2: r[k2] for k2 in ("agent", "agent_id", "bar_close", "bot", "net", "net_identitas", "selisih", "status_skor", "reasonHash")}
        data = calldata(SIG_FEEDBACK, ("uint256", "int128", "uint8", "string", "string", "string", "string", "bytes32"),
                        (r["agent_id"], val, 2, REP_TAG, r["status_skor"], f"{base_url}/analysts", f"{base_url}/analysts/{r['bar_close']}", bytes.fromhex(sha(rec)[2:])))
        tx = ev.send(pk, rep, data)
        if receipt_ok(tx):
            done[k] = tx["transactionHash"]
            n += 1
            log(f"reputasi ERC-8004: agent {r['agent_id']} bar {r['bar_hasil']} {r['bot']} selisih {r['selisih'] * 1e4:+.2f} bps ({r['status_skor']}) tx {tx['transactionHash']}")
    if n:
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(done, f, sort_keys=True)
    return n


# ---------------------------------------------------------------- CLI

def records(dirs: List[str], close: Optional[int] = None) -> List[dict]:
    """Catatan pilihan dari beberapa direktori (volume gerbang + arsip repo `ledger/analis/`); satu per (agent, bar_close), yang dikomit menang."""
    best: Dict[tuple, dict] = {}
    for d in dirs:
        if not d or not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not name.endswith(".jsonl") or (close is not None and name != f"{close}.jsonl"):
                continue
            for ln in open(os.path.join(d, name), encoding="utf-8"):
                if not ln.strip():
                    continue
                r = json.loads(ln)
                k = (r.get("agent"), int((r.get("alasan") or {}).get("bar_close") or name[:-6]))
                if k not in best or (r.get("status") == "dikomit" and best[k].get("status") != "dikomit"):
                    best[k] = r
    return [best[k] for k in sorted(best, key=lambda k: (k[1], str(k[0])))]


def load_cfg(path: str = sc.DEPLOYMENTS) -> dict:
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    return {"selection": d.get("contracts", {}).get("SelectionAnchor"), "identity": d["erc8004"]["identity"], "agents": (d.get("analis") or {}).get("agents", {})}


def _evm():
    import evm as evmmod
    ev = evmmod.Evm(sc.rpc_urls(), sc.CHAIN_ID)
    ev.chain_check()
    return ev


def cmd_kunci(a) -> int:
    from eth_account import Account
    have = sc.read_env_file(ANALIS_ENV, "ANALIS_GLM_PRIVATE_KEY") if os.path.exists(ANALIS_ENV) else None
    if have:
        for ag in AGENTS:
            k = secret(ag["key_var"])
            print(f"{ag['slug']}: {Account.from_key(k).address if k else '-'}")
        print(f"{ANALIS_ENV} sudah ada - tidak ditimpa")
        return 0
    lines = ["# kunci dompet agent analis rumah Fabius (P142). JANGAN di-commit/ditempel. Railway: variabel dengan nama yang sama"]
    for ag in AGENTS:
        acct = Account.create()
        k = acct.key.hex()
        lines.append(f"{ag['key_var']}={k if k.startswith('0x') else '0x' + k}")
        print(f"{ag['slug']}: {acct.address}")
    with open(ANALIS_ENV, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("kunci dibuat di .analis.env (tidak dicetak)")
    return 0


def card(ag: dict, sel: str) -> dict:
    return {"protocol": "erc-8004/1", "name": ag["name"], "type": "analyst",
            "description": (f"House analyst agent of Fabius ({ag['model']}, reasoning effort {ag['effort']}, via {ag['provider']}). Each day it picks ONE "
                            "locked Fabius bot for the next daily bar; the pick (bot, confidence, sha256 of the full reasoning) is committed to "
                            "SelectionAnchor before the bar closes and scored later from the public ledger. It never invents trades."),
            "model": {"provider": ag["provider"], "id": ag["model"], "effort": ag["effort"]},
            **({"model_history": [{"id": h["model"], "effort": h["effort"], "until_bar_close": h["sampai_bar_close"]} for h in ag["riwayat"]]}
               if ag.get("riwayat") else {}),
            "evidence": {"selection_anchor": sel, "chain_id": 97, "operator": "Fabius (agent 2494)",
                         "reasons": "https://fabius-x402-production.up.railway.app/analysts", "web": "https://fabius-one.vercel.app/analysts",
                         "code": "tools/analis.py"},
            "limits_stated_honestly": ["paper only, BNB testnet", "LLM output is not reproducible; what is verifiable is that the pick existed before the bar closed"]}


def cmd_daftar(a) -> int:
    from evm import address_of, calldata, receipt_ok
    cfg, ev = load_cfg(), _evm()
    with open(sc.DEPLOYMENTS, encoding="utf-8") as f:
        d = json.load(f)
    reg = d.setdefault("analis", {}).setdefault("agents", {})
    os.makedirs(CARD_DIR, exist_ok=True)
    cpk = sc.committer_key()
    for ag in AGENTS:
        if ag.get("nonaktif"):
            print(f"{ag['slug']}: nonaktif ({ag['nonaktif']}) - tidak didaftarkan")
            continue
        pk = secret(ag["key_var"])
        if not pk:
            print(f"{ag['slug']}: kunci tidak ada (jalankan kunci)")
            continue
        w = address_of(pk)
        with open(os.path.join(CARD_DIR, f"{ag['slug']}.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(card(ag, cfg["selection"]), f, indent=1, ensure_ascii=False)
            f.write("\n")
        if (reg.get(ag["slug"]) or {}).get("agent_id"):
            print(f"{ag['slug']}: sudah terdaftar agent {reg[ag['slug']]['agent_id']}")
            continue
        bal = ev.balance(w)
        print(f"{ag['slug']}: dompet {w} saldo {bal / 1e18:.6f} tBNB")
        if not a.send:
            print("  RENCANA: isi 0,01 tBNB dari committer + register(string) - tanpa --send tidak ada yang dikirim")
            continue
        if bal < FUND_WEI // 2:
            r = ev.send(cpk, w, b"", value=FUND_WEI, gas=21_000)
            print(f"  isi 0,01 tBNB tx {r['transactionHash']} {'OK' if receipt_ok(r) else 'GAGAL'}")
        uri = CARD_URL.format(slug=ag["slug"])
        r = ev.send(pk, cfg["identity"], calldata("register(string)", ("string",), (uri,)))
        if not receipt_ok(r):
            print(f"  register GAGAL tx {r.get('transactionHash')}")
            continue
        pad = "0x" + "0" * 24 + w.lower()[2:]
        tid = next(int(lg["topics"][3], 16) for lg in r["logs"] if lg["topics"][0].lower() == TRANSFER and lg["topics"][1] == "0x" + "0" * 64
                   and lg["topics"][2].lower() == pad)
        owner = ev.call_decode(cfg["identity"], "ownerOf(uint256)", ("uint256",), (tid,), ("address",))[0]
        if owner.lower() != w.lower():
            print(f"  BERHENTI: ownerOf({tid}) = {owner} bukan {w}")
            return 1
        reg[ag["slug"]] = {"agent_id": tid, "wallet": w, "tx": r["transactionHash"], "uri": uri, "model": ag["model"], "provider": ag["provider"],
                           "effort": ag["effort"]}
        print(f"  TERDAFTAR agent {tid} tx {r['transactionHash']} (ownerOf dibaca ulang = dompet)")
    with open(sc.DEPLOYMENTS, "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False))
    return 0


def cmd_masukan(a) -> int:
    print(json.dumps(masukan(ROOT, next_close(int(time.time()))), indent=1, ensure_ascii=False, sort_keys=True))
    return 0


GATE_URL = "https://fabius-x402-production.up.railway.app"


def arsip(picks: List[dict], fetch: Callable[[int], dict], out_dir: str, log: Callable[[str], None] = print, now_s: Optional[int] = None) -> int:
    """Alasan yang diterbitkan gerbang -> `ledger/analis/<bar_close>.jsonl`, HANYA bila sha256 alasannya = reasonHash on-chain (pilihan yang dikomit).
    Bar yang sudah punya catatan cocok untuk agent itu tidak ditulis ulang; bar yang BELUM tutup dilewati (alasannya masih tersegel di gerbang,
    F-D104) dan diarsip di putaran sesudah tutup. -> jumlah catatan baru."""
    now = int(time.time()) if now_s is None else now_s
    have = {(r["agent"], int(r["alasan"]["bar_close"])) for r in records([out_dir])}
    n = 0
    for close in sorted({p["bar_close"] for p in picks}):
        if close > now:
            continue
        want = {p["agent"]: p for p in picks if p["bar_close"] == close and (p["agent"], close) not in have}
        if not want:
            continue
        pub = {r["agent"]: r for r in (fetch(close).get("pilihan") or [])}
        for agent, p in sorted(want.items()):
            r = pub.get(agent)
            if r is None or sha(r.get("alasan")) != p["reasonHash"]:
                log(f"arsip: {agent} bar_close {close} DITOLAK - alasan terbit tidak ada / hash != reasonHash on-chain {p['reasonHash'][:18]}…")
                continue
            os.makedirs(out_dir, exist_ok=True)
            with open(os.path.join(out_dir, f"{close}.jsonl"), "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps({**r, "status": "dikomit"}, ensure_ascii=False, sort_keys=True) + "\n")
            n += 1
            log(f"arsip: {agent} bar_close {close} {p['bot']} (hash cocok on-chain)")
    return n


def cmd_arsip(a) -> int:
    cfg, ev = load_cfg(), _evm()
    picks = onchain_picks(ev, cfg["selection"], cfg["agents"])

    def fetch(close: int) -> dict:
        with urllib.request.urlopen(urllib.request.Request(f"{GATE_URL}/analysts/{close}", headers={"User-Agent": "fabius-arsip"}), timeout=30) as r:
            return json.loads(r.read().decode())
    n = arsip(picks, fetch, os.path.join(ROOT, "ledger", "analis"))
    print(f"RINGKAS arsip: {n} catatan baru dari {len(picks)} pilihan on-chain")
    return 0


def cmd_pilih(a) -> int:
    cfg, ev = load_cfg(), _evm()
    res = run_round(ROOT, cfg, ev, int(time.time()), a.send)
    print(f"RINGKAS: {[(r['agent'], r['status'], r.get('bot')) for r in res]}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Agent analis rumah Fabius (P142).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for n in ("daftar", "pilih"):
        sub.add_parser(n).add_argument("--send", action="store_true")
    sub.add_parser("kunci")
    sub.add_parser("arsip")
    sub.add_parser("masukan")
    a = ap.parse_args()
    return {"kunci": cmd_kunci, "daftar": cmd_daftar, "masukan": cmd_masukan, "pilih": cmd_pilih, "arsip": cmd_arsip}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
