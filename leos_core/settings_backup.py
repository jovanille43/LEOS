"""Verified, private backups of LEOS user preferences."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from leos_core.json_utils import json_nesting_within_limit
from leos_core.paths import state_home as xdg_state_home
from leos_core.settings import DEFAULTS, MAX_SETTINGS_BYTES, SettingsStore, validate_settings_values

BACKUP_SCHEMA_VERSION = 1
_BACKUP_ID = re.compile(r"^[0-9a-f]{32}$")
MAX_BACKUP_MANIFEST_BYTES = 16 * 1024
MAX_BACKUP_MANIFESTS_SCANNED = 256


def _backup_root() -> Path:
    return xdg_state_home() / "leos" / "settings-backups"


def _read_regular_file(path: Path, maximum: int) -> bytes:
    """Read one bounded regular file without following a final symlink."""
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise OSError("Expected a regular backup file")
        if before.st_size <= 0 or before.st_size > maximum:
            raise ValueError("Backup file has an unsupported size")
        chunks: list[bytes] = []
        remaining = maximum + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        after = os.fstat(descriptor)
        if (
            len(data) > maximum
            or len(data) != before.st_size
            or before.st_dev != after.st_dev
            or before.st_ino != after.st_ino
            or before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
            or before.st_ctime_ns != after.st_ctime_ns
        ):
            raise OSError("Backup file changed while it was being read")
        return data
    finally:
        os.close(descriptor)


def _atomic_write(path: Path, data: bytes) -> None:
    fd, temporary = tempfile.mkstemp(prefix="settings-backup.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _decode_backup(data: bytes) -> dict[str, Any] | None:
    try:
        text = data.decode("utf-8")
        if not json_nesting_within_limit(text):
            return None
        payload = json.loads(text)
        if (
            not isinstance(payload, dict)
            or set(payload) != {"schema_version", "settings"}
            or type(payload.get("schema_version")) is not int
            or payload["schema_version"] != BACKUP_SCHEMA_VERSION
        ):
            return None
        return validate_settings_values(payload["settings"], require_complete=True)
    except (UnicodeError, json.JSONDecodeError, RecursionError, TypeError, ValueError, KeyError):
        return None


def _read_manifest(path: Path) -> Any | None:
    try:
        raw = _read_regular_file(path, MAX_BACKUP_MANIFEST_BYTES)
        text = raw.decode("utf-8")
        if not json_nesting_within_limit(text):
            return None
        return json.loads(text)
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError, RecursionError):
        return None


class SettingsBackupManager:
    """Create, verify and explicitly restore complete LEOS preference snapshots."""

    def __init__(
        self,
        settings: SettingsStore | None = None,
        backup_dir: Path | None = None,
    ) -> None:
        self.settings = settings or SettingsStore()
        self.backup_dir = backup_dir or _backup_root()

    def _ensure_backup_directory(self) -> None:
        for candidate in (self.backup_dir, *self.backup_dir.parents):
            if candidate.is_symlink():
                raise ValueError("Symbolic-link backup directories are not accepted")
        self.backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.backup_dir.is_symlink() or not self.backup_dir.is_dir():
            raise ValueError("Settings backup directory is unsafe")
        os.chmod(self.backup_dir, 0o700)

    def create_backup(self) -> str:
        values = self.settings.snapshot(tuple(DEFAULTS))
        validated = validate_settings_values(dict(zip(DEFAULTS, values)), require_complete=True)
        payload = {
            "schema_version": BACKUP_SCHEMA_VERSION,
            "settings": validated,
        }
        data = (json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        if len(data) > MAX_SETTINGS_BYTES:
            raise ValueError("LEOS preferences exceed the supported backup size")

        self._ensure_backup_directory()
        backup_id = uuid.uuid4().hex
        backup_path = self.backup_dir / f"{backup_id}.bak"
        manifest_path = self.backup_dir / f"{backup_id}.json"
        _atomic_write(backup_path, data)
        manifest = {
            "schema_version": BACKUP_SCHEMA_VERSION,
            "backup_id": backup_id,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        try:
            encoded_manifest = (json.dumps(manifest, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
            _atomic_write(manifest_path, encoded_manifest)
        except Exception:
            backup_path.unlink(missing_ok=True)
            raise
        return backup_id

    def _verified_backup(self, backup_id: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
        if not isinstance(backup_id, str) or not _BACKUP_ID.fullmatch(backup_id):
            return None
        if any(candidate.is_symlink() for candidate in (self.backup_dir, self.backup_dir.parent)):
            return None
        manifest_path = self.backup_dir / f"{backup_id}.json"
        backup_path = self.backup_dir / f"{backup_id}.bak"
        if manifest_path.is_symlink() or backup_path.is_symlink():
            return None
        manifest = _read_manifest(manifest_path)
        if (
            not isinstance(manifest, dict)
            or type(manifest.get("schema_version")) is not int
            or manifest.get("schema_version") != BACKUP_SCHEMA_VERSION
            or manifest.get("backup_id") != backup_id
            or type(manifest.get("size")) is not int
            or not isinstance(manifest.get("sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", manifest["sha256"]) is None
            or not isinstance(manifest.get("created_utc"), str)
            or len(manifest["created_utc"]) > 64
        ):
            return None
        try:
            data = _read_regular_file(backup_path, MAX_SETTINGS_BYTES)
        except (OSError, ValueError):
            return None
        if len(data) != manifest["size"] or hashlib.sha256(data).hexdigest() != manifest["sha256"]:
            return None
        values = _decode_backup(data)
        if values is None:
            return None
        return manifest, values

    def list_backups(self) -> list[dict[str, Any]]:
        if (
            self.backup_dir.is_symlink()
            or self.backup_dir.parent.is_symlink()
            or not self.backup_dir.is_dir()
        ):
            return []
        entries: list[dict[str, Any]] = []
        try:
            manifests = self.backup_dir.glob("*.json")
            for index, path in enumerate(manifests):
                if index >= MAX_BACKUP_MANIFESTS_SCANNED:
                    break
                backup_id = path.stem
                verified = self._verified_backup(backup_id)
                if verified is not None:
                    entries.append(verified[0])
        except OSError:
            return []
        return sorted(entries, key=lambda item: item["created_utc"], reverse=True)

    def latest_backup_id(self) -> str | None:
        entries = self.list_backups()
        return str(entries[0]["backup_id"]) if entries else None

    def restore_backup(self, backup_id: str, *, confirmed: bool = False) -> str:
        """Restore a verified snapshot after preserving the currently active preferences."""
        if confirmed is not True:
            raise PermissionError("Explicit confirmation is required to restore LEOS preferences")
        verified = self._verified_backup(backup_id)
        if verified is None:
            raise ValueError("LEOS settings backup is missing, unsafe or invalid")
        _manifest, values = verified
        recovery_backup_id = self.create_backup()
        self.settings.replace_all(values, confirmed=True)
        return recovery_backup_id
