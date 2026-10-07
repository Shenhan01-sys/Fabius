"""P166: penjawab BERBASIS ATURAN untuk agent luar uji (tanpa LLM, tanpa biaya). Masukan: JSON {"siklus", "deadline", "system", "prompt"} di stdin
(dari `tools/desk_agent_client.py run --answer-cmd`). Keluaran: satu jawaban v2 JSON di stdout, dengan fitur yang benar-benar ada di prompt.

Aturan (sengaja sederhana dan jujur - agent ini membuktikan JALUR agent luar, bukan keunggulan):
  - B6-BOUNCE bila ada aset dengan z_<N>h < -2 (aturan B6), instrumen = aset paling tertekan;
  - selain itu B1-TREND bila >= 3 aset punya tren_<N>h > 0, instrumen = tren tertinggi;
  - selain itu B5-CORE-RWA dengan BTCUSDT (+ PAXGUSDT bila ada), eksposur kecil.
Keyakinan dari kekuatan sinyal, dibatasi 30-70 (tidak pernah yakin penuh)."""
from __future__ import annotations

import json
import re
import sys

BOTS = ["B1-TREND", "B2-RS", "B3-CARRY", "B4-LISTING-FADE", "B5-CORE-RWA", "B6-BOUNCE"]


def urai(prompt: str) -> tuple:
    """-> ({aset: {fitur: nilai}}, [nama fitur yang boleh dikutip])."""
    aset = {}
    for ln in prompt.splitlines():
        m = re.match(r"^([A-Z0-9]{2,20}USDT): (.*)$", ln.strip())
        if not m:
            continue
        tok = m.group(2).split()
        f = {}
        for k, v in zip(tok[0::2], tok[1::2]):
            try:
                f[k] = float(v)
            except ValueError:
                continue
        aset[m.group(1)] = f
    m = re.search(r"Feature names you may cite: (.*?)\.\n", prompt + "\n")
    nama = [x.strip() for x in m.group(1).split(",")] if m else []
    return aset, nama


def putuskan(aset: dict, nama: list) -> dict:
    tren = next((n for n in nama if re.fullmatch(r"tren_\d+h", n)), None)
    z = next((n for n in nama if re.fullmatch(r"z_\d+h", n)), None)
    tekan = sorted((a for a, f in aset.items() if z and f.get(z) is not None and f[z] < -2), key=lambda a: aset[a][z])
    naik = sorted((a for a, f in aset.items() if tren and (f.get(tren) or 0) > 0), key=lambda a: -aset[a][tren])
    if tekan:
        bot, ins, fk = "B6-BOUNCE", tekan[:2], [z]
        kuat = min(1.0, (-aset[tekan[0]][z] - 2) / 2)
        alasan = f"{tekan[0]} {z} {aset[tekan[0]][z]:+.2f} is below -2, the B6 entry condition; a stretched drop is the setup."
    elif len(naik) >= 3:
        bot, ins, fk = "B1-TREND", naik[:3], [tren]
        kuat = min(1.0, len(naik) / max(1, len(aset)) * 2)
        alasan = f"{len(naik)} of {len(aset)} instruments have {tren} > 0; strongest {naik[0]} {aset[naik[0]][tren]:+.4f}. B1 is long only when it is > 0."
    else:
        bot, ins = "B5-CORE-RWA", [a for a in ("BTCUSDT", "PAXGUSDT") if a in aset] or sorted(aset)[:1]
        fk = [n for n in nama if n.startswith("vol")][:1] or nama[:1]
        kuat = 0.2
        alasan = f"Only {len(naik)} instruments trend up and none is stretched below -2; a small core allocation is the cautious default."
    k = int(round(30 + 40 * kuat))
    skor = {b: (-20 if b != bot else 40 + int(40 * kuat)) for b in BOTS}
    return {"ringkasan": f"{bot}: rule-based test agent (no model); {alasan}"[:400], "bot": bot, "skor_bot": skor, "keyakinan": k,
            "eksposur": 40 if bot != "B5-CORE-RWA" else 20,
            "instrumen": [{"aset": a, "keyakinan": k, "faktor": fk} for a in ins], "veto_aset": [], "faktor": fk, "alasan": alasan[:400]}


def main() -> int:
    req = json.loads(sys.stdin.read())
    aset, nama = urai(req.get("prompt") or "")
    print(json.dumps(putuskan(aset, nama)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
