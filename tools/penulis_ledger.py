"""P99 + P100 (F-D86 tahap 2+3): PENULIS `ledger/` pindah dari rantai GitHub `paper-ledger` ke job Railway; tick (opsional) dari REST beberapa menit
sesudah penutupan bar.

Isi tiap putaran = isi loop `.github/workflows/paper-ledger.yml`, urutan dan gerbangnya sama (tiap 5 menit):
  1. di jendela tick (vision 08:40-11:58Z | rest 00:02-11:58Z) sampai tick hari itu beres: [rest: baris bar hari itu dari REST - dua bacaan identik
     >= 60 s (SK-R1), funding aktual TIDAK (SK-R2)] -> `paper_tick.py --feed` (rc 0 beres / 4 coba lagi / lain = BERHENTI) -> `engine.cli ledger verify`
     (gagal = BERHENTI, tidak commit) -> `feed_tick.py` (peringatan saja) -> commit `ledger/paper ledger/bars [ledger/feed]` -> dorong (5 percobaan).
     Sesudah beres: `book epoch --write` + `book verify` -> commit `ledger/book`; `kertas_eksekusi.py run` -> commit `ledger/kertas` (gagal = peringatan);
  2. sesudah beres: `worker_watch.py --alert --ringkasan` sampai ia menilai, lalu picu web-snapshot.yml, validasi.yml, bot-review.yml;
  3. tiap putaran: `eksekusi_ledger.py run --alert --state` -> `verify` -> commit `ledger/eksekusi`; `periksa --alert`; `waitlist.py --poll`.
  Dorong = fetch + rebase ke ujung cabang, `ledger verify` LAGI bila hulu bergerak, perpanjang sewa kunci, push; ditolak = ulang (12 s, 5 kali).
  BERHENTI = di rantai GitHub `exit 1` lalu watchdog menyalakan mata rantai baru <= 20 menit kemudian; di sini: klon direset, Telegram, jeda 20 menit.
  Alat dijalankan dari KLON repo (sparse: engine tools ledger config deployments), bukan dari image: versi kodenya = HEAD cabang, sama dengan rantai.
  Funding REST selalu dimatikan untuk alat (`FABIUS_FUNDING_REST=0`, SK-R2); klon yang `feed_bars.py`-nya belum mengenal sakelar itu = tidak menulis.

Mode (PENULIS_MODE):
  mati            bawaan. Tidak menulis apa pun.
  bayangan-tulis  uji paralel di cabang PENULIS_CABANG_UJI (bawaan `penulis-uji`), TIDAK PERNAH master. Tanpa Telegram alat, tanpa daftar tunggu,
                  tanpa penjaga worker, tanpa memicu workflow. Tiap putaran: catatan yang ditulis cabang uji dibandingkan dengan catatan resmi master
                  (tick: targets, data_hash, signal_ids, n_aset -> IDENTIK / BEDA; bar: baris per waktu) - sama dengan `bandingkan` di bawah.
  master          penulis resmi, HANYA bila semua syarat penulis tunggal terpenuhi (diperiksa tiap putaran; tak terbaca = tidak menulis):
                  (1) `config/penulis-ledger.json` di cabang berkata "penulis": "railway"; (2) workflow paper-ledger.yml TIDAK aktif dan tidak ada run-nya
                  yang jalan/antre (API GitHub); (3) sewa kunci `refs/penulis/kunci-master` dipegang proses ini.
Sumber (PENULIS_SUMBER): vision (tahap 2, bawaan: sama persis dengan rantai GitHub) | rest (tahap 3: baris REST, lalu sesudah zip Vision terbit baris
  itu dibandingkan dengan Vision -> SAMA / ALARM; tidak ada yang ditimpa, append-only).
Kunci: ref `refs/penulis/kunci-<cabang>` = satu commit yatim berisi kunci.json (pemegang, sampai). Diambil / diperpanjang dengan
  `push --force-with-lease=<ref>:<sha yang dibaca>` (bandingkan-dan-tukar di server git): dua proses tidak bisa sama-sama memegangnya. Sewa 20 menit,
  diperpanjang tiap putaran dan sebelum tiap push, dilepas saat SIGTERM. Ref di luar refs/heads: tidak memicu workflow / pratinjau Vercel.
Token: PENULIS_GITHUB_TOKEN (fine-grained, repo ini saja: Contents RW + Actions RW). Tidak pernah di baris perintah atau log: git menerimanya lewat
  GIT_CONFIG_* (http.extraheader, cara actions/checkout), API lewat header; keluaran disaring; alat anak TIDAK mewarisinya (eksekusi_ledger
  membaca Gist lewat URL raw publik tanpa token).

Pakai:
  Railway (service sendiri):  FABIUS_JOB=penulis_ledger  PENULIS_MODE=bayangan-tulis|master  PENULIS_SUMBER=vision|rest  (+ PENULIS_GITHUB_TOKEN)
  Lokal:  python -X utf8 tools/penulis_ledger.py siapa [--ref FETCH_HEAD]   # penulis menurut config (dipakai workflow; galat apa pun = github)
          python -X utf8 tools/penulis_ledger.py syarat                     # syarat penulis tunggal saat ini, hanya baca (token opsional)
          python -X utf8 tools/penulis_ledger.py bandingkan [--resmi origin/master] [--uji origin/penulis-uji]
Runbook alih + balik: vault/04-Tools/TL47.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from typing import Callable, Dict, List, Optional, Sequence, Tuple

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

TOKEN_ENV = "PENULIS_GITHUB_TOKEN"
CONFIG_REL = "config/penulis-ledger.json"
PENULIS = ("github", "railway")
MODES = ("mati", "bayangan-tulis", "master")
SUMBER = ("vision", "rest")
WORKFLOW, WATCHDOG = "paper-ledger.yml", "paper-ledger-watchdog.yml"
DISPATCH = ("web-snapshot.yml", "validasi.yml", "bot-review.yml")
RUN_HIDUP = ("in_progress", "queued", "waiting", "pending", "requested")
SPARSE = ("engine", "tools", "ledger", "config", "deployments")
JENDELA = {"vision": (840, 1158), "rest": (2, 1158)}         # HHMM UTC, sama dengan rantai (vision); rest mulai +2 menit sesudah penutupan (P98)
SAKELAR_FUNDING = "FABIUS_FUNDING_REST"
POLL_S = int(os.environ.get("POLL_S", "300"))
PUSH_TRIES, PUSH_SLEEP_S = 5, 12
KUNCI_TTL_S = 1200
KUNCI_PREFIX = os.environ.get("PENULIS_KUNCI_PREFIX", "refs/penulis/kunci-")   # di luar refs/heads: bukan cabang (tanpa workflow / pratinjau Vercel)
BERHENTI_S = 1200
ALAT_TIMEOUT_S = 1800
VISION_PALING_CEPAT_S = 8 * 3600                              # zip Vision terbit ±08:40-09:40Z: sebelum itu tidak ada yang bisa dibandingkan
VISION_JEDA_S = 1800
VISION_MENYERAH_S = 2 * 86400                                # baris REST yang belum bisa dibandingkan dengan Vision sesudah 2 hari = dicatat TIDAK TERUJI
GITHUB = "https://github.com/"
API = "https://api.github.com"
REPO = os.environ.get("FABIUS_REPO", "https://github.com/Shenhan01-sys/Fabius.git")
CABANG_RESMI = os.environ.get("FABIUS_BRANCH", "master")


class GitError(RuntimeError):
    pass


def log(msg: str) -> None:
    print(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}", flush=True)


def baca(path: str) -> Optional[str]:
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


def utc(ms: int) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ms / 1000))


def hari(ms: int) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(ms / 1000))


def _header(token: str) -> str:
    return base64.b64encode(f"x-access-token:{token}".encode()).decode()


def saring(text: str, token: str) -> str:
    """Token dan bentuk base64 header-nya diganti sebelum teks apa pun dicetak."""
    if not token or not text:
        return text
    return text.replace(token, "<rahasia>").replace(_header(token), "<rahasia>")


def git_env(token: str = "", base: Optional[dict] = None) -> dict:
    """Lingkungan git: token (bila ada) hanya sebagai http.extraheader lewat GIT_CONFIG_* - tidak pernah di argumen (terlihat di `ps`) atau URL remote."""
    env = dict(os.environ if base is None else base)
    for k in (TOKEN_ENV, "GH_TOKEN", "GITHUB_TOKEN"):
        env.pop(k, None)
    env["GIT_TERMINAL_PROMPT"] = "0"
    if token:
        env.update({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": f"http.{GITHUB}.extraheader",
                    "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {_header(token)}"})
    return env


def repo_slug(url: str) -> Optional[str]:
    if not url.startswith(GITHUB):
        return None
    s = url[len(GITHUB):].rstrip("/")
    return s[:-4] if s.endswith(".git") else s


def penulis_dari(teks: Optional[str]) -> Optional[str]:
    """Isi config -> 'github' | 'railway' | None (tak terbaca / nilai lain)."""
    try:
        p = json.loads(teks or "").get("penulis")
    except (ValueError, AttributeError):
        return None
    return p if p in PENULIS else None


def siapa(teks: Optional[str]) -> str:
    """Untuk workflow GitHub: config yang tak terbaca = 'github' (perilaku lama). Penulis Railway memakai `penulis_dari` (tak terbaca = tidak menulis)."""
    return penulis_dari(teks) or "github"


def di_jendela(now_ms: int, sumber: str) -> bool:
    hm = int(time.strftime("%H%M", time.gmtime(now_ms / 1000)))
    lo, hi = JENDELA[sumber]
    return lo <= hm <= hi


def pemegang_bawaan() -> str:
    e = os.environ
    host = e.get("RAILWAY_SERVICE_NAME") or socket.gethostname()
    dep = (e.get("RAILWAY_DEPLOYMENT_ID") or "")[:8]
    rep = (e.get("RAILWAY_REPLICA_ID") or "")[:8]
    return f"{host}:{dep}:{rep}" if dep else f"{host}:{os.getpid()}"


# ---------------------------------------------------------------- git
class Git:
    def __init__(self, cwd: str, token: str = "", timeout: int = 300):
        self.cwd, self.token, self.timeout = cwd, token, timeout
        self.env = git_env(token)

    def _run(self, args: Sequence[str], cwd: Optional[str], inp: Optional[str]):
        # byte, bukan mode teks: di Windows mode teks mengubah "\n" stdin menjadi "\r\n" (mktree lalu menamai berkas "kunci.json\r")
        r = subprocess.run(["git", *args], cwd=cwd or self.cwd, env=self.env, input=None if inp is None else inp.encode("utf-8"),
                           capture_output=True, timeout=self.timeout)
        dec = lambda b: b.decode("utf-8", "replace") if isinstance(b, bytes) else (b or "")      # noqa: E731
        return subprocess.CompletedProcess(r.args, r.returncode, dec(r.stdout), dec(r.stderr))

    def run(self, *args: str, cwd: Optional[str] = None, inp: Optional[str] = None) -> str:
        r = self._run(args, cwd, inp)
        if r.returncode != 0:
            raise GitError(f"git {args[0]} gagal ({r.returncode}): {saring((r.stderr or r.stdout).strip(), self.token)[:300]}")
        return r.stdout.strip()

    def coba(self, *args: str, cwd: Optional[str] = None) -> bool:
        return self._run(args, cwd, None).returncode == 0

    def rev(self, ref: str) -> str:
        r = self._run(("rev-parse", "-q", "--verify", ref), None, None)
        return r.stdout.strip() if r.returncode == 0 else ""

    def isi(self, ref: str, path: str) -> Optional[str]:
        r = self._run(("show", f"{ref}:{path}"), None, None)
        return r.stdout if r.returncode == 0 else None

    def daftar(self, ref: str, folder: str) -> Dict[str, str]:
        """{nama berkas: sha blob} di folder pada ref (sha sama = isi sama, tidak perlu dibaca)."""
        r = self._run(("ls-tree", ref, folder.rstrip("/") + "/"), None, None)
        out = {}
        for line in (r.stdout.splitlines() if r.returncode == 0 else []):
            meta, _, path = line.partition("\t")
            parts = meta.split()
            if len(parts) == 3 and parts[1] == "blob":
                out[path.rsplit("/", 1)[-1]] = parts[2]
        return out


class Kunci:
    """Sewa kunci penulis di ref git remote (bandingkan-dan-tukar lewat --force-with-lease)."""

    def __init__(self, git: Git, cabang: str, pemegang: str, mode: str, ttl_s: int = KUNCI_TTL_S):
        self.git, self.cabang, self.pemegang, self.mode, self.ttl_s = git, cabang, pemegang, mode, ttl_s
        self.ref = f"{KUNCI_PREFIX}{cabang}"
        self.sha: Optional[str] = None

    def baca(self) -> Tuple[Optional[str], dict]:
        out = self.git.run("ls-remote", "origin", self.ref)
        sha = next((ln.split()[0] for ln in out.splitlines() if ln.split()[-1] == self.ref), None)
        if sha is None:
            return None, {}
        self.git.run("fetch", "-q", "--no-tags", "origin", self.ref)
        try:
            return sha, json.loads(self.git.run("show", f"{sha}:kunci.json"))
        except (GitError, ValueError):
            return sha, {}

    def ambil(self, now_ms: int) -> Tuple[bool, str]:
        try:
            sha, cur = self.baca()
        except GitError as e:
            return False, f"kunci tak terbaca ({e}) - tidak menulis"
        if sha and cur.get("pemegang") != self.pemegang and int(cur.get("sampai_ms") or 0) > now_ms:
            return False, f"kunci {self.ref} dipegang {cur.get('pemegang')} ({cur.get('mode')}) sampai {cur.get('sampai_utc')}"
        sampai = now_ms + self.ttl_s * 1000
        isi = {"pemegang": self.pemegang, "mode": self.mode, "cabang": self.cabang, "sampai_ms": sampai, "sampai_utc": utc(sampai),
               "diperbarui_utc": utc(now_ms)}
        try:
            blob = self.git.run("hash-object", "-w", "--stdin", inp=json.dumps(isi, sort_keys=True, indent=1) + "\n")
            tree = self.git.run("mktree", inp=f"100644 blob {blob}\tkunci.json\n")
            c = self.git.run("commit-tree", tree, "-m", f"kunci penulis ledger {self.pemegang} sampai {utc(sampai)} [skip ci]")
        except GitError as e:
            return False, f"kunci tak bisa disusun ({e})"
        if not self.git.coba("push", "-q", f"--force-with-lease={self.ref}:{sha or ''}", "origin", f"{c}:{self.ref}"):
            return False, f"kunci {self.ref} direbut proses lain di antara baca dan tulis (push ditolak)"
        baru = cur.get("pemegang") != self.pemegang or not sha
        self.sha = c
        return True, f"kunci {self.ref} {'diambil' if baru else 'diperpanjang'} sampai {utc(sampai)}"

    def lepas(self) -> bool:
        if not self.sha:
            return False
        ok = self.git.coba("push", "-q", f"--force-with-lease={self.ref}:{self.sha}", "origin", f":{self.ref}")
        self.sha = None
        return ok


# ---------------------------------------------------------------- API GitHub
class GitHubApi:
    def __init__(self, slug: str, token: str = "", call: Callable = None):
        self.slug, self.token = slug, token
        self.call = call or self._http

    def _http(self, method: str, path: str, body=None) -> Tuple[int, object]:
        h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "fabius-penulis-ledger"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(API + path, data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                return r.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as e:
            return e.code, None

    def get(self, path: str):
        code, obj = self.call("GET", path, None)
        if code != 200 or obj is None:
            raise RuntimeError(f"GET {path.split('?')[0]} -> HTTP {code}")
        return obj

    def dispatch(self, wf: str, ref: str) -> bool:
        code, _ = self.call("POST", f"/repos/{self.slug}/actions/workflows/{wf}/dispatches", {"ref": ref})
        return code == 204


def syarat_rantai_github(api: GitHubApi) -> Tuple[bool, str]:
    """SK-R3: rantai GitHub mati DULU. Aman hanya bila workflow paper-ledger tidak aktif DAN tidak ada run-nya yang hidup. Tak terbaca = tidak aman."""
    base = f"/repos/{api.slug}/actions/workflows"
    try:
        state = api.get(f"{base}/{WORKFLOW}").get("state")
        runs = api.get(f"{base}/{WORKFLOW}/runs?per_page=20").get("workflow_runs") or []
        wd = api.get(f"{base}/{WATCHDOG}").get("state")
    except Exception as e:  # noqa: BLE001 - gagal = tertutup
        return False, f"API GitHub tak terbaca ({saring(str(e), api.token)[:160]}) - tidak menulis (gagal = tertutup)"
    if state not in ("disabled_manually", "disabled_inactivity"):
        return False, f"workflow {WORKFLOW} berstatus {state!r} - SK-R3: rantai GitHub dimatikan DULU (gh workflow disable {WORKFLOW})"
    hidup = [r for r in runs if r.get("status") in RUN_HIDUP]
    if hidup:
        return False, f"{len(hidup)} run paper-ledger masih hidup ({', '.join(str(r.get('id')) + ':' + str(r.get('status')) for r in hidup[:3])}) - tunggu"
    return True, f"workflow paper-ledger {state}, tidak ada run hidup" + ("; watchdog masih AKTIF (matikan juga)" if wd == "active" else "")


# ---------------------------------------------------------------- pembandingan (cabang uji vs master; juga perintah `bandingkan`)
def baca_jsonl(teks: Optional[str]) -> List[dict]:
    return [json.loads(ln) for ln in (teks or "").splitlines() if ln.strip()]


def bandingkan_ledger(uji: List[dict], resmi: List[dict]) -> List[Tuple[int, str, List[str], Optional[int], Optional[int]]]:
    """Catatan tick/gap yang DITULIS cabang uji (hash tidak ada di resmi; catatan warisan bersama tidak dihitung sebagai bukti) vs catatan resmi
    asof yang sama. -> [(asof, vonis, kolom beda, lag uji, lag resmi)]. Tambahan: tick resmi sesudah titik cabang yang tidak ditulis uji."""
    import shadow_tick as st
    hres = {r.get("h") for r in resmi}
    by = {r["asof"]: r for r in resmi if r.get("type") in ("tick", "gap")}
    fork = titik_cabang(uji, resmi)
    out, seen = [], set()
    for r in uji:
        if r.get("h") in hres or r.get("type") not in ("tick", "gap"):
            continue
        off = by.get(r["asof"])
        seen.add(r["asof"])
        if r["type"] == "gap":
            v, diff = ("MENUNGGU" if off is None else "SAMA-SAMA GAP" if off["type"] == "gap" else "UJI GAP, RESMI TICK"), []
        else:
            v, diff = st.compare_tick(r, off)
        out.append((r["asof"], v, diff, r.get("lag_s"), off.get("lag_s") if off else None))
    for asof, off in sorted(by.items()):
        if fork is not None and asof > fork and asof not in seen:
            out.append((asof, "RESMI ADA, UJI BELUM MENULIS", [], None, off.get("lag_s")))
    return sorted(out, key=lambda x: x[0])


def titik_cabang(uji: List[dict], resmi: List[dict]) -> Optional[int]:
    """asof tick/gap bersama terakhir (catatan warisan, hash sama) = bar terakhir sebelum kedua penulis berjalan sendiri-sendiri."""
    hres = {r.get("h") for r in resmi}
    shared = [r["asof"] for r in uji if r.get("h") in hres and r.get("type") in ("tick", "gap")]
    return max(shared) if shared else None


def _csv_rows(teks: Optional[str]) -> Dict[int, List[str]]:
    out = {}
    for ln in (teks or "").splitlines():
        cols = ln.strip().split(",")
        if cols and cols[0].isdigit():
            out[int(cols[0])] = cols
    return out


def bandingkan_bars(git: Git, resmi: str, uji: str, sejak: Optional[int]) -> dict:
    """Baris bar dengan waktu >= `sejak` (bar sesudah titik cabang: baris yang ditulis masing-masing penulis sendiri) di kedua cabang. Kolom = float."""
    ru, rr = git.daftar(uji, "ledger/bars"), git.daftar(resmi, "ledger/bars")
    res = {"sama": 0, "beda": [], "uji_saja": 0, "resmi_saja": 0}
    lo = -1 if sejak is None else sejak
    for name in sorted(ru):
        if not name.endswith(".csv"):
            continue
        u = _csv_rows(git.isi(uji, f"ledger/bars/{name}"))
        r = _csv_rows(git.isi(resmi, f"ledger/bars/{name}")) if name in rr else {}
        for t in sorted(set(u) | set(r)):
            if t < lo:
                continue
            if t not in r:
                res["uji_saja"] += 1
            elif t not in u:
                res["resmi_saja"] += 1
            elif [float(x) for x in u[t][1:]] == [float(x) for x in r[t][1:]]:
                res["sama"] += 1
            else:
                res["beda"].append(f"{name} {hari(t)}: uji {','.join(u[t][1:])} resmi {','.join(r[t][1:])}")
    return res


def bandingkan_ref(git: Git, resmi: str, uji: str, label: str = "penulis-uji") -> Tuple[List[str], bool]:
    """-> (baris vonis, ada beda?) untuk semua bot di ledger/paper cabang uji."""
    lines, beda, forks = [], False, []
    rr = git.daftar(resmi, "ledger/paper")
    for name in sorted(git.daftar(uji, "ledger/paper")):
        if not name.endswith(".jsonl"):
            continue
        u = baca_jsonl(git.isi(uji, f"ledger/paper/{name}"))
        r = baca_jsonl(git.isi(resmi, f"ledger/paper/{name}")) if name in rr else []
        f = titik_cabang(u, r)
        if f is not None:
            forks.append(f)
        for asof, v, diff, lu, lr in bandingkan_ledger(u, r):
            beda |= v in ("BEDA", "UJI GAP, RESMI TICK")
            lag = (f" | uji {lu / 60:.1f} menit vs resmi {lr / 3600:.1f} jam sesudah penutupan" if lu is not None and lr is not None else "")
            lines.append(f"VONIS {label} {name[:-6]} {hari(asof)}: {v}" + (f" ({', '.join(diff)})" if diff else "") + lag)
    b = bandingkan_bars(git, resmi, uji, max(forks) + 86_400_000 if forks else None)      # baris bar hari titik cabang (estimasi 08/16Z) = warisan
    beda |= bool(b["beda"])
    lines.append(f"VONIS baris bar {label}: {'ALARM - ' if b['beda'] else ''}{b['sama']} sama persis, {len(b['beda'])} beda, "
                 f"{b['uji_saja']} hanya di uji (resmi belum), {b['resmi_saja']} hanya di resmi")
    lines += [f"  ! {x}" for x in b["beda"][:20]]
    return lines, beda


# ---------------------------------------------------------------- pemeriksa baris REST vs Vision (P100, setara SK-R4 bayangan)
def vision_ulang(bars: str, rows: Dict[str, list], day_ms: int, tmp: str) -> str:
    """Salinan bar dengan baris hari `day_ms` (dan sesudahnya) pada deret REST dicabut, lalu diisi ulang dari zip Vision oleh `feed_bars` (kode yang
    sama dengan rantai). Baris yang belum terbit = tidak ada di salinan (compare_rows: menunggu)."""
    import feed_bars as fb
    from engine.series import DAY_MS
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    shutil.copytree(bars, tmp)
    for key in rows:
        kind, sym = key.split(":")
        p = os.path.join(tmp, f"fund_est_{sym}.csv" if kind == "fest" else f"{kind}_{sym}_1d.csv")
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            keep = [ln for ln in f if not (ln.split(",")[0].isdigit() and int(ln.split(",")[0]) >= day_ms)]
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.writelines(keep)
    for key in rows:
        kind, sym = key.split(":")
        if kind == "fest":
            fb.update_funding_est(tmp, sym, day_ms + DAY_MS)
        else:
            fb.update_klines(tmp, kind, sym, day_ms + DAY_MS)
    return tmp


# ---------------------------------------------------------------- penulis
class Penulis:
    def __init__(self, mode: str, sumber: str, remote: str, workdir: str, token: str = "", api: Optional[GitHubApi] = None, alerter=None,
                 log: Callable[[str], None] = log, sleep: Callable[[float], None] = time.sleep, now_fn: Callable[[], int] = None,
                 cabang_resmi: str = CABANG_RESMI, cabang_uji: str = "penulis-uji", pemegang: Optional[str] = None, rest_src=None,
                 est_fn: Callable = None, vision_fn: Callable = vision_ulang, python: str = sys.executable,
                 git_nama: str = "paper-ledger-railway", git_email: str = "paper-ledger-railway@users.noreply.github.com"):
        if mode not in MODES or sumber not in SUMBER:
            raise ValueError(f"PENULIS_MODE {mode!r} / PENULIS_SUMBER {sumber!r} tidak dikenal ({'|'.join(MODES)} ; {'|'.join(SUMBER)})")
        self.cabang = cabang_resmi if mode == "master" else cabang_uji
        if mode != "master" and self.cabang == cabang_resmi:
            raise ValueError(f"mode {mode} tidak boleh menulis ke cabang resmi {cabang_resmi!r}")
        self.mode, self.sumber, self.remote, self.workdir, self.token = mode, sumber, remote, workdir, token
        self.cabang_resmi, self.api, self.log, self.sleep = cabang_resmi, api, log, sleep
        self.now_fn = now_fn or (lambda: int(time.time() * 1000))
        self.alert = alerter
        self.rest_src, self.est_fn, self.vision_fn, self.python = rest_src, est_fn, vision_fn, python
        self.git_nama, self.git_email = git_nama, git_email
        self.klon = os.path.join(workdir, "repo")
        self.git = Git(self.klon, token)
        self.kunci = Kunci(self.git, self.cabang, pemegang or pemegang_bawaan(), mode)
        self.selesai: Optional[str] = None
        self.dijaga: Optional[str] = None
        self.berhenti_sampai = 0
        self.k = 0
        self._remote_ada: Dict[str, bool] = {}
        self._tolak_terakhir: Tuple[str, float] = ("", 0.0)
        self._banding: Optional[Tuple[str, str]] = None
        self._vonis: set = set()
        self.rest_dir = os.path.join(workdir, "rest-baris")
        self._vision_t = 0

    # ---- kabar
    def kabar(self, key: str, text: str, sekali: bool = False) -> None:
        if self.alert is not None:
            self.alert.send(key, text, sekali=sekali)

    # ---- git
    def remote_punya(self, cabang: str) -> bool:
        if self._remote_ada.get(cabang):
            return True
        out = self.git.run("ls-remote", "--heads", self.remote, cabang, cwd=self.workdir)
        ada = any(ln.split()[-1] == f"refs/heads/{cabang}" for ln in out.splitlines())
        self._remote_ada[cabang] = ada
        return ada

    def siapkan(self) -> str:
        """Klon dangkal + sparse sekali (cabang tulis; untuk cabang uji yang belum ada: dari master lalu cabang lokal baru). -> sha HEAD."""
        os.makedirs(self.workdir, exist_ok=True)
        if not os.path.isdir(os.path.join(self.klon, ".git")):
            if os.path.exists(self.klon):
                shutil.rmtree(self.klon)
            base = self.cabang if self.remote_punya(self.cabang) else self.cabang_resmi
            self.git.run("clone", "-q", "--depth", "1", "--filter=blob:none", "--sparse", "--no-tags", "--branch", base, self.remote, self.klon,
                         cwd=self.workdir)
            self.git.run("sparse-checkout", "set", *SPARSE)
            if base != self.cabang:
                self.git.run("checkout", "-q", "-B", self.cabang)
            self.git.run("config", "user.name", self.git_nama)
            self.git.run("config", "user.email", self.git_email)
            self.log(f"klon {self.cabang} dari {base} di {self.klon}")
        return self.git.run("rev-parse", "HEAD")

    def dasar(self) -> str:
        return f"origin/{self.cabang if self.remote_punya(self.cabang) else self.cabang_resmi}"

    def tarik(self) -> bool:
        """`git pull --rebase` versi refspec eksplisit (klon satu cabang). False = rebase bentrok (sudah di-abort)."""
        if not self.remote_punya(self.cabang):
            return True
        c = self.cabang
        self.git.run("fetch", "-q", "--no-tags", "origin", f"+refs/heads/{c}:refs/remotes/origin/{c}")
        if self.git.coba("rebase", "-q", f"origin/{c}"):
            return True
        self.git.coba("rebase", "--abort")
        return False

    def reset_keras(self) -> None:
        self.git.coba("rebase", "--abort")
        self.git.coba("reset", "-q", "--hard", self.dasar())
        self.git.coba("clean", "-fdq", "ledger")

    def buang(self, path: str) -> None:
        self.git.coba("checkout", "-q", "--", path)
        self.git.coba("clean", "-fdq", path)

    # ---- alat (dari klon)
    def env_alat(self) -> dict:
        env = git_env("")
        for k in ("GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0"):
            env.pop(k, None)
        env[SAKELAR_FUNDING] = "0"
        env["PYTHONUTF8"], env["PYTHONUNBUFFERED"] = "1", "1"
        if self.mode != "master":                              # uji paralel: tidak boleh mengirim Telegram dari alat (kanal milik rantai resmi)
            env.pop("ALERT_TELEGRAM_TOKEN", None)
            env.pop("ALERT_TELEGRAM_CHAT", None)
        return env

    def alat(self, args: Sequence[str], tampil: bool = True) -> Tuple[int, str]:
        try:
            r = subprocess.run([self.python, "-u", "-X", "utf8", *args], cwd=self.klon, env=self.env_alat(), capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=ALAT_TIMEOUT_S)
            rc, out = r.returncode, saring((r.stdout or "") + (r.stderr or ""), self.token)
        except subprocess.TimeoutExpired:
            rc, out = 124, f"waktu habis {ALAT_TIMEOUT_S} s"
        if tampil:
            for ln in out.rstrip().splitlines():
                self.log("  | " + ln)
        return rc, out

    # ---- syarat penulis tunggal
    def sakelar_funding_ada(self) -> bool:
        p = os.path.join(self.klon, "tools", "feed_bars.py")
        return SAKELAR_FUNDING in (baca(p) or "")

    def syarat(self) -> Tuple[bool, str]:
        if self.mode == "mati":
            return False, "PENULIS_MODE=mati"
        if not self.sakelar_funding_ada():
            return False, f"tools/feed_bars.py di cabang belum mengenal {SAKELAR_FUNDING}: funding aktual REST akan mendahului estimasi (SK-R2)"
        if self.mode == "master":
            p = penulis_dari(baca(os.path.join(self.klon, CONFIG_REL)))
            if p != "railway":
                return False, f"{CONFIG_REL} berkata {p or 'tak terbaca'!s} - penulis resmi masih rantai GitHub"
            if self.api is None:
                return False, "tanpa API GitHub status rantai tak terbaca - tidak menulis"
            ok, why = syarat_rantai_github(self.api)
            if not ok:
                return False, why
        return self.kunci.ambil(self.now_fn())

    def tolak(self, why: str) -> str:
        last, t = self._tolak_terakhir
        if why != last or time.time() - t >= 3600:
            self.log(f"TIDAK MENULIS: {why}")
            self._tolak_terakhir = (why, time.time())
            if self.mode == "master":
                self.kabar("tolak:" + why[:50], f"penulis ledger ({self.mode}) TIDAK menulis: {why}", sekali=True)
        return "tolak"

    def henti(self, alasan: str) -> str:
        self.log(f"GALAT: {alasan} - penulis BERHENTI {BERHENTI_S // 60} menit (setara exit 1 + watchdog di rantai GitHub); klon direset")
        self.kabar("berhenti:" + alasan[:50], f"penulis ledger ({self.mode}, {self.cabang}) BERHENTI: {alasan}")
        self.reset_keras()
        self.berhenti_sampai = self.now_fn() + BERHENTI_S * 1000
        return "berhenti"

    # ---- commit + dorong
    def verify(self) -> bool:
        rc, _ = self.alat(["-m", "engine.cli", "ledger", "verify"])
        return rc == 0

    def dorong(self, label: str) -> str:
        """-> 'ok' | 'gagal' (5x ditolak) | 'verify' (ledger tak sah sesudah menarik hulu) | 'kunci' (sewa hilang)."""
        assert self.mode == "master" or self.cabang != self.cabang_resmi
        for t in range(1, PUSH_TRIES + 1):
            ok_k, why_k = self.kunci.ambil(self.now_fn())
            if not ok_k:
                self.log(f"push {label}DIBATALKAN: {why_k}")
                return "kunci"
            sebelum = self.git.rev(f"origin/{self.cabang}")
            if self.tarik():
                sesudah = self.git.rev(f"origin/{self.cabang}")
                if sesudah != sebelum and not self.verify():
                    return "verify"
                if self.git.coba("push", "-q", "origin", f"HEAD:refs/heads/{self.cabang}"):
                    self._remote_ada[self.cabang] = True
                    self.git.coba("fetch", "-q", "--no-tags", "origin", f"+refs/heads/{self.cabang}:refs/remotes/origin/{self.cabang}")
                    self.log(f"push {label}OK (percobaan {t})")
                    return "ok"
            self.log(f"push {label}ditolak (percobaan {t})")
            self.sleep(PUSH_SLEEP_S)
        return "gagal"

    def komit(self, paths: Sequence[str], pesan: str, label: str) -> str:
        """-> 'kosong' | hasil `dorong`."""
        for p in paths:
            if os.path.exists(os.path.join(self.klon, p)):
                self.git.run("add", p)
        if self.git.coba("diff", "--cached", "--quiet"):
            return "kosong"
        self.git.run("commit", "-q", "-m", f"{pesan} {utc(self.now_fn())} [skip ci]")
        return self.dorong(label)

    # ---- P100: baris hari ini dari REST
    def isi_rest(self) -> str:
        import shadow_tick as st
        from engine import ledger
        from engine.series import DAY_MS
        now = self.now_fn()
        bars = os.path.join(self.klon, "ledger", "bars")
        d = ledger.last_closed_bar(now)
        lag = now - (d + DAY_MS)
        if lag < st.FIRST_READ_S * 1000:
            return "terlalu-dini"
        if not st.needs_rest(bars, d):
            return "lengkap"
        if self.rest_src is None:
            self.rest_src = st.RestSource()
        got = st.read_final(self.rest_src, bars, d, self.now_fn, self.sleep, self.log)
        if got is None:
            return "tunda"
        snap, n = got
        rows, problems = st.build_rows(snap, bars, d, self.est_fn)
        if problems and lag < st.PROBLEM_WAIT_S * 1000:
            self.log(f"REST {hari(d)}: TUNDA - " + "; ".join(problems[:4]))
            return "tunda"
        n_rows = st.append_rows(bars, rows)
        os.makedirs(self.rest_dir, exist_ok=True)
        with open(os.path.join(self.rest_dir, f"{hari(d)}.json"), "w", encoding="utf-8") as f:
            json.dump({"bar": d, "ditulis_ms": now, "rows": rows}, f)
        self.log(f"REST {hari(d)}: {n_rows} baris ditambahkan ke ledger/bars ({n} bacaan identik, {lag // 1000} s sesudah penutupan"
                 + (f"; {len(problems)} deret berhenti: " + "; ".join(problems[:3]) if problems else "") + ")")
        return "diisi"

    def cek_vision(self) -> List[str]:
        """Baris REST yang sudah dikomit vs zip Vision (sesudah terbit). Beda = ALARM, tidak ada yang ditimpa (append-only; manusia memutuskan)."""
        import shadow_tick as st
        from engine.series import DAY_MS
        out = []
        now = self.now_fn()
        if not os.path.isdir(self.rest_dir) or now - self._vision_t < VISION_JEDA_S * 1000:
            return out
        self._vision_t = now
        for name in sorted(os.listdir(self.rest_dir)):
            p = os.path.join(self.rest_dir, name)
            with open(p, encoding="utf-8") as f:
                rec = json.load(f)
            if now - (rec["bar"] + DAY_MS) < VISION_PALING_CEPAT_S * 1000:
                continue
            rows = {k: [tuple(x) for x in v] for k, v in rec["rows"].items()}
            tmp = tempfile.mkdtemp(prefix="penulis-vision-")
            try:
                c = st.compare_rows(rows, self.vision_fn(os.path.join(self.klon, "ledger", "bars"), rows, rec["bar"], os.path.join(tmp, "bars")))
            except Exception as e:  # noqa: BLE001 - jaringan / berkas: diulang putaran berikut
                self.log(f"cek Vision {name[:-5]}: belum bisa ({type(e).__name__}: {str(e)[:120]})")
                continue
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
            if c["menunggu"]:
                if self.now_fn() - rec["ditulis_ms"] > VISION_MENYERAH_S * 1000:
                    line = f"VONIS baris REST vs Vision {name[:-5]}: TIDAK TERUJI ({c['menunggu']} baris Vision tak kunjung terbit)"
                    self.log(line)
                    out.append(line)
                    os.remove(p)
                continue
            alarm = c["beda_harga"] or c["beda_estimasi"]
            line = (f"VONIS baris REST vs Vision {name[:-5]}: {'ALARM - ' if alarm else ''}{c['sama']} sama persis, beda harga {len(c['beda_harga'])}, "
                    f"beda estimasi funding {len(c['beda_estimasi'])}, beda volume saja {c['beda_volume']}")
            self.log(line)
            for x in (c["beda_harga"] + c["beda_estimasi"])[:20]:
                self.log("  ! " + x)
            out.append(line)
            self.kabar("vision:" + name, line, sekali=True)
            os.remove(p)
        return out

    # ---- bayangan: bandingkan dengan master
    def bandingkan(self) -> List[str]:
        r = self.cabang_resmi
        self.git.run("fetch", "-q", "--depth", "1", "--no-tags", "origin", f"+refs/heads/{r}:refs/remotes/origin/{r}")
        key = (self.git.run("rev-parse", f"origin/{r}"), self.git.run("rev-parse", "HEAD"))
        if key == self._banding:
            return []
        self._banding = key
        lines, _ = bandingkan_ref(self.git, f"origin/{r}", "HEAD", label=self.cabang)
        baru = [ln for ln in lines if ln not in self._vonis and (ln.startswith(f"VONIS {self.cabang} ") and "MENUNGGU" not in ln
                                                                  and "BELUM" not in ln or "ALARM" in ln)]
        for ln in lines:
            if ln not in self._vonis:
                self.log(ln)
        for ln in baru:
            self.kabar("vonis:" + ln[:90], ln, sekali=True)
        self._vonis |= set(lines)
        return lines

    # ---- satu putaran (= satu iterasi loop rantai GitHub)
    def putaran(self) -> str:
        now = self.now_fn()
        if now < self.berhenti_sampai:
            return "berhenti"
        self.k += 1
        if self.mode == "mati":
            return self.tolak("PENULIS_MODE=mati")
        self.siapkan()
        if not self.tarik():
            return self.henti("tarik (fetch + rebase) gagal")
        ok, why = self.syarat()
        if not ok:
            return self.tolak(why)
        if "diambil" in why or time.time() - self._tolak_terakhir[1] >= 3600 or self._tolak_terakhir[0] != "ok":
            self.log(f"boleh menulis: {why}")
            self._tolak_terakhir = ("ok", time.time())
        today = hari(now)
        if di_jendela(now, self.sumber) and self.selesai != today:
            r = self.blok_tick(today)
            if r == "berhenti":
                return r
        if self.selesai == today and self.dijaga != today:
            self.blok_jaga(today)
        self.blok_eksekusi()
        if self.mode == "master":
            rc, _ = self.alat(["tools/waitlist.py", "--poll"])
            if rc != 0:
                self.log(f"PERINGATAN: daftar tunggu rc={rc} (diulang 5 menit lagi; update Telegram tersimpan 24 jam)")
        if self.sumber == "rest":
            self.cek_vision()
        if self.mode == "bayangan-tulis":
            try:
                self.bandingkan()
            except GitError as e:
                self.log(f"PERINGATAN: pembandingan dengan {self.cabang_resmi} gagal ({e}) - diulang putaran berikut")
        return "ok"

    def blok_tick(self, today: str) -> str:
        self.log(f"=== putaran {self.k} {utc(self.now_fn())} ({self.mode}, {self.sumber}, cabang {self.cabang}) ===")
        if self.sumber == "rest":
            try:
                self.isi_rest()
            except Exception as e:  # noqa: BLE001 - REST tak terbaca: rantai jalan terus dengan Vision (sama dengan tahap 2)
                self.log(f"PERINGATAN: baris REST gagal dibaca ({type(e).__name__}: {saring(str(e), self.token)[:160]}) - lanjut dengan Vision")
        rc, _ = self.alat(["tools/paper_tick.py", "--feed"])
        self.log(f"paper_tick rc={rc} (0 beres; 4 tick belum bisa dibuat, coba lagi 5 menit lagi)")
        if rc not in (0, 4):
            return self.henti(f"paper_tick rc={rc}")
        if not self.verify():
            return self.henti("ledger verify GAGAL - tidak commit")
        frc, _ = self.alat(["tools/feed_tick.py"])
        if frc != 0:
            self.log(f"PERINGATAN: feed_tick rc={frc} (4 = TUNDA: gerbang/RPC tidak terbaca, diulang 5 menit lagi)")
        r = self.komit(["ledger/feed", "ledger/paper", "ledger/bars"], "ledger paper", "")
        if r == "verify":
            return self.henti("ledger verify GAGAL sesudah menarik hulu - tidak push")
        if r in ("gagal", "kunci"):
            return self.henti("5x push gagal - ledger tidak sampai ke cabang" if r == "gagal" else "sewa kunci hilang sebelum push")
        if rc != 0:
            return "tunda"
        self.selesai = today
        self.log(f"tick {today} beres; diam sampai jendela besok")
        b1, _ = self.alat(["-m", "engine.cli", "book", "epoch", "--write"])
        b2 = self.alat(["-m", "engine.cli", "book", "verify"])[0] if b1 == 0 else 1
        if b1 == 0 and b2 == 0:
            if self.komit(["ledger/book"], "buku slot epoch", "buku ") not in ("ok", "kosong"):
                self.log("PERINGATAN: push buku gagal - epoch dicoba lagi besok")
                self.reset_keras()
        else:
            self.log("PERINGATAN: book epoch/verify GAGAL - buku TIDAK di-commit; rantai ledger tetap jalan")
            self.buang("ledger/book")
        kr, _ = self.alat(["tools/kertas_eksekusi.py", "run"])
        if kr == 0:
            if self.komit(["ledger/kertas"], "kertas eksekusi", "kertas ") not in ("ok", "kosong"):
                self.log("PERINGATAN: push kertas gagal - dikejar besok")
                self.reset_keras()
        else:
            self.log("PERINGATAN: kertas eksekusi GAGAL - tidak di-commit; rantai ledger tetap jalan")
            self.buang("ledger/kertas")
        return "beres"

    def blok_jaga(self, today: str) -> None:
        if self.mode != "master":
            self.dijaga = today
            self.log("uji: penjaga luar worker dan pemicu workflow dilewati (worker + landing mengikuti master)")
            return
        rc, _ = self.alat(["tools/worker_watch.py", "--alert", "--ringkasan"])
        if rc in (0, 1):
            self.dijaga = today
            self.log("penjaga luar: worker hidup" if rc == 0 else "GALAT: penjaga luar: WORKER DIAM atau ungkap tertahan - rantai ledger tetap jalan")
        elif rc == 2:
            self.log("penjaga luar: komit belum ada, masih dalam tenggang - periksa lagi 5 menit lagi")
        else:
            self.log(f"PERINGATAN: penjaga luar tidak bisa membaca chain (rc={rc}) - bukan bukti worker mati; diulang")
        if self.dijaga == today:
            for wf in DISPATCH:
                try:
                    ok = self.api is not None and self.api.dispatch(wf, self.cabang)
                except Exception:  # noqa: BLE001
                    ok = False
                self.log(f"{wf} dipicu" if ok else f"PERINGATAN: gagal memicu {wf} - rantai ledger tetap jalan")

    def blok_eksekusi(self) -> None:
        state = os.path.join(self.workdir, "eksekusi-alert.json")
        al = ["--alert"] if self.mode == "master" else []
        xrc, _ = self.alat(["tools/eksekusi_ledger.py", "run", *al, "--state", state])
        if xrc == 1:
            self.log("GALAT: ledger eksekusi: ALARM (baris di atas) - rantai ledger tetap jalan")
        elif xrc == 3:
            self.log("PERINGATAN: umpan eksekusi / chain tak terbaca - diulang 5 menit lagi")
        if self.alat(["tools/eksekusi_ledger.py", "verify"], tampil=False)[0] == 0:
            if self.komit(["ledger/eksekusi"], "ledger eksekusi", "eksekusi ") not in ("ok", "kosong"):
                self.log("PERINGATAN: push eksekusi gagal - diulang putaran berikut")
                self.reset_keras()
        else:
            self.log("GALAT: ledger eksekusi verify GAGAL - tidak di-commit")
            self.buang("ledger/eksekusi")
        prc, out = self.alat(["tools/eksekusi_ledger.py", "periksa", *al, "--state", state], tampil=False)
        if prc == 1:
            for ln in out.rstrip().splitlines():
                self.log("  | " + ln)
            self.log("GALAT: penjaga luar eksekusi: ALARM - tick dikomit tanpa laporan eksekusi")


# ---------------------------------------------------------------- perintah
def _config_dari_ref(ref: Optional[str]) -> Optional[str]:
    if not ref:
        return baca(os.path.join(ROOT, CONFIG_REL))
    return Git(ROOT).isi(ref, CONFIG_REL)


def cmd_syarat() -> int:
    token = (os.environ.get(TOKEN_ENV) or "").strip()
    slug = os.environ.get("PENULIS_REPO_SLUG") or repo_slug(REPO)
    api = GitHubApi(slug, token)
    try:
        teks = base64.b64decode(api.get(f"/repos/{slug}/contents/{CONFIG_REL}?ref={CABANG_RESMI}")["content"]).decode()
    except Exception as e:  # noqa: BLE001
        teks = None
        print(f"config {CONFIG_REL} di {CABANG_RESMI}: tak terbaca ({type(e).__name__})")
    p = penulis_dari(teks)
    print(f"1. {CONFIG_REL} di {CABANG_RESMI}: penulis = {p or 'TAK TERBACA'}  -> {'OK' if p == 'railway' else 'Railway TIDAK menulis'}")
    ok2, why2 = syarat_rantai_github(api)
    print(f"2. rantai GitHub: {why2}  -> {'OK' if ok2 else 'Railway TIDAK menulis'}")
    g = Git(ROOT, token)
    try:
        out = g.run("ls-remote", REPO, f"refs/penulis/kunci-{CABANG_RESMI}")
        print(f"3. kunci refs/penulis/kunci-{CABANG_RESMI}: {'ADA ' + out.split()[0][:12] if out else 'kosong (penulis pertama mengambilnya)'}")
    except GitError as e:
        print(f"3. kunci: tak terbaca ({e})")
    return 0 if (p == "railway" and ok2) else 1


def cmd_jalan(once: bool) -> int:
    import alert as alertmod
    e = os.environ
    mode, sumber = e.get("PENULIS_MODE", "mati").strip(), e.get("PENULIS_SUMBER", "vision").strip()
    token = (e.get(TOKEN_ENV) or "").strip()
    remote = e.get("PENULIS_REMOTE") or REPO
    slug = e.get("PENULIS_REPO_SLUG") or repo_slug(REPO)
    if mode in ("master", "bayangan-tulis") and not token and remote.startswith(GITHUB):
        log(f"GALAT: PENULIS_MODE={mode} butuh {TOKEN_ENV} (push ke GitHub)")
        return 2
    al = alertmod.Alerter(log=log, prefix="Fabius penulis" + (" uji" if mode != "master" else ""))
    try:
        pn = Penulis(mode, sumber, remote, e.get("PENULIS_WORKDIR", os.path.join(tempfile.gettempdir(), "fabius-penulis")), token=token,
                     api=GitHubApi(slug, token) if slug else None, alerter=al, cabang_uji=e.get("PENULIS_CABANG_UJI", "penulis-uji"),
                     git_nama=e.get("PENULIS_GIT_NAME", "paper-ledger-railway"),
                     git_email=e.get("PENULIS_GIT_EMAIL", "paper-ledger-railway@users.noreply.github.com"))
    except ValueError as ex:
        log(f"GALAT: {ex}")
        return 2
    stop = {"v": False}

    def _term(signum, frame):  # noqa: ARG001
        stop["v"] = True

    try:
        signal.signal(signal.SIGTERM, _term)
    except (ValueError, AttributeError):
        pass
    log(f"penulis ledger mulai | mode {mode} | sumber {sumber} | cabang {pn.cabang} | pemegang {pn.kunci.pemegang} | "
        f"region {e.get('RAILWAY_REPLICA_REGION', '?')}")
    if al.enabled and mode != "mati":
        al.send("mulai", f"penulis ledger mulai: mode {mode}, sumber {sumber}, cabang {pn.cabang}")
    fails = 0
    try:
        while not stop["v"]:
            try:
                pn.putaran()
                fails = 0
            except Exception as ex:  # noqa: BLE001 - putaran gagal dicatat lalu diulang
                fails += 1
                log(f"putaran penulis GAGAL: {type(ex).__name__}: {saring(str(ex), token)[:240]}")
                if fails >= 3:
                    al.send("penulis-gagal", f"penulis ledger: {fails} putaran GAGAL berturut-turut; terakhir {type(ex).__name__}")
            if once:
                break
            t_end = time.time() + POLL_S
            while not stop["v"] and time.time() < t_end:
                time.sleep(min(5.0, max(0.0, t_end - time.time())))
    finally:
        if pn.kunci.lepas():
            log(f"kunci {pn.kunci.ref} dilepas")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="P99/P100: penulis ledger Railway (pengganti rantai paper-ledger GitHub).")
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("siapa", help="penulis menurut config (github|railway); galat = github")
    s.add_argument("--ref", help="baca config dari ref git (mis. FETCH_HEAD) alih-alih berkas kerja")
    sub.add_parser("syarat", help="syarat penulis tunggal saat ini (hanya baca)")
    b = sub.add_parser("bandingkan", help="tick + bar cabang uji vs master")
    b.add_argument("--resmi", default=f"origin/{CABANG_RESMI}")
    b.add_argument("--uji", default="origin/penulis-uji")
    j = sub.add_parser("jalan", help="loop penulis (bawaan tanpa argumen; Railway)")
    j.add_argument("--once", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "siapa":
        try:
            print(siapa(_config_dari_ref(a.ref)))
        except Exception:  # noqa: BLE001 - workflow: apa pun yang gagal = perilaku lama
            print("github")
        return 0
    if a.cmd == "syarat":
        return cmd_syarat()
    if a.cmd == "bandingkan":
        lines, beda = bandingkan_ref(Git(ROOT), a.resmi, a.uji, label=a.uji.rsplit("/", 1)[-1])
        for ln in lines:
            print(ln)
        return 1 if beda else 0
    return cmd_jalan(getattr(a, "once", False))


if __name__ == "__main__":
    raise SystemExit(main())
