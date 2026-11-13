"""Explicit, reversible application of the packaged LEOS Plasma Style."""
from __future__ import annotations

import configparser
import json
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable

STYLE_ID = "leos"
STYLE_NAME = "LEOS"
MANAGED_BY = "LEOS Plasma Style Manager"
from leos_core.paths import (
    config_home as xdg_config_home,
    data_home as xdg_data_home,
    state_home as xdg_state_home,
)

SCHEMA_VERSION = 1
MAX_PLASMA_STATE_BYTES = 64 * 1024
MAX_PLASMA_CONFIG_BYTES = 1024 * 1024
MAX_PLASMA_METADATA_BYTES = 256 * 1024



def _read_bounded_text(path: Path, max_bytes: int) -> str | None:
    """Read a bounded regular file without following a final symlink or blocking on a FIFO."""
    if type(max_bytes) is not int or max_bytes < 0:
        return None
    if path.parent.is_symlink():
        return None
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError:
        return None
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > max_bytes:
            return None
        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
        if (
            len(raw) > max_bytes
            or len(raw) != before.st_size
            or before.st_dev != after.st_dev
            or before.st_ino != after.st_ino
            or before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
            or before.st_ctime_ns != after.st_ctime_ns
        ):
            return None
        return raw.decode("utf-8")
    except (OSError, UnicodeError):
        return None
    finally:
        os.close(descriptor)


