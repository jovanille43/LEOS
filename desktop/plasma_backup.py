"""Safe backup and explicitly confirmed restore for KDE Plasma layout config.

This module does not apply LEOS layouts or edit Plasma configuration during
normal operation. It only creates verifiable backups and restores one after
explicit caller confirmation, first preserving the current file.
"""
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

from leos_core.paths import config_home as xdg_config_home, state_home as xdg_state_home
from leos_core.json_utils import json_nesting_within_limit

BACKUP_SCHEMA_VERSION = 1
_BACKUP_ID = re.compile(r"^[0-9a-f]{32}$")
MAX_BACKUP_BYTES = 32 * 1024 * 1024
MAX_BACKUP_MANIFEST_BYTES = 64 * 1024
MAX_BACKUP_MANIFESTS_SCANNED = 1000


def _config_root() -> Path:
    return xdg_config_home()


def _backup_root() -> Path:
    state = xdg_state_home()
    return state / "leos" / "plasma-backups"


def _read_regular_file(path: Path, maximum: int) -> bytes:
    """Read one bounded regular file without following a final symlink."""
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise OSError("Expected a regular file")
        if before.st_size <= 0 or before.st_size > maximum:
            raise ValueError("File has an unsupported size")
        chunks: list[bytes] = []
        remaining = maximum + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
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
            raise OSError("File changed while it was being read")
        return data
    finally:
        os.close(descriptor)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_manifest(path: Path) -> Any | None:
    """Read a bounded, regular backup manifest without following symlinks."""
    try:
        raw = _read_regular_file(path, MAX_BACKUP_MANIFEST_BYTES)
        text = raw.decode("utf-8")
        if not json_nesting_within_limit(text):
            return None
        return json.loads(text)
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError, RecursionError):
        return None


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    fd, temporary = tempfile.mkstemp(prefix="manifest.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


class PlasmaBackupManager:
    """Create and verify private backups of the user's Plasma applet layout."""

    def __init__(self, config_path: Path | None = None, backup_dir: Path | None = None) -> None:
        self.config_path = config_path or _config_root() / "plasma-org.kde.plasma.desktop-appletsrc"
        self.backup_dir = backup_dir or _backup_root()

    def create_backup(self) -> str:
        source = self.config_path
        if source.is_symlink() or source.parent.is_symlink():
            raise FileNotFoundError("KDE Plasma layout configuration was not found")
        try:
            source_data = _read_regular_file(source, MAX_BACKUP_BYTES)
        except FileNotFoundError:
            raise FileNotFoundError("KDE Plasma layout configuration was not found") from None
        except ValueError:
            raise ValueError("KDE Plasma configuration has an unsupported size") from None

        if self.backup_dir.is_symlink() or self.backup_dir.parent.is_symlink():
            raise ValueError("Symbolic-link backup directories are not accepted")
        self.backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.backup_dir, 0o700)
        backup_id = uuid.uuid4().hex
        backup_path = self.backup_dir / f"{backup_id}.bak"
        fd, temporary = tempfile.mkstemp(prefix="plasma.", suffix=".tmp", dir=self.backup_dir)
        try:
            with os.fdopen(fd, "wb") as dst:
                dst.write(source_data)
                dst.flush()
                os.fsync(dst.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, backup_path)
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass

        manifest = {
            "schema_version": BACKUP_SCHEMA_VERSION,
            "backup_id": backup_id,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "size": len(source_data),
            "sha256": _sha256(source_data),
        }
        try:
            _atomic_json(self.backup_dir / f"{backup_id}.json", manifest)
        except Exception:
            backup_path.unlink(missing_ok=True)
            raise
        return backup_id

    def list_backups(self) -> list[dict[str, Any]]:
        if (
            self.backup_dir.is_symlink()
            or self.backup_dir.parent.is_symlink()
            or not self.backup_dir.is_dir()
        ):
            return []
        entries: list[dict[str, Any]] = []
        for index, manifest_path in enumerate(self.backup_dir.glob("*.json")):
            if index >= MAX_BACKUP_MANIFESTS_SCANNED:
                break
            if manifest_path.is_symlink() or not _BACKUP_ID.fullmatch(manifest_path.stem):
                continue
            manifest = _read_manifest(manifest_path)
            if manifest is None:
                continue
            backup_path = self.backup_dir / f"{manifest_path.stem}.bak"
            if (
                not isinstance(manifest, dict)
                or type(manifest.get("schema_version")) is not int
                or manifest.get("schema_version") != BACKUP_SCHEMA_VERSION
                or manifest.get("backup_id") != manifest_path.stem
                or type(manifest.get("size")) is not int
                or not isinstance(manifest.get("sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", manifest["sha256"])
            ):
                continue
            try:
                backup_data = _read_regular_file(backup_path, MAX_BACKUP_BYTES)
            except (OSError, ValueError):
                continue
            if len(backup_data) != manifest["size"] or _sha256(backup_data) != manifest["sha256"]:
                continue
            entries.append(manifest)
        return sorted(entries, key=lambda item: str(item.get("created_utc", "")), reverse=True)

    def latest_backup_id(self) -> str | None:
        entries = self.list_backups()
        return str(entries[0]["backup_id"]) if entries else None

    def restore_backup(self, backup_id: str, *, confirmed: bool = False) -> str | None:
        """Restore a verified backup, preserving the current config first.

        Returns the backup ID created from the pre-restore current config, if it
        existed. confirmed=True is mandatory and must come from an explicit
        user action in the calling application.
        """
        if confirmed is not True:
            raise PermissionError("Explicit confirmation is required to restore Plasma configuration")
        if not isinstance(backup_id, str) or not _BACKUP_ID.fullmatch(backup_id):
            raise ValueError("Invalid Plasma backup identifier")

        if self.backup_dir.is_symlink() or self.backup_dir.parent.is_symlink():
            raise ValueError("Symbolic-link backup directories are not accepted")
        if self.config_path.parent.is_symlink():
            raise ValueError("Symbolic-link Plasma configuration directories are not accepted")
        backup_path = self.backup_dir / f"{backup_id}.bak"
        manifest_path = self.backup_dir / f"{backup_id}.json"
        manifest = _read_manifest(manifest_path)
        if manifest is None:
            raise FileNotFoundError("Plasma backup manifest is unavailable")
        if (
            not isinstance(manifest, dict)
            or type(manifest.get("schema_version")) is not int
            or manifest.get("schema_version") != BACKUP_SCHEMA_VERSION
            or manifest.get("backup_id") != backup_id
            or type(manifest.get("size")) is not int
            or not isinstance(manifest.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", manifest["sha256"])
        ):
            raise ValueError("Invalid Plasma backup manifest")
        try:
            backup_data = _read_regular_file(backup_path, MAX_BACKUP_BYTES)
        except (OSError, ValueError):
            raise ValueError("Plasma backup file is missing, unsafe, or too large") from None
        if len(backup_data) != manifest["size"] or _sha256(backup_data) != manifest["sha256"]:
            raise ValueError("Plasma backup integrity check failed")

        previous_backup: str | None = None
        if self.config_path.exists():
            previous_backup = self.create_backup()

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        mode = stat.S_IMODE(self.config_path.stat().st_mode) if self.config_path.exists() else 0o600
        fd, temporary = tempfile.mkstemp(prefix="plasma-restore.", suffix=".tmp", dir=self.config_path.parent)
        try:
            with os.fdopen(fd, "wb") as dst:
                dst.write(backup_data)
                dst.flush()
                os.fsync(dst.fileno())
            os.chmod(temporary, mode)
            os.replace(temporary, self.config_path)
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
        return previous_backup
