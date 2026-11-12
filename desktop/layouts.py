"""Safe, local LEOS desktop layout preferences.

This module records the desired layout. Applying a supported profile is
handled separately by the Plasma adapter after a private backup and explicit
user confirmation.
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

from leos_core.paths import config_home as xdg_config_home
from leos_core.json_utils import json_nesting_within_limit


POSITIONS = frozenset({"bottom", "left", "right", "top"})
ALIGNMENTS = frozenset({"left", "center", "right"})
MAX_LAYOUT_FILE_BYTES = 64 * 1024


def _config_path() -> Path:
    root = xdg_config_home()
    return root / "leos" / "desktop-layout.json"


def validate_layout(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != set(DEFAULT_LAYOUT):
        return False
    if type(value.get("schema_version")) is not int or value["schema_version"] != 1:
        return False
    profile = value.get("profile")
    if not isinstance(profile, str) or profile not in (set(PROFILES) | {"custom"}):
        return False
    dock = value.get("dock")
    if not isinstance(dock, dict) or set(dock) != {"enabled", "position", "alignment", "auto_hide"}:
        return False
    if not all(type(dock.get(k)) is bool for k in ("enabled", "auto_hide")):
        return False
    position = dock.get("position")
    alignment = dock.get("alignment")
    if not isinstance(position, str) or position not in POSITIONS:
        return False
    if not isinstance(alignment, str) or alignment not in ALIGNMENTS:
        return False
    return isinstance(value.get("widgets_enabled"), bool)


class DesktopLayoutStore:
    """Atomic, permission-restricted store for desired desktop layout."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _config_path()
        self._layout = json.loads(json.dumps(DEFAULT_LAYOUT))
        self.load()

    def load(self) -> None:
        if self.path.is_symlink() or self.path.parent.is_symlink():
            return
        try:
            with self.path.open("rb") as stream:
                raw = stream.read(MAX_LAYOUT_FILE_BYTES + 1)
            if len(raw) > MAX_LAYOUT_FILE_BYTES:
                return
            text = raw.decode("utf-8")
            if not json_nesting_within_limit(text):
                return
            loaded = json.loads(text)
        except (OSError, UnicodeError, json.JSONDecodeError, RecursionError):
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
            if key == "position" and (not isinstance(value, str) or value not in POSITIONS):
                raise ValueError("Invalid dock position")
            if key == "alignment" and (not isinstance(value, str) or value not in ALIGNMENTS):
                raise ValueError("Invalid dock alignment")
            dock[key] = value
        self._layout["dock"] = dock
        self._layout["profile"] = "custom"
        # "custom" is an explicit state, not a selectable built-in preset.
        self.save()

    def set_widgets_enabled(self, enabled: bool) -> None:
        if not isinstance(enabled, bool):
            raise TypeError("enabled must be a boolean")
        self._layout["widgets_enabled"] = enabled
        self._layout["profile"] = "custom"
        self.save()

    def save(self) -> None:
        if not validate_layout(self._layout):
            raise ValueError("Refusing to save invalid LEOS desktop layout")

        payload = (json.dumps(self._layout, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        if len(payload) > MAX_LAYOUT_FILE_BYTES:
            raise ValueError("LEOS desktop layout exceeds its storage limit")
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.path.parent.is_symlink() or self.path.is_symlink():
            raise OSError("LEOS desktop layout path cannot be a symbolic link")
        os.chmod(self.path.parent, 0o700)
        fd, temp_name = tempfile.mkstemp(
            prefix="desktop-layout.", suffix=".tmp", dir=self.path.parent
        )
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, self.path)
        finally:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass
