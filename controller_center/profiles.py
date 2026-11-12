"""Safe, per-user storage for LEOS controller preferences."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from typing import Any

PROFILE_NAMES = ("auto", "standard", "xbox", "playstation", "nintendo", "custom")
MAX_PROFILE_FILE_BYTES = 256 * 1024
MAX_CONTROLLER_PROFILES = 128
MAX_AXIS_CENTERS = 64
MAX_AXIS_NAME_LENGTH = 48
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

    @contextmanager
    def _exclusive_lock(self) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.path.parent.is_symlink() or self.path.is_symlink():
            raise OSError("Controller profile path cannot be a symbolic link")
        lock_path = self.path.with_name(self.path.name + ".lock")
        if lock_path.is_symlink():
            raise OSError("Controller profile lock cannot be a symbolic link")
        with lock_path.open("a", encoding="utf-8") as lock:
            os.chmod(lock_path, 0o600)
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def _read(self, strict: bool = False) -> dict[str, Any]:
        if self.path.is_symlink() or self.path.parent.is_symlink():
            if strict:
                raise OSError("Controller profile path cannot be a symbolic link")
            return {"version": 1, "devices": {}}
        try:
            with self.path.open("rb") as stream:
                raw = stream.read(MAX_PROFILE_FILE_BYTES + 1)
            if len(raw) > MAX_PROFILE_FILE_BYTES:
                raise ValueError("Controller profile file is too large")
            payload = json.loads(raw.decode("utf-8"))
        except FileNotFoundError:
            return {"version": 1, "devices": {}}
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            if strict:
                raise ValueError("Controller profile file is unreadable or too large; it was left untouched") from exc
            return {"version": 1, "devices": {}}
        if (
            not isinstance(payload, dict)
            or type(payload.get("version")) is not int
            or payload.get("version") != 1
            or not isinstance(payload.get("devices"), dict)
            or len(payload["devices"]) > MAX_CONTROLLER_PROFILES
        ):
            if strict:
                raise ValueError("Controller profile file has an invalid format; it was left untouched")
            return {"version": 1, "devices": {}}
        return payload

    def get(self, device_id: str) -> dict[str, Any]:
        record = self._read()["devices"].get(device_id, {})
        if not isinstance(record, dict):
            record = {}
        return self._validated_record(record)

    @staticmethod
    def _validated_record(record: dict[str, Any]) -> dict[str, Any]:
        profile = record.get("profile", DEFAULT_PROFILE["profile"])
        if profile not in PROFILE_NAMES:
            profile = DEFAULT_PROFILE["profile"]
        deadzone = record.get("deadzone", DEFAULT_PROFILE["deadzone"])
        if type(deadzone) is not int or not 0 <= deadzone <= 40:
            deadzone = DEFAULT_PROFILE["deadzone"]
        centers = record.get("axis_centers", {})
        if not isinstance(centers, dict):
            centers = {}
        valid_centers = {
            axis: value for axis, value in centers.items()
            if (
                isinstance(axis, str) and 0 < len(axis) <= MAX_AXIS_NAME_LENGTH
                and type(value) is int and -65536 <= value <= 65536
            
        }
        return {"profile": profile, "deadzone": deadzone, "axis_centers": valid_centers}

    def update(self, device_id: str, **changes: Any) -> dict[str, Any]:
        if not isinstance(device_id, str) or not device_id or len(device_id) > 128:
            raise ValueError("Invalid controller identifier")
        with self._exclusive_lock():
            payload = self._read(strict=True)
            devices = payload["devices"]
            record = devices.get(device_id, {})
            if not isinstance(record, dict):
                record = {}
            current = self._validated_record(record)
            if "profile" in changes:
                if changes["profile"] not in PROFILE_NAMES:
                    raise ValueError("Unknown controller profile")
                current["profile"] = changes["profile"]
            if "deadzone" in changes:
                value = changes["deadzone"]
                if type(value) is not int or not 0 <= value <= 40:
                    raise ValueError("Deadzone must be an integer between 0 and 40")
                current["deadzone"] = value
            if "axis_centers" in changes:
                centers = changes["axis_centers"]
                if not isinstance(centers, dict):
                    raise ValueError("Axis centers must be a mapping")
                for axis, value in centers.items():
                    if (
                        not isinstance(axis, str) or not 0 < len(axis) <= MAX_AXIS_NAME_LENGTH
                        or type(value) is not int or not -65536 <= value <= 65536
                    ):
                        raise ValueError("Invalid axis center")
                    current["axis_centers"][axis] = value
                if len(current["axis_centers"]) > MAX_AXIS_CENTERS:
                    raise ValueError("Too many controller axis centers")
            devices[device_id] = current
            self._write(payload)
            return current

    def _write(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.path.parent.is_symlink() or self.path.is_symlink():
            raise OSError("Controller profile path cannot be a symbolic link")
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
