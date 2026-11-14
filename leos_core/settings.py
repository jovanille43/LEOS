"""Small, safe JSON settings store shared by LEOS applications."""

from __future__ import annotations

import fcntl
import json
import os
import re
import tempfile
import stat
from pathlib import Path
from typing import Any, Callable

from leos_core.paths import config_home as xdg_config_home
from leos_core.json_utils import json_nesting_within_limit


MAX_SETTINGS_BYTES = 256 * 1024
_THEME_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
_THEME_COLOR_KEYS = frozenset({"theme_color_a", "theme_color_b"})


def _read_settings_file(path: Path) -> dict[str, Any]:
    """Read a bounded JSON object without following an untrusted symlink."""
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("LEOS settings path is not a regular file")
        if before.st_size > MAX_SETTINGS_BYTES:
            raise ValueError("LEOS settings file is too large")
        chunks: list[bytes] = []
        remaining = MAX_SETTINGS_BYTES + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
        if (
            len(raw) > MAX_SETTINGS_BYTES
            or len(raw) != before.st_size
            or before.st_ino != after.st_ino
            or before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
            or before.st_ctime_ns != after.st_ctime_ns
        ):
            raise ValueError("LEOS settings file changed during reading")
    finally:
        os.close(descriptor)
    text = raw.decode("utf-8")
    if not json_nesting_within_limit(text):
        raise ValueError("LEOS settings JSON nesting is excessive or malformed")
    loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise ValueError("LEOS settings file has an invalid format")
    return loaded

DEFAULTS: dict[str, Any] = {
    "last_mode": "desktop",
    "theme": "leos-original",
    "theme_color_a": "#00D9FF",
    "theme_color_b": "#E33BFF",
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


def validate_settings_values(
    values: object,
    *,
    require_complete: bool = False,
) -> dict[str, Any]:
    """Validate known LEOS preferences without reading or modifying a file."""
    if not isinstance(values, dict) or not values:
        raise ValueError("LEOS settings must be a non-empty dictionary")
    if require_complete and set(values) != set(DEFAULTS):
        raise ValueError("A complete LEOS settings snapshot must contain every known key")

    validated: dict[str, Any] = {}
    for key, value in values.items():
        if key not in DEFAULTS:
            raise KeyError(f"Unknown LEOS setting: {key}")
        if not isinstance(value, type(DEFAULTS[key])):
            raise TypeError(f"{key} must be {type(DEFAULTS[key]).__name__}")
        if key in _THEME_COLOR_KEYS:
            if _THEME_COLOR_PATTERN.fullmatch(value.strip()) is None:
                raise ValueError(f"Invalid hex color for {key}")
            value = value.strip().upper()
        allowed = ALLOWED_VALUES.get(key)
        if allowed is not None and value not in allowed:
            raise ValueError(f"Invalid value for {key}: {value}")
        if key == "notification_duration_seconds" and value not in {3, 5, 8}:
            raise ValueError(f"Invalid value for {key}: {value}")
        validated[key] = value
    return validated


class SettingsStore:
    """Stores user preferences in XDG_CONFIG_HOME without editing system files."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or xdg_config_home() / "leos" / "settings.json"
        self._values = DEFAULTS.copy()
        self.load()

    def validate_current_file(self) -> None:
        """Raise when an existing settings file cannot be read safely as JSON.

        A missing file is valid and represents first-run defaults. This check is
        intentionally separate from load(), which falls back to defaults for UI
        resilience and must not be mistaken for a verified backup source.
        """
        if self.path.is_symlink() or self.path.parent.is_symlink():
            raise OSError("LEOS settings path cannot be a symbolic link")
        if self.path.exists():
            _read_settings_file(self.path)

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
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError, RecursionError):
            return

        for key, default in DEFAULTS.items():
            value = loaded.get(key, default)
            if not isinstance(value, type(default)):
                continue
            if key in _THEME_COLOR_KEYS:
                if _THEME_COLOR_PATTERN.fullmatch(value.strip()) is None:
                    continue
                value = value.strip().upper()
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
        """Validate and persist one preference."""
        self.set_many({key: value})

    def set_many(self, updates: dict[str, Any]) -> None:
        """Atomically validate and persist a group of shared preferences."""
        if not isinstance(updates, dict) or not updates:
            raise ValueError("LEOS settings updates must be a non-empty dictionary")

        validated = validate_settings_values(updates)

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
                    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
                        raise ValueError(
                            "LEOS settings file is unreadable or too large; it was left untouched"
                        ) from exc
                self.load()
                self._values.update(validated)
                self.save()
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def replace_all(
        self,
        values: dict[str, Any],
        *,
        confirmed: bool = False,
        before_replace: Callable[[], None] | None = None,
    ) -> None:
        """Atomically replace the complete preference set after explicit confirmation.

        This recovery-only operation deliberately bypasses a corrupt existing JSON
        file, but still validates the replacement and serializes access with the
        same lock used by normal settings writes. The optional pre-replacement
        callback runs while that lock is held so callers can preserve the exact
        pre-restore state before the atomic replacement.
        """
        if confirmed is not True:
            raise PermissionError("Explicit confirmation is required to replace LEOS preferences")
        validated = validate_settings_values(values, require_complete=True)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.path.parent.is_symlink() or self.path.is_symlink():
            raise OSError("LEOS settings path cannot be a symbolic link")
        lock_path = self.path.with_name(self.path.name + ".lock")
        if lock_path.is_symlink():
            raise OSError("LEOS settings lock cannot be a symbolic link")
        with lock_path.open("a", encoding="utf-8") as lock:
            os.chmod(lock_path, 0o600)
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            previous = self._values
            try:
                # Refresh only after acquiring the cross-process lock. The
                # recovery callback and replacement observe one serialized
                # pre-restore settings state.
                self.load()
                if before_replace is not None:
                    if not callable(before_replace):
                        raise TypeError("before_replace must be callable")
                    before_replace()
                previous = self._values
                self._values = {**DEFAULTS, **validated}
                self.save()
            except Exception:
                self._values = previous
                raise
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
