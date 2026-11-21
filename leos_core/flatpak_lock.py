"""Shared per-user lock for every LEOS Flatpak transaction.

The shell first-run bootstraps and the Store controller must use the same
flock-compatible file so they never run concurrent Flatpak package operations.
"""

from __future__ import annotations

import fcntl
import os
import stat
from pathlib import Path

from leos_core.paths import state_home


LOCK_FILENAME = "flatpak-setup.lock"


def _ensure_directory(path: Path) -> None:
    """Create a user state directory while rejecting a symlink at its root."""
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise OSError(f"Unsafe LEOS Flatpak lock directory: {path}")


def try_acquire_flatpak_lock() -> int | None:
    """Acquire the shared Flatpak lock without blocking the GUI thread.

    Returns an open file descriptor while the lock is held, None when another
    LEOS process owns it, and raises OSError when it cannot be safely opened.
    Callers must keep the descriptor open until the Flatpak process exits.
    """
    root = state_home()
    _ensure_directory(root)
    state_dir = root / "leos"
    _ensure_directory(state_dir)
    lock_path = state_dir / LOCK_FILENAME

    flags = os.O_CREAT | os.O_RDWR
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(lock_path, flags, 0o600)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise OSError(f"LEOS Flatpak lock is not a regular file: {lock_path}")
        if metadata.st_uid != os.getuid():
            raise OSError(f"LEOS Flatpak lock is not owned by the current user: {lock_path}")
        os.fchmod(descriptor, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(descriptor)
            return None
        return descriptor
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise


def release_flatpak_lock(descriptor: int) -> None:
    """Release and close an open shared Flatpak lock descriptor."""
    try:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)
