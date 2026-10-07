"""Perawatan vault Fabius: peta otomatis + daftar berkas tertinggal.

    python scripts/sync_vault.py     # tulis _Auto-Index per folder + catatan _Perawatan
    python scripts/sync_vault.py --check   # laporkan saja, jangan menulis

Ditiru dari pola vault proyek lain kami (Lencana) dengan dua penyimpangan yang disengaja:
  1. Python, bukan PowerShell — semua perkakas Fabius sudah Python; dua bahasa operasional untuk
     satu repo berarti satu di antaranya tidak akan pernah dijalankan.
  2. Tidak ada `status: draft|ready` — untuk repo yang umurnya hitungan hari, status draf hanyalah
     cara lain menyebut "belum ditulis". Yang kami lacak sebagai gantinya: umur tiap berkas.
"""
import argparse
import datetime as dt
import os
import re
import sys
# Windows: cmd.exe default cp1252 dan glyph yang kami cetak (`①④⑥` di arah, `⚠` di laporan)
# bukan bagian dari yang di-hash - jadi encoding stdout yang disetel, bukan stringnya.
# Tanpa ini, `print` bisa pecah DI TENGAH tabel dan separuh hasilnya terbaca seperti laporan penuh.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # stdout tanpa reconfigure (mis. tertangkap harness) = biarkan apa adanya

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isdir(os.path.join(ROOT, "00-Overview")):
    sys.exit(f"ROOT bukan folder vault: {ROOT}")
SKIP_DIRS = {"Sessions", "_archive", "scripts", "Templates", "node_modules"}   # node_modules: proyek JS di vault (Video-Workspace)
ORDER = re.compile(r"^(\d{2}|[A-Z]{1,3}\d+)")


def title(name):
    return name[:-3] if name.endswith(".md") else name


def sort_key(name):
    t = title(name)
    m = ORDER.match(t)
    return (0, int(m.group(1)) if m.group(1).isdigit() else 0, t) if m else (1, 0, t)


def md_files(folder, recurse=False):
    # `folder` boleh nama relatif ("03-Data") atau path absolut. Tanpa ini, skrip yang dijalankan
    # dari `Fabius/` (bukan dari `vault/`) membuat os.walk("03-Data") mengembalikan KOSONG, semua
    # folder di-skip lewat `if not parts: continue`, dan `sync` melaporkan sukses sambil tidak
    # menyentuh satu pun hub. Perbaikan yang dijalankan dari direktori yang SALAH harus berbunyi,
    # bukan terlihat bersih.
    start = folder if os.path.isabs(folder) else os.path.join(ROOT, folder)
    out = []
    for cur, dirs, files in os.walk(start):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".md") and not f.startswith("_"):
                out.append(os.path.relpath(os.path.join(cur, f), ROOT).replace(os.sep, "/"))
        if not recurse:
            break
    return sorted(out, key=lambda p: sort_key(os.path.basename(p)))


def rel(from_path, to_path):
    d = os.path.dirname(from_path)
    return os.path.relpath(to_path, d).replace(os.sep, "/") if d else to_path


def folders():
    return sorted(d for d in os.listdir(ROOT)
                  if os.path.isdir(os.path.join(ROOT, d))
                  and d not in SKIP_DIRS and not d.startswith("_") and not d.startswith("."))


def hub_of(folder):
    """Hub = berkas `00 - Hub *`, ATAU berkas yang frontmatter-nya menandai diri `hub`.

    Yang kedua ada karena `08-Backlog/01 - Backlog.md` sudah berupa peta P1..P8; membuat
    `00 - Hub Backlog.md` di sebelahnya hanya menghasilkan dua peta yang bisa tidak cocok.
    """
    fallback = None
    for p in md_files(folder):
        head = open(os.path.join(ROOT, p.replace("/", os.sep)), encoding="utf-8").read(300)
        if os.path.basename(p).startswith("00 - Hub"):
            return p
        if re.search(r"^tags:.*\bhub\b", head, flags=re.M):
            fallback = fallback or p
    return fallback


