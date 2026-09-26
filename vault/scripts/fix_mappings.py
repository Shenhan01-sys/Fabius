"""Perbaiki mapping yang ternyata tidak akurat setelah audit 27 Sep.

Setiap pasangan (berkas, teks lama, teks baru) WAJIB ketemu satu kali. Kalau tidak ketemu, skripnya
berhenti — supaya "sudah kuperbaiki" tidak pernah berarti "sudah kuasumsikan".

Kenapa banyak angka ikut berubah: vault punya aturan "run menang". Run hari ini mencetak 39/63 test
dan split verdict 3+14 dari chain, sementara halaman lama menulis 44 dan mengutip suite yang kini
sudah pindah ke dalam repo.
"""
import io
import os
import sys
# Windows: cmd.exe default cp1252 dan glyph yang kami cetak (`①④⑥` di arah, `⚠` di laporan)
# bukan bagian dari yang di-hash - jadi encoding stdout yang disetel, bukan stringnya.
# Tanpa ini, `print` bisa pecah DI TENGAH tabel dan separuh hasilnya terbaca seperti laporan penuh.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # stdout tanpa reconfigure (mis. tertangkap harness) = biarkan apa adanya

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isdir(os.path.join(VAULT, "00-Overview")):
    sys.exit(f"VAULT bukan folder vault: {VAULT}")

FIX = [
    # 1. jumlah test: yang terukur hari ini (lihat 07-Testing/01 - Test Commands)
    ("Quick-Reference.md",
     "forge test                                                     # 21 anchor (profil default)",
     "forge test                                                     # 39 lulus (21 anchor + 18 eksekusi)"),
    ("Quick-Reference.md",
     "FOUNDRY_PROFILE=fork forge test --fork-url bscTestnet          # 44 test, termasuk settlement x402",
     "FOUNDRY_PROFILE=fork forge test --fork-url bscTestnet          # 63 lulus, termasuk 9 fork x402 (27 Sep)"),
    ("00-Overview/04 - Run It.md",
     "forge test                                       # 21 DecisionAnchor (profil default, shanghai)",
     "forge test                                       # 39 lulus: 21 DecisionAnchor + 18 ExecutionVault"),
    ("00-Overview/04 - Run It.md",
     "FOUNDRY_PROFILE=fork forge test --fork-url bscTestnet      # 44 test, termasuk settlement x402 di 97",
     "FOUNDRY_PROFILE=fork forge test --fork-url bscTestnet      # 63 lulus, termasuk 9 fork settlement x402"),
    ("00-Overview/04 - Run It.md",
     "FOUNDRY_PROFILE=fork forge test --match-contract ExecutionVaultTest   # 18 jalur eksekusi",
     "FOUNDRY_PROFILE=fork forge test --match-contract ExecutionVaultTest   # 18 lulus, di kedua profil"),
    ("00-Overview/04 - Run It.md",
     "# 2. klaim inti, dibaca ulang tanpa kunci dan tanpa gas\npython -u tools/anchor.py --verify"
     "               # cocok / BEDA / BELUM DI-ANCHOR",
     "# 2. klaim inti, dibaca ulang tanpa kunci dan tanpa gas\npython -u tools/anchor.py --verify"
     "               # cocok / BEDA / BELUM DI-ANCHOR\npython -u tools/verify_vendor.py"
     "                 # vendor identik manifest (nol jaringan)"),

    # 2. vendor: harness kini ada di dalam repo, jadi klaim "dari clone" berlaku penuh
    ("02-Contracts/C5 - Vendored x402 Sources.md",
     "- Audit integritas: `python _research/vendored_x402.py verify` (hash disk vs manifest) dan\n"
     "  `compare` (menunjukkan salinan POC kami identik upstream — jadi bukti lama tidak jalan di sumber\n"
     "  yang disunat).",
     "- Audit integritas **dari dalam clone**: `python tools/verify_vendor.py` (hash + ukuran disk vs\n"
     "  manifest; terukur 27 Sep: 4/4 identik). Mode `compare` di `_research/vendored_x402.py` membanding-\n"
     "  kan salinan POC dengan upstream — itu alat workspace, jalurnya di luar repo produk, jadi jangan\n"
     "  dipakai sebagai bukti yang bisa dijalankan orang lain."),
    ("07-Testing/01 - Test Commands.md",
     "| 6 | `python _research/vendored_x402.py verify` | 4/4 identik dengan upstream pada commit pin | vendor tidak disunat |",
     "| 6 | `python tools/verify_vendor.py` | 4/4 identik dengan manifest @ commit pin | vendor tidak disunat, **dari dalam clone** |"),
    ("07-Testing/T5 - Integrity Harness.md",
     "python -X utf8 _research/vendored_x402.py verify",
     "python -X utf8 tools/verify_vendor.py"),
    ("07-Testing/T5 - Integrity Harness.md",
     "```text\n4/4 berkas vendor identik dengan upstream pada commit pin\n```",
     "```text\n  sama   docs/upstream-x402/x402BasePermit2Proxy.sol          0x276f1d092f740ede… 7411 B\n"
     "  sama   docs/upstream-x402/x402ExactPermit2Proxy.sol         0x6af38108c14d82dc… 4055 B\n"
     "  sama   contracts/vendor/x402/interfaces/ISignatureTransfer.sol 0x9ba755409cba5cad… 3755 B\n"
     "  sama   docs/upstream-x402/LICENSE.txt                       0x50e6751797c50ded… 11324 B\n\n"
     "upstream github.com/coinbase/x402 @ dd927a26cfefc98c24b3ec38b3a8f204dad0c60d\n"
     "4/4 identik dengan yang dicatat manifest\n```"),
    ("07-Testing/T5 - Integrity Harness.md",
     "**Dijalankan:** 27 Sep 2026 ±03:35 WIB (= 26 Sep 20:35Z)",
     "**Dijalankan:** 27 Sep 2026 ±03:35 WIB (= 26 Sep 20:35Z) — empat baris `sama`, exit 0"),
    ("04-Tools/TL7 - measurement harness.md",
     "- `_research/vendored_x402.py` — men-downloader upstream pada commit **eksplisit** dan mencatat "
     "sha256-nya; `verify` membandingkan ulang tanpa jaringan.",
     "- `_research/vendored_x402.py` (workspace) men-downloader upstream pada commit **eksplisit**; "
     "`tools/verify_vendor.py` (repo produk) yang membandingkan hash tanpa jaringan — sengaja ada di "
     "dalam repo supaya pembaca clone tidak perlu alat kami."),

    # 3. split verdict: sekarang dibaca dari chain, bukan dari ingatan
    ("01-Agent/A2 - Decision Spine.md",
     "- Keputusan agen hari ini sebagian besar `ABSTAIN` (14/17 anchor) — itu keluaran, bukan kegagalan.",
     "- Sebagian besar keputusan agen adalah `ABSTAIN`: **3 Enter + 14 Abstain** dari `anchorCount()` = 17, "
     "dibaca langsung lewat `countByVerdict` (`_research/vault_verdict_counts.py`, 27 Sep). Itu keluaran "
     "gerbang, bukan kegagalan."),
    ("10-Submissions/02 - Project Detail.md",
     "> **menolak** — penolakan itulah yang ikut ter-anchor (14 dari 17 keputusan), sehingga klaim",
     "> **menolak** — penolakan itulah yang ikut ter-anchor (14 dari 17 keputusan, terukur dari "
     "`countByVerdict` di chain), sehingga klaim"),
    ("07-Testing/T2 - Anchor Verify.md",
     "- ⚠️ `anchorCount() = 17` di chain vs **11** keputusan yang dihasilkan verifier dari 2 berkas.\n"
     "  6 entri ada di chain tapi tidak muncul dari berkas yang dibaca alat. **Belum kuurut** — item\n"
     "  terbuka, lihat [[08-Backlog/01 - Backlog]] P6. Yang penting: angka 17 tidak pernah kusebut sebagai\n"
     "  jumlah \"keputusanku\" kalau berkas repo cuma menopang 11.",
     "- ⚠️ Chain vs repo **tidak sama banyak**, dan ini lubang yang kuukur, bukan kusimpulkan:\n"
     "  `anchorCount()` = **17** (3 Enter + 14 Abstain, dari `countByVerdict`) sedangkan verifier membaca\n"
     "  **11** keputusan (2 Enter + 9 Abstain) dari 2 berkas. 6 entri — termasuk 1 Enter — ada di chain "
     "tanpa\n"
     "  baris sumber yang bisa dibaca repo. Perintah pembanding: `python _research/vault_verdict_counts.py`.\n"
     "  Dijadikan item terbuka ([[08-Backlog/01 - Backlog]] P6b). Sampai itu terurut, angka yang boleh "
     "dikutip\n"
     "  adalah **11** (yang terbuktikan dari berkas), **bukan 17**."),

    # 4. klaim lama yang menunjuk POC: suite-nya sudah pindah ke repo ini
    ("06-Results/01 - Claims and Limits.md",
     "| \"Jalur settlement x402 berfungsi di chain 97 dan 56, termasuk pembayaran tanpa gas oleh klien\" "
     "| `_research/x402-bnb-poc/` — 31 test (15 unit + 8 fork 97 + 8 fork 56) vs Permit2 & proxy yang "
     "nyata ter-deploy | fork test |",
     "| \"Jalur settlement x402 berfungsi di chain 97, termasuk pembayaran tanpa gas oleh klien\" "
     "| `test/X402SettleOnBsc.fork.t.sol` + `test/X402DemoToken.t.sol` di repo ini — 9 fork + 15 unit "
     "lulus 27 Sep vs Permit2 & proxy kanonis yang nyata ter-deploy ([[07-Testing/T4 - x402 Fork Suite]]) "
     "| fork test |"),

    # 5. nama suite yang berubah
    ("04-Tools/TL4 - anchor and verify.md", "[[07-Testing/T2 - forge anchor suite]]",
     "[[07-Testing/T2 - Anchor Verify]]"),
    ("05-Ecosystem/02 - x402 Payment.md",
     "- Perbandingan dengan proyek lain kami tidak dilakukan", "- Perbandingan dengan proyek lain kami tidak dilakukan"),
    ("05-Ecosystem/02 - x402 Payment.md", "delapan fork test", "sembilan fork test"),
    ("05-Ecosystem/00 - Hub BNB Ecosystem.md",
     "- [[02 - x402 Payment]] — proxy kanonis + Permit2, **satu pembayaran nyata** di 97 (1.000 atomic)",
     "- [[02 - x402 Payment]] — proxy kanonis + Permit2, **satu pembayaran nyata** di 97 (1.000 atomic), "
     "9 fork test"),

    # 6. rujukan bentuk pendek -> nama halaman penuh
    ("04-Tools/TL2 - direction.md", "([[06-Results/04]])", "([[06-Results/04 - Negative Results]])"),
    ("04-Tools/TL3 - security_gate.md", "(lihat [[04-Tools/TL7]])", "(lihat [[04-Tools/TL7 - measurement harness]])"),
    ("06-Results/07 - Matured Outcomes.md", "Uji A ([[06-Results/06]]).",
     "Uji A ([[06-Results/06 - Pre-registration Horizon]])."),
    ("START-HERE.md", "| agen lanjutan (sesi berikutnya) | [[Notes]] terakhir + [[08-Backlog/01 - Backlog]] |",
     "| agen lanjutan (sesi berikutnya) | [[09-Inbox/00 - Hub Inbox]] terakhir + [[08-Backlog/01 - Backlog]] |"),

    # 7. skrip generator ikut disamakan (supaya tidak menulis ulang angka lama kalau dijalankan lagi)
    ("scripts/migrate_vault.py", "[[Notes]]", "[[09-Inbox/00 - Hub Inbox]]"),
    ("scripts/migrate_vault.py", '"[[T2 - forge anchor suite]] — 21 test DecisionAnchor"',
     '"[[T2 - Anchor Verify]] — trail dibaca ulang tanpa kunci"'),
    ("scripts/migrate_vault.py", '"[[T4 - x402 fork suite]] — 44 test lewat alias `bscTestnet`"',
     '"[[T4 - x402 Fork Suite]] — 9 fork test lewat alias `bscTestnet`"'),
    ("scripts/add_part_notes.py", "FOUNDRY_PROFILE=fork forge test --fork-url bscTestnet      # 44 test,"
     " termasuk settlement x402 di 97",
     "FOUNDRY_PROFILE=fork forge test --fork-url bscTestnet      # 63 lulus, termasuk 9 fork settlement x402"),
    ("scripts/add_part_notes.py", "Keputusan agen hari ini sebagian besar `ABSTAIN` (14/17 anchor)",
     "Sebagian besar keputusan agen adalah `ABSTAIN` (3 Enter + 14 Abstain, `countByVerdict`)"),
]

# 8. backlog: dua lubang yang baru ketahuan hari ini
BACKLOG_OLD = ("| P6 | Investigasi 2 snapshot universe yang sha-nya tidak bisa dihitung ulang | ⬜ "
               "2 hipotesis sudah digugurkan | `06-Results/03` #21 |")
BACKLOG_NEW = BACKLOG_OLD + """
| P6b | Rantai 6 entri anchor yang tidak punya baris sumber di repo (termasuk 1 `Enter`) | ⬜ baru terlihat 27 Sep | `python _research/vault_verdict_counts.py` vs `anchor.py --verify`; selesai = kedua angka bisa dijelaskan baris per baris |
| P8 | Bukti "clone bersih" — `git clone` ke direktori kosong lalu jalankan registry [[07-Testing/01 - Test Commands]] baris 1–6 | ⬜ | satu tangkapan keluaran di halaman itu; ini yang membuat klaim "verifiable tanpa kami" benar-benar berdiri |"""

bad = []
for rel, old, new in FIX:
    p = os.path.join(VAULT, rel.replace("/", os.sep))
    if rel == "08-Backlog/01 - Backlog.md":
        continue
    if not os.path.isfile(p):
        bad.append(f"TIDAK ADA {rel}")
        continue
    t = io.open(p, encoding="utf-8").read()
    c = t.count(old)
    if c != 1:
        bad.append(f"{rel}: cocok {c}x (harus 1) -> {old[:58]!r}")
        continue
    io.open(p, "w", encoding="utf-8", newline="\n").write(t.replace(old, new))
    print("ok  ", rel, "<-", old[:48].replace("\n", "\\n"))

bp = os.path.join(VAULT, "08-Backlog", "01 - Backlog.md")
t = io.open(bp, encoding="utf-8").read()
if t.count(BACKLOG_OLD) == 1 and BACKLOG_NEW not in t:
    io.open(bp, "w", encoding="utf-8", newline="\n").write(t.replace(BACKLOG_OLD, BACKLOG_NEW))
    print("ok   08-Backlog/01 - Backlog.md <- P6b + P8")
else:
    bad.append(f"backlog: cocok {t.count(BACKLOG_OLD)}x")

if bad:
    print("\n".join("!! " + b for b in bad))
    sys.exit(f"\n{len(bad)} perbaikan TIDAK diterapkan — periksa teksnya, jangan dipaksakan.")
print(f"\n{len(FIX)} + 1 perbaikan diterapkan.")
