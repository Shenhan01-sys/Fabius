"""Simulasi counterfactual P21: kalau setiap token DIPANTAU terus sejak kemunculan pertamanya,
berapa dari 5.110 kejadian tanpa harga masuk yang punya harga sebelum-belinya?

Aturan alat (entry = px dengan stempel <= t dan t - px <= 10 m). Counterfactual: stempel
kemunculan token (tx ATAU px) di masa lalu = kita sudah menarik harga pool itu pada siklus itu,
karena perekam pantau menarik setiap token yang pernah muncul dalam jendela W.
"""
import io
import os
import json
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(HERE)
sys.path.insert(0, HERE)
MIN = 60
W = int(sys.argv[1]) if len(sys.argv) > 1 else 120

seen, buys = {}, {}
for ln in io.open(R + r"\universe\wallet-flow.jsonl", encoding="utf-8", errors="replace"):
    ln = ln.strip()
    if not ln or ln.startswith("#"):
        continue
    d = json.loads(ln)
    tk = str(d.get("tk") or "").lower()
    t = int(d.get("t") or 0)
    if not tk or not t:
        continue
    if d.get("k") in ("tx", "txc", "px"):
        seen.setdefault(tk, []).append(t)
    if d.get("k") in ("tx", "txc") and d.get("b"):
        buys.setdefault(tk, []).append(t)

for tk in seen:
    seen[tk] = sorted(set(seen[tk]))

def bisect_le(xs, v):
    lo, hi = 0, len(xs)
    while lo < hi:
        mid = (lo + hi) // 2
        if xs[mid] <= v:
            lo = mid + 1
        else:
            hi = mid
    return lo - 1


tot = pulih = dup_ulang = 0
for tk, ts in buys.items():
    hist = seen.get(tk) or []
    for t in ts:
        tot += 1
        i = bisect_le(hist, t - 1)
        if i >= 0 and t - hist[i] <= W * MIN:
            pulih += 1
            if t - hist[i] >= 30 * MIN:
                dup_ulang += 1
print("jendela pantau %d m | kejadian beli %d | akan punya harga masuk bila dipantau: %d (%.1f %%)"
      % (W, tot, pulih, 100.0 * pulih / tot))
print("yang jaraknya >=30 menit dari kemunculan sebelumnya (batas bawah mutu): %d" % dup_ulang)


def bisect_le(xs, v):
    lo, hi = 0, len(xs)
    while lo < hi:
        mid = (lo + hi) // 2
        if xs[mid] <= v:
            lo = mid + 1
        else:
            hi = mid
    return lo - 1
