"""Per-user, kernel-managed process lock for LEOS Gaming."""

from __future__ import annotations

import fcntl
import os
import re
from pathlib import Path


class InstanceLock:
    """Own an exclusive flock until release or process exit."""

    def __init__(self, file_descriptor: int) -> None:
        self._file_descriptor: int | None = file_descriptor

    def release(self) -> None:
        """Release the lock and close its descriptor; safe to call more than once."""
        descriptor = self._file_descriptor
        if descriptor is None:
            return
        self._file_descriptor = None
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def acquire_instance_lock(
    application_id: str,
    directory: Path | None = None,
) -> InstanceLock | None:
    """Acquire a non-blocking lock, returning None when another instance owns it."""
    safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", application_id).strip(".-")
    if not safe_id:
        raise ValueError("application_id must contain a safe filename character")

    if directory is None:
        runtime = os.environ.get("XDG_RUNTIME_DIR", "").strip()
        base = Path(runtime) if runtime else Path(
            os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))
        )
        directory = base / "leos"

    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock_path = directory / f"{safe_id}.lock"
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(lock_path, flags, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(descriptor)
        return None
    except OSError:
        os.close(descriptor)
        raise
    return InstanceLock(descriptor)
