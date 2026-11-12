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
import shutil
import stat
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from leos_core.paths import config_home as xdg_config_home, state_home as xdg_state_home

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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_manifest(path: Path) -> Any | None:
    """Read a bounded backup manifest; malformed or oversized files are ignored."""
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_BACKUP_MANIFEST_BYTES + 1)
        if len(raw) > MAX_BACKUP_MANIFEST_BYTES:
            return None
        return json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
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
        if source.is_symlink() or source.parent.is_symlink() or not source.is_file():
            raise FileNotFoundError("KDE Plasma layout configuration was not found")
        size = source.stat().st_size
        if size <= 0 or size > MAX_BACKUP_BYTES:
            raise ValueError("KDE Plasma configuration has an unsupported size")

        if self.backup_dir.is_symlink() or self.backup_dir.parent.is_symlink():
            raise ValueError("Symbolic-link backup directories are not accepted")
        self.backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.backup_dir, 0o700)
        backup_id = uuid.uuid4().hex
        backup_path = self.backup_dir / f"{backup_id}.bak"
        fd, temporary = tempfile.mkstemp(prefix="plasma.", suffix=".tmp", dir=self.backup_dir)
        try:
            with os.fdopen(fd, "wb") as dst, source.open("rb") as src:
                shutil.copyfileobj(src, dst)
                dst.flush()
                os.fsync(dst.fileno())
            os.chmod(temporary, 0o600)
            copied_size = Path(temporary).stat().st_size
            if copied_size <= 0 or copied_size > MAX_BACKUP_BYTES:
                raise ValueError("KDE Plasma configuration changed to an unsupported size")
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
            "size": backup_path.stat().st_size,
            "sha256": _sha256(backup_path),
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
                or backup_path.is_symlink()
                or not backup_path.is_file()
                or backup_path.stat().st_size > MAX_BACKUP_BYTES
                or backup_path.stat().st_size != manifest["size"]
                or _sha256(backup_path) != manifest["sha256"]
            ):
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
        if backup_path.is_symlink() or manifest_path.is_symlink():
            raise ValueError("Symbolic-link backups are not accepted")
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
        if not backup_path.is_file() or backup_path.stat().st_size > MAX_BACKUP_BYTES:
            raise ValueError("Plasma backup file is missing or too large")
        if backup_path.stat().st_size != manifest["size"] or _sha256(backup_path) != manifest["sha256"]:
            raise ValueError("Plasma backup integrity check failed")

        previous_backup: str | None = None
        if self.config_path.exists():
            previous_backup = self.create_backup()

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        mode = stat.S_IMODE(self.config_path.stat().st_mode) if self.config_path.exists() else 0o600
        fd, temporary = tempfile.mkstemp(prefix="plasma-restore.", suffix=".tmp", dir=self.config_path.parent)
        try:
            with os.fdopen(fd, "wb") as dst, backup_path.open("rb") as src:
                shutil.copyfileobj(src, dst)
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