def hub_body(hub_path, parts):
    """Daftar Bagian = append-only. Gloss tulisan manusia tidak pernah ditimpa.

    Versi pertama script ini menulis ulang seluruh daftar dari nol dan akibatnya menghapus satu
    baris penjelasan di tiap hub - padahal aturan vault-nya justru "tiap baris dapat penjelasan".
    Jadi sekarang: baris yang sudah ada dibiarkan apa adanya, berkas baru ditambahkan di ujung,
    dan tautan yang berkasnya sudah tidak ada dilaporkan, bukan dihapus diam-diam.
    """
    hub_abs = hub_path if os.path.isabs(hub_path) else os.path.join(ROOT, hub_path.replace("/", os.sep))
    text = open(hub_abs, encoding="utf-8").read() if os.path.exists(hub_abs) else None
    # Tag dataview diambil dari FRONTMATTER hub (entri pertama selain `hub`), bukan dari nama file.
    # Versi sebelumnya memotong nama file dan menghasilkan `LIST FROM #hub-overview.md` - query yang
    # tidak cocok dengan tag mana pun, jadi peta otomatisnya kosong tanpa pernah bilang kosong.
    tag = None
    if text:
        m = re.search(r"^tags:\s*\[([^\]]*)\]", text, re.M)
        if m:
            for t in [x.strip() for x in m.group(1).split(",")]:
                if t and t != "hub":
                    tag = t
                    break
    tag = tag or os.path.dirname(hub_path).split("-", 1)[-1].lower().replace(" ", "-")
    listed = set()
    lines_out = []
    # SATU blok saja. Versi sebelumnya memindai seluruh berkas sehingga bullet `## Terkait`
    # diseret masuk ke daftar bagian, dan mengganti sampai blok dataview sehingga heading
    # `## Terkait` tertimpa. Keduanya: alat yang menulis ulang lebih banyak dari yang ia pahami.
    block = re.search(r"^## Bagian\n(.*?)(?=^##\s|^```|\Z)", text or "", flags=re.M | re.S)
    if block:
        # Jalankan per-BARIS, jangan per-regex-potongan-kalimat. Versi sebelumnya mengambil hanya
        # baris yang cocok `- [[nama]]` dan menulis ulang baris itu saja: setiap gloss yang
        # menyambung ke baris berikutnya (semua hub di vault ini begitu) HILANG, dan alias
        # `[[nama|label]]` dipotong menjadi `[[nama]]`. Run 28 Sep menghapus 13 baris gloss dari
        # dua hub sebelum ketahuan. Yang ditulis ulang sekarang adalah blok apa adanya - alat ini
        # hanya boleh MENAMBAH, tidak pernah memperindah.
        raw = block.group(1).split("\n")
        i = 0
        while i < len(raw):
            ln = raw[i]
            m = re.match(r"^\s*-\s*\[\[([^\]]+)\]\]", ln)
            if not m:
                i += 1
                continue
            inner = m.group(1).split("|")[0].strip()
            listed.add(os.path.basename(inner))
            chunk = [ln]
            j = i + 1
            while (j < len(raw) and raw[j].strip()
                   and not re.match(r"^\s*-\s*\[\[", raw[j])
                   and not raw[j].lstrip().startswith(("<!--", "#", "```"))):
                chunk.append(raw[j])
                j += 1
            lines_out.extend(chunk)
            i = j
    for p in parts:
        base = os.path.splitext(os.path.basename(p))[0]
        if base == os.path.splitext(os.path.basename(hub_path))[0] or base in listed:
            continue
        src = os.path.join(ROOT, p)
        age = dt.date.today() - dt.date.fromtimestamp(os.path.getmtime(src))
        # Penanda "tulis penjelasannya" WAJIB ada walau barisnya baru dibuat hari ini. Versi
        # sebelumnya hanya menandai berkas berumur >3 hari, jadi halaman yang baru ditulis hari ini
        # masuk ke peta sebagai tautan polos dan tidak pernah dapat penjelasan sama sekali.
        lines_out.append(f"- [[{rel(hub_path, p[:-3])}]] ← tulis penjelasannya"
                         + (f" · {age.days}h" if age.days > 3 else ""))
        print(f"  + bagian baru {p}")
    for line in list(lines_out):
        m = re.match(r"- \[\[([^\]|]+)", line)
        if not m:
            continue
        t = m.group(1).strip()
        # Titik referensi = folder hub itu sendiri, bukan root vault. Versi pertama memeriksa
        # ROOT/<nama>.md sehingga setiap tautan relatif ("01 - Briefing" di dalam 00-Overview)
        # diteriakkan sebagai berkas hilang: 50 baris alarm palsu per run, dan yang asli nanti
        # tenggelam di antaranya. Sekarang keduanya diuji terhadap ROOT (bukan cwd) - sama seperti
        # bug `md_files`, alarm yang bergantung pada direktori jalan adalah alarm yang tidak
        # akan dipercaya orang saat benar.
        hdir = os.path.dirname(hub_abs)
        cands = [os.path.join(ROOT, t + ".md"), os.path.join(hdir, t + ".md")]
        if not any(os.path.exists(c) for c in cands):
            print(f"  ! hub menunjuk berkas yang tidak ada ({hub_path}): {t}")
    body = ["## Bagian", ""] + lines_out
    tail = ["", "<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->"]
    if text and "```dataview" not in text:
        # HANYA kalau hub belum punya blok dataview. Versi sebelumnya selalu menempel satu blok baru
        # padahal pola penggantinya berhenti DI DEPAN blok lama -> tiap run meninggalkan salinan
        # `LIST FROM #...` tambahan; hub Testing akhirnya punya 6 blok.
        tail += ["", "```dataview", f"LIST FROM #{tag} SORT file.name ASC", "```"]
    if text is None:
        text = (f"---\ntags: [hub]\n---\n\n# {os.path.dirname(hub_path)}\n\n"
                "_(dibuat `sync_vault.py` — tulis paragraf pembuka: lapisan ini apa dan apa yang "
                "BUKAN dia)_\n")
    blk = "\n".join(body + tail) + "\n"
    if block:
        new = text[:block.start()] + blk.rstrip("\n") + "\n" + text[block.end():]
    else:
        new = text.rstrip() + "\n\n" + blk
    return new


