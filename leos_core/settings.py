"""Small, safe JSON settings store shared by LEOS components."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

DEFAULTS: dict[str, Any] = {
    "last_mode": "desktop",
    "animations_enabled": True,
    "sounds_enabled": True,
    "gaming_overlay_enabled": True,
    "transition_app_policy": "ask",
}


class SettingsStore:
    """Stores user preferences in XDG_CONFIG_HOME without editing system files."""

    def __init__(self, path: Path | None = None) -> None:
        config_home = Path(
            os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
        )
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
            if isinstance(value, type(default)):
                self._values[key] = value

        if self._values["last_mode"] not in {"desktop", "gaming"}:
            self._values["last_mode"] = DEFAULTS["last_mode"]
        if self._values["transition_app_policy"] not in {"ask", "keep", "close"}:
            self._values["transition_app_policy"] = "ask"

    def get(self, key: str, default: Any = None) -> Any:
        return self._values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if key not in DEFAULTS:
            raise KeyError(f"Unknown LEOS setting: {key}")
        expected = type(DEFAULTS[key])
        if not isinstance(value, expected):
            raise TypeError(f"{key} must be {expected.__name__}")
        if key == "last_mode" and value not in {"desktop", "gaming"}:
            raise ValueError("last_mode must be 'desktop' or 'gaming'")
        if key == "transition_app_policy" and value not in {"ask", "keep", "close"}:
            raise ValueError("transition_app_policy must be ask, keep or close")
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
