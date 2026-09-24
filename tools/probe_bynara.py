"""Uji endpoint byNara: ini Jev (model keputusan bertipe) atau LLM chat biasa?

Kenapa penting: kalau ini LLM biasa, ia TIDAK menggantikan Jev. Kontrak yang kita andalkan dari
Jev adalah jawaban berupa ANGKA (`probabilities` per kriteria + `confidence`), bukan teks. LLM
yang disuruh JSON bisa mengarang `confidence`, dan angka itu tidak terkalibrasi - itu persis
"penilai yang tidak bisa menjatuhkan" yang sudah kita tolak. Jadi sebelum lapisan arah dibangun
di atasnya, bentuk jawabannya harus dilihat dulu.

Tiga uji, satu per satu, tanpa mengarang:
  1. POST /v1/systemone dengan model dari katalog (agnes-3-flash)  -> rute SystemOne ada/tidak
  2. POST /v1/systemone dengan model "jev"                          -> mereka proxy Typesafe?
  3. POST /v1/chat/completions + response_format json               -> kalau ini saja yang jalan,
     ia LLM: jawabannya teks yang kita paksa jadi JSON, BUKAN distribusi probabilitas.

API key dibaca dari environment, tidak pernah dicetak. Tidak ada order, tidak ada transaksi.
Pakai:  set JEV_API_KEY=<key> && python tools/probe_bynara.py
"""
import json
import os
import time
import urllib.error
import urllib.request

BASE = os.environ.get("JEV_BASE_URL") or "https://router.bynara.id"
KEY = os.environ.get("JEV_API_KEY") or ""
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
     "User-Agent": "lencana-bynara-probe/1.0"}

STATE = ("BSC pool CAND. Age_hours 96. Liquidity $178,000. Vol24 $1,900,000. "
         "Top10_holder_share 0.31. Lock 0.42. Bundler_rate 0.06. Holders 2100. "
         "Honeypot unknown. News themes REGULAT=45 SANCTION=17, tone -1.0.")

QUESTIONS = {
    "side": {"type": "choice", "instructions": "Direction of price over the next 24 hours",
             "criteria": {"long": "higher", "short": "lower", "flat": "no usable edge"}},
    "exit_risk": {"type": "noul",
                  "instructions": "The position cannot be closed near entry within 24 hours"},
    "urgency": {"type": "score", "instructions": "How soon it is worth acting",
                "criteria": ["keep watching", "one more data cycle", "act now"]},
}


def post(path, payload, timeout=45):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(), headers=H)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode()), round(time.time() - t0, 2)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300], round(time.time() - t0, 2)
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {str(e)[:200]}", round(time.time() - t0, 2)


def show_answers(d):
    ans = (d or {}).get("answers") or {}
    for k, v in ans.items():
        t = v.get("type")
        if t == "choice":
            print(f"     {k:11} choice={v.get('choice')!r} confidence={v.get('confidence')} "
                  f"probs={json.dumps(v.get('probabilities'))}")
        elif t == "score":
            print(f"     {k:11} score={v.get('score')} confidence={v.get('confidence')} "
                  f"legend={json.dumps(v.get('legend'))}")
        else:
            print(f"     {k:11} {t}={v.get('noul') if t == 'noul' else v}")


if not KEY:
    raise SystemExit("JEV_API_KEY kosong - jangan menyimpulkan apa pun tanpa memanggil")

print(f"base={BASE}  key={KEY[:8]}…({len(KEY)} char)")

MODELS = []
try:
    with urllib.request.urlopen(urllib.request.Request(BASE + "/v1/models", headers=H), timeout=25) as r:
        cats = json.loads(r.read().decode())
    MODELS = [m.get("id") for m in cats.get("data", [])]
    print(f"model di katalog ({len(MODELS)}): {', '.join(str(m) for m in MODELS[:12])}")
    ada_jev = [m for m in MODELS if m and ("jev" in str(m).lower() or "system" in str(m).lower())]
    print(f"  ada model jev/system-one di katalog? {'YA: ' + str(ada_jev) if ada_jev else 'TIDAK ADA'}")
except Exception as e:  # noqa: BLE001
    print(f"  /v1/models gagal: {type(e).__name__}: {str(e)[:120]}")

print("\n=== 1) /v1/systemone dengan model dari katalog ===")
first = next((m for m in MODELS if m), "agnes-3-flash")
st, d, dt = post("/v1/systemone", {"model": first, "state": STATE, "questions": QUESTIONS})
print(f"  model={first} -> HTTP {st} {dt}s")
if st == 200 and isinstance(d, dict):
    print(f"     echoed model={d.get('model')} usage={json.dumps(d.get('usage'))}")
    show_answers(d)
else:
    print(f"     {str(d)[:280]}")

print("\n=== 2) /v1/systemone dengan model 'jev' dan 'jev-latest' ===")
for m in ("jev", "jev-latest"):
    st, d, dt = post("/v1/systemone", {"model": m, "state": STATE, "questions": QUESTIONS})
    ok = isinstance(d, dict) and d.get("answers")
    print(f"  model={m:11} -> HTTP {st} {dt}s  answers? {'YA' if ok else 'TIDAK'}")
    if ok:
        show_answers(d)
    else:
        print(f"     {str(d)[:240]}")

print("\n=== 3) /v1/chat/completions (buktikan ia LLM kalau jalur SystemOne mati) ===")
prompt = ("Anda adalah gerbang risiko. Balas HANYA JSON: "
          '{"side":"long|short|flat","confidence":0..1,"reason":"<=90 char"}\n' + STATE)
st, d, dt = post("/v1/chat/completions", {"model": first, "temperature": 0, "max_tokens": 200,
                                          "messages": [{"role": "user", "content": prompt}]}, timeout=60)
print(f"  -> HTTP {st} {dt}s")
if st == 200 and isinstance(d, dict):
    try:
        msg = d["choices"][0]["message"]
        content = (msg.get("content") or "")[:400]
        print(f"     model={d.get('model')} usage={json.dumps(d.get('usage'))}")
        print(f"     content={content!r}")
        if msg.get("reasoning_content") or msg.get("reasoning"):
            print("     (field reasoning ADA -> model penalar; isinya tidak kita butuh)")
        print("     PENTING: `confidence` di sini adalah ANGKA YANG DIKARANG MODEL, "
              "bukan distribusi hasil pengukuran seperti `probabilities` milik System-One. "
              "Ia tidak boleh dipakai sebagai gerbang tanpa uji kalibrasi.")
    except Exception as e:  # noqa: BLE001
        print(f"     bentuk tak terduga: {e} -> {json.dumps(d)[:260]}")
else:
    print(f"     {str(d)[:280]}")
