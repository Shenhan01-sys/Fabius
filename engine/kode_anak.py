"""P167b (epik 12 §3.2): PROSES ANAK sandbox `kind=code`. Stdlib saja; TIDAK mengimpor `engine` (dijalankan `python -s -S -P`, tanpa sys.path repo).

Induk (`engine/kode.py::PelariLokal`) mengirim satu pekerjaan JSON lewat stdin: kode yang SUDAH lolos analisis statis dan SUDAH diinstrumentasi
(panggilan `_l()` di tiap badan fungsi, badan perulangan, comprehension, lambda), bar publik per aset, varian parameter, sampel kausalitas, batas.
Anak ini:
  1. memasang batas sumber daya PADA DIRINYA SENDIRI sebelum membaca kode - tanpa `preexec_fn` (tidak aman di proses induk ber-thread):
     Linux / POSIX (pelari Railway): `setrlimit` CPU, memori, ukuran berkas 0, deskriptor, core 0;
     Windows (mesin builder): Job Object tanpa nama - waktu CPU per proses, memori ter-commit per proses, maksimal 1 proses (tidak bisa membuat
     proses baru), mati tanpa dialog bila galat tak tertangani, UI terkunci; tanpa padanan ukuran berkas / deskriptor (kode tidak punya `open`,
     analisis statis menolaknya). Pegangan job ditutup sesudah memasang -> kode tidak bisa melonggarkannya. Gagal memasang = gagal tertutup;
  2. menjalankan kode dengan builtins TERBATAS (daftar-izin; impor hanya `math` + `statistics` lewat proksi berisi anggota yang diizinkan);
  3. memanggil `target(bars, params)` SEKALI per bar i dengan data DIPOTONG <= i (pemetaan + tuple tak bisa diubah) -> kausal oleh konstruksi;
  4. sampel kausalitas: modul dieksekusi ULANG di namespace segar dan `target` dipanggil sekali pada data terpotong; bobot harus sama dengan jalan
     berurutan (menangkap keadaan global / argumen bawaan yang bisa diubah);
  5. memeriksa tiap keluaran (dict, kunci = aset yang punya bar, bobot terhingga, gross <= 1) dan menulis DATA berbatas ke stdout.
Pesan galat tidak pernah memuat teks dari kode pengguna (hanya nama jenis galat + tanggal bar): keluaran ini DATA bagi pihak tepercaya.
"""
import bisect
import builtins
import json
import math
import os
import statistics
import sys
from collections.abc import Mapping
from types import MappingProxyType, SimpleNamespace

if os.name == "nt":
    import ctypes
    from ctypes import wintypes
else:
    import resource

TOL_GROSS = 1e-9

# Windows: tanda batas Job Object (winnt.h) + kelas informasi (SetInformationJobObject).
JOB_OBJECT_LIMIT_PROCESS_TIME = 0x00000002
JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION = 0x00000400
JOB_OBJECT_UILIMIT_ALL = 0x000000FF
JOB_INFO_UI = 4                                                                 # JobObjectBasicUIRestrictions
JOB_INFO_EXTENDED = 9                                                           # JobObjectExtendedLimitInformation
SEM_TANPA_DIALOG = 0x0001 | 0x0002 | 0x8000                                    # FAILCRITICALERRORS | NOGPFAULTERRORBOX | NOOPENFILEERRORBOX


class Habis(BaseException):
    """Anggaran langkah per panggilan habis. BaseException: tidak bisa ditangkap kode pengguna (try/except juga ditolak analisis statis)."""


class Tolak(Exception):
    """Keluaran `target` tidak sah."""


def _batasi(b):
    if os.name == "nt":
        return _batasi_windows(int(b["cpu_s"]), int(b["memori_mb"]) * 1024 * 1024)
    cpu = int(b["cpu_s"])
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))
    mem = int(b["memori_mb"]) * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (16, 16))


