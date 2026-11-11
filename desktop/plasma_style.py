"""Explicit, reversible application of the packaged LEOS Plasma Style."""
from __future__ import annotations

import configparser
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable

STYLE_ID = "leos"
STYLE_NAME = "LEOS"
MANAGED_BY = "LEOS Plasma Style Manager"
SCHEMA_VERSION = 1


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
            os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
        )
        self.config_home = config_home or Path(
            os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
        )
        self.state_home = state_home or Path(
            os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")
        )
        self.system_theme_root = system_theme_root
        self.user_theme_root = self.data_home / "plasma" / "desktoptheme"
        self.config_file = self.config_home / "plasmarc"
        self.state_file = self.state_home / "leos" / "plasma-style.json"
        self.apply_executable = apply_executable
        self.runner = runner or subprocess.run

    def tool_available(self) -> bool:
        return bool(self.apply_executable or shutil.which("plasma-apply-desktoptheme"))

    def style_installed(self) -> bool:
        for root in (self.user_theme_root, self.system_theme_root):
            directory = root / STYLE_ID
            metadata = directory / "metadata.json"
            if directory.is_symlink() or metadata.is_symlink() or not metadata.is_file():
                continue
            try:
                payload = json.loads(metadata.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            plugin = payload.get("KPlugin", {}) if isinstance(payload, dict) else {}
            if isinstance(plugin, dict) and plugin.get("Id") == STYLE_ID:
                return True
        return False

    def current_style(self) -> str | None:
        if self.config_file.is_symlink() or not self.config_file.is_file():
            return None
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.optionxform = str
        try:
            parser.read(self.config_file, encoding="utf-8")
            value = parser.get("Theme", "name", fallback="").strip()
        except (OSError, configparser.Error):
            return None
        if not value or len(value) > 80 or any(ch in value for ch in ("/", "\", "\n", "\r")):
            return None
        return value

    def _read_state(self) -> dict[str, Any]:
        if self.state_file.is_symlink() or not self.state_file.is_file():
            return {}
        try:
            state = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
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
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        if self.state_file.parent.is_symlink():
            raise ValueError("Symbolic-link Plasma style state directories are not accepted")
        payload = json.dumps(state, indent=2, ensure_ascii=False) + "\\n"
        fd, temporary = tempfile.mkstemp(prefix="plasma-style.", suffix=".tmp", dir=self.state_file.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o600)
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

    def apply_style(self) -> str:
        if not self.tool_available():
            raise FileNotFoundError("plasma-apply-desktoptheme is unavailable")
        if not self.style_installed():
            raise FileNotFoundError("The LEOS Plasma Style package is not installed")
        if self.state_file.is_symlink():
            raise ValueError("Symbolic-link Plasma style state files are not accepted")
        state = self._read_state()
        current = self.current_style()
        if current is None:
            raise RuntimeError("The active Plasma Style cannot be identified; no change was made.")
        previous = state.get("previous_style")
        if current.lower() != STYLE_ID:
            previous = current
        elif not previous:
            raise RuntimeError("LEOS is already active but its previous Plasma Style is unavailable.")
        self._write_state({
            "schema_version": SCHEMA_VERSION,
            "managed_by": MANAGED_BY,
            "previous_style": previous,
            "last_applied": STYLE_ID,
            "apply_pending": True,
        })
        self._apply(STYLE_ID)
        self._write_state({
            "schema_version": SCHEMA_VERSION,
            "managed_by": MANAGED_BY,
            "previous_style": previous,
            "last_applied": STYLE_ID,
            "apply_pending": False,
        })
        return "Style Plasma LEOS appliqué."

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
