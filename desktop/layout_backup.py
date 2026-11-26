"""Verified, private backups of LEOS desktop layout preferences.

These snapshots cover only desktop-layout.json. KDE Plasma applet state is
managed separately by PlasmaBackupManager.
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

from leos_core.json_utils import json_nesting_within_limit
from leos_core.paths import state_home as xdg_state_home
from desktop.layouts import (
    MAX_LAYOUT_FILE_BYTES,
    DesktopLayoutStore,
    validate_layout,
)

BACKUP_SCHEMA_VERSION = 1
_BACKUP_ID = re.compile(r"^[0-9a-f]{32}$")
MAX_BACKUP_BYTES = MAX_LAYOUT_FILE_BYTES + 2048
MAX_BACKUP_MANIFEST_BYTES = 16 * 1024
MAX_BACKUP_MANIFESTS_SCANNED = 256
MAX_RETAINED_BACKUPS = 20


def _backup_root() -> Path:
    return xdg_state_home() / "leos" / "desktop-layout-backups"


def _reject_symlink_components(path: Path) -> None:
    for candidate in (path, *path.parents):
        if candidate.is_symlink():
            raise ValueError("Symbolic-link backup paths are not accepted")


def _read_regular_file(path: Path, maximum: int) -> bytes:
    """Read one stable, bounded regular file without following symlinks."""
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
    descriptor, temporary = tempfile.mkstemp(
        prefix="desktop-layout-backup.", suffix=".tmp", dir=path.parent
    )
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(
            path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
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
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        return None
    if (
        not isinstance(payload, dict)
        or set(payload) != {"schema_version", "layout"}
        or type(payload.get("schema_version")) is not int
        or payload["schema_version"] != BACKUP_SCHEMA_VERSION
        or not validate_layout(payload.get("layout"))
    ):
        return None
    return payload["layout"]


def _decode_manifest(data: bytes, backup_id: str) -> dict[str, Any] | None:
    try:
        text = data.decode("utf-8")
        if not json_nesting_within_limit(text):
            return None
        manifest = json.loads(text)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        return None
    if (
        not isinstance(manifest, dict)
        or set(manifest) != {
            "schema_version", "backup_id", "created_utc", "size",
            "sha256", "layout_schema_version",
        }
        or type(manifest.get("schema_version")) is not int
        or manifest["schema_version"] != BACKUP_SCHEMA_VERSION
        or manifest.get("backup_id") != backup_id
        or not isinstance(manifest.get("created_utc"), str)
        or type(manifest.get("size")) is not int
        or manifest["size"] <= 0
        or manifest["size"] > MAX_BACKUP_BYTES
        or type(manifest.get("layout_schema_version")) is not int
        or manifest["layout_schema_version"] != 1
        or not isinstance(manifest.get("sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", manifest["sha256"]) is None
    ):
        return None
    return manifest


class DesktopLayoutBackupManager:
    """Create, verify, import, export and explicitly restore layout snapshots."""

    def __init__(
        self,
        store: DesktopLayoutStore | None = None,
        backup_dir: Path | None = None,
    ) -> None:
        self.store = store or DesktopLayoutStore()
        self.backup_dir = backup_dir or _backup_root()

    def _ensure_backup_directory(self) -> None:
        _reject_symlink_components(self.backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.backup_dir.is_symlink() or not self.backup_dir.is_dir():
            raise ValueError("Desktop layout backup directory is unsafe")
        os.chmod(self.backup_dir, 0o700)

    def _create_backup_for_layout(
        self, layout: dict[str, Any], *, preserve_backup_ids: set[str] | None = None
    ) -> str:
        if not validate_layout(layout):
            raise ValueError("Refusing to back up an invalid desktop layout")
        payload = {
            "schema_version": BACKUP_SCHEMA_VERSION,
            "layout": layout,
        }
        data = (
            json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        if len(data) > MAX_BACKUP_BYTES:
            raise ValueError("LEOS desktop layout exceeds its backup size limit")

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
            "layout_schema_version": 1,
        }
        try:
            encoded_manifest = (
                json.dumps(manifest, sort_keys=True, ensure_ascii=False) + "\n"
            ).encode("utf-8")
            _atomic_write(manifest_path, encoded_manifest)
        except Exception:
            backup_path.unlink(missing_ok=True)
            raise
        self._prune_old_backups(preserve_backup_ids=preserve_backup_ids or set())
        return backup_id

    def create_backup(self, *, preserve_backup_ids: set[str] | None = None) -> str:
        """Back up the current persisted layout; reject corruption, never defaults."""
        persisted = self.store.validate_current_file()
        layout = persisted if persisted is not None else self.store.get()
        return self._create_backup_for_layout(
            layout, preserve_backup_ids=preserve_backup_ids
        )

    def _verified_backup(
        self, backup_id: str
    ) -> tuple[dict[str, Any], dict[str, Any], bytes, bytes] | None:
        if not isinstance(backup_id, str) or _BACKUP_ID.fullmatch(backup_id) is None:
            return None
        manifest_path = self.backup_dir / f"{backup_id}.json"
        backup_path = self.backup_dir / f"{backup_id}.bak"
        try:
            _reject_symlink_components(self.backup_dir)
            manifest_data = _read_regular_file(manifest_path, MAX_BACKUP_MANIFEST_BYTES)
            backup_data = _read_regular_file(backup_path, MAX_BACKUP_BYTES)
        except (OSError, ValueError):
            return None
        manifest = _decode_manifest(manifest_data, backup_id)
        layout = _decode_backup(backup_data)
        if (
            manifest is None
            or layout is None
            or len(backup_data) != manifest["size"]
            or hashlib.sha256(backup_data).hexdigest() != manifest["sha256"]
        ):
            return None
        return manifest, layout, backup_data, manifest_data

    def list_backups(self) -> list[dict[str, Any]]:
        try:
            _reject_symlink_components(self.backup_dir)
        except ValueError:
            return []
        if not self.backup_dir.is_dir():
            return []
        entries: list[dict[str, Any]] = []
        try:
            manifests = self.backup_dir.glob("*.json")
            for index, path in enumerate(manifests):
                if index >= MAX_BACKUP_MANIFESTS_SCANNED:
                    break
                backup_id = path.stem
                if path.is_symlink() or _BACKUP_ID.fullmatch(backup_id) is None:
                    continue
                verified = self._verified_backup(backup_id)
                if verified is not None:
                    entries.append(verified[0])
        except OSError:
            return []
        return sorted(
            entries, key=lambda item: str(item.get("created_utc", "")), reverse=True
        )

    def latest_backup_id(self) -> str | None:
        entries = self.list_backups()
        return str(entries[0]["backup_id"]) if entries else None

    def _prune_old_backups(self, *, preserve_backup_ids: set[str]) -> None:
        entries = self.list_backups()
        excess = max(0, len(entries) - MAX_RETAINED_BACKUPS)
        for entry in reversed(entries):
            if excess <= 0:
                break
            backup_id = str(entry.get("backup_id", ""))
            if backup_id in preserve_backup_ids or _BACKUP_ID.fullmatch(backup_id) is None:
                continue
            for suffix in (".bak", ".json"):
                path = self.backup_dir / f"{backup_id}{suffix}"
                if path.is_symlink():
                    continue
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    continue
            excess -= 1

    @staticmethod
    def _write_new_file(directory: Path, filename: str, data: bytes) -> Path:
        target = directory / filename
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(target, flags, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return target

    def export_backup(
        self, backup_id: str, destination_directory: Path | str
    ) -> tuple[Path, Path]:
        verified = self._verified_backup(backup_id)
        if verified is None:
            raise ValueError("LEOS desktop layout backup is missing or invalid")
        destination = Path(destination_directory).expanduser()
        if not destination.is_absolute():
            raise ValueError("Export destination must be an absolute directory")
        _reject_symlink_components(destination)
        try:
            destination = destination.resolve(strict=True)
        except OSError:
            raise ValueError("Export destination is unavailable") from None
        if not destination.is_dir():
            raise ValueError("Export destination is not a directory")

        _, _, backup_data, manifest_data = verified
        backup_name = f"{backup_id}.bak"
        manifest_name = f"{backup_id}.json"
        targets = (destination / backup_name, destination / manifest_name)
        if any(path.exists() or path.is_symlink() for path in targets):
            raise FileExistsError("An export with this backup identifier already exists")
        created: list[Path] = []
        try:
            created.append(self._write_new_file(destination, backup_name, backup_data))
            created.append(self._write_new_file(destination, manifest_name, manifest_data))
        except Exception:
            for path in created:
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise
        return targets

    def import_backup(self, manifest_path: Path | str) -> str:
        source_manifest = Path(manifest_path).expanduser()
        if (
            not source_manifest.is_absolute()
            or source_manifest.suffix.lower() != ".json"
        ):
            raise ValueError("Selected LEOS layout manifest path is invalid")
        _reject_symlink_components(source_manifest)
        try:
            source_directory = source_manifest.parent.resolve(strict=True)
        except OSError:
            raise ValueError("Selected LEOS layout backup folder is unavailable") from None
        source_manifest = source_directory / source_manifest.name
        backup_id = source_manifest.stem
        if _BACKUP_ID.fullmatch(backup_id) is None:
            raise ValueError("Selected LEOS layout manifest has an invalid identifier")
        try:
            manifest_data = _read_regular_file(source_manifest, MAX_BACKUP_MANIFEST_BYTES)
            backup_data = _read_regular_file(
                source_directory / f"{backup_id}.bak", MAX_BACKUP_BYTES
            )
        except (OSError, ValueError):
            raise ValueError("Selected LEOS layout backup files are unavailable or unsafe") from None
        manifest = _decode_manifest(manifest_data, backup_id)
        layout = _decode_backup(backup_data)
        if (
            manifest is None
            or layout is None
            or len(backup_data) != manifest["size"]
            or hashlib.sha256(backup_data).hexdigest() != manifest["sha256"]
        ):
            raise ValueError("Selected LEOS layout backup failed integrity validation")

        self._ensure_backup_directory()
        if self._verified_backup(backup_id) is not None or any(
            (self.backup_dir / f"{backup_id}{suffix}").exists()
            or (self.backup_dir / f"{backup_id}{suffix}").is_symlink()
            for suffix in (".bak", ".json")
        ):
            raise FileExistsError("This LEOS layout backup already exists")
        created: list[Path] = []
        try:
            created.append(self._write_new_file(self.backup_dir, f"{backup_id}.bak", backup_data))
            created.append(self._write_new_file(self.backup_dir, f"{backup_id}.json", manifest_data))
        except Exception:
            for path in created:
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise
        self._prune_old_backups(preserve_backup_ids={backup_id})
        return backup_id

    def restore_backup(self, backup_id: str, *, confirmed: bool = False) -> str:
        """Restore a verified layout after preserving the current valid state."""
        if confirmed is not True:
            raise PermissionError("Explicit confirmation is required to restore the desktop layout")
        verified = self._verified_backup(backup_id)
        if verified is None:
            raise ValueError("LEOS desktop layout backup is missing, unsafe or invalid")
        _, layout, backup_data, manifest_data = verified

        # A corrupt, oversized or symlinked current layout blocks restoration.
        # Never replace the original file or back up silent fallback defaults.
        self.store.validate_current_file()
        recovery_backup_id = self.create_backup(preserve_backup_ids={backup_id})
        rechecked = self._verified_backup(backup_id)
        if (
            rechecked is None
            or rechecked[2] != backup_data
            or rechecked[3] != manifest_data
        ):
            raise ValueError("LEOS desktop layout backup changed during restoration")
        self.store.replace_all(layout, confirmed=True)
        return recovery_backup_id
