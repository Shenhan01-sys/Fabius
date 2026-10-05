"""Gambar tabel paket sinyal untuk Telegram (permintaan builder 5 Okt: "dibuatkan tabel gitu di chat telegramnya? Bukan tabel ascii").

Telegram tidak punya tabel (HTML-nya pun tanpa <table>), jadi tabel digambar sebagai PNG di gerbang dan diunggah langsung lewat `sendPhoto` (multipart)
- tidak lewat URL publik, sehingga isi berbayar tidak bocor. Font = TrueType bawaan Pillow (>= 10.1; tanpa berkas font di image).
Gagal menggambar (Pillow tidak ada / galat) = None -> pemanggil kembali ke pesan teks; paket yang sudah dibayar tidak pernah tertahan karena gambar.
"""
from __future__ import annotations

import html
from typing import Optional

INK, MUTED, LAV, VIOLET, GREEN, RED, LINE, WHITE = "#1A1530", "#6B6680", "#F1ECFF", "#6E56CF", "#12805C", "#C2303F", "#E6E1F2", "#FFFFFF"


def _px(x: float) -> str:
    return f"{x:,.2f}" if x >= 100 else (f"{x:.4f}" if x >= 1 else f"{x:.6f}")


def _pct(x: float) -> str:
    return f"{x * 100:+.1f}%"


def rows_of(p: dict) -> tuple:
    """-> (kolom, baris) yang digambar; murni (diuji tanpa Pillow)."""
    r = p.get("rincian") or {}
    aset = r.get("aset") or {}
    if aset and any("keluar_berikut" in d for d in aset.values()):
        cols = ["Asset", "Side", "Weight", "Entry (rule)", "PnL", "Exit next bar if close <="]
        rows = []
        for a, d in sorted(aset.items(), key=lambda kv: kv[1].get("keluar_berikut", {}).get("jarak", -9), reverse=True):
            e, k = d.get("masuk"), d["keluar_berikut"]
            rows.append([a, d["sisi"], f"{d['bobot'] * 100:.2f}%", f"{e['bar']} @ {_px(e['harga'])}" if e else f"> {_px(d['masuk_bila']['di_atas'])}",
                         _pct(e["pnl"]) if e else "-", f"{_px(k['level'])}  ({_pct(k['jarak'])})"])
        return cols, rows
    tg = (r.get("aset") and {a: d["bobot"] for a, d in aset.items()}) or p.get("targets", {})
    rows = [[a, "LONG" if w > 0 else ("SHORT" if w < 0 else "FLAT"), f"{w * 100:.2f}%"] for a, w in sorted(tg.items(), key=lambda kv: -abs(float(kv[1])))]
    return ["Asset", "Side", "Weight"], rows or [["-", "FLAT", "0.00%"]]


def render_png(p: dict, rule_en: Optional[str] = None) -> Optional[bytes]:
    try:
        import io
        from PIL import Image, ImageDraw, ImageFont
        f_title, f_body, f_small, f_head = (ImageFont.load_default(size=s) for s in (30, 19, 15, 16))
    except Exception:  # noqa: BLE001
        return None
    try:
        cols, rows = rows_of(p)
        widths = [170, 80, 95, 270, 100, 300][:len(cols)]
        pad, row_h, top = 36, 36, 168
        w = pad * 2 + sum(widths)
        h = top + row_h * (len(rows) + 1) + 120
        im = Image.new("RGB", (w, h), WHITE)
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, w, top - 24], fill=LAV)
        r = p.get("rincian") or {}
        d.text((pad, 26), f"Fabius {p['bot']} · bar {p['bar']}", font=f_title, fill=INK)
        rule = rule_en or r.get("aturan") or ""
        d.text((pad, 70), f"Rule: {rule}"[:150], font=f_small, fill=MUTED)
        ch = r.get("perubahan") or {}
        d.text((pad, 96), f"Changes vs previous bar: enter {', '.join(ch.get('masuk') or []) or '-'} · exit {', '.join(ch.get('keluar') or []) or '-'}"[:150],
               font=f_small, fill=MUTED)
        d.text((pad, 120), "No TP/SL outside the rule · judged on the daily close (00:00 UTC) · paper position intents at 1x", font=f_small, fill=VIOLET)
        y = top
        x = pad
        for c, cw in zip(cols, widths):
            d.text((x, y + 8), c, font=f_head, fill=MUTED)
            x += cw
        d.line([pad, y + row_h - 2, w - pad, y + row_h - 2], fill=LINE, width=2)
        for i, row in enumerate(rows):
            y = top + row_h * (i + 1)
            if i % 2:
                d.rectangle([pad - 8, y, w - pad + 8, y + row_h], fill="#FAF8FF")
            x = pad
            for j, (cell, cw) in enumerate(zip(row, widths)):
                color = INK
                if cols[j] == "PnL" and cell not in ("-", ""):
                    color = GREEN if cell.startswith("+") else RED
                if cols[j] == "Side":
                    color = GREEN if cell == "LONG" else (RED if cell == "SHORT" else MUTED)
                d.text((x, y + 8), str(cell), font=f_body, fill=color)
                x += cw
        y = top + row_h * (len(rows) + 1) + 18
        k, v = p.get("komit") or {}, p.get("validasi_erc8004")
        d.text((pad, y), f"commitId {p['commitId'][:22]}…  ·  committed on-chain: {'yes' if k.get('ada') else 'not yet'}"
                         + (f"  ·  ERC-8004 validation: {v['skor']}" if v and v.get("dijawab") else ""), font=f_small, fill=MUTED)
        if p.get("pembayaran"):
            d.text((pad, y + 26), f"paid {p['pembayaran']['atomic'] / 1e6:g} FAB  ·  tx {p['pembayaran']['tx']}", font=f_small, fill=MUTED)
        d.text((pad, y + 52), "Exit levels move every day with the window: a trailing stop on the daily close. Not investment advice. BNB testnet.",
               font=f_small, fill=MUTED)
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        return buf.getvalue()
    except Exception:  # noqa: BLE001
        return None


def caption_html(p: dict) -> str:
    """Keterangan foto (HTML Telegram, <= 1024 karakter): ringkas, semua teks di-escape."""
    e = html.escape
    r = p.get("rincian") or {}
    near = r.get("terdekat_keluar")
    lines = [f"<b>Fabius {e(p['bot'])}</b> · bar {e(p['bar'])}"]
    if near and near in (r.get("aset") or {}):
        k = r["aset"][near]["keluar_berikut"]
        lines.append(f"Closest to exit: <b>{e(near)}</b> ({_pct(k['jarak'])})")
    k, v = p.get("komit") or {}, p.get("validasi_erc8004")
    lines.append(f"Proof: committed {'✓' if k.get('ada') else '…'}" + (f" · ERC-8004 {v['skor']}" if v and v.get("dijawab") else ""))
    if p.get("pembayaran"):
        tx = p["pembayaran"]["tx"]
        lines.append(f'Paid {p["pembayaran"]["atomic"] / 1e6:g} FAB · <a href="https://testnet.bscscan.com/tx/{e(tx)}">tx</a>')
    return "\n".join(lines)[:1024]
