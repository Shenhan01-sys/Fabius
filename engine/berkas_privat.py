"""P167b: berkas yang hanya bisa dibaca akun proses ini (kode privat `kind=code` di gerbang), lintas OS.

POSIX (gerbang Railway): mode 0600 saat berkas dibuat.
Windows (mesin builder): DACL TERLINDUNG (tanpa warisan dari folder induk) berisi satu ACE akses penuh untuk SID akun proses ini - padanan 0600.
Folder tempat berkas ditulis ikut dikunci dengan ACE yang diwariskan, jadi berkas sudah tertutup sejak dibuat (tidak ada jeda dengan ACL induk).
Stdlib saja (ctypes ke advapi32 / kernel32); galat Win32 = OSError (penulis gagal, tidak menulis berkas terbuka diam-diam).
"""
from __future__ import annotations

import os
import re
import stat

SDDL_REVISION_1 = 1
DACL_SECURITY_INFORMATION = 0x00000004
PROTECTED_DACL_SECURITY_INFORMATION = 0x80000000
TOKEN_QUERY = 0x0008
TOKEN_USER = 1


def tulis(path: str, teks: str) -> None:
    """Tulis `teks` (UTF-8, LF) ke `path` yang hanya bisa dibaca akun proses ini."""
    if os.name != "nt":
        with open(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w", encoding="utf-8", newline="\n") as f:
            f.write(teks)
        return
    _kunci(os.path.dirname(os.path.abspath(path)), folder=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(teks)
    _kunci(path, folder=False)


def hanya_pemilik(path: str) -> bool:
    """True bila berkas hanya bisa diakses akun proses ini (POSIX: mode 0600; Windows: DACL terlindung, satu ACE izinkan untuk SID kita)."""
    if os.name != "nt":
        return stat.S_IMODE(os.stat(path).st_mode) == 0o600
    sddl = dacl_sddl(path)
    aces = re.findall(r"\(([^)]*)\)", sddl)
    if not re.match(r"D:P", sddl) or len(aces) != 1:
        return False
    jenis, _flag, hak, _o, _io, sid = aces[0].split(";")
    return jenis == "A" and hak == "FA" and sid == sid_saya()


# ---- Windows (ctypes) -------------------------------------------------------------------------------------------------------------------------

def _api():
    import ctypes
    from ctypes import wintypes
    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    k32.LocalFree.argtypes = [ctypes.c_void_p]
    adv.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    adv.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    adv.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.LPWSTR)]
    adv.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p),
                                                                         ctypes.c_void_p]
    adv.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = [ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
                                                                         ctypes.POINTER(wintypes.LPWSTR), ctypes.c_void_p]
    adv.SetFileSecurityW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p]
    adv.GetFileSecurityW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    return ctypes, wintypes, adv, k32


def _cek(ctypes, ok, apa: str) -> None:
    if not ok:
        raise OSError(ctypes.get_last_error(), apa)


def sid_saya() -> str:
    """SID akun proses ini sebagai teks (S-1-5-21-...)."""
    ctypes, wintypes, adv, k32 = _api()
    tok = wintypes.HANDLE()
    _cek(ctypes, adv.OpenProcessToken(k32.GetCurrentProcess(), TOKEN_QUERY, ctypes.byref(tok)), "OpenProcessToken")
    try:
        n = wintypes.DWORD()
        adv.GetTokenInformation(tok, TOKEN_USER, None, 0, ctypes.byref(n))
        buf = ctypes.create_string_buffer(n.value)
        _cek(ctypes, adv.GetTokenInformation(tok, TOKEN_USER, buf, n, ctypes.byref(n)), "GetTokenInformation")
        psid = ctypes.c_void_p.from_buffer(buf).value                                  # TOKEN_USER.User.Sid = penunjuk pertama
        s = wintypes.LPWSTR()
        _cek(ctypes, adv.ConvertSidToStringSidW(psid, ctypes.byref(s)), "ConvertSidToStringSid")
        try:
            return s.value
        finally:
            k32.LocalFree(s)
    finally:
        k32.CloseHandle(tok)


def _kunci(path: str, folder: bool) -> None:
    ctypes, wintypes, adv, k32 = _api()
    sddl = f"D:P(A;{'OICI' if folder else ''};FA;;;{sid_saya()})"
    sd = ctypes.c_void_p()
    _cek(ctypes, adv.ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl, SDDL_REVISION_1, ctypes.byref(sd), None),
         "ConvertStringSecurityDescriptorToSecurityDescriptor")
    try:
        _cek(ctypes, adv.SetFileSecurityW(path, DACL_SECURITY_INFORMATION | PROTECTED_DACL_SECURITY_INFORMATION, sd), "SetFileSecurity")
    finally:
        k32.LocalFree(sd)


def dacl_sddl(path: str) -> str:
    """DACL berkas / folder sebagai SDDL (Windows), dibaca dari sistem berkas."""
    ctypes, wintypes, adv, k32 = _api()
    n = wintypes.DWORD()
    adv.GetFileSecurityW(path, DACL_SECURITY_INFORMATION, None, 0, ctypes.byref(n))
    buf = ctypes.create_string_buffer(n.value)
    _cek(ctypes, adv.GetFileSecurityW(path, DACL_SECURITY_INFORMATION, buf, n, ctypes.byref(n)), "GetFileSecurity")
    s = wintypes.LPWSTR()
    _cek(ctypes, adv.ConvertSecurityDescriptorToStringSecurityDescriptorW(buf, SDDL_REVISION_1, DACL_SECURITY_INFORMATION, ctypes.byref(s), None),
         "ConvertSecurityDescriptorToStringSecurityDescriptor")
    try:
        return s.value
    finally:
        k32.LocalFree(s)
