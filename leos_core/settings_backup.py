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
MAX_RETAINED_BACKUPS = 20


def _backup_root() -> Path:
    return xdg_state_home() / "leos" / "settings-backups"


def _read_regular_file(path: Path, maximum: int, *, allow_empty: bool = False) -> bytes:
    """Read one bounded regular file without following a final symlink."""
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise OSError("Expected a regular backup file")
        if (before.st_size <= 0 and not allow_empty) or before.st_size > maximum:
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
        # SettingsStore.load() deliberately falls back to defaults on unreadable
        # input. Never turn those fallback values into a misleading backup.
        self.settings.validate_current_file()
        return self._create_backup()

    def _create_backup(self, *, preserve_backup_ids: set[str] | None = None) -> str:
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
        self._prune_old_backups(preserve_backup_ids=preserve_backup_ids or set())
        return backup_id

    def _prune_old_backups(self, *, preserve_backup_ids: set[str] | None = None) -> None:
        """Retain a bounded set of verified restore points, honoring active restores."""
        entries = self.list_backups()
        excess = max(0, len(entries) - MAX_RETAINED_BACKUPS)
        preserved = preserve_backup_ids or set()
        for entry in reversed(entries):
            if excess <= 0:
                break
            backup_id = str(entry.get("backup_id", ""))
            if backup_id in preserved or _BACKUP_ID.fullmatch(backup_id) is None:
                continue
            for suffix in (".bak", ".json"):
                path = self.backup_dir / f"{backup_id}{suffix}"
                if path.is_symlink():
                    continue
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    # A failed cleanup must never invalidate the new backup.
                    continue
            excess -= 1

    @staticmethod
    def _write_new_export_file(directory: Path, filename: str, data: bytes) -> Path:
        """Create one export file without following or overwriting an existing path."""
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
            try:
                target.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        return target

    def export_backup(self, backup_id: str, destination_directory: Path | str) -> tuple[Path, Path]:
        """Export one verified backup and its manifest to an existing external folder."""
        verified = self._verified_backup(backup_id)
        if verified is None:
            raise ValueError("LEOS settings backup is missing, unsafe or invalid")

        destination = Path(destination_directory).expanduser()
        if not destination.is_absolute():
            raise ValueError("Export destination must be an absolute directory")
        if destination.is_symlink():
            raise ValueError("Symbolic-link export directories are not accepted")
        try:
            destination = destination.resolve(strict=True)
        except OSError:
            raise ValueError("Export destination is unavailable") from None
        if not destination.is_dir():
            raise ValueError("Export destination is not a directory")

        manifest_path = self.backup_dir / f"{backup_id}.json"
        backup_path = self.backup_dir / f"{backup_id}.bak"
        manifest_data = _read_regular_file(manifest_path, MAX_BACKUP_MANIFEST_BYTES)
        backup_data = _read_regular_file(backup_path, MAX_SETTINGS_BYTES)
        manifest, values = verified
        try:
            exported_manifest = json.loads(manifest_data.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError, RecursionError):
            raise ValueError("LEOS settings manifest changed during export") from None
        if (
            exported_manifest != manifest
            or len(backup_data) != manifest["size"]
            or hashlib.sha256(backup_data).hexdigest() != manifest["sha256"]
            or values is None
        ):
            raise ValueError("LEOS settings backup changed during export")

        backup_name = f"{backup_id}.bak"
        manifest_name = f"{backup_id}.json"
        targets = (destination / backup_name, destination / manifest_name)
        if any(path.exists() or path.is_symlink() for path in targets):
            raise FileExistsError("An export with this backup identifier already exists")

        created: list[Path] = []
        try:
            created.append(self._write_new_export_file(destination, backup_name, backup_data))
            created.append(self._write_new_export_file(destination, manifest_name, manifest_data))
        except Exception:
            for path in created:
                try:
                    if not path.is_symlink() and path.is_file():
                        path.unlink()
                except OSError:
                    pass
            raise
        return targets

    def import_backup(self, manifest_path: Path | str) -> str:
        """Import a backup selected by its JSON manifest after full verification."""
        source_manifest = Path(manifest_path).expanduser()
        if (
            not source_manifest.is_absolute()
            or source_manifest.suffix.lower() != ".json"
            or source_manifest.is_symlink()
            or source_manifest.parent.is_symlink()
        ):
            raise ValueError("Selected LEOS backup manifest path is invalid")
        try:
            source_directory = source_manifest.parent.resolve(strict=True)
            source_manifest = source_directory / source_manifest.name
        except OSError:
            raise ValueError("Selected LEOS backup folder is unavailable") from None

        backup_id = source_manifest.stem
        if _BACKUP_ID.fullmatch(backup_id) is None:
            raise ValueError("Selected LEOS backup manifest has an invalid identifier")
        backup_path = source_directory / f"{backup_id}.bak"
        if backup_path.is_symlink():
            raise ValueError("Symbolic-link LEOS backup files are not accepted")

        try:
            manifest_data = _read_regular_file(source_manifest, MAX_BACKUP_MANIFEST_BYTES)
            backup_data = _read_regular_file(backup_path, MAX_SETTINGS_BYTES)
            manifest_text = manifest_data.decode("utf-8")
            if not json_nesting_within_limit(manifest_text):
                raise ValueError("Invalid LEOS backup manifest structure")
            manifest = json.loads(manifest_text)
        except (OSError, UnicodeError, json.JSONDecodeError, RecursionError, ValueError):
            raise ValueError("Selected LEOS backup pair is missing, unsafe or unreadable") from None

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
            or len(backup_data) != manifest["size"]
            or hashlib.sha256(backup_data).hexdigest() != manifest["sha256"]
            or _decode_backup(backup_data) is None
        ):
            raise ValueError("Selected LEOS backup failed integrity or settings validation")

        self._ensure_backup_directory()
        backup_target = self.backup_dir / f"{backup_id}.bak"
        manifest_target = self.backup_dir / f"{backup_id}.json"
        if any(path.exists() or path.is_symlink() for path in (backup_target, manifest_target)):
            raise FileExistsError("This LEOS backup identifier is already present")

        created: list[Path] = []
        try:
            created.append(self._write_new_export_file(self.backup_dir, backup_target.name, backup_data))
            created.append(self._write_new_export_file(self.backup_dir, manifest_target.name, manifest_data))
        except Exception:
            for path in created:
                try:
                    if not path.is_symlink() and path.is_file():
                        path.unlink()
                except OSError:
                    pass
            raise
        self._prune_old_backups(preserve_backup_ids={backup_id})
        return backup_id

    def _quarantine_corrupt_settings(self, raw_settings: bytes) -> str:
        """Preserve bounded unreadable settings bytes before an explicit recovery."""
        self._ensure_backup_directory()
        quarantine_id = uuid.uuid4().hex
        data_name = f"corrupt-settings-{quarantine_id}.bin"
        metadata_name = f"corrupt-settings-{quarantine_id}.meta"
        data_path = self.backup_dir / data_name
        metadata_path = self.backup_dir / metadata_name
        _atomic_write(data_path, raw_settings)
        metadata = {
            "schema_version": 1,
            "kind": "unreadable-leos-settings",
            "quarantine_id": quarantine_id,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "size": len(raw_settings),
            "sha256": hashlib.sha256(raw_settings).hexdigest(),
        }
        try:
            encoded = (json.dumps(metadata, sort_keys=True) + "\n").encode("utf-8")
            _atomic_write(metadata_path, encoded)
        except Exception:
            data_path.unlink(missing_ok=True)
            raise
        return quarantine_id

    def _verified_backup(self, backup_id: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
        if not isinstance(backup_id, str) or not _BACKUP_ID.fullmatch(backup_id):
            return None
        if any(candidate.is_symlink() for candidate in (self.backup_dir, *self.backup_dir.parents)):
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
            any(candidate.is_symlink() for candidate in (self.backup_dir, *self.backup_dir.parents))
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

        # Preserve the live settings before replacing them. A valid file gets a
        # normal restorable snapshot; unreadable bytes are quarantined verbatim.
        try:
            self.settings.validate_current_file()
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError, RecursionError):
            raw_settings = _read_regular_file(
                self.settings.path,
                MAX_SETTINGS_BYTES,
                allow_empty=True,
            )
            recovery_backup_id = self._quarantine_corrupt_settings(raw_settings)
        else:
            recovery_backup_id = self._create_backup(preserve_backup_ids={backup_id})

        self.settings.replace_all(values, confirmed=True)
        return recovery_backup_id
