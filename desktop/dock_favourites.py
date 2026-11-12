"""Local LEOS dock favourites.

Stores launcher desktop-file IDs only. It never executes commands or edits
Plasma configuration; a future dock adapter can resolve IDs through the
freedesktop application database and apply changes with explicit approval.
"""
from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from leos_core.paths import config_home as xdg_config_home
from leos_core.json_utils import json_nesting_within_limit


DEFAULT_PINNED_APPS = (
    "org.kde.dolphin.desktop",
    "firefox.desktop",
    "steam.desktop",
)
MAX_PINNED_APPS = 32
MAX_DOCK_FILE_BYTES = 16 * 1024


def _config_path() -> Path:
    return xdg_config_home() / "leos" / "dock-favourites.json"


def _valid_id(value: object) -> bool:
    if not isinstance(value, str) or not value or len(value) > 200:
        return False
    if value.startswith(".") or "/" in value or "\\" in value:
        return False
    return value.endswith(".desktop") and all(
        char.isalnum() or char in "._+-" for char in value
    )


def _valid_payload(data: object) -> bool:
    return (
        isinstance(data, dict)
        and set(data) == {"schema_version", "items"}
        and type(data["schema_version"]) is int
        and data["schema_version"] == 1
        and isinstance(data["items"], list)
        and len(data["items"]) <= MAX_PINNED_APPS
        and all(_valid_id(item) for item in data["items"])
        and len(set(data["items"])) == len(data["items"])
    )


class DockFavourites:
    """Atomic, private and interprocess-safe storage for pinned desktop-file IDs."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _config_path()
        self._items = list(DEFAULT_PINNED_APPS)
        self.load()

    @contextmanager
    def _exclusive_lock(self) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.path.parent.is_symlink():
            raise OSError("Dock favourites directory cannot be a symbolic link")
        lock_path = self.path.with_name(self.path.name + ".lock")
        if lock_path.is_symlink():
            raise OSError("Dock favourites lock cannot be a symbolic link")
        with lock_path.open("a", encoding="utf-8") as lock:
            os.chmod(lock_path, 0o600)
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def load(self) -> bool:
        """Refresh from disk; leave the last valid in-memory state on corruption."""
        if self.path.is_symlink() or self.path.parent.is_symlink():
            return False
        try:
            with self.path.open("rb") as stream:
                raw = stream.read(MAX_DOCK_FILE_BYTES + 1)
            if len(raw) > MAX_DOCK_FILE_BYTES:
                return False
            text = raw.decode("utf-8")
            if not json_nesting_within_limit(text):
                return False
            data = json.loads(text)
        except FileNotFoundError:
            self._items = list(DEFAULT_PINNED_APPS)
            return True
        except (OSError, UnicodeError, json.JSONDecodeError, RecursionError):
            return False
        if not _valid_payload(data):
            return False
        self._items = list(data["items"])
        return True

    def items(self) -> list[str]:
        self.load()
        return list(self._items)

    def _write_unlocked(self) -> None:
        if self.path.is_symlink() or self.path.parent.is_symlink():
            raise OSError("Dock favourites path cannot be a symbolic link")
        payload = json.dumps(
            {"schema_version": 1, "items": self._items},
            indent=2, ensure_ascii=False,
        ) + "\n"
        fd, temp_name = tempfile.mkstemp(
            prefix="dock-favourites.", suffix=".tmp", dir=self.path.parent
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temp_name, 0o600)
            os.replace(temp_name, self.path)
        finally:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass

    def _reload_for_update(self) -> None:
        if self.path.is_symlink() or self.path.parent.is_symlink():
            raise OSError("Dock favourites path cannot be a symbolic link")
        if not self.load():
            raise ValueError("Dock favourites file is invalid or inaccessible; it was left untouched")

    def pin(self, desktop_id: str) -> None:
        if not _valid_id(desktop_id):
            raise ValueError("Expected a valid application .desktop ID")
        with self._exclusive_lock():
            self._reload_for_update()
            if desktop_id in self._items:
                return
            if len(self._items) >= MAX_PINNED_APPS:
                raise ValueError("The LEOS dock cannot contain more than 32 favourites")
            self._items.append(desktop_id)
            self._write_unlocked()

    def unpin(self, desktop_id: str) -> None:
        with self._exclusive_lock():
            self._reload_for_update()
            if desktop_id not in self._items:
                return
            self._items.remove(desktop_id)
            self._write_unlocked()


    def toggle(self, desktop_id: str) -> bool:
        """Atomically toggle one pin and return whether it is pinned afterward."""
        if not _valid_id(desktop_id):
            raise ValueError("Expected a valid application .desktop ID")
        with self._exclusive_lock():
            self._reload_for_update()
            if desktop_id in self._items:
                self._items.remove(desktop_id)
                self._write_unlocked()
                return False
            if len(self._items) >= MAX_PINNED_APPS:
                raise ValueError("The LEOS dock cannot contain more than 32 favourites")
            self._items.append(desktop_id)
            self._write_unlocked()
            return True


    def move_by(self, desktop_id: str, offset: int) -> bool:
        """Move a pinned application by a relative number of positions atomically."""
        if not _valid_id(desktop_id):
            raise ValueError("Expected a valid application .desktop ID")
        if type(offset) is not int or offset == 0:
            raise ValueError("Invalid relative dock position")
        with self._exclusive_lock():
            self._reload_for_update()
            if desktop_id not in self._items:
                raise ValueError("Application is not pinned")
            current = self._items.index(desktop_id)
            target = current + offset
            if not 0 <= target < len(self._items):
                return False
            self._items.pop(current)
            self._items.insert(target, desktop_id)
            self._write_unlocked()
            return True

    def move(self, desktop_id: str, index: int) -> None:
        with self._exclusive_lock():
            self._reload_for_update()
            if desktop_id not in self._items:
                raise ValueError("Application is not pinned")
            if type(index) is not int or not 0 <= index < len(self._items):
                raise ValueError("Invalid dock position")
            self._items.remove(desktop_id)
            self._items.insert(index, desktop_id)
            self._write_unlocked()

    def save(self) -> None:
        """Persist the in-memory list safely; intended for explicit maintenance."""
        with self._exclusive_lock():
            self._reload_for_update()
            if len(self._items) > MAX_PINNED_APPS or not all(
                _valid_id(item) for item in self._items
            ) or len(set(self._items)) != len(self._items):
                raise ValueError("Dock favourites data is invalid")
            self._write_unlocked()
