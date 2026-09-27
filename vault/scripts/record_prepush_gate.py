"""Pasang gerbang pra-push ke halaman pemiliknya (registry uji, harness, Conventions, F-D22, QRef).

Sekali-jalan; setiap pola wajib ketemu tepat satu kali, yang tidak ketemu dilaporkan, bukan dilewati.
"""
import io
import os
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isdir(os.path.join(VAULT, "00-Overview")):
    sys.exit(f"VAULT bukan folder vault: {VAULT}")

E = []

# ---- T1: registry perintah -------------------------------------------------------------
E.append(("07-Testing/01 - Test Commands.md",
 "| 8 | `python -X utf8 _research/check_garbled.py` *(workspace — di luar clone Fabius)* | 0 CJK/fullwidth/BOM di jalur yang diperiksa | teks masih terbaca di terminal Windows |",
 "| 8 | `python -X utf8 _research/check_garbled.py` *(workspace — di luar clone Fabius)* | 0 CJK/fullwidth/BOM di jalur yang diperiksa | teks masih terbaca di terminal Windows |\n"
 "| 9 | `python -X utf8 vault/scripts/prepush_check.py --self-test` | 6/6 kasus benar | detektor atribusi masih menangkap polanya |\n"
 "| 10 | `python -X utf8 vault/scripts/prepush_check.py` (sebelum **setiap** push) | `0 commit pada origin/master..HEAD -> lolos` | tidak ada commit yang akan dikirim membawa trailer atribusi AI |"))

E.append(("07-Testing/01 - Test Commands.md",
 "- ❌ Tidak ada satu pun angka di atas yang mengatakan **agen kami untung**. 39/63 = perilaku\n"
 "  kontrak, bukan hasil pasar.",
 "- ❌ Tidak ada satu pun angka di atas yang mengatakan **agen kami untung**. 39/63 = perilaku\n"
 "  kontrak, bukan hasil pasar.\n"
 "- ❌ Baris 9–10 menjaga **atribusi commit**, bukan bukti: `--all` pada 27 Sep menemukan tepat\n"
 "  **1** commit bermasalah dari **393** (`08cb049`) dan itu **sengaja ditinggalkan** — menghapusnya\n"
 "  berarti menulis ulang 147 hash (lihat [[00-Overview/03 - Decisions]] F-D22)."))

# ---- T5: harness -----------------------------------------------------------------------
E.append(("07-Testing/T5 - Integrity Harness.md",
 "python -X utf8 vault/scripts/hub_shape.py\npython -X utf8 _research/check_garbled.py",
 "python -X utf8 vault/scripts/hub_shape.py\npython -X utf8 vault/scripts/prepush_check.py --self-test\npython -X utf8 _research/check_garbled.py"))

E.append(("07-Testing/T5 - Integrity Harness.md",
 "- ✅ `Broken: 0` = setiap rujukan di vault menunjuk halaman yang benar-benar ada. Aturan yang\n"
 "  dipakai: **berkas yang tidak ditunjuk siapa-siapa adalah berkas yang tidak akan dibaca orang.**",
 "- ✅ `Broken: 0` = setiap rujukan di vault menunjuk halaman yang benar-benar ada. Aturan yang\n"
 "  dipakai: **berkas yang tidak ditunjuk siapa-siapa adalah berkas yang tidak akan dibaca orang.**\n"
 "- ✅ `prepush_check.py` = gerbang **pra-push**: memeriksa pesan commit pada `origin/master..HEAD`\n"
 "  dan keluar non-zero kalau ada trailer atribusi AI. Ia ikut jalan di Actions\n"
 "  (`.github/workflows/attribution-guard.yml`), jadi penegakannya tidak bergantung pada siapa\n"
 "  yang sedang menyetir. Terukur 27 Sep: 6/6 kasus self-test; `--all` = 1 pelanggaran / 393 commit.")

# ---- Conventions: aturan operasional ----------------------------------------------------
E.append(("Conventions.md",
 "- **Commit bukan tempat kredit alat.**",
 "- **Sebelum SETIAP push: kabari builder, lalu jalankan**\n"
 "  `python -X utf8 vault/scripts/prepush_check.py`. Kalau keluar non-zero, perbaiki pesan commitnya\n"
 "  dulu — jangan push. Alasannya konkret: dua commit sempat membawa trailer atribusi Claude ke repo\n"
 "  publik dan tidak ada satu pun pemeriksaan yang menegurnya; dan aturan yang cuma hidup di\n"
 "  `~/.qwen` laptop hilang saat mesin diganti, sedangkan yang ada di repo ikut ter-clone + ikut\n"
 "  dijalankan Actions.\n"
 "- **Commit bukan tempat kredit alat.**"))

# ---- F-D22 addendum ---------------------------------------------------------------------
E.append(("00-Overview/03 - Decisions.md",
 "**Terkait:** [[00-Overview/05 - Corrections]] · [[Conventions]] §Turunan ·\n[[09-Inbox/Session-2026-09-27-siang]]",
 "**Tambahannya hari itu juga (dicabut, bukan diperbaiki).** Percobaan pertama menegakkan aturan ini\n"
 "dengan *session hook* global (`~/.qwen/settings.json` -> `hooks.PreToolUse`). Path-nya kutulis\n"
 "berkutip; shell di mesin ini mengirim kutipnya sebagai bagian dari nama berkas, python keluar\n"
 "dengan kode 2, dan karena 2 = \"blokir\", **semua** tool tulis/terminal sesi itu tersumbat - bukan\n"
 "hanya guardnya yang mati, kerjanya juga. Builder menyuruh mencabutnya. Sekarang penegakannya\n"
 "berpindah tempat: aturan di `~/.qwen/QWEN.md` (instruksi), `vault/scripts/prepush_check.py`\n"
 "(perintah yang bisa dijalankan siapa pun, 6/6 self-test), dan `attribution-guard.yml` (jalan di\n"
 "server tiap push). Pelajaran yang lebih umum dari atribusinya: **gerbang yang menegakkan aturan\n"
 "harus gagal dengan cara yang tidak melumpuhkan pekerjaan** - dan harus diuji lewat jalur nyata\n"
 "tempat ia akan dipanggil, bukan cuma lewat logikanya.\n\n"
 "**Terkait:** [[00-Overview/05 - Corrections]] · [[Conventions]] §Turunan ·\n"
 "[[07-Testing/01 - Test Commands]] baris 9-10 · [[09-Inbox/Session-2026-09-27-siang]]"))

# ---- Quick-Reference --------------------------------------------------------------------
E.append(("Quick-Reference.md",
 "python -X utf8 -u universe/write_universe_manifest.py             # integritas dataset (sha256 per baris)",
 "python -X utf8 -u universe/write_universe_manifest.py             # integritas dataset (sha256 per baris)\n"
 "python -X utf8 vault/scripts/prepush_check.py                     # WAJIB sebelum push: cek trailer atribusi"))

bad = []
for rel, old, new in E:
    p = os.path.join(VAULT, rel.replace("/", os.sep))
    t = io.open(p, encoding="utf-8").read()
    c = t.count(old)
    if c != 1:
        bad.append(f"{rel}: {c}x -> {old[:52]!r}")
        continue
    io.open(p, "w", encoding="utf-8", newline="\n").write(t.replace(old, new, 1))
    print("ok  ", rel)

if bad:
    print("\n".join("!! " + b for b in bad))
    sys.exit(f"\n{len(bad)} dari {len(E)} tidak diterapkan.")
print(f"\n{len(E)} suntingan diterapkan.")
