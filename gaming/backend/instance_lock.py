"""Per-user, kernel-managed process lock for LEOS Gaming."""

from __future__ import annotations

import fcntl
import os
import re
import stat
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
    if len(safe_id) > 64:
        raise ValueError("application_id is too long for a lock filename")

    if directory is None:
        runtime = os.environ.get("XDG_RUNTIME_DIR", "").strip()
        runtime_path = Path(runtime) if runtime else None
        if runtime_path is not None and runtime_path.is_absolute():
            base = runtime_path
        else:
            cache_home = os.environ.get("XDG_CACHE_HOME", "").strip()
            cache_path = Path(cache_home) if cache_home else None
            base = (
                cache_path
                if cache_path is not None and cache_path.is_absolute()
                else Path.home() / ".cache"
            )
        directory = base / "leos"

    if not directory.is_absolute():
        raise OSError("LEOS lock directory must be an absolute path")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if directory.is_symlink() or not directory.is_dir():
        raise OSError("LEOS lock directory must be a real directory")

    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    directory_flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    directory_fd = os.open(directory, directory_flags)
    descriptor: int | None = None
    try:
        directory_info = os.fstat(directory_fd)
        if (
            not stat.S_ISDIR(directory_info.st_mode)
            or directory_info.st_uid != os.getuid()
        ):
            raise OSError("LEOS lock directory must belong to the current user")
        os.fchmod(directory_fd, 0o700)
        if os.fstat(directory_fd).st_mode & 0o077:
            raise OSError("LEOS lock directory permissions are not private")

        flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(f"{safe_id}.lock", flags, 0o600, dir_fd=directory_fd)
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or metadata.st_nlink != 1
        ):
            raise OSError("LEOS lock file must be an owned, private regular file")
        os.fchmod(descriptor, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        if descriptor is not None:
            os.close(descriptor)
        return None
    except OSError:
        if descriptor is not None:
            os.close(descriptor)
        raise
    finally:
        os.close(directory_fd)

    assert descriptor is not None
    return InstanceLock(descriptor)
