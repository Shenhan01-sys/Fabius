"""Suntingan Quick-Reference yang gagal dicocokkan `record_p1_p8.py` (pola pertamanya salah ingat).

Dipisah supaya yang gagal kelihatan sebagai satu berkas, bukan hilang di tengah laporan. Setiap
pola wajib ketemu tepat satu kali.
"""
import io
import os
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REL = "Quick-Reference.md"
p = os.path.join(VAULT, REL)
t = io.open(p, encoding="utf-8").read()

PAIRS = [
    # alamat kontrak eksekusi + manifest ter-track
    ("| DecisionAnchor (chain 97) | `0xdd162afb5f5f92d5092f845a93660e3b38259330` | [[02-Contracts/02 - Deployed on 97]] |",
     "| DecisionAnchor (chain 97) | `0xdd162afb5f5f92d5092f845a93660e3b38259330` | [[02-Contracts/02 - Deployed on 97]] |\n"
     "| ExecutionVault (chain 97) | `0x2743cD33C8790437594E119289838F35c0d1d290` | ter-deploy 27 Sep; cap 5 unit/hari, 1 unit/posisi |\n"
     "| DemoPair (97) | `0x6f93d787bBE99A6842CCa511ccB3b8D6d976696E` | x·y=k, fee 30 bps, spot 2,0000 |\n"
     "| DemoAsset (97) | `0x4180A42A119F0B5480637900679C0AaFB1F2a8d7` | ERC20 demo 6 desimal |\n"
     "| **manifest alamat** | `deployments/97.json` (ter-track) | 8 alamat + cek bytecode dari chain — inilah yang membuat `--verify` jalan di clone |"),

    # baris agen: sumber alamat + pembantahnya
    ("| agen (penanda-tangan anchor) | `0x4bb30E3b3bc22082c1935fE3bE7c07448e69c862` | `Fabius/.agent.env` (tidak di-commit) |",
     "| agen (penanda-tangan anchor) | `0x4bb30E3b3bc22082c1935fE3bE7c07448e69c862` | env → `deployments/97.json` → derivasi kunci; **dibantah ke kontrak** lewat `getAgent()`/`countByAgent()` = 17, aktif=True |"),

    # angka yang berlaku
    ("| aliran wallet terekam | 7.137 transaksi / 322 maker / 10,14 jam | `_research/panel_stats.py` |",
     "| **posisi nyata dieksekusi di 97** | 2 round-trip, realized **−59 bps** per putaran | `decisions/execution-trail.jsonl` (angka dari event `Closed`) |\n"
     "| gas nyata eksekusi | open 258.008/295.443 · close 123.216/150.576 | `tools/execute_live.py` |\n"
     "| jalur pemeriksaan hidup dari clone bersih | **4/4** pada HEAD `304fe4f` | [[07-Testing/T6 - Clean Clone Evidence]] |\n"
     "| aliran wallet terekam | 8.053 transaksi / 348 maker / 643 token / 11,82 jam | `_research/panel_stats.py` *(workspace)* |"),

    # batas yang harus ikut disebut
    ("- jalur eksekusi **sudah ada dan teruji, belum dipakai trading nyata di 97** (lihat [[08-Backlog/01 - Backlog]] P1)",
     "- jalur eksekusi **sudah dipakai**: dua round-trip nyata di 97, masing-masing rugi 59 bps —\n"
     "  di **venue demo milik kami sendiri**, jadi angkanya adalah biaya, bukan hasil pasar\n"
     "- `anchorCount()` di chain (17) lebih besar dari baris keputusan yang terpelacak di repo (11);\n"
     "  `--verify` memperingatkan ini di keluarannya. Jangan kutip 17 sebagai jumlah keputusan kami\n"
     "  (lihat [[08-Backlog/01 - Backlog]] P6b)"),
]

bad = []
for old, new in PAIRS:
    if t.count(old) != 1:
        bad.append(f"{t.count(old)}x untuk {old[:58]!r}")
        continue
    t = t.replace(old, new, 1)
    print("ok  ", old[:58].replace("\n", " / "))

if bad:
    io.open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("\n".join("!! " + b for b in bad))
    sys.exit(f"{len(bad)} dari {len(PAIRS)} tidak cocok — yang lain sudah ditulis, perbaiki polanya")
io.open(p, "w", encoding="utf-8", newline="\n").write(t)
print(f"\n{len(PAIRS)} suntingan {REL} diterapkan.")
