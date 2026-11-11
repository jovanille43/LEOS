"""Small, safe JSON settings store shared by LEOS applications."""

from __future__ import annotations

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
}

ALLOWED_VALUES = {
    "last_mode": {"desktop", "gaming"},
    "theme": {"leos-original", "light", "cyan", "magenta", "gaming"},
    "performance_profile": {"performance", "balanced", "quiet", "battery-saver"},
    "transition_app_policy": {"ask", "keep", "close"},
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
            self._values[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if key not in DEFAULTS:
            raise KeyError(f"Unknown LEOS setting: {key}")
        if not isinstance(value, type(DEFAULTS[key])):
            raise TypeError(f"{key} must be {type(DEFAULTS[key]).__name__}")
        allowed = ALLOWED_VALUES.get(key)
        if allowed is not None and value not in allowed:
            raise ValueError(f"Invalid value for {key}: {value}")
        self._values[key] = value
        self.save()

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
