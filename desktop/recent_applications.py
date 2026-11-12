"""Private, bounded storage for recently launched Desktop Entry identifiers."""

from __future__ import annotations

import fcntl
import json
import os
import re
import tempfile
from pathlib import Path


from leos_core.paths import state_home as xdg_state_home


MAX_RECENT_FILE_BYTES = 64 * 1024
MAX_RECENT_ENTRIES = 100


DESKTOP_ID_RE = re.compile(r"^[A-Za-z0-9_.+-]{1,240}\.desktop$")


class RecentApplications:
    """Persist an MRU list of .desktop ids without storing commands or paths."""

    def __init__(
        self,
        path: Path | None = None,
        limit: int = 20,
    ) -> None:
        if path is None:
            path = xdg_state_home() / "leos" / "recent-applications.json"
        if type(limit) is not int or not 1 <= limit <= MAX_RECENT_ENTRIES:
            raise ValueError("Recent application history limit is invalid")
        self.path = path
        self.limit = limit

    @staticmethod
    def _valid_id(value: object) -> bool:
        return isinstance(value, str) and bool(DESKTOP_ID_RE.fullmatch(value))

    def _read(self) -> list[str]:
        if self.path.is_symlink() or self.path.parent.is_symlink():
            raise ValueError("Recent application history path cannot be a symbolic link")
        if not self.path.exists():
            return []
        if not self.path.is_file():
            raise ValueError("Recent application history is not a regular file")
        try:
            with self.path.open("rb") as stream:
                raw = stream.read(MAX_RECENT_FILE_BYTES + 1)
            if len(raw) > MAX_RECENT_FILE_BYTES:
                raise ValueError("Recent application history is too large")
            payload = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
            raise ValueError("Recent application history is unreadable or too large") from exc
        if (
            not isinstance(payload, list)
            or len(payload) > MAX_RECENT_ENTRIES
            or any(not self._valid_id(item) for item in payload)
        ):
            raise ValueError("Recent application history has an invalid format")
        result: list[str] = []
        for item in payload:
            if item not in result:
                result.append(item)
        return result[: self.limit]

    def items(self) -> list[str]:
        """Read history defensively; a corrupt file is left untouched."""
        try:
            return self._read()
        except (OSError, ValueError):
            return []

    def _write(self, items: list[str]) -> None:
        if self.path.is_symlink():
            raise ValueError("Recent application history cannot be a symbolic link")
        if (
            not isinstance(items, list)
            or len(items) > MAX_RECENT_ENTRIES
            or any(not self._valid_id(item) for item in items)
        ):
            raise ValueError("Invalid recent application history")
        if self.path.is_symlink() or self.path.parent.is_symlink():
            raise ValueError("Recent application history path cannot be a symbolic link")
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.path.parent, 0o700)
        payload = json.dumps(items[: self.limit], indent=2, ensure_ascii=False) + "\n"
        if len(payload.encode("utf-8")) > MAX_RECENT_FILE_BYTES:
            raise ValueError("Recent application history exceeds its storage limit")
        descriptor, temporary = tempfile.mkstemp(
            prefix="recent-apps.", suffix=".tmp", dir=self.path.parent
        )
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, self.path)
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass

    def clear(self) -> None:
        """Clear the recent list after an explicit user request."""
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.path.parent.is_symlink():
            raise ValueError("Recent application history directory cannot be a symbolic link")
        lock_path = self.path.with_name(self.path.name + ".lock")
        if lock_path.is_symlink():
            raise ValueError("Recent application lock cannot be a symbolic link")
        with lock_path.open("a", encoding="utf-8") as lock:
            os.chmod(lock_path, 0o600)
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                self._write([])
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def record(self, desktop_id: str) -> None:
        """Move a successfully launched id to the front of the bounded list."""
        if not self._valid_id(desktop_id):
            raise ValueError("Invalid Desktop Entry identifier")
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.path.parent.is_symlink():
            raise ValueError("Recent application history directory cannot be a symbolic link")
        lock_path = self.path.with_name(self.path.name + ".lock")
        if lock_path.is_symlink():
            raise ValueError("Recent application lock cannot be a symbolic link")
        with lock_path.open("a", encoding="utf-8") as lock:
            os.chmod(lock_path, 0o600)
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                items = self._read()
                updated = [desktop_id] + [item for item in items if item != desktop_id]
                self._write(updated)
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