def _batasi_windows(cpu_s, mem_byte):
    """Masukkan proses ini ke Job Object baru tanpa nama. Melewati batas CPU = dimatikan sistem (kode keluar STATUS_QUOTA_EXCEEDED); melewati
    batas memori = alokasi gagal (MemoryError); membuat proses baru = ditolak. Galat Win32 apa pun = OSError (gagal tertutup di `main`)."""
    class Dasar(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64), ("LimitFlags", wintypes.DWORD),
                    ("MinimumWorkingSetSize", ctypes.c_size_t), ("MaximumWorkingSetSize", ctypes.c_size_t),
                    ("ActiveProcessLimit", wintypes.DWORD), ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD)]

    class Io(ctypes.Structure):
        _fields_ = [(n, ctypes.c_uint64) for n in ("Baca", "Tulis", "Lain", "BacaByte", "TulisByte", "LainByte")]

    class Diperluas(ctypes.Structure):
        _fields_ = [("Dasar", Dasar), ("Io", Io), ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateJobObjectW.restype = wintypes.HANDLE
    k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    k32.SetInformationJobObject.restype = wintypes.BOOL
    k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    k32.AssignProcessToJobObject.restype = wintypes.BOOL
    k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    k32.SetErrorMode.argtypes = [wintypes.UINT]

    def cek(ok, apa):
        if not ok:
            raise OSError(ctypes.get_last_error(), apa)

    k32.SetErrorMode(SEM_TANPA_DIALOG)
    job = k32.CreateJobObjectW(None, None)
    cek(job, "CreateJobObject")
    try:
        x = Diperluas()
        x.Dasar.LimitFlags = (JOB_OBJECT_LIMIT_PROCESS_TIME | JOB_OBJECT_LIMIT_ACTIVE_PROCESS | JOB_OBJECT_LIMIT_PROCESS_MEMORY
                              | JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION)
        x.Dasar.PerProcessUserTimeLimit = cpu_s * 10_000_000                    # satuan 100 ns
        x.Dasar.ActiveProcessLimit = 1
        x.ProcessMemoryLimit = mem_byte
        cek(k32.SetInformationJobObject(job, JOB_INFO_EXTENDED, ctypes.byref(x), ctypes.sizeof(x)), "SetInformationJobObject")
        ui = wintypes.DWORD(JOB_OBJECT_UILIMIT_ALL)
        cek(k32.SetInformationJobObject(job, JOB_INFO_UI, ctypes.byref(ui), ctypes.sizeof(ui)), "SetInformationJobObject UI")
        cek(k32.AssignProcessToJobObject(job, k32.GetCurrentProcess()), "AssignProcessToJobObject")
    finally:
        k32.CloseHandle(job)                                                    # batas tetap berlaku selama proses ada di job


def _proksi(modul, nama):
    return SimpleNamespace(**{k: getattr(modul, k) for k in nama})


def _builtins(izin_modul):
    mods = {"math": _proksi(math, izin_modul["math"]), "statistics": _proksi(statistics, izin_modul["statistics"])}

    def impor(name, globals=None, locals=None, fromlist=(), level=0):          # noqa: A002 - tanda tangan __import__
        if level != 0 or name not in mods:
            raise ImportError("impor tidak diizinkan")
        return mods[name]
    aman = {k: getattr(builtins, k) for k in (
        "abs", "all", "any", "bool", "dict", "divmod", "enumerate", "filter", "float", "frozenset", "int", "isinstance", "len", "list", "map",
        "max", "min", "pow", "range", "reversed", "round", "set", "sorted", "str", "sum", "tuple", "zip")}
    aman["__import__"] = impor
    return aman


class _Aset(Mapping):
    """Bar satu aset sampai indeks n (eksklusif): kolom t o h l c v sebagai tuple; dipotong saat diakses. Tidak bisa diubah."""
    __slots__ = ("_k", "_n", "_c")

    def __init__(self, kolom, n):
        self._k, self._n, self._c = kolom, n, {}

    def __getitem__(self, k):
        if k not in self._c:
            self._c[k] = self._k[k][:self._n]
        return self._c[k]

    def __iter__(self):
        return iter(("t", "o", "h", "l", "c", "v"))

    def __len__(self):
        return 6


def main():
    job = json.loads(sys.stdin.buffer.read().decode("ascii"))
    b = job["batas"]
    try:
        _batasi(b)
    except (OSError, ValueError) as e:                                         # tanpa batas = tidak ada kode yang dijalankan
        sys.stdout.write(json.dumps({"ok": False, "galat": f"batas sumber daya tidak terpasang ({type(e).__name__})", "bar": None}))
        sys.stdout.flush()
        return
    langkah_maks = int(b["langkah_per_panggilan"])
    kolom = {a: {k: tuple(v) for k, v in cols.items()} for a, cols in job["bars"].items()}
    aset = sorted(kolom)
    grid = sorted({t for a in aset for t in kolom[a]["t"]})
    n_upto = {a: [bisect.bisect_right(kolom[a]["t"], t) for t in grid] for a in aset}
    di_grid = set(grid)
    kode = compile(job["kode"], "<kode>", "exec")
    bawaan = _builtins(job["izin_modul"])
    hitung = [0]

    def _l():
        hitung[0] += 1
        if hitung[0] > langkah_maks:
            raise Habis()
        return True

    def namespace():
        g = {"__builtins__": bawaan, "__name__": "kode_penerbit", "_l": _l}
        hitung[0] = 0
        exec(kode, g)                                                           # noqa: S102 - kode sudah lolos daftar-izin AST + builtins terbatas
        f = g.get("target")
        if not callable(f):
            raise Tolak("target tidak ada")
        return f

    def bars_di(i):
        return MappingProxyType({a: _Aset(kolom[a], n_upto[a][i]) for a in aset if n_upto[a][i] > 0})

    def panggil(f, i, params):
        hitung[0] = 0
        bars = bars_di(i)
        w = f(bars, dict(params))
        if not isinstance(w, dict) or len(w) > len(bars):
            raise Tolak("keluaran bukan dict {aset: bobot} atau terlalu banyak kunci")
        out, gross = {}, 0.0
        for k, x in w.items():
            if not isinstance(k, str) or k not in bars:
                raise Tolak("aset di luar data yang diberikan")
            if isinstance(x, bool) or not isinstance(x, (int, float)):
                raise Tolak("bobot bukan angka")
            x = float(x)
            if not math.isfinite(x):
                raise Tolak("bobot tidak terhingga")
            gross += abs(x)
            if x != 0.0:
                out[k] = x
        if gross > 1.0 + TOL_GROSS:
            raise Tolak("gross > 1")
        return out

    def tanggal(i):
        return grid[i] if 0 <= i < len(grid) else None

    hasil, i = {}, -1
    try:
        sys.setrecursionlimit(int(b.get("rekursi_maks", 200)))
        for label, params in job["varian"].items():
            f = namespace()
            rows = []
            for i in range(len(grid)):
                rows.append([grid[i], panggil(f, i, params)])
            hasil[label] = rows
        i = -1
        beda = []
        dasar = job.get("dasar_kausal")
        if job.get("sampel") and dasar in hasil:
            pos = {t: k for k, t in enumerate(grid)}
            seq = {t: w for t, w in hasil[dasar]}
            for t in job["sampel"]:
                if t not in pos:
                    continue
                i = pos[t]
                f = namespace()
                if panggil(f, i, job["varian"][dasar]) != seq[t]:
                    beda.append(t)
            i = -1
        out = {"ok": True, "varian": hasil, "kausal": {"n": sum(1 for t in job.get("sampel") or [] if t in di_grid), "beda": beda},
               "grid_n": len(grid)}
    except Habis:
        out = {"ok": False, "galat": f"anggaran langkah habis ({langkah_maks} langkah per panggilan)", "bar": tanggal(i)}
    except MemoryError:
        out = {"ok": False, "galat": "batas memori", "bar": tanggal(i)}
    except RecursionError:
        out = {"ok": False, "galat": "rekursi terlalu dalam", "bar": tanggal(i)}
    except Tolak as e:
        out = {"ok": False, "galat": f"keluaran ditolak: {e}", "bar": tanggal(i)}
    except BaseException as e:                                                 # noqa: BLE001 - apa pun dari kode pengguna = gagal, tanpa teksnya
        out = {"ok": False, "galat": f"galat {type(e).__name__}", "bar": tanggal(i)}
    teks = json.dumps(out, separators=(",", ":"), allow_nan=False)
    if len(teks) > int(b["keluaran_maks_byte"]):
        teks = json.dumps({"ok": False, "galat": "keluaran terlalu besar", "bar": None})
    sys.stdout.write(teks)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
