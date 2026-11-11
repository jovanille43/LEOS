"""Safe, per-user storage for LEOS controller preferences."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

PROFILE_NAMES = ("standard", "xbox", "playstation", "nintendo", "custom")
DEFAULT_PROFILE = {
    "profile": "standard",
    "deadzone": 8,
    "axis_centers": {},
}


def config_path() -> Path:
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
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
    stable_location = phys or uniq or fallback_path
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
