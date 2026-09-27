"""Gerbang pra-push: pastikan TIDAK ADA trailer atribusi AI di commit yang mau dikirim.

Kenapa di repo dan bukan cuma di config laptop: aturan yang cuma hidup di `~/.qwen` hilang begitu
mesin diganti atau sesi lain jalan; yang di repo ikut ter-clone, ikut dibaca GitHub Actions, dan
ikut dinilai orang. Ini juga menutup lubang yang bikin kami malu di 27 Sep: dua commit terlanjur
membawa trailer atribusi Claude ke repo PUBLIK, dan tidak ada satu pun pemeriksaan yang menegurnya.

Yang diperiksa: pesan commit di rentang yang akan dikirim. Yang TIDAK diperiksa: diff/isi berkas
(itu urusan review), karena trailer atribusi hidup di metadata commit.

String trailer ditulis terfragmentasi: berkas ini tidak boleh memuat bentuk utuh yang ia cari,
kalau tidak `git log --grep` kami sendiri akan menyerahnya sebagai pelanggaran.

Pakai:
    python -X utf8 vault/scripts/prepush_check.py                    # origin/<branch>..HEAD
    python -X utf8 vault/scripts/prepush_check.py --range HEAD~5..HEAD
    python -X utf8 vault/scripts/prepush_check.py --self-test         # uji detektornya sendiri
Keluar: 0 bersih · 1 ada pelanggaran · 2 tidak bisa menyimpulkan (mis. ref asal tidak ada).
"""
import argparse
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.isfile(os.path.join(REPO, "foundry.toml")):
    sys.exit(f"bukan akar Fabius: {REPO}")

H = chr(45)
AI = (r"cl" + r"au" + r"de|anth" + r"ropic|chatgpt|open" + r"ai|copilot|gemini|cursor|"
      r"qwen[\s\-]?code|\bai\b|artificial intelligence|large language model|\bllm\b")
PATTERNS = [
    re.compile(r"(?im)^\s*co[\s\-]?auth" + H[0] + r"?ored[\s\-]?by\s*:\s*[^\n]*(?:" + AI + r")"),
    re.compile(r"(?im)^\s*coauth" + H[0] + r"?or\s*by\s*:\s*[^\n]*(?:" + AI + r")"),
    re.compile(r"(?im)^\s*signed[\s\-]?off[\s\-]?by\s*:\s*[^\n]*(?:" + AI + r")"),
    re.compile(r"(?im)^\s*generated[\s\-]?with\s*:\s*[^\n]*(?:" + AI + r")"),
    re.compile(r"(?i)noreply@(?:" + r"an" + r"th" + r"ropic|open" + r"ai)\.com"),
]


def git(*args):
    r = subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


def default_range():
    """Rentang yang benar-benar akan ter-push: branch tracking asal, bukan asal tebakan HEAD~N."""
    rc, up, _ = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    if rc != 0 or not up:
        return None, "tidak ada upstream untuk branch ini (repo lokal tanpa remote?)"
    return f"{up}..HEAD", f"upstream {up}"


def scan(msg):
    hits = []
    for p in PATTERNS:
        m = p.search(msg)
        if m:
            hits.append(m.group(0).strip()[:70])
    return hits


CASES = [
    ("bersih", "feat: vault disusun ulang\n\nIsi pesan normal.", 0),
    ("trailer claude", "fix: x\n\nCo" + H + "Authored" + H + "By: Cl" + "aude <noreply@ant" + "hropic.com>", 1),
    ("signed-off AI", "chore: y\n\nSigned-off-by: Anth" + "ropic Bot <bot@example.com>", 1),
    ("generated-with", "docs: z\n\nGenerated with: Cl" + "aude", 1),
    ("nama model di badan pesan", "docs: pakai Cl" + "aude untuk uji A/B", 0),
    ("pembahasan aturan", "docs: jangan menulis Co" + H + "Authored" + H + "By di commit", 0),
]


def self_test():
    bad = 0
    for label, msg, want_hits in CASES:
        n = len(scan(msg))
        ok = (n > 0) == (want_hits > 0)
        if not ok:
            bad += 1
        print(f"  {'ok   ' if ok else 'GAGAL'} {label}: terdeteksi={n} harus={'ya' if want_hits else 'tidak'}")
    print(f"\n{len(CASES)} kasus, {bad} salah.")
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--range", default=None, help="mis. HEAD~5..HEAD (default: upstream..HEAD)")
    ap.add_argument("--all", action="store_true", help="periksa SELURUH riwayat (audit, bukan pra-push)")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        sys.exit(self_test())

    if a.all:
        rng, asal = "HEAD", "--all (seluruh riwayat)"
    else:
        rng = a.range
        asal = "--range"
        if not rng:
            rng, err = default_range()
            if not rng:
                print(f"TIDAK BISA MENYIMPULKAN: {err}", file=sys.stderr)
                sys.exit(2)

    rc, out, err = git("log", "--format=%H%x00%s%x00%b%x01", rng)
    if rc != 0:
        print(f"TIDAK BISA MENYIMPULKAN: git log gagal: {err[:200]}", file=sys.stderr)
        sys.exit(2)
    commits = [c for c in out.split("\x01") if c.strip()]
    if not commits:
        print(f"0 commit pada {rng} ({asal}) -> tidak ada yang perlu diperiksa; lolos.")
        sys.exit(0)

    buruk = 0
    for c in commits:
        sha, subject, body = (c.split("\x00") + ["", ""])[:3]
        hits = scan(f"{subject}\n{body}")
        if hits:
            buruk += 1
            print(f"  PELANGGARAN {sha[:7]}  {subject[:64]}")
            for h in hits:
                print(f"      -> {h!r}")
    print(f"\n{len(commits)} commit diperiksa pada {rng} ({asal}); "
          f"{'BERSIH, boleh push.' if not buruk else f'{buruk} commit membawa atribusi AI -> JANGAN push.'}")
    if buruk:
        print("Perbaiki dulu: `git rebase -i <asal>` / `git commit --amend -F <pesan baru>` untuk yang "
              "di ujung. Kalau sudah pernah ter-push, tulis ulang riwayat adalah keputusan builder — "
              "ukur dulu `git rev-list --count <base>..HEAD`, jangan force-push sendiri.")
    sys.exit(1 if buruk else 0)


if __name__ == "__main__":
    main()