def sync(write=True):
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    changed = 0
    for f in folders():
        parts = md_files(f)
        if not parts:
            print(f"  ! folder {f} tidak menghasilkan halaman - periksa ROOT/Path, jangan diabaikan")
            continue
        hub = hub_of(f) or os.path.join(f, "00 - Hub %s.md" % f.split("-", 1)[-1])
        # Semua jalur dari sini absolut: `hub_of` mengembalikan path RELATIF terhadap ROOT, dan
        # `open(hub)` relatif akan membaca/menulis di direktori jalan - termasuk MENCIPTA hub
        # palsu di cwd kalau cwd-nya bukan vault.
        hubp = hub if os.path.isabs(hub) else os.path.join(ROOT, hub.replace("/", os.sep))
        new = hub_body(hub, parts)
        text = open(hubp, encoding="utf-8").read() if os.path.exists(hubp) else None
        if new != text:
            changed += 1
            if write:
                open(hubp, "w", encoding="utf-8", newline="\n").write(new)
            print(("sync " if write else "akan sync ") + hub)
    top = md_files(ROOT)
    lines = ["---", "tags: [generated]", "---", "",
             f"_Auto-Index — {len(top)} halaman · {now} · dari `vault/scripts/sync_vault.py`_", ""]
    for f in folders():
        parts = md_files(f)
        if parts:
            lines.append(f"### {f} ({len(parts)})")
            lines += [f"- [[{rel('_Auto-Index.md', p[:-3])}]]" for p in parts] + [""]
    target = os.path.join(ROOT, "_Auto-Index.md")
    old = open(target, encoding="utf-8").read() if os.path.exists(target) else ""
    if "\n".join(lines) != old:
        changed += 1
        if write:
            open(target, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
        print(("sync " if write else "akan sync ") + "_Auto-Index.md")
    print(f"{'ditulis' if write else 'dilaporkan'}: {changed} berkas berubah.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="laporkan tanpa menulis")
    a = ap.parse_args()
    sync(write=not a.check)
