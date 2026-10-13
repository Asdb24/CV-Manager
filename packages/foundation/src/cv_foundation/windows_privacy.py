"""Restrict a harness directory to its current Windows token using native DACL APIs."""

import ctypes
from ctypes import wintypes
from pathlib import Path


class SidAndAttributes(ctypes.Structure):
    _fields_ = [("sid", ctypes.c_void_p), ("attributes", wintypes.DWORD)]


def protect_directory(directory: Path) -> None:
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    advapi.OpenProcessToken.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    ]
    advapi.GetTokenInformation.argtypes = [
        wintypes.HANDLE,
        ctypes.c_uint,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    advapi.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_wchar_p)]
    advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.c_void_p,
    ]
    advapi.SetFileSecurityW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p]
    token = wintypes.HANDLE()
    # TOKEN_QUERY, TokenUser, SDDL revision, DACL and protected-DACL flags are Win32 invariants.
    if not advapi.OpenProcessToken(kernel.GetCurrentProcess(), 0x0008, ctypes.byref(token)):
        raise OSError("WINDOWS_TOKEN_UNAVAILABLE")
    sid_text = ctypes.c_wchar_p()
    descriptor = ctypes.c_void_p()
    try:
        length = wintypes.DWORD()
        advapi.GetTokenInformation(token, 1, None, 0, ctypes.byref(length))
        buffer = ctypes.create_string_buffer(length.value)
        if not advapi.GetTokenInformation(token, 1, buffer, length, ctypes.byref(length)):
            raise OSError("WINDOWS_IDENTITY_UNAVAILABLE")
        user = ctypes.cast(buffer, ctypes.POINTER(SidAndAttributes)).contents
        if (
            not advapi.ConvertSidToStringSidW(user.sid, ctypes.byref(sid_text))
            or not sid_text.value
        ):
            raise OSError("WINDOWS_IDENTITY_UNAVAILABLE")
        sddl = f"D:P(A;OICI;FA;;;{sid_text.value})"
        if not advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            sddl, 1, ctypes.byref(descriptor), None
        ):
            raise OSError("WINDOWS_SECURITY_DESCRIPTOR_INVALID")
        if not advapi.SetFileSecurityW(str(directory), 0x00000004 | 0x80000000, descriptor):
            raise OSError("OWNED_TEMPORARY_STORAGE_PROTECTION_FAILED")
    finally:
        if descriptor:
            kernel.LocalFree(descriptor)
        if sid_text:
            kernel.LocalFree(ctypes.cast(sid_text, ctypes.c_void_p))
        kernel.CloseHandle(token)
