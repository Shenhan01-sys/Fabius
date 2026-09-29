"""Berapa TUA harga yang kami catat sebagai 'harga kini'? (bisa diukur dari data yang ADA)

Baris `px` kami di-stamp waktu tarikan, tapi nilainya datang dari transaksi - jadi setiap kali kita
membaca "harga", sebenarnya kita membaca harga yang terjadi `t_pull - t_tx` detik yang lalu.
Itu tidak perlu menunggu perubahan kode: baris `tx` menyimpan waktu transaksi aslinya.

Untuk setiap baris `px`: staleness = waktu_tarikan - waktu transaksi terakhir token itu yang
terlihat SEBELUM tarikan itu. Distribusinya adalah umur sebenarnya dari "harga kini" kita, dan dia
menjadi syarat yang harus disebut saat menyebut angka outcome 30 menit.
"""
import bisect
import io
import os
import sys
import json
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(HERE)
FLOW = os.path.join(R, "universe", "wallet-flow.jsonl")
sys.path.insert(0, HERE)
MIN = 60

px, txs = [], {}
for ln in io.open(FLOW, encoding="utf-8", errors="replace"):
    ln = ln.strip()
    if not ln or ln.startswith("#"):
        continue
    d = json.loads(ln)
    tk = str(d.get("tk") or "").lower()
    t = int(d.get("t") or 0)
    if not tk or not t:
        continue
    if d.get("k") == "px":
        px.append((tk, t))
    elif d.get("k") in ("tx", "txc"):
        txs.setdefault(tk, []).append(t)
for tk in txs:
    txs[tk] = sorted(set(txs[tk]))

print("baris px %d | token dengan transaksi %d" % (len(px), len(txs)))
lag, tanpa = [], 0
for tk, t in px:
    s = txs.get(tk)
    if not s:
        tanpa += 1
        continue
    i = bisect.bisect_right(s, t) - 1
    if i < 0:
        tanpa += 1
        continue
    lag.append(t - s[i])

lag.sort()
n = len(lag)
print("yang tidak bisa dijadwalkan sama sekali (token px tanpa baris tx): %d" % tanpa)
print("lag harga (detik) pada %d baris px:" % n)
for q in (0.1, 0.25, 0.5, 0.75, 0.9, 0.99):
    print("   p%-4d %8.0f s  = %6.1f menit" % (int(q * 100), lag[int(q * (n - 1))],
                                               lag[int(q * (n - 1))] / 60.0))
print("   rata-rata %.0f s | maks %d s = %.1f jam" % (statistics.fmean(lag), lag[-1],
                                                      lag[-1] / 3600.0))
for amb in (60, 180, 300, 600, 1800):
    print("   px yang harganya lebih tua dari %4d mnt: %5d (%.1f %%)"
          % (amb / 60.0, sum(1 for x in lag if x > amb), 100.0 * sum(1 for x in lag if x > amb) / n))
print("\nIni sebabnya 'harga diam' 71,7 % itu terjadi: kami sering membaca ulang transaksi lama,"
      "\nbukan mengamati pool yang bergerak. Angka ini wajib disebut bersama setiap outcome 30 menit.")
