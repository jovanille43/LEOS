"""Safe, reversible activation of the packaged LEOS Plasma icon theme."""

from __future__ import annotations

import configparser
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable

from leos_core.paths import config_home as xdg_config_home, data_home as xdg_data_home, state_home as xdg_state_home

ICON_THEME = "leos"
SCHEMA_VERSION = 1
MANAGED_BY = "LEOS Plasma Icon Theme Manager"
MAX_STATE_BYTES = 64 * 1024
MAX_CONFIG_BYTES = 1024 * 1024
_THEME_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _read_regular_text(path: Path, maximum: int) -> str | None:
    if path.is_symlink() or path.parent.is_symlink():
        return None
    try:
        with path.open("rb") as stream:
            raw = stream.read(maximum + 1)
        if len(raw) > maximum:
            return None
        return raw.decode("utf-8")
    except (OSError, UnicodeError):
        return None


class PlasmaIconThemeManager:
    """Apply the user's LEOS icon theme while preserving the previous theme."""

    def __init__(
        self,
        *,
        config_home: Path | None = None,
        data_home: Path | None = None,
        state_home: Path | None = None,
        system_icon_root: Path = Path("/usr/share/icons"),
        apply_executable: str | None = None,
        runner: Callable[..., Any] | None = None,
    ) -> None:
        self.config_home = config_home or Path(xdg_config_home())
        self.data_home = data_home or Path(xdg_data_home())
        self.state_home = state_home or Path(xdg_state_home())
        self.system_icon_root = system_icon_root
        self.config_file = self.config_home / "kdeglobals"
        self.state_file = self.state_home / "leos" / "icon-theme.json"
        self.apply_executable = apply_executable
        self.runner = runner or subprocess.run

    def _executable(self) -> str | None:
        if self.apply_executable:
            return self.apply_executable
        found = shutil.which("plasma-changeicons")
        if found:
            return found
        for candidate in (Path("/usr/libexec/plasma-changeicons"), Path("/usr/lib64/libexec/plasma-changeicons")):
            if candidate.is_file() and not candidate.is_symlink():
                return str(candidate)
        return None

    def tool_available(self) -> bool:
        return self._executable() is not None

    def theme_installed(self) -> bool:
        for root in (self.data_home / "icons", self.system_icon_root):
            directory = root / ICON_THEME
            metadata = directory / "index.theme"
            if directory.is_symlink() or metadata.is_symlink() or not metadata.is_file():
                continue
            if _read_regular_text(metadata, 256 * 1024) is not None:
                return True
        return False

    def current_theme(self) -> str | None:
        content = _read_regular_text(self.config_file, MAX_CONFIG_BYTES)
        if content is None:
            return None
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.optionxform = str
        try:
            parser.read_string(content)
            value = parser.get("Icons", "Theme", fallback="").strip()
        except configparser.Error:
            return None
        return value if _THEME_RE.fullmatch(value) else None

    def _read_state(self) -> dict[str, Any]:
        content = _read_regular_text(self.state_file, MAX_STATE_BYTES)
        if content is None:
            return {}
        try:
            state = json.loads(content)
        except json.JSONDecodeError:
            return {}
        previous = state.get("previous_theme") if isinstance(state, dict) else None
        if (
            not isinstance(state, dict)
            or type(state.get("schema_version")) is not int
            or state.get("schema_version") != SCHEMA_VERSION
            or state.get("managed_by") != MANAGED_BY
            or not isinstance(previous, str)
            or not _THEME_RE.fullmatch(previous)
        ):
            return {}
        return state

    def can_restore(self) -> bool:
        return bool(self._read_state().get("previous_theme"))

    def _write_state(self, state: dict[str, Any]) -> None:
        if self.state_file.is_symlink() or self.state_file.parent.is_symlink():
            raise ValueError("LEOS icon-theme state path cannot be a symbolic link")
        if self.state_file.exists() and not self._read_state():
            raise ValueError("Existing LEOS icon-theme state is invalid; it was left untouched")
        self.state_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.state_file.parent.is_symlink():
            raise ValueError("LEOS icon-theme state directory cannot be a symbolic link")
        payload = (json.dumps(state, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        if len(payload) > MAX_STATE_BYTES:
            raise ValueError("LEOS icon-theme state is too large")
        os.chmod(self.state_file.parent, 0o700)
        fd, temporary = tempfile.mkstemp(prefix="icon-theme.", suffix=".tmp", dir=self.state_file.parent)
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

    def _apply(self, theme: str) -> None:
        if not _THEME_RE.fullmatch(theme):
            raise ValueError("Identifiant de thème d'icônes KDE invalide")
        executable = self._executable()
        if not executable:
            raise FileNotFoundError("L'outil plasma-changeicons est indisponible.")
        try:
            result = self.runner(
                [executable, theme],
                shell=False,
                capture_output=True,
                text=True,
                timeout=12,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("KDE n'a pas terminé l'application du thème d'icônes dans le délai prévu.") from exc
        if result.returncode != 0:
            detail = (getattr(result, "stderr", "") or "").strip()
            raise RuntimeError(detail or "KDE a refusé d'appliquer le thème d'icônes.")

    def apply_theme(self) -> str:
        if not self.tool_available():
            raise FileNotFoundError("plasma-changeicons is unavailable")
        if not self.theme_installed():
            raise FileNotFoundError("Le paquet du thème d'icônes LEOS n'est pas installé.")
        if self.state_file.is_symlink():
            raise ValueError("LEOS icon-theme state path cannot be a symbolic link")
        current = self.current_theme()
        if current is None:
            raise RuntimeError("Le thème d'icônes KDE actuel ne peut pas être identifié ; aucun changement n'a été effectué.")
        state = self._read_state()
        previous = state.get("previous_theme")
        if current.lower() != ICON_THEME:
            previous = current
        elif not previous:
            raise RuntimeError("Les icônes LEOS sont déjà actives, mais le thème précédent est indisponible.")
        self._write_state({
            "schema_version": SCHEMA_VERSION,
            "managed_by": MANAGED_BY,
            "previous_theme": previous,
            "last_applied": ICON_THEME,
            "apply_pending": True,
        })
        self._apply(ICON_THEME)
        if self.current_theme() != ICON_THEME:
            raise RuntimeError("KDE did not confirm activation of the LEOS icon theme.")
        self._write_state({
            "schema_version": SCHEMA_VERSION,
            "managed_by": MANAGED_BY,
            "previous_theme": previous,
            "last_applied": ICON_THEME,
            "apply_pending": False,
        })
        return "Thème d'icônes LEOS appliqué."

    def restore_previous_theme(self) -> str:
        previous = self._read_state().get("previous_theme")
        if not isinstance(previous, str) or not previous:
            raise FileNotFoundError("Aucun thème d'icônes KDE précédent n'est disponible")
        self._apply(previous)
        if self.current_theme() != previous:
            raise RuntimeError("KDE n'a pas confirmé la restauration du thème d'icônes précédent.")
        if self.state_file.is_symlink():
            raise ValueError("LEOS icon-theme state path cannot be a symbolic link")
        self.state_file.unlink(missing_ok=True)
        return f"Thème d'icônes précédent restauré : {previous}."
