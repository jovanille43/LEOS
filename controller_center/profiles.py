"""Safe, per-user storage for LEOS controller preferences."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

PROFILE_NAMES = ("auto", "standard", "xbox", "playstation", "nintendo", "custom")
from leos_core.paths import config_home as xdg_config_home


DEFAULT_PROFILE = {
    "profile": "auto",
    "deadzone": 8,
    "axis_centers": {},
}


def detect_controller_profile(name: str, vendor: int = 0, product: int = 0) -> str | None:
    """Identify common controller families without guessing unknown devices."""
    label = name.casefold()

    # Nintendo USB IDs for Switch Joy-Con and Pro controllers.
    if vendor == 0x057E and product in {0x2000, 0x2006, 0x2007, 0x2008, 0x2009}:
        return "nintendo"
    if any(token in label for token in ("nintendo", "joy-con", "joycon", "switch pro")):
        return "nintendo"

    # Sony: DualShock 3/4 and DualSense device IDs.
    if vendor == 0x054C and product in {0x0268, 0x05C4, 0x09CC, 0x0CE6, 0x0DF2}:
        return "playstation"
    if any(token in label for token in ("dualsense", "dualshock", "playstation", "ps3", "ps4", "ps5")):
        return "playstation"

    # Microsoft Xbox controllers; unknown devices keep the neutral layout.
    if vendor == 0x045E and product in {0x028E, 0x02EA, 0x0B00, 0x0B12}:
        return "xbox"
    if "xbox" in label:
        return "xbox"

    return None


def config_path() -> Path:
    root = xdg_config_home()
    return root / "leos" / "controllers.json"


def device_profile_id(
    name: str,
    vendor: int = 0,
    product: int = 0,
    phys: str = "",
    uniq: str = "",
    fallback_path: str = "",
) -> str:
    """Return a stable, non-reversible identifier for a connected controller."""
    stable_location = uniq or phys or fallback_path
    raw = f"{name}|{vendor:04x}|{product:04x}|{stable_location}"
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:24]


class ControllerProfileStore:
    """Store preferences only in the current user's config directory."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or config_path()

    def _read(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if payload.get("version") != 1 or not isinstance(payload.get("devices"), dict):
                return {"version": 1, "devices": {}}
            return payload
        except (OSError, json.JSONDecodeError, AttributeError):
            return {"version": 1, "devices": {}}

    def get(self, device_id: str) -> dict[str, Any]:
        record = self._read()["devices"].get(device_id, {})
        if not isinstance(record, dict):
            record = {}
        profile = record.get("profile", DEFAULT_PROFILE["profile"])
        if profile not in PROFILE_NAMES:
            profile = DEFAULT_PROFILE["profile"]
        deadzone = record.get("deadzone", DEFAULT_PROFILE["deadzone"])
        if not isinstance(deadzone, int) or not 0 <= deadzone <= 40:
            deadzone = DEFAULT_PROFILE["deadzone"]
        centers = record.get("axis_centers", {})
        if not isinstance(centers, dict):
            centers = {}
        valid_centers = {
            str(axis): int(value)
            for axis, value in centers.items()
            if isinstance(axis, str) and isinstance(value, int) and -65536 <= value <= 65536
        }
        return {"profile": profile, "deadzone": deadzone, "axis_centers": valid_centers}

    def update(self, device_id: str, **changes: Any) -> dict[str, Any]:
        current = self.get(device_id)
        if "profile" in changes:
            if changes["profile"] not in PROFILE_NAMES:
                raise ValueError("Unknown controller profile")
            current["profile"] = changes["profile"]
        if "deadzone" in changes:
            value = changes["deadzone"]
            if not isinstance(value, int) or not 0 <= value <= 40:
                raise ValueError("Deadzone must be an integer between 0 and 40")
            current["deadzone"] = value
        if "axis_centers" in changes:
            centers = changes["axis_centers"]
            if not isinstance(centers, dict):
                raise ValueError("Axis centers must be a mapping")
            current["axis_centers"].update({
                str(axis): int(value)
                for axis, value in centers.items()
                if isinstance(axis, str) and isinstance(value, int) and -65536 <= value <= 65536
            })

        payload = self._read()
        payload["devices"][device_id] = current
        self._write(payload)
        return current

    def _write(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".controllers-", dir=self.path.parent)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            os.chmod(self.path, 0o600)
        except Exception:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise
