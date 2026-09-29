"""Win-streak + gerbang kepercayaan (F-D16) — dibaca dari rekaman, tidak dihitung ulang.

Kenapa berkas ini ada: builder minta melihat **winstreak**, dan itu persis angka yang paling mudah
dibuat menjadi bohong. Jadi alat ini tidak menambah kebenaran baru — dia menyusun yang sudah ada
dan menampilkan **berapa lagi yang kurang** sebelum angka itu boleh disebut apa pun. Aturan F-D22/F-D16
di vault: `n >= 20`, harapan bersih > 0, dan itu semua di luar sampel. Di bawah itu, streak bukan
performa - dia kebetulan yang urutannya kita pilih sendiri.

Dua seri dipisah dan tidak pernah digabung, karena artinya beda:
  PAPER  = keputusan yang di-anchor + dinilai terhadap bar harga pasar nyata (`decisions/ledger-*.jsonl`)
  CHAIN  = fill nyata di venue demo kita sendiri (`decisions/execution-trail.jsonl`, angka dari
           event `Closed`) - strukturnya selalu -fee karena pool-nya tidak ada arus luar.

Pakai:  python -X utf8 tools/winlog.py [--json]
"""
import argparse
import glob
import io
import json
import os
import sys

# `paper-book-positions.jsonl` bisa berisi DUA penggaris sejak P42 (v1 salah satuan F-D46,
# v2 harga BNB terukur + lantai likuiditas F-D62). Streak yang dipakai sebagai bukti
# `promote-after` tidak boleh mencampur keduanya - satu deret, satu aturan hitung.
SKEMA_BUKU = "v1-bnb-dianggap-usd"
SKEMA_DIBUANG = {"n": 0, "contoh": None}



ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isfile(os.path.join(ROOT, "foundry.toml")):
    sys.exit(f"ROOT bukan akar Fabius: {ROOT} - harus berisi foundry.toml")

LEDGER = os.path.join(ROOT, "decisions", "ledger-*.jsonl")
TRAIL = os.path.join(ROOT, "decisions", "execution-trail.jsonl")
BOOK = os.path.join(ROOT, "decisions", "paper-book-positions.jsonl")

MIN_N = 20          # F-D16: di bawah ini tidak ada klaim win-rate yang boleh keluar
ALPHA = 0.10        # Benjamini-Hochberg, ambang yang sama di semua uji proyek ini


def read_jsonl(path):
    if not os.path.isfile(path):
        return []
    out = []
    for line in io.open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"  ! baris tidak sah di {os.path.basename(path)} - dilewati, bukan ditebak",
                  file=sys.stderr)
    return out


def paper_events():
    """Satu entri per `decisionHash`. Artefak ledger baru menimpa yang lama (run menang)."""
    ev = {}
    konflik = []
    pending = 0
    for f in sorted(glob.glob(LEDGER)):
        for art in read_jsonl(f):
            asof = art.get("as_of_utc", "?")
            for r in art.get("rows") or []:
                st = str(r.get("status") or "")
                if st == "BUKAN POSISI":
                    continue
                if st == "BELUM JATUH TEMPO":
                    pending += 1
                    continue
                key = r.get("decisionHash") or f"{r.get('symbol')}|{r.get('side')}|{r.get('due_utc')}"
                rec = {"id": key, "when": r.get("due_utc") or asof, "symbol": r.get("symbol"),
                       "side": r.get("side"), "net": r.get("net_bps"), "gross": r.get("gross_bps"),
                       "mfe": r.get("mfe_bps"), "status": st, "regime": r.get("regime"),
                       "horizon_h": r.get("horizon_h"), "from": os.path.basename(f),
                       "win": r.get("win")}
                old = ev.get(key)
                if old and old.get("net") != rec.get("net"):
                    konflik.append((key[:14], old.get("net"), rec.get("net")))
                ev[key] = rec                      # berkas terakhir menang (run terbaru)
    return sorted(ev.values(), key=lambda x: (str(x["when"]), str(x["id"]))), pending, konflik


