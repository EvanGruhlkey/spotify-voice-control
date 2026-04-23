"""
Send system media key events via Windows SendInput (no Spotify API, no network).
Uses ctypes only — no extra keyboard-hook libraries for the actual media control.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes

# --- Windows / SendInput (Winuser.h) ---

user32 = ctypes.windll.user32

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001

VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3

ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


def _send_vk_key(vk: int, key_up: bool) -> None:
    flags = KEYEVENTF_KEYUP if key_up else 0
    # Some drivers expect KEYEVENTF_EXTENDEDKEY for media keys on down + up
    if vk in (VK_MEDIA_NEXT_TRACK, VK_MEDIA_PREV_TRACK, VK_MEDIA_PLAY_PAUSE):
        flags |= KEYEVENTF_EXTENDEDKEY
    extra = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=flags, time=0, dwExtraInfo=0)
    inp = INPUT(type=INPUT_KEYBOARD, ki=extra)
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def send_media_vk(vk: int) -> None:
    _send_vk_key(vk, key_up=False)
    _send_vk_key(vk, key_up=True)


def next_track() -> None:
    send_media_vk(VK_MEDIA_NEXT_TRACK)


def previous_track() -> None:
    send_media_vk(VK_MEDIA_PREV_TRACK)


def play_pause() -> None:
    send_media_vk(VK_MEDIA_PLAY_PAUSE)
