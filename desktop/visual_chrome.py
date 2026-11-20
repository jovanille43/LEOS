"""Safely activate and restore LEOS Plasma splash and cursor themes."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable

from leos_core.paths import config_home as xdg_config_home
from leos_core.paths import data_home as xdg_data_home
from leos_core.paths import state_home as xdg_state_home

SCHEMA_VERSION = 1
MANAGED_BY = "LEOS Plasma visual chrome"
MAX_STATE_BYTES = 32 * 1024
_THEME_ID = re.compile(r"^[a-z][a-z0-9.-]{2,80}$")
_SETTINGS = {
    "splash": ("ksplashrc", "KSplash", "Theme"),
    "cursor": ("kcminputrc", "Mouse", "cursorTheme"),
}


def _read_state(path: Path) -> dict[str, Any]:
    if path.is_symlink() or path.parent.is_symlink() or not path.is_file():
        return {}
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_STATE_BYTES + 1)
        if len(raw) > MAX_STATE_BYTES:
            return {}
        state = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    if (
        not isinstance(state, dict)
        or type(state.get("schema_version")) is not int
        or state.get("schema_version") != SCHEMA_VERSION
        or state.get("managed_by") != MANAGED_BY
        or not isinstance(state.get("previous"), dict)
        or not isinstance(state.get("last_applied"), dict)
    ):
        return {}
    for key in _SETTINGS:
        if key not in state["previous"] or key not in state["last_applied"]:
            return {}
        for collection in ("previous", "last_applied"):
            value = state[collection][key]
            if value is not None and not isinstance(value, str):
                return {}
    return state


class PlasmaVisualChromeManager:
    """Apply splash/cursor settings only after a reversible user confirmation."""

    def __init__(
        self,
        *,
        config_home: Path | None = None,
        data_home: Path | None = None,
        state_home: Path | None = None,
        icon_theme_root: Path = Path("/usr/share/icons"),
        look_and_feel_root: Path = Path("/usr/share/plasma/look-and-feel"),
        command_lookup: Callable[[str], str | None] | None = None,
        runner: Callable[..., Any] | None = None,
    ) -> None:
        self.config_home = Path(config_home) if config_home is not None else Path(xdg_config_home())
        self.data_home = Path(data_home) if data_home is not None else Path(xdg_data_home())
        self.state_home = Path(state_home) if state_home is not None else Path(xdg_state_home())
        self.icon_theme_root = Path(icon_theme_root)
        self.look_and_feel_root = Path(look_and_feel_root)
        self.state_file = self.state_home / "leos" / "visual-chrome.json"
        self.command_lookup = command_lookup or shutil.which
        self.runner = runner or subprocess.run

    def tool_available(self) -> bool:
        return bool(self.command_lookup("kreadconfig6") and self.command_lookup("kwriteconfig6"))

    def splash_theme_installed(self, theme_id: str = "org.leos.desktop") -> bool:
        if not isinstance(theme_id, str) or not _THEME_ID.fullmatch(theme_id):
            return False
        directory = self.look_and_feel_root / theme_id
        manifest = directory / "manifest.json"
        splash = directory / "contents" / "splash" / "Splash.qml"
        if directory.is_symlink() or manifest.is_symlink() or splash.is_symlink():
            return False
        if not manifest.is_file() or not splash.is_file() or manifest.stat().st_size > 128 * 1024:
            return False
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return False
        plugin = payload.get("KPlugin", {}) if isinstance(payload, dict) else {}
        return (
            isinstance(plugin, dict)
            and payload.get("KPackageStructure") == "Plasma/LookAndFeel"
            and plugin.get("Id") == theme_id
        )

    def cursor_theme_installed(self, theme_id: str) -> bool:
        if not isinstance(theme_id, str) or not _THEME_ID.fullmatch(theme_id):
            return False
        roots = (self.data_home / "icons", self.icon_theme_root)
        return any(
            not (root / theme_id).is_symlink()
            and not (root / theme_id / "index.theme").is_symlink()
            and (root / theme_id / "index.theme").is_file()
            for root in roots
        )

    def _run(self, command: list[str]) -> Any:
        result = self.runner(
            command,
            shell=False,
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if result.returncode != 0:
            detail = (getattr(result, "stderr", "") or "").strip()
            raise RuntimeError(detail or "KDE n'a pas accepté le réglage visuel LEOS.")
        return result

    def _read_setting(self, name: str) -> str | None:
        executable = self.command_lookup("kreadconfig6")
        if not executable:
            raise FileNotFoundError("kreadconfig6 est indisponible.")
        filename, group, key = _SETTINGS[name]
        path = self.config_home / filename
        if path.is_symlink():
            raise ValueError(f"Le fichier de configuration KDE {filename} est un lien symbolique.")
        result = self._run([
            executable, "--file", str(path), "--group", group,
            "--key", key, "--default", "",
        ])
        value = (getattr(result, "stdout", "") or "").strip()
        return value or None

    def _write_setting(self, name: str, value: str | None) -> None:
        executable = self.command_lookup("kwriteconfig6")
        if not executable:
            raise FileNotFoundError("kwriteconfig6 est indisponible.")
        filename, group, key = _SETTINGS[name]
        path = self.config_home / filename
        if path.is_symlink():
            raise ValueError(f"Le fichier de configuration KDE {filename} est un lien symbolique.")
        command = [executable, "--file", str(path), "--group", group, "--key", key]
        command.append("--delete" if value is None else value)
        self._run(command)

    def _save_state(self, previous: dict[str, str | None], last_applied: dict[str, str | None]) -> None:
        if self.state_file.is_symlink() or self.state_file.parent.is_symlink():
            raise ValueError("L'état des réglages visuels LEOS ne peut pas utiliser de lien symbolique.")
        if self.state_file.exists() and not _read_state(self.state_file):
            raise ValueError("L'état visuel LEOS existant est invalide ; il est conservé sans modification.")
        self.state_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.state_file.parent, 0o700)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "managed_by": MANAGED_BY,
            "previous": previous,
            "last_applied": last_applied,
        }
        encoded = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if len(encoded) > MAX_STATE_BYTES:
            raise ValueError("L'état des réglages visuels LEOS dépasse sa limite.")
        fd, temporary = tempfile.mkstemp(prefix="visual-chrome.", suffix=".tmp", dir=self.state_file.parent)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.state_file)
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass

    def can_restore(self) -> bool:
        return bool(_read_state(self.state_file))

    def apply(self, splash_theme_id: str, cursor_theme_id: str) -> str:
        if not self.tool_available():
            raise FileNotFoundError("Les outils kreadconfig6/kwriteconfig6 sont indisponibles.")
        if not self.splash_theme_installed(splash_theme_id):
            raise FileNotFoundError("L'écran de chargement Plasma LEOS n'est pas installé.")
        if not self.cursor_theme_installed(cursor_theme_id):
            raise FileNotFoundError("Le thème de curseur LEOS personnalisé n'est pas installé.")

        current = {key: self._read_setting(key) for key in _SETTINGS}
        existing = _read_state(self.state_file)
        previous = existing["previous"] if existing and current == existing["last_applied"] else current
        target = {"splash": splash_theme_id, "cursor": cursor_theme_id}
        self._save_state(previous, target)

        try:
            for key, value in target.items():
                self._write_setting(key, value)
            verified = {key: self._read_setting(key) for key in _SETTINGS}
            if verified != target:
                raise RuntimeError("KDE n'a pas confirmé l'activation du splash et du curseur LEOS.")
        except Exception as error:
            try:
                for key, value in previous.items():
                    self._write_setting(key, value)
                if {key: self._read_setting(key) for key in _SETTINGS} != previous:
                    raise RuntimeError("KDE n'a pas confirmé le retour visuel arrière.")
            except Exception as rollback_error:
                raise RuntimeError(
                    f"Activation visuelle LEOS interrompue : {error}. "
                    f"Le retour arrière nécessite une vérification : {rollback_error}."
                ) from error
            self.state_file.unlink(missing_ok=True)
            raise
        return "Écran de chargement Plasma et curseur LEOS configurés pour la prochaine ouverture de session."

    def restore_previous(self) -> str:
        state = _read_state(self.state_file)
        if not state:
            raise FileNotFoundError("Aucun réglage visuel Plasma précédent n'est disponible.")
        current = {key: self._read_setting(key) for key in _SETTINGS}
        if current != state["last_applied"]:
            raise RuntimeError(
                "Les réglages visuels ont changé depuis l'application du profil LEOS ; "
                "la restauration automatique est refusée pour préserver les choix récents."
            )
        for key, value in state["previous"].items():
            self._write_setting(key, value)
        restored = {key: self._read_setting(key) for key in _SETTINGS}
        if restored != state["previous"]:
            raise RuntimeError("KDE n'a pas confirmé la restauration des réglages visuels précédents.")
        if self.state_file.is_symlink():
            raise ValueError("L'état des réglages visuels LEOS est un lien symbolique.")
        self.state_file.unlink(missing_ok=True)
        return "Écran de chargement et curseur précédents restaurés."