class PlasmaStyleManager:
    """Apply the packaged Plasma Style without editing plasmarc directly."""

    def __init__(
        self,
        data_home: Path | None = None,
        config_home: Path | None = None,
        state_home: Path | None = None,
        system_theme_root: Path = Path("/usr/share/plasma/desktoptheme"),
        apply_executable: str | None = None,
        runner: Callable[..., Any] | None = None,
    ) -> None:
        self.data_home = data_home or Path(
            xdg_data_home()
        )
        self.config_home = config_home or Path(
            xdg_config_home()
        )
        self.state_home = state_home or Path(
            xdg_state_home()
        )
        self.system_theme_root = system_theme_root
        self.user_theme_root = self.data_home / "plasma" / "desktoptheme"
        self.config_file = self.config_home / "plasmarc"
        self.state_file = self.state_home / "leos" / "plasma-style.json"
        self.apply_executable = apply_executable
        self.runner = runner or subprocess.run

    def tool_available(self) -> bool:
        return bool(self.apply_executable or shutil.which("plasma-apply-desktoptheme"))

    def style_installed(self, style_id: str = STYLE_ID) -> bool:
        if not isinstance(style_id, str) or not re.fullmatch(r"[a-z][a-z0-9-]{1,31}", style_id):
            return False
        for root in (self.user_theme_root, self.system_theme_root):
            directory = root / style_id
            metadata = directory / "metadata.json"
            if directory.is_symlink() or metadata.is_symlink() or not metadata.is_file():
                continue
            metadata_text = _read_bounded_text(metadata, MAX_PLASMA_METADATA_BYTES)
            if metadata_text is None:
                continue
            try:
                payload = json.loads(metadata_text)
            except json.JSONDecodeError:
                continue
            plugin = payload.get("KPlugin", {}) if isinstance(payload, dict) else {}
            if isinstance(plugin, dict) and plugin.get("Id") == style_id:
                return True
        return False

    def current_style(self) -> str | None:
        if self.config_file.is_symlink() or not self.config_file.is_file():
            return None
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.optionxform = str
        content = _read_bounded_text(self.config_file, MAX_PLASMA_CONFIG_BYTES)
        if content is None:
            return None
        try:
            parser.read_string(content)
            value = parser.get("Theme", "name", fallback="").strip()
        except configparser.Error:
            return None
        if not value or len(value) > 80 or any(ch in value for ch in ("/", chr(92), chr(10), chr(13))):
            return None
        return value

    def _read_state(self) -> dict[str, Any]:
        if self.state_file.is_symlink() or not self.state_file.is_file():
            return {}
        content = _read_bounded_text(self.state_file, MAX_PLASMA_STATE_BYTES)
        if content is None:
            return {}
        try:
            state = json.loads(content)
        except json.JSONDecodeError:
            return {}
        if (
            not isinstance(state, dict)
            or type(state.get("schema_version")) is not int
            or state.get("schema_version") != SCHEMA_VERSION
            or state.get("managed_by") != MANAGED_BY
        ):
            return {}
        previous = state.get("previous_style")
        if previous is not None and (
            not isinstance(previous, str)
            or not previous
            or len(previous) > 80
            or any(ch in previous for ch in ("/", "\\\\", "\\n", "\\r"))
        ):
            return {}
        return state

    def can_restore(self) -> bool:
        previous = self._read_state().get("previous_style")
        return isinstance(previous, str) and bool(previous)

    def _write_state(self, state: dict[str, Any]) -> None:
        if self.state_file.is_symlink():
            raise ValueError("Symbolic-link Plasma style state files are not accepted")
        if self.state_file.exists() and not self._read_state():
            raise ValueError("Existing Plasma style state is invalid; it was left untouched")
        self.state_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.state_file.parent.is_symlink():
            raise ValueError("Symbolic-link Plasma style state directories are not accepted")
        payload = (json.dumps(state, indent=2, ensure_ascii=False) + chr(10)).encode("utf-8")
        if len(payload) > MAX_PLASMA_STATE_BYTES:
            raise ValueError("Plasma style state exceeds its storage limit")
        os.chmod(self.state_file.parent, 0o700)
        fd, temporary = tempfile.mkstemp(prefix="plasma-style.", suffix=".tmp", dir=self.state_file.parent)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.state_file)
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass

    def _apply(self, style: str) -> None:
        if not isinstance(style, str) or not style or len(style) > 80:
            raise ValueError("Invalid Plasma Style identifier")
        executable = self.apply_executable or shutil.which("plasma-apply-desktoptheme")
        if not executable:
            raise FileNotFoundError("plasma-apply-desktoptheme is unavailable")
        try:
            result = self.runner(
                [executable, style],
                shell=False,
                capture_output=True,
                text=True,
                timeout=12,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Plasma did not finish applying the desktop style in time") from exc
        if result.returncode != 0:
            detail = (getattr(result, "stderr", "") or "").strip()
            raise RuntimeError(detail or "Plasma refused to apply the desktop style")

    def apply_style(self, style_id: str = STYLE_ID) -> str:
        if not isinstance(style_id, str) or not re.fullmatch(r"[a-z][a-z0-9-]{1,31}", style_id):
            raise ValueError("Invalid Plasma Style identifier")
        if not self.tool_available():
            raise FileNotFoundError("plasma-apply-desktoptheme is unavailable")
        if not self.style_installed(style_id):
            raise FileNotFoundError("The requested LEOS Plasma Style package is not installed")
        if self.state_file.is_symlink():
            raise ValueError("Symbolic-link Plasma style state files are not accepted")
        state = self._read_state()
        current = self.current_style()
        if current is None:
            raise RuntimeError("The active Plasma Style cannot be identified; no change was made.")
        previous = state.get("previous_style")
        if current.lower() != style_id.lower():
            if not current.lower().startswith("leos-") or not previous:
                previous = current
        elif not previous:
            raise RuntimeError("The requested LEOS Plasma Style is active but its previous style is unavailable.")
        self._write_state({
            "schema_version": SCHEMA_VERSION,
            "managed_by": MANAGED_BY,
            "previous_style": previous,
            "last_applied": style_id,
            "apply_pending": True,
        })
        self._apply(style_id)
        self._write_state({
            "schema_version": SCHEMA_VERSION,
            "managed_by": MANAGED_BY,
            "previous_style": previous,
            "last_applied": style_id,
            "apply_pending": False,
        })
        return f"Style Plasma LEOS appliqué : {style_id}."

    def restore_previous_style(self) -> str:
        state = self._read_state()
        previous = state.get("previous_style")
        if not isinstance(previous, str) or not previous:
            raise FileNotFoundError("No previous Plasma Style is available")
        self._apply(previous)
        if self.state_file.is_symlink():
            raise ValueError("Symbolic-link Plasma style state files are not accepted")
        self.state_file.unlink(missing_ok=True)
        return f"Style Plasma précédent restauré : {previous}."
