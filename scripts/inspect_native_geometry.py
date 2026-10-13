"""Read-only Win32 measurement of a selected shell HWND, with no UI input APIs."""

import argparse
import ctypes
import hashlib
import json
from ctypes import wintypes
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--window", type=int, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
user = ctypes.WinDLL("user32", use_last_error=True)
# Disable coordinate virtualization only for this read-only measurement thread.
# DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 is the Win32 constant -4.
user.SetThreadDpiAwarenessContext.argtypes = [ctypes.c_void_p]
user.SetThreadDpiAwarenessContext.restype = ctypes.c_void_p
if not user.SetThreadDpiAwarenessContext(ctypes.c_void_p(-4)):
    raise OSError("MEASUREMENT_DPI_CONTEXT_UNAVAILABLE")
user.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user.GetDpiForWindow.argtypes = [wintypes.HWND]
user.GetDpiForWindow.restype = wintypes.UINT
user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
title = ctypes.create_unicode_buffer(256)
user.GetWindowTextW(args.window, title, len(title))
if title.value != "Quản lý hồ sơ tuyển dụng":
    raise ValueError("SELECTED_SHELL_WINDOW_REQUIRED")
client = wintypes.RECT()
outer = wintypes.RECT()
if not user.GetClientRect(args.window, ctypes.byref(client)) or not user.GetWindowRect(
    args.window, ctypes.byref(outer)
):
    raise OSError("WINDOW_GEOMETRY_UNAVAILABLE")
dpi = user.GetDpiForWindow(args.window)
if not dpi:
    raise OSError("WINDOW_DISPLAY_SCALE_UNAVAILABLE")
result = {
    "hwnd": args.window,
    "title": title.value,
    "client_physical_pixels": [client.right - client.left, client.bottom - client.top],
    "outer_physical_pixels": [outer.right - outer.left, outer.bottom - outer.top],
    "dpi": dpi,
    "display_scale": dpi / 96,
    "client_logical_pixels": [
        (client.right - client.left) * 96 / dpi,
        (client.bottom - client.top) * 96 / dpi,
    ],
    "binary_sha256": hashlib.sha256(
        (root / "apps/desktop/src-tauri/target/debug/agency-cv-shell.exe").read_bytes()
    ).hexdigest(),
    "method": "Read-only Win32 client rect and DPI, selected HWND from Computer Use",
}
file = root / f".local/native-geometry-{int(result['client_logical_pixels'][0])}.json"
file.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
