"""Per-user process lock for preventing duplicate LEOS Gaming windows."""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QLockFile, QStandardPaths


def acquire_instance_lock(
    application_id: str,
    directory: Path | None = None,
) -> QLockFile | None:
    """Acquire a non-blocking lock, returning None when another instance owns it."""
    safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", application_id).strip(".-")
    if not safe_id:
        raise ValueError("application_id must contain a safe filename character")

    if directory is None:
        runtime = QStandardPaths.writableLocation(QStandardPaths.RuntimeLocation)
        base = runtime or QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)
        if not base:
            base = str(Path.home() / ".cache")
        directory = Path(base) / "leos"

    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock = QLockFile(str(directory / f"{safe_id}.lock"))
    # Detect abandoned locks immediately by checking the recorded process.
    lock.setStaleLockTime(0)
    return lock if lock.tryLock(0) else None
