"""Secure first-frame handoff marker shared by the mode selector and Gaming."""

from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path

_READY_PREFIX = "leos-gaming-ready-"
_READY_VALUE = b"ready\n"
_MAX_MARKER_BYTES = 32


def _validated_marker_path(value: str | Path) -> Path | None:
    """Accept only LEOS marker names directly inside the active temp directory."""
    try:
        marker = Path(value)
        if not marker.is_absolute() or not marker.name.startswith(_READY_PREFIX):
            return None
        expected_parent = Path(tempfile.gettempdir()).resolve(strict=True)
        actual_parent = marker.parent.resolve(strict=True)
        if actual_parent != expected_parent:
            return None
        return marker
    except (OSError, RuntimeError, TypeError, ValueError):
        return None


def create_gaming_handoff_marker() -> Path:
    """Create an empty, private marker that only the current user can access."""
    descriptor, name = tempfile.mkstemp(prefix=_READY_PREFIX)
    try:
        os.fchmod(descriptor, 0o600)
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600:
            raise OSError("LEOS handoff marker could not be secured")
    except Exception:
        try:
            os.close(descriptor)
        finally:
            Path(name).unlink(missing_ok=True)
        raise
    os.close(descriptor)
    return Path(name)


def mark_gaming_handoff_ready(value: str | Path) -> bool:
    """Write the readiness token only to an owned, private, empty marker file."""
    marker = _validated_marker_path(value)
    if marker is None:
        return False
    flags = os.O_WRONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(marker, flags)
    except OSError:
        return False
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid != os.getuid()
            or stat.S_IMODE(before.st_mode) != 0o600
            or before.st_size != 0
        ):
            return False
        offset = 0
        while offset < len(_READY_VALUE):
            written = os.write(descriptor, _READY_VALUE[offset:])
            if written <= 0:
                return False
            offset += written
        os.fsync(descriptor)
        return True
    except OSError:
        return False
    finally:
        os.close(descriptor)


def gaming_handoff_is_ready(value: str | Path) -> bool:
    """Read and validate the bounded readiness token without following links."""
    marker = _validated_marker_path(value)
    if marker is None:
        return False
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(marker, flags)
    except OSError:
        return False
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid != os.getuid()
            or stat.S_IMODE(before.st_mode) != 0o600
            or before.st_size <= 0
            or before.st_size > _MAX_MARKER_BYTES
        ):
            return False
        payload = os.read(descriptor, _MAX_MARKER_BYTES + 1)
        after = os.fstat(descriptor)
        stable = (
            before.st_dev == after.st_dev
            and before.st_ino == after.st_ino
            and before.st_size == after.st_size
            and before.st_mtime_ns == after.st_mtime_ns
            and before.st_ctime_ns == after.st_ctime_ns
        )
        return stable and payload == _READY_VALUE
    except OSError:
        return False
    finally:
        os.close(descriptor)


def remove_gaming_handoff_marker(value: str | Path) -> None:
    """Remove only an owned, regular LEOS marker; never follow a symlink."""
    marker = _validated_marker_path(value)
    if marker is None:
        return
    try:
        info = marker.lstat()
        if (
            stat.S_ISREG(info.st_mode)
            and info.st_uid == os.getuid()
            and stat.S_IMODE(info.st_mode) == 0o600
        ):
            marker.unlink(missing_ok=True)
    except OSError:
        pass
