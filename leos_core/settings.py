"""Small, safe JSON settings store shared by LEOS applications."""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from leos_core.paths import config_home as xdg_config_home


MAX_SETTINGS_BYTES = 256 * 1024


def _read_settings_file(path: Path) -> dict[str, Any]:
    """Read a bounded JSON object without following an untrusted symlink."""
    with path.open("rb") as stream:
        raw = stream.read(MAX_SETTINGS_BYTES + 1)
    if len(raw) > MAX_SETTINGS_BYTES:
        raise ValueError("LEOS settings file is too large")
    loaded = json.loads(raw.decode("utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("LEOS settings file has an invalid format")
    return loaded

DEFAULTS: dict[str, Any] = {
    "last_mode": "desktop",
    "theme": "leos-original",
    "performance_profile": "balanced",
    "animations_enabled": True,
    "sounds_enabled": True,
    "gaming_overlay_enabled": True,
    "onboarding_complete": False,
    "transition_app_policy": "ask",
    "last_notified_system_update": "",
    "notifications_enabled": True,
    "notification_duration_seconds": 5,
    "notification_minimum_priority": "all",
    "notification_sounds_enabled": True,
    "silent_notifications_in_gaming": True,
}

ALLOWED_VALUES = {
    "last_mode": {"desktop", "gaming"},
    "theme": {"leos-original", "light", "cyan", "magenta", "gaming"},
    "performance_profile": {"performance", "balanced", "quiet", "battery-saver"},
    "transition_app_policy": {"ask"},
    "notification_minimum_priority": {"all", "important", "critical"},
}


class SettingsStore:
    """Stores user preferences in XDG_CONFIG_HOME without editing system files."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or xdg_config_home() / "leos" / "settings.json"
        self._values = DEFAULTS.copy()
        self.load()

    def load(self) -> None:
        # Never retain stale values when another LEOS process replaces the
        # shared preferences with a missing, corrupt, or oversized file.
        self._values = DEFAULTS.copy()
        if self.path.is_symlink() or self.path.parent.is_symlink():
            return
        if not self.path.is_file():
            return
        try:
            loaded = _read_settings_file(self.path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            return

        for key, default in DEFAULTS.items():
            value = loaded.get(key, default)
            if not isinstance(value, type(default)):
                continue
            allowed = ALLOWED_VALUES.get(key)
            if allowed is not None and value not in allowed:
                continue
            if key == "notification_duration_seconds" and value not in {3, 5, 8}:
                continue
            self._values[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        # Settings are shared by several LEOS processes (Desktop, Gaming and
        # Control Center). Refresh before reading so a long-lived process does
        # not keep using a stale in-memory copy.
        self.load()
        return self._values.get(key, default)

    def snapshot(self, keys: tuple[str, ...]) -> tuple[Any, ...]:
        """Read several preferences from one consistent file refresh."""
        self.load()
        return tuple(self._values.get(key) for key in keys)

    def set(self, key: str, value: Any) -> None:
        if key not in DEFAULTS:
            raise KeyError(f"Unknown LEOS setting: {key}")
        if not isinstance(value, type(DEFAULTS[key])):
            raise TypeError(f"{key} must be {type(DEFAULTS[key]).__name__}")
        allowed = ALLOWED_VALUES.get(key)
        if allowed is not None and value not in allowed:
            raise ValueError(f"Invalid value for {key}: {value}")
        if key == "notification_duration_seconds" and value not in {3, 5, 8}:
            raise ValueError(f"Invalid value for {key}: {value}")

        # Serialize read-modify-write across Desktop, Gaming and Control Center.
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.path.parent.is_symlink() or self.path.is_symlink():
            raise OSError("LEOS settings path cannot be a symbolic link")
        lock_path = self.path.with_name(self.path.name + ".lock")
        if lock_path.is_symlink():
            raise OSError("LEOS settings lock cannot be a symbolic link")
        with lock_path.open("a", encoding="utf-8") as lock:
            os.chmod(lock_path, 0o600)
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                if self.path.exists():
                    try:
                        _read_settings_file(self.path)
                    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
                        raise ValueError(
                            "LEOS settings file is unreadable or too large; it was left untouched"
                        ) from exc
                self.load()
                self._values[key] = value
                self.save()
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.path.parent.is_symlink() or self.path.is_symlink():
            raise OSError("LEOS settings path cannot be a symbolic link")
        os.chmod(self.path.parent, 0o700)
        payload = json.dumps(self._values, indent=2, ensure_ascii=False) + "\n"
        fd, temp_name = tempfile.mkstemp(
            prefix="settings.", suffix=".tmp", dir=self.path.parent
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
