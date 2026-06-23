"""Ensure only one Howlbert process runs; duplicate bots break Discord interactions."""

from __future__ import annotations

import atexit
import os
from pathlib import Path

LOCK_PATH = Path(__file__).resolve().parent.parent / ".howlbert.lock"


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        synchronize = 0x00100000
        handle = kernel32.OpenProcess(synchronize, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def acquire_bot_lock() -> None:
    """Exit the process if another Howlbert instance is already running."""
    if LOCK_PATH.exists():
        try:
            old_pid = int(LOCK_PATH.read_text(encoding="utf-8").strip())
        except ValueError:
            old_pid = 0
        if _pid_alive(old_pid):
            raise SystemExit(
                "Another Howlbert instance is already running "
                f"(PID {old_pid}).\n"
                "Stop that process before starting again; two bots cause "
                "random 'interaction failed' errors on slash commands.\n"
                f"Lock file: {LOCK_PATH}"
            )
        LOCK_PATH.unlink(missing_ok=True)

    LOCK_PATH.write_text(str(os.getpid()), encoding="utf-8")
    atexit.register(release_bot_lock)


def release_bot_lock() -> None:
    try:
        if LOCK_PATH.exists() and LOCK_PATH.read_text(encoding="utf-8").strip() == str(os.getpid()):
            LOCK_PATH.unlink()
    except OSError:
        pass
