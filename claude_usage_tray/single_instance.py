"""Prevents more than one instance of the tray app running at the same time.

Uses a PID file in the system temp directory rather than QSharedMemory:
QSharedMemory's cross-process locking proved unreliable for this app on
Windows (two instances both succeeded in creating the segment), while a
PID-checked lock file is simple to reason about and self-heals after a
crash (a stale file pointing at a dead PID is treated as no lock at all).
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import os
import tempfile
from pathlib import Path
from typing import Optional

_LOCK_PATH = Path(tempfile.gettempdir()) / "claude-usage-monitor.lock"
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_OUR_IMAGE_NAMES = {"python.exe", "pythonw.exe"}


def _pid_is_running(pid: int) -> bool:
    """Checks that `pid` is not just alive, but actually a python(w).exe process.

    Windows recycles PIDs quickly, so a lock file left behind by a crashed or
    force-killed instance can point at a PID that now belongs to some
    unrelated process. Without this extra check, that coincidence would make
    the stale lock look permanently held and block every future launch.
    """
    handle = ctypes.windll.kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    try:
        buffer = ctypes.create_unicode_buffer(260)
        size = ctypes.wintypes.DWORD(260)
        if not ctypes.windll.kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return False
        return Path(buffer.value).name.lower() in _OUR_IMAGE_NAMES
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def _try_create_lock_file() -> bool:
    try:
        fd = os.open(str(_LOCK_PATH), os.O_CREAT | os.O_EXCL | os.O_RDWR)
    except FileExistsError:
        return False
    os.write(fd, str(os.getpid()).encode("ascii"))
    os.close(fd)
    return True


def acquire_lock() -> bool:
    """Returns True if this process now holds the lock, False if another instance is already running."""
    if _try_create_lock_file():
        return True

    try:
        existing_pid = int(_LOCK_PATH.read_text(encoding="ascii").strip())
    except (OSError, ValueError):
        existing_pid = None

    if existing_pid is not None and _pid_is_running(existing_pid):
        return False

    # Stale lock left behind by a crash; clear it and retry once.
    try:
        _LOCK_PATH.unlink()
    except OSError:
        pass
    return _try_create_lock_file()


def release_lock() -> None:
    try:
        if int(_LOCK_PATH.read_text(encoding="ascii").strip()) == os.getpid():
            _LOCK_PATH.unlink()
    except (OSError, ValueError):
        pass
