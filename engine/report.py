"""Ringkasan kinerja dari deret PnL harian (stdlib). Semua angka dicetak ulang oleh perintah yang memanggilnya."""
from __future__ import annotations

import datetime as dt
import math
from typing import Dict, Optional, Sequence, Tuple

from .series import max_drawdown, sharpe

Pnl = Sequence[Tuple[int, float]]


def _iso(t_ms: int) -> str:
    return dt.datetime.fromtimestamp(t_ms / 1000, dt.timezone.utc).strftime("%Y-%m-%d")


def date_ms(s: str) -> int:
    return int(dt.datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp() * 1000)


def summary(pnl: Pnl, since_ms: Optional[int] = None) -> Dict[str, object]:
    xs = [(t, v) for t, v in pnl if since_ms is None or t >= since_ms]
    vals = [v for _, v in xs]
    n = len(vals)
    if n < 2:
        return {"n": n, "ann": float("nan"), "vol": float("nan"), "sharpe": float("nan"), "mdd": float("nan"),
                "first": None, "last": None, "by_year": {}}
    m = sum(vals) / n
    sd = math.sqrt(sum((v - m) ** 2 for v in vals) / (n - 1))
    by_year: Dict[int, float] = {}
    years = sorted({dt.datetime.fromtimestamp(t / 1000, dt.timezone.utc).year for t, _ in xs})
    for y in years:
        yv = [v for t, v in xs if dt.datetime.fromtimestamp(t / 1000, dt.timezone.utc).year == y]
        if len(yv) >= 60:
            by_year[y] = sharpe(yv)
    return {"n": n, "ann": m * 365, "vol": sd * math.sqrt(365), "sharpe": sharpe(vals), "mdd": max_drawdown(vals),
            "first": _iso(xs[0][0]), "last": _iso(xs[-1][0]), "by_year": by_year}


def fmt(s: Dict[str, object]) -> str:
    by = " ".join(f"{y}:{v:+.2f}" for y, v in s["by_year"].items())
    return (f"n {s['n']:>5} {s['first']}..{s['last']}  Sharpe {s['sharpe']:+.3f}  ann {s['ann'] * 100:+7.1f}%  "
            f"vol {s['vol'] * 100:5.1f}%  MDD {s['mdd'] * 100:6.1f}%  | per-tahun {by}")
