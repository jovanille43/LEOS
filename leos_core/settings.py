"""Small, safe JSON settings store shared by LEOS applications."""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
from pathlib import Path
from typing import Any

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
    "transition_app_policy": {"ask", "keep", "close"},
    "notification_minimum_priority": {"all", "important", "critical"},
}


class SettingsStore:
    """Stores user preferences in XDG_CONFIG_HOME without editing system files."""

    def __init__(self, path: Path | None = None) -> None:
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        self.path = path or config_home / "leos" / "settings.json"
        self._values = DEFAULTS.copy()
        self.load()

    def load(self) -> None:
        if not self.path.is_file():
            return
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(loaded, dict):
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
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self.path.with_name(self.path.name + ".lock")
        with lock_path.open("a", encoding="utf-8") as lock:
            os.chmod(lock_path, 0o600)
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                self.load()
                self._values[key] = value
                self.save()
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
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
