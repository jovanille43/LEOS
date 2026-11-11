"""Safe, local LEOS desktop layout preferences.

This module records the user's desired layout without applying changes to KDE
Plasma. A future Plasma adapter must back up the current panel configuration
and require explicit approval before applying any profile.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_LAYOUT: dict[str, Any] = {
    "schema_version": 1,
    "profile": "leos-default",
    "dock": {
        "enabled": True,
        "position": "bottom",
        "alignment": "center",
        "auto_hide": False,
    },
    "widgets_enabled": False,
}

PROFILES: dict[str, dict[str, Any]] = {
    "leos-default": {
        "dock": {"enabled": True, "position": "bottom", "alignment": "center", "auto_hide": False},
        "widgets_enabled": False,
    },
    "minimal": {
        "dock": {"enabled": True, "position": "bottom", "alignment": "center", "auto_hide": True},
        "widgets_enabled": False,
    },
    "workspace": {
        "dock": {"enabled": True, "position": "left", "alignment": "center", "auto_hide": False},
        "widgets_enabled": True,
    },
}

POSITIONS = frozenset({"bottom", "left", "right", "top"})
ALIGNMENTS = frozenset({"left", "center", "right"})


def _config_path() -> Path:
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "leos" / "desktop-layout.json"


def validate_layout(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != set(DEFAULT_LAYOUT):
        return False
    if value.get("schema_version") != 1 or value.get("profile") not in PROFILES:
        return False
    dock = value.get("dock")
    if not isinstance(dock, dict) or set(dock) != {"enabled", "position", "alignment", "auto_hide"}:
        return False
    if not all(isinstance(dock.get(k), bool) for k in ("enabled", "auto_hide")):
        return False
    if dock.get("position") not in POSITIONS or dock.get("alignment") not in ALIGNMENTS:
        return False
    return isinstance(value.get("widgets_enabled"), bool)


class DesktopLayoutStore:
    """Atomic, permission-restricted store for desired desktop layout."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _config_path()
        self._layout = json.loads(json.dumps(DEFAULT_LAYOUT))
        self.load()

    def load(self) -> None:
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if validate_layout(loaded):
            self._layout = loaded

    def get(self, key: str | None = None) -> Any:
        if key is None:
            return json.loads(json.dumps(self._layout))
        if key == "dock":
            return dict(self._layout["dock"])
        return self._layout.get(key)

    def apply_profile(self, profile: str) -> None:
        if profile not in PROFILES:
            raise ValueError(f"Unknown LEOS desktop profile: {profile}")
        selected = PROFILES[profile]
        self._layout = {
            "schema_version": 1,
            "profile": profile,
            "dock": dict(selected["dock"]),
            "widgets_enabled": selected["widgets_enabled"],
        }
        self.save()

    def set_dock(self, *, enabled: bool | None = None, position: str | None = None,
                 alignment: str | None = None, auto_hide: bool | None = None) -> None:
        dock = dict(self._layout["dock"])
        changes = {"enabled": enabled, "position": position,
                   "alignment": alignment, "auto_hide": auto_hide}
        for key, value in changes.items():
            if value is None:
                continue
            if key in {"enabled", "auto_hide"} and not isinstance(value, bool):
                raise TypeError(f"{key} must be a boolean")
            if key == "position" and value not in POSITIONS:
                raise ValueError("Invalid dock position")
            if key == "alignment" and value not in ALIGNMENTS:
                raise ValueError("Invalid dock alignment")
            dock[key] = value
        self._layout["dock"] = dock
        self._layout["profile"] = "custom"
        # "custom" is an explicit state, not a selectable built-in preset.
        self.save(allow_custom=True)

    def set_widgets_enabled(self, enabled: bool) -> None:
        if not isinstance(enabled, bool):
            raise TypeError("enabled must be a boolean")
        self._layout["widgets_enabled"] = enabled
        self._layout["profile"] = "custom"
        self.save(allow_custom=True)

    def save(self, *, allow_custom: bool = False) -> None:
        if allow_custom:
            valid_profiles = set(PROFILES) | {"custom"}
            candidate = dict(self._layout)
            if candidate.get("profile") == "custom":
                candidate_for_validation = dict(candidate)
                candidate_for_validation["profile"] = "leos-default"
            else:
                candidate_for_validation = candidate
            if candidate.get("profile") not in valid_profiles or not validate_layout(candidate_for_validation):
                raise ValueError("Refusing to save invalid LEOS desktop layout")
        elif not validate_layout(self._layout):
            raise ValueError("Refusing to save invalid LEOS desktop layout")

        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self._layout, indent=2, ensure_ascii=False) + "\n"
        fd, temp_name = tempfile.mkstemp(prefix="desktop-layout.", suffix=".tmp", dir=self.path.parent)
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
