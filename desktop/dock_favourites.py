"""Local LEOS dock favourites.

Stores launcher desktop-file IDs only. It never executes commands or edits
Plasma configuration; a future dock adapter can resolve IDs through the
freedesktop application database and apply changes with explicit approval.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

DEFAULT_PINNED_APPS = (
    "org.kde.dolphin.desktop",
    "firefox.desktop",
    "steam.desktop",
)
from leos_core.paths import config_home as xdg_config_home


from leos_core.paths import config_home as xdg_config_home


MAX_PINNED_APPS = 32


def _config_path() -> Path:
    root = xdg_config_home()
    return root / "leos" / "dock-favourites.json"


def _valid_id(value: object) -> bool:
    if not isinstance(value, str) or not value or len(value) > 200:
        return False
    if value.startswith(".") or "/" in value or "\\" in value:
        return False
    return value.endswith(".desktop") and all(
        char.isalnum() or char in "._+-" for char in value
    )


class DockFavourites:
    """Atomic, private local store for pinned application desktop-file IDs."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _config_path()
        self._items = list(DEFAULT_PINNED_APPS)
        self.load()

    def load(self) -> None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if (isinstance(data, dict) and set(data) == {"schema_version", "items"}
                and data["schema_version"] == 1 and isinstance(data["items"], list)
                and len(data["items"]) <= MAX_PINNED_APPS
                and all(_valid_id(item) for item in data["items"])
                and len(set(data["items"])) == len(data["items"])):
            self._items = list(data["items"])

    def items(self) -> list[str]:
        return list(self._items)

    def pin(self, desktop_id: str) -> None:
        if not _valid_id(desktop_id):
            raise ValueError("Expected a valid application .desktop ID")
        if desktop_id in self._items:
            return
        if len(self._items) >= MAX_PINNED_APPS:
            raise ValueError("The LEOS dock cannot contain more than 32 favourites")
        self._items.append(desktop_id)
        self.save()

    def unpin(self, desktop_id: str) -> None:
        if desktop_id in self._items:
            self._items.remove(desktop_id)
            self.save()

    def move(self, desktop_id: str, index: int) -> None:
        if desktop_id not in self._items:
            raise ValueError("Application is not pinned")
        if type(index) is not int or not 0 <= index < len(self._items):
            raise ValueError("Invalid dock position")
        self._items.remove(desktop_id)
        self._items.insert(index, desktop_id)
        self.save()

    def save(self) -> None:
        payload = json.dumps(
            {"schema_version": 1, "items": self._items},
            indent=2, ensure_ascii=False,
        ) + "\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
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