def chain_events():
    out = []
    for r in read_jsonl(TRAIL):
        if r.get("action") != "close":
            continue
        bps = r.get("realized_bps")
        if bps is None:
            continue
        out.append({"when": r.get("at_utc"), "symbol": r.get("symbol"), "net": bps,
                    "gas_units_paid": r.get("gas_units_paid"), "win": bps > 0,
                    "tx": (r.get("tx") or "")[:12]})
    return sorted(out, key=lambda x: str(x["when"]))


def book_events():
    """Seri KETIGA: slot BUKU PAPER dari aliran ⑦ (`tools/paper_book.py`).

    Tidak pernah digabung dengan dua seri lain, dan namanya pun sengaja mirip tapi beda barang:
      PAPER  = keputusan yang DI-ANCHOR lalu dinilai terhadap bar harga pasar nyata (Aster)
      CHAIN  = fill nyata di pool demo kami sendiri
      BUKU   = posisi BOONGAN dari aliran ⑦ pada harga peristiwa, berlabel `mode: PAPER`, dengan
               kolom `pengganti_real` kosong sampai order asli mengisi slot yang sama
    Mean-nya di-winsor +-2.000 bps dan winsor itu DILAPORKAN: pada payoff yang p99-nya +105.000 bps,
    mean tanpa batas bukan angka yang bisa dibaca.
    """
    out = []
    if not os.path.exists(BOOK):
        return out
    for ln in io.open(BOOK, encoding="utf-8", errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if r.get("status") != "dinilai" or r.get("net_bps") is None:
            continue
        sk = r.get("skema_dampak")
        if sk is not None and sk != SKEMA_BUKU:
            # tanpa cap = v1 (ditulis sebelum F-D62); cap yang BEDA baru dibuang
            SKEMA_DIBUANG["n"] += 1
            SKEMA_DIBUANG["contoh"] = sk
            continue
        w = max(-2000.0, min(2000.0, float(r["net_bps"])))
        out.append({"when": r.get("due_utc"), "symbol": r.get("tk"), "net": w,
                    "net_tanpa_batas": r["net_bps"], "win": r["net_bps"] > 0,
                    "slot": r.get("slot_id"), "kebijakan": r.get("kebijakan"),
                    "promosi": r.get("promosi"), "layak": r.get("kebijakan_layak_real"),
                    "pengganti_real": r.get("pengganti_real"), "mode": r.get("mode", "PAPER")})
    return sorted(out, key=lambda x: (str(x["when"]), str(x["slot"])))


def streaks(seq):
    """(streak sekarang, terpanjang menang, terpanjang kalah) pada baris yang DINILAI."""
    rows = [e for e in seq if e.get("win") is not None]
    cur = cur_win = 0
    longest_up = longest_down = 0
    run_dir, run_len = None, 0
    for e in rows:
        d = "W" if e["win"] else "L"
        run_len = run_len + 1 if d == run_dir else 1
        run_dir = d
        longest_up = max(longest_up, run_len) if d == "W" else longest_up
        longest_down = max(longest_down, run_len) if d == "L" else longest_down
        cur = run_len
        cur_win = run_len if d == "W" else 0
    return cur, cur_win, longest_up, longest_down, len(rows)


def gate(seq, label, extra=""):
    n = len(seq)
    wins = sum(1 for e in seq if e.get("win"))
    nets = [float(e["net"]) for e in seq if isinstance(e.get("net"), (int, float))]
    mean = sum(nets) / len(nets) if nets else None
    print(f"\n### {label}{extra}")
    if not seq:
        print("  belum ada peristiwa yang dinilai.")
        return
    print("  urut waktu:")
    for e in seq:
        mark = "MENANG" if e.get("win") else ("RUGI" if e.get("win") is False else "AMBIGU")
        net = e.get("net")
        net = f"{net:+8.1f} bps" if isinstance(net, (int, float)) else "     -   "
        print(f"    {str(e.get('when'))[:19]}  {str(e.get('symbol'))[:14]:14} "
              f"{str(e.get('side') or '-')[:6]:6} {net}  {mark}"
              + (f"  mfe {e['mfe']:+.0f}" if isinstance(e.get("mfe"), (int, float)) else ""))
    cur, cur_win, up, down, dn = streaks(seq)
    wr = 100.0 * wins / dn if dn else 0.0
    print(f"  streak sekarang: {cur} ({'MENANG' if cur_win else 'KALAH' if cur else '-'})"
          f" | terpanjang menang {up} | terpanjang kalah {down}")
    print(f"  n={dn} | WR {wr:.1f} % | net rata-rata "
          f"{mean:+.1f} bps | total {sum(nets):+.1f} bps" if mean is not None else "  (net tak terbaca)")
    ok_n = dn >= MIN_N
    ok_e = mean is not None and mean > 0
    print(f"  gerbang F-D16: n>= {MIN_N} -> {'LEWAT' if ok_n else f'BELUM (kurang {MIN_N - dn})'} | "
          f"harapan bersih > 0 -> {'LEWAT' if ok_e else 'BELUM'}")
    verdict = ("KLAIM BOLEH DIUCAPKAN" if (ok_n and ok_e)
               else "STREAK BELUM BOLEH DIJUAL - baca sebagai log, bukan performa "
                    "(10-Submissions/01 menahan kalimatnya)")
    print("  " + verdict)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    paper, pending, konflik = paper_events()
    chain = chain_events()
    dinilai = [e for e in paper if e.get("win") is not None]
    ambigu = [e for e in paper if "AMBIGU" in str(e.get("status"))]

    if a.json:
        print(json.dumps({"paper": dinilai, "chain": chain, "ambigu": ambigu,
                          "belum_jatuh_tempo_baris": pending}, indent=1, sort_keys=False,
                         ensure_ascii=False))
        return

    print(f"sumber: {len(glob.glob(LEDGER))} artefak ledger + {1 if chain else 0} trail chain")
    print(f"baris BELUM JATUH TEMPO (tidak ikut agregat): {pending}")
    if konflik:
        print(f"  ! {len(konflik)} decisionHash dengan net berbeda antar artefak: {konflik[:3]}")
    gate(dinilai, "PAPER - keputusan ter-anchor vs harga pasar nyata (Aster)")
    if SKEMA_DIBUANG["n"]:
        print(f"  {SKEMA_DIBUANG['n']} slot buku paper memakai penggaris lain "
              f"({SKEMA_DIBUANG['contoh']}) - tidak masuk streak; bukti `promote-after` harus satu "
              f"aturan hitung (P42/F-D62)")
    if ambigu:
        print(f"  AMBIGU yang sengaja dikecualikan dari streak: {len(ambigu)}")
    buku = book_events()
    gate(buku, "BUKU PAPER ⑦ - slot boongan pada harga peristiwa (mean di-winsor +-2.000 bps)",
         "  LABEL: tiap baris membawa mode=PAPER + slot_id; `pengganti_real` masih kosong berarti "
         "belum ada order asli yang menambalnya")
    gate(chain, "CHAIN - fill nyata di venue demo sendiri",
         "  (pool x·y=k tanpa arus luar: realisasi = -fee, jadi ini ongkos, bukan sinyal)")
    siap = [x for x in buku if x.get("layak") == "YA"]
    kalau = [x for x in buku if x.get("pengganti_real")]
    print("\nPeringatan yang menempel: TIGA seri ini tidak dibandingkan dan tidak digabung - satu "
          "menguji tebakan terhadap pasar nyata, satu mengukur biaya eksekusi di kolam sendiri, satu "
          "lagi adalah buku posisi boongan.")
    if buku:
        print("  BUKU PAPER: %d slot dinilai | %d kebijakan layak real | %d slot sudah ditambal "
              "posisi ASLI" % (len(buku), len(siap), len(kalau)))
        if tidak := len(buku) - len(kalau):
            print("  -> %d slot masih boongan. Yang boongan tidak boleh ditulis sebagai PnL, dan "
                  "yang sudah ditambal harus menunjuk satu tx." % tidak)


if __name__ == "__main__":
    main()
